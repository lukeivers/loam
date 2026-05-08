"""PreToolUse gate — refuses Agent dispatches (Task tool calls) that
match one of the three A4 failure classes (T1 wrong-WD dispatch, T2
method-enumerated prompt above the length threshold, T3 stale dispatch
re-targeting an already-sealed amendment).

Added by structural-enforcement A4 (Bash/Agent-context guards). The
gate fires on the Claude Code PreToolUse matcher ``Task`` (every
Agent dispatch). It composes alongside A2's objective-binding gate +
A3's TDD-guard + A4's bash-guard in the multi-contributor PreToolUse
stanza; matcher independence (Task matcher vs Edit|Write|MultiEdit
matcher vs Bash matcher) means no cross-matcher interference.

## Failure classes covered (AC.AG.1 .. AC.AG.5)

ALL DEV-MODE-only (the rules are pos-v2-dev-specific):

  - **T1 / AC.AG.1** — wrong-WD dispatch. Detected via prompt
    mentions of pos-v2 surfaces (``framework/<comp>/src/``,
    ``framework/<comp>/tests/``, ``loam amend``, "seal commit",
    canonical path string, ``amendment #N`` shapes) combined with a
    parent envelope ``cwd`` that does NOT match the canonical pos-v2
    path.
  - **T2 / AC.AG.2** — method-enumerated prompt. Detected via a
    prompt length above 2500 characters. The threshold is NAMED in
    the AC text per D-A4.7.
  - **T3 / AC.AG.3** — stale dispatch. Detected via prompt mentions
    of an already-sealed ``amendment #N`` (manifest table query +
    git-log fallback) OR ``AC.<X>.<Y>`` (manifest table query). Fail-
    closed-to-permissive when tracker unreachable (fall through to
    allow) per A2's R7 mirror.

ENVELOPE:

  - **AC.AG.4** — non-matching dispatches → no-op.
  - **AC.AG.5** — every fire (allow / deny / no-op) appends one
    NDJSON line to ``<workspace>/workspace/.pos/agent-guard.log``.

## Surface contract

Reads the Claude Code PreToolUse JSON envelope from stdin:

    {
      "session_id": "...",
      "cwd": "<workspace>",
      "hook_event_name": "PreToolUse",
      "tool_name": "Task",
      "tool_input": { "prompt": "...", "subagent_type": "...",
                      "description": "..." }
    }

The parent's working directory is at the envelope's TOP LEVEL ``cwd``
field — NOT inside ``tool_input``. The subagent inherits this cwd.

Writes one of two JSON shapes to stdout:

  - allow / no-op: empty stdout.
  - deny: ``{"hookSpecificOutput": {"hookEventName": "PreToolUse",
    "permissionDecision": "deny", "permissionDecisionReason":
    "<structured text>"}}``.

Exits 0 on every path (fail-soft per A2/A3 convention).

Stdlib only (json, re, subprocess, sys) plus shared ``_gate_helpers``.
"""

from __future__ import annotations

import json
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
AUDIT_LOG_FILENAME = "agent-guard.log"

TOOLS_GATED = ("Task",)

# AC.AG.2 — length threshold (NAMED per D-A4.7).
PROMPT_LENGTH_THRESHOLD = 2500

# Canonical pos-v2 path — the tree against which AC.AG.1 verifies the
# dispatch's parent cwd. Hardcoded per the A2/A3 dispatch-template
# defaults convention; a future maintainer changing the canonical path
# updates this in lock-step with the rest of the codebase.
CANONICAL_LOAM_PATH = "/Users/lukeivers/ivers-corp-pos-v2"


def _audit_log_path(workspace_root: Path) -> Path:
    return _helpers.audit_log_path(workspace_root, AUDIT_LOG_FILENAME)


def _open_tracker(workspace_root: Path) -> Any | None:
    return _helpers.open_tracker_or_none(workspace_root)


# ---------------------------------------------------------------------
# AC.AG.1 — wrong-WD detection
# ---------------------------------------------------------------------

# Surface mentions of pos-v2 — when any of these appears in the
# dispatch prompt, the dispatch is targeting pos-v2 dev surfaces.
_LOAM_SURFACE_PATTERNS: tuple[re.Pattern, ...] = (
    re.compile(r"framework/[\w-]+/src/"),
    re.compile(r"framework/[\w-]+/tests/"),
    re.compile(r"\bloam amend\b"),
    re.compile(r"\bseal commit\b"),
    re.compile(r"/Users/lukeivers/ivers-corp-pos-v2/"),
    re.compile(r"\bamendment\s+#\d+", re.IGNORECASE),
)


def _detect_pos_v2_surface_mentions(prompt: str) -> list[str]:
    """Return the matched surface mention substrings.

    Empty list when none match.
    """
    found: list[str] = []
    for pat in _LOAM_SURFACE_PATTERNS:
        m = pat.search(prompt)
        if m is not None:
            found.append(m.group(0))
    return found


def _is_canonical_cwd(cwd: str) -> bool:
    """True iff ``cwd`` resolves to the canonical pos-v2 path.

    Tolerates trailing slash + symlink resolution.
    """
    if not cwd:
        return False
    try:
        cwd_resolved = Path(cwd).resolve()
        canonical_resolved = Path(CANONICAL_LOAM_PATH).resolve()
    except (OSError, ValueError):
        return False
    return cwd_resolved == canonical_resolved


# ---------------------------------------------------------------------
# AC.AG.3 — stale-dispatch detection
# ---------------------------------------------------------------------

_AMENDMENT_NUMBER_PATTERN = re.compile(
    r"amendment\s+#(\d+)", re.IGNORECASE
)
_AC_ID_PATTERN = re.compile(r"\bAC\.([A-Za-z0-9]+)\.([A-Za-z0-9]+)\b")


def _detect_amendment_numbers(prompt: str) -> list[int]:
    """Return amendment numbers mentioned in the prompt.

    Returns the unique sorted set of integers matched by `amendment
    #N`.
    """
    seen: set[int] = set()
    for m in _AMENDMENT_NUMBER_PATTERN.finditer(prompt):
        try:
            seen.add(int(m.group(1)))
        except ValueError:
            continue
    return sorted(seen)


def _detect_ac_ids(prompt: str) -> list[tuple[str, str]]:
    """Return AC IDs mentioned in the prompt as `(component-key, ac-suffix)`.

    Returns the unique tuples in order of first occurrence.
    """
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for m in _AC_ID_PATTERN.finditer(prompt):
        key = (m.group(1), m.group(2))
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def _amendment_seal_commit_for_number(
    workspace_root: Path, number: int
) -> str | None:
    """Find a seal commit naming `amendment #N`, or None.

    Searches `git log --grep="amendment #N"` for the most recent match.
    The classifier returns the SHA when a match exists; the caller
    surfaces it in the deny diagnostic. Method per ODD §7.4.
    """
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(workspace_root),
                "log",
                "--grep",
                f"amendment #{number}",
                "--pretty=format:%H",
                "-n",
                "1",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    sha = (result.stdout or "").strip()
    return sha or None


def _ac_is_sealed(tracker: Any, component: str, ac_id: str) -> bool:
    """True iff the manifest has at least one row for (component, ac_id).

    A row's existence means the AC is registered (sealed or in-flight).
    The classifier is conservative: if the tracker call fails, return
    False (fall through to allow per fail-closed-to-permissive).
    """
    try:
        rows = tracker.manifest_rows_for_ac(component, ac_id)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return False
    return bool(rows)


# ---------------------------------------------------------------------
# Decision (the hook's outcome)
# ---------------------------------------------------------------------


class Decision:
    """Tiny container for an Agent-guard decision.

    ``decision`` is one of {"allow", "deny", "no-op"}.
    ``failure_class`` names the specific class on deny:
    {"wrong-wd", "method-enumerated-prompt", "stale-dispatch", None}.
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


def evaluate(
    *,
    workspace_root: Path,
    tool_name: str,
    tool_input: dict[str, Any],
    envelope_cwd: str,
) -> Decision:
    """Decide allow / deny / no-op for one PreToolUse Task fire.

    AC.AG.4: NORMAL USE workspaces short-circuit to no-op (cheap path).
    AC.AG.1: pos-v2 surface mentions + non-canonical cwd → deny.
    AC.AG.2: prompt length > 2500 chars → deny.
    AC.AG.3: amendment / AC mentions of an already-sealed scope → deny.
    """
    # Tool gate — only Task is inspected.
    if tool_name not in TOOLS_GATED:
        return Decision("no-op")

    prompt = tool_input.get("prompt")
    if not isinstance(prompt, str):
        return Decision("no-op")

    # AC.AG.4 — Mode-bit short circuit (DEV-MODE-only gate).
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    if mode != "dev-mode":
        return Decision("no-op")

    # AC.AG.1 — wrong-WD dispatch.
    surface_mentions = _detect_pos_v2_surface_mentions(prompt)
    if surface_mentions and not _is_canonical_cwd(envelope_cwd):
        reason = _reason_wrong_wd(envelope_cwd, surface_mentions)
        return Decision(
            "deny",
            reason=reason,
            failure_class="wrong-wd",
            matched=", ".join(surface_mentions[:5]),
        )

    # AC.AG.2 — method-enumerated prompt (length-only check).
    if len(prompt) > PROMPT_LENGTH_THRESHOLD:
        reason = _reason_method_enumerated(len(prompt))
        return Decision(
            "deny",
            reason=reason,
            failure_class="method-enumerated-prompt",
            matched=str(len(prompt)),
        )

    # AC.AG.3 — stale dispatch detection.
    amendment_numbers = _detect_amendment_numbers(prompt)
    ac_ids = _detect_ac_ids(prompt)
    if amendment_numbers or ac_ids:
        tracker = _open_tracker(workspace_root)
        # AC mentions: query manifest table.
        sealed_ac_hits: list[tuple[str, str]] = []
        if ac_ids and tracker is not None:
            for (comp_key, ac_suffix) in ac_ids:
                # The AC id format on disk is `AC.<X>.<Y>`. The
                # tracker's manifest_rows_for_ac expects component +
                # full ac_id; we query for both.
                full_ac = f"AC.{comp_key}.{ac_suffix}"
                # Component name in manifest is the framework
                # component slug, not the AC's component-key. Iterate
                # known components by trying common slugs that match
                # the AC's component-key heuristic.
                if _ac_is_sealed_anywhere(tracker, full_ac):
                    sealed_ac_hits.append((comp_key, ac_suffix))
        # Amendment-number mentions: git-log fallback.
        sealed_amendment_hits: list[tuple[int, str]] = []
        for n in amendment_numbers:
            sha = _amendment_seal_commit_for_number(workspace_root, n)
            if sha is not None:
                sealed_amendment_hits.append((n, sha))
        if sealed_ac_hits or sealed_amendment_hits:
            reason = _reason_stale_dispatch(
                sealed_amendment_hits, sealed_ac_hits
            )
            return Decision(
                "deny",
                reason=reason,
                failure_class="stale-dispatch",
                matched=_stale_matched_text(
                    sealed_amendment_hits, sealed_ac_hits
                ),
            )

    return Decision("allow")


def _ac_is_sealed_anywhere(tracker: Any, full_ac: str) -> bool:
    """True iff any component has a manifest row for ``full_ac``.

    Iterates the known component slugs from the tracker's manifest
    table — fall-back when the AC's component-key heuristic differs
    from the actual framework slug.
    """
    try:
        # Try the cheap path: query each known framework component.
        # The tracker doesn't expose a "list-all-components" surface
        # cheaply; we attempt the canonical set.
        candidate_components = (
            "hands-off-lifecycle",
            "objective-tracker",
            "orchestrator",
            "workspace-bootstrap",
            "primary-persona",
            "memory-system",
            "loam-mode",
            "safety-layer",
        )
        for comp in candidate_components:
            try:
                rows = tracker.manifest_rows_for_ac(comp, full_ac)
            except Exception:  # noqa: BLE001
                continue
            if rows:
                return True
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return False
    return False


def _stale_matched_text(
    sealed_amendment_hits: list[tuple[int, str]],
    sealed_ac_hits: list[tuple[str, str]],
) -> str:
    parts: list[str] = []
    for (n, sha) in sealed_amendment_hits:
        parts.append(f"#{n}@{sha[:8]}")
    for (k, s) in sealed_ac_hits:
        parts.append(f"AC.{k}.{s}")
    return ", ".join(parts)


# ---------------------------------------------------------------------
# Reason text builders (structured natural-language deny reasons)
# ---------------------------------------------------------------------


def _reason_wrong_wd(cwd: str, surface_mentions: list[str]) -> str:
    mentions_text = ", ".join(
        f"`{m}`" for m in surface_mentions[:5]
    ) or "(none captured)"
    return (
        f"AC.AG.1 (wrong-WD dispatch, DEV-MODE) — refused: the "
        f"dispatch prompt mentions pos-v2 dev surfaces ({mentions_text}) "
        f"but the parent session's `cwd` is `{cwd}`, not the canonical "
        f"pos-v2 path `{CANONICAL_LOAM_PATH}`. Per "
        f"`feedback_always_specify_wd_in_dispatches`, dispatches that "
        f"target pos-v2 surfaces from a non-canonical cwd produce "
        f"orphan commits in the wrong working tree. Repair "
        f"directions: (a) re-dispatch from a session whose `cwd` is "
        f"the canonical pos-v2 path; (b) if the dispatch is for a "
        f"derived workspace (pos3, eval clone), strip the pos-v2 "
        f"surface mentions from the prompt; (c) halt and surface to "
        f"the dispatcher."
    )


def _reason_method_enumerated(length: int) -> str:
    return (
        f"AC.AG.2 (method-enumerated prompt, DEV-MODE) — refused: "
        f"the dispatch prompt is {length} characters, exceeding the "
        f"named threshold of {PROMPT_LENGTH_THRESHOLD}. Per "
        f"`feedback_agent_prompts_scope_only`, scope-only dispatches "
        f"land at ~1000-2200 chars; method-enumerated content "
        f"(file/symbol/AC/layouts) belongs in the plan-doc, not the "
        f"dispatch. Repair directions: (a) extract method-enumerated "
        f"content into the plan-doc and reference it; (b) compress "
        f"the dispatch to objective + constraints + halt + ODD-check "
        f"only; (c) if the prompt genuinely needs to be long for a "
        f"non-method reason, surface a refinement of the threshold."
    )


def _reason_stale_dispatch(
    sealed_amendment_hits: list[tuple[int, str]],
    sealed_ac_hits: list[tuple[str, str]],
) -> str:
    amendment_lines = [
        f"`amendment #{n}` already sealed at commit `{sha[:8]}`"
        for (n, sha) in sealed_amendment_hits
    ]
    ac_lines = [
        f"`AC.{k}.{s}` already registered in the manifest table"
        for (k, s) in sealed_ac_hits
    ]
    bullets = "; ".join(amendment_lines + ac_lines)
    return (
        f"AC.AG.3 (stale dispatch, DEV-MODE) — refused: the dispatch "
        f"prompt re-targets sealed scope: {bullets}. Per "
        f"`feedback_verify_dispatch_before_sending`, re-dispatch of "
        f"already-sealed work duplicates audit history and produces "
        f"divergent rebuilds. Repair directions: (a) re-target to "
        f"the next-sequential amendment / un-sealed AC; (b) if the "
        f"intent is a corrective extension on a sealed amendment, "
        f"author a fresh corrective amendment plan; (c) halt and "
        f"surface to the dispatcher with the seal commit SHAs above."
    )


# ---------------------------------------------------------------------
# Audit log (AC.AG.5)
# ---------------------------------------------------------------------


def _append_audit_line(
    workspace_root: Path,
    *,
    tool_name: str,
    prompt_len: int,
    cwd: str,
    mode: str,
    decision: Decision,
) -> None:
    """Append one NDJSON line to A4's agent-guard audit log. Fail-soft.

    Schema mirrors A2/A3's per-fire shape with task-specific keys.
    The full prompt is NOT recorded (privacy + size); the prompt
    length is recorded.
    """
    payload = {
        "ts": _helpers.now_iso_z(),
        "tool": tool_name,
        "prompt_length": prompt_len,
        "cwd": cwd,
        "mode": mode,
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
        envelope_cwd=cwd,
    )

    prompt = tool_input.get("prompt")
    prompt_len = len(prompt) if isinstance(prompt, str) else 0
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)

    _append_audit_line(
        workspace_root,
        tool_name=tool_name,
        prompt_len=prompt_len,
        cwd=cwd,
        mode=mode,
        decision=decision,
    )

    if decision.decision == "deny" and decision.reason is not None:
        _emit_deny_response(decision.reason)
    else:
        _emit_allow_response()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
