"""CR20 — reversibility rollback invokes the registered compensation handler.

The concrete rollback runtime is in reversibility-primitive (sealed).
This test verifies our compensation_handler's shape satisfies the
reversibility-primitive's handler contract: it is async, accepts
`scope_id` keyword, returns a dict with `ok=True`.

The actual rollback cascade is exercised by reversibility-primitive's
own test suite; this test is the self-correction-side wire-check.
"""

from __future__ import annotations

import inspect

from loam.self_correction import SelfCorrectionController


async def test_CR20_compensation_handler_is_async_and_accepts_scope_id(
    controller: SelfCorrectionController,
) -> None:
    handler = controller.compensation_handler
    assert inspect.iscoroutinefunction(handler)
    result = await handler(scope_id="scope-nope")
    assert result["ok"] is True
    # No episode for scope-nope → noop.
    assert result.get("noop") is True


async def test_CR20_handler_tolerates_extra_kwargs(
    controller: SelfCorrectionController,
) -> None:
    # Reversibility-primitive's rollback runtime passes extra kwargs
    # (reason, idempotency_key, etc.) — handler must accept and ignore.
    result = await controller.compensation_handler(
        scope_id="scope-x",
        reason="rollback_invoked",
        idempotency_key="abc",
    )
    assert result["ok"] is True
