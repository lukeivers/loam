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

"""Working-directory-discipline PreToolUse gate (AC.WDGUARD.*).

Structural enforcement of the rule that **framework-SOURCE code is
edited in CANONICAL loam, never inside a DERIVED workspace's vendored
framework copy.** The failure mode this prevents (task #89, seen
twice): a session edits framework code directly in a derived
workspace's `framework/` tree (e.g. `pos3/framework/...`) instead of
canonical `~/loam`; the vendored copy diverges and is nearly clobbered
by the next framework upgrade.

Blocks ``Edit`` / ``Write`` / ``MultiEdit`` when BOTH hold:

  (a) the target ``file_path`` is FRAMEWORK-SOURCE — under the
      repo-relative ``framework/`` or ``plugins/`` tree, and NOT in
      the workspace-local exclusion set; AND
  (b) the enclosing git repository is NOT canonical loam — i.e. none
      of its git remotes points at the canonical loam upstream
      (``github.com[:/]…/loam(.git)?``).

The detection signal is POSITIVE-IDENTITY-OF-CANONICAL: a framework-
source edit is allowed only when the repo PROVES it is canonical loam
(carries the canonical-loam remote URL). Every real canonical checkout
AND every canonical git worktree carries that origin URL, so the guard
never false-positives on legitimate framework dev. A derived/vendored
copy (empty origin, or a different repo like ``pos3-workspace``, or a
local-path-only ``canonical`` remote) fails the identity check and is
blocked.

Three ALLOW cases (the discipline this guard must NOT obstruct):

  * framework-source inside canonical loam / a canonical worktree
    -> ALLOW (that is the correct place to do framework dev).
  * workspace-local content — ``.loam/`` user-state, ``.scratch/``,
    ``products/``, ``workspace/``, persona ``/memory/`` files,
    ``docs/plans/`` plan-docs, ``CLAUDE.md``, ``.claude/`` infra,
    ``.git/`` — ALLOW everywhere (those legitimately live in the
    workspace).
  * any tool other than Edit/Write/MultiEdit -> not our concern.

Override hatch (the rare legitimate case — e.g. a one-off framework
edit in a derived tree that will be hand-carried to canonical):

  * env ``LOAM_WD_GUARD=off`` (this guard), or
  * env ``LOAM_SAFETY_HOOKS=off`` (all safety hooks), or
  * a ``<repo-root>/.loam/.wd-guard-override`` sentinel file.

Fail-OPEN per D-SECHK.FAIL-OPEN: any internal error / malformed input /
unresolvable repo -> ALLOW (exit 0, no deny). The hook can never wedge
the session. Decisions + overrides + fail-opens are logged to
``<workspace>/.loam/safety-hooks.log`` (best-effort).

Block contract (Claude Code PreToolUse, same as config_write_guard):
JSON ``hookSpecificOutput.permissionDecision: deny`` on stdout.

Stdlib only.
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


SAFETY_HOOKS_LOG_RELATIVE = (".loam", "safety-hooks.log")
ENV_TOGGLE_ALL = "LOAM_SAFETY_HOOKS"
ENV_TOGGLE_THIS = "LOAM_WD_GUARD"
TOGGLE_OFF_VALUES: frozenset[str] = frozenset({"off", "0", "false", "no"})

CONTENT_TOOLS: frozenset[str] = frozenset({"Edit", "Write", "MultiEdit"})

# Override sentinel, resolved relative to the enclosing git repo root.
OVERRIDE_SENTINEL_RELATIVE = (".loam", ".wd-guard-override")

# Canonical-loam upstream identity. A repo whose any remote URL matches
# this is CANONICAL (framework dev allowed there). Matches HTTPS + SSH
# forms: https://github.com/<owner>/loam(.git), git@github.com:<owner>/
# loam(.git). The owner segment is intentionally not pinned to a single
# account so a fork-based canonical clone still identifies as canonical.
CANONICAL_REMOTE_RE = re.compile(
    r"github\.com[:/][^/\s]+/loam(?:\.git)?(?:\s|$)",
    re.IGNORECASE,
)

# Repo-relative top-level trees that hold framework-SOURCE.
FRAMEWORK_SOURCE_PREFIXES: tuple[str, ...] = ("framework/", "plugins/")

# Workspace-local content — ALLOWED even inside a derived workspace.
# Matched as a path SUBSTRING (leading + trailing slash anchored where
# it matters) against the repo-relative POSIX path.
WORKSPACE_LOCAL_SUBSTRINGS: tuple[str, ...] = (
    "/.loam/",
    ".loam/",
    "/.scratch/",
    ".scratch/",
    "/.claude/",
    ".claude/",
    "/.git/",
    ".git/",
    "/products/",
    "products/",
    "/workspace/",
    "workspace/",
    "/memory/",
    "/docs/plans/",
    "docs/plans/",
)

WORKSPACE_LOCAL_BASENAMES: frozenset[str] = frozenset(
    {"claude.md", "claude.dev.md", "memory.md"}
)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _log_path(workspace_root: Path) -> Path:
    return workspace_root.joinpath(*SAFETY_HOOKS_LOG_RELATIVE)


def _append_log(workspace_root: Path | None, payload: dict[str, Any]) -> None:
    if workspace_root is None:
        return
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


def _target_dir(file_path: str, cwd: Path) -> Path:
    """Directory in which the write target lives (existing or not).

    Relative paths resolve against the envelope cwd. The directory is
    used to locate the enclosing git repo; the file itself need not yet
    exist (a Write may be creating it).
    """
    p = Path(file_path)
    if not p.is_absolute():
        p = cwd / p
    # The parent dir is where we probe git from. If the path names a
    # directory-like target, probing from it directly is also fine —
    # git -C walks up regardless.
    return p.parent if p.parent != p else p


def _git_toplevel(probe_dir: Path) -> Path | None:
    """Absolute path of the enclosing git working tree, or None."""
    try:
        out = subprocess.run(
            ["git", "-C", str(probe_dir), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:  # noqa: BLE001 — fail-open on any git error
        return None
    if out.returncode != 0:
        return None
    top = out.stdout.strip()
    if not top:
        return None
    try:
        return Path(top)
    except Exception:  # noqa: BLE001
        return None


def _repo_is_canonical(probe_dir: Path) -> bool:
    """True iff the enclosing git repo identifies as canonical loam.

    Reads ALL remote URLs (`git remote -v`) and checks any against the
    canonical-loam upstream pattern. Positive-identity check: only a
    repo that PROVES it is canonical loam returns True. Empty-origin /
    different-repo / local-path-only-remote derived copies return
    False. Fail-open is the CALLER's job — here, an unresolvable repo
    returns False (treated as derived), but the caller has already
    confirmed we are inside *some* git repo via _git_toplevel before
    reaching the block path, and any subprocess failure short-circuits
    to allow upstream.
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(probe_dir), "remote", "-v"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:  # noqa: BLE001
        # Can't read remotes -> cannot prove canonical. Caller wraps
        # this in a try/except that fails OPEN, so a hard subprocess
        # error never reaches a deny.
        raise
    if out.returncode != 0:
        return False
    return bool(CANONICAL_REMOTE_RE.search(out.stdout))


def _repo_relative_posix(file_path: str, cwd: Path, repo_root: Path) -> str:
    """POSIX path of the target relative to the repo root.

    Falls back to the basename-anchored absolute POSIX string if the
    target is not under repo_root (defensive — shouldn't happen once
    _git_toplevel succeeded).
    """
    p = Path(file_path)
    if not p.is_absolute():
        p = cwd / p
    try:
        return p.resolve(strict=False).relative_to(
            repo_root.resolve(strict=False)
        ).as_posix()
    except Exception:  # noqa: BLE001
        return p.as_posix()


def _is_workspace_local(rel_posix: str) -> bool:
    low = rel_posix.lower()
    for sub in WORKSPACE_LOCAL_SUBSTRINGS:
        if sub in low:
            return True
    base = low.rsplit("/", 1)[-1]
    if base in WORKSPACE_LOCAL_BASENAMES:
        return True
    return False


def _is_framework_source(rel_posix: str) -> bool:
    """True iff the repo-relative path is framework-SOURCE.

    Under the repo-relative framework/ or plugins/ tree (the leading
    segment), AND not workspace-local. The leading-segment anchor (not
    a substring) is deliberate: a derived workspace's vendored copy
    sits at `framework/framework/...` from the OUTER repo's view, but
    we classify relative to the INNER (vendored) repo root, where it is
    `framework/...` again — so the anchor is correct for both canonical
    and the vendored repo.
    """
    if _is_workspace_local(rel_posix):
        return False
    low = rel_posix.lstrip("./")
    for prefix in FRAMEWORK_SOURCE_PREFIXES:
        if low.startswith(prefix):
            return True
    return False


def _override_sentinel_present(repo_root: Path) -> bool:
    try:
        return repo_root.joinpath(*OVERRIDE_SENTINEL_RELATIVE).exists()
    except Exception:  # noqa: BLE001
        return False


def _reason(rel_posix: str) -> str:
    return (
        "AC.WDGUARD.1 (working-directory discipline, UNIVERSAL) — "
        f"refused: framework-source edit `{rel_posix}` inside a DERIVED "
        "workspace (a vendored framework copy), not canonical loam. "
        "Framework code is edited in CANONICAL loam at "
        "`/Users/lukeivers/loam`; edits to a derived workspace's "
        "vendored `framework/` tree diverge silently and are clobbered "
        "by the next framework upgrade. Repair direction: make this "
        "change in `/Users/lukeivers/loam` (or a canonical worktree), "
        "seal it, and let the derived workspace receive it via the "
        "normal framework upgrade/re-sync. If a one-off edit in this "
        "tree is genuinely correct (and will be hand-carried to "
        "canonical), set `LOAM_WD_GUARD=off` for the session or "
        "`touch <repo>/.loam/.wd-guard-override` (the bypass is logged "
        "to `<workspace>/.loam/safety-hooks.log`)."
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
        cwd_str = envelope.get("cwd")
        if not isinstance(cwd_str, str) or not cwd_str:
            return 0
        cwd = Path(cwd_str)
        workspace_root = cwd

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
                    "hook": "wd_discipline_guard",
                    "decision": "toggled-off",
                    "tool": tool_name,
                    "file_path": file_path,
                },
            )
            return 0

        probe = _target_dir(file_path, cwd)
        repo_root = _git_toplevel(probe)
        if repo_root is None:
            # Not inside any git repo -> cannot be a framework-source
            # tree we govern. Allow (fail-open / out-of-scope).
            return 0

        # Sentinel override lives at the enclosing repo root.
        if _override_sentinel_present(repo_root):
            _append_log(
                workspace_root,
                {
                    "ts": _now_iso(),
                    "hook": "wd_discipline_guard",
                    "decision": "override-sentinel",
                    "tool": tool_name,
                    "file_path": file_path,
                    "repo": str(repo_root),
                },
            )
            return 0

        rel_posix = _repo_relative_posix(file_path, cwd, repo_root)
        if not _is_framework_source(rel_posix):
            # Workspace-local or non-framework path -> always allow.
            return 0

        # Framework-source. Allow ONLY if the repo proves it is
        # canonical loam; otherwise it is a derived workspace -> block.
        if _repo_is_canonical(probe):
            return 0

        reason = _reason(rel_posix)
        _emit_deny(reason)
        _append_log(
            workspace_root,
            {
                "ts": _now_iso(),
                "hook": "wd_discipline_guard",
                "decision": "deny",
                "tool": tool_name,
                "file_path": file_path,
                "repo": str(repo_root),
                "rel": rel_posix,
            },
        )
        return 0
    except Exception as exc:  # noqa: BLE001 — fail-OPEN per D-SECHK.FAIL-OPEN
        _append_log(
            workspace_root,
            {
                "ts": _now_iso(),
                "hook": "wd_discipline_guard",
                "decision": "fail-open",
                "exception": f"{type(exc).__name__}: {exc!s}",
            },
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
