"""AC.PRSG.6 — CLI: `loam pr-safety gate <repo>`."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from loam_pr_safety.cli import (
    _EXIT_HARD_BLOCK,
    _EXIT_PASS,
    _EXIT_SURFACE_DECISION,
    build_pr_safety_subcommand,
)


def _build_parser() -> argparse.ArgumentParser:
    """Construct a minimal argparse tree mirroring loam_cli.cli.main."""
    parser = argparse.ArgumentParser(prog="loam")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_pr_safety_subcommand(sub)
    return parser


def test_argparse_surface_help_runs():
    """`loam pr-safety gate --help` constructs without error."""
    parser = _build_parser()
    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["pr-safety", "gate", "--help"])
    assert exc_info.value.code == 0


def test_argparse_required_positional():
    """`gate` requires a repo positional."""
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["pr-safety", "gate"])


def test_argparse_flags_parsed():
    parser = _build_parser()
    args = parser.parse_args(
        [
            "pr-safety",
            "gate",
            "/tmp/somewhere",
            "--diff",
            "abc..def",
            "--override",
            "--dry-run",
            "--json",
            "--repo-id",
            "custom-id",
        ]
    )
    assert args.repo == Path("/tmp/somewhere")
    assert args.diff_range == "abc..def"
    assert args.override is True
    assert args.dry_run is True
    assert args.json is True
    assert args.repo_id == "custom-id"
    assert args.func.__name__ == "_run_gate"


def _make_workspace_with_contract_and_repo(
    tmp_path,
    workspace_with_contract_factory,
    git_repo,
):
    """Helper: creates a workspace+contract that points at the tmp git repo."""
    return workspace_with_contract_factory


def test_gate_pass_against_clean_diff(
    workspace_with_contract,
    tmp_git_repo,
):
    """A clean repo (no diff vs HEAD~?) → PASS exit code 0."""
    workspace_root, repo_id = workspace_with_contract
    parser = _build_parser()
    args = parser.parse_args(
        [
            "pr-safety",
            "gate",
            str(tmp_git_repo),
            "--workspace-root",
            str(workspace_root),
            "--repo-id",
            repo_id,
            "--diff",
            "HEAD..HEAD",  # No diff.
            "--json",
        ]
    )
    rc = args.func(args)
    assert rc == _EXIT_PASS


def test_gate_hard_block_against_verified_touch(
    workspace_with_contract,
    tmp_git_repo,
    make_repo_commit,
    capsys,
):
    """A diff touching the VERIFIED AC's cited line range → HARD-BLOCK."""
    workspace_root, repo_id = workspace_with_contract
    # AC.SYNTH.1 cites app/auth.py:42-58.
    # Build the file with 60 lines so we modify line 50.
    initial_lines = "\n".join(
        f"# original line {i}" for i in range(1, 61)
    )
    make_repo_commit(
        {"app/auth.py": initial_lines + "\n"},
        "feat: add auth.py with 60 lines",
    )
    # Now modify line ~50 (within citation range 42-58).
    modified_lines = "\n".join(
        f"# changed line {i}" if i == 50 else f"# original line {i}"
        for i in range(1, 61)
    )
    sha = make_repo_commit(
        {"app/auth.py": modified_lines + "\n"},
        "fix: tighten auth at line 50",
    )

    parser = _build_parser()
    args = parser.parse_args(
        [
            "pr-safety",
            "gate",
            str(tmp_git_repo),
            "--workspace-root",
            str(workspace_root),
            "--repo-id",
            repo_id,
            "--diff",
            "HEAD~1..HEAD",
            "--json",
        ]
    )
    rc = args.func(args)
    captured = capsys.readouterr()
    assert rc == _EXIT_HARD_BLOCK, (
        f"expected HARD_BLOCK; stdout: {captured.out}"
    )
    payload = json.loads(captured.out)
    assert payload["action"] == "HARD_BLOCK"


def test_gate_audit_log_written(
    workspace_with_contract,
    tmp_git_repo,
):
    """Every gate invocation writes one audit-log entry."""
    workspace_root, repo_id = workspace_with_contract
    parser = _build_parser()
    args = parser.parse_args(
        [
            "pr-safety",
            "gate",
            str(tmp_git_repo),
            "--workspace-root",
            str(workspace_root),
            "--repo-id",
            repo_id,
            "--diff",
            "HEAD..HEAD",
            "--json",
        ]
    )
    args.func(args)
    audit_dir = workspace_root / ".loam" / "pr-safety" / "audit-log"
    assert audit_dir.exists()
    entries = list(audit_dir.iterdir())
    assert len(entries) >= 1


def test_gate_with_invalid_diff_range_fails():
    parser = _build_parser()
    args = parser.parse_args(
        [
            "pr-safety",
            "gate",
            "/tmp/nonexistent",
            "--diff",
            "no-double-dot",
        ]
    )
    rc = args.func(args)
    assert rc != 0
