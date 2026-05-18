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

"""AC.SCS-R1.2 + AC.SCS-R2.2 — the session-start digest is ordered by
open-loop priority (not query/recency order), and owner-pending
objectives surface as open loops awaiting the owner, never as done.

Plan: docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.md
§5 Family AC.SCS-R1.* (AC.SCS-R1.2) + Family AC.SCS-R2.* (AC.SCS-R2.2,
staged into sub-amendment 2/R1 per D-SCS.4 — its digest-surface outcome
is satisfiable only under R1's primary-persona seal anchor).

Outcomes (verbatim from §5):

  AC.SCS-R1.2: The session-start digest the persona reads is ordered
  by open-loop priority (an open owner-pending / higher-priority
  objective precedes a lower-priority one), NOT by episode recency,
  when in-flight objectives exist.

  AC.SCS-R2.2: The session-start digest surfaces owner-pending
  objectives as open loops awaiting the owner, never collapsed into
  "done".

Verification (verbatim from §5):

  R1.2: Cold session-start with a known tracker state where the
  highest-priority open loop is older than the newest episode; assert
  the digest surfaces the priority item ahead of the recent-but-lower
  one.

  R2.2: Seed an owner-pending objective; cold session-start; assert it
  appears in the open-loop digest tagged as owner-pending (not absent,
  not done-styled).

Method note (D-SCS-R1.build.2): the ordering function is a status
priority key (owner_pending=0 < active=1 < proposed=2) applied to the
open-loop set before render; the surfaced set is in-flight ∪
owner-pending; owner-pending lines carry an "AWAITING OWNER" tag. The
AC pins the *outcome* (priority item precedes lower; owner-pending
present + not done-styled), not the ranking mechanism (§5
method-in-AC test: YES).
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


def _digest_block(tmp_path: Path, client: FakeTrackerClient, ws_name: str) -> str:
    workspace_root = tmp_path / ws_name
    seed_baseline_workspace(workspace_root)
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_tracker_context(
        composer,
        workspace_root=workspace_root,
        tracker_factory=lambda: client,
    )
    payload = composer.on_session_start(workspace_root)
    outputs = dict(payload.contributor_outputs)
    return outputs.get("tracker-context", "")


def _root_plus(*children):
    root = make_projection(
        DEFAULT_VALUE_PROP_ROOT_ID, goal="value prop root", status="active"
    )
    trace = {DEFAULT_VALUE_PROP_ROOT_ID: [root]}
    for c in children:
        trace[c.objective_id] = [c, root]
    return FakeTrackerClient(
        query_result=(root, *children), trace_map=trace
    )


def test_AC_SCS_R1_2_owner_pending_precedes_active_even_when_added_first(
    tmp_path: Path,
) -> None:
    """The highest-priority open loop (owner_pending) is surfaced
    AHEAD of a lower-priority (active) one, regardless of query order
    — query order here puts active FIRST (the recency-ish ordering
    that buried the dev priority). Priority must override it."""
    active_obj = make_projection(
        "obj-active",
        goal="ACTIVELY-WORKING the lower-priority thing",
        status="active",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    owner_pending_obj = make_projection(
        "obj-op",
        goal="SHIPPED-AWAITING-OWNER the higher-priority decision",
        status="owner_pending",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    # Query order = active first (would be surfaced first under the
    # pre-R1 iteration-order render — the exact RESUME-STATE failure).
    client = _root_plus(active_obj, owner_pending_obj)
    block = _digest_block(tmp_path, client, "ws-r1-2-a")

    assert block, "digest must be non-empty when open loops exist"
    op_pos = block.index("SHIPPED-AWAITING-OWNER")
    active_pos = block.index("ACTIVELY-WORKING")
    assert op_pos < active_pos, (
        "AC.SCS-R1.2 — owner-pending (highest open loop) must precede "
        f"active in the digest; got owner_pending@{op_pos} "
        f"active@{active_pos}"
    )


def test_AC_SCS_R1_2_active_precedes_proposed(tmp_path: Path) -> None:
    """Within the in-flight set the digest is still priority-ordered:
    active (work underway) precedes proposed (merely queued), not
    query order."""
    proposed_obj = make_projection(
        "obj-prop",
        goal="QUEUED-ONLY the proposed thing",
        status="proposed",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    active_obj = make_projection(
        "obj-act",
        goal="UNDERWAY the active thing",
        status="active",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    # Query order = proposed first.
    client = _root_plus(proposed_obj, active_obj)
    block = _digest_block(tmp_path, client, "ws-r1-2-b")
    assert block.index("UNDERWAY") < block.index("QUEUED-ONLY"), (
        "AC.SCS-R1.2 — active must precede proposed"
    )


def test_AC_SCS_R2_2_owner_pending_surfaced_as_open_loop(
    tmp_path: Path,
) -> None:
    """An owner-pending objective APPEARS in the open-loop digest
    (it is not filtered out as the pre-R1 IN_FLIGHT_STATUSES would)."""
    op = make_projection(
        "obj-op",
        goal="OWNER-PENDING-VISIBLE shipped research awaiting Luke",
        status="owner_pending",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    client = _root_plus(op)
    block = _digest_block(tmp_path, client, "ws-r2-2-a")
    assert "OWNER-PENDING-VISIBLE" in block, (
        "AC.SCS-R2.2 — owner-pending objective must appear in the "
        "open-loop digest (not absent)"
    )


def test_AC_SCS_R2_2_owner_pending_tagged_awaiting_owner_not_done(
    tmp_path: Path,
) -> None:
    """The owner-pending line is tagged AWAITING OWNER and is NOT
    done-styled — never collapsed into "done"/achieved language."""
    op = make_projection(
        "obj-op",
        goal="shipped thing pending ruling",
        status="owner_pending",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    client = _root_plus(op)
    block = _digest_block(tmp_path, client, "ws-r2-2-b")
    assert "AWAITING OWNER" in block, (
        "AC.SCS-R2.2 — owner-pending must be tagged as awaiting the owner"
    )
    # Never done-styled: the owner-pending objective's line must not
    # carry a terminal/done token.
    op_line = next(
        ln for ln in block.splitlines() if "shipped thing pending ruling" in ln
    )
    lowered = op_line.lower()
    assert "achieved" not in lowered, "owner-pending must not read as achieved"
    assert "done" not in lowered, "owner-pending must not read as done"
    assert "owner_pending" in op_line, (
        "the owner-pending status token must be present on the line"
    )


def test_AC_SCS_R2_2_terminal_records_still_excluded(tmp_path: Path) -> None:
    """Surfacing owner-pending must NOT regress AC40.1's terminal
    exclusion: achieved/abandoned still never appear."""
    op = make_projection(
        "obj-op", goal="OPEN awaiting owner", status="owner_pending",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    done = make_projection(
        "obj-done", goal="CLOSED-MUST-NOT-APPEAR finished", status="achieved",
        parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    canned = make_projection(
        "obj-canned", goal="DROPPED-MUST-NOT-APPEAR abandoned",
        status="abandoned", parent_id=DEFAULT_VALUE_PROP_ROOT_ID,
    )
    client = _root_plus(op, done, canned)
    block = _digest_block(tmp_path, client, "ws-r2-2-c")
    assert "OPEN awaiting owner" in block
    assert "CLOSED-MUST-NOT-APPEAR" not in block
    assert "DROPPED-MUST-NOT-APPEAR" not in block
