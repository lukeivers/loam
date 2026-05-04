"""D5 cross-session — audit-log persists across fresh-process boundary."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import yaml


def test_d5_audit_log_persists_across_subprocess(
    workspace_with_contract,
    tmp_git_repo,
):
    """Process A writes audit-log; process B (fresh subprocess) appends
    a new entry — both visible.
    """
    workspace_root, repo_id = workspace_with_contract
    audit_dir = workspace_root / ".loam" / "pr-safety" / "audit-log"

    # Process A — invoke the CLI directly (in-process).
    import argparse

    from loam_pr_safety.cli import build_pr_safety_subcommand

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
            "HEAD..HEAD",
            "--json",
        ]
    )
    args.func(args)
    entries_after_a = list(audit_dir.iterdir())
    assert len(entries_after_a) == 1

    # Process B — fresh subprocess invocation of `loam pr-safety gate`.
    env = os.environ.copy()
    proc = subprocess.run(  # noqa: S603 — controlled command
        [
            "loam",
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
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"subprocess failed: {proc.stderr}\nstdout: {proc.stdout}"
    )

    # Audit-log now has 2 entries; first is preserved (no overwrite).
    entries_after_b = sorted(audit_dir.iterdir(), key=lambda p: p.name)
    assert len(entries_after_b) == 2

    # Process A's entry filename + payload preserved.
    a_payload = yaml.safe_load(
        entries_after_a[0].read_text(encoding="utf-8")
    )
    a_payload_after = yaml.safe_load(
        entries_after_b[0].read_text(encoding="utf-8")
    )
    assert a_payload == a_payload_after


def test_d5_decisions_stable_across_processes(
    workspace_with_contract, tmp_git_repo
):
    """Same gate invocation in two fresh processes → same decision
    (modulo timestamps).
    """
    workspace_root, repo_id = workspace_with_contract
    env = os.environ.copy()
    cmd = [
        "loam",
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
    p1 = subprocess.run(cmd, env=env, capture_output=True, text=True)
    p2 = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert p1.returncode == p2.returncode

    import json

    payload1 = json.loads(p1.stdout)
    payload2 = json.loads(p2.stdout)
    assert payload1["action"] == payload2["action"]
    assert payload1["requires_ratification"] == payload2["requires_ratification"]
    assert payload1["touched_ac_ids"] == payload2["touched_ac_ids"]
