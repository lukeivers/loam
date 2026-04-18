"""Retirement (D8).

Retired personas move to `personas/_retired/<handle>-<timestamp>/`.
The active loader ignores anything under `_retired/`. Memory and
scope references to the retired persona by handle continue to
resolve via the history (the directory is preserved, just moved).
Retirement emits an auditable event naming the persona and the reason.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from . import observability as obs


class RetirementReason(str, Enum):
    user_initiated = "user_initiated"
    never_acknowledged = "never_acknowledged"  # pending intro stayed pending too long
    workspace_policy = "workspace_policy"  # framework/workspace-level decision
    superseded = "superseded"  # replaced by a better-authored persona


@dataclass(frozen=True)
class RetirementRecord:
    handle: str
    reason: RetirementReason
    from_dir: Path
    to_dir: Path
    retired_at: str


def retire_persona(
    *,
    workspace_root: str | Path,
    handle: str,
    reason: RetirementReason,
) -> RetirementRecord:
    """Move `personas/<handle>/` to `personas/_retired/<handle>-<ts>/`.

    Raises `FileNotFoundError` if the persona directory does not
    exist. Emits an OTel event with the handle and reason (D9).
    """
    workspace = Path(workspace_root)
    personas = workspace / "personas"
    source = personas / handle
    if not source.exists() or not source.is_dir():
        raise FileNotFoundError(f"persona directory not found: {source}")

    retired_root = personas / "_retired"
    retired_root.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = retired_root / f"{handle}-{ts}"
    if target.exists():
        # Collision on same-second retire (unlikely, but handle it):
        target = retired_root / f"{handle}-{ts}-{source.stat().st_ino}"

    shutil.move(str(source), str(target))

    obs.retirement_event(handle=handle, reason=reason.value)

    return RetirementRecord(
        handle=handle,
        reason=reason,
        from_dir=source,
        to_dir=target,
        retired_at=datetime.now(timezone.utc).isoformat(),
    )
