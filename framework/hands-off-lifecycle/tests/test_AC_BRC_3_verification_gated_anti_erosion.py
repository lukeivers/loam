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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.BRC.3 — each refine iteration is VERIFICATION-GATED (anti-
erosion; a binding constraint, not a footnote).

Outcome under test (not method): every refine iteration's
continuation is gated by a verification step — the loop accepts
"done" / "advanced" ONLY on the independent check result, NEVER on the
sub-agent's unverified self-report.  A sub-agent that LOUDLY claims
"I fixed it" (the DONE_SENTINEL in its transcript) while the
independent verify still fails MUST NOT flip the loop's outcome to
done, and the loop MUST NOT silently accumulate non-improving passes.
Deterministic (no real claude): the sub-agent self-reports done on
every pass while the independent verify keeps failing.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop import orchestrator as orch  # noqa: E402
from handsoff_loop.goal_drive import DONE_SENTINEL  # noqa: E402
from handsoff_loop.orchestrator import (  # noqa: E402
    SubTask,
    run_handsoff_loop,
)
from handsoff_loop.verify import (  # noqa: E402
    FrozenAcceptance,
    VerifyResult,
)


def _frozen() -> FrozenAcceptance:
    return FrozenAcceptance(
        acceptance_id="brc3",
        content="frozen-graded-acceptance-never-in-any-brief",
        content_sha256="x",
        check_argv=["true"],
    )


def _subtask() -> SubTask:
    return SubTask(
        name="t", brief="do it",
        tighter_acceptance="done", check_command="placeholder",
    )


def test_AC_BRC_3_self_report_done_does_not_flip_outcome(
    tmp_path, monkeypatch,
) -> None:
    """The sub-agent SHOUTS the done-sentinel every pass; the
    independent verify never passes -> the loop's outcome stays the
    honest negative.  Progress is NOT accepted on self-report."""

    def loud_self_report(spec, *, work_dir, timeout):
        # The transcript contains the done sentinel — i.e. the
        # sub-agent claims success. AC.BRC.3 says this must NOT be
        # what advances the loop.
        return (f"I fixed it. {DONE_SENTINEL}\n", 1.0, 0.01)

    monkeypatch.setattr(orch, "_dispatch_subagent", loud_self_report)
    monkeypatch.setattr(
        orch, "verify",
        lambda *a, **k: VerifyResult(
            False, 1, None, "independent check: still wrong", "",
            "brc3", "x"),
    )
    r = run_handsoff_loop(
        objective="o", sub_tasks=[_subtask()], frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
        max_refine_attempts=3,
    )
    assert r.reached_done is False, (
        "self-reported done with a failing independent verify must "
        "NOT flip the loop to done (AC.BRC.3 anti-erosion)"
    )
    # Every iteration was gated on the independent verify, not the
    # self-report — observable in the refine log.
    assert len(r.refine_log) == 4  # pass0 + 3 re-drives
    for entry in r.refine_log:
        assert entry["gated_on"] == "independent-verify"
        assert entry["verify_done"] is False


def test_AC_BRC_3_gate_is_a_fresh_verify_per_iteration(
    tmp_path, monkeypatch,
) -> None:
    """Each re-drive triggers a FRESH independent verify whose result
    is the sole continue/stop signal (a stale pass cannot carry)."""
    verify_calls = {"n": 0}

    def fake_dispatch(spec, *, work_dir, timeout):
        return ("t\n", 1.0, 0.01)

    def counting_verify(*a, **k):
        verify_calls["n"] += 1
        return VerifyResult(False, 1, None, "wrong", "", "brc3", "x")

    monkeypatch.setattr(orch, "_dispatch_subagent", fake_dispatch)
    monkeypatch.setattr(orch, "verify", counting_verify)
    r = run_handsoff_loop(
        objective="o", sub_tasks=[_subtask()], frozen=_frozen(),
        work_dir=tmp_path / "wd", artifact_dir=tmp_path / "ad",
        max_refine_attempts=2,
    )
    # 1 verify after pass0 + 1 verify after each of 2 re-drives.
    assert verify_calls["n"] == 3
    assert r.refine_stop_reason == "attempt-bound"
    assert r.reached_done is False
