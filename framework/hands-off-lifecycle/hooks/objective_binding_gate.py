"""PreToolUse gate — refuses Edit/Write/MultiEdit when the path does not
trace to a manifest-registered (component, ac_id, source_path_glob) row
that the active-scope sentinel binds against.

Added by structural-enforcement A2 (objective-binding gate). Consumes
A1's substrate (active-scope sentinel reader, objective-manifest
queries, workspace-mode bit) — read-only against every A1 surface.

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
append via ``open(..., "a")`` + write of one line — POSIX guarantees
single-write atomicity for writes shorter than ``PIPE_BUF`` (typically
4 KB; a single decision row is well under that).

Stdlib only (json, fnmatch, pathlib, os, sys, time). objective-tracker
imported lazily inside the decision path so an environment without the
shared venv on path still falls through to allow (fail-closed-to-
permissive at the import boundary; the gate's deny path requires the
substrate to be reachable).
"""

from __future__ import annotations

import fnmatch
import json
import os
import sys
import time
from pathlib import Path
from typing import Any


# Ensure sibling modules (active_scope_sentinel, corpus_load_sentinel)
# are importable when this script is invoked directly as
# ``python <hooks-dir>/objective_binding_gate.py``.
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


# D-migration D.2 (amendment #63): workspace-state lives under
# ``<workspace>/workspace/`` post-D.2. Hook scripts duplicate the
# constant per stdlib-only contract (canonical source:
# ``framework/workspace-bootstrap/src/workspace_bootstrap/
# workspace_paths.py`` ``WORKSPACE_STATE_SUBDIR``).
WORKSPACE_STATE_SUBDIR = "workspace"
POS_SUBDIR = ".pos"
AUDIT_LOG_FILENAME = "objective-binding-gate.log"

TOOLS_GATED = ("Edit", "Write", "MultiEdit")


# ---------------------------------------------------------------------
# Carve-out path list (D-A2.6 — D1 dev-discipline)
# ---------------------------------------------------------------------
#
# Workspace-relative path PREFIXES that admit edits regardless of
# sentinel state. Per AC.OBG.5: paths under any of these admit allow
# in DEV MODE. The list is union of pre-D-migration + post-D-migration
# shapes per locked plan §D-A2.6 (the migration window admits both).
#
# The list is expansive by design — false-deny on operator dev-
# discipline edits would erode trust in the gate. Method per ODD §7.4
# is "prefix match against workspace-relative path"; ordering does not
# affect correctness because the predicate is OR over prefixes.
_CARVE_OUT_PREFIXES: tuple[str, ...] = (
    "docs/",
    "tools/",
    ".scratch/",
    "personas/",
    "framework/docs/",
    "framework/tools/",
    "framework/personas/",
)

# Workspace-relative path FILES (exact match) admitted regardless of
# sentinel. Includes CLAUDE*.md at root, framework root, and the
# universal-paths admissions used in pos-amend manifests.
_CARVE_OUT_FILES: frozenset[str] = frozenset(
    {
        "CLAUDE.md",
        "CLAUDE.dev.md",
        "framework/CLAUDE.md",
        "framework/CLAUDE.dev.md",
        ".gitignore",
        "framework/.gitignore",
        "docs/odd-methodology.md",
        "docs/odd-in-pos.md",
        "docs/rebuild/FUTURE_IDEAS.md",
        "docs/rebuild/FUTURE_IDEAS_DRAFT.md",
    }
)


def _is_carve_out_path(workspace_relative_path: str) -> bool:
    """True iff ``workspace_relative_path`` is a dev-discipline carve-
    out admitted by AC.OBG.5 regardless of sentinel state.

    Method per ODD §7.4: prefix-match for tree carve-outs + exact-match
    for file admissions. Path is workspace-relative, forward-slash
    separated.
    """
    if workspace_relative_path in _CARVE_OUT_FILES:
        return True
    for prefix in _CARVE_OUT_PREFIXES:
        if workspace_relative_path.startswith(prefix):
            return True
    return False


# ---------------------------------------------------------------------
# Path canonicalisation (R8 mitigation)
# ---------------------------------------------------------------------


def _workspace_relative(
    file_path: str, workspace_root: Path
) -> str | None:
    """Canonicalise ``file_path`` to a workspace-relative POSIX-style
    string, OR return None when the path is not under workspace_root.

    Per R8: tool_input.file_path may be absolute or relative. Resolve
    both via ``Path.resolve()`` then compute the relative path. Returns
    None when the path lies outside the workspace (the gate's scope is
    workspace-relative; foreign paths are not gated — they fall through
    to allow because no manifest row can match a non-workspace path).
    """
    try:
        p = Path(file_path)
        if not p.is_absolute():
            p = workspace_root / p
        p_resolved = p.resolve()
        ws_resolved = workspace_root.resolve()
        rel = p_resolved.relative_to(ws_resolved)
    except (ValueError, OSError):
        return None
    return rel.as_posix()


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
    try:
        from corpus_load_sentinel import workspace_mode

        mode = workspace_mode(workspace_root)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        mode = "normal-use"
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

    rel_path = _workspace_relative(raw_path, workspace_root)
    if rel_path is None:
        # Foreign path (outside workspace_root). The gate's scope is
        # workspace-relative; no manifest row can bind such a path.
        # Fall through to allow — this matches R8 ("path-canonicalisation
        # bugs") mitigation: out-of-workspace paths are not gated by A2.
        return Decision("allow")

    # Carve-out (AC.OBG.5) — first check, so dev-discipline edits
    # admit regardless of sentinel/manifest state.
    if _is_carve_out_path(rel_path):
        return Decision("allow")

    # Read the active-scope sentinel (AC.OBG.1).
    try:
        from active_scope_sentinel import read_active_scope_sentinel

        sentinel = read_active_scope_sentinel(workspace_root)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        sentinel = None

    if sentinel is None:
        return Decision(
            "deny",
            failure_class="missing-sentinel",
            reason=_reason_missing_sentinel(rel_path),
        )

    # Resolve the tracker. Lazy import so the venv path-fix runs only
    # when the gate reaches the manifest-query branch.
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
# Tracker open
# ---------------------------------------------------------------------


def _open_tracker(workspace_root: Path) -> Any | None:
    """Open the workspace's ObjectiveTracker, or return None on failure.

    Lazy import + venv path-fix so a system-Python-invoked hook script
    can still reach the shared venv's installed objective_tracker
    package (matching the existing hands-off-lifecycle convention in
    first_run_helper.py / corpus_load_sentinel.py).
    """
    try:
        venv_lib = workspace_root / ".venv" / "lib"
        if venv_lib.is_dir():
            for site_dir in venv_lib.iterdir():
                site_pkgs = site_dir / "site-packages"
                if site_pkgs.is_dir() and str(site_pkgs) not in sys.path:
                    sys.path.insert(0, str(site_pkgs))
        from objective_tracker import ObjectiveTracker  # type: ignore[import-not-found]
        from workspace_bootstrap.workspace_paths import (  # type: ignore[import-not-found]
            tracker_db_path,
        )

        db_path = tracker_db_path(workspace_root)
        if not db_path.exists():
            return None
        return ObjectiveTracker(db_path)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return None


# ---------------------------------------------------------------------
# Audit log (AC.OBG.7)
# ---------------------------------------------------------------------


def _audit_log_path(workspace_root: Path) -> Path:
    return (
        workspace_root
        / WORKSPACE_STATE_SUBDIR
        / POS_SUBDIR
        / AUDIT_LOG_FILENAME
    )


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
    """
    payload = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
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
    target = _audit_log_path(workspace_root)
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
    encoded = line.encode("utf-8")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        # O_APPEND atomicity for writes < PIPE_BUF (POSIX). Single
        # NDJSON row is well under that boundary.
        fd = os.open(
            target, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644
        )
        try:
            os.write(fd, encoded)
        finally:
            os.close(fd)
    except OSError:
        # Fail-soft per the surrounding hooks convention; log failure
        # must never block the gate decision.
        return


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
    rel_path = _workspace_relative(raw_path, workspace_root) if raw_path else None
    try:
        from corpus_load_sentinel import workspace_mode

        mode = workspace_mode(workspace_root)
    except Exception:  # noqa: BLE001 — fail-soft
        mode = "normal-use"
    try:
        from active_scope_sentinel import read_active_scope_sentinel

        sentinel_state = (
            "present"
            if read_active_scope_sentinel(workspace_root) is not None
            else "absent"
        )
    except Exception:  # noqa: BLE001 — fail-soft
        sentinel_state = "absent"

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
