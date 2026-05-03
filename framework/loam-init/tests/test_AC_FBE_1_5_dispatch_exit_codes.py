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

"""AC.FBE.1.5 — `loam init` exit-code mapping mirrors `cli_main`'s
four-class structure.

The wrapper's exit code surface:

  - 0 — bootstrap succeeded
  - 1 — TargetNotEmptyError
  - 2 — CanonicalSourceInvalidError
  - 3 — CloneFailedError
  - 4 — ScaffoldFailedError
  - 5 — other NewWorkspaceError (catch-all for halt conditions outside
        the named subclasses)

Stubs `bootstrap_new_workspace` to raise each error class in turn +
asserts the dispatched callable returns the matching exit code.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pytest

from loam.loam_init.cli import _cmd_init


def _make_args(**overrides: Any) -> argparse.Namespace:
    """Build a minimal Namespace mirroring `loam init` CLI args."""
    defaults = {
        "path": Path("/tmp/loam-fbe1-test-ws"),
        "canonical_source": "/Users/example/loam",
        "init_existing": False,
        "persona_handle": "primary",
    }
    defaults.update(overrides)
    return argparse.Namespace(**defaults)


def _patch_bootstrap_to_raise(
    monkeypatch: pytest.MonkeyPatch, exc_cls_name: str, message: str = "boom"
) -> None:
    """Patch bootstrap_new_workspace to raise the named exception class."""
    from loam.workspace_bootstrap import new_workspace as _wb

    exc_cls = getattr(_wb, exc_cls_name)

    def _raise(**_kwargs: Any) -> None:
        raise exc_cls(message)

    monkeypatch.setattr(_wb, "bootstrap_new_workspace", _raise)


def test_AC_FBE_1_5_success_returns_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Bootstrap success → exit 0."""
    from loam.workspace_bootstrap import new_workspace as _wb

    class _ScaffoldResult:
        reason = "first_run"

    class _Result:
        new_ws_path = Path("/tmp/loam-fbe1-test-ws")
        framework_dir = Path("/tmp/loam-fbe1-test-ws/framework")
        workspace_state_dir = Path("/tmp/loam-fbe1-test-ws/workspace")
        claude_dir = Path("/tmp/loam-fbe1-test-ws/.claude")
        sync_config_path = Path(
            "/tmp/loam-fbe1-test-ws/workspace/.pos/sync-config.yaml"
        )
        canonical_source = "/Users/example/loam"
        canonical_source_kind = "local"
        scaffold_result = _ScaffoldResult()
        init_existing = False

    monkeypatch.setattr(
        _wb, "bootstrap_new_workspace", lambda **_kwargs: _Result()
    )
    rc = _cmd_init(_make_args())
    assert rc == 0


def test_AC_FBE_1_5_target_not_empty_returns_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """TargetNotEmptyError → exit 1."""
    _patch_bootstrap_to_raise(monkeypatch, "TargetNotEmptyError")
    assert _cmd_init(_make_args()) == 1


def test_AC_FBE_1_5_canonical_source_invalid_returns_two(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CanonicalSourceInvalidError → exit 2."""
    _patch_bootstrap_to_raise(monkeypatch, "CanonicalSourceInvalidError")
    assert _cmd_init(_make_args()) == 2


def test_AC_FBE_1_5_clone_failed_returns_three(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CloneFailedError → exit 3."""
    _patch_bootstrap_to_raise(monkeypatch, "CloneFailedError")
    assert _cmd_init(_make_args()) == 3


def test_AC_FBE_1_5_scaffold_failed_returns_four(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ScaffoldFailedError → exit 4."""
    _patch_bootstrap_to_raise(monkeypatch, "ScaffoldFailedError")
    assert _cmd_init(_make_args()) == 4


def test_AC_FBE_1_5_other_new_workspace_error_returns_five(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Plain NewWorkspaceError (catch-all) → exit 5."""
    _patch_bootstrap_to_raise(monkeypatch, "NewWorkspaceError")
    assert _cmd_init(_make_args()) == 5


def test_AC_FBE_1_5_canonical_source_omitted_defaults_to_cwd_when_git_tree(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """FBE.9 / AC.FBE.9.1 — `--from` omitted + cwd is a git tree → exit 0.

    The resolver default-routes canonical_source to cwd when cwd has
    `.git/`. The bootstrap stub captures the resolved value to verify.
    """
    from loam.workspace_bootstrap import new_workspace as _wb

    captured: dict[str, Any] = {}

    class _ScaffoldResult:
        reason = "first_run"

    class _Result:
        new_ws_path = Path("/tmp/loam-fbe9-test-ws")
        framework_dir = Path("/tmp/loam-fbe9-test-ws/framework")
        workspace_state_dir = Path("/tmp/loam-fbe9-test-ws/workspace")
        claude_dir = Path("/tmp/loam-fbe9-test-ws/.claude")
        sync_config_path = Path(
            "/tmp/loam-fbe9-test-ws/workspace/.pos/sync-config.yaml"
        )
        canonical_source = "(captured at call-time)"
        canonical_source_kind = "local"
        scaffold_result = _ScaffoldResult()
        init_existing = False

    def _stub_bootstrap(**kwargs: Any) -> Any:
        captured.update(kwargs)
        return _Result()

    monkeypatch.setattr(_wb, "bootstrap_new_workspace", _stub_bootstrap)

    # Set up cwd as a git tree.
    (tmp_path / ".git").mkdir()
    monkeypatch.chdir(tmp_path)

    rc = _cmd_init(_make_args(canonical_source=None))
    assert rc == 0
    # Resolver should have set canonical_source to the cwd.
    assert captured["canonical_source"] == str(tmp_path.resolve())


def test_AC_FBE_1_5_canonical_source_omitted_errors_when_cwd_not_git(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """FBE.9 / AC.FBE.9.1 — `--from` omitted + cwd not a git tree → exit 2.

    The resolver returns the existing CanonicalSourceInvalidError exit
    code (2) so the surface is consistent with explicitly-passed
    invalid `--from` values.
    """
    # Ensure tmp_path has no .git/ — verify before chdir.
    assert not (tmp_path / ".git").exists()
    monkeypatch.chdir(tmp_path)

    rc = _cmd_init(_make_args(canonical_source=None))
    assert rc == 2
