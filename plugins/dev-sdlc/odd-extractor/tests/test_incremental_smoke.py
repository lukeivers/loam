"""AC.WATCH.10 — End-to-end smoke (D1 cold-state).

Tests the full path: `read_prior_contract → classify_evidence →
generate_proposals → group_by_domain → enqueue_through_pm` against
a synthetic prior-contract + multi-domain drift fixture.

Per plan-doc §7 D1: tmp workspace; tmp git repo seeded with the
synthetic prior-contract + multi-domain drift; assert PM queue
carries N domain-batched entries + audit-log carries all expected
event-kinds.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.incremental import run_incremental
from loam_odd_extractor.state import compute_repo_id, extraction_dir

from _incremental_helpers import (  # type: ignore[import-not-found]
    StubPMRuntime,
    commit_changes,
    init_git_repo,
    make_hypothesised_ac,
    make_plausible_ac,
    make_verified_ac,
    write_prior_contract,
)


def test_d1_cold_state_full_path(tmp_path: Path) -> None:
    """End-to-end smoke against a synthetic 4-AC prior-contract +
    multi-domain mixed-drift repo-state."""
    repo = tmp_path / "repo"
    init_git_repo(
        repo,
        files={
            "app/payment/charge.rb": "class Charge\nend\n",
            "app/auth/login.rb": "class Login\nend\n",
            "app/legacy/old_module.rb": "# legacy\n",
            "tests/test_charge.rb": "describe Charge\nend\n",
        },
    )
    # Mixed-drift commit: modify charge.rb + login.rb; delete legacy.
    commit_changes(
        repo,
        files={
            "app/payment/charge.rb": "class Charge\n  def call; end\nend\n",
            "app/auth/login.rb": "class Login\n  def call; end\nend\n",
            "app/legacy/old_module.rb": None,
        },
        message="evolve",
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    acs = [
        make_plausible_ac(
            ac_id="AC.PAYMENT.1",
            backing_files=["app/payment/charge.rb"],
            citations=["app/payment/charge.rb:1-2"],
        ),
        make_verified_ac(
            ac_id="AC.PAYMENT.2",
            backing_files=[
                "app/payment/charge.rb",
                "tests/test_charge.rb",
            ],
            citations=[
                "tests/test_charge.rb::test_idempotency",
                "app/payment/charge.rb:1-2",
            ],
        ),
        make_plausible_ac(
            ac_id="AC.AUTH.1",
            backing_files=["app/auth/login.rb"],
            citations=["app/auth/login.rb:1-2"],
        ),
        make_hypothesised_ac(
            ac_id="AC.LEGACY.1",
            backing_files=["app/legacy/old_module.rb"],
        ),
    ]
    write_prior_contract(
        workspace_root=workspace,
        repo_path=repo,
        acs=acs,
        created_at="2020-01-01T00:00:00+00:00",
    )
    pm = StubPMRuntime(workspace / "pm")

    result = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=pm,
        pm_handle="test-pm",
        dry_run=False,
    )

    # Classification: at least 1 orphan + at least 1 out-of-date.
    assert result.classification.orphaned_count >= 1
    assert result.classification.out_of_date_count >= 1
    # Domain-batches: payment + auth + legacy (orphan → legacy bucket).
    assert result.enqueue_result.enqueued_count >= 2
    assert "payment" in result.enqueue_result.enqueued_domains
    assert "auth" in result.enqueue_result.enqueued_domains
    # Legacy bucket from orphan.
    assert "legacy" in result.enqueue_result.enqueued_domains

    # Audit-log entries.
    repo_id = compute_repo_id(repo)
    audit_dir = extraction_dir(workspace, repo_id) / "audit-log"
    entries = sorted(audit_dir.iterdir())
    kinds = [
        yaml.safe_load(fp.read_text(encoding="utf-8"))["event_kind"]
        for fp in entries
        if fp.suffix == ".yaml"
    ]
    assert "incremental_watch_run" in kinds
    assert "incremental_classification" in kinds
    assert "incremental_proposal" in kinds


def test_d1_cold_state_human_readable_summary(tmp_path: Path) -> None:
    """summary_line() format mirrors plan-doc §1 expectations."""
    repo = tmp_path / "repo"
    init_git_repo(repo, files={"a.py": "print(1)\n"})
    workspace = tmp_path / "ws"
    workspace.mkdir()
    acs = [
        make_plausible_ac(
            ac_id="AC.MIX.1",
            backing_files=["a.py"],
            citations=["a.py:1-1"],
        )
    ]
    write_prior_contract(
        workspace_root=workspace,
        repo_path=repo,
        acs=acs,
        created_at="2099-01-01T00:00:00+00:00",
    )
    result = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
    )
    summary = result.summary_line()
    assert "still-current" in summary
    assert "out-of-date" in summary
    assert "orphaned" in summary
