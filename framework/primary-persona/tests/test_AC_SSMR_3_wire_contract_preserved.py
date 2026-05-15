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

"""AC.SSMR.3 — the SEALED wire contract is preserved byte-for-byte by
the prose-only reframe: no behaviour change crosses any boundary.

The reframe (AC.SSMR.1 / AC.SSMR.2) edits docstrings + the Pydantic
``Field`` description + comments only. This AC is the structural guard
that the edit was prose-only: the ``service_state`` dict shape, the
``memory`` + ``orchestrator`` keys, and the value set
(``up`` / ``down`` / ``unknown`` / ``not_expected``) are unchanged,
and ``probe_service_state`` still returns the same dict shape with
values drawn only from the sealed set.

If any of these assertions fails, the reframe was NOT prose-only and
plan §7 halt-trigger 4 fires. The pre-existing session-start suites
(``test_D8_1_session_start_emission`` / ``test_D8_4_cold_start_budget``
/ ``test_AC46_1_session_start_cli_emits_structured_payload`` /
``test_AC_V11_E_2_probe_memory_skips_when_plist_absent``) are NOT
modified by this amendment and continue to assert the same contract
from the consumer side.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona import session_start_gate as gate

_SEALED_VALUE_SET = {"up", "down", "unknown", "not_expected"}


def test_AC_SSMR_3_probe_returns_memory_and_orchestrator_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``probe_service_state`` still returns a dict carrying exactly
    the ``memory`` + ``orchestrator`` keys (contract unchanged)."""
    fake_home = tmp_path / "home"
    (fake_home / "Library" / "LaunchAgents").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    state = gate.probe_service_state(workspace_root=tmp_path)

    assert isinstance(state, dict)
    assert set(state.keys()) == {"memory", "orchestrator"}, (
        "the prose reframe must not add/remove/rename service_state "
        "keys (SEALED contract)"
    )


def test_AC_SSMR_3_values_drawn_only_from_sealed_set(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every value is drawn from the sealed value set — the reframe
    introduces no new value (``not_expected`` already existed)."""
    fake_home = tmp_path / "home"
    (fake_home / "Library" / "LaunchAgents").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    state = gate.probe_service_state(workspace_root=tmp_path)

    for key, value in state.items():
        assert value in _SEALED_VALUE_SET, (
            f"service_state[{key!r}] == {value!r} is outside the "
            f"sealed value set {sorted(_SEALED_VALUE_SET)} — the "
            "reframe must be prose-only"
        )


def test_AC_SSMR_3_mfbm_memory_signal_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The V11.E M-FBM signal is behaviourally untouched: plist-absent
    → ``memory: not_expected`` exactly as before the reframe."""
    fake_home = tmp_path / "home"
    (fake_home / "Library" / "LaunchAgents").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: fake_home)

    state = gate.probe_service_state(workspace_root=tmp_path)

    assert state["memory"] == "not_expected", (
        "the M-FBM-only memory signal must be byte-identical to the "
        "sealed V11.E behaviour (the reframe touches prose only)"
    )


def test_AC_SSMR_3_session_payload_accepts_service_state_dict() -> None:
    """The ``SessionPayload`` model still accepts a ``dict[str, str]``
    ``service_state`` — the Field description reword did not change the
    field's type contract."""
    from loam.primary_persona.context_composer import SessionPayload

    field = SessionPayload.model_fields["service_state"]
    # Type annotation unchanged: dict[str, str].
    assert field.annotation == dict[str, str], (
        "the service_state field type contract must be unchanged by "
        "the description reword"
    )
