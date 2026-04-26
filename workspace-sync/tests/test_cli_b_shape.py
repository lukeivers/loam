"""AC.WS.1, AC.WS.7, AC.WS.10 — CLI flow tests."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from workspace_sync.cli import (
    WorkspaceRootError,
    _ref_already_applied,
    _seed_default_envelope,
    derive_workspace_root,
    main,
)
from workspace_sync.merge_resolver import MergeVerdict, MergeResolver, ResolverBudget


def _git_head_sha(canonical: Path) -> str:
    return subprocess.check_output(
        ["git", "-C", str(canonical), "rev-parse", "HEAD"],
        text=True,
    ).strip()


def test_derive_workspace_root_from_pos_marker(tmp_path: Path) -> None:
    (tmp_path / ".pos").mkdir()
    (tmp_path / ".pos" / "sync-protected.yaml").write_text("framework_floor: []")
    assert derive_workspace_root(workspace_arg=None, cwd=tmp_path) == tmp_path


def test_derive_workspace_root_from_git_marker(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    assert derive_workspace_root(workspace_arg=None, cwd=tmp_path) == tmp_path


def test_derive_workspace_root_explicit_arg(tmp_path: Path) -> None:
    target = tmp_path / "ws"
    target.mkdir()
    assert derive_workspace_root(workspace_arg=target, cwd=tmp_path) == target


def test_derive_workspace_root_halt_on_neither(tmp_path: Path) -> None:
    """AC.WS.1: structural argument-validation halt when no marker present."""
    with pytest.raises(WorkspaceRootError, match="not derivable"):
        derive_workspace_root(workspace_arg=None, cwd=tmp_path)


def test_derive_workspace_root_invalid_arg(tmp_path: Path) -> None:
    with pytest.raises(WorkspaceRootError, match="not an existing directory"):
        derive_workspace_root(workspace_arg=tmp_path / "nope", cwd=tmp_path)


def test_seed_default_envelope_first_run(tmp_path: Path) -> None:
    """AC.WS.10: first-run writes the default envelope."""
    sp = _seed_default_envelope(tmp_path)
    target = tmp_path / ".pos" / "sync-protected.yaml"
    assert target.exists()
    # Class-A floor entries are present.
    assert any(r.pattern == ".mcp.json" for r in sp.framework_floor)


def test_ref_already_applied_no_state_returns_false(tmp_path: Path) -> None:
    assert _ref_already_applied(tmp_path, "abc123") is False


def test_main_halts_on_missing_canonical(tmp_path: Path, capsys, monkeypatch) -> None:
    """AC.WS.1: missing canonical produces structured error exit."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    (workspace / ".git").mkdir()  # marker
    rc = main(
        [
            "--canonical",
            str(tmp_path / "nope"),
            "--workspace",
            str(workspace),
        ]
    )
    assert rc == 2
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


def test_main_dry_run_against_clean_canonical(
    make_canonical_repo, make_workspace, monkeypatch, capsys
) -> None:
    """AC.WS.1 + AC.WS.7: dry-run + identical content = no apply, no error."""
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)

    # Pre-stub the resolver factory so import doesn't try to load
    # a real claude binary.
    import workspace_sync.cli as cli_mod
    real_load = cli_mod._load_merge_resolver

    def fake_factory(module_spec: str, *, budget=None) -> MergeResolver:
        class NeverInvoked:
            def invoke(self, prompt, response_model):
                raise AssertionError("resolver should not be called for clean tree")
        return MergeResolver(NeverInvoked(), budget or ResolverBudget())

    monkeypatch.setattr(cli_mod, "_load_merge_resolver", fake_factory)

    rc = main(
        [
            "--canonical",
            str(canonical),
            "--workspace",
            str(workspace),
            "--dry-run",
        ]
    )
    assert rc == 0
    captured = capsys.readouterr()
    # sync_ref printed in summary.
    assert "sync_ref" in captured.out
