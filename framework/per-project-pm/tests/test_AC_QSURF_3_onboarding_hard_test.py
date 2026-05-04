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

"""AC.QSURF.3 — onboarding-mode hard test (per dispatch wording).

Per cycle-4 plan §4 + AC.QSURF.3:

  Across 5 simulated turns of onboarding-mode (5 distinct
  surface_next_questions_batch() calls), with 5 enqueued questions,
  exactly 1 question is surfaced per turn; total = 5; queue depth
  goes 5→4→3→2→1→0; audit-log carries 5 entries; assertion
  len(surfaced_in_turn_N) == 1 for N=1..5.

Per cycle-4 plan §5 Surface #6: the test is structurally
deterministic, not probabilistic. Tuple length is the assertion;
internal randomness is impossible.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam.per_project_pm.runtime import PMRuntime


def _author_onboarding_pm(
    workspace_root: Path,
    pm_name: str,
    *,
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
            "onboarding_mode": True,
            "max_questions_per_turn": 1,
            "cool_down_seconds": 0,
            "require_owner_response": require_owner_response,
        },
    }
    (pm_dir / "contract.yaml").write_text(yaml.safe_dump(contract))


def test_exactly_one_per_turn_across_five_turns(
    tmp_workspace: Path,
) -> None:
    """The hard test: 5 turns × 1 question per turn × 5 enqueued."""
    _author_onboarding_pm(tmp_workspace, "hard-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "hard-pm")
    questions = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    for q in questions:
        runtime.enqueue_decision(q)

    surfaced_per_turn: list[tuple[str, ...]] = []
    for turn in range(5):
        batch = runtime.surface_next_questions_batch()
        # **The structural assertion**: exactly 1 per turn.
        assert len(batch) == 1, (
            f"Turn {turn + 1}: expected exactly 1 surfaced, got {len(batch)}"
        )
        surfaced_per_turn.append(tuple(sq.text for sq in batch))

    # Total = 5; FIFO order preserved across turns.
    flat = [text for turn_texts in surfaced_per_turn for text in turn_texts]
    assert flat == questions
    # Queue drained.
    state = runtime.state_of_world()
    assert state.queue_depth == 0
    # Audit-log has 5 surface entries.
    audit_dir = (
        tmp_workspace / "workspace" / ".loam" / "pms" / "hard-pm" / "audit-log"
    )
    surface_entries = [
        yaml.safe_load(f.read_text())
        for f in sorted(audit_dir.glob("*.yaml"))
        if yaml.safe_load(f.read_text()).get("event_kind") == "surface_question"
    ]
    assert len(surface_entries) == 5


def test_queue_depth_decrements_one_per_turn(tmp_workspace: Path) -> None:
    """Queue depth goes 5→4→3→2→1→0 across 5 turns."""
    _author_onboarding_pm(tmp_workspace, "depth-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "depth-pm")
    for q in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        runtime.enqueue_decision(q)

    expected_depths = [4, 3, 2, 1, 0]
    for expected in expected_depths:
        runtime.surface_next_questions_batch()
        state = runtime.state_of_world()
        assert state.queue_depth == expected


def test_structural_determinism_repeated_runs(tmp_workspace: Path) -> None:
    """Run the hard test 3 times in a row from clean state; every run
    produces identical results. Per cycle-4 plan §5 Surface #6:
    the assertion `len(returned) == 1` is structural, not
    probabilistic.
    """
    for run_number in range(3):
        pm_name = f"determinism-pm-{run_number}"
        _author_onboarding_pm(tmp_workspace, pm_name)
        runtime = PMRuntime.from_workspace(tmp_workspace, pm_name)
        for q in ["A", "B", "C"]:
            runtime.enqueue_decision(q)

        # Every turn yields exactly 1.
        for turn in range(3):
            batch = runtime.surface_next_questions_batch()
            assert len(batch) == 1


def test_onboarding_mode_with_n_override_still_one(
    tmp_workspace: Path,
) -> None:
    """Even when caller passes n=100, onboarding-mode forces 1."""
    _author_onboarding_pm(tmp_workspace, "override-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "override-pm")
    for q in ["Q1", "Q2", "Q3"]:
        runtime.enqueue_decision(q)

    batch = runtime.surface_next_questions_batch(n=100)
    assert len(batch) == 1
