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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.MSC.2 — session-start active-thread contributor (Gap A part b).

A session restart is behaviourally transparent: a fresh session
reconstructs *where we were* from durably-stored memory read at
session-start, **without any bespoke session-end capture hook**.
Continuous passive capture (the long-running memory-write worker)
already exists and is healthy; the failure this closes is purely
read-side — memory was never consulted at session-start at all
(``context_composer.on_session_start`` skips every contributor whose
``trigger_kind != TriggerKind.session``; both memory contributors
register at ``TriggerKind.turn``).

This module adds a ``TriggerKind.session`` contributor that, at every
session-start, emits a bounded digest of the most-recent active
working thread reconstructed from:

  1. the most-recent durably-stored episodes (deterministic recency
     scan — D-MSC.4: stdlib only, zero LLM cost, fits the 5s
     session-start hook timeout; a ``claude -p`` enrichment is an
     explicit follow-on, not this cycle's path); and
  2. the named-thread durable surface (``docs/FUTURE_IDEAS_DRAFT.md``)
     — defence-in-depth (AC.MSC.3 also adds it to the session-start
     corpus path-list; two independent paths to the same outcome per
     plan §10 risk 4).

The digest names the live topic and any pending owner ruling
associated with it. No Stop / SessionEnd hook is read or required —
the contributor reads only the episode store + the named-thread
surface (§12 halt trigger 1: a session-end hook would violate the
owner constraint AND be unnecessary; this module deliberately adds
none).

Fail-soft (AC.MSC.5): any boundary error inside the contributor
yields an empty block and the session proceeds, consistent with the
composer's contributor sandbox + the AC46.4 / AC.MFBM.2 fail-closed
contracts. The block is bounded so the session-start payload stays
within ``ADDITIONAL_CONTEXT_CAP`` (§12 halt trigger 3).

Composed on the SEALED #45 multi-contributor SessionStart registry +
#46 session-start emitter substrate — no new hook machinery (Lens 1).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

# Structurally-detectable marker (mirrors onboarding's
# STARTER_PENDING_MARKER convention) so a consumer can discriminate
# this block without parsing prose. The marker naming the *active
# thread* is the structural signal that session-amnesia did not
# occur.
ACTIVE_THREAD_MARKER = "[primary-persona/active-thread]"

# The named-thread durable surface (D-MSC.3 primary). FIDRAFT carries
# the "where we were + open owner rulings" entries by the existing
# surface-to-chat-then-append convention. Workspace-relative; the
# resolver falls through to ``framework/`` per the #67 restructure.
NAMED_THREAD_SURFACE_REL = "docs/FUTURE_IDEAS_DRAFT.md"

# How many of the most-recent episodes the recency scan reads to
# reconstruct the active thread. Bounded so the deterministic scan
# stays inside the 5s session-start envelope on a 600+-episode store
# and the rendered digest stays well under the per-contributor
# budget. The newest episodes ARE the active thread (continuous
# passive capture writes one episode per turn).
ACTIVE_THREAD_EPISODE_SCAN = 8

# Per-episode preview length in the digest (chars). Enough to name
# the topic; short enough that the whole block stays bounded.
_EPISODE_PREVIEW_CHARS = 220

# Total block hard cap (chars). The composer enforces the 10k
# ADDITIONAL_CONTEXT_CAP across all contributors; this per-contributor
# bound keeps the active-thread block from crowding the cap (§12 halt
# trigger 3 — bounded, never silently truncating load-bearing thread
# context past a documented bound).
ACTIVE_THREAD_BLOCK_CAP = 2000

# Lines that signal an open owner ruling inside a FIDRAFT entry. The
# digest lifts the first such line so the pending-ruling fact is
# present at session-start even when episode retrieval ranks
# imperfectly.
_PENDING_RULING_RE = re.compile(
    r"(pending|open|owner ruling|awaiting|halt|ratif)",
    re.IGNORECASE,
)


def _resolve_surface(workspace_root: Path, rel: str) -> Path | None:
    """Resolve a workspace-relative durable surface, falling through
    to ``<workspace>/framework/<rel>`` (the #67 single-framework
    restructure convention). Returns ``None`` when neither exists."""
    direct = workspace_root / rel
    if direct.is_file():
        return direct
    framework = workspace_root / "framework" / rel
    if framework.is_file():
        return framework
    return None


def _named_thread_digest(workspace_root: Path) -> list[str]:
    """Lift the most-recent named-thread entry from the durable
    surface: its heading line + the first open-owner-ruling line.

    FIDRAFT entries are authored newest-relevant with a bolded
    heading (``- **F-... — ...**``). The reader scans for the last
    bolded-heading bullet and the first line in/after it that signals
    a pending ruling. Best-effort: a surface that does not match the
    convention contributes nothing rather than raising (AC.MSC.5).
    """
    surface = _resolve_surface(workspace_root, NAMED_THREAD_SURFACE_REL)
    if surface is None:
        return []
    try:
        text = surface.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    lines = text.splitlines()
    heading_idxs = [
        i
        for i, ln in enumerate(lines)
        if ln.lstrip().startswith("- **") and "—" in ln
    ]
    if not heading_idxs:
        return []
    last = heading_idxs[-1]
    heading = lines[last].strip()
    if len(heading) > 320:
        heading = heading[:317].rstrip() + "..."
    out = [f"named-thread surface ({NAMED_THREAD_SURFACE_REL}):", f"  {heading}"]
    # First pending-ruling-signalling line at/after the heading.
    for ln in lines[last : last + 60]:
        stripped = ln.strip()
        if not stripped or stripped == heading:
            continue
        if _PENDING_RULING_RE.search(stripped):
            if len(stripped) > 320:
                stripped = stripped[:317].rstrip() + "..."
            out.append(f"  pending: {stripped}")
            break
    return out


def build_active_thread_contributor(
    store: Any,
    *,
    workspace_root: Path,
    workspace_slug: str,
) -> Callable[[dict[str, Any]], str]:
    """Return the callable registered against
    ``ComposedContextPayload.register(name="active-thread",
    trigger_kind=TriggerKind.session, fn=<returned callable>)``.

    On every ``on_session_start`` the contributor:

      - reads the most-recent ``ACTIVE_THREAD_EPISODE_SCAN`` episodes
        via the store's deterministic recency scan
        (``store.recent_episodes``) — D-MSC.4 stdlib path, no LLM, no
        query;
      - lifts the most-recent named-thread entry + its pending-ruling
        line from the durable surface (defence-in-depth with
        AC.MSC.3);
      - emits a bounded digest whose first line is
        ``ACTIVE_THREAD_MARKER`` followed by the recent-episode topic
        markers and the named-thread digest.

    When there is no durable memory at all (fresh workspace, zero
    episodes, no named-thread surface) the contributor returns the
    empty string (the composer's convention for "no contribution this
    turn") — a genuinely-empty workspace has no active thread to
    surface and that is AC-shape-correct, not a failure.

    Fail-soft: any boundary error returns the empty string; the
    session proceeds (AC.MSC.5). ``store`` is duck-typed (any object
    exposing ``recent_episodes(group_ids=..., limit=...)``) so tests
    can inject a fake.
    """

    def contributor(context: dict[str, Any]) -> str:
        try:
            episodes = store.recent_episodes(
                group_ids=[workspace_slug],
                limit=ACTIVE_THREAD_EPISODE_SCAN,
            )
        except Exception:  # noqa: BLE001 — AC.MSC.5 fail-soft
            episodes = []

        try:
            named = _named_thread_digest(workspace_root)
        except Exception:  # noqa: BLE001 — AC.MSC.5 fail-soft
            named = []

        if not episodes and not named:
            return ""

        lines: list[str] = [ACTIVE_THREAD_MARKER]
        lines.append(
            "most-recent active working thread (reconstructed from "
            "durably-stored memory at session-start; no session-end "
            "hook required):"
        )
        if episodes:
            lines.append("recent episodes (newest first):")
            for ep in episodes:
                name = str(ep.get("name", "")).strip() or "(unnamed)"
                valid_at = str(ep.get("valid_at", "")).strip()
                preview = " ".join(
                    str(ep.get("content", "")).split()
                )[:_EPISODE_PREVIEW_CHARS]
                stamp = f" @ {valid_at}" if valid_at else ""
                lines.append(f"  - {name}{stamp}")
                if preview:
                    lines.append(f"    {preview}")
        if named:
            lines.extend(named)

        block = "\n".join(lines)
        if len(block) > ACTIVE_THREAD_BLOCK_CAP:
            # Line-boundary-aware truncation (never a half-line); the
            # marker + the named-thread pending-ruling line are the
            # load-bearing facts and are emitted before the
            # per-episode previews, so a truncation drops the
            # lowest-signal tail first.
            kept: list[str] = []
            running = 0
            for ln in lines:
                if running + len(ln) + 1 > ACTIVE_THREAD_BLOCK_CAP:
                    break
                kept.append(ln)
                running += len(ln) + 1
            block = "\n".join(kept)
        return block

    return contributor
