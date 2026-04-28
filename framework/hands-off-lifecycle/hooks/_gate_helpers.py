"""Shared helper library for hands-off-lifecycle PreToolUse gate
scripts (structural-enforcement A2 + A3 + future).

Extracted by structural-enforcement A3 (D-A3.7 of the locked plan).
A2's ``objective_binding_gate.py`` was the first gate; helpers were
inlined there per A2's D-build.2 (premature-extraction rationale).
A3 is the second gate; the rationale flips, and the shared helpers
move here. A4 (Bash/Agent-context guards) inherits this library.

The helpers carry:

  - workspace-state path constants (``WORKSPACE_STATE_SUBDIR``,
    ``POS_SUBDIR``);
  - dev-discipline carve-out tuples (``_CARVE_OUT_PREFIXES``,
    ``_CARVE_OUT_FILES``);
  - carve-out predicate (``is_carve_out_path``);
  - workspace-relative path canonicaliser (``workspace_relative``);
  - workspace-mode reader with fail-closed-to-permissive default
    (``read_workspace_mode_or_normal_use``);
  - active-scope sentinel reader with fail-closed-to-permissive
    default (``read_active_scope_sentinel_or_none``);
  - ObjectiveTracker opener with venv path-fix
    (``open_tracker_or_none``);
  - audit-log path resolver + atomic-append writer
    (``audit_log_path``, ``append_audit_line``).

Stdlib only (json, fnmatch, pathlib, os, sys, time). The
``read_active_scope_sentinel_or_none`` and
``read_workspace_mode_or_normal_use`` helpers do lazy imports of
``active_scope_sentinel`` and ``corpus_load_sentinel`` (sibling
modules under hooks/) to keep cold-start cost minimal and to allow
tests to monkeypatch ``sys.modules`` for those names. The
``open_tracker_or_none`` helper does a lazy import of
``objective_tracker`` + ``workspace_bootstrap`` after the venv path-
fix runs.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any


# Ensure sibling modules (active_scope_sentinel, corpus_load_sentinel)
# are importable when an importing script is invoked directly via
# ``python <hooks-dir>/<gate>.py``. Add this module's directory once
# at import time.
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))


# ---------------------------------------------------------------------
# Workspace-state path constants (D-migration D.2 — amendment #63)
# ---------------------------------------------------------------------
#
# Workspace state lives under ``<workspace>/workspace/`` post-D.2.
# Hook scripts duplicate the constant per stdlib-only contract
# (canonical source: ``framework/workspace-bootstrap/src/
# workspace_bootstrap/workspace_paths.py`` ``WORKSPACE_STATE_SUBDIR``).

WORKSPACE_STATE_SUBDIR = "workspace"
POS_SUBDIR = ".pos"


# ---------------------------------------------------------------------
# Carve-out path list (D-A2.6 — D1 dev-discipline)
# ---------------------------------------------------------------------
#
# Workspace-relative path PREFIXES that admit edits regardless of
# sentinel state. Per AC.OBG.5: paths under any of these admit allow
# in DEV MODE. The list is union of pre-D-migration + post-D-migration
# shapes per locked plan §D-A2.6 (the migration window admits both).
#
# A3 inherits this list verbatim — the carve-out is shared structural
# infrastructure across all gates. A3 adds an additional "test-tree"
# short-circuit at its own decision-chain layer (NOT in the carve-out
# list — A3's tests/ short-circuit fires before the new-AC check
# specifically; it's a chicken-and-egg avoidance, not a dev-discipline
# admission).

_CARVE_OUT_PREFIXES: tuple[str, ...] = (
    "docs/",
    "tools/",
    ".scratch/",
    "personas/",
    "framework/docs/",
    "framework/tools/",
    "framework/personas/",
)

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


def is_carve_out_path(workspace_relative_path: str) -> bool:
    """True iff ``workspace_relative_path`` is a dev-discipline carve-
    out admitted regardless of sentinel state.

    Method per ODD §7.4: prefix-match for tree carve-outs + exact-
    match for file admissions. Path is workspace-relative, forward-
    slash separated.
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


def workspace_relative(
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
# Lazy-imported substrate readers (fail-closed-to-permissive)
# ---------------------------------------------------------------------


def read_workspace_mode_or_normal_use(workspace_root: Path) -> str:
    """Read the workspace-mode bit, or fall back to ``normal-use``.

    Lazy import of ``corpus_load_sentinel`` so a system-Python invoked
    hook script picks up the sibling module via the ``_HOOKS_DIR``
    insertion above. Failure (corpus-load-sentinel module absent,
    workspace_root unreadable) falls through to ``normal-use``, which
    short-circuits the gate to no-op (fail-closed-to-permissive at
    the import boundary).
    """
    try:
        from corpus_load_sentinel import workspace_mode

        return workspace_mode(workspace_root)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return "normal-use"


def read_active_scope_sentinel_or_none(workspace_root: Path) -> Any:
    """Read the active-scope sentinel, or return None on failure.

    Lazy import of ``active_scope_sentinel``. Returns None when the
    sentinel is absent OR when the read fails (malformed JSON, IO
    error). Caller decides whether absent-sentinel is a deny or an
    allow per its own gate-specific contract.
    """
    try:
        from active_scope_sentinel import read_active_scope_sentinel

        return read_active_scope_sentinel(workspace_root)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return None


# ---------------------------------------------------------------------
# Tracker open
# ---------------------------------------------------------------------


def open_tracker_or_none(workspace_root: Path) -> Any | None:
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
# Audit log writer
# ---------------------------------------------------------------------


def audit_log_path(workspace_root: Path, log_filename: str) -> Path:
    """Resolve the audit-log path for a gate.

    Per the D-migration D.2 convention (amendment #63):
    ``<workspace>/workspace/.pos/<log_filename>``.
    """
    return workspace_root / WORKSPACE_STATE_SUBDIR / POS_SUBDIR / log_filename


def append_audit_line(
    workspace_root: Path,
    log_filename: str,
    payload: dict[str, Any],
) -> None:
    """Append one NDJSON line to the gate's audit log. Fail-soft.

    Atomic single-line append via ``os.O_APPEND`` for writes shorter
    than ``PIPE_BUF`` (POSIX guarantees single-write atomicity for
    such payloads; one decision row is well under that).
    """
    target = audit_log_path(workspace_root, log_filename)
    line = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
    encoded = line.encode("utf-8")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
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
# Misc utilities used by gates
# ---------------------------------------------------------------------


def now_iso_z() -> str:
    """ISO-8601 UTC timestamp with second resolution + ``Z`` suffix.

    Mirrors A2's ``time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())``
    pattern; centralised here so all gates share the same shape.
    """
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
