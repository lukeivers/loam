"""AC.SL.1 — renderer active-phase line during ``starting`` / ``running``.

Outcome (per locked plan §4): when the worker's state file declares a
non-terminal status with one of the recognised phase strings, the
renderer prints a one-line plain-English progress line containing the
phase's plain-English label, an elapsed-seconds token (``Xm Ys``),
and a remaining-time estimate. ≤ 200 chars; exit 0.

Covers AC.SL.1 across the worker's recognised phase set (one fixture
per phase the worker writes via ``_advance_state``).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_state import FirstRunState, write_state  # noqa: E402
from statusline import _MAX_LINE, render  # noqa: E402


_PHASES = [
    ("phase-2-venv-creation", "creating Python environment"),
    ("phase-3a-inventory", "reading install manifest"),
    ("phase-3b-shared-deps", "installing shared dependencies"),
    ("phase-3e-editable-installs", "registering component packages"),
    ("phase-3c-dedicated-venvs", "installing heavy dependencies"),
    ("phase-4a-scaffold", "writing config files"),
    ("phase-4b-health-poll", "starting background services"),
    ("phase-4c-agent-file-authorship", "preparing your assistant"),
    ("phase-5-confirmation", "finishing up"),
    ("phase-6-self-retire", "finishing up"),
]


@pytest.mark.parametrize("phase,label", _PHASES)
def test_AC_SL_1_active_phase_line_contains_label_elapsed_estimate(
    tmp_path: Path,
    phase: str,
    label: str,
) -> None:
    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    started = time.time() - 90.0  # 1m 30s elapsed
    state = FirstRunState(
        status="running",
        pid=os.getpid(),
        started_at=started,
        updated_at=time.time(),
        phase=phase,
        workspace_root=str(workspace.resolve()),
        progress_pct=25,
    )
    write_state(state, workspace)

    envelope = {"workspace": {"project_dir": str(workspace)}}
    line = render(envelope)

    assert line, f"renderer returned empty line for phase {phase!r}"
    assert label in line, (
        f"phase {phase!r}: rendered line {line!r} missing label {label!r}"
    )
    # Elapsed token shape: "Xm Ys" for >= 60 s elapsed.
    assert "elapsed" in line, (
        f"phase {phase!r}: rendered line missing elapsed token: {line!r}"
    )
    assert "1m" in line, (
        f"phase {phase!r}: expected '1m' in elapsed token: {line!r}"
    )
    # Remaining estimate token — either "less than a minute remaining"
    # or "about N min remaining".
    assert "remaining" in line, (
        f"phase {phase!r}: rendered line missing remaining estimate: {line!r}"
    )
    assert len(line) <= _MAX_LINE, (
        f"phase {phase!r}: rendered line exceeds {_MAX_LINE} chars: "
        f"len={len(line)}"
    )


def test_AC_SL_1_starting_status_renders_active_line(tmp_path: Path) -> None:
    """``status=starting`` is also an active branch (per AC.SL.1 wording)."""
    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    state = FirstRunState(
        status="starting",
        pid=os.getpid(),
        started_at=time.time() - 5.0,
        updated_at=time.time(),
        phase="phase-2-venv-creation",
        workspace_root=str(workspace.resolve()),
    )
    write_state(state, workspace)

    envelope = {"workspace": {"project_dir": str(workspace)}}
    line = render(envelope)

    assert line, "starting status produced empty line"
    assert "creating Python environment" in line
    assert "5s elapsed" in line
