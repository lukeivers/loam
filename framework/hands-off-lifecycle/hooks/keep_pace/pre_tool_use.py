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
exits 0 (allow the tool).

LIVE WIRING (activation cycle): ``contributors()`` registers the staged
KP9 draft-gate contributor the Cycle-3 build left out of its fence (the
registration deferred to activation, per D-KP0.1 / KP9 staging, RF-6):

  - KP9 abstraction-voice + constraint draft gate —
    ``build_draft_gate_contributor()``
    (``draft_gate`` in this same ``keep_pace`` hooks dir; AC.KP9.* — the
    Layer 1 jargon lint + Layer C constraint check that routes every
    outbound user-facing draft). On BLOCK / FLAG the contributor yields
    the MODEL-FACING report (AC.KP9.4), never a user-visible message; on
    PASS / no-draft it is silent.

The contributor is reached via a BEST-EFFORT import wrapped fail-soft
(uniform with the cross-component discipline KP7 uses): an import / run
failure degrades to "no gate" and the tool proceeds.

Critically (AC.KP0.4): this hook NEVER blocks a tool call by erroring.
On any internal failure it exits 0 (allow). A future gate contributor
that wants to BLOCK does so via the documented PreToolUse decision
envelope, but the chain substrate itself is allow-by-default fail-open so
a broken memory hook can never wedge the live session. Stdlib-only at the
substrate; the lazy import reaches the sibling draft_gate module.
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
    Contributor,
    DEFAULT_PER_HOOK_TIMEOUT_S,
    DEFAULT_PER_TURN_BUDGET_S,
    default_latency_log_path,
    run_chain,
)


def _kp9_draft_gate_contributor(envelope: dict):
    """Best-effort KP9 draft-gate contributor (AC.KP9.*).

    Imports ``build_draft_gate_contributor`` from the sibling
    ``draft_gate`` module (already on ``sys.path`` via ``_HOOKS_DIR``)
    and delegates to it. The returned callable extracts any outbound
    user-facing draft from the PreToolUse envelope, runs the gate, and
    returns the model-facing report on BLOCK / FLAG (AC.KP9.4) or
    ``None`` on PASS / no-draft. Any import / runtime failure → ``None``;
    composed with the chain's fail-open guarantee the tool always
    proceeds (AC.KP0.4 / AC.KP.S.1).
    """
    try:
        from draft_gate import (  # type: ignore[import-not-found]
            build_draft_gate_contributor,
        )

        return build_draft_gate_contributor()(envelope)
    except BaseException:  # noqa: BLE001 — fail-soft; chain fail-open
        return None


# LIVE WIRING: the staged KP9 draft-gate contributor, registered on the
# PreToolUse chain. The chain isolates every failure mode (raise /
# timeout / non-str) per AC.KP0.4 so a broken gate never wedges a tool
# call on the live session (AC.KP.S.1); the gate's own logic is
# additionally fail-open (AC.KP9.4).
def contributors() -> list:
    return [
        Contributor("kp9-draft-gate", _kp9_draft_gate_contributor),
    ]


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
