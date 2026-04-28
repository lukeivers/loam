"""AC.CI.3 — mode-partition refusal (NORMAL USE → no-op).

Per the locked plan-doc §4 AC.CI.3: on a SessionStart fan-out in a
workspace where ``workspace_mode`` returns ``normal-use``, the hook
fires, observes the mode bit, and exits 0 with empty stdout. No
additionalContext emission; no error; no sentinel update. The
persona's existing #46 dossier remains the NORMAL USE shape
unchanged.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK_SCRIPT = (
    REPO_ROOT
    / "framework"
    / "hands-off-lifecycle"
    / "hooks"
    / "corpus_inline_session_start.py"
)


def _make_normal_use_workspace(tmp_path: Path) -> Path:
    """Workspace with NO dev_intent answer → workspace_mode returns
    `normal-use` per A1's fail-closed-to-permissive contract."""
    # Provide the always-load files so we can prove they're NOT
    # emitted despite being readable.
    (tmp_path / "CLAUDE.md").write_text(
        "# Workspace CLAUDE — should NOT be emitted in normal-use.\n",
        encoding="utf-8",
    )
    rebuild_dir = tmp_path / "docs" / "rebuild"
    rebuild_dir.mkdir(parents=True, exist_ok=True)
    (rebuild_dir / "VALUE_PROPOSITION.md").write_text(
        "# VP — should NOT be emitted in normal-use.\n",
        encoding="utf-8",
    )
    (rebuild_dir / "STATE.md").write_text(
        "# STATE — should NOT be emitted in normal-use.\n",
        encoding="utf-8",
    )
    # Deliberately NO ``.pos/primary-persona-contract.yaml`` so
    # `workspace_mode` returns `normal-use` per A1's contract.
    return tmp_path


def _run_hook(workspace: Path, session_id: str = "sess-normal") -> tuple[str, int]:
    envelope = json.dumps(
        {
            "session_id": session_id,
            "workspace": {"project_dir": str(workspace)},
        }
    )
    result = subprocess.run(
        [sys.executable, str(HOOK_SCRIPT)],
        input=envelope,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.stdout, result.returncode


def test_AC_CI_3_normal_use_emits_empty_stdout(tmp_path: Path) -> None:
    """NORMAL USE workspace → hook exits 0 with empty stdout (no
    additionalContext emission)."""
    workspace = _make_normal_use_workspace(tmp_path)
    stdout, rc = _run_hook(workspace)
    assert rc == 0
    assert stdout == "" or stdout.strip() == "", (
        f"NORMAL USE hook should emit empty stdout; got {stdout!r}"
    )


def test_AC_CI_3_normal_use_does_not_emit_corpus_content(
    tmp_path: Path,
) -> None:
    """NORMAL USE workspace → no always-load content is leaked even
    though the workspace files exist on disk."""
    workspace = _make_normal_use_workspace(tmp_path)
    stdout, _rc = _run_hook(workspace)
    # Hidden marker text from the workspace files must not appear.
    assert "should NOT be emitted in normal-use" not in stdout
    # No banner text either.
    assert "=== pos-v2 always-loaded corpus" not in stdout
    assert "=== pos-v2 on-demand corpus" not in stdout


def test_AC_CI_3_normal_use_does_not_write_sentinel(
    tmp_path: Path,
) -> None:
    """NORMAL USE workspace → no per-(workspace, session) sentinel
    file is written by the corpus-inline hook (A1's
    `corpus_load_session_start.py` writes its own sentinel
    independently; this AC verifies the corpus-inline hook does
    not touch the sentinel in NORMAL USE)."""
    workspace = _make_normal_use_workspace(tmp_path)
    stdout, rc = _run_hook(workspace, session_id="sess-no-sentinel")
    assert rc == 0
    sentinel_path = (
        workspace / "workspace" / ".pos" / "session-state" /
        "sess-no-sentinel.json"
    )
    # The corpus-inline hook is the only thing running in this test
    # (A1's CLI is NOT invoked here), so the sentinel must NOT exist.
    assert not sentinel_path.exists()
