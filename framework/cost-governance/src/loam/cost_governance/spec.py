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

"""Pydantic records + error codes for cost governance.

Structural-impossibility defence-in-depth (C27): every amount is
`Field(ge=0)` on the Pydantic model AND a SQL `CHECK (>= 0)`
constraint on the matching column. A negative amount cannot be
constructed at Python, cannot be stored via SQLite, cannot slip in
via row-factory round-trip.

Error codes are reserved in the `-32060..-32069` range (brief hard
constraint; no overlap with safety `-32040..-32049` or reversibility
`-32050..-32059`).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ---- error codes (IPC, reserved range -32060..-32069) ----------------

IPC_COST_SCOPE_BUDGET_EXCEEDED = -32060
IPC_COST_SESSION_CEILING_EXCEEDED = -32061
IPC_COST_ROLLING_CEILING_EXCEEDED = -32062
# -32063..-32069 reserved for future (ceiling-adjustment validation,
# reservation-reconcile errors).


# ---- timestamp helper -----------------------------------------------


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def unix_now() -> float:
    return datetime.now(timezone.utc).timestamp()


# ---- reservation record ---------------------------------------------


ReservationState = Literal["active", "reconciled"]


class Reservation(BaseModel):
    """One row per activation that passed the cost gate.

    `reserved_*` are the declared-at-activation caps. `actual_*` are the
    accumulated spend as `BudgetDebited` / `BudgetRefunded` events arrive.
    Reconciliation copies `actual_*` forward, flips state, stamps
    `reconciled_at`.

    Pydantic `ge=0` on every amount field — clause-(g): negative spend
    is structurally impossible. Matched by SQL `CHECK` constraints in
    the store.
    """

    model_config = ConfigDict(extra="forbid")

    scope_id: str
    session_id: str
    state: ReservationState = "active"

    # Declared-at-activation caps (per axis). `None` = axis not declared.
    reserved_time_seconds: int | None = Field(default=None, ge=0)
    reserved_tokens: int | None = Field(default=None, ge=0)
    reserved_money_cents: int | None = Field(default=None, ge=0)

    # Accumulated actual spend. `ge=0` — refunds are applied as
    # negative-delta updates but the stored total is bounded at zero by
    # the ledger (prevents an unrelated refund from sinking the row
    # below zero).
    actual_time_seconds: int = Field(default=0, ge=0)
    actual_tokens: int = Field(default=0, ge=0)
    actual_money_cents: int = Field(default=0, ge=0)

    reserved_at: str = Field(default_factory=iso_now)
    reconciled_at: str | None = None


# ---- session rollup --------------------------------------------------


class SessionRollup(BaseModel):
    """One row per session. In-place updates on each debit/refund.

    Retained 365 days after `ended_at` (Luke's ruling #3).
    """

    model_config = ConfigDict(extra="forbid")

    session_id: str
    total_time_seconds: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    total_money_cents: int = Field(default=0, ge=0)
    started_at: str = Field(default_factory=iso_now)
    ended_at: str | None = None


# ---- rolling-window rollup ------------------------------------------

WindowKind = str  # "daily", "hourly", "4-hourly", ... — workspace-declared.


class RollingRollup(BaseModel):
    """One row per (window_kind, interval_end_unix) — closed interval.

    Retained indefinitely (Luke's ruling #3 — low volume, audit record).
    Idempotent under double-run and clock skew: the PRIMARY KEY
    `(window_kind, interval_end_unix)` prevents duplicates.
    """

    model_config = ConfigDict(extra="forbid")

    window_kind: WindowKind
    interval_start_unix: float
    interval_end_unix: float
    total_time_seconds: int = Field(default=0, ge=0)
    total_tokens: int = Field(default=0, ge=0)
    total_money_cents: int = Field(default=0, ge=0)
    closed_at: str = Field(default_factory=iso_now)


# ---- ceiling adjustment audit row -----------------------------------

CeilingKind = Literal["session", "rolling"]
CeilingAxis = Literal["money", "tokens", "time"]


class CeilingAdjustment(BaseModel):
    """Audit record for an IPC-initiated ceiling change.

    `new_value` is an absolute cap (proposal §8 inference #8 — not a
    delta). `None` removes the cap on the axis.
    """

    model_config = ConfigDict(extra="forbid")

    audit_record_id: int = 0  # assigned by store on append
    ceiling_kind: CeilingKind
    axis: CeilingAxis
    window_kind: WindowKind | None = None  # required iff ceiling_kind=rolling
    new_value: int | None = Field(default=None, ge=0)
    reason: str
    adjusted_at: str = Field(default_factory=iso_now)
    adjusted_by: str = "ipc"
