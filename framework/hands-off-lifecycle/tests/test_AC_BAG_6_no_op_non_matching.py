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

"""AC.BAG.6 — Bash gate is no-op for non-targeted commands
(UNIVERSAL behavior — applies to non-matching commands in any mode).

Per the locked plan-doc §4 AC.BAG.6: given a Bash tool call whose
``tool_input.command`` matches none of the AC.BAG.1..AC.BAG.5
patterns: hook returns no ``permissionDecision`` (default-allow).
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest


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


def _stub_modules(monkeypatch, *, mode: str):
    cls_mod = types.ModuleType("corpus_load_sentinel")
    cls_mod.workspace_mode = lambda _: mode
    monkeypatch.setitem(sys.modules, "corpus_load_sentinel", cls_mod)


@pytest.mark.parametrize(
    "command",
    [
        "echo hello",
        "ls -la",
        "git status",
        "git log --oneline",
        "pytest -q",
        "python -c 'print(1)'",
        "find . -name '*.py' | head",
        "cat /etc/hostname",
        "pwd",
        "true",
    ],
)
def test_AC_BAG_6_normal_command_no_deny(
    tmp_path, monkeypatch, command
) -> None:
    """Non-matching commands → allow / no-op (default-allow)."""
    _stub_modules(monkeypatch, mode="dev-mode")
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": command},
        env={},
    )
    assert decision.decision != "deny"
    assert decision.failure_class is None


def test_AC_BAG_6_normal_use_universal_admits_normal_commands(
    tmp_path, monkeypatch
) -> None:
    _stub_modules(monkeypatch, mode="normal-use")
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": "ls /tmp"},
        env={},
    )
    assert decision.decision != "deny"


def test_AC_BAG_6_empty_command_no_op(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={"command": ""},
        env={},
    )
    assert decision.decision == "no-op"


def test_AC_BAG_6_missing_command_no_op(tmp_path, monkeypatch) -> None:
    _stub_modules(monkeypatch, mode="dev-mode")
    import bash_guard

    decision = bash_guard.evaluate(
        workspace_root=tmp_path,
        tool_name="Bash",
        tool_input={},
        env={},
    )
    assert decision.decision == "no-op"
