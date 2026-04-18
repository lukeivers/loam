"""Scope-of-work specifications and typed models.

The seven-field primitive from objectives spec v1.0:

    1. goal                    — what the scope is trying to accomplish
    2. constraints             — things the scope must not do
    3. budget                  — time, tokens, money caps (per-axis policies)
    4. reversibility_class     — fully_reversible | compensatable | irreversible
    5. success_criteria        — how "done" is judged
    6. observers               — who receives events for this scope
    7. escalation_triggers     — declarative predicates that can escalate

Pydantic validates every field at construction. A scope constructed with
any missing required field raises `ValidationError` — this is the
"missing any field rejects scope creation" acceptance criterion
(v1.0 Core primitives) handled deterministically with no runtime branch.
"""

from __future__ import annotations

from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


# ---- enums ------------------------------------------------------------


class ScopeState(str, Enum):
    """Lifecycle states (proposal §Lifecycle).

    proposed  → active → {paused ↔ active}* → {completed | failed | cancelled | escalated}

    `paused` with a pause_reason of `pending_extension_request` is the
    default exhaustion state — this is Luke's decision (brief §"Three
    decisions Luke made"): request-extension across all three budget
    axes by default.
    """

    proposed = "proposed"
    active = "active"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    escalated = "escalated"


class ReversibilityClass(str, Enum):
    fully_reversible = "fully_reversible"
    compensatable = "compensatable"
    irreversible = "irreversible"


class BudgetAxis(str, Enum):
    time = "time"
    tokens = "tokens"
    money = "money"


class BudgetExhaustionPolicy(str, Enum):
    """What happens when a budget axis is exhausted.

    Luke's decision: default is `request_extension` across all three axes
    (brief §"Three decisions Luke made"). Per-scope authors may override
    per axis at scope creation.
    """

    request_extension = "request_extension"
    halt_and_signal = "halt_and_signal"
    throttle = "throttle"


class ParentClosePolicy(str, Enum):
    """Child scope behaviour when parent is cancelled.

    Luke's decision: default is `TERMINATE` (brief §"Three decisions
    Luke made"). Per-scope authors may override to ABANDON or
    REQUEST_CANCEL.
    """

    TERMINATE = "TERMINATE"
    ABANDON = "ABANDON"
    REQUEST_CANCEL = "REQUEST_CANCEL"


# ---- budget -----------------------------------------------------------


class Budget(BaseModel):
    """Three-axis budget with per-axis exhaustion policy.

    A scope's budget is declared at creation. Any or all axes may be
    None, meaning "no cap on this axis" — but a cap of zero means "no
    budget granted" (exhaustion-immediate). At least one axis must be
    specified; a scope without any budget is a cost-governance
    violation (v1.0 Cost governance).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    time_seconds: int | None = Field(
        default=None,
        ge=0,
        description="Wall-clock seconds while state == active.",
    )
    tokens: int | None = Field(
        default=None,
        ge=0,
        description="Total LLM tokens across all calls.",
    )
    money_cents: int | None = Field(
        default=None,
        ge=0,
        description="Monetary cap in whole cents (derived-from-tokens by default).",
    )

    time_policy: BudgetExhaustionPolicy = BudgetExhaustionPolicy.request_extension
    tokens_policy: BudgetExhaustionPolicy = BudgetExhaustionPolicy.request_extension
    money_policy: BudgetExhaustionPolicy = BudgetExhaustionPolicy.request_extension

    def policy_for(self, axis: BudgetAxis) -> BudgetExhaustionPolicy:
        return {
            BudgetAxis.time: self.time_policy,
            BudgetAxis.tokens: self.tokens_policy,
            BudgetAxis.money: self.money_policy,
        }[axis]

    def cap_for(self, axis: BudgetAxis) -> int | None:
        return {
            BudgetAxis.time: self.time_seconds,
            BudgetAxis.tokens: self.tokens,
            BudgetAxis.money: self.money_cents,
        }[axis]

    def model_post_init(self, __context) -> None:  # noqa: D401
        if self.time_seconds is None and self.tokens is None and self.money_cents is None:
            raise ValueError(
                "Budget must declare at least one axis (time/tokens/money). "
                "A scope with no budget violates cost-governance."
            )


# ---- success criteria -------------------------------------------------


class SuccessCriterion(BaseModel):
    """One piece of the definition-of-done.

    Scope completion runs each criterion's evaluation (v1.0 Objective-
    based — alignment re-checked at every scope boundary). The
    evaluation result is itself an event and is auditable.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    criterion_id: str
    description: str
    # Criterion evaluation is by a caller-supplied check at completion
    # time. The primitive does not inspect this string — it is persisted
    # for audit / replay only.
    evaluation_hint: str | None = None


# ---- observers --------------------------------------------------------


class Observer(BaseModel):
    """A subscriber to this scope's events.

    The observer list is carried as a scope field (one of the seven) AND
    replayed through the event log — `observer_added` / `observer_removed`
    events let the audit trail reconstruct the subscriber list at any
    point in the scope's life (proposal §2.5).

    The `callback_handle` is a string identifier the runtime resolves to
    an actual async callable via `ScopeRuntime.register_callback`. This
    keeps the scope spec serialisable (closures are not).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    observer_id: str
    callback_handle: str | None = None
    event_types: tuple[str, ...] = ()
    """Empty tuple = subscribe to all event types."""


# ---- escalation triggers ----------------------------------------------
#
# Pydantic discriminated union of predicate shapes. Each trigger is
# stored in the event log as a literal record (no closures); the runtime
# evaluates them on every event emission.


class _TriggerBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    trigger_id: str
    reason_on_fire: str = ""


class BudgetThreshold(_TriggerBase):
    """Fires when a budget axis' remaining value crosses a threshold.

    The comparison is on *remaining* (not *consumed*) and is 'lt' (less
    than) — i.e. "escalate when tokens remaining falls below 10,000".
    """

    kind: Literal["budget_threshold"] = "budget_threshold"
    axis: BudgetAxis
    threshold: int = Field(ge=0)


class TimeElapsed(_TriggerBase):
    """Fires when wall-clock elapsed (in active state) exceeds seconds."""

    kind: Literal["time_elapsed"] = "time_elapsed"
    seconds: int = Field(ge=0)


class EventTypeTrigger(_TriggerBase):
    """Fires when a specific event type is emitted on this scope.

    Useful for "escalate when any child fails" (set `event_type` to
    `child_failed`) or "escalate when an unreachable-model event
    occurs".
    """

    kind: Literal["event_type"] = "event_type"
    event_type: str


class SuccessCriterionTrigger(_TriggerBase):
    """Fires when a named success criterion is evaluated not-met."""

    kind: Literal["success_criterion"] = "success_criterion"
    criterion_id: str
    fire_on: Literal["not_met", "met"] = "not_met"


class ReversibilityTrigger(_TriggerBase):
    """Fires when the scope's reversibility class matches the declared gate.

    Default use: irreversible scopes escalate on activation so a human
    confirms before the action runs. The safety layer (future
    component) will seed this trigger at scope creation when the class
    is `irreversible`.
    """

    kind: Literal["reversibility"] = "reversibility"
    match_class: ReversibilityClass = ReversibilityClass.irreversible


Trigger = Annotated[
    Union[
        BudgetThreshold,
        TimeElapsed,
        EventTypeTrigger,
        SuccessCriterionTrigger,
        ReversibilityTrigger,
    ],
    Field(discriminator="kind"),
]


# ---- ScopeSpec — the seven-field primitive ----------------------------


class ScopeSpec(BaseModel):
    """The seven-field declaration of a scope of work.

    Every field is required. Missing any raises `ValidationError` at
    construction — that is the v1.0 Core-primitives acceptance
    criterion ("scope of work carries all seven declared fields; missing
    any rejects scope creation") handled deterministically.

    Notes on representation:
    - `goal` is plain-text; caller authors it in whatever language.
    - `constraints` is a tuple of plain-text constraints (frozen to
      preserve replay determinism).
    - `observers` and `escalation_triggers` are tuples for the same
      reason — scope creation is an immutable declaration; mutations
      land via the API (which writes new events).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    goal: str = Field(min_length=1)
    constraints: tuple[str, ...]
    budget: Budget
    reversibility_class: ReversibilityClass
    success_criteria: tuple[SuccessCriterion, ...]
    observers: tuple[Observer, ...]
    escalation_triggers: tuple[Trigger, ...]

    # Optional scope-authoring metadata (not one of the seven fields;
    # useful for owner_persona cross-referencing per proposal §2.3).
    owner_persona: str | None = None
    parent_close_policy: ParentClosePolicy = ParentClosePolicy.TERMINATE
    """Policy applied when THIS scope's parent is cancelled.
    (Named from the child's perspective per Temporal convention.)"""

    # Opt-in stuck-detection hint consumed by the background-work
    # monitor (primary-persona layer D3). When set, a scope whose
    # wall-clock elapsed since first activation exceeds
    # `2 × expected_duration_seconds` with no state events since start
    # is reported as stuck via `list(stuck=True)`. Default `None` means
    # the scope opts out — the monitor will not attempt stuck inference
    # for it. (Luke's decision, brief §"Luke's decisions": default None.)
    expected_duration_seconds: float | None = Field(default=None, ge=0)
