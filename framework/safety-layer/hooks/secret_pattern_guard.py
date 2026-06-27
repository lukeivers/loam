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

"""Secret-pattern PreToolUse gate (AC.SECHK.1 + AC.SECHK.B2-MIGRATION-*
+ AC.SBB.1).

Three pattern families compose:

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
* **STAGED-DIFF patterns** (AC.SBB.1 — secure-build baseline, Sub-cycle
  C). A ``git commit`` / ``git push`` boundary command triggers a scan of
  the *staged diff* (commit) or the *unpushed commit range* (push) of the
  repository the command runs in (``cwd``) for the same CONTENT credential
  shapes. This catches a secret embedded in a file's CONTENT — not just a
  literal in the command string — at the commit/push boundary, and fires
  for the artifact loam BUILDS (any repo under ``cwd``), not only loam's
  own repository. The scanned content is read via ``git`` against ``cwd``;
  no secret value is ever echoed (the deny reason carries only a redacted
  token shape). This path is **strictly additive**: it adds a new branch
  on the Bash path and changes none of the existing CONTENT / FILE logic
  or the guard's fail-OPEN fault policy (the staged-diff read fails SOFT —
  any ``git`` error yields no match, so the inbound-paste path's
  ``D-SECHK.FAIL-OPEN`` behavior is preserved unchanged).

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
import re
import subprocess
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
from _fail_policy import FailPolicy, apply_fault_policy  # noqa: E402

# Declared per-gate fail-policy (AC.DSF.5): ADVISORY guard — fails OPEN on
# its own internal fault (D-SECHK.FAIL-OPEN, unchanged).
FAIL_POLICY = FailPolicy.FAIL_OPEN


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


# ---- STAGED-DIFF boundary scan (AC.SBB.1, secure-build baseline).
# A commit / push boundary command triggers a scan of the repo's staged
# diff (commit) or unpushed range (push) for CONTENT credential shapes.
# The git invocation is read-only and target-scoped to the command's
# ``cwd`` repository, so it covers the artifact loam BUILDS, not only
# loam's own repo. Every git error is swallowed (returns no diff text) so
# the guard's fail-OPEN fault policy is preserved (a broken git read never
# blocks; it simply yields no match).

# A commit boundary: ``git commit`` (allowing global flags between ``git``
# and the ``commit`` subcommand). A push boundary: ``git push``. The match
# is anchored on the subcommand token so ``git log --grep=commit`` /
# ``git show`` do not trip it.
_GIT_COMMIT_RE = re.compile(r"\bgit\b(?:\s+-{1,2}\S+)*\s+commit\b")
_GIT_PUSH_RE = re.compile(r"\bgit\b(?:\s+-{1,2}\S+)*\s+push\b")


def _is_commit_boundary(command: str) -> bool:
    return bool(_GIT_COMMIT_RE.search(command))


def _is_push_boundary(command: str) -> bool:
    return bool(_GIT_PUSH_RE.search(command))


def _git_text(cwd: Path, args: list[str]) -> str:
    """Run a read-only ``git`` command in *cwd*; return stdout or "".

    Fail-SOFT: any non-zero exit, missing git, or OS error yields the
    empty string (no match) so the staged-diff scan can never block on a
    git read failure — preserving the guard's ``D-SECHK.FAIL-OPEN``
    fault policy (AC.SBB.1 additive constraint)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout or ""


def _boundary_diff_text(workspace_root: Path, command: str) -> str:
    """Collect the content a commit/push boundary would publish.

    Commit boundary -> the staged diff (``git diff --cached``). Push
    boundary -> the unpushed commit range against the tracked upstream
    (``git log -p @{upstream}..HEAD``), falling back to the full local
    history when no upstream is configured (a first push). Returns "" on
    any git failure (fail-soft)."""
    parts: list[str] = []
    if _is_commit_boundary(command):
        parts.append(_git_text(workspace_root, ["diff", "--cached", "--no-color"]))
    if _is_push_boundary(command):
        rng = _git_text(
            workspace_root,
            ["log", "-p", "--no-color", "@{upstream}..HEAD"],
        )
        if not rng.strip():
            # No upstream configured (first push) — scan local history so
            # an initial push of an embedded secret is still caught.
            rng = _git_text(workspace_root, ["log", "-p", "--no-color"])
        parts.append(rng)
    return "\n".join(p for p in parts if p)


def _reason_staged_diff(pattern_name: str, matched_text: str) -> str:
    redacted = (
        matched_text[:6] + "..." + matched_text[-4:]
        if len(matched_text) > 16
        else matched_text[:4] + "..."
    )
    return (
        f"AC.SBB.1 (secret-at-commit, secure-build baseline, UNIVERSAL) — "
        f"refused: the content this commit/push would publish matches "
        f"credential pattern `{pattern_name}` (token redacted: "
        f"`{redacted}`). A secret embedded in a file (not just on the "
        f"command line) was found in the staged diff / unpushed commits of "
        f"the repository this command targets — the secure-build baseline "
        f"blocks it at the commit/push boundary so the credential never "
        f"enters version control (this fires for any project loam builds, "
        f"not only loam's own repo). Repair directions: (a) remove the "
        f"credential from the file and re-stage; (b) source it from an env "
        f"var / secret store at runtime; (c) if it is a sample, move it to "
        f"a `.env.example` / `.env.sample` documentation file. "
        f"`secret-never-committed` is a NON-tunable floor of the "
        f"secure-build baseline (AC.SBB.4) — its strictness is not "
        f"configurable down to surface-only. Set "
        f"`LOAM_SAFETY_HOOKS_SECRET=off` for the session to bypass this "
        f"hook (the toggle is logged to "
        f"`<workspace>/.loam/safety-hooks.log`)."
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

        # ---- STAGED-DIFF patterns (AC.SBB.1) — Bash commit/push boundary.
        # Additive: scans the content a commit/push would PUBLISH (staged
        # diff / unpushed range) for the same CONTENT credential shapes.
        # Fail-soft git read => no match => existing fail-OPEN preserved.
        if tool_name == "Bash":
            cmd = tool_input.get("command")
            if isinstance(cmd, str) and (
                _is_commit_boundary(cmd) or _is_push_boundary(cmd)
            ):
                diff_text = _boundary_diff_text(workspace_root, cmd)
                matched, pattern_name, matched_text = _check_content_patterns(
                    workspace_root, diff_text
                )
                if matched:
                    reason = _reason_staged_diff(pattern_name, matched_text)
                    _emit_deny(reason, pattern_name=pattern_name)
                    _append_log(
                        workspace_root,
                        {
                            "ts": _now_iso(),
                            "hook": "secret_pattern_guard",
                            "decision": "deny",
                            "class": "secret-at-commit",
                            "tool": tool_name,
                            "pattern": pattern_name,
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
    except Exception as exc:  # noqa: BLE001 — declared fail-policy (D-SECHK.FAIL-OPEN)
        decision = apply_fault_policy(FAIL_POLICY)
        if workspace_root is not None:
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "secret_pattern_guard",
                    "decision": decision.label,
                    "exception": f"{type(exc).__name__}: {exc!s}",
                },
            )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
