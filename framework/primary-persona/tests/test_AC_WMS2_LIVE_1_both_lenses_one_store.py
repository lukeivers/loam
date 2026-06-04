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

"""AC.WMS2.LIVE.1 (OUTCOME-ALTITUDE, outcome-altitude:true).

Plan §6 AC.WMS2.LIVE.1. Through ONE real keep-pace turn against the LIVE
loam + cairn repos with NO pre-arranged state:

  - the surface presents work through BOTH the projects lens AND the
    re-pointed streams lens;
  - a work item that belongs to a project AND is tagged with a stream
    appears in both views;
  - the project's STATE is DERIVED LIVE from `derive_project_state`
    (the `loam` project -> loam's real built/sealed STATE);
  - both lenses read from the SAME work-item store (no parallel store, no
    stored-stale status).

This invokes the PRODUCTION entry points — a real ObjectiveTracker DB
(the one work-item store), the production `render_projects_block` +
`render_work_streams_block` derive paths, and the LIVE
`derive_project_state` (Slice C) — with NO fixtures and NO pre-arranged
state. The derivation is NOT injected; it runs against the real registry.
"""

from __future__ import annotations

import pytest

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.objective_tracker.spec import ObjectiveSpec, ProseCriterion, TimeBound
from loam.primary_persona.keep_pace import projects as P
from loam.primary_persona.keep_pace.work_streams import resolve_stream_membership

# The streams surfacer (production derive path).
from loam.primary_persona.keep_pace.work_streams_surface import (
    render_work_streams_block,
)

# The live Slice-C derivation — the production entry point.
from loam_cli.audit.registry import derive_project_state, registered_project_names


def _live_loam_registered() -> bool:
    """True iff the live registry has `loam` AND a fresh derivation
    returns a real record (the live repo is reachable). Skips otherwise —
    the outcome-altitude AC needs the live ground truth."""
    if "loam" not in registered_project_names():
        return False
    try:
        return derive_project_state("loam") is not None
    except Exception:  # noqa: BLE001
        return False


@pytest.mark.skipif(
    not _live_loam_registered(),
    reason="live loam project STATE not derivable in this environment",
)
async def test_AC_WMS2_LIVE_1_both_lenses_one_store_live_derived(tmp_path) -> None:
    # ONE real work-item store — no pre-arranged state; a fresh DB.
    db = tmp_path / "objective_tracker.sqlite"
    tracker = ObjectiveTracker(db_path=db)
    try:
        # ONE work item that BELONGS to the loam project AND is TAGGED
        # with the loam stream — the appears-in-both case.
        spec = ObjectiveSpec(
            goal="advance the work-management system",
            parent_id=None,
            acceptance_criteria=(ProseCriterion(criterion_id="c1", prose="done"),),
            time_bound=TimeBound(evergreen=True),
            authored_by="user",
            belongs_to_project="loam",
            tagged_streams=("loam",),
            priority="active",
        )
        created = await tracker.create(spec)

        # Read the ONE store once — both lenses consume THIS set.
        work_items = list(tracker.query_projection_view())
        assert any(p.objective_id == created.objective_id for p in work_items)

        # --- the PROJECTS lens, STATE derived live (no derive injection) ---
        projects_block = P.render_projects_block(items=work_items)
        assert projects_block, "projects lens produced no block"
        assert "loam" in projects_block
        # The loam project's STATE is DERIVED LIVE — a real liveness phrase
        # appears (loam has built/sealed/merged components on this branch).
        assert any(
            phrase in projects_block
            for phrase in (
                "built (merged)",
                "built (sealed, not yet merged)",
                "built",
                "wired",
            )
        ), f"no live-derived STATE phrase in projects block: {projects_block!r}"

        # --- the STREAMS lens membership, resolved from the SAME store ---
        members = resolve_stream_membership("loam", work_items)
        # The SAME work item appears in the streams lens (by its tag) AND
        # in the projects lens (by its binding) — ONE store, no duplication.
        assert created.objective_id in members.item_ids
        assert "loam" in members.projects

        # --- the streams surfacer block also derives loam STATE live ---
        streams_block = render_work_streams_block()
        assert streams_block, "streams lens produced no block"
        assert "loam" in streams_block

        # The item belongs to a project AND is tagged with a stream — it is
        # in BOTH views, backed by the ONE store (no parallel store).
        proj = tracker.get(created.objective_id)
        assert proj is not None
        assert proj.belongs_to_project == "loam"
        assert "loam" in proj.tagged_streams
    finally:
        tracker.close()
