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

"""AC.PPM.4 — PMRuntime.from_workspace() loader resolves workspace-state.

Per parent plan §5 + cycle-2 plan §4 Surface #5:
  - Reads <workspace>/workspace/.loam/pms/<pm_name>/contract.yaml +
    state.yaml + decision-queue.yaml.
  - Returns hydrated runtime.
  - Raises PMNotFoundError when contract.yaml absent.
  - Raises PMStateCorruptedError on schema mismatch.
  - PMRuntime.empty_state_for(workspace_root) returns empty StateOfWorld
    without raising.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.per_project_pm.errors import PMNotFoundError, PMStateCorruptedError
from loam.per_project_pm.runtime import PMRuntime
from loam.per_project_pm.state import StateOfWorld


def test_load_authored_pm(authored_pm: tuple[Path, str]) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    assert runtime.contract.handle == pm_name
    assert runtime.contract.project_kind == "general"
    assert runtime.workspace_state_dir == (
        workspace_root / "workspace" / ".loam" / "pms" / pm_name
    )


def test_PMNotFoundError_on_missing_contract(tmp_workspace: Path) -> None:
    with pytest.raises(PMNotFoundError) as excinfo:
        PMRuntime.from_workspace(tmp_workspace, "no-such-pm")
    # Error message names the missing path so the operator can fix.
    assert "contract.yaml" in str(excinfo.value)


def test_PMStateCorruptedError_on_missing_required_field(
    tmp_workspace: Path,
) -> None:
    pm_name = "broken-pm"
    pm_dir = tmp_workspace / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    # Missing required fields: project_name, project_kind, owner_name,
    # workspace_root.
    (pm_dir / "contract.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "handle": pm_name,
            }
        )
    )
    with pytest.raises(PMStateCorruptedError) as excinfo:
        PMRuntime.from_workspace(tmp_workspace, pm_name)
    # The exception body carries the underlying ValidationError text
    # which names each missing field.
    msg = str(excinfo.value)
    assert "validation" in msg.lower() or "field" in msg.lower()


def test_PMStateCorruptedError_on_invalid_project_kind(
    tmp_workspace: Path,
) -> None:
    pm_name = "wrong-kind-pm"
    pm_dir = tmp_workspace / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    (pm_dir / "contract.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "handle": pm_name,
                "project_name": "wrong-kind",
                "project_kind": "not-a-kind",
                "owner_name": "Tester",
                "workspace_root": str(tmp_workspace),
            }
        )
    )
    with pytest.raises(PMStateCorruptedError):
        PMRuntime.from_workspace(tmp_workspace, pm_name)


def test_PMStateCorruptedError_on_unexpected_schema_version(
    tmp_workspace: Path,
) -> None:
    pm_name = "future-pm"
    pm_dir = tmp_workspace / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    (pm_dir / "contract.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 99,
                "handle": pm_name,
                "project_name": "future",
                "project_kind": "general",
                "owner_name": "Tester",
                "workspace_root": str(tmp_workspace),
            }
        )
    )
    with pytest.raises(PMStateCorruptedError) as excinfo:
        PMRuntime.from_workspace(tmp_workspace, pm_name)
    assert "schema_version" in str(excinfo.value)


def test_PMStateCorruptedError_on_malformed_yaml(tmp_workspace: Path) -> None:
    pm_name = "malformed-pm"
    pm_dir = tmp_workspace / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    (pm_dir / "contract.yaml").write_text("not: valid: yaml: [[[\nbad\n")
    with pytest.raises(PMStateCorruptedError):
        PMRuntime.from_workspace(tmp_workspace, pm_name)


def test_empty_state_for_returns_empty_state(tmp_workspace: Path) -> None:
    state = PMRuntime.empty_state_for(tmp_workspace)
    assert isinstance(state, StateOfWorld)
    assert state.pm_loaded is False
    assert state.handle is None
    assert state.project_name is None
    assert state.queue_depth == 0
    assert state.pending_questions == ()
    assert state.last_surfaced_at is None
    assert state.workspace_state_dir is None


def test_empty_state_for_does_not_raise_when_workspace_has_no_pms_dir(
    tmp_workspace: Path,
) -> None:
    # No <ws>/workspace/.loam/pms/ directory exists; empty_state_for
    # must not touch the filesystem at all.
    pms_dir = tmp_workspace / "workspace" / ".loam" / "pms"
    assert not pms_dir.exists()
    PMRuntime.empty_state_for(tmp_workspace)
    # Still doesn't exist — no side effect.
    assert not pms_dir.exists()


def test_load_with_state_yaml_and_decision_queue(
    authored_pm: tuple[Path, str],
) -> None:
    """A PM with state.yaml + decision-queue.yaml authored loads cleanly."""
    workspace_root, pm_name = authored_pm
    pm_dir = workspace_root / "workspace" / ".loam" / "pms" / pm_name
    (pm_dir / "state.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "in_flight": ["task-1"],
                "last_surfaced_at": "2026-05-04T10:00:00+00:00",
                "notes": "Test notes",
            }
        )
    )
    (pm_dir / "decision-queue.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "queue": [
                    {
                        "text": "Q1",
                        "provenance": "test",
                        "enqueued_at": "2026-05-04T09:00:00+00:00",
                    }
                ],
            }
        )
    )
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    state = runtime.state_of_world()
    assert state.pm_loaded is True
    assert state.queue_depth == 1
    assert state.pending_questions == ("Q1",)
    assert state.last_surfaced_at == "2026-05-04T10:00:00+00:00"


def test_PMStateCorruptedError_on_corrupt_decision_queue(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    pm_dir = workspace_root / "workspace" / ".loam" / "pms" / pm_name
    # Queue entry missing required 'text' field.
    (pm_dir / "decision-queue.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "queue": [{"provenance": "test"}],
            }
        )
    )
    with pytest.raises(PMStateCorruptedError):
        PMRuntime.from_workspace(workspace_root, pm_name)
