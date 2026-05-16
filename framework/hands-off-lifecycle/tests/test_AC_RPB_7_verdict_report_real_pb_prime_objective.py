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

"""AC.RPB.7 (LEAD; honest-negative VALID) — the verdict report
answers the prime-objective question ON THE REAL PUBLIC PROGRAMBENCH.

Real-claude + real-amd64-emulated-eval-driven; DISPATCHER-OWNED
(own-the-wait); gated behind RPB_RUN_REAL=1 so the deterministic seal
sweep COLLECTS but SKIPS it (the AC.PBR.7 / AC.B.5 / GR.5 /
subloam-driver precedent — the captured verdict artefact + the report
are the durable facts; re-spawning real claude + the wall-clock-heavy
real eval to flip a test assertion would itself be the retry-to-green
the plan forbids). Every spawn routes through the sealed shared
loam-spawn-isolation surface via the REUSED v2 arms/scorer (the
Telegram-death #5 vector — non-negotiable).

Outcome under test (not method): a definite, independently-judged,
evidence-backed THREE-VALUED verdict over the REAL public ProgramBench
+ the per-arm failure-signature map + the FROZEN-RATIFIED margin +
the k_min small-k floor + the all-tasks-pass metric labelled NOT the
gate + measured cost/latency + the explicit "this is the REAL public
ProgramBench, a different/harder artefact than the v2 substitute"
statement + a plain-language answer EXISTS at
docs/experiments/programbench-revival-real-pb.md — for ANY polarity
(material-win / no-material-win / indeterminate, incl. the
k_min-forced indeterminate). "loam does NOT materially beat the
baseline on the real benchmark" satisfies this AC EXACTLY as a
material-win does; it is NEVER retried to green, the FROZEN margin
NEVER weakened.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
REALPB = ROOT / "framework" / "tools" / "programbench-revival" / "realpb"
V2 = ROOT / "framework" / "tools" / "programbench-revival"
sys.path.insert(0, str(REALPB / "src"))
sys.path.insert(0, str(V2 / "src"))

RPB_RUN_GATE = os.environ.get("RPB_RUN_REAL") == "1"
VERDICT_JSON = REALPB / ".run_evidence" / "verdict.json"
REPORT_MD = ROOT / "docs" / "experiments" / \
    "programbench-revival-real-pb.md"


def _verdict_or_run() -> dict:
    """Consume the already-written verdict artefact when present (the
    empirical result is the durable fact). Fall back to running the
    real experiment only if no verdict exists yet (the
    dispatcher-owned real run, gated)."""
    if VERDICT_JSON.exists():
        return json.loads(VERDICT_JSON.read_text())
    from programbench_revival_realpb.runner import (
        run_realpb_experiment,
    )

    return run_realpb_experiment(
        cost_ceiling_usd=float(
            os.environ.get("RPB_COST_CEILING", "20.0")),
        wall_ceiling_s=float(
            os.environ.get("RPB_WALL_CEILING_S", "21600")),
    )


@pytest.mark.skipif(
    not RPB_RUN_GATE,
    reason=(
        "AC.RPB.7 is the real-claude + real-amd64-emulated-eval "
        "ProgramBench-revival REAL-public-PB end-to-end measurement; "
        "run explicitly by the dispatcher with RPB_RUN_REAL=1 "
        "(own-the-wait — spawns real claude for both arms + the "
        "independent judge through the mandated isolation surface AND "
        "runs the wall-clock-heavy real upstream programbench eval "
        "under amd64 emulation). Deterministic seal sweep skips by "
        "design — the three-valued verdict + per-arm failure-"
        "signature map are captured to the report, not gated in CI."
    ),
)
def test_AC_RPB_7_definite_three_valued_verdict_any_polarity() -> None:
    """Assert the real-PB run produced a DEFINITE, independently-
    judged, evidence-backed three-valued verdict + the report — for
    ANY polarity. A no-material-win / indeterminate (incl. the
    k_min-forced indeterminate) finding satisfies this AC EXACTLY as
    a material-win does (NEVER retried to green)."""
    result = _verdict_or_run()
    v = result["verdict"]

    from programbench_revival_realpb.verdict import THREE_VALUED

    # (1) the verdict is one of exactly three definite values,
    # computed (not asserted) — any polarity satisfies the AC
    assert v["verdict"] in THREE_VALUED
    assert v["reason"].strip(), "the verdict must name WHY"

    # (2) it IS the REAL public ProgramBench, NOT the v2 substitute
    assert result["is_real_public_programbench"] is True
    assert "real-public" in result["task_set_id"]
    assert "MUST NOT be cited as a real-PB result" in \
        result["v2_substitute_relationship"]

    # (3) scored by the INDEPENDENT judge grounded in the REAL
    # upstream eval, PROVABLY NOT the loop's own
    assert "PROVABLY NOT the loop's own" in \
        result["scoring_authority"]
    assert "REAL upstream" in result["scoring_authority"]

    # (4) the per-arm failure-signature map with the false-success
    # "produced-but-no-real-effect" class explicit per arm
    sig = v["per_arm_failure_signature"]
    for arm in ("baseline", "loam"):
        for cls in ("produced-but-no-real-effect",
                    "did-not-produce-output",
                    "produced-but-wrong",
                    "honest-negative-refusal"):
            assert cls in sig[arm]

    # (5) the FROZEN-RATIFIED margin + the k_min small-k floor + the
    # aspirational-NOT-the-gate label
    assert "CLEAR MAJORITY" in v["margin_text"]
    assert "k_min >= 2" in v["margin_text"]
    assert v["k_min"] >= 2
    assert "NOT the real-PB pass/fail gate" in \
        v["all_tasks_pass_aspirational"]["note"]

    # (6) measured cost + the agent-vs-eval-emulation wall-clock split
    for d in (result["baseline_dispositions"]
              + result["loam_dispositions"]):
        assert "cost_usd" in d
        assert "agent_wall_clock_s" in d
        assert "eval_emulation_wall_clock_s" in d
        assert "upstream_score" in d  # the real graded signal

    # (7) the report exists, names the verdict, and explicitly states
    # this is the REAL public ProgramBench (a different/harder
    # artefact than the v2 substitute)
    assert REPORT_MD.exists(), f"report missing: {REPORT_MD}"
    md = REPORT_MD.read_text()
    assert v["verdict"] in md
    assert "REAL public ProgramBench" in md
    assert "NOT the v2 substitute" in md
    assert "first-class plan-success" in md.lower()
