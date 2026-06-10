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

"""★ AC.EWR.S (outcome-altitude) — the REAL Claude Code SubagentStart
envelope shape (``cwd`` only, NO ``workspace`` dict — the shape observed
live on a real dispatched agent, Tier-0 2026-06-10) driven end-to-end
through the PRODUCTION hook entry-point yields a NON-degraded
microkernel tier against the real on-disk kernel.

outcome-altitude: true

This is the real-shape twin of AC.SACH.S. That probe's synthetic
envelope used ``workspace.project_dir`` — a shape real envelopes do not
carry — which is exactly why the 1a contract gap shipped unobserved:
the synthetic probe passed while every real dispatch degraded all three
tiers to placeholders. This regression test pins the REAL shape through
the same production spine (the hook script as a subprocess under the
venv interpreter, a real envelope on stdin, the REAL repo-root
``kernel/loam-microkernel.md`` read from disk, NOTHING pre-arranged).
n=1 architectural verdict (does the real envelope shape populate the
bundle AT ALL?) per feedback_n1_architectural_vs_n3_statistical.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from conftest import KERNEL_FILE, REPO_ROOT

from loam.frame_kernel.bundle import (
    MICROKERNEL_PRIME_MARKER,
    MISSING_KERNEL_MARKER,
)

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


def test_AC_EWR_S_real_cwd_only_envelope_yields_nondegraded_microkernel() -> None:
    """★ outcome-altitude: drive the REAL production hook invocation with
    the REAL observed envelope shape (cwd-only); assert the injected
    additionalContext carries the real on-disk microkernel, NOT the
    degraded missing-marker."""
    # The REAL SubagentStart envelope shape observed live (Tier-0,
    # 2026-06-10): the standard hook common-input ``cwd`` field; NO
    # ``workspace`` dict.
    envelope = {
        "hook_event_name": "SubagentStart",
        "cwd": str(REPO_ROOT),
        "prompt": "scoped sub-task: report the first lines of your injected context",
    }

    proc = subprocess.run(
        [_venv_python(), str(_HOOK_PATH)],
        input=json.dumps(envelope),
        capture_output=True,
        text=True,
        timeout=30,
    )

    # (a) The production hook exited clean (never aborts the dispatch —
    #     AC.SACH.4 unchanged).
    assert proc.returncode == 0, (
        f"production hook exited {proc.returncode}; stderr:\n{proc.stderr}"
    )

    # (b) The emitted stdout is the additionalContext envelope Claude
    #     Code injects into the dispatched subagent's context.
    payload = json.loads(proc.stdout)
    out = payload["hookSpecificOutput"]
    assert out["hookEventName"] == "SubagentStart"
    injected = out["additionalContext"]

    # (c) ★ THE outcome-altitude assertion: the microkernel tier is
    #     NON-degraded on the REAL envelope shape. Pre-fix this failed:
    #     the marker was present but the tier carried
    #     MISSING_KERNEL_MARKER (workspace_root=None on every real
    #     dispatch).
    assert MICROKERNEL_PRIME_MARKER in injected
    assert MISSING_KERNEL_MARKER not in injected, (
        "REGRESSION (AC.EWR.S): the real cwd-only envelope shape "
        "degraded the microkernel tier — workspace_root did not resolve "
        "from the envelope's cwd field."
    )

    # (d) The injected content is the REAL on-disk microkernel (no
    #     fixture stand-in) — the same verbatim-content guard AC.SACH.S
    #     applies.
    real_kernel = KERNEL_FILE.read_text(encoding="utf-8")
    assert "THREE ROLES" in real_kernel  # guard: the real file is the TCB
    assert "THREE ROLES" in injected, (
        "the injected microkernel is not the real on-disk kernel content"
    )
