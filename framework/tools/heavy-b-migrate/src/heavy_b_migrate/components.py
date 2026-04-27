"""Phase α — seed sealed-component objectives chained to the value-prop root.

Each component dir under ``docs/rebuild/components/<slug>/`` whose
``proposal.md`` is present yields one Phase α objective record. The
record's ``parent_id`` is the appropriate spec-phase ancestor (per
sub-plan §1.1 + builder-plan §6 — every Phase 1–4 sealed component
ladders to ``spec-v1.0``).

Idempotency-by-`lifted_from`: the seeder queries the tracker for
records whose ``lifted_from.source_doc`` equals the component's
proposal.md path; an existing match skips creation.

Per CLAUDE.md §6 constraint 7: every Phase α record is
``authored_by="user"`` (Luke approved every sealed component proposal).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from objective_tracker import (
    LiftedFrom,
    ObjectiveFilter,
    ObjectiveSpec,
    ObjectiveTracker,
    ProseCriterion,
    TimeBound,
)

from heavy_b_migrate.extraction import truncate_for_goal
from heavy_b_migrate.ids import SPEC_V10, component_objective_id


COMPONENTS_DIR_REL = "docs/rebuild/components"


@dataclass(frozen=True)
class ComponentSeedReport:
    """Outcome of one Phase α seeding pass."""

    created: tuple[str, ...] = field(default_factory=tuple)
    skipped: tuple[str, ...] = field(default_factory=tuple)
    missing_proposal: tuple[str, ...] = field(default_factory=tuple)


def discover_component_slugs(workspace_root: Path | str) -> list[str]:
    """Return component slugs (dir names) whose proposal.md is present.

    Components without a proposal.md are excluded — there's nothing
    to lift from. The list is alphabetical for determinism.
    """
    components_dir = Path(workspace_root) / COMPONENTS_DIR_REL
    if not components_dir.is_dir():
        return []
    out: list[str] = []
    for child in sorted(components_dir.iterdir()):
        if not child.is_dir():
            continue
        if (child / "proposal.md").is_file():
            out.append(child.name)
    return out


def discover_components_missing_proposal(
    workspace_root: Path | str,
) -> list[str]:
    """Return component-dir slugs that lack a proposal.md.

    Used for diagnostic logging — these dirs are skipped during Phase α.
    """
    components_dir = Path(workspace_root) / COMPONENTS_DIR_REL
    if not components_dir.is_dir():
        return []
    out: list[str] = []
    for child in sorted(components_dir.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "proposal.md").is_file():
            out.append(child.name)
    return out


def _component_proposal_relpath(slug: str) -> str:
    return f"{COMPONENTS_DIR_REL}/{slug}/proposal.md"


async def seed_phase_alpha_async(
    workspace_root: Path | str,
    tracker: ObjectiveTracker,
) -> ComponentSeedReport:
    """Seed sealed-component objectives. Idempotent via `lifted_from`.

    For each component slug discovered:

    1. Query the tracker for any record whose ``lifted_from.source_doc``
       matches the component's proposal.md path. If present, skip.
    2. Read the proposal's H1 title (first ``# `` line) for the goal
       text. Fall back to the slug name if no H1.
    3. Create the ObjectiveSpec record with parent_id ``spec-v1.0``,
       authored_by ``user``, lifted_from pointing at the proposal,
       a single prose acceptance criterion citing the proposal.

    Returns a ``ComponentSeedReport`` with the slugs created vs skipped.
    """
    slugs = discover_component_slugs(workspace_root)
    missing = discover_components_missing_proposal(workspace_root)

    created: list[str] = []
    skipped: list[str] = []
    workspace_root_p = Path(workspace_root)

    for slug in slugs:
        proposal_rel = _component_proposal_relpath(slug)
        existing = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=proposal_rel)
        )
        component_oid = component_objective_id(slug)
        if any(p.objective_id == component_oid for p in existing):
            skipped.append(slug)
            continue

        proposal_path = workspace_root_p / proposal_rel
        try:
            text = proposal_path.read_text(encoding="utf-8")
        except OSError:
            # File reported present in discover() but unreadable now.
            # Skip rather than raise — the migration is best-effort.
            skipped.append(slug)
            continue

        title = _extract_h1(text) or slug
        goal = truncate_for_goal(
            f"Sealed component: {title} — see {proposal_rel}."
        )
        criterion_prose = (
            f"The {slug} sealed component is in COMPLETE state per "
            f"docs/rebuild/STATE.md. Source proposal: {proposal_rel}."
        )
        spec = ObjectiveSpec(
            goal=goal,
            parent_id=SPEC_V10,
            acceptance_criteria=(
                ProseCriterion(
                    criterion_id=f"{slug}-sealed",
                    prose=criterion_prose,
                ),
            ),
            time_bound=TimeBound(
                evergreen=True, review_cadence="amendment-driven"
            ),
            authored_by="user",
            lifted_from=LiftedFrom(
                source_doc=proposal_rel,
                source_ac="component-root",
            ),
        )
        await tracker.create(spec, objective_id=component_oid)
        created.append(slug)

    return ComponentSeedReport(
        created=tuple(created),
        skipped=tuple(skipped),
        missing_proposal=tuple(missing),
    )


def seed_phase_alpha(
    workspace_root: Path | str,
    tracker: ObjectiveTracker,
) -> ComponentSeedReport:
    """Synchronous wrapper around :func:`seed_phase_alpha_async`."""
    return asyncio.run(seed_phase_alpha_async(workspace_root, tracker))


def _extract_h1(text: str) -> str | None:
    """Return the first ``# Title`` line, stripped. None if absent."""
    for line in text.splitlines():
        line = line.rstrip()
        if line.startswith("# ") and not line.startswith("## "):
            return line[2:].strip() or None
    return None
