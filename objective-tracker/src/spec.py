"""Objective-tracker specifications and typed models.

The Objective primitive (objectives spec v1.0, §"Core primitives —
Objective") carries:

    1. goal                     — plain-language objective statement
    2. parent_id or root marker — forest-of-trees, one parent max
    3. acceptance_criteria      — testable criteria (discriminated union)
    4. time_bound               — ISO deadline or the literal "evergreen"
    5. authored_by              — "user" or a persona-handle string
    6. status                   — event-sourced; mutation is via events
    7. id                       — UUID string

Luke's decisions baked in (brief §"Luke's decisions baked into this
brief"):

- `authored_by` carries arbitrary provenance — the tracker stores
  whatever string the caller passes; no handle-registry cross-check.
- `time_bound` is mandatory at creation. Authors must pass either an
  ISO datetime string (deadline) or the literal string "evergreen"
  (with optional review cadence). Omission → construction raises.
- Parent-close policy default is `notify`, not TERMINATE. Children of
  a closed parent receive notification events; their own state is not
  automatically touched.

Pydantic validates every field at construction. An ObjectiveSpec
constructed with any missing required field raises ValidationError —
that is the v1.0 Core-primitives acceptance criterion handled
deterministically with no runtime branch.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ---- enums ------------------------------------------------------------


class ObjectiveStatus(str, Enum):
    """Event-sourced status.

    Lifecycle:

        proposed → active → {achieved | abandoned}
                    ↑           ↓
                    └── re_open ┘  (achieved → active, rationale mandatory)

    Abandoned → active via re_open is permitted too; Luke's decision
    attached `re_open` to "achieved" in the approved proposal, but the
    tracker accepts either direction as a corrective transition with
    mandatory rationale.
    """

    proposed = "proposed"
    active = "active"
    achieved = "achieved"
    abandoned = "abandoned"


class ParentClosePolicy(str, Enum):
    """What happens to a child objective when its parent closes.

    Default `notify` (Luke's decision — brief §"Luke's decisions"):
    abandonment of a parent objective is semantically distinct from
    cancellation of a parent scope. Children receive a notification
    event so their owner can decide; no automatic state change.

    Per-objective override available at creation.
    """

    notify = "notify"
    terminate = "terminate"
    abandon = "abandon"


class ParentCloseEventKind(str, Enum):
    """Why the parent closed — carried in the child's notification event."""

    achieved = "achieved"
    abandoned = "abandoned"


# ---- acceptance criteria ----------------------------------------------
#
# Discriminated union of four variants (proposal §"Criterion
# discriminated union"):
#
#   - prose              — free-text; caller-dispatched evaluation.
#   - scope_success      — references a scope-of-work; auto-evaluates on
#                          scope terminal state events.
#   - child_closure      — N-of-M children reaching `achieved` — the
#                          caller queries the current projection to
#                          evaluate.
#   - external_predicate — names a registered predicate (entry-point-
#                          pattern); caller dispatches evaluation.


class _CriterionBase(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    criterion_id: str = Field(min_length=1)
    description: str = ""


class ProseCriterion(_CriterionBase):
    """Free-text acceptance criterion.

    Evaluation is always caller-dispatched: a user or a persona (or an
    LLM harness via Claude via Max) reads the prose, makes a judgment,
    and pushes the result via `evaluate_criterion`.
    """

    kind: Literal["prose"] = "prose"
    prose: str = Field(min_length=1)


class ScopeSuccessCriterion(_CriterionBase):
    """Acceptance is "the referenced scope completes without failure".

    The tracker subscribes to scope-of-work's pyee emitter at runtime
    startup for every scope referenced by a ScopeSuccessCriterion. On a
    terminal state-change event (completed | failed | cancelled), the
    tracker writes an evaluation event automatically (Luke's decision
    — brief §"Luke's decisions": `scope_success` auto-evaluates).

    The `success_states` set determines which terminal states count as
    "met". Default is {"completed"}.
    """

    kind: Literal["scope_success"] = "scope_success"
    scope_id: str = Field(min_length=1)
    success_states: frozenset[str] = frozenset({"completed"})


class ChildClosureCriterion(_CriterionBase):
    """Acceptance is N-of-M children reaching `achieved`.

    The tracker records the criterion but does NOT auto-evaluate — the
    caller queries `list(parent_id=...)` and pushes the evaluation when
    they decide to check. This matches the "caller-dispatched" posture
    for everything except `scope_success`.
    """

    kind: Literal["child_closure"] = "child_closure"
    required_count: int = Field(ge=1)
    """At least this many children must be in `achieved` state."""


class ExternalPredicateCriterion(_CriterionBase):
    """Acceptance is a registered predicate evaluating true.

    `predicate_id` is an opaque string; the ODD harness (or any
    external consumer) matches it against its registry and runs the
    predicate. The result comes back through `evaluate_criterion`.
    """

    kind: Literal["external_predicate"] = "external_predicate"
    predicate_id: str = Field(min_length=1)


Criterion = Annotated[
    Union[
        ProseCriterion,
        ScopeSuccessCriterion,
        ChildClosureCriterion,
        ExternalPredicateCriterion,
    ],
    Field(discriminator="kind"),
]


# ---- time-bound model -------------------------------------------------


class TimeBound(BaseModel):
    """How the objective is time-bound.

    Luke's decision: mandatory at creation. Caller must pick one:

    - `deadline`: an absolute ISO datetime (UTC recommended). The
      objective is expected to resolve by this moment.
    - `evergreen`: the string literal `"evergreen"`; the objective
      has no deadline. Optional `review_cadence` names a human-readable
      review interval (e.g. "weekly") — recorded for audit only; the
      tracker does not act on it.

    Exactly one of `deadline` or `evergreen` must be set.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    deadline: datetime | None = None
    evergreen: bool = False
    review_cadence: str | None = None

    @model_validator(mode="after")
    def _exactly_one(self) -> "TimeBound":
        if self.deadline is None and not self.evergreen:
            raise ValueError(
                "TimeBound requires either a deadline or evergreen=True. "
                "Omission rejects objective creation (Luke's decision)."
            )
        if self.deadline is not None and self.evergreen:
            raise ValueError(
                "TimeBound may declare a deadline OR evergreen, not both."
            )
        if self.review_cadence is not None and not self.evergreen:
            raise ValueError(
                "review_cadence is only meaningful when evergreen=True."
            )
        return self


# ---- LiftedFrom — provenance pointer (amendment #38) ------------------


class LiftedFrom(BaseModel):
    """Source-document provenance for an extracted objective.

    Records which document, which clause within that document, and
    (optionally) at which commit a tracker record was lifted from.
    Additive metadata on `ObjectiveSpec` introduced by amendment #38
    to make plan-doc-as-projection (Heavy-B downstream) tractable.

    Strict-shape contract mirrors `TimeBound`: `extra="forbid"`,
    `frozen=True`, every key validated. The parent `ObjectiveSpec`
    keeps `lifted_from = None` as the default; a record with no
    provenance pointer is well-formed (all pre-amendment-#38 records
    deserialise this way under D8 semantic round-trip).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_doc: str = Field(min_length=1)
    """Path or URI of the source document (e.g. plan doc path)."""

    source_ac: str = Field(min_length=1)
    """The clause/AC label inside the source document this record
    was lifted from (e.g. "AC38.1")."""

    source_commit: str | None = None
    """Optional commit SHA at which the source clause was canonical.
    Empty string rejects; missing/None is allowed."""

    @field_validator("source_commit")
    @classmethod
    def _source_commit_non_empty_when_set(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError(
                "source_commit must be a non-empty string when set; "
                "use None to omit"
            )
        return v


# ---- ObjectiveSpec — the seven-field primitive ------------------------


class ObjectiveSpec(BaseModel):
    """The declaration of an objective.

    Mandatory fields: goal, parent_id-or-root, acceptance_criteria,
    time_bound, authored_by, status is assigned by the tracker (not by
    the caller).

    Every field is validated at construction. Missing any required
    field → ValidationError at construction — the v1.0 Core-primitives
    acceptance criterion handled deterministically.

    Notes:

    - `parent_id` is None for roots. A root objective must be authored
      by "user" for any descendant to be bindable to a scope (D2 +
      D4 enforcement invariant); non-user roots are accepted but
      bindings that chain up to them raise `OrphanRootError`.
    - `authored_by` is an unvalidated string — `"user"` or any
      persona handle (e.g. `"mara"`). The tracker does NOT cross-check
      handle strings against any registry. (Proposal assumption #1;
      confirmed in Luke's decisions.)
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    goal: str = Field(min_length=1)
    parent_id: str | None = None
    acceptance_criteria: tuple[Criterion, ...]
    time_bound: TimeBound
    authored_by: str = Field(min_length=1)
    owner: str | None = None
    parent_close_policy: ParentClosePolicy = ParentClosePolicy.notify
    lifted_from: LiftedFrom | None = None
    """Optional source-document provenance (amendment #38). Defaults
    to None for records authored without provenance — preserves the
    pre-widening shape under D8 semantic round-trip."""

    @field_validator("acceptance_criteria")
    @classmethod
    def _unique_criterion_ids(
        cls, v: tuple[Criterion, ...]
    ) -> tuple[Criterion, ...]:
        ids = [c.criterion_id for c in v]
        if len(ids) != len(set(ids)):
            raise ValueError("acceptance_criteria criterion_ids must be unique")
        return v
