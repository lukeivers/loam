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

"""AC.WFD.3 — a non-fact is never served AS a verified fact.

Over the read path, a record typed non-fact surfaces marked
not-a-verified-fact (substance still exposed, never silently withheld); a
record typed fact surfaces unmarked. The annotation is keyed on the STORED
``epistemic:`` tag; an absent tag reads as a fact (never-suppress
fail-safe). Mirrors the ``VOLATILE_SOFT_ANNOTATION`` render seam.
"""

from __future__ import annotations

from loam.primary_persona.file_memory import EPISTEMIC_NON_FACT_ANNOTATION
from loam.primary_persona.keep_pace.retrieval import _episode_pointer


def test_AC_WFD_3_non_fact_pointer_is_annotated() -> None:
    non_fact_ep = {
        "content": (
            "[user]\nwhat did you make of the ranker design\n\n[assistant]\n"
            "the ranker design is elegant and clean\n"
        ),
        "name": "turn/op1",
        "epistemic": "non-fact",
    }
    pointer = _episode_pointer(non_fact_ep)
    assert EPISTEMIC_NON_FACT_ANNOTATION in pointer, (
        f"a non-fact pointer must carry the not-a-verified-fact marker: {pointer!r}"
    )
    # Substance still exposed — the summary survives alongside the caution.
    assert "ranker design" in pointer


def test_AC_WFD_3_fact_pointer_is_not_annotated() -> None:
    fact_ep = {
        "content": (
            "[user]\nwhat is the ranker cap\n\n[assistant]\n"
            "the ranked-pool cap is DEFAULT_TOP_N set to 5\n"
        ),
        "name": "turn/fact1",
        "epistemic": "fact",
    }
    pointer = _episode_pointer(fact_ep)
    assert pointer.startswith("From an earlier turn:")
    assert EPISTEMIC_NON_FACT_ANNOTATION not in pointer, (
        f"a fact pointer must NOT be annotated: {pointer!r}"
    )


def test_AC_WFD_3_absent_tag_reads_as_fact() -> None:
    # A record with no stored epistemic tag (legacy / lever-off) reads as a
    # fact — never marked (never-suppress fail-safe).
    tagless_ep = {
        "content": (
            "[user]\nthoughts on the design\n\n[assistant]\n"
            "the design is elegant\n"
        ),
        "name": "turn/legacy1",
    }
    pointer = _episode_pointer(tagless_ep)
    assert EPISTEMIC_NON_FACT_ANNOTATION not in pointer, (
        f"an absent tag must read as a fact (unmarked): {pointer!r}"
    )
