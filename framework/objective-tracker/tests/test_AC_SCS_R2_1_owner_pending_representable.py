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

"""AC.SCS-R2.1 — owner-pending representable, distinct from in-progress
and from closed.

Plan: docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.md
§5 Family AC.SCS-R2.*.

Outcome (verbatim from §5 AC.SCS-R2.1):

  The tracker can represent an objective as "work shipped, owner
  decision pending" — distinct from in-progress (`active`) and from
  closed (`achieved`/`abandoned`).

Verification (verbatim from §5):

  Construct an objective, transition it to the owner-pending
  representation via the production API, query it back; assert it is
  neither in the in-progress set nor the terminal set.

Method note (D-SCS-R2.build.1, builder's call narrated at build): the
owner-pending representation is a new additive `ObjectiveStatus` enum
value `owner_pending`, reached via the production runtime API
`ObjectiveTracker.mark_owner_pending`. The AC pins the *distinction*
(neither in-progress nor terminal), not the representation mechanism —
a flag or an event-kind would also satisfy it (§5 method-in-AC test:
YES).
"""

from __future__ import annotations

from loam.objective_tracker.policies import TERMINAL_STATES, is_terminal
from loam.objective_tracker.spec import ObjectiveStatus
from tests.conftest import make_user_root_spec


# The "in-progress" set the AC names: an objective the persona reads as
# actively being worked. owner_pending must be excluded from it.
IN_PROGRESS_STATES = {ObjectiveStatus.active}


async def test_AC_SCS_R2_1_owner_pending_reachable_via_production_api(
    tracker,
) -> None:
    """An objective transitioned via the production runtime API ends
    in the owner-pending representation."""
    root = await tracker.create(make_user_root_spec(goal="shipped-research"))
    await tracker.start(root.objective_id)
    proj = await tracker.mark_owner_pending(
        root.objective_id, evidence="research artefact shipped; awaiting owner"
    )
    assert proj.status == ObjectiveStatus.owner_pending


async def test_AC_SCS_R2_1_owner_pending_not_in_progress(tracker) -> None:
    """owner_pending is distinct from in-progress (`active`)."""
    root = await tracker.create(make_user_root_spec(goal="shipped-research"))
    await tracker.start(root.objective_id)
    proj = await tracker.mark_owner_pending(root.objective_id)
    assert proj.status not in IN_PROGRESS_STATES
    assert proj.status != ObjectiveStatus.active


async def test_AC_SCS_R2_1_owner_pending_not_terminal(tracker) -> None:
    """owner_pending is distinct from closed (`achieved`/`abandoned`):
    it is an open loop awaiting the owner, not a terminal record."""
    root = await tracker.create(make_user_root_spec(goal="shipped-research"))
    await tracker.start(root.objective_id)
    proj = await tracker.mark_owner_pending(root.objective_id)
    assert proj.status not in TERMINAL_STATES
    assert not is_terminal(proj.status)
    assert proj.status != ObjectiveStatus.achieved
    assert proj.status != ObjectiveStatus.abandoned


async def test_AC_SCS_R2_1_owner_pending_queryable_back_via_get(
    tracker,
) -> None:
    """Query it back through the production read-model: the owner-pending
    representation survives the projection round-trip and is still
    neither in-progress nor terminal."""
    root = await tracker.create(make_user_root_spec(goal="shipped-research"))
    await tracker.start(root.objective_id)
    await tracker.mark_owner_pending(root.objective_id)

    queried = tracker.get(root.objective_id)
    assert queried is not None
    assert queried.status == ObjectiveStatus.owner_pending
    assert queried.status not in IN_PROGRESS_STATES
    assert queried.status not in TERMINAL_STATES


async def test_AC_SCS_R2_1_owner_pending_resolves_when_owner_rules(
    tracker,
) -> None:
    """The owner-pending state is a *loop*, not a sink: once the owner
    rules, it transitions onward (resume / done / drop). Pins that the
    representation does not strand the objective."""
    # owner rules: resume / re-scope
    a = await tracker.create(make_user_root_spec(goal="a"))
    await tracker.start(a.objective_id)
    await tracker.mark_owner_pending(a.objective_id)
    resumed = await tracker.start(a.objective_id)
    assert resumed.status == ObjectiveStatus.active

    # owner rules: done
    b = await tracker.create(make_user_root_spec(goal="b"))
    await tracker.start(b.objective_id)
    await tracker.mark_owner_pending(b.objective_id)
    done = await tracker.mark_achieved(b.objective_id, evidence="owner accepted")
    assert done.status == ObjectiveStatus.achieved

    # owner rules: drop
    c = await tracker.create(make_user_root_spec(goal="c"))
    await tracker.start(c.objective_id)
    await tracker.mark_owner_pending(c.objective_id)
    dropped = await tracker.mark_abandoned(
        c.objective_id, rationale="owner ruled out of scope"
    )
    assert dropped.status == ObjectiveStatus.abandoned
