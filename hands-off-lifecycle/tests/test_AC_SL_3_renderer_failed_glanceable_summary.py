"""AC.SL.3 — failure-state glanceable summary.

Outcome (per locked plan §4): when the state-file ``status`` is
``failed``, the renderer produces a glanceable failure line containing
a plain-English summary derived from the file's ``detail`` field
(no traceback, no JSON keys, ≤ 200 chars) and exits 0.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_state import FirstRunState, write_state  # noqa: E402
from statusline import _MAX_LINE, render  # noqa: E402


def test_AC_SL_3_failure_summary_strips_kind_prefix(tmp_path: Path) -> None:
    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    now = time.time()
    state = FirstRunState(
        status="failed",
        pid=0,
        started_at=now - 30.0,
        updated_at=now,
        phase="phase-3b-shared-deps",
        detail=(
            "pip-install-failed:memory-system: connection-reset by upstream"
        ),
        error_code=-32097,
        remediation="check network or proxy settings, then reopen claude.",
        workspace_root=str(workspace.resolve()),
    )
    write_state(state, workspace)

    envelope = {"workspace": {"project_dir": str(workspace)}}
    line = render(envelope)

    assert line, "expected glanceable failure summary, got empty line"
    assert "failed" in line.lower()
    # Plain-English content present.
    assert "connection-reset by upstream" in line, (
        f"summary missing plain-English detail: {line!r}"
    )
    # No raw kind prefix.
    assert "pip-install-failed:" not in line, (
        f"summary should strip the category prefix: {line!r}"
    )
    # No error_code numeric prefix.
    assert "-32097" not in line, (
        f"summary should not surface the error code: {line!r}"
    )
    # No traceback (no "Traceback" word; no Python file path).
    assert "Traceback" not in line
    assert len(line) <= _MAX_LINE


def test_AC_SL_3_failure_summary_handles_empty_detail(tmp_path: Path) -> None:
    workspace = tmp_path / "pos-v2"
    workspace.mkdir()
    now = time.time()
    state = FirstRunState(
        status="failed",
        pid=0,
        started_at=now - 30.0,
        updated_at=now,
        phase="",
        detail="",
        workspace_root=str(workspace.resolve()),
    )
    write_state(state, workspace)

    envelope = {"workspace": {"project_dir": str(workspace)}}
    line = render(envelope)

    assert line, "empty-detail failure should still produce a fallback line"
    assert "failed" in line.lower()
    assert len(line) <= _MAX_LINE
