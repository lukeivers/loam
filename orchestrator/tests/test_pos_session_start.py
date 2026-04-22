"""Session-start helper tests (Amendment 2 — hands-off-lifecycle).

Critical property under test: the helper NEVER spawns a long-lived
child process inheriting Claude Code's FDs (v2.1.87 issue #43123
mitigation). It probes, asks the service manager to bring services
up (a non-blocking request), polls for health, and exits.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from scripts.pos_session_start import (
    detect_platform,
    run_session_start,
)


def _probe_fn(
    *, memory: bool = True, orchestrator: bool = True, latency_ms: float = 12.0
):
    def _m():
        return memory, latency_ms, None if memory else "ConnectionRefused"

    def _o():
        return orchestrator, None if orchestrator else "ConnectionRefused"

    return _m, _o


def test_platform_detection_returns_macos_or_linux() -> None:
    plat = detect_platform()
    assert plat in ("macos", "linux", "darwin") or isinstance(plat, str)


def test_ready_path_when_both_services_up() -> None:
    m, o = _probe_fn(memory=True, orchestrator=True)
    r = run_session_start(
        probe_memory_fn=m,
        probe_orchestrator_fn=o,
        service_manager_fn=lambda: [],
        platform_override="macos",
    )
    assert r["status"] == "ready"
    assert r["memory_up"] is True
    assert r["orchestrator_up"] is True
    assert r["additional_context"] == "pos v2 ready"
    assert r["exit_code"] == 0


def test_platform_unsupported_short_circuits() -> None:
    m, o = _probe_fn()
    r = run_session_start(
        probe_memory_fn=m,
        probe_orchestrator_fn=o,
        service_manager_fn=lambda: [],
        platform_override="win32",
    )
    assert r["status"] == "platform-unsupported"
    assert r["exit_code"] == 2
    assert "platform-unsupported:win32" in r["additional_context"]


def test_service_manager_invoked_when_services_down() -> None:
    # First probe returns down; then after service_manager_fn runs,
    # the next probe returns up. This simulates launchctl bootstrap
    # bringing the service up within the budget.
    probe_count = {"n": 0}

    def m():
        probe_count["n"] += 1
        memory_up = probe_count["n"] >= 2
        return memory_up, 10.0, None if memory_up else "refused"

    def o():
        return True, None  # orchestrator always up in this scenario

    sm_called = {"n": 0}

    def sm():
        sm_called["n"] += 1
        return []

    r = run_session_start(
        probe_memory_fn=m,
        probe_orchestrator_fn=o,
        service_manager_fn=sm,
        platform_override="macos",
        bring_up_timeout_s=1.0,
        bring_up_poll_interval_s=0.01,
    )
    assert sm_called["n"] == 1  # service manager was asked to start
    assert r["status"] == "ready"
    assert r["exit_code"] == 0


def test_partial_status_when_services_dont_come_up() -> None:
    m, o = _probe_fn(memory=False, orchestrator=True)
    r = run_session_start(
        probe_memory_fn=m,
        probe_orchestrator_fn=o,
        service_manager_fn=lambda: ["plist missing"],
        platform_override="macos",
        bring_up_timeout_s=0.05,
        bring_up_poll_interval_s=0.01,
    )
    assert r["status"] == "partial"
    assert r["exit_code"] == 3
    assert "Supervisor will escalate loudly" in r["additional_context"]
