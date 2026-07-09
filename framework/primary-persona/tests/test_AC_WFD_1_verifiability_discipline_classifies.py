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

"""AC.WFD.1 — the verifiability discipline classifies candidates correctly.

``classify_epistemic_type`` is deterministic + stdlib-only. It yields the
fact-eligible verdict for the fact classes (event / state-after-work /
verified finding / attributed expression) and the not-a-fact verdict for
the bare non-fact classes (opinion / speculation / plan). The one-line
test: "could someone else, given the cited source, confirm this happened
or is true?"
"""

from __future__ import annotations

import pytest

from loam.primary_persona.file_memory import (
    EPISTEMIC_FACT,
    EPISTEMIC_NON_FACT,
    classify_epistemic_type,
)


# One row per named FACT class — each is fact-eligible.
FACT_CASES = [
    ("event-occurred", "we sealed the volatility amendment and the suite went green"),
    ("state-after-work", "the build branch is at commit a1166b8d after the apply"),
    ("verified-finding", "the ranked-pool cap is DEFAULT_TOP_N set to 5"),
    ("attributed-opinion", "Luke assessed the ranker design as elegant on 2026-07-02"),
    (
        "attributed-utterance",
        "Luke said god damn it that was annoying on 2026-06-14",
    ),
    # A hedged FINDING is still a fact — the durable-fact signal ("passed")
    # vetoes the "I think" hedge (§16.2's named limitation, handled).
    ("hedged-fact-durable-veto", "i think the test passed"),
]

# One row per named NON-FACT class — each is a bare thought, not a fact.
NON_FACT_CASES = [
    ("bare-opinion", "the ranker design is elegant"),
    ("bare-opinion-hedged", "i think this refactor is the cleanest approach"),
    ("bare-prediction", "the tilth funding will probably come through next quarter"),
    ("bare-speculation", "i suspect the bug is somewhere in the frontmatter parser"),
    ("bare-plan", "next i'll wire the read-side annotation and then ship"),
    ("bare-intent", "the plan is to rework the ranker tonight"),
    ("clear-opinion", "honestly this whole design is gorgeous"),
]


@pytest.mark.parametrize("label,text", FACT_CASES, ids=[c[0] for c in FACT_CASES])
def test_AC_WFD_1_fact_classes_are_fact_eligible(label: str, text: str) -> None:
    assert classify_epistemic_type(text) == EPISTEMIC_FACT, (
        f"{label!r} should be fact-eligible: {text!r}"
    )


@pytest.mark.parametrize(
    "label,text", NON_FACT_CASES, ids=[c[0] for c in NON_FACT_CASES]
)
def test_AC_WFD_1_non_fact_classes_are_not_facts(label: str, text: str) -> None:
    assert classify_epistemic_type(text) == EPISTEMIC_NON_FACT, (
        f"{label!r} should classify not-a-fact: {text!r}"
    )
