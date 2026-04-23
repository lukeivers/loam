"""Pydantic record models + structural_hash helper.

These are the deterministic surfaces the safety store persists and the
gates consult. `structural_hash(spec)` binds approval decisions to the
content-identity of a scope spec — see the "Eve-inferences challenged"
section of the build report.

ScopeSpec.structural_hash() does NOT exist on pos-v2 (verified by grep
of scope-of-work/src/). The proposal flagged this as Eve-inference #7.
Rather than halt-and-signal and wait, the alternative the builder
chose (and documented here) is to compute the hash INSIDE the safety
layer — `structural_hash(spec)` takes a frozen ScopeSpec, dumps it to
canonical JSON via `model_dump_json(...)` (Pydantic's own deterministic
serialisation), and SHA-256s the result. This is a pure consumer of the
sealed ScopeSpec surface. No amendment to scope-of-work. If Luke
wishes the hash as a first-class ScopeSpec method later, that is a
scope-of-work amendment to land separately.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from scope_of_work import ScopeSpec


class KillLevel(str, Enum):
    scope = "scope"
    session = "session"
    system = "system"


class AskDecisionRecord(BaseModel):
    """One persisted ask-gate decision.

    Binds to `scope_spec_hash` so approvals do not extend across spec
    mutations (A14). `expires_at` is an ISO-8601 timestamp; expiry is
    checked at gate-time, not by a background sweep.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    scope_id: str | None = None
    scope_spec_hash: str
    action_classes: tuple[str, ...]
    state: Literal["approved", "refused", "pending", "expired"]
    decided_at: str
    expires_at: str | None
    decided_by: str = "user"
    reasoning: str | None = None


class KillEventRecord(BaseModel):
    """Audit row for a single kill issuance.

    Amendment #19 adds the optional ``failed_scope_ids`` field to
    distinguish "nothing to cancel" from "per-scope cancel raised" on
    system-kill; the field defaults to ``()`` so existing callers are
    unaffected (backwards-compatible additive extension; no shape
    change). See ``docs/rebuild/plans/amendment-19-s1-silent-excepts.md``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    level: KillLevel
    reason: str
    source: Literal["cli", "persona", "ipc"]
    scope_id: str | None = None
    issued_at: str
    cancelled_scope_ids: tuple[str, ...] = ()
    failed_scope_ids: tuple[str, ...] = ()


class SystemKillStateRecord(BaseModel):
    """Terminal system-kill record read by the next orchestrator bootstrap.

    When a matching `cleared_at` row exists, the next bootstrap is
    permitted to activate scopes again. Otherwise it refuses to run
    `activate_scope` and emits `pos.safety.system_kill_block_activation`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    killed_at: str
    reason: str
    source: Literal["cli", "persona", "ipc"]
    cleared_at: str | None = None
    cleared_reason: str | None = None


# ---- structural hash ---------------------------------------------------


def structural_hash(spec: ScopeSpec) -> str:
    """Deterministic content-identity hash of a ScopeSpec.

    The hash binds an approval decision to the exact spec shape the
    user approved. Any spec mutation (different constraint, different
    budget, different reversibility_class) produces a different hash
    and re-fires the gate (A14).

    Uses Pydantic's canonical JSON serialisation — every field in
    ScopeSpec is frozen and Pydantic-validated, so the JSON output is
    reproducible across runs.
    """
    payload = spec.model_dump_json()
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def iso_now() -> str:
    """UTC-ISO timestamp. One place so tests can monkeypatch clock."""
    return datetime.now(timezone.utc).isoformat()
