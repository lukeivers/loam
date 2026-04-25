"""Amendment #39 — AC39.1 — Fresh-clone first-run on a pos-v2 dev
workspace seeds the value-prop root + spec-tier descendants.

Plan §4 AC39.1 outcomes:

- The tracker contains exactly one objective whose ``parent_id is
  None``, with ``goal`` derived from
  ``docs/rebuild/VALUE_PROPOSITION.md``'s prime statement, two
  ``prose`` criteria (AC.PO.1 + AC.PO.2),
  ``authored_by == "user"``, ``time_bound.evergreen is True``, and
  ``lifted_from.source_doc == "docs/rebuild/VALUE_PROPOSITION.md"``.
- The tracker contains spec-tier child objectives chaining to the
  root: at minimum one objective per spec phase (v1.0, v1.1, v1.2),
  each ``authored_by == "user"``, each with
  ``lifted_from.source_doc == "docs/rebuild/spec/pos-v2-objectives-
  spec.md"``.
- ``tracker.bind_scope`` against any descendant succeeds.

Maps to v1.0 Architectural "Objective-based" + objective-tracker D2
→ AC.PO.1.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from objective_tracker import (
    ObjectiveFilter,
    ObjectiveTracker,
)

from workspace_bootstrap.adapters.first_run_scaffold import (
    run_first_run_scaffold,
)
from workspace_bootstrap.adapters.tracker_seed import (
    FRAMEWORK_VALUE_PROP_RELPATH,
    ROOT_OBJECTIVE_ID,
    SPEC_DOC_RELPATH,
    _SPEC_TIER_PHASES,
    tracker_db_path_for,
)


def _seed_pos_v2_dev_workspace(tmp_path: Path) -> tuple[Path, Path]:
    """Create a workspace classified as pos-v2-dev (it carries the
    canonical VALUE_PROPOSITION.md at the framework path), run the
    scaffold, return ``(workspace_root, pos_root)``."""
    workspace = tmp_path / "ws-dev"
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
    agents = tmp_path / "LaunchAgents"
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )
    return workspace, pos_root


def test_AC39_1_root_record_carries_value_prop_shape(tmp_path: Path) -> None:
    """The seeded root carries goal + AC.PO.1 + AC.PO.2 + evergreen
    time-bound + ``lifted_from.source_doc`` pointing at the framework
    value-prop doc."""
    _, pos_root = _seed_pos_v2_dev_workspace(tmp_path)
    db_path = tracker_db_path_for(pos_root)
    assert db_path.exists(), "tracker DB not materialised by first-run"

    tracker = ObjectiveTracker(db_path)
    try:
        root = tracker.get(ROOT_OBJECTIVE_ID)
        assert root is not None, "value-prop root not seeded"
        assert root.parent_id is None
        assert root.authored_by == "user"
        assert root.time_bound.evergreen is True
        assert root.lifted_from is not None
        assert root.lifted_from.source_doc == FRAMEWORK_VALUE_PROP_RELPATH
        assert root.lifted_from.source_ac == "prime"

        criterion_ids = {c.criterion_id for c in root.acceptance_criteria}
        assert "AC.PO.1" in criterion_ids
        assert "AC.PO.2" in criterion_ids

        # Goal should derive from the framework value-prop doc — non-
        # empty and recognisably the H1 of the canonical document.
        assert root.goal
        assert "Value Proposition" in root.goal
    finally:
        tracker.close()


def test_AC39_1_spec_descendants_chain_to_root(tmp_path: Path) -> None:
    """Each spec-tier descendant chains to the value-prop root via
    ``trace_to_root`` and carries ``lifted_from.source_doc`` pointing
    at the spec doc."""
    _, pos_root = _seed_pos_v2_dev_workspace(tmp_path)
    tracker = ObjectiveTracker(tracker_db_path_for(pos_root))
    try:
        for suffix, ac_label, _ in _SPEC_TIER_PHASES:
            obj_id = f"spec-{suffix}"
            proj = tracker.get(obj_id)
            assert proj is not None, f"spec descendant {obj_id} not seeded"
            assert proj.authored_by == "user"
            assert proj.lifted_from is not None
            assert proj.lifted_from.source_doc == SPEC_DOC_RELPATH
            assert proj.lifted_from.source_ac == ac_label

            chain = tracker.trace_to_root(obj_id)
            terminal = chain[-1]
            assert terminal.objective_id == ROOT_OBJECTIVE_ID
            assert terminal.parent_id is None
    finally:
        tracker.close()


def test_AC39_1_bind_scope_against_descendant_succeeds(tmp_path: Path) -> None:
    """``tracker.bind_scope`` against a seeded descendant succeeds —
    the user-authored-root invariant on the terminal ancestor (D2 +
    D4) is satisfied by every record the seed produces."""
    _, pos_root = _seed_pos_v2_dev_workspace(tmp_path)
    tracker = ObjectiveTracker(tracker_db_path_for(pos_root))
    try:
        # Use the v1.0 descendant as the bind target.
        binding = asyncio.run(
            tracker.bind_scope(scope_id="test-scope-1", objective_id="spec-v1.0")
        )
        assert binding["scope_id"] == "test-scope-1"
        assert binding["objective_id"] == "spec-v1.0"
        assert tracker.is_scope_bound("test-scope-1")
    finally:
        tracker.close()


def test_AC39_1_query_projection_view_returns_seeded_records(tmp_path: Path) -> None:
    """``query_projection_view`` filters on
    ``lifted_from_source_doc`` return the seeded subset — the
    surface amendment #38 introduced is the read-side the seed
    relies on for idempotency, and downstream consumers (#40) will
    use the same surface."""
    _, pos_root = _seed_pos_v2_dev_workspace(tmp_path)
    tracker = ObjectiveTracker(tracker_db_path_for(pos_root))
    try:
        from_value_prop = tracker.query_projection_view(
            ObjectiveFilter(
                lifted_from_source_doc=FRAMEWORK_VALUE_PROP_RELPATH
            )
        )
        assert len(from_value_prop) == 1
        assert from_value_prop[0].objective_id == ROOT_OBJECTIVE_ID

        from_spec = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=SPEC_DOC_RELPATH)
        )
        assert len(from_spec) == len(_SPEC_TIER_PHASES)
        seeded_ids = {p.objective_id for p in from_spec}
        for suffix, _, _ in _SPEC_TIER_PHASES:
            assert f"spec-{suffix}" in seeded_ids
    finally:
        tracker.close()


def test_AC39_1_scaffold_result_reports_seed_outcome(tmp_path: Path) -> None:
    """``ScaffoldResult`` carries the new tracker-seed fields so the
    confirmation surface and downstream callers can observe what
    landed."""
    workspace = tmp_path / "ws-result"
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
    agents = tmp_path / "LaunchAgents"
    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )
    assert result.tracker_seeded is True
    assert result.tracker_seed_reason == "fresh_seed"
    assert result.tracker_classification == "pos-v2-dev"
    assert result.tracker_root_id == ROOT_OBJECTIVE_ID
    assert set(result.tracker_descendants_seeded) == {
        f"spec-{suffix}" for suffix, _, _ in _SPEC_TIER_PHASES
    }
    assert result.tracker_value_prop_source == FRAMEWORK_VALUE_PROP_RELPATH
