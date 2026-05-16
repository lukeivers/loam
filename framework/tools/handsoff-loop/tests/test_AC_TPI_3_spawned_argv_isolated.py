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

"""AC.TPI.3 — the argv every §1b handsoff-loop site spawns carries the
empty-strict-MCP isolation and zero telegram-plugin markers.

Plan: docs/plans/telegram-poller-isolation-fix.md
Contract: pos3/.../telegram-isolation-fix-plan-2026-05-16.md §3.3
Fast structural assertion (no real binary).  Mirrors
`test_AC_LIPW_5_spawned_argv_has_no_telegram_plugin_or_channels`.
Covers BOTH §1b argv-producing sites: `goal_drive.build_goal_drive_argv`
(the orchestrator dispatch path) and the literal argv constructed in
`intake._claude_json` (asserted via the shared `inject_isolation`
contract the site uses).  The §1b argv shape is PRESERVED — the test
also asserts the existing `-p`/json/permission flags survive (no
reshape — plan §12 D-2).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop._isolation import inject_isolation  # noqa: E402
from handsoff_loop.goal_drive import (  # noqa: E402
    GoalDriveSpec,
    build_goal_drive_argv,
)

_TELEGRAM_MARKERS = (
    "plugin:telegram",
    "telegram@claude-plugins-official",
    "claude-plugins-official/telegram",
    "--channels",
)


def _assert_isolated(argv: list[str]) -> None:
    joined = " ".join(argv)
    for marker in _TELEGRAM_MARKERS:
        assert marker not in joined, (
            f"§1b argv carries kill-vector marker {marker!r}: {argv}"
        )
    assert "--strict-mcp-config" in argv, (
        f"§1b argv missing --strict-mcp-config: {argv}"
    )
    assert "--mcp-config" in argv, (
        f"§1b argv missing --mcp-config: {argv}"
    )


def test_AC_TPI_3_goal_drive_argv_is_telegram_isolated() -> None:
    """`build_goal_drive_argv` (the orchestrator-dispatch §1b site)
    returns an argv carrying the empty-strict-MCP isolation and zero
    telegram markers, with its `-p`/json/permission shape preserved."""
    spec = GoalDriveSpec(directive="do x", check_command="true")
    argv = build_goal_drive_argv(spec, cost_json=True)
    _assert_isolated(argv)
    # §1b shape preserved (plan §12 D-2 — not reshaped).
    assert "-p" in argv
    assert "--permission-mode" in argv
    assert "bypassPermissions" in argv
    assert "--output-format" in argv and "json" in argv


def test_AC_TPI_3_intake_claude_json_argv_is_telegram_isolated() -> None:
    """The intake `_claude_json` §1b site builds its argv via the same
    `inject_isolation` contract; the isolated result carries the
    empty-strict-MCP isolation, zero telegram markers, and preserves
    the intake `-p`/json shape."""
    intake_argv = inject_isolation([
        "claude", "-p", "PROMPT",
        "--model", "sonnet",
        "--output-format", "json",
        "--permission-mode", "bypassPermissions",
    ])
    _assert_isolated(intake_argv)
    assert "-p" in intake_argv
    assert "--output-format" in intake_argv and "json" in intake_argv
