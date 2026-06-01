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

"""AC.SMOKE.3 — variant C and ONLY variant C triggers deep-role-research, and
its run stays within the sealed ≤3 round-trip budget; A and B reach zero
research (the featherlight invariant AC.DRRSEAM.2 holds end-to-end).

Drives the real ``judge._score_deep_research`` scorer over synthetic runs so
the gating verdict is proven without paying for live spawns.
"""

from __future__ import annotations

from pathlib import Path

from loam_acceptance_smoke.judge import _score_deep_research
from loam_acceptance_smoke.runner import VariantRun
from loam_acceptance_smoke.variants import variant_by_key


def _run(key: str, *, invoked: bool, roundtrips=None, stub=None) -> VariantRun:
    return VariantRun(
        variant=variant_by_key(key),
        workspace_root=Path("/tmp/x"),
        global_home=Path("/tmp/x/.claude"),
        invoked_deep_research=invoked,
        research_roundtrips=roundtrips,
        research_is_stub=stub,
    )


def test_AC_SMOKE_3_variant_C_fires_within_budget_passes():
    score = _score_deep_research(_run("C", invoked=True, roundtrips=3))
    assert score.verdict == "PASS", score.evidence
    assert "budget" in score.evidence.lower()


def test_AC_SMOKE_3_variant_C_not_firing_fails():
    score = _score_deep_research(_run("C", invoked=False))
    assert score.verdict == "FAIL"
    assert "should trigger" in score.evidence.lower()


def test_AC_SMOKE_3_variant_C_over_budget_fails():
    score = _score_deep_research(_run("C", invoked=True, roundtrips=5))
    assert score.verdict == "FAIL"
    assert "budget" in score.evidence.lower()


def test_AC_SMOKE_3_variant_A_zero_research_passes():
    score = _score_deep_research(_run("A", invoked=False))
    assert score.verdict == "PASS"
    assert "zero research" in score.evidence.lower()


def test_AC_SMOKE_3_variant_B_invoking_research_fails_featherlight():
    # An idea-rich/day-derived variant reaching the seam breaks the invariant.
    score = _score_deep_research(_run("B", invoked=True, roundtrips=2))
    assert score.verdict == "FAIL"
    assert "featherlight" in score.evidence.lower()
