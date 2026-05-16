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

"""AC.B.5 — Phase B end-test: intent -> checkable-done.

Plan: docs/plans/handsoff-loop-real-build.md (§3 AC.B.5, §4, §10)

The §10.5 honest end-test for Risk B.  A genuinely under-specified
plain-language intent is run through the intake; the output is the
elicitation transcript, the derived plain-language acceptance, the
machine-checkable form, an independent faithfulness verdict, and a
per-dimension table for:

  (i)   derived done is machine-checkable
  (ii)  derived done is faithful to original intent (INDEPENDENT
        adversarial judge)
  (iii) elicitation stayed bounded (user not turned into a spec
        author)
  (iv)  the one approval gate was plain-language

The end-test PASSES AS A PLAN-DELIVERABLE when the table is DEFINITE
and evidence-backed — either polarity.  Contract §10 flags Phase B as
the risk MOST LIKELY to retire NEGATIVE; a definite "intent->done
cannot be made faithful/checkable reliably enough — here is the
failure class + evidence" is a valid plan-success outcome (§10.5),
reported straight, NEVER retried to green, NEVER softened to
'fixable'.

Real-claude-driven; DISPATCHER-OWNED (own-the-wait); gated behind
HANDSOFF_RUN_PHASE_B=1 so the deterministic seal sweep collects but
skips it (subloam-driver-fix precedent).
"""

from __future__ import annotations

import os

import pytest

PHASE_B_GATE = os.environ.get("HANDSOFF_RUN_PHASE_B") == "1"


@pytest.mark.skipif(
    not PHASE_B_GATE,
    reason=(
        "AC.B.5 is the real-claude-driven Phase B honest end-test; run "
        "explicitly by the dispatcher with HANDSOFF_RUN_PHASE_B=1 "
        "(own-the-wait). Deterministic seal sweep skips by design — "
        "verdict table captured to the build report, not gated in CI."
    ),
)
def test_AC_B5_phase_b_intake_verdict_is_definite() -> None:
    """Run a genuinely fuzzy intent through the real intake; assert the
    per-dimension verdict table is DEFINITE + evidence-backed.  Either
    polarity is plan-success — a NEGATIVE (intent cannot be made
    faithfully checkable reliably enough) is reported straight and is
    explicitly NOT retried (the contract's §10 expected-possible)."""
    from handsoff_loop_phase_b_runner import run_phase_b  # type: ignore

    verdict = run_phase_b()
    table = verdict.as_table()

    assert table["definite"] is True, (
        "Phase B end-test must produce a DEFINITE verdict; only a "
        "could-not-determine is a real failure of this AC"
    )
    assert table["passed_as_deliverable"] is True, (
        "every named dimension must carry evidence (D-NEG-DEPTH)"
    )
    for dim in ("derived_done_machine_checkable",
                "derived_done_faithful_independent",
                "elicitation_bounded",
                "approval_gate_plain_language"):
        assert dim in table["dimensions"], (
            f"AC.B.5 requires named dimension {dim!r}"
        )
        assert table["dimensions"][dim]["evidence"].strip(), (
            f"dimension {dim!r} must be evidence-backed"
        )
