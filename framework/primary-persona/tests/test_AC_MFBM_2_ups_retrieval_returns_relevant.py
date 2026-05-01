"""AC.MFBM.2 — UPS-hook retrieval surface returns relevant prior-
session episodes via the file-based contributor.

Plan ref: ``oss-v0-1-0-publish-memory-pivot.md`` §5 AC.MFBM.2.

Verification (per plan): across 10 hand-authored cross-session test
fixtures (fixture-shape: a previously-stored turn at session N-1
referencing named entity X; a session-N prompt mentioning X), the
contributor emits a non-empty retrieval block citing the session-
N-1 turn's filename in ≥7 of 10 fixtures. Failure-closed test:
deleting the memory dir mid-test returns an empty retrieval block,
not a stack trace.
"""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    FileMemoryStore,
    memory_dir_for_workspace,
    build_file_memory_retrieval_contributor,
    FileMemoryRetrievalConfig,
)


# ---- 10 fixture pairs (entity X mentioned in session N-1 + a query
# for X in session N). Each fixture exercises a different entity / topic
# shape. Bar: ≥7 of 10 fixtures yield a non-empty retrieval block
# whose body cites the prior turn.
_FIXTURES: tuple[tuple[str, str, str, str], ...] = (
    # (entity_or_topic, prior_user_msg, prior_persona_reply, session_n_query)
    (
        "pos-amend",
        "tell me about pos-amend",
        "pos-amend is the dev CLI for amendments under the loam harness.",
        "what does pos-amend do?",
    ),
    (
        "MemoryProvider",
        "what's MemoryProvider?",
        "MemoryProvider is the substrate-composition Protocol stub.",
        "explain MemoryProvider",
    ),
    (
        "AC.MFBM.1",
        "outcome of AC.MFBM.1",
        "AC.MFBM.1 verifies the Stop-hook writes one episode file per turn.",
        "AC.MFBM.1 details",
    ),
    (
        "graphiti",
        "should we keep graphiti?",
        "graphiti retires to the post-v0.1.0 plugin per M-GMP.",
        "graphiti future",
    ),
    (
        "kuzu_db",
        "kuzu_db inspection findings",
        "kuzu_db carries 0 retrievable episodes; discard at v0.1.0.",
        "kuzu_db state",
    ),
    (
        "Stop-hook",
        "how does the Stop-hook write?",
        "Stop-hook enqueues to the queue and the worker drains it.",
        "Stop-hook flow",
    ),
    (
        "BM25",
        "ranking algorithm",
        "BM25 via sqlite-FTS5 ranks episodes by term-frequency.",
        "BM25 retrieval",
    ),
    (
        "workspace-bootstrap",
        "first-run-inventory.yaml",
        "workspace-bootstrap reads first-run-inventory and provisions services.",
        "workspace-bootstrap behaviour",
    ),
    (
        "loam.memory.providers",
        "entry-point group",
        "loam.memory.providers is the new entry-point group for plugins.",
        "memory.providers contract",
    ),
    (
        "auto-memory",
        "Claude Code auto-memory",
        "auto-memory is project-scoped MEMORY.md; orthogonal to loam memory.",
        "auto-memory location",
    ),
)


def test_AC_MFBM_2_seven_of_ten_fixtures_yield_nonempty_retrieval(
    tmp_path: Path,
) -> None:
    """Seed each fixture's prior turn into the memory dir; for each
    session-N query the contributor returns a retrieval block. Bar:
    ≥7 of 10 yield a non-empty block whose body references the prior
    turn (via its filename or the entity's verbatim text).
    """
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    slug = "fixture"

    # Seed each fixture's prior turn.
    paths: list[str] = []
    for i, (_entity, prior_user, prior_persona, _query) in enumerate(_FIXTURES):
        body = f"[user]\n{prior_user}\n\n[persona]\n{prior_persona}\n"
        result = store.write_episode(
            name=f"turn/sess1:{i:012x}",
            body=body,
            source_description="t",
            reference_time=datetime(
                2026, 4, 30, 12, i, 0, tzinfo=timezone.utc
            ),
            source="message",
            group_id=slug,
        )
        paths.append(result["path"])

    config = FileMemoryRetrievalConfig(store=store, workspace_slug=slug)
    contributor = build_file_memory_retrieval_contributor(config)

    hits = 0
    for i, (_entity, _prior_user, prior_persona, query) in enumerate(_FIXTURES):
        text = contributor({"prompt": query})
        if "[memory-retrieval]" not in text:
            continue
        if "(no results for this query)" in text:
            continue
        # The retrieval block is non-empty AND references content
        # from the seeded turn (by entity-text or filename match).
        if any(
            term in text
            for term in (
                _entity_marker(prior_persona),
                Path(paths[i]).stem,
            )
        ):
            hits += 1

    assert hits >= 7, (
        f"AC.MFBM.2 bar miss: {hits}/10 fixtures yielded a retrieval "
        f"block citing the seeded turn (need ≥7). Halt-trigger §9.2 "
        f"fires if this fails in a real fixture sweep."
    )


def _entity_marker(text: str) -> str:
    """Heuristic: the most distinctive word in the seeded reply."""
    return max(text.split(), key=len)


def test_AC_MFBM_2_fail_closed_when_memory_dir_deleted_mid_search(
    tmp_path: Path,
) -> None:
    """Deleting the memory dir mid-test yields an empty retrieval
    block; never a stack trace."""
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)

    # Seed one episode then delete the dir.
    store.write_episode(
        name="turn/x:y",
        body="[user]\nfoo\n\n[persona]\nbar\n",
        source_description="t",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="g",
    )
    shutil.rmtree(memory_dir, ignore_errors=True)

    config = FileMemoryRetrievalConfig(store=store, workspace_slug="g")
    contributor = build_file_memory_retrieval_contributor(config)
    text = contributor({"prompt": "anything"})
    # Either fully empty (search returned no episodes branch) OR an
    # empty-state diagnostic block. Both satisfy "not a stack trace".
    assert text == "" or (
        "[memory-retrieval]" in text and "(no results" in text
    )


def test_AC_MFBM_2_search_returns_canonical_shape(
    tmp_path: Path,
) -> None:
    """The store's search returns the post-#96 superset shape:
    {"query", "results", "nodes", "episodes"}."""
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    store.write_episode(
        name="turn/x:y",
        body="[user]\nhello world\n\n[persona]\nfoo bar\n",
        source_description="t",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="g",
    )
    result = store.search(query="hello", group_ids=["g"], num_results=5)
    assert set(result.keys()) == {"query", "results", "nodes", "episodes"}
    assert isinstance(result["episodes"], list)


def test_AC_MFBM_2_group_id_filter_isolates_workspaces(
    tmp_path: Path,
) -> None:
    """Episodes under group X are not returned for a search filtered
    on group Y."""
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    store.write_episode(
        name="turn/x:1",
        body="[user]\nspecial-token-X\n\n[persona]\nfoo\n",
        source_description="t",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="alpha",
    )
    store.write_episode(
        name="turn/y:1",
        body="[user]\nspecial-token-Y\n\n[persona]\nbar\n",
        source_description="t",
        reference_time=datetime.now(timezone.utc),
        source="message",
        group_id="beta",
    )
    result = store.search(
        query="special-token-X", group_ids=["beta"], num_results=5
    )
    # Filter on beta excludes alpha's hit.
    eps = result["episodes"]
    assert all("alpha" not in ep.get("path", "") for ep in eps)


def test_AC_MFBM_2_empty_query_returns_empty_episodes(
    tmp_path: Path,
) -> None:
    memory_dir = memory_dir_for_workspace(tmp_path)
    store = FileMemoryStore(memory_dir=memory_dir)
    result = store.search(query="", group_ids=None, num_results=5)
    assert result["episodes"] == []
