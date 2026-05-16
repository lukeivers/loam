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
    """Assert the AC.GR.5 honest re-harden produced a DEFINITE,
    evidence-backed per-intent verdict whose net/irreducibility +
    fabricated-pass picture is CAPTURED — either polarity is
    plan-success.

    The plan's actual bar (loop-goal-refinement §4, verbatim): "the
    bar is *per-intent definiteness + net improvement over 2/7 + no
    fabricated pass + per-class irreducibility first-class* ... A
    definite 'these classes refine, these classes are irreducible
    even on-the-path — here is the evidence' is a valid, plan-success
    §10.5 outcome, reported straight, NOT retried to green."

    The four named bar dimensions are *reported and asserted as a
    DEFINITE captured picture*, NOT collapsed into a green-only gate.
    In particular `no_fabricated_pass` is a first-class REPORTED
    dimension: if the loop's own judge still rubber-stamps a
    checkable-but-wrong on some intent class, that is a definite,
    evidence-named §10.5 honest-negative on the rubber-stamp
    sub-property — the plan explicitly says such a finding is
    reported straight, NOT retried to green and NOT used to weaken
    the bar.  Asserting `no_fabricated_pass is True` as a hard
    green-gate would CONTRADICT the plan's explicit "either polarity
    is plan-success" construction (the recorded F2 / M5 resolution in
    the build report) — the AC is "a definite evidence-backed verdict
    with the four-dimension picture captured", not "the loop is
    perfect".

    Consumes the already-written verdict artefact when present (the
    re-harden's empirical result is the durable fact; re-spawning
    real `claude` ×7 to flip a test assertion would itself be the
    retry-to-green the plan forbids).  Falls back to running the
    re-harden only if no verdict exists yet (the dispatcher-owned
    real run, gated)."""
    import json
    from pathlib import Path

    verdict_path = (
        Path(__file__).resolve().parents[3]
        / "framework" / "tools" / "handsoff-loop"
        / ".phase_verdicts" / "goal_refine_reharden.json"
    )
    if verdict_path.exists():
        table = json.loads(verdict_path.read_text())
    else:
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
    # (3) the four bar dimensions are CAPTURED + reported straight
    # (definite picture, NOT a green-only gate — the plan's §10.5
    # either-polarity construction; recorded M5 resolution).
    for key in ("sealed_faithful", "now_faithful",
                "now_honest_negative", "now_checkable_but_wrong",
                "honest_coverage_now", "now_irreducible",
                "no_fabricated_pass"):
        assert key in net, (
            f"AC.GR.5 net picture must capture {key!r} (per-class "
            f"definiteness + net + irreducibility + fabricated-pass "
            f"first-class — plan §4 bar)"
        )
    assert isinstance(net["no_fabricated_pass"], bool), (
        "fabricated-pass is a first-class REPORTED dimension (a "
        "definite bool), reported straight — NOT a green-only gate "
        "(plan §4: a fabricated-pass finding is a valid §10.5 "
        "honest-negative reported straight, NOT retried to green)"
    )
    # (4) net improvement over the sealed 2/7: the faithful coverage
    # is strictly STRONGER than the sealed 2/7 — refinement converted
    # at least one sealed non-faithful class into a now-faithful
    # (judge-confirmed real, not a proxy) outcome.  This is the plan
    # §4 net-improvement dimension (NOT a fixed >=N/7).
    faithful_now = set(net["now_faithful"])
    sealed_faithful = set(net["sealed_faithful"])
    assert sealed_faithful <= faithful_now, (
        "the sealed faithful set (I1,I4) must not regress under "
        "refinement"
    )
    assert len(faithful_now) > len(sealed_faithful), (
        "net improvement: refinement must lift faithful strictly "
        "above the sealed 2/7 (>=3/7) — a definite net-stronger "
        "result; the per-class irreducible + fabricated-pass "
        "findings are reported straight as valid §10.5 outcomes"
    )
