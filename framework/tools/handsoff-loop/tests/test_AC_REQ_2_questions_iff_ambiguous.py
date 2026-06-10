"""AC.REQ.2 — meaningful questions IFF a build-shaping decision is open.

Both halves binding:

  * when the ask leaves a build-shaping question genuinely open, the
    user gets a BOUNDED number of meaningful plain-language questions
    before the confirm (the bound is structural — a model that
    over-asks is capped, never a spec interview);
  * an unambiguous ask proceeds with ZERO questions.

The live ambiguity discrimination (3/3 seeded-ambiguous asks get >=1
question, 3/3 clear asks get zero) is the S1 measured-prediction
probe, logged in the run evidence; this test pins the structural
contract deterministically.

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.request_intent import (  # noqa: E402
    MAX_MEANINGFUL_QUESTIONS,
    build_confirm_text,
    understand_request,
)


def _llm_with_questions(questions):
    def _fn(prompt, *, model="sonnet", timeout=0):
        return {"result": json.dumps({
            "inferred_intent": "You want the files cleaned up.",
            "objective": "Clean up the files as asked.",
            "questions": questions,
            "form_factor": "cli",
            "form_factor_plain": "A command you run.",
        })}
    return _fn


def test_ambiguous_ask_yields_bounded_meaningful_questions():
    intent = understand_request(
        "sort out our records",
        llm_json_fn=_llm_with_questions(
            ["Which records do you mean — customers or orders?",
             "Where should the result go?"]),
    )
    assert intent.ambiguous is True
    assert 1 <= len(intent.questions) <= MAX_MEANINGFUL_QUESTIONS
    assert "customers or orders" in intent.questions[0]


def test_overasking_model_is_capped_never_a_spec_interview():
    nine = [f"Question number {i}?" for i in range(9)]
    intent = understand_request(
        "sort out our records", llm_json_fn=_llm_with_questions(nine))
    assert len(intent.questions) == MAX_MEANINGFUL_QUESTIONS
    assert MAX_MEANINGFUL_QUESTIONS <= 3  # the named bound stays small


def test_unambiguous_ask_proceeds_with_zero_questions():
    intent = understand_request(
        "dedupe rows in customers.csv by email, keep the newest",
        llm_json_fn=_llm_with_questions([]))
    assert intent.ambiguous is False
    assert intent.questions == []
    # The confirm still surfaces; zero questions does not block it.
    assert "Is that what you want?" in build_confirm_text(intent)


def test_answers_flow_into_the_confirm_surface():
    intent = understand_request(
        "sort out our records",
        llm_json_fn=_llm_with_questions(["Which records?"]))
    confirm = build_confirm_text(
        intent, answers={"Which records?": "the customer list"})
    assert "the customer list" in confirm
