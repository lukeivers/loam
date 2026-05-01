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

"""R13, R15: rollback invocation lifecycle — requested → in_progress →
succeeded, with scope-runtime cancel driven on success."""

from __future__ import annotations

import pytest

from loam.reversibility_primitive import (
    CompensationPathBinding,
    RollbackContext,
    RollbackResult,
)
from loam.scope_of_work import ReversibilityClass, ScopeState

from .conftest import make_spec


async def _create_and_activate(scope_runtime, spec_kwargs=None):
    spec = make_spec(**(spec_kwargs or {}))
    proj = await scope_runtime.create(spec, scope_id="s1")
    await scope_runtime.start("s1")
    return proj


@pytest.mark.asyncio
async def test_R13_rollback_records_fsm_and_invokes_handler(
    controller, scope_runtime, active_channel
) -> None:
    """R13: rollback writes the invocation row, transitions to
    in_progress, invokes the handler, records outcome."""
    await _create_and_activate(
        scope_runtime,
        {"reversibility": ReversibilityClass.compensatable},
    )
    received: list[RollbackContext] = []

    async def h(ctx: RollbackContext) -> RollbackResult:
        received.append(ctx)
        return RollbackResult(outcome="succeeded", narrative="unwound ok")

    controller.register_handler("h", h)
    controller.store.upsert_binding(
        CompensationPathBinding(
            scope_id="s1", handle="h", idempotency_key="k1"
        )
    )
    record = await controller.rollback_runtime.rollback(
        scope_id="s1", reason="test"
    )
    assert record.state == "succeeded"
    assert record.outcome == "succeeded"
    assert record.narrative == "unwound ok"
    assert len(received) == 1
    # R15: scope driven to cancelled.
    proj = scope_runtime.get("s1")
    assert proj is not None and proj.state == ScopeState.cancelled


@pytest.mark.asyncio
async def test_R15_scope_cancelled_via_scoperuntime_cancel(
    controller, scope_runtime
) -> None:
    """R15: explicit — on handler success, scope_runtime.cancel fires."""
    await _create_and_activate(
        scope_runtime, {"reversibility": ReversibilityClass.compensatable}
    )

    async def h(ctx: RollbackContext) -> RollbackResult:
        return RollbackResult(outcome="succeeded", narrative="")

    controller.register_handler("h", h)
    controller.store.upsert_binding(
        CompensationPathBinding(scope_id="s1", handle="h", idempotency_key="k")
    )
    await controller.rollback_runtime.rollback(scope_id="s1", reason="r")
    proj = scope_runtime.get("s1")
    assert proj is not None
    assert proj.state == ScopeState.cancelled
