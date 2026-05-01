# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""β.1 AC.β.1 — sync-config schema, loader, URL discrimination, cache.

Covers:

- ``SyncConfig`` schema validation (``extra="forbid"`` mirrors #56).
- ``load_sync_config`` precedence chain (workspace-local > ~/-rooted >
  defaults).
- ``canonical_source_kind`` URL/local discrimination + halts on
  ambiguous shapes.
- ``derive_repo_id`` shape across https/http/git@ + ``.git`` suffix.
- ``ensure_cache_clone`` clone-or-fetch flow (mocked git for hermetic
  tests).

The tests run with the operator's real ``$HOME`` patched via
``monkeypatch.setenv`` to a per-test ``tmp_path``, so no test
touches the operator's actual ``~/.loam/``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from loam.workspace_sync.canonical_cache import (
    CanonicalCacheError,
    cache_root,
    derive_repo_id,
    ensure_cache_clone,
)
from loam.workspace_sync.sync_config import (
    SyncConfig,
    canonical_source_kind,
    load_sync_config,
    user_sync_config_path,
    workspace_sync_config_path,
)


# ---- Schema tests --------------------------------------------------


def test_sync_config_defaults_all_none() -> None:
    """All fields default to ``None`` so partial files validate."""
    cfg = SyncConfig()
    assert cfg.canonical_source is None
    assert cfg.cumulative_token_budget is None
    assert cfg.per_conflict_token_budget is None


def test_sync_config_canonical_source_accepted() -> None:
    cfg = SyncConfig(canonical_source="/abs/path")
    assert cfg.canonical_source == "/abs/path"


def test_sync_config_budget_fields_accepted() -> None:
    cfg = SyncConfig(
        cumulative_token_budget=200_000,
        per_conflict_token_budget=10_000,
    )
    assert cfg.cumulative_token_budget == 200_000
    assert cfg.per_conflict_token_budget == 10_000


def test_sync_config_unknown_field_rejected() -> None:
    """``extra="forbid"`` mirrors #56's sync_protected pattern."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SyncConfig(state_thing="rejected")  # type: ignore[call-arg]


def test_sync_config_budget_zero_rejected() -> None:
    """Budgets must be > 0 (Pydantic ``gt=0``)."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        SyncConfig(cumulative_token_budget=0)


# ---- Loader / precedence chain tests -------------------------------


def _patch_home(monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    """Redirect ``Path.home()`` to *home* via $HOME env-var.

    On POSIX, ``Path.home()`` honours $HOME first.
    """
    monkeypatch.setenv("HOME", str(home))


def _write_yaml(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)


def test_load_sync_config_no_files_returns_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No files exist → all fields default None."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    cfg = load_sync_config(workspace)
    assert cfg.canonical_source is None
    assert cfg.cumulative_token_budget is None


def test_load_sync_config_workspace_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """fixture-1: workspace-local file populates the field."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    _write_yaml(
        workspace_sync_config_path(workspace),
        "canonical_source: /Users/test/canonical\n",
    )

    cfg = load_sync_config(workspace)
    assert cfg.canonical_source == "/Users/test/canonical"


def test_load_sync_config_user_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """~/-rooted file populates the field when workspace-local is absent."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    _write_yaml(
        user_sync_config_path(),
        "canonical_source: https://github.com/owner/repo\n",
    )

    cfg = load_sync_config(workspace)
    assert cfg.canonical_source == "https://github.com/owner/repo"


def test_load_sync_config_workspace_overrides_user(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """fixture-6: workspace-local field wins over ~/-rooted field."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    _write_yaml(
        user_sync_config_path(),
        "canonical_source: /home/canonical\n",
    )
    _write_yaml(
        workspace_sync_config_path(workspace),
        "canonical_source: /workspace/canonical\n",
    )

    cfg = load_sync_config(workspace)
    assert cfg.canonical_source == "/workspace/canonical"


def test_load_sync_config_field_by_field_merge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Workspace-local supplies one field; ~/-rooted supplies another."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    _write_yaml(
        user_sync_config_path(),
        "cumulative_token_budget: 200000\n",
    )
    _write_yaml(
        workspace_sync_config_path(workspace),
        "canonical_source: /workspace/canonical\n",
    )

    cfg = load_sync_config(workspace)
    assert cfg.canonical_source == "/workspace/canonical"
    assert cfg.cumulative_token_budget == 200_000


def test_load_sync_config_yaml_parse_error_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    _write_yaml(
        workspace_sync_config_path(workspace),
        "canonical_source: [unclosed\n",
    )
    with pytest.raises(Exception):
        load_sync_config(workspace)


def test_load_sync_config_top_level_must_be_mapping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    _write_yaml(
        workspace_sync_config_path(workspace),
        "- a list at top level\n",
    )
    with pytest.raises(ValueError, match="must be a mapping"):
        load_sync_config(workspace)


# ---- canonical_source_kind tests -----------------------------------


def test_canonical_source_kind_https() -> None:
    """fixture-2 / discrimination-url: https URL → "url"."""
    assert canonical_source_kind("https://github.com/owner/repo") == "url"


def test_canonical_source_kind_http() -> None:
    assert canonical_source_kind("http://example.com/repo") == "url"


def test_canonical_source_kind_git_ssh() -> None:
    """discrimination-git-ssh: git@-style spec → "url"."""
    assert canonical_source_kind("git@github.com:owner/repo.git") == "url"


def test_canonical_source_kind_local_absolute() -> None:
    """fixture-1 / discrimination-local: absolute POSIX path → "local"."""
    assert canonical_source_kind("/Users/test/pos-v2") == "local"


def test_canonical_source_kind_relative_halts() -> None:
    """discrimination-relative-halts: relative paths reject (D-β.1 LOCKED)."""
    with pytest.raises(ValueError, match="must be one of"):
        canonical_source_kind("relative/path")


def test_canonical_source_kind_file_url_halts() -> None:
    """discrimination-unsupported-scheme: file:// halts (D-β.1 LOCKED)."""
    with pytest.raises(ValueError, match="must be one of"):
        canonical_source_kind("file:///abs/path")


def test_canonical_source_kind_ssh_url_halts() -> None:
    """ssh:// (without git@) halts per D-β.1 LOCKED narrowing."""
    with pytest.raises(ValueError, match="must be one of"):
        canonical_source_kind("ssh://git@host/owner/repo")


def test_canonical_source_kind_empty_halts() -> None:
    with pytest.raises(ValueError):
        canonical_source_kind("")


# ---- derive_repo_id tests ------------------------------------------


def test_derive_repo_id_https() -> None:
    assert (
        derive_repo_id("https://github.com/owner/repo")
        == "github.com/owner/repo"
    )


def test_derive_repo_id_http() -> None:
    assert (
        derive_repo_id("http://example.com/owner/repo")
        == "example.com/owner/repo"
    )


def test_derive_repo_id_git_ssh() -> None:
    assert (
        derive_repo_id("git@github.com:owner/repo.git")
        == "github.com/owner/repo"
    )


def test_derive_repo_id_strips_dot_git_suffix() -> None:
    assert (
        derive_repo_id("https://github.com/owner/repo.git")
        == "github.com/owner/repo"
    )


def test_derive_repo_id_strips_trailing_slash() -> None:
    assert (
        derive_repo_id("https://github.com/owner/repo/")
        == "github.com/owner/repo"
    )


def test_derive_repo_id_empty_input_raises() -> None:
    with pytest.raises(CanonicalCacheError):
        derive_repo_id("https://")


# ---- ensure_cache_clone tests --------------------------------------


def test_cache_root_is_under_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)
    assert cache_root() == home / ".loam" / "canonical-cache"


def test_ensure_cache_clone_clones_when_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """fixture-2: URL form invokes ``git clone`` when cache is empty."""
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    calls: list[list[str]] = []

    def fake_run(argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        # Simulate a successful clone by creating the .git marker.
        if argv[1] == "clone":
            target = Path(argv[3])
            target.mkdir(parents=True, exist_ok=True)
            (target / ".git").mkdir()
        return subprocess.CompletedProcess(
            argv, 0, stdout="", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    cache_dir = ensure_cache_clone(
        "https://github.com/owner/repo",
        ref="HEAD",
    )

    expected = home / ".loam" / "canonical-cache" / "github.com/owner/repo"
    assert cache_dir == expected
    # Two git invocations: clone + fetch.
    assert calls[0][:2] == ["git", "clone"]
    assert calls[1][:2] == ["git", "fetch"]
    assert "--all" in calls[1]
    assert "--tags" in calls[1]


def test_ensure_cache_clone_fetches_when_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Always-fetch (D-β.1 LOCKED): existing cache_dir → fetch only, no clone."""
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    # Pre-create the cache as if it had been cloned earlier.
    expected = home / ".loam" / "canonical-cache" / "github.com/owner/repo"
    expected.mkdir(parents=True)
    (expected / ".git").mkdir()

    calls: list[list[str]] = []

    def fake_run(argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        calls.append(argv)
        return subprocess.CompletedProcess(
            argv, 0, stdout="", stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    cache_dir = ensure_cache_clone(
        "https://github.com/owner/repo",
        ref="HEAD",
    )

    assert cache_dir == expected
    # Only fetch, no clone.
    assert len(calls) == 1
    assert calls[0][:2] == ["git", "fetch"]


def test_ensure_cache_clone_existing_non_git_dir_halts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A pre-existing dir without .git/ halts with structured error."""
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    expected = home / ".loam" / "canonical-cache" / "github.com/owner/repo"
    expected.mkdir(parents=True)
    # NO .git/ marker — cache directory has been corrupted somehow.

    with pytest.raises(CanonicalCacheError, match="not a git working tree"):
        ensure_cache_clone(
            "https://github.com/owner/repo",
            ref="HEAD",
        )


def test_ensure_cache_clone_clone_failure_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    home = tmp_path / "home"
    home.mkdir()
    _patch_home(monkeypatch, home)

    def fake_run(argv: list[str], **kw: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            argv, 128, stdout="", stderr="fatal: bad URL"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(CanonicalCacheError, match="exit 128"):
        ensure_cache_clone(
            "https://github.com/owner/nonexistent",
            ref="HEAD",
        )
