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

"""ReversibilityController — composed runtime the workspace bootstrap wires.

Composition (proposal §3.1):
  - ReversibilityStore          — SQLite persistence
  - ActivationGate              — class-dispatch refusal before orig_activate
  - RollbackRuntime             — FSM + idempotence + cascade subscribe
  - RollbackNotifier            — one-on-one channel fail-closed dispatch
  - Handler registry            — `register_handler(handle, fn)` API

Usage:

    controller = ReversibilityController(
        store=ReversibilityStore(path),
        scope_runtime=scope_runtime,
        notifier=RollbackNotifier(channels=[...]),
        safety_approval_resolver=lambda h: safety_store.find_active_approval(h),
    )
    controller.register_handler("compensate_foo", async_fn)
    # Wire IPC (reversibility first, safety second):
    register_reversibility_ipc(server=server, store=controller.store,
        gate=controller.gate, rollback_runtime=controller.rollback_runtime,
        spec_resolver=resolver)
    register_safety_ipc(...)  # after reversibility
    controller.rollback_runtime.subscribe_to_cascade(scope_runtime)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from loam.scope_of_work import ScopeRuntime

from .activation_gate import ActivationGate, SafetyApprovalResolver
from .notification import RollbackNotifier
from .rollback import HandlerFn, RollbackRuntime
from .store import ReversibilityStore


@dataclass
class ReversibilityController:
    """Composed reversibility runtime — wired by workspace bootstrap."""

    store: ReversibilityStore
    scope_runtime: ScopeRuntime
    notifier: RollbackNotifier
    safety_approval_resolver: SafetyApprovalResolver | None = None
    handlers: dict[str, HandlerFn] = field(default_factory=dict)
    gate: ActivationGate = field(init=False)
    rollback_runtime: RollbackRuntime = field(init=False)

    def __post_init__(self) -> None:
        self.gate = ActivationGate(
            store=self.store,
            safety_approval_resolver=self.safety_approval_resolver,
        )
        self.rollback_runtime = RollbackRuntime(
            store=self.store,
            handlers=self.handlers,
            scope_runtime=self.scope_runtime,
            notifier=self.notifier,
        )

    def register_handler(self, handle: str, fn: HandlerFn) -> None:
        """Register an async compensation handler under `handle`."""
        if not handle:
            raise ValueError("handle must not be empty")
        self.handlers[handle] = fn
