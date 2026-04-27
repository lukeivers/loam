"""AC.D-mig.2 — Phase β registers component ACs with `lifted_from` provenance.

After Phase β completes, the tracker contains records for every
component proposal's declared AC. Each record:

- has ``parent_id`` pointing at its component objective (Phase α),
- has ``authored_by == "user"``,
- has ``lifted_from.source_doc`` pointing at the component proposal,
- has ``lifted_from.source_ac`` matching the AC identifier.
"""

from __future__ import annotations

from pathlib import Path

from objective_tracker import ObjectiveFilter, ObjectiveTracker

from heavy_b_migrate.component_acs import extract_and_seed
from heavy_b_migrate.components import seed_phase_alpha


_PROPOSAL_WITH_THREE_ACS = """\
# Memory-system fixture proposal

## D1 — durable storage

Memory must persist across sessions.

## D2 — query-by-tag

Memory must be queryable by tag.

## D3 — eviction policy

Old entries must be evictable on policy.
"""


def test_phase_beta_extracts_ac_records_per_proposal(
    workspace: Path, seeded_tracker_db: Path, write_component_proposal
) -> None:
    write_component_proposal(workspace, "memory-fixture", _PROPOSAL_WITH_THREE_ACS)
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        seed_phase_alpha(workspace, tracker)
        report = extract_and_seed(workspace, tracker)
        assert len(report.created) == 3
        # Verify the three records are queryable + carry lifted_from.
        proposal_rel = (
            "docs/rebuild/components/memory-fixture/proposal.md"
        )
        records = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=proposal_rel)
        )
        # 1 component-root (Phase α) + 3 AC records (Phase β) = 4.
        assert len(records) == 4
        ac_records = [
            r for r in records
            if r.lifted_from is not None
            and r.lifted_from.source_ac in ("D1", "D2", "D3")
        ]
        assert len(ac_records) == 3
        for r in ac_records:
            assert r.authored_by == "user"
            assert r.lifted_from is not None
            assert r.lifted_from.source_doc == proposal_rel
    finally:
        tracker.close()


def test_phase_beta_idempotent(
    workspace: Path, seeded_tracker_db: Path, write_component_proposal
) -> None:
    write_component_proposal(workspace, "fixture", _PROPOSAL_WITH_THREE_ACS)
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        seed_phase_alpha(workspace, tracker)
        first = extract_and_seed(workspace, tracker)
        second = extract_and_seed(workspace, tracker)
        assert len(first.created) == 3
        assert len(second.created) == 0
        assert len(second.skipped) >= 3
    finally:
        tracker.close()


def test_phase_beta_records_parent_at_component_objective(
    workspace: Path, seeded_tracker_db: Path, write_component_proposal
) -> None:
    write_component_proposal(workspace, "x-comp", _PROPOSAL_WITH_THREE_ACS)
    tracker = ObjectiveTracker(seeded_tracker_db)
    try:
        seed_phase_alpha(workspace, tracker)
        extract_and_seed(workspace, tracker)
        proposal_rel = "docs/rebuild/components/x-comp/proposal.md"
        records = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=proposal_rel)
        )
        ac_record = next(
            r for r in records
            if r.lifted_from is not None and r.lifted_from.source_ac == "D1"
        )
        assert ac_record.parent_id == "component-x-comp"
    finally:
        tracker.close()
