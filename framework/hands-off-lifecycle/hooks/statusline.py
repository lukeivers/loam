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

"""Status-line renderer for the detached first-run worker.

Composes onto Claude Code's project-scoped ``statusLine`` primitive:
``.claude/settings.json`` declares this script as the ``statusLine``
command with ``refreshInterval: 1``; Claude Code spawns the script
every ~1 s, passes a small JSON envelope on stdin, and renders
stdout at the bottom of the terminal.

The script reads ``<workspace>/.pos/first-run.state`` (the state file
the worker maintains per amendment #28's workspace-local routing),
dispatches by ``state.status``, and prints one plain-English progress
line. Stdlib-only by design — pre-venv first runs invoke this script
under the system Python before ``<workspace>/.venv/`` exists.

Per locked design (D1-D6, captured 2026-04-26):

  - D1: ``progress_pct`` is read from ``FirstRunState`` (additive
    field landed in this amendment).
  - D2: post-completion steady-state for 60 s after ``updated_at``,
    then blank stdout (status line goes blank by Claude Code's
    "no output" semantics).
  - D3: state-file path derived from stdin envelope's
    ``workspace.project_dir``.
  - D4: Python 3.13 stdlib only.
  - D5 / D6: see ``first_run_helper.py`` (worker write-side) and
    the static ``_PHASE_DURATIONS_S`` map below.

Fail-closed contract: any unhandled exception → empty stdout +
exit 0 → blank status line. Never raises, never blocks, never spams
the terminal. Per locked plan §5 hard constraints.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path


# Sibling-import convention — same shape ``first_run_helper.py`` uses.
_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from first_run_state import (  # noqa: E402
    FirstRunState,
    is_stale_live_state,
    read_state,
    state_path,
)


# Maximum bytes the rendered line may emit. Per AC.SL.1 / AC.SL.2 /
# AC.SL.3 / AC.SL.5 — every active branch caps at 200 chars.
_MAX_LINE = 200

# Steady-state window after ``updated_at`` for the post-completion
# "ready" line. Per D2 ruling 2026-04-26.
_COMPLETED_STEADY_STATE_S = 60.0


# Phase -> plain-English label. The keys are the strings the worker
# writes via ``_advance_state``. Per D6 / D-build.6: builder-side
# calibration for non-tech readability.
_PHASE_LABELS: dict[str, str] = {
    "phase-2-venv-creation": "creating Python environment",
    "phase-3a-inventory": "reading install manifest",
    "phase-3b-shared-deps": "installing shared dependencies",
    "phase-3e-editable-installs": "registering component packages",
    "phase-3c-dedicated-venvs": "installing heavy dependencies",
    "phase-4a-scaffold": "writing config files",
    "phase-4b-health-poll": "starting background services",
    "phase-4c-agent-file-authorship": "preparing your assistant",
    "phase-5-confirmation": "finishing up",
    "phase-6-self-retire": "finishing up",
    "complete": "ready",
}


# Phase -> rough total-duration estimate (seconds), seeded from the
# helper's existing ~5 minute total figure plus per-phase wall-clock
# observation. Per D6 / D-build.7: static table; dynamic last-N-runs
# averaging is out of scope.
_PHASE_DURATIONS_S: dict[str, int] = {
    "phase-2-venv-creation": 15,
    "phase-3a-inventory": 5,
    "phase-3b-shared-deps": 180,
    "phase-3e-editable-installs": 60,
    "phase-3c-dedicated-venvs": 90,
    "phase-4a-scaffold": 10,
    "phase-4b-health-poll": 30,
    "phase-4c-agent-file-authorship": 10,
    "phase-5-confirmation": 1,
    "phase-6-self-retire": 1,
    "complete": 0,
}

# Total budget the worker advertises to non-tech users as "~5 minutes
# total". Used as a remaining-time fallback when the recognised phase
# falls outside ``_PHASE_DURATIONS_S``.
_TOTAL_BUDGET_S = 300


def _state_belongs_to(state: FirstRunState, project_dir: Path) -> bool:
    """Defence-in-depth mirror of ``first_run_dispatch._state_belongs_to``.

    A state whose recorded ``workspace_root`` is empty or does not
    match ``project_dir`` is treated as foreign — the renderer emits
    empty stdout for it (AC.SL.4). Keeps the renderer in lockstep
    with the dispatcher's amendment-#28 cross-workspace defence.
    """
    if not state.workspace_root:
        return False
    try:
        recorded = Path(state.workspace_root).resolve()
    except (OSError, RuntimeError):
        return False
    try:
        current = Path(project_dir).resolve()
    except (OSError, RuntimeError):
        return False
    return recorded == current


def _format_elapsed(seconds: float) -> str:
    """Human-readable elapsed time. ``Xm Ys`` for >= 60 s, ``Ys`` else."""
    if seconds < 0:
        seconds = 0
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    return f"{s // 60}m {s % 60}s"


def _format_remaining(state: FirstRunState, elapsed: float) -> str:
    """Estimate plain-English remaining time.

    Falls back to ``~N min remaining`` (rounded to the nearest minute)
    when the phase is recognised; falls back to the total-budget
    leftover when the phase is unknown; returns empty string when no
    sensible estimate is available.
    """
    phase_total = _PHASE_DURATIONS_S.get(state.phase)
    if phase_total is None:
        # Unknown phase — fall back to total-budget arithmetic. Use
        # progress_pct when present and non-zero so the estimate stays
        # honest as the worker advances.
        pct = max(0, min(100, int(state.progress_pct or 0)))
        if pct == 0:
            return ""
        # Linear projection: total time ~ elapsed / (pct/100); remaining
        # ~ total - elapsed.
        if elapsed <= 0:
            return ""
        total = elapsed / (pct / 100.0)
        remaining = max(0.0, total - elapsed)
    else:
        # Sum the durations of phases NOT yet entered. Use the phase
        # ordering implied by the static map's insertion order (Python
        # dicts preserve insertion order since 3.7).
        keys = list(_PHASE_DURATIONS_S.keys())
        try:
            idx = keys.index(state.phase)
        except ValueError:
            return ""
        remaining = sum(_PHASE_DURATIONS_S[k] for k in keys[idx:])
        # Soften: if elapsed has already exceeded the static estimate
        # for the current phase, project by progress_pct instead.
        pct = max(0, min(100, int(state.progress_pct or 0)))
        if pct > 0 and elapsed > 0:
            projected_total = elapsed / (pct / 100.0)
            projected_remaining = max(0.0, projected_total - elapsed)
            # Prefer the larger of the two so the estimate doesn't
            # collapse to "0 s" while the worker is still running.
            remaining = max(remaining, projected_remaining)

    if remaining <= 0:
        return ""
    if remaining < 60:
        return "less than a minute remaining"
    minutes = max(1, int(round(remaining / 60.0)))
    return f"about {minutes} min remaining"


def _truncate(line: str) -> str:
    """Cap output at ``_MAX_LINE`` characters. Per AC.SL.1 / AC.SL.2 etc."""
    if len(line) <= _MAX_LINE:
        return line
    return line[: _MAX_LINE - 1] + "…"


def _render_active(state: FirstRunState, now: float) -> str:
    """AC.SL.1 — active-phase line during ``starting`` or ``running``."""
    label = _PHASE_LABELS.get(state.phase, "setting up")
    elapsed = max(0.0, now - (state.started_at or now))
    remaining = _format_remaining(state, elapsed)
    parts = [
        f"pos-v2 setting up: {label}",
        f"{_format_elapsed(elapsed)} elapsed",
    ]
    if remaining:
        parts.append(remaining)
    return _truncate(" · ".join(parts))


def _render_completed(state: FirstRunState, now: float) -> str:
    """AC.SL.2 — steady-state then blank.

    Per D2 ruling: render "pos-v2 ready" for the first 60 s after
    ``updated_at``, then return empty string (status line blanks).
    """
    age = now - (state.updated_at or 0.0)
    if age < _COMPLETED_STEADY_STATE_S:
        return _truncate("pos-v2 ready")
    return ""


def _render_failed(state: FirstRunState) -> str:
    """AC.SL.3 — glanceable failure summary, no JSON keys, no traceback."""
    detail = (state.detail or "").strip()
    # Strip the worker's "category:label" prefix if present so the line
    # reads in plain English (the SessionStart additionalContext path
    # carries the structured remediation).
    if detail and ":" in detail:
        head, tail = detail.split(":", 1)
        # Only collapse the prefix when the head looks like a
        # category-label key (no spaces, ASCII).
        if head and " " not in head and all(c.isalnum() or c in "-_" for c in head):
            detail = tail.strip()
    if not detail:
        detail = "see SessionStart context for details"
    return _truncate(f"pos-v2 first-run failed — {detail}")


def _render_stalled() -> str:
    """AC.SL.5 — silent-death summary line."""
    return _truncate(
        "pos-v2 first-run stalled — reopen Claude to retry"
    )


def _resolve_project_dir(envelope: dict) -> Path | None:
    """Pull ``workspace.project_dir`` from the stdin envelope.

    Per D3: the renderer's source of truth for the workspace path is
    the Claude Code status-line stdin envelope, NOT environment
    variables (rejected at research time). Returns None when the
    field is absent or malformed.
    """
    workspace = envelope.get("workspace")
    if not isinstance(workspace, dict):
        return None
    project_dir = workspace.get("project_dir")
    if not isinstance(project_dir, str) or not project_dir:
        return None
    try:
        return Path(project_dir).expanduser()
    except (OSError, RuntimeError):
        return None


def render(envelope: dict, *, now: float | None = None) -> str:
    """Pure rendering entry point. Returns the line to print (may be empty).

    Stdin parsing happens in ``main``; this function takes the parsed
    envelope so unit tests can exercise every branch without touching
    the process boundary. Per AC.SL.1 / AC.SL.2 / AC.SL.3 / AC.SL.4 /
    AC.SL.5 every branch caps at ``_MAX_LINE`` chars and returns ""
    on the no-render paths.
    """
    project_dir = _resolve_project_dir(envelope)
    if project_dir is None:
        return ""
    if not state_path(project_dir).exists():
        return ""
    state = read_state(project_dir)
    if state is None:
        return ""
    if not _state_belongs_to(state, project_dir):
        return ""

    t = time.time() if now is None else now

    # Stale-live check first — a "running" state whose pid is gone
    # belongs to AC.SL.5, not AC.SL.1. Use a 0-second grace window
    # so the test fixture (with a non-existent pid) trips the
    # branch immediately; production callers see ``updated_at``
    # naturally aging so the grace window is moot.
    if is_stale_live_state(state, stale_after_s=0.0):
        return _render_stalled()

    if state.status == "completed":
        return _render_completed(state, t)
    if state.status == "failed":
        return _render_failed(state)
    if state.status in ("starting", "running"):
        return _render_active(state, t)
    # Unknown status — empty render (defence in depth against future
    # state-file shapes that haven't been admitted to AC.SL.1-5).
    return ""


def main(argv: list[str] | None = None) -> int:  # noqa: ARG001
    """Process entry point.

    Reads stdin JSON (Claude Code status-line envelope); calls
    ``render``; prints stdout; exits 0. Any exception is swallowed
    to preserve the fail-closed contract (locked plan §5).
    """
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return 0
        try:
            envelope = json.loads(raw)
        except json.JSONDecodeError:
            return 0
        if not isinstance(envelope, dict):
            return 0
        line = render(envelope)
        if line:
            print(line)
    except Exception:  # noqa: BLE001 — fail-closed per locked plan §5
        return 0
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
