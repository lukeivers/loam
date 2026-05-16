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

"""AC.GR.6 — the intake→loop seam closed for the milestone leg (the
named in-scope prerequisite, §3b).

Plan: pos3 loop-goal-refinement-plan-2026-05-16.md §3b + §4 AC.GR.6
F2: the sealed phase-b-fix-plan classed this seam "out of fence,
candidate follow-on" — correct for the three PBF fixes (fix-2 did not
depend on it) but the owner's MILESTONE behaviour is structurally
unverifiable without it: an agreed milestone is meaningless if a
different hand-authored command decides done.  Evidence (the
disconnected halves the plan named): cli `_cmd_run` read a
hand-authored frozen JSON and `derive_acceptance_from_intent` was
called by no run-path code.

Outcome under test (not method): the command the loop FREEZES and
EXECUTES for an agreed-milestone unit is PROVABLY derived from the
`IntakeOutcome.machine_checkable` the user agreed to at the approval
gate — not a separately hand-authored frozen-spec JSON.  Observable:
for a milestone unit the executed check is traceable to the approved
milestone (a content/identity link the read path enforces).  Scope
(F2): this is the ONE AC touching a read-path connection beyond
intake; it is in-scope ONLY as the milestone leg's prerequisite — NOT
a licence to modify decompose/dispatch/judge (AC.FOUND.0 untouched).

Method-independence: satisfiable by intake emitting the freeze-input
directly, by cli/orchestrator consuming IntakeOutcome instead of a
hand-authored JSON, or by an identity/hash binding — the test asserts
agreed-command == executed-command provably, never the wiring
technique.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "framework" / "tools" / "handsoff-loop" / "src"
sys.path.insert(0, str(SRC))

from handsoff_loop import (  # noqa: E402
    IntakeOutcome,
    freeze_input_from_outcome,
)
from handsoff_loop.verify import freeze_acceptance  # noqa: E402


def _milestone_outcome(check_command="python3 count_days.py --min 12"):
    return IntakeOutcome(
        original_intent="get in the best shape of my life",
        under_specification=["unmeasurable aim"],
        elicited_questions=["how often?"],
        elicited_answers={"how often?": "a few times a week"},
        plain_language_acceptance=(
            "Done when you have logged 12 workout days this month."
        ),
        machine_checkable={
            "check_command": check_command,
            "spec": ">=12 logged workout days this month",
        },
        approved=True,
        faithful=True,
        faithfulness_reason="real measurable milestone",
        is_milestone=True,
        milestone_toward="being in the best shape of your life",
        check_in_pending=True,
        refinement_attempts=1,
        refinement_outcome="milestone",
    )


def test_AC_GR_6_executed_check_is_derived_from_agreed_milestone() -> None:
    """The freeze input is provably derived from the AGREED
    machine_checkable — the executed check command IS the user-agreed
    one, not an unrelated hand-authored argv."""
    out = _milestone_outcome("python3 verify_milestone.py --min 12")
    fi = freeze_input_from_outcome(out)
    # the executed argv carries EXACTLY the agreed check command.
    assert "python3 verify_milestone.py --min 12" in fi["check_argv"]
    # the frozen content is the user-approved plain acceptance (so a
    # later sha-pin / assert_unseen_by operates on the agreed artefact).
    assert fi["content"] == out.plain_language_acceptance
    # the acceptance id makes the milestone identity auditable.
    assert "milestone" in fi["acceptance_id"]


def test_AC_GR_6_frozen_acceptance_executes_the_agreed_command(
    tmp_path,
) -> None:
    """End-to-end seam: freeze_acceptance(freeze_input_from_outcome(M))
    yields a FrozenAcceptance whose check_argv is the agreed milestone
    command — 'you agreed to M and the loop verifies exactly M' is
    structurally true, not coincidental."""
    out = _milestone_outcome("/bin/sh -c 'exit 0'")
    fi = freeze_input_from_outcome(out)
    frozen = freeze_acceptance(
        acceptance_id=fi["acceptance_id"],
        content=fi["content"],
        check_argv=fi["check_argv"],
        held_out_argv=fi["held_out_argv"],
        freeze_dir=tmp_path / "_frozen",
    )
    # the loop's verify(...) runs frozen.check_argv (orchestrator.py).
    # That argv is derived from the agreed machine_checkable — the
    # disconnected-halves gap (§3b) is closed for the milestone leg.
    assert "/bin/sh -c 'exit 0'" in frozen.check_argv
    assert frozen.content == out.plain_language_acceptance


def test_AC_GR_6_refuses_non_approved_outcome_as_freeze_source() -> None:
    """A poisoned/non-agreed contract must NEVER reach the executed
    freeze: a non-approved outcome is refused (the AC.PBF.1 honesty
    property carried through the seam)."""
    out = IntakeOutcome(
        original_intent="x", under_specification=[],
        elicited_questions=[], elicited_answers={},
        plain_language_acceptance="",
        machine_checkable={"check_command": "echo ok"},
        approved=False, faithful=False,
        faithfulness_reason="refused",
    )
    with pytest.raises(ValueError):
        freeze_input_from_outcome(out)


def test_AC_GR_6_refuses_empty_check_command() -> None:
    """An empty check command must never reach the command the loop
    executes (AC.GR.6 / AC.PBF.1 carried through the seam)."""
    out = IntakeOutcome(
        original_intent="x", under_specification=[],
        elicited_questions=[], elicited_answers={},
        plain_language_acceptance="done when something",
        machine_checkable={"check_command": "  "},
        approved=True, faithful=True, faithfulness_reason="ok",
    )
    with pytest.raises(ValueError):
        freeze_input_from_outcome(out)


def test_AC_GR_6_cli_from_intake_path_wires_the_seam(
    tmp_path, monkeypatch, capsys,
) -> None:
    """The REAL cli `run --from-intake` read-path consumes an
    IntakeOutcome evidence JSON and freezes the AGREED command —
    proving the seam is wired into the actual run path, not only the
    helper.  We stub the loop body so decompose/dispatch/judge is NOT
    exercised (AC.FOUND.0 untouched) and assert that the FrozenAcceptance
    the real cli builds carries the agreed milestone command."""
    from handsoff_loop import cli

    out = _milestone_outcome("python3 agreed_milestone_check.py --n 12")
    intake_json = tmp_path / "intake.json"
    intake_json.write_text(json.dumps(out.as_evidence()))
    spec_json = tmp_path / "spec.json"
    # the spec file still supplies sub_tasks (D-UNIT — decomposition
    # internal); its check_argv is a DECOY the seam must NOT execute.
    spec_json.write_text(json.dumps({
        "acceptance_id": "hand-authored-decoy",
        "content": "a DIFFERENT hand-authored done",
        "check_argv": ["/bin/sh", "-c", "exit 1"],   # decoy
        "sub_tasks": [{
            "name": "s0", "brief": "b", "tighter_acceptance": "t",
            "check_command": "true",
        }],
    }))

    captured_frozen = {}

    def fake_loop(*, objective, sub_tasks, frozen, work_dir,
                  artifact_dir, **kw):
        # capture what the REAL cli froze; do NOT run the core loop
        # (AC.FOUND.0 — decompose/dispatch/judge untouched).
        captured_frozen["check_argv"] = list(frozen.check_argv)
        captured_frozen["content"] = frozen.content
        captured_frozen["id"] = frozen.acceptance_id

        class _R:
            reached_done = True
            human_loop_driving = False
            cost_usd = 0.0
            wall_clock_s = 0.0
            sub_task_results = []
        return _R()

    monkeypatch.setattr(cli, "_cmd_run", cli._cmd_run)  # real fn
    import handsoff_loop.orchestrator as orch
    monkeypatch.setattr(orch, "run_handsoff_loop", fake_loop)

    rc = cli.main([
        "run", "--objective", "get in shape",
        "--frozen", str(spec_json),
        "--from-intake", str(intake_json),
        "--work-dir", str(tmp_path / "w"),
        "--artifact-dir", str(tmp_path / "a"),
    ])
    assert rc == 0
    # the EXECUTED freeze is the AGREED milestone command — NOT the
    # hand-authored decoy. The disconnected-halves gap is closed.
    assert "python3 agreed_milestone_check.py --n 12" in (
        captured_frozen["check_argv"]
    )
    assert "exit 1" not in " ".join(captured_frozen["check_argv"])
    assert captured_frozen["content"] == out.plain_language_acceptance
    assert "milestone" in captured_frozen["id"]
