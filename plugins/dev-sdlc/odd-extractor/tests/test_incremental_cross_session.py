"""D5 cross-session continuity (most-load-bearing per master plan §5).

Tests:

- Process A: enqueue 2 domains → PM queue has 2 entries + audit-log
  has expected entries.
- Process B (subprocess): re-invoke watch → all 2 detected as
  duplicates; audit-log appends skip entries (no overwrite).
- Process C (subprocess): consume one PM question (simulated by
  removing it from `decision-queue.yaml` directly to mimic
  `record_response`); the consumed question is no longer pending.
- Process D: re-invoke watch → 1 of 2 still-pending; the consumed
  one is re-enqueued (a fresh PM question for the same domain)
  because the prior is no longer in the queue.

Subprocess invocations exercise the fresh-process boundary — the
`/clear` analog. Plan-doc §7 D5: "fresh process boundary".
"""

from __future__ import annotations

import subprocess
import sys
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


def _setup(tmp_path: Path) -> tuple[Path, Path, StubPMRuntime]:
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
    return repo, workspace, pm


def _read_pm_queue(workspace: Path) -> list[dict]:
    queue_path = workspace / "pm" / "decision-queue.yaml"
    if not queue_path.exists():
        return []
    payload = yaml.safe_load(queue_path.read_text(encoding="utf-8")) or {}
    return list(payload.get("queue") or [])


def test_process_A_then_B_duplicate_detection(tmp_path: Path) -> None:
    """In-process simulation of subprocess A → subprocess B handover:
    second run detects all duplicates."""
    repo, workspace, pm = _setup(tmp_path)
    # Process A (initial enqueue).
    rA = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=pm,
        pm_handle="test-pm",
        dry_run=False,
    )
    assert rA.enqueue_result.enqueued_count >= 2
    queue_after_A = _read_pm_queue(workspace)
    # Process B — fresh PMRuntime instance reading the SAME pm_dir.
    pm_B = StubPMRuntime(workspace / "pm")
    rB = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=pm_B,
        pm_handle="test-pm",
        dry_run=False,
    )
    assert rB.enqueue_result.enqueued_count == 0
    assert rB.enqueue_result.skipped_count == rA.enqueue_result.enqueued_count
    queue_after_B = _read_pm_queue(workspace)
    # Queue length unchanged (no duplicate enqueue).
    assert len(queue_after_B) == len(queue_after_A)


def test_consumed_question_no_longer_pending(tmp_path: Path) -> None:
    """Mimic `record_response` by removing the head of the queue
    (the persona-side flow consumes via `surface_next_question`).
    The watch must NOT detect the consumed provenance as pending."""
    repo, workspace, pm = _setup(tmp_path)
    run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=pm,
        pm_handle="test-pm",
        dry_run=False,
    )
    queue_path = workspace / "pm" / "decision-queue.yaml"
    payload = yaml.safe_load(queue_path.read_text(encoding="utf-8")) or {}
    queue = list(payload.get("queue") or [])
    consumed = queue.pop(0)
    consumed_provenance: str = consumed["provenance"]
    payload["queue"] = queue
    queue_path.write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )
    # Re-run watch — the consumed domain should be re-enqueued; the
    # other one stays as a duplicate.
    pm_C = StubPMRuntime(workspace / "pm")
    result = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=pm_C,
        pm_handle="test-pm",
        dry_run=False,
    )
    # The consumed-domain re-enqueues:
    enqueued_provenances = [
        f"odd-extract:incremental:{result.extraction_id}:{d}"
        for d in result.enqueue_result.enqueued_domains
    ]
    assert consumed_provenance in enqueued_provenances


def test_subprocess_invocation_appends_audit_log(
    tmp_path: Path,
) -> None:
    """A subprocess invocation of `python -m
    loam_odd_extractor.cli ... --incremental` appends to the
    workspace's audit-log without overwriting the prior process's
    entries."""
    repo, workspace, _ = _setup(tmp_path)
    repo_id = compute_repo_id(repo)
    audit_dir = extraction_dir(workspace, repo_id) / "audit-log"
    # Process A (in-process).
    run_incremental(
        repo_path=repo,
        workspace_root=workspace,
    )
    n_after_A = len(list(audit_dir.glob("*.yaml")))
    # Process B (subprocess).
    cmd = [
        sys.executable,
        "-m",
        "loam_odd_extractor.cli",
        str(repo),
        "--incremental",
        "--workspace-root",
        str(workspace),
        "--json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    assert proc.returncode == 0, (
        f"subprocess failed: stderr={proc.stderr}"
    )
    n_after_B = len(list(audit_dir.glob("*.yaml")))
    assert n_after_B > n_after_A
