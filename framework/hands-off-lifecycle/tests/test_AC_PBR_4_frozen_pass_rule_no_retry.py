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

"""AC.PBR.4 — pass/fail per task on a pre-frozen rule, no
retry-to-pass.

Outcome under test (not method): a task is "passed" for an arm IFF
the independent judge tags FAITHFUL **and** the positive-real-outcome
floor check exits 0 **and** the held-out anti-overfit check exits 0
(the verify.py:213-215 both-must-pass spine), frozen with the task
set; each (arm,task) is run once for the headline with no
retry-to-pass.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PBR = ROOT / "framework" / "tools" / "programbench-revival"
sys.path.insert(0, str(PBR / "src"))


def test_AC_PBR_4_pass_requires_all_three_legs() -> None:
    from programbench_revival import frozen_pass

    # all three legs satisfied -> pass
    assert frozen_pass(judge_tag="FAITHFUL", floor_exit=0,
                        held_out_exit=0) is True
    # judge not faithful -> non-pass even if checks exit 0
    assert frozen_pass(judge_tag="CHECKABLE-BUT-WRONG", floor_exit=0,
                        held_out_exit=0) is False
    assert frozen_pass(judge_tag="HONEST-NEGATIVE", floor_exit=0,
                        held_out_exit=0) is False
    assert frozen_pass(judge_tag="INDETERMINATE", floor_exit=0,
                        held_out_exit=0) is False
    # floor non-zero -> non-pass even if judge faithful
    assert frozen_pass(judge_tag="FAITHFUL", floor_exit=1,
                        held_out_exit=0) is False
    # held-out non-zero (overfit) -> non-pass even if floor passed +
    # judge faithful (the both-must-pass spine catches false-success)
    assert frozen_pass(judge_tag="FAITHFUL", floor_exit=0,
                        held_out_exit=1) is False
    # held-out absent (None) is permitted (verify.py spine)
    assert frozen_pass(judge_tag="FAITHFUL", floor_exit=0,
                        held_out_exit=None) is True


def test_AC_PBR_4_rule_is_frozen_with_task_set() -> None:
    """The pass rule is pinned in the content-hashed task set (frozen
    before any run)."""
    from programbench_revival import load_frozen_task_set

    ts = load_frozen_task_set()
    assert "independent" in ts.frozen_pass_rule.lower()
    assert "floor" in ts.frozen_pass_rule.lower()
    assert "no retry-to-pass" in ts.frozen_pass_rule.lower()
    assert "both-must-pass" in ts.frozen_pass_rule.lower() or \
        "213-215" in ts.frozen_pass_rule


def test_AC_PBR_4_no_retry_to_pass_in_runner() -> None:
    """The runner runs each (arm,task) ONCE for the headline — no
    loop that re-spawns an arm to flip a fail to a pass. Asserted on
    the parsed CODE (not docstring prose, which legitimately NAMES
    'no retry-to-pass' to document the constraint — the ODD-correct
    precise outcome is 'each arm has exactly one call site and no
    pass-conditioned re-invocation loop')."""
    import ast

    runner = PBR / "src" / "programbench_revival" / "runner.py"
    tree = ast.parse(runner.read_text())
    baseline_calls = loam_calls = 0
    while_nodes = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            fn = node.func
            name = (fn.id if isinstance(fn, ast.Name)
                    else getattr(fn, "attr", ""))
            if name == "run_baseline_arm":
                baseline_calls += 1
            if name == "run_loam_arm":
                loam_calls += 1
        if isinstance(node, ast.While):
            while_nodes += 1
    # exactly one call site per arm — no re-spawn to flip a fail
    assert baseline_calls == 1
    assert loam_calls == 1
    # no while-loop anywhere in the runner (no pass-conditioned
    # re-invocation; the only iteration is the `for task` task walk)
    assert while_nodes == 0, (
        "a while-loop in the runner risks a retry-to-pass path; the "
        "headline is single-run per (arm,task)"
    )
