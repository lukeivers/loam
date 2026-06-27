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

"""Dangerous-flag PreToolUse gate (AC.SECHK.2).

Blocks three Bash command-flag shapes per the ECC-floor:

* ``git push --no-verify`` — bypasses pre-push hooks
* ``git commit --no-verify`` — bypasses pre-commit hooks
* ``git push --force`` (or ``--force-with-lease``) against a
  protected branch (default protected set: ``main``, ``master``,
  ``pos-v2``, ``production``; extensible per workspace via
  ``<workspace>/.loam/protected-branches.yaml``)

Fires regardless of workspace mode (UNIVERSAL).

Toggle off via ``LOAM_SAFETY_HOOKS=off`` or
``LOAM_SAFETY_HOOKS_DANGEROUS_FLAG=off``. Fail-open per
D-SECHK.FAIL-OPEN.

NOTE: this hook intentionally does NOT overlap bash_guard's B5
(blast-radius) surface — bash_guard still owns force-push-to-
protected, ``rm -rf`` outside scratch, ``chmod -R 777`` against
home, etc. This hook fires on a DIFFERENT axis (``--no-verify``
flag bypass) that bash_guard does not cover. The single overlap
``git push --force <protected-branch>`` produces a dual-deny —
acceptable per D-SECHK.OVERLAP partial-absorb (the hook layer
admits matcher independence; both hooks denying is harmless).

Stdlib only: json, os, re, sys, time, pathlib.
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
# standalone script (Claude Code spawns it as ``python <path>``). Stdlib-
# only sibling import — does NOT pull the loam.safety_layer package.
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from _fail_policy import FailPolicy, apply_fault_policy  # noqa: E402

# Declared per-gate fail-policy (AC.DSF.5): this is an ADVISORY guard, so
# it fails OPEN on its own internal fault — the D-SECHK.FAIL-OPEN
# convention, unchanged. Only floor destructive gates declare FAIL_CLOSED.
FAIL_POLICY = FailPolicy.FAIL_OPEN


SAFETY_HOOKS_LOG_RELATIVE = (".loam", "safety-hooks.log")
ENV_TOGGLE_ALL = "LOAM_SAFETY_HOOKS"
ENV_TOGGLE_THIS = "LOAM_SAFETY_HOOKS_DANGEROUS_FLAG"
TOGGLE_OFF_VALUES: frozenset[str] = frozenset({"off", "0", "false", "no"})

_DEFAULT_PROTECTED_BRANCHES: frozenset[str] = frozenset(
    {"main", "master", "pos-v2", "production"}
)


# Flag-shape patterns. Each entry: (compiled regex, dispatch-class
# label, description for the diagnostic).

_GIT_PUSH_NO_VERIFY = re.compile(
    r"\bgit\s+push\b[^\n;|&]*\s--no-verify\b"
)
_GIT_COMMIT_NO_VERIFY = re.compile(
    r"\bgit\s+commit\b[^\n;|&]*\s--no-verify\b"
)
_GIT_PUSH_FORCE = re.compile(
    r"\bgit\s+push\b[^\n;|&]*\s--force(?:-with-lease)?\b"
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


def _load_protected_branches(workspace_root: Path) -> frozenset[str]:
    """Load workspace-local protected-branch additions; floor stays.

    Schema:
        branches:
          - feature-prod
          - release-train
    """
    additions_path = (
        workspace_root / ".loam" / "protected-branches.yaml"
    )
    if not additions_path.is_file():
        return _DEFAULT_PROTECTED_BRANCHES
    try:
        text = additions_path.read_text(encoding="utf-8")
    except OSError:
        return _DEFAULT_PROTECTED_BRANCHES
    extras: list[str] = []
    in_list = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.strip() == "branches:":
            in_list = True
            continue
        if in_list and line.lstrip().startswith("- "):
            name = line.lstrip()[2:].strip().strip("'\"")
            if name:
                extras.append(name)
        elif in_list and not line.startswith(" "):
            in_list = False
    return _DEFAULT_PROTECTED_BRANCHES | frozenset(extras)


def _force_push_targets_protected(
    command: str, protected: frozenset[str]
) -> tuple[bool, str]:
    """True iff a ``git push --force`` command names a protected
    branch as a positional argument. Returns ``(matched, ref)``.
    """
    m = _GIT_PUSH_FORCE.search(command)
    if m is None:
        return (False, "")
    # Look for the trailing ref token after --force in the same
    # segment. Conservative: split on shell separators, walk the
    # push segment's tokens, find the ref.
    segment_match = re.search(
        r"\bgit\s+push\b[^\n;|&]*",
        command,
    )
    if segment_match is None:
        return (False, "")
    segment = segment_match.group(0)
    tokens = segment.split()
    # Walk tokens; ignore flags + remote name; find the trailing
    # branch/ref. The shape is `git push [flags] [remote] [ref]`.
    refs: list[str] = []
    saw_remote = False
    for tok in tokens[2:]:  # skip `git push`
        if tok.startswith("-"):
            continue
        if not saw_remote:
            saw_remote = True
            continue
        refs.append(tok)
    for ref in refs:
        # Strip refspec (`local:remote`) — check the remote half.
        remote_side = ref.split(":")[-1] if ":" in ref else ref
        # Strip leading refs/heads/ if present.
        if remote_side.startswith("refs/heads/"):
            remote_side = remote_side[len("refs/heads/") :]
        if remote_side in protected:
            return (True, remote_side)
    return (False, "")


def _reason_no_verify(command: str, *, flag_class: str) -> str:
    return (
        f"AC.SECHK.2 (dangerous-flag, UNIVERSAL) — refused: command "
        f"uses `{flag_class}`. The `--no-verify` flag bypasses git "
        f"pre-commit / pre-push hooks; loam treats those hooks as "
        f"part of the user's defense-in-depth and refuses to "
        f"bypass them. Repair directions: (a) fix the underlying "
        f"hook failure rather than bypassing; (b) if a genuine "
        f"emergency bypass is needed, the user runs the git "
        f"command in a shell outside Claude Code; (c) set "
        f"`LOAM_SAFETY_HOOKS_DANGEROUS_FLAG=off` for the session "
        f"(logged to `<workspace>/.loam/safety-hooks.log`)."
    )


def _reason_force_protected(command: str, ref: str) -> str:
    return (
        f"AC.SECHK.2 (dangerous-flag, UNIVERSAL) — refused: command "
        f"force-pushes to protected branch `{ref}`. Protected "
        f"branches default to `main`, `master`, `pos-v2`, "
        f"`production`; extensible via "
        f"`<workspace>/.loam/protected-branches.yaml`. Repair "
        f"directions: (a) push to a feature branch and open a PR; "
        f"(b) if the force-push is intentional and authorized, run "
        f"the git command in a shell outside Claude Code; (c) set "
        f"`LOAM_SAFETY_HOOKS_DANGEROUS_FLAG=off` for the session."
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
        if not isinstance(tool_name, str) or tool_name != "Bash":
            return 0
        if not isinstance(tool_input, dict):
            return 0
        command = tool_input.get("command")
        if not isinstance(command, str) or not command:
            return 0

        env = dict(os.environ)
        if _is_toggled_off(env):
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "dangerous_flag_guard",
                    "decision": "toggled-off",
                    "tool": tool_name,
                },
            )
            return 0

        if _GIT_PUSH_NO_VERIFY.search(command) is not None:
            reason = _reason_no_verify(
                command, flag_class="git push --no-verify"
            )
            _emit_deny(reason)
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "dangerous_flag_guard",
                    "decision": "deny",
                    "class": "git-push-no-verify",
                    "tool": tool_name,
                },
            )
            return 0

        if _GIT_COMMIT_NO_VERIFY.search(command) is not None:
            reason = _reason_no_verify(
                command, flag_class="git commit --no-verify"
            )
            _emit_deny(reason)
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "dangerous_flag_guard",
                    "decision": "deny",
                    "class": "git-commit-no-verify",
                    "tool": tool_name,
                },
            )
            return 0

        protected = _load_protected_branches(workspace_root)
        matched_force, ref = _force_push_targets_protected(
            command, protected
        )
        if matched_force:
            reason = _reason_force_protected(command, ref)
            _emit_deny(reason)
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "dangerous_flag_guard",
                    "decision": "deny",
                    "class": "git-push-force-protected",
                    "ref": ref,
                    "tool": tool_name,
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
                    "hook": "dangerous_flag_guard",
                    "decision": decision.label,
                    "exception": f"{type(exc).__name__}: {exc!s}",
                },
            )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
