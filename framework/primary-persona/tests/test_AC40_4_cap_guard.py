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

"""AC40.4 — Cap-guard honoured when in-flight set is large.

If the in-flight objective set produces a contributor output that
would exceed the existing ``additionalContext`` cap, the contributor's
output is truncated or summarised before being handed to the registry,
such that the registry's cap-guard is satisfied without the
contributor causing a ``AdditionalContextCapExceededError``.

Maps to: primary-persona context-composer cap-guard surface → AC.PO.1.

Plan: docs/rebuild/plans/amendment-40-primary-persona-tracker-context-contributor.md
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.context_composer import (
    ADDITIONAL_CONTEXT_CAP,
    AdditionalContextCapExceededError,
    ComposedContextPayload,
)
from loam.primary_persona.session_start_gate import compose_session_fields
from loam.primary_persona.tracker_context import (
    DEFAULT_VALUE_PROP_ROOT_ID,
    register_tracker_context,
)

from _helpers_d40 import FakeTrackerClient, make_projection
from _helpers_d7 import seed_baseline_workspace


def _build_oversized_in_flight_set(
    n: int, *, goal_size: int
) -> FakeTrackerClient:
    root = make_projection(
        DEFAULT_VALUE_PROP_ROOT_ID, goal="root", status="active"
    )
    payload_char = "Q"  # arbitrary single non-whitespace char
    children = []
    trace_map = {}
    for i in range(n):
        oid = f"obj-cap-{i:03d}"
        big_goal = f"large-{i}-" + payload_char * goal_size
        child = make_projection(
            oid,
            goal=big_goal,
            status="active",
            parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
        )
        children.append(child)
        trace_map[oid] = [child, root]

    return FakeTrackerClient(
        query_result=tuple([root, *children]),
        trace_map=trace_map,
    )


def test_AC40_4_no_cap_exceeded_on_large_in_flight_set(tmp_path: Path) -> None:
    """50 in-flight objectives each carrying a 500-char goal would
    far exceed the composer's 10 000-char cap if rendered verbatim;
    the contributor's sub-cap must trim before the composer sees the
    payload.
    """
    workspace_root = tmp_path / "ws-ac40-4"
    seed_baseline_workspace(workspace_root)

    client = _build_oversized_in_flight_set(50, goal_size=500)

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=lambda: client,
        char_cap=2000,  # default; explicit for clarity
    )

    # The composer's structural cap (10 000) MUST NOT raise.
    try:
        payload = composer.on_session_start(workspace_root)
    except AdditionalContextCapExceededError as exc:  # pragma: no cover
        raise AssertionError(
            f"AC40.4 — composer cap-guard raised; contributor failed to trim: {exc}"
        )

    block = dict(payload.contributor_outputs).get("tracker-context", "")
    # Sub-cap honoured (with a small line-boundary tolerance window —
    # the renderer may slightly overshoot the soft cap before the line
    # boundary; the structural composer cap is the hard wall).
    assert len(block) <= 2200, (
        f"AC40.4 — tracker-context block length {len(block)} exceeds expected "
        f"sub-cap envelope (2000 + 200 line-boundary tolerance)"
    )
    # Composer's own structural cap honoured.
    assert len(payload.additional_context_text) <= ADDITIONAL_CONTEXT_CAP


def test_AC40_4_truncation_marker_surfaces_dropped_count(tmp_path: Path) -> None:
    """When the contributor trims, the persona observes the truncation
    outcome via a marker — so the user (and the persona) can tell the
    contribution was elided rather than missing."""
    workspace_root = tmp_path / "ws-ac40-4b"
    seed_baseline_workspace(workspace_root)

    # 100 small in-flight objectives — exceeds the objective_id_cap
    # default (20), forcing the truncation marker.
    client = _build_oversized_in_flight_set(100, goal_size=20)

    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=lambda: client,
    )

    payload = composer.on_session_start(workspace_root)
    block = dict(payload.contributor_outputs).get("tracker-context", "")
    assert "truncated" in block, (
        "AC40.4 — truncation marker must surface dropped-count for elided in-flight set"
    )
