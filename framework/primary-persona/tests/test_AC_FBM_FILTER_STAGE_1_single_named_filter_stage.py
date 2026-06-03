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

"""AC-FBM-FILTER-STAGE-1 (Slice B / B3) — ONE systematic filter stage.

The salience gate, the absolute relevance floor, and the near-duplicate dedup are
a single named pre-merge filter stage inside ``_merge_by_score`` — no per-case
relevance or duplicate signature lives outside it. This is the structural
retirement of the reactive-patch pattern (the whack-a-mole the parent plan names):
the next "a weak/duplicate thing surfaced" class is absorbed by tuning the three
named constants, not by adding a sixth signature or a new retrieval entry point.
"""

from __future__ import annotations

import inspect

from loam.primary_persona.keep_pace import retrieval


def test_AC_FBM_FILTER_STAGE_1_three_named_constants_exist() -> None:
    """The three filter mechanisms are NAMED, tunable module constants — the
    single systematic stage, not scattered magic numbers."""
    assert isinstance(retrieval.SALIENCE_THRESHOLD, float)
    assert isinstance(retrieval.EPISODE_MIN_RELEVANCE_SCORE, float)
    assert isinstance(retrieval.DEDUP_JACCARD_THRESHOLD, float)


def test_AC_FBM_FILTER_STAGE_1_all_three_consumed_in_merge() -> None:
    """All three filter constants are consumed inside the ONE merge function —
    the systematic stage. No mechanism lives in a separate per-case patch."""
    src = inspect.getsource(retrieval._merge_by_score)
    # The salience gate (existing) + the two Slice-B mechanisms are all wired
    # through _merge_by_score, directly or via its named helpers.
    assert "salience_threshold" in src, "salience gate runs in the merge stage"
    assert "_apply_episode_floor" in src or "EPISODE_MIN_RELEVANCE_SCORE" in src, (
        "the absolute floor runs in the merge stage"
    )
    assert "_dedup_hits" in src or "DEDUP_JACCARD_THRESHOLD" in src, (
        "the dedup runs in the merge stage"
    )


def test_AC_FBM_FILTER_STAGE_1_no_separate_retrieval_entry_point_added() -> None:
    """The consolidation did NOT add a new public retrieval entry point — the
    one production surface is still ``retrieve`` (the reactive-patch pattern is
    retired by extending the single stage, not by bolting on a new path)."""
    public = {n for n in dir(retrieval) if not n.startswith("_")}
    # The single production entry point + its contributor factories are the only
    # public retrieval surfaces; no new "filter"/"dedup"/"floor" public verb was
    # introduced (the mechanisms are internal helpers of the one stage).
    assert "retrieve" in public
    leaked = {
        n
        for n in public
        if n.endswith("_filter") or n.endswith("_dedup") or n.endswith("_floor")
    }
    assert not leaked, f"no new public filter entry point should leak; got {leaked}"
