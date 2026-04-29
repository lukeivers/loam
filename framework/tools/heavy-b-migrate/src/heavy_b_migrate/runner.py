"""Phase runner — orchestrates Phase α / β / γ in order.

AC.D-mig.6 — phase ordering is structurally enforced:

- Phase β cannot run before Phase α has seeded the relevant
  ``component-<slug>`` parent objective.
- Phase γ does not depend on Phase β individually — its records
  parent at ``spec-v1.0`` (per builder-plan §6) — but it MUST follow
  α so the spec-v1.0 ancestor is in place. (Phase α does not create
  ``spec-v1.0``; that's #39's seed. The runner verifies the seed
  before any phase runs.)
- Direct invocation `phase-beta` without prior α produces
  ``PhaseOrderingError`` with a structured diagnostic — the CLI
  surfaces this as a non-zero exit.

Idempotency: each phase queries the tracker and skips already-projected
records per ``lifted_from``. Repeated runs of ``run_phases`` against
an already-projected tracker are a no-op.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

from loam.objective_tracker import (
    ObjectiveFilter,
    ObjectiveTracker,
)

from heavy_b_migrate.amendment_acs import (
    AmendmentACReport,
    extract_and_seed_async as run_phase_gamma,
)
from heavy_b_migrate.component_acs import (
    ComponentACReport,
    extract_and_seed_async as run_phase_beta,
)
from heavy_b_migrate.components import (
    ComponentSeedReport,
    seed_phase_alpha_async as run_phase_alpha,
)
from heavy_b_migrate.ids import SPEC_V10


VALID_PHASES = ("alpha", "beta", "gamma")


class PhaseOrderingError(RuntimeError):
    """Raised when phases are requested out of order."""


@dataclass(frozen=True)
class RunReport:
    """Aggregate report from one ``run_phases`` invocation."""

    phases_run: tuple[str, ...] = field(default_factory=tuple)
    alpha: ComponentSeedReport | None = None
    beta: ComponentACReport | None = None
    gamma: AmendmentACReport | None = None


async def run_phases_async(
    workspace_root: Path | str,
    tracker_db_path: Path | str,
    *,
    phases: tuple[str, ...] = VALID_PHASES,
) -> RunReport:
    """Run the named phases in order against the workspace's tracker.

    Validates the request:

    - Every requested phase must be one of ``alpha`` / ``beta`` / ``gamma``.
    - The list must be a contiguous prefix in canonical order (i.e.
      ("alpha",), ("alpha","beta"), ("alpha","beta","gamma")). Calling
      with ``("beta",)`` or ``("alpha","gamma")`` raises
      ``PhaseOrderingError``.

    The first run on a fresh dev-mode workspace runs all three phases.
    Subsequent runs are no-ops (idempotency-by-`lifted_from`).
    """
    _validate_phase_request(phases)
    workspace_root = Path(workspace_root)
    tracker_db_path = Path(tracker_db_path)
    tracker_db_path.parent.mkdir(parents=True, exist_ok=True)
    tracker = ObjectiveTracker(tracker_db_path)
    try:
        # Pre-flight: spec-v1.0 ancestor exists.
        if not _spec_v10_present(tracker):
            raise PhaseOrderingError(
                "spec-v1.0 ancestor missing in tracker — run "
                "workspace-bootstrap tracker-seed (amendment #39) "
                "before running heavy-b-migrate phases."
            )
        alpha_report: ComponentSeedReport | None = None
        beta_report: ComponentACReport | None = None
        gamma_report: AmendmentACReport | None = None
        for phase in phases:
            if phase == "alpha":
                alpha_report = await run_phase_alpha(workspace_root, tracker)
            elif phase == "beta":
                beta_report = await run_phase_beta(workspace_root, tracker)
                if beta_report.missing_component_objective:
                    raise PhaseOrderingError(
                        "Phase β requires Phase α component objectives in "
                        "place. Missing parents for: "
                        f"{beta_report.missing_component_objective}"
                    )
            elif phase == "gamma":
                gamma_report = await run_phase_gamma(workspace_root, tracker)
        return RunReport(
            phases_run=tuple(phases),
            alpha=alpha_report,
            beta=beta_report,
            gamma=gamma_report,
        )
    finally:
        tracker.close()


def run_phases(
    workspace_root: Path | str,
    tracker_db_path: Path | str,
    *,
    phases: tuple[str, ...] = VALID_PHASES,
) -> RunReport:
    """Synchronous wrapper around :func:`run_phases_async`."""
    return asyncio.run(
        run_phases_async(workspace_root, tracker_db_path, phases=phases)
    )


def _validate_phase_request(phases: tuple[str, ...]) -> None:
    if not phases:
        raise PhaseOrderingError("at least one phase must be requested")
    for p in phases:
        if p not in VALID_PHASES:
            raise PhaseOrderingError(
                f"unknown phase {p!r}; expected one of {VALID_PHASES}"
            )
    # Must be a contiguous prefix of VALID_PHASES.
    expected = VALID_PHASES[: len(phases)]
    if tuple(phases) != expected:
        raise PhaseOrderingError(
            f"phases must be a contiguous prefix of {VALID_PHASES}; "
            f"got {phases}. Phase β requires α first; γ requires α first."
        )


def _spec_v10_present(tracker: ObjectiveTracker) -> bool:
    """Return True iff the spec-v1.0 ancestor record exists in the tracker."""
    proj = tracker.query_projection_view(ObjectiveFilter())
    return any(p.objective_id == SPEC_V10 for p in proj)
