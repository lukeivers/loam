"""AC.D-mig.6 — phase ordering enforced; α before β before γ.

The runner enforces ordering structurally:

- ``run_phases(..., phases=("beta",))`` raises PhaseOrderingError
  (β requires α first).
- ``run_phases(..., phases=("alpha", "gamma"))`` raises (γ requires
  contiguous prefix; not skip-β).
- Running α then β then γ in order succeeds.
- Re-running the full sequence on an already-projected tracker is a
  no-op (idempotency-by-`lifted_from`).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from heavy_b_migrate.runner import (
    PhaseOrderingError,
    run_phases,
)


def test_run_phases_full_sequence_succeeds(
    workspace: Path,
    seeded_tracker_db: Path,
    write_component_proposal,
    write_amendment_plan,
) -> None:
    write_component_proposal(workspace, "fixture-x", "# Fixture X\n## D1 — d1\n")
    write_amendment_plan(
        workspace, 1, "x", "# Amendment 1\n## AC1.1 — first\nBody.\n"
    )
    report = run_phases(workspace, seeded_tracker_db)
    assert report.phases_run == ("alpha", "beta", "gamma")
    assert report.alpha is not None and "fixture-x" in report.alpha.created
    assert report.beta is not None and len(report.beta.created) >= 1
    assert report.gamma is not None and len(report.gamma.created) >= 1


def test_run_phases_beta_only_rejected(
    workspace: Path, seeded_tracker_db: Path
) -> None:
    with pytest.raises(PhaseOrderingError):
        run_phases(workspace, seeded_tracker_db, phases=("beta",))


def test_run_phases_alpha_then_gamma_skips_beta_rejected(
    workspace: Path, seeded_tracker_db: Path
) -> None:
    with pytest.raises(PhaseOrderingError):
        run_phases(
            workspace, seeded_tracker_db, phases=("alpha", "gamma")
        )


def test_run_phases_rejects_unknown_phase(
    workspace: Path, seeded_tracker_db: Path
) -> None:
    with pytest.raises(PhaseOrderingError):
        run_phases(workspace, seeded_tracker_db, phases=("delta",))


def test_run_phases_pre_flight_rejects_missing_spec_v10(
    workspace: Path, tracker_db: Path
) -> None:
    """Without #39's seed (no value-prop-root + spec-v1.0), the runner
    refuses to write any records — surfaces the missing prerequisite."""
    with pytest.raises(PhaseOrderingError):
        run_phases(workspace, tracker_db)


def test_run_phases_idempotent_on_already_projected(
    workspace: Path,
    seeded_tracker_db: Path,
    write_component_proposal,
    write_amendment_plan,
) -> None:
    write_component_proposal(workspace, "fix", "# Fix\n## D1 — d\n")
    write_amendment_plan(workspace, 1, "x", "# A\n## AC1.1 — first\n")
    first = run_phases(workspace, seeded_tracker_db)
    second = run_phases(workspace, seeded_tracker_db)
    assert first.phases_run == ("alpha", "beta", "gamma")
    assert second.phases_run == ("alpha", "beta", "gamma")
    # Second run created nothing new.
    assert second.alpha is not None and second.alpha.created == ()
    assert second.beta is not None and len(second.beta.created) == 0
    assert second.gamma is not None and len(second.gamma.created) == 0
