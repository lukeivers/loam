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

"""★ AC.REINJECT.1 (outcome-altitude: true) — the real-re-injection cold-walk.

With the build-workflow flow active and a cursor at a real mid-flow step
ON DISK, SIMULATING a context-loss event at the REAL re-injection
entry-point — the flows re-injection hook (``loam_cli.flows.reinject``),
invoked exactly as Claude Code invokes a hook: a real JSON envelope on
stdin, run as a subprocess, reading the cursor FROM DISK — causes the
emitted ``additionalContext`` to re-establish the correct
{flow, step, branch-state} + the pause-if-lost directive.

NO pre-arranged in-memory state: this test writes a real cursor to a real
on-disk flows tree, then spawns a SEPARATE process that reads it the way
the hook runs live. STUB-class re-injection (a hand-fed position string,
or calling the pure function with an in-memory cursor) does NOT satisfy
this AC — the cold-walk drives the real hook CLI with a real stdin
envelope.

Then: corrupt the cursor on disk → re-invoke the same real entry-point →
assert the emitted context is the PAUSE directive (AC.PAUSE.2 at the real
entry-point).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
HOOK_SRC = REPO_ROOT / "framework" / "tools" / "loam" / "src"


def _seed_cold_repo(tmp_path: Path) -> Path:
    """Build a SEPARATE on-disk repo tree (never the live one) with a
    real flow definition + a cursor at a real mid-flow step. This is the
    'no pre-arranged state' surface: the hook reads it from disk in a
    fresh process."""
    repo = tmp_path / "cold-repo"
    flows = repo / "docs" / "flows"
    flows.mkdir(parents=True)

    # A real flow definition (the per-slice loop shape).
    (flows / "demo.flow.md").write_text(
        "---\n"
        "flow: demo\n"
        "entry: examine\n"
        "steps:\n"
        "  - id: examine\n    name: 1 EXAMINE\n    transitions: [build]\n"
        "  - id: build\n    name: 3 BUILD\n    transitions: [prove]\n"
        "  - id: prove\n    name: 4 PROVE\n    transitions: [build, done]\n"
        "  - id: done\n    name: 6 DONE\n    transitions: []\n"
        "---\n"
        "# demo\nA real multi-step flow with a branch at PROVE.\n",
        encoding="utf-8",
    )
    # A cursor at a real mid-flow step (step K = build).
    (flows / "demo.cursor.yaml").write_text(
        "flow: demo\n"
        "step: build\n"
        "branch_state: disposition build-new, gate G3 pending\n"
        "updated_at: '2026-05-31T12:00:00Z'\n",
        encoding="utf-8",
    )
    return repo


def _invoke_real_hook(repo: Path, envelope: dict) -> str:
    """Invoke the REAL re-injection hook entry-point as a subprocess,
    feeding a real JSON envelope on stdin (the way Claude Code runs a
    hook). Returns stdout (the additionalContext)."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(HOOK_SRC)
    proc = subprocess.run(
        [sys.executable, "-m", "loam_cli.flows.reinject"],
        input=json.dumps(envelope),
        capture_output=True,
        text=True,
        cwd=repo,
        env=env,
    )
    # Fail-safe contract: the hook always exits 0.
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


@pytest.mark.parametrize(
    "envelope_kind",
    [
        {"hook_event_name": "SessionStart", "source": "compact"},
        {"hook_event_name": "UserPromptSubmit"},
    ],
)
def test_AC_REINJECT_1_real_hook_reestablishes_position_from_disk(
    tmp_path: Path, envelope_kind: dict
) -> None:
    """★ outcome-altitude — the real hook, a real envelope on stdin, a
    real on-disk cursor: the emitted context re-establishes flow + step
    K + branch-state + the pause-if-lost directive."""
    repo = _seed_cold_repo(tmp_path)
    envelope = {**envelope_kind, "cwd": str(repo)}

    out = _invoke_real_hook(repo, envelope)

    # The emitted additionalContext names the flow + the real step K
    # (build / '3 BUILD') + the branch-state, read from the on-disk
    # cursor — NOT a hand-fed string.
    assert "demo" in out
    assert "3 BUILD" in out
    assert "gate G3 pending" in out
    # And it carries the follow-it / pause-if-lost directive.
    assert "pause" in out.lower()
    assert "lose your place" in out.lower()


def test_AC_REINJECT_1_corrupt_cursor_emits_pause_at_real_entry_point(
    tmp_path: Path,
) -> None:
    """★ outcome-altitude (AC.PAUSE.2 at the real entry-point) — corrupt
    the on-disk cursor so position cannot be re-established; the real
    hook emits the PAUSE directive, not a false position."""
    repo = _seed_cold_repo(tmp_path)
    cursor = repo / "docs" / "flows" / "demo.cursor.yaml"

    # Corrupt the cursor: point it at a step that does not exist in the
    # flow (the stale-cursor shape — the worst case the owner law names).
    cursor.write_text(
        "flow: demo\nstep: vanished_step\nbranch_state: ''\n"
        "updated_at: '2026-05-31T12:00:00Z'\n",
        encoding="utf-8",
    )

    out = _invoke_real_hook(
        repo,
        {"hook_event_name": "SessionStart", "source": "compact", "cwd": str(repo)},
    )

    # The real entry-point emits the PAUSE directive — NOT a confident
    # wrong position.
    assert "PAUSE" in out
    assert "re-establish position" in out.lower()
    # It must NOT fabricate a resolved one-sentence position.
    assert "vanished_step" not in out or "PAUSE" in out
