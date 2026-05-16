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

"""AC.GR.4 — refinement is BOUNDED and the honest-negative survives.

Plan: pos3 loop-goal-refinement-plan-2026-05-16.md §4 AC.GR.4
Binding foundation: the owner steer's "do your best to refine" is a
*bounded* best — the bar is honest, not gamed.  Evidence base: the
sealed `ceb629b` no-fake property (the loop must NOT fabricate a cheap
stand-in test) is preserved.

Outcome under test (not method): the refinement construct has an
explicit FINITE bound; on exhausting it without a faithful measurable
goal or an agreed milestone, the intake produces a DEFINITE
honest-negative naming the goal class + why it resisted — NOT an
unbounded refine loop, NOT a fabricated cheap test (the sealed
no-fake property holds), NOT a silently weakened acceptance to force
a pass.  The honest-negative is an AC-satisfying outcome exactly as a
successful refinement is.

Method-independence: satisfiable by an attempt counter, a
judge-`needs_fresh_start`-style irreducible verdict, or a cost/time
budget — the test asserts bounded + honest-negative-preserved +
no-fake-preserved, never the bounding mechanism.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop import intake as I  # noqa: E402


def test_AC_GR_4_refine_attempt_count_is_finitely_bounded(
    monkeypatch,
) -> None:
    """An explicit finite bound exists and is honoured: even when the
    model NEVER produces a measurable goal, the construct stops at the
    declared bound — it does not loop forever."""
    call_count = {"derive_like": 0}

    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        if "List ONLY the few missing" in prompt:
            return {"result": "How?\nWhere?"}
        if "Ask ONLY the few plain questions" in prompt:
            return {"result": "What exactly?"}
        # every derive/refine/milestone prompt -> still broken.
        if ("Produce TWO things" in prompt
                or "Re-derive a FAITHFUL" in prompt
                or "pick ONE measurable goal that is a real" in prompt):
            call_count["derive_like"] += 1
            return {"result": "garbled, no structure, never usable"}
        return {"result": ""}

    monkeypatch.setattr(I, "_claude_json", fake)
    out = I.derive_acceptance_from_intent(
        intent="make me happy",
        under_specification=["fundamentally unmeasurable"],
        approval_fn=lambda p: True,
        elicit_answer_fn=lambda q: "i dunno",
        run_model=True,
    )
    # bounded: refinement attempts never exceed the declared max.
    assert out.refinement_attempts <= I._REFINE_MAX_ATTEMPTS
    assert out.refinement_attempts >= 1
    # the construct did not loop unbounded — the derive-like calls are
    # finite (1 original derive + at most _REFINE_MAX_ATTEMPTS refine).
    assert call_count["derive_like"] <= 1 + I._REFINE_MAX_ATTEMPTS


def test_AC_GR_4_exhausted_bound_yields_definite_honest_negative(
    monkeypatch,
) -> None:
    """On exhaustion the outcome is a DEFINITE honest-negative that
    NAMES why the class resisted measurement — an AC-satisfying
    outcome, reported straight (not a failure, not retried)."""

    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        if "List ONLY the few missing" in prompt:
            return {"result": "How?"}
        if "Ask ONLY the few plain questions" in prompt:
            return {"result": "What?"}
        return {"result": "never anything usable"}

    monkeypatch.setattr(I, "_claude_json", fake)
    out = I.derive_acceptance_from_intent(
        intent="make my life meaningful",
        under_specification=["irreducible"],
        approval_fn=lambda p: True,
        elicit_answer_fn=lambda q: "vague",
        run_model=True,
    )
    assert out.refinement_outcome == "honest-negative"
    assert out.approved is False
    assert out.faithful is False
    # DEFINITE + names the class + names the bound (evidence-carrying).
    r = out.faithfulness_reason.lower()
    assert "refine" in r
    assert "bounded refinement attempt" in r
    assert "honest-negative" in r or "valid outcome" in r


def test_AC_GR_4_honest_negative_is_not_a_fabricated_cheap_test(
    monkeypatch,
) -> None:
    """The sealed `ceb629b` no-fake property survives: on exhaustion
    the construct does NOT lower the bar to a trivially-true check to
    force a pass — it yields the honest-negative with NO machine check
    promoted to approved."""

    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        if "List ONLY the few missing" in prompt:
            return {"result": "How?"}
        if "Ask ONLY the few plain questions" in prompt:
            return {"result": "What?"}
        return {"result": "no usable contract ever"}

    monkeypatch.setattr(I, "_claude_json", fake)
    out = I.derive_acceptance_from_intent(
        intent="make everyone like me",
        under_specification=["socially irreducible"],
        approval_fn=lambda p: True,
        elicit_answer_fn=lambda q: "i guess",
        run_model=True,
    )
    # NOT a fabricated pass: never approved, never faithful, no
    # trivially-true check promoted as the accepted unit.
    assert out.approved is False
    assert out.faithful is False
    assert out.is_milestone is False
    assert out.check_in_pending is False
    # the construct never invented an always-true stand-in: the
    # machine_checkable is the (broken) prior, not a forged passer.
    mc = out.machine_checkable or {}
    assert not str(mc.get("check_command") or "").strip() or mc.get(
        "_parse_failed"
    )


def test_AC_GR_4_honest_negative_is_ac_satisfying_like_a_success(
    monkeypatch,
) -> None:
    """The honest-negative is a first-class AC-satisfying outcome: it
    is DEFINITE (not could-not-determine) and evidence-backed exactly
    as a successful refinement is — the bar is honest, not gamed."""

    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        if "List ONLY" in prompt:
            return {"result": "How?"}
        if "Ask ONLY" in prompt:
            return {"result": "What?"}
        return {"result": "irreducible, nothing measurable"}

    monkeypatch.setattr(I, "_claude_json", fake)
    out = I.derive_acceptance_from_intent(
        intent="give my life purpose",
        under_specification=["philosophically irreducible"],
        approval_fn=lambda p: True,
        elicit_answer_fn=lambda q: "no idea",
        run_model=True,
    )
    ev = out.as_evidence()
    # definite (a named refinement_outcome, a non-empty reason) — the
    # outcome is reportable straight, not an indeterminate failure.
    assert ev["refinement_outcome"] == "honest-negative"
    assert ev["faithfulness_reason"].strip()
    assert ev["refinement_attempts"] >= 1
