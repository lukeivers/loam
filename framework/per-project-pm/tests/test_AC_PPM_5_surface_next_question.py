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

"""AC.PPM.5 — surface_next_question() API.

Per parent plan §5 + cycle-2 plan §4 Surface #5:
  - Returns SurfacedQuestion with text + provenance + queue_position +
    surfaced_at + audit_path.
  - Writes audit-log/<YYYY-MM-DD>-<NNNN>.yaml with timestamp + question
    + queue-state-pre + queue-state-post.
  - Returns None when queue empty.
  - <NNNN> is 4-digit zero-padded monotonic counter scoped to (pm, UTC date).
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from loam.per_project_pm.runtime import PMRuntime
from loam.per_project_pm.state import SurfacedQuestion


_AUDIT_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(\d{4})\.yaml$")


def test_surface_returns_None_on_empty_queue(authored_pm: tuple[Path, str]) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    assert runtime.surface_next_question() is None


def test_surface_returns_SurfacedQuestion_and_advances_queue(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    pos1 = runtime.enqueue_decision("Q1", provenance="t1")
    pos2 = runtime.enqueue_decision("Q2", provenance="t2")
    assert pos1 == 1 and pos2 == 2

    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    assert isinstance(surfaced, SurfacedQuestion)
    assert surfaced.text == "Q1"
    assert surfaced.provenance == "t1"
    assert surfaced.queue_position == 1
    # ISO 8601 timestamp roughly == now.
    surfaced_dt = datetime.fromisoformat(surfaced.surfaced_at)
    delta = abs((datetime.now(tz=timezone.utc) - surfaced_dt).total_seconds())
    assert delta < 5

    # Queue advances by exactly 1.
    state = runtime.state_of_world()
    assert state.queue_depth == 1
    assert state.pending_questions == ("Q2",)


def test_surface_writes_audit_log_entry(authored_pm: tuple[Path, str]) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    runtime.enqueue_decision("Q1", provenance="test")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    assert surfaced.audit_path.exists()

    # Filename pattern: YYYY-MM-DD-NNNN.yaml.
    match = _AUDIT_RE.match(surfaced.audit_path.name)
    assert match is not None
    assert match.group(2) == "0001"  # first audit entry of the day

    # Content schema.
    payload = yaml.safe_load(surfaced.audit_path.read_text())
    assert payload["schema_version"] == 1
    assert payload["event_kind"] == "surface_question"
    assert payload["pm_handle"] == pm_name
    assert payload["question_text"] == "Q1"
    assert payload["question_provenance"] == "test"
    assert payload["queue_position_pre"] == 1
    assert payload["queue_depth_pre"] == 1
    assert payload["queue_depth_post"] == 0


def test_audit_log_seq_increments_within_same_day(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    for i in range(3):
        runtime.enqueue_decision(f"Q{i}", provenance=None)
    s1 = runtime.surface_next_question()
    s2 = runtime.surface_next_question()
    s3 = runtime.surface_next_question()
    assert s1 is not None and s2 is not None and s3 is not None
    seq1 = int(_AUDIT_RE.match(s1.audit_path.name).group(2))
    seq2 = int(_AUDIT_RE.match(s2.audit_path.name).group(2))
    seq3 = int(_AUDIT_RE.match(s3.audit_path.name).group(2))
    # Same day, monotonic increment.
    assert seq2 == seq1 + 1
    assert seq3 == seq2 + 1
    # Zero-padded to 4 digits.
    assert s1.audit_path.name.endswith("-0001.yaml")
    assert s2.audit_path.name.endswith("-0002.yaml")
    assert s3.audit_path.name.endswith("-0003.yaml")


def test_surface_updates_state_yaml_last_surfaced_at(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    runtime.enqueue_decision("Q1")
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    state = runtime.state_of_world()
    assert state.last_surfaced_at == surfaced.surfaced_at


def test_audit_log_records_provenance_None_when_omitted(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    runtime.enqueue_decision("Q1")  # no provenance
    surfaced = runtime.surface_next_question()
    assert surfaced is not None
    assert surfaced.provenance is None
    payload = yaml.safe_load(surfaced.audit_path.read_text())
    assert payload["question_provenance"] is None


def test_FIFO_ordering_across_multiple_surfacings(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    questions = ["Alpha", "Beta", "Gamma", "Delta"]
    for q in questions:
        runtime.enqueue_decision(q)
    surfaced_in_order = []
    while True:
        s = runtime.surface_next_question()
        if s is None:
            break
        surfaced_in_order.append(s.text)
    assert surfaced_in_order == questions
