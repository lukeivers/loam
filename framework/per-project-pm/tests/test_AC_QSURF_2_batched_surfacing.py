# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.QSURF.2 — non-onboarding-mode permits batched surfacing per
max_questions_per_turn.

Per cycle-4 plan §4 + AC.QSURF.2:

  - With onboarding_mode=False + max_questions_per_turn=3: enqueue 5;
    surface_next_questions_batch() returns 3.
  - Queue advances by exactly 3.
  - Audit-log records 3 entries.
  - Each entry has its own queue_position (1, 2, 3 within the batch).
  - FIFO order preserved across the batch.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam.per_project_pm.runtime import PMRuntime


def _author_pm_with_policy(
    workspace_root: Path,
    pm_name: str,
    *,
    onboarding_mode: bool,
    max_questions_per_turn: int,
    require_owner_response: bool = False,
) -> None:
    pm_dir = workspace_root / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True, exist_ok=True)
    contract = {
        "schema_version": 1,
        "handle": pm_name,
        "project_name": "test-project",
        "project_kind": "general",
        "owner_name": "Tester",
        "workspace_root": str(workspace_root),
        "decision_surfacing_policy": {
            "onboarding_mode": onboarding_mode,
            "max_questions_per_turn": max_questions_per_turn,
            "cool_down_seconds": 0,
            "require_owner_response": require_owner_response,
        },
    }
    (pm_dir / "contract.yaml").write_text(yaml.safe_dump(contract))


def test_batch_returns_three_for_max_three_n_three(
    tmp_workspace: Path,
) -> None:
    _author_pm_with_policy(
        tmp_workspace,
        "batch-pm",
        onboarding_mode=False,
        max_questions_per_turn=3,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "batch-pm")
    for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        runtime.enqueue_decision(q)

    batch = runtime.surface_next_questions_batch(n=3)
    assert len(batch) == 3


def test_batch_advances_queue_by_three(tmp_workspace: Path) -> None:
    _author_pm_with_policy(
        tmp_workspace,
        "batch-pm",
        onboarding_mode=False,
        max_questions_per_turn=3,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "batch-pm")
    for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        runtime.enqueue_decision(q)

    runtime.surface_next_questions_batch(n=3)
    state = runtime.state_of_world()
    assert state.queue_depth == 2
    assert state.pending_questions == ("Q4", "Q5")


def test_batch_writes_three_audit_log_entries(tmp_workspace: Path) -> None:
    _author_pm_with_policy(
        tmp_workspace,
        "batch-pm",
        onboarding_mode=False,
        max_questions_per_turn=3,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "batch-pm")
    for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        runtime.enqueue_decision(q)

    batch = runtime.surface_next_questions_batch(n=3)
    audit_dir = (
        tmp_workspace / "workspace" / ".loam" / "pms" / "batch-pm" / "audit-log"
    )
    audit_files = sorted(audit_dir.glob("*.yaml"))
    # 3 surface_question entries.
    surface_entries = [
        yaml.safe_load(f.read_text())
        for f in audit_files
        if yaml.safe_load(f.read_text()).get("event_kind") == "surface_question"
    ]
    assert len(surface_entries) == 3
    # And each batch element points at one of those audit files.
    audit_paths = {sq.audit_path for sq in batch}
    assert len(audit_paths) == 3


def test_batch_preserves_FIFO_order(tmp_workspace: Path) -> None:
    _author_pm_with_policy(
        tmp_workspace,
        "fifo-batch-pm",
        onboarding_mode=False,
        max_questions_per_turn=4,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "fifo-batch-pm")
    questions = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
    for q in questions:
        runtime.enqueue_decision(q)

    batch = runtime.surface_next_questions_batch(n=4)
    # FIFO across the batch.
    assert tuple(sq.text for sq in batch) == ("Alpha", "Beta", "Gamma", "Delta")


def test_batch_queue_positions_are_per_batch(tmp_workspace: Path) -> None:
    """Each element in the batch has a queue_position reflecting its
    1-based position WITHIN the batch (1, 2, 3...)."""
    _author_pm_with_policy(
        tmp_workspace,
        "pos-batch-pm",
        onboarding_mode=False,
        max_questions_per_turn=3,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "pos-batch-pm")
    for q in ["Q1", "Q2", "Q3"]:
        runtime.enqueue_decision(q)

    batch = runtime.surface_next_questions_batch(n=3)
    assert tuple(sq.queue_position for sq in batch) == (1, 2, 3)


def test_batch_two_calls_advance_queue_correctly(
    tmp_workspace: Path,
) -> None:
    _author_pm_with_policy(
        tmp_workspace,
        "multi-batch-pm",
        onboarding_mode=False,
        max_questions_per_turn=2,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "multi-batch-pm")
    for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        runtime.enqueue_decision(q)

    batch1 = runtime.surface_next_questions_batch(n=2)
    batch2 = runtime.surface_next_questions_batch(n=2)
    assert tuple(sq.text for sq in batch1) == ("Q1", "Q2")
    assert tuple(sq.text for sq in batch2) == ("Q3", "Q4")
    state = runtime.state_of_world()
    assert state.queue_depth == 1
    assert state.pending_questions == ("Q5",)
