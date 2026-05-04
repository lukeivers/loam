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

"""AC.QSURF.6 — record_response() API.

Per cycle-4 plan §4 + §5 Surface #3 + AC.QSURF.6:

  - Returns a RecordedResponse dataclass.
  - Writes a record_response audit-log entry.
  - Clears pending_response_for in state.yaml.
  - Idempotent on duplicate call against the same surfaced_audit_path.
  - Rejects empty response_text.
  - Validates the linked surfacing exists + is well-formed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.per_project_pm.errors import PMStateCorruptedError
from loam.per_project_pm.runtime import PMRuntime
from loam.per_project_pm.state import RecordedResponse


def _author_pm(
    workspace_root: Path,
    pm_name: str,
    *,
    require_owner_response: bool = True,
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
            "onboarding_mode": False,
            "max_questions_per_turn": 1,
            "cool_down_seconds": 0,
            "require_owner_response": require_owner_response,
        },
    }
    (pm_dir / "contract.yaml").write_text(yaml.safe_dump(contract))


def test_record_response_returns_RecordedResponse(
    tmp_workspace: Path,
) -> None:
    _author_pm(tmp_workspace, "rr-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "rr-pm")
    runtime.enqueue_decision("Q1", provenance="t1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    response = runtime.record_response(surfaced.audit_path, "A1")
    assert isinstance(response, RecordedResponse)
    assert response.response_text == "A1"
    assert response.surfaced_question_text == "Q1"
    assert response.surfaced_audit_path == surfaced.audit_path
    assert response.audit_path.exists()


def test_record_response_writes_audit_entry(tmp_workspace: Path) -> None:
    _author_pm(tmp_workspace, "audit-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "audit-pm")
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    response = runtime.record_response(surfaced.audit_path, "Yes")
    payload = yaml.safe_load(response.audit_path.read_text())
    assert payload["event_kind"] == "record_response"
    assert payload["response_text"] == "Yes"


def test_record_response_clears_pending_flag(tmp_workspace: Path) -> None:
    _author_pm(tmp_workspace, "clear-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "clear-pm")
    runtime.enqueue_decision("Q1")
    runtime.surface_next_questions_batch(n=1)  # sets pending_response_for=Q1

    state_pre = runtime.state_of_world()
    assert state_pre.pending_response_for == "Q1"

    audit_dir = (
        tmp_workspace / "workspace" / ".loam" / "pms" / "clear-pm" / "audit-log"
    )
    surfacing = sorted(audit_dir.glob("*.yaml"))[0]
    runtime.record_response(surfacing, "A1")

    state_post = runtime.state_of_world()
    assert state_post.pending_response_for is None


def test_record_response_idempotent_on_duplicate_call(
    tmp_workspace: Path,
) -> None:
    """A second record_response against the same surfaced_audit_path
    returns the prior response without writing a duplicate entry."""
    _author_pm(tmp_workspace, "idem-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "idem-pm")
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None

    r1 = runtime.record_response(surfaced.audit_path, "first answer")
    audit_dir = (
        tmp_workspace / "workspace" / ".loam" / "pms" / "idem-pm" / "audit-log"
    )
    files_after_first = set(audit_dir.glob("*.yaml"))

    # Second call — should NOT write a new entry.
    r2 = runtime.record_response(surfaced.audit_path, "second answer (ignored)")
    files_after_second = set(audit_dir.glob("*.yaml"))
    assert files_after_first == files_after_second

    # Both calls return the SAME data (the FIRST response, unchanged).
    assert r1.response_text == "first answer"
    assert r2.response_text == "first answer"
    assert r1.audit_path == r2.audit_path


def test_record_response_rejects_empty_text(tmp_workspace: Path) -> None:
    _author_pm(tmp_workspace, "empty-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "empty-pm")
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    with pytest.raises(ValueError):
        runtime.record_response(surfaced.audit_path, "")


def test_record_response_rejects_missing_audit_path(
    tmp_workspace: Path,
) -> None:
    _author_pm(tmp_workspace, "missing-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "missing-pm")
    bogus = (
        tmp_workspace
        / "workspace"
        / ".loam"
        / "pms"
        / "missing-pm"
        / "audit-log"
        / "9999-12-31-9999.yaml"
    )
    with pytest.raises(FileNotFoundError):
        runtime.record_response(bogus, "A")


def test_record_response_rejects_wrong_event_kind(
    tmp_workspace: Path,
) -> None:
    """If the linked path points at a record_response (or any
    non-surface_question entry), record_response refuses."""
    _author_pm(tmp_workspace, "wrong-kind-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "wrong-kind-pm")
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    response = runtime.record_response(surfaced.audit_path, "A1")

    # Now try to record_response against the response audit path itself.
    with pytest.raises(PMStateCorruptedError):
        runtime.record_response(response.audit_path, "A2")


def test_record_response_RecordedResponse_is_audit_block_trigger(
    tmp_workspace: Path,
) -> None:
    """RecordedResponse exposes is_audit_block_trigger=True per
    AC.QSURF.8 (cross-AC tie-in for completeness)."""
    _author_pm(tmp_workspace, "trigger-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "trigger-pm")
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    response = runtime.record_response(surfaced.audit_path, "A1")
    assert response.is_audit_block_trigger is True


def test_record_response_accepts_relative_path(tmp_workspace: Path) -> None:
    """The API accepts a relative path (relative to PM dir) for
    convenience — matches the storage shape inside audit-log entries."""
    _author_pm(tmp_workspace, "rel-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "rel-pm")
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    pm_dir = tmp_workspace / "workspace" / ".loam" / "pms" / "rel-pm"
    relative_path = surfaced.audit_path.relative_to(pm_dir)

    response = runtime.record_response(relative_path, "A1")
    assert response.response_text == "A1"
