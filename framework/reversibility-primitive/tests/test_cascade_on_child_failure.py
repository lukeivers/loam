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

"""R18: cascade trigger — a child scope that transitions to `failed`
with a registered binding and ParentClosePolicy=TERMINATE invokes
rollback automatically via the pyee subscription."""

from __future__ import annotations

import asyncio
import pytest

from loam.reversibility_primitive import (
    CompensationPathBinding,
    RollbackContext,
    RollbackResult,
)
from loam.scope_of_work import ReversibilityClass

from .conftest import make_spec


@pytest.mark.asyncio
async def test_R18_child_failure_triggers_rollback(
    controller, scope_runtime
) -> None:
    spec = make_spec(reversibility=ReversibilityClass.compensatable)
    await scope_runtime.create(spec, scope_id="s-child")
    await scope_runtime.start("s-child")

    calls: list[RollbackContext] = []

    async def h(ctx: RollbackContext) -> RollbackResult:
        calls.append(ctx)
        return RollbackResult(outcome="succeeded", narrative="cascade unwind")

    controller.register_handler("h", h)
    controller.store.upsert_binding(
        CompensationPathBinding(
            scope_id="s-child", handle="h", idempotency_key="bind-k"
        )
    )

    # Wire the cascade subscription after binding is in place.
    controller.rollback_runtime.subscribe_to_cascade(scope_runtime)

    # Drive the child to failed — this emits StateTransitioned which
    # the cascade subscription observes.
    await scope_runtime.fail("s-child", reason="child broke")

    # The subscription runs in the same event loop; yield once to let
    # the async handler complete.
    await asyncio.sleep(0)
    # pyee schedules the handler; give the loop a tick to drain.
    for _ in range(5):
        await asyncio.sleep(0.01)
        if calls:
            break

    assert len(calls) == 1
    # The cascade-generated idempotency_key differs from the binding key.
    assert calls[0].idempotency_key.startswith("cascade-s-child-")


@pytest.mark.asyncio
async def test_R18_cascade_skipped_when_no_binding(
    controller, scope_runtime
) -> None:
    """No binding → no cascade. The subscription's filter short-circuits."""
    spec = make_spec(reversibility=ReversibilityClass.compensatable)
    await scope_runtime.create(spec, scope_id="s-child")
    await scope_runtime.start("s-child")

    called: list[int] = []

    async def h(ctx: RollbackContext) -> RollbackResult:
        called.append(1)
        return RollbackResult(outcome="succeeded", narrative="")

    controller.register_handler("h", h)
    # NO binding registered.
    controller.rollback_runtime.subscribe_to_cascade(scope_runtime)

    await scope_runtime.fail("s-child", reason="x")
    await asyncio.sleep(0.05)
    assert called == []
