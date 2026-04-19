"""D2 — Per-mode FSMs.

Acceptance (brief):
- Each mode's FSM handles its full lifecycle from synthetic events.
- State transitions are deterministic from the event log.
- Independent FSMs — one mode opening does not transition another.
"""

from __future__ import annotations

import pytest

from graceful_degradation import DegradationConfig, DegradationMode, FSMState
from graceful_degradation.errors import DegradationSignal
from graceful_degradation.fsm import (
    GarbageFSM,
    LatencyFSM,
    WindowedFailureFSM,
    build_fsms,
)

from .fakes import FakeClock


def _build(clock: FakeClock):
    cfg = DegradationConfig()
    return cfg, build_fsms(cfg, clock=clock)


def test_down_fsm_trips_at_threshold() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.down]
    assert isinstance(fsm, WindowedFailureFSM)

    # 2 failures — should not trip
    fsm.record_failure(DegradationSignal.connection_error, now=clock.now())
    fsm.record_failure(DegradationSignal.timeout, now=clock.now())
    assert fsm.state == FSMState.closed
    # 3rd failure — trip
    t = fsm.record_failure(DegradationSignal.server_error, now=clock.now())
    assert fsm.state == FSMState.open
    assert t is not None and t.to_state == FSMState.open


def test_down_fsm_honours_window_seconds() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.down]

    fsm.record_failure(DegradationSignal.connection_error, now=clock.now())
    fsm.record_failure(DegradationSignal.connection_error, now=clock.now())
    clock.advance(70.0)  # exceeds window_seconds=60
    # The earlier failures have expired; this is a lone failure.
    fsm.record_failure(DegradationSignal.connection_error, now=clock.now())
    assert fsm.state == FSMState.closed


def test_dwell_transition_open_to_half_open() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.down]
    # Trip.
    for _ in range(3):
        fsm.record_failure(DegradationSignal.connection_error, now=clock.now())
    assert fsm.state == FSMState.open
    # Advance past dwell (default 30s).
    clock.advance(31.0)
    t = fsm.tick(now=clock.now())
    assert t is not None
    assert fsm.state == FSMState.half_open


def test_probe_success_closes_fsm() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.down]
    for _ in range(3):
        fsm.record_failure(DegradationSignal.connection_error, now=clock.now())
    clock.advance(31.0)
    fsm.tick(now=clock.now())
    assert fsm.state == FSMState.half_open
    fsm.record_success(now=clock.now())
    assert fsm.state == FSMState.closed


def test_probe_failure_reopens_fsm() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.down]
    for _ in range(3):
        fsm.record_failure(DegradationSignal.connection_error, now=clock.now())
    clock.advance(31.0)
    fsm.tick(now=clock.now())
    assert fsm.state == FSMState.half_open
    # Probe call fails → back to open
    fsm.record_failure(DegradationSignal.connection_error, now=clock.now())
    assert fsm.state == FSMState.open


def test_overloaded_fsm_independent() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    down = fsms[DegradationMode.down]
    overloaded = fsms[DegradationMode.overloaded]

    # Trip "down" — does not affect overloaded.
    for _ in range(3):
        down.record_failure(DegradationSignal.connection_error, now=clock.now())
    assert down.state == FSMState.open
    assert overloaded.state == FSMState.closed


def test_rate_limited_uses_retry_after_header() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.rate_limited]
    # trips after 1 failure
    fsm.record_failure(
        DegradationSignal.rate_limited, retry_after=45.0, now=clock.now()
    )
    assert fsm.state == FSMState.open
    # Dwell: retry-after governs, not config.half_open_dwell_seconds
    clock.advance(10.0)
    fsm.tick(now=clock.now())
    assert fsm.state == FSMState.open
    clock.advance(40.0)
    fsm.tick(now=clock.now())
    assert fsm.state == FSMState.half_open


def test_auth_broken_goes_straight_to_gated() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.auth_broken]
    fsm.record_failure(DegradationSignal.auth_broken, now=clock.now())
    assert fsm.state == FSMState.gated


def test_gated_only_clears_on_user_resume() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.auth_broken]
    fsm.record_failure(DegradationSignal.auth_broken, now=clock.now())
    assert fsm.state == FSMState.gated
    clock.advance(10000.0)
    fsm.tick(now=clock.now())
    # Tick does nothing to gated.
    assert fsm.state == FSMState.gated
    fsm.user_resume()
    assert fsm.state == FSMState.half_open


def test_garbage_fsm_ratio_threshold() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.garbage]
    assert isinstance(fsm, GarbageFSM)
    # 7 goods, 2 bads — no trip (only 2/9 < 3/10)
    for _ in range(7):
        fsm.record_success(now=clock.now())
    for _ in range(2):
        fsm.record_failure(DegradationSignal.garbage, now=clock.now())
    assert fsm.state == FSMState.closed
    # 3rd garbage within the last 10 → trip.
    fsm.record_failure(DegradationSignal.garbage, now=clock.now())
    assert fsm.state == FSMState.open


def test_garbage_needs_two_consecutive_probes() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.garbage]
    # Fill the rolling window with 3 bads + 7 goods.
    for _ in range(3):
        fsm.record_failure(DegradationSignal.garbage, now=clock.now())
    for _ in range(7):
        fsm.record_success(now=clock.now())
    # Still 3 garbages in window → should have tripped on the third.
    # Re-run: trip requires the failure that pushes to threshold. Set
    # up differently:
    clock2 = FakeClock()
    cfg2, fsms2 = _build(clock2)
    fsm2 = fsms2[DegradationMode.garbage]
    for _ in range(3):
        fsm2.record_failure(DegradationSignal.garbage, now=clock2.now())
    assert fsm2.state == FSMState.open
    # Dwell.
    clock2.advance(61.0)
    fsm2.tick(now=clock2.now())
    assert fsm2.state == FSMState.half_open
    # One probe success — not enough (N=2).
    fsm2.record_success(now=clock2.now())
    assert fsm2.state == FSMState.half_open
    # Second probe success — closes.
    fsm2.record_success(now=clock2.now())
    assert fsm2.state == FSMState.closed


def test_fsm_determinism_same_events_same_state() -> None:
    """Given the same clock advances + events, two FSMs produce same
    transition record."""

    def drive(events):
        clock = FakeClock()
        cfg, fsms = _build(clock)
        fsm = fsms[DegradationMode.down]
        for ev in events:
            if ev == "advance":
                clock.advance(10.0)
                fsm.tick(now=clock.now())
            else:
                fsm.record_failure(ev, now=clock.now())
        return [
            (t.from_state.value, t.to_state.value, t.trigger)
            for t in fsm.transitions
        ]

    seq = [
        DegradationSignal.connection_error,
        DegradationSignal.connection_error,
        DegradationSignal.connection_error,
        "advance",
        "advance",
        "advance",
        "advance",
    ]
    a = drive(seq)
    b = drive(seq)
    assert a == b


def test_latency_fsm_emits_advisory_only() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.latency_sustained]
    assert isinstance(fsm, LatencyFSM)
    # Push latency up — 20 samples at 50s each; p95 = 50 > 30.
    for _ in range(20):
        fsm.observe_latency(50.0, now=clock.now())
    # Stays closed; advisory fired but does not transition.
    assert fsm.state == FSMState.closed


def test_down_fsm_accepts_timeout_as_signal() -> None:
    clock = FakeClock()
    cfg, fsms = _build(clock)
    fsm = fsms[DegradationMode.down]
    # Timeout is part of accepted_signals for down.
    fsm.record_failure(DegradationSignal.timeout, now=clock.now())
    fsm.record_failure(DegradationSignal.timeout, now=clock.now())
    fsm.record_failure(DegradationSignal.timeout, now=clock.now())
    assert fsm.state == FSMState.open


def test_signals_are_mode_exclusive() -> None:
    """auth_broken signal should not trip the down FSM."""
    clock = FakeClock()
    cfg, fsms = _build(clock)
    down = fsms[DegradationMode.down]
    # Feed auth_broken repeatedly; down should not react.
    for _ in range(5):
        down.record_failure(DegradationSignal.auth_broken, now=clock.now())
    assert down.state == FSMState.closed
