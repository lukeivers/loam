"""Phase γ — extract amendment plan ACs into tracker records.

For each amendment plan file under
``docs/rebuild/plans/amendment-*.md`` (excluding ``.builder-plan.md``
companion files), parse for AC anchors and create one ObjectiveSpec
record per AC. Plans without parseable ACs receive a placeholder
record per AC.D-mig.5.

`source_commit` population: this phase does NOT itself populate
``lifted_from.source_commit`` — the per-amendment seal commit SHA is
known to the per-plan §14 method-decision register, but reading that
register reliably across all 25+ plans is brittle. Instead:

- Phase γ writes records with ``source_commit=None``.
- AC.D-mig.4's continuous-registration verifier exercises the
  ``loam amend seal`` path which DOES populate source_commit
  (via the existing ``update_source_commits`` helper at #16).
- The migration log surfaces ``source_commit=None`` records for an
  optional follow-on pass that backfills SHAs from git log.

Authoring policy (§6 constraint 7 + D-build.3 (a)): every Phase γ
record is ``authored_by="user"``.
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, field
from pathlib import Path

from loam.objective_tracker import (
    LiftedFrom,
    ObjectiveFilter,
    ObjectiveSpec,
    ObjectiveTracker,
    ProseCriterion,
    TimeBound,
)

from loam.heavy_b_migrate.extraction import (
    ExtractedAC,
    extract_acs_from_markdown,
    truncate_for_goal,
)
from loam.heavy_b_migrate.ids import (
    SPEC_V10,
    amendment_ac_objective_id,
    amendment_placeholder_id,
)


PLANS_DIR_REL = "docs/rebuild/plans"

# Match ``amendment-NN-...`` filenames; exclude ``.builder-plan.md``
# companions and ``.manifest.yaml`` siblings.
_AMENDMENT_PLAN_RE = re.compile(r"^amendment-(\d+)-.+\.md$")


@dataclass(frozen=True)
class AmendmentPlanFile:
    """A single amendment plan file discovered for Phase γ."""

    number: int
    path: Path
    relpath: str


@dataclass(frozen=True)
class AmendmentACReport:
    """Outcome of one Phase γ extraction pass."""

    created: tuple[str, ...] = field(default_factory=tuple)
    skipped: tuple[str, ...] = field(default_factory=tuple)
    placeholders_seeded: tuple[str, ...] = field(default_factory=tuple)
    plans_visited: int = 0


def discover_amendment_plans(
    workspace_root: Path | str,
) -> list[AmendmentPlanFile]:
    """Return amendment plan files in numeric order.

    Excludes ``.builder-plan.md`` companions (they contain method-level
    detail, not the canonical AC declarations) — only the
    ``amendment-NN-<name>.md`` (no ``.builder-plan``) files are lifted.
    """
    plans_dir = Path(workspace_root) / PLANS_DIR_REL
    if not plans_dir.is_dir():
        return []
    out: list[AmendmentPlanFile] = []
    for child in sorted(plans_dir.iterdir()):
        if not child.is_file() or child.suffix != ".md":
            continue
        if ".builder-plan." in child.name:
            continue
        m = _AMENDMENT_PLAN_RE.match(child.name)
        if not m:
            continue
        number = int(m.group(1))
        out.append(
            AmendmentPlanFile(
                number=number,
                path=child,
                relpath=f"{PLANS_DIR_REL}/{child.name}",
            )
        )
    out.sort(key=lambda p: p.number)
    return out


async def extract_and_seed_async(
    workspace_root: Path | str,
    tracker: ObjectiveTracker,
) -> AmendmentACReport:
    """Run Phase γ across every amendment plan in numeric order.

    Records are parented at ``spec-v1.0`` (the value-prop-rooted spec
    phase covering Phases 1–4). A future re-extension may parent each
    amendment AC at the relevant component objective; the current
    parent-policy (per builder-plan §6) is conservative — every
    amendment AC chains via spec-v1.0 to the value-prop root, which
    is the AC.PO.1 / AC.PO.2 ladder.

    Idempotency: by ``(source_doc, source_ac)``. Re-running the phase
    against an already-projected tracker is a no-op.
    """
    plans = discover_amendment_plans(workspace_root)

    created: list[str] = []
    skipped: list[str] = []
    placeholders: list[str] = []

    for plan in plans:
        try:
            text = plan.path.read_text(encoding="utf-8")
        except OSError:
            # Unreadable plan — placeholder seed.
            await _seed_amendment_placeholder(
                tracker=tracker,
                plan=plan,
                placeholders=placeholders,
                skipped=skipped,
                reason="plan file unreadable",
            )
            continue

        existing_keys: set[str] = set()
        for proj in tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=plan.relpath)
        ):
            lf = proj.lifted_from
            if lf is not None:
                existing_keys.add(lf.source_ac)

        acs = extract_acs_from_markdown(text)
        if not acs:
            await _seed_amendment_placeholder(
                tracker=tracker,
                plan=plan,
                placeholders=placeholders,
                skipped=skipped,
                reason="no parseable AC anchors in plan",
                existing_keys=existing_keys,
            )
            continue

        for ac in acs:
            if ac.ac_id in existing_keys:
                skipped.append(f"{plan.number}:{ac.ac_id}")
                continue
            await _seed_amendment_ac(
                tracker=tracker,
                plan=plan,
                ac=ac,
            )
            existing_keys.add(ac.ac_id)
            created.append(f"{plan.number}:{ac.ac_id}")

    return AmendmentACReport(
        created=tuple(created),
        skipped=tuple(skipped),
        placeholders_seeded=tuple(placeholders),
        plans_visited=len(plans),
    )


def extract_and_seed(
    workspace_root: Path | str,
    tracker: ObjectiveTracker,
) -> AmendmentACReport:
    """Synchronous wrapper around :func:`extract_and_seed_async`."""
    return asyncio.run(extract_and_seed_async(workspace_root, tracker))


async def _seed_amendment_placeholder(
    *,
    tracker: ObjectiveTracker,
    plan: AmendmentPlanFile,
    placeholders: list[str],
    skipped: list[str],
    reason: str,
    existing_keys: set[str] | None = None,
) -> None:
    """Seed a single placeholder ObjectiveSpec for an unparseable plan."""
    keys = existing_keys if existing_keys is not None else set()
    if "placeholder" in keys:
        skipped.append(f"{plan.number}:placeholder")
        return
    spec = ObjectiveSpec(
        goal=truncate_for_goal(
            f"Amendment #{plan.number} — review needed (no parseable ACs in plan)."
        ),
        parent_id=SPEC_V10,
        acceptance_criteria=(
            ProseCriterion(
                criterion_id=f"amendment-{plan.number}-placeholder",
                prose=(
                    f"Manual review required for amendment #{plan.number}. "
                    f"Reason: {reason}. Source: {plan.relpath}."
                ),
            ),
        ),
        time_bound=TimeBound(evergreen=True, review_cadence="ad-hoc"),
        authored_by="user",
        lifted_from=LiftedFrom(
            source_doc=plan.relpath,
            source_ac="placeholder",
        ),
    )
    await tracker.create(
        spec, objective_id=amendment_placeholder_id(plan.number)
    )
    placeholders.append(str(plan.number))


async def _seed_amendment_ac(
    *,
    tracker: ObjectiveTracker,
    plan: AmendmentPlanFile,
    ac: ExtractedAC,
) -> None:
    """Seed one ObjectiveSpec for a single extracted amendment AC."""
    body_for_prose = ac.body or ac.title
    prose = (
        f"{ac.ac_id}: {ac.title}\n\n{body_for_prose}"
        if ac.body
        else f"{ac.ac_id}: {ac.title}"
    )
    if len(prose) > 4000:
        prose = prose[:3997].rstrip() + "..."
    spec = ObjectiveSpec(
        goal=truncate_for_goal(
            f"Amendment #{plan.number} {ac.ac_id}: {ac.title}"
        ),
        parent_id=SPEC_V10,
        acceptance_criteria=(
            ProseCriterion(
                criterion_id=ac.ac_id[:64],
                prose=prose,
            ),
        ),
        time_bound=TimeBound(evergreen=True, review_cadence="amendment-driven"),
        authored_by="user",
        lifted_from=LiftedFrom(
            source_doc=plan.relpath,
            source_ac=ac.ac_id,
            # source_commit intentionally omitted — see module docstring.
        ),
    )
    await tracker.create(
        spec, objective_id=amendment_ac_objective_id(plan.number, ac.ac_id)
    )
