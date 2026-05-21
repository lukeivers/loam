"""AC.FBMT1.SUPM.4 — missing supersession target is a soft error.

A ``superseded-by:`` value pointing at a non-existent file is a soft
error (logged via the ranker's warning surface; penalty still applies;
not a crash).

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.SUPM family.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona import file_memory
from loam.primary_persona.file_memory import FileMemoryStore


def test_AC_FBMT1_SUPM_4_missing_target_warning_surfaced(tmp_path: Path):
    """A superseded-by pointing at a non-existent file: ranker
    still runs to completion; a warning is observable in the
    diagnostic surface."""
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)
    ref_time = datetime(2026, 5, 21, 10, 0, 0, tzinfo=timezone.utc)
    store.write_episode(
        name="turn/orphan",
        body="alpha beta gamma",
        source_description="test",
        reference_time=ref_time,
        source="message",
        group_id="testgroup",
    )
    # Annotate with a path that DOES NOT exist anywhere.
    files = list((memory_dir / "episodes" / "testgroup").rglob("*.md"))
    assert files
    path = files[0]
    text = path.read_text(encoding="utf-8")
    annotated = text.replace(
        "group_id: testgroup\n",
        "group_id: testgroup\nsuperseded-by: ./this-path-does-not-exist.md\n",
    )
    path.write_text(annotated, encoding="utf-8")

    # Run search; the call should NOT raise even though the marker
    # target is missing.
    result = store.search(
        query="alpha beta",
        group_ids=["testgroup"],
        num_results=5,
    )
    assert "episodes" in result
    # The warning surface (module-level list) carries the missing-
    # target diagnostic.
    warnings = file_memory._LAST_RANKER_WARNINGS
    assert any("this-path-does-not-exist.md" in w for w in warnings), (
        f"expected missing-target warning; got {warnings}"
    )


def test_AC_FBMT1_SUPM_4_missing_target_still_applies_penalty(tmp_path: Path):
    """Even when the marker target is missing, the penalty still
    applies (the superseded file is still demoted)."""
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)
    ref_time = datetime(2026, 5, 21, 10, 0, 0, tzinfo=timezone.utc)
    store.write_episode(
        name="turn/keeper-baseline",
        body="alpha beta gamma",
        source_description="test",
        reference_time=ref_time,
        source="message",
        group_id="testgroup",
    )
    store.write_episode(
        name="turn/orphan-with-bad-marker",
        body="alpha beta gamma",
        source_description="test",
        reference_time=ref_time,
        source="message",
        group_id="testgroup",
    )
    # Annotate the second with a non-existent target.
    orphan_files = list(
        (memory_dir / "episodes" / "testgroup").rglob("orphan-with-bad-marker.md")
    )
    assert orphan_files
    text = orphan_files[0].read_text(encoding="utf-8")
    annotated = text.replace(
        "group_id: testgroup\n",
        "group_id: testgroup\nsuperseded-by: ./nonexistent.md\n",
    )
    orphan_files[0].write_text(annotated, encoding="utf-8")

    result = store.search(
        query="alpha beta gamma",
        group_ids=["testgroup"],
        num_results=5,
    )
    episodes = result["episodes"]
    idx_keeper = next(
        (i for i, ep in enumerate(episodes)
         if ep["path"].endswith("keeper-baseline.md")),
        None,
    )
    idx_orphan = next(
        (i for i, ep in enumerate(episodes)
         if ep["path"].endswith("orphan-with-bad-marker.md")),
        None,
    )
    assert idx_keeper is not None
    assert idx_orphan is not None
    assert idx_keeper < idx_orphan, (
        "orphan-with-bad-marker should rank below keeper-baseline "
        "despite the marker target being missing"
    )
