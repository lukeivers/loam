"""Workspace-local sync state record (D-migration D.3 shape).

D-migration D.3 (amendment #64) — the pre-D.3 ``StateRecord`` model
carried fields shaped around the bespoke resolve→stage→apply pipeline
(``cumulative_tokens_used``, ``halt_reason``, ``deferred_count``,
etc.). Under D.3's git-merge architecture those fields no longer
carry information — the merge mechanics are git's; the per-run
audit lives in ``git log``; resolver token usage (when the fallback
fires) is already captured per-verdict in
``<ws>/workspace/.pos/sync/resolver-runs/<sha>/<path>.yaml``.

The simplified ``SyncState`` records:

  - ``last_synced_sha`` — git SHA of canonical's HEAD that was
    merged into framework/HEAD (or framework/HEAD itself when
    the sync was a no-op idempotency hit).
  - ``last_synced_at`` — ISO-8601 UTC timestamp.
  - ``last_branch`` — the framework/ branch that was advanced.
  - ``last_outcome`` — the terminal outcome
    (``up-to-date`` / ``fast-forward`` / ``merged`` /
    ``conflict-fallback`` / ``resolver-halted``).

Path: ``<workspace>/workspace/.pos/sync/state.yaml``. The
workspace-state directory ships under ``workspace/`` per D.2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict


class SyncOutcome(str, Enum):
    """Terminal outcome of a workspace-sync execution under D.3."""

    UP_TO_DATE = "up-to-date"
    FAST_FORWARD = "fast-forward"
    MERGED = "merged"
    CONFLICT_FALLBACK = "conflict-fallback"
    RESOLVER_HALTED = "resolver-halted"


class SyncState(BaseModel):
    """Workspace-local sync state.yaml schema (D.3 shape)."""

    model_config = ConfigDict(extra="forbid")

    last_synced_sha: str
    last_synced_at: str
    last_branch: str
    last_outcome: SyncOutcome


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_yaml_path(workspace_root: Path) -> Path:
    """Return ``<workspace_root>/workspace/.pos/sync/state.yaml``.

    D-migration D.2 (amendment #63): workspace-state under
    ``<workspace>/workspace/.pos/``. D.3 keeps the same path.
    """
    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "sync" / "state.yaml"


def load_state(workspace_root: Path) -> SyncState | None:
    """Load the workspace's state.yaml; return None if absent.

    Raises Pydantic validation error on a malformed file (the file
    is framework-written, so a malformed file is a bug worth
    surfacing, not a soft-fail).
    """
    p = state_yaml_path(workspace_root)
    if not p.exists():
        return None
    raw = yaml.safe_load(p.read_text()) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{p}: top-level must be a mapping")
    return SyncState.model_validate(raw)


def save_state(record: SyncState, workspace_root: Path) -> Path:
    """Write the state.yaml for ``workspace_root``. Returns the path."""
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
