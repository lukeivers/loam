"""Amendment #39 — AC39.4 — ``partial_recovery`` recognises a
half-seeded tracker as a recoverable state.

Plan §4 AC39.4 outcomes:

- If ``first_run_scaffold`` is interrupted mid-seed (root created
  but some spec-tier descendants missing), a subsequent
  ``seed_tracker`` invocation completes the seed by querying for
  missing records (via ``query_projection_view`` with
  ``lifted_from.source_doc`` filter — amendment #38's API) and
  creating only the missing ones.
- No record is duplicated; no record is left in a half-state.

Maps to workspace-bootstrap proposal partial_recovery surface →
AC.PO.1.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from objective_tracker import (
    LiftedFrom,
    ObjectiveSpec,
    ObjectiveTracker,
    ProseCriterion,
    TimeBound,
)

from workspace_bootstrap.adapters.tracker_seed import (
    FRAMEWORK_VALUE_PROP_RELPATH,
    ROOT_OBJECTIVE_ID,
    SPEC_DOC_RELPATH,
    _SPEC_TIER_PHASES,
    classify_workspace,
    load_value_prop_source,
    seed_tracker,
    tracker_db_path_for,
)


def _build_workspace(tmp_path: Path) -> tuple[Path, Path]:
    workspace = tmp_path / "ws-partial"
    workspace.mkdir()
    (workspace / "docs" / "rebuild").mkdir(parents=True)
    framework_vp = (
        Path(__file__).resolve().parent.parent.parent
        / "docs"
        / "rebuild"
        / "VALUE_PROPOSITION.md"
    )
    (workspace / FRAMEWORK_VALUE_PROP_RELPATH).write_text(
        framework_vp.read_text()
    )
    pos_root = tmp_path / ".pos"
    pos_root.mkdir()
    return workspace, pos_root


def _seed_root_only(workspace: Path, db_path: Path) -> None:
    """Simulate an interrupted seed: create the root but no
    descendants. Bypasses ``seed_tracker`` so the test sets up the
    half-state directly via the public tracker API."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tracker = ObjectiveTracker(db_path)
    try:
        spec = ObjectiveSpec(
            goal="pOS v2 — Value Proposition of the Harness and the Primary Persona",
            parent_id=None,
            acceptance_criteria=(
                ProseCriterion(criterion_id="AC.PO.1", prose="primary-persona test"),
                ProseCriterion(criterion_id="AC.PO.2", prose="harness test"),
            ),
            time_bound=TimeBound(evergreen=True, review_cadence="amendment-driven"),
            authored_by="user",
            lifted_from=LiftedFrom(
                source_doc=FRAMEWORK_VALUE_PROP_RELPATH,
                source_ac="prime",
            ),
        )
        asyncio.run(tracker.create(spec, objective_id=ROOT_OBJECTIVE_ID))
    finally:
        tracker.close()


def _seed_root_and_one_descendant(workspace: Path, db_path: Path) -> None:
    """Simulate an interrupted seed: root + one spec descendant
    present, two missing."""
    _seed_root_only(workspace, db_path)
    tracker = ObjectiveTracker(db_path)
    try:
        suffix, ac_label, prose = _SPEC_TIER_PHASES[0]
        child = ObjectiveSpec(
            goal=prose,
            parent_id=ROOT_OBJECTIVE_ID,
            acceptance_criteria=(
                ProseCriterion(
                    criterion_id=f"spec-{suffix}-met",
                    prose="placeholder",
                ),
            ),
            time_bound=TimeBound(evergreen=True, review_cadence="amendment-driven"),
            authored_by="user",
            lifted_from=LiftedFrom(source_doc=SPEC_DOC_RELPATH, source_ac=ac_label),
        )
        asyncio.run(tracker.create(child, objective_id=f"spec-{suffix}"))
    finally:
        tracker.close()


def test_AC39_4_root_only_state_resumes_to_full_tree(tmp_path: Path) -> None:
    """A tracker carrying only the value-prop root (no descendants)
    completes to the full tree on the next ``seed_tracker``
    invocation. The result reports ``completed_partial``."""
    workspace, pos_root = _build_workspace(tmp_path)
    db_path = tracker_db_path_for(pos_root)
    _seed_root_only(workspace, db_path)

    classification = classify_workspace(workspace)
    vp = load_value_prop_source(workspace, classification)
    result = asyncio.run(
        seed_tracker(
            workspace_root=workspace,
            tracker_db_path=db_path,
            classification=classification,
            value_prop=vp,
        )
    )
    assert result.reason == "completed_partial"
    assert set(result.descendants_seeded) == {
        f"spec-{suffix}" for suffix, _, _ in _SPEC_TIER_PHASES
    }

    tracker = ObjectiveTracker(db_path)
    try:
        for suffix, _, _ in _SPEC_TIER_PHASES:
            assert tracker.get(f"spec-{suffix}") is not None
    finally:
        tracker.close()


def test_AC39_4_partial_descendants_state_resumes_to_full_tree(
    tmp_path: Path,
) -> None:
    """A tracker carrying root + one descendant (two missing) creates
    only the missing descendants; the existing one is untouched."""
    workspace, pos_root = _build_workspace(tmp_path)
    db_path = tracker_db_path_for(pos_root)
    _seed_root_and_one_descendant(workspace, db_path)

    classification = classify_workspace(workspace)
    vp = load_value_prop_source(workspace, classification)

    # Capture pre-resume snapshot of the existing descendant.
    tracker = ObjectiveTracker(db_path)
    try:
        existing_suffix = _SPEC_TIER_PHASES[0][0]
        pre = tracker.get(f"spec-{existing_suffix}")
        assert pre is not None
        pre_event_count = len(tracker.store.events_for(f"spec-{existing_suffix}"))
    finally:
        tracker.close()

    result = asyncio.run(
        seed_tracker(
            workspace_root=workspace,
            tracker_db_path=db_path,
            classification=classification,
            value_prop=vp,
        )
    )
    assert result.reason == "completed_partial"
    expected_missing = {
        f"spec-{suffix}" for suffix, _, _ in _SPEC_TIER_PHASES[1:]
    }
    assert set(result.descendants_seeded) == expected_missing

    tracker = ObjectiveTracker(db_path)
    try:
        # Pre-existing descendant unchanged.
        post = tracker.get(f"spec-{existing_suffix}")
        assert post is not None
        post_event_count = len(tracker.store.events_for(f"spec-{existing_suffix}"))
        assert post_event_count == pre_event_count, (
            "additional events emitted on already-seeded descendant"
        )
        # Missing descendants now present.
        for suffix, _, _ in _SPEC_TIER_PHASES[1:]:
            assert tracker.get(f"spec-{suffix}") is not None
    finally:
        tracker.close()


def test_AC39_4_no_duplicate_records_after_resume(tmp_path: Path) -> None:
    """Cross-check after partial-recovery: every objective ID present
    exactly once (deterministic ID enumeration via the tracker's
    ``list`` surface)."""
    workspace, pos_root = _build_workspace(tmp_path)
    db_path = tracker_db_path_for(pos_root)
    _seed_root_only(workspace, db_path)

    classification = classify_workspace(workspace)
    vp = load_value_prop_source(workspace, classification)
    asyncio.run(
        seed_tracker(
            workspace_root=workspace,
            tracker_db_path=db_path,
            classification=classification,
            value_prop=vp,
        )
    )

    tracker = ObjectiveTracker(db_path)
    try:
        all_recs = tracker.list()
        ids = [p.objective_id for p in all_recs]
        # Each expected ID appears exactly once.
        for expected in [ROOT_OBJECTIVE_ID] + [
            f"spec-{suffix}" for suffix, _, _ in _SPEC_TIER_PHASES
        ]:
            assert ids.count(expected) == 1, (
                f"{expected} present {ids.count(expected)} times; expected 1"
            )
    finally:
        tracker.close()
