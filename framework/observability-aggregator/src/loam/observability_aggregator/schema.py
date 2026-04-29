"""Canonical Pydantic schema for the aggregator store.

Both ingest paths (in-process OTel SpanExporter and memory JSONL
tailer) normalise into these models. The store persists them; the
query API returns them.

Retention class is enforced at construction time per v1.1 R10:
  - normal: payload attributes preserved
  - derived-only: payload attributes dropped (inputs/outputs/etc.)
  - ephemeral: only minimal stub fields preserved
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class RetentionClass(str, Enum):
    NORMAL = "normal"
    DERIVED_ONLY = "derived-only"
    EPHEMERAL = "ephemeral"


# Attribute keys that count as "payload" — dropped under derived-only.
# Anything not in this set is structural metadata and is retained.
PAYLOAD_ATTRIBUTE_KEYS = frozenset(
    {
        "inputs",
        "outputs",
        "input",
        "output",
        "prompt",
        "completion",
        "raw_text",
        "content",
        "message",
        "messages",
        "rationale_text",
        "narrative",
    }
)


def apply_retention_class(
    attributes: dict[str, Any],
    retention_class: RetentionClass,
) -> dict[str, Any]:
    """Drop payload attributes per v1.1 R10 retention class.

    `normal` returns attributes unchanged.
    `derived-only` returns attributes minus payload keys.
    `ephemeral` returns only the retention-class marker (caller must
    ensure span/event itself is reduced to a stub elsewhere).
    """
    if retention_class is RetentionClass.NORMAL:
        return attributes
    if retention_class is RetentionClass.DERIVED_ONLY:
        return {k: v for k, v in attributes.items() if k not in PAYLOAD_ATTRIBUTE_KEYS}
    # EPHEMERAL: strip everything except the class marker.
    return {"loam.retention.class": RetentionClass.EPHEMERAL.value}


class SpanRecord(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: str | None = None
    name: str
    tracer_name: str
    component: str  # scope_of_work | primary_persona | objective_tracker | orchestrator | degradation | memory_system | aggregator | other
    kind: str = "INTERNAL"
    start_time_unix_nano: int
    end_time_unix_nano: int
    status: str = "UNSET"  # OK | ERROR | UNSET
    status_message: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    retention_class: RetentionClass = RetentionClass.NORMAL
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def duration_ns(self) -> int:
        return self.end_time_unix_nano - self.start_time_unix_nano

    @field_validator("retention_class", mode="before")
    @classmethod
    def _coerce_retention(cls, v):
        if isinstance(v, RetentionClass):
            return v
        if v is None:
            return RetentionClass.NORMAL
        try:
            return RetentionClass(v)
        except ValueError:
            return RetentionClass.NORMAL


class EventRecord(BaseModel):
    span_id: str
    trace_id: str
    name: str
    time_unix_nano: int
    attributes: dict[str, Any] = Field(default_factory=dict)
    retention_class: RetentionClass = RetentionClass.NORMAL
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("retention_class", mode="before")
    @classmethod
    def _coerce_retention(cls, v):
        if isinstance(v, RetentionClass):
            return v
        if v is None:
            return RetentionClass.NORMAL
        try:
            return RetentionClass(v)
        except ValueError:
            return RetentionClass.NORMAL


class TokenRecord(BaseModel):
    trace_id: str | None = None
    span_id: str | None = None
    prompt_name: str  # the v1.1 R12 grouping key (`loam.prompt.type`)
    model: str
    input_tokens: int
    output_tokens: int
    call_count: int = 1
    at_time: datetime
    scope_id: str | None = None
    component: str | None = None


class AuditRecord(BaseModel):
    at_time: datetime
    operation: str
    actor: str
    scope_id: str | None = None
    subject_uuid: str | None = None
    rationale: str
    extras: dict[str, Any] = Field(default_factory=dict)


# ---- helpers for component inference ----

# Map tracer-name prefix → component label.
# Mirrors the actual emission namespaces in the six OTel components.
TRACER_TO_COMPONENT = {
    "loam.scope_of_work": "scope_of_work",
    "loam.primary_persona": "primary_persona",
    "loam.objective_tracker": "objective_tracker",
    "loam.orchestrator": "orchestrator",
    "loam.degradation": "degradation",
    "loam.aggregator": "aggregator",
    "loam.memory": "memory_system",
}


def infer_component(tracer_name: str) -> str:
    if not tracer_name:
        return "unknown"
    for prefix, label in TRACER_TO_COMPONENT.items():
        if tracer_name == prefix or tracer_name.startswith(prefix + "."):
            return label
    return "other"


def extract_retention_class(attributes: dict[str, Any]) -> RetentionClass:
    """Read the `loam.retention.class` span attribute, defaulting to normal.

    Memory-system records use `retention_class` (no prefix) on the
    record root; OTel-emitting components use the `loam.retention.class`
    attribute convention. Both are honoured here.
    """
    raw = attributes.get("loam.retention.class") or attributes.get("retention_class")
    if not raw:
        return RetentionClass.NORMAL
    try:
        return RetentionClass(raw)
    except ValueError:
        return RetentionClass.NORMAL
