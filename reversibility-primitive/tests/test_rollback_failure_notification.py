"""R16: handler failure transitions FSM to failed, emits failure span,
and surfaces a Tier-1 one-on-one notification."""

from __future__ import annotations

import pytest

from reversibility_primitive import (
    CompensationPathBinding,
    RollbackContext,
    RollbackResult,
)
from scope_of_work import ReversibilityClass

from .conftest import make_spec


@pytest.mark.asyncio
async def test_R16_failure_transitions_and_notifies(
    controller, scope_runtime, active_channel
) -> None:
    _, received = active_channel
    spec = make_spec(reversibility=ReversibilityClass.compensatable)
    await scope_runtime.create(spec, scope_id="s1")
    await scope_runtime.start("s1")

    async def h(ctx: RollbackContext) -> RollbackResult:
        raise RuntimeError("unwind broke")

    controller.register_handler("h", h)
    controller.store.upsert_binding(
        CompensationPathBinding(scope_id="s1", handle="h", idempotency_key="k")
    )

    record = await controller.rollback_runtime.rollback(
        scope_id="s1", reason="boom"
    )
    assert record.state == "failed"
    assert record.outcome == "failed"
    # A failure notification went out.
    assert len(received) == 1
    assert "Rollback failed" in received[0]
    assert "s1" in received[0]


@pytest.mark.asyncio
async def test_R16_timeout_counts_as_failure(
    controller, scope_runtime, active_channel
) -> None:
    """A handler that exceeds budget_seconds is recorded as failed."""
    import asyncio

    _, received = active_channel
    spec = make_spec(reversibility=ReversibilityClass.compensatable)
    await scope_runtime.create(spec, scope_id="s1")
    await scope_runtime.start("s1")

    async def slow(ctx: RollbackContext) -> RollbackResult:
        await asyncio.sleep(5)
        return RollbackResult(outcome="succeeded", narrative="")

    controller.register_handler("slow", slow)
    controller.store.upsert_binding(
        CompensationPathBinding(
            scope_id="s1",
            handle="slow",
            idempotency_key="k",
            budget_seconds=1,
        )
    )
    record = await controller.rollback_runtime.rollback(
        scope_id="s1", reason="tmo"
    )
    assert record.state == "failed"
    assert received and "timeout" in received[0].lower()


@pytest.mark.asyncio
async def test_R16_handler_returning_failed_notifies(
    controller, scope_runtime, active_channel
) -> None:
    """Handler returning RollbackResult(outcome='failed') is a failure
    path too — notification fires."""
    _, received = active_channel
    spec = make_spec(reversibility=ReversibilityClass.compensatable)
    await scope_runtime.create(spec, scope_id="s1")
    await scope_runtime.start("s1")

    async def h(ctx: RollbackContext) -> RollbackResult:
        return RollbackResult(outcome="failed", narrative="partial")

    controller.register_handler("h", h)
    controller.store.upsert_binding(
        CompensationPathBinding(scope_id="s1", handle="h", idempotency_key="k")
    )
    record = await controller.rollback_runtime.rollback(
        scope_id="s1", reason="r"
    )
    assert record.state == "failed"
    assert received
