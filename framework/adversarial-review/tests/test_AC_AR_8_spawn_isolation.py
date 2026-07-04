# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.8 (P9) — every critic/judge/validator spawn routes through the sealed
spawn_isolated_claude surface; a hand-rolled bare `claude` argv is refused."""
from __future__ import annotations

import pytest

from adversarial_review import spawn


def test_AC_AR_8_isolated_argv_carries_isolation_flags():
    argv = spawn.isolated_argv("hello", model="sonnet")
    assert "--strict-mcp-config" in argv
    assert "--mcp-config" in argv
    # The prompt shape is preserved.
    assert "-p" in argv


def test_AC_AR_8_bare_claude_argv_is_refused():
    with pytest.raises(ValueError):
        spawn.assert_isolated(["claude", "-p", "hello"])


def test_AC_AR_8_isolated_argv_roundtrips_through_the_sealed_guard():
    # AC.AR.8's own contract: an argv built by this package's spawn module
    # satisfies the guard (it routed through the sealed isolation). The
    # telegram-marker kill-vector refusal is the sealed surface's OWN tested
    # contract (AC.PROMO.4) and is not re-asserted here.
    argv = spawn.isolated_argv("review this artifact", model="sonnet")
    spawn.assert_isolated(argv)  # no raise — the round-trip holds
    if spawn.SPAWN_AVAILABLE:
        # When sealed, the empty-MCP path (not a telegram marker) is present.
        assert any("empty" in a or ".mcp.json" in a for a in argv)


def test_AC_AR_8_non_claude_argv_passes_untouched():
    # The guard is a claude-spawn sentinel, not a blanket reject.
    spawn.assert_isolated(["python", "-c", "print(1)"])  # no raise
