"""PreToolUse gate — refuses Edit/Write/MultiEdit when a NEW AC bound
by the active-scope sentinel lacks a backing test on disk.

Added by structural-enforcement A3 (TDD-guard). Composes with A2's
objective-binding gate in the PreToolUse hook chain: A2 admits the
path (the path traces to a manifest-registered binding the sentinel
admits); A3 then verifies the additional invariant — every NEW AC in
this diff has a test pinned to its filename + function-name
convention.

## Failure class closed by this hook (AC.TDG.1 .. AC.TDG.7)

A1 + A2 close the binding gap: source edits trace back to a (component,
ac_id) the sentinel admits. A3 closes the test-pinning gap: source
edits introducing code for a NEW AC must have a test for that AC
already on disk.

After A3 lands, every Edit/Write/MultiEdit issued in a DEV MODE pos-v2
workspace either:

  - has no NEW AC in scope (the sentinel binds only existing ACs whose
    manifest rows pre-date the sentinel) — A3 ALLOWS; OR
  - is on a test-tree path (``framework/<comp>/tests/**``) — A3 ALLOWS
    (chicken-and-egg avoidance); OR
  - has at least one NEW AC in scope, AND a file matching
    ``framework/<comp>/tests/test_AC_<Y-normalised>_*.py`` exists AND
    contains a function whose name starts with
    ``test_AC_<Y-normalised>_`` — A3 ALLOWS; OR
  - has at least one NEW AC in scope with no matching test file →
    A3 DENIES with structured reason naming the missing test path; OR
  - has at least one NEW AC in scope with a matching test file but no
    matching function → A3 DENIES with structured reason naming the
    file + the expected function-name pattern.

NORMAL USE workspaces no-op the gate at the mode-bit short circuit
(D-A3.6 / programme D4 lock — A3 is ODD-discipline, DEV-MODE-only).

## Surface contract

Reads the same Claude Code PreToolUse JSON envelope from stdin as A2.
Writes one of two JSON shapes to stdout (allow = empty; deny =
structured envelope). Exits 0 on every path.

## Hook-chain ordering (D-A3.8)

A3 runs AFTER A2 in settings.json. A2's deny short-circuits A3
(Claude Code stops the chain on the first deny). A3 nevertheless runs
the full decision chain (defensive duplication of mode + carve-out +
sentinel-presence checks) so the gate is self-contained against
hook-chain reordering, A2 removal, and asymmetric carve-out lists.
The duplicated work is sub-millisecond.

## Audit log (AC.TDG.7)

Every fire (allow / deny / no-op / error) appends one NDJSON line to
``<workspace>/workspace/.pos/tdd-guard.log``. Atomic append via POSIX
O_APPEND for writes < PIPE_BUF.

Stdlib only (json, fnmatch, pathlib, os, re, sys, time) plus shared
``_gate_helpers``.
"""

from __future__ import annotations

import fnmatch
import json
import re
import sys
from pathlib import Path
from typing import Any


# Ensure sibling modules are importable when invoked as a standalone
# script (``python <hooks-dir>/tdd_guard.py``).
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
# Module-level shims (mirror A2's pattern; tests monkeypatch these).
# ---------------------------------------------------------------------

WORKSPACE_STATE_SUBDIR = _helpers.WORKSPACE_STATE_SUBDIR
POS_SUBDIR = _helpers.POS_SUBDIR
AUDIT_LOG_FILENAME = "tdd-guard.log"

TOOLS_GATED = ("Edit", "Write", "MultiEdit")


def _is_carve_out_path(workspace_relative_path: str) -> bool:
    return _helpers.is_carve_out_path(workspace_relative_path)


def _workspace_relative(
    file_path: str, workspace_root: Path
) -> str | None:
    return _helpers.workspace_relative(file_path, workspace_root)


def _open_tracker(workspace_root: Path) -> Any | None:
    return _helpers.open_tracker_or_none(workspace_root)


def _audit_log_path(workspace_root: Path) -> Path:
    return _helpers.audit_log_path(workspace_root, AUDIT_LOG_FILENAME)


# ---------------------------------------------------------------------
# AC normalisation rule (D-A3.9 default per locked plan §6)
# ---------------------------------------------------------------------
#
# `AC.OBG.1` → `OBG_1`; `AC.SE.S` → `SE_S`; `AC.A8.A` → `A8_A`.
# Drop leading `AC.` if present; replace `.` with `_`; uppercase.
# Method per ODD §7.4 — verified empirically at build start by reading
# existing test names: every `framework/*/tests/test_AC_*.py` follows
# the dotted-AC-id-with-dots-replaced convention.


def _normalise_ac_id(ac_id: str) -> str:
    """Normalise an AC ID to the test-file/function naming form.

    Drops a leading ``AC.`` prefix (case-insensitive); replaces every
    ``.`` with ``_``; uppercases. The output is suitable for both the
    file-glob (``test_AC_<normalised>_*.py``) and the function-name
    prefix (``test_AC_<normalised>_``).
    """
    s = ac_id
    if s[:3].lower() == "ac.":
        s = s[3:]
    s = s.replace(".", "_")
    return s.upper()


def _expected_test_glob(component: str, ac_id: str) -> str:
    """Workspace-relative glob the gate expects the test file to match.

    Returns the POSIX-style glob ``framework/<comp>/tests/
    test_AC_<normalised>_*.py``.
    """
    return (
        f"framework/{component}/tests/"
        f"test_AC_{_normalise_ac_id(ac_id)}_*.py"
    )


def _function_prefix(ac_id: str) -> str:
    """Function-name prefix the gate expects inside a matching test
    file."""
    return f"test_AC_{_normalise_ac_id(ac_id)}_"


def _find_matching_test_files(
    workspace_root: Path, component: str, ac_id: str
) -> list[Path]:
    """Return every test file in ``framework/<component>/tests/``
    matching the AC's expected glob.

    Recurses into subdirectories under ``tests/`` (e.g. integration/
    sub-trees). Returns absolute Paths. Empty list when no file
    matches OR when the tests directory itself does not exist.
    """
    tests_dir = workspace_root / "framework" / component / "tests"
    if not tests_dir.is_dir():
        return []
    pattern_filename = f"test_AC_{_normalise_ac_id(ac_id)}_*.py"
    matches: list[Path] = []
    # rglob covers tests/ AND nested subdirs (tests/integration/, etc.).
    for p in tests_dir.rglob(pattern_filename):
        if p.is_file():
            matches.append(p)
    return matches


def _file_contains_matching_function(
    test_file: Path, ac_id: str
) -> bool:
    """True iff ``test_file`` defines a function whose name starts
    with the AC's expected prefix.

    Regex over file source text (no AST parse) per builder D-build.4:
    pattern is ``^def\\s+test_AC_<NORM>_\\w*\\s*\\(`` (multiline). False
    positives (a string literal containing the pattern) are vanishingly
    rare and harmless — false-positive direction is "allow" (the
    softer outcome).
    """
    try:
        source = test_file.read_text(encoding="utf-8")
    except OSError:
        return False
    pattern = (
        r"^def\s+" + re.escape(_function_prefix(ac_id)) + r"\w*\s*\("
    )
    return re.search(pattern, source, re.MULTILINE) is not None


# ---------------------------------------------------------------------
# Decision (the hook's outcome)
# ---------------------------------------------------------------------


class Decision:
    """Tiny container for a TDD-guard decision.

    ``decision`` is one of {"allow", "deny", "no-op"}.
    ``failure_class`` is one of:
    {"missing-test-file", "missing-test-function", None}.
    """

    __slots__ = (
        "decision",
        "reason",
        "failure_class",
        "bound_acs",
        "new_acs_in_scope",
        "tests_present",
        "tests_missing",
    )

    def __init__(
        self,
        decision: str,
        *,
        reason: str | None = None,
        failure_class: str | None = None,
        bound_acs: tuple[tuple[str, str], ...] = (),
        new_acs_in_scope: tuple[tuple[str, str], ...] = (),
        tests_present: tuple[tuple[str, str], ...] = (),
        tests_missing: tuple[tuple[str, str], ...] = (),
    ) -> None:
        self.decision = decision
        self.reason = reason
        self.failure_class = failure_class
        self.bound_acs = bound_acs
        self.new_acs_in_scope = new_acs_in_scope
        # tests_present: tuple of (ac_id, test_path) pairs.
        # tests_missing: tuple of (ac_id, expected_test_glob) pairs.
        self.tests_present = tests_present
        self.tests_missing = tests_missing


def evaluate(
    *,
    workspace_root: Path,
    tool_name: str,
    tool_input: dict[str, Any],
) -> Decision:
    """Decide allow / deny / no-op for one PreToolUse fire.

    AC.TDG.6: NORMAL USE workspaces short-circuit to no-op (cheap path).
    AC.TDG.3: test-tree paths (``framework/<comp>/tests/**``) allow
    regardless of new-AC state.
    AC.TDG.4: NEW AC means a manifest row's created_at is strictly
    after the sentinel's created_at. ACs that do not satisfy this are
    treated as in-AC modifications — A3 allows.
    AC.TDG.1: NEW AC + no matching test file → deny.
    AC.TDG.2: NEW AC + matching file present + no matching function →
    deny.
    AC.TDG.5: NEW AC + matching file + matching function → allow.

    Defensive duplication of A2's mode + carve-out + sentinel-presence
    checks per D-A3.8: A3 is self-contained against hook-chain
    reordering or A2 removal.
    """
    # AC.TDG.6 — Mode-bit short circuit.
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    if mode != "dev-mode":
        return Decision("no-op")

    # Tool gate — only Edit / Write / MultiEdit are inspected.
    if tool_name not in TOOLS_GATED:
        return Decision("no-op")

    raw_path = tool_input.get("file_path")
    if not isinstance(raw_path, str) or not raw_path:
        return Decision("no-op")

    rel_path = _workspace_relative(raw_path, workspace_root)
    if rel_path is None:
        # Foreign path (outside workspace_root). Out of A3's gate
        # scope; allow.
        return Decision("allow")

    # Carve-out (mirrors A2's AC.OBG.5 — defensive duplication).
    if _is_carve_out_path(rel_path):
        return Decision("allow")

    # AC.TDG.3 — test-tree path → allow (chicken-and-egg avoidance).
    # Match ``framework/<comp>/tests/**``: any path whose components
    # include a ``tests`` segment immediately under ``framework/<comp>/``.
    if _is_test_tree_path(rel_path):
        return Decision("allow")

    # Read the active-scope sentinel. Defensive duplication of
    # AC.OBG.1 — when A2 has already admitted (or A3 runs without A2),
    # missing sentinel falls through to allow because A3's deny class
    # is test-pinning, not binding-presence.
    sentinel = _read_active_scope_sentinel_or_none(workspace_root)
    if sentinel is None:
        # A2 would have denied here on the same path; A3's defensive
        # fallback is to allow (don't double-deny on the same failure
        # class). The audit log records the absent sentinel.
        return Decision("allow")

    bound_acs = tuple(
        (b.component, b.ac_id) for b in sentinel.bindings
    )

    tracker = _open_tracker(workspace_root)
    if tracker is None:
        # Substrate unreachable. Fail-closed-to-permissive — allow,
        # mirror A2's R7 envelope.
        return Decision("allow", bound_acs=bound_acs)

    # AC.TDG.4 — partition bindings into "new-in-this-diff" vs
    # "existing". A binding is NEW iff at least one of its manifest
    # rows has created_at strictly after the sentinel's created_at.
    sentinel_created_at = sentinel.created_at
    new_acs: list[tuple[str, str]] = []
    glob_matches_new_ac: list[tuple[str, str]] = []
    for binding in sentinel.bindings:
        rows = tracker.manifest_rows_for_ac(
            binding.component, binding.ac_id
        )
        is_new = False
        path_admitted_by_new_row = False
        for row in rows:
            row_created_at = row.get("created_at")
            if (
                isinstance(row_created_at, str)
                and row_created_at > sentinel_created_at
            ):
                is_new = True
                glob = row.get("source_path_glob", "")
                if isinstance(glob, str) and fnmatch.fnmatchcase(
                    rel_path, glob
                ):
                    path_admitted_by_new_row = True
        if is_new:
            new_acs.append((binding.component, binding.ac_id))
            # AC.TDG.1 / AC.TDG.5 only fire on bindings whose row
            # admits the path (a different AC's source-glob isn't
            # gating the current edit). When NO new-AC row admits the
            # path, the edit is for an EXISTING AC — A3 allows.
            if path_admitted_by_new_row:
                glob_matches_new_ac.append(
                    (binding.component, binding.ac_id)
                )

    new_acs_in_scope = tuple(new_acs)

    # AC.TDG.4 — no NEW AC admits this path → allow (existing-AC
    # modification or no-new-AC edit).
    if not glob_matches_new_ac:
        return Decision("allow", bound_acs=bound_acs, new_acs_in_scope=new_acs_in_scope)

    # AC.TDG.1 + AC.TDG.2 + AC.TDG.5 — for each new AC whose glob
    # admits this path, the test must exist (file + function).
    tests_present: list[tuple[str, str]] = []
    tests_missing_file: list[tuple[str, str]] = []
    tests_missing_function: list[tuple[str, str]] = []
    files_for_missing_function: list[tuple[str, str]] = []
    for (component, ac_id) in glob_matches_new_ac:
        candidate_files = _find_matching_test_files(
            workspace_root, component, ac_id
        )
        if not candidate_files:
            tests_missing_file.append(
                (ac_id, _expected_test_glob(component, ac_id))
            )
            continue
        # File(s) present — at least one must contain a matching
        # function for AC.TDG.5 to admit.
        any_function_match = False
        for test_file in candidate_files:
            if _file_contains_matching_function(test_file, ac_id):
                any_function_match = True
                rel_test = _workspace_relative(
                    str(test_file), workspace_root
                )
                tests_present.append((ac_id, rel_test or str(test_file)))
                break
        if not any_function_match:
            tests_missing_function.append(
                (ac_id, _function_prefix(ac_id))
            )
            files_for_missing_function.extend(
                (
                    ac_id,
                    _workspace_relative(str(p), workspace_root)
                    or str(p),
                )
                for p in candidate_files
            )

    # AC.TDG.1 — at least one new AC has no matching file → deny.
    if tests_missing_file:
        reason = _reason_missing_test_file(
            rel_path, tests_missing_file
        )
        return Decision(
            "deny",
            reason=reason,
            failure_class="missing-test-file",
            bound_acs=bound_acs,
            new_acs_in_scope=new_acs_in_scope,
            tests_present=tuple(tests_present),
            tests_missing=tuple(tests_missing_file),
        )

    # AC.TDG.2 — files present but no matching function → deny.
    if tests_missing_function:
        reason = _reason_missing_test_function(
            rel_path,
            tests_missing_function,
            files_for_missing_function,
        )
        return Decision(
            "deny",
            reason=reason,
            failure_class="missing-test-function",
            bound_acs=bound_acs,
            new_acs_in_scope=new_acs_in_scope,
            tests_present=tuple(tests_present),
            tests_missing=tuple(tests_missing_function),
        )

    # AC.TDG.5 — every new AC has a matching test file + function.
    return Decision(
        "allow",
        bound_acs=bound_acs,
        new_acs_in_scope=new_acs_in_scope,
        tests_present=tuple(tests_present),
    )


# ---------------------------------------------------------------------
# Test-tree path detection (AC.TDG.3)
# ---------------------------------------------------------------------


def _is_test_tree_path(rel_path: str) -> bool:
    """True iff ``rel_path`` lies under ``framework/<comp>/tests/``.

    Forward-slash POSIX form. Handles arbitrary subdirectories under
    ``tests/`` (integration/, fixtures/, etc.).
    """
    parts = rel_path.split("/")
    if len(parts) < 4:
        return False
    if parts[0] != "framework":
        return False
    if parts[2] != "tests":
        return False
    return True


# ---------------------------------------------------------------------
# Sentinel reader shim (defensive duplication mirrors A2)
# ---------------------------------------------------------------------


def _read_active_scope_sentinel_or_none(workspace_root: Path) -> Any:
    return _helpers.read_active_scope_sentinel_or_none(workspace_root)


# ---------------------------------------------------------------------
# Reason text builders (structured natural-language deny reasons)
# ---------------------------------------------------------------------


def _reason_missing_test_file(
    rel_path: str,
    tests_missing: list[tuple[str, str]],
) -> str:
    pairs = "; ".join(
        f"{ac_id} (expected: `{glob}`)" for (ac_id, glob) in tests_missing
    )
    return (
        f"ODD §4 (re-extension) — file `{rel_path}` cannot be edited: "
        f"the active-scope sentinel binds NEW acceptance criterion(a) "
        f"that lack a matching test on disk. Missing: {pairs}. Repair "
        f"directions: (a) author the test FIRST (write a file matching "
        f"the expected glob containing a function whose name starts "
        f"with the AC's prefix), then retry the source edit; (b) if "
        f"the AC ID is wrong (typo, drift), correct the manifest row "
        f"or the sentinel binding before retrying; (c) if this edit "
        f"is not for the bound AC, halt and surface to the dispatcher."
    )


def _reason_missing_test_function(
    rel_path: str,
    tests_missing: list[tuple[str, str]],
    files_seen: list[tuple[str, str]],
) -> str:
    pairs = "; ".join(
        f"{ac_id} (expected function-name prefix: `def {prefix}...`)"
        for (ac_id, prefix) in tests_missing
    )
    files_text = "; ".join(
        f"{ac_id}: `{path}`" for (ac_id, path) in files_seen
    ) or "(none)"
    return (
        f"ODD §4 (re-extension) — file `{rel_path}` cannot be edited: "
        f"a test file matching the expected glob exists for the new "
        f"AC(s) but no function whose name starts with the AC's "
        f"prefix is defined inside. Missing: {pairs}. Files found: "
        f"{files_text}. Repair directions: (a) rename the existing "
        f"function so its name starts with the expected prefix; (b) "
        f"add a new function whose name starts with the prefix; (c) "
        f"if the test was copy-pasted from a sibling AC, update the "
        f"function name to match the bound AC."
    )


# ---------------------------------------------------------------------
# Audit log (AC.TDG.7)
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
    """Append one NDJSON line to A3's audit log. Fail-soft.

    Schema mirrors A2's keys + three A3-new keys (new_acs_in_scope,
    tests_present, tests_missing).
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
        "new_acs_in_scope": [
            {"component": c, "ac_id": a}
            for (c, a) in decision.new_acs_in_scope
        ],
        "tests_present": [
            {"ac_id": a, "test_path": p}
            for (a, p) in decision.tests_present
        ],
        "tests_missing": [
            {"ac_id": a, "expected_test_glob": g}
            for (a, g) in decision.tests_missing
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

    Fail-soft on every environmental / parse failure (mirrors A2).
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

    rel_path = (
        _workspace_relative(raw_path, workspace_root) if raw_path else None
    )
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    sentinel_state = (
        "present"
        if _read_active_scope_sentinel_or_none(workspace_root) is not None
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
