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

"""AC.QSURF.4 — audit-log records each surfacing AND each response with
full provenance.

Per cycle-4 plan §4 + §5 Surface #4 + AC.QSURF.4:

  - surface_question entries carry all Cycle 2 fields (verified by
    Cycle 2 tests).
  - record_response entries carry: schema_version, event_kind, timestamp,
    pm_handle, response_text, surfaced_audit_path, surfaced_question_text,
    responded_at.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from loam.per_project_pm.runtime import PMRuntime


def _author_pm_with_policy(
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


def test_record_response_audit_entry_carries_all_fields(
    tmp_workspace: Path,
) -> None:
    _author_pm_with_policy(tmp_workspace, "prov-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "prov-pm")
    runtime.enqueue_decision("Should we ship?", provenance="cycle-4-test")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None

    response = runtime.record_response(
        surfaced.audit_path, "Yes; ship it."
    )

    payload = yaml.safe_load(response.audit_path.read_text())
    assert payload["schema_version"] == 1
    assert payload["event_kind"] == "record_response"
    assert payload["pm_handle"] == "prov-pm"
    assert payload["response_text"] == "Yes; ship it."
    assert payload["surfaced_question_text"] == "Should we ship?"
    # surfaced_audit_path is stored relative to the PM dir.
    assert payload["surfaced_audit_path"].startswith("audit-log/")
    # Timestamp is ISO 8601 UTC.
    parsed = datetime.fromisoformat(payload["timestamp"])
    delta = abs((datetime.now(tz=timezone.utc) - parsed).total_seconds())
    assert delta < 5
    # responded_at == timestamp.
    assert payload["responded_at"] == payload["timestamp"]


def test_surface_then_record_audit_log_ordered(tmp_workspace: Path) -> None:
    """The audit-log NNNN counter increments across surface and
    record_response events within the same UTC date.
    """
    _author_pm_with_policy(tmp_workspace, "ordered-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "ordered-pm")
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    response = runtime.record_response(surfaced.audit_path, "A1")

    audit_dir = (
        tmp_workspace / "workspace" / ".loam" / "pms" / "ordered-pm" / "audit-log"
    )
    files = sorted(audit_dir.glob("*.yaml"))
    assert len(files) == 2
    assert files[0].name.endswith("-0001.yaml")
    assert files[1].name.endswith("-0002.yaml")
    # First is the surface_question, second is the record_response.
    p0 = yaml.safe_load(files[0].read_text())
    p1 = yaml.safe_load(files[1].read_text())
    assert p0["event_kind"] == "surface_question"
    assert p1["event_kind"] == "record_response"


def test_record_response_linkage_round_trip(tmp_workspace: Path) -> None:
    """The audit-log linkage is round-trippable: stored relative path
    resolves back to the surfacing's audit file."""
    _author_pm_with_policy(tmp_workspace, "linkage-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "linkage-pm")
    pm_dir = tmp_workspace / "workspace" / ".loam" / "pms" / "linkage-pm"
    runtime.enqueue_decision("Q1", provenance="lp-1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    response = runtime.record_response(surfaced.audit_path, "A1")

    payload = yaml.safe_load(response.audit_path.read_text())
    relative = payload["surfaced_audit_path"]
    resolved = (pm_dir / relative).resolve()
    assert resolved == surfaced.audit_path.resolve()


def test_two_surface_two_record_four_audit_entries(
    tmp_workspace: Path,
) -> None:
    _author_pm_with_policy(
        tmp_workspace,
        "four-events-pm",
        require_owner_response=False,
    )
    runtime = PMRuntime.from_workspace(tmp_workspace, "four-events-pm")
    runtime.enqueue_decision("Q1")
    runtime.enqueue_decision("Q2")
    s1 = runtime.surface_next_question()
    s2 = runtime.surface_next_question()
    assert s1 is not None and s2 is not None
    runtime.record_response(s1.audit_path, "A1")
    runtime.record_response(s2.audit_path, "A2")

    audit_dir = (
        tmp_workspace
        / "workspace"
        / ".loam"
        / "pms"
        / "four-events-pm"
        / "audit-log"
    )
    files = sorted(audit_dir.glob("*.yaml"))
    assert len(files) == 4
    kinds = [yaml.safe_load(f.read_text())["event_kind"] for f in files]
    assert kinds == [
        "surface_question",
        "surface_question",
        "record_response",
        "record_response",
    ]
