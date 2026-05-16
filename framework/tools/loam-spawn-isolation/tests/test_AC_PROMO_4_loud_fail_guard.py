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

"""AC.PROMO.4 — a loam-adjacent ``claude`` argv constructed WITHOUT
the shared isolation fails loudly (raises) rather than silently
shipping a kill-capable invocation.

Plan: docs/plans/telegram-5-fix.md §3.3
Reuses the PROVEN subloam-driver marker-guard discipline
(`driver.py` `_TELEGRAM_PLUGIN_MARKERS` guard / sealed
`_isolation._assert_telegram_free`) AND additionally asserts the
empty-strict-MCP isolation flag pair is present — so the EXACT #5
pattern (a hand-rolled raw `["claude","-p",...]` with no isolation)
raises rather than shipping green.  Falsifiable: remove the guard ->
a kill-capable argv ships green.  Durability — the asymmetry that
caused #1..#5 cannot silently recur.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from loam_spawn_isolation import (  # noqa: E402
    assert_loam_spawn_isolated,
    inject_isolation,
)


def test_AC_PROMO_4_raw_unisolated_claude_argv_raises() -> None:
    """THE #5 reproduction at the guard level: the exact hand-rolled
    raw argv the /tmp reharden harness used (no --strict-mcp-config,
    no --mcp-config, no isolation import) raises rather than silently
    shipping a kill-capable invocation."""
    with pytest.raises(ValueError, match="WITHOUT the shared isolation"):
        assert_loam_spawn_isolated([
            "claude", "-p", "PROMPT", "--model", "sonnet",
            "--output-format", "json",
            "--permission-mode", "bypassPermissions",
        ])


def test_AC_PROMO_4_telegram_marker_in_argv_raises() -> None:
    """A regression re-introducing a telegram-plugin marker raises
    (the sealed marker-guard discipline, reused verbatim)."""
    with pytest.raises(ValueError, match="telegram marker"):
        assert_loam_spawn_isolated([
            "claude", "-p", "PROMPT",
            "--plugin", "plugin:telegram",
            "--strict-mcp-config", "--mcp-config", "/tmp/empty.json",
        ])


def test_AC_PROMO_4_official_plugin_spelling_raises() -> None:
    """The full official-plugin marker spelling is also guarded."""
    with pytest.raises(ValueError, match="telegram marker"):
        assert_loam_spawn_isolated([
            "claude", "-p", "PROMPT",
            "--plugin", "telegram@claude-plugins-official",
            "--strict-mcp-config", "--mcp-config", "/tmp/e.json",
        ])


def test_AC_PROMO_4_isolated_argv_passes_guard() -> None:
    """An argv built via the shared surface passes the guard (the
    guard is a regression sentinel, not a blanket reject) — and
    `inject_isolation` itself routes through the guard before
    returning (a kill-capable result can never escape)."""
    isolated = inject_isolation([
        "claude", "-p", "PROMPT", "--model", "sonnet",
        "--output-format", "json",
        "--permission-mode", "bypassPermissions",
    ])
    # Does not raise.
    assert_loam_spawn_isolated(isolated)
    assert "--strict-mcp-config" in isolated
    assert "plugin:telegram" not in " ".join(isolated)


def test_AC_PROMO_4_non_claude_argv_not_over_reached() -> None:
    """The guard is a `claude`-spawn-isolation sentinel, not a blanket
    subprocess reject: a non-claude argv (e.g. git/pytest) is not a
    SIGTERM vector and passes untouched (no false positive that would
    push callers to disable the guard)."""
    assert_loam_spawn_isolated(["git", "status"])
    assert_loam_spawn_isolated(
        ["python", "-m", "pytest", "-q", "claude_thing"]
    )


def test_AC_PROMO_4_empty_argv_raises() -> None:
    """An empty argv is a programming error, not a silent pass."""
    with pytest.raises(ValueError, match="empty argv"):
        assert_loam_spawn_isolated([])
