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
    # D-migration D.2 (amendment #63): personas live under
    # <ws>/workspace/personas/ post-D.2.
    from loam.workspace_bootstrap.workspace_paths import (
        personas_dir as _personas_dir,
    )

    workspace = Path(workspace_root)
    personas = _personas_dir(workspace)
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
