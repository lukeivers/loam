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
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.DMP.OA (outcome-altitude: true) — THE JUNE-9 DISPATCH REPLAY.
Through the production SubagentStart entry point, with the live ledger
(Tilth record present) and NO other pre-arranged state, a dispatch
whose task text concerns Tilth planning yields a composed bundle
containing the $750k ruling whole.

This is the memory-blind planning agent of 2026-06-09, replayed and
structurally impossible: the agent that drafted the Tilth workstream
plan received ZERO memory; now the bundle composition itself carries
the ruling. Skips (does not fail) when the live workspace state is
absent (CI / fresh machine).

Memory recall cycle, Slice 4.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.frame_kernel.bundle import compose_bundle


LIVE_WORKSPACE = Path.home() / "pos3"
LIVE_DECISIONS = LIVE_WORKSPACE / "workspace" / ".loam" / "memory" / "decisions"


def _live_tilth_record_present() -> bool:
    if not LIVE_DECISIONS.is_dir():
        return False
    return any("tilth" in p.name.lower() for p in LIVE_DECISIONS.glob("*.md"))


@pytest.mark.skipif(
    not _live_tilth_record_present(),
    reason="live workspace ledger / Tilth record absent (CI / fresh machine)",
)
def test_AC_DMP_OA_tilth_dispatch_bundle_carries_ruling_whole() -> None:
    bundle = compose_bundle(
        {
            "workspace": {"project_dir": str(LIVE_WORKSPACE)},
            "prompt": (
                "Plan the next steps for the Tilth raise workstream — "
                "draft the investor follow-up."
            ),
        }
    )
    memory_tier = bundle.split("=== relevant memory ===", 1)[1]
    assert "750" in memory_tier, f"ruling value missing: {memory_tier!r}"
    assert "AI-era raises differ" in memory_tier or "AI era" in memory_tier, (
        f"ruling reasoning missing: {memory_tier!r}"
    )
    assert "14053" in memory_tier, (
        f"ruling source pointer missing: {memory_tier!r}"
    )
