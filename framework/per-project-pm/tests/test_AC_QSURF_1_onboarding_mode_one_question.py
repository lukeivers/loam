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

"""AC.QSURF.1 — onboarding_mode flag toggles max_questions_per_turn enforcement.

Per cycle-4 plan §4 + AC.QSURF.1:

  - With onboarding_mode=True, surface_next_questions_batch() returns
    exactly 1 question per call regardless of n or
    max_questions_per_turn.
  - With onboarding_mode=False, surface_next_questions_batch() returns
    up to min(n, max_questions_per_turn, len(queue)) questions.
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
    """Author a PM contract with explicit policy values."""
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


def test_onboarding_mode_forces_one_per_batch_call(
    tmp_workspace: Path,
) -> None:
    """With onboarding_mode=True, every batch call returns exactly 1
    question — even when max_questions_per_turn is higher and the
    caller passes a larger n."""
    _author_pm_with_policy(
        tmp_workspace,
        "onboarding-pm",
        onboarding_mode=True,
        max_questions_per_turn=3,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "onboarding-pm")
    for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        runtime.enqueue_decision(q)

    # n=3 + max_questions_per_turn=3 BUT onboarding_mode=True → forced 1.
    batch = runtime.surface_next_questions_batch(n=3)
    assert len(batch) == 1
    assert batch[0].text == "Q1"


def test_non_onboarding_permits_max_questions_per_turn(
    tmp_workspace: Path,
) -> None:
    """With onboarding_mode=False + max_questions_per_turn=3 + n=3,
    batch returns 3."""
    _author_pm_with_policy(
        tmp_workspace,
        "post-onboarding-pm",
        onboarding_mode=False,
        max_questions_per_turn=3,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "post-onboarding-pm")
    for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        runtime.enqueue_decision(q)

    batch = runtime.surface_next_questions_batch(n=3)
    assert len(batch) == 3
    assert tuple(sq.text for sq in batch) == ("Q1", "Q2", "Q3")


def test_onboarding_mode_n_param_ignored(tmp_workspace: Path) -> None:
    """Onboarding-mode forces 1 even when caller passes n=10."""
    _author_pm_with_policy(
        tmp_workspace,
        "onboarding-pm",
        onboarding_mode=True,
        max_questions_per_turn=10,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "onboarding-pm")
    for q in ["Q1", "Q2", "Q3"]:
        runtime.enqueue_decision(q)

    batch = runtime.surface_next_questions_batch(n=10)
    assert len(batch) == 1


def test_non_onboarding_caps_at_queue_length(tmp_workspace: Path) -> None:
    """Effective batch size is capped at queue length when queue is
    shallower than n + max_questions_per_turn."""
    _author_pm_with_policy(
        tmp_workspace,
        "shallow-queue-pm",
        onboarding_mode=False,
        max_questions_per_turn=5,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "shallow-queue-pm")
    runtime.enqueue_decision("Q1")
    runtime.enqueue_decision("Q2")

    batch = runtime.surface_next_questions_batch(n=5)
    assert len(batch) == 2  # capped at queue length


def test_default_n_uses_max_questions_per_turn(
    tmp_workspace: Path,
) -> None:
    """When n is omitted, batch defaults to max_questions_per_turn."""
    _author_pm_with_policy(
        tmp_workspace,
        "default-n-pm",
        onboarding_mode=False,
        max_questions_per_turn=2,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "default-n-pm")
    for q in ["Q1", "Q2", "Q3", "Q4"]:
        runtime.enqueue_decision(q)

    batch = runtime.surface_next_questions_batch()  # no n
    assert len(batch) == 2


def test_empty_queue_returns_empty_tuple(tmp_workspace: Path) -> None:
    """Empty queue → empty tuple (not None / not exception)."""
    _author_pm_with_policy(
        tmp_workspace,
        "empty-pm",
        onboarding_mode=False,
        max_questions_per_turn=3,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "empty-pm")
    batch = runtime.surface_next_questions_batch(n=3)
    assert batch == ()


def test_zero_n_returns_empty_tuple(tmp_workspace: Path) -> None:
    """n=0 → empty tuple (legitimate caller no-op)."""
    _author_pm_with_policy(
        tmp_workspace,
        "zero-n-pm",
        onboarding_mode=False,
        max_questions_per_turn=3,
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "zero-n-pm")
    runtime.enqueue_decision("Q1")
    batch = runtime.surface_next_questions_batch(n=0)
    assert batch == ()
