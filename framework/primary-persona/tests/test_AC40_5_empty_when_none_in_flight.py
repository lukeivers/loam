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

"""AC40.5 — Contributor produces empty contribution when no in-flight
objectives exist.

When the tracker carries the seeded root + spec descendants but no
objective has been started (every objective has ``status == proposed``
or terminal), the contributor produces an empty contribution — the
registry does not include an empty tracker-context block in the
composed ``additionalContext``.

NOTE on vocabulary: the plan's AC40.5 names "every objective has
``status == declared`` or similar pre-start state." The tracker's
actual lifecycle starts at ``proposed`` (the spec calls this the
"declared" pre-start state). "In flight" maps to ``{proposed, active}``
in the tracker's vocabulary; ``proposed`` IS treated as in-flight
(amendment #39's seeded root is created at status ``proposed`` and is
explicitly counted as in-flight per #39 + #40 contract). This test
exercises the empty-contribution path by ensuring the only records
available are TERMINAL (achieved/abandoned), so the in-flight set is
truly empty.

Maps to: primary-persona contributor registry contribution semantics
→ AC.PO.1.

Plan: docs/rebuild/plans/amendment-40-primary-persona-tracker-context-contributor.md
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.context_composer import ComposedContextPayload
from loam.primary_persona.session_start_gate import compose_session_fields
from loam.primary_persona.tracker_context import (
    DEFAULT_VALUE_PROP_ROOT_ID,
    register_tracker_context,
)

from _helpers_d40 import FakeTrackerClient, make_projection
from _helpers_d7 import seed_baseline_workspace


def test_AC40_5_empty_contribution_when_only_terminal_records(
    tmp_path: Path,
) -> None:
    """Tracker carries only terminal (achieved + abandoned) records
    rooted at the value-prop root. No in-flight set exists. The
    contributor returns the empty string."""
    workspace_root = tmp_path / "ws-ac40-5"
    seed_baseline_workspace(workspace_root)

    root = make_projection(
        DEFAULT_VALUE_PROP_ROOT_ID, goal="vp root", status="active"
    )
    achieved = make_projection(
        "obj-done",
        goal="finished work",
        status="achieved",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    abandoned = make_projection(
        "obj-canned",
        goal="abandoned work",
        status="abandoned",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )

    client = FakeTrackerClient(
        query_result=(root, achieved, abandoned),
        trace_map={
            "obj-done": [achieved, root],
            "obj-canned": [abandoned, root],
        },
    )

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=lambda: client,
    )

    payload = composer.on_session_start(workspace_root)
    outputs = dict(payload.contributor_outputs)
    block = outputs.get("tracker-context", "")
    assert block == "", (
        "AC40.5 — empty contribution when no in-flight objectives exist"
    )


def test_AC40_5_empty_contribution_when_no_records_at_all(
    tmp_path: Path,
) -> None:
    """Tracker is empty (no records seeded). The contributor returns
    the empty string. Exercises the boundary where there's no root
    and no descendants — equivalent to a fresh DB before first-run
    seeded anything (defence-in-depth; #39 ordering ensures the seed
    runs first in production)."""
    workspace_root = tmp_path / "ws-ac40-5b"
    seed_baseline_workspace(workspace_root)

    client = FakeTrackerClient(query_result=())

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=lambda: client,
    )

    payload = composer.on_session_start(workspace_root)
    block = dict(payload.contributor_outputs).get("tracker-context", "")
    assert block == ""
