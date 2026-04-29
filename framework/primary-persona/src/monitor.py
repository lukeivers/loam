"""BackgroundWorkMonitor (D3).

A long-lived asyncio coroutine that subscribes to scope-of-work's
pyee emitter and a 30-second stuck-detection tick, producing a capped
structured awareness block on every `UserPromptSubmit` — injected
deterministically so STATE.md rule #7 is a hook, not an instruction.

Awareness-block constraints:
- JSON-like structured format (callers can render however they prefer)
- six categories: active / pending-decision / stuck / recently-finished
  / escalated / failed
- ≤ 5 rows per category
- token estimate ≤ 1,000 per injection

The monitor survives brief asyncio task failures (one failed tick does
not kill the coroutine) and emits its own health via OTel.
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Awaitable, Callable, Deque, Iterable, Sequence

from scope_of_work.runtime import ScopeRuntime  # type: ignore[import-not-found]
from scope_of_work.spec import ScopeState  # type: ignore[import-not-found]
from scope_of_work.projection_view import ScopeProjection  # type: ignore[import-not-found]

from . import observability as obs


# ---- public types ----------------------------------------------------


class AwarenessCategory(str, Enum):
    active = "active"
    pending_decision = "pending_decision"
    stuck = "stuck"
    recently_finished = "recently_finished"
    escalated = "escalated"
    failed = "failed"


@dataclass(frozen=True)
class AwarenessRow:
    """One row in the awareness block.

    Kept intentionally small — the block is injected on every
    UserPromptSubmit, so bytes-per-row multiplies by 6 categories × 5
    rows = up to 30 rows per turn.
    """

    scope_id: str
    goal: str
    state: str
    owner_persona: str | None = None
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "scope_id": self.scope_id,
            "goal": self.goal[:120],  # hard cap: goals over 120 chars get truncated
            "state": self.state,
        }
        if self.owner_persona:
            d["owner_persona"] = self.owner_persona
        if self.detail:
            d["detail"] = self.detail[:160]
        return d


# Approximate token count — 4 chars ≈ 1 token is the Anthropic-style
# estimate. The monitor uses this for the 1,000-token cap.
def _estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


@dataclass(frozen=True)
class AwarenessBlock:
    """The structured awareness block injected on every
    UserPromptSubmit.

    Categories are always populated (empty list if no rows). Callers
    render this as JSON or as prose; the canonical form is JSON for
    determinism.
    """

    turn_id: str
    generated_at: str
    active: tuple[AwarenessRow, ...] = ()
    pending_decision: tuple[AwarenessRow, ...] = ()
    stuck: tuple[AwarenessRow, ...] = ()
    recently_finished: tuple[AwarenessRow, ...] = ()
    escalated: tuple[AwarenessRow, ...] = ()
    failed: tuple[AwarenessRow, ...] = ()

    MAX_ROWS_PER_CATEGORY = 5
    MAX_TOKENS = 1_000

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "generated_at": self.generated_at,
            "active": [r.to_dict() for r in self.active],
            "pending_decision": [r.to_dict() for r in self.pending_decision],
            "stuck": [r.to_dict() for r in self.stuck],
            "recently_finished": [r.to_dict() for r in self.recently_finished],
            "escalated": [r.to_dict() for r in self.escalated],
            "failed": [r.to_dict() for r in self.failed],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=False)

    def token_estimate(self) -> int:
        return _estimate_tokens(self.to_json())

    def total_rows(self) -> int:
        return (
            len(self.active)
            + len(self.pending_decision)
            + len(self.stuck)
            + len(self.recently_finished)
            + len(self.escalated)
            + len(self.failed)
        )


# ---- monitor ---------------------------------------------------------


StuckReasonFn = Callable[[ScopeProjection], Awaitable[str | None]]


@dataclass
class BackgroundWorkMonitor:
    """Long-lived asyncio coroutine feeding the primary persona.

    Usage:
        monitor = BackgroundWorkMonitor(runtime)
        await monitor.start()            # spawns the tick task
        block = monitor.on_user_prompt() # synchronous snapshot
        await monitor.stop()

    The monitor listens via `runtime.subscribe_all` to real-time
    events and refreshes its stuck-detection view every 30 seconds.

    `stuck_reason_fn` is an optional async function that returns a
    short human-readable reason for a stuck scope (the Claude-via-Max
    second pass). Calls are capped per tick by `stuck_reason_budget`.
    Omitting it means stuck rows have no `detail` field.
    """

    runtime: ScopeRuntime
    tick_interval_seconds: float = 30.0
    finished_lookback_seconds: float = 3600.0  # 1 hour
    stuck_reason_fn: StuckReasonFn | None = None
    stuck_reason_budget: int = 3  # max stuck-reason calls per tick

    _task: asyncio.Task[None] | None = None
    _tick_count: int = 0
    _stop: asyncio.Event = field(default_factory=asyncio.Event)
    _recent_terminal: Deque[tuple[float, ScopeProjection]] = field(
        default_factory=lambda: deque(maxlen=64)
    )
    _stuck_reasons: dict[str, str] = field(default_factory=dict)

    # ---- lifecycle -------------------------------------------------

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop.clear()
        # Subscribe to all scope events; the store is the authoritative
        # data source so the subscription is just a trigger for "wake
        # up and refresh".
        self.runtime.subscribe_all(self._on_scope_event)
        self._task = asyncio.create_task(self._tick_loop(), name="bg-monitor")

    async def stop(self) -> None:
        self._stop.set()
        if self._task is not None:
            try:
                await asyncio.wait_for(self._task, timeout=self.tick_interval_seconds + 1)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self._task.cancel()
        self._task = None

    # ---- public: synchronous snapshot for UserPromptSubmit --------

    def on_user_prompt(self, turn_id: str | None = None) -> AwarenessBlock:
        """Produce the awareness block for a single UserPromptSubmit.

        Synchronous — monitors are allowed to be slow off the critical
        path (the tick loop), but the per-turn snapshot must not block
        the prompt pipeline.
        """
        tid = turn_id or f"turn-{uuid.uuid4()}"
        with obs.monitor_span("loam.persona.monitor.snapshot", **{"loam.persona.monitor.turn_id": tid}):
            block = self._build_block(tid)
            obs.monitor_injection_event(
                turn_id=tid, token_estimate=block.token_estimate()
            )
            return block

    # ---- internals: tick loop -------------------------------------

    async def _tick_loop(self) -> None:
        """Run ticks until stopped. Survives per-tick errors.

        Brief D3 acceptance: one failed tick does not kill the
        coroutine. We swallow exceptions per tick and log them via the
        OTel span on that tick.
        """
        while not self._stop.is_set():
            try:
                await self._tick()
            except Exception as e:  # noqa: BLE001 — intentional catch-all
                # Record the failure as an event on a tick span; the
                # monitor must survive.
                with obs.monitor_span("loam.persona.monitor.tick") as span:
                    span.record_exception(e)
                    span.set_attribute("loam.persona.monitor.tick_outcome", "error")
            # Interruptible sleep so stop() returns promptly.
            try:
                await asyncio.wait_for(
                    self._stop.wait(), timeout=self.tick_interval_seconds
                )
            except asyncio.TimeoutError:
                pass

    async def _tick(self) -> None:
        self._tick_count += 1
        with obs.monitor_span("loam.persona.monitor.tick") as span:
            span.set_attribute("loam.persona.monitor.tick_id", self._tick_count)

            # Pick up any scopes that have been closed since last tick
            # (completed / failed / cancelled) for the recently-
            # finished category. This is O(n); single-user cardinality
            # is low.
            await self._refresh_recent_terminal()

            # Optional stuck-reason second pass — only when a second-
            # pass callback is installed.
            stuck_scopes = self.runtime.list(stuck=True)
            if self.stuck_reason_fn and stuck_scopes:
                await self._annotate_stuck(stuck_scopes[: self.stuck_reason_budget])

            # Count each category for the tick event (not the full
            # awareness block, which the prompt path builds).
            active = len(self.runtime.list(states=[ScopeState.active]))
            pending = len(self.runtime.list(include_pending_extension=True))
            stuck = len(stuck_scopes)
            finished = len(self._recent_terminal)
            escalated = len(self.runtime.list(states=[ScopeState.escalated]))
            failed = len(self.runtime.list(states=[ScopeState.failed]))
            obs.monitor_tick_event(
                tick_id=self._tick_count,
                active=active,
                pending=pending,
                stuck=stuck,
                finished=finished,
                escalated=escalated,
                failed=failed,
            )

    async def _annotate_stuck(
        self, scopes: Sequence[ScopeProjection]
    ) -> None:
        """Run the optional stuck-reason second pass; stash results
        on an internal map keyed by scope_id."""
        assert self.stuck_reason_fn is not None
        for scope in scopes:
            try:
                reason = await self.stuck_reason_fn(scope)
            except Exception:
                reason = None
            if reason:
                self._stuck_reasons[scope.scope_id] = reason

    def _on_scope_event(self, event: Any) -> None:
        """pyee callback — catches terminal transitions for the
        recently-finished category without a full re-scan."""
        try:
            kind = getattr(event, "kind", None)
            if kind == "state_transitioned":
                to_state = getattr(event, "to_state", None)
                if to_state is None:
                    return
                if to_state.value in ("completed", "failed", "cancelled"):
                    proj = self.runtime.get(event.scope_id)
                    if proj is not None:
                        self._recent_terminal.append((time.time(), proj))
        except Exception:
            # Monitor must not die on event-callback errors.
            pass

    async def _refresh_recent_terminal(self) -> None:
        """Prune terminals older than the lookback window."""
        cutoff = time.time() - self.finished_lookback_seconds
        while self._recent_terminal and self._recent_terminal[0][0] < cutoff:
            self._recent_terminal.popleft()

    # ---- internals: block builder ---------------------------------

    def _build_block(self, turn_id: str) -> AwarenessBlock:
        """Assemble the awareness block from the authoritative scope-
        of-work state. Respects the per-category cap; if the block
        exceeds the token budget, trims from the lowest-priority
        category last."""

        # Query the runtime for each category.
        all_scopes = self.runtime.list()

        active_rows: list[AwarenessRow] = []
        pending_rows: list[AwarenessRow] = []
        stuck_rows: list[AwarenessRow] = []
        escalated_rows: list[AwarenessRow] = []
        failed_rows: list[AwarenessRow] = []

        for p in all_scopes:
            if p.pending_extension_axis is not None:
                pending_rows.append(self._row(p, detail=f"pending {p.pending_extension_axis.value}"))
            elif p.is_stuck:
                detail = self._stuck_reasons.get(p.scope_id)
                stuck_rows.append(self._row(p, detail=detail))
            elif p.state == ScopeState.active:
                active_rows.append(self._row(p))
            elif p.state == ScopeState.escalated:
                escalated_rows.append(self._row(p, detail=p.pause_reason))
            elif p.state == ScopeState.failed:
                failed_rows.append(self._row(p, detail=p.pause_reason))

        finished_rows = [
            self._row(p, detail=p.state.value)
            for _ts, p in list(self._recent_terminal)[-AwarenessBlock.MAX_ROWS_PER_CATEGORY :]
        ]

        block = AwarenessBlock(
            turn_id=turn_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            active=tuple(active_rows[: AwarenessBlock.MAX_ROWS_PER_CATEGORY]),
            pending_decision=tuple(
                pending_rows[: AwarenessBlock.MAX_ROWS_PER_CATEGORY]
            ),
            stuck=tuple(stuck_rows[: AwarenessBlock.MAX_ROWS_PER_CATEGORY]),
            recently_finished=tuple(
                finished_rows[: AwarenessBlock.MAX_ROWS_PER_CATEGORY]
            ),
            escalated=tuple(escalated_rows[: AwarenessBlock.MAX_ROWS_PER_CATEGORY]),
            failed=tuple(failed_rows[: AwarenessBlock.MAX_ROWS_PER_CATEGORY]),
        )

        return self._enforce_token_cap(block)

    def _enforce_token_cap(self, block: AwarenessBlock) -> AwarenessBlock:
        """If the block exceeds the token budget, trim categories
        from lowest-priority upward.

        Priority order (highest first — these are most important to
        keep): stuck, pending_decision, escalated, failed, active,
        recently_finished. We trim from the bottom of this list.
        """
        if block.token_estimate() <= AwarenessBlock.MAX_TOKENS:
            return block

        def trim(seq: tuple[AwarenessRow, ...]) -> tuple[AwarenessRow, ...]:
            # Shrink by one; if empty return as-is.
            return seq[:-1] if seq else seq

        # Mutate by replace; the categories to trim from first.
        current = block
        trim_order = (
            "recently_finished",
            "active",
            "failed",
            "escalated",
            "pending_decision",
            "stuck",
        )
        for field_name in trim_order:
            while current.token_estimate() > AwarenessBlock.MAX_TOKENS:
                rows: tuple[AwarenessRow, ...] = getattr(current, field_name)
                if not rows:
                    break
                current = _replace(current, **{field_name: trim(rows)})
            if current.token_estimate() <= AwarenessBlock.MAX_TOKENS:
                break
        return current

    def _row(
        self,
        p: ScopeProjection,
        *,
        detail: str | None = None,
    ) -> AwarenessRow:
        return AwarenessRow(
            scope_id=p.scope_id,
            goal=p.goal,
            state=p.state.value,
            owner_persona=p.owner_persona,
            detail=detail,
        )


# Small helper — dataclasses.replace works on frozen dataclasses.
from dataclasses import replace as _replace  # noqa: E402
