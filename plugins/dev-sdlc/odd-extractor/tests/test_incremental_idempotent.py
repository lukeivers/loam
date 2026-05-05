"""D2 idempotency variant — 5 watch invocations against the same
state produce byte-identical proposal sets.

Per master plan dispatch + plan-doc §7 D2: 5+ watch runs on same
state are byte-identical.
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
    make_plausible_ac,
    write_prior_contract,
)


def _setup(tmp_path: Path) -> tuple[Path, Path, Path, StubPMRuntime]:
    repo = tmp_path / "repo"
    init_git_repo(
        repo,
        files={
            "app/payment/charge.rb": "class Charge\nend\n",
            "app/auth/login.rb": "class Login\nend\n",
        },
    )
    commit_changes(
        repo,
        files={
            "app/payment/charge.rb": "class Charge\n  def call; end\nend\n",
            "app/auth/login.rb": "class Login\n  def call; end\nend\n",
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
        make_plausible_ac(
            ac_id="AC.AUTH.1",
            backing_files=["app/auth/login.rb"],
            citations=["app/auth/login.rb:1-2"],
        ),
    ]
    write_prior_contract(
        workspace_root=workspace,
        repo_path=repo,
        acs=acs,
        created_at="2020-01-01T00:00:00+00:00",
    )
    pm = StubPMRuntime(workspace / "pm")
    return tmp_path, repo, workspace, pm


def test_five_runs_identical_classification(tmp_path: Path) -> None:
    """All 5 runs produce same still_current/out_of_date/orphaned
    counts."""
    _, repo, workspace, pm = _setup(tmp_path)
    counts = []
    for _ in range(5):
        result = run_incremental(
            repo_path=repo,
            workspace_root=workspace,
            pm_runtime=pm,
            pm_handle="test-pm",
            dry_run=False,
        )
        counts.append(
            (
                result.classification.still_current_count,
                result.classification.out_of_date_count,
                result.classification.orphaned_count,
            )
        )
    # All 5 tuples identical.
    assert len(set(counts)) == 1


def test_first_run_enqueues_subsequent_skip(tmp_path: Path) -> None:
    """Run 1 enqueues N domains; runs 2-5 all skip them."""
    _, repo, workspace, pm = _setup(tmp_path)
    # Run 1.
    r1 = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=pm,
        pm_handle="test-pm",
        dry_run=False,
    )
    n_enqueued = r1.enqueue_result.enqueued_count
    assert n_enqueued >= 2  # at least payment + auth
    assert r1.enqueue_result.skipped_count == 0
    # Runs 2-5.
    for _ in range(4):
        r = run_incremental(
            repo_path=repo,
            workspace_root=workspace,
            pm_runtime=pm,
            pm_handle="test-pm",
            dry_run=False,
        )
        assert r.enqueue_result.enqueued_count == 0
        assert r.enqueue_result.skipped_count == n_enqueued


def test_audit_log_grows_monotonically(tmp_path: Path) -> None:
    """5 runs → audit-log grows; no overwrite; new entries appended."""
    _, repo, workspace, pm = _setup(tmp_path)
    repo_id = compute_repo_id(repo)
    audit_dir = extraction_dir(workspace, repo_id) / "audit-log"
    counts = []
    for _ in range(5):
        run_incremental(
            repo_path=repo,
            workspace_root=workspace,
            pm_runtime=pm,
            pm_handle="test-pm",
            dry_run=False,
        )
        counts.append(
            len(list(audit_dir.glob("*.yaml")))
        )
    # Strictly monotonic (each run appends at least one entry).
    for prev, nxt in zip(counts, counts[1:]):
        assert nxt > prev


def test_proposal_set_byte_identical(tmp_path: Path) -> None:
    """Proposal sets across 5 runs are byte-identical (modulo
    timestamps inside each proposal — proposed_evidence is stable;
    affected_files sorted; ac_id sorted)."""
    _, repo, workspace, pm = _setup(tmp_path)
    snapshots = []
    for _ in range(5):
        result = run_incremental(
            repo_path=repo,
            workspace_root=workspace,
            pm_runtime=pm,
            pm_handle="test-pm",
            dry_run=False,
        )
        snapshot = tuple(
            (
                p.ac_id,
                p.drift_kind,
                p.affected_files,
                p.confidence_band.value,
            )
            for p in result.proposal_set.proposals
        )
        snapshots.append(snapshot)
    # All 5 byte-identical.
    assert len(set(snapshots)) == 1
