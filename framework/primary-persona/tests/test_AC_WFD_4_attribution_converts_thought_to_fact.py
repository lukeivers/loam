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

"""AC.WFD.4 — attribution converts a thought into a fact.

The tension-dissolving move (Fork B): a thought authored WITH an
attribution (an author + a time) is fact-eligible — the utterance-event is
provable even when its content is an opinion. The SAME content as a bare
truth-claim is not. Attribution requires BOTH who and when.
"""

from __future__ import annotations

from loam.primary_persona.file_memory import (
    EPISTEMIC_FACT,
    EPISTEMIC_NON_FACT,
    classify_epistemic_type,
)


def test_AC_WFD_4_attributed_thought_is_fact() -> None:
    # Same evaluative content as the bare form below, but authored as a
    # provable utterance-event (who + when).
    attributed = "Luke said the design is elegant on 2026-07-02"
    assert classify_epistemic_type(attributed) == EPISTEMIC_FACT


def test_AC_WFD_4_bare_thought_is_not_a_fact() -> None:
    bare = "the design is elegant"
    assert classify_epistemic_type(bare) == EPISTEMIC_NON_FACT


def test_AC_WFD_4_attribution_needs_both_author_and_time() -> None:
    # An author with NO time is not a complete attributed record; it fails
    # SAFE to fact (never-suppress) rather than being asserted as ground
    # truth, but the point stands: the temporal anchor is required for the
    # veto to fire on an otherwise-bare opinion.
    with_time = "Luke predicted on 2026-07-02 that the funding would probably land"
    no_time_bare_prediction = "the funding will probably land"
    assert classify_epistemic_type(with_time) == EPISTEMIC_FACT
    assert classify_epistemic_type(no_time_bare_prediction) == EPISTEMIC_NON_FACT
