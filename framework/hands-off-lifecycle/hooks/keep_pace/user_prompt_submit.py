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

"""UserPromptSubmit CLI entry for the keep-pace hook chain (KP0).

Reads the Claude Code UserPromptSubmit JSON envelope from stdin, runs the
fail-open chain, and emits the merged additionalContext (silent on
no-contributor / no-match).

LIVE WIRING (activation cycle): ``contributors()`` registers the two
staged UserPromptSubmit contributors the prior cycles built but left
out of their fences (the registration each cycle deferred to activation,
per D-KP0.1 / D-KP1.1 / D-KP7.1, RF-6):

  1. KP1 work-anchored retrieval — ``build_keep_pace_contributor()``
     (``loam.primary_persona.keep_pace.retrieval``; AC.KP1.* — the
     per-prompt corpus pointer injection).
  2. KP7 SessionStart re-assert — ``reassert_surface_for_user_prompt_submit()``
     (``framework/orchestrator/scripts/session_surface.py``; AC.KP7.2 —
     the #15174 SessionStart-compact mitigation, re-emitted on the first
     UserPromptSubmit after a compaction).

Both live in OTHER components, so each is reached via a BEST-EFFORT
lazy import wrapped fail-soft (the same discipline KP7's own
cross-component reads use): a contributor whose import fails degrades
to "no injection" and the turn proceeds. Composed with the chain's
fail-open-whole-chain guarantee (AC.KP0.4), a raising / slow / absent
contributor still lets the turn proceed.

Exits 0 on every path (fail-open-whole-chain — AC.KP0.4). Stdlib-only
at the substrate; the lazy imports reach loam source packages.
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
    emit_user_prompt_submit,
    run_chain,
)


def _loam_root() -> Path:
    """Repo root from this hook script.

    ``framework/hands-off-lifecycle/hooks/keep_pace/user_prompt_submit.py``
    → parents[4] is the loam repo root.
    """
    return Path(__file__).resolve().parents[4]


def _kp1_retrieval_contributor(envelope: dict):
    """Best-effort KP1 work-anchored retrieval contributor (AC.KP1.*).

    Lazy-imports ``build_keep_pace_contributor`` from the primary-persona
    component and delegates to it (its returned callable already resolves
    a live config from the envelope per turn and is fail-soft internally).
    Any import / runtime failure → ``None`` (no injection); composed with
    the chain's fail-open guarantee the turn always proceeds.
    """
    try:
        pkg = _loam_root() / "framework" / "primary-persona" / "src"
        if pkg.is_dir() and str(pkg) not in sys.path:
            sys.path.insert(0, str(pkg))
        from loam.primary_persona.keep_pace.retrieval import (  # type: ignore[import-not-found]
            build_keep_pace_contributor,
        )

        return build_keep_pace_contributor()(envelope)
    except BaseException:  # noqa: BLE001 — fail-soft; chain fail-open
        return None


def _kp7_reassert_contributor(envelope: dict):
    """Best-effort KP7 SessionStart re-assert contributor (AC.KP7.2).

    Lazy-imports ``reassert_surface_for_user_prompt_submit`` from the
    orchestrator component and adapts it to the chain's
    ``fn(envelope) -> Optional[str]`` contract: the orchestrator function
    takes no envelope (it reads the live objectives register, falling
    back to the in-source SEED), returning the same plain-language
    last-state surface the SessionStart step emits so a compaction can be
    repaired on the first prompt. Returns ``None`` on empty surface or any
    failure (no injection); composed with the chain's fail-open guarantee.
    """
    try:
        scripts = _loam_root() / "framework" / "orchestrator" / "scripts"
        if scripts.is_dir() and str(scripts) not in sys.path:
            sys.path.insert(0, str(scripts))
        from session_surface import (  # type: ignore[import-not-found]
            reassert_surface_for_user_prompt_submit,
        )

        surface = reassert_surface_for_user_prompt_submit()
        return surface or None
    except BaseException:  # noqa: BLE001 — fail-soft; chain fail-open
        return None


# LIVE WIRING: the two staged UserPromptSubmit contributors, registered
# in chain order (KP1 retrieval first, then the KP7 re-assert). Each is
# a best-effort lazy-import wrapper; the chain isolates every failure
# mode (raise / timeout / non-str) per AC.KP0.4 so a broken contributor
# never breaks the live session (AC.KP.S.1).
def contributors() -> list:
    return [
        Contributor("kp1-retrieval", _kp1_retrieval_contributor),
        Contributor("kp7-reassert", _kp7_reassert_contributor),
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
        result = run_chain(
            "UserPromptSubmit",
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
        emit_user_prompt_submit(result)
    except BaseException:  # noqa: BLE001 — the whole-chain guarantee
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
