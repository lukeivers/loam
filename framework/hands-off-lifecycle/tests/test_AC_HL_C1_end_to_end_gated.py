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

"""AC.C.1 — end-to-end hands-off, GATED on A AND B both positive.

Plan: docs/plans/handsoff-loop-real-build.md (§3 AC.C.1, §4)

Conditional on Phase A and Phase B both retiring POSITIVE: one
plain-language intent, walked away from, produces real verified work
via the packaged mechanism with the single plain-language approval as
the only human touch.

If EITHER phase retired negative, AC.C.1 is **not attempted** — it is
GATED, not failed.  The honest-negative on A or B makes C out of
scope, which is a CORRECT outcome, not a miss.  This test encodes the
gate itself: it asserts the gating rule, and the actual end-to-end
run is dispatcher-owned (HANDSOFF_RUN_TIER_C=1) and only legitimate
when both phase verdicts on disk are positive.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
PHASE_A_VERDICT = (
    ROOT / "framework" / "tools" / "handsoff-loop"
    / ".phase_verdicts" / "phase_a.json"
)
PHASE_B_VERDICT = (
    ROOT / "framework" / "tools" / "handsoff-loop"
    / ".phase_verdicts" / "phase_b.json"
)
TIER_C_GATE = os.environ.get("HANDSOFF_RUN_TIER_C") == "1"


def _polarity(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text()).get("polarity")
    except json.JSONDecodeError:
        return None


def test_AC_C1_gating_rule_holds() -> None:
    """The gate is structural: Tier C is attempted IFF A and B are both
    positive.  This is always-on (deterministic) and verifies the
    gating logic regardless of whether the phase runs happened."""
    a = _polarity(PHASE_A_VERDICT)
    b = _polarity(PHASE_B_VERDICT)
    both_positive = a == "positive" and b == "positive"
    # If either is negative/absent, Tier C MUST be gated (not run).
    # The gate env flag is only legitimate when both are positive.
    if not both_positive:
        assert not TIER_C_GATE or (a is None or b is None), (
            "Tier C must be GATED (not attempted) unless BOTH phase "
            f"verdicts are positive (A={a!r}, B={b!r}). A negative on "
            "A or B makes C out of scope — a correct outcome, not a "
            "miss."
        )


@pytest.mark.skipif(
    not TIER_C_GATE,
    reason=(
        "AC.C.1 end-to-end is dispatcher-owned and only legitimate "
        "when BOTH phase verdicts are positive; gated behind "
        "HANDSOFF_RUN_TIER_C=1. If either phase retired negative this "
        "AC is not attempted — gated, not failed."
    ),
)
def test_AC_C1_end_to_end_only_if_both_phases_positive() -> None:
    """End-to-end run is legitimate ONLY when both phases are positive."""
    a = _polarity(PHASE_A_VERDICT)
    b = _polarity(PHASE_B_VERDICT)
    if not (a == "positive" and b == "positive"):
        pytest.skip(
            f"GATED (correct outcome): A={a!r} B={b!r} — Tier C not "
            f"attempted because a phase retired negative/absent."
        )
    from handsoff_loop_tier_c_runner import run_tier_c  # type: ignore

    result = run_tier_c()
    assert result["reached_done"] is True
    assert result["human_touches"] == 1, (
        "the single plain-language approval is the ONLY human touch"
    )
