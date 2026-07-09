"""Per-persona human-readable handoff surface (per-session-resume-handoff, D4).

``workspace/.loam/handoffs/<persona>.md`` — a SECONDARY, human-readable resume
surface: written at turn-close, read at session-start filtered to THIS persona.

D4 (recommendation adopted as convenience, not correctness): the crash-robust
filtered episodes are the PRIMARY resume path (AC.PSR.1 / AC.PSR.7). This file
is a convenience fallback (AC.PSR.2) — it can go stale on a refusal/crash where
no Stop hook fires (the 2026-06-10 no-Stop-hook failure mode), so it is NEVER
promoted above the episodes. It formalizes the manual handoff a channel-session
operator already writes by hand.

The read is persona-scoped by construction: it opens exactly ``<persona>.md``,
so persona P's session never surfaces persona Q's handoff (AC.PSR.2's negative
guarantee). A workspace with no channel-session identity (no ``session_key``)
has no handoff file to read — single-session workspaces are unaffected.
"""

from __future__ import annotations

import re
from pathlib import Path

from .file_memory import LOAM_SUBDIR

HANDOFFS_SUBDIR = "handoffs"

# A persona/session key must be a safe single filename component — the resolver
# yields CLAUDE_PERSONA / a DISCORD_STATE_DIR basename, both of which SHOULD be
# simple slugs, but the read/write must never escape the handoffs dir on a
# surprising value. Reject anything with a path separator or traversal.
_SAFE_PERSONA_RE = re.compile(r"^[A-Za-z0-9._-]+$")


def handoffs_dir(workspace_root: Path | str) -> Path:
    """Resolve ``<workspace>/workspace/.loam/handoffs/`` (not created here)."""
    from loam.workspace_bootstrap.workspace_paths import (  # noqa: WPS433
        WORKSPACE_STATE_SUBDIR,
    )

    ws_root = Path(workspace_root)
    return ws_root / WORKSPACE_STATE_SUBDIR / LOAM_SUBDIR / HANDOFFS_SUBDIR


def _safe_persona(persona: str | None) -> str | None:
    if not persona:
        return None
    persona = persona.strip()
    if not persona or persona in (".", ".."):
        return None
    if not _SAFE_PERSONA_RE.match(persona):
        return None
    return persona


def write_handoff(
    workspace_root: Path | str,
    *,
    persona: str | None,
    content: str,
) -> Path | None:
    """Write persona P's handoff file at turn-close (SECONDARY, best-effort).

    Returns the written path, or ``None`` when there is no channel-session
    identity (``persona`` falsy/unsafe → single-session workspace, nothing to
    write). Atomic via tmp + replace so a crash mid-write leaves the prior
    handoff intact. Never raises — the handoff is a convenience; a write
    failure must not disturb the turn-close path (D4).
    """
    safe = _safe_persona(persona)
    if safe is None:
        return None
    try:
        target_dir = handoffs_dir(workspace_root)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{safe}.md"
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(target)
        return target
    except OSError:
        return None


def read_handoff(
    workspace_root: Path | str,
    *,
    persona: str | None,
) -> str | None:
    """Read persona P's handoff file at session-start (persona-filtered).

    Returns the file's content, or ``None`` when there is no channel-session
    identity, the file is absent, or it cannot be read. Opens EXACTLY
    ``<persona>.md`` — persona P never reads persona Q's handoff (AC.PSR.2
    negative guarantee). Never raises (AC.PSR.5 fail-soft).
    """
    safe = _safe_persona(persona)
    if safe is None:
        return None
    try:
        target = handoffs_dir(workspace_root) / f"{safe}.md"
        if not target.is_file():
            return None
        return target.read_text(encoding="utf-8")
    except OSError:
        return None
