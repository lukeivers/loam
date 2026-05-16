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

"""AC.PBR.6 — cost, latency, per-task evidence, and a per-non-pass
failure class are captured and reproducible.

Outcome under test (not method): every (arm,task) records measured
cost (from --output-format json total_cost_usd, never estimated),
wall-clock, raw transcript, the used check command, the independent
judge verdict+reason; AND every non-pass carries EXACTLY ONE class
from the frozen four-class taxonomy so the verdict is a per-arm
failure-signature map, not only a pass count.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PBR = ROOT / "framework" / "tools" / "programbench-revival"
sys.path.insert(0, str(PBR / "src"))


def test_AC_PBR_6_frozen_four_class_taxonomy() -> None:
    from programbench_revival.verdict import FROZEN_FAILURE_TAXONOMY

    assert FROZEN_FAILURE_TAXONOMY == (
        "did-not-produce-output",
        "produced-but-no-real-effect",
        "produced-but-wrong",
        "honest-negative-refusal",
    )


def test_AC_PBR_6_every_nonpass_maps_to_exactly_one_class() -> None:
    from programbench_revival.verdict import (
        FROZEN_FAILURE_TAXONOMY,
        FailureClass,
        classify_failure,
    )

    # honest refusal -> honest-negative-refusal
    assert classify_failure(
        produced_artifact=False, judge_tag="HONEST-NEGATIVE",
        floor_exit=1, held_out_exit=None,
    ) == "honest-negative-refusal"
    # nothing produced -> did-not-produce-output
    assert classify_failure(
        produced_artifact=False, judge_tag="CHECKABLE-BUT-WRONG",
        floor_exit=1, held_out_exit=None,
    ) == "did-not-produce-output"
    # produced, floor passed but anti-overfit failed (hardcoded/
    # hollow) -> produced-but-no-real-effect (the false-success class)
    assert classify_failure(
        produced_artifact=True, judge_tag="CHECKABLE-BUT-WRONG",
        floor_exit=0, held_out_exit=1,
    ) == "produced-but-no-real-effect"
    # produced a real but wrong effect -> produced-but-wrong
    assert classify_failure(
        produced_artifact=True, judge_tag="INDETERMINATE",
        floor_exit=1, held_out_exit=1,
    ) == "produced-but-wrong"
    # FailureClass refuses an off-taxonomy class
    import pytest

    with pytest.raises(ValueError):
        FailureClass(task_id="T", arm="loam",
                     failure_class="something-else", evidence="e")
    # every produced class is in the frozen taxonomy
    for fc in (classify_failure(produced_artifact=True,
                                judge_tag="CHECKABLE-BUT-WRONG",
                                floor_exit=0, held_out_exit=1),):
        assert fc in FROZEN_FAILURE_TAXONOMY


def test_AC_PBR_6_disposition_record_carries_measured_cost() -> None:
    from programbench_revival.verdict import ArmTaskDisposition

    d = ArmTaskDisposition(
        task_id="T", arm="baseline", passed=False,
        judge_tag="CHECKABLE-BUT-WRONG", judge_reason="r",
        floor_exit=1, held_out_exit=1,
        failure_class="produced-but-no-real-effect",
        cost_usd=0.0123, wall_clock_s=12.5,
        transcript_path="/ev/t", check_command="python check.py",
    )
    rec = d.as_record()
    for k in ("cost_usd", "wall_clock_s", "transcript_path",
              "check_command", "judge_tag", "judge_reason",
              "failure_class"):
        assert k in rec
    assert rec["cost_usd"] == 0.0123  # measured, not estimated


def test_AC_PBR_6_cost_is_measured_from_json_envelope() -> None:
    """The arm drivers read total_cost_usd from the --output-format
    json envelope (measured, never estimated — D-COST-BAND)."""
    arms = (PBR / "src" / "programbench_revival"
            / "arms.py").read_text()
    assert '"--output-format", "json"' in arms
    assert "total_cost_usd" in arms
    runner = (PBR / "src" / "programbench_revival"
              / "runner.py").read_text()
    # the per-arm failure signature is built per arm in the verdict
    vr = (PBR / "src" / "programbench_revival"
          / "verdict.py").read_text()
    assert "per_arm_failure_signature" in vr
    assert "_sig(" in vr


def test_AC_PBR_6_per_arm_failure_signature_in_verdict() -> None:
    from programbench_revival import compute_verdict
    from programbench_revival.verdict import ArmTaskDisposition

    def d(tid, arm, passed, fc=""):
        return ArmTaskDisposition(
            task_id=tid, arm=arm, passed=passed,
            judge_tag="FAITHFUL" if passed else "CHECKABLE-BUT-WRONG",
            judge_reason="r", floor_exit=0 if passed else 1,
            held_out_exit=0 if passed else 1,
            failure_class=fc, cost_usd=0.01, wall_clock_s=1.0,
            transcript_path="t", check_command="c",
        )

    baseline = [
        d("T0", "baseline", False, "produced-but-no-real-effect"),
        d("T1", "baseline", False, "did-not-produce-output"),
        d("T2", "baseline", True),
    ]
    loam = [
        d("T0", "loam", True),
        d("T1", "loam", False, "honest-negative-refusal"),
        d("T2", "loam", True),
    ]
    v = compute_verdict(baseline, loam)
    sig = v.per_arm_failure_signature
    assert sig["baseline"]["produced-but-no-real-effect"] == 1
    assert sig["baseline"]["did-not-produce-output"] == 1
    assert sig["loam"]["honest-negative-refusal"] == 1
