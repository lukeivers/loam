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

"""AC.TPI.1 — with a sentinel process holding the single-consumer
poller slot, a full handsoff-loop sub-agent dispatch
(`orchestrator._dispatch_subagent` via `build_goal_drive_argv`)
completes and the sentinel is still alive afterward (`.poll() is
None`).

Plan: docs/plans/telegram-poller-isolation-fix.md
Contract: pos3/.../telegram-isolation-fix-plan-2026-05-16.md §3.3
Mirrors the PROVEN subloam-driver acceptance shape
(`test_AC_LIPW_5_sentinel_poller_survives_full_driver_run`): one
opt-in EMPIRICAL poller-survives test (this file) + the fast structural
sentinels (AC.TPI.3/.4).  The empirical survival of a sentinel holding
the single-consumer slot across a REAL handsoff-loop spawn IS the proof
the §1b isolation closes the kill vector — never a structural assertion
alone, never a sub-agent self-report.

The SOLE kill vector (contract §2): a second `claude` that loads the
telegram plugin spawns a competing `bun server.ts` that SIGTERMs the
prior poller for the single bot-token getUpdates slot.  Removing the
telegram plugin from the spawned process's reachable set (empty
strict-MCP) + scrubbing the bot-token env is necessary AND sufficient.

Opt-in real-binary (`TPI_REAL_CLAUDE=1`) — mirrors the
`PB_SUBLOAM_REAL_CLAUDE` opt-in shape.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.goal_drive import GoalDriveSpec  # noqa: E402
from handsoff_loop.orchestrator import _dispatch_subagent  # noqa: E402


@pytest.mark.skipif(
    os.environ.get("TPI_REAL_CLAUDE") != "1",
    reason=(
        "sentinel-survives integration is opt-in (real claude + a "
        "live sentinel poller); set TPI_REAL_CLAUDE=1."
    ),
)
def test_AC_TPI_1_sentinel_poller_survives_handsoff_dispatch(
    tmp_path: Path,
) -> None:  # pragma: no cover - opt-in real-binary path
    """A sentinel process holding the single-consumer slot is still
    alive after a full real `/goal`-driven handsoff-loop sub-agent
    dispatch (the spawned `claude` never SIGTERMs it because the
    telegram plugin is unreachable + the bot-token env is scrubbed)."""
    sentinel = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(600)"]
    )
    try:
        spec = GoalDriveSpec(
            directive="Say ACK and stop. Do not run any tool.",
            check_command="true",
        )
        # A short timeout — the dispatch only needs to actually spawn a
        # real isolated `claude`; the survival assertion is about the
        # sentinel, not the sub-agent's completion.
        _dispatch_subagent(spec, work_dir=tmp_path, timeout=180)
        time.sleep(0.5)
        assert sentinel.poll() is None, (
            "sentinel poller was SIGTERM'd by a handsoff-loop dispatch "
            "— AC.TPI.1 VIOLATED (the §1b isolation did not close the "
            "kill vector)"
        )
    finally:
        sentinel.terminate()
        sentinel.wait(timeout=5)
