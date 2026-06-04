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
                    ↑  ↕        ↓
                    │  owner_pending
                    │  ↓     ↓     ↓
                    │ active achieved abandoned
                    └── re_open ┘  (achieved → active, rationale mandatory)

    Abandoned → active via re_open is permitted too; Luke's decision
    attached `re_open` to "achieved" in the approved proposal, but the
    tracker accepts either direction as a corrective transition with
    mandatory rationale.

    `owner_pending` (session-`/clear`-safety R2 — additive lifecycle
    widening, amendment-38 additive precedent): "work shipped, owner
    decision pending." Distinct from `active` (in progress) and from
    the terminal set `{achieved, abandoned}` (closed). It is the single
    distinction a hand-maintained RESUME-STATE file existed to carry —
    that a shipped item is *awaiting the owner's call, not done*. An
    objective enters it from `active` (work shipped) and leaves it when
    the owner rules: back to `active` (resume / re-scope) or onward to
    `achieved` / `abandoned` (closed). It is NOT terminal and NOT
    treated as in-flight-by-default — it is its own category so the
    session-start digest never collapses it into "done" (R2.2, surfaced
    in R1's primary-persona digest fence per D-SCS.4) nor buries it as
    just another active item. Pre-R2 records never carry this status;
    the default lifecycle and every existing transition are unchanged
    (default-preserving, D8 round-trip — AC.SCS-R2.3).
    """

    proposed = "proposed"
    active = "active"
    owner_pending = "owner_pending"
    blocked = "blocked"
    achieved = "achieved"
    abandoned = "abandoned"

    # ---- WMS increment 2 — the `blocked` lifecycle distinction --------
    #
    # `blocked` (WMS-D1 / AC.WI.1 — additive lifecycle widening, the
    # `owner_pending` R2 precedent): "work is started but cannot proceed
    # because it waits on an unresolved blocker (another work item or an
    # external party)." Distinct from `active` (in progress, unblocked),
    # from `owner_pending` (shipped, owner-blocked), and from the terminal
    # set `{achieved, abandoned}`. The work-management unblocked-next query
    # (AC.WI.EDGE.2) reads the `waits-on`/`blocks` edge graph to answer
    # "what is the next unblocked thing"; the `blocked` status is the
    # lifecycle signal an item is parked on a blocker. An objective enters
    # it from `active` (a blocker surfaced) and leaves it back to `active`
    # when the blocker clears. It is NOT terminal. Pre-increment-2 records
    # never carry this status; the default lifecycle and every existing
    # transition are unchanged (default-preserving D8 round-trip —
    # AC.WI.1).


class WorkEdgeKind(str, Enum):
    """The kind of a non-tree relational edge between two work items.

    WMS increment 2 (AC.WI.EDGE.1). The objective tracker's native
    structure is a single-parent forest (the `parent_id` tree); these
    are the NON-tree relationships memory has no concept of:

    - `blocks`     — the `from` item blocks the `to` item (the `to` item
                     cannot proceed until the `from` item resolves). The
                     inverse the unblocked-next query reads.
    - `waits_on`   — the `from` item waits on the `to` item (or, when an
                     external `party` is named on the edge, on a party
                     outside the work graph — "the launch waits on Eric").
    - `relates_to` — a soft, non-blocking link (the `from` and `to`
                     items are related but neither blocks the other).

    Edges are recorded as append-only `WorkEdge` / `WorkEdgeCleared`
    events (D-WMS2.2), not in-spec fields — the spec is frozen and edges
    are mutable relationships (a `waits_on` clears when the blocker
    ships). The event-pair keeps the single-source-of-truth + the D8
    replay round-trip.
    """

    blocks = "blocks"
    waits_on = "waits_on"
    relates_to = "relates_to"


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

    # ---- WMS increment 2 — the work-item field-groups (AC.WI.1) -------
    #
    # All three are ADDITIVE optional fields with defaults that preserve
    # the pre-increment-2 shape under the D8 round-trip (the `lifted_from`
    # additive precedent above). A work item constructed without any of
    # them is still well-formed; every pre-existing record deserialises
    # unchanged.

    belongs_to_project: str | None = None
    """Optional binding to a project (resolved at render time against
    the FBM `PROJECT_REGISTRY`). A bound item's STATE derives live from
    `derive_project_state`; an unbound item is honestly marked. WMS-D1
    (AC.PROJ.1/AC.PROJ.3). Defaults to None — pre-increment-2 records
    deserialise unbound."""

    tagged_streams: tuple[str, ...] = ()
    """The cross-cutting work-streams this item is tagged with (the
    streams-lens membership the increment-1 streams re-point reads —
    WMS-D7 / AC.REPOINT.1). A single item may be tagged with several
    streams AND bound to a project; it appears in both lenses without
    being stored twice. Defaults to the empty tuple — pre-increment-2
    records deserialise untagged."""

    priority: str | None = None
    """Optional priority signal the projects-lens sort reads (AC.PROJ.1).
    This cycle the field EXISTS and is populated from the existing
    `tracker_context` open-loop priority vocabulary (D-WMS2.5); the
    multi-signal WMS-D5 derived weighting is increment 4, not here.
    Defaults to None — an item with no priority sorts after prioritised
    items. Pre-increment-2 records deserialise with priority None."""

    @field_validator("acceptance_criteria")
    @classmethod
    def _unique_criterion_ids(
        cls, v: tuple[Criterion, ...]
    ) -> tuple[Criterion, ...]:
        ids = [c.criterion_id for c in v]
        if len(ids) != len(set(ids)):
            raise ValueError("acceptance_criteria criterion_ids must be unique")
        return v
