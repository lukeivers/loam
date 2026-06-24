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

"""AC.RCT.2 — the lift is reported on the near-tie subset SEPARATELY
from uniform lift. Uniform lift everywhere = generic perturbation, not
the mechanism earning its place (the flagged-vs-unflagged discriminator,
mirrors AC.MGRL.6).
"""

from __future__ import annotations

import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent.parent / "eval"
if str(_EVAL.parent) not in sys.path:
    sys.path.insert(0, str(_EVAL.parent))

from eval import harness  # noqa: E402


def test_AC_RCT_2_near_tie_and_non_near_tie_reported_separately():
    res = harness.run_gate_b()
    # Both quantities are computed and distinct fields — the
    # discriminator is reported, not collapsed into one number.
    assert hasattr(res, "gain_on_near_tie")
    assert hasattr(res, "gain_on_non_near_tie")


def test_AC_RCT_2_tie_breaker_is_noop_off_near_tie_subset():
    """The tie-breaker re-orders ONLY near-ties: its effect on the
    non-near-tie subset is exactly 0 (a uniform-everywhere lift would be
    a generic perturbation, NOT the mechanism). This is the structural
    guarantee behind the discriminator."""
    res = harness.run_gate_b()
    assert res.gain_on_non_near_tie == 0.0, (
        "the tie-breaker must be a NO-OP off the near-tie subset; "
        f"gain_on_non_near_tie={res.gain_on_non_near_tie}"
    )
