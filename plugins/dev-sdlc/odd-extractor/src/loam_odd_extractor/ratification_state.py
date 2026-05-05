"""Ratification-state file shape + atomic loader/saver.

Per AC.BANDS.4 + AC.BANDS.7 + plan-doc §5 Surface #4 — ratification
state lives at ``<workspace>/.loam/extractions/<repo-id>/ratification-state.yaml``,
SEPARATE from Cycle 1's ``state.yaml``.

Per v0.2.3 Cycle 2 (sub-plan-doc §3 AC.OBJRAT.6) — schema_version
bumped to 2 with additive ``altitude_index`` + ``pending_targets``
fields. v1 → v2 auto-migration on read with atomic
``ratification-state.yaml.v1.bak`` backup. v1 callers transparent —
the ``RatificationStateV2`` exposes back-compat reads of v1 fields
for ``altitude="banded_ac"`` legacy targets.

Schema (schema_version=2):

.. code:: yaml

    schema_version: 2
    extraction_id: <repo-id>
    draft_path: <relative path under .loam/extractions/<repo-id>/>
    created_at: <ISO 8601>
    last_updated_at: <ISO 8601>
    pending_acs: [<id>, ...]               # v0.1.8 back-compat list
    in_flight_action: <id | null>          # v0.1.8 back-compat
    completed_actions:
      - ac_id: <id>
        action_kind: promote | demote | edit | reject
        applied_at: <ISO 8601>
    pm_handle: <pm name>
    # v0.2.3 Cycle 2 additive fields:
    altitude_index: {<id>: <altitude>}     # banded_ac | objective | ...
    pending_targets:
      - target_id: <id>
        altitude: banded_ac | objective | constraint | capability
    in_flight_target: <id | null>

D5 cross-session resume reads this file, identifies
``in_flight_action`` + ``pending_targets``, and re-surfaces the next
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


_RATIFICATION_STATE_SCHEMA_VERSION = 2
_RATIFICATION_STATE_LEGACY_SCHEMA_VERSION = 1


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
    """In-memory typed handle on ratification-state.yaml (v0.1.8 shape).

    Per v0.2.3 Cycle 2 — preserved unchanged for callers that want the
    legacy v1 surface; the loader returns :class:`RatificationStateV2`
    on read by default. Construct an instance via this class only when
    direct v1 typing is needed (most callers should use V2).
    """

    extraction_id: str
    draft_path: str
    pm_handle: str
    pending_acs: list[str] = field(default_factory=list)
    in_flight_action: str | None = None
    completed_actions: list[CompletedAction] = field(default_factory=list)
    created_at: str = ""
    last_updated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        # NB: still writes schema_version=2 — v0.2.3 Cycle 2 makes v2
        # authoritative; this dataclass is preserved as a legacy
        # surface, but any save-cycle through it lands as v2.
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
            # v2 additive fields — derived from v1 surface as legacy
            # banded-AC altitudes.
            "altitude_index": {
                ac_id: "banded_ac" for ac_id in self.pending_acs
            },
            "pending_targets": [
                {"target_id": ac_id, "altitude": "banded_ac"}
                for ac_id in self.pending_acs
            ],
            "in_flight_target": self.in_flight_action,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RatificationState":
        sv = d.get("schema_version")
        if sv not in (_RATIFICATION_STATE_SCHEMA_VERSION, _RATIFICATION_STATE_LEGACY_SCHEMA_VERSION):
            raise StageError(
                f"ratification-state.yaml: unexpected schema_version="
                f"{sv!r}; expected {_RATIFICATION_STATE_LEGACY_SCHEMA_VERSION} "
                f"or {_RATIFICATION_STATE_SCHEMA_VERSION}"
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


# v0.2.3 Cycle 2 — altitude-tagged extension.

_ALLOWED_ALTITUDES = {"banded_ac", "objective", "constraint", "capability"}


@dataclass
class PendingTarget:
    """One pending-target row, altitude-tagged.

    Per v0.2.3 Cycle 2 (sub-plan-doc §3 AC.OBJRAT.6) — replaces the
    untyped string-ID in ``pending_acs`` for new-style ratifications.
    Legacy v0.1.8 reads still mirror to ``pending_acs`` for back-compat.
    """

    target_id: str
    altitude: str  # one of _ALLOWED_ALTITUDES

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_id": self.target_id,
            "altitude": self.altitude,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PendingTarget":
        altitude = d.get("altitude", "banded_ac")
        if altitude not in _ALLOWED_ALTITUDES:
            raise StageError(
                f"PendingTarget.from_dict: altitude {altitude!r} not "
                f"in {_ALLOWED_ALTITUDES}"
            )
        return cls(
            target_id=d["target_id"],
            altitude=altitude,
        )


@dataclass
class RatificationStateV2(RatificationState):
    """v0.2.3 schema_version=2 ratification state.

    Extends :class:`RatificationState` (v0.1.8 surface) additively
    with ``altitude_index`` + ``pending_targets`` + ``in_flight_target``.
    The v0.1.8 ``pending_acs`` + ``in_flight_action`` fields are
    mirrored from / to ``pending_targets`` + ``in_flight_target`` so
    legacy code reading the v1 surface continues to work.
    """

    altitude_index: dict[str, str] = field(default_factory=dict)
    pending_targets: list[PendingTarget] = field(default_factory=list)
    in_flight_target: str | None = None

    def to_dict(self) -> dict[str, Any]:
        # Sync v1 ↔ v2 surfaces before serializing.
        # pending_acs derives from pending_targets (v2 authoritative).
        v1_pending = [pt.target_id for pt in self.pending_targets]
        if v1_pending != self.pending_acs:
            self.pending_acs = v1_pending
        if self.in_flight_target != self.in_flight_action:
            self.in_flight_action = self.in_flight_target
        # Index keeps an entry per pending target.
        idx = dict(self.altitude_index)
        for pt in self.pending_targets:
            idx[pt.target_id] = pt.altitude
        self.altitude_index = idx

        return {
            "schema_version": _RATIFICATION_STATE_SCHEMA_VERSION,
            "extraction_id": self.extraction_id,
            "draft_path": self.draft_path,
            "pm_handle": self.pm_handle,
            # v0.1.8 surface (back-compat).
            "pending_acs": list(self.pending_acs),
            "in_flight_action": self.in_flight_action,
            "completed_actions": [
                ca.to_dict() for ca in self.completed_actions
            ],
            "created_at": self.created_at,
            "last_updated_at": self.last_updated_at,
            # v0.2.3 Cycle 2 additive.
            "altitude_index": dict(self.altitude_index),
            "pending_targets": [
                pt.to_dict() for pt in self.pending_targets
            ],
            "in_flight_target": self.in_flight_target,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "RatificationStateV2":
        sv = d.get("schema_version")
        if sv == _RATIFICATION_STATE_LEGACY_SCHEMA_VERSION:
            # Auto-migrate. Every v1 pending_acs entry becomes a
            # banded_ac-altitude pending target.
            v1_pending = list(d.get("pending_acs") or [])
            altitude_index = {ac_id: "banded_ac" for ac_id in v1_pending}
            pending_targets = [
                PendingTarget(target_id=ac_id, altitude="banded_ac")
                for ac_id in v1_pending
            ]
            in_flight_target = d.get("in_flight_action")
            return cls(
                extraction_id=d["extraction_id"],
                draft_path=d["draft_path"],
                pm_handle=d["pm_handle"],
                pending_acs=v1_pending,
                in_flight_action=d.get("in_flight_action"),
                completed_actions=[
                    CompletedAction.from_dict(ca)
                    for ca in (d.get("completed_actions") or [])
                ],
                created_at=d.get("created_at", ""),
                last_updated_at=d.get("last_updated_at", ""),
                altitude_index=altitude_index,
                pending_targets=pending_targets,
                in_flight_target=in_flight_target,
            )
        if sv == _RATIFICATION_STATE_SCHEMA_VERSION:
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
                altitude_index=dict(d.get("altitude_index") or {}),
                pending_targets=[
                    PendingTarget.from_dict(pt)
                    for pt in (d.get("pending_targets") or [])
                ],
                in_flight_target=d.get("in_flight_target"),
            )
        raise StageError(
            f"ratification-state.yaml: unexpected schema_version="
            f"{sv!r}; expected {_RATIFICATION_STATE_LEGACY_SCHEMA_VERSION} "
            f"or {_RATIFICATION_STATE_SCHEMA_VERSION}"
        )


def ratification_state_path(extraction_dir_: Path) -> Path:
    """``<extraction_dir>/ratification-state.yaml``."""
    return extraction_dir_ / "ratification-state.yaml"


def load_ratification_state(
    extraction_dir_: Path,
) -> "RatificationStateV2 | None":
    """Return the typed state, or ``None`` if no ratification has
    been started for this extraction yet.

    Per AC.OBJRAT.6 — single migrating loader. v1 files trigger
    auto-migration: an atomic ``ratification-state.yaml.v1.bak``
    backup is written before the v2 payload is rewritten in place.
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
    sv = raw.get("schema_version")
    if sv == _RATIFICATION_STATE_LEGACY_SCHEMA_VERSION:
        # v1 → v2 atomic migration.
        backup_path = p.with_suffix(".yaml.v1.bak")
        # Atomic backup: copy raw bytes to .v1.bak via tmp+rename.
        _atomic_copy(p, backup_path)
        state = RatificationStateV2.from_dict(raw)
        # Persist v2 payload in place.
        save_ratification_state(extraction_dir_, state)
        return state
    return RatificationStateV2.from_dict(raw)


def _atomic_copy(src: Path, dst: Path) -> None:
    """Atomically copy ``src`` to ``dst`` via tmp+rename."""
    payload = src.read_bytes()
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{dst.name}.",
        suffix=".tmp",
        dir=str(dst.parent),
    )
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, dst)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def save_ratification_state(
    extraction_dir_: Path,
    state: "RatificationState | RatificationStateV2",
    *,
    timestamp: str | None = None,
) -> Path:
    """Atomically write ratification-state.yaml via tmp+rename.

    Mirrors per-project-pm's ``atomic_write_yaml`` convention.
    Bumps :attr:`RatificationState.last_updated_at` (and
    :attr:`created_at` on first write) before serializing.

    Accepts both v0.1.8 :class:`RatificationState` and v0.2.3
    :class:`RatificationStateV2`; the latter writes schema_version=2.
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
) -> "RatificationStateV2":
    """First-write helper: create + save a fresh ratification state.

    Idempotent if invoked against an existing state file: returns the
    existing state unchanged (caller may :func:`save_ratification_state`
    after mutating). Per v0.2.3 Cycle 2 (AC.OBJRAT.6) — fresh writes
    use the v2 schema; legacy ``pending_acs`` argument is retained
    for v0.1.8 source-compat (every entry tagged ``"banded_ac"``).
    """
    existing = load_ratification_state(extraction_dir_)
    if existing is not None:
        return existing
    state = RatificationStateV2(
        extraction_id=extraction_id,
        draft_path=draft_path,
        pm_handle=pm_handle,
        pending_acs=list(pending_acs),
        in_flight_action=None,
        completed_actions=[],
        altitude_index={ac_id: "banded_ac" for ac_id in pending_acs},
        pending_targets=[
            PendingTarget(target_id=ac_id, altitude="banded_ac")
            for ac_id in pending_acs
        ],
        in_flight_target=None,
    )
    save_ratification_state(extraction_dir_, state, timestamp=timestamp)
    return state
