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

"""AC.QSURF.5 — require_owner_response blocks subsequent surfacings
until prior is responded.

Per cycle-4 plan §4 + §5 Surface #8 + AC.QSURF.5:

  - Blocking enforcement lives on surface_next_questions_batch (NOT
    on surface_next_question, per the Cycle 2 contract preservation
    fallback).
  - With require_owner_response=True: enqueue Q1, Q2; surface batch →
    Q1 lands. Surface batch again → PendingResponseError raised.
    Record Q1's response → next batch surfaces Q2.
  - With require_owner_response=False: no blocking; sequential batches
    succeed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.per_project_pm.errors import PendingResponseError
from loam.per_project_pm.runtime import PMRuntime


def _author_pm_with_policy(
    workspace_root: Path,
    pm_name: str,
    *,
    require_owner_response: bool,
    onboarding_mode: bool = False,
    max_questions_per_turn: int = 1,
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


def test_blocking_raises_on_second_batch_without_response(
    tmp_workspace: Path,
) -> None:
    _author_pm_with_policy(
        tmp_workspace,
        "block-pm",
        require_owner_response=True,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "block-pm")
    runtime.enqueue_decision("Q1")
    runtime.enqueue_decision("Q2")

    batch1 = runtime.surface_next_questions_batch(n=1)
    assert len(batch1) == 1
    assert batch1[0].text == "Q1"

    # Second batch without record_response → blocked.
    with pytest.raises(PendingResponseError) as excinfo:
        runtime.surface_next_questions_batch(n=1)
    assert excinfo.value.pending_question == "Q1"


def test_record_response_clears_blocking(tmp_workspace: Path) -> None:
    _author_pm_with_policy(
        tmp_workspace,
        "clear-pm",
        require_owner_response=True,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "clear-pm")
    runtime.enqueue_decision("Q1")
    runtime.enqueue_decision("Q2")

    batch1 = runtime.surface_next_questions_batch(n=1)
    runtime.record_response(batch1[0].audit_path, "A1")

    # Now the second surfacing succeeds.
    batch2 = runtime.surface_next_questions_batch(n=1)
    assert len(batch2) == 1
    assert batch2[0].text == "Q2"


def test_no_blocking_when_require_owner_response_false(
    tmp_workspace: Path,
) -> None:
    """With require_owner_response=False, sequential batches succeed
    without intervening record_response calls."""
    _author_pm_with_policy(
        tmp_workspace,
        "noblock-pm",
        require_owner_response=False,
        max_questions_per_turn=1,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "noblock-pm")
    for q in ["Q1", "Q2", "Q3"]:
        runtime.enqueue_decision(q)

    batch1 = runtime.surface_next_questions_batch(n=1)
    batch2 = runtime.surface_next_questions_batch(n=1)
    batch3 = runtime.surface_next_questions_batch(n=1)
    assert tuple(b[0].text for b in (batch1, batch2, batch3)) == (
        "Q1",
        "Q2",
        "Q3",
    )


def test_pending_response_error_carries_question_text(
    tmp_workspace: Path,
) -> None:
    """The exception body carries pending_question + surfaced_audit_path
    so the caller can re-prompt."""
    _author_pm_with_policy(
        tmp_workspace,
        "err-fields-pm",
        require_owner_response=True,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "err-fields-pm")
    runtime.enqueue_decision("Important question?")
    runtime.enqueue_decision("Q2")

    batch1 = runtime.surface_next_questions_batch(n=1)
    surfaced_path = batch1[0].audit_path

    with pytest.raises(PendingResponseError) as excinfo:
        runtime.surface_next_questions_batch(n=1)
    err = excinfo.value
    assert err.pending_question == "Important question?"
    # surfaced_audit_path resolves back to the original surfacing.
    assert str(surfaced_path) in err.surfaced_audit_path or (
        Path(err.surfaced_audit_path).resolve() == surfaced_path.resolve()
    )


def test_blocking_does_not_partial_surface(tmp_workspace: Path) -> None:
    """Per cycle-4 plan §5 Surface #2: blocking raises immediately;
    no partial batch.
    """
    _author_pm_with_policy(
        tmp_workspace,
        "no-partial-pm",
        require_owner_response=True,
        max_questions_per_turn=3,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "no-partial-pm")
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        runtime.enqueue_decision(q)

    # First batch: surfaces Q1 (the require_owner_response stops the
    # batch after 1 surfacing per cycle-4 design — see runtime.py
    # comment in surface_next_questions_batch).
    batch1 = runtime.surface_next_questions_batch(n=3)
    assert len(batch1) == 1
    state = runtime.state_of_world()
    assert state.queue_depth == 3  # Q1 surfaced; Q2/Q3/Q4 still queued.
    assert state.pending_response_for == "Q1"

    # Second batch: blocked.
    with pytest.raises(PendingResponseError):
        runtime.surface_next_questions_batch(n=3)


def test_pending_response_for_visible_in_state_of_world(
    tmp_workspace: Path,
) -> None:
    """state_of_world() exposes pending_response_for so callers can
    detect blocking without triggering the exception."""
    _author_pm_with_policy(
        tmp_workspace,
        "state-pm",
        require_owner_response=True,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "state-pm")
    runtime.enqueue_decision("Q1")

    # Pre-surface: pending_response_for is None.
    state_pre = runtime.state_of_world()
    assert state_pre.pending_response_for is None

    runtime.surface_next_questions_batch(n=1)

    # Post-surface: pending_response_for is set.
    state_post = runtime.state_of_world()
    assert state_post.pending_response_for == "Q1"

    # Post-record: cleared.
    audit_dir = tmp_workspace / "workspace" / ".loam" / "pms" / "state-pm" / "audit-log"
    audit_files = sorted(audit_dir.glob("*.yaml"))
    surfacing_audit = audit_files[0]
    runtime.record_response(surfacing_audit, "A1")

    state_after_response = runtime.state_of_world()
    assert state_after_response.pending_response_for is None
