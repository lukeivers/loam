"""Typed contract surfaces for the reversibility primitive.

Per proposal §3.1:
  - CompensationPathBinding: the persisted row that binds a scope to a
    registered compensation handler.
  - RollbackContext: the frozen snapshot a handler receives — scope_id,
    spec, events, projection, idempotency_key, invocation_id.
  - RollbackResult: the Pydantic-validated outcome handlers return.

Pydantic `extra="forbid"` + `frozen=True` everywhere so unknown fields
are rejected at construction and records cannot mutate after creation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from scope_of_work import ScopeProjection, ScopeSpec


def iso_now() -> str:
    """UTC ISO-8601 timestamp. One place so tests can monkeypatch."""
    return datetime.now(timezone.utc).isoformat()


# ---- compensation-path binding ----------------------------------------


class CompensationPathBinding(BaseModel):
    """A registered compensation path bound to one scope.

    Frozen + extra-forbid. R1: empty `handle` or empty `idempotency_key`
    rejected at construction via the model_validator below.

    Per ruling #3 (proposal §2), `budget_seconds` defaults to `None`
    meaning "no framework-imposed timeout." Setting `budget_seconds=0`
    is rejected (`ge=1`) per R25.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    scope_id: str
    handle: str
    description: str = ""
    budget_seconds: int | None = Field(default=None, ge=1)
    idempotency_key: str
    registered_at: str = Field(default_factory=iso_now)
    registered_by: str = "workspace"

    @model_validator(mode="after")
    def _reject_empty(self) -> "CompensationPathBinding":
        if not self.handle.strip():
            raise ValueError("handle must not be empty")
        if not self.idempotency_key.strip():
            raise ValueError("idempotency_key must not be empty")
        if not self.scope_id.strip():
            raise ValueError("scope_id must not be empty")
        return self


# ---- rollback invocation ----------------------------------------------


RollbackState = Literal["requested", "in_progress", "succeeded", "failed", "degraded"]


@dataclass(frozen=True)
class RollbackContext:
    """Frozen snapshot a handler receives at invocation.

    Handlers read the committed state (events + projection) to decide
    how to compensate. The runtime constructs this from sealed
    scope-of-work read surfaces (`ScopeRuntime.get` + events_for).
    """

    scope_id: str
    scope_spec: ScopeSpec | None
    events: tuple[Any, ...]
    projection: ScopeProjection | None
    idempotency_key: str
    invocation_id: str


class RollbackResult(BaseModel):
    """Handler return value. Pydantic-validated so handlers cannot emit
    an outcome outside the known set."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    outcome: Literal["succeeded", "failed", "degraded"]
    narrative: str = ""
    compensated_at: str = Field(default_factory=iso_now)
    recoverable: bool = True


class RollbackInvocationRecord(BaseModel):
    """One row in the rollback_invocation table — FSM plus cached result."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    invocation_id: str
    scope_id: str
    idempotency_key: str
    state: RollbackState
    reason: str | None
    outcome: Literal["succeeded", "failed", "degraded"] | None
    narrative: str | None
    handle: str | None
    requested_at: str
    updated_at: str


# ---- path-choice output ------------------------------------------------


class RankedAlternatives(BaseModel):
    """Return value of `rank_alternatives` — which alternative won and why.

    `chosen_index` is into the *input* list order; the caller can use
    it to retrieve the spec they originally supplied.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    chosen_index: int
    chosen_class: str
    alternatives_count: int
    alternative_classes: tuple[str, ...]
    reason: str
    override: bool = False
    downrank_warning: bool = False
