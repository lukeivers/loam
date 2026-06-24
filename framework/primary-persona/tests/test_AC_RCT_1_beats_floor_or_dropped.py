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

"""AC.RCT.1 — the tie-breaker beats the BM25 floor with a paired BCa
bootstrap CI lower-bound > 0 AND permutation p < 0.05, ELSE it is
NOT-EARNED and does not ship (the pre-committed drop rule).

This test verifies the VERDICT RULE is applied without further judgment:
it runs the real Gate B (paired bootstrap + permutation) and asserts the
verdict is computed correctly from the CI + p + concentration — NOT that
the tie-breaker passes. The plan PREDICTS a null (CI straddling zero);
the honest outcome is NOT-EARNED, recorded as a valid null. The test
fails only if the verdict logic is wrong, or if a NOT-EARNED result were
to be mis-reported as EARNED.
"""

from __future__ import annotations

import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent.parent / "eval"
if str(_EVAL.parent) not in sys.path:
    sys.path.insert(0, str(_EVAL.parent))

from eval import harness  # noqa: E402


def test_AC_RCT_1_verdict_rule_applied_without_judgment():
    res = harness.run_gate_b()
    # The verdict is a deterministic function of (CI lower bound, p,
    # concentration). Re-derive it and assert the harness applied the
    # SAME pre-committed rule.
    earned = (
        res.ci_lower > 0
        and res.perm_p < 0.05
        and res.gain_on_non_near_tie == 0.0
        and res.gain_on_near_tie > 0
    )
    expected = "EARNED" if earned else "NOT-EARNED"
    assert res.verdict == expected, (
        f"verdict mis-applied: ci_lower={res.ci_lower} p={res.perm_p} "
        f"near={res.gain_on_near_tie} non_near={res.gain_on_non_near_tie} "
        f"-> harness said {res.verdict}, rule says {expected}"
    )


def test_AC_RCT_1_ci_is_real_not_asserted():
    """The CI must be an actual paired-bootstrap interval (lower <=
    point <= upper), not a hand-asserted band — the measurement is real."""
    res = harness.run_gate_b()
    assert res.ci_lower <= res.ci_point <= res.ci_upper, (
        f"CI must bracket the point estimate; got "
        f"[{res.ci_lower}, {res.ci_point}, {res.ci_upper}]"
    )
    assert 0.0 <= res.perm_p <= 1.0


def test_AC_RCT_1_not_earned_does_not_ship():
    """If NOT-EARNED (the predicted outcome), the drop rule fires: the
    tie-breaker is not wired into the production search path (it stays a
    separate default-OFF function). This pins the pre-committed drop
    rule structurally — a NOT-EARNED verdict must coincide with the
    tie-breaker being absent from the production ranker."""
    res = harness.run_gate_b()
    if res.verdict == "NOT-EARNED":
        # The production search path must NOT reference the tie-breaker.
        fm_src = (
            Path(__file__).resolve().parent.parent
            / "src" / "loam" / "primary_persona" / "file_memory.py"
        ).read_text(encoding="utf-8")
        assert "reference_count_tiebreak" not in fm_src, (
            "a NOT-EARNED tie-breaker must NOT be wired into the "
            "production ranker (the pre-committed drop rule)"
        )
