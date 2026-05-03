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
