"""Telegram availability probe — hybrid cadence.

Steady-state: background probe every 60s refreshes the cached flag.
At-send-time check consults the cached flag (no extra API call).
On send failure the adapter flips to ``unavailable`` immediately and
schedules aggressive 5s-cadence recovery probing for up to 60s. All
transitions emit OTel spans.

Nine failure classes (research §2.7 + §4.3) each have a named
``FailureClass``. Dispositions live on the adapter layer; this module
is probe-only.
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Awaitable, Callable

from . import observability as obs


_LOGGER = logging.getLogger(__name__)


PROBE_INTERVAL_S = 60.0
AGGRESSIVE_PROBE_INTERVAL_S = 5.0
AGGRESSIVE_PROBE_DURATION_S = 60.0


class FailureClass(str, Enum):
    plugin_not_installed = "plugin_not_installed"
    token_missing = "token_missing"
    plugin_not_connected = "plugin_not_connected"
    api_unreachable = "api_unreachable"
    conflict_stale_poller = "conflict_stale_poller"
    token_invalid = "token_invalid"
    blocked_by_user = "blocked_by_user"
    rate_limited = "rate_limited"
    background_dispatch = "background_dispatch"


class AvailabilityState(str, Enum):
    available = "available"
    unavailable = "unavailable"
    unknown = "unknown"


@dataclass
class ProbeResult:
    available: bool
    latency_ms: float | None = None
    failure_class: FailureClass | None = None
    detail: str | None = None


GetMeProbeFn = Callable[[], Awaitable[ProbeResult]]
McpToolProbeFn = Callable[[], Awaitable[bool]]


def plugin_installed(cache_dir: Path | None = None) -> bool:
    """Filesystem check. The plugin lives at the cache path research §2.1."""
    path = Path(
        cache_dir
        or os.environ.get(
            "TELEGRAM_PLUGIN_CACHE_DIR",
            "~/.claude/plugins/cache/claude-plugins-official/telegram",
        )
    ).expanduser()
    return path.exists() and any(path.iterdir()) if path.exists() else False


def token_configured(env_path: Path | None = None) -> bool:
    p = Path(
        env_path or os.environ.get("TELEGRAM_ENV_PATH", "~/.claude/channels/telegram/.env")
    ).expanduser()
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        return True
    if not p.exists():
        return False
    try:
        for line in p.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                _, _, value = line.partition("=")
                return bool(value.strip().strip('"').strip("'"))
    except OSError:
        return False
    return False


@dataclass
class AvailabilityProbe:
    """Hybrid cadence probe.

    Two external hooks injected:
      - ``getme_probe`` — async call returning a ProbeResult; used for
        both steady-state and aggressive probing.
      - ``mcp_tool_probe`` — async boolean; returns True if the Claude
        session in which this probe runs exposes the plugin's ``reply``
        tool (research §4.1 step 3). None for out-of-session callers —
        the probe treats "no MCP session" as background-dispatch, which
        is not a failure for the direct-Bot-API path.
    """

    getme_probe: GetMeProbeFn
    mcp_tool_probe: McpToolProbeFn | None = None
    cache_dir: Path | None = None
    env_path: Path | None = None
    clock: Callable[[], float] = time.monotonic

    _state: AvailabilityState = AvailabilityState.unknown
    _last_probe_at: float | None = None
    _last_result: ProbeResult | None = None
    _background_task: asyncio.Task[None] | None = field(
        default=None, init=False, repr=False
    )
    _aggressive_until: float = 0.0

    @property
    def state(self) -> AvailabilityState:
        return self._state

    @property
    def current(self) -> bool:
        return self._state == AvailabilityState.available

    @property
    def last_failure_class(self) -> FailureClass | None:
        return self._last_result.failure_class if self._last_result else None

    async def probe_once(self) -> ProbeResult:
        """Run a single probe across all four availability conditions."""
        # 1. Plugin installed?
        if not plugin_installed(self.cache_dir):
            result = ProbeResult(
                available=False,
                failure_class=FailureClass.plugin_not_installed,
                detail="plugin cache directory absent",
            )
            self._record(result, cached=False)
            return result

        # 2. Token configured?
        if not token_configured(self.env_path):
            result = ProbeResult(
                available=False,
                failure_class=FailureClass.token_missing,
                detail="TELEGRAM_BOT_TOKEN not set",
            )
            self._record(result, cached=False)
            return result

        # 3. MCP tool probe (in-session only).
        if self.mcp_tool_probe is not None:
            connected = await self.mcp_tool_probe()
            if not connected:
                result = ProbeResult(
                    available=False,
                    failure_class=FailureClass.plugin_not_connected,
                    detail="reply tool not advertised by MCP session",
                )
                self._record(result, cached=False)
                return result

        # 4. getMe (API reachability + token validity).
        result = await self.getme_probe()
        self._record(result, cached=False)
        return result

    def cached_available(self) -> bool:
        """Returns the cached flag without probing. Callers use this
        at send-time for the cheap path."""
        obs.availability_probe(
            cached=True,
            available=self.current,
            latency_ms=None,
            failure_class=(
                self._last_result.failure_class.value
                if self._last_result and self._last_result.failure_class
                else None
            ),
        )
        return self.current

    async def mark_failure(self, failure_class: FailureClass, *, detail: str = "") -> None:
        """Called by the adapter when a send fails. Flips to
        unavailable immediately and schedules aggressive recovery
        probing for AGGRESSIVE_PROBE_DURATION_S."""
        result = ProbeResult(
            available=False, failure_class=failure_class, detail=detail
        )
        self._record(result, cached=False, forced_transition=True)
        self._aggressive_until = self.clock() + AGGRESSIVE_PROBE_DURATION_S

    async def start_background(self) -> None:
        """Fire-and-forget. Caller awaits `stop_background()` to shut
        down cleanly. Safe to call twice; second call is no-op."""
        if self._background_task is not None and not self._background_task.done():
            return
        self._background_task = asyncio.create_task(self._run_background())

    async def stop_background(self) -> None:
        if self._background_task is None:
            return
        self._background_task.cancel()
        try:
            await self._background_task
        except asyncio.CancelledError:
            # Expected flow on cancel — bare pass per tightened CDC 2.
            pass
        except Exception:
            # Amendment #26 — teardown CDC 2: surface exception to
            # observability. No span in scope; logger.debug is the
            # tightened-CDC fallback.
            _LOGGER.debug(
                "availability_stop_background_failed", exc_info=True
            )
        self._background_task = None

    async def _run_background(self) -> None:
        while True:
            try:
                await self.probe_once()
            except Exception as e:  # noqa: BLE001 — never let probe crash loop
                self._record(
                    ProbeResult(
                        available=False,
                        failure_class=FailureClass.api_unreachable,
                        detail=f"probe raised: {e}",
                    ),
                    cached=False,
                )
            now = self.clock()
            interval = (
                AGGRESSIVE_PROBE_INTERVAL_S
                if now < self._aggressive_until
                else PROBE_INTERVAL_S
            )
            try:
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                raise

    # ---- internal ------------------------------------------------

    def _record(
        self,
        result: ProbeResult,
        *,
        cached: bool,
        forced_transition: bool = False,
    ) -> None:
        prev = self._state
        if result.available:
            next_state = AvailabilityState.available
        else:
            next_state = AvailabilityState.unavailable
        self._last_result = result
        self._last_probe_at = self.clock()
        self._state = next_state

        obs.availability_probe(
            cached=cached,
            available=result.available,
            latency_ms=result.latency_ms,
            failure_class=(
                result.failure_class.value if result.failure_class else None
            ),
        )
        if prev != next_state or forced_transition:
            obs.availability_transition(
                from_state=prev.value,
                to_state=next_state.value,
                reason=(
                    result.failure_class.value
                    if result.failure_class
                    else "recovery"
                ),
            )
