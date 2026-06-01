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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.SMOKE.7 — the ``four-step-loop-ran`` rubric is CONTRACT-ALIGNED to the
owner's ratified one-rung default-ask close.

The old rubric demanded leg 2 show committed CONCRETE STRUCTURE (a recurring
workflow / template / designed enablement pattern) while ``no-over-engineering``
PASSED precisely BECAUSE loam proposed no structure — the two dimensions demanded
OPPOSITE things on the same transcript (rerun12 A+B PARTIAL/PASS contradiction).

Owner ruling (Luke 13401 + 13403): the close LANDS the literal ask as the ONE
thing and BY DEFAULT ASKS about EXACTLY ONE rung up (opt-in), suppressed only on a
clear one-off signal. The aligned rubric REWARDS that one-rung opt-in default-ask,
PENALIZES jumping two+ rungs / asserting structure / failing to offer the ask
absent a suppressing signal, and no longer demands committed concrete structure.
This is a contract-ALIGNMENT (the old rubric demanded the OPPOSITE of the ratified
design), NOT a bar-lowering.
"""

from __future__ import annotations

from loam_acceptance_smoke.judge import SOFT_DIMENSIONS


def _rubric() -> str:
    return SOFT_DIMENSIONS["four-step-loop-ran"].lower()


def test_AC_SMOKE_7_rubric_rewards_the_one_rung_opt_in_default_ask():
    r = _rubric()
    assert "one rung" in r or "one-rung" in r or "rung up" in r
    assert "opt-in" in r
    assert "default" in r  # the ask is the DEFAULT


def test_AC_SMOKE_7_rubric_penalizes_two_plus_rungs():
    r = _rubric()
    assert "two+" in r or "two or more" in r or "2+" in r
    # naming the forbidden over-jump targets.
    assert "workflow" in r or "system" in r or "framework" in r


def test_AC_SMOKE_7_rubric_penalizes_asserted_structure_instead_of_an_ask():
    r = _rubric()
    assert "assert" in r  # asserted/already-built structure is penalized
    assert "ask" in r


def test_AC_SMOKE_7_rubric_penalizes_missing_ask_absent_a_suppressing_signal():
    r = _rubric()
    assert "suppress" in r or "one-off" in r or "one off" in r
    assert "fail" in r  # the missing-ask case is a FAIL


def test_AC_SMOKE_7_rubric_no_longer_demands_committed_concrete_structure():
    """The contradiction is gone: the rubric explicitly does NOT require committed
    concrete structure (an opt-in ask is the right-sized leg)."""
    r = _rubric()
    assert "do not require" in r and "structure" in r


def test_AC_SMOKE_7_rubric_keeps_all_four_legs_required():
    """The alignment did not drop the four-leg requirement — surfaced hypothesis +
    adapt are still required (no bar-lowering)."""
    r = _rubric()
    assert "hypothesis" in r
    assert "adapt" in r
    assert "four legs" in r or "all four" in r
