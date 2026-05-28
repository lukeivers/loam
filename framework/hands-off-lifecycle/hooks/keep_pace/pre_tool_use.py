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

"""PreToolUse CLI entry for the keep-pace hook chain (KP0).

Reads the Claude Code PreToolUse JSON envelope from stdin, runs the
fail-open chain (per-hook timeout + per-turn budget + latency log), and
exits 0 (allow the tool). KP0 ships with an EMPTY contributor list — the
KP9 draft-gate (Cycle 3) registers its contributor here.

Critically (AC.KP0.4): this hook NEVER blocks a tool call by erroring.
On any internal failure it exits 0 (allow). A future gate contributor
that wants to BLOCK does so via the documented PreToolUse decision
envelope, but the chain substrate itself is allow-by-default fail-open so
a broken memory hook can never wedge the live session. Stdlib-only.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from chain_runner import (  # noqa: E402
    DEFAULT_PER_HOOK_TIMEOUT_S,
    DEFAULT_PER_TURN_BUDGET_S,
    default_latency_log_path,
    run_chain,
)


# KP0: no contributors yet. KP9 (Cycle 3) registers the draft-gate
# contributor here.
def contributors() -> list:
    return []


def _float_env(name: str, default: float) -> float:
    try:
        v = os.environ.get(name)
        return float(v) if v else default
    except (TypeError, ValueError):
        return default


def main(argv: list | None = None) -> int:
    try:
        raw = sys.stdin.read()
    except BaseException:  # noqa: BLE001 — fail-open
        return 0
    envelope: dict = {}
    if raw and raw.strip():
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                envelope = parsed
        except BaseException:  # noqa: BLE001 — fail-open on bad input
            envelope = {}

    try:
        run_chain(
            "PreToolUse",
            envelope,
            contributors(),
            per_hook_timeout_s=_float_env(
                "KEEP_PACE_PER_HOOK_TIMEOUT_S", DEFAULT_PER_HOOK_TIMEOUT_S
            ),
            per_turn_budget_s=_float_env(
                "KEEP_PACE_PER_TURN_BUDGET_S", DEFAULT_PER_TURN_BUDGET_S
            ),
            latency_log_path=os.environ.get("KEEP_PACE_LATENCY_LOG")
            or default_latency_log_path(envelope),
        )
        # KP0 PreToolUse is non-blocking: emit nothing, allow the tool.
    except BaseException:  # noqa: BLE001 — the whole-chain guarantee
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
