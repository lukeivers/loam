"""AC.FBMT1.SUPM.2 — retrieval ranker demotes superseded files.

Constructs two memory files with comparable content; marks one
``superseded-by``; runs the retrieval contributor against a query
that lexically matches both; asserts the superseded file's final
rank score is strictly less than the unsuperseded file's score
(multiplicative penalty observable).

Per plan-doc ``amendment-134-fbm-tier1-foundations.md`` §4
AC.FBMT1.SUPM family + §14 D-T1.1.PENALTY (0.1x multiplicative).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from loam.primary_persona.file_memory import (
    FileMemoryStore,
    SUPERSEDED_PENALTY,
)


def test_AC_FBMT1_SUPM_2_ranker_demotes_superseded_below_unsuperseded(tmp_path: Path):
    """Two memory files with comparable lexical content; the
    superseded one ranks BELOW the unsuperseded one after the
    ranker applies the multiplicative penalty."""
    memory_dir = tmp_path / "memory"
    store = FileMemoryStore(memory_dir=memory_dir)
    ref_time = datetime(2026, 5, 21, 10, 0, 0, tzinfo=timezone.utc)
    # Two files with the SAME lexical content (so any rank
    # difference is attributable to the supersession penalty, not
    # BM25 scoring variance).
    store.write_episode(
        name="turn/keeper-rule",
        body="alpha beta gamma delta epsilon",
        source_description="test",
        reference_time=ref_time,
        source="message",
        group_id="testgroup",
    )
    store.write_episode(
        name="turn/old-rule",
        body="alpha beta gamma delta epsilon",
        source_description="test",
        reference_time=ref_time,
        source="message",
        group_id="testgroup",
    )
    # Manually annotate the second file with ``superseded-by:``.
    # The writer doesn't emit this field yet (that's a future
    # amendment); the supersession-marker convention is an
    # operator-authored annotation on existing memory files.
    sup_file = list((memory_dir / "episodes" / "testgroup").rglob("old-rule.md"))
    assert sup_file, "fixture: old-rule file not written"
    sup_path = sup_file[0]
    text = sup_path.read_text(encoding="utf-8")
    annotated = text.replace(
        "group_id: testgroup\n",
        "group_id: testgroup\nsuperseded-by: ./keeper-rule.md\n",
    )
    sup_path.write_text(annotated, encoding="utf-8")

    result = store.search(
        query="alpha beta gamma",
        group_ids=["testgroup"],
        num_results=5,
    )
    episodes = result["episodes"]
    # Both files should be returned (AC.FBMT1.SUPM.3 — not filtered).
    paths = [ep["path"] for ep in episodes]
    assert any(p.endswith("keeper-rule.md") for p in paths)
    assert any(p.endswith("old-rule.md") for p in paths)
    # The unsuperseded file ranks BEFORE the superseded file
    # (lower index = higher rank).
    idx_keeper = next(
        i for i, ep in enumerate(episodes) if ep["path"].endswith("keeper-rule.md")
    )
    idx_old = next(
        i for i, ep in enumerate(episodes) if ep["path"].endswith("old-rule.md")
    )
    assert idx_keeper < idx_old, (
        f"superseded file (old-rule) should rank below unsuperseded "
        f"(keeper-rule); got positions {idx_keeper} and {idx_old}"
    )


def test_AC_FBMT1_SUPM_2_penalty_value_is_zero_point_one():
    """The penalty constant matches the §14 D-T1.1.PENALTY ruling
    (0.1× multiplicative). A change to this constant must be a
    deliberate plan-doc amendment, not an accidental tweak."""
    assert SUPERSEDED_PENALTY == 0.1
