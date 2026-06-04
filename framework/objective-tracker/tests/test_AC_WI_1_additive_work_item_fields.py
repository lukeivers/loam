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

"""AC.WI.1 — additive work-item field-groups + the D8 round-trip.

Plan: docs/plans/wms-increment-2-unified-work-item-model-and-projects-lens.md §6.

Outcome (paraphrased): a work item carries, in addition to the existing
identity/lifecycle/parent-child/criteria/provenance, a
`belongs-to-project` binding, a `tagged-streams` set, and a `priority`
value; a work item constructed WITHOUT any of these is still well-formed
(every pre-existing record deserialises unchanged). The D8 round-trip is
the hard property — adding the fields must not change how a pre-widening
record folds. Also exercises the additive `blocked` lifecycle member.
"""

from __future__ import annotations

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.objective_tracker.spec import (
    ObjectiveSpec,
    ObjectiveStatus,
    ProseCriterion,
    TimeBound,
)
from tests.conftest import make_user_root_spec


def _spec_with_work_item_fields(**over) -> ObjectiveSpec:
    base = dict(
        goal="ship the projects lens",
        parent_id=None,
        acceptance_criteria=(ProseCriterion(criterion_id="c1", prose="done"),),
        time_bound=TimeBound(evergreen=True),
        authored_by="user",
    )
    base.update(over)
    return ObjectiveSpec(**base)


async def test_AC_WI_1_fields_present_and_surfaced(tracker: ObjectiveTracker) -> None:
    spec = _spec_with_work_item_fields(
        belongs_to_project="loam",
        tagged_streams=("loam", "money"),
        priority="active",
    )
    proj = await tracker.create(spec)
    assert proj.belongs_to_project == "loam"
    assert proj.tagged_streams == ("loam", "money")
    assert proj.priority == "active"

    # Re-read from a fresh get() (cache + replay path).
    again = tracker.get(proj.objective_id)
    assert again is not None
    assert again.belongs_to_project == "loam"
    assert again.tagged_streams == ("loam", "money")
    assert again.priority == "active"


async def test_AC_WI_1_item_without_fields_is_well_formed(
    tracker: ObjectiveTracker,
) -> None:
    """A record constructed with NONE of the new fields is well-formed
    and deserialises with the default-preserving sentinels."""
    proj = await tracker.create(make_user_root_spec(goal="legacy-shaped"))
    assert proj.belongs_to_project is None
    assert proj.tagged_streams == ()
    assert proj.priority is None


async def test_AC_WI_1_pre_widening_record_replays_unchanged(
    tracker: ObjectiveTracker,
) -> None:
    """D8: a record authored with no work-item fields folds identically
    whether or not the new fields exist — the new fields take their
    defaults and nothing about the existing fold drifts."""
    proj = await tracker.create(make_user_root_spec(goal="alpha"))
    await tracker.start(proj.objective_id)
    await tracker.evaluate_criterion(
        proj.objective_id, criterion_id="root-c1", result="met"
    )
    achieved = await tracker.mark_achieved(proj.objective_id, evidence="done")

    # Cold replay from the raw event stream.
    from loam.objective_tracker.projection import project

    events = tracker.store.events_for(proj.objective_id)
    replayed = project(proj.objective_id, events)
    assert replayed.status == ObjectiveStatus.achieved
    assert replayed.belongs_to_project is None
    assert replayed.tagged_streams == ()
    assert replayed.priority is None
    assert achieved.status == ObjectiveStatus.achieved


async def test_AC_WI_1_blocked_is_additive_lifecycle_member(
    tracker: ObjectiveTracker,
) -> None:
    """`blocked` is a non-terminal lifecycle member reached from active
    and left back to active (additive, the owner_pending precedent)."""
    proj = await tracker.create(make_user_root_spec(goal="blockable"))
    await tracker.start(proj.objective_id)
    blocked = await tracker.mark_blocked(proj.objective_id, evidence="waits on review")
    assert blocked.status == ObjectiveStatus.blocked

    unblocked = await tracker.unblock(proj.objective_id)
    assert unblocked.status == ObjectiveStatus.active
