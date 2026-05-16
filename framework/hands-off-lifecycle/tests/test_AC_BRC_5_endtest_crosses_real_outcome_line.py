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

"""AC.BRC.5 (LEAD; honest-negative VALID) — an end-test produces a
DEFINITE per-dimension verdict that the loop now CROSSES the real-
outcome line before stopping.

Real-claude-driven; DISPATCHER-OWNED (own-the-wait); gated behind
HANDSOFF_RUN_BRC=1 so the deterministic seal sweep COLLECTS but SKIPS
it (the AC.RPB.7 / GR.5 / AC.B.5 precedent — the captured per-dimension
verdict artefact is the durable fact; re-spawning real `claude` to
flip a test assertion would itself be the retry-to-green the plan
forbids). Every spawn is the loop's own, routed through the loop's
sealed isolation surface (no new spawn machinery).

Outcome under test (not method): a DEFINITE, evidence-backed PER-
DIMENSION verdict on a real (probe-class-or-harder) task that the loop
(i) gates "done" on a behavioural self-check (not structural presence),
(ii) re-drove a bounded failure-context-carrying refinement (bound
held, observable), (iii) verification-gated every iteration, (iv)
stayed within the EXISTING measured cost/wall ceiling — OR a definite,
evidence-backed HONEST-NEGATIVE naming which dimension could not be
demonstrated and why.  An honest-negative satisfies this AC EXACTLY as
a positive does; it is NEVER retried to green, the bound NEVER
weakened.  n=1 here is a deliberate ARCHITECTURAL-verdict choice (the
loop's CAPABILITY to cross the real-outcome line), NOT a statistical
payoff-size claim — the score-payoff SIZE is the SEPARATE post-
aggregate fast-follow and is asserted by NO dimension here.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

BRC_RUN_GATE = os.environ.get("HANDSOFF_RUN_BRC") == "1"
VERDICT_PATH = (
    ROOT / "framework" / "tools" / "handsoff-loop"
    / ".phase_verdicts" / "behavioral_refine_endtest.json"
)


def _verdict_or_run() -> dict:
    """Consume the already-written verdict artefact when present (the
    end-test's empirical result is the durable fact). Fall back to
    running the real end-test only if no verdict exists yet (the
    dispatcher-owned real run, gated)."""
    if VERDICT_PATH.exists():
        return json.loads(VERDICT_PATH.read_text())
    from handsoff_loop.behavioral_refine_endtest import (
        run_behavioral_refine_endtest,
    )

    return run_behavioral_refine_endtest(
        max_refine_attempts=int(
            os.environ.get("HANDSOFF_BRC_MAX_REFINE", "2")),
        cost_ceiling_usd=float(
            os.environ.get("HANDSOFF_BRC_COST_CEILING", "8.0")),
        wall_ceiling_s=float(
            os.environ.get("HANDSOFF_BRC_WALL_CEILING_S", "2400")),
    )


@pytest.mark.skipif(
    not BRC_RUN_GATE,
    reason=(
        "AC.BRC.5 is the real-claude behavioural-refine end-test; run "
        "explicitly by the dispatcher with HANDSOFF_RUN_BRC=1 "
        "(own-the-wait — the loop spawns real `claude` through its "
        "sealed isolation surface and may re-drive a bounded number "
        "of refine attempts under the existing cost/wall ceiling). "
        "Deterministic seal sweep skips by design — the definite "
        "per-dimension verdict (honest-negative first-class) is "
        "captured to the verdict artefact, not gated in CI."
    ),
)
def test_AC_BRC_5_definite_per_dimension_verdict_any_polarity(
) -> None:
    """Assert the end-test produced a DEFINITE, evidence-backed
    per-dimension verdict — for ANY polarity. An honest-negative
    ("the loop did not cross the line on this task — here is the
    per-dimension evidence") satisfies this AC EXACTLY as a positive
    does; it is NEVER retried to green and the bound is NEVER
    weakened."""
    table = _verdict_or_run()

    # (1) DEFINITE + evidence-backed for EITHER polarity (not green-
    # only — an honest-negative is a first-class plan-success).
    assert table["ac"] == "AC.BRC.5"
    assert table["definite"] is True, (
        "AC.BRC.5 requires a DEFINITE per-dimension verdict; only a "
        "could-not-determine is a real failure of this AC"
    )
    assert table["polarity"] in ("positive", "negative")
    assert table["honest_negative_is_plan_success"] is True
    assert table["never_retried_to_green"] is True

    # (2) the four named dimensions are present, each carrying
    # definite evidence (NOT collapsed into a green-only gate).
    dims = table["dimensions"]
    for name in (
        "behavioural_done_not_structural",
        "bounded_failure_context_redrive",
        "verification_gated_iteration",
        "within_existing_cost_wall_ceiling",
    ):
        assert name in dims, f"missing dimension {name}"
        assert isinstance(dims[name]["verdict"], bool)
        assert dims[name]["evidence"].strip(), (
            f"dimension {name} must carry definite evidence "
            "(honest-negative is reported straight, with evidence)"
        )

    # (3) the bound HELD (never exceeded) regardless of polarity —
    # the honest-negative is the bound being honest, not gamed.
    assert table["refine_attempts"] <= table["refine_bound"]
    assert table["refine_stop_reason"] in (
        "done", "attempt-bound", "cost-ceiling", "wall-ceiling")

    # (4) cost/wall MEASURED (the loop's own json cost surface), not
    # estimated; a measurement gap is reported as an honest None, not
    # papered over.
    assert "measured_cost_usd" in table
    assert "measured_wall_clock_s" in table

    # (5) n=1 is the ARCHITECTURAL-verdict framing, stated in plain
    # language; this end-test asserts NO benchmark-score magnitude
    # (the payoff SIZE is the separate post-aggregate fast-follow).
    assert "ARCHITECTURAL verdict" in table["n1_framing"]
    assert "post-aggregate fast-follow" in table["n1_framing"]
    assert "NO benchmark-score magnitude" in table["n1_framing"]
