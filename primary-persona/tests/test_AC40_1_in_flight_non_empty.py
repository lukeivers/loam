"""AC40.1 — Tracker-context contributor produces non-empty
``additionalContext`` when in-flight objectives exist.

A contributor registered on the persona's ``ComposedContextPayload``
registry produces a non-empty textual block when invoked under a
workspace whose tracker DB carries at least one in-flight (pre-
terminal) objective chain-up to the workspace's value-prop root. The
block contains at minimum the goal text of each in-flight objective.

Maps to: v1.0 Architectural "Objective-based" + VALUE_PROPOSITION
"process structure" → AC.PO.1.

Plan: docs/rebuild/plans/amendment-40-primary-persona-tracker-context-contributor.md
"""

from __future__ import annotations

from pathlib import Path

from src.context_composer import ComposedContextPayload, TriggerKind
from src.session_start_gate import compose_session_fields
from src.tracker_context import (
    DEFAULT_VALUE_PROP_ROOT_ID,
    register_tracker_context,
)

from _helpers_d40 import FakeTrackerClient, make_projection
from _helpers_d7 import seed_baseline_workspace


def _build_root_and_in_flight() -> tuple[FakeTrackerClient, list[str]]:
    """Build a fake tracker carrying one root + two in-flight
    descendants. Returns the client + the goal strings expected to
    appear in the contributor's output."""
    root = make_projection(
        DEFAULT_VALUE_PROP_ROOT_ID,
        goal="value prop root goal",
        status="active",
    )
    child_a = make_projection(
        "obj-a",
        goal="UNIQUE-AC40-1-CHILD-A — figure out the alpha thing",
        status="active",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    child_b = make_projection(
        "obj-b",
        goal="UNIQUE-AC40-1-CHILD-B — investigate the beta thing",
        status="proposed",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    achieved = make_projection(
        "obj-c",
        goal="UNIQUE-AC40-1-CHILD-C-DONE — finished thing (must NOT appear)",
        status="achieved",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )

    client = FakeTrackerClient(
        query_result=(root, child_a, child_b, achieved),
        trace_map={
            "obj-a": [child_a, root],
            "obj-b": [child_b, root],
            "obj-c": [achieved, root],
        },
    )
    return client, [child_a.goal, child_b.goal]


def test_AC40_1_contributor_output_contains_in_flight_goals(tmp_path: Path) -> None:
    """The contributor's output, fired under SessionStart, contains
    the goal text of every in-flight objective whose chain terminates
    at the workspace value-prop root."""
    workspace_root = tmp_path / "ws-ac40-1"
    seed_baseline_workspace(workspace_root)

    client, expected_goals = _build_root_and_in_flight()

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=lambda: client,
    )

    payload = composer.on_session_start(workspace_root)
    outputs = dict(payload.contributor_outputs)
    assert "tracker-context" in outputs, (
        "tracker-context contributor must register at session level"
    )
    block = outputs["tracker-context"]
    assert block, "AC40.1 — non-empty when in-flight objectives exist"
    for goal in expected_goals:
        assert goal in block, (
            f"AC40.1 — in-flight goal {goal!r} must appear in contributor output"
        )


def test_AC40_1_contributor_excludes_terminal_objectives(tmp_path: Path) -> None:
    """Achieved or abandoned objectives MUST NOT appear in the
    contributor's output — only in-flight (proposed | active)
    descendants are surfaced.
    """
    workspace_root = tmp_path / "ws-ac40-1b"
    seed_baseline_workspace(workspace_root)
    client, _ = _build_root_and_in_flight()

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=lambda: client,
    )

    payload = composer.on_session_start(workspace_root)
    block = dict(payload.contributor_outputs).get("tracker-context", "")
    assert "UNIQUE-AC40-1-CHILD-C-DONE" not in block, (
        "AC40.1 — achieved (terminal) objectives must NOT be surfaced"
    )


def test_AC40_1_contributor_registered_at_session_trigger_kind(
    tmp_path: Path,
) -> None:
    """The contributor registers under TriggerKind.session (D-build.1
    chose SessionStart-only). Verifies registration discriminates by
    trigger kind — turn-firing does NOT invoke this contributor."""
    workspace_root = tmp_path / "ws-ac40-1c"
    seed_baseline_workspace(workspace_root)
    client, _ = _build_root_and_in_flight()

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=lambda: client,
    )

    # Discriminate registry by kind.
    session_contribs = composer.contributors(trigger_kind=TriggerKind.session)
    turn_contribs = composer.contributors(trigger_kind=TriggerKind.turn)
    assert any(c.name == "tracker-context" for c in session_contribs)
    assert not any(c.name == "tracker-context" for c in turn_contribs)
