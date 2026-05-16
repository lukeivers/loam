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

"""AC.PBR.5 — the "materially beats" margin is pre-declared and the
answer is a computed number, not a vibe (FROZEN-RATIFIED D-PBR-1).

Outcome under test (not method): a pre-declared decision rule maps
the two arms' independently-judged pass profiles to EXACTLY THREE
definite verdicts; the verdict is COMPUTED from the numbers; the
honest-negative ("loam does not materially beat") is a first-class
polarity; the all-tasks-pass metric is reported but is NOT the gate;
the frozen margin is the clear-majority-of-baseline-misses-recovered
AND no-total-regression conjunction.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PBR = ROOT / "framework" / "tools" / "programbench-revival"
sys.path.insert(0, str(PBR / "src"))


def _disp(task_id, arm, passed):
    from programbench_revival.verdict import ArmTaskDisposition

    return ArmTaskDisposition(
        task_id=task_id, arm=arm, passed=passed,
        judge_tag="FAITHFUL" if passed else "CHECKABLE-BUT-WRONG",
        judge_reason="x", floor_exit=0 if passed else 1,
        held_out_exit=0 if passed else 1,
        failure_class="" if passed else "produced-but-no-real-effect",
        cost_usd=0.01, wall_clock_s=1.0, transcript_path="t",
        check_command="c",
    )


def test_AC_PBR_5_exactly_three_verdicts() -> None:
    from programbench_revival.verdict import THREE_VALUED

    assert set(THREE_VALUED) == {
        "loam-materially-beats-baseline",
        "loam-does-not-materially-beat-baseline",
        "indeterminate",
    }


def test_AC_PBR_5_material_beat_is_computed() -> None:
    """Baseline misses 4 of 6; loam recovers a clear majority (3/4 >
    50%) AND does not regress total -> computed material beat."""
    from programbench_revival import compute_verdict

    ids = [f"T{i}" for i in range(6)]
    baseline = [_disp(ids[i], "baseline", i < 2) for i in range(6)]
    # loam passes T0,T1 (no regression) + recovers T2,T3,T4 (3/4 of
    # the 4 baseline misses {T2,T3,T4,T5})
    loam = [_disp(ids[i], "loam", i < 5) for i in range(6)]
    v = compute_verdict(baseline, loam)
    assert v.verdict == "loam-materially-beats-baseline"
    assert v.clear_majority_cleared is True
    assert v.no_total_regression is True


def test_AC_PBR_5_no_material_beat_is_first_class() -> None:
    """Loam recovers only a minority of baseline misses -> the
    honest-negative polarity, computed and reported straight."""
    from programbench_revival import compute_verdict

    ids = [f"T{i}" for i in range(6)]
    baseline = [_disp(ids[i], "baseline", i < 2) for i in range(6)]
    # loam keeps T0,T1, recovers only T2 (1/4 of the baseline misses)
    loam = [_disp(ids[i], "loam", i < 3) for i in range(6)]
    v = compute_verdict(baseline, loam)
    assert v.verdict == "loam-does-not-materially-beat-baseline"
    assert v.clear_majority_cleared is False
    assert "FIRST-CLASS plan-success" in v.reason


def test_AC_PBR_5_indeterminate_when_no_baseline_misses() -> None:
    """Baseline passes everything -> no baseline-miss subset ->
    INDETERMINATE, a definite reportable finding naming why."""
    from programbench_revival import compute_verdict

    ids = [f"T{i}" for i in range(6)]
    baseline = [_disp(ids[i], "baseline", True) for i in range(6)]
    loam = [_disp(ids[i], "loam", True) for i in range(6)]
    v = compute_verdict(baseline, loam)
    assert v.verdict == "indeterminate"
    assert "0 independently-judged non-passes" in v.reason


def test_AC_PBR_5_all_tasks_pass_is_reported_not_the_gate() -> None:
    from programbench_revival import compute_verdict

    ids = [f"T{i}" for i in range(6)]
    baseline = [_disp(ids[i], "baseline", i < 2) for i in range(6)]
    loam = [_disp(ids[i], "loam", i < 5) for i in range(6)]
    v = compute_verdict(baseline, loam)
    asp = v.all_tasks_pass_aspirational
    assert "NOT the v2 pass/fail gate" in asp["note"]
    assert "baseline_all_tasks_pass" in asp
    assert "loam_all_tasks_pass" in asp


def test_AC_PBR_5_margin_text_frozen_ratified() -> None:
    """The FROZEN-RATIFIED D-PBR-1 margin text is pinned in code
    (frozen before any run; not moved after)."""
    from programbench_revival.verdict import FROZEN_MARGIN_TEXT

    assert "CLEAR MAJORITY" in FROZEN_MARGIN_TEXT
    assert "does NOT regress" in FROZEN_MARGIN_TEXT
    assert "ASPIRATIONAL" in FROZEN_MARGIN_TEXT
    assert "NOT the gate" in FROZEN_MARGIN_TEXT
