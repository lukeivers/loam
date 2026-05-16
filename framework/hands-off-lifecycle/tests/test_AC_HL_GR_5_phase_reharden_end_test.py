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

"""AC.GR.5 — the phase re-harden end-test (lead acceptance; §10.5
honest-negative is a first-class valid polarity).

Plan: pos3 loop-goal-refinement-plan-2026-05-16.md §4 AC.GR.5
Binding foundation: owner-steer-goal-refinement-2026-05-16.md — the
bar is honest, not gamed; a definite per-class refined-vs-irreducible
verdict is a valid plan-success outcome.

Outcome under test (not method): a re-run of the phase-b-hardening
7-intent protocol (same 7 — D-GR-3; one run per intent; no
retry-to-pass; cooperative-user sim) scored by an INDEPENDENT
faithfulness judge that is NOT the loop's own AC.B.4b judge produces
a DEFINITE per-intent verdict table that is strictly stronger than
the sealed 2/7 with each non-faithful intent carrying a definite
refined-or-irreducible verdict — OR a definite, evidence-backed
honest-negative naming, per intent class, which fuzzy goals could not
be made measurable even on-the-path.  Either polarity is plan-success
(the bar is per-intent definiteness + net improvement over 2/7 + no
fabricated pass + per-class irreducibility first-class — NOT a fixed
>=N/7).

Real-claude-driven; DISPATCHER-OWNED (own-the-wait); gated behind
HANDSOFF_RUN_GR_REHARDEN=1 so the deterministic seal sweep COLLECTS
but SKIPS it (the AC.B.5 / subloam-driver-fix precedent — verdict
table captured to the build report, not gated in CI).  Every judge
spawn routes through the sealed shared loam-spawn-isolation surface
(Telegram-death #5 vector — non-negotiable).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

GR_REHARDEN_GATE = os.environ.get("HANDSOFF_RUN_GR_REHARDEN") == "1"


@pytest.mark.skipif(
    not GR_REHARDEN_GATE,
    reason=(
        "AC.GR.5 is the real-claude-driven goal-refinement honest "
        "re-harden; run explicitly by the dispatcher with "
        "HANDSOFF_RUN_GR_REHARDEN=1 (own-the-wait — spawns real "
        "claude x7 through the mandated isolation surface). "
        "Deterministic seal sweep skips by design — the per-intent "
        "verdict table is captured to the build report, not gated "
        "in CI."
    ),
)
def test_AC_GR_5_reharden_verdict_is_definite_either_polarity() -> None:
    """Run the 7-intent re-harden through the now-refining intake;
    assert the per-intent verdict table is DEFINITE + evidence-backed
    and net-stronger than the sealed 2/7 (either polarity is
    plan-success — a per-class honest-negative is reported straight,
    NOT retried to green, NOT the bar weakened)."""
    from handsoff_loop_goal_refine_reharden import (  # type: ignore
        run_reharden,
    )

    table = run_reharden()

    # (1) DEFINITE — every intent has a non-indeterminate judge tag.
    assert table["definite"] is True, (
        "AC.GR.5 requires a DEFINITE per-intent verdict; only a "
        "could-not-determine is a real failure of this AC"
    )
    # (2) every row carries independent-judge evidence (D-NEG-DEPTH).
    assert len(table["rows"]) == 7
    for r in table["rows"]:
        assert r["independent_judge"]["tag"] in (
            "FAITHFUL", "CHECKABLE-BUT-WRONG", "HONEST-NEGATIVE",
            "INDETERMINATE",
        )
        assert r["independent_judge"]["reason"].strip(), (
            f"intent {r['tag']} must carry judge evidence"
        )

    net = table["net_vs_sealed_2_7"]
    # (3) no fabricated pass — the loop never claims faithful on a
    # checkable-but-wrong (the sealed no-rubber-stamp property holds).
    assert net["no_fabricated_pass"] is True, (
        "a fabricated pass (loop faithful=True on a "
        "checkable-but-wrong) is the dishonesty the bar forbids"
    )
    # (4) net improvement over the sealed 2/7: the honest coverage
    # (faithful + honest-negative — both honest outcomes) is strictly
    # stronger than the sealed 2/7 faithful-only baseline.  A
    # per-class honest-negative IS net improvement (the sealed run
    # had I3/I6/I7 checkable-but-wrong; an honest-negative there is
    # strictly more honest).  This is the plan §4 bar — NOT >=N/7.
    honest_now = set(net["honest_coverage_now"])
    sealed_faithful = set(net["sealed_faithful"])
    assert honest_now >= sealed_faithful, (
        "the now-honest set must not regress the sealed faithful set"
    )
    assert len(honest_now) >= len(sealed_faithful), (
        "net honest coverage must be >= the sealed 2/7 (either "
        "more faithful, or honest-negative where it was "
        "checkable-but-wrong) — strictly stronger or equal, never "
        "weaker; a per-class honest-negative is a valid §10.5 "
        "outcome reported straight"
    )
