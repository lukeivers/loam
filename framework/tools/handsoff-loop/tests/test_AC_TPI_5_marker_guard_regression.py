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

"""AC.TPI.5 — a regression that re-introduces a telegram-reachable
argv at any §1b site fails loudly (raises) rather than silently
shipping a kill-capable invocation.

Plan: docs/plans/telegram-poller-isolation-fix.md
Contract: pos3/.../telegram-isolation-fix-plan-2026-05-16.md §3.3
Reuses the PROVEN subloam-driver marker-guard discipline
(`driver.py` `_TELEGRAM_PLUGIN_MARKERS` guard) at the §1b sites:
`inject_isolation` asserts the produced argv carries zero telegram
markers and raises ValueError otherwise.  Falsifiable: remove the
guard → a kill-capable argv ships green.  Durability — the fix cannot
silently regress (the asymmetry that caused this must not recur).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop._isolation import inject_isolation  # noqa: E402


def test_AC_TPI_5_telegram_marker_in_argv_raises() -> None:
    """If a regression re-introduces a telegram-plugin marker into a
    §1b argv, `inject_isolation` raises rather than silently shipping
    a kill-capable invocation."""
    with pytest.raises(ValueError, match="telegram marker"):
        inject_isolation([
            "claude", "-p", "PROMPT",
            "--plugin", "plugin:telegram",
            "--model", "sonnet",
        ])


def test_AC_TPI_5_official_telegram_plugin_spelling_raises() -> None:
    """The full official-plugin marker spelling is also guarded."""
    with pytest.raises(ValueError, match="telegram marker"):
        inject_isolation([
            "claude", "-p", "PROMPT",
            "--plugin", "telegram@claude-plugins-official",
        ])


def test_AC_TPI_5_clean_argv_does_not_raise() -> None:
    """The guard is a regression sentinel, not a blanket reject: a
    clean §1b argv passes and emerges isolated."""
    argv = inject_isolation([
        "claude", "-p", "PROMPT",
        "--model", "sonnet",
        "--output-format", "json",
        "--permission-mode", "bypassPermissions",
    ])
    assert "--strict-mcp-config" in argv
    joined = " ".join(argv)
    assert "plugin:telegram" not in joined
