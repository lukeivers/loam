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

"""AC.WMS6.LIVE.1 (OUTCOME-ALTITUDE, outcome-altitude:true).

Plan §6 AC.WMS6.LIVE.1. Against a REAL #34 matrix file (an isolated
fixture home) carrying a REAL technical-exposure / preferred-lens profile,
and a REAL work-item store with NO pre-arranged lens / registration state:

  (a) the live resolver + the live per-turn registration path surface the
      RIGHT lens for that profile (a plain/plate profile surfaces the
      on-my-plate block and NOT the always-on streams/projects/relational
      trio; a projects profile surfaces the projects block);
  (b) invoking the live switch path with a plain-language preference
      change WRITES the cell such that a fresh live resolve returns the
      switched-to lens-set;
  (c) the un-chosen lenses' live render_*_block entry points still render
      correctly on demand.

Exercised through the real production entry points (the resolver, the
registration assembly, the switch writer), no mocks at the #34-file or
store boundary, no pre-seeded registration.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.objective_tracker.spec import ObjectiveSpec, ProseCriterion, TimeBound
from loam.primary_persona.context_composer import (
    ComposedContextPayload,
    TriggerKind,
)
from loam.primary_persona.session_start_gate import compose_session_fields
from loam.primary_persona.keep_pace import lens_choice as lc
from loam.primary_persona.keep_pace import plate as PL
from loam.primary_persona.keep_pace import projects as PR
from loam.workspace_bootstrap.seed_writer import render_interaction_model


def _real_home(tmp_path: Path, area: str, cells: str) -> Path:
    """Write a REAL matrix file (the seed-writer's output) + a real profile
    section in the live line-shape. No stub — the production parser reads
    this exact file."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    matrix = render_interaction_model()
    matrix += f"\n## {area}\n{cells}"
    (tmp_path / "INTERACTION-MODEL.md").write_text(matrix, encoding="utf-8")
    return tmp_path


def _turn_names(claude_home: Path, tracker_factory) -> set[str]:
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    lc.register_chosen_lenses(
        composer, claude_home=claude_home, tracker_factory=tracker_factory
    )
    return {c.name for c in composer.contributors(TriggerKind.turn)}


async def _seed_real_store(db: Path) -> ObjectiveTracker:
    """A REAL ObjectiveTracker over a fresh tmp DB with ONE active item —
    no pre-arranged surfacing/registration state."""
    tracker = ObjectiveTracker(db_path=db)
    spec = ObjectiveSpec(
        goal="write the launch announcement",
        parent_id=None,
        acceptance_criteria=(ProseCriterion(criterion_id="c1", prose="done"),),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
        belongs_to_project="cairn",
        priority="active",
    )
    created = await tracker.create(spec)
    # Promote proposed -> active so the on-my-plate lens (which filters to
    # active/owner_pending work) has a live item to surface (AC.PLATE.1).
    await tracker.start(created.objective_id)
    return tracker


async def test_AC_WMS6_LIVE_1_real_profile_surfaces_right_lens(
    tmp_path: Path,
) -> None:
    # --- (a) a REAL plain/plate profile surfaces on-my-plate, NOT the trio ---
    _real_home(
        tmp_path / "plate",
        "work-tracking",
        "preferred-lens: { value: on-my-plate, confidence: high, "
        "evidence: [], locked: true }\n",
    )

    db = tmp_path / "store.sqlite"
    tracker = await _seed_real_store(db)
    try:
        factory = lambda: tracker  # noqa: E731 — the live store, read-only

        names = _turn_names(tmp_path / "plate", factory)
        assert lc.LENS_PLATE in names
        assert lc.LENS_STREAMS not in names
        assert lc.LENS_PROJECTS not in names
        assert lc.LENS_RELATIONAL not in names

        # --- (b) a live plain-language switch WRITES the cell; fresh resolve
        #         returns the switched-to set ---
        switch = lc.apply_lens_switch(
            preference_text="I think in projects",
            claude_home=tmp_path / "plate",
        )
        assert switch.ok
        assert lc.resolve_lens_set(claude_home=tmp_path / "plate") == (
            lc.LENS_PROJECTS,
        )
        # And the per-turn registration now surfaces projects, not plate.
        names_after = _turn_names(tmp_path / "plate", factory)
        assert lc.LENS_PROJECTS in names_after
        assert lc.LENS_PLATE not in names_after

        # --- (c) the un-chosen lens still renders on demand (live store) ---
        # After the switch to projects, the on-my-plate lens is no longer a
        # per-turn block but its render entry point still works live.
        items = list(tracker.query_projection_view())
        plate_block = PL.render_plate_block(items=items)
        assert plate_block, "on-demand plate render produced nothing live"
        # And projects (now chosen) renders live too.
        projects_block = PR.render_projects_block(items=items)
        assert projects_block
        assert "cairn" in projects_block
    finally:
        tracker.close()


async def test_AC_WMS6_LIVE_1_projects_profile_surfaces_projects(
    tmp_path: Path,
) -> None:
    home = _real_home(
        tmp_path,
        "work-tracking",
        "preferred-lens: { value: projects, confidence: high, "
        "evidence: [], locked: true }\n",
    )
    db = tmp_path / "store.sqlite"
    tracker = await _seed_real_store(db)
    try:
        factory = lambda: tracker  # noqa: E731
        names = _turn_names(home, factory)
        assert names == {lc.LENS_PROJECTS}
    finally:
        tracker.close()
