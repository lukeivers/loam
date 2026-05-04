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

"""AC.PPM.6 — enqueue_decision() API.

Per parent plan §5 + cycle-2 plan §4 Surface #5:
  - Appends to FIFO decision-queue.yaml.
  - Returns 1-based enqueued position.
  - Persists synchronously (no in-memory drift).
  - Records enqueued_at ISO 8601 timestamp.
  - Atomic write via tmp+rename.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

from loam.per_project_pm.runtime import PMRuntime


def test_enqueue_returns_1_based_position(authored_pm: tuple[Path, str]) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    p1 = runtime.enqueue_decision("Q1")
    p2 = runtime.enqueue_decision("Q2")
    p3 = runtime.enqueue_decision("Q3")
    assert p1 == 1
    assert p2 == 2
    assert p3 == 3


def test_enqueue_persists_to_disk_synchronously(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    runtime.enqueue_decision("Q1", provenance="prov-1")
    # Re-load from disk in a fresh runtime — no in-memory drift.
    runtime2 = PMRuntime.from_workspace(workspace_root, pm_name)
    state = runtime2.state_of_world()
    assert state.queue_depth == 1
    assert state.pending_questions == ("Q1",)


def test_enqueue_records_enqueued_at_iso_8601(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    pm_dir = workspace_root / "workspace" / ".loam" / "pms" / pm_name
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    runtime.enqueue_decision("Q1")
    queue_yaml = yaml.safe_load((pm_dir / "decision-queue.yaml").read_text())
    enqueued_at = queue_yaml["queue"][0]["enqueued_at"]
    parsed = datetime.fromisoformat(enqueued_at)
    delta = abs((datetime.now(tz=timezone.utc) - parsed).total_seconds())
    assert delta < 5


def test_enqueue_provenance_None_on_omitted(authored_pm: tuple[Path, str]) -> None:
    workspace_root, pm_name = authored_pm
    pm_dir = workspace_root / "workspace" / ".loam" / "pms" / pm_name
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    runtime.enqueue_decision("Q1")
    queue_yaml = yaml.safe_load((pm_dir / "decision-queue.yaml").read_text())
    assert queue_yaml["queue"][0]["provenance"] is None


def test_enqueue_rejects_empty_text(authored_pm: tuple[Path, str]) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    with pytest.raises(ValueError):
        runtime.enqueue_decision("")


def test_enqueue_writes_schema_version(authored_pm: tuple[Path, str]) -> None:
    workspace_root, pm_name = authored_pm
    pm_dir = workspace_root / "workspace" / ".loam" / "pms" / pm_name
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    runtime.enqueue_decision("Q1")
    queue_yaml = yaml.safe_load((pm_dir / "decision-queue.yaml").read_text())
    assert queue_yaml["schema_version"] == 1


def test_atomic_write_no_partial_state_visible(
    authored_pm: tuple[Path, str],
) -> None:
    """tmp+rename atomicity: post-call, the queue file always reflects
    the full new state. We can't easily inject a crash mid-write, but
    we verify the tmp file is cleaned up + the final file exists."""
    workspace_root, pm_name = authored_pm
    pm_dir = workspace_root / "workspace" / ".loam" / "pms" / pm_name
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    runtime.enqueue_decision("Q1")
    # No leftover .tmp files in the PM dir.
    tmp_files = list(pm_dir.glob(".decision-queue.yaml.*.tmp"))
    assert tmp_files == []
    assert (pm_dir / "decision-queue.yaml").exists()
