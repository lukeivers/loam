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

"""N4 — the MVP user-model: read the N3-seeded AIM matrix, classify the
live work-anchor to an area, inject the per-area cell, and give the user
the controls (explicit-override + plain-language inspect + FBM rule
auto-weight infer-and-surface).

This is the adaptive-interaction-model's FIRST functioning brick (the
PRIME DIRECTIVE / Lens 0 — per-user-tuned translation): N3 seeds the
openness-biased prior matrix at ``confidence: prior``; N4 makes that
prior STEER BEHAVIOUR every turn and lets the user drive it directly.

**The read contract (D-rec-1).** The matrix file format is a PREDECESSOR
contract owned by the N3 seed-writer
(``workspace_bootstrap.seed_writer.render_interaction_model``): a
``## <area>`` header per area, then one line per axis in the exact shape

    <axis>: { value: <v>, confidence: <c>, evidence: [<...>] }

over ``AIM_AREAS`` (6 areas) and the four axes (technical-exposure,
autonomy, tone, learning-appetite). N4 binds a READER to this format; it
does NOT re-seed or re-shape it (a format change is an N3 regression —
OUT of N4's fence). The override WRITER re-emits the same line shape so a
hand-set cell round-trips through the same reader.

**The MVP cut (design §8 AIM-1/2/3).** N4 reads + injects the
``technical-exposure`` + ``autonomy`` cell (the two-axis MVP). The
behavioural auto-learn engine (signal counters, hysteresis,
fast-down-on-distress, weekly re-eval, the tone + learning-appetite
adaptive axes) is the LATER remainder (AIM-4..8) — explicitly OUT. In
this slice **cells move ONLY by explicit user statement** (override); no
behavioural signal writes a cell (D-rec-3, the MVP fence — AC.UM.FENCE.1).

**Fail-open (G5 / AC.UM.READ.2).** Any matrix error (missing, unreadable,
malformed) degrades to the openness prior: the read-path emits no
injection and the turn proceeds exactly as the un-personalized keep-pace
chain does today. Openness applies to TALKING (exposure), never to
consequence-bearing ACTING — the autonomy floor stays at the seeded
cautious value for the consequence-bearing areas.

Stdlib-only. Fail-soft throughout (composes with the chain's
fail-open-whole-chain guarantee, AC.KP0.4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .work_anchor import WorkAnchor


# ====================================================================
# The matrix taxonomy (predecessor contract — mirrors the seed-writer)
# ====================================================================
#
# These mirror ``seed_writer.AIM_AREAS`` + the four axes WITHOUT importing
# across the package boundary on the live hot path (the seed-writer lives
# in workspace-bootstrap; a runtime import from a live hook is the exact
# wedge-the-turn risk the chain's fail-soft discipline exists to avoid).
# The values are the read contract, asserted equal to the seed-writer's
# by a co-located test (AC.UM.AREA.1 taxonomy-binding) so a drift in the
# seed-writer is caught, not silently tolerated.

AIM_AREAS: tuple[str, ...] = (
    "harness-mechanics",
    "code-and-builds",
    "their-domain-work",
    "ops-and-money",
    "decisions-and-tradeoffs",
    "default",
)

AIM_AXES: tuple[str, ...] = (
    "technical-exposure",
    "autonomy",
    "tone",
    "learning-appetite",
)

# The area the read-path falls open to (AC.UM.AREA.2) and the area a
# missing/garbled matrix degrades to (AC.UM.READ.2). The openness prior.
DEFAULT_AREA = "default"

# The two axes the MVP read-path injects (design §8 — the two-axis MVP).
# tone + learning-appetite are SEEDED + READABLE (inspect renders them)
# but not adaptively MOVED in this slice (AIM-6, OUT).
INJECTED_AXES: tuple[str, ...] = ("technical-exposure", "autonomy")

# The openness-prior cell values the read-path degrades to when the
# matrix is absent/garbled (G5 — never escalate exposure beyond the
# seeded prior; the autonomy prior is the SAFE cautious value, never the
# bold one, so a degraded read never bumps consequence-bearing autonomy).
_PRIOR_EXPOSURE = "open"
_PRIOR_AUTONOMY = "surface"


# ====================================================================
# The cell + the parsed matrix
# ====================================================================


@dataclass
class Cell:
    """One (area, axis) cell: value + confidence + evidence + lock.

    Mirrors the seed-writer's per-cell shape
    ``{ value, confidence, evidence: [] }`` and ADDS the ``locked``
    marker N4's explicit-override records (D-N4.3) — forward-compatible
    with AIM-4's "never silently override a stated preference."
    """

    value: str
    confidence: str = "prior"
    evidence: tuple[str, ...] = ()
    locked: bool = False

    def render_line(self, axis: str) -> str:
        """Re-emit this cell as the seed-writer's matrix line shape.

        ``<axis>: { value: <v>, confidence: <c>, evidence: [<...>], locked: <b> }``
        The ``locked`` key is appended only when True so an un-locked
        prior cell round-trips byte-identically to the seed-writer's
        output (no spurious diff against a freshly-seeded matrix).
        """
        ev = ", ".join(self.evidence)
        line = (
            f"{axis}: {{ value: {self.value}, confidence: {self.confidence}, "
            f"evidence: [{ev}]"
        )
        if self.locked:
            line += ", locked: true"
        line += " }"
        return line


@dataclass
class InteractionModel:
    """The parsed AIM matrix: area -> axis -> Cell.

    Built by :func:`parse_matrix` from the seed-writer's markdown. A
    missing area or axis is absent from the dict (the reader degrades to
    the openness prior for it — never raises).
    """

    areas: dict[str, dict[str, Cell]] = field(default_factory=dict)

    def cell(self, area: str, axis: str) -> Optional[Cell]:
        return self.areas.get(area, {}).get(axis)

    def cell_or_prior(self, area: str, axis: str) -> Cell:
        """The cell for (area, axis), or the openness-prior cell.

        AC.UM.READ.2 / G5 — a missing cell degrades to the openness
        prior: ``open`` exposure, the cautious ``surface`` autonomy
        (never the bold value), at ``confidence: prior``.
        """
        c = self.cell(area, axis)
        if c is not None:
            return c
        if axis == "technical-exposure":
            return Cell(value=_PRIOR_EXPOSURE)
        if axis == "autonomy":
            return Cell(value=_PRIOR_AUTONOMY)
        return Cell(value="")


# ====================================================================
# Parse — bind a READER to the seed-writer's matrix format
# ====================================================================

_AREA_HEADER_RE = re.compile(r"^##\s+(.+?)\s*$")
# An axis line: ``<axis>: { value: <v>, confidence: <c>, evidence: [...] }``
# Tolerant of extra whitespace + an optional trailing ``locked: true`` key.
_AXIS_LINE_RE = re.compile(
    r"^([A-Za-z][A-Za-z0-9_-]*):\s*\{\s*(.*?)\s*\}\s*$"
)
_KV_INNER_RE = re.compile(r"([A-Za-z_-]+)\s*:\s*([^,]*?)(?:,|$)")


def parse_matrix(text: str) -> InteractionModel:
    """Parse the seed-writer's AIM matrix markdown into an InteractionModel.

    Binds to ``render_interaction_model()``'s format (the read contract):
    ``## <area>`` headers, each followed by per-axis ``<axis>: { value:
    <v>, confidence: <c>, evidence: [...] }`` lines. Tolerant + fail-soft:

    - lines outside any ``## <area>`` section (the ``# interaction-model``
      title + the HTML comment) are ignored;
    - an axis name not in :data:`AIM_AXES` is still parsed (forward-compat
      with a seed-writer that grows an axis) but never injected;
    - a malformed axis line is skipped (the cell degrades to the prior);
    - ``evidence`` is parsed as a comma-list inside ``[...]``;
    - ``locked: true`` is recognised so an overridden cell round-trips.

    NEVER raises — a wholly-garbled input yields an empty model whose
    every cell resolves to the openness prior (AC.UM.READ.2).
    """
    model = InteractionModel()
    current_area: Optional[str] = None
    try:
        for raw in text.splitlines():
            header = _AREA_HEADER_RE.match(raw)
            if header:
                current_area = header.group(1).strip()
                model.areas.setdefault(current_area, {})
                continue
            if current_area is None:
                continue
            line = _AXIS_LINE_RE.match(raw.strip())
            if not line:
                continue
            axis = line.group(1).strip()
            inner = line.group(2)
            cell = _parse_cell_inner(inner)
            if cell is not None:
                model.areas[current_area][axis] = cell
    except Exception:  # noqa: BLE001 — fail-soft; degrade to prior
        return model
    return model


def _parse_cell_inner(inner: str) -> Optional[Cell]:
    """Parse the ``{ ... }`` body of an axis line into a Cell.

    The body holds ``value: <v>``, ``confidence: <c>``,
    ``evidence: [<...>]``, and optionally ``locked: true``. The
    ``evidence`` value is the bracketed list (which may itself contain
    commas), so it is extracted directly rather than via the comma-split
    KV scan. Returns ``None`` only when no ``value`` is present.
    """
    value = ""
    confidence = "prior"
    evidence: tuple[str, ...] = ()
    locked = False

    # evidence: [ ... ] — extract the bracketed list verbatim first.
    ev_match = re.search(r"evidence\s*:\s*\[(.*?)\]", inner)
    if ev_match:
        body = ev_match.group(1).strip()
        if body:
            evidence = tuple(
                e.strip() for e in body.split(",") if e.strip()
            )
        # Blank out the evidence span so the KV scan below doesn't trip
        # on commas inside the list.
        inner = inner[: ev_match.start()] + inner[ev_match.end():]

    for m in _KV_INNER_RE.finditer(inner):
        key = m.group(1).strip().lower()
        val = m.group(2).strip()
        if key == "value":
            value = val
        elif key == "confidence":
            confidence = val or "prior"
        elif key == "locked":
            locked = val.lower() in {"true", "yes", "1"}

    if not value:
        return None
    return Cell(
        value=value, confidence=confidence, evidence=evidence, locked=locked
    )


def render_matrix(model: InteractionModel) -> str:
    """Re-render an InteractionModel back to the seed-writer's markdown.

    Used by the override WRITER (AC.UM.OVR.1) so a hard-set cell persists
    in the exact format the reader binds to. Preserves the seed-writer's
    header + comment + area/axis order so the file stays diff-stable and
    inherits the FBM budget discipline. Areas + axes are emitted in the
    canonical :data:`AIM_AREAS` / :data:`AIM_AXES` order; any extra
    area/axis the model carries (forward-compat) is appended after.
    """
    lines: list[str] = [
        "# interaction-model",
        "",
        (
            "<!-- The per-user interaction model (AIM matrix): "
            "component-area x axis -> {value, confidence, evidence}. "
            "SEEDED by N3 onboarding at confidence: prior (the openness-biased "
            "default — assume an engaged learner who wants to grow). N4 moves "
            "the cells from evidence; confidence climbs prior -> low -> medium "
            "-> high. `confidence: prior` means no evidence yet. -->"
        ),
        "",
    ]
    seen_areas: set[str] = set()
    ordered_areas = list(AIM_AREAS) + [
        a for a in model.areas if a not in AIM_AREAS
    ]
    for area in ordered_areas:
        if area not in model.areas or area in seen_areas:
            continue
        seen_areas.add(area)
        lines.append(f"## {area}")
        axes = model.areas[area]
        ordered_axes = list(AIM_AXES) + [
            ax for ax in axes if ax not in AIM_AXES
        ]
        seen_axes: set[str] = set()
        for axis in ordered_axes:
            if axis not in axes or axis in seen_axes:
                continue
            seen_axes.add(axis)
            lines.append(axes[axis].render_line(axis))
        lines.append("")
    return "\n".join(lines)


# ====================================================================
# Load — read the live matrix file (fail-open to the openness prior)
# ====================================================================


def default_interaction_model_path(claude_home: Path | str | None = None) -> Path:
    """Resolve the user-scope ``INTERACTION-MODEL.md`` path.

    Default base is ``~/.claude/`` (where the N3 seed-writer writes it);
    an explicit ``claude_home`` lets a test point at a tmp fixture home
    (the outcome-altitude AC.UM.READ.4 seeds an isolated fixture matrix,
    never the developer's real home).
    """
    base = (
        Path(claude_home)
        if claude_home is not None
        else Path.home() / ".claude"
    )
    return base / "INTERACTION-MODEL.md"


def load_interaction_model(
    claude_home: Path | str | None = None,
) -> InteractionModel:
    """Load + parse the live AIM matrix, fail-open to an empty model.

    AC.UM.READ.2: a missing / unreadable / malformed file yields an
    EMPTY :class:`InteractionModel` whose every cell resolves to the
    openness prior — the turn proceeds exactly as the un-personalized
    chain does today. NEVER raises.
    """
    path = default_interaction_model_path(claude_home)
    try:
        if not path.is_file():
            return InteractionModel()
        return parse_matrix(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — fail-open to the openness prior
        return InteractionModel()


# ====================================================================
# Area classifier (D-N4.1 — DETERMINISTIC, fail-open to default)
# ====================================================================
#
# D-N4.1 RULED: a deterministic keyword/objective-tag map over the
# already-built WorkAnchor (NO LLM call on the hot path — the design
# §4b forbids model-decides-each-turn; the hook fires every turn and must
# fail-open). The taxonomy is coarse (6 buckets) so a mis-route is
# low-harm + self-correcting (AC.UM.AREA.2), and the override + inspect
# paths are the user's recourse. This is the single biggest N4 design
# risk (signal-classification accuracy is unverified, design §7) — coarse
# + fail-open-to-default is the mitigation.
#
# The classifier reads the EXISTING WorkAnchor (AC.UM.AREA.3 — no
# recompute of objective/subgoal/last-topic); it only TAGS it.

# Per-area keyword sets (lowercased single tokens). A token matched in any
# anchor component routes to that area. Ordered by precedence: the more
# specific consequence-bearing areas (ops-and-money,
# decisions-and-tradeoffs) win ties over the broader work areas so a
# money/decision turn never under-routes to the bold default.
_AREA_KEYWORDS: tuple[tuple[str, frozenset[str]], ...] = (
    (
        "ops-and-money",
        frozenset(
            {
                "money", "revenue", "income", "invest", "investing",
                "payment", "pay", "invoice", "billing", "budget", "cost",
                "price", "pricing", "purchase", "buy", "sell", "publish",
                "publishing", "deploy", "release", "production", "ship",
                "credentials", "secret", "token", "api", "account",
                "bank", "financial", "passive", "asset", "tax",
            }
        ),
    ),
    (
        "decisions-and-tradeoffs",
        frozenset(
            {
                "decide", "decision", "tradeoff", "tradeoffs", "choose",
                "choice", "strategy", "strategic", "prioritize",
                "priority", "roadmap", "plan", "weigh", "option",
                "options", "pivot", "risk", "recommend", "recommendation",
            }
        ),
    ),
    (
        "harness-mechanics",
        frozenset(
            {
                "loam", "hook", "hooks", "contributor", "keep_pace",
                "keep", "pace", "amendment", "amend", "seal", "manifest",
                "component", "persona", "harness", "telegram", "mcp",
                "dispatch", "agent", "memory", "corpus", "objective",
                "objectives", "skill", "settings", "matrix", "interaction",
            }
        ),
    ),
    (
        "code-and-builds",
        frozenset(
            {
                "code", "build", "builds", "test", "tests", "function",
                "module", "class", "bug", "fix", "refactor", "compile",
                "import", "python", "script", "implement", "implementation",
                "debug", "stack", "traceback", "lint", "type", "api",
            }
        ),
    ),
    (
        "their-domain-work",
        frozenset(
            {
                "litrpg", "novel", "novels", "chapter", "chapters",
                "fiction", "story", "prose", "canon", "character",
                "scene", "book", "books", "series", "manuscript", "draft",
                "edit", "narrative", "plot", "patch", "reality", "writer",
                "writing",
            }
        ),
    ),
)


def classify_area(anchor: WorkAnchor) -> str:
    """Map a WorkAnchor to exactly one AIM area slug (D-N4.1).

    AC.UM.AREA.1: resolves to one slug from :data:`AIM_AREAS`.
    AC.UM.AREA.2: a no-match / low-confidence anchor resolves to
    :data:`DEFAULT_AREA` (the openness prior — a mis-route is low-harm).
    AC.UM.AREA.3: reads the EXISTING anchor (its tokens), does NOT
    recompute it.

    Deterministic keyword scoring: each area's keyword set is matched
    against the anchor's full token set (prompt + objective + subgoal +
    last-topic). The area with the most matched keywords wins; ties break
    by the precedence order in :data:`_AREA_KEYWORDS` (the
    consequence-bearing areas first, so a money/decision turn never
    under-routes). No keyword match => ``default``. NEVER raises.
    """
    try:
        tokens = set(anchor.query_tokens())
        if not tokens:
            return DEFAULT_AREA
        best_area = DEFAULT_AREA
        best_score = 0
        for area, keywords in _AREA_KEYWORDS:
            score = len(tokens & keywords)
            if score > best_score:
                best_score = score
                best_area = area
        return best_area
    except Exception:  # noqa: BLE001 — fail-open to default
        return DEFAULT_AREA


# ====================================================================
# The injection (AC.UM.READ.1/.3 — clean, plain, no mechanism-leak)
# ====================================================================
#
# AC.UM.READ.3: the injected directive carries NO raw file content, NO
# mechanism narration ("I raised your exposure cell"), NO SHAs / paths /
# axis-jargon in the user-visible register — it is a plain behavioural
# directive the persona acts on (design §4a "clean, no disclaimer
# wrapper" + §5 "never narrates its own mechanism"). The syntactic-leak
# floor (no SHAs/paths/IDs) survives unconditionally regardless of any
# cell value (G5 doubt 4) — these directive strings are authored
# plain-by-construction so they pass KP9's Layer-1 lint.

# Per-value behavioural directive for the technical-exposure axis. The
# SUBSTANCE is always exposed (G5 openness-default); only the VOCABULARY
# / depth adapts. There is no "hide the substance" value — the lowest
# exposure still answers fully, just in plainer words.
_EXPOSURE_DIRECTIVE: dict[str, str] = {
    "plain": (
        "For this kind of work, lead in plain language — give the full "
        "answer, but keep the wording everyday and spell out any term "
        "before leaning on it."
    ),
    "open": (
        "For this kind of work, give the full answer in clear language and "
        "introduce the technical terms as you use them — the substance is "
        "always on the table."
    ),
    "deep": (
        "For this kind of work, go deep — full technical depth is welcome, "
        "name the mechanisms directly, and don't pre-simplify."
    ),
}

# Per-value behavioural directive for the autonomy axis. Openness applies
# to TALKING, never to consequence-bearing ACTING — so the cautious
# values genuinely gate action (surface-before-acting), not just tone.
_AUTONOMY_DIRECTIVE: dict[str, str] = {
    "surface": (
        "Before taking any consequence-bearing action here, surface the "
        "plan and what it touches first — this area carries real-world "
        "weight, so confirm before acting."
    ),
    "recommend": (
        "Here, recommend a clear next step and proceed on the low-risk "
        "parts; pause to confirm only the consequence-bearing moves."
    ),
    "act": (
        "Here, act on the confident path without a check-in; surface only "
        "a genuine fork or a true blocker."
    ),
}


def render_injection(model: InteractionModel, area: str) -> str:
    """Render the per-area exposure + autonomy cell as a plain directive.

    AC.UM.READ.1: emits the area's ``technical-exposure`` + ``autonomy``
    cell values as a terse, plain-language behavioural directive.
    AC.UM.READ.3: NO raw file content, NO mechanism narration, NO axis
    jargon / SHAs / paths in the user-visible register — authored
    plain-by-construction. Returns ``""`` when neither axis yields a
    directive (so a fully-degraded read injects nothing — the
    no-regression path, AC.UM.READ.2).

    The block is unlabelled-by-mechanism: a terse ``[interaction]`` tag
    (the same plain-block convention KP1's ``[keep-pace]`` uses) carrying
    the directive, never "your exposure cell is X."
    """
    exposure = model.cell_or_prior(area, "technical-exposure").value
    autonomy = model.cell_or_prior(area, "autonomy").value
    parts: list[str] = []
    exp_dir = _EXPOSURE_DIRECTIVE.get(exposure)
    if exp_dir:
        parts.append(exp_dir)
    aut_dir = _AUTONOMY_DIRECTIVE.get(autonomy)
    if aut_dir:
        parts.append(aut_dir)
    if not parts:
        return ""
    lines = ["[interaction] How to pitch this turn:"]
    for p in parts:
        lines.append(f"  - {p}")
    return "\n".join(lines)


# ====================================================================
# Inspect (AC.UM.INSP.* — render the cells in PROSE, never the raw file)
# ====================================================================
#
# Design §5: the system explaining itself is the HIGHEST-RISK leak
# surface — so inspect renders the per-area stance as plain-language
# prose, never the raw matrix or axis-jargon. The prose reads the LIVE
# file (AC.UM.INSP.2 — truthful to the file, so an inspect after an
# override reflects the override).

# Plain-language descriptions of each axis VALUE for the inspect prose.
# These describe the STANCE in user-words, never the axis name or value
# token (those are mechanism). Keyed (axis, value).
_INSPECT_EXPOSURE: dict[str, str] = {
    "plain": "I keep the wording everyday and spell terms out",
    "open": "I use clear language and introduce technical terms as they come up",
    "deep": "I go to full technical depth without pre-simplifying",
}
_INSPECT_AUTONOMY: dict[str, str] = {
    "surface": "I check the plan with you before any consequence-bearing move",
    "recommend": "I recommend a next step and handle the low-risk parts myself",
    "act": "I act on the confident path and only flag a real fork",
}

# Human-readable area names for the inspect prose (never the slug).
_AREA_PROSE_NAME: dict[str, str] = {
    "harness-mechanics": "the tooling and how the assistant itself works",
    "code-and-builds": "code and builds",
    "their-domain-work": "your own domain work",
    "ops-and-money": "operations and money",
    "decisions-and-tradeoffs": "decisions and tradeoffs",
    "default": "everything else",
}


def render_inspect(
    model: InteractionModel, area: Optional[str] = None
) -> str:
    """Render the per-area stance as plain-language prose (AC.UM.INSP.1).

    When ``area`` is given, describes that one area; when ``None``,
    describes every area. PROSE only — never the raw matrix, never the
    axis name or value token (those are mechanism, design §5). Reads the
    live ``model`` so the description is truthful to the file
    (AC.UM.INSP.2 — reflects an override). Returns ``""`` only on a fully
    empty model with no area requested.
    """
    areas = [area] if area else [a for a in AIM_AREAS]
    out: list[str] = []
    for a in areas:
        name = _AREA_PROSE_NAME.get(a, a.replace("-", " "))
        exposure = model.cell_or_prior(a, "technical-exposure").value
        autonomy = model.cell_or_prior(a, "autonomy").value
        exp = _INSPECT_EXPOSURE.get(
            exposure, "I keep the substance fully on the table"
        )
        aut = _INSPECT_AUTONOMY.get(
            autonomy, "I confirm consequence-bearing moves with you"
        )
        out.append(f"On {name}: {exp}, and {aut}.")
    return "\n".join(out)


# ====================================================================
# Explicit-override (AC.UM.OVR.* — D-N4.3 hard-set + high + locked)
# ====================================================================
#
# D-N4.3 RULED: a stated preference hard-sets the cell value, bumps
# confidence to ``high``, and marks the cell ``locked`` — recorded NOW so
# the file is forward-compatible with AIM-4's "behavioural evidence can
# only PROMPT A RE-ASK, never silently override a stated preference."
# Nothing contends with the lock in N4 (the behavioural path is dark) —
# recording it is cheap + makes the file future-proof.
#
# The user's own statement is the highest-confidence, classifier-free
# signal (design §5/§7) — it carries early personalization SAFELY while
# the behavioural classifier is unproven. This is the ONLY path that
# moves a cell in N4 (the MVP fence, AC.UM.FENCE.1).

OVERRIDE_CONFIDENCE = "high"

# The valid value vocabulary per axis (override is validated against it —
# an unknown value is rejected so a fat-fingered override can't write
# garbage into the matrix).
_VALID_VALUES: dict[str, frozenset[str]] = {
    "technical-exposure": frozenset({"plain", "open", "deep"}),
    "autonomy": frozenset({"surface", "recommend", "act"}),
    "tone": frozenset({"plain-warm", "peer-warm", "crisp"}),
    "learning-appetite": frozenset({"minimal", "invite", "teach"}),
}


@dataclass
class OverrideResult:
    """The outcome of an explicit-override write (AC.UM.OVR.*)."""

    ok: bool
    area: str
    axis: str
    value: str
    path: Path
    reason: str = ""


def apply_override(
    *,
    area: str,
    axis: str,
    value: str,
    claude_home: Path | str | None = None,
) -> OverrideResult:
    """Hard-set one cell from a stated user preference (AC.UM.OVR.1/.2).

    Reads the live matrix, sets ``model[area][axis]`` to ``value`` at
    ``confidence: high`` with ``locked: true`` (D-N4.3), and persists the
    whole matrix back in the seed-writer's format (AC.UM.OVR.1 — survives
    the next read; AC.UM.OVR.3 round-trips through the live read-path).

    Validates ``area`` against :data:`AIM_AREAS` and ``value`` against the
    axis's vocabulary — a bad area/axis/value is REJECTED (``ok=False``,
    file untouched) so an override can never corrupt the matrix. When the
    matrix file does not yet exist (a fresh machine before the N3 seed),
    the override seeds a minimal matrix carrying just the overridden cell
    — the user's stated preference is honoured even pre-seed.
    """
    path = default_interaction_model_path(claude_home)
    if area not in AIM_AREAS:
        return OverrideResult(
            ok=False, area=area, axis=axis, value=value, path=path,
            reason=f"unknown area {area!r}",
        )
    valid = _VALID_VALUES.get(axis)
    if valid is None:
        return OverrideResult(
            ok=False, area=area, axis=axis, value=value, path=path,
            reason=f"unknown axis {axis!r}",
        )
    if value not in valid:
        return OverrideResult(
            ok=False, area=area, axis=axis, value=value, path=path,
            reason=f"value {value!r} not valid for {axis!r}",
        )

    model = load_interaction_model(claude_home)
    model.areas.setdefault(area, {})
    model.areas[area][axis] = Cell(
        value=value, confidence=OVERRIDE_CONFIDENCE, evidence=(), locked=True
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_matrix(model) + "\n", encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        return OverrideResult(
            ok=False, area=area, axis=axis, value=value, path=path,
            reason=f"write failed: {exc!r}",
        )
    return OverrideResult(
        ok=True, area=area, axis=axis, value=value, path=path
    )


# ====================================================================
# FBM rule auto-weighting (AC.UM.WT.* — D-N4.4 infer + surface, never silent)
# ====================================================================
#
# D-N4.4 RULED: infer a COARSE band (low / normal / high), ALWAYS surface
# for confirm, NEVER silent-write. This keeps auto-weighting INSIDE the
# MVP fence (a silent weight write is a behavioural-style auto-change —
# the exact thing the fence defers). N4 adds the infer + surface layer
# over the B1 ``weight:`` frontmatter MECHANISM (already built in
# corpus_index); it adds NO new weighting math.
#
# The aggressive auto-tune (move the weight from observed retrieval
# signal automatically) is LATER with the rest of the behavioural engine.

# The coarse bands -> the B1 weight value. ``normal`` maps to the B1
# BASELINE_WEIGHT (the no-op band — a normal-band confirm is byte-stable
# against an un-weighted doc). low/high are the two off-baseline bands.
WEIGHT_BANDS: dict[str, int] = {
    "low": 20,
    "normal": 50,   # == corpus_index.BASELINE_WEIGHT (the no-op band)
    "high": 80,
}


@dataclass
class WeightSuggestion:
    """An inferred-but-unconfirmed weight (AC.UM.WT.1 — surface, never write).

    Carries the inferred band + the B1 weight value it maps to + a
    plain-language rationale to surface for confirm. NOTHING is written
    until :func:`confirm_weight` is called (AC.UM.WT.3 — decline is a
    no-op).
    """

    doc_path: Path
    band: str
    weight: int
    rationale: str


def infer_weight_band(*, importance_signal: str) -> str:
    """Infer a coarse weight band from an importance signal (AC.UM.WT.1).

    Deterministic + coarse (D-N4.4) — maps a plain importance signal to
    one of low / normal / high. The signal is a free-text descriptor of
    the rule's importance (e.g. "load-bearing safety rule",
    "nice-to-have", "core directive"). Unknown / empty => ``normal`` (the
    no-op baseline band). This is the INFER half; the SURFACE half is
    :func:`suggest_weight`, and NOTHING writes until :func:`confirm_weight`.
    """
    sig = (importance_signal or "").lower()
    high_markers = (
        "load-bearing", "load bearing", "critical", "safety", "core",
        "prime", "directive", "always", "must", "hard rule", "foundational",
        "high",
    )
    low_markers = (
        "nice-to-have", "nice to have", "minor", "optional", "rarely",
        "low", "trivial", "cosmetic", "edge-case", "edge case",
    )
    if any(m in sig for m in high_markers):
        return "high"
    if any(m in sig for m in low_markers):
        return "low"
    return "normal"


def suggest_weight(
    *, doc_path: Path | str, importance_signal: str
) -> WeightSuggestion:
    """Infer a weight band + build the surface-for-confirm suggestion.

    AC.UM.WT.1: infers + SURFACES; writes NOTHING. The caller renders the
    ``rationale`` to the user and only on an explicit confirm calls
    :func:`confirm_weight`. The band maps to a B1 ``weight`` value via
    :data:`WEIGHT_BANDS` (``normal`` == BASELINE_WEIGHT, the no-op band).
    """
    band = infer_weight_band(importance_signal=importance_signal)
    weight = WEIGHT_BANDS[band]
    p = Path(doc_path)
    if band == "normal":
        rationale = (
            f"This rule looks like a normal-priority one, so I'd leave its "
            f"retrieval weight at the default. Want me to set it anyway?"
        )
    elif band == "high":
        rationale = (
            f"This rule reads as load-bearing, so I'd raise how strongly it "
            f"surfaces in recall (high). Want me to set that?"
        )
    else:
        rationale = (
            f"This rule reads as lower-priority, so I'd lower how strongly it "
            f"surfaces in recall (low). Want me to set that?"
        )
    return WeightSuggestion(
        doc_path=p, band=band, weight=weight, rationale=rationale
    )


# The B1 frontmatter regexes (mirror corpus_index — the WRITE side of the
# read mechanism). Kept self-contained here (the live hot path reads via
# corpus_index; this writer is the config arm, invoked only on a confirm).
_FM_BLOCK_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.DOTALL)
_FM_WEIGHT_LINE_RE = re.compile(r"^weight:.*$", re.MULTILINE)


def confirm_weight(
    *, doc_path: Path | str, weight: int
) -> bool:
    """Write the confirmed weight as B1 ``weight:`` frontmatter (AC.UM.WT.2).

    Called ONLY on an explicit user confirm of a :class:`WeightSuggestion`
    (AC.UM.WT.1 — never auto-called). Writes the B1-format ``weight:``
    frontmatter the existing ``corpus_index`` retrieval-boost reads — N4
    adds NO new weighting mechanism, only this infer+surface+confirm
    layer. If the doc already has a frontmatter block, the ``weight:``
    line is upserted into it; otherwise a minimal ``---`` block is
    prepended. Returns ``True`` on a successful write, ``False`` on error.

    AC.UM.WT.3: this is the ONLY write path — an un-confirmed suggestion
    never reaches here, so a declined surface leaves the doc byte-for-byte
    unchanged.
    """
    p = Path(doc_path)
    try:
        raw = p.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return False
    try:
        weight_line = f"weight: {int(weight)}"
        m = _FM_BLOCK_RE.match(raw)
        if m:
            block = m.group(1)
            if _FM_WEIGHT_LINE_RE.search(block):
                new_block = _FM_WEIGHT_LINE_RE.sub(weight_line, block, count=1)
            else:
                new_block = block.rstrip("\n") + "\n" + weight_line
            new_raw = f"---\n{new_block}\n---\n" + raw[m.end():]
        else:
            new_raw = f"---\n{weight_line}\n---\n" + raw
        p.write_text(new_raw, encoding="utf-8")
        return True
    except Exception:  # noqa: BLE001
        return False


# ====================================================================
# The read-path contributor (AC.UM.READ.* — the live-hook seam)
# ====================================================================


@dataclass
class InteractionModelConfig:
    """Resolution config for the read-path contributor.

    ``claude_home`` is injectable so the outcome-altitude AC.UM.READ.4
    seeds an ISOLATED fixture matrix (a tmp ``.claude`` home) and runs the
    REAL hook against it — never the developer's real home. ``None`` =>
    the live ``~/.claude`` home.
    """

    claude_home: Optional[Path] = None
    last_topic: str = ""


def _resolve_anchor(envelope: dict) -> WorkAnchor:
    """Build the WorkAnchor for this turn from the envelope.

    Reads the objectives FRESH (the same source KP1 uses), so the
    classifier tags against the live work — composing on, not recomputing,
    the anchor (AC.UM.AREA.3). Fail-soft: any error degrades to a
    prompt-only anchor (which routes to ``default`` if the prompt carries
    no area keyword).
    """
    prompt = ""
    last_topic = ""
    try:
        if isinstance(envelope, dict):
            prompt = str(envelope.get("prompt", "") or "")
            kp = envelope.get("keep_pace")
            if isinstance(kp, dict):
                last_topic = str(kp.get("last_topic", "") or "")
    except Exception:  # noqa: BLE001
        prompt = ""
    objective_texts: list[str] = []
    subgoals: list[str] = []
    try:
        from . import objectives as _objectives

        objs = _objectives.load_user_scope_register()
        objective_texts = _objectives.active_objective_texts(objs)
        subgoals = _objectives.active_subgoals(objs)
    except Exception:  # noqa: BLE001 — degrade to prompt-only anchor
        objective_texts = []
        subgoals = []
    return WorkAnchor(
        prompt=prompt,
        objective_texts=objective_texts,
        subgoals=subgoals,
        last_topic=last_topic,
    )


def build_interaction_model_contributor(
    config: Optional[InteractionModelConfig] = None,
) -> Callable[[dict], Optional[str]]:
    """Return the KP0-chain ``Contributor.fn``-compatible read-path callable.

    Shape matches the chain contract
    (``fn(envelope: dict) -> Optional[str]``). The live keep-pace
    ``contributors()`` list registers this (NO new hook — Lens 1). Per
    turn it:

      1. builds the WorkAnchor for the turn (composing the existing
         objectives source — AC.UM.AREA.3, no recompute);
      2. classifies it to one area slug (D-N4.1 deterministic, fail-open
         to ``default`` — AC.UM.AREA.1/.2);
      3. loads the live matrix (fail-open to the openness prior on any
         error — AC.UM.READ.2);
      4. injects the area's exposure + autonomy cell as a clean, plain
         behavioural directive (AC.UM.READ.1/.3).

    AC.UM.READ.4 (outcome-altitude): this IS the production entry-point
    the live hook reaches — given a seeded fixture matrix + a real
    envelope, it emits the correct per-area cell. Fail-soft: any error
    yields ``None`` (no injection) so the chain's fail-open-whole-chain
    guarantee holds (AC.KP0.4).
    """
    cfg = config if config is not None else InteractionModelConfig()

    def contributor(envelope: dict) -> Optional[str]:
        try:
            anchor = _resolve_anchor(envelope)
            area = classify_area(anchor)
            model = load_interaction_model(cfg.claude_home)
            block = render_injection(model, area)
            return block or None
        except Exception:  # noqa: BLE001 — fail-soft; chain fail-open
            return None

    return contributor
