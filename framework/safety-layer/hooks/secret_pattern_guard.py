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

"""Secret-pattern PreToolUse gate (AC.SECHK.1 + AC.SECHK.B2-MIGRATION-*).

Two pattern families compose:

* **CONTENT patterns** (14-pattern ECC floor + workspace-additions).
  Match against:
    - Bash command argument strings (``tool_input.command``);
    - Edit/Write/MultiEdit content fields
      (``tool_input.content`` / ``tool_input.new_string`` /
       ``tool_input.edits[*].new_string``).
* **FILE patterns** (B2 surface migrated from
  ``plugins/dev-sdlc/hooks/bash_guard.py`` per D-SECHK.OVERLAP
  partial-absorb). Match against Bash commands that stage / commit /
  stash secret-class files (``.env``, ``*.pem``, ``id_rsa``, etc.).

Fires regardless of workspace mode (UNIVERSAL). Per
``feedback_no_amend_in_agent_dispatches`` / D-SECHK.FAIL-OPEN:

* On internal exception (regex fault, malformed envelope) → exit 0
  with empty stdout (default-allow) AND append an NDJSON failure-log
  line to ``<workspace>/.loam/safety-hooks.log``.
* Toggle-off env vars: ``LOAM_SAFETY_HOOKS=off`` (all three hooks)
  OR ``LOAM_SAFETY_HOOKS_SECRET=off`` (this hook only). When off,
  the hook records a no-op log line and exits 0 without pattern
  matching.

Diagnostic shape: Claude Code ``hookSpecificOutput`` envelope per
``feedback_translate_outbound_too`` discipline (persona translates).

Stdlib only: json, os, re, sys, pathlib.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any


# Ensure the sibling helper module resolves when the hook is invoked
# as a standalone script (Claude Code spawns it as ``python <path>``).
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _secret_patterns import (  # noqa: E402
    all_content_patterns,
    is_secret_file_commit,
)


SAFETY_HOOKS_LOG_RELATIVE = (".loam", "safety-hooks.log")
ENV_TOGGLE_ALL = "LOAM_SAFETY_HOOKS"
ENV_TOGGLE_THIS = "LOAM_SAFETY_HOOKS_SECRET"
TOGGLE_OFF_VALUES: frozenset[str] = frozenset({"off", "0", "false", "no"})

CONTENT_TOOLS: frozenset[str] = frozenset(
    {"Bash", "Edit", "Write", "MultiEdit"}
)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _log_path(workspace_root: Path) -> Path:
    return workspace_root.joinpath(*SAFETY_HOOKS_LOG_RELATIVE)


def _append_log(workspace_root: Path, payload: dict[str, Any]) -> None:
    """Append one NDJSON line to the safety-hooks log. Fail-soft."""
    try:
        target = _log_path(workspace_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
        with open(target, "a", encoding="utf-8") as fh:
            fh.write(line)
    except Exception:  # noqa: BLE001 — fail-soft on log write
        return


def _is_toggled_off(env: dict[str, str]) -> bool:
    """True iff either toggle (all-hooks or this-hook) is off-valued."""
    all_val = env.get(ENV_TOGGLE_ALL, "").strip().lower()
    this_val = env.get(ENV_TOGGLE_THIS, "").strip().lower()
    return all_val in TOGGLE_OFF_VALUES or this_val in TOGGLE_OFF_VALUES


def _emit_deny(reason: str, *, pattern_name: str) -> None:
    """Emit the Claude Code deny envelope; flush stdout."""
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))
    sys.stdout.flush()


def _extract_content_haystack(
    tool_name: str, tool_input: dict[str, Any]
) -> str:
    """Collect every string field where CONTENT-class secrets could
    appear, joined with newlines. Empty string when the tool has no
    relevant fields. Conservative: includes more fields than strictly
    necessary so a future Edit-tool field rename doesn't silently
    bypass detection.
    """
    parts: list[str] = []
    if tool_name == "Bash":
        cmd = tool_input.get("command")
        if isinstance(cmd, str):
            parts.append(cmd)
    if tool_name in ("Write", "Edit"):
        for key in ("content", "new_string", "old_string"):
            val = tool_input.get(key)
            if isinstance(val, str):
                parts.append(val)
    if tool_name == "MultiEdit":
        edits = tool_input.get("edits")
        if isinstance(edits, list):
            for e in edits:
                if not isinstance(e, dict):
                    continue
                for key in ("new_string", "old_string"):
                    val = e.get(key)
                    if isinstance(val, str):
                        parts.append(val)
    return "\n".join(parts)


def _check_content_patterns(
    workspace_root: Path,
    haystack: str,
) -> tuple[bool, str, str]:
    """Scan ``haystack`` for any floor-or-additive CONTENT pattern.

    Returns ``(matched, pattern_name, matched_text)``.
    """
    if not haystack:
        return (False, "", "")
    for pat in all_content_patterns(workspace_root):
        m = pat.regex.search(haystack)
        if m is not None:
            return (True, pat.name, m.group(0))
    return (False, "", "")


def _reason_content(pattern_name: str, matched_text: str) -> str:
    redacted = (
        matched_text[:6] + "..." + matched_text[-4:]
        if len(matched_text) > 16
        else matched_text[:4] + "..."
    )
    return (
        f"AC.SECHK.1 (secret-content, UNIVERSAL) — refused: input "
        f"matches pattern `{pattern_name}` (token redacted: "
        f"`{redacted}`). The safety-layer secret-pattern hook denies "
        f"writes / commands containing high-entropy credential token "
        f"shapes. Repair directions: (a) remove the credential from "
        f"the input; (b) source it from an env var / secret-store at "
        f"runtime rather than embedding the literal; (c) if the match "
        f"is a false positive, add the literal to "
        f"`<workspace>/.loam/secret-patterns.yaml` is NOT the right "
        f"escape — that file is additive only. Set "
        f"`LOAM_SAFETY_HOOKS_SECRET=off` for the session to bypass "
        f"this hook (the toggle is logged to "
        f"`<workspace>/.loam/safety-hooks.log`)."
    )


def _reason_file(matched_paths: list[str]) -> str:
    paths_text = ", ".join(f"`{p}`" for p in matched_paths) or "(unnamed)"
    return (
        f"AC.SECHK.B2-MIGRATION (secret-file, UNIVERSAL) — refused: "
        f"the command stages / commits secret-class file(s): "
        f"{paths_text}. Pattern matched: `.env` / `*.pem` / `*.key` / "
        f"`id_rsa` / `credentials.json` / `.aws/credentials` / "
        f"`.npmrc` / `.pypirc` family. Repair directions: (a) rename "
        f"to `.env-example` / `.env.sample` if this is documentation; "
        f"(b) add the file to `.gitignore` and un-stage it; (c) halt "
        f"and surface to the operator if a genuine credential file "
        f"is being committed by mistake. This detection migrated from "
        f"plugins/dev-sdlc/hooks/bash_guard.py (D-SECHK.OVERLAP "
        f"partial-absorb); the env-var override "
        f"`POS_BASH_GUARD_ALLOW=1` from bash_guard does NOT bypass "
        f"this hook. Set `LOAM_SAFETY_HOOKS_SECRET=off` for the "
        f"session to bypass."
    )


def main(argv: list[str] | None = None) -> int:
    """Hook entry. Reads PreToolUse envelope from stdin; emits
    allow/deny; always exits 0 (fail-soft per A2/A3 convention)."""
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
        if not isinstance(tool_input, dict):
            return 0
        if tool_name not in CONTENT_TOOLS:
            return 0

        env = dict(os.environ)
        if _is_toggled_off(env):
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "secret_pattern_guard",
                    "decision": "toggled-off",
                    "tool": tool_name,
                },
            )
            return 0

        # ---- FILE patterns (B2 migration) — Bash only.
        if tool_name == "Bash":
            cmd = tool_input.get("command")
            if isinstance(cmd, str):
                matched_files, paths = is_secret_file_commit(cmd)
                if matched_files:
                    reason = _reason_file(paths)
                    _emit_deny(reason, pattern_name="secret-file")
                    _append_log(
                        workspace_root,
                        {
                            "ts": _now_iso(),
                            "hook": "secret_pattern_guard",
                            "decision": "deny",
                            "class": "secret-file",
                            "tool": tool_name,
                            "matched": ", ".join(paths),
                        },
                    )
                    return 0

        # ---- CONTENT patterns (the 14-pattern floor + additions).
        haystack = _extract_content_haystack(tool_name, tool_input)
        matched, pattern_name, matched_text = _check_content_patterns(
            workspace_root, haystack
        )
        if matched:
            reason = _reason_content(pattern_name, matched_text)
            _emit_deny(reason, pattern_name=pattern_name)
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "secret_pattern_guard",
                    "decision": "deny",
                    "class": "secret-content",
                    "tool": tool_name,
                    "pattern": pattern_name,
                },
            )
            return 0

        return 0
    except Exception as exc:  # noqa: BLE001 — fail-OPEN per D-SECHK.FAIL-OPEN
        if workspace_root is not None:
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "secret_pattern_guard",
                    "decision": "fail-open",
                    "exception": f"{type(exc).__name__}: {exc!s}",
                },
            )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
