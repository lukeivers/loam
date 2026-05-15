"""subloam-driver — isolated sub-loam test-instance driver.

Authored at the loam-init-persona-wiring-and-isolated-subloam-driver
MINOR (Part 2), 2026-05-15, per plan
`docs/plans/loam-init-persona-wiring-and-isolated-subloam-driver.md`.

The driver stands up a fresh persona-active loam workspace via the
production bootstrap path (`bootstrap_new_workspace`, made
persona-active by Part 1's first-run scaffold extension), then drives
an INTERACTIVE `claude` session inside it over a PTY harness under one
isolation mechanism. The single :class:`IsolationConfig` object drives
BOTH operator-protection (the operator's telegram/bun poller is never
SIGTERM'd) AND bench-validity (the measured behaviour is loam's, not
the operator's ambient plugins/channels) — AC.LIPW.6: they are the
same configuration, not two.

NO Anthropic API key: the driver spawns the real `claude` binary
(default Sonnet); every loam LLM call stays subscription-only.
"""

from __future__ import annotations

from .driver import (
    DriverResult,
    IsolationConfig,
    SubLoamDriver,
    build_isolated_claude_argv,
    build_isolated_env,
)

__all__ = [
    "DriverResult",
    "IsolationConfig",
    "SubLoamDriver",
    "build_isolated_claude_argv",
    "build_isolated_env",
]
