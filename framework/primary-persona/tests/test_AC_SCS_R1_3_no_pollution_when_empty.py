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

"""AC.SCS-R1.3 — when no in-flight objectives exist, the digest emits
no tracker block (no empty/polluting section); AC40.5 semantics
preserved.

Plan: docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.md
§5 Family AC.SCS-R1.* (AC.SCS-R1.3); §15 (AC40.5 empty-contribution
semantics preserved).

Outcome (verbatim from §5 AC.SCS-R1.3):

  When no in-flight objectives exist, the digest emits no tracker
  block (no empty/polluting section).

Verification (verbatim from §5):

  Cold session-start with empty tracker; assert no tracker block
  (preserves AC40.5 semantics).

Method note (D-SCS-R1.build.2): R1 widened the surfaced set to OPEN
LOOPS (in-flight ∪ owner-pending). "No open loops" must still produce
the empty contribution — the empty-guard is preserved, not removed.
This test pins that a tracker with zero records, only-terminal
records, and only-cross-root records all yield an empty digest after
the R1 widening (AC.SCS-R1.3 / AC40.5 non-regression).
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


def _block(tmp_path: Path, client: FakeTrackerClient, ws: str) -> str:
    workspace_root = tmp_path / ws
    seed_baseline_workspace(workspace_root)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer, workspace_root=workspace_root, tracker_factory=lambda: client
    )
    payload = composer.on_session_start(workspace_root)
    return dict(payload.contributor_outputs).get("tracker-context", "")


def test_AC_SCS_R1_3_empty_tracker_emits_no_block(tmp_path: Path) -> None:
    """Zero records → empty contribution (no polluting section)."""
    client = FakeTrackerClient(query_result=(), trace_map={})
    assert _block(tmp_path, client, "ws-r1-3-a") == "", (
        "AC.SCS-R1.3 — an empty tracker must emit no tracker block"
    )


def test_AC_SCS_R1_3_only_terminal_records_emits_no_block(
    tmp_path: Path,
) -> None:
    """Only terminal records (achieved/abandoned) → no open loops →
    empty contribution (AC40.5 preserved post-R1 widening)."""
    root = make_projection(
        DEFAULT_VALUE_PROP_ROOT_ID, goal="vp root", status="active"
    )
    done = make_projection(
        "obj-done", goal="finished", status="achieved",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    canned = make_projection(
        "obj-canned", goal="abandoned", status="abandoned",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    client = FakeTrackerClient(
        query_result=(root, done, canned),
        trace_map={
            DEFAULT_VALUE_PROP_ROOT_ID: [root],
            "obj-done": [done, root],
            "obj-canned": [canned, root],
        },
    )
    assert _block(tmp_path, client, "ws-r1-3-b") == "", (
        "AC.SCS-R1.3 — only-terminal records must emit no block"
    )


def test_AC_SCS_R1_3_only_root_no_descendants_emits_no_block(
    tmp_path: Path,
) -> None:
    """A seeded value-prop root with NO open-loop descendants → empty
    contribution (the root itself is not an open loop to surface)."""
    root = make_projection(
        DEFAULT_VALUE_PROP_ROOT_ID, goal="vp root only", status="active"
    )
    client = FakeTrackerClient(
        query_result=(root,),
        trace_map={DEFAULT_VALUE_PROP_ROOT_ID: [root]},
    )
    assert _block(tmp_path, client, "ws-r1-3-c") == "", (
        "AC.SCS-R1.3 — root-only (no open-loop descendants) emits no block"
    )
