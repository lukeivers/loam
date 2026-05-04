"""D5 — cross-session continuity smoke.

Per smoke-test-discipline §2.5 + plan-doc §6 D5: state produced by
session A is retrievable and operationally meaningful in session B.

For the extractor, the "session boundary" is a fresh process —
exercised here via subprocess invocations of the CLI.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml


def _loam_cmd(*args: str, workspace_root: Path) -> tuple[int, str, str]:
    """Run `loam odd-extract <args>` in a SUBPROCESS (fresh process =
    cross-session boundary). Returns (rc, stdout, stderr).
    """
    cmd = [
        sys.executable,
        "-m",
        "loam_odd_extractor.cli",
        *args,
        "--workspace-root",
        str(workspace_root),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def test_state_yaml_persists_across_process_boundary(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Process A writes; process B reads; same state."""
    # Process A: full extraction.
    rc, stdout, stderr = _loam_cmd(
        str(fixture_repo), workspace_root=workspace_root
    )
    assert rc == 0, f"process A failed: {stderr}"

    # Process B: --status read.
    rc, stdout_b, stderr_b = _loam_cmd(
        str(fixture_repo),
        "--status",
        workspace_root=workspace_root,
    )
    assert rc == 0, f"process B failed: {stderr_b}"
    assert "all_stages_complete: True" in stdout_b


def test_resume_after_interrupted_run(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Run only --stage init in process A; --resume in process B
    runs the remaining stages."""
    rc, _, stderr = _loam_cmd(
        str(fixture_repo),
        "--stage",
        "init",
        workspace_root=workspace_root,
    )
    assert rc == 0, stderr

    repo_id_dir = next(
        (workspace_root / ".loam" / "extractions").iterdir()
    )
    state_a = yaml.safe_load(
        (repo_id_dir / "state.yaml").read_text(encoding="utf-8")
    )
    assert state_a["init_complete"] is True
    assert state_a["analyze_complete"] is False
    assert state_a["verify_complete"] is False

    rc, stdout_b, stderr_b = _loam_cmd(
        str(fixture_repo),
        "--resume",
        workspace_root=workspace_root,
    )
    assert rc == 0, stderr_b

    state_b = yaml.safe_load(
        (repo_id_dir / "state.yaml").read_text(encoding="utf-8")
    )
    assert state_b["init_complete"] is True
    assert state_b["analyze_complete"] is True
    assert state_b["generate_complete"] is True
    assert state_b["verify_complete"] is True


def test_resume_on_complete_extraction_is_noop(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """If all stages complete, --resume reports + does nothing."""
    rc, _, stderr = _loam_cmd(
        str(fixture_repo), workspace_root=workspace_root
    )
    assert rc == 0, stderr
    rc, stdout, stderr_b = _loam_cmd(
        str(fixture_repo),
        "--resume",
        workspace_root=workspace_root,
    )
    assert rc == 0, stderr_b
    assert "already complete" in stdout
