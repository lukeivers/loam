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

"""Tracker-seed adapter (Amendment #39 — workspace-bootstrap tracker-seed).

First-run extension that seeds the workspace's objective-tracker DB
with a value-prop-rooted objective tree. Sub-plan reference:
``docs/plans/amendment-39-workspace-bootstrap-tracker-seed.md``.

Sub-plan §1 owner ruling D-4 (b): the workspace user authors the
value-prop root; pos-v2 dev workspaces template Luke's value prop
from ``docs/VALUE_PROPOSITION.md`` (read at first-run time,
not bundled in source — AC39.6 enforces no-payload-in-source).
Non-dev workspaces read a workspace-supplied path
(``<workspace>/value-prop.md``); if absent, the seed skips with a
structured diagnostic and is non-fatal so the scaffold does not
block first-run.

Idempotency contract (mirrors amendment #36 + sub-plan §6 #8):
re-runs query the tracker via ``query_projection_view`` (amendment
#38's API) for already-seeded records and skip; never clobber.
Stable objective IDs (``value-prop-root`` + ``spec-v1.0`` /
``spec-v1.1`` / ``spec-v1.2``) make the query-then-skip check
deterministic across re-runs.

The seed is FRAMEWORK; the CONTENT of the value prop is workspace-
owned. pos-v2 core ships zero canonical value-prop content — the
canonical doc lives under ``docs/`` (framework documentation), and
the seed reads it at runtime on dev workspaces. STATE.md rule #4
("pOS core ships zero personas/content") + single-tree ruling +
D-4 (b) all hold under this shape.
"""

from __future__ import annotations

import asyncio
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

from loam.objective_tracker import (
    LiftedFrom,
    ObjectiveFilter,
    ObjectiveSpec,
    ObjectiveTracker,
    ProseCriterion,
    TimeBound,
)


# ---- workspace classification (sub-plan E — read dev_intent answer)


# Path of the canonical pos-v2 value-prop doc, relative to a workspace
# root. Amendment #39 used this file's presence as the dev-marker; sub-
# plan E (amendment #42, two-modes-and-multi-workspace) replaces that
# heuristic — every fresh GitHub clone ships VALUE_PROPOSITION.md, so
# end-user clones were misclassified as pos-v2-dev. The constant
# remains load-bearing for ``load_value_prop_source`` (the dev path
# still reads this file as content); only the CLASSIFICATION source-
# of-truth moves to ``read_dev_intent``.
FRAMEWORK_VALUE_PROP_RELPATH = "docs/VALUE_PROPOSITION.md"

# Path of the workspace-user-authored value-prop doc on a workspace
# NOT classified pos-v2 dev. Pre-populated by the workspace operator
# before first-run; sub-plan §11 D-build.3 candidate (b) — non-
# interactive, durable, parallels amendment #36's persona template-
# from-disk shape.
WORKSPACE_VALUE_PROP_RELPATH = "value-prop.md"


CLASSIFICATION_LOAM_DEV = "pos-v2-dev"
CLASSIFICATION_USER = "user"


def classify_workspace(workspace_root: Path | str) -> str:
    """Return ``"pos-v2-dev"`` iff the workspace's persona contract
    carries ``dev_intent="yes"``; ``"user"`` otherwise.

    Sub-plan E (amendment #42) — replaces amendment #39's
    ``VALUE_PROPOSITION.md``-presence heuristic with a read of the
    workspace-local dev-intent answer (sub-plan A's
    ``read_dev_intent``).

    Mapping:
        - ``read_dev_intent == "yes"``  -> ``"pos-v2-dev"``
        - ``read_dev_intent == "no"``   -> ``"user"``
        - ``read_dev_intent == "absent"`` -> ``"user"`` (defensive
          default per locked owner ruling 4 + AC.E.3).

    The ``read_dev_intent`` reader is itself fail-safe (returns
    ``"absent"`` on missing or malformed contracts), so this function
    never raises on contract-shape issues — the failure mode is
    fail-soft to user-mode.

    Lazy import of ``read_dev_intent`` mirrors amendment #40's pattern
    (``primary_persona.tracker_context``'s lazy import of
    ``objective_tracker``) — keeps the import graph acyclic against
    primary-persona's loader chain.

    Pure function from the caller's perspective: the only I/O is the
    persona-contract read inside ``read_dev_intent``.
    """
    workspace_root = Path(workspace_root)
    from loam.primary_persona.onboarding import read_dev_intent

    answer = read_dev_intent(workspace_root)
    if answer == "yes":
        return CLASSIFICATION_LOAM_DEV
    return CLASSIFICATION_USER


# ---- value-prop source loading ---------------------------------------


@dataclass(frozen=True)
class ValuePropSource:
    """Where the seed read the value prop from + the raw text.

    ``source_doc`` is the workspace-relative path stored as the
    ``LiftedFrom.source_doc`` attribute on the seeded root and
    descendants. ``source_text`` is the markdown content used to
    extract the goal + criteria. ``available`` is False when the seed
    classified non-dev but the workspace user has not yet supplied
    ``value-prop.md`` — the seed skips in this case (sub-plan §11
    D-build.3 (b) shape).
    """

    available: bool
    source_doc: str
    source_text: str


def load_value_prop_source(
    workspace_root: Path | str,
    classification: str,
    *,
    value_prop_path_override: Path | None = None,
) -> ValuePropSource:
    """Read the value-prop source for the workspace.

    On a pos-v2 dev workspace, reads the framework's canonical
    ``docs/VALUE_PROPOSITION.md`` (or the override path the
    test fixture passes). On a non-dev workspace, reads
    ``<workspace>/value-prop.md`` (or the override). Returns
    ``ValuePropSource(available=False, ...)`` if the file is missing
    on a non-dev workspace — AC39.5 path; the scaffold keeps going
    without raising.

    Raises ``FileNotFoundError`` on a pos-v2 dev workspace whose
    classified-source file is missing — that contradicts the
    classifier and means something structural is broken; surface
    loudly rather than silently skip.
    """
    workspace_root = Path(workspace_root)

    if classification == CLASSIFICATION_LOAM_DEV:
        path = (
            value_prop_path_override
            if value_prop_path_override is not None
            else workspace_root / FRAMEWORK_VALUE_PROP_RELPATH
        )
        rel = FRAMEWORK_VALUE_PROP_RELPATH
        text = Path(path).read_text()
        return ValuePropSource(available=True, source_doc=rel, source_text=text)

    # Non-dev workspace.
    path = (
        value_prop_path_override
        if value_prop_path_override is not None
        else workspace_root / WORKSPACE_VALUE_PROP_RELPATH
    )
    rel = WORKSPACE_VALUE_PROP_RELPATH
    if not Path(path).is_file():
        return ValuePropSource(available=False, source_doc=rel, source_text="")
    text = Path(path).read_text()
    return ValuePropSource(available=True, source_doc=rel, source_text=text)


# ---- value-prop content extraction (parser) --------------------------


# Generic AC.PO criterion fallbacks. Used on non-dev workspaces whose
# user-supplied value-prop file may omit the standard
# Primary-persona-test / Harness-test sections; the seed still creates
# a well-formed root with these criteria so the structural invariant
# holds (AC.PO.1 + AC.PO.2 are present on every seeded root). The
# fallback prose is generic policy, NOT Luke's value-prop content,
# and lives here in source because (a) it carries no workspace-
# specific content (no goal text, no domain), and (b) it is
# methodology-shaped, mirroring AC.PO.1 / AC.PO.2 as universal
# framework invariants. AC39.6 forbids workspace value-prop CONTENT
# (the goal/prose specific to a workspace's mission); the abstract
# invariant text below is framework methodology and is permitted.
_AC_PO_1_FALLBACK = (
    "Primary-persona test: this workspace's primary persona reduces "
    "the translation burden between the user's natural-language "
    "intent and AI-effective execution."
)
_AC_PO_2_FALLBACK = (
    "Harness test: this workspace's harness adds to the toolkit the "
    "primary persona can draw from."
)

# Default goal fallback when no extractable headline appears in the
# user-supplied value-prop file. Generic framework wording; not
# workspace-content-specific.
_GOAL_FALLBACK = (
    "Workspace value-prop root — the user-authored prime objective "
    "this workspace ladders up to."
)


_HEADER_RE = re.compile(r"^(#+)\s+(.*?)\s*$", re.MULTILINE)


def _extract_h1_title(text: str) -> str | None:
    """Return the first H1 (``# Title``) in the text, with the
    leading ``#`` stripped. None if no H1 is present.

    The H1 is the durable label of a value-prop document; using it as
    the goal-string keeps the seeded root's identity stable across
    edits to the body prose.
    """
    for raw in text.splitlines():
        line = raw.rstrip()
        m = re.match(r"^#\s+(.+?)\s*$", line)
        if m:
            return m.group(1).strip()
    return None


def _extract_section_body(text: str, header_pattern: str) -> str | None:
    """Return the body text under the FIRST header whose title matches
    ``header_pattern`` (case-insensitive), up to the next header at
    the same or higher level. None if no matching header is found.
    """
    pat = re.compile(header_pattern, re.IGNORECASE)
    matches = list(_HEADER_RE.finditer(text))
    for i, m in enumerate(matches):
        title = m.group(2).strip()
        if pat.search(title):
            level = len(m.group(1))
            start = m.end()
            end = len(text)
            for n in matches[i + 1 :]:
                if len(n.group(1)) <= level:
                    end = n.start()
                    break
            body = text[start:end].strip()
            return body if body else None
    return None


@dataclass(frozen=True)
class ValuePropRecord:
    """Extracted value-prop fields for the seeded root.

    Pure data; no provenance metadata (that's added at seed time
    via ``LiftedFrom``).
    """

    goal: str
    ac_po_1_prose: str
    ac_po_2_prose: str


def extract_value_prop_record(text: str) -> ValuePropRecord:
    """Parse the value-prop source text into goal + AC.PO.1 + AC.PO.2.

    On the canonical framework VALUE_PROPOSITION.md, both AC sections
    are extractable verbatim. On a workspace-user-authored value-
    prop file, sections may be absent — the parser falls back to the
    generic invariant prose so the seeded root is well-formed. The
    fallback text carries NO workspace-content (no domain, no
    mission); it is methodology-invariant text mirroring the
    universal AC.PO definitions.

    The function never raises on shape mismatch — it always returns
    a well-formed ``ValuePropRecord``. The seed's job is to produce
    a tree where the user authored the root; the parser's job is to
    surface the user's content where extractable, and to provide
    framework-default invariants where the user's source is silent.
    """
    goal = _extract_h1_title(text) or _GOAL_FALLBACK
    if len(goal) > 1000:
        # Pydantic accepts arbitrary-length strings, but the goal is
        # intended as a one-liner; trim to keep tracker UIs readable.
        goal = goal[:997].rstrip() + "..."

    ac_po_1_body = _extract_section_body(text, r"primary[-\s]?persona\s+test")
    ac_po_2_body = _extract_section_body(text, r"harness\s+test")

    return ValuePropRecord(
        goal=goal,
        ac_po_1_prose=ac_po_1_body or _AC_PO_1_FALLBACK,
        ac_po_2_prose=ac_po_2_body or _AC_PO_2_FALLBACK,
    )


# ---- spec-tier descendants (D-build.2: one per spec phase) -----------


# Spec-tier descendants — one objective per spec phase. Each has
# ``authored_by="user"`` and ``lifted_from.source_doc`` pointing at
# the framework spec doc; ``source_ac`` carries the phase label so
# downstream consumers (#40 contributor, loam amend project) can
# filter cleanly. The descendant prose is methodology-shaped (the
# spec phases are universal framework invariants, not workspace
# content); AC39.6 enforces that no workspace-specific value-prop
# prose appears in source. The spec doc is canonically located at
# the constant below; the same path applies whether the workspace is
# pos-v2 dev or user-authored (a workspace operator who is not
# building pos-v2 itself can leave the file absent — the spec-tier
# seed simply records the canonical path as its ``source_doc``
# without requiring the file to exist on disk).
SPEC_DOC_RELPATH = "docs/spec/loam-objectives-spec.md"


# Each entry: (suffix used in objective_id, AC label stored in
# lifted_from.source_ac, goal prose for the descendant). Three phases
# matches sub-plan §11 D-build.2 (a) — keeps the seeded tree compact.
_SPEC_TIER_PHASES: tuple[tuple[str, str, str], ...] = (
    (
        "v1.0",
        "v1.0",
        "v1.0 spec phase: foundational primitives, objective-based "
        "work, structural refusal, and the architectural / foundational "
        "/ user-facing layers the rebuild's first round delivered.",
    ),
    (
        "v1.1",
        "v1.1",
        "v1.1 spec phase: semantic round-trip equivalence, upgrade "
        "fidelity contracts, and the maturity layer added between "
        "v1.0 and v1.2 (R1 + cross-cutting upgrade discipline).",
    ),
    (
        "v1.2",
        "v1.2",
        "v1.2 spec phase: framework-not-content invariants, the "
        "primary-persona contract surface, the toolkit-purity "
        "rules R16+ extended in the rebuild's third round.",
    ),
)


# ---- seeding -----------------------------------------------------------


# Stable objective IDs — D-build.4 idempotency-by-query relies on
# stable IDs so the re-run check (``query_projection_view`` filter on
# ``lifted_from.source_doc``) produces exactly the right hits without
# UUID equality risk.
ROOT_OBJECTIVE_ID = "value-prop-root"


def _spec_tier_objective_id(phase_suffix: str) -> str:
    return f"spec-{phase_suffix}"


@dataclass(frozen=True)
class TrackerSeedResult:
    """Outcome of one tracker-seed invocation.

    ``reason`` is one of:

    - ``"fresh_seed"``  — root + every descendant created this run.
    - ``"already_seeded"`` — every record present pre-run; no creates.
    - ``"completed_partial"`` — root or some descendants pre-existed;
      this run created only the missing ones (AC39.4 partial-recovery).
    - ``"skipped_no_value_prop"`` — non-dev workspace without a
      ``value-prop.md`` file; seed deferred until the user supplies it.

    ``value_prop_source`` is the workspace-relative path stored on
    seeded records (``LiftedFrom.source_doc``); None when skipped.
    """

    seeded: bool
    reason: str
    classification: str
    root_id: str | None
    descendants_seeded: tuple[str, ...]
    value_prop_source: str | None


# Trackers DB path. Sub-plan E (amendment #42) — the seed writes to a
# *workspace-rooted* path, parallel to
# ``primary_persona.tracker_context.tracker_db_path_for(workspace_root)``
# (amendment #40's contributor read path). Closes the latent
# #39 ↔ #40 path-mismatch (the seed wrote to ``pos_root``, the
# contributor read from ``workspace_root`` — the moment #40's
# contributor wires to live persona registration the bug bites).
# Single source of truth for the tracker DB location: workspace-
# rooted. Method-level constant; tests can observe the seam.
TRACKER_DB_FILENAME = "objective_tracker.sqlite"


def tracker_db_path_for(workspace_root: Path | str) -> Path:
    """Return the tracker DB path for ``workspace_root``.

    Sub-plan E (amendment #42) — argument source moves from
    ``pos_root`` to ``workspace_root`` to align with
    ``primary_persona.tracker_context.tracker_db_path_for``. The
    returned path is ``<workspace_root>/workspace/objective_tracker.sqlite``;
    the seed writes here and amendment #40's contributor reads here.

    D-migration D.2 (amendment #63 / AC.D.2.1): post-D.2 the tracker
    DB lives under ``<workspace>/workspace/`` per the workspace-state
    structural-split. Delegates to the canonical
    ``workspace_paths.tracker_db_path`` helper.
    """
    from loam.workspace_bootstrap.workspace_paths import tracker_db_path

    return tracker_db_path(workspace_root)


async def seed_tracker(
    *,
    workspace_root: Path | str,
    tracker_db_path: Path | str,
    classification: str,
    value_prop: ValuePropSource,
) -> TrackerSeedResult:
    """Seed the tracker DB with the value-prop root + spec descendants.

    Idempotent: queries ``query_projection_view`` (amendment #38) for
    already-seeded records via ``ObjectiveFilter(lifted_from_source_doc
    =...)`` and creates only what is missing. Per sub-plan §6 #8 the
    re-run is "by query, not by clobber" — pre-existing user-edited
    descendants are left untouched.

    Returns a structured ``TrackerSeedResult`` describing what
    happened. Never raises on the seeded-state-already-correct path;
    raises on tracker-construction failure (DB unwriteable, etc.) so
    the failure surfaces rather than silently no-ops.

    Sub-plan §11 D-build.4 (b) — root first, then each descendant
    individually so an interrupted run leaves a consistent partial
    state that AC39.4's re-run resumes cleanly.
    """
    workspace_root = Path(workspace_root)
    tracker_db_path = Path(tracker_db_path)

    if classification == CLASSIFICATION_USER and not value_prop.available:
        return TrackerSeedResult(
            seeded=False,
            reason="skipped_no_value_prop",
            classification=classification,
            root_id=None,
            descendants_seeded=(),
            value_prop_source=None,
        )

    record = extract_value_prop_record(value_prop.source_text)
    source_doc = value_prop.source_doc

    tracker_db_path.parent.mkdir(parents=True, exist_ok=True)
    tracker = ObjectiveTracker(tracker_db_path)
    try:
        existing = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=source_doc)
        )
        existing_ids = {p.objective_id for p in existing}

        existing_spec_doc = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=SPEC_DOC_RELPATH)
        )
        existing_ids.update(p.objective_id for p in existing_spec_doc)

        descendants_seeded: list[str] = []
        root_id_pre_existed = ROOT_OBJECTIVE_ID in existing_ids

        # Root first (D-build.4 (b)).
        if not root_id_pre_existed:
            root_spec = ObjectiveSpec(
                goal=record.goal,
                parent_id=None,
                acceptance_criteria=(
                    ProseCriterion(
                        criterion_id="AC.PO.1",
                        prose=record.ac_po_1_prose,
                    ),
                    ProseCriterion(
                        criterion_id="AC.PO.2",
                        prose=record.ac_po_2_prose,
                    ),
                ),
                time_bound=TimeBound(
                    evergreen=True, review_cadence="amendment-driven"
                ),
                authored_by="user",
                lifted_from=LiftedFrom(
                    source_doc=source_doc,
                    source_ac="prime",
                ),
            )
            await tracker.create(root_spec, objective_id=ROOT_OBJECTIVE_ID)

        # Spec descendants (D-build.2 (a) — three phases).
        for suffix, ac_label, prose in _SPEC_TIER_PHASES:
            obj_id = _spec_tier_objective_id(suffix)
            if obj_id in existing_ids:
                continue
            child_spec = ObjectiveSpec(
                goal=prose,
                parent_id=ROOT_OBJECTIVE_ID,
                acceptance_criteria=(
                    ProseCriterion(
                        criterion_id=f"spec-{suffix}-met",
                        prose=(
                            f"Spec phase {ac_label} acceptance criteria are "
                            "met by the components and amendments tracing "
                            "to this objective."
                        ),
                    ),
                ),
                time_bound=TimeBound(
                    evergreen=True, review_cadence="amendment-driven"
                ),
                authored_by="user",
                lifted_from=LiftedFrom(
                    source_doc=SPEC_DOC_RELPATH,
                    source_ac=ac_label,
                ),
            )
            await tracker.create(child_spec, objective_id=obj_id)
            descendants_seeded.append(obj_id)

        if root_id_pre_existed and not descendants_seeded:
            reason = "already_seeded"
        elif root_id_pre_existed:
            reason = "completed_partial"
        elif descendants_seeded and len(descendants_seeded) < len(_SPEC_TIER_PHASES):
            # Should not occur on a fresh seed (we just created the
            # root, so every descendant is missing) but the branch
            # guards an unexpected mid-loop interruption recovery
            # path that re-enters this loop.
            reason = "completed_partial"
        else:
            reason = "fresh_seed"

        return TrackerSeedResult(
            seeded=not root_id_pre_existed or bool(descendants_seeded),
            reason=reason,
            classification=classification,
            root_id=ROOT_OBJECTIVE_ID,
            descendants_seeded=tuple(descendants_seeded),
            value_prop_source=source_doc,
        )
    finally:
        tracker.close()


# Type alias for the runner injection seam tests use.
TrackerSeedRunner = Callable[
    ..., Awaitable[TrackerSeedResult]
]


def run_seed_synchronously(
    *,
    workspace_root: Path | str,
    tracker_db_path: Path | str,
    classification: str,
    value_prop: ValuePropSource,
) -> TrackerSeedResult:
    """Synchronous wrapper around ``seed_tracker`` so the scaffold's
    sync caller can invoke the async tracker API without surfacing
    asyncio plumbing into the scaffold body.
    """
    return asyncio.run(
        seed_tracker(
            workspace_root=workspace_root,
            tracker_db_path=tracker_db_path,
            classification=classification,
            value_prop=value_prop,
        )
    )
