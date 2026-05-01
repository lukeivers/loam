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

"""Parent-close policy behaviour.

Luke's decision (brief §"Luke's decisions"): default `notify`, not
TERMINATE. Abandonment or achievement of a parent objective is
semantically distinct from cancellation of a parent scope — children
of a closed parent receive a notification event; no automatic state
change. Per-objective override to `terminate` or `abandon` is
honoured by the runtime.

This test file lives alongside D2 (hierarchy). It exists because the
parent-close policy is not called out as a separate D-letter, but is a
first-class Luke-decision and needs coverage.
"""

from __future__ import annotations

import pytest

from loam.objective_tracker.spec import ObjectiveStatus, ParentClosePolicy
from tests.conftest import make_child_spec, make_user_root_spec


async def test_default_parent_close_is_notify(tracker):
    root = await tracker.create(make_user_root_spec())
    child = await tracker.create(make_child_spec(parent_id=root.objective_id))
    # Parent achieves.
    await tracker.start(root.objective_id)
    await tracker.mark_achieved(root.objective_id, evidence="done")
    # Child status unchanged.
    child_proj = tracker.get(child.objective_id)
    assert child_proj.status == ObjectiveStatus.proposed
    # Child received a notification event.
    kinds = [e.kind for e in tracker.store.events_for(child.objective_id)]
    assert "parent_closed" in kinds


async def test_parent_notify_carries_parent_id_and_event_kind(tracker):
    root = await tracker.create(make_user_root_spec())
    child = await tracker.create(make_child_spec(parent_id=root.objective_id))
    await tracker.mark_abandoned(root.objective_id, rationale="drop")
    child_proj = tracker.get(child.objective_id)
    notifs = list(child_proj.parent_close_notifications)
    assert len(notifs) == 1
    assert notifs[0]["parent_id"] == root.objective_id
    assert notifs[0]["parent_event"] == "abandoned"
    assert notifs[0]["applied_policy"] == "notify"


async def test_parent_terminate_policy_cascades(tracker):
    root = await tracker.create(make_user_root_spec())
    child = await tracker.create(
        make_child_spec(
            parent_id=root.objective_id,
            parent_close_policy=ParentClosePolicy.terminate,
        )
    )
    await tracker.mark_abandoned(root.objective_id, rationale="drop")
    child_proj = tracker.get(child.objective_id)
    assert child_proj.status == ObjectiveStatus.abandoned


async def test_parent_abandon_policy_cascades(tracker):
    root = await tracker.create(make_user_root_spec())
    child = await tracker.create(
        make_child_spec(
            parent_id=root.objective_id,
            parent_close_policy=ParentClosePolicy.abandon,
        )
    )
    await tracker.mark_abandoned(root.objective_id, rationale="drop")
    child_proj = tracker.get(child.objective_id)
    assert child_proj.status == ObjectiveStatus.abandoned


async def test_parent_notify_mark_abandoned_requires_rationale(tracker):
    """mark_abandoned always requires rationale — not just re_open."""
    from loam.objective_tracker.errors import MissingRationaleError

    proj = await tracker.create(make_user_root_spec())
    with pytest.raises(MissingRationaleError):
        await tracker.mark_abandoned(proj.objective_id, rationale="")
