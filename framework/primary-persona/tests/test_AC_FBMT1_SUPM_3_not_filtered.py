"""AC.FBMT1.SUPM.3 — superseded files are demoted, not filtered.

Constructs a superseded memory file with very high lexical-match
score against a query; asserts the file IS in the returned candidate
set (just demoted), not filtered out. Mark-don't-delete per the v2
FBM rethink's reading of Anderson & Green 2001.

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.SUPM family.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import FileMemoryStore


def test_AC_FBMT1_SUPM_3_high_relevance_superseded_still_returned(tmp_path: Path):
    """A superseded file with very strong lexical match still
    appears in the returned candidate set — the penalty demotes,
    it does NOT filter."""
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)
    ref_time = datetime(2026, 5, 21, 10, 0, 0, tzinfo=timezone.utc)
    # Single superseded file, high lexical match for query
    # "quokka platypus" (rare terms unlikely to false-match).
    store.write_episode(
        name="turn/superseded-strong-match",
        body=(
            "quokka platypus quokka platypus quokka platypus "
            "quokka platypus quokka platypus"
        ),
        source_description="test",
        reference_time=ref_time,
        source="message",
        group_id="testgroup",
    )
    # Annotate the file as superseded.
    sup_file = list((memory_dir / "episodes" / "testgroup").rglob("*.md"))
    assert sup_file
    sup_path = sup_file[0]
    text = sup_path.read_text(encoding="utf-8")
    annotated = text.replace(
        "group_id: testgroup\n",
        "group_id: testgroup\nsuperseded-by: ./other.md\n",
    )
    sup_path.write_text(annotated, encoding="utf-8")

    result = store.search(
        query="quokka platypus",
        group_ids=["testgroup"],
        num_results=5,
    )
    # The superseded file IS in the result set despite the penalty.
    episodes = result["episodes"]
    paths = [ep["path"] for ep in episodes]
    assert any("superseded-strong-match.md" in p for p in paths), (
        f"superseded file filtered out of result set; "
        f"paths returned: {paths}"
    )
