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

"""AC.QSURF.7 — PM-mediated dispatches log per audit-trail floor (D6).

Per cycle-4 plan §4 + AC.QSURF.7:

  Every PM-mediated surfacing AND every recorded response produces an
  audit-log entry. No surfacing/response slips through without an audit
  row. Aligned with v0.1.6 SOC-2 audit-trail floor (Eric synthesis
  Decision P).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam.per_project_pm.runtime import PMRuntime


def _author_pm(
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
            "onboarding_mode": False,
            "max_questions_per_turn": 5,
            "cool_down_seconds": 0,
            "require_owner_response": require_owner_response,
        },
    }
    (pm_dir / "contract.yaml").write_text(yaml.safe_dump(contract))


def test_every_surfacing_writes_one_audit_entry(tmp_workspace: Path) -> None:
    """5 surfacings → 5 surface_question audit entries; no slips."""
    _author_pm(tmp_workspace, "audit-floor-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "audit-floor-pm")
    for i in range(5):
        runtime.enqueue_decision(f"Q{i + 1}")

    runtime.surface_next_questions_batch(n=5)

    audit_dir = (
        tmp_workspace
        / "workspace"
        / ".loam"
        / "pms"
        / "audit-floor-pm"
        / "audit-log"
    )
    surface_entries = [
        f
        for f in audit_dir.glob("*.yaml")
        if yaml.safe_load(f.read_text()).get("event_kind") == "surface_question"
    ]
    assert len(surface_entries) == 5


def test_every_response_writes_one_audit_entry(tmp_workspace: Path) -> None:
    """5 surfacings + 5 record_responses → 10 audit entries (5 surface,
    5 response)."""
    _author_pm(tmp_workspace, "response-floor-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "response-floor-pm")
    for i in range(5):
        runtime.enqueue_decision(f"Q{i + 1}")

    batch = runtime.surface_next_questions_batch(n=5)
    for sq in batch:
        runtime.record_response(sq.audit_path, f"A-{sq.text}")

    audit_dir = (
        tmp_workspace
        / "workspace"
        / ".loam"
        / "pms"
        / "response-floor-pm"
        / "audit-log"
    )
    files = sorted(audit_dir.glob("*.yaml"))
    kinds = [yaml.safe_load(f.read_text())["event_kind"] for f in files]
    assert kinds.count("surface_question") == 5
    assert kinds.count("record_response") == 5
    assert len(kinds) == 10


def test_audit_entries_carry_pm_handle(tmp_workspace: Path) -> None:
    """Every audit entry carries pm_handle (SOC-2: traceability of who
    issued the dispatch)."""
    _author_pm(tmp_workspace, "handle-trace-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "handle-trace-pm")
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    runtime.record_response(surfaced.audit_path, "A1")

    audit_dir = (
        tmp_workspace
        / "workspace"
        / ".loam"
        / "pms"
        / "handle-trace-pm"
        / "audit-log"
    )
    for f in audit_dir.glob("*.yaml"):
        payload = yaml.safe_load(f.read_text())
        assert payload["pm_handle"] == "handle-trace-pm"
        assert payload["schema_version"] == 1


def test_audit_entries_have_iso_8601_timestamps(tmp_workspace: Path) -> None:
    """Every audit entry has an ISO 8601 UTC timestamp (SOC-2: ordered,
    parseable audit trail)."""
    from datetime import datetime

    _author_pm(tmp_workspace, "iso-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "iso-pm")
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    runtime.record_response(surfaced.audit_path, "A1")

    audit_dir = (
        tmp_workspace / "workspace" / ".loam" / "pms" / "iso-pm" / "audit-log"
    )
    for f in audit_dir.glob("*.yaml"):
        payload = yaml.safe_load(f.read_text())
        # Timestamp parses as ISO 8601 with timezone.
        ts = datetime.fromisoformat(payload["timestamp"])
        assert ts.tzinfo is not None  # has timezone


def test_no_silent_path_around_audit(tmp_workspace: Path) -> None:
    """A single Q1 surface + record produces exactly 2 audit-log
    entries; never 1, never 0. The audit trail floor is enforced
    structurally — there is no API path that surfaces or records
    without an audit-log write.
    """
    _author_pm(tmp_workspace, "structural-pm")
    runtime = PMRuntime.from_workspace(tmp_workspace, "structural-pm")
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    runtime.record_response(surfaced.audit_path, "A1")

    audit_dir = (
        tmp_workspace
        / "workspace"
        / ".loam"
        / "pms"
        / "structural-pm"
        / "audit-log"
    )
    files = list(audit_dir.glob("*.yaml"))
    assert len(files) == 2
