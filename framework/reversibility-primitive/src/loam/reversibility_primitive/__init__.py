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

"""pOS v2 Reversibility Primitive.

Public surface:

    ActivationGate              — class-dispatch refusal wrap
    CompensationPathBinding     — Pydantic binding record
    RankedAlternatives          — `rank_alternatives` return
    ReversibilityChannel        — one-on-one rollback-failure channel
    ReversibilityController     — composed runtime
    ReversibilityStore          — SQLite persistence
    RollbackContext             — frozen handler input
    RollbackInvocationRecord    — FSM row
    RollbackNotifier            — one-on-one notifier
    RollbackResult              — handler output
    RollbackRuntime             — rollback FSM / invocation
    rank_alternatives           — pure preference ranking
    register_reversibility_ipc  — bootstrap wiring

Error codes (IPC, reserved range -32050..-32059):
    -32050 reversibility_missing_compensation
    -32051 reversibility_unregistered_handle
    -32052 reversibility_not_activated

The primitive reuses safety's `structural_hash` (ruling #4). No
amendments to sealed components.
"""

from __future__ import annotations

from .activation_gate import (
    IPC_REVERSIBILITY_MISSING_COMPENSATION,
    ActivationGate,
    SafetyApprovalResolver,
)
from .controller import ReversibilityController
from .ipc_wiring import register_reversibility_ipc
from .notification import (
    ReversibilityChannel,
    RollbackNotification,
    RollbackNotifier,
    render_rollback_failure_text,
)
from .path_choice import rank_alternatives
from .rollback import (
    IPC_REVERSIBILITY_NOT_ACTIVATED,
    IPC_REVERSIBILITY_UNREGISTERED_HANDLE,
    HandlerFn,
    RollbackRuntime,
)
from .spec import (
    CompensationPathBinding,
    RankedAlternatives,
    RollbackContext,
    RollbackInvocationRecord,
    RollbackResult,
)
from .store import ReversibilityStore


# Re-export safety's structural_hash so callers can reference a single
# symbol via this package; R26 asserts identity with safety's export.
from loam.safety_layer.events import structural_hash as get_spec_hash  # noqa: E402


__all__ = [
    "ActivationGate",
    "CompensationPathBinding",
    "HandlerFn",
    "IPC_REVERSIBILITY_MISSING_COMPENSATION",
    "IPC_REVERSIBILITY_NOT_ACTIVATED",
    "IPC_REVERSIBILITY_UNREGISTERED_HANDLE",
    "RankedAlternatives",
    "ReversibilityChannel",
    "ReversibilityController",
    "ReversibilityStore",
    "RollbackContext",
    "RollbackInvocationRecord",
    "RollbackNotification",
    "RollbackNotifier",
    "RollbackResult",
    "RollbackRuntime",
    "SafetyApprovalResolver",
    "get_spec_hash",
    "rank_alternatives",
    "register_reversibility_ipc",
    "render_rollback_failure_text",
]
