"""PreToolUse gate — refuses Edit/Write/MultiEdit when the path does not
trace to a manifest-registered (component, ac_id, source_path_glob) row
that the active-scope sentinel binds against.

Added by structural-enforcement A2 (objective-binding gate). Refactored
in-place by structural-enforcement A3 (D-A3.7) to consume shared
helpers from ``_gate_helpers.py`` — A4 will inherit the same library.
The refactor is internal-only: every external symbol A2's tests reach
for is preserved as a module-level shim that delegates to the helper.

## Failure class closed by this hook (AC.OBG.1 .. AC.OBG.7)

A1 shipped the substrate (sentinel + manifest table + mode bit) but no
gate. A2 is the first amendment that turns the substrate into a deny.
After A2 lands, every Edit/Write/MultiEdit issued in a DEV MODE pos-v2
workspace either:

  - traces to a manifest row whose source_path_glob admits the path
    AND the active-scope sentinel binds the (component, ac_id) the row
    belongs to — the gate ALLOWS; OR
  - falls under a dev-discipline carve-out path (docs/, tools/,
    .scratch/, personas/, CLAUDE*.md, .gitignore, the universal-paths
    admissions) — the gate ALLOWS regardless of sentinel state; OR
  - is denied with a structured ``permissionDecisionReason`` that
    names the failing check + at least one repair direction.

NORMAL USE workspaces no-op the gate at the mode-bit short circuit
(D-A2.5 / programme D4 lock — A2 is ODD-discipline, DEV-MODE-only).

## Surface contract

CLI entry reads the Claude Code PreToolUse JSON envelope from stdin:

  {
    "session_id": "...",
    "cwd": "<workspace_root>",
    "hook_event_name": "PreToolUse",
    "tool_name": "Edit" | "Write" | "MultiEdit",
    "tool_input": { "file_path": "...", ... }
  }

Writes one of two JSON shapes to stdout:

  - allow: empty stdout (default-allow per Claude Code's
    PreToolUse contract — no ``permissionDecision`` key); OR
  - deny:  {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": "deny",
                                   "permissionDecisionReason": "<text>"}}

Exits 0 on every path. Refusals route through the structured JSON
surface, never through exit code 2 — that is documented but less
structured (research §3.2).

## Audit log (AC.OBG.7)

Every fire (allow / deny / no-op / error) appends one NDJSON line to
``<workspace>/workspace/.pos/objective-binding-gate.log``. Atomic
append via ``os.O_APPEND`` + write of one line — POSIX guarantees
single-write atomicity for writes shorter than ``PIPE_BUF`` (typically
4 KB; a single decision row is well under that).

Stdlib only (json, fnmatch, pathlib, os, sys, time) plus shared
``_gate_helpers``. objective-tracker imported lazily inside the
helper's ``open_tracker_or_none`` so an environment without the shared
venv on path still falls through to allow (fail-closed-to-permissive
at the import boundary; the gate's deny path requires the substrate
to be reachable).
"""

from __future__ import annotations

import fnmatch
import json
import sys
from pathlib import Path
from typing import Any


# Ensure sibling modules (active_scope_sentinel, corpus_load_sentinel,
# _gate_helpers) are importable when this script is invoked directly as
# ``python <hooks-dir>/objective_binding_gate.py``.
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
# Module-level shims preserved for A2's existing test imports + A3's
# regression equivalence (AC.TDG.8).
#
# A2's tests reach into module privates: ``gate._audit_log_path``,
# ``gate._is_carve_out_path``, ``gate._workspace_relative``, etc. The
# helper-extraction refactor must not break those imports — D-A3.7's
# regression contract is byte-for-byte. The shims below delegate to
# ``_gate_helpers`` while preserving every name A2's test surface
# touched.
# ---------------------------------------------------------------------

WORKSPACE_STATE_SUBDIR = _helpers.WORKSPACE_STATE_SUBDIR
POS_SUBDIR = _helpers.POS_SUBDIR
AUDIT_LOG_FILENAME = "objective-binding-gate.log"

_CARVE_OUT_PREFIXES = _helpers._CARVE_OUT_PREFIXES
_CARVE_OUT_FILES = _helpers._CARVE_OUT_FILES

TOOLS_GATED = ("Edit", "Write", "MultiEdit")


def _is_carve_out_path(workspace_relative_path: str) -> bool:
    """Module-level shim → ``_gate_helpers.is_carve_out_path``."""
    return _helpers.is_carve_out_path(workspace_relative_path)


def _workspace_relative(
    file_path: str, workspace_root: Path
) -> str | None:
    """Module-level shim → ``_gate_helpers.workspace_relative``."""
    return _helpers.workspace_relative(file_path, workspace_root)


def _open_tracker(workspace_root: Path) -> Any | None:
    """Module-level shim → ``_gate_helpers.open_tracker_or_none``."""
    return _helpers.open_tracker_or_none(workspace_root)


def _audit_log_path(workspace_root: Path) -> Path:
    """Module-level shim → ``_gate_helpers.audit_log_path``."""
    return _helpers.audit_log_path(workspace_root, AUDIT_LOG_FILENAME)


# ---------------------------------------------------------------------
# Decision (the hook's outcome)
# ---------------------------------------------------------------------


class Decision:
    """Tiny container for a gate decision.

    Not a dataclass — keeping the audit-log shape decoupled from any
    library-level type. ``decision`` is one of {"allow", "deny",
    "no-op"}. ``reason`` is the structured deny reason (None on allow /
    no-op). ``failure_class`` is one of:
    {"missing-sentinel", "no-manifest-row-for-binding",
     "no-glob-matches-path", None}.
    """

    __slots__ = ("decision", "reason", "failure_class", "bound_acs")

    def __init__(
        self,
        decision: str,
        *,
        reason: str | None = None,
        failure_class: str | None = None,
        bound_acs: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self.decision = decision
        self.reason = reason
        self.failure_class = failure_class
        self.bound_acs = bound_acs


def evaluate(
    *,
    workspace_root: Path,
    tool_name: str,
    tool_input: dict[str, Any],
) -> Decision:
    """Decide allow / deny / no-op for one PreToolUse fire.

    Caller supplies the resolved workspace_root + the tool envelope
    fields. Returns a ``Decision`` carrying the outcome + reason.

    AC.OBG.6: NORMAL USE workspaces short-circuit to no-op (the cheap
    path; mode-bit read only).
    AC.OBG.5: dev-discipline carve-outs admit regardless of sentinel.
    AC.OBG.1: missing sentinel → deny.
    AC.OBG.2: sentinel binds AC with no manifest row → deny.
    AC.OBG.3: no row's glob matches → deny.
    AC.OBG.4: at least one bound row's glob matches → allow.
    """
    # Mode-bit short circuit (AC.OBG.6).
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    if mode != "dev-mode":
        return Decision("no-op")

    # Tool gate — only Edit / Write / MultiEdit are inspected.
    if tool_name not in TOOLS_GATED:
        return Decision("no-op")

    # Resolve file_path. MultiEdit / Edit / Write all carry a single
    # ``file_path`` at tool_input top-level (MultiEdit operates on ONE
    # file with multiple edits; Q1 empirical answer recorded in §14).
    raw_path = tool_input.get("file_path")
    if not isinstance(raw_path, str) or not raw_path:
        return Decision("no-op")

    rel_path = _helpers.workspace_relative(raw_path, workspace_root)
    if rel_path is None:
        # Foreign path (outside workspace_root). The gate's scope is
        # workspace-relative; no manifest row can bind such a path.
        # Fall through to allow — this matches R8 ("path-canonicalisation
        # bugs") mitigation: out-of-workspace paths are not gated by A2.
        return Decision("allow")

    # Carve-out (AC.OBG.5) — first check, so dev-discipline edits
    # admit regardless of sentinel/manifest state.
    if _helpers.is_carve_out_path(rel_path):
        return Decision("allow")

    # Read the active-scope sentinel (AC.OBG.1).
    sentinel = _helpers.read_active_scope_sentinel_or_none(workspace_root)

    if sentinel is None:
        return Decision(
            "deny",
            failure_class="missing-sentinel",
            reason=_reason_missing_sentinel(rel_path),
        )

    # Resolve the tracker. Lazy import so the venv path-fix runs only
    # when the gate reaches the manifest-query branch. The call goes
    # through the module-level shim so test fixtures can patch
    # ``gate._open_tracker`` (the convention A2's existing tests use).
    tracker = _open_tracker(workspace_root)
    if tracker is None:
        # Substrate unreachable. Fail-closed-to-permissive at the
        # import boundary — no manifest substrate means no binding can
        # be verified; allow rather than mass-deny on environment
        # misconfiguration. The audit-log records the failure.
        return Decision("allow")

    # AC.OBG.2 + AC.OBG.3 — collect every manifest row reachable through
    # the sentinel's bindings; check whether any row's glob matches.
    bound_acs = tuple(
        (b.component, b.ac_id) for b in sentinel.bindings
    )
    rows_per_binding: list[tuple[tuple[str, str], list[dict[str, Any]]]] = []
    for binding in sentinel.bindings:
        rows = tracker.manifest_rows_for_ac(
            binding.component, binding.ac_id
        )
        rows_per_binding.append(((binding.component, binding.ac_id), rows))

    if not any(rows for (_pair, rows) in rows_per_binding):
        # AC.OBG.2 — every binding has zero rows.
        return Decision(
            "deny",
            failure_class="no-manifest-row-for-binding",
            reason=_reason_no_manifest_row(rel_path, bound_acs),
            bound_acs=bound_acs,
        )

    # AC.OBG.3 + AC.OBG.4 — search bound rows for a glob matching path.
    matched = False
    bound_globs: list[tuple[str, str, str]] = []
    for ((comp, ac_id), rows) in rows_per_binding:
        for row in rows:
            glob = row.get("source_path_glob", "")
            if not isinstance(glob, str):
                continue
            bound_globs.append((comp, ac_id, glob))
            if fnmatch.fnmatchcase(rel_path, glob):
                matched = True
                break
        if matched:
            break

    if matched:
        return Decision("allow", bound_acs=bound_acs)

    return Decision(
        "deny",
        failure_class="no-glob-matches-path",
        reason=_reason_no_glob_matches(rel_path, bound_globs),
        bound_acs=bound_acs,
    )


# ---------------------------------------------------------------------
# Reason text builders (structured natural-language deny reasons)
# ---------------------------------------------------------------------


def _reason_missing_sentinel(rel_path: str) -> str:
    return (
        f"ODD §2.5 — file `{rel_path}` cannot be edited: the active-"
        f"scope sentinel is absent (workspace/.pos/active-scope.json "
        f"not present). Repair directions: (a) if this is a docs/ / "
        f"plans/ / CLAUDE*.md / personas/ / .scratch/ edit, retry on "
        f"a path that matches one of those carve-outs; (b) if this is "
        f"a sealed-component source edit, the dispatcher should have "
        f"authored the active-scope sentinel before the build agent "
        f"started — author it via the dispatch wrapper or "
        f"hands-off-lifecycle.hooks.active_scope_sentinel."
        f"write_active_scope_sentinel(...); (c) if this edit is not "
        f"part of an active scope, halt and surface to the dispatcher."
    )


def _reason_no_manifest_row(
    rel_path: str, bound_acs: tuple[tuple[str, str], ...]
) -> str:
    pairs = ", ".join(f"({c}, {a})" for (c, a) in bound_acs) or "(none)"
    return (
        f"ODD §2.5 — file `{rel_path}` cannot be edited: the active-"
        f"scope sentinel binds {pairs} but no manifest row exists for "
        f"any of those (component, ac_id) pairs. Repair direction: "
        f"register the row(s) before the first edit via "
        f"`tracker.register_source_binding(component=..., ac_id=..., "
        f"source_path_glob=...)`; this is the build agent's "
        f"authoring discipline (every AC's source-path-glob is "
        f"registered at build start)."
    )


def _reason_no_glob_matches(
    rel_path: str, bound_globs: list[tuple[str, str, str]]
) -> str:
    if bound_globs:
        glob_text = "; ".join(
            f"({c}, {a}, `{g}`)" for (c, a, g) in bound_globs
        )
    else:
        glob_text = "(none)"
    return (
        f"ODD §2.5 — file `{rel_path}` does not match any glob bound "
        f"by the active-scope sentinel. Bound (component, ac_id, "
        f"source_path_glob) tuples: {glob_text}. Repair directions: "
        f"(a) retry on a path matching one of the bound globs; (b) "
        f"if this edit belongs in the active scope but the manifest "
        f"row is too narrow, register a wider glob via "
        f"`tracker.register_source_binding(...)`; (c) if this edit "
        f"belongs in a sibling scope, halt and surface to the "
        f"dispatcher — silently extending the sentinel hides drift."
    )


# ---------------------------------------------------------------------
# Audit log (AC.OBG.7) — module-level shim around helper writer.
# ---------------------------------------------------------------------


def _append_audit_line(
    workspace_root: Path,
    *,
    tool_name: str,
    raw_path: str,
    rel_path: str | None,
    mode: str,
    sentinel_state: str,
    decision: Decision,
) -> None:
    """Append one NDJSON line to the audit log. Fail-soft.

    Format: ``{ts, tool, path, rel_path, mode, sentinel_state,
    bound_acs, decision, failure_class, reason}``.

    AC.OBG.7: deterministic surface, append-only, atomic single-line
    writes (POSIX O_APPEND with a payload < PIPE_BUF). Path / format
    are method per ODD §7.4.

    Refactored in A3: shape preserved byte-for-byte (every key still
    written); the actual I/O is delegated to
    ``_gate_helpers.append_audit_line`` which carries the atomic-
    append + fail-soft logic shared with A3.
    """
    payload = {
        "ts": _helpers.now_iso_z(),
        "tool": tool_name,
        "path": raw_path,
        "rel_path": rel_path,
        "mode": mode,
        "sentinel_state": sentinel_state,
        "bound_acs": [
            {"component": c, "ac_id": a} for (c, a) in decision.bound_acs
        ],
        "decision": decision.decision,
        "failure_class": decision.failure_class,
        "reason": decision.reason,
    }
    _helpers.append_audit_line(workspace_root, AUDIT_LOG_FILENAME, payload)


# ---------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------


def _emit_allow_response() -> None:
    """Allow path: emit empty stdout (Claude Code's default-allow)."""
    return


def _emit_deny_response(reason: str) -> None:
    """Deny path: emit the structured PreToolUse deny envelope."""
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

    Fail-soft on every environmental / parse failure (no envelope, no
    JSON, missing fields) — the gate must never break a session by
    raising into Claude Code. The cheap path (mode = normal-use) exits
    well under 10ms; the deny path exits under 100ms p95.
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

    raw_path = tool_input.get("file_path")
    if not isinstance(raw_path, str):
        raw_path = ""

    decision = evaluate(
        workspace_root=workspace_root,
        tool_name=tool_name,
        tool_input=tool_input,
    )

    # Compute audit-log fields (best-effort; never raises into Claude).
    rel_path = (
        _helpers.workspace_relative(raw_path, workspace_root)
        if raw_path
        else None
    )
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    sentinel_state = (
        "present"
        if _helpers.read_active_scope_sentinel_or_none(workspace_root)
        is not None
        else "absent"
    )

    _append_audit_line(
        workspace_root,
        tool_name=tool_name,
        raw_path=raw_path,
        rel_path=rel_path,
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
