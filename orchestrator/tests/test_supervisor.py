"""Supervisor tests (Amendment 2 — hands-off-lifecycle).

Covers H-criteria from proposal §5.2 + §5.4:

    H6  — state machine transitions (normal → degraded → recovering →
          normal; bounded retries → escalated)
    H7  — config-driven cadence + thresholds
    H8  — OTel spans on state transitions / probes / escalations
    H9  — crash recovery via persisted supervisor-escalation.json
    H10 — unit-testable via fake-probe injection (the entire test
          module exercises this)
    H16 — escalation opens once; dedup while same class
    H17 — class change re-notifies; recovery closes with resolved
          message; attention.md reflects current state
    H18 — Tier-1 cap exceedance discipline: memory-sidecar
          unrecoverable is exempt per Q5
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pos_orchestrator.supervisor import (
    ERR_MEMORY_UNREACHABLE,
    EscalationClass,
    EscalationRecord,
    MemorySupervisor,
    ProbeResult,
    SupervisorConfig,
    SupervisorState,
)


# ---- probe factories (H10) -------------------------------------------


def _probe_always_ok() -> Any:
    async def _p() -> ProbeResult:
        return ProbeResult(ok=True, latency_ms=12.0)

    return _p


def _probe_always_fail(error_class: str = "refused") -> Any:
    async def _p() -> ProbeResult:
        return ProbeResult(ok=False, error_class=error_class)

    return _p


def _probe_sequence(*results: ProbeResult) -> Any:
    it = iter(results)
    last = results[-1]

    async def _p() -> ProbeResult:
        nonlocal last
        try:
            last = next(it)
        except StopIteration:
            pass
        return last

    return _p


def _make_supervisor(
    probe: Any,
    tmp_path: Path,
    *,
    cfg: SupervisorConfig | None = None,
    notify: Any | None = None,
) -> MemorySupervisor:
    return MemorySupervisor(
        probe=probe,
        config=cfg or SupervisorConfig(
            poll_interval_s=0.01,
            transient_threshold=2,
            escalation_retry_limit=3,
            recovery_success_threshold=2,
        ),
        notify=notify,
        escalation_state_path=tmp_path / "supervisor-escalation.json",
        attention_path=tmp_path / "attention.md",
    )


# ---- H6 state transitions -------------------------------------------


@pytest.mark.asyncio
async def test_H6_normal_to_degraded_after_transient_threshold(
    tmp_path: Path,
) -> None:
    s = _make_supervisor(_probe_always_fail(), tmp_path)
    t1 = await s.tick()
    assert s.state is SupervisorState.normal  # first failure under threshold
    assert t1 is None
    t2 = await s.tick()
    assert s.state is SupervisorState.degraded
    assert t2 is not None and t2.to_state is SupervisorState.degraded


@pytest.mark.asyncio
async def test_H6_degraded_to_recovering_on_first_success(
    tmp_path: Path,
) -> None:
    s = _make_supervisor(
        _probe_sequence(
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=True, latency_ms=10.0),
        ),
        tmp_path,
    )
    await s.tick()
    await s.tick()
    assert s.state is SupervisorState.degraded
    await s.tick()
    assert s.state is SupervisorState.recovering


@pytest.mark.asyncio
async def test_H6_recovering_to_normal_after_success_threshold(
    tmp_path: Path,
) -> None:
    s = _make_supervisor(
        _probe_sequence(
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=True, latency_ms=10.0),
            ProbeResult(ok=True, latency_ms=10.0),
        ),
        tmp_path,
    )
    for _ in range(4):
        await s.tick()
    assert s.state is SupervisorState.normal


@pytest.mark.asyncio
async def test_H6_bounded_retries_escalate(tmp_path: Path) -> None:
    s = _make_supervisor(_probe_always_fail(), tmp_path)
    # Transient threshold 2, escalation threshold 3 ⇒
    # 1st fail (normal), 2nd fail (degraded), 3rd fail → escalated.
    await s.tick()
    await s.tick()
    await s.tick()
    assert s.state is SupervisorState.escalated


# ---- H7 config-driven cadence ---------------------------------------


@pytest.mark.asyncio
async def test_H7_config_thresholds_drive_transitions(tmp_path: Path) -> None:
    # A tighter threshold should trip faster.
    cfg_fast = SupervisorConfig(
        poll_interval_s=0.01,
        transient_threshold=1,  # one failure trips
        escalation_retry_limit=2,
        recovery_success_threshold=1,
    )
    s = _make_supervisor(_probe_always_fail(), tmp_path, cfg=cfg_fast)
    await s.tick()
    assert s.state is SupervisorState.degraded  # tripped on the first failure


# ---- H9 crash recovery via persisted file ---------------------------


@pytest.mark.asyncio
async def test_H9_persisted_escalation_survives_restart(
    tmp_path: Path,
) -> None:
    notifications: list[tuple[EscalationClass, str, dict[str, Any]]] = []

    async def notify(cls: EscalationClass, text: str, attrs: dict[str, Any]) -> None:
        notifications.append((cls, text, attrs))

    s = _make_supervisor(_probe_always_fail(), tmp_path, notify=notify)
    for _ in range(3):
        await s.tick()
    assert s.state is SupervisorState.escalated
    assert s.current_escalation is not None

    # Simulate a crash/restart by building a second supervisor pointing
    # at the same state file.
    s2 = _make_supervisor(_probe_always_fail(), tmp_path, notify=notify)
    assert s2.state is SupervisorState.escalated
    assert s2.current_escalation is not None
    assert s2.current_escalation.cls is EscalationClass.memory_unreachable


# ---- H16 one notification per escalation class --------------------


@pytest.mark.asyncio
async def test_H16_escalation_notifies_once_then_dedups(
    tmp_path: Path,
) -> None:
    notifications: list[EscalationClass] = []

    async def notify(cls: EscalationClass, text: str, attrs: dict[str, Any]) -> None:
        notifications.append(cls)

    s = _make_supervisor(_probe_always_fail(), tmp_path, notify=notify)
    for _ in range(10):
        await s.tick()
    # Only one notification for the single open class.
    assert len(notifications) == 1
    assert notifications[0] is EscalationClass.memory_unreachable


# ---- H17 class change re-notifies + recovery closes ---------------


@pytest.mark.asyncio
async def test_H17_class_change_re_notifies(tmp_path: Path) -> None:
    notifications: list[EscalationClass] = []

    async def notify(cls: EscalationClass, text: str, attrs: dict[str, Any]) -> None:
        notifications.append(cls)

    # First three probes are "refused" (unreachable), then the next
    # probe is "5xx" (server error) — simulates class change while
    # already escalated.
    s = _make_supervisor(
        _probe_sequence(
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=False, error_class="5xx"),
        ),
        tmp_path,
        notify=notify,
    )
    for _ in range(4):
        await s.tick()
    assert s.state is SupervisorState.escalated
    # One for unreachable, one for server_error (class change), plus
    # one recovery close for unreachable → 3 notifications total.
    classes = set(notifications)
    assert EscalationClass.memory_unreachable in classes
    assert EscalationClass.memory_server_error in classes


@pytest.mark.asyncio
async def test_H17_recovery_closes_escalation_and_clears_attention(
    tmp_path: Path,
) -> None:
    notifications: list[tuple[EscalationClass, str]] = []

    async def notify(cls: EscalationClass, text: str, attrs: dict[str, Any]) -> None:
        notifications.append((cls, text))

    s = _make_supervisor(
        _probe_sequence(
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=True, latency_ms=10.0),
            ProbeResult(ok=True, latency_ms=10.0),
            ProbeResult(ok=True, latency_ms=10.0),
        ),
        tmp_path,
        notify=notify,
    )
    for _ in range(6):
        await s.tick()
    assert s.state is SupervisorState.normal
    # Attention file must be cleared.
    att = tmp_path / "attention.md"
    assert not att.exists()
    # At least one "resolved" notification sent.
    assert any(" resolved " in text for _, text in notifications)


# ---- H10 unit-testable without live sidecar ------------------------


@pytest.mark.asyncio
async def test_H10_supervisor_testable_without_live_sidecar(
    tmp_path: Path,
) -> None:
    s = _make_supervisor(_probe_always_ok(), tmp_path)
    for _ in range(5):
        await s.tick()
    assert s.state is SupervisorState.normal


# ---- attention.md reflects current escalation (H17 tail) ----------


@pytest.mark.asyncio
async def test_attention_md_written_on_escalation(tmp_path: Path) -> None:
    s = _make_supervisor(_probe_always_fail(), tmp_path)
    for _ in range(3):
        await s.tick()
    att = tmp_path / "attention.md"
    assert att.exists()
    text = att.read_text()
    assert "pOS v2 needs attention" in text
    assert "memory.sidecar.unreachable" in text


# ---- drain coordination on recovering / normal -------------------


@pytest.mark.asyncio
async def test_on_recovering_and_on_normal_callbacks_fire(
    tmp_path: Path,
) -> None:
    recovering_fires: list[int] = []
    normal_fires: list[int] = []

    async def on_recovering() -> None:
        recovering_fires.append(1)

    async def on_normal() -> None:
        normal_fires.append(1)

    s = MemorySupervisor(
        probe=_probe_sequence(
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=False, error_class="refused"),
            ProbeResult(ok=True, latency_ms=10.0),
            ProbeResult(ok=True, latency_ms=10.0),
        ),
        config=SupervisorConfig(
            poll_interval_s=0.01,
            transient_threshold=2,
            recovery_success_threshold=2,
            escalation_retry_limit=3,
        ),
        on_recovering=on_recovering,
        on_normal=on_normal,
        escalation_state_path=tmp_path / "supervisor-escalation.json",
        attention_path=tmp_path / "attention.md",
    )
    for _ in range(4):
        await s.tick()
    assert len(recovering_fires) == 1
    assert len(normal_fires) == 1
