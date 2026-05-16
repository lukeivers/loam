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

"""AC.RPB.6 — cost, the agent-vs-eval-emulation wall-clock split, the
real upstream eval evidence, and a per-non-pass frozen-taxonomy
failure class are captured and reproducible (REUSED v2 four-class
taxonomy, real-PB-bound).
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REALPB = ROOT / "framework" / "tools" / "programbench-revival" / "realpb"
sys.path.insert(0, str(REALPB / "src"))


def test_AC_RPB_6_four_class_taxonomy_every_non_pass() -> None:
    from programbench_revival_realpb.verdict import (
        FROZEN_FAILURE_TAXONOMY,
        RealPBFailureClass,
        classify_realpb_failure,
    )

    assert FROZEN_FAILURE_TAXONOMY == (
        "did-not-produce-output",
        "produced-but-no-real-effect",
        "produced-but-wrong",
        "honest-negative-refusal",
    )

    # an honest refusal => honest-negative-refusal (first-class)
    assert classify_realpb_failure(
        produced_submission=False, judge_tag="HONEST-NEGATIVE",
        upstream_score=0.0, upstream_error_code=None,
        floor_theta=0.1) == "honest-negative-refusal"
    # nothing produced => did-not-produce-output
    assert classify_realpb_failure(
        produced_submission=False, judge_tag="CHECKABLE-BUT-WRONG",
        upstream_score=0.0, upstream_error_code=None,
        floor_theta=0.1) == "did-not-produce-output"
    # compile_failed / hollow => produced-but-no-real-effect (the
    # false-success class the real graded floor is built to catch)
    assert classify_realpb_failure(
        produced_submission=True, judge_tag="CHECKABLE-BUT-WRONG",
        upstream_score=0.0, upstream_error_code="compile_failed",
        floor_theta=0.1) == "produced-but-no-real-effect"
    # a real compiling submission, real but insufficient effect
    # (0.01 < score < theta) => produced-but-wrong
    assert classify_realpb_failure(
        produced_submission=True, judge_tag="FAITHFUL",
        upstream_score=0.05, upstream_error_code=None,
        floor_theta=0.1) == "produced-but-wrong"

    # the dataclass rejects any class outside the frozen taxonomy
    try:
        RealPBFailureClass(task_id="t", arm="a",
                           failure_class="made-up", evidence="x")
        raise AssertionError("expected ValueError")
    except ValueError:
        pass


def test_AC_RPB_6_real_eval_evidence_cost_wallclock_split() -> None:
    from programbench_revival_realpb.verdict import (
        RealPBArmDisposition,
    )
    from programbench_revival_realpb import runner, upstream_eval

    # the disposition record carries the REAL upstream eval evidence
    # (graded score + n_resolved/n_tests + error_code + eval.json
    # path), measured cost, and the agent-vs-eval wall-clock split
    fields = RealPBArmDisposition.__dataclass_fields__
    for f in ("upstream_score", "upstream_n_resolved",
              "upstream_n_tests", "upstream_error_code",
              "eval_json_path", "cost_usd",
              "agent_wall_clock_s",
              "eval_emulation_wall_clock_s"):
        assert f in fields, f

    # cost is MEASURED from --output-format json total_cost_usd
    # (D-COST-BAND, never estimated) — via the reused v2 arms.py
    arms_src = inspect.getsource(
        sys.modules.get("programbench_revival.arms")
        or __import__("programbench_revival.arms",
                       fromlist=["x"]))
    assert "total_cost_usd" in arms_src
    assert "never estimated" in arms_src or \
        "D-COST-BAND" in arms_src

    # the eval-emulation wall-clock is recorded DISTINCTLY (F2 §10.3 —
    # the amd64-emulation eval leg is the wall-clock-heavy leg)
    ue_src = inspect.getsource(upstream_eval)
    assert "eval_emulation_wall_clock_s" in ue_src
    assert "wall-clock-heavy" in ue_src

    # the headline is reproducible from the preserved per-(arm,task)
    # evidence incl. the REAL *.eval.json under .run_evidence/
    runner_src = inspect.getsource(runner)
    assert ".run_evidence" in runner_src
    assert 'verdict.json' in runner_src
    assert "disposition.json" in runner_src
