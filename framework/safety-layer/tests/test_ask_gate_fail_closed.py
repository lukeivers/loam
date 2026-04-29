"""Ask-gate fail-closed behaviour — A10 + ruling #5.

A10. When no reachable OneOnOneChannel exists at gate-fire time, the
     gate returns BLOCK and no notification is queued. The scope stays
     `proposed`; `pos safety status` surfaces it.
"""

from __future__ import annotations

import pytest

from loam.orchestrator.ipc import ApplicationError

from loam.safety_layer import (
    SafetyConfig,
    SafetyController,
    SafetyNotifier,
)
from loam.safety_layer.controller import (
    IPC_SAFETY_CHANNEL_UNAVAILABLE,
)

from .conftest import make_spec
from .fakes import FakeOrchestrator, make_fake_channel


@pytest.mark.asyncio
async def test_A10_no_active_channel_fails_closed(
    scope_runtime, safety_store, default_ask_list
):
    # Channel present but inactive → fail-closed.
    ch, received = make_fake_channel(name="down", active=False)
    notifier = SafetyNotifier(channels=[ch])
    controller = SafetyController(
        scope_runtime=scope_runtime,
        orchestrator=FakeOrchestrator(),
        store=safety_store,
        ask_list=default_ask_list,
        config=SafetyConfig(),
        notifier=notifier,
    )

    spec = make_spec(
        constraints=("action_class=commit_external_funds",),
    )
    with pytest.raises(ApplicationError) as exc:
        await controller.check_gates(spec, scope_id="s-fc")

    assert exc.value.code == IPC_SAFETY_CHANNEL_UNAVAILABLE
    # No message was queued — nothing delivered.
    assert received == []


@pytest.mark.asyncio
async def test_A10_no_channels_at_all_also_fail_closed(
    scope_runtime, safety_store, default_ask_list
):
    notifier = SafetyNotifier(channels=[])
    controller = SafetyController(
        scope_runtime=scope_runtime,
        orchestrator=FakeOrchestrator(),
        store=safety_store,
        ask_list=default_ask_list,
        config=SafetyConfig(),
        notifier=notifier,
    )

    spec = make_spec(
        constraints=("action_class=commit_external_funds",),
    )
    with pytest.raises(ApplicationError) as exc:
        await controller.check_gates(spec, scope_id="s-empty")
    assert exc.value.code == IPC_SAFETY_CHANNEL_UNAVAILABLE


@pytest.mark.asyncio
async def test_A10_active_channel_delivers_ask(
    scope_runtime, safety_store, default_ask_list
):
    ch, received = make_fake_channel(active=True)
    notifier = SafetyNotifier(channels=[ch])
    controller = SafetyController(
        scope_runtime=scope_runtime,
        orchestrator=FakeOrchestrator(),
        store=safety_store,
        ask_list=default_ask_list,
        config=SafetyConfig(),
        notifier=notifier,
    )
    spec = make_spec(
        constraints=("action_class=commit_external_funds",),
    )
    with pytest.raises(ApplicationError):
        await controller.check_gates(spec, scope_id="s-live")
    # An ask message was delivered (active channel).
    assert len(received) == 1
    assert "Safety gate" in received[0]
