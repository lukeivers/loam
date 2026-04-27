"""Availability probe — TG12, TG13.

TG12: background probe fires every 60s and updates the in-memory flag;
      probe cost (latency) is OTel-emitted.
TG13: on send-failure, adapter enters 5s-cadence retry mode for 60s
      before declaring outage; per-retry spans emit.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from telegram_interface.availability import (
    AGGRESSIVE_PROBE_DURATION_S,
    AGGRESSIVE_PROBE_INTERVAL_S,
    PROBE_INTERVAL_S,
    AvailabilityProbe,
    AvailabilityState,
    FailureClass,
    ProbeResult,
)


async def _ok() -> ProbeResult:
    return ProbeResult(available=True, latency_ms=5.0)


async def _fail() -> ProbeResult:
    return ProbeResult(
        available=False,
        latency_ms=100.0,
        failure_class=FailureClass.api_unreachable,
        detail="mock",
    )


def test_tg12_probe_intervals_are_60s_and_5s() -> None:
    """TG12/13 — the documented probe cadences are present as
    module-level constants that tests can assert against."""
    assert PROBE_INTERVAL_S == 60.0
    assert AGGRESSIVE_PROBE_INTERVAL_S == 5.0
    assert AGGRESSIVE_PROBE_DURATION_S == 60.0


@pytest.mark.asyncio
async def test_tg12_probe_once_updates_cached_flag(tmp_path: Path) -> None:
    """A single probe_once call flips the cached flag when the fake
    getMe transitions from failing to succeeding."""
    # Force both pre-getMe checks to pass by pointing plugin_cache at a
    # real-looking dir and env at a present token.
    cache = tmp_path / "plugin-cache"
    cache.mkdir()
    (cache / "0.0.6").mkdir()
    env = tmp_path / "env"
    env.write_text("TELEGRAM_BOT_TOKEN=123:abcdefghijklmnopqrstuv\n")

    states: list[bool] = [False, True]

    async def flipper() -> ProbeResult:
        ok = states.pop(0)
        return ProbeResult(
            available=ok,
            latency_ms=1.0,
            failure_class=None if ok else FailureClass.api_unreachable,
        )

    async def mcp_ok() -> bool:
        return True

    probe = AvailabilityProbe(
        getme_probe=flipper,
        mcp_tool_probe=mcp_ok,
        cache_dir=cache,
        env_path=env,
    )
    r1 = await probe.probe_once()
    assert r1.available is False
    assert probe.current is False
    r2 = await probe.probe_once()
    assert r2.available is True
    assert probe.current is True


@pytest.mark.asyncio
async def test_tg13_mark_failure_flips_immediately_and_sets_aggressive_window(tmp_path: Path) -> None:
    """TG13 — ``mark_failure`` immediately sets state to unavailable
    and sets an aggressive-probe window the background loop honours."""
    probe = AvailabilityProbe(
        getme_probe=_ok,
        mcp_tool_probe=None,
        cache_dir=tmp_path,
    )
    probe._state = AvailabilityState.available
    await probe.mark_failure(FailureClass.api_unreachable, detail="test")
    assert probe.current is False
    assert probe._aggressive_until > 0
