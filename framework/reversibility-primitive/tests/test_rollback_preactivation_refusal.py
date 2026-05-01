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

"""R17: rollback invoked on a scope that never activated → -32052.

Ruling #2 locks the specific code and reason."""

from __future__ import annotations

import pytest
from loam.orchestrator.ipc import ApplicationError

from loam.reversibility_primitive import (
    CompensationPathBinding,
    IPC_REVERSIBILITY_NOT_ACTIVATED,
    RollbackContext,
    RollbackResult,
)
from loam.scope_of_work import ReversibilityClass

from .conftest import make_spec


@pytest.mark.asyncio
async def test_R17_preactivation_raises_not_activated(
    controller, scope_runtime
) -> None:
    """Scope is created but not started → rollback refuses."""
    spec = make_spec(reversibility=ReversibilityClass.compensatable)
    await scope_runtime.create(spec, scope_id="s1")

    # Bind and register a handler — they are irrelevant because the
    # scope hasn't activated.
    async def h(ctx: RollbackContext) -> RollbackResult:
        return RollbackResult(outcome="succeeded", narrative="")

    controller.register_handler("h", h)
    controller.store.upsert_binding(
        CompensationPathBinding(scope_id="s1", handle="h", idempotency_key="k")
    )
    with pytest.raises(ApplicationError) as exc:
        await controller.rollback_runtime.rollback(
            scope_id="s1", reason="pre"
        )
    assert exc.value.code == IPC_REVERSIBILITY_NOT_ACTIVATED


@pytest.mark.asyncio
async def test_R17_nonexistent_scope_also_refuses(
    controller, scope_runtime
) -> None:
    """A scope that has no events at all also refuses."""
    with pytest.raises(ApplicationError) as exc:
        await controller.rollback_runtime.rollback(
            scope_id="never-existed", reason="pre"
        )
    assert exc.value.code == IPC_REVERSIBILITY_NOT_ACTIVATED
