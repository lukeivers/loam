"""AC.D-mig.3 — Phase γ registers amendment ACs with proper provenance.

After Phase γ completes, the tracker contains records for every
amendment plan's declared AC. Each record:

- has ``parent_id`` pointing at ``spec-v1.0`` (per builder-plan §6),
- has ``authored_by == "user"`` (D-build.3 (a)),
- has ``lifted_from.source_doc`` pointing at the amendment plan file,
- has ``lifted_from.source_ac`` matching the AC identifier.

Note: ``source_commit`` is intentionally None during Phase γ — the
migration writes records without SHA, and AC.D-mig.4's continuous-
registration verifier exercises the seal-step that DOES populate
source_commit. Phase γ is the substrate; AC.D-mig.4 is the live cycle.
"""

from __future__ import annotations

from pathlib import Path

from loam.objective_tracker import ObjectiveFilter, ObjectiveTracker

from loam.heavy_b_migrate.amendment_acs import extract_and_seed


_AMENDMENT_PLAN_WITH_THREE_ACS = """\
# Amendment 999 — fixture amendment for tests

## AC999.1 — first criterion

Body of first criterion.

## AC999.2 — second criterion

Body of second criterion.

## AC999.3 — third criterion

Body of third criterion.
"""


def test_phase_gamma_extracts_ac_records_per_amendment(
    workspace: Path, seeded_tracker_db: Path, write_amendment_plan
) -> None:
    write_amendment_plan(workspace, 999, "fixture", _AMENDMENT_PLAN_WITH_THREE_ACS)
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        report = extract_and_seed(workspace, tracker)
        assert report.plans_visited == 1
        assert len(report.created) == 3
        plan_rel = "docs/plans/amendment-999-fixture.md"
        records = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=plan_rel)
        )
        assert len(records) == 3
        ac_ids = sorted(
            r.lifted_from.source_ac for r in records if r.lifted_from
        )
        assert ac_ids == ["AC999.1", "AC999.2", "AC999.3"]
        for r in records:
            assert r.authored_by == "user"
            assert r.parent_id == "spec-v1.0"
            assert r.lifted_from is not None
            assert r.lifted_from.source_doc == plan_rel
    finally:
        tracker.close()


def test_phase_gamma_idempotent(
    workspace: Path, seeded_tracker_db: Path, write_amendment_plan
) -> None:
    write_amendment_plan(workspace, 998, "fix", _AMENDMENT_PLAN_WITH_THREE_ACS)
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        first = extract_and_seed(workspace, tracker)
        second = extract_and_seed(workspace, tracker)
        assert len(first.created) == 3
        assert len(second.created) == 0
        assert len(second.skipped) >= 3
    finally:
        tracker.close()


def test_phase_gamma_excludes_builder_plan_companions(
    workspace: Path, seeded_tracker_db: Path, write_amendment_plan
) -> None:
    """Builder-plan companions (.builder-plan.md) are filtered out."""
    write_amendment_plan(workspace, 997, "fix", _AMENDMENT_PLAN_WITH_THREE_ACS)
    # Drop a .builder-plan.md sibling that should be skipped.
    plans_dir = workspace / "docs" / "plans"
    (plans_dir / "amendment-997-fix.builder-plan.md").write_text(
        "# Builder plan stub\n## AC.builder.1 — should not be lifted\n"
    )
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        report = extract_and_seed(workspace, tracker)
        assert report.plans_visited == 1
        ac_ids = [c.split(":", 1)[1] for c in report.created]
        assert "AC.builder.1" not in ac_ids
    finally:
        tracker.close()
