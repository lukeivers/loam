#!/usr/bin/env python3
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

"""Deploy-safety FLOOR PreToolUse gate (AC.DSF.2/.3/.4/.6/.7).

The always-on framework-native gate that reads the per-environment config +
attestation contract and refuses, by default, a destructive action against a
production-class target that has no fresh attestation — and refuses a
production connection string written into a non-production config file.

Fail-policy: this is a FLOOR gate, NOT an advisory guard. It DECLARES
``FAIL_POLICY = FailPolicy.FAIL_CLOSED`` and routes its on-fault decision
through the shared per-gate fail-policy primitive
(``framework/safety-layer/hooks/_fail_policy.py``, AC.DSF.5/AC.DSF.8) — the
single source of fail-closed behaviour, no local ad-hoc enactment. When its
own evaluation of a destructive-candidate raises (e.g. a corrupt attestations
file), it fails CLOSED — it denies, because it could not prove the action
safe (AC.DSF.7). This inverts the advisory ``D-SECHK.FAIL-OPEN`` convention
for the destructive-floor path only; a non-candidate (a read, a
non-destructive command) is unaffected and the hook exits 0.

Disable-friction (plan Decision E): the floor is on by default and is
non-TRIVIALLY-disable-able — turning it off requires a deliberate
``LOAM_SAFETY_HOOKS=off`` / ``LOAM_DEPLOY_SAFETY_FLOOR=off`` env act (logged),
or removing the hook from settings. TRUE non-disable is the Claude Code
managed-settings / admin-policy path, named as the hard-non-disable upgrade.

Stdlib + the component's own ``loam.deploy_safety_floor`` package. Registered
via ``hooks/settings.fragment.json``.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Make the component's ``src`` importable when the hook runs as a bare script
# (the settings fragment invokes it by absolute path, not as an installed
# module). Mirrors the conftest self-contained-import pattern.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from loam.deploy_safety_floor.classifier import classify_destructive  # noqa: E402
from loam.deploy_safety_floor.config import load_deploy_config  # noqa: E402
from loam.deploy_safety_floor.attestation import load_attestations  # noqa: E402
from loam.deploy_safety_floor.deny_message import (  # noqa: E402
    PRODUCTION_TARGET_PHRASE,
    destructive_fail_closed_message,
)
from loam.deploy_safety_floor.gate import (  # noqa: E402
    Decision,
    evaluate_bash,
    evaluate_write,
    _is_local_config_file,
)

# Make the sibling safety-layer fail-policy primitive importable when the hook
# runs as a bare script. The floor gate ADOPTS the shared per-gate fail-policy
# field (AC.DSF.8) as its single source of fail-closed behaviour rather than a
# local ad-hoc enactment. Stdlib-only sibling module — does NOT pull the
# loam.safety_layer package at hook runtime. The safety-layer tree ships
# alongside this component as one framework unit.
_FAIL_POLICY_HOOKS = (
    Path(__file__).resolve().parent.parent.parent / "safety-layer" / "hooks"
)
if str(_FAIL_POLICY_HOOKS) not in sys.path:
    sys.path.insert(0, str(_FAIL_POLICY_HOOKS))

from _fail_policy import (  # noqa: E402
    FailPolicy,
    apply_fault_policy,
    emit_deny,
)

# Declared per-gate fail-policy (AC.DSF.8 / AC.DSF.5): this is a FLOOR gate —
# it fails CLOSED on its own internal fault against a destructive candidate (a
# non-candidate still fails open, in read-parity). Sourced from the shared
# safety-layer primitive; there is no local fail-closed enactment.
FAIL_POLICY = FailPolicy.FAIL_CLOSED


SAFETY_HOOKS_LOG_RELATIVE = (".loam", "safety-hooks.log")
ENV_TOGGLE_ALL = "LOAM_SAFETY_HOOKS"
ENV_TOGGLE_THIS = "LOAM_DEPLOY_SAFETY_FLOOR"
TOGGLE_OFF_VALUES: frozenset[str] = frozenset({"off", "0", "false", "no"})

_BASH_TOOL = "Bash"
_WRITE_TOOLS: frozenset[str] = frozenset({"Write", "Edit", "MultiEdit"})


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append_log(workspace_root: Path, payload: dict[str, Any]) -> None:
    try:
        target = workspace_root.joinpath(*SAFETY_HOOKS_LOG_RELATIVE)
        target.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:  # noqa: BLE001 — fail-soft on log write
        return


def _is_toggled_off(env: dict[str, str]) -> bool:
    all_val = env.get(ENV_TOGGLE_ALL, "").strip().lower()
    this_val = env.get(ENV_TOGGLE_THIS, "").strip().lower()
    return all_val in TOGGLE_OFF_VALUES or this_val in TOGGLE_OFF_VALUES


def _write_content(tool_input: dict[str, Any]) -> str:
    """Best-effort extraction of the text a Write/Edit/MultiEdit would land.

    Write carries ``content``; Edit carries ``new_string``; MultiEdit carries
    ``edits: [{new_string: ...}]``. Concatenated so a production identity in
    any landed text is seen."""
    parts: list[str] = []
    content = tool_input.get("content")
    if isinstance(content, str):
        parts.append(content)
    new_string = tool_input.get("new_string")
    if isinstance(new_string, str):
        parts.append(new_string)
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        for e in edits:
            if isinstance(e, dict) and isinstance(e.get("new_string"), str):
                parts.append(e["new_string"])
    return "\n".join(parts)


def _evaluate(
    tool_name: str, tool_input: dict[str, Any], workspace_root: Path
) -> Decision:
    """Run the floor evaluation. May RAISE on a malformed config /
    attestations file — the caller turns a raise into a fail-CLOSED deny for
    a destructive candidate (AC.DSF.7)."""
    config = load_deploy_config(workspace_root)
    if config is None or not config.environments:
        # No declared environments — the floor is inert (nothing to gate).
        return Decision(action="allow", reason="")

    if tool_name == _BASH_TOOL:
        command = tool_input.get("command")
        if not isinstance(command, str) or not command:
            return Decision(action="allow", reason="")
        attestations = load_attestations(workspace_root)
        now = datetime.now(timezone.utc)
        return evaluate_bash(command, config, attestations, now)

    if tool_name in _WRITE_TOOLS:
        file_path = tool_input.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            return Decision(action="allow", reason="")
        return evaluate_write(file_path, _write_content(tool_input), config)

    return Decision(action="allow", reason="")


def _floor_should_fail_closed(
    tool_name: str, tool_input: dict[str, Any]
) -> bool:
    """True iff a raised evaluation is a FLOOR destructive-candidate that must
    fail CLOSED rather than open (AC.DSF.7).

    A destructive Bash command, or a Write to a non-production config file, is
    a candidate the floor must not let through when it could not prove safety.
    A read or a non-destructive command is NOT a candidate (it fails open, in
    parity with the advisory convention)."""
    if tool_name == _BASH_TOOL:
        command = tool_input.get("command")
        if isinstance(command, str) and command:
            try:
                return classify_destructive(command).is_destructive
            except Exception:  # noqa: BLE001 — classifier itself errored
                # Could not even classify a Bash command while evaluating a
                # destructive-floor context — fail CLOSED (cannot prove safe).
                return True
    if tool_name in _WRITE_TOOLS:
        file_path = tool_input.get("file_path")
        if isinstance(file_path, str):
            return _is_local_config_file(file_path)
    return False


def main(argv: list[str] | None = None) -> int:
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-soft on stdin
        return 0
    if not raw.strip():
        return 0

    workspace_root: Path | None = None
    tool_name: str = ""
    tool_input: dict[str, Any] = {}
    try:
        envelope = json.loads(raw)
        if not isinstance(envelope, dict):
            return 0
        cwd = envelope.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            return 0
        workspace_root = Path(cwd)

        tn = envelope.get("tool_name")
        ti = envelope.get("tool_input")
        if not isinstance(tn, str):
            return 0
        if tn != _BASH_TOOL and tn not in _WRITE_TOOLS:
            return 0
        if not isinstance(ti, dict):
            return 0
        tool_name, tool_input = tn, ti

        env = dict(os.environ)
        if _is_toggled_off(env):
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "deploy_safety_floor_guard",
                    "decision": "toggled-off",
                    "tool": tool_name,
                },
            )
            return 0
    except Exception:  # noqa: BLE001 — malformed envelope, no target context
        return 0

    # Floor evaluation, fail-CLOSED on a raised destructive-candidate — the
    # decision is resolved and enacted by the shared fail-policy primitive
    # (AC.DSF.8): a destructive candidate denies, a non-candidate fails open.
    try:
        decision = _evaluate(tool_name, tool_input, workspace_root)
    except Exception as exc:  # noqa: BLE001 — the floor's own check errored
        fault = apply_fault_policy(
            FAIL_POLICY,
            is_destructive_candidate=_floor_should_fail_closed(
                tool_name, tool_input
            ),
            deny_reason=destructive_fail_closed_message(
                target_phrase=PRODUCTION_TARGET_PHRASE
            ),
        )
        _append_log(
            workspace_root,
            {
                "ts": _now_iso(),
                "hook": "deploy_safety_floor_guard",
                "decision": fault.label,
                "tool": tool_name,
                "exception": f"{type(exc).__name__}: {exc!s}",
            },
        )
        return 0

    if decision.denied:
        emit_deny(decision.reason)
        _append_log(
            workspace_root,
            {
                "ts": _now_iso(),
                "hook": "deploy_safety_floor_guard",
                "decision": "deny",
                "tool": tool_name,
                "sub_action": decision.sub_action,
            },
        )
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
