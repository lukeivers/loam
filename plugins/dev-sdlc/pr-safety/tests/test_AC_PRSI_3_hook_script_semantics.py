"""AC.PRSI.3 — Hook-script semantics honour production-stake profile.

LOAM_PR_SAFETY_BYPASS=1 honoured under dev/research; ignored under
production-stake (bypass attempt audit-logged as
hook_bypass_attempt_rejected).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml
import pytest

from loam_pr_safety.installers.hooks import fire_hook


def _setup_workspace(
    tmp_path: Path, *, profile: str | None
) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()
    if profile is not None:
        (ws / "loam.yaml").write_text(
            (
                "version: 1\n"
                "contributions: []\n"
                f"safety_profile: {profile}\n"
            ),
            encoding="utf-8",
        )
    return ws


def _setup_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q", "-b", "main"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@x.com"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    (repo / "README.md").write_text("# r\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "-m", "i"], check=True)
    return repo


def _audit_entries(ws: Path) -> list[dict]:
    audit_dir = ws / ".loam" / "pr-safety" / "audit-log"
    if not audit_dir.exists():
        return []
    out: list[dict] = []
    for p in sorted(audit_dir.iterdir()):
        out.append(yaml.safe_load(p.read_text(encoding="utf-8")))
    return out


def test_bypass_honoured_under_dev(
    monkeypatch, tmp_path: Path
) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path, profile="dev")
    monkeypatch.setenv("LOAM_PR_SAFETY_BYPASS", "1")

    rc = fire_hook(repo, "pre-commit", workspace_root=ws)
    assert rc == 0

    entries = _audit_entries(ws)
    bypass_entries = [
        e for e in entries if e["event_kind"] == "hook_bypass"
    ]
    assert len(bypass_entries) == 1
    assert bypass_entries[0]["decision"] == "bypass_honoured"
    assert bypass_entries[0]["safety_profile"] == "dev"
    assert bypass_entries[0]["hook"] == "pre-commit"


def test_bypass_ignored_under_production_stake(
    monkeypatch, tmp_path: Path
) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path, profile="production-stake")
    monkeypatch.setenv("LOAM_PR_SAFETY_BYPASS", "1")

    rc = fire_hook(repo, "pre-commit", workspace_root=ws)
    # Contract is missing → hook returns 0 (don't block on missing
    # contract per fire_hook contract); but bypass attempt entry
    # MUST be present.
    assert rc == 0

    entries = _audit_entries(ws)
    rejected = [
        e
        for e in entries
        if e["event_kind"] == "hook_bypass_attempt_rejected"
    ]
    assert len(rejected) == 1
    assert rejected[0]["decision"] == "bypass_rejected"
    assert rejected[0]["safety_profile"] == "production-stake"


def test_bypass_not_set_runs_normally(
    monkeypatch, tmp_path: Path
) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path, profile="dev")
    monkeypatch.delenv("LOAM_PR_SAFETY_BYPASS", raising=False)

    rc = fire_hook(repo, "pre-commit", workspace_root=ws)
    assert rc == 0

    entries = _audit_entries(ws)
    bypass_entries = [
        e
        for e in entries
        if e["event_kind"] in ("hook_bypass", "hook_bypass_attempt_rejected")
    ]
    assert len(bypass_entries) == 0


def test_default_profile_dev_when_no_manifest(
    monkeypatch, tmp_path: Path
) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path, profile=None)
    monkeypatch.setenv("LOAM_PR_SAFETY_BYPASS", "1")

    rc = fire_hook(repo, "pre-commit", workspace_root=ws)
    assert rc == 0

    entries = _audit_entries(ws)
    bypass_entries = [
        e for e in entries if e["event_kind"] == "hook_bypass"
    ]
    assert len(bypass_entries) == 1
    assert bypass_entries[0]["safety_profile"] == "dev"


def test_hook_fired_event_emitted_for_normal_invocation(
    workspace_with_contract_and_repo, monkeypatch
) -> None:
    workspace_root, repo_id, repo_path = workspace_with_contract_and_repo
    monkeypatch.delenv("LOAM_PR_SAFETY_BYPASS", raising=False)

    rc = fire_hook(repo_path, "pre-commit", workspace_root=workspace_root)
    assert rc == 0  # working-tree-vs-HEAD with no diff = PASS

    entries = _audit_entries(workspace_root)
    fired = [
        e for e in entries if e["event_kind"] == "hook_fired"
    ]
    assert len(fired) >= 1
    assert fired[-1]["hook"] == "pre-commit"
