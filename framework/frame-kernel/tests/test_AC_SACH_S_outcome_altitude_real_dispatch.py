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

"""★ AC.SACH.S (outcome-altitude) — a REAL subagent dispatch through the
PRODUCTION dispatch entry-point, with NO pre-arranged in-test bundle,
receives the microkernel in its context.

outcome-altitude: true

WHAT "production dispatch entry-point" means here + WHY (F2, named at
build time): the production SubagentStart dispatch path is the hook
SCRIPT exactly as ``settings.fragment.json`` registers it —
``${LOAM_REPO}/.venv/bin/python .../subagent_start_context.py`` reading a
real SubagentStart envelope on stdin and emitting the bundle as
``hookSpecificOutput.additionalContext``. This probe drives THAT real
invocation: a genuine subprocess under the venv interpreter, a real
SubagentStart envelope on stdin, the REAL on-disk repo-root
``kernel/loam-microkernel.md`` read from disk (NOT a fixture copy, NOT a
monkeypatched bundle, NOTHING pre-arranged). The "subagent receives the
microkernel" outcome IS the additionalContext the real production
invocation injects — that is what Claude Code hands the dispatched
subagent verbatim.

This probe does NOT spawn a live ``claude -p`` subagent from inside
pytest: there is no Anthropic API key in this environment (subscription
-only via ``claude -p``; see feedback_no_anthropic_api_key) and spawning
an un-isolated ``claude`` from a sealed unit test is both flaky and a
Telegram-slot-steal hazard. The altitude this probe sets is the SAME one
AC.SWARM.4 sets for the swarm leaf dispatch — the REAL production spine
end-to-end, the spawn primitive exercised through its real registered
mechanism. n=1 architectural verdict (does SubagentStart
additionalContext carry the microkernel AT ALL?) per
feedback_n1_architectural_vs_n3_statistical.

§8 halt-trigger #1: if this probe comes back WITHOUT the microkernel, the
build HALTS — the mechanism is infeasible in the running Claude Code
version. (Build-time result quoted in the build report.)
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import KERNEL_FILE, REPO_ROOT

from loam.frame_kernel.bundle import MICROKERNEL_PRIME_MARKER

_HOOK_PATH = (
    REPO_ROOT / "framework" / "frame-kernel" / "hooks" / "subagent_start_context.py"
)


def _venv_python() -> str:
    """Return the workspace venv Python the fragment names, else the
    ambient interpreter (so the probe runs in CI environments without a
    .venv)."""
    venv_py = REPO_ROOT / ".venv" / "bin" / "python"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def test_AC_SACH_S_real_dispatch_receives_microkernel() -> None:
    """★ outcome-altitude: drive the REAL production hook invocation with
    a real SubagentStart envelope; assert the injected additionalContext
    a dispatched subagent would receive carries the microkernel.

    No pre-arranged state: the envelope points project_dir at the real
    repo root, so the hook reads the REAL kernel/loam-microkernel.md off
    disk. The returned additionalContext IS what Claude Code injects into
    the subagent's context.
    """
    # A real SubagentStart envelope — the shape Claude Code delivers:
    # workspace.project_dir + the dispatch prompt (task text seed).
    envelope = {
        "hook_event_name": "SubagentStart",
        "workspace": {"project_dir": str(REPO_ROOT)},
        "prompt": "scoped sub-task: report the first lines of your injected context",
    }

    proc = subprocess.run(
        [_venv_python(), str(_HOOK_PATH)],
        input=json.dumps(envelope),
        capture_output=True,
        text=True,
        timeout=30,
    )

    # (a) The production hook exited clean (never aborts the dispatch).
    assert proc.returncode == 0, (
        f"production hook exited {proc.returncode}; stderr:\n{proc.stderr}"
    )

    # (b) The emitted stdout is the additionalContext envelope Claude Code
    #     injects into the dispatched subagent's context.
    payload = json.loads(proc.stdout)
    out = payload["hookSpecificOutput"]
    assert out["hookEventName"] == "SubagentStart"
    injected = out["additionalContext"]

    # (c) ★ THE outcome-altitude assertion: the microkernel's
    #     prime-directive marker is in the context the subagent receives.
    #     If this is absent, §8 halt-trigger #1 fires (mechanism
    #     infeasible) — HALT, do not seal.
    assert MICROKERNEL_PRIME_MARKER in injected, (
        "HALT (plan §8 trigger #1): SubagentStart additionalContext did "
        "NOT carry the microkernel. The mechanism is infeasible in the "
        "running Claude Code version."
    )

    # (d) The injected content is the REAL on-disk microkernel (no
    #     fixture stand-in): a stable, load-bearing line from the shipped
    #     kernel file is present verbatim in the subagent's context.
    real_kernel = KERNEL_FILE.read_text(encoding="utf-8")
    assert "THREE ROLES" in real_kernel  # guard: the real file is the TCB
    assert "THREE ROLES" in injected, (
        "the injected microkernel is not the real on-disk kernel content"
    )
    # The three-role identity reached the subagent.
    for role in ("RUNTIME", "PLATFORM", "PRODUCT"):
        assert role in injected
