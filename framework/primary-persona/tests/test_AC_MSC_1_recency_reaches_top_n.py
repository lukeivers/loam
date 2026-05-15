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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.MSC.1 — recency reaches the top-N (Gap B closed).

Outcome (plan §4 AC.MSC.1): given an episode store containing (a) an
older episode with a strong lexical match to a recency-shaped query
and (b) a newer episode that is the active thread with a
weaker-but-present lexical match, a recency-shaped retrieval surfaces
the newer active-thread episode within the returned top-N. The older
lexically-stronger episode does not crowd the active thread out.

Pre-MSC behaviour (the regression this closes): ``_fts_search``
ordered by pure ``bm25(episodes)`` with ``reference_time UNINDEXED``,
so a stale lexically-strong episode out-ranked the most-recent active
thread and a small top-N never saw it.

Method-in-AC test (plan §4): PASS — the AC pins the outcome
(newer-active reachable in top-N, older-strong not crowding it out),
not the curve. This test asserts the outcome, not the decay function.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    FileMemoryStore,
)


def _store(tmp_path: Path) -> FileMemoryStore:
    return FileMemoryStore(memory_dir=tmp_path / "mem")


def _write(
    store: FileMemoryStore,
    *,
    name: str,
    body: str,
    when: datetime,
    group: str = "ws",
) -> None:
    store.write_episode(
        name=name,
        body=body,
        source_description="test",
        reference_time=when,
        source="test",
        group_id=group,
    )


def test_AC_MSC_1_newer_active_thread_in_top_n(tmp_path: Path) -> None:
    """A recency-shaped query surfaces the newer active-thread episode
    within the top-N even though an older episode has the stronger
    lexical match."""
    store = _store(tmp_path)
    now = datetime.now(timezone.utc)

    # Older episode: STRONG lexical match (repeats the query term many
    # times) but stale (40 days old — well past the 5d half-life).
    _write(
        store,
        name="turn/old-strong",
        body=(
            "programbench programbench programbench programbench "
            "programbench programbench an old answer about "
            "programbench tuning from weeks ago programbench"
        ),
        when=now - timedelta(days=40),
    )
    # Newer episode: the ACTIVE THREAD — weaker-but-present lexical
    # match, written today.
    _write(
        store,
        name="turn/new-active",
        body=(
            "today's active thread: the v0.11.0 corrective and the "
            "programbench v2 experiment owner ruling is pending"
        ),
        when=now - timedelta(hours=2),
    )

    result = store.search(
        query="programbench v2 active thread",
        group_ids=["ws"],
        num_results=2,
    )
    names = [e["name"] for e in result["episodes"]]

    assert "turn/new-active" in names, (
        "the most-recent active-thread episode must be reachable in "
        f"the top-N for a recency-shaped query; got {names}"
    )


def test_AC_MSC_1_older_strong_does_not_crowd_out_active(
    tmp_path: Path,
) -> None:
    """With a single-result cap, the recency blend does not let the
    stale lexically-strong episode crowd the active thread out
    entirely."""
    store = _store(tmp_path)
    now = datetime.now(timezone.utc)
    _write(
        store,
        name="turn/old-strong",
        body=" ".join(["recency"] * 30) + " stale answer",
        when=now - timedelta(days=60),
    )
    _write(
        store,
        name="turn/new-active",
        body="recency-shaped active thread today pending owner ruling",
        when=now - timedelta(minutes=30),
    )

    result = store.search(
        query="recency active thread today",
        group_ids=["ws"],
        num_results=1,
    )
    names = [e["name"] for e in result["episodes"]]
    assert names == ["turn/new-active"], (
        "with num_results=1 the recency blend must surface the "
        f"active thread, not the stale lexically-strong episode; got {names}"
    )


def test_AC_MSC_1_non_recency_query_still_surfaces_relevant_older(
    tmp_path: Path,
) -> None:
    """§12 halt trigger 4 guard: a non-recency query whose only
    relevant answer is an older episode still surfaces that older
    episode — recency must not trade away retrieval quality."""
    store = _store(tmp_path)
    now = datetime.now(timezone.utc)
    # The only episode that answers the question is old.
    _write(
        store,
        name="turn/the-answer",
        body=(
            "the kuzu_db discard is by design per D-Q.MFBM.6 — the "
            "M-FBM file-based pivot intentionally drops the graph store"
        ),
        when=now - timedelta(days=20),
    )
    # Recent noise episodes that do NOT answer the question.
    for i in range(4):
        _write(
            store,
            name=f"turn/noise-{i}",
            body="unrelated recent chatter about scheduling and logs",
            when=now - timedelta(hours=i + 1),
        )

    result = store.search(
        query="why was kuzu_db discarded D-Q.MFBM.6",
        group_ids=["ws"],
        num_results=3,
    )
    names = [e["name"] for e in result["episodes"]]
    assert "turn/the-answer" in names, (
        "a directly-relevant older answer must still surface for a "
        f"non-recency query (recency must not drown relevance); got {names}"
    )
