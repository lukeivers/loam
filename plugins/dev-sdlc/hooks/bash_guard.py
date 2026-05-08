"""PreToolUse gate — refuses Bash commands that match one of the
five A4 failure classes (B1 amend-in-subagent, B2 secret-commit, B3
loam-amend-dry-run-failure, B4 wrong-tree-write, B5 blast-radius).

Added by structural-enforcement A4 (Bash/Agent-context guards). The
gate fires on the Claude Code PreToolUse matcher ``Bash`` (every shell
command). It composes alongside A2's objective-binding gate + A3's
TDD-guard in the multi-contributor PreToolUse stanza; matcher
independence (Bash matcher vs Edit|Write|MultiEdit matcher) means no
cross-matcher interference.

## Failure classes covered (AC.BAG.1 .. AC.BAG.7)

UNIVERSAL (fire regardless of workspace mode):

  - **B2 / AC.BAG.1** — secret-file commit. Detects a ``git add /
    commit / stash`` whose argument list names a secret-class file
    (``.env``, ``*.pem``, ``id_rsa``, etc.). The env-var override
    ``POS_BASH_GUARD_ALLOW=1`` does NOT bypass this gate.
  - **B5 / AC.BAG.2** — blast-radius destructive command (force-push
    to protected branch; ``rm -rf`` outside ``.scratch/`` + ``/tmp/``;
    ``chmod -R 777|0`` against home; ``dd`` to device; ``curl |
    bash``; ``mkfs`` to device). The env-var override does NOT
    bypass this gate.

DEV-MODE-only (fire only when ``corpus_load_sentinel.workspace_mode``
returns ``"dev-mode"``):

  - **B1 / AC.BAG.3** — ``git commit --amend`` in subagent context.
    Detected via active-scope sentinel presence (proxy: a sentinel
    written by the dispatcher marks the agent-context window).
    Bypassable via ``POS_BASH_GUARD_ALLOW=1``.
  - **B3 / AC.BAG.4** — amendment-shape commit pattern when
    ``loam amend apply --dry-run <manifest>`` would fail. Detection:
    commit message starting with ``feat(...)``, ``fix(...)``,
    ``chore(...)``, or ``seal(...)`` over a sealed-component slug.
    Invokes loam amend; on exit ≠ 0 deny. Bypassable via
    ``POS_BASH_GUARD_ALLOW=1``.
  - **B4 / AC.BAG.5** — wrong-tree-write via ``cd <ws>/framework
    && <write>``. Detected via a ``cd <path>`` clause whose target
    resolves to ``<workspace>/framework/`` followed by a write
    action. Bypassable via ``POS_BASH_GUARD_ALLOW=1``.

ENVELOPE:

  - **AC.BAG.6** — non-matching commands → no-op (default-allow).
  - **AC.BAG.7** — every fire (allow / deny / no-op) appends one
    NDJSON line to ``<workspace>/workspace/.pos/bash-guard.log``.

## Surface contract

Reads the Claude Code PreToolUse JSON envelope from stdin:

    {
      "session_id": "...",
      "cwd": "<workspace>",
      "hook_event_name": "PreToolUse",
      "tool_name": "Bash",
      "tool_input": { "command": "<shell string>", ... }
    }

Writes one of two JSON shapes to stdout:

  - allow / no-op: empty stdout (Claude Code's default-allow).
  - deny: ``{"hookSpecificOutput": {"hookEventName": "PreToolUse",
    "permissionDecision": "deny", "permissionDecisionReason":
    "<structured text>"}}``.

Exits 0 on every path (fail-soft per A2/A3 convention).

Stdlib only (json, os, re, subprocess, sys) plus shared
``_gate_helpers``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


# Ensure sibling modules are importable when invoked as a standalone
# script.
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

# Post-M6b.0 (F2 ruling — gate hook source MOVED from
# framework/hands-off-lifecycle/hooks/ to plugins/dev-sdlc/hooks/):
# _gate_helpers.py STAYS at the canonical hooks/ dir (used by gate
# hooks AND by other infrastructure). Add the canonical hooks dir
# to sys.path so _gate_helpers resolves regardless of which hooks/
# tree this script is invoked from.
_CANONICAL_HOOKS_DIR = (
    Path(__file__).resolve().parents[3]
    / "framework"
    / "hands-off-lifecycle"
    / "hooks"
)
if (
    _CANONICAL_HOOKS_DIR.exists()
    and str(_CANONICAL_HOOKS_DIR) not in sys.path
):
    sys.path.insert(0, str(_CANONICAL_HOOKS_DIR))


import _gate_helpers as _helpers  # noqa: E402


# ---------------------------------------------------------------------
# Module-level shims (mirror A2/A3 patterns; tests monkeypatch these).
# ---------------------------------------------------------------------

WORKSPACE_STATE_SUBDIR = _helpers.WORKSPACE_STATE_SUBDIR
POS_SUBDIR = _helpers.POS_SUBDIR
AUDIT_LOG_FILENAME = "bash-guard.log"

ENV_OVERRIDE_NAME = "POS_BASH_GUARD_ALLOW"

TOOLS_GATED = ("Bash",)


def _audit_log_path(workspace_root: Path) -> Path:
    return _helpers.audit_log_path(workspace_root, AUDIT_LOG_FILENAME)


def _read_active_scope_sentinel_or_none(workspace_root: Path) -> Any:
    return _helpers.read_active_scope_sentinel_or_none(workspace_root)


# ---------------------------------------------------------------------
# Decision (the hook's outcome)
# ---------------------------------------------------------------------


class Decision:
    """Tiny container for a Bash-guard decision.

    ``decision`` is one of {"allow", "deny", "no-op"}.
    ``failure_class`` names the specific class on deny:
    {"secret-commit", "blast-radius", "amend-in-subagent",
     "loam-amend-dry-run-failure", "wrong-tree-write", None}.
    """

    __slots__ = (
        "decision",
        "reason",
        "failure_class",
        "matched",
    )

    def __init__(
        self,
        decision: str,
        *,
        reason: str | None = None,
        failure_class: str | None = None,
        matched: str | None = None,
    ) -> None:
        self.decision = decision
        self.reason = reason
        self.failure_class = failure_class
        self.matched = matched


# ---------------------------------------------------------------------
# AC.BAG.3 — amend-in-subagent detection
# ---------------------------------------------------------------------


_AMEND_PATTERN = re.compile(r"\bgit\s+commit\b[^\n]*--amend\b")


def _is_amend_command(command: str) -> bool:
    """True iff ``command`` invokes ``git commit --amend``.

    Conservative match — any ``git commit`` followed by ``--amend``
    anywhere in the same pipeline segment fires. Heredoc-style
    invocations (``bash -c 'git commit --amend ...'``) are caught by
    the same regex because the pattern matches on the literal string.
    """
    return _AMEND_PATTERN.search(command) is not None


# ---------------------------------------------------------------------
# AC.BAG.4 — amendment-shape commit pattern detection
# ---------------------------------------------------------------------


# Sealed-component-shape commit message regex. Matches commits whose
# message opens with one of {feat, fix, chore, seal}(<component-slug>):
# i.e. the canonical amendment commit shape across pos-v2's history.
_AMENDMENT_COMMIT_PATTERN = re.compile(
    r"git\s+commit\s+[^\n]*-m\s+[\"'](feat|fix|chore|seal)\("
)


def _is_amendment_shape_commit(command: str) -> bool:
    """True iff ``command`` is a sealed-component-shape commit.

    Per AC.BAG.4: the commit message opens with
    ``feat|fix|chore|seal(<slug>):`` — the canonical amendment commit
    pattern. The classifier matches the literal command string; quoting
    differences (``-m "..."`` vs ``-m '...'``) are tolerated.
    """
    return _AMENDMENT_COMMIT_PATTERN.search(command) is not None


def _candidate_manifest_paths(
    workspace_root: Path, sentinel: Any
) -> list[Path]:
    """Discover candidate manifest paths for the loam amend dry-run.

    Method per ODD §7.4: when an active-scope sentinel is present and
    its ``plan_path`` resolves to a ``docs/plans/<slug>.md``,
    derive the sibling ``<slug>.manifest.yaml``. Otherwise, fall
    through to a glob over ``docs/plans/*.manifest.yaml`` —
    the dry-run iterates and aggregates the result.
    """
    candidates: list[Path] = []
    plan_path = getattr(sentinel, "plan_path", None) if sentinel else None
    if isinstance(plan_path, str) and plan_path:
        plan_p = workspace_root / plan_path
        if plan_p.suffix == ".md":
            manifest_p = plan_p.with_suffix("")
            manifest_p = manifest_p.with_suffix(".manifest.yaml")
            if manifest_p.is_file():
                candidates.append(manifest_p)
    if not candidates:
        plans_dir = workspace_root / "docs" / "plans"
        if plans_dir.is_dir():
            candidates = sorted(plans_dir.glob("*.manifest.yaml"))
    return candidates


def _loam_amend_dry_run(
    workspace_root: Path, manifest: Path
) -> tuple[int, str]:
    """Invoke ``loam amend apply --dry-run <manifest>``.

    Returns ``(exit_code, combined_stdout_stderr)``. Resolves
    loam (the unified top-level CLI; ``loam amend`` is the post-M1g
    rename of pre-M1g ``pos-amend``) via the workspace's venv.
    """
    loam = workspace_root / ".venv" / "bin" / "loam"
    if not loam.is_file():
        return (-1, "loam not found at .venv/bin/loam")
    try:
        result = subprocess.run(
            [
                str(loam),
                "amend",
                "apply",
                "--dry-run",
                str(manifest),
            ],
            capture_output=True,
            text=True,
            cwd=str(workspace_root),
            timeout=30,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        return (-1, f"loam amend invocation failed: {exc!s}")
    return (
        result.returncode,
        (result.stdout or "") + (result.stderr or ""),
    )


# ---------------------------------------------------------------------
# AC.BAG.5 — wrong-tree-write detection
# ---------------------------------------------------------------------


# `cd <path>` followed by a write-action chain. The classifier looks
# for `cd <ws-prefix>/framework[/<sub>] && <write>` patterns.
_CD_FRAMEWORK_PATTERN = re.compile(
    r"\bcd\s+(?P<target>['\"]?[^\s;|&'\"]+/framework(?:/[^\s;|&'\"]*)?[\"']?)"
    r"\s*(?:&&|;)\s*(?P<action>.+?)(?:$|;|\|)",
    re.DOTALL,
)


# Write-action subcommand prefixes.
_WRITE_ACTION_PATTERNS: tuple[str, ...] = (
    r"\bgit\s+(?:commit|apply|restore|add|stash\s+pop|stash\s+apply|am)\b",
    r"\btee\b",
    r"\bsed\s+-i\b",
    r">[^|]",  # redirect (excluding `>|`)
    r">>",
    r"\bcp\b",
    r"\bmv\b",
    r"\brm\b",
    r"\btouch\b",
    r"\bmkdir\b",
    r"\bchmod\b",
    r"\bchown\b",
    r"\bln\s+(?:-s\s+)?",
    r"\bpython\s+[^\n|;&]*\s+--write\b",
)


def _detect_wrong_tree_write(
    command: str, workspace_root: Path
) -> tuple[bool, str]:
    """Detect ``cd <ws>/framework && <write>`` patterns.

    Returns ``(matched, target_path)``. Per AC.BAG.5: fires when the
    target path resolves to ``<workspace>/framework/`` (or a subdir)
    AND the chained action is a write AND the target path is NOT in
    the dev-discipline carve-out set.
    """
    for m in _CD_FRAMEWORK_PATTERN.finditer(command):
        target = m.group("target").strip("'\"")
        action = m.group("action")
        if not _action_is_write(action):
            continue
        # Resolve target relative to workspace_root if relative.
        try:
            tgt_p = Path(target)
            if not tgt_p.is_absolute():
                tgt_p = workspace_root / tgt_p
            tgt_resolved = tgt_p.resolve()
            ws_resolved = workspace_root.resolve()
        except (OSError, ValueError):
            continue
        # Must be under <ws>/framework/.
        try:
            rel = tgt_resolved.relative_to(ws_resolved)
        except ValueError:
            continue
        rel_str = rel.as_posix()
        if not (
            rel_str == "framework"
            or rel_str.startswith("framework/")
        ):
            continue
        # Carve-out check: framework/docs/, framework/tools/,
        # framework/personas/ are admitted.
        carve_out_subpath = rel_str  # like "framework" or
        # "framework/<comp>"
        if _helpers.is_carve_out_path(carve_out_subpath):
            continue
        return (True, target)
    return (False, "")


def _action_is_write(action: str) -> bool:
    """True iff the chained shell action is a write."""
    for pattern in _WRITE_ACTION_PATTERNS:
        if re.search(pattern, action):
            return True
    return False


# ---------------------------------------------------------------------
# Decision pipeline
# ---------------------------------------------------------------------


def evaluate(
    *,
    workspace_root: Path,
    tool_name: str,
    tool_input: dict[str, Any],
    env: dict[str, str] | None = None,
) -> Decision:
    """Decide allow / deny / no-op for one PreToolUse Bash fire.

    Universal-leg checks fire BEFORE the mode-bit read (AC.BAG.1 +
    AC.BAG.2 fire regardless of mode). DEV-MODE-only checks fire only
    after the mode-bit confirms ``dev-mode``.

    The env-var override ``POS_BASH_GUARD_ALLOW=1`` admits B1, B3, B4
    (DEV-MODE-only classes) — the universal classes B2 + B5 are NOT
    bypassable per hard constraint 18.
    """
    if env is None:
        env = dict(os.environ)

    # Tool gate — only Bash is inspected.
    if tool_name not in TOOLS_GATED:
        return Decision("no-op")

    command = tool_input.get("command")
    if not isinstance(command, str) or not command:
        return Decision("no-op")

    # ---- Universal-leg checks (fire regardless of mode) -----
    # AC.BAG.1 — secret-file commit. NOT bypassable by env var.
    matched_secret, paths = _helpers.is_secret_commit_command(command)
    if matched_secret:
        reason = _reason_secret_commit(command, paths)
        return Decision(
            "deny",
            reason=reason,
            failure_class="secret-commit",
            matched=", ".join(paths),
        )

    # AC.BAG.2 — blast-radius. NOT bypassable by env var.
    matched_blast, reason_class, matched_text = (
        _helpers.is_blast_radius_command(command, workspace_root)
    )
    if matched_blast:
        reason = _reason_blast_radius(
            command, reason_class, matched_text
        )
        return Decision(
            "deny",
            reason=reason,
            failure_class="blast-radius",
            matched=matched_text,
        )

    # ---- Mode-bit partition gate ----
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    if mode != "dev-mode":
        return Decision("no-op")

    # Env-var override admits B1, B3, B4 (DEV-MODE-only classes).
    override_active = env.get(ENV_OVERRIDE_NAME) == "1"

    # AC.BAG.3 — git commit --amend in subagent context.
    if not override_active and _is_amend_command(command):
        sentinel = _read_active_scope_sentinel_or_none(workspace_root)
        if sentinel is not None:
            reason = _reason_amend_in_subagent(command, sentinel)
            return Decision(
                "deny",
                reason=reason,
                failure_class="amend-in-subagent",
                matched="--amend",
            )

    # AC.BAG.5 — wrong-tree-write `cd <ws>/framework && <write>`.
    if not override_active:
        matched_wt, target = _detect_wrong_tree_write(
            command, workspace_root
        )
        if matched_wt:
            reason = _reason_wrong_tree_write(command, target)
            return Decision(
                "deny",
                reason=reason,
                failure_class="wrong-tree-write",
                matched=target,
            )

    # AC.BAG.4 — amendment-shape commit pattern + loam amend dry-run.
    if not override_active and _is_amendment_shape_commit(command):
        sentinel = _read_active_scope_sentinel_or_none(workspace_root)
        candidates = _candidate_manifest_paths(workspace_root, sentinel)
        for manifest in candidates:
            exit_code, output = _loam_amend_dry_run(
                workspace_root, manifest
            )
            if exit_code != 0 and exit_code != -1:
                # Real dry-run failure (not a missing-loam env).
                reason = _reason_loam_amend_dry_run(
                    command, manifest, exit_code, output
                )
                return Decision(
                    "deny",
                    reason=reason,
                    failure_class="loam-amend-dry-run-failure",
                    matched=str(manifest),
                )

    return Decision("allow")


# ---------------------------------------------------------------------
# Reason text builders (structured natural-language deny reasons)
# ---------------------------------------------------------------------


def _reason_secret_commit(command: str, paths: list[str]) -> str:
    paths_text = ", ".join(f"`{p}`" for p in paths) or "(unnamed)"
    return (
        f"AC.BAG.1 (secret-commit, UNIVERSAL) — refused: the command "
        f"stages or commits secret-class file(s): {paths_text}. "
        f"Secret-class detected from the path pattern (`.env`, "
        f"`*.pem`, `*.key`, `id_rsa`, `id_ed25519`, "
        f"`credentials.json`, `.aws/credentials`). Repair "
        f"directions: (a) rename to `.env-example` / `.env.sample` if "
        f"this is documentation; (b) add the file to `.gitignore` and "
        f"un-stage it; (c) halt and surface to the operator if a "
        f"genuine credential file is being committed by mistake. The "
        f"`POS_BASH_GUARD_ALLOW=1` env-var override does NOT bypass "
        f"this gate (UNIVERSAL class)."
    )


def _reason_blast_radius(
    command: str, reason_class: str, matched_text: str
) -> str:
    repair_by_class = {
        "git-push-force-protected": (
            "use `git push` without `--force` (a regular merge or "
            "rebase-then-push); if a force-push really is intended, "
            "verify the target branch is not protected and the team "
            "has agreed"
        ),
        "git-push-force": (
            "use `git push` without `--force`; if force is needed for "
            "an unprotected branch, name the branch explicitly"
        ),
        "rm-rf-outside-scratch": (
            "scope deletes to `<workspace>/.scratch/`, `node_modules/`, "
            "`__pycache__/`, `.venv/`, or `/tmp/` — these are admitted "
            "carve-outs; absolute paths to user data are not"
        ),
        "chmod-recursive-home": (
            "scope `chmod -R` to a single project directory; never "
            "apply recursive permissions to `~` or `/`"
        ),
        "dd-to-device": (
            "halt; if a real disk-write is intended, the operator runs "
            "this command outside Claude Code"
        ),
        "curl-pipe-shell": (
            "save the URL output to a file (`curl URL -o /tmp/x.sh`), "
            "inspect the contents, then explicitly invoke if safe"
        ),
        "mkfs-on-device": (
            "halt; mkfs against a real device is data loss"
        ),
    }
    repair = repair_by_class.get(
        reason_class,
        "halt and surface to the operator",
    )
    return (
        f"AC.BAG.2 (blast-radius, UNIVERSAL) — refused: command "
        f"matches the `{reason_class}` class. Matched substring: "
        f"`{matched_text}`. Repair direction: {repair}. The "
        f"`POS_BASH_GUARD_ALLOW=1` env-var override does NOT bypass "
        f"this gate (UNIVERSAL class)."
    )


def _reason_amend_in_subagent(command: str, sentinel: Any) -> str:
    scope = getattr(sentinel, "scope_id", "(unknown)")
    return (
        f"AC.BAG.3 (amend-in-subagent, DEV-MODE) — refused: the "
        f"command invokes `git commit --amend` while an active-scope "
        f"sentinel is present (scope_id `{scope}`). Per "
        f"`feedback_no_amend_in_agent_dispatches`, agent-context "
        f"amends collapse the audit trail. Repair directions: (a) "
        f"author a NEW corrective commit instead; (b) if this is a "
        f"main-session intentional amend, remove the active-scope "
        f"sentinel or set `POS_BASH_GUARD_ALLOW=1` for this shell."
    )


def _reason_wrong_tree_write(command: str, target: str) -> str:
    return (
        f"AC.BAG.5 (wrong-tree-write, DEV-MODE) — refused: the "
        f"command chains a `cd {target} && <write-action>` against a "
        f"workspace-mirror's `framework/` tree. Per FIDRAFT-136, "
        f"main-session writes to a mirror's framework/ tree corrupt "
        f"the canonical pos-v2 audit trail. Repair directions: (a) "
        f"redirect the command to operate inside canonical pos-v2 "
        f"(`/Users/lukeivers/ivers-corp-pos-v2/`); (b) if the "
        f"workspace IS canonical, this gate should not have fired — "
        f"surface the false-positive; (c) `POS_BASH_GUARD_ALLOW=1` "
        f"bypasses for operator-trusted triage."
    )


def _reason_loam_amend_dry_run(
    command: str, manifest: Path, exit_code: int, output: str
) -> str:
    output_excerpt = (output or "").strip()
    if len(output_excerpt) > 1000:
        output_excerpt = output_excerpt[:1000] + " ... (truncated)"
    return (
        f"AC.BAG.4 (loam-amend-dry-run-failure, DEV-MODE) — refused: "
        f"the command is an amendment-shape commit (`feat|fix|chore|"
        f"seal(<slug>): ...`) but `loam amend apply --dry-run "
        f"{manifest}` exited {exit_code}. Output:\n{output_excerpt}\n"
        f"Repair directions: (a) fix the manifest's BASELINE / "
        f"components / universal_paths; (b) run `loam amend apply "
        f"<manifest>` to advance BASELINE before the seal commit; "
        f"(c) `POS_BASH_GUARD_ALLOW=1` bypasses for operator-trusted "
        f"triage."
    )


# ---------------------------------------------------------------------
# Audit log (AC.BAG.7)
# ---------------------------------------------------------------------


def _append_audit_line(
    workspace_root: Path,
    *,
    tool_name: str,
    command: str,
    mode: str,
    sentinel_state: str,
    decision: Decision,
) -> None:
    """Append one NDJSON line to A4's bash-guard audit log. Fail-soft.

    Schema mirrors A2/A3's per-fire shape with bash-specific keys.
    """
    payload = {
        "ts": _helpers.now_iso_z(),
        "tool": tool_name,
        "command": command,
        "mode": mode,
        "sentinel_state": sentinel_state,
        "decision": decision.decision,
        "failure_class": decision.failure_class,
        "matched": decision.matched,
        "reason": decision.reason,
    }
    _helpers.append_audit_line(
        workspace_root, AUDIT_LOG_FILENAME, payload
    )


# ---------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------


def _emit_allow_response() -> None:
    return


def _emit_deny_response(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    """Read PreToolUse envelope from stdin; emit allow/deny; exit 0.

    Fail-soft on every environmental / parse failure.
    """
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-soft
        return 0
    if not raw.strip():
        return 0
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError:
        return 0
    if not isinstance(envelope, dict):
        return 0

    tool_name = envelope.get("tool_name")
    if not isinstance(tool_name, str):
        return 0
    tool_input = envelope.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0

    cwd = envelope.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        return 0
    workspace_root = Path(cwd)

    decision = evaluate(
        workspace_root=workspace_root,
        tool_name=tool_name,
        tool_input=tool_input,
    )

    command = tool_input.get("command")
    if not isinstance(command, str):
        command = ""
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    sentinel_state = (
        "present"
        if _read_active_scope_sentinel_or_none(workspace_root) is not None
        else "absent"
    )

    _append_audit_line(
        workspace_root,
        tool_name=tool_name,
        command=command,
        mode=mode,
        sentinel_state=sentinel_state,
        decision=decision,
    )

    if decision.decision == "deny" and decision.reason is not None:
        _emit_deny_response(decision.reason)
    else:
        _emit_allow_response()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
