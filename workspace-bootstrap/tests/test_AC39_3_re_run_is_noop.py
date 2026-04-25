"""Amendment #39 — AC39.3 — Re-running first-run on a workspace
with an existing seeded tracker is a no-op.

Plan §4 AC39.3 outcomes:

- Re-run does NOT create a duplicate root.
- Re-run does NOT modify any existing seeded record (``get(<seed-id>)``
  returns identical fields pre/post).
- Re-run does NOT emit additional ``objective_created`` events for
  already-seeded IDs.
- Re-run does NOT raise — first-run completes successfully.

Behaviour holds whether descendants have been added, modified, or
marked achieved/abandoned by user activity since the original seed.

Maps to objective-tracker D8 (semantic round-trip — re-runs preserve
state) → AC.PO.1.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from objective_tracker import ObjectiveTracker

from workspace_bootstrap.adapters.first_run_scaffold import (
    run_first_run_scaffold,
)
from workspace_bootstrap.adapters.tracker_seed import (
    FRAMEWORK_VALUE_PROP_RELPATH,
    ROOT_OBJECTIVE_ID,
    _SPEC_TIER_PHASES,
    classify_workspace,
    load_value_prop_source,
    seed_tracker,
    tracker_db_path_for,
)


def _seed_dev(tmp_path: Path, suffix: str = "") -> tuple[Path, Path]:
    """Seed a dev-classified workspace. Sub-plan E (amendment #42):
    pre-create the persona contract carrying ``dev_intent: yes`` so
    ``classify_workspace`` returns "pos-v2-dev"."""
    workspace = tmp_path / f"ws-noop{suffix}"
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
    _seed_dev_intent_contract(workspace)
    pos_root = tmp_path / f".pos{suffix}"
    agents = tmp_path / f"LaunchAgents{suffix}"
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
    )
    return workspace, pos_root


def _seed_dev_intent_contract(workspace: Path) -> None:
    """Pre-create a persona contract carrying ``dev_intent: yes`` so
    sub-plan E's ``classify_workspace`` reads "pos-v2-dev"."""
    from primary_persona.contract import PersonaContract
    from primary_persona.onboarding import dev_intent_storage_path

    personas_dir = dev_intent_storage_path(workspace)
    persona_dir = personas_dir / "primary"
    persona_dir.mkdir(parents=True)
    contract = PersonaContract.model_validate(
        {
            "handle": "primary",
            "given_name": "Primary",
            "contract_version": "1.0.0",
            "responsibilities": {
                "single_point_of_contact": "Coordinator.",
                "context_holder": "Holds context.",
                "escalation_judge": "Decides surfacing.",
            },
            "authority_boundary": {
                "tier_a": "defer",
                "tier_b": "defer",
                "tier_c": "execute",
                "tier_d": "execute",
            },
            "escalation_taxonomy": {"categories": ["x"]},
            "severity_vocabulary": {"labels": ["a", "b"]},
            "is_starter": False,
            "is_primary": True,
            "dev_intent": "yes",
        }
    )
    (persona_dir / "contract.yaml").write_text(contract.to_yaml())


def _record_snapshot(tracker: ObjectiveTracker, ids: list[str]) -> dict:
    """Return a stable comparison view of each named record."""
    out: dict[str, dict] = {}
    for oid in ids:
        proj = tracker.get(oid)
        assert proj is not None, f"{oid} missing"
        out[oid] = {
            "goal": proj.goal,
            "parent_id": proj.parent_id,
            "authored_by": proj.authored_by,
            "lifted_from": (
                None
                if proj.lifted_from is None
                else (
                    proj.lifted_from.source_doc,
                    proj.lifted_from.source_ac,
                    proj.lifted_from.source_commit,
                )
            ),
            "criteria": tuple(
                (c.criterion_id, c.kind) for c in proj.acceptance_criteria
            ),
            "evergreen": proj.time_bound.evergreen,
        }
    return out


def test_AC39_3_seed_tracker_re_invocation_is_noop(tmp_path: Path) -> None:
    """Calling ``seed_tracker`` directly twice on the same DB
    produces ``reason == "already_seeded"`` on the second call and
    leaves every record unchanged."""
    workspace, pos_root = _seed_dev(tmp_path)
    db_path = tracker_db_path_for(workspace)
    classification = classify_workspace(workspace)
    vp = load_value_prop_source(workspace, classification)

    ids = [ROOT_OBJECTIVE_ID] + [
        f"spec-{suffix}" for suffix, _, _ in _SPEC_TIER_PHASES
    ]
    tracker = ObjectiveTracker(db_path)
    try:
        pre = _record_snapshot(tracker, ids)
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
    assert result.reason == "already_seeded"
    assert result.descendants_seeded == ()
    assert result.seeded is False

    tracker = ObjectiveTracker(db_path)
    try:
        post = _record_snapshot(tracker, ids)
    finally:
        tracker.close()

    assert pre == post


def test_AC39_3_full_scaffold_re_run_does_not_raise(tmp_path: Path) -> None:
    """``run_first_run_scaffold`` re-invoked against an
    already-scaffolded workspace returns the existing
    ``already_scaffolded`` short-circuit and leaves the tracker
    state intact (the short-circuit fires before tracker-seed runs;
    the seed's idempotency contract is verified by the direct
    re-invocation test above)."""
    workspace, pos_root = _seed_dev(tmp_path)
    db_path = tracker_db_path_for(workspace)

    ids = [ROOT_OBJECTIVE_ID] + [
        f"spec-{suffix}" for suffix, _, _ in _SPEC_TIER_PHASES
    ]
    tracker = ObjectiveTracker(db_path)
    try:
        pre = _record_snapshot(tracker, ids)
    finally:
        tracker.close()

    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "LaunchAgents",
        workspace_root=workspace,
    )
    assert result.ran is False
    assert result.reason == "already_scaffolded"

    tracker = ObjectiveTracker(db_path)
    try:
        post = _record_snapshot(tracker, ids)
    finally:
        tracker.close()
    assert pre == post


def test_AC39_3_re_run_preserves_user_modifications(tmp_path: Path) -> None:
    """A user-driven status transition on a seeded descendant survives
    a direct re-invocation of ``seed_tracker``. The seed never clobbers."""
    workspace, pos_root = _seed_dev(tmp_path)
    db_path = tracker_db_path_for(workspace)
    classification = classify_workspace(workspace)
    vp = load_value_prop_source(workspace, classification)

    # User marks one spec descendant as active.
    tracker = ObjectiveTracker(db_path)
    try:
        asyncio.run(tracker.start("spec-v1.0"))
    finally:
        tracker.close()

    # Re-seed.
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
        proj = tracker.get("spec-v1.0")
        assert proj is not None
        assert proj.status.value == "active", (
            "user-driven status transition lost across re-seed"
        )
    finally:
        tracker.close()


def test_AC39_3_only_one_objective_created_event_per_seed_id(
    tmp_path: Path,
) -> None:
    """For each seeded objective ID there is exactly one
    ``ObjectiveCreated`` event in the event log after multiple
    re-runs of ``seed_tracker``."""
    workspace, pos_root = _seed_dev(tmp_path)
    db_path = tracker_db_path_for(workspace)
    classification = classify_workspace(workspace)
    vp = load_value_prop_source(workspace, classification)

    # Multiple re-runs — should not emit additional ObjectiveCreated.
    for _ in range(3):
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
        ids = [ROOT_OBJECTIVE_ID] + [
            f"spec-{suffix}" for suffix, _, _ in _SPEC_TIER_PHASES
        ]
        for oid in ids:
            events = tracker.store.events_for(oid)
            created_events = [
                e for e in events if e.__class__.__name__ == "ObjectiveCreated"
            ]
            assert len(created_events) == 1, (
                f"{oid} has {len(created_events)} ObjectiveCreated events; "
                "expected exactly one"
            )
    finally:
        tracker.close()
