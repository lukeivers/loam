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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.MGRL.3 — on an escalated turn the deliberate loop yields the revised
answer ONLY when critique produced an evidence-backed improvement, else the
original draft (the no-degradation guard, D-MGRL.2).

Four cases pin the guard, with a deterministic (LLM-free) critic so the
guard itself is what is verified:

1. Draft already correct, critic finds no defect -> original returned.
2. Draft has a checkable defect, critic cites evidence + a revision ->
   corrected answer returned.
3. Critic claims an improvement but cites NO evidence -> guard rejects it,
   original returned (the anti-confabulation defence).
4. Critic claims an improvement + evidence but proposes no revised answer
   -> guard rejects, original returned.
"""

from __future__ import annotations

from loam.deliberate_reasoning.loop import Critique, run_deliberate_loop


def _critic_no_defect(draft, prompt):
    return Critique(
        weakest_link="answer is sound",
        evidence=(),
        revised_answer=None,
        has_defensible_improvement=False,
    )


def _critic_evidence_backed_fix(draft, prompt):
    return Critique(
        weakest_link="step 2 used the wrong operand",
        evidence=("recomputed 17*23 = 391, not 371",),
        revised_answer="391",
        has_defensible_improvement=True,
    )


def _critic_improvement_claim_no_evidence(draft, prompt):
    # Claims an improvement but cites nothing — the confabulation shape.
    return Critique(
        weakest_link="could be phrased better",
        evidence=(),
        revised_answer="something different",
        has_defensible_improvement=True,
    )


def _critic_evidence_but_no_revision(draft, prompt):
    return Critique(
        weakest_link="noted a concern",
        evidence=("some citation",),
        revised_answer=None,
        has_defensible_improvement=True,
    )


def test_AC_MGRL_3_correct_draft_no_defect_returns_original():
    res = run_deliberate_loop("371", "What is 17*23?", _critic_no_defect)
    assert res.revised is False
    assert res.final_answer == "371"


def test_AC_MGRL_3_checkable_defect_returns_corrected_answer():
    res = run_deliberate_loop("371", "What is 17*23?", _critic_evidence_backed_fix)
    assert res.revised is True
    assert res.final_answer == "391"


def test_AC_MGRL_3_improvement_claim_without_evidence_is_rejected():
    res = run_deliberate_loop("371", "What is 17*23?", _critic_improvement_claim_no_evidence)
    assert res.revised is False
    assert res.final_answer == "371"  # original kept — no evidence => no degradation


def test_AC_MGRL_3_evidence_but_no_revision_keeps_original():
    res = run_deliberate_loop("371", "What is 17*23?", _critic_evidence_but_no_revision)
    assert res.revised is False
    assert res.final_answer == "371"
