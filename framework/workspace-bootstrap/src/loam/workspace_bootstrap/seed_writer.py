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

"""N3 seed-writer — writes the MINIMUM useful per-user prior into the
two-tier user-state home (slice N3 / AC.ONSEED.*).

This is FRAMEWORK code whose *output* is USER-STATE (the same shape as
``loam_layout.establish_loam_layout`` + ``new_workspace``). It writes
ONLY under the two declared homes (ADR-0001 / gate 9):

  - global, cross-workspace:  ``~/.claude/``
      - ``OBJECTIVES.md``         the user-confirmed end-intent as an objective
      - ``INTERACTION-MODEL.md``  the openness-biased AIM matrix at ``confidence: prior``
  - workspace-scoped:         ``<workspace>/.loam/``  (composed via
      ``establish_loam_layout`` — N3 seeds NOTHING into the workspace model
      homes per the ratified D-2 (a) minimum seed; N4 fills them from evidence)

**D-2 (a) — the minimum seed (RATIFIED).** N3 seeds the smallest prior that
makes the next session useful:

  1. the user-confirmed end-intent as an objective in ``~/.claude/OBJECTIVES.md``
     (the live ``status``/``last-touched``/``cadence``/``objective``/
     ``detail-path`` header shape);
  2. an openness-biased ``~/.claude/INTERACTION-MODEL.md`` with every cell at
     ``confidence: prior`` (so N4 can move it from evidence);
  3. the channel/voice basics (carried in the interaction-model ``tone`` axis +
     captured by the existing capability ritual — not re-asked here).

It does NOT pre-populate the full per-user model (that is N4's job). The
workspace model homes (``user-model/``, ``session-model/``) are left empty.

**Design invariants (mirror ``establish_loam_layout``):**

- **Idempotent / non-destructive (AC.ONFIRE.2 — the protection floor).** A seed
  file that already exists is detected and LEFT BYTE-FOR-BYTE INTACT — the
  seed-writer never clobbers a prior seed (or a user's hand-edit). A second run
  on an already-seeded home is a no-op for the existing files.
- **Boundary-respecting (AC.ONSEED.1 — gate 9 GREEN).** Every write is addressed
  relative to the home ``Path`` passed in — never a literal under ``framework/``.
- **Additive.** It only ever creates absent seed files; it removes nothing.

The global home is a PARAMETER (defaults to ``~/.claude``) so tests drive an
isolated fixture home — the cold-walk (AC.ONFIRE.3) seeds into a tmp ``.claude``
and asserts the post-conditions without touching the developer's real home.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

# The four interaction-surface areas the AIM matrix seeds rows for, plus the
# ``default`` catch-all (per adaptive-interaction-model.md §1b). N3 seeds the
# taxonomy at the openness-biased prior; N4 grows rows + moves cells.
AIM_AREAS: tuple[str, ...] = (
    "harness-mechanics",
    "code-and-builds",
    "their-domain-work",
    "ops-and-money",
    "decisions-and-tradeoffs",
    "default",
)

# The four axes per cell (AIM §1c). The openness-biased prior values: every
# axis starts open/inviting EXCEPT autonomy, which floors at the cautious end
# for the consequence-bearing areas (the §1c floor exception — exposure is
# reversible, a wrong autonomous action may not be).
_OPEN_DEFAULTS = {
    "technical-exposure": "open",
    "autonomy": "recommend",
    "tone": "peer-warm",
    "learning-appetite": "invite",
}
# Areas whose autonomy floors at the cautious end (real-world consequence).
_CAUTIOUS_AUTONOMY_AREAS = ("ops-and-money", "decisions-and-tradeoffs")


def default_global_home() -> Path:
    """The global user-state home (``~/.claude``). A function (not a module
    constant) so a test can monkeypatch ``Path.home`` and so the value is
    resolved at call time, never frozen at import."""
    return Path.home() / ".claude"


@dataclass
class SeedResult:
    """What a seed run created vs left intact (AC.ONSEED.* / AC.ONFIRE.2).

    ``created`` + ``existing`` together name every seed file the writer is
    responsible for, so a test can assert idempotency (a second run has empty
    ``created``) and completeness (every seed file is present after the run).
    """

    global_home: Path
    objectives_path: Path
    interaction_model_path: Path
    created: list[str] = field(default_factory=list)
    existing: list[str] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.created)


def _aim_cell(area: str, axis: str) -> str:
    """The openness-biased prior VALUE for one (area, axis) cell."""
    if axis == "autonomy" and area in _CAUTIOUS_AUTONOMY_AREAS:
        return "surface"
    return _OPEN_DEFAULTS[axis]


def render_interaction_model() -> str:
    """Render the openness-biased AIM matrix at ``confidence: prior``.

    Index-and-detail shaped like ``OBJECTIVES.md`` (so it inherits the FBM
    budget discipline and lands in the audited-surface set). Every cell carries
    ``{ value, confidence: prior, evidence: [] }`` — N3 seeds the prior; N4
    moves the cells from evidence (AC.ONSEED.2).
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
    for area in AIM_AREAS:
        lines.append(f"## {area}")
        for axis in ("technical-exposure", "autonomy", "tone", "learning-appetite"):
            value = _aim_cell(area, axis)
            lines.append(
                f"{axis}: {{ value: {value}, confidence: prior, evidence: [] }}"
            )
        lines.append("")
    return "\n".join(lines)


def render_objective_entry(
    *,
    slug: str,
    objective: str,
    cadence: str = "as-needed",
    last_touched: str = "",
    status: str = "active",
    detail_path: str = "",
) -> str:
    """Render ONE objective entry in the live ``OBJECTIVES.md`` header shape.

    The shape mirrors the live file:
    ``status``/``last-touched``/``cadence``/``objective``/``detail-path``.
    ``status`` reflects that the USER CONFIRMED the intent (the verification
    gate IS the owner-gate — a confirmed intent is ``active``; AC.ONSEED.3).
    """
    parts = [
        f"## {slug}",
        f"status: {status}",
    ]
    if last_touched:
        parts.append(f"last-touched: {last_touched}")
    parts.append(f"cadence: {cadence}")
    parts.append(f"objective: {objective}")
    if detail_path:
        parts.append(f"detail-path: {detail_path}")
    return "\n".join(parts)


_OBJECTIVES_HEADER = (
    "# user-objectives\n\n"
    "<!-- The user's current-focus objectives (life/work). NOT loam's dev-ODD "
    "objectives. SEEDED by N3 onboarding from the user-CONFIRMED end-intent. "
    "`status` is OWNER-GATED — a confirmed intent is recorded active; "
    "the verification gate at intake IS that owner-gate. -->\n"
)


def seed_user_state(
    *,
    objective_slug: str,
    objective_text: str,
    workspace_root: Path,
    global_home: Path | None = None,
    cadence: str = "as-needed",
    last_touched: str = "",
    detail_path: str = "",
    establish_layout: bool = True,
) -> SeedResult:
    """Write the D-2 (a) minimum seed into the two-tier home, idempotently.

    Arguments:
        objective_slug: the kebab-slug for the confirmed end-intent (e.g.
            ``stop-manual-status-reports``).
        objective_text: the user-confirmed end-intent prose (the objective).
        workspace_root: the workspace whose ``.loam/`` home is composed via
            ``establish_loam_layout`` (the workspace-scoped half — N3 seeds
            nothing INTO the model homes per D-2; it only ensures the layout).
        global_home: the global ``~/.claude`` home (default: real home). Tests
            pass an isolated fixture dir.
        establish_layout: when True (default), compose ``establish_loam_layout``
            so the workspace-scoped home exists (the layout, not a model seed).

    Returns a :class:`SeedResult` recording created vs pre-existing seed files.

    Idempotent / non-destructive: an existing ``OBJECTIVES.md`` or
    ``INTERACTION-MODEL.md`` is LEFT INTACT (AC.ONFIRE.2). For ``OBJECTIVES.md``,
    "intact" means: if the file exists and already names this objective slug,
    it is untouched; if it exists but does NOT name this slug, the new entry is
    APPENDED (additive — never rewrites the existing objectives).
    """
    home = global_home if global_home is not None else default_global_home()
    home.mkdir(parents=True, exist_ok=True)

    objectives_path = home / "OBJECTIVES.md"
    interaction_model_path = home / "INTERACTION-MODEL.md"

    result = SeedResult(
        global_home=home,
        objectives_path=objectives_path,
        interaction_model_path=interaction_model_path,
    )

    # --- INTERACTION-MODEL.md (AC.ONSEED.2) — additive, never overwrite. ---
    if interaction_model_path.exists():
        result.existing.append("INTERACTION-MODEL.md")
    else:
        interaction_model_path.write_text(
            render_interaction_model() + "\n", encoding="utf-8"
        )
        result.created.append("INTERACTION-MODEL.md")

    # --- OBJECTIVES.md (AC.ONSEED.3) — additive, never clobber. ---
    entry = render_objective_entry(
        slug=objective_slug,
        objective=objective_text,
        cadence=cadence,
        last_touched=last_touched,
        detail_path=detail_path,
    )
    if objectives_path.exists():
        existing_text = objectives_path.read_text(encoding="utf-8")
        if f"## {objective_slug}\n" in existing_text or existing_text.rstrip().endswith(
            f"## {objective_slug}"
        ):
            # Already seeded this objective — leave the file byte-for-byte.
            result.existing.append("OBJECTIVES.md")
        else:
            # Append the new objective additively (never rewrite prior ones).
            sep = "" if existing_text.endswith("\n\n") else (
                "\n" if existing_text.endswith("\n") else "\n\n"
            )
            objectives_path.write_text(
                existing_text + sep + entry + "\n", encoding="utf-8"
            )
            result.created.append("OBJECTIVES.md")
    else:
        objectives_path.write_text(
            _OBJECTIVES_HEADER + "\n" + entry + "\n", encoding="utf-8"
        )
        result.created.append("OBJECTIVES.md")

    # --- Workspace-scoped home (D-2: layout only, NO model seed). ---
    if establish_layout:
        # Lazy import to keep the seed-writer importable in constrained envs.
        from .loam_layout import establish_loam_layout

        establish_loam_layout(workspace_root)

    return result
