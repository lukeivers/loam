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

"""Compaction survival — replay-from-authoritative-sources (D4).

After compaction, persona identity, authority boundary, current scope
context, pending decisions, and recent corrections are re-injected
deterministically on the first post-compaction `UserPromptSubmit`.

The Python Agent SDK has no `PostCompact` hook, so v1 uses a
`PreCompact` flag + `UserPromptSubmit` detection workaround
(Luke-approved, brief §"Luke's decisions").

Flow:
1. `PreCompact` hook calls `mark_precompact(flag_dir)` before the
   model compacts.
2. After compaction, the first `UserPromptSubmit` calls
   `consume_survival_payload(...)` — if the flag is present, the
   survival block is assembled from authoritative sources (loaded
   contract, scope-of-work `list()`, memory recent corrections) and
   the flag is cleared.
3. Subsequent turns detect no flag and inject nothing extra.

The five-item canonical survival list (v1.0 session-resilience):
    1. persona identity (given_name, handle)
    2. authority boundary (tier actions)
    3. current scope context (active + pending scopes)
    4. pending decisions (pending-extension scopes)
    5. recent corrections (top-N from memory)
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from loam.scope_of_work.runtime import ScopeRuntime  # type: ignore[import-not-found]

from .contract import PersonaContract
from .loader import LoadedPersona


# The canonical five-item survival list. Named so tests can import
# and reference it without duplicating the names.
SURVIVAL_LIST: tuple[str, ...] = (
    "persona_identity",
    "authority_boundary",
    "current_scope_context",
    "pending_decisions",
    "recent_corrections",
)


_PRECOMPACT_FLAG_FILENAME = "pos_precompact.flag"


# ---- recent-corrections adapter --------------------------------------


# A recent-corrections provider is any callable returning a list of
# short correction records from memory. Typed as a Callable so callers
# can wire in the memory-system's retrieval without this module taking
# a dependency on that package's public types.
RecentCorrectionsProvider = Callable[[int], list[dict[str, Any]]]


# ---- payload ----------------------------------------------------------


@dataclass(frozen=True)
class CompactionSurvivor:
    """The payload re-injected after compaction.

    Every field in SURVIVAL_LIST is represented. A test reads the
    payload after a simulated compact-and-restore cycle and asserts
    the five-item list is intact — this is the D4 acceptance.
    """

    persona_identity: dict[str, str]
    authority_boundary: dict[str, str]
    current_scope_context: list[dict[str, Any]]
    pending_decisions: list[dict[str, Any]]
    recent_corrections: list[dict[str, Any]]
    restored_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "persona_identity": self.persona_identity,
            "authority_boundary": self.authority_boundary,
            "current_scope_context": self.current_scope_context,
            "pending_decisions": self.pending_decisions,
            "recent_corrections": self.recent_corrections,
            "restored_at": self.restored_at,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=False)


# ---- flag file API ----------------------------------------------------


def mark_precompact(flag_dir: str | Path) -> Path:
    """Invoked by the PreCompact hook. Writes a flag file whose
    presence on the next UserPromptSubmit triggers restoration.
    Returns the flag path for debugging."""
    flag_path = _flag_path(flag_dir)
    flag_path.parent.mkdir(parents=True, exist_ok=True)
    flag_path.write_text(
        json.dumps(
            {
                "pre_compact_at": datetime.now(timezone.utc).isoformat(),
                "schema_version": 1,
            },
            indent=2,
        )
    )
    return flag_path


def precompact_flag_present(flag_dir: str | Path) -> bool:
    return _flag_path(flag_dir).exists()


def clear_precompact_flag(flag_dir: str | Path) -> None:
    try:
        _flag_path(flag_dir).unlink()
    except FileNotFoundError:
        pass


def _flag_path(flag_dir: str | Path) -> Path:
    return Path(flag_dir) / _PRECOMPACT_FLAG_FILENAME


# ---- restoration ------------------------------------------------------


def build_survival_payload(
    *,
    persona: LoadedPersona,
    runtime: ScopeRuntime,
    recent_corrections_provider: RecentCorrectionsProvider | None = None,
    corrections_limit: int = 5,
) -> CompactionSurvivor:
    """Assemble the survival payload from authoritative sources.

    - `persona_identity` comes from the loaded contract.
    - `authority_boundary` comes from the loaded contract.
    - `current_scope_context` comes from `runtime.list()` (active
      scopes).
    - `pending_decisions` comes from `runtime.list(
      include_pending_extension=True)`.
    - `recent_corrections` comes from the memory-system via the
      provided callback; if no provider is supplied, the list is
      empty (degrades gracefully rather than failing hard).
    """
    contract: PersonaContract = persona.contract
    identity = {
        "handle": contract.handle,
        "given_name": contract.given_name,
        "contract_version": contract.contract_version,
    }
    authority = {
        "tier_a": contract.authority_boundary.tier_a.value,
        "tier_b": contract.authority_boundary.tier_b.value,
        "tier_c": contract.authority_boundary.tier_c.value,
        "tier_d": contract.authority_boundary.tier_d.value,
    }

    active_scopes = runtime.list()
    current = [
        _proj_summary(p)
        for p in active_scopes
        if p.state.value in ("active", "paused", "escalated")
        and p.pending_extension_axis is None
    ]
    pending = [
        _proj_summary(p)
        for p in runtime.list(include_pending_extension=True)
    ]

    corrections: list[dict[str, Any]] = []
    if recent_corrections_provider is not None:
        try:
            corrections = list(recent_corrections_provider(corrections_limit))
        except Exception:
            corrections = []

    return CompactionSurvivor(
        persona_identity=identity,
        authority_boundary=authority,
        current_scope_context=current,
        pending_decisions=pending,
        recent_corrections=corrections,
        restored_at=datetime.now(timezone.utc).isoformat(),
    )


def consume_survival_payload(
    *,
    flag_dir: str | Path,
    persona: LoadedPersona,
    runtime: ScopeRuntime,
    recent_corrections_provider: RecentCorrectionsProvider | None = None,
    corrections_limit: int = 5,
) -> CompactionSurvivor | None:
    """On UserPromptSubmit: if the flag is present, build + return the
    survival payload and clear the flag. Otherwise return None so the
    caller knows no restoration is needed.

    Acceptance (D4): repeated UserPromptSubmit turns do not re-inject;
    the flag is cleared after the first successful call.
    """
    if not precompact_flag_present(flag_dir):
        return None
    payload = build_survival_payload(
        persona=persona,
        runtime=runtime,
        recent_corrections_provider=recent_corrections_provider,
        corrections_limit=corrections_limit,
    )
    clear_precompact_flag(flag_dir)
    return payload


# ---- helpers ----------------------------------------------------------


def _proj_summary(p: Any) -> dict[str, Any]:
    """Small serialisable summary of a ScopeProjection for survival."""
    return {
        "scope_id": p.scope_id,
        "goal": p.goal[:120],
        "state": p.state.value,
        "owner_persona": p.owner_persona,
        "pause_reason": p.pause_reason,
        "pending_extension_axis": (
            p.pending_extension_axis.value if p.pending_extension_axis else None
        ),
    }
