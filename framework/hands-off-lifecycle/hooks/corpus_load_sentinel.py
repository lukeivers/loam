"""Corpus-load sentinel — workspace-local session-scoped file recording
that the session-start required-corpus reads have happened.

Added by the structural-enforcement A1 substrate amendment.

## Failure class closed by this module

Future structural-enforcement gates (A2 / A3 / A4) need to know
whether the current Claude Code session has loaded the required
design corpus before allowing source edits. Today the requirement
is advisory — Luke's ``feedback_session_start_discipline`` rule.
The sentinel is the on-disk surface that future gates consult to
turn the discipline structural.

## Contract

One sentinel file per (workspace, session_id) pair:
``<workspace>/.pos/session-state/<session_id>.json``. JSON shape
(per AC.SE.4):

  - ``session_id`` (string).
  - ``corpus_paths_required`` (list of workspace-relative paths
    drawn from the dev-mode-manifest's mode-aware always-loaded
    set per AC.SE.5).
  - ``corpus_paths_loaded`` (list — empty at session-start; future
    hooks may append).
  - ``state`` ∈ ``{loaded, partial, missing}`` (computed from
    path-existence checks at session-start time).
  - ``created_at`` (ISO-8601 UTC).

The hook completes within the SessionStart inner-hook budget (5s
matches loam-mode's #45 envelope) and exits 0 on every path
(fail-soft per the SessionStart contract).

## Workspace-mode partition (AC.SE.5)

The required-corpus set is mode-aware: NORMAL USE workspaces get
``always_loaded`` only; DEV MODE workspaces get
``always_loaded ∪ dev_only``. The mode bit is queried via
``loam_mode``'s existing ``read_dev_intent_safe`` +
``compute_session_mode`` pair (consumer-only — no edits to
``loam_mode``). The mode-bit string contract per AC.SE.1 is
``"dev-mode" | "normal-use"``.

Stdlib-plus-loam-mode (loam_mode is dev-discipline; A1 consumes,
does not amend).
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


SENTINEL_DIR = ".pos"
SESSION_STATE_SUBDIR = "session-state"

# D-migration D.2 (amendment #63 / D.2-build.B): workspace-state lives
# under ``<workspace>/workspace/`` post-D.2. Hook scripts duplicate
# the constant per stdlib-only contract. Canonical source:
# ``framework/workspace-bootstrap/src/workspace_bootstrap/
#   workspace_paths.py`` (``WORKSPACE_STATE_SUBDIR``).
WORKSPACE_STATE_SUBDIR = "workspace"

WorkspaceMode = Literal["dev-mode", "normal-use"]
CorpusState = Literal["loaded", "partial", "missing"]


# ---------------------------------------------------------------------
# AC.SE.1 — workspace-mode bit
# ---------------------------------------------------------------------


def workspace_mode(workspace_root: Path | str) -> WorkspaceMode:
    """Return the workspace's structural-enforcement mode bit.

    AC.SE.1: returns ``"dev-mode" | "normal-use"`` deterministically
    given the workspace's primary-persona contract ``dev_intent``
    field. When ``dev_intent`` is unset / unreadable / corrupt, the
    helper returns ``"normal-use"`` (fail-closed-to-permissive — the
    DEV-MODE machinery is opt-in).

    The helper composes on ``loam_mode``'s existing surface
    (``read_dev_intent_safe`` + ``compute_session_mode``) — consumer
    only; no edits to ``loam_mode``. The two-string remapping
    isolates this AC's contract from ``loam_mode``'s internal terms
    (``dev`` / ``user``).

    Sub-100ms p95: pure synchronous YAML read against the persona
    contract via ``loam_mode``'s existing path. Never raises.
    """
    try:
        from loam_mode.session_start import (
            compute_session_mode,
            read_dev_intent_safe,
        )
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return "normal-use"
    try:
        intent = read_dev_intent_safe(Path(workspace_root))
        mode = compute_session_mode(intent)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return "normal-use"
    if mode == "dev":
        return "dev-mode"
    return "normal-use"


# ---------------------------------------------------------------------
# AC.SE.4 / AC.SE.5 — corpus-load sentinel write contract
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CorpusLoadSentinel:
    """Parsed corpus-load sentinel content."""

    session_id: str
    corpus_paths_required: tuple[str, ...]
    corpus_paths_loaded: tuple[str, ...]
    state: CorpusState
    created_at: str


@dataclass(frozen=True)
class CorpusLoadWriteResult:
    """Outcome of a ``write_corpus_load_sentinel`` call.

    ``wrote`` is True iff the call wrote new content; False on
    idempotent skip OR environmental failure. ``reason`` names the
    outcome class structurally; ``path`` is the absolute target
    sentinel path.
    """

    wrote: bool
    reason: str
    path: Path
    error_detail: str = ""


def session_state_path(
    workspace_root: Path | str, session_id: str
) -> Path:
    """Path to the (workspace, session_id) sentinel file.

    D-migration D.2 (amendment #63): now under
    ``<workspace>/workspace/.pos/session-state/<session_id>.json``.
    """
    return (
        Path(workspace_root).expanduser()
        / WORKSPACE_STATE_SUBDIR
        / SENTINEL_DIR
        / SESSION_STATE_SUBDIR
        / f"{session_id}.json"
    )


def compute_corpus_paths_required(
    workspace_root: Path | str,
    mode: WorkspaceMode,
) -> list[str]:
    """Return the sorted workspace-relative paths the session must
    load.

    AC.SE.5: NORMAL USE workspaces get ``always_loaded`` only; DEV
    MODE workspaces get ``always_loaded ∪ dev_only``. The set is
    drawn from the dev-mode-manifest at
    ``docs/rebuild/dev-mode-manifest.yaml`` via ``loam_mode``'s
    existing ``select_corpus`` surface (consumer-only).

    Fail-soft: if the manifest is missing or malformed, returns the
    empty list (the hook still writes a sentinel; ``state`` field
    surfaces the degradation as ``"missing"``).
    """
    try:
        from loam_mode.manifest import load_manifest
        from loam_mode.selector import select_corpus
    except Exception:  # noqa: BLE001 — fail-soft on missing dep
        return []
    workspace_root = Path(workspace_root)
    manifest_path = (
        workspace_root / "docs" / "rebuild" / "dev-mode-manifest.yaml"
    )
    try:
        manifest = load_manifest(manifest_path)
    except Exception:  # noqa: BLE001 — fail-soft on missing/malformed
        return []
    selector_mode = "dev" if mode == "dev-mode" else "user"
    try:
        return list(select_corpus(manifest, workspace_root, selector_mode))
    except Exception:  # noqa: BLE001
        return []


def write_corpus_load_sentinel(
    workspace_root: Path | str,
    *,
    session_id: str,
    mode: WorkspaceMode | None = None,
) -> CorpusLoadWriteResult:
    """Write the corpus-load sentinel for the current session.

    ``mode`` is computed via ``workspace_mode`` when None. The
    required-corpus path set is computed via
    ``compute_corpus_paths_required``. The ``state`` field is
    derived from path-existence checks at write time:

      - ``"loaded"`` — every required path exists in the workspace.
      - ``"partial"`` — at least one but not all required paths
        exist.
      - ``"missing"`` — no required paths exist (or the manifest
        was unreadable, returning the empty required-set; the
        sentinel still writes per AC.SE.5).

    Atomic write via ``.tmp`` sibling + ``os.replace``. Returns
    ``CorpusLoadWriteResult`` on every path; environmental failures
    do not raise.
    """
    if not session_id:
        return CorpusLoadWriteResult(
            wrote=False,
            reason="failed-empty-session-id",
            path=Path(workspace_root),
            error_detail="session_id is empty",
        )

    if mode is None:
        mode = workspace_mode(workspace_root)

    required = compute_corpus_paths_required(workspace_root, mode)
    state = _classify_corpus_state(workspace_root, required)
    target = session_state_path(workspace_root, session_id)

    payload = _serialise_sentinel(
        session_id=session_id,
        corpus_paths_required=tuple(required),
        corpus_paths_loaded=(),
        state=state,
        created_at=_now_iso(),
    )
    encoded = (payload + "\n").encode("utf-8")

    if target.exists():
        try:
            existing = target.read_bytes()
        except OSError:
            existing = None
        if existing is not None and existing == encoded:
            return CorpusLoadWriteResult(
                wrote=False, reason="skipped-identical", path=target,
            )

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        return CorpusLoadWriteResult(
            wrote=False,
            reason="failed-permission",
            path=target,
            error_detail=f"{type(e).__name__}: {e}",
        )
    except OSError as e:
        return CorpusLoadWriteResult(
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
        return CorpusLoadWriteResult(
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
        return CorpusLoadWriteResult(
            wrote=False,
            reason="failed-os-error",
            path=target,
            error_detail=f"{type(e).__name__}: {e}",
        )

    return CorpusLoadWriteResult(wrote=True, reason="written", path=target)


def read_corpus_load_sentinel(
    workspace_root: Path | str,
    session_id: str,
) -> CorpusLoadSentinel | None:
    """Read and parse a (workspace, session_id) sentinel file.

    Returns ``None`` when the file is absent, unreadable, or
    malformed. Never raises.
    """
    p = session_state_path(workspace_root, session_id)
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
        sid = data["session_id"]
        required = data["corpus_paths_required"]
        loaded = data["corpus_paths_loaded"]
        state = data["state"]
        created_at = data["created_at"]
    except KeyError:
        return None
    if not isinstance(sid, str) or not sid:
        return None
    if state not in ("loaded", "partial", "missing"):
        return None
    if not isinstance(required, list) or not all(
        isinstance(p, str) for p in required
    ):
        return None
    if not isinstance(loaded, list) or not all(
        isinstance(p, str) for p in loaded
    ):
        return None
    if not isinstance(created_at, str) or not created_at:
        return None
    return CorpusLoadSentinel(
        session_id=sid,
        corpus_paths_required=tuple(required),
        corpus_paths_loaded=tuple(loaded),
        state=state,  # type: ignore[arg-type]
        created_at=created_at,
    )


def _classify_corpus_state(
    workspace_root: Path | str,
    required_paths: list[str],
) -> CorpusState:
    """Classify ``loaded`` / ``partial`` / ``missing`` from path existence.

    Empty ``required_paths`` (manifest unreadable per AC.SE.5
    fail-soft) → ``"missing"``.
    """
    if not required_paths:
        return "missing"
    root = Path(workspace_root)
    present = sum(1 for p in required_paths if (root / p).exists())
    if present == len(required_paths):
        return "loaded"
    if present == 0:
        return "missing"
    return "partial"


def _serialise_sentinel(
    *,
    session_id: str,
    corpus_paths_required: tuple[str, ...],
    corpus_paths_loaded: tuple[str, ...],
    state: CorpusState,
    created_at: str,
) -> str:
    """Render the sentinel JSON string deterministically."""
    payload = {
        "session_id": session_id,
        "corpus_paths_required": list(corpus_paths_required),
        "corpus_paths_loaded": list(corpus_paths_loaded),
        "state": state,
        "created_at": created_at,
    }
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False)


def _now_iso() -> str:
    """ISO-8601 UTC timestamp (Z-suffixed; matches first_run_state)."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
