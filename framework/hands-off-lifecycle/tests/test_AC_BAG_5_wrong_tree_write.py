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

"""AC.BAG.5 — Bash gate denies wrong-tree-write via
``cd <ws>/framework && <write>`` (DEV-MODE-only).

Per the locked plan-doc §4 AC.BAG.5: given workspace-mode = ``dev-
mode``, given the ``tool_input.command`` contains a ``cd`` clause
whose target resolves to ``<workspace>/framework/`` OR
``<workspace>/framework/<subdir>`` AND the command's subsequent
action is a write (``git commit``, ``git apply``, ``git restore``,
``>`` redirect, ``tee``, ``sed -i``, etc.) AND the target path is
NOT in the dev-discipline carve-out: hook returns ``permissionDecision:
"deny"`` with reason naming the failure (FIDRAFT-136 main-session-
write-prevention) + the canonical pos-v2 path as the right target +
at least one repair direction. NORMAL USE workspaces no-op this
check. The env-var override ``POS_BASH_GUARD_ALLOW=1`` bypasses
this gate (operator-trusted triage).
"""

from __future__ import annotations

import sys
import types
from pathlib import Path



REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
# Post-M6b.0: gate-hook source files MOVED to plugins/dev-sdlc/hooks/.
# Add plugin's hooks dir to sys.path so the test imports resolve to
# the moved gate modules. _gate_helpers.py STAYS at canonical
# (HOOKS_DIR above) and remains importable.
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))
if PLUGIN_HOOKS_DIR.exists():
    sys.path.insert(0, str(PLUGIN_HOOKS_DIR))


from active_scope_sentinel import ActiveScopeSentinel, ScopeBinding  # noqa: E402


def _stub_modules(monkeypatch, *, mode: str, sentinel):
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)

    ass_mod = types.ModuleType("active_scope_sentinel")
    ass_mod.read_active_scope_sentinel = lambda _: sentinel
    ass_mod.ActiveScopeSentinel = ActiveScopeSentinel
    ass_mod.ScopeBinding = ScopeBinding
    monkeypatch.setitem(sys.modules, "active_scope_sentinel", ass_mod)


def test_AC_BAG_5_cd_framework_then_git_commit_denies(
    tmp_path, monkeypatch
) -> None:
    """cd <ws>/framework && git commit ... → deny."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)
    # Build a framework dir to make the resolution concrete.
    framework_dir = tmp_path / "framework" / "orchestrator"
    framework_dir.mkdir(parents=True)
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": (
                f"cd {tmp_path}/framework/orchestrator && "
                f"git commit -m 'edit'"
            )
        },
        env={},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "wrong-tree-write"
    assert "AC.BAG.5" in decision.reason
    assert "FIDRAFT-136" in decision.reason
    assert "/Users/lukeivers/loam" in decision.reason


def test_AC_BAG_5_cd_framework_then_redirect_denies(
    tmp_path, monkeypatch
) -> None:
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)
    framework_dir = tmp_path / "framework" / "orchestrator"
    framework_dir.mkdir(parents=True)
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": (
                f"cd {tmp_path}/framework/orchestrator && "
                f"echo content > out.txt"
            )
        },
        env={},
    )
    assert decision.decision == "deny"
    assert decision.failure_class == "wrong-tree-write"


def test_AC_BAG_5_cd_framework_docs_admitted(
    tmp_path, monkeypatch
) -> None:
    """cd <ws>/framework/docs && tee → admitted (carve-out)."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)
    framework_docs = tmp_path / "framework" / "docs"
    framework_docs.mkdir(parents=True)
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": (
                f"cd {tmp_path}/framework/docs && "
                f"echo x | tee out.md"
            )
        },
        env={},
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_BAG_5_cd_no_write_admitted(
    tmp_path, monkeypatch
) -> None:
    """cd <ws>/framework && ls (no write) → admitted."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)
    framework_dir = tmp_path / "framework" / "orchestrator"
    framework_dir.mkdir(parents=True)
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": (
                f"cd {tmp_path}/framework/orchestrator && ls -la"
            )
        },
        env={},
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_BAG_5_normal_use_no_op(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="normal-use", sentinel=None)
    framework_dir = tmp_path / "framework" / "orchestrator"
    framework_dir.mkdir(parents=True)
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": (
                f"cd {tmp_path}/framework/orchestrator && "
                f"git commit -m 'edit'"
            )
        },
        env={},
    )
    assert decision.decision == "no-op"


def test_AC_BAG_5_env_override_admits(tmp_path, monkeypatch) -> None:
    """POS_BASH_GUARD_ALLOW=1 admits the wrong-tree-write."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)
    framework_dir = tmp_path / "framework" / "orchestrator"
    framework_dir.mkdir(parents=True)
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": (
                f"cd {tmp_path}/framework/orchestrator && "
                f"git commit -m 'edit'"
            )
        },
        env={"POS_BASH_GUARD_ALLOW": "1"},
    )
    assert decision.decision in ("allow", "no-op")


def test_AC_BAG_5_cd_outside_framework_admitted(
    tmp_path, monkeypatch
) -> None:
    """cd <ws>/docs && git commit → admitted (not framework/)."""
    _stub_modules(monkeypatch, mode="dev-mode", sentinel=None)
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={
            "command": (
                f"cd {tmp_path}/docs && git commit -m 'doc'"
            )
        },
        env={},
    )
    assert decision.decision in ("allow", "no-op")
