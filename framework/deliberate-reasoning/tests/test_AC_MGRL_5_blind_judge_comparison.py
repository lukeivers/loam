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

"""AC.MGRL.5 — the experiment compares escalated vs. baseline on the fixed
task set, scored by a judge BLIND to the hypothesis, against objective
pre-registered criteria; the judge's inputs demonstrably exclude any
hypothesis/arm labelling.

The blindness is structural: ``score_answer``'s signature is
``(prompt, answer, canonical_answer)`` — there is no parameter through which
the arm label could enter. This test pins (a) the signature carries no arm
parameter and (b) a full baseline-vs-escalated run produces per-arm scores
from the blind judge.
"""

from __future__ import annotations

import inspect

from judge import score_answer
from runner import reference_critic, load_task_set, run_experiment


def test_AC_MGRL_5_judge_signature_excludes_any_arm_or_hypothesis_label():
    params = list(inspect.signature(score_answer).parameters)
    assert params == ["prompt", "answer", "canonical_answer"]
    # No arm / hypothesis / trigger parameter exists for a label to enter.
    for forbidden in ("arm", "hypothesis", "trigger", "escalated", "baseline"):
        assert forbidden not in params


def test_AC_MGRL_5_blind_judge_scores_identically_regardless_of_arm():
    # The same answer text scores identically no matter which arm produced
    # it — there is no arm channel to influence the score.
    s1 = score_answer("q", "Canberra", "canberra")
    s2 = score_answer("q", "Canberra", "canberra")
    assert s1 == s2 == 1
    assert score_answer("q", "Sydney", "canberra") == 0


def test_AC_MGRL_5_run_produces_per_arm_blind_scores():
    items = load_task_set()
    answer_key = {it["id"]: it["canonical_answer"] for it in items}

    def _baseline(item):
        # Flawed draft on flagged items, correct on controls.
        if item["trigger_intended"] == "none":
            return item["canonical_answer"]
        return "WRONG-PLACEHOLDER"

    res = run_experiment(
        baseline_answer_for=_baseline,
        critic_factory=reference_critic(answer_key),
    )
    # The run produces totals for both arms from the blind judge.
    assert res.baseline_correct_total >= 0
    assert res.escalated_correct_total >= res.baseline_correct_total
    assert len(res.per_item) == len(items)
