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

"""AC.SMOKE.6 — variant B reliably exercises the DAY-DERIVED path.

The second smoke re-run sampled a PURE-VACUUM opener for variant B ('afternoons
just disappear, not sure where the time goes' — no concrete pain), so B routed
to the idea-vacuum ladder + deep-research and tripped the featherlight gate.
loam routed CORRECTLY for that input — the defect was the persona script
allowing a contentless opener, not a loam bug.

This AC hardens B's persona brief so its FIRST stop/start answer reliably
describes the day AND names a concrete pain (the claim-summary write-ups), which
the production classifier demotes to a day-derived PARTIAL idea (off the research
ladder). It does NOT loosen AC.SMOKE.3 — variant B is still asserted to reach
zero research there; this AC fixes the INPUT so B reliably presents the
day-derived shape.
"""

from __future__ import annotations

from loam.workspace_bootstrap.translate_in_intake import (
    IdeaRichness,
    _classify_richness,
)
from loam_acceptance_smoke.variants import variant_by_key


# The representative opener the hardened brief prescribes (day + named pain in
# the same first reply) — the shape the role-play LLM is now steered to produce.
_PRESCRIBED_B_OPENER = (
    "honestly I don't think in terms of stop/start — but I'll tell you where my "
    "day goes: I take first-notice-of-loss calls in the mornings, look at "
    "damage photos, and then my whole afternoon is writing up the claim-summary "
    "narratives for the file and the policyholder, and that part just piles up "
    "on me."
)


def test_AC_SMOKE_6_brief_instructs_a_day_with_named_pain_opener():
    """The brief must steer B to name the day + the pile-up in the FIRST reply —
    not a contentless 'time just disappears' vacuum opener."""
    brief = variant_by_key("B").persona_brief.lower()
    # The brief names the concrete pain it must surface in the first answer.
    assert "claim-summary" in brief or "claim summary" in brief
    assert "piles up" in brief or "pile up" in brief
    # The brief explicitly forbids the contentless vacuum opener.
    assert "same reply" in brief or "same first" in brief or "first answer" in brief
    assert "never" in brief  # the negative instruction against the pure vacuum


def test_AC_SMOKE_6_prescribed_opener_classifies_day_derived_not_vacuum():
    """The opener the hardened brief prescribes routes to the DAY-DERIVED path
    (a single concrete pain → PARTIAL), not the idea-vacuum path — so B does NOT
    reach the research seam (the featherlight invariant holds)."""
    richness = _classify_richness(_PRESCRIBED_B_OPENER)
    assert richness is not IdeaRichness.EMPTY, (
        "the prescribed variant-B opener must classify as a day-derived PARTIAL "
        f"idea, got {richness!r} (would route B to the research ladder)"
    )


def test_AC_SMOKE_6_variant_b_still_expects_zero_research():
    """Guard against papering over the gate: variant B's spec still expects NO
    deep-research (AC.SMOKE.3 unchanged); this AC fixes the INPUT, not the gate."""
    assert variant_by_key("B").expect_deep_research is False
