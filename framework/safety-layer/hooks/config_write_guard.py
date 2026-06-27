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

"""Config-write PreToolUse gate (AC.SECHK.3).

Blocks Edit / Write / MultiEdit operations against config files that
are typically modified by build / lint / dev-tool harnesses but
should not be edited by an AI agent without explicit operator
intervention:

* ``.eslintrc`` (any extension — ``.eslintrc``, ``.eslintrc.json``,
  ``.eslintrc.js``, ``.eslintrc.yaml``, ``.eslintrc.cjs``)
* ``biome.json``
* ``.pre-commit-config.yaml`` / ``.pre-commit-config.yml``
* ``.git/config``
* ``.gitignore`` (top-level only — subdirectory ``.gitignore`` files
  are typically intentional)

Fires regardless of workspace mode (UNIVERSAL). Matcher: per
Claude Code convention, the hook is registered against
``Edit|Write|MultiEdit`` only; Bash ``git config`` commands do NOT
match (bash_guard already handles those).

Toggle off via ``LOAM_SAFETY_HOOKS=off`` or
``LOAM_SAFETY_HOOKS_CONFIG_WRITE=off``. Fail-open per
D-SECHK.FAIL-OPEN.

Stdlib only.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any


# Ensure the sibling fail-policy helper resolves when the hook runs as a
# standalone script. Stdlib-only sibling import — does NOT pull the
# loam.safety_layer package.
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _fail_policy import FailPolicy, apply_fault_policy  # noqa: E402

# Declared per-gate fail-policy (AC.DSF.5): ADVISORY guard — fails OPEN on
# its own internal fault (D-SECHK.FAIL-OPEN, unchanged).
FAIL_POLICY = FailPolicy.FAIL_OPEN


SAFETY_HOOKS_LOG_RELATIVE = (".loam", "safety-hooks.log")
ENV_TOGGLE_ALL = "LOAM_SAFETY_HOOKS"
ENV_TOGGLE_THIS = "LOAM_SAFETY_HOOKS_CONFIG_WRITE"
TOGGLE_OFF_VALUES: frozenset[str] = frozenset({"off", "0", "false", "no"})

CONTENT_TOOLS: frozenset[str] = frozenset({"Edit", "Write", "MultiEdit"})


# Protected-path matchers. Each entry: (compiled regex against the
# basename or trailing path segment, dispatch class).
_PROTECTED_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^\.eslintrc(?:\.[A-Za-z0-9]+)?$"), "eslintrc"),
    (re.compile(r"^biome\.json$"), "biome"),
    (re.compile(r"^\.pre-commit-config\.ya?ml$"), "pre-commit"),
)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _log_path(workspace_root: Path) -> Path:
    return workspace_root.joinpath(*SAFETY_HOOKS_LOG_RELATIVE)


def _append_log(workspace_root: Path, payload: dict[str, Any]) -> None:
    try:
        target = _log_path(workspace_root)
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


def _classify_path(
    file_path: str, workspace_root: Path
) -> tuple[bool, str, str]:
    """Classify a target path against the protected patterns.

    Returns ``(matched, class_label, matched_path_display)``.
    Handles ``.git/config`` (trailing-segment match) and top-level
    ``.gitignore`` (workspace-root-relative match) specially.
    """
    p = Path(file_path)
    name = p.name
    # `.git/config` — match trailing two segments.
    parts_tail = "/".join(p.parts[-2:]) if len(p.parts) >= 2 else ""
    if parts_tail == ".git/config" or file_path.endswith("/.git/config"):
        return (True, "git-config", file_path)
    # Top-level `.gitignore` — only the workspace-root one fires
    # (subdir .gitignore files are typically intentional).
    if name == ".gitignore":
        try:
            if p.is_absolute():
                resolved = p.resolve()
                ws = workspace_root.resolve()
                rel = resolved.relative_to(ws)
                if rel.as_posix() == ".gitignore":
                    return (True, "root-gitignore", file_path)
            else:
                # Relative path — treat as workspace-relative.
                if file_path.lstrip("./") == ".gitignore":
                    return (True, "root-gitignore", file_path)
        except (OSError, ValueError):
            # Resolution failure → conservative: do NOT fire (this
            # hook is restrictive enough that ambiguous matches
            # should not extend to gitignore).
            return (False, "", "")
    for pattern, class_label in _PROTECTED_PATTERNS:
        if pattern.match(name):
            return (True, class_label, file_path)
    return (False, "", "")


def _reason(class_label: str, matched_path: str) -> str:
    class_to_repair = {
        "eslintrc": (
            "edit ESLint config via the project's `eslint --init` "
            "flow or by hand in an editor — AI-driven edits to "
            "lint config drift fast"
        ),
        "biome": (
            "edit biome.json via `biome init` / `biome migrate` or "
            "by hand"
        ),
        "pre-commit": (
            "edit `.pre-commit-config.yaml` via the operator's "
            "preferred editor; AI-driven hook-config edits often "
            "silently bypass team conventions"
        ),
        "git-config": (
            "edit `.git/config` via `git config` invocations or by "
            "hand; AI-driven edits here can change remote URLs / "
            "hooks paths / user identity in non-obvious ways"
        ),
        "root-gitignore": (
            "edit the top-level `.gitignore` via a focused commit "
            "by the operator; AI-driven edits frequently miss "
            "entries the operator wants kept"
        ),
    }
    repair = class_to_repair.get(class_label, "halt and surface")
    return (
        f"AC.SECHK.3 (config-write, UNIVERSAL) — refused: write "
        f"target `{matched_path}` matches the protected config "
        f"class `{class_label}`. Repair direction: {repair}. Set "
        f"`LOAM_SAFETY_HOOKS_CONFIG_WRITE=off` for the session to "
        f"bypass this hook (the toggle is logged to "
        f"`<workspace>/.loam/safety-hooks.log`)."
    )


def main(argv: list[str] | None = None) -> int:
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-soft on stdin
        return 0
    if not raw.strip():
        return 0

    workspace_root: Path | None = None
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
        if not isinstance(tool_name, str):
            return 0
        if tool_name not in CONTENT_TOOLS:
            return 0
        if not isinstance(tool_input, dict):
            return 0
        file_path = tool_input.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            return 0

        env = dict(os.environ)
        if _is_toggled_off(env):
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "config_write_guard",
                    "decision": "toggled-off",
                    "tool": tool_name,
                },
            )
            return 0

        matched, class_label, matched_path = _classify_path(
            file_path, workspace_root
        )
        if matched:
            reason = _reason(class_label, matched_path)
            _emit_deny(reason)
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "config_write_guard",
                    "decision": "deny",
                    "class": class_label,
                    "tool": tool_name,
                    "file_path": file_path,
                },
            )
            return 0

        return 0
    except Exception as exc:  # noqa: BLE001 — declared fail-policy (D-SECHK.FAIL-OPEN)
        decision = apply_fault_policy(FAIL_POLICY)
        if workspace_root is not None:
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "config_write_guard",
                    "decision": decision.label,
                    "exception": f"{type(exc).__name__}: {exc!s}",
                },
            )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
