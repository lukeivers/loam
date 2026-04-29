"""R1–R5: compensation-path contract + registration surfaces."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from loam.reversibility_primitive import (
    CompensationPathBinding,
    ReversibilityStore,
)


def test_R1_binding_refuses_empty_handle(store: ReversibilityStore) -> None:
    """R1: Pydantic rejects empty handle."""
    with pytest.raises(ValidationError):
        CompensationPathBinding(
            scope_id="s1", handle="", idempotency_key="k1"
        )


def test_R1_binding_refuses_empty_idempotency_key(
    store: ReversibilityStore,
) -> None:
    """R1: Pydantic rejects empty idempotency_key."""
    with pytest.raises(ValidationError):
        CompensationPathBinding(
            scope_id="s1", handle="h1", idempotency_key=""
        )


def test_R1_binding_refuses_empty_scope_id(
    store: ReversibilityStore,
) -> None:
    """R1 tightening: empty scope_id also rejected at construction."""
    with pytest.raises(ValidationError):
        CompensationPathBinding(
            scope_id="", handle="h1", idempotency_key="k1"
        )


def test_R2_register_compensation_writes_binding(
    store: ReversibilityStore,
) -> None:
    """R2: a well-formed binding persists + emits the registered span."""
    b = CompensationPathBinding(
        scope_id="s1", handle="h1", idempotency_key="k1"
    )
    replaced, prior = store.upsert_binding(b)
    assert replaced is False
    assert prior is None
    assert store.get_binding("s1") is not None


def test_R3_cli_path_reaches_same_ipc_method(
    controller, tmp_path
) -> None:
    """R3: the CLI dispatch path reaches `reversibility.register_compensation`.

    We exercise the `register_compensation` IPC handler directly via
    the IPC wiring surface — the CLI is a thin forwarder around the
    same method name.
    """
    from loam.orchestrator.ipc import IPCServer

    server = IPCServer(tmp_path / "sock")
    from loam.reversibility_primitive import register_reversibility_ipc

    register_reversibility_ipc(
        server=server,
        store=controller.store,
        gate=controller.gate,
        rollback_runtime=controller.rollback_runtime,
    )
    handler = server._handlers["reversibility.register_compensation"]
    import asyncio

    result = asyncio.run(
        handler({"scope_id": "s1", "handle": "h1", "idempotency_key": "k1"})
    )
    assert result == {"ok": True, "binding_id": "s1", "replaced": False}
    assert controller.store.get_binding("s1") is not None


def test_R4_registration_before_scope_exists_is_accepted(
    store: ReversibilityStore,
) -> None:
    """R4: registration is not gated on scope existence — activation is."""
    b = CompensationPathBinding(
        scope_id="not-yet-created", handle="h1", idempotency_key="k1"
    )
    store.upsert_binding(b)
    assert store.get_binding("not-yet-created") is not None


def test_R5_duplicate_registration_replaces_binding(
    store: ReversibilityStore,
) -> None:
    """R5 (Eve-inference carried forward): last-writer-wins."""
    b1 = CompensationPathBinding(
        scope_id="s1", handle="old_handle", idempotency_key="k1"
    )
    store.upsert_binding(b1)
    b2 = CompensationPathBinding(
        scope_id="s1", handle="new_handle", idempotency_key="k2"
    )
    replaced, prior = store.upsert_binding(b2)
    assert replaced is True
    assert prior == "old_handle"
    assert store.get_binding("s1").handle == "new_handle"
