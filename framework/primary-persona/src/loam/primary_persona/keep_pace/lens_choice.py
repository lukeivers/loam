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

"""WMS Increment 6 — PER-USER LENS CHOICE (the L4 wiring).

This module is the CHOOSER over the lens SET increment 5 completed. It
builds NO new lens; it decides WHICH lens(es) a given user sees by
default per-turn, derived from their #34 profile, owner-settable, with a
plain-language switch path. Three pieces, all composing built primitives
read-only (Lens-1: compose, don't duplicate):

  1. **The RESOLVER** (:func:`resolve_lens_set`) — a deterministic,
     fail-open read over the #34 ``work-tracking`` / ``preferred-lens``
     cell. It mirrors ``intake.py``'s ``resolve_aggressiveness`` EXACTLY
     (the same ``cell_or_prior`` read on the SAME ``work-tracking`` area):
     a recognised cell value maps to a lens-SET; an absent / garbled /
     unrecognised cell degrades to a NON-EMPTY default derived from the
     existing ``technical-exposure`` axis (D-WMS6.5). It makes NO model
     call (mirrors ``classify_area``), performs NO store mutation, NEVER
     raises, and NEVER returns an empty set (the anti-regression floor —
     RF #3 / plan §8 #3).

  2. **The choice-aware REGISTRATION** (:func:`register_chosen_lenses`) —
     the per-turn surface reconciliation. It resolves the set and
     registers exactly the CHOSEN lens(es) as ``TriggerKind.turn`` blocks
     (the FBM-don't-bloat composition — the right lens, not all of them).
     The un-chosen lenses keep their inc-5 on-demand ``render_*_block``
     entry points (rendered when asked, never removed — D-WMS6.3 replace-
     not-delete). Any error fails OPEN to the current always-on
     :data:`DEFAULT_ALWAYS_ON_SET` (the inc-4 trio), never to zero blocks
     (AC.SURFACE.4).

  3. **The SWITCH WRITER** (:func:`write_lens_choice` /
     :func:`apply_lens_switch`) — how a user changes their lens. A plain-
     language ask is treated as an explicit #34 statement (the highest-
     confidence, classifier-free signal that hard-sets a cell — D-WMS6.6):
     the persona confirms in plain language and the cell is persisted so
     the next turn surfaces the new choice. CRITICAL fence constraint
     (verified): ``interaction_model.apply_override`` REJECTS any area not
     in ``AIM_AREAS`` (line 694), and ``work-tracking`` is NOT in
     ``AIM_AREAS`` — so the switch CANNOT round-trip through the existing
     override writer. The writer is a WMS-area-scoped path that re-emits
     the matrix in the seed-writer's line-shape (reusing
     ``render_matrix`` + the ``Cell`` format) WITHOUT adding
     ``work-tracking`` to ``AIM_AREAS``, WITHOUT changing
     ``apply_override``'s gate, and WITHOUT editing the workspace-bootstrap
     seed-writer (D-WMS6.4 / plan §5). It deliberately does NOT call
     ``apply_override``.

The objective-tracker store and ``interaction_model.py`` are CONSUMED
read-only (the resolver reads the #34 cell; the chosen lens reads the
store via the existing API exactly as inc-2/4/5 do) — NOT modified. This
module adds NO new store, field, lifecycle, lens, or #34-taxonomy area.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

# ====================================================================
# The #34 area + axis the choice lives in (D-WMS6.1)
# ====================================================================
#
# The SAME ``work-tracking`` area intake.py reads (INTAKE_AREA), a sibling
# ``preferred-lens`` axis. Neither is in interaction_model.AIM_AREAS /
# AIM_AXES — the cell is a forward-compat read exactly as intake's
# ``intake-aggressiveness`` is. The resolver reads it via cell_or_prior;
# the writer persists it via render_matrix. Neither widens the taxonomy.

LENS_CHOICE_AREA = "work-tracking"
LENS_CHOICE_AXIS = "preferred-lens"

# ====================================================================
# The lens NAMES — the registered turn-block names (the resolver's targets)
# ====================================================================
#
# These EXACTLY match the block names the inc-1/2/4/5 lenses register /
# render under, so a resolved set maps 1:1 to a registration.

LENS_PLATE = "on-my-plate"      # inc-5 on-demand (the simplest actionable view)
LENS_PROJECTS = "projects"      # inc-2 always-on
LENS_STREAMS = "work-streams"   # inc-1 always-on (the broadest openness default)
LENS_RELATIONAL = "relational"  # inc-4 always-on
LENS_GOALS = "goals"            # inc-5 on-demand
LENS_WAITING = "waiting-on"     # inc-5 on-demand

# All recognised lens names (a value->set map targets only these).
_ALL_LENSES: tuple[str, ...] = (
    LENS_PLATE,
    LENS_PROJECTS,
    LENS_STREAMS,
    LENS_RELATIONAL,
    LENS_GOALS,
    LENS_WAITING,
)

# ====================================================================
# The fail-open floor (RF #3 / §8 #3 / AC.SURFACE.4)
# ====================================================================
#
# The CURRENT always-on default-set (the inc-4 trio every turn fires
# today). The resolver / registration degrade to THIS — never to an empty
# surface. A user can never lose their per-turn surface because the choice
# machinery degraded.

DEFAULT_ALWAYS_ON_SET: tuple[str, ...] = (
    LENS_STREAMS,
    LENS_PROJECTS,
    LENS_RELATIONAL,
)

# ====================================================================
# The preferred-lens value vocabulary (D-WMS6.2 / RF #5 — small + plain)
# ====================================================================
#
# A recognised ``preferred-lens`` cell value maps to a lens-SET. The
# vocabulary is deliberately SMALL + plain (the lens names + a "simplest"
# alias) and calibrate-on-use (the same Lens-4 discipline as intake's
# _VALID_AGGR + the #34 thresholds). An unrecognised value degrades to the
# exposure-derived default (never to nothing — AC.CHOICE.2/.3), so the
# over-fit risk is bounded by the fail-open floor.

_LENS_ALIASES: dict[str, str] = {
    "plate": LENS_PLATE,
    "on-my-plate": LENS_PLATE,
    "on_my_plate": LENS_PLATE,
    "my-plate": LENS_PLATE,
    "simplest": LENS_PLATE,    # the plain "just the simplest view" alias
    "plain": LENS_PLATE,
    "projects": LENS_PROJECTS,
    "project": LENS_PROJECTS,
    "streams": LENS_STREAMS,
    "work-streams": LENS_STREAMS,
    "work_streams": LENS_STREAMS,
    "broad": LENS_STREAMS,
    "relational": LENS_RELATIONAL,
    "relationships": LENS_RELATIONAL,
    "goals": LENS_GOALS,
    "goal": LENS_GOALS,
    "waiting-on": LENS_WAITING,
    "waiting_on": LENS_WAITING,
    "waiting": LENS_WAITING,
}


def _parse_lens_value(value: str) -> tuple[str, ...]:
    """Map a ``preferred-lens`` cell value to a lens-SET (D-WMS6.3).

    A power user expresses "I want several always-on" as a multi-select
    value (``projects+work-streams`` / ``projects, streams``) — the value
    is a delimiter-separated list, so multi-select subsumes the "add" case
    without a second code path. Returns an EMPTY tuple when no token is
    recognised (the caller then degrades to the exposure-derived default).
    """
    out: list[str] = []
    seen: set[str] = set()
    for raw in value.replace("+", ",").replace("/", ",").split(","):
        token = raw.strip().lower()
        if not token:
            continue
        lens = _LENS_ALIASES.get(token)
        if lens is not None and lens not in seen:
            seen.add(lens)
            out.append(lens)
    return tuple(out)


# ====================================================================
# The exposure-derived default (D-WMS6.5 — map to the EXISTING #34 axis)
# ====================================================================
#
# No NEW signal: the default lens per tech-level reads the EXISTING
# ``technical-exposure`` axis the #34 matrix already carries. plain (the
# non-tech, meet-them-simply user) -> on-my-plate (the simplest actionable
# view); open (the engaged default) -> work-streams (the architecture's
# broadest openness default); deep -> the broad streams set (an explicit
# pick overrides this via the cell — AC.SWITCH.4).

_EXPOSURE_DEFAULT_LENS: dict[str, tuple[str, ...]] = {
    "plain": (LENS_PLATE,),
    "open": (LENS_STREAMS,),
    "deep": (LENS_STREAMS,),
}

# The area the exposure default reads from. ``default`` is the #34
# openness area (interaction_model.DEFAULT_AREA) — the read-path's home
# for an un-area-specific user.
_EXPOSURE_AREA = "default"
_EXPOSURE_AXIS = "technical-exposure"


def _exposure_default_set(model: Any) -> tuple[str, ...]:
    """The NON-EMPTY default lens-set derived from technical-exposure.

    Reads the ``default`` area's ``technical-exposure`` cell via
    ``cell_or_prior`` (which itself degrades to the ``open`` openness prior
    when absent — so an un-seeded user lands on the work-streams default,
    never empty). NEVER returns an empty set (the anti-regression floor)."""
    try:
        exposure = (
            getattr(
                model.cell_or_prior(_EXPOSURE_AREA, _EXPOSURE_AXIS), "value", ""
            )
            or ""
        ).strip().lower()
    except Exception:  # noqa: BLE001 — fail-open to the always-on floor
        return DEFAULT_ALWAYS_ON_SET
    derived = _EXPOSURE_DEFAULT_LENS.get(exposure)
    if derived:
        return derived
    # An unrecognised exposure value -> the broadest openness default
    # (never empty).
    return (LENS_STREAMS,)


# ====================================================================
# The RESOLVER (D-WMS6.1 / D-WMS6.2 / AC.CHOICE.*)
# ====================================================================


def resolve_lens_set(
    claude_home: Path | str | None = None,
) -> tuple[str, ...]:
    """Resolve the lens-SET that surfaces by DEFAULT per-turn for this user.

    Reads the #34 ``work-tracking`` / ``preferred-lens`` cell via
    ``InteractionModel.cell_or_prior`` (the SAME path intake.py uses):

      - a recognised cell value -> the lens-set it maps to (AC.CHOICE.1);
      - an absent / unrecognised value -> the NON-EMPTY exposure-derived
        default (plain -> on-my-plate, open -> work-streams — AC.CHOICE.2 /
        D-WMS6.5);
      - any loader/parse error -> the always-on floor (AC.CHOICE.3).

    Deterministic — NO model call on the per-turn path (D-WMS6.2, mirrors
    ``classify_area``). NEVER raises and NEVER returns an empty set (the
    anti-regression floor — RF #3). Performs NO store mutation."""
    try:
        from .interaction_model import load_interaction_model  # noqa: WPS433

        model = load_interaction_model(claude_home)
        cell = model.cell(LENS_CHOICE_AREA, LENS_CHOICE_AXIS)
        value = (getattr(cell, "value", "") or "").strip() if cell else ""
        if value:
            chosen = _parse_lens_value(value)
            if chosen:
                return chosen
        # No explicit choice (or an unrecognised value) -> the
        # exposure-derived default (never empty).
        derived = _exposure_default_set(model)
        return derived if derived else DEFAULT_ALWAYS_ON_SET
    except Exception:  # noqa: BLE001 — fail-open to the always-on floor
        return DEFAULT_ALWAYS_ON_SET


# ====================================================================
# The per-lens REGISTRARS (compose the built lens entry points read-only)
# ====================================================================
#
# Each registrar registers ONE lens as a TriggerKind.turn contributor
# under its canonical block name. The inc-1/2/4 lenses ship their own
# register_*_contributor; the inc-5 on-demand lenses (plate/goals/
# waiting-on) ship only render_*_block, so this module wraps their render
# entry point in a thin turn-contributor (composing the built render path
# read-only — it adds no new render logic, AC.SURFACE.2). The store is read
# READ-ONLY through the chosen lens's existing API.


def _register_streams(composer: Any, *, tracker_factory: Any = None) -> None:
    from .work_streams_surface import (  # noqa: WPS433
        register_work_streams_contributor,
    )

    register_work_streams_contributor(composer)


def _register_projects(composer: Any, *, tracker_factory: Any = None) -> None:
    from .projects import register_projects_contributor  # noqa: WPS433

    register_projects_contributor(composer, tracker_factory=tracker_factory)


def _register_relational(composer: Any, *, tracker_factory: Any = None) -> None:
    from .relational import register_relational_contributor  # noqa: WPS433

    register_relational_contributor(composer, tracker_factory=tracker_factory)


def _make_render_contributor(
    render_fn: Callable[..., str], *, tracker_factory: Any = None
) -> Callable[[dict], str]:
    """Wrap an inc-5 on-demand render_*_block in a fail-soft turn
    contributor (composes the built render path read-only — no new render
    logic). Returns ``""`` on any boundary error so the turn proceeds."""

    def _contributor(_envelope: dict) -> str:
        try:
            return render_fn(tracker_factory=tracker_factory) or ""
        except Exception:  # noqa: BLE001 — AC46.2 graceful empty
            return ""

    return _contributor


def _register_plate(composer: Any, *, tracker_factory: Any = None) -> None:
    from ..context_composer import TriggerKind  # noqa: WPS433
    from .plate import render_plate_block  # noqa: WPS433

    composer.register(
        name=LENS_PLATE,
        trigger_kind=TriggerKind.turn,
        fn=_make_render_contributor(
            render_plate_block, tracker_factory=tracker_factory
        ),
    )


def _register_goals(composer: Any, *, tracker_factory: Any = None) -> None:
    from ..context_composer import TriggerKind  # noqa: WPS433
    from .goals import render_goals_block  # noqa: WPS433

    composer.register(
        name=LENS_GOALS,
        trigger_kind=TriggerKind.turn,
        fn=_make_render_contributor(
            render_goals_block, tracker_factory=tracker_factory
        ),
    )


def _register_waiting(composer: Any, *, tracker_factory: Any = None) -> None:
    from ..context_composer import TriggerKind  # noqa: WPS433
    from .waiting_on import render_waiting_on_block  # noqa: WPS433

    composer.register(
        name=LENS_WAITING,
        trigger_kind=TriggerKind.turn,
        fn=_make_render_contributor(
            render_waiting_on_block, tracker_factory=tracker_factory
        ),
    )


_LENS_REGISTRARS: dict[str, Callable[..., None]] = {
    LENS_STREAMS: _register_streams,
    LENS_PROJECTS: _register_projects,
    LENS_RELATIONAL: _register_relational,
    LENS_PLATE: _register_plate,
    LENS_GOALS: _register_goals,
    LENS_WAITING: _register_waiting,
}


# ====================================================================
# The choice-aware REGISTRATION (AC.SURFACE.*)
# ====================================================================


def register_chosen_lenses(
    composer: Any,
    *,
    claude_home: Path | str | None = None,
    tracker_factory: Any = None,
) -> tuple[str, ...]:
    """Register exactly the CHOSEN lens(es) as TriggerKind.turn blocks.

    Resolves the user's lens-set and registers only those lenses — the
    per-turn surface = the chosen set (AC.SURFACE.1), block-count = set-size
    (AC.SURFACE.3). The un-chosen lenses are NOT registered here; their
    on-demand render entry points are unchanged (AC.SURFACE.2).

    Fail-OPEN: any resolver error, an empty resolved set, or a per-lens
    registration error degrades to the current always-on
    :data:`DEFAULT_ALWAYS_ON_SET` (the inc-4 trio) — NEVER to zero blocks
    (AC.SURFACE.4 / §8 #3). Returns the set actually registered."""
    try:
        chosen = resolve_lens_set(claude_home)
    except Exception:  # noqa: BLE001 — fail-open to the always-on floor
        chosen = DEFAULT_ALWAYS_ON_SET
    if not chosen:
        chosen = DEFAULT_ALWAYS_ON_SET

    registered = _register_set(composer, chosen, tracker_factory=tracker_factory)
    if not registered:
        # Every chosen lens failed to register (or the set was unknown) —
        # fall open to the trio so the user never loses their surface.
        registered = _register_set(
            composer, DEFAULT_ALWAYS_ON_SET, tracker_factory=tracker_factory
        )
    return registered


def _register_set(
    composer: Any, lenses: tuple[str, ...], *, tracker_factory: Any = None
) -> tuple[str, ...]:
    """Register each lens in ``lenses`` fail-soft; return the names that
    actually registered (a per-lens registration error is skipped, not
    fatal — the surface still carries the lenses that registered)."""
    registered: list[str] = []
    for lens in lenses:
        registrar = _LENS_REGISTRARS.get(lens)
        if registrar is None:
            continue
        try:
            registrar(composer, tracker_factory=tracker_factory)
            registered.append(lens)
        except Exception:  # noqa: BLE001 — AC46.2 graceful empty per lens
            continue
    return tuple(registered)


# ====================================================================
# The SWITCH WRITER (D-WMS6.4 / D-WMS6.6 / AC.SWITCH.*)
# ====================================================================
#
# Persists the work-tracking/preferred-lens cell by re-emitting the matrix
# in the seed-writer line-shape via interaction_model.render_matrix +
# Cell(value=<lens>, confidence=high, locked=True). It deliberately does
# NOT call apply_override (which rejects the work-tracking area, line 694)
# and does NOT widen AIM_AREAS or touch the seed-writer. parse_matrix
# accepts the forward-compat work-tracking area (setdefault), and
# render_matrix preserves extra areas (the canonical-order tail), so the
# cell round-trips through the live reader (AC.SWITCH.2).


@dataclass
class LensSwitchResult:
    """The outcome of a lens switch (AC.SWITCH.1/.2/.3)."""

    ok: bool
    lens_set: tuple[str, ...]
    path: Path
    confirmation: str = ""
    reason: str = ""


def write_lens_choice(
    *,
    lenses: tuple[str, ...],
    claude_home: Path | str | None = None,
) -> LensSwitchResult:
    """Persist the work-tracking/preferred-lens cell for ``lenses``.

    Re-emits the live matrix with a ``work-tracking`` / ``preferred-lens``
    Cell carrying the chosen lens-set as a ``+``-joined value, at
    ``confidence: high`` + ``locked: true`` (the explicit-statement marker,
    D-WMS6.6 — honoured over the exposure-derived default, AC.SWITCH.4).
    Does NOT route through ``apply_override`` and does NOT widen the #34
    taxonomy (D-WMS6.4 / AC.SWITCH.2). When the matrix file does not yet
    exist (pre-seed), seeds a minimal matrix carrying just the cell."""
    from .interaction_model import (  # noqa: WPS433
        Cell,
        default_interaction_model_path,
        load_interaction_model,
        render_matrix,
    )

    path = default_interaction_model_path(claude_home)
    if not lenses:
        return LensSwitchResult(
            ok=False, lens_set=(), path=path, reason="no lens given"
        )

    value = "+".join(lenses)
    try:
        model = load_interaction_model(claude_home)
        model.areas.setdefault(LENS_CHOICE_AREA, {})
        model.areas[LENS_CHOICE_AREA][LENS_CHOICE_AXIS] = Cell(
            value=value, confidence="high", evidence=(), locked=True
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_matrix(model) + "\n", encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        return LensSwitchResult(
            ok=False, lens_set=lenses, path=path, reason=f"write failed: {exc!r}"
        )
    return LensSwitchResult(
        ok=True,
        lens_set=lenses,
        path=path,
        confirmation=confirm_switch_phrase(lenses),
    )


# ====================================================================
# The plain-language switch handler (D-WMS6.6 / AC.SWITCH.1/.3)
# ====================================================================
#
# A plain-language ask ("just show me what's on my plate" / "I think in
# projects") IS an explicit user statement — the highest-confidence,
# classifier-free #34 signal that hard-sets a cell. The handler maps the
# ask to a lens-set, writes the cell, and returns a plain-language
# confirmation. The write is owner-INITIATED (the user asked); the plain
# confirm is the verify-before-write step (the prime-directive loop), so it
# needs no separate ratification gate. DETERMINISTIC keyword map — NO model
# call (the switch fires on an explicit ask, not a per-turn inference).

# Plain-language phrase -> lens. Ordered: a more specific phrase wins. The
# map is small + plain (calibrate-on-use, RF #5).
_SWITCH_PHRASES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("on my plate", "my plate", "what's on my plate", "whats on my plate",
      "what i should do", "what to do now", "simplest", "just the next",
      "one thing"), LENS_PLATE),
    (("think in projects", "by project", "in projects", "project view",
      "organize by project", "group by project"), LENS_PROJECTS),
    (("work streams", "work-streams", "by stream", "across streams",
      "the streams", "everything at once", "the broad view",
      "all my work"), LENS_STREAMS),
    (("waiting on", "what i'm waiting on", "what im waiting on",
      "blocked on", "waiting for"), LENS_WAITING),
    (("toward my goals", "by goal", "goal", "goals", "what advances"),
     LENS_GOALS),
    (("relationships", "relational", "who owes", "who's waiting on me",
      "whos waiting on me"), LENS_RELATIONAL),
)


def lens_from_preference_text(text: str) -> tuple[str, ...]:
    """Map a plain-language preference statement to a lens-SET.

    Deterministic phrase match (NO model call, D-WMS6.6). Returns an empty
    tuple when no phrase matches — the caller then declines the switch (the
    persona asks plainly rather than guessing)."""
    lowered = (text or "").strip().lower()
    if not lowered:
        return ()
    for phrases, lens in _SWITCH_PHRASES:
        for phrase in phrases:
            if phrase in lowered:
                return (lens,)
    return ()


def apply_lens_switch(
    *,
    preference_text: Optional[str] = None,
    lens: Optional[str] = None,
    lenses: Optional[tuple[str, ...]] = None,
    claude_home: Path | str | None = None,
) -> LensSwitchResult:
    """Switch the user's lens from a plain-language ask OR an explicit lens.

    Resolves the target lens-set from (in precedence): an explicit
    ``lenses`` tuple, an explicit single ``lens``, or a plain-language
    ``preference_text``. Persists the cell via :func:`write_lens_choice` so
    the NEXT turn's resolver returns the switched-to set (AC.SWITCH.1) and
    returns a plain-language confirmation (AC.SWITCH.3). Declines (``ok=
    False``, no write) when no lens can be resolved from the ask."""
    target: tuple[str, ...] = ()
    if lenses:
        target = tuple(le for le in lenses if le in _ALL_LENSES)
    elif lens:
        target = (lens,) if lens in _ALL_LENSES else ()
    elif preference_text:
        target = lens_from_preference_text(preference_text)

    if not target:
        path = _path_for(claude_home)
        return LensSwitchResult(
            ok=False,
            lens_set=(),
            path=path,
            reason="could not resolve a lens from the request",
        )
    return write_lens_choice(lenses=target, claude_home=claude_home)


def _path_for(claude_home: Path | str | None) -> Path:
    from .interaction_model import (  # noqa: WPS433
        default_interaction_model_path,
    )

    return default_interaction_model_path(claude_home)


# ====================================================================
# The plain-language confirmation (AC.SWITCH.3 — zero internal vocab)
# ====================================================================
#
# The user-facing acknowledgement of the new framing. ZERO internal
# vocabulary by construction — no axis names, cell values, slugs, paths, or
# enums. Mirrors the #34 inspect/inject plain-by-construction discipline.

_LENS_PHRASE: dict[str, str] = {
    LENS_PLATE: "lead with what's on your plate",
    LENS_PROJECTS: "organize what I show you around your projects",
    LENS_STREAMS: "lay out your work across all its threads",
    LENS_RELATIONAL: "lead with what's blocked and who owes what",
    LENS_GOALS: "lead with how your work ladders up to your goals",
    LENS_WAITING: "lead with what you're waiting on",
}


def confirm_switch_phrase(lenses: tuple[str, ...]) -> str:
    """A plain-language confirmation of the new framing (AC.SWITCH.3).

    Carries NO internal vocabulary — a human-readable acknowledgement only.
    Composes a multi-select choice with a plain "and"."""
    phrases = [_LENS_PHRASE.get(le, "show your work the way that fits") for le in lenses]
    if not phrases:
        return "Okay — I'll keep showing your work the way I have been."
    if len(phrases) == 1:
        body = phrases[0]
    elif len(phrases) == 2:
        body = f"{phrases[0]} and {phrases[1]}"
    else:
        body = ", ".join(phrases[:-1]) + f", and {phrases[-1]}"
    return f"Okay — from now on I'll {body}."
