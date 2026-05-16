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

"""AC.GR.3 — milestone-on-the-path with explicit agreement + a
re-engaged check-in.

Plan: pos3 loop-goal-refinement-plan-2026-05-16.md §4 AC.GR.3
Binding foundation: owner steer — "sometimes the right choice is to
pick a measurable goal that is ON THE PATH to what the user asked, get
them to AGREE to that, achieve it, then CHECK IN".

Outcome under test (not method): when refinement determines the real
goal is not directly measurable even after clarification, the intake
derives a measurable goal ON THE PATH, surfaces THAT milestone (not
the fuzzy aim) through the single plain-language approval gate framed
as a milestone the loop will aim at first, and — on agreement —
produces an outcome that (i) carries the measurable milestone as the
approved unit, AND (ii) records this is a milestone TOWARD a still-open
fuzzy aim such that a check-in is structurally re-engaged after the
milestone (the outcome is NOT a terminal "done").  A milestone that
silently REPLACES the user's aim with no recorded check-in obligation
does NOT satisfy this AC.

Method-independence: satisfiable by a milestone field + check-in flag,
a chained-unit representation, or a recursive decomposition where the
milestone is the first tighter sub-objective — the test asserts the
agreed-measurable-milestone + structurally-recorded check-in, never
the data structure.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop import intake as I  # noqa: E402

_FUZZY = "help me get in the best shape of my life"

# A milestone-on-the-path derive: is_milestone=true, names the open
# fuzzy aim, carries a REAL measurable check (not a proxy).
_MILESTONE_BODY = (
    "Done when you have logged a workout on at least 12 days this "
    "month.\n---\n"
    '{"check_command": "python3 count_workout_days.py --min 12", '
    '"spec": ">=12 logged workout days this month", '
    '"is_milestone": true, "milestone_toward": '
    '"being in the best shape of your life (an open, ongoing aim)"}'
)


def _stub(monkeypatch, *, whole_refine_body):
    """elicit -> broken derive -> whole-goal re-derive (here: emits a
    milestone, since the whole aim is not directly measurable) ->
    faithfulness judge."""

    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        if "List ONLY the few missing" in prompt:
            return {"result": "How often?\nWhat counts?"}
        if "Ask ONLY the few plain questions" in prompt:
            return {"result": "What does best shape mean to you?"}
        if "Re-derive a FAITHFUL" in prompt:
            return {"result": whole_refine_body}
        if "pick ONE measurable goal that is a real" in prompt:
            return {"result": _MILESTONE_BODY}
        if "Produce TWO things" in prompt:
            return {"result": "broken, no separator"}
        if "Adversarial faithfulness check" in prompt:
            return {"result": '{"faithful": true, "reason": "real"}'}
        return {"result": ""}

    monkeypatch.setattr(I, "_claude_json", fake)


def test_AC_GR_3_milestone_carries_aim_and_checkin(monkeypatch) -> None:
    """The whole goal is not directly measurable -> the re-derive
    emits a milestone-on-the-path; the outcome carries the measurable
    milestone as the approved unit AND records the still-open fuzzy
    aim + a re-engaged check-in (NOT a terminal done)."""
    gate_seen: list[str] = []

    def approve(text: str) -> bool:
        gate_seen.append(text)
        return True

    _stub(monkeypatch, whole_refine_body=_MILESTONE_BODY)
    out = I.derive_acceptance_from_intent(
        intent=_FUZZY,
        under_specification=["unmeasurable aim"],
        approval_fn=approve,
        elicit_answer_fn=lambda q: "I just want to feel good",
        run_model=True,
    )
    # (i) the measurable milestone is the approved unit.
    assert out.approved is True
    assert out.is_milestone is True
    assert out.machine_checkable.get("check_command")
    # (ii) it records the still-open fuzzy aim (does NOT silently
    # replace the user's aim) + a structurally re-engaged check-in.
    assert out.milestone_toward.strip()
    assert out.original_intent == _FUZZY      # the aim stays visible
    assert out.check_in_pending is True       # check-in re-engaged
    assert out.refinement_outcome == "milestone"


def test_AC_GR_3_gate_frames_it_as_a_milestone_not_the_full_done(
    monkeypatch,
) -> None:
    """The single approval gate must surface the MILESTONE framed as
    'aim at this first, then check back' — not silently present it as
    the full done (the user's plain-language agreement is to *that
    milestone*)."""
    gate_seen: list[str] = []
    _stub(monkeypatch, whole_refine_body=_MILESTONE_BODY)
    I.derive_acceptance_from_intent(
        intent=_FUZZY,
        under_specification=["unmeasurable aim"],
        approval_fn=lambda t: gate_seen.append(t) or True,
        elicit_answer_fn=lambda q: "feel good",
        run_model=True,
    )
    assert len(gate_seen) == 1, "still EXACTLY one approval gate"
    text = gate_seen[0].lower()
    assert "milestone" in text
    assert "check back" in text or "check in" in text
    # the still-open fuzzy aim is named in the gate, not hidden.
    assert "best shape" in text


def test_AC_GR_3_no_silent_replacement_without_checkin(
    monkeypatch,
) -> None:
    """The AC's explicit negative: a milestone that does not record a
    check-in obligation is NOT this AC.  Here we assert the positive
    invariant — whenever is_milestone is True AND approved, the
    check-in obligation is ALWAYS set (never a silent terminal
    replacement of the user's aim)."""
    _stub(monkeypatch, whole_refine_body=_MILESTONE_BODY)
    out = I.derive_acceptance_from_intent(
        intent=_FUZZY,
        under_specification=["unmeasurable aim"],
        approval_fn=lambda t: True,
        elicit_answer_fn=lambda q: "feel good",
        run_model=True,
    )
    if out.is_milestone and out.approved:
        assert out.check_in_pending is True
        assert out.milestone_toward.strip()
    # and the evidence dict carries the obligation for the seam.
    ev = out.as_evidence()
    assert ev["is_milestone"] is True
    assert ev["check_in_pending"] is True
    assert ev["milestone_toward"].strip()
