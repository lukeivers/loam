"""AC.PRSG.8 — production-stake profile integration."""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_pr_safety.profile import (
    DEFAULT_SAFETY_PROFILE,
    is_production_stake,
    read_safety_profile,
)


def _write_manifest(workspace_root: Path, safety_profile: str) -> None:
    manifest = {
        "version": 1,
        "safety_profile": safety_profile,
        "contributions": [],
    }
    (workspace_root / "loam.yaml").write_text(
        yaml.safe_dump(manifest), encoding="utf-8"
    )


def test_default_profile_when_manifest_absent(tmp_workspace):
    """No loam.yaml → default safety_profile = "dev"."""
    assert read_safety_profile(tmp_workspace) == DEFAULT_SAFETY_PROFILE
    assert read_safety_profile(tmp_workspace) == "dev"
    assert is_production_stake(tmp_workspace) is False


def test_dev_profile_explicit(tmp_workspace):
    _write_manifest(tmp_workspace, "dev")
    assert read_safety_profile(tmp_workspace) == "dev"
    assert is_production_stake(tmp_workspace) is False


def test_research_profile(tmp_workspace):
    _write_manifest(tmp_workspace, "research")
    assert read_safety_profile(tmp_workspace) == "research"
    assert is_production_stake(tmp_workspace) is False


def test_production_stake_profile(tmp_workspace):
    _write_manifest(tmp_workspace, "production-stake")
    assert read_safety_profile(tmp_workspace) == "production-stake"
    assert is_production_stake(tmp_workspace) is True


# ---- Integration: gate decision honours profile -----------------------


def test_gate_under_production_stake_forces_ratification(
    tmp_workspace,
    workspace_with_contract,
    tmp_git_repo,
    make_repo_commit,
    capsys,
):
    """SURFACE_DECISION under production-stake → requires_ratification=True."""
    from loam_pr_safety.cli import build_pr_safety_subcommand
    import argparse
    import json

    workspace_root, repo_id = workspace_with_contract
    _write_manifest(workspace_root, "production-stake")
    # Touch AC.SYNTH.2 (PLAUSIBLE) — file app/models/order.rb at line 15-25.
    initial_lines = "\n".join(
        f"# original line {i}" for i in range(1, 30)
    )
    make_repo_commit(
        {"app/models/order.rb": initial_lines + "\n"},
        "feat: add Order model with 30 lines",
    )
    modified_lines = "\n".join(
        f"# changed line {i}" if i == 20 else f"# original line {i}"
        for i in range(1, 30)
    )
    make_repo_commit(
        {"app/models/order.rb": modified_lines + "\n"},
        "fix: tweak Order model at line 20",
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
    payload = json.loads(captured.out)
    assert payload["action"] == "SURFACE_DECISION"
    assert payload["requires_ratification"] is True


def test_gate_under_dev_proceeds_with_warning(
    workspace_with_contract,
    tmp_git_repo,
    make_repo_commit,
    capsys,
):
    """Same diff under dev → requires_ratification=False (default)."""
    from loam_pr_safety.cli import build_pr_safety_subcommand
    import argparse
    import json

    workspace_root, repo_id = workspace_with_contract
    _write_manifest(workspace_root, "dev")
    initial_lines = "\n".join(
        f"# original line {i}" for i in range(1, 30)
    )
    make_repo_commit(
        {"app/models/order.rb": initial_lines + "\n"},
        "feat: add Order model with 30 lines",
    )
    modified_lines = "\n".join(
        f"# changed line {i}" if i == 20 else f"# original line {i}"
        for i in range(1, 30)
    )
    make_repo_commit(
        {"app/models/order.rb": modified_lines + "\n"},
        "fix: tweak Order model at line 20",
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
    payload = json.loads(captured.out)
    assert payload["action"] == "SURFACE_DECISION"
    assert payload["requires_ratification"] is False
