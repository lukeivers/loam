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

"""AC.GR.1 — the honest-refuse terminal becomes a refinement ENTRY.

Plan: pos3 loop-goal-refinement-plan-2026-05-16.md §4 AC.GR.1
Binding foundation: owner-steer-goal-refinement-2026-05-16.md (Luke,
Telegram 11408) — honest-refuse becomes the trigger, not the terminal.
Evidence base: phase-b-fix-build-report-2026-05-16.md (sealed 2/7;
I2/I5 REFUSED-HONEST were dead ends; I3/I6/I7 faithful=False were dead
ends) — exactly the two terminals this AC converts to entries.

Outcome under test (not method): when the intake reaches the state it
PREVIOUSLY honest-refused (empty/broken/unparsed derive — the
AC.PBF.1 defect predicate) OR the independent judge returns
`faithful=False`, the outcome is NO LONGER an immediate terminal
`approved=False`.  Instead a BOUNDED refinement attempt runs whose
observable result is one of: (a) a refined goal that passes the
existing machine-checkable + faithful checks; (b) a measurable
milestone-on-the-path; or (c) — only after the bound is exhausted —
a definite honest-negative naming why the class resisted refinement.
A bare immediate refusal with NO refinement attempt does NOT satisfy
this AC.

Method-independence: the AC is satisfiable by a bounded re-derive
loop, a refinement sub-phase, or a recursive single-step
decomposition with a judge-driven stop — the test asserts the
terminal→entry transition + bounded exhaustion, never the construct.
Deterministic (`_claude_json` stubbed) — the real 7-intent re-harden
is AC.GR.5.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop import intake as I  # noqa: E402


def _stub(monkeypatch, *, derive_body, refine_body=None,
          judge='{"faithful": true, "reason": "ok"}',
          judge_after_refine=None, milestone_body=None):
    """Stub the real claude subprocess: a bounded elicit, then a
    derive, then (on the refinement re-derive / milestone prompts) a
    refine/milestone body, then the faithfulness judge.

    `judge` is the FIRST faithfulness verdict; `judge_after_refine`
    (when set) is the verdict on the post-refinement re-judge — the
    realistic shape the binding foundation assumes when the judge
    catches a proxy and refinement recovers a real check."""
    state = {"judge_calls": 0}

    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        if "List ONLY the few missing" in prompt:
            return {"result": "How?\nWhere?"}
        if "Ask ONLY the few plain questions" in prompt:
            return {"result": "What exactly counts as done?"}
        if "pick ONE measurable goal that is a real" in prompt:
            return {"result": milestone_body if milestone_body
                    is not None else "---\n{}"}
        if "Re-derive a FAITHFUL" in prompt:
            return {"result": refine_body if refine_body is not None
                    else "---\n{}"}
        if "Produce TWO things" in prompt:
            return {"result": derive_body}
        if "Adversarial faithfulness check" in prompt:
            state["judge_calls"] += 1
            if state["judge_calls"] >= 2 and judge_after_refine:
                return {"result": judge_after_refine}
            return {"result": judge}
        return {"result": ""}

    monkeypatch.setattr(I, "_claude_json", fake)


def _run(monkeypatch, **kw):
    calls: list[str] = []

    def approve(plain: str) -> bool:
        calls.append(plain)
        return True

    _stub(monkeypatch, **kw)
    out = I.derive_acceptance_from_intent(
        intent="make sure my photos are safe",
        under_specification=["implicit constraints"],
        approval_fn=approve,
        elicit_answer_fn=lambda q: "a vague layperson answer",
        run_model=True,
    )
    return out, calls


def test_AC_GR_1_empty_broken_derive_enters_refinement_not_terminal(
    monkeypatch,
) -> None:
    """The AC.PBF.1 empty/broken state (the I2/I5 dead-end shape) is no
    longer an immediate terminal: a refinement attempt runs and, here,
    recovers a faithful measurable whole goal that reaches approval."""
    out, calls = _run(
        monkeypatch,
        # I7/I2 shape: model put everything one side of `---` -> empty
        # plain + empty check -> the PREVIOUSLY-terminal refuse state.
        derive_body="Routine is live. Here is the required output:",
        # the bounded refine re-derive recovers a real measurable goal.
        refine_body=(
            "Done when every photo on your phone and laptop is "
            "uploaded and you can restore them.\n---\n"
            '{"check_command": '
            '"python3 verify_all_photos_uploaded.py --expect 20000", '
            '"spec": "all photos actually uploaded + restorable", '
            '"is_milestone": false, "milestone_toward": ""}'
        ),
    )
    # NOT a bare immediate refusal: refinement ran and recovered.
    assert out.refinement_outcome in ("interactive", "self")
    assert out.refinement_attempts >= 1
    assert out.approved is True
    assert out.faithful is True
    # the approval gate WAS reached (with the refined text), proving
    # the terminal became an entry, not an exit.
    assert calls and calls[0]


def test_AC_GR_1_unfaithful_judge_enters_refinement_not_terminal(
    monkeypatch,
) -> None:
    """The OTHER terminal: a `faithful=False` proxy verdict (the
    I3/I6/I7 dead-end shape) routes into the SAME bounded refinement,
    here recovering a faithful measurable goal — not a dead end."""
    out, calls = _run(
        monkeypatch,
        # a well-formed but PROXY derive -> judge says faithful=false.
        derive_body=(
            "Done when your photos are safe.\n---\n"
            '{"check_command": "[ -f ~/Library/cloudkit.db ]", '
            '"spec": "presence test for a setup file"}'
        ),
        judge='{"faithful": false, "reason": "stale proxy check"}',
        # the realistic shape: judge catches the proxy, refinement
        # recovers a REAL check, the re-judge passes the real check.
        judge_after_refine='{"faithful": true, "reason": "real check"}',
        refine_body=(
            "Done when all your photos are verifiably uploaded.\n---\n"
            '{"check_command": '
            '"python3 verify_uploaded.py --count 20000", '
            '"spec": "real upload verification", '
            '"is_milestone": false, "milestone_toward": ""}'
        ),
    )
    assert out.refinement_outcome in ("interactive", "self")
    assert out.refinement_attempts >= 1
    assert out.faithful is True          # refinement recovered it
    assert out.approved is True


def test_AC_GR_1_bare_refusal_without_attempt_does_not_satisfy(
    monkeypatch,
) -> None:
    """The AC's explicit negative: when refinement is exhausted with
    no measurable goal/milestone, the outcome must be a DEFINITE
    honest-negative that NAMED a refinement attempt ran — never a
    bare immediate refusal with zero attempts."""
    out, _calls = _run(
        monkeypatch,
        derive_body="garbled, no structure at all",
        refine_body="still garbled, no structure",
        milestone_body="still nothing usable",
    )
    assert out.refinement_outcome == "honest-negative"
    assert out.refinement_attempts >= 1          # an attempt DID run
    assert out.approved is False
    assert out.faithful is False
    # the negative NAMES why the class resisted (not a bare refuse).
    assert "refine" in out.faithfulness_reason.lower()
    assert "attempt" in out.faithfulness_reason.lower()
