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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PROMO.2 — a ``claude`` argv constructed via the shared surface
carries the empty-strict-MCP isolation and zero telegram-plugin
markers; the env has TELEGRAM_BOT_TOKEN /
CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN / ANTHROPIC_API_KEY absent AND
CLAUDE_PERSONA set (belt-and-braces).

Plan: docs/plans/telegram-5-fix.md §3.3
Fast structural assertion (no real binary).  Mirrors the sealed
`test_AC_TPI_3_*` / `test_AC_TPI_4_*` patterns, extended with the
`CLAUDE_PERSONA` independent-defense assertion the promote adds.
Falsifiable: a regression dropping the isolation flags, leaking a
token spelling, or omitting CLAUDE_PERSONA -> RED.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from loam_spawn_isolation import (  # noqa: E402
    ISOLATED_PERSONA_VALUE,
    inject_isolation,
    isolated_claude_argv,
    isolated_env,
)

_TELEGRAM_MARKERS = (
    "plugin:telegram",
    "telegram@claude-plugins-official",
    "claude-plugins-official/telegram",
    "--channels",
)


def _assert_argv_isolated(argv: list[str]) -> None:
    joined = " ".join(argv)
    for marker in _TELEGRAM_MARKERS:
        assert marker not in joined, (
            f"shared-surface argv carries kill-vector marker "
            f"{marker!r}: {argv}"
        )
    assert "--strict-mcp-config" in argv, (
        f"shared-surface argv missing --strict-mcp-config: {argv}"
    )
    assert "--mcp-config" in argv, (
        f"shared-surface argv missing --mcp-config: {argv}"
    )


def test_AC_PROMO_2_argv_carries_isolation_zero_markers() -> None:
    """An argv built via the shared surface carries the
    empty-strict-MCP isolation, zero telegram markers, and preserves
    the caller's `-p`/json/permission shape (no reshape)."""
    argv = inject_isolation([
        "claude", "-p", "PROMPT",
        "--model", "sonnet",
        "--output-format", "json",
        "--permission-mode", "bypassPermissions",
    ])
    _assert_argv_isolated(argv)
    # Caller shape preserved (no reshape to the interactive argv).
    assert "-p" in argv
    assert "--permission-mode" in argv and "bypassPermissions" in argv
    assert "--output-format" in argv and "json" in argv


def test_AC_PROMO_2_isolated_claude_argv_alias_equivalent() -> None:
    """The outcome-named `isolated_claude_argv` handle yields the same
    isolated argv as `inject_isolation` (one mechanism, two handles)."""
    raw = ["claude", "-p", "X", "--model", "sonnet"]
    assert isolated_claude_argv(list(raw)) == inject_isolation(
        list(raw)
    )


def test_AC_PROMO_2_env_scrubs_token_api_key_sets_persona() -> None:
    """The shared-surface env scrubs the operator bot-token spellings
    + any API key AND sets CLAUDE_PERSONA (the independent
    belt-and-braces defense)."""
    base = {
        "PATH": "/usr/bin",
        "HOME": str(Path.home()),
        "TELEGRAM_BOT_TOKEN": "operator-secret",
        "CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN": "operator-secret-2",
        "ANTHROPIC_API_KEY": "must-not-leak",
    }
    env = isolated_env(base)
    assert "TELEGRAM_BOT_TOKEN" not in env
    assert "CLAUDE_PLUGIN_TELEGRAM_BOT_TOKEN" not in env
    assert "ANTHROPIC_API_KEY" not in env
    # The independent defense the promote adds (would alone have
    # prevented #5 — the reharden judge inherited an env with no
    # CLAUDE_PERSONA).
    assert env["CLAUDE_PERSONA"] == ISOLATED_PERSONA_VALUE
    # Non-kill-vector env survives (real binary needs PATH/HOME +
    # keychain credential).
    assert env["PATH"] == "/usr/bin"
    assert env["HOME"] == str(Path.home())


def test_AC_PROMO_2_env_does_not_relocate_config_dir() -> None:
    """`feedback_no_anthropic_api_key`: the shared isolation does NOT
    relocate CLAUDE_CONFIG_DIR (a relocated virgin root reports `Not
    logged in` with no API key). Operator-protection does not depend
    on it — the empty-MCP/marker/env-scrub exclusion is the
    necessary-and-sufficient kill-vector isolation."""
    env = isolated_env({"PATH": "/usr/bin"})
    assert "CLAUDE_CONFIG_DIR" not in env, (
        "the shared isolation must NOT relocate CLAUDE_CONFIG_DIR or "
        "subscription auth breaks (no API key)"
    )
