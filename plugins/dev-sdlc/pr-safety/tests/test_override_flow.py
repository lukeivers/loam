"""Override-flow integration tests (AC.PRSG.5 + Decision I).

Per plan-doc §4 — synthetic `contract-update:` commit + `Loam-Override:`
trailer + `--override` flag end-to-end. The CLI honours the recognition
chain and routes through the override flow when --override is set.
Without --override, the same commit shape is silently passed through
(Decision I default-no).

This file tests the recognition + override-proposed audit-log path
through the CLI surface. The full ratification-approve/reject path is
unit-tested in test_AC_PRSG_5_override_flow.py via stub PMRuntime.
"""

from __future__ import annotations

import argparse
import json

import yaml


def _gate_args(workspace_root, repo_id, repo_path, *, diff, override=False, dry_run=False):
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
        "--json",
    ]
    if override:
        cmd.append("--override")
    if dry_run:
        cmd.append("--dry-run")
    return parser.parse_args(cmd)


def test_override_flag_recognises_loam_override_trailer(
    workspace_with_contract,
    tmp_git_repo,
    make_repo_commit,
    capsys,
):
    """Override-shaped commit + --override flag → override_proposed
    audit-log entry written.
    """
    workspace_root, repo_id = workspace_with_contract
    # Build a regression commit (touches AC.SYNTH.1 line 50).
    initial_lines = "\n".join(
        f"# original line {i}" for i in range(1, 61)
    )
    make_repo_commit(
        {"app/auth.py": initial_lines + "\n"},
        "feat: add 60-line auth.py",
    )
    modified_lines = "\n".join(
        f"# changed at {i}" if i == 50 else f"# original line {i}"
        for i in range(1, 61)
    )
    make_repo_commit(
        {"app/auth.py": modified_lines + "\n"},
        "fix: tweak line 50\n\nLoam-Override: relax password rule per ADR-42\n",
    )
    args = _gate_args(
        workspace_root,
        repo_id,
        tmp_git_repo,
        diff="HEAD~1..HEAD",
        override=True,
    )
    rc = args.func(args)
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "HARD_BLOCK"

    audit_dir = workspace_root / ".loam" / "pr-safety" / "audit-log"
    entries = list(audit_dir.iterdir())
    kinds = []
    for entry in entries:
        kinds.append(
            yaml.safe_load(entry.read_text(encoding="utf-8"))["event_kind"]
        )
    # We expect at least: override_proposed + gate_decision (or dry_run).
    assert "override_proposed" in kinds


def test_no_override_flag_no_auto_promotion(
    workspace_with_contract,
    tmp_git_repo,
    make_repo_commit,
    capsys,
):
    """Even with override-shaped commit, absence of --override flag
    → no override_proposed entry (Decision I default-no honoured).
    """
    workspace_root, repo_id = workspace_with_contract
    initial_lines = "\n".join(
        f"# original line {i}" for i in range(1, 61)
    )
    make_repo_commit(
        {"app/auth.py": initial_lines + "\n"},
        "feat: add 60-line auth.py",
    )
    modified_lines = "\n".join(
        f"# changed at {i}" if i == 50 else f"# original line {i}"
        for i in range(1, 61)
    )
    make_repo_commit(
        {"app/auth.py": modified_lines + "\n"},
        "fix: tweak line 50\n\nLoam-Override: relax password rule per ADR-42\n",
    )
    args = _gate_args(
        workspace_root,
        repo_id,
        tmp_git_repo,
        diff="HEAD~1..HEAD",
        override=False,
    )
    rc = args.func(args)
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["action"] == "HARD_BLOCK"

    audit_dir = workspace_root / ".loam" / "pr-safety" / "audit-log"
    entries = list(audit_dir.iterdir())
    kinds = []
    for entry in entries:
        kinds.append(
            yaml.safe_load(entry.read_text(encoding="utf-8"))["event_kind"]
        )
    assert "override_proposed" not in kinds


def test_override_dry_run_does_not_write_overlay(
    workspace_with_contract,
    tmp_git_repo,
    make_repo_commit,
    capsys,
):
    """--override + --dry-run → no contract-overrides file written."""
    workspace_root, repo_id = workspace_with_contract
    initial_lines = "\n".join(
        f"# original line {i}" for i in range(1, 61)
    )
    make_repo_commit(
        {"app/auth.py": initial_lines + "\n"},
        "feat: add 60-line auth.py",
    )
    modified_lines = "\n".join(
        f"# changed at {i}" if i == 50 else f"# original line {i}"
        for i in range(1, 61)
    )
    make_repo_commit(
        {"app/auth.py": modified_lines + "\n"},
        "fix: tweak line 50\n\nLoam-Override: dry-run check\n",
    )
    args = _gate_args(
        workspace_root,
        repo_id,
        tmp_git_repo,
        diff="HEAD~1..HEAD",
        override=True,
        dry_run=True,
    )
    args.func(args)
    overlays_dir = (
        workspace_root
        / ".loam"
        / "pr-safety"
        / "contract-overrides"
        / repo_id
    )
    # No overlay should be written under --dry-run.
    if overlays_dir.exists():
        overlays = [
            p for p in overlays_dir.iterdir() if p.suffix == ".yaml"
        ]
        assert not overlays, (
            f"unexpected overlays under --dry-run: {overlays}"
        )
