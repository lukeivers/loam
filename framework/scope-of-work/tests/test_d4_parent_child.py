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

"""D4 — parent/child hierarchy with parent-close policies.

Acceptance (brief D4):
- Creating a child scope under a parent links them in the event log.
- Cancelling the parent under TERMINATE policy (default) cascades to
  active children within a bounded time.
- Under ABANDON, children continue; under REQUEST_CANCEL, children
  receive a cancel request they can honour or reject.
- asyncio.TaskGroup handles in-process children; event-log polling
  handles cross-process coordination.
"""

from __future__ import annotations

import asyncio

import pytest

from loam.scope_of_work.events import ChildLinked, ParentCloseRequested
from loam.scope_of_work.spec import (
    Budget,
    ParentClosePolicy,
    ScopeState,
)
from tests.conftest import make_spec


async def test_child_linked_event_on_parent(runtime):
    parent = await runtime.create(make_spec(goal="parent"))
    await runtime.start(parent.scope_id)
    child = await runtime.create(make_spec(goal="child"), parent_scope_id=parent.scope_id)
    parent_events = runtime.store.events_for(parent.scope_id)
    links = [e for e in parent_events if isinstance(e, ChildLinked)]
    assert len(links) == 1
    assert links[0].child_scope_id == child.scope_id
    # The child also remembers its parent.
    fetched_child = runtime.get(child.scope_id)
    assert fetched_child.parent_scope_id == parent.scope_id


async def test_terminate_default_cascades(runtime):
    parent = await runtime.create(make_spec(goal="parent"))
    await runtime.start(parent.scope_id)
    a = await runtime.create(make_spec(goal="a"), parent_scope_id=parent.scope_id)
    b = await runtime.create(make_spec(goal="b"), parent_scope_id=parent.scope_id)
    await runtime.start(a.scope_id)
    await runtime.start(b.scope_id)

    await runtime.cancel(parent.scope_id, reason="user halt")

    # Both children should be cancelled (TERMINATE is the default).
    assert runtime.get(a.scope_id).state == ScopeState.cancelled
    assert runtime.get(b.scope_id).state == ScopeState.cancelled


async def test_abandon_policy_lets_child_continue(runtime):
    parent = await runtime.create(make_spec())
    await runtime.start(parent.scope_id)
    child = await runtime.create(
        make_spec(parent_close_policy=ParentClosePolicy.ABANDON),
        parent_scope_id=parent.scope_id,
    )
    await runtime.start(child.scope_id)
    await runtime.cancel(parent.scope_id)
    # Child's state untouched.
    assert runtime.get(child.scope_id).state == ScopeState.active


async def test_request_cancel_policy_signals_child(runtime):
    parent = await runtime.create(make_spec())
    await runtime.start(parent.scope_id)
    child = await runtime.create(
        make_spec(parent_close_policy=ParentClosePolicy.REQUEST_CANCEL),
        parent_scope_id=parent.scope_id,
    )
    await runtime.start(child.scope_id)
    await runtime.cancel(parent.scope_id)
    # The child saw a parent_close_requested event but is still active
    # — it can choose to honour or reject.
    events = runtime.store.events_for(child.scope_id)
    assert any(isinstance(e, ParentCloseRequested) for e in events)
    assert runtime.get(child.scope_id).state == ScopeState.active


async def test_terminate_cascade_walks_grandchildren(runtime):
    grandparent = await runtime.create(make_spec(goal="grandparent"))
    await runtime.start(grandparent.scope_id)
    parent = await runtime.create(make_spec(goal="parent"), parent_scope_id=grandparent.scope_id)
    await runtime.start(parent.scope_id)
    child = await runtime.create(make_spec(goal="child"), parent_scope_id=parent.scope_id)
    await runtime.start(child.scope_id)

    await runtime.cancel(grandparent.scope_id)

    assert runtime.get(parent.scope_id).state == ScopeState.cancelled
    assert runtime.get(child.scope_id).state == ScopeState.cancelled


async def test_terminate_cascade_within_bounded_time(runtime):
    """Cascade halt is bounded — within 1 second for an in-process tree
    of 50 children. (Proposal §6 surprise #1: cross-process is the hard
    case; in-process is trivially fast via asyncio.)"""
    import time

    parent = await runtime.create(make_spec())
    await runtime.start(parent.scope_id)
    children = []
    for i in range(50):
        c = await runtime.create(
            make_spec(goal=f"c{i}"), parent_scope_id=parent.scope_id
        )
        await runtime.start(c.scope_id)
        children.append(c)

    t0 = time.monotonic()
    await runtime.cancel(parent.scope_id)
    elapsed = time.monotonic() - t0
    assert elapsed < 1.0, f"cascade took {elapsed:.3f}s for 50 children"
    for c in children:
        assert runtime.get(c.scope_id).state == ScopeState.cancelled


async def test_taskgroup_friendly_dispatch(runtime):
    """asyncio.TaskGroup-style structured concurrency: spawn children
    in a task group; when one fails, sibling cancellations propagate
    via the runtime's cancel API."""
    parent = await runtime.create(make_spec())
    await runtime.start(parent.scope_id)

    children = []
    for i in range(3):
        c = await runtime.create(
            make_spec(goal=f"sibling-{i}"), parent_scope_id=parent.scope_id
        )
        await runtime.start(c.scope_id)
        children.append(c)

    async def child_work(scope_id: str, fail: bool):
        await asyncio.sleep(0.01)
        if fail:
            await runtime.fail(scope_id, "boom")

    # Run all three under a task group; second one fails fast.
    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(child_work(children[0].scope_id, fail=False))
            tg.create_task(child_work(children[1].scope_id, fail=False))
            tg.create_task(child_work(children[2].scope_id, fail=True))
    except* RuntimeError:
        # A failed scope transitions to `failed` and the task completes
        # — we don't actually raise here. Pattern is illustrative.
        pass

    # No assertion on cancellation here — TaskGroup is the in-process
    # concurrency primitive; the cancel-cascade test above is the
    # acceptance case. This test confirms the runtime is TaskGroup-
    # compatible.
    assert runtime.get(children[2].scope_id).state == ScopeState.failed
