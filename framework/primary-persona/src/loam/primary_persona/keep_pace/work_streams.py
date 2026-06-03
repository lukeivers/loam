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

"""WORK-STREAMS — the cross-cutting attention-track register (Increment 1).

The streams LENS-DEFINITION surface. Formalizes Luke's hand-maintained
``CURRENT-WORK.md`` "WORK STREAMS" section (Money / LitRPG / loam / Cairn
/ Personal-Home) into a durable ``~/.claude/WORK-STREAMS.md`` register
whose schema is a SUPERSET of the ``OBJECTIVES.md`` ``Objective`` schema
(KP5) — same index/detail markdown shape, same user-scope home, same
owner-gated-write discipline — extended with the three stream-specific
fields:

  - ``projects: [<fbm-registry-name>, ...]`` — the FBM
    ``PROJECT_REGISTRY`` names this stream binds to, so the surfacer can
    call ``derive_project_state(name)`` per bound project and compose a
    REAL ground-truth STATE per stream (Slice C). Zero, one, or many
    (AC.WS.REG.2: a stream may span projects).
  - ``attention: active | deep-dive | paused`` — the per-stream
    surfacing control. OWNER-GATED-WRITE (no automated path mutates it,
    mirroring KP5 ``status``). ``deep-dive`` surfaces a stream in full +
    mutes other streams' staleness nudges; ``paused`` drops a stream's
    line + nudge.
  - ``nest-under: <stream-slug>`` (optional) — a sub-stream nests under a
    parent stream (AC.WS.REG.2: a stream may nest). A stream may BOTH
    span projects AND nest.

★ WMS-D7 PRE-L1 SHIM (work-management-system-architecture §8 / WMS-D7).
Under the unified work-management model a stream is a VIEW (a tag) over
work items, NOT a store of bindings. This register is authored as the
streams LENS-DEFINITION + ATTENTION-CONFIG (the ``attention`` /
``nest-under`` fields legitimately describe the VIEW and stay). But its
``projects`` binding + per-stream backlog are a PRE-UNIFIED-MODEL SHIM:
in Increment 1 (before the L1 work graph exists) they are necessarily a
register-local list. :data:`SHIM_FIELDS` + :func:`shim_marker` mark them
explicitly, and AC.WS.SHIM.1 asserts the binding is RE-POINTABLE at the
L1 work graph in Increment 2 without a register rewrite — so the
foundation is not boxed-in. This is the ONE adjustment WMS-D7 names.

Lens-1: this REUSES the KP5 register machinery (the index/detail parse
discipline, the ``~/.claude/`` user-scope home, the owner-gated /
soft-auto field-class split). It does NOT re-implement state-tracking —
the STATE derivation is Slice C's, consumed by the surfacer
(:mod:`work_streams_surface`).

The three-source backlog import (D6 / AC.WS.IMPORT.1) is documented in
the register header + carried in the seed: the FIDRAFT capture surface,
the persona task list, and the dev ``workstream-queue.yaml`` are the
three currently-disconnected sources; the dev-queue ``ws-*`` items map
UNDER the ``loam`` stream as "dev-queue items" (the naming collision,
resolved-not-silent — no file rename).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

# ---- register identity + scope -------------------------------------

#: Header marker — names the register ``work-streams`` (sibling to the
#: ``user-objectives`` register, distinct from loam's dev-ODD).
REGISTER_HEADER = "# work-streams"

#: AC.WS.REG.1 — the valid attention values.
VALID_ATTENTION: frozenset[str] = frozenset({"active", "deep-dive", "paused"})

#: AC.WS.SURFACE.2 — field-class split (mirrors KP5). ``attention`` is the
#: ONLY owner-gated field (no automated path flips deep-dive / pause);
#: ``last-touched`` + ``cadence`` are soft-auto bookkeeping.
OWNER_GATED_FIELDS: frozenset[str] = frozenset({"attention"})
SOFT_AUTO_FIELDS: frozenset[str] = frozenset({"last-touched", "cadence"})

#: ★ WMS-D7 — the fields that are the PRE-L1 SHIM (register-local in
#: Increment 1; re-pointed at the L1 work graph in Increment 2 without a
#: register rewrite). ``attention`` + ``nest-under`` are NOT shim — they
#: describe the VIEW and stay (WMS-D7).
SHIM_FIELDS: frozenset[str] = frozenset({"projects", "backlog"})

#: Hot byte-budget headroom (mirrors KP5). Detail lives in each stream's
#: detail-path file, NOT inlined into the index.
HOT_INDEX_BUDGET_BYTES = 20_000

#: The register lives at user-scope (mirrors OBJECTIVES.md).
USER_SCOPE_WORK_STREAMS_NAME = "WORK-STREAMS.md"


def user_scope_work_streams_path(claude_home: Path | str | None = None) -> Path:
    """Resolve the user-scope ``WORK-STREAMS.md`` path.

    Default base is ``~/.claude/``; an explicit ``claude_home`` is
    accepted so tests write to a tmp dir. The file is NOT created here —
    :func:`seed_user_scope_register` writes it (an out-of-tree
    side-effect, not committed source — same discipline as KP5).
    """
    base = Path(claude_home) if claude_home is not None else Path.home() / ".claude"
    return base / USER_SCOPE_WORK_STREAMS_NAME


def field_class(field_name: str) -> str:
    """Return the write-class of ``field_name`` (AC.WS.SURFACE.2).

    ``"owner-gated"`` for ``attention`` (no automated path mutates it),
    ``"soft-auto"`` for ``last-touched`` / ``cadence``, ``"static"`` for
    every other schema field.
    """
    if field_name in OWNER_GATED_FIELDS:
        return "owner-gated"
    if field_name in SOFT_AUTO_FIELDS:
        return "soft-auto"
    return "static"


def shim_marker(field_name: str) -> str:
    """★ WMS-D7 — return whether ``field_name`` is the pre-L1 shim.

    ``"pre-l1-shim"`` for ``projects`` / ``backlog`` (register-local in
    Increment 1; re-pointable at the L1 work graph in Increment 2),
    ``"lens-config"`` for everything else (describes the VIEW, stays).
    AC.WS.SHIM.1 asserts the shim fields are re-pointable.
    """
    return "pre-l1-shim" if field_name in SHIM_FIELDS else "lens-config"


# ---- the work-stream entry (superset of Objective, KP5) ------------


@dataclass
class WorkStream:
    """One stream register entry — a superset of KP5's :class:`Objective`.

    The shared KP5 fields (``slug`` / ``last_touched`` / ``cadence`` /
    ``detail_path`` / ``subgoals``) carry their KP5 meaning. The three
    stream-specific fields are:

      - ``attention`` — ``active`` / ``deep-dive`` / ``paused``
        (owner-gated; AC.WS.SURFACE.2).
      - ``projects`` — the bound FBM registry names (AC.WS.REG.2 span;
        ★ WMS-D7 pre-L1 shim).
      - ``nest_under`` — optional parent stream slug (AC.WS.REG.2 nest;
        lens-config, not shim).

    ``ground_truth_bound`` is DERIVED, not stored: True iff ``projects``
    is non-empty (AC.WS.DERIVE.2 — a stream with no bound project is
    explicitly marked "no ground-truth project bound" by the surfacer,
    never faking a derived STATE).
    """

    slug: str
    attention: str
    objective: str
    detail_path: str
    projects: list[str] = field(default_factory=list)
    nest_under: str = ""
    last_touched: str = ""
    cadence: str = ""
    subgoals: list[str] = field(default_factory=list)
    backlog: list[str] = field(default_factory=list)

    def is_paused(self) -> bool:
        return self.attention == "paused"

    def is_deep_dive(self) -> bool:
        return self.attention == "deep-dive"

    def is_active(self) -> bool:
        return self.attention == "active"

    @property
    def ground_truth_bound(self) -> bool:
        """True iff the stream binds >=1 FBM-registered project (so the
        surfacer can derive a real STATE). False → AC.WS.DERIVE.2 path
        (staleness-based next-action + "no ground-truth project bound").
        """
        return bool(self.projects)


# ---- the 5 seeded streams (from CURRENT-WORK.md) -------------------
#
# Sourced from the hand-maintained CURRENT-WORK.md "WORK STREAMS"
# section (the 5 real parallel tracks). loam + Cairn + LitRPG bind to
# FBM-registered projects (ground-truth-derived STATE). Money +
# Personal-Home bind NO project (no repo to derive from — they ride the
# detail-path/cadence staleness path, AC.WS.DERIVE.2, marked "no
# ground-truth project bound"). Detail lives in each detail-path, NOT
# inlined (index/detail shape).

SEEDED_WORK_STREAMS: tuple[WorkStream, ...] = (
    WorkStream(
        slug="money",
        attention="active",
        objective=(
            "Build durable financial independence weighted toward passive "
            "income — the revenue push (no repo to derive from; rides the "
            "work-item model, out of FBM-registry scope this cycle)."
        ),
        detail_path="workspace/strategy/revenue/PLAN.md",
        projects=[],  # no ground-truth project bound (AC.WS.DERIVE.2)
        last_touched="2026-05-28",
        cadence="weekly",
        subgoals=[
            "fiction-catalog-as-passive-asset",
            "ai-operated-acquired-assets",
            "buy-to-rent-durable-leg",
        ],
        backlog=[
            "task-list: #16 Money execution plan; #78 Iran-region exposure map",
        ],
    ),
    WorkStream(
        slug="litrpg",
        attention="active",
        objective=(
            "Produce the LitRPG series 'Patch Notes for Reality' (7 books) "
            "via the autonomous production pipeline; quality bar is Luke's "
            "felt-verdict; a self-publishing revenue path."
        ),
        detail_path=(
            "workspace/products/litrpg-writer/workspace/PRODUCTION-LOG.md"
        ),
        projects=["litrpg"],  # ground-truth-derived production STATE (Slice C)
        last_touched="2026-06-02",
        cadence="daily",
        subgoals=[
            "book-1-batch-production",
            "canon-consistency-across-the-series",
            "self-publishing-revenue-path",
        ],
        backlog=[
            "task-list: #7 production arc; #8 layer-6/7 pipeline; #85 book-1 finishing pass",
        ],
    ),
    WorkStream(
        slug="loam",
        attention="active",
        objective=(
            "Build loam — the per-user-tuned translation harness — to its "
            "prime-directive bar; the keep-pace flagship + the work-"
            "management system are the live build fronts."
        ),
        detail_path="docs/STATE.md",
        projects=["loam"],  # ground-truth-derived build STATE (Slice C)
        last_touched="2026-06-03",
        cadence="daily",
        subgoals=[
            "fbm-quality-and-accuracy",
            "work-management-system",
            "non-tech-user-self-recovery",
        ],
        backlog=[
            # D6 — the dev-queue maps UNDER the loam stream as "dev-queue
            # items" (the ws-* naming collision, resolved-not-silent).
            "dev-queue items (.claude/workstream-queue.yaml ws-* items, "
            "UNDER loam — the dev BUILD/amend queue, NOT a cross-cutting "
            "stream; mapped here, no file rename)",
            "fidraft: graduated items under loam (docs/FUTURE_IDEAS_DRAFT.md)",
            "task-list: #69 FBM overhaul; #70 work-streams; #71 mismatch channel",
        ],
    ),
    WorkStream(
        slug="cairn",
        attention="active",
        objective=(
            "Stand Cairn up as a proper open-source cause-coordination "
            "project (MIT + OSS hygiene + recruitable benign launch)."
        ),
        detail_path="docs/STATE.md",
        projects=["cairn"],  # ground-truth-derived build STATE (Slice C)
        last_touched="2026-06-01",
        cadence="weekly",
        subgoals=[
            "cause-layer-and-vetting-workflows",
            "oss-hygiene-and-public-standup",
            "outreach-and-onboarding",
        ],
        backlog=[
            "task-list: #28/#29 OSS + launch; #76 online-harms framework",
        ],
    ),
    WorkStream(
        slug="personal-home",
        attention="active",
        objective=(
            "House repairs + HELOC + personal-life logistics (no repo to "
            "derive from; rides the detail-path/cadence staleness path)."
        ),
        detail_path="workspace/strategy/personal/PLAN.md",
        projects=[],  # no ground-truth project bound (AC.WS.DERIVE.2)
        last_touched="2026-05-20",
        cadence="weekly",
        subgoals=[
            "house-repairs-ordered-plan",
            "heloc-path",
        ],
        backlog=[
            "task-list: #17 personal-life execution plan",
        ],
    ),
)


# ---- the three-source reconciliation header (D6 / AC.WS.IMPORT.1) ---

_RECONCILIATION_NOTE = (
    "<!-- WORK-STREAMS register — the cross-cutting attention-track lens "
    "(work-streams Increment 1). SCHEMA is a SUPERSET of OBJECTIVES.md "
    "(KP5): same index/detail shape, same user-scope home, same "
    "owner-gated-write discipline, PLUS `projects:` (bound FBM-registry "
    "names — ground-truth STATE derived live, never stored), `attention:` "
    "(active/deep-dive/paused — OWNER-GATED, no automated path mutates "
    "it), and optional `nest-under:` (sub-streams).\n\n"
    "  ★ WMS-D7 PRE-L1 SHIM: under the unified work-management model a "
    "stream is a VIEW (tag) over work items, not a store. The `attention` "
    "and `nest-under` fields describe the VIEW and stay; the `projects` "
    "binding and per-stream `backlog` are a PRE-UNIFIED-MODEL SHIM, "
    "register-local in Increment 1 and RE-POINTABLE at the L1 work graph "
    "in Increment 2 without a register rewrite (AC.WS.SHIM.1). The "
    "foundation is not boxed-in.\n\n"
    "  THREE-SOURCE BACKLOG IMPORT (D6): the backlog from three "
    "currently-disconnected sources is indexed here, grouped by stream:\n"
    "    1. FIDRAFT (docs/FUTURE_IDEAS_DRAFT.md) — idea capture; graduated "
    "items index under the relevant stream (mostly loam). FIDRAFT stays "
    "the capture surface; this register INDEXES, does not absorb.\n"
    "    2. the persona task list (TaskCreate backlog) — tasks index under "
    "their stream. The task list stays the live tracker; this register "
    "GROUPS by stream for the surfacer.\n"
    "    3. the dev workstream-queue.yaml (the `ws-*` BUILD/amend queue) — "
    "the NAMING COLLISION, resolved-not-silent: the `ws-*` dev-queue is "
    "the dev BUILD queue (decoupled publish-vs-build), NOT a cross-cutting "
    "attention stream. It maps UNDER the `loam` stream as 'dev-queue "
    "items'; NO file rename (it is load-bearing for the dev-amend "
    "cadence). The `ws-*` prefix overlap is documented here so a future "
    "agent does not re-disconnect them. -->"
)


# ---- render (schema authoring) -------------------------------------


def render_register(streams: Iterable[WorkStream]) -> str:
    """Render the ``WORK-STREAMS.md`` index from ``streams``.

    Emits the ``# work-streams`` header + the three-source reconciliation
    note + one ``## <slug>`` section per stream with flat ``key: value``
    lines, a ``projects:`` list, a ``subgoals:`` list, and a ``backlog:``
    list. Detail is NOT inlined — only the ``detail-path`` pointer
    (index/detail shape; AC.WS.REG.1).
    """
    lines: list[str] = [REGISTER_HEADER, "", _RECONCILIATION_NOTE, ""]
    for s in streams:
        lines.append(f"## {s.slug}")
        lines.append(f"attention: {s.attention}")
        lines.append(f"nest-under: {s.nest_under}")
        lines.append(f"last-touched: {s.last_touched}")
        lines.append(f"cadence: {s.cadence}")
        lines.append(f"objective: {s.objective}")
        lines.append(f"detail-path: {s.detail_path}")
        lines.append("projects:")
        for p in s.projects:
            lines.append(f"  - {p}")
        lines.append("subgoals:")
        for sg in s.subgoals:
            lines.append(f"  - {sg}")
        lines.append("backlog:")
        for b in s.backlog:
            lines.append(f"  - {b}")
        lines.append("")
    return "\n".join(lines) + "\n"


# ---- load (the loader the field-class split lives in) --------------

_SECTION_RE = re.compile(r"^##\s+(.+)\s*$")
_KV_RE = re.compile(r"^([A-Za-z][A-Za-z0-9_-]*):\s?(.*)$")
_LIST_ITEM_RE = re.compile(r"^\s+-\s+(.+)\s*$")

# The keys whose value is a list block (a bare ``key:`` line followed by
# ``  - item`` lines), not a scalar.
_LIST_KEYS = frozenset({"projects", "subgoals", "backlog"})


def load_streams(text: str) -> list[WorkStream]:
    """Parse the ``WORK-STREAMS.md`` index into :class:`WorkStream` list.

    Stdlib-only (no YAML dependency — mirrors KP5's
    ``load_objectives``). Lines outside a ``## <slug>`` section (the
    header + the reconciliation note) are ignored. An entry missing a
    field degrades to its default rather than raising (AC.WS.REG.1
    fail-soft on a hand-edited register). The three list keys
    (``projects`` / ``subgoals`` / ``backlog``) parse their ``  - item``
    blocks.
    """
    streams: list[WorkStream] = []
    current: dict[str, object] | None = None
    list_key: str | None = None

    def _flush() -> None:
        nonlocal current
        if current is None:
            return
        streams.append(
            WorkStream(
                slug=str(current.get("slug", "")),
                attention=str(current.get("attention", "")),
                objective=str(current.get("objective", "")),
                detail_path=str(current.get("detail-path", "")),
                projects=list(current.get("projects", [])),  # type: ignore[arg-type]
                nest_under=str(current.get("nest-under", "")),
                last_touched=str(current.get("last-touched", "")),
                cadence=str(current.get("cadence", "")),
                subgoals=list(current.get("subgoals", [])),  # type: ignore[arg-type]
                backlog=list(current.get("backlog", [])),  # type: ignore[arg-type]
            )
        )
        current = None

    for raw in text.splitlines():
        section = _SECTION_RE.match(raw)
        if section:
            _flush()
            current = {
                "slug": section.group(1).strip(),
                "projects": [],
                "subgoals": [],
                "backlog": [],
            }
            list_key = None
            continue
        if current is None:
            continue
        # A bare ``<list-key>:`` line opens a list block.
        stripped = raw.strip()
        if stripped[:-1] in _LIST_KEYS and stripped.endswith(":"):
            list_key = stripped[:-1]
            continue
        if list_key is not None:
            item = _LIST_ITEM_RE.match(raw)
            if item:
                current[list_key].append(item.group(1).strip())  # type: ignore[union-attr]
                continue
            # A non-item line closes the list block.
            list_key = None
        kv = _KV_RE.match(raw)
        if kv and kv.group(1) not in _LIST_KEYS:
            current[kv.group(1)] = kv.group(2).strip()
    _flush()
    return streams


# ---- byte-budget guard ---------------------------------------------


def register_index_bytes(streams: Iterable[WorkStream]) -> int:
    """Return the rendered register's UTF-8 byte size (mirrors KP5).

    Compared against :data:`HOT_INDEX_BUDGET_BYTES` by the caller; a
    register past the budget signals detail leaked into the index.
    """
    return len(render_register(streams).encode("utf-8"))


# ---- nest / span resolution (AC.WS.REG.2) --------------------------


def resolve_nest(streams: Iterable[WorkStream]) -> dict[str, list[str]]:
    """Map each parent stream slug -> the slugs of its sub-streams.

    AC.WS.REG.2: a stream that nests (``nest_under`` set) resolves under
    its parent. A stream with no ``nest_under`` is a top-level stream.
    A ``nest_under`` pointing at an unknown parent is dropped (fail-soft
    on a hand-edited register).
    """
    by_slug = {s.slug for s in streams}
    children: dict[str, list[str]] = {}
    for s in streams:
        if s.nest_under and s.nest_under in by_slug:
            children.setdefault(s.nest_under, []).append(s.slug)
    return children


# ---- seed step (the out-of-tree user-scope write) ------------------


def seed_user_scope_register(
    *,
    claude_home: Path | str | None = None,
    overwrite: bool = False,
) -> Path:
    """Write the seeded register to the user-scope path.

    Returns the written path. By default does NOT overwrite an existing
    register (the live file may carry owner edits); pass
    ``overwrite=True`` only for a deliberate reseed. The schema +
    seed content are sealed loam source; THIS write is the out-of-tree
    side-effect (not a committed source edit) — same discipline as KP5.
    """
    path = user_scope_work_streams_path(claude_home)
    if path.exists() and not overwrite:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_register(SEEDED_WORK_STREAMS), encoding="utf-8")
    return path


def load_user_scope_register(
    claude_home: Path | str | None = None,
) -> list[WorkStream]:
    """Load the live user-scope register, falling back to the SEED.

    When the live user-scope file is absent (the seed step has not run —
    e.g. in-tree tests, or a fresh machine), the in-source
    :data:`SEEDED_WORK_STREAMS` are the floor so the surfacer always has
    the 5 real streams to work with. This is what lets AC.WS.LIVE.1
    surface the per-stream block with NO pre-arranged state.
    """
    path = user_scope_work_streams_path(claude_home)
    try:
        if path.exists():
            loaded = load_streams(path.read_text(encoding="utf-8"))
            if loaded:
                return loaded
    except OSError:
        pass
    return list(SEEDED_WORK_STREAMS)
