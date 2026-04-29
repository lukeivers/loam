"""Continuous-registration verification — AC.D-mig.4 harness.

Per plan AC.D-mig.4: after Phase γ, every NEW amendment landed via
``pos-amend apply``'s `objectives` manifest block (per pos-amend-
tracker-integration plan AC.D-pa.1) registers its declared ACs in
the tracker as part of the apply step. ``pos-amend seal`` then
populates ``lifted_from.source_commit``.

This module verifies that property end-to-end inside an isolated
tracker DB, without polluting the canonical workspace's tracker. It
does NOT verify the apply-CLI subprocess shape; it composes against
the same underlying ``register_objectives`` + ``update_source_commits``
helpers the CLI uses, which is the substrate the AC actually
guarantees.

Public entry: :func:`verify_continuous_registration` returns a
``VerifyReport`` describing what was registered + whether
source_commit landed correctly.

The module is fully synchronous: pos-amend's ``register_objectives``
runs its own ``asyncio.run`` per entry, so we cannot nest under our
own event loop. The minimal-ancestry seed runs through a separate
top-level ``asyncio.run`` BEFORE invoking the registration helper.
"""

from __future__ import annotations

import asyncio
import tempfile
from dataclasses import dataclass
from pathlib import Path

from objective_tracker import (
    LiftedFrom,
    ObjectiveFilter,
    ObjectiveSpec,
    ObjectiveTracker,
    ProseCriterion,
    TimeBound,
)


@dataclass(frozen=True)
class VerifyReport:
    """Outcome of one continuous-registration verification."""

    registered_count: int
    source_commit_updated_count: int
    fixture_amendment_id: str
    contributor_surfaces_record: bool
    failure_reason: str | None = None


def verify_continuous_registration(
    *,
    pos_amend_repo_root: Path | None = None,
) -> VerifyReport:
    """Run an end-to-end continuous-registration verification.

    Builds a tracker DB inside a tmpfs-style temporary directory,
    seeds the value-prop root + spec-v1.0 ancestor (so the fixture
    amendment-AC has a parent), then composes against pos-amend's
    public ``register_objectives`` and ``update_source_commits``
    helpers (the surface the apply + seal CLI invokes) with a
    fixture amendment manifest.

    Returns a ``VerifyReport`` describing what landed.

    The function does NOT shell out to ``pos-amend apply`` — that's a
    CLI integration test, out of scope for this verification. The
    harness composes against the registration API directly so the
    AC's substantive contract is checked.
    """
    # Late imports — keep heavy-b-migrate's install graph clean even
    # if pos-amend isn't on path at import time.
    from pos_amend.manifest import (  # type: ignore
        LiftedFromEntry,
        Manifest,
        ObjectiveEntry,
    )
    from pos_amend.tracker_registration import (  # type: ignore
        register_objectives,
        update_source_commits,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)

        # Seed the minimum ancestry the fixture needs: value-prop root +
        # spec-v1.0 (#39's seed shape). This is the only async step;
        # we run it through a top-level asyncio.run, then exit cleanly
        # before invoking the synchronous registration helpers (each of
        # which runs its OWN asyncio.run per entry — we cannot nest).
        asyncio.run(_seed_minimal_ancestry(repo_root))

        # Craft a fixture amendment manifest with one ObjectiveEntry.
        fixture_amendment_id = "amendment-fixture-vc"
        fixture_plan_doc = (
            f"docs/rebuild/plans/{fixture_amendment_id}.md"
        )
        fixture_ac_id = "AC.fixture.1"
        manifest = Manifest(
            schema_version=2,
            number=99999,
            slug="fixture-vc",
            title="fixture",
            baseline="0" * 40,
            plan=fixture_plan_doc,
            components=(),
            objectives=(
                ObjectiveEntry(
                    goal="Fixture AC.fixture.1 — verifies continuous "
                    "registration writes a record + seal updates "
                    "source_commit.",
                    parent_root=False,
                    parent_id="spec-v1.0",
                    acceptance_criteria=(
                        {
                            "kind": "prose",
                            "criterion_id": "fixture-1",
                            "prose": "Fixture criterion exercised by "
                            "verify_continuous_registration.",
                        },
                    ),
                    time_bound={"evergreen": True},
                    authored_by="user",
                    lifted_from=LiftedFromEntry(
                        source_doc=fixture_plan_doc,
                        source_ac=fixture_ac_id,
                    ),
                ),
            ),
        )

        # Register: should create exactly 1 record.
        result = register_objectives(manifest, repo_root)
        registered_count = len(result.created)

        # Verify the record landed by querying the tracker.
        tracker_db = repo_root / "objective_tracker.sqlite"
        tracker = ObjectiveTracker(tracker_db)
        try:
            projections = tracker.query_projection_view(
                ObjectiveFilter(lifted_from_source_doc=fixture_plan_doc)
            )
            if not projections:
                return VerifyReport(
                    registered_count=registered_count,
                    source_commit_updated_count=0,
                    fixture_amendment_id=fixture_amendment_id,
                    contributor_surfaces_record=False,
                    failure_reason="record not found post-register",
                )
            contributor_surfaces_record = any(
                p.lifted_from is not None
                and p.lifted_from.source_ac == fixture_ac_id
                for p in projections
            )
        finally:
            tracker.close()

        # Run update_source_commits with a fixture SHA.
        fixture_sha = "0123456789abcdef0123456789abcdef01234567"
        updated = update_source_commits(manifest, repo_root, fixture_sha)

        # Re-query and confirm source_commit is now set.
        tracker = ObjectiveTracker(tracker_db)
        try:
            projections = tracker.query_projection_view(
                ObjectiveFilter(lifted_from_source_doc=fixture_plan_doc)
            )
            sc_set = any(
                p.lifted_from is not None
                and p.lifted_from.source_commit == fixture_sha
                for p in projections
            )
        finally:
            tracker.close()

        if not sc_set:
            return VerifyReport(
                registered_count=registered_count,
                source_commit_updated_count=updated,
                fixture_amendment_id=fixture_amendment_id,
                contributor_surfaces_record=contributor_surfaces_record,
                failure_reason="source_commit not propagated post-seal",
            )

        return VerifyReport(
            registered_count=registered_count,
            source_commit_updated_count=updated,
            fixture_amendment_id=fixture_amendment_id,
            contributor_surfaces_record=contributor_surfaces_record,
            failure_reason=None,
        )


async def _seed_minimal_ancestry(repo_root: Path) -> None:
    """Seed the value-prop root + spec-v1.0 inside a fresh tmpfs tracker."""
    tracker_db = repo_root / "objective_tracker.sqlite"
    tracker = ObjectiveTracker(tracker_db)
    try:
        await tracker.create(
            ObjectiveSpec(
                goal="Verify-fixture root.",
                parent_id=None,
                acceptance_criteria=(
                    ProseCriterion(
                        criterion_id="AC.PO.1", prose="Primary-persona test."
                    ),
                    ProseCriterion(
                        criterion_id="AC.PO.2", prose="Harness test."
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
        await tracker.create(
            ObjectiveSpec(
                goal="spec v1.0 phase.",
                parent_id="value-prop-root",
                acceptance_criteria=(
                    ProseCriterion(criterion_id="spec-v1.0-met", prose="met"),
                ),
                time_bound=TimeBound(evergreen=True),
                authored_by="user",
                lifted_from=LiftedFrom(
                    source_doc=(
                        "docs/rebuild/spec/loam-objectives-spec.md"
                    ),
                    source_ac="v1.0",
                ),
            ),
            objective_id="spec-v1.0",
        )
    finally:
        tracker.close()
