"""Test fixtures for heavy-b-migrate.

Provides a tmpfs-style workspace fixture that mirrors the real
workspace layout enough to exercise the extractors deterministically:

- ``docs/rebuild/components/<slug>/proposal.md`` for component fixtures.
- ``docs/rebuild/plans/amendment-<NN>-<slug>.md`` for amendment fixtures.

Each test pre-seeds the tracker with the value-prop root + spec-v1.0
(mirroring #39's seed) so phase α has a parent to chain to and phase
β / γ have a tracker to compose against.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from loam.objective_tracker import (
    LiftedFrom,
    ObjectiveSpec,
    ObjectiveTracker,
    ProseCriterion,
    TimeBound,
)


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """Return a fresh workspace root with the seed-stub tree.

    Includes empty ``docs/rebuild/components/`` and
    ``docs/rebuild/plans/`` dirs so discovery functions return empty
    lists rather than raising. Tests populate these as needed.
    """
    (tmp_path / "docs" / "rebuild" / "components").mkdir(parents=True)
    (tmp_path / "docs" / "rebuild" / "plans").mkdir(parents=True)
    (tmp_path / "docs" / "rebuild" / "spec").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def tracker_db(workspace: Path) -> Path:
    """Return the tracker DB path inside the workspace fixture."""
    return workspace / "objective_tracker.sqlite"


@pytest.fixture
def seeded_tracker_db(workspace: Path, tracker_db: Path) -> Path:
    """Pre-seed the tracker with value-prop root + spec-v1.0 ancestors.

    Mirrors amendment #39's seed shape; gives Phase α a parent.
    """
    asyncio.run(_seed_minimal(tracker_db))
    return tracker_db


async def _seed_minimal(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    tracker = ObjectiveTracker(db_path)
    try:
        await tracker.create(
            ObjectiveSpec(
                goal="Workspace value-prop root.",
                parent_id=None,
                acceptance_criteria=(
                    ProseCriterion(
                        criterion_id="AC.PO.1",
                        prose="Primary-persona test placeholder.",
                    ),
                    ProseCriterion(
                        criterion_id="AC.PO.2",
                        prose="Harness test placeholder.",
                    ),
                ),
                time_bound=TimeBound(evergreen=True),
                authored_by="user",
                lifted_from=LiftedFrom(
                    source_doc="docs/rebuild/VALUE_PROPOSITION.md",
                    source_ac="prime",
                ),
            ),
            objective_id="value-prop-root",
        )
        for suffix, ac_label in (("v1.0", "v1.0"), ("v1.1", "v1.1"), ("v1.2", "v1.2")):
            await tracker.create(
                ObjectiveSpec(
                    goal=f"spec phase {suffix}.",
                    parent_id="value-prop-root",
                    acceptance_criteria=(
                        ProseCriterion(
                            criterion_id=f"spec-{suffix}-met",
                            prose="met",
                        ),
                    ),
                    time_bound=TimeBound(evergreen=True),
                    authored_by="user",
                    lifted_from=LiftedFrom(
                        source_doc="docs/rebuild/spec/loam-objectives-spec.md",
                        source_ac=ac_label,
                    ),
                ),
                objective_id=f"spec-{suffix}",
            )
    finally:
        tracker.close()


@pytest.fixture
def write_component_proposal():
    """Return a callable that writes a fixture component proposal.md."""

    def _write(workspace: Path, slug: str, proposal_text: str) -> None:
        component_dir = (
            workspace / "docs" / "rebuild" / "components" / slug
        )
        component_dir.mkdir(parents=True, exist_ok=True)
        (component_dir / "proposal.md").write_text(
            proposal_text, encoding="utf-8"
        )

    return _write


@pytest.fixture
def write_amendment_plan():
    """Return a callable that writes a fixture amendment plan."""

    def _write(
        workspace: Path, number: int, slug: str, plan_text: str
    ) -> None:
        plans_dir = workspace / "docs" / "rebuild" / "plans"
        plans_dir.mkdir(parents=True, exist_ok=True)
        (plans_dir / f"amendment-{number}-{slug}.md").write_text(
            plan_text, encoding="utf-8"
        )

    return _write
