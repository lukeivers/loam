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

"""Bounded-time proof — A1/A2/A3 timing.

A5. The kill initiates within budget even if the wedged task has not
    yet returned. This file covers the multi-sample mean check to keep
    the CI signal stable across jitter.
"""

from __future__ import annotations

import statistics
import time

import pytest

from loam.scope_of_work import (
    Budget,
    ReversibilityClass,
    ScopeSpec,
    SuccessCriterion,
)

from loam.safety_layer import KillEngine


def _spec() -> ScopeSpec:
    return ScopeSpec(
        goal="timing test",
        constraints=(),
        budget=Budget(time_seconds=60),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(
            SuccessCriterion(criterion_id="c", description="d"),
        ),
        observers=(),
        escalation_triggers=(),
    )


@pytest.mark.asyncio
async def test_scope_kill_timing_median_under_budget(
    scope_runtime, safety_store, fake_orchestrator
):
    engine = KillEngine(
        scope_runtime=scope_runtime,
        store=safety_store,
        orchestrator=fake_orchestrator,
    )

    samples: list[float] = []
    for i in range(20):
        await scope_runtime.create(_spec(), scope_id=f"t-{i}")
        await scope_runtime.start(f"t-{i}")
        t0 = time.monotonic()
        await engine.kill_scope(
            scope_id=f"t-{i}", reason="timing", source="ipc"
        )
        samples.append((time.monotonic() - t0) * 1000)

    # A1 target: 500ms p95. The actual median for in-memory cancels
    # should be single-digit milliseconds; we assert a very loose
    # ceiling so CI jitter does not flake.
    assert statistics.median(samples) < 200, f"median={statistics.median(samples):.1f}ms"
    assert max(samples) < 500, f"max={max(samples):.1f}ms"
