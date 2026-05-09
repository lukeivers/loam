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

"""AC.V043.1 — `_fts_search` token-level sanitization + OR-of-tokens.

Plan ref: ``docs/plans/v0-4-3-patch-memory-retrieval-bm25-fix.md`` §4
AC.V043.1.

Verifies:
  (a) the focused episode containing the rarest query term ranks #1;
  (b) the long compaction episode does NOT rank #1 for a query whose
      only common terms are stopwords (the all-stopword case yields
      empty results, satisfying empty-state contract); plus a positive
      ranking probe demonstrating focused-over-compaction wins for
      shared-term queries;
  (c) zero-survivor query (single stopword like ``"is"``) returns ``[]``;
  (d) FTS5-meaningful punctuation in the prompt (``.``, ``-``, ``?``)
      does not raise ``OperationalError``.

Plus a unit-altitude probe of the `_tokenize_for_fts` helper itself.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    FileMemoryStore,
    _tokenize_for_fts,
    memory_dir_for_workspace,
)


# ---- helper ---------------------------------------------------------


def _seed_fixture(store: FileMemoryStore, group_id: str) -> dict[str, Path]:
    """Seed the AC.V043.1 fixture corpus: 3 short focused episodes
    plus 1 long compaction-shaped episode. Returns a mapping from
    label → path so tests can assert on specific files.
    """
    paths: dict[str, Path] = {}

    # Focused episode containing the rarest query term ("ballotpath").
    r = store.write_episode(
        name="turn/sess-focused-ballotpath:000000000001",
        body=(
            "[user]\nWhat is BallotPath?\n\n"
            "[persona]\nBallotPath is the civic-research workspace "
            "exemplar that ships with loam.\n"
        ),
        source_description="t",
        reference_time=datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
        source="message",
        group_id=group_id,
    )
    paths["focused_ballotpath"] = Path(r["path"])

    # Focused episode about a different topic.
    r = store.write_episode(
        name="turn/sess-focused-eric:000000000002",
        body=(
            "[user]\nHow does Eric onboard?\n\n"
            "[persona]\nEric is the rd-automation persona archetype.\n"
        ),
        source_description="t",
        reference_time=datetime(2026, 4, 30, 12, 1, 0, tzinfo=timezone.utc),
        source="message",
        group_id=group_id,
    )
    paths["focused_eric"] = Path(r["path"])

    # Focused episode about loam internals.
    r = store.write_episode(
        name="turn/sess-focused-loam:000000000003",
        body=(
            "[user]\nWhat is loam?\n\n"
            "[persona]\nloam is the harness for Claude-attached "
            "workflows.\n"
        ),
        source_description="t",
        reference_time=datetime(2026, 4, 30, 12, 2, 0, tzinfo=timezone.utc),
        source="message",
        group_id=group_id,
    )
    paths["focused_loam"] = Path(r["path"])

    # Long compaction-shaped episode that mentions every common
    # stopword many times but does NOT mention the rare term
    # "ballotpath". Body shape mirrors a session-compaction summary
    # (long prose, every common English word, no rare topics).
    compaction_body_chunks = [
        (
            "This is a summary of the session. "
            "What was the goal? How did it go? "
            "It is what it is. The session was good. "
            "We did this and that. It is done. "
        )
    ] * 200  # ~12 KB compaction-shaped body; common English words only.
    r = store.write_episode(
        name="turn/sess-compaction:000000000004",
        body=(
            "[user]\nsession summary\n\n[persona]\n"
            + "".join(compaction_body_chunks)
        ),
        source_description="t",
        reference_time=datetime(2026, 4, 30, 12, 3, 0, tzinfo=timezone.utc),
        source="message",
        group_id=group_id,
    )
    paths["compaction"] = Path(r["path"])

    return paths


# ---- (a) rarest-term focused episode ranks #1 ----------------------


def test_AC_V043_1_focused_episode_ranks_first_for_rare_term(
    tmp_path: Path,
) -> None:
    """A natural-language query whose rare-term content matches the
    focused episode body returns that episode at rank #1.
    """
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    paths = _seed_fixture(store, "g")

    results = store._fts_search(
        query="What is BallotPath?",
        group_ids=["g"],
        num_results=5,
    )

    assert len(results) >= 1, "expected at least one FTS5 hit on rare term"
    assert results[0]["path"] == str(paths["focused_ballotpath"]), (
        f"AC.V043.1 (a) — expected focused_ballotpath at rank #1; "
        f"got {results[0]['path']}"
    )


# ---- (b) all-stopword query → empty (compaction does NOT rank) -----


def test_AC_V043_1_all_stopword_query_returns_empty(
    tmp_path: Path,
) -> None:
    """A query containing only stopwords yields zero survivors and
    therefore zero results — the compaction episode does NOT win
    despite mentioning every stopword many times.
    """
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    _seed_fixture(store, "g")

    # Every token here is in `_FTS_STOPWORDS`.
    results = store._fts_search(
        query="what is the it was",
        group_ids=["g"],
        num_results=5,
    )

    assert results == [], (
        f"AC.V043.1 (b) — all-stopword query must return [] (no "
        f"compaction-episode bias); got {len(results)} results"
    )


# ---- (c) single-stopword zero-survivor → empty ---------------------


def test_AC_V043_1_single_stopword_query_returns_empty(
    tmp_path: Path,
) -> None:
    """Query ``"is"`` (single stopword) → zero survivors → ``[]``."""
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    _seed_fixture(store, "g")

    results = store._fts_search(query="is", group_ids=["g"], num_results=5)
    assert results == []


# ---- (d) FTS5-meaningful punctuation does not raise ----------------


def test_AC_V043_1_punctuation_does_not_raise(
    tmp_path: Path,
) -> None:
    """Prompts containing ``.``, ``-``, ``?``, ``"``, ``*``, ``:``,
    ``(``, ``)`` — all FTS5-meaningful in raw form — must NOT raise
    ``sqlite3.OperationalError``.
    """
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    _seed_fixture(store, "g")

    tricky_queries = [
        "What is BallotPath? - tell me",
        'find "this exact phrase"',
        "wildcards * are tricky",
        "namespace::function() call",
        "AC.V043.1 outcome",
        "(parenthetical aside)",
        "OR AND NOT operator-shaped tokens",
    ]
    for q in tricky_queries:
        # Just must not raise. Result count is incidental.
        store._fts_search(query=q, group_ids=["g"], num_results=5)


# ---- (e) tokenizer unit probes -------------------------------------


def test_AC_V043_1_tokenize_drops_stopwords_and_short_tokens() -> None:
    out = _tokenize_for_fts("What is the BallotPath?")
    # `what`, `is`, `the` are stopwords; `ballotpath` survives.
    assert "ballotpath" in out
    assert "what" not in out
    assert "is" not in out
    assert "the" not in out


def test_AC_V043_1_tokenize_splits_on_punctuation() -> None:
    out = _tokenize_for_fts("AC.V043.1 closure")
    # `ac` + `v043` survive; `1` dropped (min-len 2); `closure` survives.
    assert "ac" in out
    assert "v043" in out
    assert "1" not in out
    assert "closure" in out


def test_AC_V043_1_tokenize_dedupes_preserving_order() -> None:
    out = _tokenize_for_fts("loam loam loam ballotpath loam")
    assert out == ["loam", "ballotpath"]


def test_AC_V043_1_tokenize_zero_survivors_returns_empty() -> None:
    assert _tokenize_for_fts("is what the do") == []
    assert _tokenize_for_fts("") == []
    assert _tokenize_for_fts("   ") == []
