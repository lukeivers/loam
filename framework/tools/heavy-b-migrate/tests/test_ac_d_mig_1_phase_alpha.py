"""AC.D-mig.1 — Phase α seeds sealed-component objectives chained to root.

After Phase α completes against a workspace whose tracker has been
seeded by amendment #39 (root + spec descendants), the tracker
contains additional records — one per sealed-component proposal.md
discovered. Each record:

- has ``parent_id`` pointing at ``spec-v1.0`` (per builder-plan §6),
- has ``authored_by == "user"``,
- has ``lifted_from.source_doc == docs/archive/component-research/<slug>/proposal.md``,
- chains to the value-prop root via ``trace_to_root``.
"""

from __future__ import annotations

from pathlib import Path

from loam.objective_tracker import ObjectiveFilter, ObjectiveTracker

from loam.heavy_b_migrate.components import seed_phase_alpha
from loam.heavy_b_migrate.ids import component_objective_id


def test_phase_alpha_seeds_one_record_per_component_with_proposal(
    workspace: Path, seeded_tracker_db: Path, write_component_proposal
) -> None:
    write_component_proposal(
        workspace, "fixture-a", "# Fixture A\n\nA proposal.\n"
    )
    write_component_proposal(
        workspace, "fixture-b", "# Fixture B\n\nB proposal.\n"
    )

    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        report = seed_phase_alpha(workspace, tracker)
        assert sorted(report.created) == ["fixture-a", "fixture-b"]
        # Both records present + chain to value-prop root.
        for slug in ("fixture-a", "fixture-b"):
            chain = tracker.trace_to_root(component_objective_id(slug))
            ids_in_chain = [p.objective_id for p in chain]
            assert "value-prop-root" in ids_in_chain
            assert "spec-v1.0" in ids_in_chain
    finally:
        tracker.close()


def test_phase_alpha_records_are_authored_by_user(
    workspace: Path, seeded_tracker_db: Path, write_component_proposal
) -> None:
    write_component_proposal(
        workspace, "fixture-c", "# Fixture C\n"
    )
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        seed_phase_alpha(workspace, tracker)
        proj = tracker.get(component_objective_id("fixture-c"))
        assert proj is not None
        assert proj.authored_by == "user"
        assert proj.parent_id == "spec-v1.0"
        assert proj.lifted_from is not None
        assert proj.lifted_from.source_doc == (
            "docs/archive/component-research/fixture-c/proposal.md"
        )
    finally:
        tracker.close()


def test_phase_alpha_idempotent_re_run(
    workspace: Path, seeded_tracker_db: Path, write_component_proposal
) -> None:
    write_component_proposal(
        workspace, "fixture-d", "# Fixture D\n"
    )
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        first = seed_phase_alpha(workspace, tracker)
        second = seed_phase_alpha(workspace, tracker)
        assert first.created == ("fixture-d",)
        assert second.created == ()
        assert second.skipped == ("fixture-d",)
    finally:
        tracker.close()


def test_phase_alpha_skips_components_without_proposal(
    workspace: Path, seeded_tracker_db: Path, write_component_proposal
) -> None:
    # Make a dir without a proposal.md.
    (workspace / "docs" / "archive" / "component-research" / "no-proposal").mkdir()
    write_component_proposal(workspace, "with-proposal", "# With\n")
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        report = seed_phase_alpha(workspace, tracker)
        assert "with-proposal" in report.created
        assert "no-proposal" not in report.created
        assert "no-proposal" in report.missing_proposal
    finally:
        tracker.close()
