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

"""AC.SR-WATCH.1 + AC.SR-WATCH.2 — the watchdog detects a stuck/silent
agent and a dead comms channel PROACTIVELY (no user signal required).

AC.SR-WATCH.1 — a stalled/silent agent (no progress past a tunable
threshold) is detected and routed to recovery, with NO user distress
signal required.

AC.SR-WATCH.2 — a down comms channel (availability probe negative) is
detected and triggers the outage self-heal path (out-of-band notify),
without waiting for the user to report silence.
"""

from __future__ import annotations

import pytest

from loam.self_correction import (
    StallWatchdog,
    availability_probe_to_channel_probe,
    check_channel_and_self_heal,
    evaluate_stall,
)


# ---- AC.SR-WATCH.1 — proactive stuck-agent detection ------------------


def test_AC_SR_WATCH_1_stall_detected_past_threshold_no_user_signal() -> None:
    """Progress quiet past the threshold is detected as stuck — with NO
    user signal in the loop (the watchdog drives it)."""
    clock = {"t": 0.0}
    wd = StallWatchdog(
        stall_threshold_seconds=300, clock=lambda: clock["t"]
    )
    wd.beat()  # progress at t=0
    clock["t"] = 100  # within threshold
    assert wd.is_stuck() is False

    clock["t"] = 400  # 400s since last progress > 300s threshold
    assert wd.is_stuck() is True

    verdict = evaluate_stall(wd)
    assert verdict.stuck is True
    assert verdict.seconds_since_progress == pytest.approx(400.0)
    # Routed to recovery with a plain-language detail (no internal IDs).
    assert verdict.detail
    assert "stuck" in verdict.detail.lower()


def test_AC_SR_WATCH_1_fresh_progress_is_not_stuck() -> None:
    clock = {"t": 0.0}
    wd = StallWatchdog(stall_threshold_seconds=300, clock=lambda: clock["t"])
    wd.beat()
    clock["t"] = 10
    assert wd.is_stuck() is False
    assert evaluate_stall(wd).stuck is False


def test_AC_SR_WATCH_1_never_started_is_not_stuck() -> None:
    """A watchdog that has never seen progress is not 'stuck' — nothing has
    started; only an observed-then-quiet sequence is a stall."""
    wd = StallWatchdog(stall_threshold_seconds=1)
    assert wd.seconds_since_progress() is None
    assert wd.is_stuck() is False


# ---- AC.SR-WATCH.2 — dead-channel detection + self-heal ---------------


@pytest.mark.asyncio
async def test_AC_SR_WATCH_2_dead_channel_triggers_self_heal() -> None:
    """A negative availability probe triggers the out-of-band self-heal —
    the watchdog notifies another way without waiting for the user."""
    delivered: list[dict] = []

    async def _dead_probe() -> bool:
        return False  # channel down

    async def _deliver(*, text: str, reason: str) -> list[str]:
        delivered.append({"text": text, "reason": reason})
        return ["attention_md"]

    verdict = await check_channel_and_self_heal(
        probe=_dead_probe, deliver=_deliver
    )
    assert verdict.channel_live is False
    # Self-heal fired: the out-of-band surface was reached.
    assert verdict.fallback_surfaces == ("attention_md",)
    assert delivered, "a dead channel must trigger out-of-band delivery"
    assert delivered[0]["reason"].startswith("self-recovery-watchdog")


@pytest.mark.asyncio
async def test_AC_SR_WATCH_2_live_channel_no_fallback() -> None:
    """A live channel sends no fallback (no spurious out-of-band noise)."""
    delivered: list[dict] = []

    async def _live_probe() -> bool:
        return True

    async def _deliver(*, text: str, reason: str) -> list[str]:
        delivered.append({"text": text})
        return ["attention_md"]

    verdict = await check_channel_and_self_heal(
        probe=_live_probe, deliver=_deliver
    )
    assert verdict.channel_live is True
    assert verdict.fallback_surfaces == ()
    assert delivered == []  # no fallback when channel is live


@pytest.mark.asyncio
async def test_AC_SR_WATCH_2_probe_error_treated_as_dead() -> None:
    """A probe that raises is treated as a dead channel → self-heal fires
    (fail toward reaching the user, not toward silence)."""
    delivered: list[str] = []

    async def _boom() -> bool:
        raise RuntimeError("probe error")

    async def _deliver(*, text: str, reason: str) -> list[str]:
        delivered.append(reason)
        return ["attention_md"]

    verdict = await check_channel_and_self_heal(probe=_boom, deliver=_deliver)
    assert verdict.channel_live is False
    assert delivered  # self-heal fired


@pytest.mark.asyncio
async def test_AC_SR_WATCH_2_availability_probe_adapter() -> None:
    """The production adapter maps an AvailabilityProbe's ProbeResult.available
    to the boolean the watchdog consumes (composition is a library call)."""

    class _FakeResult:
        available = False

    class _FakeAvailabilityProbe:
        async def probe_once(self):
            return _FakeResult()

    channel_probe = availability_probe_to_channel_probe(_FakeAvailabilityProbe())
    assert await channel_probe() is False
