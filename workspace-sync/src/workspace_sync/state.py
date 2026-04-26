"""state.yaml + workspace-local audit-path resolution (B-shape).

Salvaged from ``self-upgrade/src/self_upgrade/state.py`` with the
following caller-side rebadgings:

  - ``UpgradeStatus`` → ``SyncStatus`` (terminal status of a sync run).
  - ``StateRecord.upgrade_tag`` → ``StateRecord.sync_ref`` (commit-SHA
    or git ref, the B-mode equivalent of A-mode's release-tag).
  - ``state_yaml_path`` returns ``<workspace>/.pos/sync/state.yaml``
    (was ``.pos/upgrade/state.yaml``).
  - ``audit_yaml_path`` returns ``<workspace>/.pos/sync/<ref>/audit.yaml``
    (was ``.pos/upgrade/<tag>/audit.yaml``).

AC.WS.5 mandates the new audit path; AC.WS.8 mandates state.yaml under
the same ``.pos/sync/`` namespace. Self-upgrade's ``state.py`` keeps
the ``.pos/upgrade/`` shape unchanged (Hard Constraint #1).

Schema:

.. code-block:: yaml

    sync_ref:               "abc123def..."   # 7-40 char SHA or ref
    timestamp:              "2026-04-26T13:30:00+00:00"
    audit_path:             "/abs/.pos/sync/<ref>/audit.yaml"
    total_conflicts:        3
    resolved_count:         3
    deferred_count:         0
    cumulative_tokens_used: 1200
    status:                 "success"
    halt_reason:            null

``status`` is one of ``success`` / ``failure`` / ``partial``:

- ``success`` — every conflict resolved without raising.
- ``failure`` — the helper raised ``BudgetExhausted`` or
  ``ResolverFailure``; the run aborted mid-stream.
- ``partial`` — the helper completed without raising but some
  conflicts remained PENDING (e.g. binary files the resolver could
  not read).

The state.yaml is read by the next workspace-sync invocation against
the same workspace + ref; if the prior audit's already-resolved
entries cover the current ConflictReport's PENDING set, the resolver
is not re-invoked (the helper's existing
``if entry.resolution is not Resolution.PENDING: continue`` branch
fires for every entry — convergent idempotency per AC.WS.8).
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field


class SyncStatus(str, Enum):
    """Terminal status of a workspace-sync execution."""

    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


class StateRecord(BaseModel):
    """Workspace-local sync state.yaml schema."""

    model_config = ConfigDict(extra="forbid")

    sync_ref: str
    timestamp: str
    audit_path: str
    total_conflicts: int = Field(ge=0)
    resolved_count: int = Field(ge=0)
    deferred_count: int = Field(ge=0)
    cumulative_tokens_used: int = Field(ge=0)
    status: SyncStatus
    halt_reason: str | None = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_yaml_path(workspace_root: Path) -> Path:
    """Return ``<workspace_root>/.pos/sync/state.yaml``."""
    return Path(workspace_root) / ".pos" / "sync" / "state.yaml"


def audit_yaml_path(workspace_root: Path, ref: str) -> Path:
    """Return ``<workspace_root>/.pos/sync/<ref>/audit.yaml``."""
    return Path(workspace_root) / ".pos" / "sync" / ref / "audit.yaml"


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
    sync_ref: str,
    workspace_root: Path,
    total_conflicts: int,
    resolved_count: int,
    deferred_count: int,
    cumulative_tokens_used: int,
    status: SyncStatus,
    halt_reason: str | None = None,
    timestamp: str | None = None,
) -> StateRecord:
    """Build a StateRecord with a freshly-stamped ISO-8601 timestamp.

    Separates record construction from disk I/O so callers can compose
    additional context (e.g. tests asserting individual fields) before
    persisting.
    """
    return StateRecord(
        sync_ref=sync_ref,
        timestamp=timestamp or _now_iso(),
        audit_path=str(audit_yaml_path(workspace_root, sync_ref).resolve()),
        total_conflicts=total_conflicts,
        resolved_count=resolved_count,
        deferred_count=deferred_count,
        cumulative_tokens_used=cumulative_tokens_used,
        status=status,
        halt_reason=halt_reason,
    )
