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

"""AC.V043.2 — `_grep_search` length-normalization (sqrt path).

Plan ref: ``docs/plans/v0-4-3-patch-memory-retrieval-bm25-fix.md`` §4
AC.V043.2.

Verifies the focused episode ranks above the giant compaction
episode despite lower raw term-occurrence count, because the
ranker now divides by ``sqrt(doclen)``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    FileMemoryStore,
    memory_dir_for_workspace,
)


def test_AC_V043_2_focused_episode_outranks_compaction_despite_lower_raw_count(
    tmp_path: Path,
) -> None:
    """Fixture:
      - One ~100 KB compaction-shaped episode that mentions every
        query term ≥10 times.
      - One ~2 KB focused episode that mentions the rarest query
        term twice and matches no other terms.

    Pre-V043.2 (raw count): compaction wins because raw count is
    higher (≥10 of every term) than focused (2 of one term).
    Post-V043.2 (sqrt normalization): focused wins because
    2/sqrt(2KB) > 30/sqrt(100KB).
    """
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)

    # Force the FTS index to be unavailable so search() falls through
    # to _grep_search. Easiest way: delete the index after the writes
    # land but before the search.

    # Write compaction-shaped episode: ~100 KB, mentions every query
    # term ≥10 times each across the whole body. Uses three query
    # terms: "ballotpath", "schema", "civic". Filler body is neutral
    # English prose to reach the size target without adding more
    # query-term hits (matches the AC spec).
    filler_chunk = (
        "session compaction summary: the user asked about many "
        "things and the persona answered with many context blocks "
        "and the session was long with ack-first audit-block "
        "language and translation rule reminders. lots of words. "
    )
    seed_body = (
        "[user]\nsession summary\n\n[persona]\n"
        + (
            "ballotpath came up. schema came up. civic came up. "
        ) * 10  # 10x of every query term — matches the AC spec.
        + filler_chunk * 400  # neutral filler to reach ~100 KB body.
    )
    compaction_body = seed_body
    compaction_r = store.write_episode(
        name="turn/compaction:000000000001",
        body=compaction_body,
        source_description="t",
        reference_time=datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
        source="message",
        group_id="g",
    )

    # Write focused episode: ~2 KB, mentions only the rarest term
    # ("ballotpath") and just twice. Padded with neutral filler.
    focused_body = (
        "[user]\nWhat is BallotPath?\n\n"
        "[persona]\nBallotPath is the civic-research workspace "
        "exemplar that ships with loam. BallotPath helps voters "
        "research candidates and ballot measures.\n"
        + ("Padding line for length control.\n" * 30)
    )
    focused_r = store.write_episode(
        name="turn/focused:000000000002",
        body=focused_body,
        source_description="t",
        reference_time=datetime(2026, 4, 30, 12, 1, 0, tzinfo=timezone.utc),
        source="message",
        group_id="g",
    )

    # Delete the FTS index file so the grep fallback path is exercised
    # (the writer calls `_index_episode` which auto-builds the index;
    # rip it down to force grep).
    from loam.primary_persona.file_memory import SEARCH_INDEX_NAME

    if store._conn is not None:
        store._conn.close()
        store._conn = None
    (memory_dir / SEARCH_INDEX_NAME).unlink(missing_ok=True)

    # Confirm body sizes match the AC fixture spec (sanity assertion;
    # if the chunk repeat count drifts the AC's empirical premise
    # changes too).
    compaction_path = Path(compaction_r["path"])
    focused_path = Path(focused_r["path"])
    assert compaction_path.stat().st_size > 50_000, (
        "compaction fixture must be >>50 KB to exercise length bias"
    )
    assert focused_path.stat().st_size < 5_000, (
        "focused fixture must stay small to verify length normalization"
    )

    # Grep-rank the corpus on a query that hits both episodes.
    results = store._grep_search(
        query="ballotpath",
        group_ids=["g"],
        num_results=5,
    )
    assert len(results) >= 2, (
        f"expected both episodes scored; got {len(results)}"
    )
    # Top result MUST be focused, not compaction. This is the
    # AC.V043.2 outcome.
    assert results[0]["path"] == str(focused_path), (
        f"AC.V043.2 — expected focused at rank #1 (length-normalized "
        f"win); got {results[0]['path']}"
    )


def test_AC_V043_2_zero_match_episode_skipped(
    tmp_path: Path,
) -> None:
    """An episode whose content matches no query term is skipped
    (raw_score==0 guard above the divide; mirrors the pre-V043
    skip)."""
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)

    store.write_episode(
        name="turn/x:000000000001",
        body="[user]\nhello world\n\n[persona]\nfoo bar\n",
        source_description="t",
        reference_time=datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
        source="message",
        group_id="g",
    )

    results = store._grep_search(
        query="completely-absent-term",
        group_ids=["g"],
        num_results=5,
    )
    assert results == []
