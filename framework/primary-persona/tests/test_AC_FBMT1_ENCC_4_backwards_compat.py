"""AC.FBMT1.ENCC.4 — pre-amendment memory files remain readable.

Existing memory files written by the M-FBM worker (pre-amendment)
are still readable by the retrieval contributor and the FileMemoryStore
— backwards-compat verification. The retrieval contributor returns
them without error; the parsed representation reports ``context``
absent / falsy.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.ENCC family + §15 backwards-compat.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    FileMemoryStore,
    _split_frontmatter,
)


def test_AC_FBMT1_ENCC_4_pre_amendment_file_parses_without_context(tmp_path: Path):
    """A memory file that pre-dates amendment #134 (no ``context:``
    block in its frontmatter) parses cleanly; the parsed
    representation reports ``context`` absent."""
    memory_dir = tmp_path / "memory" / "episodes" / "testgroup" / "2026-05-01"
    memory_dir.mkdir(parents=True)
    # Pre-amendment shape — no ``context:`` block.
    pre_amendment_content = (
        "---\n"
        "name: turn/legacy:abc\n"
        "source: message\n"
        "source_description: legacy stop-hook\n"
        "reference_time: 2026-05-01T08:00:00+00:00\n"
        "group_id: testgroup\n"
        "---\n"
        "[user]\n"
        "legacy turn body\n"
        "\n"
        "[assistant]\n"
        "legacy assistant reply\n"
    )
    (memory_dir / "legacy.md").write_text(
        pre_amendment_content, encoding="utf-8"
    )
    # Parse it back.
    front, body = _split_frontmatter(pre_amendment_content)
    # No context key on a pre-amendment file.
    assert "context" not in front, (
        f"unexpected context key on legacy file: {front!r}"
    )
    # Other fields still parse.
    assert front["name"] == "turn/legacy:abc"
    assert "legacy turn body" in body


def test_AC_FBMT1_ENCC_4_retrieval_returns_legacy_file_cleanly(tmp_path: Path):
    """The retrieval contributor returns a legacy file (no
    context: block) without raising. The file is searchable."""
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)
    # Manually author a legacy file (pre-amendment shape) instead
    # of using write_episode (which now emits context:).
    legacy_dir = memory_dir / "episodes" / "testgroup" / "2026-05-01"
    legacy_dir.mkdir(parents=True)
    legacy_content = (
        "---\n"
        "name: turn/legacy:abc\n"
        "source: message\n"
        "source_description: legacy stop-hook\n"
        "reference_time: 2026-05-01T08:00:00+00:00\n"
        "group_id: testgroup\n"
        "---\n"
        "quokka platypus legacy content\n"
    )
    (legacy_dir / "legacy.md").write_text(legacy_content, encoding="utf-8")
    # Search for a term that matches the legacy file.
    result = store.search(
        query="quokka platypus",
        group_ids=["testgroup"],
        num_results=5,
    )
    episodes = result["episodes"]
    assert any("legacy.md" in ep["path"] for ep in episodes), (
        f"legacy file not surfaced by retrieval; got {episodes}"
    )


def test_AC_FBMT1_ENCC_4_mixed_corpus_both_parse_cleanly(tmp_path: Path):
    """A corpus carrying BOTH legacy files (no context: block) and
    new files (with context: block) parses cleanly across the mix.
    The parser handles both shapes — that is the backwards-compat
    contract (the retrieval path's index-coverage is orthogonal)."""
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)
    # Legacy file authored by hand.
    legacy_dir = memory_dir / "episodes" / "testgroup" / "2026-05-01"
    legacy_dir.mkdir(parents=True)
    legacy_content = (
        "---\n"
        "name: turn/legacy:abc\n"
        "reference_time: 2026-05-01T08:00:00+00:00\n"
        "group_id: testgroup\n"
        "---\n"
        "alpha legacy body\n"
    )
    (legacy_dir / "legacy.md").write_text(legacy_content, encoding="utf-8")
    # New-shape file via the writer.
    store.write_episode(
        name="turn/modern",
        body="alpha modern body",
        source_description="modern stop-hook",
        reference_time=datetime(2026, 5, 21, 10, 0, 0, tzinfo=timezone.utc),
        source="message",
        group_id="testgroup",
        context={
            "triggering_msg_id": "msg-1",
            "active_task_id": "task-1",
            "cwd": "/p",
            "active_files": ["x.py"],
        },
    )
    # Both files parse cleanly.
    legacy_front, _ = _split_frontmatter(legacy_content)
    assert legacy_front["name"] == "turn/legacy:abc"
    assert "context" not in legacy_front

    modern_files = list(
        (memory_dir / "episodes" / "testgroup").rglob("modern.md")
    )
    assert modern_files
    modern_text = modern_files[0].read_text(encoding="utf-8")
    modern_front, _ = _split_frontmatter(modern_text)
    assert "context" in modern_front
    assert modern_front["context"]["triggering_msg_id"] == "msg-1"

    # Retrieval doesn't raise on the mixed corpus (the legacy file
    # may not surface if it predates the FTS5 index, but the call
    # completes cleanly without errors).
    result = store.search(
        query="modern",
        group_ids=["testgroup"],
        num_results=5,
    )
    assert "episodes" in result
