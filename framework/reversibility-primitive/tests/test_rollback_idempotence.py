"""R14: rollback idempotence by (scope_id, idempotency_key)."""

from __future__ import annotations

import pytest

from loam.reversibility_primitive import (
    CompensationPathBinding,
    RollbackContext,
    RollbackResult,
)
from loam.scope_of_work import ReversibilityClass

from .conftest import make_spec


@pytest.mark.asyncio
async def test_R14_second_call_returns_cached_result(
    controller, scope_runtime
) -> None:
    spec = make_spec(reversibility=ReversibilityClass.compensatable)
    await scope_runtime.create(spec, scope_id="s1")
    await scope_runtime.start("s1")

    invocations: list[int] = []

    async def h(ctx: RollbackContext) -> RollbackResult:
        invocations.append(1)
        return RollbackResult(outcome="succeeded", narrative="did it")

    controller.register_handler("h", h)
    controller.store.upsert_binding(
        CompensationPathBinding(
            scope_id="s1", handle="h", idempotency_key="same-key"
        )
    )

    r1 = await controller.rollback_runtime.rollback(
        scope_id="s1", reason="first", idempotency_key="same-key"
    )
    r2 = await controller.rollback_runtime.rollback(
        scope_id="s1", reason="second", idempotency_key="same-key"
    )
    assert r1.outcome == "succeeded"
    assert r2.outcome == "succeeded"
    assert r1.invocation_id == r2.invocation_id
    # Handler invoked exactly once.
    assert len(invocations) == 1
