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

"""AC.A.4 — Phase A end-test: packaged-skill orchestration fidelity.

Plan: docs/plans/handsoff-loop-real-build.md (§3 AC.A.4, §4)

The §10.5 honest end-test. A frozen, pre-authored, sub-agent-unseen
acceptance on a REAL task of probe-class-or-harder is run THROUGH the
packaged mechanism with NO human driving the loop; the result is a
per-dimension verdict table with evidence for:

  (i)   reached frozen done without human loop-driving
  (ii)  no silent regression across composed sub-tasks
  (iii) honest-negative reporting still fires when a sub-task can't
        be done
  (iv)  cost/wall-clock within the stated band ($2-8 / <=20 min,
        MEASURED via --output-format json — D-COST-BAND)

The end-test PASSES AS A PLAN-DELIVERABLE when the table is DEFINITE
and evidence-backed — regardless of polarity.  A definite
"fidelity NOT achieved — packaged mechanism materially worse than
hand-run, here is the dimension + evidence" is a valid plan-success
outcome (§10.5), reported straight, NEVER retried to green.

This is real-claude-driven (minutes of sub-agent wall-clock) and is
the DISPATCHER-OWNED end-test (own-the-wait): it is gated behind
HANDSOFF_RUN_PHASE_A=1 so the deterministic seal sweep collects but
SKIPS it (mirrors the subloam-driver-fix honest-end-test precedent
where the real-binary end-test is run explicitly, not in CI).  The
dispatcher runs it explicitly to a definite verdict and captures the
table; AC.FOUND.0 is honoured — the task is a FRESH probe-class task,
NOT a re-run of the §6 probe.
"""

from __future__ import annotations

import os

import pytest

PHASE_A_GATE = os.environ.get("HANDSOFF_RUN_PHASE_A") == "1"


@pytest.mark.skipif(
    not PHASE_A_GATE,
    reason=(
        "AC.A.4 is the real-claude-driven Phase A honest end-test; run "
        "explicitly by the dispatcher with HANDSOFF_RUN_PHASE_A=1 "
        "(own-the-wait). The deterministic seal sweep skips it by "
        "design — the verdict table is captured to the build report, "
        "not gated in CI (subloam-driver-fix precedent)."
    ),
)
def test_AC_A4_phase_a_fidelity_verdict_is_definite() -> None:
    """Drive the packaged loop on a fresh probe-class task; assert the
    per-dimension verdict table is DEFINITE + evidence-backed (either
    polarity is plan-success; no retry-to-green path exists)."""
    from handsoff_loop_phase_a_runner import run_phase_a  # type: ignore

    verdict = run_phase_a()
    table = verdict.as_table()

    # The AC is satisfied by a DEFINITE, evidence-backed table for
    # EITHER polarity — there is deliberately no `polarity == positive`
    # assertion here (that would be the build-and-assume failure the
    # objective forbids).
    assert table["definite"] is True, (
        "Phase A end-test must produce a DEFINITE verdict (a "
        "could-not-determine is the only real failure of this AC)"
    )
    assert table["passed_as_deliverable"] is True, (
        "every named dimension must carry evidence (D-NEG-DEPTH: "
        "class + evidence; not root-cause)"
    )
    for dim in ("reached_frozen_done_no_human_driving",
                "no_silent_regression",
                "honest_negative_fires",
                "cost_wallclock_in_band"):
        assert dim in table["dimensions"], (
            f"AC.A.4 requires named dimension {dim!r}"
        )
        assert table["dimensions"][dim]["evidence"].strip(), (
            f"dimension {dim!r} must be evidence-backed"
        )
