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

"""AC.SR-DISTRESS.1 + AC.SR-DISTRESS.2 — distress detection trips the
self-diagnosis by the 2nd signal, and the diagnosis checks the two
load-bearing things.

AC.SR-DISTRESS.1 — On the inbound-message path, a 2nd qualifying distress
signal within the detection window TRIPS the self-diagnosis routine; it
does NOT wait for the user to escalate to an explicit "diagnose this".

AC.SR-DISTRESS.2 — The triggered diagnosis checks (a) comms-path liveness
and (b) recent-actions-vs-claims (the narration-not-action check).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HOOKS_DIR = REPO_ROOT / "framework" / "self-correction" / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from distress_detector import (  # noqa: E402
    DEFAULT_TRIP_THRESHOLD,
    DistressClass,
    DistressDetector,
    classify_distress,
    distress_trigger_description,
)

from loam.self_correction import (  # noqa: E402
    ClaimCheck,
    SelfCorrectionController,
    TriggerSource,
    open_user_reported_correction,
    run_self_diagnosis,
)


# ---- AC.SR-DISTRESS.1 — deterministic rubric, no LLM -------------------


def test_AC_SR_DISTRESS_1_rubric_is_deterministic_classification() -> None:
    # The three qualifying distress classes (the silent-night shapes).
    assert classify_distress("are you there?") == DistressClass.presence
    assert classify_distress("is this broken?") == DistressClass.broken
    assert (
        classify_distress("you keep saying you'll do it but nothing")
        == DistressClass.unfulfilled
    )
    # A non-distress chatty message does NOT qualify (no spurious trip).
    assert classify_distress("please add a chapter about dragons") is None
    assert classify_distress("thanks, that looks great") is None


def test_AC_SR_DISTRESS_1_second_signal_trips(tmp_path: Path) -> None:
    """The 2nd qualifying signal within the window trips — the fire-alarm
    law (2nd signal at the latest)."""
    det = DistressDetector(state_path=tmp_path / "counter.json")

    first = det.observe("are you there?")
    assert first.classified == DistressClass.presence
    assert first.window_count == 1
    assert first.tripped is False  # 1st signal does NOT trip

    second = det.observe("is this thing broken?")
    assert second.window_count == 2
    assert second.tripped is True  # 2nd signal TRIPS — does not wait further

    # The trip threshold default IS the 2nd signal.
    assert DEFAULT_TRIP_THRESHOLD == 2


def test_AC_SR_DISTRESS_1_non_distress_does_not_advance_counter(
    tmp_path: Path,
) -> None:
    det = DistressDetector(state_path=tmp_path / "counter.json")
    det.observe("are you there?")  # 1 qualifying
    mid = det.observe("write me a poem")  # non-distress — no count
    assert mid.classified is None
    assert mid.window_count == 1
    assert mid.tripped is False
    # A 2nd genuine distress signal still trips.
    trip = det.observe("is it stuck?")
    assert trip.tripped is True


def test_AC_SR_DISTRESS_1_window_evicts_stale_signals(tmp_path: Path) -> None:
    """A signal older than the window does not contribute to the trip — the
    counter is a ROLLING window, not a lifetime tally."""
    clock = {"t": 1000.0}
    det = DistressDetector(
        state_path=tmp_path / "counter.json",
        window_seconds=100,
        clock=lambda: clock["t"],
    )
    det.observe("are you there?")  # at t=1000
    clock["t"] = 1000.0 + 200  # 200s later — first signal now stale
    second = det.observe("is it broken?")
    # Only the in-window signal counts → not tripped on a single fresh one.
    assert second.window_count == 1
    assert second.tripped is False


def test_AC_SR_DISTRESS_1_hook_entrypoint_emits_trip_decision(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    """The hook entry-point (the inbound surface) emits a tripped decision
    with a plain-language description on the 2nd signal — without the user
    ever asking to 'diagnose this'."""
    import distress_detector as dd

    state = tmp_path / "counter.json"
    monkeypatch.setenv("LOAM_DISTRESS_STATE", str(state))

    # 1st inbound distress message.
    monkeypatch.setattr("sys.stdin", _FakeStdin(json.dumps({"prompt": "are you there?"})))
    assert dd.main([]) == 0
    out1 = json.loads(capsys.readouterr().out)
    assert out1["tripped"] is False

    # 2nd inbound distress message → trip.
    monkeypatch.setattr("sys.stdin", _FakeStdin(json.dumps({"prompt": "is this stuck?"})))
    assert dd.main([]) == 0
    out2 = json.loads(capsys.readouterr().out)
    assert out2["tripped"] is True
    assert out2["description"]  # plain-language description present
    # The description names the worry, not an internal command/ID.
    assert "diagnose this" not in out2["description"].lower()


class _FakeStdin:
    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> str:
        return self._text


# ---- AC.SR-DISTRESS.1 — the trip opens a REAL correction episode -------


@pytest.mark.asyncio
async def test_AC_SR_DISTRESS_1_trip_opens_user_reported_episode(
    controller: SelfCorrectionController,
) -> None:
    """The trip feeds the EXISTING self-correction user_reported engine (not
    a parallel one): a real correction intake runs."""
    det_obs_desc = distress_trigger_description(
        # any tripped observation; the description is fixed plain-language
        _TrippedObs()
    )
    result = await open_user_reported_correction(
        intake=controller.intake,
        description=det_obs_desc,
        reporter="primary-persona",
    )
    # A real episode opened (intake returns a CorrectionOpenResult, not None).
    assert result is not None
    # And it is a user_reported correction (the existing trigger surface).
    episodes = controller.store.list_all_episodes()
    assert episodes, "the trip must open a real correction episode"


class _TrippedObs:
    classified = "presence"
    window_count = 2
    tripped = True
    window_classes = ("presence", "broken")


# ---- AC.SR-DISTRESS.2 — the diagnosis checks the two load-bearing things


def test_AC_SR_DISTRESS_2_diagnosis_checks_comms_and_claims(
    tmp_path: Path,
) -> None:
    """The diagnosis establishes (a) comms-path liveness and (b)
    recent-actions-vs-claims — the two silent-night root causes."""
    # (b) one claim WITH an artifact (verified), one WITHOUT (the
    # narration-not-action failure).
    done = tmp_path / "saved-notes.txt"
    done.write_text("real artifact")
    missing = tmp_path / "claimed-but-absent.txt"  # never created

    claims = (
        ClaimCheck(claim="saved your notes", artifact_path=done),
        ClaimCheck(claim="published the chapter", artifact_path=missing),
    )

    # (a) comms-path probe says output is NOT reaching the user.
    diag = run_self_diagnosis(comms_probe=lambda: False, claims=claims)

    # (a) checked:
    assert diag.comms.reaching_user is False
    # (b) checked: the unverified claim is named.
    assert diag.actions.all_verified is False
    assert "published the chapter" in diag.actions.unverified_claims
    assert "saved your notes" not in diag.actions.unverified_claims
    # Composed: an unhealthy system.
    assert diag.healthy is False


def test_AC_SR_DISTRESS_2_healthy_system_finds_nothing(tmp_path: Path) -> None:
    """A spurious trip on a healthy system finds nothing wrong — cheap +
    quiet (the asymmetry that justifies bias-early)."""
    done = tmp_path / "a.txt"
    done.write_text("x")
    diag = run_self_diagnosis(
        comms_probe=lambda: True,
        claims=(ClaimCheck(claim="saved", artifact_path=done),),
    )
    assert diag.comms.reaching_user is True
    assert diag.actions.all_verified is True
    assert diag.healthy is True


def test_AC_SR_DISTRESS_2_comms_probe_error_is_not_reaching() -> None:
    """A probe that raises is treated as 'not reaching the user' — fail
    toward surfacing the comms problem, not hiding it."""
    def _boom() -> bool:
        raise RuntimeError("probe blew up")

    diag = run_self_diagnosis(comms_probe=_boom, claims=())
    assert diag.comms.reaching_user is False
