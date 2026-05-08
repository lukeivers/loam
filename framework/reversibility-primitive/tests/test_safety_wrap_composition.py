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

"""Wrap ordering (Luke's ruling #1 / brief critical anchor #2).

Reversibility first → safety second → orig_activate. When both wraps
are installed on the same IPCServer:

    - a reversibility refusal bubbles up first (-32050), safety never
      runs.
    - when reversibility passes, safety fires next — e.g. dangerous-op
      gate may still block irreversible classes.
    - when both pass, orig_activate runs.

This test installs a fake `orig_activate` directly on the IPCServer,
then composes reversibility (first) and safety (second) wraps, and
asserts the resulting call chain.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from loam.orchestrator.ipc import ApplicationError, IPCServer

from loam.reversibility_primitive import (
    IPC_REVERSIBILITY_MISSING_COMPENSATION,
    ReversibilityController,
    ReversibilityStore,
    RollbackNotifier,
    register_reversibility_ipc,
)
from loam.safety_layer import (
    AlwaysAskList,
    DEFAULT_DANGEROUS_OP_SUBSET,
    DEFAULT_FRAMEWORK_FLOOR,
    SafetyConfig,
    SafetyController,
    SafetyNotifier,
    SafetyStore,
)
from loam.safety_layer.ipc_wiring import register_safety_ipc
from loam.scope_of_work import (
    ReversibilityClass,
    ScopeRuntime,
    ScopeSpec,
)

from .conftest import make_fake_channel, make_spec


@pytest.mark.asyncio
async def test_reversibility_wrap_runs_before_safety(tmp_path: Path) -> None:
    """Reversibility wrap raises -32050 before safety's wrap has a
    chance to run. If reversibility ran AFTER safety, safety's
    dangerous-op gate would fire first on an irreversible spec.
    """
    server = IPCServer(tmp_path / "sock")
    orig_calls: list[dict[str, Any]] = []

    async def orig_activate(params: dict[str, Any]) -> dict[str, Any]:
        orig_calls.append(params)
        return {"ok": True}

    server.register("activate_scope", orig_activate)

    # Reversibility primitive wiring.
    rev_store = ReversibilityStore(tmp_path / "rev.sqlite")
    scope_runtime = ScopeRuntime(tmp_path / "scope.sqlite")
    ch, _ = make_fake_channel()
    rev_notifier = RollbackNotifier(channels=[ch])

    # For the gate to check, we need a spec_resolver.
    spec_by_id: dict[str, ScopeSpec] = {}

    def resolve(scope_id: str) -> ScopeSpec | None:
        return spec_by_id.get(scope_id)

    controller = ReversibilityController(
        store=rev_store,
        scope_runtime=scope_runtime,
        notifier=rev_notifier,
    )
    register_reversibility_ipc(
        server=server,
        store=controller.store,
        gate=controller.gate,
        rollback_runtime=controller.rollback_runtime,
        spec_resolver=resolve,
    )

    # Safety-layer wiring — installed AFTER reversibility, so its wrap
    # captures the reversibility wrap as its orig_activate and the
    # call chain becomes reversibility → safety → orig.
    class _FakeOrch:
        def pause_activation(self, reason: str) -> None:
            pass

        def resume_activation(self) -> None:
            pass

        def request_stop(self) -> None:
            pass

    from loam.safety_layer.notification import SafetyChannel
    from loam.primary_persona.introduction import ChannelKind

    received: list[str] = []

    async def send(text: str) -> None:
        received.append(text)

    safety_ch = SafetyChannel(
        kind=ChannelKind.personal_telegram,
        name="safety-active",
        send=send,
        is_active=True,
    )

    safety_store = SafetyStore(tmp_path / "safety.sqlite")
    ask_list = AlwaysAskList(
        version=1,
        framework_floor=DEFAULT_FRAMEWORK_FLOOR,
        workspace_additions=(),
        dangerous_op_subset=DEFAULT_DANGEROUS_OP_SUBSET,
    )
    safety_controller = SafetyController(
        scope_runtime=scope_runtime,
        orchestrator=_FakeOrch(),
        store=safety_store,
        ask_list=ask_list,
        config=SafetyConfig(),
        notifier=SafetyNotifier(channels=[safety_ch]),
    )

    register_safety_ipc(
        server=server,
        controller=safety_controller,
        spec_resolver=resolve,
    )

    # Seed a compensatable spec with NO binding — reversibility must
    # refuse before safety runs.
    spec = make_spec(reversibility=ReversibilityClass.compensatable)
    spec_by_id["s-order"] = spec

    handler = server._handlers["activate_scope"]
    with pytest.raises(ApplicationError) as exc:
        await handler({"scope_id": "s-order"})
    assert exc.value.code == IPC_REVERSIBILITY_MISSING_COMPENSATION
    # Neither safety nor orig ran.
    assert orig_calls == []


@pytest.mark.asyncio
async def test_both_pass_forwards_to_orig(tmp_path: Path) -> None:
    """Fully-reversible + no safety hit → both wraps pass → orig runs."""
    server = IPCServer(tmp_path / "sock")
    orig_calls: list[dict[str, Any]] = []

    async def orig_activate(params: dict[str, Any]) -> dict[str, Any]:
        orig_calls.append(params)
        return {"ok": True, "forwarded": True}

    server.register("activate_scope", orig_activate)

    scope_runtime = ScopeRuntime(tmp_path / "scope.sqlite")
    rev_store = ReversibilityStore(tmp_path / "rev.sqlite")
    ch, _ = make_fake_channel()

    spec_by_id: dict[str, ScopeSpec] = {}

    def resolve(scope_id: str) -> ScopeSpec | None:
        return spec_by_id.get(scope_id)

    controller = ReversibilityController(
        store=rev_store,
        scope_runtime=scope_runtime,
        notifier=RollbackNotifier(channels=[ch]),
    )
    register_reversibility_ipc(
        server=server,
        store=controller.store,
        gate=controller.gate,
        rollback_runtime=controller.rollback_runtime,
        spec_resolver=resolve,
    )

    # Safety with default ask_list — no hits on a plain spec.
    from loam.primary_persona.introduction import ChannelKind
    from loam.safety_layer.notification import SafetyChannel

    received: list[str] = []

    async def send(text: str) -> None:
        received.append(text)

    safety_ch = SafetyChannel(
        kind=ChannelKind.personal_telegram,
        name="s-active",
        send=send,
        is_active=True,
    )

    class _FakeOrch:
        def pause_activation(self, reason: str) -> None:
            pass

        def resume_activation(self) -> None:
            pass

        def request_stop(self) -> None:
            pass

    safety_controller = SafetyController(
        scope_runtime=scope_runtime,
        orchestrator=_FakeOrch(),
        store=SafetyStore(tmp_path / "safety.sqlite"),
        ask_list=AlwaysAskList(
            version=1,
            framework_floor=DEFAULT_FRAMEWORK_FLOOR,
            workspace_additions=(),
            dangerous_op_subset=DEFAULT_DANGEROUS_OP_SUBSET,
        ),
        config=SafetyConfig(),
        notifier=SafetyNotifier(channels=[safety_ch]),
    )
    register_safety_ipc(
        server=server,
        controller=safety_controller,
        spec_resolver=resolve,
    )

    # Fully-reversible spec with no constraints that map to ask/dangerous.
    spec = make_spec(reversibility=ReversibilityClass.fully_reversible)
    spec_by_id["s-ok"] = spec

    handler = server._handlers["activate_scope"]
    result = await handler({"scope_id": "s-ok"})
    assert result == {"ok": True, "forwarded": True}
    assert len(orig_calls) == 1
