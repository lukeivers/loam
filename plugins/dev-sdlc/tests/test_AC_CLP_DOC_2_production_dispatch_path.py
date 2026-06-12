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

"""AC.CLP-DOC.2 ★ (outcome-altitude) — a deliberately-bespoke dispatch
through the PRODUCTION PreToolUse path produces the observable check
event, with no pre-arranged state.

The production entry-point is ``primitive_check_guard.main()`` reading
the PreToolUse JSON envelope from stdin exactly as Claude Code invokes
it. This test runs the hook AS A SUBPROCESS (the real fire surface),
feeds it a hand-authored bespoke dispatch envelope, and observes the
deny payload on stdout + the NDJSON audit line on disk. No production
state is pre-arranged: the only setup is the dev-mode marker the hook
itself requires to be active (NORMAL-USE workspaces are out of the
dispatch-path-enforcement scope per master §2 row 4), authored into a
fresh tmp workspace exactly as a real bootstrapped workspace carries it.

Outcome-altitude: the entry point is the production CLI, the envelope is
the production envelope, and the observable is the production deny +
audit record — not an internal helper called with arranged arguments.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOK = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks" / "primitive_check_guard.py"

# The hook reads workspace-mode through loam_mode, which is installed in
# the workspace venv. Claude Code invokes shipped PreToolUse guards with
# the workspace venv's interpreter (the first_run_helper wiring resolves
# the guard command under sys.executable at registration time inside the
# venv); the venv python is therefore the production interpreter for this
# fire path. Fall back to sys.executable only if the venv is absent.
_VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
PYTHON = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else sys.executable


def _dev_mode_workspace(tmp_path: Path) -> Path:
    """Author the real dev-mode persona contract a bootstrapped
    workspace carries.

    The hook reads workspace-mode through the production reader
    (``corpus_load_sentinel.workspace_mode`` →
    ``loam_mode.read_dev_intent_safe`` → the persona contract's
    ``dev_intent`` field). A dev-mode workspace carries
    ``<ws>/workspace/personas/primary/contract.yaml`` with
    ``dev_intent: yes`` (the contract shape verified against the
    existing hands-off-lifecycle tests). We author exactly that — no
    monkeypatch, the real fire path end-to-end.
    """
    persona_dir = tmp_path / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True, exist_ok=True)
    (persona_dir / "contract.yaml").write_text(
        "is_primary: true\ndev_intent: yes\n", encoding="utf-8"
    )
    return tmp_path


def _run_hook(workspace_root: Path, envelope: dict) -> tuple[str, int]:
    proc = subprocess.run(
        [PYTHON, str(HOOK)],
        input=json.dumps(envelope),
        capture_output=True,
        text=True,
        cwd=str(workspace_root),
    )
    return proc.stdout, proc.returncode


def test_AC_CLP_DOC_2_bespoke_dispatch_denied_on_production_path(
    tmp_path,
) -> None:
    """A bespoke 'build a polling loop that re-checks every hour'
    dispatch with no primitive-rationale line, fed through the real
    hook subprocess, yields a deny payload naming the matched primitive
    + the audit record on disk. No pre-arranged production state."""
    ws = _dev_mode_workspace(tmp_path)

    # Verify the workspace really reads as dev-mode through the
    # PRODUCTION reader (run under the venv interpreter the hook fires
    # with — the test interpreter lacks loam_mode). Else the outcome is
    # vacuous and we skip rather than assert a false green.
    probe = subprocess.run(
        [
            PYTHON,
            "-c",
            (
                "import sys; sys.path.insert(0, "
                f"{str(REPO_ROOT / 'framework' / 'hands-off-lifecycle' / 'hooks')!r}); "
                "import corpus_load_sentinel as c; "
                f"print(c.workspace_mode({str(ws)!r}))"
            ),
        ],
        capture_output=True,
        text=True,
    )
    if probe.stdout.strip() != "dev-mode":
        pytest.skip(
            "venv loam_mode unavailable; the production-path assertion "
            "needs a dev-mode-readable workspace. (The fire-path logic "
            "is additionally covered by the in-process evaluate() AC "
            "tests.)"
        )

    envelope = {
        "session_id": "test",
        "cwd": str(ws),
        "hook_event_name": "PreToolUse",
        "tool_name": "Task",
        "tool_input": {
            "description": "bespoke build",
            "prompt": (
                "Build a polling loop that re-checks the deploy status "
                "every hour and reports when it goes green."
            ),
        },
    }

    stdout, rc = _run_hook(ws, envelope)
    assert rc == 0, "hook must exit 0 (fail-open contract)"

    payload = json.loads(stdout) if stdout.strip() else {}
    decision = (
        payload.get("hookSpecificOutput", {}).get("permissionDecision")
    )
    assert decision == "deny", (
        f"bespoke dispatch must be denied on the production path; "
        f"got stdout={stdout!r}"
    )
    reason = payload["hookSpecificOutput"]["permissionDecisionReason"]
    assert "/loop" in reason, (
        "deny reason must name the matched native primitive (/loop)"
    )
    assert "primitive-rationale:" in reason, (
        "deny reason must name the one-line fix (the rationale hatch)"
    )

    # The audit record exists on disk (observable event).
    log = ws / "workspace" / ".pos" / "primitive-check-guard.log"
    assert log.exists(), "fire must leave an NDJSON audit record"
    last = log.read_text(encoding="utf-8").strip().splitlines()[-1]
    row = json.loads(last)
    assert row["decision"] == "deny"
    assert row["kind"] == "deny"
