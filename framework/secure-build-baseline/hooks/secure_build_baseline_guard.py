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

"""Secure-build baseline PreToolUse gate (AC.SBB.2 / .3 / .4).

The always-on build floor for the artifact loam PRODUCES. On a Bash
command it enforces two boundary guarantees over the repository the
command targets (``cwd``):

* **artifact-cleanliness** (AC.SBB.3) — a broad-stage command
  (``git add -A`` / ``.`` / ``git commit -a``) is checked for harness
  runtime state / secret files that are present and NOT git-ignored (would
  enter the artifact). Block (default) or surface, per strictness.
* **dependency-hygiene** (AC.SBB.2) — a build / publish command in a
  supported ecosystem (Node/Next, Python) runs the ecosystem audit; a vuln
  at or above the severity floor blocks-or-surfaces; a clean audit passes
  silently; an unavailable audit tool is surfaced honestly (never faked).

The third guarantee — secrets-never-committed (AC.SBB.1) — is enforced in
the safety-layer's ``secret_pattern_guard`` staged-diff extension and is a
NON-tunable floor (AC.SBB.4); this hook does not duplicate it.

Fault policy: ADVISORY-style fail-soft. A fault in the gate's OWN
evaluation (corrupt config, git read error) exits 0 without blocking — the
floor must not turn its own bug into a wall in front of every build. The
guarantees are on by DEFAULT; only their strictness (block vs surface) is
tunable, and the secret floor is not among the tunables (AC.SBB.4). The
floor is disable-friction'd, not absolutely undisable-able: a deliberate
``LOAM_SAFETY_HOOKS=off`` / ``LOAM_SECURE_BUILD=off`` env act (logged)
turns it off; TRUE non-disable is the Claude Code managed-settings path.

Stdlib + the component's ``loam.secure_build_baseline`` package; registered
via ``hooks/settings.fragment.json``.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Make the component's ``src`` importable when the hook runs as a bare
# script (the settings fragment invokes it by absolute path).
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from loam.secure_build_baseline.artifact_sweep import (  # noqa: E402
    is_broad_stage_command,
    offending_paths,
)
from loam.secure_build_baseline.dependency_audit import (  # noqa: E402
    detect_ecosystems,
    run_ecosystem_audit,
)
from loam.secure_build_baseline.deny_message import (  # noqa: E402
    artifact_cleanliness_reason,
    dependency_audit_reason,
    dependency_audit_unavailable_reason,
)
from loam.secure_build_baseline.strictness import (  # noqa: E402
    Strictness,
    load_secure_build_config,
    resolve_strictness,
)


SAFETY_HOOKS_LOG_RELATIVE = (".loam", "safety-hooks.log")
ENV_TOGGLE_ALL = "LOAM_SAFETY_HOOKS"
ENV_TOGGLE_THIS = "LOAM_SECURE_BUILD"
TOGGLE_OFF_VALUES: frozenset[str] = frozenset({"off", "0", "false", "no"})

_BASH_TOOL = "Bash"

# Build / publish command shapes that arm the dependency-hygiene audit.
_BUILD_MARKERS: tuple[str, ...] = (
    "npm run build",
    "npm publish",
    "npm ci",
    "yarn build",
    "pnpm build",
    "next build",
    "vite build",
    "python -m build",
    "python setup.py",
    "pip install -e",
    "poetry build",
    "poetry publish",
)


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


def _emit_deny(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.flush()


def _is_build_command(command: str) -> bool:
    return any(marker in command for marker in _BUILD_MARKERS)


def _evaluate_artifact_cleanliness(
    workspace_root: Path, command: str, config: dict[str, Any] | None
) -> tuple[bool, str] | None:
    """Return ``(should_block, reason)`` when the broad-stage sweep finds
    offending paths, else ``None``. ``should_block`` reflects strictness."""
    if not is_broad_stage_command(command):
        return None
    offending = offending_paths(workspace_root)
    if not offending:
        return None
    strictness = resolve_strictness("artifact-cleanliness", config)
    blocking = strictness is Strictness.BLOCK
    reason = artifact_cleanliness_reason(offending, blocking=blocking)
    return blocking, reason


def _evaluate_dependency_hygiene(
    workspace_root: Path, command: str, config: dict[str, Any] | None
) -> tuple[bool, str] | None:
    """Return ``(should_block, reason)`` when a build command's audit finds
    a vuln at/above floor OR the audit tool is unavailable (surfaced), else
    ``None`` (clean audit passes silently)."""
    if not _is_build_command(command):
        return None
    ecosystems = detect_ecosystems(workspace_root)
    if not ecosystems:
        return None
    strictness = resolve_strictness("dependency-audit", config)
    blocking = strictness is Strictness.BLOCK
    for eco in ecosystems:
        result = run_ecosystem_audit(workspace_root, eco)
        if result.must_surface_unavailable:
            # Honest surface — never silently report clean. Surface is
            # non-blocking (the tool's absence is the operator's to fix),
            # but it is logged + reported as an ``ask`` would be loud; we
            # keep it non-blocking and let it fall through (logged below).
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "secure_build_baseline_guard",
                    "decision": "surface-audit-unavailable",
                    "ecosystem": eco,
                    "detail": result.parse_error,
                },
            )
            continue
        if result.findings_at_or_above_floor:
            reason = dependency_audit_reason(
                eco,
                list(result.findings_at_or_above_floor),
                result.floor,
                blocking=blocking,
            )
            return blocking, reason
    return None


def main(argv: list[str] | None = None) -> int:
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-soft on stdin
        return 0
    if not raw.strip():
        return 0

    workspace_root: Path | None = None
    command: str = ""
    try:
        envelope = json.loads(raw)
        if not isinstance(envelope, dict):
            return 0
        cwd = envelope.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            return 0
        workspace_root = Path(cwd)

        tool_name = envelope.get("tool_name")
        tool_input = envelope.get("tool_input")
        if tool_name != _BASH_TOOL or not isinstance(tool_input, dict):
            return 0
        cmd = tool_input.get("command")
        if not isinstance(cmd, str) or not cmd:
            return 0
        command = cmd

        env = dict(os.environ)
        if _is_toggled_off(env):
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "secure_build_baseline_guard",
                    "decision": "toggled-off",
                    "tool": tool_name,
                },
            )
            return 0
    except Exception:  # noqa: BLE001 — malformed envelope, no target context
        return 0

    # Fail-soft on the gate's OWN evaluation error (config / git fault):
    # the floor must not turn its own bug into a wall in front of a build.
    try:
        config = load_secure_build_config(workspace_root)
    except Exception as exc:  # noqa: BLE001 — broken tuning file => default
        _append_log(
            workspace_root,
            {
                "ts": _now_iso(),
                "hook": "secure_build_baseline_guard",
                "decision": "config-fault-default-strictness",
                "exception": f"{type(exc).__name__}: {exc!s}",
            },
        )
        config = None

    try:
        # AC.SBB.3 — artifact-cleanliness sweep at the broad-stage boundary.
        verdict = _evaluate_artifact_cleanliness(workspace_root, command, config)
        if verdict is not None:
            blocking, reason = verdict
            if blocking:
                _emit_deny(reason)
                _append_log(
                    workspace_root,
                    {
                        "ts": _now_iso(),
                        "hook": "secure_build_baseline_guard",
                        "decision": "deny",
                        "guarantee": "artifact-cleanliness",
                    },
                )
                return 0
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "secure_build_baseline_guard",
                    "decision": "surface",
                    "guarantee": "artifact-cleanliness",
                },
            )

        # AC.SBB.2 — dependency-hygiene audit at the build boundary.
        verdict = _evaluate_dependency_hygiene(workspace_root, command, config)
        if verdict is not None:
            blocking, reason = verdict
            if blocking:
                _emit_deny(reason)
                _append_log(
                    workspace_root,
                    {
                        "ts": _now_iso(),
                        "hook": "secure_build_baseline_guard",
                        "decision": "deny",
                        "guarantee": "dependency-audit",
                    },
                )
                return 0
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "secure_build_baseline_guard",
                    "decision": "surface",
                    "guarantee": "dependency-audit",
                },
            )
    except Exception as exc:  # noqa: BLE001 — fail-soft on gate fault
        _append_log(
            workspace_root,
            {
                "ts": _now_iso(),
                "hook": "secure_build_baseline_guard",
                "decision": "fail-soft-on-fault",
                "exception": f"{type(exc).__name__}: {exc!s}",
            },
        )
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
