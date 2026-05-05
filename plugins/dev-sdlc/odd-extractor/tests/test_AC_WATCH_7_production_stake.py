"""AC.WATCH.7 — Production-stake honour-flow.

Tests:

- Default safety_profile (no manifest) → dev → no downgrade.
- production-stake → forces dry_run=True regardless of caller.
- Defense-in-depth: contract sidecar is NEVER mutated by the watch
  regardless of profile.
- Audit-log carries `production_stake_dry_run_downgrade` note when
  caller passes dry_run=False under production-stake.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.incremental import run_incremental
from loam_odd_extractor.state import compute_repo_id, extraction_dir

from _incremental_helpers import (  # type: ignore[import-not-found]
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


def _write_workspace_manifest(
    workspace: Path, *, safety_profile: str
) -> None:
    """Write a workspace bootstrap manifest with the named
    safety_profile.

    Mirrors the schema expected by
    :func:`loam.workspace_bootstrap.load_manifest` (v0.1.6 Cycle 1).
    Minimal fields: version, contributions, safety_profile.
    """
    manifest_path = workspace / "loam.yaml"
    manifest_path.write_text(
        "version: 1\n"
        "contributions: []\n"
        f"safety_profile: {safety_profile}\n",
        encoding="utf-8",
    )


def test_default_profile_no_downgrade(tmp_path: Path) -> None:
    """No manifest → defaults to dev → no downgrade note in audit-log."""
    repo = tmp_path / "repo"
    init_git_repo(repo, files={"a.py": "print(1)\n"})
    ac = make_plausible_ac(
        ac_id="AC.MIX.1",
        backing_files=["a.py"],
        citations=["a.py:1-1"],
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    write_prior_contract(
        workspace_root=workspace,
        repo_path=repo,
        acs=[ac],
        created_at="2099-01-01T00:00:00+00:00",
    )
    result = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        dry_run=False,
    )
    # Default profile is dev; dry_run remains False as caller asked.
    assert result.safety_profile in ("dev", "research")
    assert result.dry_run is False
    repo_id = compute_repo_id(repo)
    entries = _read_audit_entries(workspace, repo_id)
    watch_entries = [
        e for e in entries
        if e.get("event_kind") == "incremental_watch_run"
    ]
    assert len(watch_entries) >= 1
    notes = watch_entries[0]["notes"]
    assert "production_stake_dry_run_downgrade" not in notes
    assert "safety_profile=dev" in notes or "safety_profile=research" in notes


def test_production_stake_forces_dry_run(tmp_path: Path) -> None:
    """production-stake silently downgrades dry_run=False to True."""
    repo = tmp_path / "repo"
    init_git_repo(repo, files={"a.py": "print(1)\n"})
    ac = make_plausible_ac(
        ac_id="AC.MIX.1",
        backing_files=["a.py"],
        citations=["a.py:1-1"],
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    _write_workspace_manifest(workspace, safety_profile="production-stake")
    write_prior_contract(
        workspace_root=workspace,
        repo_path=repo,
        acs=[ac],
        created_at="2099-01-01T00:00:00+00:00",
    )
    # Caller asks for live mode; production-stake must downgrade.
    result = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        dry_run=False,
    )
    assert result.safety_profile == "production-stake"
    assert result.dry_run is True  # forced downgrade
    repo_id = compute_repo_id(repo)
    entries = _read_audit_entries(workspace, repo_id)
    watch_entries = [
        e for e in entries
        if e.get("event_kind") == "incremental_watch_run"
    ]
    assert len(watch_entries) >= 1
    notes = watch_entries[0]["notes"]
    assert "production_stake_dry_run_downgrade" in notes
    assert "safety_profile=production-stake" in notes
    assert "dry_run=true" in notes


def test_contract_sidecar_unchanged_regardless_of_profile(
    tmp_path: Path,
) -> None:
    """Defense-in-depth: contract-draft.yaml is NEVER mutated by the
    watch regardless of profile or dry_run flag."""
    repo = tmp_path / "repo"
    init_git_repo(repo, files={"a.py": "print(1)\n"})
    ac = make_plausible_ac(
        ac_id="AC.MIX.1",
        backing_files=["a.py"],
        citations=["a.py:1-1"],
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    _write_workspace_manifest(workspace, safety_profile="dev")
    sidecar = write_prior_contract(
        workspace_root=workspace,
        repo_path=repo,
        acs=[ac],
        created_at="2099-01-01T00:00:00+00:00",
    )
    pre = sidecar.read_bytes()
    pre_mtime = sidecar.stat().st_mtime
    run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        dry_run=False,
    )
    post = sidecar.read_bytes()
    post_mtime = sidecar.stat().st_mtime
    assert pre == post
    assert pre_mtime == post_mtime


def test_research_profile_treats_like_dev(tmp_path: Path) -> None:
    """research profile: same as dev (no downgrade)."""
    repo = tmp_path / "repo"
    init_git_repo(repo, files={"a.py": "print(1)\n"})
    ac = make_plausible_ac(
        ac_id="AC.MIX.1",
        backing_files=["a.py"],
        citations=["a.py:1-1"],
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    _write_workspace_manifest(workspace, safety_profile="research")
    write_prior_contract(
        workspace_root=workspace,
        repo_path=repo,
        acs=[ac],
        created_at="2099-01-01T00:00:00+00:00",
    )
    result = run_incremental(
        repo_path=repo,
        workspace_root=workspace,
        dry_run=False,
    )
    assert result.safety_profile == "research"
    assert result.dry_run is False  # no downgrade
