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

"""End-of-turn trait-reflection Stop-hook contributor.

The Stop hook is Claude Code's once-per-turn-close trigger. Loam
already wires a memory-write contributor at ``cli_stop`` (see
:mod:`loam.primary_persona.stop_emitter`). This module is an
INDEPENDENT contributor on the same Stop event: a deterministic
self-reflection check that inspects the just-emitted assistant
reply against the persona's seven top-value traits and emits a
PASS/CONCERN verdict per trait to a workspace-local log.

Scope contract (ODD §2.5):

  - AC.EOTTR.1 — component exists at this canonical path with the
    documented :func:`run_trait_reflection` API surface.
  - AC.EOTTR.2 — wired via a new ``trait-reflection-stop`` argparse
    subparser in :mod:`loam.primary_persona.cli`; invokable as
    ``python -m loam.primary_persona.cli trait-reflection-stop``.
  - AC.EOTTR.3 — deterministic. Identical assistant text yields
    identical verdicts across runs. No LLM, no clock-derived
    state inside the verdict computation (timestamps are recorded
    in the log envelope but excluded from the verdict payload).
  - AC.EOTTR.4 — each of the seven traits has at least one
    keyword/heuristic scored. The :data:`TRAIT_HEURISTICS` table
    is the single source of truth.
  - AC.EOTTR.5 — graceful on absent content. Empty or missing
    assistant text emits CONCERN: missing content for every
    trait; no crash, no non-zero exit.

Composition with the existing Stop-hook contributors:

  - Independent module. Does not call into ``stop_emitter``'s
    write path; does not touch the ``last-turn-id`` marker; does
    not enqueue to ``memory-write-queue``. The two contributors
    fire side-by-side via separate entries in pos3's
    ``.claude/settings.json`` Stop array.
  - Observer + reporter only. Always exits 0. A non-zero exit
    from a Stop hook blocks Claude Code's normal stop behaviour;
    this contributor never blocks the send.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Re-use the existing Stop envelope parser + transcript walker so
# this contributor stays in lockstep with the canonical recovery
# path. AC.EOTTR.5's empty-content branch shares the same
# ("", "") trigger as AC.M.9.
from .stop_emitter import (
    StopEnvelope,
    _walk_transcript_for_turn,
    derive_turn_id,
    parse_stop_envelope,
)


# ---- the seven traits + keyword heuristics (AC.EOTTR.4) ----------------
#
# Each entry carries:
#   - ``trait``: the canonical trait name from the persona prompt's
#     "Top-value traits" section.
#   - ``positive_signals``: substring patterns whose PRESENCE in the
#     assistant text is evidence the trait was in effect on this
#     turn.
#   - ``anti_signals``: substring patterns whose PRESENCE in the
#     assistant text is evidence the trait was VIOLATED on this
#     turn.
#
# Verdict rule (deterministic, AC.EOTTR.3):
#   - If any ``anti_signal`` matches → CONCERN.
#   - Else if any ``positive_signal`` matches → PASS (signal observed).
#   - Else → PASS (no anti-signal observed) — the trait was not
#     stressed on this turn so no violation could be detected.
#
# All matching is case-insensitive substring matching against the
# raw assistant text. The patterns are intentionally narrow —
# overbroad heuristics generate noise that erodes the signal.


@dataclass(frozen=True)
class TraitHeuristic:
    trait: str
    positive_signals: tuple[str, ...]
    anti_signals: tuple[str, ...]


# Source: ``templates/persona-template/prompt.md`` §"Top-value traits".
# Verdict semantics:
#   - anti_signals lean on phrasings the prompt explicitly names as
#     violations ("are you sure?", "is there a serialization here
#     that's actually load-bearing", etc.); positive_signals lean on
#     the language the prompt uses to describe the trait in effect.
#   - The signals are NOT exhaustive — they're the cheapest
#     keyword-grade tells. The Stop-hook contributor is a smoke
#     test, not an LLM judge.
TRAIT_HEURISTICS: tuple[TraitHeuristic, ...] = (
    TraitHeuristic(
        trait="Autonomy",
        positive_signals=(
            "dispatching",
            "going ahead",
            "running it",
            "proceeding",
            "autonomous",
        ),
        anti_signals=(
            "are you sure?",
            "should i proceed",
            "would you like me to",
            "do you want me to",
            "shall i proceed",
            "confirm and i",
            "let me know if",
        ),
    ),
    TraitHeuristic(
        trait="Asymmetric problem solving",
        positive_signals=(
            "leverage",
            "high-leverage",
            "asymmetric",
            "disproportionate",
            "cheap probe",
        ),
        anti_signals=(),
    ),
    TraitHeuristic(
        trait="Parallelism",
        positive_signals=(
            "in parallel",
            "concurrently",
            "parallel",
            "side by side",
            "fan out",
        ),
        anti_signals=(
            "one at a time",
            "sequentially",
            "first i'll then i'll",
        ),
    ),
    TraitHeuristic(
        trait="Test theories before acting on them",
        positive_signals=(
            "verify",
            "verified",
            "probe",
            "test theory",
            "checked",
            "re-read",
            "let me check",
        ),
        anti_signals=(
            "must be because",
            "obviously caused",
        ),
    ),
    TraitHeuristic(
        trait="Calibration",
        positive_signals=(
            "estimate",
            "estimated",
            "approximately",
            "guess",
            "uncertain",
            "verified:",
            "tier-0",
            "tier-1",
            "tier-2",
            "confidence",
        ),
        anti_signals=(
            "definitely happened",
            "for sure",
        ),
    ),
    TraitHeuristic(
        trait="Self-correction",
        positive_signals=(
            "noticed",
            "didn't work",
            "did not work",
            "doesn't work",
            "capture",
            "fix-it",
            "self-correct",
            "course-correct",
            "lesson",
        ),
        anti_signals=(),
    ),
    TraitHeuristic(
        trait="Pruning",
        positive_signals=(
            "prune",
            "pruned",
            "cut ",
            "remove",
            "removed",
            "stale",
            "no longer load-bearing",
            "no longer relevant",
            "retire",
            "retired",
        ),
        anti_signals=(),
    ),
)


# ---- verdict computation (AC.EOTTR.3 / AC.EOTTR.4 / AC.EOTTR.5) -------


def _match_any(text_lower: str, patterns: tuple[str, ...]) -> str | None:
    """Return the first pattern in ``patterns`` that occurs as a
    case-insensitive substring of ``text_lower`` (which the caller
    has already lower-cased), or ``None``."""
    for pat in patterns:
        if pat in text_lower:
            return pat
    return None


def evaluate_trait(
    heuristic: TraitHeuristic, assistant_text: str
) -> dict[str, str]:
    """Compute the PASS/CONCERN verdict for one trait.

    Deterministic (AC.EOTTR.3): same input → same output. No
    randomness, no clock, no I/O.

    AC.EOTTR.5: empty/whitespace-only assistant text yields
    ``CONCERN: missing content``.
    """
    if not assistant_text or not assistant_text.strip():
        return {
            "trait": heuristic.trait,
            "verdict": "CONCERN",
            "reason": "missing content",
        }
    text_lower = assistant_text.lower()
    anti = _match_any(text_lower, heuristic.anti_signals)
    if anti is not None:
        return {
            "trait": heuristic.trait,
            "verdict": "CONCERN",
            "reason": f"anti-signal: {anti!r}",
        }
    pos = _match_any(text_lower, heuristic.positive_signals)
    if pos is not None:
        return {
            "trait": heuristic.trait,
            "verdict": "PASS",
            "reason": f"positive-signal: {pos!r}",
        }
    return {
        "trait": heuristic.trait,
        "verdict": "PASS",
        "reason": "no anti-signal observed",
    }


def evaluate_all_traits(assistant_text: str) -> list[dict[str, str]]:
    """Run :func:`evaluate_trait` over every entry in
    :data:`TRAIT_HEURISTICS`. AC.EOTTR.4 guarantees the returned
    list has seven entries.
    """
    return [evaluate_trait(h, assistant_text) for h in TRAIT_HEURISTICS]


# ---- workspace-local log path (workspace-state convention) -------------


def _trait_reflection_log_dir(workspace_root: Path) -> Path:
    """``<workspace>/workspace/.pos/trait-reflection/``.

    Mirrors the workspace-state convention used by
    :func:`stop_emitter._diag_log_path` — the canonical workspace-
    local diagnostic surface lives under ``workspace/.pos/`` so it
    survives sealed-component boundaries and is co-located with the
    other Stop-hook diagnostics.
    """
    from loam.workspace_bootstrap.workspace_paths import pos_subdir

    return pos_subdir(workspace_root) / "trait-reflection"


def _trait_reflection_log_path(
    workspace_root: Path, session_id: str
) -> Path:
    """One JSONL per session (D8-style)."""
    # Defensive: a session id with path separators would escape the
    # log dir. Replace any non-filename-safe character.
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", session_id) or "unknown-session"
    return _trait_reflection_log_dir(workspace_root) / f"{safe}.jsonl"


def _append_log(
    workspace_root: Path, session_id: str, entry: dict[str, Any]
) -> None:
    """Append one NDJSON entry to the per-session trait-reflection
    log. Best-effort: failure to log is silent — a Stop-hook
    contributor MUST NOT bleed tracebacks into Claude Code's debug
    log."""
    try:
        log_path = _trait_reflection_log_path(workspace_root, session_id)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        return


# ---- public API (AC.EOTTR.1) -------------------------------------------


def run_trait_reflection(
    *,
    workspace_root: Path,
    session_id: str,
    assistant_text: str,
    turn_id: str | None = None,
) -> dict[str, Any]:
    """Compute trait-reflection verdicts for one turn-close.

    AC.EOTTR.1: this is the documented module-level API surface.
    AC.EOTTR.3: deterministic given ``assistant_text`` — the
    ``verdicts`` list is a pure function of the input. The
    enclosing envelope (``ts``, ``session_id``, ``turn_id``,
    ``assistant_text_sha256``) is metadata; ``verdicts`` itself
    contains no clock/random/IO-derived state.
    AC.EOTTR.5: empty / missing ``assistant_text`` yields seven
    ``CONCERN: missing content`` verdicts.

    Side effect: appends one NDJSON line to
    ``<workspace>/workspace/.pos/trait-reflection/<session>.jsonl``.
    Returns the envelope dict that was written.
    """
    verdicts = evaluate_all_traits(assistant_text)
    sha = hashlib.sha256(
        (assistant_text or "").encode("utf-8")
    ).hexdigest()
    envelope: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "turn_id": turn_id,
        "assistant_text_sha256": sha,
        "verdicts": verdicts,
    }
    _append_log(Path(workspace_root), session_id, envelope)
    return envelope


# ---- envelope handling (AC.EOTTR.2) ------------------------------------


def handle_stop_envelope(
    envelope: StopEnvelope, workspace_root: Path
) -> None:
    """Recover the assistant reply from the Stop envelope's
    ``transcript_path`` and run trait-reflection on it.

    Uses ``_walk_transcript_for_turn`` from ``stop_emitter`` so the
    recovery surface is byte-identical to the memory-write
    contributor — no drift between what gets persisted to memory and
    what gets reflected on.
    """
    user_message, assistant_reply = _walk_transcript_for_turn(
        Path(envelope.transcript_path)
    )
    # turn_id derivation matches stop_emitter so the two contributors'
    # log entries can be joined on turn_id downstream.
    turn_id = (
        derive_turn_id(
            session_id=envelope.session_id, user_message=user_message
        )
        if user_message
        else None
    )
    run_trait_reflection(
        workspace_root=workspace_root,
        session_id=envelope.session_id,
        assistant_text=assistant_reply,
        turn_id=turn_id,
    )


def cli_trait_reflection_stop(
    workspace_root: Path | None = None,
) -> int:
    """Read a Stop envelope from stdin and emit trait-reflection
    verdicts.

    Mirrors :func:`stop_emitter.cli_stop`'s fail-soft contract: every
    internal exception is caught and the function returns 0
    unconditionally. A Stop-hook contributor that exits non-zero
    blocks Claude Code's normal stop behaviour.
    """
    root = workspace_root if workspace_root is not None else Path.cwd()
    raw = ""
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — AC.EOTTR.5 fail-soft
        raw = ""
    envelope = parse_stop_envelope(raw)
    if envelope is None:
        return 0
    try:
        handle_stop_envelope(envelope, Path(root))
    except Exception:  # noqa: BLE001 — AC.EOTTR.5 fail-soft
        # Best-effort: try to log the failure but never propagate.
        try:
            _append_log(
                Path(root),
                envelope.session_id,
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "session_id": envelope.session_id,
                    "error": "trait-reflection internal failure",
                },
            )
        except Exception:  # noqa: BLE001
            pass
    return 0
