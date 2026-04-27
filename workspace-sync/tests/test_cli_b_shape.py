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


# ---- β.1 (AC.β.1) — config-file-driven canonical_source ------------


def _patch_home(monkeypatch, home: Path) -> None:
    """Redirect ``Path.home()`` to an isolated tmp dir (no real ~/.pos/)."""
    monkeypatch.setenv("HOME", str(home))


def _stub_resolver_factory(monkeypatch) -> None:
    """Stub the resolver factory the same way other tests do."""
    import workspace_sync.cli as cli_mod

    def fake_factory(module_spec: str, *, budget=None) -> MergeResolver:
        class NeverInvoked:
            def invoke(self, prompt, response_model):
                raise AssertionError("resolver should not be called for clean tree")
        return MergeResolver(NeverInvoked(), budget or ResolverBudget())

    monkeypatch.setattr(cli_mod, "_load_merge_resolver", fake_factory)


def test_main_no_canonical_no_config_halts(
    make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 fixture-3: no --canonical + no config file → halt with structured error.

    The error message names ALL THREE fall-through paths.
    """
    workspace = make_workspace(seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    with pytest.raises(SystemExit) as exc:
        main(["--workspace", str(workspace)])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    err = captured.err
    assert "no canonical source" in err
    assert "--canonical" in err
    assert "<workspace>/.pos/sync-config.yaml" in err
    assert "~/.pos/sync-config.yaml" in err


def test_main_canonical_via_workspace_config(
    make_canonical_repo, make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 fixture-1: workspace-local sync-config.yaml supplies canonical_source.

    Operator runs `pos-sync` with no flags; the CLI loads the workspace-local
    sync-config.yaml's canonical_source: <local-path> and proceeds.
    """
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)
    _stub_resolver_factory(monkeypatch)

    # Write workspace-local sync-config.yaml with canonical_source.
    sync_cfg_path = workspace / ".pos" / "sync-config.yaml"
    sync_cfg_path.parent.mkdir(parents=True, exist_ok=True)
    sync_cfg_path.write_text(f"canonical_source: {canonical}\n")

    rc = main(["--workspace", str(workspace), "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "sync_ref" in captured.out


def test_main_canonical_via_user_config(
    make_canonical_repo, make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1: ~/-rooted sync-config.yaml supplies canonical_source.

    No workspace-local file; ~/-rooted file's canonical_source is used.
    """
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)
    _stub_resolver_factory(monkeypatch)

    user_cfg_path = home / ".pos" / "sync-config.yaml"
    user_cfg_path.parent.mkdir(parents=True, exist_ok=True)
    user_cfg_path.write_text(f"canonical_source: {canonical}\n")

    rc = main(["--workspace", str(workspace), "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "sync_ref" in captured.out


def test_main_cli_flag_overrides_config(
    make_canonical_repo, make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 fixture-5: --canonical overrides workspace-local config_source.

    Workspace-local config points to /nonexistent; --canonical points to
    real canonical; the flag wins.
    """
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)
    _stub_resolver_factory(monkeypatch)

    sync_cfg_path = workspace / ".pos" / "sync-config.yaml"
    sync_cfg_path.parent.mkdir(parents=True, exist_ok=True)
    sync_cfg_path.write_text("canonical_source: /nonexistent/path\n")

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
    assert "sync_ref" in captured.out


def test_main_back_compat_canonical_flag_no_config(
    make_canonical_repo, make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 fixture-4 / HC#1: workspace WITHOUT sync-config.yaml + --canonical
    flag = byte-identical to today's pos-sync flow.

    The original test_main_dry_run_against_clean_canonical above already
    covers this shape (no config file present, --canonical passed). This
    test additionally verifies the flow under an explicitly-isolated $HOME
    so any leftover ~/.pos/sync-config.yaml on the operator's real disk
    doesn't leak in.
    """
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)
    _stub_resolver_factory(monkeypatch)

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
    assert "sync_ref" in captured.out


def test_main_canonical_url_form_invokes_cache(
    make_canonical_repo, make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 fixture-2: URL form triggers ensure_cache_clone.

    Mocks ensure_cache_clone to return the local canonical repo path so
    the rest of the flow proceeds normally.
    """
    canonical = make_canonical_repo({"a.py": "content"})
    workspace = make_workspace({"a.py": "content"}, seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)
    _stub_resolver_factory(monkeypatch)

    import workspace_sync.cli as cli_mod

    captured_calls: list[tuple[str, str]] = []

    def fake_ensure_cache_clone(url: str, ref: str = "HEAD"):
        captured_calls.append((url, ref))
        return canonical  # the test-real local repo stands in for the cache

    monkeypatch.setattr(cli_mod, "ensure_cache_clone", fake_ensure_cache_clone)

    rc = main(
        [
            "--canonical",
            "https://github.com/test/canonical",
            "--workspace",
            str(workspace),
            "--dry-run",
        ]
    )
    assert rc == 0
    assert captured_calls == [("https://github.com/test/canonical", "HEAD")]


def test_main_canonical_relative_path_halts(
    make_workspace, monkeypatch, capsys, tmp_path
) -> None:
    """AC.β.1 / D-β.1 LOCKED: relative path halts at discrimination."""
    workspace = make_workspace(seed_envelope=True)
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    rc = main(
        [
            "--canonical",
            "relative/path",
            "--workspace",
            str(workspace),
        ]
    )
    assert rc == 2
    captured = capsys.readouterr()
    assert "must be one of" in captured.err
