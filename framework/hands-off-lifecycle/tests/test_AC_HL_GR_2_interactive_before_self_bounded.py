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

"""AC.GR.2 — interactive-refine BEFORE self-refine, both bounded, the
durable elicitation leg NOT regressed.

Plan: pos3 loop-goal-refinement-plan-2026-05-16.md §4 AC.GR.2 + D-GR-2
Binding foundation: the owner steer prefers interactive-refine *first*;
self-refine is the degrade when no live user is reachable.
Evidence base: phase-b-hardening-2026-05-16.md "What worked" — the
elicit-the-minimum leg stayed bounded (3-4 plain Qs) across all 7
intents; that durable AC.B.2 property must survive refinement.

Outcome under test (not method): refinement attempts an INTERACTIVE
clarification first (the existing bounded elicitation primitive,
re-scoped to the measurability gap — plain questions, hard-capped, no
spec interview) and only SELF-refines (model derives without further
user input) when interactive input is unavailable.  The total
user-facing question count across original elicitation +
interactive-refine stays bounded (the user is never turned into a
spec author).  A healthy intent's original elicitation behaviour is
unchanged (no regression of the durable leg).

Method-independence: satisfiable by reusing the elicit fn with a
refinement-scoped prompt + a question budget, by a separate bounded
clarify routine, or by a single re-elicit — the test asserts
interactive-first + bounded + elicitation-not-regressed, never the
question-routing mechanism.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop import intake as I  # noqa: E402

_REFINED_OK = (
    "Done when all photos are verifiably uploaded.\n---\n"
    '{"check_command": "python3 verify.py --n 20000", '
    '"spec": "real upload check", "is_milestone": false, '
    '"milestone_toward": ""}'
)


def _stub(monkeypatch, prompts_seen, *, derive_body):
    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        prompts_seen.append(prompt)
        if "List ONLY the few missing" in prompt:
            return {"result": "How?\nWhere?"}
        if "Ask ONLY the few plain questions" in prompt:
            # the interactive measurability-gap elicitation.
            return {"result": "What counts as done?\nHow many?"}
        if "Re-derive a FAITHFUL" in prompt:
            return {"result": _REFINED_OK}
        if "Produce TWO things" in prompt:
            return {"result": derive_body}
        if "Adversarial faithfulness check" in prompt:
            return {"result": '{"faithful": true, "reason": "ok"}'}
        return {"result": ""}

    monkeypatch.setattr(I, "_claude_json", fake)


def test_AC_GR_2_interactive_refine_attempted_first_when_user_present(
    monkeypatch,
) -> None:
    """A live user (elicit_answer_fn provided) -> the refinement asks
    a measurability-gap clarification BEFORE self-deriving; the
    answers are routed back into the re-derive."""
    prompts: list[str] = []
    answered: list[str] = []

    def elicit(q: str) -> str:
        answered.append(q)
        return "a short plain answer"

    _stub(monkeypatch, prompts, derive_body="broken, no ---")
    out = I.derive_acceptance_from_intent(
        intent="make sure my photos are safe",
        under_specification=["x"],
        approval_fn=lambda p: True,
        elicit_answer_fn=elicit,
        run_model=True,
    )
    # the interactive measurability-gap prompt was issued AND answered
    # via the existing elicit callback (interactive-FIRST).
    assert any("Ask ONLY the few plain questions" in p for p in prompts)
    assert answered, "the live user's elicit callback was consulted"
    assert out.refinement_outcome == "interactive"
    assert out.approved is True and out.faithful is True


def test_AC_GR_2_self_refine_when_no_live_user(monkeypatch) -> None:
    """No live user (elicit_answer_fn is None — the hands-off 'just
    go' case) -> the construct SELF-refines (no interactive gap
    elicitation issued) and degrades cleanly."""
    prompts: list[str] = []
    _stub(monkeypatch, prompts, derive_body="broken, no ---")
    out = I.derive_acceptance_from_intent(
        intent="make sure my photos are safe",
        under_specification=["x"],
        approval_fn=lambda p: True,
        elicit_answer_fn=None,           # hands-off: no live user
        run_model=True,
    )
    # no interactive measurability-gap elicitation was issued.
    assert not any(
        "Ask ONLY the few plain questions" in p for p in prompts
    )
    assert out.refinement_outcome == "self"
    assert out.approved is True and out.faithful is True


def test_AC_GR_2_total_question_count_stays_bounded(monkeypatch) -> None:
    """The user is NEVER turned into a spec author: original
    elicitation (cap 4) + interactive-refine (cap 3) is bounded; the
    elicitation primitive is reused, not unbounded."""
    prompts: list[str] = []
    asked: list[str] = []
    _stub(monkeypatch, prompts, derive_body="broken, no ---")
    I.derive_acceptance_from_intent(
        intent="make sure my photos are safe",
        under_specification=["x"],
        approval_fn=lambda p: True,
        elicit_answer_fn=lambda q: asked.append(q) or "a",
        run_model=True,
    )
    # original elicit returned 2, refine-elicit returned 2 here; the
    # structural caps are 4 + 3 = 7. The total must stay <= that bound
    # (never an unbounded spec interview).
    assert 0 < len(asked) <= 7


def test_AC_GR_2_healthy_intent_elicitation_unchanged(
    monkeypatch,
) -> None:
    """No regression of the durable leg: a HEALTHY derive never enters
    refinement, so original elicitation behaviour is byte-identical to
    the sealed path (no refinement-driven extra questions)."""
    prompts: list[str] = []
    asked: list[str] = []

    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        prompts.append(prompt)
        if "List ONLY the few missing" in prompt:
            return {"result": "Which photos?\nWhat does safe mean?"}
        if "Produce TWO things" in prompt:
            return {"result": _REFINED_OK}
        if "Adversarial faithfulness check" in prompt:
            return {"result": '{"faithful": true, "reason": "ok"}'}
        return {"result": ""}

    monkeypatch.setattr(I, "_claude_json", fake)
    out = I.derive_acceptance_from_intent(
        intent="make sure my photos are safe",
        under_specification=["x"],
        approval_fn=lambda p: True,
        elicit_answer_fn=lambda q: asked.append(q) or "a",
        run_model=True,
    )
    # healthy derive -> NO refinement -> NO measurability-gap elicit.
    assert out.refinement_outcome == "none"
    assert out.refinement_attempts == 0
    assert not any(
        "Ask ONLY the few plain questions" in p for p in prompts
    )
    assert 0 < len(asked) <= 4          # the durable AC.B.2 bound
    assert out.approved is True and out.faithful is True
