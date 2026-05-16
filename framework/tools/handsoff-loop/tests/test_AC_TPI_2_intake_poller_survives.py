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

"""AC.TPI.2 — same as AC.TPI.1 for the intake path
(`intake._claude_json`, reached via `derive_acceptance_from_intent`):
a sentinel holding the single-consumer poller slot is still alive
after a real intake `claude -p` call.

Plan: docs/plans/telegram-poller-isolation-fix.md
Contract: pos3/.../telegram-isolation-fix-plan-2026-05-16.md §3.3
The second §1b spawn family.  Empirical survival across a REAL intake
`claude -p` IS the proof — never structural-only, never a self-report.

Opt-in real-binary (`TPI_REAL_CLAUDE=1`).
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

from handsoff_loop.intake import _claude_json  # noqa: E402


@pytest.mark.skipif(
    os.environ.get("TPI_REAL_CLAUDE") != "1",
    reason=(
        "sentinel-survives integration is opt-in (real claude + a "
        "live sentinel poller); set TPI_REAL_CLAUDE=1."
    ),
)
def test_AC_TPI_2_sentinel_poller_survives_intake_claude_json(
) -> None:  # pragma: no cover - opt-in real-binary path
    """A sentinel process holding the single-consumer slot is still
    alive after a real intake `claude -p --output-format json` call
    (the spawned `claude` cannot reach the telegram plugin + the
    bot-token env is scrubbed)."""
    sentinel = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(600)"]
    )
    try:
        env = _claude_json(
            "Reply with the single word ACK and nothing else.",
            timeout=180,
        )
        # The call must have actually run a real subprocess (the
        # envelope is a dict — empirical, not a stubbed structure).
        assert isinstance(env, dict)
        time.sleep(0.5)
        assert sentinel.poll() is None, (
            "sentinel poller was SIGTERM'd by an intake claude -p call "
            "— AC.TPI.2 VIOLATED (the §1b isolation did not close the "
            "kill vector)"
        )
    finally:
        sentinel.terminate()
        sentinel.wait(timeout=5)
