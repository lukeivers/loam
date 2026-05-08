# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Session-start helper tests (Amendment 2 — hands-off-lifecycle).

Critical property under test: the helper NEVER spawns a long-lived
child process inheriting Claude Code's FDs (v2.1.87 issue #43123
mitigation). It probes, asks the service manager to bring services
up (a non-blocking request), polls for health, and exits.
"""

from __future__ import annotations



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


def test_platform_detection_returns_macos_or_unsupported_label() -> None:
    plat = detect_platform()
    assert isinstance(plat, str)
    assert plat != ""


def test_ready_path_when_both_services_up() -> None:
    m, o = _probe_fn(memory=True, orchestrator=True)
    r = run_session_start(
        probe_memory_fn=m,
        probe_orchestrator_fn=o,
        service_manager_fn=lambda: [],
        platform_override="macos",
        # V11.E: opt into legacy "memory expected" semantics so the
        # probe runs (mirrors a workspace where graphiti IS installed).
        is_memory_expected_fn=lambda: True,
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
        # V11.E: memory expected → probe actually runs.
        is_memory_expected_fn=lambda: True,
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
        # V11.E: legacy semantics — probe runs and reports memory down.
        is_memory_expected_fn=lambda: True,
    )
    assert r["status"] == "partial"
    assert r["exit_code"] == 3
    assert "Supervisor will escalate loudly" in r["additional_context"]


# ---- AC.V11.E.1 — graphiti probe graceful-skip (Resolution A) -------


def test_AC_V11_E_1_memory_skipped_when_plist_absent() -> None:
    """When the memory-graphiti launchd plist is absent at the canonical
    location, ``run_session_start`` skips the memory probe entirely:
    ``probe_memory_fn`` is not called; ``memory_expected`` is False;
    ``status`` is 'ready' if the orchestrator is up; the additional
    context warning text omits ``memory_up=...``.

    Per V11.E item (b) Resolution A — plist-existence-as-detection-
    signal. Closes the M-FBM-only stranger-workspace false-alarm.
    """
    pm_called = {"n": 0}

    def pm_should_not_run():
        pm_called["n"] += 1
        return False, 0.0, "ConnectionRefused"

    _, o = _probe_fn(orchestrator=True)
    r = run_session_start(
        probe_memory_fn=pm_should_not_run,
        probe_orchestrator_fn=o,
        service_manager_fn=lambda: [],
        platform_override="macos",
        is_memory_expected_fn=lambda: False,
    )
    assert pm_called["n"] == 0, "memory probe ran despite plist-absent"
    assert r["memory_expected"] is False
    assert r["status"] == "ready"
    assert r["exit_code"] == 0
    assert r["additional_context"] == "pos v2 ready"


def test_AC_V11_E_1_partial_warning_text_drops_memory_up_when_not_expected() -> None:
    """When memory is not expected AND the orchestrator is down, the
    partial-status warning text carries ``memory_expected=False`` rather
    than ``memory_up=...`` (which would be a misleading false-alarm).
    The ``com.loam.memory-graphiti.plist not installed`` warning is
    filtered from ``additional_context`` in the not-expected case.
    """
    _, o = _probe_fn(orchestrator=False)
    r = run_session_start(
        probe_memory_fn=lambda: (True, 0.0, None),  # never called
        probe_orchestrator_fn=o,
        service_manager_fn=lambda: [
            "com.loam.memory-graphiti.plist not installed at /tmp/x",
            "com.loam.orchestrator.plist not installed at /tmp/y",
        ],
        platform_override="macos",
        bring_up_timeout_s=0.05,
        bring_up_poll_interval_s=0.01,
        is_memory_expected_fn=lambda: False,
    )
    assert r["status"] == "partial"
    assert r["memory_expected"] is False
    # Warning string carries the not-expected token.
    assert "memory_expected=False" in r["additional_context"]
    assert "memory_up=" not in r["additional_context"]
    # The memory-plist-not-installed warning is filtered (it's the
    # expected state for an M-FBM-only workspace).
    assert "memory-graphiti.plist not installed" not in r["additional_context"]
    # The orchestrator-plist warning is preserved (real problem).
    assert "orchestrator.plist not installed" in r["additional_context"]


def test_AC_V11_E_4_memory_probe_runs_when_plist_present() -> None:
    """Negative AC: when the plist IS present, behaviour is unchanged
    from pre-V11.E. The memory probe runs; up/down outcome is reported
    per the probe result; ``memory_expected`` is True.
    """
    m, o = _probe_fn(memory=True, orchestrator=True)
    r = run_session_start(
        probe_memory_fn=m,
        probe_orchestrator_fn=o,
        service_manager_fn=lambda: [],
        platform_override="macos",
        is_memory_expected_fn=lambda: True,
    )
    assert r["memory_expected"] is True
    assert r["memory_up"] is True
    assert r["status"] == "ready"
    assert r["exit_code"] == 0


def test_AC_V11_E_3_is_memory_expected_uses_canonical_location(
    tmp_path,
) -> None:
    """The plist-existence helper checks the canonical launchd location
    ``<launch_agents_dir>/<memory_label>.plist``. Test parameterises
    ``launch_agents_dir`` (matching ``ask_service_manager_to_start``'s
    existing pattern) for isolation.
    """
    from scripts.pos_session_start import _is_memory_expected

    # Empty dir → not expected.
    empty = tmp_path / "empty"
    empty.mkdir()
    assert _is_memory_expected(launch_agents_dir=empty) is False

    # Touch the plist → expected.
    present = tmp_path / "present"
    present.mkdir()
    (present / "com.loam.memory-graphiti.plist").write_text("<plist/>")
    assert _is_memory_expected(launch_agents_dir=present) is True
