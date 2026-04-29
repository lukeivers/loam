"""AC40.2 — Contributor filters to the workspace's value-prop-rooted
tree only.

Records authored under any other root co-existing in the same DB do
NOT appear in the contributor's output.

Maps to: objective-tracker D2 (user-authored-root invariant per
workspace) + v1.0 Architectural "Objective-based" → AC.PO.1.

Plan: docs/rebuild/plans/amendment-40-primary-persona-tracker-context-contributor.md
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.context_composer import ComposedContextPayload
from loam.primary_persona.session_start_gate import compose_session_fields
from loam.primary_persona.tracker_context import (
    DEFAULT_VALUE_PROP_ROOT_ID,
    register_tracker_context,
)

from _helpers_d40 import FakeTrackerClient, make_projection
from _helpers_d7 import seed_baseline_workspace


def test_AC40_2_only_value_prop_rooted_objectives_appear(tmp_path: Path) -> None:
    """Two roots co-exist in the same tracker DB:

    - the workspace's value-prop root (id ``value-prop-root``); one
      in-flight descendant under it.
    - a secondary unrelated root (id ``secondary-root``); one in-flight
      descendant under it.

    The contributor surfaces ONLY the value-prop-rooted descendant.
    """
    workspace_root = tmp_path / "ws-ac40-2"
    seed_baseline_workspace(workspace_root)

    vp_root = make_projection(
        DEFAULT_VALUE_PROP_ROOT_ID,
        goal="VP root",
        status="active",
    )
    vp_child = make_projection(
        "vp-child",
        goal="UNIQUE-AC40-2-VP-CHILD — vp-rooted in-flight",
        status="active",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )

    other_root = make_projection(
        "secondary-root",
        goal="other root",
        status="active",
    )
    other_child = make_projection(
        "secondary-child",
        goal="UNIQUE-AC40-2-OTHER-CHILD — secondary-rooted noise",
        status="active",
        parent_id="secondary-root",
    )

    client = FakeTrackerClient(
        query_result=(vp_root, vp_child, other_root, other_child),
        trace_map={
            "vp-child": [vp_child, vp_root],
            "secondary-child": [other_child, other_root],
        },
    )

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=lambda: client,
    )

    payload = composer.on_session_start(workspace_root)
    block = dict(payload.contributor_outputs).get("tracker-context", "")

    assert "UNIQUE-AC40-2-VP-CHILD" in block, (
        "AC40.2 — value-prop-rooted descendant must appear"
    )
    assert "UNIQUE-AC40-2-OTHER-CHILD" not in block, (
        "AC40.2 — secondary-rooted descendant MUST NOT appear "
        "(cross-workspace-root noise must be filtered)"
    )


def test_AC40_2_orphan_record_with_unknown_terminal_excluded(
    tmp_path: Path,
) -> None:
    """A record whose ``trace_to_root`` lands on a terminal id NOT
    matching ``value_prop_root_id`` is excluded — even if that
    terminal id is some other arbitrary root.
    """
    workspace_root = tmp_path / "ws-ac40-2b"
    seed_baseline_workspace(workspace_root)

    vp_root = make_projection(
        DEFAULT_VALUE_PROP_ROOT_ID, goal="vp root", status="active"
    )
    orphan = make_projection(
        "orphan",
        goal="UNIQUE-AC40-2B-ORPHAN — wrong terminal",
        status="active",
        parent_id=None,
    )

    client = FakeTrackerClient(
        query_result=(vp_root, orphan),
        trace_map={
            "orphan": [orphan],  # terminal id != value-prop-root
        },
    )

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=lambda: client,
    )

    payload = composer.on_session_start(workspace_root)
    block = dict(payload.contributor_outputs).get("tracker-context", "")
    assert "UNIQUE-AC40-2B-ORPHAN" not in block
