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

"""The position re-injection hook entry-point (★ AC.REINJECT.1 — D3).

This is the REAL production entry-point the outcome-altitude AC drives.
It composes on the SAME re-injection mechanism the framework's
SessionStart-family hooks already use (the ``corpus_inline_session_start``
/ ``compaction_discipline_reinject`` pattern — Lens 1; plan D3): read a
Claude Code hook envelope on stdin, read the active flow's cursor FROM
DISK, run the positive-resolution pause check, and emit the position
block (or the PAUSE directive) on stdout — which Claude Code captures as
``additionalContext``. No new engine is authored; this is one more thing
the re-injection carrier holds (D3 / Lens 1).

Registration points (Fork A / A1 — additive context on every
context-loss point; the PreToolUse arm is ADVISORY, never a hard tool
block in this first cut):

  - **SessionStart(source=compact)** — post-compaction re-entry.
  - **PreCompact** — just before the summarizer runs.
  - **UserPromptSubmit** — the highest-frequency context-loss point in
    normal work.
  - **PreToolUse** — before a consequential action; emits the position
    block / PAUSE directive as ADVISORY context (A1), never blocking.

★ AC.REINJECT.1 (outcome-altitude): with the build-workflow flow active
and a cursor at a real mid-flow step ON DISK, invoking this entry-point
with a genuine envelope on stdin (NO pre-arranged in-memory state) emits
context naming flow + step + branch-state + the follow-it / pause-if-lost
directive — read from the on-disk cursor. Corrupting the cursor and
re-invoking emits the PAUSE directive (AC.PAUSE.2 at the real
entry-point). STUB-class re-injection (a hand-fed position string) does
NOT satisfy this.

Fail-safe (mirrors the framework SessionStart-hook precedent): every
path returns 0. The hook never raises into Claude Code's fan-out, never
blocks a tool call.

Stdlib + PyYAML only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from loam_cli.flows.cursor import (
    methodology_cursor_path,
    read_cursor,
    resolve_cursor,
    user_state_cursor_path,
)
from loam_cli.flows.format import FlowParseError, parse_flow_definition
from loam_cli.flows.pause import position_check

# The directory holding tracked methodology flow definitions (plan §2).
_FLOWS_DIR = "docs/flows"

# The context-loss event kinds this hook re-injects on (Fork A / A1).
_REINJECT_EVENTS = {
    "sessionstart",
    "precompact",
    "userpromptsubmit",
    "pretooluse",
}


def _read_envelope() -> dict:
    """Read + parse the JSON hook envelope on stdin (fail-soft)."""
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001 — fail-soft.
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001 — fail-soft.
        return {}
    return data if isinstance(data, dict) else {}


def _detect_event(envelope: dict) -> str:
    """Classify the hook event into a normalized lowercase token.

    Mirrors compaction_discipline_reinject's best-effort detection
    across envelope shapes. For SessionStart we re-inject only on the
    compaction source (the established no-op-on-startup/resume/clear
    contract — those paths already load the corpus); every other named
    event in _REINJECT_EVENTS re-injects unconditionally.
    """
    event = (
        envelope.get("hook_event_name")
        or envelope.get("hookEventName")
        or envelope.get("event")
        or ""
    )
    event_low = str(event).lower().replace("_", "").replace("-", "")
    for known in _REINJECT_EVENTS:
        if known in event_low:
            if known == "sessionstart":
                source = str(
                    envelope.get("source") or envelope.get("trigger") or ""
                ).lower()
                # Only the compaction source re-injects (the corpus is
                # loaded fresh on startup / resume / clear).
                return "sessionstart" if source == "compact" else ""
            return known
    return ""


def _resolve_repo_root(envelope: dict) -> Path:
    """Resolve the repo / workspace root from the envelope, else cwd.

    Claude Code envelopes carry the workspace under ``workspace.project_dir``
    (SessionStart) or ``cwd`` (other events); fall back to the process
    cwd. The flows dir is resolved relative to this root.
    """
    workspace = envelope.get("workspace")
    if isinstance(workspace, dict):
        project_dir = workspace.get("project_dir")
        if isinstance(project_dir, str) and project_dir:
            return Path(project_dir)
    cwd = envelope.get("cwd")
    if isinstance(cwd, str) and cwd:
        return Path(cwd)
    return Path.cwd()


def _active_cursor_path(envelope: dict, repo_root: Path) -> Path | None:
    """Locate the active flow's cursor file on disk.

    Resolution order (single-active-flow, D5):
      1. an explicit ``flow`` field on the envelope (the flow the
         caller names as active);
      2. otherwise, the single methodology cursor present under
         ``docs/flows/`` (the dogfood — single active flow).

    Returns None when no active cursor can be located (an honest
    UNRESOLVED input — the pause-check then surfaces PAUSE, never a
    guessed position).
    """
    flow = envelope.get("flow")
    if isinstance(flow, str) and flow:
        candidate = methodology_cursor_path(repo_root, flow)
        if candidate.exists():
            return candidate
        candidate = user_state_cursor_path(repo_root, flow)
        if candidate.exists():
            return candidate
        return None
    flows_dir = repo_root / _FLOWS_DIR
    if not flows_dir.is_dir():
        return None
    cursors = sorted(flows_dir.glob("*.cursor.yaml"))
    if len(cursors) == 1:
        return cursors[0]
    # Zero cursors, or more than one with no explicit selection: cannot
    # name a single active flow (single-active-flow contract, D5).
    return None


def _load_flow_for_cursor(repo_root: Path, flow: str):
    """Load + parse the flow definition for ``flow`` from docs/flows/.

    Returns the FlowDefinition, or None when the definition is absent /
    unparseable (the cursor then resolves UNRESOLVED — the stale-flow
    case, AC.CURSOR.3 / plan §10 doubt 1).
    """
    path = repo_root / _FLOWS_DIR / f"{flow}.flow.md"
    try:
        if not path.exists():
            return None
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        return parse_flow_definition(text)
    except FlowParseError:
        return None


def build_reinjection_context(envelope: dict) -> str:
    """Build the additionalContext text for a hook envelope.

    The pure function behind ``main`` (testable without stdin). Returns
    the empty string on a non-reinject event; otherwise the position
    block (AC.PAUSE.1) on a resolved cursor or the PAUSE directive
    (AC.PAUSE.2) on an unresolved one.
    """
    kind = _detect_event(envelope)
    if kind not in _REINJECT_EVENTS:
        return ""

    repo_root = _resolve_repo_root(envelope)
    cursor_path = _active_cursor_path(envelope, repo_root)
    cursor = read_cursor(cursor_path) if cursor_path is not None else None
    definition = (
        _load_flow_for_cursor(repo_root, cursor.flow)
        if cursor is not None
        else None
    )
    resolution = resolve_cursor(cursor, definition)
    decision = position_check(resolution)

    header = "=== ACTIVE FLOW POSITION (defined-workflow re-injection) ==="
    advisory = ""
    if kind == "pretooluse" and decision.paused:
        # Fork A / A1 — PreToolUse is ADVISORY in the first cut: surface
        # the PAUSE directive as context the agent must honour, NOT a
        # hard tool block.
        advisory = (
            "\n(advisory: this fires before a consequential action; "
            "honour the pause directive before proceeding — it does "
            "not hard-block the tool call.)"
        )
    return f"{header}\n{decision.directive}{advisory}\n"


def main() -> int:
    """Hook CLI entry-point: read envelope, emit position context, exit 0.

    Fail-safe on every path (mirrors the framework SessionStart-hook
    precedent). stdout is captured by Claude Code as additionalContext.
    """
    try:
        envelope = _read_envelope()
        text = build_reinjection_context(envelope)
        if text:
            sys.stdout.write(text)
            if not text.endswith("\n"):
                sys.stdout.write("\n")
        return 0
    except Exception:  # noqa: BLE001 — never raise into the fan-out.
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        sys.exit(0)
