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

"""AC.RPB.5 — the "materially beats" margin is pre-declared, computed
not asserted, with a NON-DEGENERATE denominator: the FROZEN-RATIFIED
D-PBR-1 margin + the NEW frozen k_min>=2 small-k floor that FORCES
verdict (c) indeterminate on a < k_min baseline-miss denominator (the
named v2 task-#44 / PB3 degenerate-denominator defect fix, D-RPB-1).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
REALPB = ROOT / "framework" / "tools" / "programbench-revival" / "realpb"
sys.path.insert(0, str(REALPB / "src"))


def _disp(tid, arm, passed, fc=""):
    from programbench_revival_realpb.verdict import (
        RealPBArmDisposition,
    )

    return RealPBArmDisposition(
        task_id=tid, instance_id=tid, arm=arm, passed=passed,
        judge_tag="FAITHFUL" if passed else "CHECKABLE-BUT-WRONG",
        judge_reason="x", upstream_score=0.5 if passed else 0.0,
        upstream_n_resolved=1, upstream_n_tests=2,
        upstream_error_code=None, floor_theta=0.1,
        held_out_clean=True, failure_class=fc, cost_usd=0.1,
        agent_wall_clock_s=1.0, eval_emulation_wall_clock_s=1.0,
        transcript_path="t", eval_json_path="e",
    )


def test_AC_RPB_5_kmin_forces_indeterminate_on_degenerate() -> None:
    """THE NAMED v2 TASK-#44 DEFECT FIX: a baseline-miss denominator
    < k_min (k_min>=2) is FORCED to (c) indeterminate with the
    machine-stated reason — NOT a determinate loss/win. v2's rule
    forced indeterminate only at EXACTLY 0; this forces at < k_min."""
    from programbench_revival_realpb.verdict import (
        compute_realpb_verdict,
    )

    # exactly 1 baseline miss (< k_min=2) — the v2 task-#44 shape
    b = [_disp("t1", "baseline", True),
         _disp("t2", "baseline", True),
         _disp("t3", "baseline", True),
         _disp("t4", "baseline", True),
         _disp("t5", "baseline", False, "produced-but-wrong")]
    lo = [_disp(f"t{i}", "loam", True) for i in range(1, 6)]
    v = compute_realpb_verdict(b, lo, k_min=2)
    assert v.verdict == "indeterminate"
    assert v.baseline_miss_count == 1
    assert v.baseline_miss_below_k_min is True
    assert "baseline-miss-denominator < k_min" in v.reason
    assert "task-#44" in v.reason  # named, not silent

    # 0 baseline misses is also < k_min => indeterminate
    b0 = [_disp(f"t{i}", "baseline", True) for i in range(5)]
    l0 = [_disp(f"t{i}", "loam", True) for i in range(5)]
    assert compute_realpb_verdict(
        b0, l0, k_min=2).verdict == "indeterminate"


def test_AC_RPB_5_margin_computed_not_asserted_three_valued() -> None:
    from programbench_revival_realpb.verdict import (
        THREE_VALUED,
        compute_realpb_verdict,
    )

    # >= k_min baseline misses, loam recovers a clear majority
    # (>50%), no total regression => (a) materially beats — COMPUTED
    b = [_disp("t1", "baseline", True)] + [
        _disp(f"t{i}", "baseline", False, "produced-but-no-real-"
              "effect") for i in range(2, 6)]
    lo = [_disp("t1", "loam", True)] + [
        _disp(f"t{i}", "loam", True) for i in range(2, 5)] + [
        _disp("t5", "loam", False, "produced-but-wrong")]
    v = compute_realpb_verdict(b, lo, k_min=2)
    assert v.verdict == "loam-materially-beats-baseline"
    assert v.verdict in THREE_VALUED
    assert v.clear_majority_cleared is True
    assert v.no_total_regression is True

    # loam recovers a minority => (b) does NOT materially beat
    # (first-class plan-success polarity, reported straight)
    lo2 = [_disp("t1", "loam", True), _disp("t2", "loam", True)] + [
        _disp(f"t{i}", "loam", False, "produced-but-no-real-effect")
        for i in range(3, 6)]
    v2 = compute_realpb_verdict(b, lo2, k_min=2)
    assert v2.verdict == "loam-does-not-materially-beat-baseline"
    assert "FIRST-CLASS plan-success outcome" in v2.reason
    assert "NOT retried to green" in v2.reason

    # the FROZEN-RATIFIED margin text + the aspirational-NOT-the-gate
    # label are present and the k_min floor is in the margin text
    assert "CLEAR MAJORITY" in v.margin_text
    assert "k_min >= 2" in v.margin_text
    assert "EXPLICITLY NOT the gate" in v.margin_text
    assert "NOT the real-PB pass/fail gate" in \
        v.all_tasks_pass_aspirational["note"]


def test_AC_RPB_5_kmin_below_2_rejected() -> None:
    from programbench_revival_realpb.verdict import (
        compute_realpb_verdict,
    )

    with pytest.raises(ValueError, match="k_min must be >= 2"):
        compute_realpb_verdict([], [], k_min=1)
