"""Per-mode finite-state machines (D2).

Six modes, each a four-state FSM:

    closed       — normal operation
    open         — tripped; pause policy has been dispatched
    half_open    — dwell timer has expired; awaiting probe result
    gated        — terminal-until-user (auth_broken or long-dwell) —
                   never transitions to `closed` without a user resume
                   event

Transitions are driven exclusively by `record_event()` (adapter signal)
and `tick(now)` (clock-driven dwell expiry). Given the same event
sequence and clock, state is deterministic.

The FSMs are independent — one mode opening does NOT side-effect
another. Each carries its own counters and dwell state.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Deque

from . import observability as obs
from .config import (
    BinaryModeConfig,
    GarbageModeConfig,
    LatencyModeConfig,
)
from .errors import DegradationSignal


# ---- public enums ------------------------------------------------------


class FSMState(str, Enum):
    closed = "closed"
    open = "open"
    half_open = "half_open"
    gated = "gated"  # auth-broken / long-dwell; user must release


class DegradationMode(str, Enum):
    """The seven tracked modes. Names match the config keys verbatim.

    ``memory_sidecar`` is added by Amendment 3 of hands-off-lifecycle
    to close the memory-system detection blind spot documented in
    architecture.md. It is driven by the supervisor's probe loop, not
    by the Claude-adapter event stream, via
    :meth:`DegradationDetector.record_supervisor_signal`.
    """

    down = "down"
    overloaded = "overloaded"
    rate_limited = "rate_limited"
    garbage = "garbage"
    auth_broken = "auth_broken"
    latency_sustained = "latency_sustained"
    memory_sidecar = "memory_sidecar"


# ---- transition record -------------------------------------------------


@dataclass(frozen=True)
class FSMTransition:
    mode: DegradationMode
    from_state: FSMState
    to_state: FSMState
    trigger: str
    at: float  # clock() value when transition fired


# ---- base FSM ----------------------------------------------------------


@dataclass
class ModeFSM:
    """Base FSM for one mode.

    Subclasses override:
      - `accepted_signals` — which DegradationSignal values are fed here
      - `should_trip(now)` — predicate on counters
      - `on_success(now)` — called when adapter reports a success for
        this mode (reset counters)
      - `_dwell_expired(now)` — when to leave `open` for `half_open`

    The `clock` callable is injected for time-compressed simulation.
    """

    mode: DegradationMode
    clock: Callable[[], float] = field(default=time.monotonic)
    state: FSMState = FSMState.closed
    state_entered_at: float = 0.0
    retry_after_until: float | None = None  # for rate_limited
    consecutive_probe_successes: int = 0
    transitions: list[FSMTransition] = field(default_factory=list)

    # subclasses populate this (signals which feed this mode)
    accepted_signals: tuple[DegradationSignal, ...] = ()

    def __post_init__(self) -> None:
        self.state_entered_at = self.clock()

    # ---- public API ---------------------------------------------------

    def record_success(self, now: float | None = None) -> FSMTransition | None:
        """Adapter reported a success. If we're in half_open, count it
        toward the probe-success requirement; may transition to closed.
        If we're in closed, reset counters. Does nothing if open/gated."""
        t = self.clock() if now is None else now
        if self.state == FSMState.closed:
            self.on_success(t)
            return None
        if self.state == FSMState.half_open:
            self.consecutive_probe_successes += 1
            if self.consecutive_probe_successes >= self.probe_success_requirement:
                return self._transition(FSMState.closed, "probe_succeeded")
            return None
        # open / gated — a passive success during open is rare (new calls
        # are usually paused); treat as noise.
        return None

    def record_failure(
        self, signal: DegradationSignal, *, retry_after: float | None = None, now: float | None = None
    ) -> FSMTransition | None:
        """Adapter reported a failure whose signal maps to this mode.
        May trip the FSM (closed → open) or invalidate a probe
        (half_open → open)."""
        if signal not in self.accepted_signals:
            return None
        t = self.clock() if now is None else now
        self.on_failure(signal, retry_after=retry_after, now=t)
        if self.state == FSMState.closed and self.should_trip(t):
            return self._trip(signal)
        if self.state == FSMState.half_open:
            # A failure in half_open invalidates the probe — re-open.
            return self._transition(FSMState.open, f"probe_failed:{signal.value}")
        return None

    def tick(self, now: float | None = None) -> FSMTransition | None:
        """Clock-driven transition. Called periodically; moves open →
        half_open when the dwell has expired."""
        t = self.clock() if now is None else now
        if self.state == FSMState.open and self._dwell_expired(t):
            return self._transition(FSMState.half_open, "dwell_expired")
        return None

    def force_gated(self, reason: str) -> FSMTransition | None:
        """Promote open / half_open → gated (long dwell, user-confirm
        required). Auth-broken goes straight to gated on trip."""
        if self.state in (FSMState.open, FSMState.half_open, FSMState.closed):
            return self._transition(FSMState.gated, reason)
        return None

    def user_resume(self) -> FSMTransition | None:
        """User explicitly confirmed resume (gated → half_open)."""
        if self.state == FSMState.gated:
            return self._transition(FSMState.half_open, "user_resume")
        return None

    # ---- subclass overrides -------------------------------------------

    def on_success(self, now: float) -> None:
        """Called when a passive success observed in closed."""
        pass

    def on_failure(
        self,
        signal: DegradationSignal,
        *,
        retry_after: float | None = None,
        now: float,
    ) -> None:
        """Called for every failure matching accepted_signals."""
        pass

    def should_trip(self, now: float) -> bool:
        return False

    def _dwell_expired(self, now: float) -> bool:
        raise NotImplementedError

    @property
    def probe_success_requirement(self) -> int:
        return 1

    # ---- internal -----------------------------------------------------

    def _trip(self, signal: DegradationSignal) -> FSMTransition:
        return self._transition(FSMState.open, f"trip:{signal.value}")

    def _transition(self, to: FSMState, trigger: str) -> FSMTransition:
        from_state = self.state
        self.state = to
        self.state_entered_at = self.clock()
        if to == FSMState.half_open:
            self.consecutive_probe_successes = 0
        t = FSMTransition(
            mode=self.mode,
            from_state=from_state,
            to_state=to,
            trigger=trigger,
            at=self.state_entered_at,
        )
        self.transitions.append(t)
        obs.fsm_transition(
            mode=self.mode.value,
            from_state=from_state.value,
            to_state=to.value,
            trigger=trigger,
        )
        return t


# ---- binary (count-in-window) modes ------------------------------------


@dataclass
class WindowedFailureFSM(ModeFSM):
    """For down / overloaded / rate_limited / auth_broken.

    Failures trip when `failures` hit in `window_seconds` (or once, with
    window_seconds effectively 0 — a single failure).

    Rate-limited honours `retry-after` for dwell. Auth-broken goes
    straight to gated (no auto-recovery).
    """

    cfg: BinaryModeConfig | None = None
    auto_gated_on_trip: bool = False  # True for auth_broken
    honour_retry_after_for_dwell: bool = False  # True for rate_limited
    _failures: Deque[float] = field(default_factory=deque)

    def on_success(self, now: float) -> None:
        self._failures.clear()

    def on_failure(
        self,
        signal: DegradationSignal,
        *,
        retry_after: float | None = None,
        now: float,
    ) -> None:
        # Drop expired failure timestamps from the left.
        assert self.cfg is not None
        horizon = now - self.cfg.trip_threshold.window_seconds
        while self._failures and self._failures[0] < horizon:
            self._failures.popleft()
        self._failures.append(now)
        if self.honour_retry_after_for_dwell and retry_after is not None:
            self.retry_after_until = now + retry_after

    def should_trip(self, now: float) -> bool:
        assert self.cfg is not None
        horizon = now - self.cfg.trip_threshold.window_seconds
        while self._failures and self._failures[0] < horizon:
            self._failures.popleft()
        return len(self._failures) >= self.cfg.trip_threshold.failures

    def _trip(self, signal: DegradationSignal) -> FSMTransition:
        if self.auto_gated_on_trip:
            t = self._transition(FSMState.gated, f"trip:{signal.value}")
        else:
            t = self._transition(FSMState.open, f"trip:{signal.value}")
        return t

    def _dwell_expired(self, now: float) -> bool:
        assert self.cfg is not None
        if self.state != FSMState.open:
            return False
        if self.retry_after_until is not None:
            return now >= self.retry_after_until
        if self.cfg.half_open_dwell_seconds is None:
            return False  # no auto-dwell (e.g. rate_limited w/o retry-after)
        return (now - self.state_entered_at) >= self.cfg.half_open_dwell_seconds

    @property
    def probe_success_requirement(self) -> int:
        return self.cfg.probe_success_requirement if self.cfg else 1


# ---- garbage FSM -------------------------------------------------------


@dataclass
class GarbageFSM(ModeFSM):
    """3-of-10 rolling ratio mode.

    `record_success` / `record_failure(garbage)` each append to the
    rolling deque; trip when the count of garbage within the last
    `window_calls` exceeds `failures`.
    """

    cfg: GarbageModeConfig | None = None
    _rolling: Deque[bool] = field(default_factory=deque)

    def on_success(self, now: float) -> None:
        assert self.cfg is not None
        self._rolling.append(False)
        while len(self._rolling) > self.cfg.trip_threshold.window_calls:
            self._rolling.popleft()

    def on_failure(
        self,
        signal: DegradationSignal,
        *,
        retry_after: float | None = None,
        now: float,
    ) -> None:
        assert self.cfg is not None
        self._rolling.append(True)
        while len(self._rolling) > self.cfg.trip_threshold.window_calls:
            self._rolling.popleft()

    def should_trip(self, now: float) -> bool:
        assert self.cfg is not None
        count = sum(1 for v in self._rolling if v)
        return count >= self.cfg.trip_threshold.failures

    def _dwell_expired(self, now: float) -> bool:
        assert self.cfg is not None
        return (now - self.state_entered_at) >= self.cfg.half_open_dwell_seconds

    @property
    def probe_success_requirement(self) -> int:
        return self.cfg.probe_success_requirement if self.cfg else 2


# ---- latency FSM (advisory only) ---------------------------------------


@dataclass
class LatencyFSM(ModeFSM):
    """Advisory-only: emits a signal when p95 > threshold in window.

    Does not trip to open; stays in closed but records a transition to
    closed->closed with trigger=advisory_fired so the episode layer can
    emit a signal. Implemented as a rolling window of observed
    latencies.
    """

    cfg: LatencyModeConfig | None = None
    _latencies: Deque[float] = field(default_factory=deque)
    _advised: bool = False

    def on_success(self, now: float) -> None:
        return None

    def observe_latency(self, seconds: float, *, now: float | None = None) -> FSMTransition | None:
        """Called by the detector for every adapter call (success or
        failure) with the latency value."""
        assert self.cfg is not None
        t = self.clock() if now is None else now
        self._latencies.append(seconds)
        while len(self._latencies) > self.cfg.trip_threshold.window_calls:
            self._latencies.popleft()
        if len(self._latencies) < self.cfg.trip_threshold.window_calls:
            return None
        # p95
        arr = sorted(self._latencies)
        idx = min(int(0.95 * len(arr)), len(arr) - 1)
        p95 = arr[idx]
        if p95 >= self.cfg.trip_threshold.p95_seconds and not self._advised:
            self._advised = True
            # Record a "latency advisory" marker; do not change state.
            obs.fsm_transition(
                mode=self.mode.value,
                from_state=self.state.value,
                to_state=self.state.value,
                trigger="latency_advisory",
                p95_seconds=p95,
            )
            return FSMTransition(
                mode=self.mode,
                from_state=self.state,
                to_state=self.state,
                trigger="latency_advisory",
                at=t,
            )
        if p95 < self.cfg.trip_threshold.p95_seconds:
            self._advised = False
        return None

    def should_trip(self, now: float) -> bool:
        return False

    def _dwell_expired(self, now: float) -> bool:
        return False


# ---- factory -----------------------------------------------------------


def build_fsms(
    cfg: Any,  # DegradationConfig
    *,
    clock: Callable[[], float] | None = None,
) -> dict[DegradationMode, ModeFSM]:
    """Construct the six FSMs from a DegradationConfig."""
    clk = clock or time.monotonic
    return {
        DegradationMode.down: WindowedFailureFSM(
            mode=DegradationMode.down,
            clock=clk,
            cfg=cfg.modes.down,
            accepted_signals=(
                DegradationSignal.connection_error,
                DegradationSignal.timeout,
                DegradationSignal.server_error,
            ),
        ),
        DegradationMode.overloaded: WindowedFailureFSM(
            mode=DegradationMode.overloaded,
            clock=clk,
            cfg=cfg.modes.overloaded,
            accepted_signals=(DegradationSignal.overloaded,),
        ),
        DegradationMode.rate_limited: WindowedFailureFSM(
            mode=DegradationMode.rate_limited,
            clock=clk,
            cfg=cfg.modes.rate_limited,
            accepted_signals=(DegradationSignal.rate_limited,),
            honour_retry_after_for_dwell=True,
        ),
        DegradationMode.garbage: GarbageFSM(
            mode=DegradationMode.garbage,
            clock=clk,
            cfg=cfg.modes.garbage,
            accepted_signals=(DegradationSignal.garbage,),
        ),
        DegradationMode.auth_broken: WindowedFailureFSM(
            mode=DegradationMode.auth_broken,
            clock=clk,
            cfg=cfg.modes.auth_broken,
            accepted_signals=(DegradationSignal.auth_broken,),
            auto_gated_on_trip=True,
        ),
        DegradationMode.latency_sustained: LatencyFSM(
            mode=DegradationMode.latency_sustained,
            clock=clk,
            cfg=cfg.modes.latency_sustained,
            accepted_signals=(DegradationSignal.latency_high,),
        ),
        DegradationMode.memory_sidecar: WindowedFailureFSM(
            mode=DegradationMode.memory_sidecar,
            clock=clk,
            cfg=cfg.modes.memory_sidecar,
            accepted_signals=(DegradationSignal.memory_sidecar_down,),
        ),
    }
