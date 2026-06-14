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

"""AC.CLP-ADOPT.5 ★ (no pre-arranged state) — a deliberately-bespoke
KEEP-GOING dispatch through the PRODUCTION PreToolUse path produces the
guard's observable check event naming ``/goal``.

This is the Slice-3 worked example of the Slice-2 prefer-the-primitive
doctrine: Slice 2 shipped the dispatch-time guard
(``primitive_check_guard.py``) + its matcher table
(``primitive_check_matchers.ROWS``), but that table covered only
schedule / loop / background-agents / hooks — there was NO row for the
bespoke keep-going / drive-to-goal work-shape that ``/goal`` covers, so
a bespoke keep-going dispatch was NOT caught. Slice 3 closes that gap by
adding the ``goal.md``-keyed deny + warn rows; this test verifies a
bespoke keep-going dispatch is now denied on the real fire path and the
deny names ``/goal`` + its corpus entry.

The production entry-point is ``primitive_check_guard.main()`` reading
the PreToolUse JSON envelope from stdin exactly as Claude Code invokes
it. This test runs the hook AS A SUBPROCESS (the real fire surface),
feeds it a hand-authored bespoke keep-going dispatch envelope, and
observes the deny payload on stdout + the NDJSON audit line on disk. No
production state is pre-arranged: the only setup is the dev-mode marker
the hook itself requires to be active, authored into a fresh tmp
workspace exactly as a real bootstrapped workspace carries it.

The dispatch prompt uses a keep-going phrase ("keep going until ...")
that the ``goal.md`` row uniquely owns — the loop.md / schedule.md /
background-agents rows do not match it — so the deny is attributed to
``/goal``, not a sibling primitive.

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

# The hook reads workspace-mode through loam_mode, installed in the
# workspace venv — the production interpreter for this fire path. Fall
# back to sys.executable only if the venv is absent.
_VENV_PYTHON = REPO_ROOT / ".venv" / "bin" / "python"
PYTHON = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else sys.executable


def _dev_mode_workspace(tmp_path: Path) -> Path:
    """Author the real dev-mode persona contract a bootstrapped
    workspace carries (same shape the AC.CLP-DOC.2 production-path test
    uses — the hook reads ``dev_intent: yes`` through the production
    reader, no monkeypatch)."""
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


def test_AC_CLP_ADOPT_5_bespoke_keep_going_dispatch_denied_naming_goal(
    tmp_path,
) -> None:
    """A bespoke 'build a loop that keeps going until the build is
    green' dispatch with no primitive-rationale line, fed through the
    real hook subprocess, yields a deny payload naming ``/goal`` + its
    ``goal.md`` corpus entry + the audit record on disk. No pre-arranged
    production state."""
    ws = _dev_mode_workspace(tmp_path)

    # Verify the workspace really reads as dev-mode through the
    # PRODUCTION reader (run under the venv interpreter the hook fires
    # with). Else the outcome is vacuous and we skip rather than assert
    # a false green.
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
            "is additionally covered by the matcher-row precision test.)"
        )

    envelope = {
        "session_id": "test",
        "cwd": str(ws),
        "hook_event_name": "PreToolUse",
        "tool_name": "Task",
        "tool_input": {
            "description": "bespoke keep-going build",
            "prompt": (
                "Build a continuation loop that keeps going until the "
                "build is green — re-dispatch the sub-agent each turn "
                "and only stop when the acceptance check passes."
            ),
        },
    }

    stdout, rc = _run_hook(ws, envelope)
    assert rc == 0, "hook must exit 0 (fail-open contract)"

    payload = json.loads(stdout) if stdout.strip() else {}
    decision = payload.get("hookSpecificOutput", {}).get("permissionDecision")
    assert decision == "deny", (
        f"bespoke keep-going dispatch must be denied on the production "
        f"path; got stdout={stdout!r}"
    )
    reason = payload["hookSpecificOutput"]["permissionDecisionReason"]
    assert "/goal" in reason, (
        "deny reason must name the matched native primitive (/goal) — "
        "this is the Slice-3 coverage the matcher row adds"
    )
    assert "goal.md" in reason, (
        "deny reason must point at the goal.md corpus entry (the "
        "single refresh-kept claims surface for the primitive)"
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
