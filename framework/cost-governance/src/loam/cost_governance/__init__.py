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

"""pOS v2 Cost Governance.

Public surface:

    CeilingAdjustment           — Pydantic audit record for IPC adjustments
    CostChannel                 — subclassed one-on-one channel
    CostConfig                  — YAML-loaded ceilings config
    CostController              — composed runtime
    CostLedger                  — gate + event-subscription runtime
    CostNotification            — Tier-2 warning payload
    CostNotifier                — one-on-one dispatcher
    CostStore                   — SQLite persistence
    Reservation                 — Pydantic reservation row
    RollingCeiling              — per-window cap record
    RollingRollup               — closed-interval rollup row
    RollupTask                  — interval-closure + retention
    SessionCeiling              — session-wide cap record
    SessionRollup               — in-place session totals
    default_config              — v1.0 defaults factory
    load_config                 — YAML loader
    register_cost_governance_ipc — bootstrap wiring
    render_ceiling_warning_text — notification text renderer

Error codes (IPC, reserved range -32060..-32069):
    -32060 cost_scope_budget_exceeded
    -32061 cost_session_ceiling_exceeded
    -32062 cost_rolling_ceiling_exceeded

Wrap registration order (brief §"Critical discipline anchors" #2):
    cost FIRST → reversibility SECOND → safety THIRD → orig_activate at core.
Dispatch chain: safety → reversibility → cost → orig_activate.
"""

from __future__ import annotations

from .config import (
    CostConfig,
    RollingCeiling,
    SessionCeiling,
    default_config,
    load_config,
)
from .controller import CostController
from .ipc_wiring import register_cost_governance_ipc
from .ledger import CostLedger
from .notification import (
    CostChannel,
    CostNotification,
    CostNotifier,
    render_ceiling_warning_text,
)
from .rollup import RollupRunResult, RollupTask
from .spec import (
    IPC_COST_ROLLING_CEILING_EXCEEDED,
    IPC_COST_SCOPE_BUDGET_EXCEEDED,
    IPC_COST_SESSION_CEILING_EXCEEDED,
    CeilingAdjustment,
    Reservation,
    RollingRollup,
    SessionRollup,
    iso_now,
    unix_now,
)
from .store import CostStore


__all__ = [
    "CeilingAdjustment",
    "CostChannel",
    "CostConfig",
    "CostController",
    "CostLedger",
    "CostNotification",
    "CostNotifier",
    "CostStore",
    "IPC_COST_ROLLING_CEILING_EXCEEDED",
    "IPC_COST_SCOPE_BUDGET_EXCEEDED",
    "IPC_COST_SESSION_CEILING_EXCEEDED",
    "Reservation",
    "RollingCeiling",
    "RollingRollup",
    "RollupRunResult",
    "RollupTask",
    "SessionCeiling",
    "SessionRollup",
    "default_config",
    "iso_now",
    "load_config",
    "register_cost_governance_ipc",
    "render_ceiling_warning_text",
    "unix_now",
]
