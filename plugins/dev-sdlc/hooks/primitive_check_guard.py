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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""PreToolUse guard — the dispatch-time leg of the prefer-the-primitive
doctrine (claude-leverage program, DOCTRINE slice, D-CLP.1 / D-DOC.2).

Fifth sibling of the dev-sdlc PreToolUse guard family (objective-binding
/ tdd / bash / agent). Matcher ``Task`` — fires only on Agent dispatch,
adding ZERO latency to every other tool call (Claude Code's matcher
primitive does the scoping, not this code).

WHAT IT DOES

Inspects every ``Task`` dispatch prompt (+ description) for a
bespoke-equivalent work-shape — a brief that asks an agent to BUILD a
custom loop / scheduler / orchestrator / lifecycle-interceptor that
re-implements a catalogued native Claude primitive. The detection data
is the D-DOC.4 matcher table (``primitive_check_matchers.ROWS``); each
row points at the corpus entry naming the primitive it re-implements.

Two-tier posture (D-DOC.2):

  * HIGH-precision (``deny``-tier) bespoke-build match AND no
    ``primitive-rationale:`` line in the prompt → **DENY**, with a
    reason naming the matched primitive, its corpus entry, and the
    one-line fix.
  * LOWER-confidence (``warn``-tier) match AND no rationale line →
    **allow + systemMessage warn** naming the same.
  * A ``primitive-rationale:`` line present anywhere in the prompt is
    the ESCAPE HATCH (D-DOC.3): allow, fire logged as hatch-use.
    ``primitive-rationale: bespoke — <reason>`` is valid.
  * Emergency-off (env ``LOAM_PRIMITIVE_CHECK=off`` OR a workspace
    sentinel file) → allow, logged.
  * No match → no-op allow.

The FIRE PATH reads NO files and makes NO network/LLM call (AC.CLP-DOC.7
/ no-API-key constraint): it runs compiled regexes over the prompt
string. The corpus is consulted only at TEST time by the coverage guard.

ENVELOPE / SURFACE CONTRACT — identical to the sibling guards. Reads the
PreToolUse JSON envelope on stdin; the parent cwd is the top-level
``cwd`` field. Writes an empty stdout on allow/no-op or a deny payload
with ``permissionDecision: deny``; a ``systemMessage`` on warn. Exits 0
on every path (fail-open: a broken check must never block dispatch).

DEV-MODE short-circuit + fail-open mirror the sibling guards.

Stdlib only (json, os, re, sys) plus shared ``_gate_helpers`` +
``primitive_check_matchers``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


# Ensure sibling modules are importable when invoked as a standalone
# script (mirror of agent_guard's sys.path setup).
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

# _gate_helpers.py lives at the canonical hooks dir (shared by gate
# hooks and other infrastructure). Add it to sys.path so the import
# resolves regardless of which tree this script runs from.
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
import primitive_check_matchers as _matchers  # noqa: E402


AUDIT_LOG_FILENAME = "primitive-check-guard.log"

TOOLS_GATED = ("Task",)

# Emergency-off (D-DOC.3): env var OR workspace sentinel file.
EMERGENCY_OFF_ENV = "LOAM_PRIMITIVE_CHECK"
EMERGENCY_OFF_SENTINEL = ".loam/.primitive-check-off"

# The hatch / audit-record line (D-DOC.3 / D-DOC.4). Presence anywhere
# in the prompt clears the check.
_RATIONALE_MARKER = "primitive-rationale:"


# ---------------------------------------------------------------------
# Decision container
# ---------------------------------------------------------------------


class Decision:
    """Outcome of one primitive-check fire.

    ``decision`` ∈ {"allow", "deny", "warn", "no-op"}.
    ``kind`` names the sub-shape for the audit row:
    {"deny", "warn", "hatch", "off", "no-op", None}.
    """

    __slots__ = (
        "decision",
        "reason",
        "kind",
        "matched_row",
        "primitive",
    )

    def __init__(
        self,
        decision: str,
        *,
        reason: str | None = None,
        kind: str | None = None,
        matched_row: str | None = None,
        primitive: str | None = None,
    ) -> None:
        self.decision = decision
        self.reason = reason
        self.kind = kind
        self.matched_row = matched_row
        self.primitive = primitive


def _has_rationale_line(prompt: str) -> bool:
    return _RATIONALE_MARKER in prompt.lower()


def _emergency_off(workspace_root: Path) -> bool:
    """True iff the env var or workspace sentinel disables the check."""
    if os.environ.get(EMERGENCY_OFF_ENV, "").strip().lower() == "off":
        return True
    try:
        if (workspace_root / EMERGENCY_OFF_SENTINEL).exists():
            return True
    except OSError:
        return False
    return False


def _first_match(prompt: str) -> _matchers.MatcherRow | None:
    """Return the highest-precedence matcher row that fires, or None.

    ``deny``-tier rows take precedence over ``warn``-tier rows so a
    prompt that triggers both reports the deny. Within a tier, the
    table order decides.
    """
    deny_hit: _matchers.MatcherRow | None = None
    warn_hit: _matchers.MatcherRow | None = None
    for row in _matchers.ROWS:
        if row.pattern.search(prompt) is None:
            continue
        if row.tier == "deny" and deny_hit is None:
            deny_hit = row
        elif row.tier == "warn" and warn_hit is None:
            warn_hit = row
    return deny_hit or warn_hit


def evaluate(
    *,
    workspace_root: Path,
    tool_name: str,
    tool_input: dict[str, Any],
) -> Decision:
    """Decide allow / deny / warn / no-op for one PreToolUse Task fire.

    DEV-MODE-only gate: NORMAL-USE workspaces short-circuit to no-op
    (the dispatch-path enforcement is dev-mode-first per master §2
    row 4). Mirrors the sibling guards' mode short-circuit.
    """
    if tool_name not in TOOLS_GATED:
        return Decision("no-op")

    prompt = tool_input.get("prompt")
    if not isinstance(prompt, str):
        return Decision("no-op")
    description = tool_input.get("description")
    if isinstance(description, str):
        haystack = f"{description}\n{prompt}"
    else:
        haystack = prompt

    # DEV-MODE short-circuit (the structural leg guards the dev
    # dispatch path; NORMAL-USE gets the advisory skills, not the gate).
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)
    if mode != "dev-mode":
        return Decision("no-op")

    # Emergency-off (D-DOC.3) — allow, logged as "off".
    if _emergency_off(workspace_root):
        return Decision("allow", kind="off")

    row = _first_match(haystack)
    if row is None:
        return Decision("allow", kind="no-op")

    # Hatch (D-DOC.3): a primitive-rationale line clears any match.
    if _has_rationale_line(haystack):
        return Decision(
            "allow",
            kind="hatch",
            matched_row=row.name,
            primitive=row.primitive,
        )

    if row.tier == "deny":
        return Decision(
            "deny",
            reason=_reason_deny(row),
            kind="deny",
            matched_row=row.name,
            primitive=row.primitive,
        )
    # warn-tier
    return Decision(
        "warn",
        reason=_reason_warn(row),
        kind="warn",
        matched_row=row.name,
        primitive=row.primitive,
    )


# ---------------------------------------------------------------------
# Reason builders
# ---------------------------------------------------------------------


def _one_line_fix(row: _matchers.MatcherRow) -> str:
    return (
        f"Add a `primitive-rationale: <primitive or bespoke> — "
        f"<reason>` line to the dispatch prompt (the line is the audit "
        f"record AND the escape hatch; `primitive-rationale: bespoke — "
        f"<reason>` is valid when bespoke genuinely is correct), OR "
        f"reach for the native primitive — see "
        f"`{row.corpus_entry}`."
    )


def _reason_deny(row: _matchers.MatcherRow) -> str:
    return (
        f"prefer-the-primitive (DEV-MODE) — refused: this dispatch "
        f"asks an agent to build a bespoke equivalent of a catalogued "
        f"Claude primitive (`{row.primitive}`) without a recorded "
        f"primitive-consideration. The native primitive is documented "
        f"at `{row.corpus_entry}`. Per loam Lens 1 "
        f"(Claude-leverage-first) + `feedback_structural_enforcement_"
        f"on_recurrence`, re-implementing a maintained primitive is a "
        f"default AI betrayal the doctrine guards against. Fix: "
        f"{_one_line_fix(row)}"
    )


def _reason_warn(row: _matchers.MatcherRow) -> str:
    return (
        f"prefer-the-primitive (DEV-MODE) — note: this dispatch "
        f"mentions a work-shape that a catalogued Claude primitive "
        f"(`{row.primitive}`) may already cover (documented at "
        f"`{row.corpus_entry}`). If you are building a bespoke "
        f"equivalent, consider the native primitive first. "
        f"{_one_line_fix(row)} (Allowed; this is advisory.)"
    )


# ---------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------


def _append_audit_line(
    workspace_root: Path,
    *,
    prompt_len: int,
    mode: str,
    decision: Decision,
) -> None:
    """Append one NDJSON line per fire. Fail-soft (sibling format)."""
    payload = {
        "ts": _helpers.now_iso_z(),
        "tool": "Task",
        "prompt_length": prompt_len,
        "mode": mode,
        "decision": decision.decision,
        "kind": decision.kind,
        "matched_row": decision.matched_row,
        "primitive": decision.primitive,
    }
    _helpers.append_audit_line(
        workspace_root, AUDIT_LOG_FILENAME, payload
    )


# ---------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------


def _emit_deny_response(reason: str) -> None:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


def _emit_warn_response(message: str) -> None:
    payload = {"systemMessage": message}
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    """Read PreToolUse envelope from stdin; emit allow/deny/warn; exit 0.

    Fail-open on every environmental / parse failure (a broken check
    must never block all dispatches).
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

    try:
        decision = evaluate(
            workspace_root=workspace_root,
            tool_name=tool_name,
            tool_input=tool_input,
        )
    except Exception:  # noqa: BLE001 — fail-open on any internal error
        return 0

    prompt = tool_input.get("prompt")
    prompt_len = len(prompt) if isinstance(prompt, str) else 0
    mode = _helpers.read_workspace_mode_or_normal_use(workspace_root)

    _append_audit_line(
        workspace_root,
        prompt_len=prompt_len,
        mode=mode,
        decision=decision,
    )

    if decision.decision == "deny" and decision.reason is not None:
        _emit_deny_response(decision.reason)
    elif decision.decision == "warn" and decision.reason is not None:
        _emit_warn_response(decision.reason)
    # allow / no-op → empty stdout.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
