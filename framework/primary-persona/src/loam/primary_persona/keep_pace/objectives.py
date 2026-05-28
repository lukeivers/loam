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

"""KP5 — the ``OBJECTIVES.md`` register (schema + loader + seed).

The register is the user-scope index of current life/work objectives
that KP1's retrieval anchor reads for the active-objective term. It is
named ``user-objectives`` in its header (Surface #6) to keep agents
from confusing it with loam's dev-ODD: the entries are NOT ODD
objectives, they are the user's current-focus rotation key.

Schema (AC.KP5.1) — each entry carries:

  - ``slug`` — scope-descriptive (NOT version-packed; per
    ``feedback_scope_descriptive_ac_ids`` applied to objective slugs).
  - ``status`` — ``active`` / ``dormant`` / ``retired``.
    **OWNER-GATED-WRITE** (AC.KP5.4 / Surface #3 PROPOSE-AND-SURFACE):
    no automated path mutates this field; a drift-audit may only
    *propose* a change.
  - ``last-touched`` — ISO date the objective was last worked.
    **SOFT-AUTO-WRITE** (bookkeeping; an automated path may update it).
  - ``cadence`` — free-text expected work rhythm (e.g. ``daily``).
    **SOFT-AUTO-WRITE** (bookkeeping).
  - ``objective`` — the objective text.
  - ``completion`` — the completion criterion.
  - ``subgoals`` — list of project-local subgoal labels that ladder up.
  - ``detail-path`` — the path to the objective's detail doc (the
    index/detail shape per memory-architecture §3.3 — detail lives in
    the linked file, NOT inlined into the index, keeping the register
    under the hot byte-budget per AC.KP5.3).

The file format is a markdown index: a ``# user-objectives`` header
followed by one ``## <slug>`` section per objective, each carrying
flat ``key: value`` lines (+ a ``subgoals:`` list). The loader is
stdlib-only (mirrors ``file_memory._split_frontmatter``'s
no-dependency parse discipline).

ACs delivered (plan §5):

  - **AC.KP5.1** — :func:`load_objectives` parses the index/detail
    schema; :func:`render_register` emits it.
  - **AC.KP5.2** — :data:`SEEDED_OBJECTIVES` carries the two real
    objectives (fiction pipeline + revenue push), both ``active``.
  - **AC.KP5.3** — :func:`register_index_bytes` measures the rendered
    index size against the hot byte-budget (~20KB headroom target).
  - **AC.KP5.4** — :data:`OWNER_GATED_FIELDS` /
    :data:`SOFT_AUTO_FIELDS` expose the field-class distinction the
    loader enforces (``status`` owner-gated; ``last-touched`` /
    ``cadence`` soft-auto).
  - **AC.KP5.5** — :func:`active_objective_texts` extracts the active
    objectives' text for KP1's anchor (cross-AC binding; consumed by
    :mod:`work_anchor`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


# ---- register identity + scope (Surface #5 + Surface #6) -----------

# Header marker — names the register ``user-objectives`` to keep it
# distinct from loam's dev-ODD (Surface #6).
REGISTER_HEADER = "# user-objectives"

# AC.KP5.1 — the valid status values.
VALID_STATUSES: frozenset[str] = frozenset({"active", "dormant", "retired"})

# AC.KP5.4 / Surface #3 — field-class split. ``status`` is the ONLY
# owner-gated field (a drift audit may PROPOSE a change, never write
# it); ``last-touched`` + ``cadence`` are soft-auto bookkeeping an
# automated path may update.
OWNER_GATED_FIELDS: frozenset[str] = frozenset({"status"})
SOFT_AUTO_FIELDS: frozenset[str] = frozenset({"last-touched", "cadence"})

# AC.KP5.3 — hot byte-budget headroom target (per memory-architecture
# §5 #5). The register index is an always-load surface; detail lives
# in the per-objective detail-path file, NOT inlined here.
HOT_INDEX_BUDGET_BYTES = 20_000


# ---- user-scope resolution (Surface #5) ----------------------------

# The register lives at user-scope (mirrors the MEMORY.md / CLAUDE.md
# user-scope hierarchy). The schema/template + seed are sealed loam
# source; the live user-scope FILE is a runtime write by the seed step
# (an out-of-tree side-effect, not committed source).
USER_SCOPE_OBJECTIVES_NAME = "OBJECTIVES.md"


def user_scope_objectives_path(claude_home: Path | str | None = None) -> Path:
    """Resolve the user-scope ``OBJECTIVES.md`` path (Surface #5).

    Default base is ``~/.claude/``; an explicit ``claude_home`` is
    accepted so tests write to a tmp dir rather than the live home.
    The file is NOT created here — the seed step
    (:func:`seed_user_scope_register`) writes it.
    """
    base = Path(claude_home) if claude_home is not None else Path.home() / ".claude"
    return base / USER_SCOPE_OBJECTIVES_NAME


# ---- the objective entry -------------------------------------------


@dataclass
class Objective:
    """One register entry (AC.KP5.1 schema)."""

    slug: str
    status: str
    objective: str
    completion: str
    detail_path: str
    last_touched: str = ""
    cadence: str = ""
    subgoals: list[str] = field(default_factory=list)

    def is_active(self) -> bool:
        return self.status == "active"


# ---- the two real seeded objectives (AC.KP5.2) ---------------------
#
# Sourced from the hand-maintained CURRENT-WORK.md surface (the two
# real current priorities the keep-pace design formalises). Both
# ``active``. Detail lives in the linked detail-path docs, NOT inlined
# (index/detail shape — AC.KP5.3).

SEEDED_OBJECTIVES: tuple[Objective, ...] = (
    Objective(
        slug="revenue-independence",
        status="active",
        objective=(
            "Build durable, robust financial independence — the best chance "
            "to never be an employee again, weighted toward passive income "
            "(target >=$250k/yr). Active consulting is the bootstrap engine, "
            "not the goal; convert active income into passive assets "
            "(investing, real estate, IP catalog, AI-operated bought "
            "businesses) until active work is optional."
        ),
        completion=(
            "Passive income share grows past the coast-point so active work "
            "is optional; the fiction catalog + AI-operated assets + index "
            "core carry the durable legs."
        ),
        detail_path="workspace/strategy/revenue/PLAN.md",
        last_touched="2026-05-28",
        cadence="weekly",
        subgoals=[
            "fiction-catalog-as-in-motion-passive-asset",
            "ai-operated-acquired-assets",
            "buy-to-rent-durable-leg",
        ],
    ),
    Objective(
        slug="litrpg-fiction-pipeline",
        status="active",
        objective=(
            "Produce the LitRPG series 'Patch Notes for Reality' (7 books) "
            "via the autonomous Layer-4 production pipeline; quality bar is "
            "Luke's felt-verdict. A revenue path via self-publishing."
        ),
        completion=(
            "The 7-book series is produced to Luke's felt-verdict quality bar "
            "and on a self-publishing revenue path."
        ),
        detail_path=(
            "workspace/products/litrpg-writer/workspace/PRODUCTION-LOG.md"
        ),
        last_touched="2026-05-28",
        cadence="daily",
        subgoals=[
            "book-1-batch-production",
            "canon-consistency-across-the-series",
            "self-publishing-revenue-path",
        ],
    ),
)


# ---- render (schema authoring) -------------------------------------


def render_register(objectives: Iterable[Objective]) -> str:
    """Render the ``OBJECTIVES.md`` index from ``objectives``.

    Emits the ``# user-objectives`` header (Surface #6) + one
    ``## <slug>`` section per objective with flat ``key: value`` lines
    and a ``subgoals:`` list. Detail is NOT inlined — only the
    ``detail-path`` pointer is written (index/detail shape, AC.KP5.3).
    """
    lines: list[str] = [
        REGISTER_HEADER,
        "",
        (
            "<!-- The user's current-focus objectives (life/work). NOT loam's "
            "dev-ODD objectives. This is the rotation key keep-pace retrieval "
            "anchors against. `status` is OWNER-GATED (propose-and-surface, "
            "never auto-written); `last-touched`/`cadence` are soft-auto "
            "bookkeeping. Detail lives in each entry's detail-path, not here. -->"
        ),
        "",
    ]
    for obj in objectives:
        lines.append(f"## {obj.slug}")
        lines.append(f"status: {obj.status}")
        lines.append(f"last-touched: {obj.last_touched}")
        lines.append(f"cadence: {obj.cadence}")
        lines.append(f"objective: {obj.objective}")
        lines.append(f"completion: {obj.completion}")
        lines.append(f"detail-path: {obj.detail_path}")
        lines.append("subgoals:")
        for sg in obj.subgoals:
            lines.append(f"  - {sg}")
        lines.append("")
    return "\n".join(lines) + "\n"


# ---- load (the loader the field-class split lives in) --------------

_SECTION_RE = re.compile(r"^##\s+(.+)\s*$")
_KV_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s?(.*)$")
_SUBGOAL_RE = re.compile(r"^\s*-\s+(.+)\s*$")


def load_objectives(text: str) -> list[Objective]:
    """Parse the ``OBJECTIVES.md`` index into :class:`Objective` list.

    Stdlib-only (no YAML dependency — mirrors
    ``file_memory._split_frontmatter``). Lines outside a ``## <slug>``
    section (the header + the comment) are ignored. An entry missing a
    required field degrades to an empty string for that field rather
    than raising (AC.KP5.1 fail-soft on a hand-edited register).

    AC.KP5.4: the loader recognises the field-class split — see
    :func:`field_class` — but does NOT enforce immutability at parse
    time (the register is a file; enforcement is at the WRITE path,
    which is owner-gated for ``status``). The loader EXPOSES the
    distinction so a writer can assert it.
    """
    objectives: list[Objective] = []
    current: dict[str, object] | None = None
    in_subgoals = False

    def _flush() -> None:
        nonlocal current
        if current is None:
            return
        objectives.append(
            Objective(
                slug=str(current.get("slug", "")),
                status=str(current.get("status", "")),
                objective=str(current.get("objective", "")),
                completion=str(current.get("completion", "")),
                detail_path=str(current.get("detail-path", "")),
                last_touched=str(current.get("last-touched", "")),
                cadence=str(current.get("cadence", "")),
                subgoals=list(current.get("subgoals", [])),  # type: ignore[arg-type]
            )
        )
        current = None

    for raw in text.splitlines():
        section = _SECTION_RE.match(raw)
        if section:
            _flush()
            current = {"slug": section.group(1).strip(), "subgoals": []}
            in_subgoals = False
            continue
        if current is None:
            continue
        if raw.strip() == "subgoals:":
            in_subgoals = True
            continue
        if in_subgoals:
            sg = _SUBGOAL_RE.match(raw)
            if sg:
                current["subgoals"].append(sg.group(1).strip())  # type: ignore[union-attr]
                continue
            # A non-subgoal line closes the subgoals block.
            in_subgoals = False
        kv = _KV_RE.match(raw)
        if kv:
            current[kv.group(1)] = kv.group(2).strip()
    _flush()
    return objectives


# ---- field-class introspection (AC.KP5.4) --------------------------


def field_class(field_name: str) -> str:
    """Return the write-class of ``field_name``.

    AC.KP5.4 / Surface #3: ``"owner-gated"`` for ``status`` (a drift
    audit may PROPOSE a change but never write it), ``"soft-auto"``
    for ``last-touched`` / ``cadence`` (an automated path may update
    them), ``"static"`` for every other schema field (set at authoring
    time, not mutated by the running system).
    """
    if field_name in OWNER_GATED_FIELDS:
        return "owner-gated"
    if field_name in SOFT_AUTO_FIELDS:
        return "soft-auto"
    return "static"


# ---- byte-budget guard (AC.KP5.3) ----------------------------------


def register_index_bytes(objectives: Iterable[Objective]) -> int:
    """Return the rendered register's UTF-8 byte size (AC.KP5.3).

    Compared against :data:`HOT_INDEX_BUDGET_BYTES` by the caller; a
    register that grows past the budget is a signal that detail leaked
    into the index instead of staying in the detail-path file.
    """
    return len(render_register(objectives).encode("utf-8"))


# ---- KP1 anchor binding (AC.KP5.5) ---------------------------------


def active_objective_texts(objectives: Iterable[Objective]) -> list[str]:
    """Return the ``objective`` text of every ``active`` objective.

    AC.KP5.5 — the cross-AC binding KP1's :mod:`work_anchor` consumes:
    the active-objective text is the anchor term the bare prompt cannot
    supply (the term that surfaces the canon pointer in AC.KP1.6).
    """
    return [obj.objective for obj in objectives if obj.is_active()]


def active_subgoals(objectives: Iterable[Objective]) -> list[str]:
    """Return every ``active`` objective's subgoal labels (flattened).

    Consumed by :mod:`work_anchor` as the active-subgoal anchor term
    (AC.KP1.2's third key component).
    """
    out: list[str] = []
    for obj in objectives:
        if obj.is_active():
            out.extend(obj.subgoals)
    return out


# ---- seed step (the out-of-tree user-scope write) ------------------


def seed_user_scope_register(
    *,
    claude_home: Path | str | None = None,
    overwrite: bool = False,
) -> Path:
    """Write the seeded register to the user-scope path (Surface #5).

    Returns the written path. By default does NOT overwrite an
    existing register (the live file may carry owner edits); pass
    ``overwrite=True`` only for a deliberate reseed. The
    schema/template + seed content are sealed loam source; THIS write
    is the out-of-tree side-effect documented in the manifest (not a
    committed source edit).
    """
    path = user_scope_objectives_path(claude_home)
    if path.exists() and not overwrite:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_register(SEEDED_OBJECTIVES), encoding="utf-8")
    return path


def load_user_scope_register(
    claude_home: Path | str | None = None,
) -> list[Objective]:
    """Load the live user-scope register, falling back to the SEED.

    AC.KP5.5 + AC.KP1.6: KP1's anchor reads the active-objective text
    from here. When the live user-scope file is absent (the seed step
    has not run — e.g. in-tree tests, or a fresh machine), the
    in-source :data:`SEEDED_OBJECTIVES` are the floor so the anchor
    always has the two real objectives to work with. This is what lets
    AC.KP1.6 surface the canon pointer with NO pre-arranged state.
    """
    path = user_scope_objectives_path(claude_home)
    try:
        if path.exists():
            loaded = load_objectives(path.read_text(encoding="utf-8"))
            if loaded:
                return loaded
    except OSError:
        pass
    return list(SEEDED_OBJECTIVES)
