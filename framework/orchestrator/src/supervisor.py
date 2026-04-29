"""Memory-sidecar supervisor (Amendment 2 — hands-off-lifecycle).

Lives inside the orchestrator process per proposal §Q2 (B.1).
Continuously probes the memory sidecar, maintains a state machine
across ``normal → degraded → recovering → escalated``, coordinates
the memory-drain worker on recovery, and opens / closes escalations
per-class via ``~/.loam/supervisor-escalation.json``.

Key design constraints:

- **Silent-stay-degraded is forbidden.** Bounded retries, then LOUD
  escalation. A code path that leaves the system indefinitely in
  degraded without surfacing violates the fourth lens.
- **Client UUIDs idempotent.** The drain worker passes back the same
  UUID it staged with; Graphiti's add_episode deduplicates on UUID
  if seen before.
- **OTel via ``trace.get_tracer(...)`` only** per the A1 correction.
  No ``TracerProvider`` construction here.
- **Unit-testable without a live sidecar.** Probe target is a callable
  injected at construction.

Error-code range reserved: -32090..-32099 (-32090 and -32091 claimed
by first_run_scaffold; -32092..-32099 available).

    -32092  memory_unreachable        (escalated after bounded retries)
    -32093  memory_corrupt            (canary-query shape mismatch)
    -32094  supervisor_lost_quorum    (orchestrator self-probe failed)
    -32095  (staging_overflow — already claimed by staging.py)
    -32096  (drain_poison — already claimed by drain.py)
    -32097  reserved
    -32098  reserved
    -32099  hands_off_lifecycle_internal
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Iterable

from opentelemetry import trace


_TRACER = trace.get_tracer("pos.hands_off_lifecycle", "0.1.0")

_LOGGER = logging.getLogger(__name__)


# ---- error codes reserved to this component --------------------------


ERR_MEMORY_UNREACHABLE = -32092
ERR_MEMORY_CORRUPT = -32093
ERR_SUPERVISOR_LOST_QUORUM = -32094
ERR_HOL_INTERNAL = -32099


# ---- state machine ---------------------------------------------------


class SupervisorState(str, Enum):
    normal = "normal"
    degraded = "degraded"
    recovering = "recovering"
    escalated = "escalated"


class EscalationClass(str, Enum):
    memory_unreachable = "memory.sidecar.unreachable"
    memory_hanging = "memory.sidecar.hanging"
    memory_server_error = "memory.sidecar.server_error"
    memory_corrupt = "memory.sidecar.corrupt"
    memory_restart_storm = "memory.sidecar.restart_storm"
    drain_poison_accumulation = "memory.drain.poison_accumulation"
    drain_reconcile_drift = "memory.drain.reconcile_drift"


# ---- probe result ----------------------------------------------------


@dataclass(frozen=True)
class ProbeResult:
    ok: bool
    latency_ms: float = 0.0
    status_code: int | None = None
    error_class: str | None = None  # one of: refused, timeout, 5xx, corrupt

    @property
    def escalation_class(self) -> EscalationClass:
        """Classify the probe result into an escalation class."""
        if self.error_class == "timeout":
            return EscalationClass.memory_hanging
        if self.error_class == "5xx":
            return EscalationClass.memory_server_error
        if self.error_class == "corrupt":
            return EscalationClass.memory_corrupt
        return EscalationClass.memory_unreachable


ProbeFn = Callable[[], Awaitable[ProbeResult]]


# ---- escalation record ----------------------------------------------


@dataclass
class EscalationRecord:
    """Amendment #19 adds the optional ``notification_failures`` field
    (site 7) — a counter of per-escalation notifier failures surfaced
    via the ``supervisor.notify_failed`` span. Default 0; backwards-
    compatible additive extension."""

    id: str
    cls: EscalationClass
    opened_at: str  # ISO 8601
    notifications_sent: int = 0
    last_notified_at: str | None = None
    resolved_at: str | None = None
    notification_failures: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "class": self.cls.value,
            "opened_at": self.opened_at,
            "notifications_sent": self.notifications_sent,
            "last_notified_at": self.last_notified_at,
            "resolved_at": self.resolved_at,
            "notification_failures": self.notification_failures,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "EscalationRecord":
        return cls(
            id=str(d["id"]),
            cls=EscalationClass(d["class"]),
            opened_at=str(d["opened_at"]),
            notifications_sent=int(d.get("notifications_sent", 0) or 0),
            last_notified_at=d.get("last_notified_at"),
            resolved_at=d.get("resolved_at"),
            notification_failures=int(
                d.get("notification_failures", 0) or 0
            ),
        )


# ---- notification contract ------------------------------------------


NotificationFn = Callable[[EscalationClass, str, dict[str, Any]], Awaitable[None]]


# ---- supervisor config ----------------------------------------------


@dataclass(frozen=True)
class SupervisorConfig:
    """Loaded from ``~/.loam/memory.yaml`` + ``~/.loam/memory-staging.yaml``
    per H7. Defaults match research §Q2."""

    poll_interval_s: float = 30.0
    transient_threshold: int = 2  # failures before declaring degraded
    recovery_probe_interval_s: float = 2.0
    recovery_success_threshold: int = 2  # probes to reach 'normal'
    escalation_retry_limit: int = 3  # unhealed retries → 'escalated'
    latency_threshold_ms: float = 500.0
    escalation_state_path: str = "~/.loam/supervisor-escalation.json"
    attention_path: str = "~/.loam/attention.md"
    tier1_cap_override: bool = True  # Q5 ruling


# ---- transition record ----------------------------------------------


@dataclass(frozen=True)
class SupervisorTransition:
    from_state: SupervisorState
    to_state: SupervisorState
    trigger: str
    at: float


# ---- the supervisor --------------------------------------------------


class MemorySupervisor:
    """State machine + probe loop + escalation coordinator.

    Drain coordination is external: the supervisor calls the supplied
    ``on_recovering`` / ``on_normal`` callables on state transition;
    the caller hooks the drain worker into those.
    """

    def __init__(
        self,
        *,
        probe: ProbeFn,
        config: SupervisorConfig | None = None,
        notify: NotificationFn | None = None,
        on_transition: Callable[[SupervisorTransition], Awaitable[None]] | None = None,
        on_recovering: Callable[[], Awaitable[None]] | None = None,
        on_normal: Callable[[], Awaitable[None]] | None = None,
        clock: Callable[[], float] | None = None,
        escalation_state_path: str | Path | None = None,
        attention_path: str | Path | None = None,
    ) -> None:
        self._probe = probe
        self._cfg = config or SupervisorConfig()
        self._notify = notify
        self._on_transition = on_transition
        self._on_recovering = on_recovering
        self._on_normal = on_normal
        self._clock = clock or time.monotonic
        self._state = SupervisorState.normal
        self._state_entered_at = self._clock()
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._retries_since_first_failure = 0
        self._current_escalation: EscalationRecord | None = None
        self._escalation_path = Path(
            escalation_state_path or self._cfg.escalation_state_path
        ).expanduser()
        self._attention_path = Path(
            attention_path or self._cfg.attention_path
        ).expanduser()
        self._lock = asyncio.Lock()
        self._probe_task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()
        self._transitions: list[SupervisorTransition] = []
        self._load_persisted_escalation()

    # ---- introspection ---------------------------------------------

    @property
    def state(self) -> SupervisorState:
        return self._state

    @property
    def current_escalation(self) -> EscalationRecord | None:
        return self._current_escalation

    @property
    def transitions(self) -> list[SupervisorTransition]:
        return list(self._transitions)

    @property
    def config(self) -> SupervisorConfig:
        return self._cfg

    # ---- lifecycle -------------------------------------------------

    async def start(self) -> None:
        """Start the probe loop in the background."""
        if self._probe_task is not None:
            return
        self._probe_task = asyncio.create_task(
            self._loop(), name="memory-supervisor-loop"
        )

    async def stop(self) -> None:
        self._stop.set()
        if self._probe_task is not None:
            self._probe_task.cancel()
            try:
                await self._probe_task
            except asyncio.CancelledError:
                # Expected flow on cancel — bare pass per tightened CDC 2.
                pass
            except Exception:
                # Amendment #26 — teardown CDC 2: surface exception to
                # observability. No component-owned span open at this
                # site; logger.debug is the tightened-CDC fallback.
                _LOGGER.debug(
                    "supervisor_stop_probe_task_failed", exc_info=True
                )
            self._probe_task = None

    async def _loop(self) -> None:
        try:
            while not self._stop.is_set():
                await self.tick()
                # State-dependent cadence.
                if self._state == SupervisorState.recovering:
                    interval = self._cfg.recovery_probe_interval_s
                else:
                    interval = self._cfg.poll_interval_s
                try:
                    await asyncio.wait_for(self._stop.wait(), timeout=interval)
                except asyncio.TimeoutError:
                    pass
        except asyncio.CancelledError:
            return

    # ---- probe tick (the state machine) ----------------------------

    async def tick(self) -> SupervisorTransition | None:
        """Run one probe and update state. Returns the transition, if
        any. Callable directly from tests — no wall-clock awaits."""
        async with self._lock:
            with _TRACER.start_as_current_span(
                "pos.hands_off_lifecycle.supervisor.probe"
            ) as span:
                try:
                    result = await self._probe()
                except Exception as e:
                    result = ProbeResult(
                        ok=False, error_class="refused", latency_ms=0.0
                    )
                    span.set_attribute("probe.exception", type(e).__name__)
                span.set_attribute("probe.ok", result.ok)
                span.set_attribute("probe.latency_ms", float(result.latency_ms))
                if result.error_class:
                    span.set_attribute("probe.error_class", result.error_class)
            if result.ok:
                return await self._on_ok(result)
            return await self._on_fail(result)

    async def _on_ok(self, result: ProbeResult) -> SupervisorTransition | None:
        self._consecutive_failures = 0
        if self._state == SupervisorState.normal:
            return None
        if self._state in (SupervisorState.degraded, SupervisorState.escalated):
            # First good probe after bad — enter recovering.
            t = self._transition(
                SupervisorState.recovering, "probe_recovered"
            )
            self._consecutive_successes = 1
            if self._on_recovering is not None:
                await self._on_recovering()
            return t
        # SupervisorState.recovering
        self._consecutive_successes += 1
        if self._consecutive_successes >= self._cfg.recovery_success_threshold:
            t = self._transition(
                SupervisorState.normal, "recovery_confirmed"
            )
            self._retries_since_first_failure = 0
            await self._close_escalation("recovered")
            if self._on_normal is not None:
                await self._on_normal()
            return t
        return None

    async def _on_fail(
        self, result: ProbeResult
    ) -> SupervisorTransition | None:
        self._consecutive_successes = 0
        self._consecutive_failures += 1
        self._retries_since_first_failure += 1
        if self._state == SupervisorState.normal:
            if self._consecutive_failures >= self._cfg.transient_threshold:
                return self._transition(
                    SupervisorState.degraded,
                    f"trip:{result.error_class or 'unknown'}",
                )
            return None
        if self._state == SupervisorState.degraded:
            # Count retries until escalation threshold.
            if (
                self._retries_since_first_failure
                >= self._cfg.escalation_retry_limit
            ):
                t = self._transition(
                    SupervisorState.escalated,
                    f"escalation_retry_limit:{result.error_class}",
                )
                await self._open_escalation(
                    result.escalation_class,
                    {
                        "error_class": result.error_class,
                        "consecutive_failures": self._consecutive_failures,
                        "retries_since_first_failure": (
                            self._retries_since_first_failure
                        ),
                    },
                )
                return t
            return None
        if self._state == SupervisorState.recovering:
            # A failure during recovery drops back to degraded.
            self._consecutive_successes = 0
            return self._transition(
                SupervisorState.degraded, "recovery_aborted"
            )
        # SupervisorState.escalated — check whether the class changed.
        if self._current_escalation is not None:
            new_cls = result.escalation_class
            if new_cls != self._current_escalation.cls:
                # Class change → re-notify per H17.
                await self._open_escalation(new_cls, {"class_changed_from": self._current_escalation.cls.value})
        return None

    # ---- transitions ----------------------------------------------

    def _transition(
        self, to: SupervisorState, trigger: str
    ) -> SupervisorTransition:
        t = SupervisorTransition(
            from_state=self._state,
            to_state=to,
            trigger=trigger,
            at=self._clock(),
        )
        self._state = to
        self._state_entered_at = t.at
        self._transitions.append(t)
        with _TRACER.start_as_current_span(
            "pos.hands_off_lifecycle.supervisor.state_transition"
        ) as span:
            span.set_attribute("from_state", t.from_state.value)
            span.set_attribute("to_state", t.to_state.value)
            span.set_attribute("trigger", t.trigger)
        if self._on_transition is not None:
            asyncio.ensure_future(self._on_transition(t))
        return t

    # ---- escalation lifecycle -------------------------------------

    async def _open_escalation(
        self, cls: EscalationClass, attrs: dict[str, Any]
    ) -> None:
        """Open (or change class on) the current escalation. Notifies
        idempotently per-class — one notification per class per
        opening; a class change produces a second. Deduplication
        addresses the Tier-1 cap exceedance rule (Q5)."""
        import uuid
        from datetime import datetime, timezone

        now_iso = datetime.now(timezone.utc).isoformat()
        need_notify = True
        if self._current_escalation is not None:
            if self._current_escalation.cls == cls:
                need_notify = False  # same class, dedup
            else:
                # Class change — close old, open new
                await self._close_escalation("class_changed")
        if self._current_escalation is None:
            self._current_escalation = EscalationRecord(
                id=str(uuid.uuid4()), cls=cls, opened_at=now_iso
            )
        if need_notify and self._notify is not None:
            text = self._render_alert(cls, attrs)
            try:
                await self._notify(cls, text, attrs)
                self._current_escalation.notifications_sent += 1
                self._current_escalation.last_notified_at = now_iso
            except Exception as e:
                # Amendment #19 (site 7): loop-safety invariant —
                # never kill the probe loop on notifier failure — is
                # preserved. The observable surface is the span below
                # plus the notification_failures counter on the
                # persisted record. Operators can now see "escalation
                # opened but notification failed N times" rather than
                # the prior silent drop.
                if self._current_escalation is not None:
                    self._current_escalation.notification_failures += 1
                with _TRACER.start_as_current_span(
                    "pos.hands_off_lifecycle.supervisor.notify_failed"
                ) as fail_span:
                    fail_span.set_attribute("escalation.class", cls.value)
                    fail_span.set_attribute(
                        "exception.class", type(e).__name__
                    )
                    fail_span.set_attribute("phase", "open")
        self._persist_escalation()
        self._write_attention(self._render_alert(cls, attrs))
        with _TRACER.start_as_current_span(
            "pos.hands_off_lifecycle.supervisor.escalation_opened"
        ) as span:
            span.set_attribute("escalation.class", cls.value)
            if self._current_escalation is not None:
                span.set_attribute(
                    "escalation.id", self._current_escalation.id
                )

    async def _close_escalation(self, reason: str) -> None:
        if self._current_escalation is None:
            return
        from datetime import datetime, timezone

        prior_cls = self._current_escalation.cls
        self._current_escalation.resolved_at = datetime.now(
            timezone.utc
        ).isoformat()
        text = self._render_resolved(prior_cls, reason)
        if self._notify is not None:
            try:
                await self._notify(prior_cls, text, {"reason": reason})
            except Exception as e:
                # Amendment #19 (site 8): local-state invariant —
                # _current_escalation is cleared + attention file
                # removed even if the "resolved" notification failed
                # to send — is preserved (those side-effects live
                # outside this try-block). The observable surface is
                # the span below; operators see the close-path notify
                # failure without the user-visible state being
                # corrupted.
                with _TRACER.start_as_current_span(
                    "pos.hands_off_lifecycle.supervisor.notify_failed"
                ) as fail_span:
                    fail_span.set_attribute(
                        "escalation.class", prior_cls.value
                    )
                    fail_span.set_attribute(
                        "exception.class", type(e).__name__
                    )
                    fail_span.set_attribute("close_reason", reason)
                    fail_span.set_attribute("phase", "close")
        with _TRACER.start_as_current_span(
            "pos.hands_off_lifecycle.supervisor.escalation_closed"
        ) as span:
            span.set_attribute("escalation.class", prior_cls.value)
            span.set_attribute("reason", reason)
        self._current_escalation = None
        self._persist_escalation()
        self._clear_attention()

    # ---- persistence (H9 crash recovery) --------------------------

    def _persist_escalation(self) -> None:
        try:
            self._escalation_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "current": (
                    self._current_escalation.to_dict()
                    if self._current_escalation
                    else None
                ),
                "state": self._state.value,
            }
            self._escalation_path.write_text(
                json.dumps(payload, indent=2, sort_keys=True)
            )
        except Exception:
            pass

    def _load_persisted_escalation(self) -> None:
        if not self._escalation_path.exists():
            return
        try:
            data = json.loads(self._escalation_path.read_text())
            cur = data.get("current")
            if cur:
                self._current_escalation = EscalationRecord.from_dict(cur)
            stored_state = data.get("state")
            if stored_state:
                try:
                    self._state = SupervisorState(stored_state)
                except ValueError:
                    pass
        except Exception:
            pass

    def _write_attention(self, text: str) -> None:
        try:
            self._attention_path.parent.mkdir(parents=True, exist_ok=True)
            self._attention_path.write_text(text)
        except Exception:
            pass

    def _clear_attention(self) -> None:
        try:
            if self._attention_path.exists():
                self._attention_path.unlink()
        except Exception:
            pass

    # ---- message rendering ----------------------------------------

    def _render_alert(
        self, cls: EscalationClass, attrs: dict[str, Any]
    ) -> str:
        # Plain-language alert per research §Q7 shape.
        return (
            "pOS v2 needs attention.\n"
            f"What failed: {cls.value}.\n"
            f"What was tried: bounded retries up to "
            f"{self._cfg.escalation_retry_limit}; last error "
            f"class={attrs.get('error_class','?')}.\n"
            "Current state: memory writes staged; normal operation "
            "partially paused.\n"
            "What you can do now: check the sidecar log at "
            "memory-system/data/graphiti-service.err.log; run `pos "
            "memory doctor` for a diagnostic dump.\n"
            "Updates will not repeat until the state clears or "
            "changes class."
        )

    def _render_resolved(
        self, cls: EscalationClass, reason: str
    ) -> str:
        return (
            f"[pOS] {cls.value} resolved ({reason}); normal operation "
            "resumed."
        )

    # ---- test hooks -----------------------------------------------

    def force_state(self, state: SupervisorState) -> None:
        """Test helper — set state without going through tick()."""
        self._state = state
        self._state_entered_at = self._clock()
