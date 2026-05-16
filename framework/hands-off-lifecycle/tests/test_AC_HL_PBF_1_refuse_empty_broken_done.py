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

"""AC.PBF.1 — refuse an empty/broken 'done' BEFORE the approval gate.

Plan: pos3 phase-b-fix-plan-2026-05-16.md §4 AC.PBF.1
Evidence base: phase-b-hardening-2026-05-16.md I2 (broken JSON ->
empty check, approved=True) + I7 (empty plain, approved=True) — the
FAILED-TO-DERIVE-via-format-fragility-plus-rubber-stamp pattern.

Outcome under test (not method): when the derived plain "done" is
empty/whitespace-only, OR the machine check command is empty, OR the
machine-checkable JSON failed to parse, the intake produces a
definite, evidence-carrying refusal (a non-approved outcome with a
recorded reason) surfaced BEFORE the approval gate can return true —
never a silent approved=True on empty/garbage. Satisfiable by a
pre-gate guard / derive-retry-then-refuse / structured-output
contract — multiple methods; scope is tight, method is not asserted.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop import intake as I  # noqa: E402


@pytest.fixture
def approval_recorder():
    calls: list[str] = []

    def approve(plain: str) -> bool:
        calls.append(plain)
        return True

    return approve, calls


def _patch_claude(monkeypatch, derive_body: str) -> None:
    """Stub the real claude subprocess: a bounded elicit, then the
    exact broken derive body the hardening run observed."""

    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        if "List ONLY the few missing" in prompt:        # elicit leg
            return {"result": "How often?\nWhere should it live?"}
        return {"result": derive_body}                   # derive leg

    monkeypatch.setattr(I, "_claude_json", fake)


def test_AC_PBF_1_empty_plain_done_refused_before_approval(
    monkeypatch, approval_recorder
) -> None:
    """I7 shape: the model put everything on the JSON side, the plain
    part is empty. The outcome must be a refusal, NOT approved=True,
    and the approval gate must never be reached."""
    approve, calls = approval_recorder
    _patch_claude(
        monkeypatch,
        '---\n{"check_command": "echo ok", "spec": "x"}',
    )
    out = I.derive_acceptance_from_intent(
        intent="set something up so I actually work out more",
        under_specification=["ambiguous success"],
        approval_fn=approve,
        elicit_answer_fn=lambda q: "a plain vague answer",
        run_model=True,
    )
    assert out.approved is False
    assert out.faithful is False
    assert out.faithfulness_reason  # an evidence-carrying reason
    assert "empty" in out.faithfulness_reason.lower()
    # surfaced BEFORE the gate — the approval fn was never consulted.
    assert calls == []


def test_AC_PBF_1_broken_json_empty_check_refused(
    monkeypatch, approval_recorder
) -> None:
    """I2 shape: the `---` split broke, JSON parse failed, the check
    command is empty. Must refuse, not approve a poisoned contract."""
    approve, calls = approval_recorder
    _patch_claude(
        monkeypatch,
        "Routine is live. Here is the required output:",
    )
    out = I.derive_acceptance_from_intent(
        intent="make sure my photos are safe",
        under_specification=["implicit constraints"],
        approval_fn=approve,
        elicit_answer_fn=lambda q: "all of them I guess",
        run_model=True,
    )
    assert out.approved is False
    assert out.faithful is False
    assert "check command is empty" in out.faithfulness_reason.lower()
    assert calls == []


def test_AC_PBF_1_unparsed_machine_checkable_refused(
    monkeypatch, approval_recorder
) -> None:
    """The JSON side is present but unparseable garbage. The
    _parse_failed marker must drive a refusal, not an approval."""
    approve, calls = approval_recorder
    _patch_claude(
        monkeypatch,
        "Done when your photos are safe.\n---\n{not valid json at all",
    )
    out = I.derive_acceptance_from_intent(
        intent="keep my photos safe",
        under_specification=["x"],
        approval_fn=approve,
        elicit_answer_fn=lambda q: "a",
        run_model=True,
    )
    assert out.approved is False
    assert out.faithful is False
    assert "parse" in out.faithfulness_reason.lower()
    assert calls == []


def test_AC_PBF_1_well_formed_derive_still_reaches_approval(
    monkeypatch, approval_recorder
) -> None:
    """The refusal is targeted: a well-formed plain done + non-empty
    check command must still pass the gate (no over-refusal). This
    proves the guard does not regress the healthy path."""
    approve, calls = approval_recorder

    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        if "List ONLY the few missing" in prompt:
            return {"result": "Which recipes?\nWhere stored?"}
        if "Produce TWO things" in prompt:
            return {
                "result": (
                    "Done when your recipes are saved and you can "
                    "search them later.\n---\n"
                    '{"check_command": "test -s recipes.db", '
                    '"spec": "recipes persisted + searchable"}'
                )
            }
        if "Adversarial faithfulness check" in prompt:
            return {"result": '{"faithful": true, "reason": "ok"}'}
        return {"result": ""}

    monkeypatch.setattr(I, "_claude_json", fake)
    out = I.derive_acceptance_from_intent(
        intent="help me keep track of my recipes",
        under_specification=["missing scope"],
        approval_fn=approve,
        elicit_answer_fn=lambda q: "a",
        run_model=True,
    )
    assert out.approved is True
    assert calls and calls[0]  # the gate WAS reached with real text
