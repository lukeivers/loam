"""D6 telemetry-floor — every gate path writes the expected audit-log entry."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


def _gate(workspace_root, repo_id, repo_path, diff="HEAD..HEAD", json_mode=True):
    from loam_pr_safety.cli import build_pr_safety_subcommand

    parser = argparse.ArgumentParser(prog="loam")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_pr_safety_subcommand(sub)
    cmd = [
        "pr-safety",
        "gate",
        str(repo_path),
        "--workspace-root",
        str(workspace_root),
        "--repo-id",
        repo_id,
        "--diff",
        diff,
    ]
    if json_mode:
        cmd.append("--json")
    args = parser.parse_args(cmd)
    return args.func(args)


def test_d6_pass_writes_one_entry(workspace_with_contract, tmp_git_repo):
    workspace_root, repo_id = workspace_with_contract
    _gate(workspace_root, repo_id, tmp_git_repo)
    audit_dir = workspace_root / ".loam" / "pr-safety" / "audit-log"
    entries = list(audit_dir.iterdir())
    assert len(entries) == 1
    payload = yaml.safe_load(entries[0].read_text(encoding="utf-8"))
    assert payload["event_kind"] in ("gate_decision", "dry_run")
    assert payload["decision"] == "PASS"


def test_d6_each_invocation_appends_no_overwrite(
    workspace_with_contract, tmp_git_repo
):
    workspace_root, repo_id = workspace_with_contract
    _gate(workspace_root, repo_id, tmp_git_repo)
    _gate(workspace_root, repo_id, tmp_git_repo)
    _gate(workspace_root, repo_id, tmp_git_repo)
    audit_dir = workspace_root / ".loam" / "pr-safety" / "audit-log"
    entries = list(audit_dir.iterdir())
    assert len(entries) == 3
