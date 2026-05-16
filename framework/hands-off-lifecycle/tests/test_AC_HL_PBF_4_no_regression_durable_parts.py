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

"""AC.PBF.4 — the fix does not regress the parts the hardening test
proved durable.

Plan: pos3 phase-b-fix-plan-2026-05-16.md §4 AC.PBF.4
Evidence base: phase-b-hardening-2026-05-16.md "What worked" — the
elicit-the-minimum leg stayed bounded across all 7 intents; the single
plain-language approval gate stayed exactly one; genuine jargon was
still refused.

Outcome under test: after the three fixes, (1) elicitation stays
bounded (<=4 plain questions, AC.B.2), (2) the plain-language approval
gate stays exactly one on a healthy derive (AC.B.3), (3) genuine
jargon is still refused (AC.B.3 guard still fires on real AC-IDs /
pytest / exit code), and (4) the pre-existing deterministic
`test_AC_HL_B1_B4_intake_structure.py` invariants still hold (adjusted
ONLY where a fix legitimately tightens behaviour — recorded as a
fix-driven tightening, never a loosening to pass a broken test).
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


def _healthy_claude(monkeypatch):
    """A well-formed real-path stub: bounded elicit, well-formed
    derive, faithful judge — the I1/I4/I5 'durable' shape."""
    from handsoff_loop import intake as I

    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        if "List ONLY the few missing" in prompt:
            # 4 questions — at the AC.B.2 cap, must stay bounded.
            return {"result": "How many?\nWhere stored?\n"
                               "Search by what?\nPrivate or shared?"}
        if "Produce TWO things" in prompt:
            return {
                "result": (
                    "Done when your recipes are saved with their "
                    "ingredients and you can search them later.\n---\n"
                    '{"check_command": "test -s recipes.db", '
                    '"spec": "recipes persisted and keyword-searchable"}'
                )
            }
        if "Adversarial faithfulness check" in prompt:
            return {"result": '{"faithful": true, "reason": "matches"}'}
        return {"result": ""}

    monkeypatch.setattr(I, "_claude_json", fake)


def test_AC_PBF_4_elicitation_stays_bounded(monkeypatch) -> None:
    """AC.B.2 durable: elicitation stays <=4 plain questions even when
    the model offers more — the bound is structural and unaffected."""
    _healthy_claude(monkeypatch)
    out = derive_acceptance_from_intent(
        intent="help me keep track of my recipes so I can find them",
        under_specification=["missing scope"],
        approval_fn=lambda p: True,
        elicit_answer_fn=lambda q: "a short vague answer",
        run_model=True,
    )
    assert 0 < len(out.elicited_questions) <= 4


def test_AC_PBF_4_exactly_one_approval_gate_on_healthy_derive(
    monkeypatch,
) -> None:
    """AC.B.3 durable: a healthy derive still hits the approval gate
    EXACTLY once (the AC.PBF.1 refusal short-circuits ONLY the
    empty/broken path; the healthy path is unchanged)."""
    _healthy_claude(monkeypatch)
    calls: list[str] = []

    def approve(plain: str) -> bool:
        calls.append(plain)
        return True

    out = derive_acceptance_from_intent(
        intent="help me keep track of my recipes",
        under_specification=["missing scope"],
        approval_fn=approve,
        elicit_answer_fn=lambda q: "a",
        run_model=True,
    )
    assert len(calls) == 1
    assert out.approved is True


def test_AC_PBF_4_genuine_jargon_still_refused() -> None:
    """AC.B.3 durable: the guard still fires on real jargon — the
    AC.PBF.3 tightening did not loosen the protection."""
    with pytest.raises(ValueError):
        assert_plain_language(
            "Done when AC.B.4 passes and pytest exit code is 0"
        )
    with pytest.raises(ValueError):
        assert_plain_language("Done when the manifest is sealed")


def test_AC_PBF_4_existing_deterministic_suite_invariants_hold(
) -> None:
    """The pre-existing deterministic structural invariants
    (run_model=False) still hold unchanged — the fixes touch only the
    real-model path's empty/broken + faithfulness-evidence behaviour,
    not the deterministic structural placeholder path."""
    out = derive_acceptance_from_intent(
        intent="make me a thing that reads my csv and tells me totals",
        under_specification=["no path", "no columns", "no destination"],
        approval_fn=lambda p: True,
        run_model=False,
    )
    # AC.B.1 / AC.B.2 / AC.B.3 / AC.B.4 deterministic invariants:
    assert out.original_intent
    assert 0 < len(out.elicited_questions) <= 4
    assert out.approved is True            # healthy placeholder path
    assert out.machine_checkable["check_command"]
    assert isinstance(out.faithful, bool)
    assert out.faithfulness_reason
    # the plain done is still jargon-free under the new guard
    assert_plain_language(out.plain_language_acceptance)
