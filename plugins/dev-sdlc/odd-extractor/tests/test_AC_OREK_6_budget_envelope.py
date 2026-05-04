"""AC.OREK.6 — Foreign-codebase budget envelope.

- Default ceiling: hard=1000, soft=500, halt-on-overrun.
- --budget-cents N sets both caps to N.
- --live without --budget-override + estimate > ceiling raises
  BudgetExceededError; CLI exits with status 3.
- --live --budget-override proceeds; audit-log records the override.
- Dry-run mode never enforces (cold-start returns 0 estimate; gate is
  --live-only).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.cost_governance import (
    BudgetEnvelope,
    ConfidenceBand,
    EstimateResult,
    OverrunAction,
)

from loam_odd_extractor import (
    BudgetExceededError,
    budget_from_cents,
    default_budget,
    enforce_budget,
)
from loam_odd_extractor.cli import main as cli_main


def test_default_budget_shape() -> None:
    e = default_budget()
    assert isinstance(e, BudgetEnvelope)
    assert e.hard_cap_money_cents == 1000
    assert e.soft_cap_money_cents == 500
    assert e.overrun_action == OverrunAction.halt


def test_budget_from_cents_sets_both_caps() -> None:
    e = budget_from_cents(250)
    assert e.hard_cap_money_cents == 250
    assert e.soft_cap_money_cents == 250
    assert e.overrun_action == OverrunAction.halt


def test_budget_from_cents_rejects_negative() -> None:
    with pytest.raises(ValueError):
        budget_from_cents(-1)


def test_enforce_budget_passes_when_estimate_within_ceiling() -> None:
    estimate = EstimateResult(
        estimated_money_cents=400,
        estimated_tokens=1000,
        estimated_time_seconds=10,
        confidence_band=ConfidenceBand.HIGH,
    )
    envelope = budget_from_cents(500)
    enforce_budget(estimate=estimate, envelope=envelope, override=False)
    # No exception → pass.


def test_enforce_budget_raises_when_estimate_exceeds_hard_cap() -> None:
    estimate = EstimateResult(
        estimated_money_cents=1500,
        estimated_tokens=10_000,
        estimated_time_seconds=60,
        confidence_band=ConfidenceBand.HIGH,
    )
    envelope = default_budget()  # hard=1000
    with pytest.raises(BudgetExceededError, match="ceiling"):
        enforce_budget(estimate=estimate, envelope=envelope, override=False)


def test_enforce_budget_passes_with_override() -> None:
    estimate = EstimateResult(
        estimated_money_cents=99999,
        estimated_tokens=1_000_000,
        estimated_time_seconds=600,
        confidence_band=ConfidenceBand.HIGH,
    )
    envelope = default_budget()
    enforce_budget(estimate=estimate, envelope=envelope, override=True)
    # No exception.


def test_dry_run_never_enforces_ceiling(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Dry-run + cold-start estimate=0 never trips the gate (not
    --live), even with very low budget."""
    rc = cli_main(
        [
            str(fixture_repo),
            "--workspace-root",
            str(workspace_root),
            "--budget-cents",
            "1",
        ]
    )
    assert rc == 0


def test_live_without_override_blocked_when_estimate_exceeds(
    monkeypatch, fixture_repo: Path, workspace_root: Path
) -> None:
    """Patch estimate_for_extraction to return high cost; --live
    without override exits with status 3 + does NOT write
    config.yaml under live mode (extraction_failed audit ok)."""
    from loam_odd_extractor import budget as budget_mod
    from loam_odd_extractor import cli as cli_mod

    high_estimate = EstimateResult(
        estimated_money_cents=99_000,
        estimated_tokens=1_000_000,
        estimated_time_seconds=600,
        confidence_band=ConfidenceBand.HIGH,
    )

    def _stub_estimate(*, scope_id: str, recent_actuals=None):
        return high_estimate

    monkeypatch.setattr(
        cli_mod, "estimate_for_extraction", _stub_estimate
    )
    monkeypatch.setattr(
        budget_mod, "estimate_for_extraction", _stub_estimate
    )

    rc = cli_main(
        [
            str(fixture_repo),
            "--workspace-root",
            str(workspace_root),
            "--live",
        ]
    )
    assert rc == 3  # _EXIT_BUDGET


def test_live_with_override_proceeds(
    monkeypatch, fixture_repo: Path, workspace_root: Path
) -> None:
    """Same high estimate + --budget-override → proceeds + writes
    a budget_override audit-log entry."""
    from loam_odd_extractor import budget as budget_mod
    from loam_odd_extractor import cli as cli_mod

    high_estimate = EstimateResult(
        estimated_money_cents=99_000,
        estimated_tokens=1_000_000,
        estimated_time_seconds=600,
        confidence_band=ConfidenceBand.HIGH,
    )

    def _stub_estimate(*, scope_id: str, recent_actuals=None):
        return high_estimate

    monkeypatch.setattr(
        cli_mod, "estimate_for_extraction", _stub_estimate
    )
    monkeypatch.setattr(
        budget_mod, "estimate_for_extraction", _stub_estimate
    )

    rc = cli_main(
        [
            str(fixture_repo),
            "--workspace-root",
            str(workspace_root),
            "--live",
            "--budget-override",
        ]
    )
    assert rc == 0
    # Find the budget_override audit-log entry.
    repo_id_dir = next(
        (workspace_root / ".loam" / "extractions").iterdir()
    )
    audit_dir = repo_id_dir / "audit-log"
    overrides_found = []
    for entry_path in audit_dir.iterdir():
        data = yaml.safe_load(entry_path.read_text(encoding="utf-8"))
        if data["event_kind"] == "budget_override":
            overrides_found.append(data)
    assert len(overrides_found) == 1
    assert overrides_found[0]["estimate"]["estimated_money_cents"] == 99_000
