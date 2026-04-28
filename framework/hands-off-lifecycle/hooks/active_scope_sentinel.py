"""Active-scope sentinel — workspace-local file declaring the (component,
AC) binding the current dispatch is operating against.

Added by the structural-enforcement A1 substrate amendment.

## Failure class closed by this module

Future structural-enforcement gates (A2 objective-binding gate, A3
TDD-guard, A4 Bash/Agent-context guards) need a deterministic answer
to "what AC is this Edit/Write tool call binding to?" without
re-deriving it from the dispatch prompt or commit message every fire.
The active-scope sentinel is the on-disk surface that answers.

## Contract

One sentinel file per **workspace**:
``<workspace>/.pos/active-scope.json``. JSON shape (per AC.SE.2):

  - ``scope_id`` (string) — caller-supplied scope identifier.
  - ``plan_path`` (workspace-relative) — path to the plan-doc
    governing this scope.
  - ``bindings`` (list of ``{component, ac_id}`` dicts) — the
    (component, AC) pairs this scope binds against.
  - ``created_at`` (ISO-8601 UTC) — write timestamp.
  - ``session_id`` (string or null) — Claude Code session id when
    available; null otherwise.

The file is written atomically via ``.tmp`` sibling + ``os.rename``,
so concurrent readers always see a complete snapshot. Re-invocation
with the same ``scope_id`` is idempotent (byte-equal write skipped);
re-invocation with a different ``scope_id`` overwrites atomically.

## Read contract

The reader returns either a typed ``ActiveScopeSentinel`` dataclass or
``None`` (file absent / malformed / unreadable). Reader never raises
on environmental failure; malformed JSON is surfaced via
``read_active_scope_sentinel(...)`` returning ``None`` (the
``MalformedSentinel`` outcome). Callers route on the absence.

Stdlib only. No third-party deps.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


SENTINEL_DIR = ".pos"
SENTINEL_FILE = "active-scope.json"

# D-migration D.2 (amendment #63 / D.2-build.B): workspace-state lives
# under ``<workspace>/workspace/`` post-D.2. Hook scripts duplicate the
# constant per stdlib-only contract. Canonical source:
# ``framework/workspace-bootstrap/src/workspace_bootstrap/
#   workspace_paths.py`` (``WORKSPACE_STATE_SUBDIR``).
WORKSPACE_STATE_SUBDIR = "workspace"


@dataclass(frozen=True)
class ScopeBinding:
    """A single (component, ac_id) pair the scope binds to."""

    component: str
    ac_id: str


@dataclass(frozen=True)
class ActiveScopeSentinel:
    """Parsed active-scope sentinel file content."""

    scope_id: str
    plan_path: str
    bindings: tuple[ScopeBinding, ...]
    created_at: str
    session_id: str | None = None


@dataclass(frozen=True)
class ActiveScopeWriteResult:
    """Outcome of an ``write_active_scope_sentinel`` call.

    ``wrote`` is True iff the call wrote new content to disk; False
    when the existing file already held byte-equal content (idempotent
    skip) OR when an environmental failure prevented the write
    (graceful degradation). ``reason`` names the outcome class
    structurally; ``path`` is the absolute target path; ``error_detail``
    carries the exception detail for ``failed-*`` reasons.
    """

    wrote: bool
    reason: str
    path: Path
    error_detail: str = ""


def active_scope_path(workspace_root: Path | str) -> Path:
    """Path to a workspace's active-scope sentinel file.

    D-migration D.2 (amendment #63): now under
    ``<workspace>/workspace/.pos/active-scope.json``.
    """
    return (
        Path(workspace_root).expanduser()
        / WORKSPACE_STATE_SUBDIR
        / SENTINEL_DIR
        / SENTINEL_FILE
    )


def write_active_scope_sentinel(
    workspace_root: Path | str,
    *,
    scope_id: str,
    plan_path: str,
    bindings: list[ScopeBinding] | tuple[ScopeBinding, ...],
    session_id: str | None = None,
) -> ActiveScopeWriteResult:
    """Write the active-scope sentinel for ``workspace_root``.

    Atomic write via ``.tmp`` sibling + ``os.replace``. Idempotent on
    byte-equal content (mtime preserved). Returns
    ``ActiveScopeWriteResult`` on every path; environmental failures
    do not raise.
    """
    target = active_scope_path(workspace_root)
    payload = _serialise_sentinel(
        scope_id=scope_id,
        plan_path=plan_path,
        bindings=tuple(bindings),
        created_at=_now_iso(),
        session_id=session_id,
    )
    encoded = (payload + "\n").encode("utf-8")

    if target.exists():
        try:
            existing = target.read_bytes()
        except OSError:
            existing = None
        if existing is not None and existing == encoded:
            return ActiveScopeWriteResult(
                wrote=False, reason="skipped-identical", path=target,
            )

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        return ActiveScopeWriteResult(
            wrote=False,
            reason="failed-permission",
            path=target,
            error_detail=f"{type(e).__name__}: {e}",
        )
    except OSError as e:
        return ActiveScopeWriteResult(
            wrote=False,
            reason="failed-os-error",
            path=target,
            error_detail=f"{type(e).__name__}: {e}",
        )

    tmp = target.with_suffix(target.suffix + ".tmp")
    try:
        tmp.write_bytes(encoded)
        os.replace(tmp, target)
    except PermissionError as e:
        try:
            tmp.unlink()
        except OSError:
            pass
        return ActiveScopeWriteResult(
            wrote=False,
            reason="failed-permission",
            path=target,
            error_detail=f"{type(e).__name__}: {e}",
        )
    except OSError as e:
        try:
            tmp.unlink()
        except OSError:
            pass
        return ActiveScopeWriteResult(
            wrote=False,
            reason="failed-os-error",
            path=target,
            error_detail=f"{type(e).__name__}: {e}",
        )

    return ActiveScopeWriteResult(
        wrote=True, reason="written", path=target,
    )


def read_active_scope_sentinel(
    workspace_root: Path | str,
) -> ActiveScopeSentinel | None:
    """Read and parse the workspace's active-scope sentinel.

    Returns a typed ``ActiveScopeSentinel`` on success, or ``None`` when
    the file is absent, unreadable, or malformed. Never raises.
    """
    p = active_scope_path(workspace_root)
    if not p.exists():
        return None
    try:
        raw = p.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    try:
        scope_id = data["scope_id"]
        plan_path = data["plan_path"]
        bindings_raw = data["bindings"]
        created_at = data["created_at"]
    except KeyError:
        return None
    if not isinstance(scope_id, str) or not scope_id:
        return None
    if not isinstance(plan_path, str) or not plan_path:
        return None
    if not isinstance(created_at, str) or not created_at:
        return None
    if not isinstance(bindings_raw, list):
        return None
    bindings: list[ScopeBinding] = []
    for entry in bindings_raw:
        if not isinstance(entry, dict):
            return None
        comp = entry.get("component")
        ac = entry.get("ac_id")
        if not isinstance(comp, str) or not comp:
            return None
        if not isinstance(ac, str) or not ac:
            return None
        bindings.append(ScopeBinding(component=comp, ac_id=ac))
    sid = data.get("session_id")
    if sid is not None and not isinstance(sid, str):
        return None
    return ActiveScopeSentinel(
        scope_id=scope_id,
        plan_path=plan_path,
        bindings=tuple(bindings),
        created_at=created_at,
        session_id=sid,
    )


def _serialise_sentinel(
    *,
    scope_id: str,
    plan_path: str,
    bindings: tuple[ScopeBinding, ...],
    created_at: str,
    session_id: str | None,
) -> str:
    """Render the sentinel JSON string deterministically (sorted keys)."""
    payload = {
        "scope_id": scope_id,
        "plan_path": plan_path,
        "bindings": [
            {"component": b.component, "ac_id": b.ac_id} for b in bindings
        ],
        "created_at": created_at,
        "session_id": session_id,
    }
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False)


def _now_iso() -> str:
    """ISO-8601 UTC timestamp for the active-scope sentinel's
    ``created_at`` field.

    Format γ (microsecond resolution + ``Z`` suffix, fixed-width 27
    chars). Delegates to ``_gate_helpers.now_iso_microsecond_z`` which
    is the single source-of-truth for the A1-substrate timestamp shape
    per amendment #75 AC.TFN.3.

    Pre-amendment-#75 this emitted ``%Y-%m-%dT%H:%M:%SZ`` (second
    resolution); the format change closes the same-second collision
    class A3's lex-compare predicate exhibited on tight back-to-back
    sentinel + manifest writes (Q1 empirical: 1000/1000 collisions
    pre-fix, 0/N post-fix).
    """
    from _gate_helpers import now_iso_microsecond_z

    return now_iso_microsecond_z()
