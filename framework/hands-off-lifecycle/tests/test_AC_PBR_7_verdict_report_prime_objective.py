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

"""AC.PBR.7 (LEAD; honest-negative VALID) — the verdict report
answers the prime-objective question.

Real-claude-driven; DISPATCHER-OWNED (own-the-wait); gated behind
PBR_RUN_V2=1 so the deterministic seal sweep COLLECTS but SKIPS it
(the AC.B.5 / GR.5 / subloam-driver precedent — the captured verdict
artefact + the report are the durable facts; re-spawning real
`claude` to flip a test assertion would itself be the retry-to-green
the plan forbids). Every spawn routes through the sealed shared
loam-spawn-isolation surface (Telegram-death #5 vector —
non-negotiable).

Outcome under test (not method): a definite, independently-judged,
evidence-backed THREE-VALUED verdict + the per-arm failure-signature
map + the FROZEN-RATIFIED margin + the all-tasks-pass metric labelled
NOT the gate + measured cost/latency + a plain-language answer EXISTS
at docs/experiments/programbench-revival-v2.md — for ANY polarity
(material-win / no-material-win / indeterminate). "loam does NOT
materially beat the baseline" satisfies this AC EXACTLY as a
material-win does; it is NEVER retried to green, the margin NEVER
weakened.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PBR = ROOT / "framework" / "tools" / "programbench-revival"
sys.path.insert(0, str(PBR / "src"))

PBR_RUN_GATE = os.environ.get("PBR_RUN_V2") == "1"
VERDICT_JSON = PBR / ".run_evidence" / "verdict.json"
REPORT_MD = ROOT / "docs" / "experiments" / "programbench-revival-v2.md"


def _verdict_or_run() -> dict:
    """Consume the already-written verdict artefact when present (the
    empirical result is the durable fact). Fall back to running the
    real experiment only if no verdict exists yet (the
    dispatcher-owned real run, gated)."""
    if VERDICT_JSON.exists():
        return json.loads(VERDICT_JSON.read_text())
    from programbench_revival.runner import run_experiment

    return run_experiment(
        cost_ceiling_usd=float(os.environ.get("PBR_COST_CEILING",
                                              "8.0"))
    )


@pytest.mark.skipif(
    not PBR_RUN_GATE,
    reason=(
        "AC.PBR.7 is the real-claude-driven ProgramBench-revival v2 "
        "end-to-end measurement; run explicitly by the dispatcher "
        "with PBR_RUN_V2=1 (own-the-wait — spawns real claude for "
        "both arms + the independent judge through the mandated "
        "isolation surface). Deterministic seal sweep skips by "
        "design — the three-valued verdict + per-arm failure-"
        "signature map are captured to the report, not gated in CI."
    ),
)
def test_AC_PBR_7_definite_three_valued_verdict_any_polarity() -> None:
    """Assert the v2 run produced a DEFINITE, independently-judged,
    evidence-backed three-valued verdict + the report — for ANY
    polarity. A no-material-win / indeterminate finding satisfies
    this AC exactly as a material-win does (NOT retried to green)."""
    result = _verdict_or_run()
    v = result["verdict"]

    # (1) the verdict is one of exactly three definite values,
    # computed (not asserted) — any polarity satisfies the AC
    from programbench_revival.verdict import THREE_VALUED

    assert v["verdict"] in THREE_VALUED
    assert v["reason"].strip(), "the verdict must name WHY"

    # (2) scored by the INDEPENDENT judge, provably NOT the loop's own
    assert "PROVABLY NOT the loop's own" in result["scoring_authority"]

    # (3) the per-arm failure-signature map exists with the
    # false-success "produced-but-no-real-effect" class explicit per
    # arm (a pass-count alone would not answer the false-success
    # question)
    sig = v["per_arm_failure_signature"]
    for arm in ("baseline", "loam"):
        assert "produced-but-no-real-effect" in sig[arm]
        assert "did-not-produce-output" in sig[arm]
        assert "produced-but-wrong" in sig[arm]
        assert "honest-negative-refusal" in sig[arm]

    # (4) the FROZEN-RATIFIED margin + the aspirational metric
    # labelled NOT the gate are both present
    assert "CLEAR MAJORITY" in v["margin_text"]
    assert "NOT the v2 pass/fail gate" in \
        v["all_tasks_pass_aspirational"]["note"]

    # (5) measured (never estimated) cost is recorded per arm
    for d in result["baseline_dispositions"] + \
            result["loam_dispositions"]:
        assert "cost_usd" in d  # measured or honest-None

    # (6) the report exists at the canonical path with the
    # plain-language answer + the honest-scope statement + the n=1
    # limitation named
    assert REPORT_MD.exists(), (
        "AC.PBR.7 requires the verdict report at "
        "docs/experiments/programbench-revival-v2.md"
    )
    body = REPORT_MD.read_text()
    assert "Plain-language answer" in body
    assert "Honest scope" in body
    assert "n=1 per task" in body
    assert v["verdict"] in body
    # honest-negative / indeterminate is a first-class satisfying
    # polarity — the report states it straight, never retried
    assert ("first-class plan-success" in body.lower()
            or "reported straight" in body.lower())


def test_AC_PBR_7_report_renderer_is_polarity_blind() -> None:
    """The report renderer produces a definite plain-language answer
    for ALL THREE polarities (no green-only path) — a deterministic
    check that does not need real claude."""
    from programbench_revival.report import render_report

    base = {
        "task_set_id": "x", "task_set_sha256": "0" * 64,
        "frozen_pass_rule": "r", "frozen_failure_taxonomy": [],
        "tasks_total": 6, "tasks_completed": ["a"] * 6,
        "halted_on_cost_ceiling": False, "cost_ceiling_usd": 8.0,
        "measured_spent_usd": 1.0, "wall_clock_s": 10.0,
        "baseline_dispositions": [], "loam_dispositions": [],
        "scoring_authority": "INDEPENDENT ... PROVABLY NOT the "
        "loop's own ... judge.",
    }
    for verdict in (
        "loam-materially-beats-baseline",
        "loam-does-not-materially-beat-baseline",
        "indeterminate",
    ):
        result = dict(base)
        result["verdict"] = {
            "verdict": verdict, "reason": "because numbers",
            "baseline_pass_count": 2, "loam_pass_count": 5,
            "baseline_non_pass_tasks": ["c"],
            "loam_recovered_of_baseline_misses": ["c"],
            "clear_majority_threshold": 0.5,
            "clear_majority_cleared": verdict.startswith("loam-mat"),
            "no_total_regression": True,
            "all_tasks_pass_aspirational": {
                "baseline_all_tasks_pass": False,
                "loam_all_tasks_pass": False,
                "note": "DOCUMENTED ASPIRATIONAL ... NOT the v2 "
                "pass/fail gate ...",
            },
            "per_arm_failure_signature": {
                "baseline": {}, "loam": {},
            },
            "margin_text": "loam ... CLEAR MAJORITY ... NOT the gate",
        }
        md = render_report(result)
        assert verdict in md
        assert "Plain-language answer" in md
        assert "Honest scope" in md
        assert "n=1 per task" in md
