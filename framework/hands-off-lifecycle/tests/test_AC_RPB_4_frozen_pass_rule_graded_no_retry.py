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

"""AC.RPB.4 — per (arm,task) pass/fail computed by a rule FROZEN
before any run over the GRADED real upstream signal, no
retry-to-pass: passed IFF independent judge FAITHFUL AND the real
upstream graded score clears the frozen per-task theta AND the
held-out anti-overfit binding holds.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REALPB = ROOT / "framework" / "tools" / "programbench-revival" / "realpb"
sys.path.insert(0, str(REALPB / "src"))


def test_AC_RPB_4_frozen_pass_rule_over_graded_score() -> None:
    from programbench_revival_realpb.verdict import realpb_frozen_pass

    # both-must-pass spine over the GRADED upstream score:
    # judge FAITHFUL AND score >= theta AND held-out clean
    assert realpb_frozen_pass(
        judge_tag="FAITHFUL", upstream_score=0.44,
        floor_theta=0.10, held_out_clean=True) is True
    # compile_failed / hollow => score 0.0 < theta => non-pass by
    # construction (the GRADED-floor positive-real-outcome rule)
    assert realpb_frozen_pass(
        judge_tag="FAITHFUL", upstream_score=0.0,
        floor_theta=0.10, held_out_clean=True) is False
    # a non-zero but sub-theta real score is still a non-pass (a real
    # but insufficient effect — not a partial win)
    assert realpb_frozen_pass(
        judge_tag="FAITHFUL", upstream_score=0.05,
        floor_theta=0.10, held_out_clean=True) is False
    # the independent judge is a hard gate even with a high score
    assert realpb_frozen_pass(
        judge_tag="CHECKABLE-BUT-WRONG", upstream_score=0.9,
        floor_theta=0.10, held_out_clean=True) is False
    assert realpb_frozen_pass(
        judge_tag="HONEST-NEGATIVE", upstream_score=0.9,
        floor_theta=0.10, held_out_clean=True) is False
    # the held-out anti-overfit binding is a hard gate
    assert realpb_frozen_pass(
        judge_tag="FAITHFUL", upstream_score=0.9,
        floor_theta=0.10, held_out_clean=False) is False


def test_AC_RPB_4_frozen_before_run_no_retry_to_pass() -> None:
    from programbench_revival_realpb.loader import (
        load_frozen_realpb_set,
    )
    from programbench_revival_realpb import runner

    ts = load_frozen_realpb_set()
    # the rule + theta + taxonomy are CONTENT-HASH-PINNED with the
    # task set BEFORE any run (the contamination spine)
    assert "FROZEN before any run" in ts.frozen_pass_rule or \
        "Run ONCE per (arm,task)" in ts.frozen_pass_rule
    assert "NO retry-to-pass" in ts.frozen_pass_rule
    assert "NEVER to flip a fail to a pass" in ts.frozen_pass_rule

    # the runner runs each (arm,task) ONCE for the headline (no
    # retry loop around the arm drivers)
    rr = inspect.getsource(runner.run_realpb_experiment)
    assert "for task in ts.tasks:" in rr
    # one baseline call + one loam call per task; no retry-to-pass
    assert rr.count("run_baseline_arm(") == 1
    assert rr.count("run_loam_arm(") == 1
