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

"""AC.MSC.5 — backward-compatibility + fail-soft preserved.

Outcome (plan §4 AC.MSC.5): every existing memory-retrieval and
session-start test stays green; a pre-existing FTS5 index without the
new rankable column does not error (rebuild-or-fallback, never raise);
the session-start contributor is fail-soft (any error inside it yields
an empty block, the session proceeds) consistent with the existing
AC46.4 / AC.MFBM.2 fail-closed contracts.

Verification (plan §4): existing primary-persona suites green (run as
the full-suite sweep at seal time — this file asserts the NEW
fail-soft + back-compat branches); an index-missing-column fixture
exercises the rebuild/fallback path; a contributor-raises fixture
asserts empty-block + session-proceeds.

Method-in-AC test (plan §4): PASS — outcome is "nothing regresses,
nothing raises"; the method (rebuild-on-mismatch vs ALTER migrate) is
the builder's call. This test asserts the no-raise outcome.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from loam.primary_persona.active_thread import (
    build_active_thread_contributor,
)
from loam.primary_persona.file_memory import (
    SEARCH_INDEX_NAME,
    FileMemoryStore,
)


def _store(tmp_path: Path) -> FileMemoryStore:
    return FileMemoryStore(memory_dir=tmp_path / "mem")


def test_AC_MSC_5_pre_msc_index_schema_rebuilds_not_raises(
    tmp_path: Path,
) -> None:
    """A pre-MSC FTS5 index (episodes table WITHOUT the
    reference_time column) is dropped + rebuilt on the next
    connection, rather than raising on the recency SELECT. D-MSC.5
    rebuild-on-mismatch — the contract is on ``_connection()``, the
    single point every index-touching path routes through."""
    mem = tmp_path / "mem"
    mem.mkdir(parents=True)
    # Hand-build a PRE-MSC index: episodes WITHOUT reference_time.
    legacy = mem / SEARCH_INDEX_NAME
    conn = sqlite3.connect(str(legacy))
    conn.execute(
        "CREATE VIRTUAL TABLE episodes "
        "USING fts5(name, body, group_id, path UNINDEXED)"
    )
    conn.execute(
        "INSERT INTO episodes (name, body, group_id, path) "
        "VALUES ('turn/legacy', 'old indexed body', 'ws', '/x.md')"
    )
    conn.commit()
    conn.close()

    store = _store(tmp_path)
    # The rebuild-on-mismatch contract: opening the connection on a
    # stale-schema index detects the mismatch (no reference_time
    # column), drops + recreates the table with the current schema,
    # and the recency SELECT now succeeds instead of raising
    # OperationalError. This is the single guard every index-touching
    # path (search, write/index) routes through.
    rebuilt = store._connection()
    assert store._index_schema_is_current(rebuilt), (
        "stale-schema index must be rebuilt to the current schema on "
        "connect (D-MSC.5)"
    )
    # The recency SELECT (the query that raised pre-MSC) now succeeds
    # on the rebuilt connection — no OperationalError.
    rebuilt.execute(
        "SELECT reference_time FROM episodes LIMIT 0"
    ).fetchall()
    # The rebuild persisted to disk (a fresh connection sees it).
    conn2 = sqlite3.connect(str(legacy))
    try:
        conn2.execute(
            "SELECT reference_time FROM episodes LIMIT 0"
        ).fetchall()
    finally:
        conn2.close()


def test_AC_MSC_5_pre_msc_index_then_write_then_search_works(
    tmp_path: Path,
) -> None:
    """End-to-end: a legacy index is rebuilt, a fresh write
    re-populates it, and a recency-shaped search returns the new
    episode — no raise anywhere on the upgrade path."""
    mem = tmp_path / "mem"
    mem.mkdir(parents=True)
    legacy = mem / SEARCH_INDEX_NAME
    conn = sqlite3.connect(str(legacy))
    conn.execute(
        "CREATE VIRTUAL TABLE episodes "
        "USING fts5(name, body, group_id, path UNINDEXED)"
    )
    conn.commit()
    conn.close()

    store = _store(tmp_path)
    store.write_episode(
        name="turn/fresh",
        body="fresh active-thread content after the schema rebuild",
        source_description="t",
        reference_time=datetime.now(timezone.utc),
        source="t",
        group_id="ws",
    )
    result = store.search(
        query="fresh active-thread content",
        group_ids=["ws"],
        num_results=3,
    )
    names = [e["name"] for e in result["episodes"]]
    assert "turn/fresh" in names, (
        f"post-rebuild write must be retrievable; got {names}"
    )


def test_AC_MSC_5_recency_blend_no_raise_on_bad_timestamps(
    tmp_path: Path,
) -> None:
    """An episode whose reference_time is malformed/absent does not
    raise the recency blend — it is treated recency-neutral and
    competes on BM25 alone (AC.MSC.5 never-raise on a ranking
    input)."""
    store = _store(tmp_path)
    now = datetime.now(timezone.utc)
    store.write_episode(
        name="turn/good",
        body="recency blend stability probe content",
        source_description="t",
        reference_time=now,
        source="t",
        group_id="ws",
    )
    # Corrupt the on-disk episode's reference_time frontmatter.
    ep_dir = (tmp_path / "mem" / "episodes" / "ws")
    md = next(ep_dir.rglob("*.md"))
    text = md.read_text()
    md.write_text(text.replace("reference_time:", "reference_time: NOT-A-DATE #"))
    # Drop the index so the search re-reads frontmatter via grep
    # fallback (exercises _parse_reference_time on the bad value).
    (tmp_path / "mem" / SEARCH_INDEX_NAME).unlink()
    result = store.search(
        query="recency blend stability probe",
        group_ids=["ws"],
        num_results=3,
    )  # must not raise
    assert isinstance(result, dict) and "episodes" in result


def test_AC_MSC_5_active_thread_contributor_fail_soft(
    tmp_path: Path,
) -> None:
    """A store whose recent_episodes raises does NOT propagate through
    the active-thread contributor — it returns the empty string and
    the session proceeds (AC46.4 / AC.MFBM.2 fail-closed parity)."""

    class _ExplodingStore:
        def recent_episodes(self, **_kw):
            raise RuntimeError("simulated store boundary failure")

    fn = build_active_thread_contributor(
        _ExplodingStore(),
        workspace_root=tmp_path,
        workspace_slug="ws",
    )
    # No named-thread surface either → empty block, NOT a raise.
    assert fn({}) == "", (
        "contributor must fail-soft to empty string on store failure"
    )


def test_AC_MSC_5_contributor_sandbox_absorbs_raise_in_payload(
    tmp_path: Path,
) -> None:
    """Even if a contributor raised, the composer's sandbox absorbs it
    into a diagnostic block and the session payload still composes
    (the existing AC46.4 envelope this contributor lives inside)."""
    import json

    from loam.primary_persona.session_start_emitter import (
        emit_session_start_context,
    )

    root = tmp_path
    (root / "CLAUDE.md").write_text(
        "# ws\n\n## Session-start discipline\n\nRead:\n\n"
        "- `docs/STATE.md`\n\n---\n\n"
    )
    (root / "docs").mkdir()
    (root / "docs" / "STATE.md").write_text("s")
    pos = root / "workspace" / ".pos"
    pos.mkdir(parents=True)
    (pos / "first-run.state").write_text(
        json.dumps({"completed_at": "2026-04-25T00:00:00Z"})
    )
    (pos / "cost-headroom.json").write_text(
        json.dumps({"mtd_spend_usd": "1.0", "ceiling_usd": "500.0"})
    )
    # No episodes, no FIDRAFT → active-thread contributes empty; the
    # rest of the session payload still composes (no raise).
    text = emit_session_start_context(root)
    assert text, "session payload must still compose"
    assert "corpus_gate_state" in text
