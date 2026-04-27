"""Clause-(h) state.yaml + workspace-local audit-path resolution.

Per amendment #54 plan §2 + §4 (AC.H.5 + AC.H.8): the clause-(h)
audit lands at ``<workspace>/.pos/upgrade/<tag>/audit.yaml`` and a
sibling ``<workspace>/.pos/upgrade/state.yaml`` records the
upgrade-state for convergent idempotency on re-run. Amendment #55
(BB-feat bugfix) lands the writer + read helper that #54's
implementation omitted.

Schema:

.. code-block:: yaml

    upgrade_tag:           "pos-v2-v0.2.0"
    timestamp:             "2026-04-26T13:30:00+00:00"
    audit_path:            "/abs/path/to/.pos/upgrade/<tag>/audit.yaml"
    total_conflicts:       3
    resolved_count:        3
    deferred_count:        0
    cumulative_tokens_used: 1200
    status:                "success"
    halt_reason:           null

``status`` is one of ``success`` / ``failure`` / ``partial``:

- ``success`` — every conflict resolved without raising.
- ``failure`` — the helper raised ``BudgetExhausted`` or
  ``ResolverFailure``; the run aborted mid-stream.
- ``partial`` — the helper completed without raising but some
  conflicts remained PENDING (e.g. binary files the resolver
  could not read).

The state.yaml is read by the next clause-(h) invocation against
the same workspace + tag; if the prior audit's already-resolved
entries cover the current ConflictReport's PENDING set, the
resolver is not re-invoked (the helper's existing
``if entry.resolution is not Resolution.PENDING: continue`` branch
fires for every entry).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class UpgradeStatus(str, Enum):
    """Terminal status of a clause-(h) execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class StateRecord(BaseModel):
    """Workspace-local clause-(h) state.yaml schema."""

    model_config = ConfigDict(extra="forbid")

    upgrade_tag: str
    timestamp: str
    audit_path: str
    total_conflicts: int = Field(ge=0)
    resolved_count: int = Field(ge=0)
    deferred_count: int = Field(ge=0)
    cumulative_tokens_used: int = Field(ge=0)
    status: UpgradeStatus
    halt_reason: str | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_yaml_path(workspace_root: Path) -> Path:
    """Return ``<workspace_root>/workspace/.pos/upgrade/state.yaml``.

    D-migration D.2 (amendment #63): workspace-state under
    ``<workspace>/workspace/.pos/``.
    """
    from workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "upgrade" / "state.yaml"


def audit_yaml_path(workspace_root: Path, tag: str) -> Path:
    """Return ``<workspace_root>/workspace/.pos/upgrade/<tag>/audit.yaml``.

    D-migration D.2 (amendment #63): workspace-state under
    ``<workspace>/workspace/.pos/``.
    """
    from workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "upgrade" / tag / "audit.yaml"


def load_state(workspace_root: Path) -> StateRecord | None:
    """Load + validate the workspace's state.yaml; return None if absent.

    Raises Pydantic validation error on a malformed file (the file is
    framework-written, so a malformed file is a bug worth surfacing,
    not a soft-fail).
    """
    p = state_yaml_path(workspace_root)
    if not p.exists():
        return None
    raw = yaml.safe_load(p.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{p}: top-level must be a mapping")
    return StateRecord.model_validate(raw)


def save_state(record: StateRecord, workspace_root: Path) -> Path:
    """Write the state.yaml for *workspace_root*. Returns the path."""
    p = state_yaml_path(workspace_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        yaml.safe_dump(
            record.model_dump(mode="json"),
            default_flow_style=False,
            sort_keys=False,
        )
    )
    return p


def make_state_record(
    *,
    upgrade_tag: str,
    workspace_root: Path,
    total_conflicts: int,
    resolved_count: int,
    deferred_count: int,
    cumulative_tokens_used: int,
    status: UpgradeStatus,
    halt_reason: str | None = None,
    timestamp: str | None = None,
) -> StateRecord:
    """Build a StateRecord with a freshly-stamped ISO-8601 timestamp.

    Separates record construction from disk I/O so callers can compose
    additional context (e.g. tests asserting individual fields) before
    persisting.
    """
    return StateRecord(
        upgrade_tag=upgrade_tag,
        timestamp=timestamp or _now_iso(),
        audit_path=str(audit_yaml_path(workspace_root, upgrade_tag).resolve()),
        total_conflicts=total_conflicts,
        resolved_count=resolved_count,
        deferred_count=deferred_count,
        cumulative_tokens_used=cumulative_tokens_used,
        status=status,
        halt_reason=halt_reason,
    )
