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

"""AC.LIPW.6 — the isolation in AC.LIPW.5 and the bench-validity
isolation in AC.LIPW.4 are THE SAME MECHANISM. No second, divergent
isolation surface exists; the driver's single isolation configuration
simultaneously protects the operator's session AND yields a clean
(operator-environment-free) bench measurement.

Plan: docs/plans/loam-init-persona-wiring-and-isolated-subloam-driver.md
Ladders to AC.PO.2.

Verification: a single isolation configuration object/path drives
both properties; a test asserts the bench-measurement environment and
the operator-protection environment are produced by ONE code path,
not two.
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[3]
        / "framework"
        / "tools"
        / "subloam-driver"
        / "src"
    ),
)

from subloam_driver import (  # noqa: E402
    IsolationConfig,
    build_isolated_claude_argv,
    build_isolated_env,
)
from subloam_driver import driver as driver_mod  # noqa: E402


def _isolation(tmp_path: Path) -> IsolationConfig:
    return IsolationConfig(
        claude_config_dir=tmp_path / ".claude-home",
        empty_mcp_config_path=tmp_path / "empty.mcp.json",
        workspace_slug="iso-subloam-one",
    )


def test_AC_LIPW_6_single_config_object_drives_both_properties(
    tmp_path: Path,
) -> None:
    """One IsolationConfig instance yields BOTH the operator-
    protection env (token + API-key scrubbed) AND the bench-validity
    argv (empty MCP, no channels, no telegram plugin) — from the same
    object, no second config. The corrected (D-LIPW.5 build-time)
    mechanism: the telegram-plugin/channel/MCP exclusion IS both
    properties; it is one code path, not two."""
    iso = _isolation(tmp_path)

    env = build_isolated_env(
        iso, base_env={"TELEGRAM_BOT_TOKEN": "x", "PATH": "/usr/bin"}
    )
    argv = build_isolated_claude_argv(iso)

    # Operator-protection falls out: token + API-key scrubbed.
    assert "TELEGRAM_BOT_TOKEN" not in env
    assert "ANTHROPIC_API_KEY" not in env
    # Bench-validity falls out of the SAME object: empty MCP + no
    # channels + no telegram plugin (the necessary-and-sufficient
    # kill-vector isolation).
    assert "--strict-mcp-config" in argv
    joined = " ".join(argv)
    assert "--channels" not in joined
    assert "plugin:telegram" not in joined
    # The empty-MCP path traces to the one IsolationConfig — not two
    # divergent surfaces.
    assert str(iso.empty_mcp_config_path) in argv


def test_AC_LIPW_6_no_second_isolation_surface_in_module() -> None:
    """Structural: the driver module exposes exactly ONE isolation
    config type and the spawn env/argv are built by exactly one
    function each. A second divergent isolation builder would be an
    AC.LIPW.6 violation."""
    members = dict(inspect.getmembers(driver_mod))
    # Exactly one IsolationConfig dataclass.
    iso_types = [
        name
        for name, obj in members.items()
        if isinstance(obj, type)
        and name.endswith("IsolationConfig")
    ]
    assert iso_types == ["IsolationConfig"], (
        f"expected exactly one isolation config type; got {iso_types}"
    )
    # Exactly one env-builder + one argv-builder (no parallel
    # bench-only vs operator-only variants).
    env_builders = [
        n for n in members if n.startswith("build_isolated_env")
    ]
    argv_builders = [
        n for n in members if n.startswith("build_isolated_claude_argv")
    ]
    assert env_builders == ["build_isolated_env"]
    assert argv_builders == ["build_isolated_claude_argv"]


def test_AC_LIPW_6_driver_drive_uses_the_same_builders(
    tmp_path: Path,
) -> None:
    """The PTY drive path constructs the spawn env+argv via the same
    two builders the AC.LIPW.5 assertions check — not an inline
    divergent isolation construction."""
    src = inspect.getsource(driver_mod.SubLoamDriver.drive)
    assert "build_isolated_claude_argv(" in src
    assert "build_isolated_env(" in src
    # drive() must not CONSTRUCT a second isolation surface inline:
    # no inline assignment of CLAUDE_CONFIG_DIR (reading env.get(...)
    # for the result record is fine — that is the same env the single
    # builder produced) and no inline --channels argv construction.
    assert 'env["CLAUDE_CONFIG_DIR"]' not in src
    assert '"CLAUDE_CONFIG_DIR"]' not in src.replace(
        'env.get("CLAUDE_CONFIG_DIR", "")', ""
    )
    assert "--channels" not in src
