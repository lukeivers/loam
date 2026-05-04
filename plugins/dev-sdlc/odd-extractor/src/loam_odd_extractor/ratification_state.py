"""Ratification-state file shape + atomic loader/saver.

Per AC.BANDS.4 + AC.BANDS.7 + plan-doc §5 Surface #4 — ratification
state lives at ``<workspace>/.loam/extractions/<repo-id>/ratification-state.yaml``,
SEPARATE from Cycle 1's ``state.yaml``. Separation rationale (Surface
#4): Cycle 1's ``state.yaml`` tracks the four-stage extraction's
stage-completion flags; ratification is post-extraction; two state
files clearly delineate "ratification state for THIS draft" vs
"extraction state, persistent across draft refreshes".

Schema (schema_version=1):

.. code:: yaml

    schema_version: 1
    extraction_id: <repo-id>
    draft_path: <relative path under .loam/extractions/<repo-id>/>
    created_at: <ISO 8601>
    last_updated_at: <ISO 8601>
    pending_acs: [<ac_id>, ...]
    in_flight_action: <ac_id | null>
    completed_actions:
      - ac_id: <id>
        action_kind: promote | demote | edit | reject
        applied_at: <ISO 8601>
    pm_handle: <pm name>

D5 cross-session resume reads this file, identifies
``in_flight_action`` + ``pending_acs``, and re-surfaces the next
pending question via the PM.
"""

from __future__ import annotations

import datetime as _dt
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .errors import StageError


_RATIFICATION_STATE_SCHEMA_VERSION = 1


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


@dataclass
class CompletedAction:
    """Record of a ratification action applied during this draft's
    ratification cycle.

    Stored in :attr:`RatificationState.completed_actions` after
    :func:`apply_ratification_action` succeeds.
    """

    ac_id: str
    action_kind: str  # "promote" | "demote" | "edit" | "reject"
    applied_at: str  # ISO 8601 with timezone

    def to_dict(self) -> dict[str, str]:
        return {
            "ac_id": self.ac_id,
            "action_kind": self.action_kind,
            "applied_at": self.applied_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CompletedAction":
        return cls(
            ac_id=d["ac_id"],
            action_kind=d["action_kind"],
            applied_at=d["applied_at"],
        )


@dataclass
class RatificationState:
    """In-memory typed handle on ratification-state.yaml."""

    extraction_id: str
    draft_path: str
    pm_handle: str
    pending_acs: list[str] = field(default_factory=list)
    in_flight_action: str | None = None
    completed_actions: list[CompletedAction] = field(default_factory=list)
    created_at: str = ""
    last_updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": _RATIFICATION_STATE_SCHEMA_VERSION,
            "extraction_id": self.extraction_id,
            "draft_path": self.draft_path,
            "pm_handle": self.pm_handle,
            "pending_acs": list(self.pending_acs),
            "in_flight_action": self.in_flight_action,
            "completed_actions": [
                ca.to_dict() for ca in self.completed_actions
            ],
            "created_at": self.created_at,
            "last_updated_at": self.last_updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RatificationState":
        sv = d.get("schema_version")
        if sv != _RATIFICATION_STATE_SCHEMA_VERSION:
            raise StageError(
                f"ratification-state.yaml: unexpected schema_version="
                f"{sv!r}; expected {_RATIFICATION_STATE_SCHEMA_VERSION}"
            )
        return cls(
            extraction_id=d["extraction_id"],
            draft_path=d["draft_path"],
            pm_handle=d["pm_handle"],
            pending_acs=list(d.get("pending_acs") or []),
            in_flight_action=d.get("in_flight_action"),
            completed_actions=[
                CompletedAction.from_dict(ca)
                for ca in (d.get("completed_actions") or [])
            ],
            created_at=d.get("created_at", ""),
            last_updated_at=d.get("last_updated_at", ""),
        )


def ratification_state_path(extraction_dir_: Path) -> Path:
    """``<extraction_dir>/ratification-state.yaml``."""
    return extraction_dir_ / "ratification-state.yaml"


def load_ratification_state(
    extraction_dir_: Path,
) -> RatificationState | None:
    """Return the typed state, or ``None`` if no ratification has
    been started for this extraction yet.
    """
    p = ratification_state_path(extraction_dir_)
    if not p.exists():
        return None
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise StageError(
            f"ratification-state.yaml at {p}: top-level must be a "
            f"mapping; got {type(raw).__name__}"
        )
    return RatificationState.from_dict(raw)


def save_ratification_state(
    extraction_dir_: Path,
    state: RatificationState,
    *,
    timestamp: str | None = None,
) -> Path:
    """Atomically write ratification-state.yaml via tmp+rename.

    Mirrors per-project-pm's ``atomic_write_yaml`` convention.
    Bumps :attr:`RatificationState.last_updated_at` (and
    :attr:`created_at` on first write) before serializing.
    """
    p = ratification_state_path(extraction_dir_)
    p.parent.mkdir(parents=True, exist_ok=True)

    now = timestamp if timestamp is not None else _now_iso()
    if not state.created_at:
        state.created_at = now
    state.last_updated_at = now

    payload = state.to_dict()

    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{p.name}.",
        suffix=".tmp",
        dir=str(p.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(payload, fh, sort_keys=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, p)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return p


def initialise_ratification_state(
    extraction_dir_: Path,
    *,
    extraction_id: str,
    draft_path: str,
    pm_handle: str,
    pending_acs: list[str],
    timestamp: str | None = None,
) -> RatificationState:
    """First-write helper: create + save a fresh ratification state.

    Idempotent if invoked against an existing state file: returns the
    existing state unchanged (caller may :func:`save_ratification_state`
    after mutating).
    """
    existing = load_ratification_state(extraction_dir_)
    if existing is not None:
        return existing
    state = RatificationState(
        extraction_id=extraction_id,
        draft_path=draft_path,
        pm_handle=pm_handle,
        pending_acs=list(pending_acs),
        in_flight_action=None,
        completed_actions=[],
    )
    save_ratification_state(extraction_dir_, state, timestamp=timestamp)
    return state
