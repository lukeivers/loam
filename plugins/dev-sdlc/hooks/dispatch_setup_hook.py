"""PreToolUse setup-phase hook — authors disk-side four gates on
``Task`` dispatches that carry an ``<AC-MANIFEST>`` block in the
prompt.

Added by M4 (amendment #85) — wires AC.OSS.2 (D-1 from feature-usage
audit; ``dispatch_with_scope`` had zero non-test callers) into the
persona's actual Agent-dispatch path via Claude Code's native
PreToolUse event on ``Task``. Per plan §10 D-build.M4.1, the hook
applies the disk-side four gates (sentinel + manifest rows + test
stubs + plan-doc reference via the sentinel's ``plan_path`` field);
the IPC-bound chain (cost / safety / reversibility / orchestrator
inside ``activate_scope_with_spec``) stays as the explicit-call
surface for in-process callers of ``dispatch_with_scope``. Claude
Code's PreToolUse hook protocol admits only allow/deny/ask outputs —
it cannot wrap tool execution — so the disk-side phase is the most
the hook can do.

## AC declaration format (D-build.M4.2)

The dispatch prompt may carry exactly one ``<AC-MANIFEST>`` block:

    <AC-MANIFEST>
    primary-persona,AC.A8.1,framework/primary-persona/src/loam/primary_persona/dispatch_wrapper.py
    hands-off-lifecycle,AC.AG.1,framework/hands-off-lifecycle/hooks/agent_guard.py
    </AC-MANIFEST>

Lines starting with ``#`` are comments; blank lines are skipped.
Stdlib ``csv.reader`` parses each non-comment, non-blank line as
``component,ac_id,source_path_glob``. Malformed rows (wrong column
count, empty fields) are logged + skipped (fail-soft per AC.OSS-M4.2).

## Behaviour matrix

  - tool_name != "Task" → no-op (allow).
  - workspace_mode != "dev-mode" → short-circuit allow (AC.OSS-M4.5).
  - LOAM_DISPATCH_BYPASS_HOOK=1 → short-circuit allow (D-build.M4.4
    recursion bypass — design-for-future; today no production caller
    invokes ``dispatch_with_scope``).
  - No ``<AC-MANIFEST>`` block → passthrough with NDJSON deprecation
    log (AC.OSS-M4.2 + D-build.M4.3 — preserves AC.DSA.10 backwards-
    compat for research/plan dispatches).
  - ``<AC-MANIFEST>`` block with at least one well-formed row → run
    the disk-side four gates:
      1. Write the active-scope sentinel.
      2. Register one manifest row per declared AC.
      3. Author one placeholder test stub per declared AC.
      4. Plan-doc reference recorded via the sentinel's plan_path
         field (already part of step 1; named separately for
         traceability per the dispatch's enumeration).
    Then allow.

## Audit log

Every fire appends NDJSON lines to
``<workspace>/workspace/.pos/dispatch-setup-hook.log``. Schema mirrors
``agent_guard.log`` per-step rows: ``{ts, event, tool, prompt_length,
cwd, mode, decision, acs_declared, ...step-specific...}``. The full
prompt is NOT recorded (privacy + size); the AC declarations + per-
step outcomes are.

## Stdlib only

The hook itself depends only on the stdlib + sibling
``active_scope_sentinel`` + ``_gate_helpers``. The
``write_dispatcher_stub`` import from
``loam.primary_persona.dispatch_wrapper`` is lazy + fail-soft — when
the shared venv lacks the editable-install (e.g. derived workspaces
without primary-persona installed), the stub-author step degrades to
an NDJSON diagnostic and the other steps still fire.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


# Ensure sibling modules are importable when invoked as a standalone
# script (mirrors agent_guard.py / bash_guard.py / tdd_guard.py /
# objective_binding_gate.py pattern).
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
# Module-level shims (mirror A2/A3/A4 patterns; tests monkeypatch
# these).
# ---------------------------------------------------------------------

WORKSPACE_STATE_SUBDIR = _helpers.WORKSPACE_STATE_SUBDIR
POS_SUBDIR = _helpers.POS_SUBDIR
AUDIT_LOG_FILENAME = "dispatch-setup-hook.log"

TOOLS_GATED = ("Task",)

# AC.OSS-M4.2 — block markers are case-sensitive per plan-doc §4 +
# D-build.M4.2.
_AC_MANIFEST_BLOCK_PATTERN = re.compile(
    r"<AC-MANIFEST>\s*\n(.*?)\n\s*</AC-MANIFEST>",
    re.DOTALL,
)

# D-build.M4.4 — recursion bypass env-var per plan §10.
BYPASS_ENV_VAR = "LOAM_DISPATCH_BYPASS_HOOK"


# ---------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------


class ParsedAC:
    """A single parsed AC declaration row.

    Mirrors ``loam.primary_persona.dispatch_wrapper.NewACSpec``'s
    field layout but is independent (no cross-component import at
    parse time).
    """

    __slots__ = ("component", "ac_id", "source_path_glob")

    def __init__(
        self, component: str, ac_id: str, source_path_glob: str
    ) -> None:
        self.component = component
        self.ac_id = ac_id
        self.source_path_glob = source_path_glob

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ParsedAC):
            return NotImplemented
        return (
            self.component == other.component
            and self.ac_id == other.ac_id
            and self.source_path_glob == other.source_path_glob
        )

    def __repr__(self) -> str:
        return (
            f"ParsedAC(component={self.component!r}, "
            f"ac_id={self.ac_id!r}, "
            f"source_path_glob={self.source_path_glob!r})"
        )


def extract_ac_manifest_block(prompt: str) -> str | None:
    """Return the body inside ``<AC-MANIFEST>...</AC-MANIFEST>``, or
    None when absent.

    Case-sensitive on the marker. Returns the inner text (without the
    marker lines).
    """
    if not isinstance(prompt, str):
        return None
    m = _AC_MANIFEST_BLOCK_PATTERN.search(prompt)
    if m is None:
        return None
    return m.group(1)


def parse_ac_manifest_block(
    block_body: str,
) -> tuple[list[ParsedAC], list[str]]:
    """Parse the AC manifest block body. Returns (well-formed rows,
    malformed-row diagnostics).

    Each non-blank, non-comment line is parsed via ``csv.reader``.
    Comments start with ``#``. Malformed rows (wrong column count,
    empty fields) are appended to the diagnostics list and skipped
    (fail-soft per AC.OSS-M4.2).
    """
    rows: list[ParsedAC] = []
    diagnostics: list[str] = []
    if not isinstance(block_body, str):
        return rows, diagnostics
    reader = csv.reader(io.StringIO(block_body))
    for row_num, row in enumerate(reader, start=1):
        # csv.reader yields [] for blank lines.
        if not row:
            continue
        # Skip comment lines (first cell starts with '#').
        first = row[0].strip() if row else ""
        if first.startswith("#"):
            continue
        if len(row) != 3:
            diagnostics.append(
                f"row {row_num}: expected 3 columns "
                f"(component,ac_id,source_path_glob), got {len(row)}"
            )
            continue
        component = row[0].strip()
        ac_id = row[1].strip()
        source_path_glob = row[2].strip()
        if not component or not ac_id or not source_path_glob:
            diagnostics.append(
                f"row {row_num}: empty field(s) — component="
                f"{component!r}, ac_id={ac_id!r}, "
                f"source_path_glob={source_path_glob!r}"
            )
            continue
        rows.append(
            ParsedAC(
                component=component,
                ac_id=ac_id,
                source_path_glob=source_path_glob,
            )
        )
    return rows, diagnostics


# ---------------------------------------------------------------------
# Setup-phase invocation (the four disk-side gates)
# ---------------------------------------------------------------------


def _scope_id_for_dispatch(prompt: str, session_id: str | None) -> str:
    """Derive a deterministic scope_id for this dispatch.

    Per AC.DSA.4 idempotency, re-fire on the same prompt + session
    needs the same scope_id so the sentinel's byte-equal short-circuit
    fires. We use a stable-hash of the prompt-prefix + session_id.
    """
    import hashlib

    seed = f"{session_id or 'no-session'}|{(prompt or '')[:1024]}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return f"dispatch-hook-{digest}"


def _derive_plan_path(prompt: str) -> str:
    """Best-effort plan-doc path extraction from the dispatch prompt.

    Looks for ``docs/plans/<slug>.md`` mentions; falls back to
    a sentinel ``"<plan-not-declared>"`` when none found. The sentinel
    keeps the field non-empty per the active-scope sentinel's schema
    (plan_path is required + must be a non-empty string).
    """
    if not isinstance(prompt, str):
        return "<plan-not-declared>"
    m = re.search(
        r"docs/plans/[A-Za-z0-9._-]+\.md", prompt
    )
    if m is not None:
        return m.group(0)
    return "<plan-not-declared>"


def _run_setup_phase(
    *,
    workspace_root: Path,
    parsed_acs: list[ParsedAC],
    scope_id: str,
    plan_path: str,
    audit_base: dict[str, Any],
) -> list[dict[str, Any]]:
    """Run the four disk-side gates. Returns per-step outcomes.

    Each step is fail-soft (mirrors ``dispatch_wrapper._run_setup_phase``
    semantics): substrate failures emit a structured NDJSON line and
    the next step still fires.
    """
    outcomes: list[dict[str, Any]] = []

    # Gate 1 — sentinel.
    sentinel_outcome: dict[str, Any] = {
        "step": "sentinel",
        "scope_id": scope_id,
    }
    try:
        from active_scope_sentinel import (  # type: ignore[import-not-found]
            ScopeBinding,
            write_active_scope_sentinel,
        )

        bindings = tuple(
            ScopeBinding(component=ac.component, ac_id=ac.ac_id)
            for ac in parsed_acs
        )
        result = write_active_scope_sentinel(
            workspace_root,
            scope_id=scope_id,
            plan_path=plan_path,
            bindings=bindings,
        )
        sentinel_outcome["wrote"] = bool(result.wrote)
        sentinel_outcome["reason"] = result.reason
        sentinel_outcome["path"] = str(result.path)
        if result.error_detail:
            sentinel_outcome["error_detail"] = result.error_detail
    except Exception as e:  # noqa: BLE001 — fail-soft per AC.OSS-M4.6
        sentinel_outcome["wrote"] = False
        sentinel_outcome["reason"] = "failed-exception"
        sentinel_outcome["error_detail"] = f"{type(e).__name__}: {e}"
    outcomes.append(sentinel_outcome)
    _emit_audit(workspace_root, {**audit_base, **sentinel_outcome})

    # Gate 2 — manifest rows.
    tracker = _open_tracker(workspace_root)
    for ac in parsed_acs:
        manifest_outcome: dict[str, Any] = {
            "step": "manifest",
            "scope_id": scope_id,
            "component": ac.component,
            "ac_id": ac.ac_id,
            "source_path_glob": ac.source_path_glob,
        }
        if tracker is None:
            manifest_outcome["outcome"] = "failed-tracker-unavailable"
        else:
            try:
                tracker.register_source_binding(
                    component=ac.component,
                    ac_id=ac.ac_id,
                    source_path_glob=ac.source_path_glob,
                )
                manifest_outcome["outcome"] = "registered"
            except Exception as e:  # noqa: BLE001 — fail-soft
                manifest_outcome["outcome"] = "failed-exception"
                manifest_outcome["error_detail"] = (
                    f"{type(e).__name__}: {e}"
                )
        outcomes.append(manifest_outcome)
        _emit_audit(workspace_root, {**audit_base, **manifest_outcome})

    # Gate 3 — placeholder test stubs.
    for ac in parsed_acs:
        stub_outcome: dict[str, Any] = {
            "step": "stub",
            "scope_id": scope_id,
            "component": ac.component,
            "ac_id": ac.ac_id,
        }
        try:
            # Lazy import — primary-persona's dispatch_wrapper lives in
            # the shared venv's editable install. Failure (venv stale,
            # primary-persona uninstalled) degrades to an NDJSON
            # diagnostic; the dispatch is still allowed.
            from loam.primary_persona.dispatch_wrapper import (  # type: ignore[import-not-found]
                NewACSpec,
                write_dispatcher_stub,
            )

            spec = NewACSpec(
                component=ac.component,
                ac_id=ac.ac_id,
                source_path_glob=ac.source_path_glob,
            )
            result = write_dispatcher_stub(
                workspace_root,
                spec,
                scope_id=scope_id,
                plan_path=plan_path,
            )
            stub_outcome.update(result)
        except Exception as e:  # noqa: BLE001 — fail-soft
            stub_outcome["outcome"] = "failed-exception"
            stub_outcome["error_detail"] = f"{type(e).__name__}: {e}"
        outcomes.append(stub_outcome)
        _emit_audit(workspace_root, {**audit_base, **stub_outcome})

    # Gate 4 — plan-doc reference. Implicit via gate 1 (sentinel
    # carries plan_path); enumerate it explicitly per the dispatch's
    # four-gate language so the audit log surfaces it.
    plan_outcome = {
        "step": "plan-doc-reference",
        "scope_id": scope_id,
        "plan_path": plan_path,
        "outcome": "recorded-via-sentinel",
    }
    outcomes.append(plan_outcome)
    _emit_audit(workspace_root, {**audit_base, **plan_outcome})

    return outcomes


def _open_tracker(workspace_root: Path) -> Any | None:
    return _helpers.open_tracker_or_none(workspace_root)


# ---------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------


def _emit_audit(
    workspace_root: Path, payload: dict[str, Any]
) -> None:
    """Append one NDJSON line to dispatch-setup-hook.log. Fail-soft."""
    enriched = {"ts": _helpers.now_iso_z(), **payload}
    _helpers.append_audit_line(
        workspace_root, AUDIT_LOG_FILENAME, enriched
    )


# ---------------------------------------------------------------------
# Decision (the hook's outcome)
# ---------------------------------------------------------------------


class Decision:
    """Tiny container for a dispatch-setup-hook decision.

    ``decision`` is one of {"allow", "no-op", "passthrough-no-ac",
    "short-circuit-normal-use", "short-circuit-bypass-env",
    "setup-fired"}.
    The hook NEVER emits "deny" — composition with A4 (agent_guard,
    which IS a refusal gate) handles deny per plan §9 risk #1.
    """

    __slots__ = (
        "decision",
        "parsed_acs",
        "parse_diagnostics",
        "step_outcomes",
    )

    def __init__(
        self,
        decision: str,
        *,
        parsed_acs: list[ParsedAC] | None = None,
        parse_diagnostics: list[str] | None = None,
        step_outcomes: list[dict[str, Any]] | None = None,
    ) -> None:
        self.decision = decision
        self.parsed_acs = parsed_acs or []
        self.parse_diagnostics = parse_diagnostics or []
        self.step_outcomes = step_outcomes or []


def evaluate(
    *,
    workspace_root: Path,
    tool_name: str,
    tool_input: dict[str, Any],
    envelope_cwd: str,
    session_id: str | None = None,
    env: dict[str, str] | None = None,
) -> Decision:
    """Decide the hook's outcome for one PreToolUse Task fire.

    Returns a ``Decision`` describing the path taken. Always emits one
    or more audit log lines as a side effect (the hook is observable
    even on no-op).

    Branches:
      - tool_name != "Task" → "no-op" (no audit line; not the hook's
        traffic).
      - workspace_mode != "dev-mode" → "short-circuit-normal-use"
        (AC.OSS-M4.5).
      - LOAM_DISPATCH_BYPASS_HOOK=1 → "short-circuit-bypass-env"
        (D-build.M4.4).
      - No <AC-MANIFEST> block → "passthrough-no-ac" (AC.OSS-M4.2 +
        D-build.M4.3).
      - <AC-MANIFEST> block with no well-formed rows → still
        "passthrough-no-ac" (every row was malformed; nothing to
        author; diagnostics emitted).
      - <AC-MANIFEST> block with one or more well-formed rows →
        "setup-fired" (gates run, outcomes returned).
    """
    if tool_name not in TOOLS_GATED:
        return Decision("no-op")

    prompt = tool_input.get("prompt")
    if not isinstance(prompt, str):
        return Decision("no-op")

    audit_base: dict[str, Any] = {
        "event": "dispatch-setup-hook",
        "tool": tool_name,
        "prompt_length": len(prompt),
        "cwd": envelope_cwd,
    }

    # AC.OSS-M4.5 — mode-bit short circuit.
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    audit_base["mode"] = mode
    if mode != "dev-mode":
        _emit_audit(
            workspace_root,
            {
                **audit_base,
                "decision": "short-circuit-normal-use",
            },
        )
        return Decision("short-circuit-normal-use")

    # D-build.M4.4 — env-var bypass.
    env_lookup = env if env is not None else os.environ
    if env_lookup.get(BYPASS_ENV_VAR) == "1":
        _emit_audit(
            workspace_root,
            {
                **audit_base,
                "decision": "short-circuit-bypass-env",
            },
        )
        return Decision("short-circuit-bypass-env")

    # AC.OSS-M4.2 — block extraction + parse.
    block_body = extract_ac_manifest_block(prompt)
    if block_body is None:
        # D-build.M4.3 — passthrough with NDJSON deprecation log.
        _emit_audit(
            workspace_root,
            {
                **audit_base,
                "decision": "passthrough-no-ac",
                "reason": "no-ac-manifest-block",
            },
        )
        return Decision("passthrough-no-ac")

    parsed_acs, parse_diagnostics = parse_ac_manifest_block(block_body)
    for diag in parse_diagnostics:
        _emit_audit(
            workspace_root,
            {
                **audit_base,
                "decision": "parse-diagnostic",
                "detail": diag,
            },
        )

    if not parsed_acs:
        _emit_audit(
            workspace_root,
            {
                **audit_base,
                "decision": "passthrough-no-ac",
                "reason": "ac-manifest-block-empty-or-all-malformed",
            },
        )
        return Decision(
            "passthrough-no-ac",
            parse_diagnostics=parse_diagnostics,
        )

    # AC.OSS-M4.1 — run the four disk-side gates.
    scope_id = _scope_id_for_dispatch(prompt, session_id)
    plan_path = _derive_plan_path(prompt)
    audit_base["acs_declared"] = [
        {"component": ac.component, "ac_id": ac.ac_id}
        for ac in parsed_acs
    ]
    _emit_audit(
        workspace_root,
        {
            **audit_base,
            "decision": "setup-firing",
            "scope_id": scope_id,
            "plan_path": plan_path,
        },
    )

    step_outcomes = _run_setup_phase(
        workspace_root=workspace_root,
        parsed_acs=parsed_acs,
        scope_id=scope_id,
        plan_path=plan_path,
        audit_base=audit_base,
    )

    return Decision(
        "setup-fired",
        parsed_acs=parsed_acs,
        parse_diagnostics=parse_diagnostics,
        step_outcomes=step_outcomes,
    )


# ---------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------


def _emit_allow_response() -> None:
    """Allow path — empty stdout per the A2/A3/A4 convention."""
    return


def main(argv: list[str] | None = None) -> int:
    """Read PreToolUse envelope from stdin; emit allow; exit 0.

    The hook NEVER denies (composition with A4 handles deny). Every
    path emits empty stdout (allow) and exits 0 — fail-soft per
    A2/A3/A4 convention.
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

    session_id_raw = envelope.get("session_id")
    session_id = (
        session_id_raw if isinstance(session_id_raw, str) else None
    )

    try:
        evaluate(
            workspace_root=workspace_root,
            tool_name=tool_name,
            tool_input=tool_input,
            envelope_cwd=cwd,
            session_id=session_id,
        )
    except Exception:  # noqa: BLE001 — fail-soft per AC.OSS-M4.6
        # Last-resort fail-soft: any unhandled exception in evaluate()
        # itself should still emit allow + exit 0. We do NOT propagate
        # the exception — it would block the underlying Task tool,
        # which is not the hook's contract.
        pass

    _emit_allow_response()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
