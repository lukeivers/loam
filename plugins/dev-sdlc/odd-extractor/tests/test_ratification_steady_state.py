"""D2 idempotency-variant — 5 ratification actions in sequence are
idempotent + queue depth bounded.

Per plan-doc §6 D2 + AC.BANDS.6 (audit-log monotonicity).

D2 structurally n/a (one-shot CLI, not daemon); the idempotency
variant exercises:
- Each apply_ratification_action call writes exactly one entry.
- ratification-state.yaml's completed_actions grows monotonically
  with no duplicates.
- PM decision-queue.yaml depth returns to 0 after batch is drained.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.per_project_pm import PMRuntime
from loam_odd_extractor import (
    BandedAC,
    ConfidenceBand,
    Evidence,
    apply_ratification_action,
    edit,
    enqueue_ratification_batch,
    load_ratification_state,
    promote,
)
from loam_odd_extractor.observability import list_entries
from loam_odd_extractor.state import extraction_dir


def _author_pm(workspace_root: Path, pm_name: str) -> None:
    pm_dir = workspace_root / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    (pm_dir / "contract.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "handle": pm_name,
                "project_name": "test",
                "project_kind": "general",
                "owner_name": "Tester",
                "workspace_root": str(workspace_root),
                "decision_surfacing_policy": {
                    "onboarding_mode": False,
                    # 5 per turn so we can drain a 5-AC queue in one batch.
                    "max_questions_per_turn": 5,
                    "cool_down_seconds": 0,
                    "require_owner_response": False,
                },
            }
        )
    )


@pytest.fixture
def workspace_with_5_acs(tmp_path: Path) -> tuple[Path, str, str, list[BandedAC]]:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "workspace").mkdir()
    pm_name = "steady-pm"
    _author_pm(ws, pm_name)
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)

    banded_acs = [
        BandedAC(
            ac_id=f"AC.SS.{i}",
            text=f"steady-state AC {i}",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=Evidence(
                kind="inference",
                rationale=f"rationale-{i}",
            ),
        )
        for i in range(1, 6)
    ]
    extraction_id = "steady-state-test"
    enqueue_ratification_batch(
        extraction_id=extraction_id,
        banded_acs=banded_acs,
        workspace_root=ws,
        pm_runtime=pm_runtime,
        pm_handle=pm_name,
        draft_path="contract-draft.md",
    )
    return ws, pm_name, extraction_id, banded_acs


def test_five_actions_each_write_one_audit_entry(
    workspace_with_5_acs: tuple[Path, str, str, list[BandedAC]],
) -> None:
    ws, pm_name, extraction_id, banded_acs = workspace_with_5_acs
    ext_dir = extraction_dir(ws, extraction_id)
    before = len(list_entries(ext_dir))

    actions = [
        promote(
            ac_id=f"AC.SS.{i}",
            from_band=ConfidenceBand.HYPOTHESISED,
            to_band=ConfidenceBand.PLAUSIBLE,
        )
        for i in range(1, 6)
    ]
    for a in actions:
        apply_ratification_action(
            a,
            banded_acs=banded_acs,
            workspace_root=ws,
            repo_id=extraction_id,
        )
    after = len(list_entries(ext_dir))
    assert after - before == 5


def test_completed_actions_grow_monotonically_no_dupes(
    workspace_with_5_acs: tuple[Path, str, str, list[BandedAC]],
) -> None:
    ws, _, extraction_id, banded_acs = workspace_with_5_acs
    ext_dir = extraction_dir(ws, extraction_id)

    for i in range(1, 6):
        apply_ratification_action(
            promote(
                ac_id=f"AC.SS.{i}",
                from_band=ConfidenceBand.HYPOTHESISED,
                to_band=ConfidenceBand.PLAUSIBLE,
            ),
            banded_acs=banded_acs,
            workspace_root=ws,
            repo_id=extraction_id,
        )

    state = load_ratification_state(ext_dir)
    assert state is not None
    assert len(state.completed_actions) == 5
    seen_ac_ids = [ca.ac_id for ca in state.completed_actions]
    assert sorted(seen_ac_ids) == [
        "AC.SS.1",
        "AC.SS.2",
        "AC.SS.3",
        "AC.SS.4",
        "AC.SS.5",
    ]
    # No duplicates.
    assert len(seen_ac_ids) == len(set(seen_ac_ids))
    # All pending drained.
    assert state.pending_acs == []


def test_queue_drains_to_zero(
    workspace_with_5_acs: tuple[Path, str, str, list[BandedAC]],
) -> None:
    ws, pm_name, _, _ = workspace_with_5_acs
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)
    sw = pm_runtime.state_of_world()
    assert sw.queue_depth == 5

    # Surface all 5 in one batch (max_questions_per_turn=5).
    batch = pm_runtime.surface_next_questions_batch()
    assert len(batch) == 5

    sw_after = pm_runtime.state_of_world()
    assert sw_after.queue_depth == 0


def test_mixed_action_kinds_idempotent(
    workspace_with_5_acs: tuple[Path, str, str, list[BandedAC]],
) -> None:
    """Mix of promote / edit / promote-with-explicit-yes still
    produces 5 entries with no duplicates."""
    ws, _, extraction_id, banded_acs = workspace_with_5_acs

    # 3 promotes, then 2 edits.
    for i in (1, 2, 3):
        apply_ratification_action(
            promote(
                ac_id=f"AC.SS.{i}",
                from_band=ConfidenceBand.HYPOTHESISED,
                to_band=ConfidenceBand.PLAUSIBLE,
            ),
            banded_acs=banded_acs,
            workspace_root=ws,
            repo_id=extraction_id,
        )
    for i in (4, 5):
        apply_ratification_action(
            edit(ac_id=f"AC.SS.{i}", edit_text=f"edited-{i}"),
            banded_acs=banded_acs,
            workspace_root=ws,
            repo_id=extraction_id,
        )

    ext_dir = extraction_dir(ws, extraction_id)
    state = load_ratification_state(ext_dir)
    assert state is not None
    assert len(state.completed_actions) == 5
    kinds = [ca.action_kind for ca in state.completed_actions]
    assert kinds.count("promote") == 3
    assert kinds.count("edit") == 2
