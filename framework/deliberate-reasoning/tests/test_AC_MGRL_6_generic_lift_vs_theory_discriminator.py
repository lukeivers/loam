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

"""AC.MGRL.6 — the experiment reports SEPARATELY (a) the aggregate quality
delta (generic lift) and (b) the theory-prediction discriminator (whether
the gain concentrates on gate-flagged turns rather than generic difficulty);
"the theory's prediction held" is a DISTINCT verdict from "escalation helped
on average."

Two scenarios pin the distinction:

1. Gain concentrates on flagged turns, none on unflagged, no regression ->
   verdict THEORY-PREDICTION-CONFIRMED, distinct from the aggregate delta.
2. The result object exposes the aggregate delta AND the flagged/unflagged
   breakdown as separate fields — the report cannot collapse them.
"""

from __future__ import annotations

from runner import reference_critic, load_task_set, run_experiment


def _run_with_flawed_flagged_drafts():
    items = load_task_set()
    answer_key = {it["id"]: it["canonical_answer"] for it in items}

    def _baseline(item):
        if item["trigger_intended"] == "none":
            return item["canonical_answer"]  # controls correct at baseline
        return "WRONG-PLACEHOLDER"  # flagged items wrong at baseline

    return run_experiment(
        baseline_answer_for=_baseline,
        critic_factory=reference_critic(answer_key),
    )


def test_AC_MGRL_6_aggregate_delta_and_discriminator_are_separate_fields():
    res = _run_with_flawed_flagged_drafts()
    # Aggregate generic-lift delta is its own reported field.
    assert hasattr(res, "aggregate_delta")
    # The discriminator is reported as its own separate breakdown.
    assert hasattr(res, "gain_on_flagged")
    assert hasattr(res, "gain_on_unflagged")
    # The verdict is a DISTINCT field from the aggregate delta.
    assert hasattr(res, "verdict")


def test_AC_MGRL_6_theory_verdict_distinct_from_helped_on_average():
    res = _run_with_flawed_flagged_drafts()
    # The aggregate delta says escalation "helped on average".
    assert res.aggregate_delta > 0
    # The discriminator says the gain concentrated on flagged turns and was
    # absent on unflagged turns — the theory's specific prediction.
    assert res.gain_on_flagged > 0
    assert res.gain_on_unflagged == 0
    assert res.regressions == 0
    # These two facts are reported separately and the verdict reflects the
    # discriminator, not merely the aggregate delta.
    assert res.verdict == "THEORY-PREDICTION-CONFIRMED"


def test_AC_MGRL_6_generic_lift_does_not_auto_confirm_theory():
    # If gain bled onto unflagged turns (a default-OFF breach), the verdict
    # must NOT be CONFIRMED even though the aggregate delta is positive —
    # generic lift alone never confirms the theory.
    from runner import _verdict
    assert _verdict(gain_flagged=2, gain_unflagged=1, regressions=0) == "INVALID-DEFAULT-OFF-BREACH"
    assert _verdict(gain_flagged=0, gain_unflagged=0, regressions=0) == "NULL"
