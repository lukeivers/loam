"""Phase β — extract component proposal ACs into tracker records.

For each component objective seeded by Phase α, parse its
``proposal.md`` for AC anchors (per :mod:`extraction`) and create one
ObjectiveSpec record per AC under the component objective. Proposals
that fail to yield any AC anchors get a single placeholder record
per AC.D-mig.5.

Idempotency: by ``(source_doc, source_ac)`` per §6 constraint 6 + 14.
The tracker is queried once per source_doc; existing keys are skipped.

Phase β depends on Phase α having seeded the component objectives —
the runner enforces ordering. If a component objective is missing
when Phase β tries to extend it, the runner raises before any record
is written.
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

from heavy_b_migrate.components import (
    COMPONENTS_DIR_REL,
    discover_component_slugs,
)
from heavy_b_migrate.extraction import (
    ExtractedAC,
    extract_acs_from_markdown,
    truncate_for_goal,
)
from heavy_b_migrate.ids import (
    component_ac_objective_id,
    component_objective_id,
    component_placeholder_id,
)


@dataclass(frozen=True)
class ComponentACReport:
    """Outcome of one Phase β extraction pass."""

    created: tuple[str, ...] = field(default_factory=tuple)
    skipped: tuple[str, ...] = field(default_factory=tuple)
    placeholders_seeded: tuple[str, ...] = field(default_factory=tuple)
    missing_component_objective: tuple[str, ...] = field(default_factory=tuple)


def _proposal_relpath(slug: str) -> str:
    return f"{COMPONENTS_DIR_REL}/{slug}/proposal.md"


async def extract_and_seed_async(
    workspace_root: Path | str,
    tracker: ObjectiveTracker,
) -> ComponentACReport:
    """Run Phase β across every component with a Phase α objective.

    Pre-condition (enforced by the runner): every component with a
    proposal.md has a ``component-<slug>`` Phase α objective record
    in the tracker. This function checks the pre-condition per
    component and adds the slug to ``missing_component_objective`` if
    Phase α has not yet run for it (does not raise; the runner is
    responsible for the structural ordering signal).
    """
    workspace_root_p = Path(workspace_root)
    slugs = discover_component_slugs(workspace_root)

    created: list[str] = []
    skipped: list[str] = []
    placeholders: list[str] = []
    missing_parent: list[str] = []

    for slug in slugs:
        proposal_rel = _proposal_relpath(slug)
        component_oid = component_objective_id(slug)

        # Pre-condition check: Phase α objective exists.
        parent_exists = bool(
            tracker.query_projection_view(
                ObjectiveFilter(lifted_from_source_doc=proposal_rel)
            )
        )
        # The component-objective itself uses source_ac="component-root";
        # AC records will use source_ac=<the AC label>. We query once
        # per source_doc and dedupe by source_ac.
        if not parent_exists:
            missing_parent.append(slug)
            continue

        # Build the existing-key set for this proposal.
        existing_keys: set[str] = set()
        for proj in tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=proposal_rel)
        ):
            lf = proj.lifted_from
            if lf is not None:
                existing_keys.add(lf.source_ac)

        proposal_path = workspace_root_p / proposal_rel
        try:
            text = proposal_path.read_text(encoding="utf-8")
        except OSError:
            # Unreadable proposal — placeholder seed.
            await _seed_placeholder(
                tracker=tracker,
                slug=slug,
                proposal_rel=proposal_rel,
                component_oid=component_oid,
                existing_keys=existing_keys,
                placeholders=placeholders,
                skipped=skipped,
                reason="proposal.md unreadable",
            )
            continue

        acs = extract_acs_from_markdown(text)
        if not acs:
            await _seed_placeholder(
                tracker=tracker,
                slug=slug,
                proposal_rel=proposal_rel,
                component_oid=component_oid,
                existing_keys=existing_keys,
                placeholders=placeholders,
                skipped=skipped,
                reason="no parseable AC anchors in proposal.md",
            )
            continue

        for ac in acs:
            if ac.ac_id in existing_keys:
                skipped.append(f"{slug}:{ac.ac_id}")
                continue
            await _seed_one_ac(
                tracker=tracker,
                slug=slug,
                proposal_rel=proposal_rel,
                component_oid=component_oid,
                ac=ac,
            )
            existing_keys.add(ac.ac_id)
            created.append(f"{slug}:{ac.ac_id}")

    return ComponentACReport(
        created=tuple(created),
        skipped=tuple(skipped),
        placeholders_seeded=tuple(placeholders),
        missing_component_objective=tuple(missing_parent),
    )


def extract_and_seed(
    workspace_root: Path | str,
    tracker: ObjectiveTracker,
) -> ComponentACReport:
    """Synchronous wrapper around :func:`extract_and_seed_async`."""
    return asyncio.run(extract_and_seed_async(workspace_root, tracker))


async def _seed_placeholder(
    *,
    tracker: ObjectiveTracker,
    slug: str,
    proposal_rel: str,
    component_oid: str,
    existing_keys: set[str],
    placeholders: list[str],
    skipped: list[str],
    reason: str,
) -> None:
    """Seed a single placeholder ObjectiveSpec for an unparseable proposal."""
    placeholder_ac = "placeholder"
    if placeholder_ac in existing_keys:
        skipped.append(f"{slug}:placeholder")
        return
    placeholder_oid = component_placeholder_id(slug)
    spec = ObjectiveSpec(
        goal=truncate_for_goal(
            f"Component {slug} — review needed (no parseable ACs in proposal)."
        ),
        parent_id=component_oid,
        acceptance_criteria=(
            ProseCriterion(
                criterion_id=f"{slug}-placeholder",
                prose=(
                    f"Manual review required for component {slug}. "
                    f"Reason: {reason}. Source: {proposal_rel}."
                ),
            ),
        ),
        time_bound=TimeBound(evergreen=True, review_cadence="ad-hoc"),
        authored_by="user",
        lifted_from=LiftedFrom(
            source_doc=proposal_rel,
            source_ac=placeholder_ac,
        ),
    )
    await tracker.create(spec, objective_id=placeholder_oid)
    placeholders.append(slug)


async def _seed_one_ac(
    *,
    tracker: ObjectiveTracker,
    slug: str,
    proposal_rel: str,
    component_oid: str,
    ac: ExtractedAC,
) -> None:
    """Seed one ObjectiveSpec for a single extracted AC."""
    body_for_prose = ac.body or ac.title
    prose = (
        f"{ac.ac_id}: {ac.title}\n\n{body_for_prose}"
        if ac.body
        else f"{ac.ac_id}: {ac.title}"
    )
    if len(prose) > 4000:
        prose = prose[:3997].rstrip() + "..."
    spec = ObjectiveSpec(
        goal=truncate_for_goal(f"{slug} {ac.ac_id}: {ac.title}"),
        parent_id=component_oid,
        acceptance_criteria=(
            ProseCriterion(
                criterion_id=ac.ac_id[:64],
                prose=prose,
            ),
        ),
        time_bound=TimeBound(evergreen=True, review_cadence="amendment-driven"),
        authored_by="user",
        lifted_from=LiftedFrom(
            source_doc=proposal_rel,
            source_ac=ac.ac_id,
        ),
    )
    oid = component_ac_objective_id(slug, ac.ac_id)
    await tracker.create(spec, objective_id=oid)
