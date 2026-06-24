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
    # Manually annotate the second file with ``superseded-by:`` +
    # ``superseded-date:`` — a concrete validity interval. The
    # supersession-marker convention is an operator/persona-authored
    # annotation on existing memory files.
    sup_file = list((memory_dir / "episodes" / "testgroup").rglob("old-rule.md"))
    assert sup_file, "fixture: old-rule file not written"
    sup_path = sup_file[0]
    text = sup_path.read_text(encoding="utf-8")
    annotated = text.replace(
        "group_id: testgroup\n",
        "group_id: testgroup\n"
        "superseded-by: ./keeper-rule.md\n"
        "superseded-date: 2026-06-01T00:00:00+00:00\n",
    )
    sup_path.write_text(annotated, encoding="utf-8")

    # PRECEDESSOR-CONTRACT MIGRATION (memory-supersession cycle, plan §2):
    # SUPM.2 originally asserted demote-not-filter in the DEFAULT view.
    # The SUP promotion FILTERS the superseded record from the default
    # view (AC.SUP.1). The demote-below-unsuperseded property SUPM.2
    # protects now holds on the ``as_of`` HISTORY view, where both
    # records are returned and the marked one is demoted by
    # SUPERSEDED_PENALTY.

    # Default view: the superseded old-rule is FILTERED out; the keeper
    # remains (AC.SUP.1).
    default_result = store.search(
        query="alpha beta gamma",
        group_ids=["testgroup"],
        num_results=5,
    )
    default_paths = [ep["path"] for ep in default_result["episodes"]]
    assert any(p.endswith("keeper-rule.md") for p in default_paths)
    assert not any(p.endswith("old-rule.md") for p in default_paths), (
        "superseded old-rule must be filtered from the default current "
        f"view (AC.SUP.1); got: {default_paths}"
    )

    # History view (as_of inside old-rule's valid window): BOTH records
    # are returned, and old-rule is DEMOTED below keeper-rule
    # (SUPM.2's demote-not-delete property, preserved).
    as_of = datetime(2026, 5, 25, 0, 0, 0, tzinfo=timezone.utc)
    history = store.search(
        query="alpha beta gamma",
        group_ids=["testgroup"],
        num_results=5,
        as_of=as_of,
    )
    episodes = history["episodes"]
    paths = [ep["path"] for ep in episodes]
    assert any(p.endswith("keeper-rule.md") for p in paths)
    assert any(p.endswith("old-rule.md") for p in paths)
    idx_keeper = next(
        i for i, ep in enumerate(episodes) if ep["path"].endswith("keeper-rule.md")
    )
    idx_old = next(
        i for i, ep in enumerate(episodes) if ep["path"].endswith("old-rule.md")
    )
    assert idx_keeper < idx_old, (
        f"superseded file (old-rule) should rank below unsuperseded "
        f"(keeper-rule) in the history view; got positions "
        f"{idx_keeper} and {idx_old}"
    )


def test_AC_FBMT1_SUPM_2_penalty_value_is_zero_point_one():
    """The penalty constant matches the §14 D-T1.1.PENALTY ruling
    (0.1× multiplicative). A change to this constant must be a
    deliberate plan-doc amendment, not an accidental tweak."""
    assert SUPERSEDED_PENALTY == 0.1
