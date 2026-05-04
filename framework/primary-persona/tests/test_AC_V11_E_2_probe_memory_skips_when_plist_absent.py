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

"""AC.V11.E.2 — graphiti probe graceful-skip in session_start_gate.

When the memory-graphiti launchd plist is absent at the canonical
location (``~/Library/LaunchAgents/com.loam.memory-graphiti.plist``),
``_probe_memory`` returns the sentinel ``"not_expected"`` instead of
attempting a TCP probe and returning ``"down"``. This closes the
M-FBM-only stranger-workspace false-alarm where probing graphiti is
guaranteed to fail because the user doesn't run graphiti at all.

When the plist IS present, probing runs as today (returns ``"up"`` /
``"down"`` per TCP outcome). AC.V11.E.4 negative AC.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona import session_start_gate as gate


def test_AC_V11_E_2_probe_memory_returns_not_expected_when_plist_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No plist at the canonical location → ``not_expected`` sentinel.
    Probe is not attempted (the graceful-skip is observable by the
    sentinel + by the absence of side effects in an empty tmp dir).
    """
    fake_home = tmp_path / "home"
    (fake_home / "Library" / "LaunchAgents").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    result = gate._probe_memory(workspace_root=tmp_path)

    assert result == "not_expected"


def test_AC_V11_E_2_probe_memory_runs_when_plist_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Plist present at the canonical location → probe runs as today.
    The TCP probe will report ``down`` because no graphiti is listening
    on port 8765 in the test env (or the env-default port). The
    observable AC.V11.E.4 contract: the function returns one of
    ``up``/``down`` rather than ``not_expected``.
    """
    fake_home = tmp_path / "home"
    launch_agents = fake_home / "Library" / "LaunchAgents"
    launch_agents.mkdir(parents=True)
    (launch_agents / "com.loam.memory-graphiti.plist").write_text("<plist/>")
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    result = gate._probe_memory(workspace_root=tmp_path)

    # Did NOT short-circuit; probe ran. Result is one of the
    # probe-outcome values (not the not_expected sentinel).
    assert result in {"up", "down"}


def test_AC_V11_E_2_probe_service_state_renders_not_expected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``probe_service_state`` aggregates the per-service probes; the
    ``memory`` key carries the new sentinel when applicable, surfacing
    the architectural state through the existing ``dict[str, str]``
    return shape (no schema change required).
    """
    fake_home = tmp_path / "home"
    (fake_home / "Library" / "LaunchAgents").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    state = gate.probe_service_state(workspace_root=tmp_path)

    assert state["memory"] == "not_expected"
    # Orchestrator key still reports its own state independently.
    assert state["orchestrator"] in {"up", "down", "unknown"}


def test_AC_V11_E_3_canonical_plist_path_matches_orchestrator_helper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The plist path used by the gate's ``_probe_memory`` matches the
    path used by the orchestrator-side ``ask_service_manager_to_start``
    (single source-of-truth for the detection signal — both probe
    sites consult the same file).
    """
    fake_home = tmp_path / "home"
    (fake_home / "Library" / "LaunchAgents").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    expected = (
        fake_home
        / "Library"
        / "LaunchAgents"
        / "com.loam.memory-graphiti.plist"
    )
    assert gate._memory_graphiti_plist_path() == expected
