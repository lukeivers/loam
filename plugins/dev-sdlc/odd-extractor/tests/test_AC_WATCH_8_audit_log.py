"""AC.WATCH.8 — Audit-trail floor (D6 telemetry).

Tests:

- Every watch run writes one `incremental_watch_run` entry.
- One `incremental_classification` entry per run.
- One `incremental_proposal` entry per domain-batch (enqueued or
  not).
- One `incremental_enqueue_skip_duplicate` entry per duplicate.
- Audit-log filenames follow `<YYYY-MM-DD>-<NNNN>.yaml`.
- Every entry carries schema_version + timestamp + extraction_id.
"""

from __future__ import annotations

import re
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


def _read_audit_entries(workspace: Path, repo_id: str) -> list[dict]:
    audit_dir = extraction_dir(workspace, repo_id) / "audit-log"
    if not audit_dir.exists():
        return []
    entries: list[dict] = []
    for fp in sorted(audit_dir.iterdir()):
        if fp.suffix == ".yaml":
            entries.append(
                yaml.safe_load(fp.read_text(encoding="utf-8"))
            )
    return entries


def _setup_drift_workspace(
    tmp_path: Path,
) -> tuple[Path, Path, str]:
    """Set up a workspace + repo with multi-domain drift.

    Returns (workspace, repo, repo_id).
    """
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
    return workspace, repo, compute_repo_id(repo)


def test_watch_run_event_kind_written(tmp_path: Path) -> None:
    workspace, repo, repo_id = _setup_drift_workspace(tmp_path)
    run_incremental(repo_path=repo, workspace_root=workspace)
    entries = _read_audit_entries(workspace, repo_id)
    kinds = [e.get("event_kind") for e in entries]
    assert "incremental_watch_run" in kinds


def test_classification_event_kind_written(tmp_path: Path) -> None:
    workspace, repo, repo_id = _setup_drift_workspace(tmp_path)
    run_incremental(repo_path=repo, workspace_root=workspace)
    entries = _read_audit_entries(workspace, repo_id)
    classification_entries = [
        e for e in entries
        if e.get("event_kind") == "incremental_classification"
    ]
    assert len(classification_entries) == 1
    notes = classification_entries[0]["notes"]
    assert "still_current_count=" in notes
    assert "out_of_date_count=" in notes
    assert "orphaned_count=" in notes


def test_proposal_event_kind_per_domain(tmp_path: Path) -> None:
    """Two domains drifted → 2 incremental_proposal entries."""
    workspace, repo, repo_id = _setup_drift_workspace(tmp_path)
    pm = StubPMRuntime(workspace / "pm")
    run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=pm,
        pm_handle="test-pm",
        dry_run=False,
    )
    entries = _read_audit_entries(workspace, repo_id)
    proposal_entries = [
        e for e in entries
        if e.get("event_kind") == "incremental_proposal"
    ]
    assert len(proposal_entries) == 2
    notes_concat = " ".join(e["notes"] for e in proposal_entries)
    assert "domain=payment" in notes_concat
    assert "domain=auth" in notes_concat
    assert "enqueued=true" in notes_concat


def test_skip_duplicate_event_kind(tmp_path: Path) -> None:
    """Re-running watch produces incremental_enqueue_skip_duplicate
    entries."""
    workspace, repo, repo_id = _setup_drift_workspace(tmp_path)
    pm = StubPMRuntime(workspace / "pm")
    run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=pm,
        pm_handle="test-pm",
        dry_run=False,
    )
    run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        pm_runtime=pm,
        pm_handle="test-pm",
        dry_run=False,
    )
    entries = _read_audit_entries(workspace, repo_id)
    skip_entries = [
        e for e in entries
        if e.get("event_kind") == "incremental_enqueue_skip_duplicate"
    ]
    assert len(skip_entries) == 2  # one per domain on the second run


def test_dry_run_emits_proposal_with_enqueued_false(
    tmp_path: Path,
) -> None:
    """Under dry-run, proposal entries are still written but
    enqueued=false (observability of dry-run)."""
    workspace, repo, repo_id = _setup_drift_workspace(tmp_path)
    run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        dry_run=True,
        # No pm_runtime — covers the dry-run path.
    )
    entries = _read_audit_entries(workspace, repo_id)
    proposal_entries = [
        e for e in entries
        if e.get("event_kind") == "incremental_proposal"
    ]
    assert len(proposal_entries) >= 2
    for e in proposal_entries:
        assert "enqueued=false" in e["notes"]


def test_audit_filenames_follow_convention(tmp_path: Path) -> None:
    """Filenames follow `<NNNN>.yaml` (existing odd-extractor
    observability.py convention; AC.WATCH.8 composes on this).

    Plan-doc §4 AC.WATCH.8 originally framed the shape as
    `<YYYY-MM-DD>-<NNNN>.yaml` mirroring per-project-pm's date-scoped
    convention; the actual existing odd-extractor convention (sealed
    v0.1.8 Cycle 1, `observability.py:80`) is `<NNNN>.yaml`. Cycle 1
    composes on the existing convention rather than introducing a
    new shape (per `feedback_loose_AC_text_fix_AC_not_implementation`).
    """
    workspace, repo, repo_id = _setup_drift_workspace(tmp_path)
    run_incremental(repo_path=repo, workspace_root=workspace)
    audit_dir = extraction_dir(workspace, repo_id) / "audit-log"
    assert audit_dir.exists()
    for fp in audit_dir.iterdir():
        if fp.suffix == ".yaml":
            assert re.match(
                r"^\d{4}\.yaml$", fp.name
            ), f"unexpected filename: {fp.name}"


def test_every_entry_has_required_fields(tmp_path: Path) -> None:
    """Every audit entry carries schema_version + timestamp +
    extraction_id + event_kind."""
    workspace, repo, repo_id = _setup_drift_workspace(tmp_path)
    run_incremental(repo_path=repo, workspace_root=workspace)
    entries = _read_audit_entries(workspace, repo_id)
    assert len(entries) > 0
    for e in entries:
        assert "schema_version" in e
        assert "timestamp" in e
        assert e.get("extraction_id") == repo_id
        assert "event_kind" in e
        # ISO 8601 timestamp with TZ
        assert "T" in e["timestamp"]
        assert e["timestamp"].endswith("+00:00") or "+" in e["timestamp"]
