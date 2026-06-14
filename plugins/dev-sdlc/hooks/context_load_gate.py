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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""PreToolUse guard — the structural context-load gate
(principle-foundation-structural-enforcement, AC.PFSE.5, D-PFSE.4).

Sibling of the dev-sdlc PreToolUse guard family. The persona cannot
DISPATCH (a Task) or AUTHOR (a Write/Edit to a non-carve-out source
path) until the session has loaded the required design corpus — the
follow-the-defined-workflow rule (Lens 0) made structural.

THE LOADED-SET PREDICATE (NOT an LLM relevance judgment — plan §3 /
halt-trigger 2). The gate consults the existing corpus-load sentinel
(``corpus_load_sentinel.read_corpus_load_sentinel``), which records the
session's ``corpus_paths_required`` / ``corpus_paths_loaded`` and a
computed ``state`` in {loaded, partial, missing}. The gate is a pure
deterministic predicate over that state — it makes NO judgment about
whether a SPECIFIC doc is relevant to THIS dispatch; it asks only "has
the session loaded its required-corpus set?" (the explicit required-doc
set, per the §3.1 latency ruling).

Two-tier posture:
  * state == "loaded" (or no required set) → allow.
  * state in {"partial", "missing"} AND the tool is a gated work-shape
    (Task dispatch / Write-or-Edit to a non-carve-out path) → DENY,
    naming the unloaded required docs + the one-line fix (load them,
    then the SessionStart corpus-load advances the sentinel).

DEV-MODE short-circuit + carve-out exemption (you must be able to edit
docs/scratch to LOAD context) + fail-open mirror the sibling guards.

Stdlib only (json, sys) plus shared ``_gate_helpers`` +
``corpus_load_sentinel``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

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


AUDIT_LOG_FILENAME = "context-load-gate.log"

# Work-shapes the gate governs: dispatching a sub-agent or authoring a
# source edit. Read-only / diagnostic tools are never gated.
DISPATCH_TOOLS = ("Task",)
AUTHOR_TOOLS = ("Write", "Edit", "MultiEdit")


class Decision:
    """Outcome of one context-load-gate fire.

    ``decision`` in {"allow", "deny", "no-op"}. ``kind`` names the
    sub-shape for the audit row: {"deny", "loaded", "carve-out",
    "no-op", None}. ``state`` carries the corpus state for the audit.
    """

    __slots__ = ("decision", "reason", "kind", "state")

    def __init__(
        self,
        decision: str,
        *,
        reason: str | None = None,
        kind: str | None = None,
        state: str | None = None,
    ) -> None:
        self.decision = decision
        self.reason = reason
        self.kind = kind
        self.state = state


def _read_sentinel(workspace_root: Path, session_id: str) -> Any | None:
    """Read the corpus-load sentinel via the production reader, or None.

    Lazy import so a system-Python invocation resolves the sibling
    module via the canonical-hooks-dir insertion above."""
    try:
        import corpus_load_sentinel as cls

        return cls.read_corpus_load_sentinel(workspace_root, session_id)
    except Exception:  # noqa: BLE001 — fail-closed-to-permissive
        return None


def _author_target_is_carve_out(
    tool_input: dict[str, Any], workspace_root: Path
) -> bool:
    """True iff a Write/Edit targets a dev-discipline carve-out path
    (docs/, .scratch/, etc.) — editing those is how context gets
    loaded, so they are never gated."""
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        # No path — cannot classify; treat as carve-out (fail-open).
        return True
    rel = _helpers.workspace_relative(file_path, workspace_root)
    if rel is None:
        # Outside the workspace — not a gated source edit.
        return True
    return _helpers.is_carve_out_path(rel)


def evaluate(
    *,
    workspace_root: Path,
    tool_name: str,
    tool_input: dict[str, Any],
    session_id: str | None,
) -> Decision:
    """Decide allow / deny / no-op for one PreToolUse fire.

    DEV-MODE-only. Gates Task dispatch + non-carve-out Write/Edit.
    Denies when the session corpus state is not ``loaded``.
    """
    is_dispatch = tool_name in DISPATCH_TOOLS
    is_author = tool_name in AUTHOR_TOOLS
    if not (is_dispatch or is_author):
        return Decision("no-op")

    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    if mode != "dev-mode":
        return Decision("no-op")

    # Author edits to carve-out paths (docs/scratch) are how context is
    # loaded — never gated.
    if is_author and _author_target_is_carve_out(
        tool_input, workspace_root
    ):
        return Decision("allow", kind="carve-out")

    if not session_id:
        # No session id on the envelope — cannot consult the per-session
        # sentinel; fail-open (a broken predicate must never block).
        return Decision("allow", kind="no-op")

    sentinel = _read_sentinel(workspace_root, session_id)
    if sentinel is None:
        # No sentinel yet (session just started / SessionStart hook has
        # not written it) — fail-open: absence of the predicate is not a
        # block (the SessionStart corpus-load is the writer).
        return Decision("allow", kind="no-op")

    # No required set → nothing to gate on.
    if not sentinel.corpus_paths_required:
        return Decision("allow", kind="loaded", state=sentinel.state)

    if sentinel.state == "loaded":
        return Decision("allow", kind="loaded", state=sentinel.state)

    # partial / missing → block the gated work-shape.
    unloaded = [
        p
        for p in sentinel.corpus_paths_required
        if p not in set(sentinel.corpus_paths_loaded)
    ]
    return Decision(
        "deny",
        reason=_reason_deny(
            unloaded=unloaded,
            state=sentinel.state,
            is_dispatch=is_dispatch,
        ),
        kind="deny",
        state=sentinel.state,
    )


def _reason_deny(
    *, unloaded: list[str], state: str, is_dispatch: bool
) -> str:
    shape = "dispatch a sub-agent" if is_dispatch else "author a source edit"
    names = ", ".join(unloaded) if unloaded else "(the required design corpus)"
    return (
        f"context-load gate (DEV-MODE) — refused: the session has not "
        f"loaded its required design corpus (state: {state}), so it may "
        f"not {shape} yet. Follow-the-defined-workflow (Lens 0): load "
        f"your position before acting. Unloaded required doc(s): {names}. "
        f"Fix: Read the unloaded doc(s) — the SessionStart corpus-load "
        f"advances the sentinel to `loaded`, then this gate allows the "
        f"work. (Editing docs/scratch to load context is never gated.)"
    )


def _append_audit_line(
    workspace_root: Path,
    *,
    tool_name: str,
    mode: str,
    decision: Decision,
) -> None:
    payload = {
        "ts": _helpers.now_iso_z(),
        "tool": tool_name,
        "mode": mode,
        "decision": decision.decision,
        "kind": decision.kind,
        "corpus_state": decision.state,
    }
    _helpers.append_audit_line(
        workspace_root, AUDIT_LOG_FILENAME, payload
    )


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
    """Read the PreToolUse envelope from stdin; emit allow/deny; exit 0.

    Fail-open on every environmental / parse failure.
    """
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-open
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
    session_id = envelope.get("session_id")
    session_id = session_id if isinstance(session_id, str) else None

    try:
        decision = evaluate(
            workspace_root=workspace_root,
            tool_name=tool_name,
            tool_input=tool_input,
            session_id=session_id,
        )
    except Exception:  # noqa: BLE001 — fail-open on any internal error
        return 0

    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    if decision.decision != "no-op":
        _append_audit_line(
            workspace_root,
            tool_name=tool_name,
            mode=mode,
            decision=decision,
        )

    if decision.decision == "deny" and decision.reason is not None:
        _emit_deny_response(decision.reason)
    # allow / no-op → empty stdout.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
