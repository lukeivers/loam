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

"""AC.B.1 / AC.B.2 / AC.B.3 / AC.B.4 — intake leg structure.

Plan: docs/plans/handsoff-loop-real-build.md (§3 AC.B.1..B.4)

  AC.B.1 — fuzzy-intent input (under-specified plain language; the
           under-specification is documented).
  AC.B.2 — elicit-the-minimum (only the missing decisions, bounded —
           the user is NOT turned into a spec author).
  AC.B.3 — plain-language acceptance + EXACTLY ONE plain-English
           approval gate; no jargon/AC-IDs/spec-syntax surfaced.
  AC.B.4 — derived-done machine-checkable AND faithful (an
           independent check guards checkable-but-WRONG).

Deterministic structural path (`run_model=False`) — the real
intent->done run with a real faithfulness judge is the AC.B.5 phase
end-test.  Each AC is satisfiable by more than one method (question-
elicitation / default-and-confirm / example-driven; plan-mode /
custom-confirm; independent-judge / round-trip) — scope is tight.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop.intake import (  # noqa: E402
    assert_plain_language,
    derive_acceptance_from_intent,
)

FUZZY_INTENT = "make me a thing that reads my csv and tells me totals"
UNDER_SPEC = [
    "did not say the file path or name",
    "did not say which columns or what 'totals' means",
    "did not say where the result should go",
    "gave no acceptance criteria, no spec",
]


def _approve(_plain: str) -> bool:
    return True


def test_B1_fuzzy_intent_and_under_spec_documented() -> None:
    """AC.B.1: a genuinely under-specified plain-language intent, with
    the under-specification recorded (what the user did NOT say)."""
    outcome = derive_acceptance_from_intent(
        intent=FUZZY_INTENT,
        under_specification=UNDER_SPEC,
        approval_fn=_approve,
        run_model=False,
    )
    assert outcome.original_intent == FUZZY_INTENT
    assert outcome.under_specification == UNDER_SPEC
    # The input is genuinely under-specified (no acceptance/spec).
    assert "acceptance" not in FUZZY_INTENT.lower()


def test_B2_elicitation_is_bounded() -> None:
    """AC.B.2: elicitation asks only a few missing decisions, bounded.

    The hard cap is structural: at most 4 questions (the deterministic
    path returns 2).  This is "elicit the minimum", not a spec
    interview that turns the user into a requirements author.
    """
    outcome = derive_acceptance_from_intent(
        intent=FUZZY_INTENT, under_specification=UNDER_SPEC,
        approval_fn=_approve, run_model=False,
    )
    assert 0 < len(outcome.elicited_questions) <= 4, (
        "elicit-the-minimum is bounded (<=4) so the user is not "
        "turned into a spec author"
    )


def test_B3_exactly_one_plain_language_approval_no_jargon() -> None:
    """AC.B.3: exactly ONE plain-English approval; no jargon surfaced.

    The approval gate is called exactly once, and the text it is
    shown carries no AC-IDs / pytest / exit-code / seal / ODD jargon.
    """
    calls: list[str] = []

    def approve_once(plain: str) -> bool:
        calls.append(plain)
        return True

    outcome = derive_acceptance_from_intent(
        intent=FUZZY_INTENT, under_specification=UNDER_SPEC,
        approval_fn=approve_once, run_model=False,
    )
    assert len(calls) == 1, "exactly ONE approval gate (AC.B.3)"
    assert outcome.approved is True
    # The user-facing acceptance is plain English.
    assert_plain_language(outcome.plain_language_acceptance)  # no raise


def test_B3_jargon_in_user_facing_acceptance_is_rejected() -> None:
    """AC.B.3 guard fires: jargon in the plain acceptance is refused."""
    with pytest.raises(ValueError):
        assert_plain_language(
            "Done when AC.B.4 passes and pytest exit code is 0"
        )


def test_B4_derived_done_is_machine_checkable_and_faithfulness_tracked() -> None:
    """AC.B.4: the derived done is machine-checkable AND a faithfulness
    verdict is carried (the independent check that guards
    checkable-but-wrong; real judge runs in the AC.B.5 end-test)."""
    outcome = derive_acceptance_from_intent(
        intent=FUZZY_INTENT, under_specification=UNDER_SPEC,
        approval_fn=_approve, run_model=False,
    )
    # (a) machine-checkable form exists (a check command).
    assert "check_command" in outcome.machine_checkable
    assert outcome.machine_checkable["check_command"]
    # (b) faithfulness is a tracked, reasoned verdict (either polarity
    #     valid; real adversarial judge runs in AC.B.5).
    assert isinstance(outcome.faithful, bool)
    assert outcome.faithfulness_reason
