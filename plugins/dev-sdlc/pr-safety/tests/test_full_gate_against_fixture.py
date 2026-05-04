"""D1 cold-state — end-to-end gate against canonical fixture."""

from __future__ import annotations

import argparse
import json

import pytest


def test_d1_cold_state_full_gate(
    workspace_with_contract,
    tmp_git_repo,
    make_repo_commit,
    capsys,
):
    """Fresh workspace + synthetic contract + tmp git repo with regression
    diff → gate runs end-to-end; produces HARD_BLOCK + audit-log entry.
    """
    from loam_pr_safety.cli import (
        _EXIT_HARD_BLOCK,
        build_pr_safety_subcommand,
    )

    workspace_root, repo_id = workspace_with_contract

    # Build a regression-shaped diff: touches AC.SYNTH.1's cited line 50
    # (range 42-58).
    initial_lines = "\n".join(
        f"# original line {i}" for i in range(1, 61)
    )
    make_repo_commit(
        {"app/auth.py": initial_lines + "\n"},
        "feat: add 60-line auth.py",
    )
    modified_lines = "\n".join(
        f"# REGRESSION at {i}" if i == 50 else f"# original line {i}"
        for i in range(1, 61)
    )
    make_repo_commit(
        {"app/auth.py": modified_lines + "\n"},
        "fix: reverse password rule",
    )

    parser = argparse.ArgumentParser(prog="loam")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_pr_safety_subcommand(sub)
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
    assert rc == _EXIT_HARD_BLOCK

    payload = json.loads(captured.out)
    assert payload["action"] == "HARD_BLOCK"
    assert "AC.SYNTH.1" in payload["touched_ac_ids"]

    # Audit-log entry present.
    audit_dir = workspace_root / ".loam" / "pr-safety" / "audit-log"
    assert audit_dir.exists()
    entries = list(audit_dir.iterdir())
    assert len(entries) >= 1
