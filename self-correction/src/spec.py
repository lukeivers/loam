"""Pydantic schemas for self-correction.

Four record types enforce the four-part protocol structurally:

    FailureClassIdentified  →  InstanceFixed  →  CauseDiagnosed  →  StructuralRemedyApplied

Records are persisted any-order but order-preserving: the `at`
timestamp on each record tells the real story (CR10).

Every model uses `extra="forbid"` + `frozen=True` — structural
impossibility pattern cloned from safety-layer/src/events.py and
reversibility-primitive/src/spec.py.

Error codes (reserved range -32070..-32079 — brief hard constraint):

    -32070 CORRECTION_INCOMPLETE_RECORDS
        Terminal-transition pre-check refusing `completed` without all
        four record types in `correction_episode_records`.

    -32071..-32079 reserved for future.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---- error codes -----------------------------------------------------

IPC_CORRECTION_INCOMPLETE_RECORDS = -32070


# ---- enums -----------------------------------------------------------


class TriggerSource(str, Enum):
    scope_failure = "scope_failure"
    otel_anomaly = "otel_anomaly"
    review_verdict = "review_verdict"
    user_reported = "user_reported"


class EpisodeState(str, Enum):
    running = "running"
    completed = "completed"
    escalated = "escalated"
    refused = "refused"


class RecordType(str, Enum):
    """The four record types required for `completed` transition (CR7)."""

    failure_class = "failure_class"
    instance_fix = "instance_fix"
    cause_diagnosed = "cause_diagnosed"
    structural_remedy = "structural_remedy"


# The set tested against `correction_episode_records` at terminal
# transition. Changing this set is a structural change to the four-part
# protocol — flag in review.
REQUIRED_RECORD_TYPES: frozenset[RecordType] = frozenset(
    {
        RecordType.failure_class,
        RecordType.instance_fix,
        RecordType.cause_diagnosed,
        RecordType.structural_remedy,
    }
)


# ---- helpers ---------------------------------------------------------


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---- CorrectionTrigger ----------------------------------------------


class CorrectionTrigger(BaseModel):
    """Normalised intake record for any of the four detection surfaces.

    All four sources converge here before dedup/bounds/open. Caller
    identity (for `user_reported`) is enforced upstream at the IPC
    boundary (ruling #4); this record is transport-agnostic.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    trigger_id: str = Field(min_length=1)
    source: TriggerSource
    scope_id: str | None = None
    trace_id: str | None = None
    failure_class_hint: str | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    received_at: str = Field(default_factory=iso_now)
    reporter: str | None = None
    # For dedup: SHA-256(scope_id, source, normalised_reason). Populated
    # by the normaliser; deterministic given the inputs above.
    dedup_key: str | None = None


# ---- CorrectionEpisode -----------------------------------------------


class CorrectionEpisode(BaseModel):
    """Sidecar record for a correction-in-progress."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    episode_id: str = Field(min_length=1)
    trigger_id: str = Field(min_length=1)
    correction_scope_id: str | None = None  # None only when `refused` pre-open.
    parent_correction_id: str | None = None  # depth walk
    failure_class: str = Field(min_length=1)
    state: EpisodeState
    opened_at: str = Field(default_factory=iso_now)
    closed_at: str | None = None
    refusal_reason: str | None = None


# ---- four record types -----------------------------------------------


class _RecordBase(BaseModel):
    """Shared frozen-Pydantic base for all four record types."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    episode_id: str = Field(min_length=1)
    at: str = Field(default_factory=iso_now)


class FailureClassIdentified(_RecordBase):
    """Part 1 of the four-part protocol — name the failure class.

    Eve-inference #6 field names: `class_name` + `rationale`. Challenge
    would be to rename if primary-persona authoring patterns differ.
    """

    record_type: Literal[RecordType.failure_class] = RecordType.failure_class
    class_name: str = Field(min_length=1)
    rationale: str = Field(default="")


class InstanceFixed(_RecordBase):
    """Part 2 — describe the specific fix applied right now."""

    record_type: Literal[RecordType.instance_fix] = RecordType.instance_fix
    fix_description: str = Field(min_length=1)
    affected_scope_id: str | None = None


class CauseDiagnosed(_RecordBase):
    """Part 3 — diagnose the systemic cause."""

    record_type: Literal[RecordType.cause_diagnosed] = RecordType.cause_diagnosed
    root_cause: str = Field(min_length=1)


class StructuralRemedyApplied(_RecordBase):
    """Part 4 — describe the change that closes the class."""

    record_type: Literal[RecordType.structural_remedy] = RecordType.structural_remedy
    change_description: str = Field(min_length=1)
    artefact_path: str | None = None


# Union of payload shapes for record-part IPC validation.
AnyRecord = (
    FailureClassIdentified
    | InstanceFixed
    | CauseDiagnosed
    | StructuralRemedyApplied
)


RECORD_MODELS: dict[RecordType, type[_RecordBase]] = {
    RecordType.failure_class: FailureClassIdentified,
    RecordType.instance_fix: InstanceFixed,
    RecordType.cause_diagnosed: CauseDiagnosed,
    RecordType.structural_remedy: StructuralRemedyApplied,
}


# ---- cascade escalation payloads (non-persisted, for notification) ---


class CorrectionCascadeEscalated(BaseModel):
    """One-on-one-channel notification payload when a bound trips (CR15)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["depth_cap", "same_class_cascade"]
    reason: str
    failure_class: str | None = None
    parent_correction_id: str | None = None
    depth: int | None = None
    window_count: int | None = None
