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

"""AC.WVS-S.1 ★ (outcome-altitude:true) — a REAL workspace carrying
genuine live work-state (no pre-arranged snapshot, no hand-fed status
string, no mocked sources) produces the real plain-language surface at
the PRODUCTION entry-point: it names the current work + what's next +
whether anything looks stuck, in plain English, with zero internal
vocabulary, sourced end-to-end from the live tracker + cursor +
watchdog.

A STUB-class test (pre-built snapshot, hand-fed status text, mocked
sources) does NOT satisfy this. This test stands up:

  * a REAL ``objective_tracker.ObjectiveTracker`` on disk (via the
    shared ``seed_value_prop_tree`` + ``start_objective`` helpers that
    run the live tracker in-process — no FakeTrackerClient),
  * a REAL position-cursor written + resolved against a REAL
    ``FlowDefinition`` loaded from a flow file (no FakeProjection /
    fake step), and
  * a REAL ``StallWatchdog`` whose heartbeat drives the health signal,

then invokes the production surface entry-point ``render_work_visibility``
with NO pre-arranged in-memory state and asserts the live-sourced
plain-language surface.

Plan: docs/plans/work-visibility-surface.md §5 (the required
outcome-altitude AC per feedback_test_outcome_altitude_required).
"""

from __future__ import annotations

import time
from pathlib import Path

from loam.primary_persona.work_visibility import render_work_visibility
from loam.self_correction.recovery_surface import contains_internal_vocabulary
from loam.self_correction.watchdog import StallWatchdog

from _helpers_d40 import seed_value_prop_tree, start_objective


def test_AC_WVS_S_1_real_workspace_real_surface(tmp_path: Path) -> None:
    """Outcome-altitude: the production entry-point produces the real
    plain-language surface from genuine live state."""
    # --- REAL tracker state (no mock): seed a real DB, start the spec
    # descendant so it is genuinely 'active' (running now). --------------
    from loam.primary_persona.tracker_context import tracker_db_path_for

    db_path = tracker_db_path_for(tmp_path)
    seeded = seed_value_prop_tree(db_path)
    # The descendant is created 'proposed'; start it so it is 'active'.
    start_objective(db_path, seeded["descendant_id"])

    # --- REAL cursor state (no mock): write a real cursor to disk +
    # resolve it against a REAL FlowDefinition parsed from real flow
    # text via the public parser. ---------------------------------------
    from loam_cli.flows.cursor import Cursor, user_state_cursor_path, write_cursor
    from loam_cli.flows.format import parse_flow_definition

    flow_text = (
        "---\n"
        "flow: build\n"
        "title: Build flow\n"
        "entry: s1\n"
        "steps:\n"
        "  - id: s1\n"
        "    name: author the surface\n"
        "    transitions: [s2, s3]\n"
        "  - id: s2\n"
        "    name: test the surface\n"
        "    transitions: [s3]\n"
        "  - id: s3\n"
        "    name: seal the surface\n"
        "    transitions: []\n"
        "---\n\n"
        "First author the surface, then test it, then seal it. This is\n"
        "the human-followable narrative the flow definition carries\n"
        "alongside the machine graph.\n"
    )
    real_definition = parse_flow_definition(flow_text)
    cursor_path = user_state_cursor_path(tmp_path, real_definition.flow)
    write_cursor(
        cursor_path,
        Cursor(flow=real_definition.flow, step=real_definition.entry, branch_state=""),
    )

    def _real_flow_loader(flow_name: str):
        # The production loader shape: a flow_name -> FlowDefinition. Here
        # it returns the genuinely-parsed definition (no fake step).
        return real_definition if flow_name == real_definition.flow else None

    # --- REAL watchdog (no mock): a live StallWatchdog that just beat,
    # so the health signal is genuinely 'ok'. --------------------------
    watchdog = StallWatchdog(stall_threshold_seconds=300.0, clock=time.monotonic)
    watchdog.beat()

    # --- Invoke the PRODUCTION entry-point with NO pre-arranged
    # in-memory state: tracker_factory is None (the entry-point opens
    # the REAL tracker DB itself), the cursor + flow + watchdog are
    # live. -------------------------------------------------------------
    surface = render_work_visibility(
        tmp_path,
        tracker_factory=None,  # production opens the live DB on disk
        cursor_path=cursor_path,
        flow_loader=_real_flow_loader,
        stall_watchdog=watchdog,
    )

    lower = surface.lower()
    # Names the current work (the started descendant is running now).
    assert "right now" in lower
    assert "working on" in lower
    # Names what's next.
    assert "what's next" in lower
    # Names whether anything looks stuck (health, sourced from the live
    # watchdog → no problems detected).
    assert "health" in lower
    assert "no problems detected" in lower
    # Names where in the process (the live cursor resolved against the
    # real flow definition).
    assert "where i am" in lower
    # ZERO internal vocabulary, end-to-end from live sources.
    assert not contains_internal_vocabulary(surface), (
        f"AC.WVS-S.1 — live surface leaked internal vocab: {surface!r}"
    )


def test_AC_WVS_S_1_real_owner_pending_surfaces(tmp_path: Path) -> None:
    """Outcome-altitude variant: a REAL owner-pending objective on disk
    surfaces the 'waiting on you' answer through the production entry-
    point with no pre-arranged state."""
    from loam.objective_tracker import ObjectiveTracker
    from loam.primary_persona.tracker_context import tracker_db_path_for

    db_path = tracker_db_path_for(tmp_path)
    seeded = seed_value_prop_tree(db_path)
    start_objective(db_path, seeded["descendant_id"])

    # Genuinely mark the descendant owner-pending via the live tracker.
    import asyncio

    tracker = ObjectiveTracker(db_path)
    try:
        asyncio.get_event_loop_policy().new_event_loop().run_until_complete(
            tracker.mark_owner_pending(seeded["descendant_id"])
        )
    finally:
        tracker.close()

    watchdog = StallWatchdog(stall_threshold_seconds=300.0)
    watchdog.beat()

    surface = render_work_visibility(
        tmp_path, tracker_factory=None, stall_watchdog=watchdog
    )
    lower = surface.lower()
    assert "waiting on you" in lower
    assert not contains_internal_vocabulary(surface)
