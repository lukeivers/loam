"""AC.D-mig.5 — best-effort extraction with placeholder seeding.

Plans whose structure does not parse cleanly produce a single
placeholder ObjectiveSpec record. Three test fixtures:

- well-structured (post-#22 shape) → N records (one per AC).
- ambiguous (no clear AC layout) → 1 placeholder record.
- malformed (broken markdown / no headers) → 1 placeholder record.

No exception propagates from any of the three.
"""

from __future__ import annotations

from pathlib import Path

from loam.objective_tracker import ObjectiveFilter, ObjectiveTracker

from loam.heavy_b_migrate.amendment_acs import extract_and_seed


_WELL_STRUCTURED = """\
# Amendment 1 — well structured

## AC1.1 — first

Body.

## AC1.2 — second

Body.
"""

_AMBIGUOUS = """\
# Amendment 2 — pre-#22 shape

This plan describes work without explicit AC headers. There are
acceptance criteria mentioned in prose but they don't appear as
parseable ## ACX.Y blocks. The placeholder convention exists for
exactly this case.
"""

_MALFORMED = """just some text with no markdown structure"""


def test_well_structured_plan_yields_per_ac_records(
    workspace: Path, seeded_tracker_db: Path, write_amendment_plan
) -> None:
    write_amendment_plan(workspace, 1, "well", _WELL_STRUCTURED)
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        report = extract_and_seed(workspace, tracker)
        assert len(report.created) == 2
        assert len(report.placeholders_seeded) == 0
    finally:
        tracker.close()


def test_ambiguous_plan_yields_placeholder(
    workspace: Path, seeded_tracker_db: Path, write_amendment_plan
) -> None:
    write_amendment_plan(workspace, 2, "ambiguous", _AMBIGUOUS)
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        report = extract_and_seed(workspace, tracker)
        assert len(report.created) == 0
        assert "2" in report.placeholders_seeded
        # Verify the placeholder record landed.
        plan_rel = "docs/rebuild/plans/amendment-2-ambiguous.md"
        records = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=plan_rel)
        )
        assert len(records) == 1
        assert records[0].lifted_from is not None
        assert records[0].lifted_from.source_ac == "placeholder"
    finally:
        tracker.close()


def test_malformed_plan_yields_placeholder_no_exception(
    workspace: Path, seeded_tracker_db: Path, write_amendment_plan
) -> None:
    write_amendment_plan(workspace, 3, "malformed", _MALFORMED)
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        # No exception should propagate.
        report = extract_and_seed(workspace, tracker)
        assert "3" in report.placeholders_seeded
    finally:
        tracker.close()


def test_three_fixtures_combined_no_exception(
    workspace: Path, seeded_tracker_db: Path, write_amendment_plan
) -> None:
    write_amendment_plan(workspace, 1, "well", _WELL_STRUCTURED)
    write_amendment_plan(workspace, 2, "ambiguous", _AMBIGUOUS)
    write_amendment_plan(workspace, 3, "malformed", _MALFORMED)
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        report = extract_and_seed(workspace, tracker)
        assert report.plans_visited == 3
        assert len(report.created) == 2  # well-structured AC1.1 + AC1.2
        assert sorted(report.placeholders_seeded) == ["2", "3"]
    finally:
        tracker.close()
