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

"""KP7 — SessionStart objective + last-state surface (keep-pace MVP Cycle 4).

A NEW surfacing step composed onto the existing ``pos_session_start.py``
SessionStart hook. On session start the persona surfaces, in PLAIN
language, "last session you were on X; next likely Y" — the user's
active objectives + last subgoal + likely-next-action — routed THROUGH
KP9's draft-gate so no file-names / IDs / internal-mechanism tokens leak
(AC.KP7.1, AC.KP7.3).

The surface is re-asserted via the FIRST ``UserPromptSubmit`` after a
compaction (:func:`reassert_surface_for_user_prompt_submit`) so a
compaction — including the Claude-Code ``#15174`` SessionStart-compact
bug, if live — cannot evaporate it (AC.KP7.2). KP0.3's recorded probe
confirmed the ``UserPromptSubmit`` re-assert route reaches the model;
that is the route this re-assert rides.

**Fail-open / fail-soft (AC.KP.S.1).** Every cross-component dependency
(the primary-persona ``objectives`` register reader, the
hands-off-lifecycle ``draft_gate``) is reached via a BEST-EFFORT lazy
import wrapped so any failure degrades to "no surface" rather than
breaking the live SessionStart hook. A live session hook must NEVER
wedge or error on a missing/broken dependency — the same discipline
D-KP9.1 applied to the draft-gate's jargon module. The existing
service-health probing behaviour of ``pos_session_start.py`` is
PRESERVED; KP7 ADDS a step, it does not replace the probe.

Stdlib-only. Importable so tests exercise it without subprocess.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional


# The surface text the user sees. Plain language, no internal tokens
# (AC.KP7.3 — composes with the KP9 Layer 1 lint). Routed through the
# gate before it is ever returned.
_LEAD_IN = "Picking up where you left off:"


def _loam_root() -> Path:
    """The workspace root that holds the framework/ tree.

    ``framework/orchestrator/scripts/session_surface.py`` → parents[3]
    is the workspace root (mirrors pos_session_start.py's own
    ``parents[3]`` derivation).
    """
    return Path(__file__).resolve().parents[3]


# ---- best-effort cross-component readers (fail-soft) ----------------
#
# KP7 lives in the orchestrator component. It reads two surfaces that
# live in OTHER components:
#   - the user's active objectives (primary-persona keep_pace.objectives)
#   - the draft-to-send gate (hands-off-lifecycle keep_pace.draft_gate)
# Neither is taken as a hard top-level import: a live SessionStart hook
# must not crash if a sibling component is mid-edit or absent on a
# stranger workspace. Each reader returns a graceful empty / pass-through
# value on any failure.


def _load_active_objectives() -> list:
    """Best-effort: return the live active Objective entries (or []).

    Reads the primary-persona keep_pace objectives register via the
    same fallback-to-seed path KP1 uses (``load_user_scope_register``
    falls back to the in-source SEED when no live user-scope file
    exists — so the surface always has the two real objectives even on
    a fresh machine, AC.KP5.5 binding). Any import / read failure →
    [] (the surface then degrades to nothing; the health probe is
    untouched).
    """
    try:
        pkg = (
            _loam_root()
            / "framework"
            / "primary-persona"
            / "src"
        )
        if pkg.is_dir() and str(pkg) not in sys.path:
            sys.path.insert(0, str(pkg))
        from loam.primary_persona.keep_pace.objectives import (  # type: ignore[import-not-found]
            load_user_scope_register,
        )

        objectives = load_user_scope_register()
        return [o for o in objectives if getattr(o, "is_active", lambda: False)()]
    except BaseException:  # noqa: BLE001 — fail-soft: no objectives → no surface
        return []


def _gate_text(text: str) -> str:
    """Best-effort: route ``text`` through KP9's draft-gate.

    Returns ``text`` unchanged when the gate PASSES. When the gate
    BLOCKS (a Layer 1 jargon / mechanism leak slipped into the
    surface), returns "" — the surface is SUPPRESSED rather than
    leaking internal tokens to the user (AC.KP7.1 routes through the
    gate; AC.KP7.3 self-description stays plain). On any gate import /
    runtime failure the gate is fail-OPEN per AC.KP9.4: the text passes
    unchanged (a broken gate must never block a send).
    """
    try:
        hooks_dir = (
            _loam_root()
            / "framework"
            / "hands-off-lifecycle"
            / "hooks"
            / "keep_pace"
        )
        if hooks_dir.is_dir() and str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))
        from draft_gate import gate  # type: ignore[import-not-found]

        result = gate(text, surface_kind="session-start-summary")
        # BLOCK → suppress (do not leak); FLAG / PASS → send the text.
        if result.blocked():
            return ""
        return text
    except BaseException:  # noqa: BLE001 — fail-OPEN: a broken gate never blocks
        return text


# ---- surface composition (the plain-language last-state string) -----


def _likely_next_action(objective_text: str, last_subgoal: str) -> str:
    """Derive a plain-language "next likely" clause.

    Method-level (builder's call): the likely-next-action is the
    active objective's most-recent subgoal phrased in plain words. The
    subgoal slug is de-slugged (hyphens → spaces) so no internal slug
    token surfaces (AC.KP7.3). When there is no subgoal, fall back to
    continuing the objective itself.
    """
    if last_subgoal:
        return _deslug(last_subgoal)
    return "continuing that work"


def _deslug(slug: str) -> str:
    """Turn a ``kebab-case-slug`` into plain words ("canon consistency
    across the series"). Keeps the surface human-readable so no slug
    token leaks (AC.KP7.3 composes with the KP9 lint)."""
    return slug.replace("-", " ").replace("_", " ").strip()


def build_session_surface(objectives: Optional[list] = None) -> str:
    """Build the plain-language SessionStart last-state surface (AC.KP7.1).

    Returns "last session you were on X; next likely Y" composed from
    the active objectives + last subgoal + likely-next-action, in plain
    language, ROUTED THROUGH the KP9 gate (so no file-names / IDs /
    internal-mechanism tokens leak). Returns "" when there is no active
    objective to surface (silent — no noise) or when the gate suppresses
    a leaking surface.

    ``objectives`` may be injected (tests / callers); when None, the
    live active objectives are read best-effort. Fail-soft throughout:
    any failure yields "" (no surface), never an exception — the
    SessionStart health probe must be untouched.
    """
    try:
        raw = objectives if objectives is not None else _load_active_objectives()
        # Only ACTIVE objectives surface — regardless of whether they were
        # injected (tests / callers) or read live. An inactive/dormant
        # entry is not "what you were on last session". Duck-typed:
        # entries without is_active() are treated as active (the live
        # reader already filters, this guards injected sets).
        objs = [
            o
            for o in raw
            if getattr(o, "is_active", lambda: True)()
        ]
        if not objs:
            return ""

        clauses: list[str] = []
        for obj in objs:
            obj_text = str(getattr(obj, "objective", "") or "").strip()
            if not obj_text:
                continue
            # Plain-language objective phrasing: take the first sentence
            # (the headline intent) so the surface stays short and
            # human, not a wall of text.
            headline = _headline(obj_text)
            subgoals = list(getattr(obj, "subgoals", []) or [])
            last_subgoal = subgoals[-1] if subgoals else ""
            nxt = _likely_next_action(obj_text, last_subgoal)
            clauses.append(f"{headline}; next likely: {nxt}")

        if not clauses:
            return ""

        body = " | ".join(clauses)
        surface = f"{_LEAD_IN} {body}"
        return _gate_text(surface)
    except BaseException:  # noqa: BLE001 — fail-soft: no surface, never break
        return ""


def _headline(objective_text: str) -> str:
    """First-sentence headline of an objective, in plain words.

    Splits on the first sentence boundary so the surface carries the
    intent ("Build durable financial independence") not the full
    paragraph. No internal tokens are added; the source objective text
    is already plain language (it is user-authored)."""
    text = objective_text.strip()
    for sep in (". ", "; ", " — "):
        idx = text.find(sep)
        if 0 < idx < 160:
            return text[:idx].strip()
    # No early boundary — trim to a readable length on a word boundary.
    if len(text) > 160:
        cut = text[:160].rsplit(" ", 1)[0]
        return cut.strip()
    return text


# ---- the #15174 re-assert route (AC.KP7.2) --------------------------


def reassert_surface_for_user_prompt_submit(
    objectives: Optional[list] = None,
) -> str:
    """Re-emit the SessionStart surface for the first UserPromptSubmit.

    AC.KP7.2 — the ``#15174`` mitigation: a SessionStart-injected
    surface can be evaporated by a compaction (the ``#15174``
    SessionStart-compact bug). KP0.3's recorded probe confirmed the
    ``UserPromptSubmit`` re-assert route reaches the model; this
    function produces the same plain-language surface so the KP1
    ``UserPromptSubmit`` chain (or any caller on that event) can
    re-inject it as additionalContext after a compaction. Returns ""
    when there is nothing to surface (silent). Fail-soft.

    The re-assert is the IDENTICAL gated surface as the SessionStart
    step — a compaction must restore the SAME plain-language state, not
    a different one.
    """
    return build_session_surface(objectives=objectives)
