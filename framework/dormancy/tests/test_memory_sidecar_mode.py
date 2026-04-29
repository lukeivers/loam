"""Memory-sidecar failure mode tests (Amendment 3 — hands-off-lifecycle).

Covers the supervisor-signal consumption path that closes the memory
detection blind spot documented in architecture.md. Maps to H-criteria
H6 (supervisor → degradation transition), H7 (config-driven), and the
cross-cutting H19/H20 regression safety.

The Claude-adapter detection path remains unchanged and untouched by
this amendment — tests for it live in the existing test files.
"""

from __future__ import annotations

import pytest

from loam.dormancy.config import DegradationConfig
from loam.dormancy.detection import DegradationDetector
from loam.dormancy.errors import DegradationSignal
from loam.dormancy.fsm import DegradationMode, FSMState


@pytest.mark.asyncio
async def test_memory_sidecar_mode_exists_in_fsm_registry() -> None:
    cfg = DegradationConfig()
    det = DegradationDetector.from_config(cfg)
    assert DegradationMode.memory_sidecar in det.fsms


@pytest.mark.asyncio
async def test_supervisor_down_signal_trips_memory_sidecar_mode() -> None:
    cfg = DegradationConfig()
    det = DegradationDetector.from_config(cfg)
    t = await det.record_supervisor_signal(
        signal=DegradationSignal.memory_sidecar_down
    )
    assert t is not None
    assert t.mode is DegradationMode.memory_sidecar
    assert t.to_state is FSMState.open
    # The other modes must be unaffected.
    for mode, fsm in det.fsms.items():
        if mode is DegradationMode.memory_sidecar:
            assert fsm.state is FSMState.open
        else:
            assert fsm.state is FSMState.closed


@pytest.mark.asyncio
async def test_recovery_signal_closes_memory_sidecar_mode() -> None:
    cfg = DegradationConfig()
    det = DegradationDetector.from_config(cfg)
    # Trip it, then recover.
    await det.record_supervisor_signal(
        signal=DegradationSignal.memory_sidecar_down
    )
    fsm = det.fsms[DegradationMode.memory_sidecar]
    assert fsm.state is FSMState.open
    # Force half_open (would normally happen after dwell) so the
    # recovery signal can close it.
    fsm.state = FSMState.half_open
    t = await det.record_supervisor_signal(
        signal=DegradationSignal.memory_sidecar_recovered
    )
    assert t is not None
    assert t.to_state is FSMState.closed


@pytest.mark.asyncio
async def test_adapter_path_untouched_by_memory_sidecar_amendment() -> None:
    """Regression guard: the Claude-adapter path continues to work.

    A failure event with a connection_error signal must still trip the
    `down` mode; it MUST NOT trip the new memory_sidecar mode (whose
    accepted_signals are memory_sidecar_down only).
    """
    from loam.dormancy.adapter import AdapterEvent

    cfg = DegradationConfig()
    det = DegradationDetector.from_config(cfg)
    # Three connection-error events should trip `down` (threshold 3
    # failures in 60s, per default config).
    for i in range(3):
        await det.record_event(
            AdapterEvent(
                call_id=f"c{i}",
                prompt_name="p",
                model="m",
                ok=False,
                signal=DegradationSignal.connection_error,
                retry_after=None,
                latency_seconds=0.1,
                status_code=None,
                timestamp=float(i),
            )
        )
    assert det.fsms[DegradationMode.down].state is FSMState.open
    # memory_sidecar untouched.
    assert det.fsms[DegradationMode.memory_sidecar].state is FSMState.closed


@pytest.mark.asyncio
async def test_supervisor_signal_invokes_on_transition_callback() -> None:
    """Integration with the downstream notification layer: on_transition
    fires so graceful-degradation's component layer can act."""
    fired: list[str] = []

    async def on_transition(t) -> None:
        fired.append(t.to_state.value)

    cfg = DegradationConfig()
    det = DegradationDetector.from_config(cfg, on_transition=on_transition)
    await det.record_supervisor_signal(
        signal=DegradationSignal.memory_sidecar_down
    )
    assert "open" in fired


@pytest.mark.asyncio
async def test_non_memory_signal_ignored_by_supervisor_path() -> None:
    """Defensive: record_supervisor_signal ignores non-memory signals."""
    cfg = DegradationConfig()
    det = DegradationDetector.from_config(cfg)
    t = await det.record_supervisor_signal(
        signal=DegradationSignal.connection_error
    )
    assert t is None
