"""AC40.6 — Contributor reads tracker DB at workspace-identity-derived
path.

The contributor resolves the tracker DB path from the workspace-
identity surface (existing convention per amendments #6/#28/#29 +
workspace-bootstrap's tracker DB convention). On a multi-workspace
machine, two parallel workspaces each register the contributor against
their own tracker DB; the contributor in workspace A surfaces only
A's tree; the contributor in workspace B surfaces only B's tree.

Maps to: workspace-identity invariant (amendments #6/#28/#29) +
objective-tracker D2 → AC.PO.1.

Plan: docs/rebuild/plans/amendment-40-primary-persona-tracker-context-contributor.md
"""

from __future__ import annotations

from pathlib import Path

from src.context_composer import ComposedContextPayload
from src.session_start_gate import compose_session_fields
from src.tracker_context import (
    TRACKER_DB_FILENAME,
    register_tracker_context,
    tracker_db_path_for,
)


def test_AC40_6_path_resolver_is_pure_workspace_identity_function(
    tmp_path: Path,
) -> None:
    """``tracker_db_path_for(workspace_root)`` returns the well-known
    DB path under the workspace identity. Two workspaces resolve to
    two distinct paths."""
    ws_a = tmp_path / "workspace-a"
    ws_b = tmp_path / "workspace-b"
    ws_a.mkdir()
    ws_b.mkdir()

    path_a = tracker_db_path_for(ws_a)
    path_b = tracker_db_path_for(ws_b)

    assert path_a == ws_a / TRACKER_DB_FILENAME
    assert path_b == ws_b / TRACKER_DB_FILENAME
    assert path_a != path_b
    # Filename is the convention-parity constant (workspace-bootstrap
    # writes the same filename per amendment #39).
    assert TRACKER_DB_FILENAME == "objective_tracker.sqlite"


def test_AC40_6_two_parallel_workspaces_each_see_own_tree(tmp_path: Path) -> None:
    """Two workspaces each have their own tracker (here represented by
    distinct fakes). The contributor registered in each workspace's
    composer surfaces only that workspace's tree.

    The path-resolution surface is the contract — the default
    factory inside ``register_tracker_context`` derives the DB path
    from ``workspace_root``. We override the factory in each call to
    a per-workspace fake so this test stays Protocol-driven; the
    contract under test is "the contributor's data source is keyed
    on workspace_root and only that workspace's tree leaks out."
    """
    from _helpers_d40 import FakeTrackerClient, make_projection
    from _helpers_d7 import seed_baseline_workspace
    from src.tracker_context import DEFAULT_VALUE_PROP_ROOT_ID

    ws_a = tmp_path / "ws-a"
    ws_b = tmp_path / "ws-b"
    seed_baseline_workspace(ws_a)
    seed_baseline_workspace(ws_b)

    root_a = make_projection(
        DEFAULT_VALUE_PROP_ROOT_ID, goal="root A", status="active"
    )
    child_a = make_projection(
        "obj-a-only",
        goal="UNIQUE-AC40-6-A — workspace A only",
        status="active",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    client_a = FakeTrackerClient(
        query_result=(root_a, child_a),
        trace_map={"obj-a-only": [child_a, root_a]},
    )

    root_b = make_projection(
        DEFAULT_VALUE_PROP_ROOT_ID, goal="root B", status="active"
    )
    child_b = make_projection(
        "obj-b-only",
        goal="UNIQUE-AC40-6-B — workspace B only",
        status="active",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    client_b = FakeTrackerClient(
        query_result=(root_b, child_b),
        trace_map={"obj-b-only": [child_b, root_b]},
    )

    composer_a = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer_a, workspace_root=ws_a, tracker_factory=lambda: client_a
    )
    composer_b = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer_b, workspace_root=ws_b, tracker_factory=lambda: client_b
    )

    block_a = dict(composer_a.on_session_start(ws_a).contributor_outputs).get(
        "tracker-context", ""
    )
    block_b = dict(composer_b.on_session_start(ws_b).contributor_outputs).get(
        "tracker-context", ""
    )

    assert "UNIQUE-AC40-6-A" in block_a
    assert "UNIQUE-AC40-6-B" not in block_a
    assert "UNIQUE-AC40-6-B" in block_b
    assert "UNIQUE-AC40-6-A" not in block_b


def test_AC40_6_default_factory_uses_resolved_path(tmp_path: Path) -> None:
    """When ``tracker_factory`` is not supplied, the default factory
    invokes a real tracker against ``tracker_db_path_for(workspace_root)``.

    Verified by registering the contributor without a factory against
    a workspace whose tracker DB does not exist — the contributor must
    still degrade gracefully (per AC40.3) but the *path* the default
    factory targets must be the workspace-identity-derived one.
    """
    from _helpers_d7 import seed_baseline_workspace

    workspace_root = tmp_path / "ws-no-tracker"
    seed_baseline_workspace(workspace_root)

    composer = ComposedContextPayload(session_builder=compose_session_fields)

    # Capture the path the default factory uses by monkey-patching the
    # objective_tracker.ObjectiveTracker construction inside the
    # default factory's lazy import. We do this by intercepting the
    # call via a sys.modules shim.
    import sys
    import types

    captured_paths: list[Path] = []
    fake_module = types.ModuleType("objective_tracker")

    class FakeTracker:
        def __init__(self, db_path):
            captured_paths.append(Path(db_path))

        def query_projection_view(self, filter=None):
            return ()

        def trace_to_root(self, oid):
            return []

        def close(self):
            pass

    fake_module.ObjectiveTracker = FakeTracker  # type: ignore[attr-defined]

    # Save the prior module so test cleanup can restore it.
    prior = sys.modules.get("objective_tracker")
    sys.modules["objective_tracker"] = fake_module

    try:
        register_tracker_context(composer, workspace_root=workspace_root)
        composer.on_session_start(workspace_root)
    finally:
        if prior is not None:
            sys.modules["objective_tracker"] = prior
        else:
            sys.modules.pop("objective_tracker", None)

    assert captured_paths, (
        "AC40.6 — default factory must invoke the tracker constructor at least once"
    )
    assert captured_paths[0] == tracker_db_path_for(workspace_root), (
        f"AC40.6 — default factory must target workspace-identity-derived path; "
        f"got {captured_paths[0]} expected {tracker_db_path_for(workspace_root)}"
    )
