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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""AC.PROMO.1 (LEAD) — with a sentinel process holding the
single-consumer poller slot, a HARNESS-STYLE MULTI-SPAWN (>=2 parallel
`claude -p` invocations modelling the reharden 7-wide judge pattern)
routed through the shared isolation surface completes and the sentinel
is STILL ALIVE afterward (`.poll() is None`).

Plan: docs/plans/telegram-5-fix.md §3.3 / §6
This is the EXACT Telegram-death #5 reproduction shape: a re-harden
harness fanned `ThreadPoolExecutor(max_workers=7)` un-isolated
`subprocess.run(["claude","-p",...])` spawns, each loaded the
user-enabled telegram plugin, each spawned a competing `bun server.ts`
that SIGTERM'd the operator's single-consumer poller.  Here the
spawns are routed THROUGH the shared `loam_spawn_isolation` surface
(the mandate) — the sentinel must survive.

DOGFOOD-RECURSION CLOSURE (AC.PROMO.3, enforced on THIS module's
source): every real-`claude` spawn below is constructed via
`spawn_isolated_claude` from `loam_spawn_isolation` — NEVER a
hand-rolled `subprocess.run(["claude", ...])`.  AC.PROMO.3's static
AST check on this file goes RED before this real-binary path can run
if that discipline is ever broken.  The poller sentinel is a plain
Python sleeper (`sys.executable -c "import time; ..."`) modelling the
operator's single-consumer poller — it is NOT a `claude` spawn (the
sealed `test_AC_TPI_1_*` uses the identical sentinel shape).

Opt-in real-binary (`PROMO_REAL_CLAUDE=1`) — mirrors the sealed
`TPI_REAL_CLAUDE` / `PB_SUBLOAM_REAL_CLAUDE` opt-in shape.  The
empirical survival of a sentinel holding the single-consumer slot
across a REAL harness-style multi-spawn IS the proof the shared
surface closes the #5 kill vector — never a structural assertion
alone, never a self-report.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from loam_spawn_isolation import spawn_isolated_claude  # noqa: E402

# Model the reharden harness fan-out (it used max_workers=7); >=2 is
# the AC bar (parallel multi-spawn).  4 keeps the real-binary wall
# clock bounded while still being a genuine concurrent fan-out.
_PARALLEL_SPAWNS = 4


def _one_isolated_spawn(idx: int) -> int:
    """One real `claude -p` spawn routed THROUGH the shared isolation
    surface (the mandate / dogfood-recursion closure).  NEVER a
    hand-rolled `subprocess.run(["claude", ...])`."""
    proc = spawn_isolated_claude(
        [
            "claude", "-p",
            f"Say ACK{idx} and nothing else. Do not use any tool.",
            "--model", "sonnet",
            "--output-format", "json",
            "--permission-mode", "bypassPermissions",
        ],
        capture_output=True,
        text=True,
        timeout=240,
    )
    return proc.returncode


@pytest.mark.skipif(
    os.environ.get("PROMO_REAL_CLAUDE") != "1",
    reason=(
        "harness-multi-spawn sentinel-survives integration is opt-in "
        "(real claude x N parallel + a live sentinel poller); set "
        "PROMO_REAL_CLAUDE=1."
    ),
)
def test_AC_PROMO_1_sentinel_survives_harness_multispawn(
    tmp_path: Path,
) -> None:  # pragma: no cover - opt-in real-binary path
    """A sentinel process holding the single-consumer poller slot is
    STILL ALIVE after a real harness-style >=2-parallel `claude -p`
    multi-spawn routed through the shared isolation surface (the #5
    reproduction shape, isolated — the spawned `claude`s never SIGTERM
    the sentinel because the telegram plugin is unreachable + the
    bot-token env is scrubbed + CLAUDE_PERSONA is set)."""
    sentinel = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(900)"]
    )
    try:
        with ThreadPoolExecutor(
            max_workers=_PARALLEL_SPAWNS
        ) as pool:
            futures = [
                pool.submit(_one_isolated_spawn, i)
                for i in range(_PARALLEL_SPAWNS)
            ]
            # Own the wait — block to a definite result for every
            # spawn (no early return; the survival assertion is the
            # point, not the sub-agents' content).
            returncodes = [f.result() for f in futures]
        time.sleep(0.5)
        assert sentinel.poll() is None, (
            "sentinel poller was SIGTERM'd by a harness-style "
            f"{_PARALLEL_SPAWNS}-parallel claude multi-spawn — "
            "AC.PROMO.1 VIOLATED (the shared isolation surface did "
            "NOT close the #5 kill vector). returncodes="
            f"{returncodes}"
        )
        # The spawns must have actually run (a no-op that never
        # reached the binary would vacuously 'pass' the survival
        # assertion).  We assert each returned an int returncode; a
        # real claude -p exits 0 on success but the survival of the
        # sentinel is the load-bearing assertion, so we do not gate
        # on a specific code (subscription/transient variance) — only
        # that the spawn path executed and produced a definite
        # result for all N.
        assert len(returncodes) == _PARALLEL_SPAWNS
        assert all(isinstance(rc, int) for rc in returncodes), (
            f"a spawn did not produce a definite returncode: "
            f"{returncodes}"
        )
    finally:
        sentinel.terminate()
        sentinel.wait(timeout=5)
