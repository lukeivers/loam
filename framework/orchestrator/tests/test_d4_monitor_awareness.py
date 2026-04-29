"""D4 — monitor hosting + awareness pull.

Acceptance (from brief D4):
- Monitor starts with the orchestrator; pyee events from scope-of-
  work flow in real time.
- GET /awareness?turn_id=T returns a structured awareness block
  (≤1k tokens, six categories, ≤5 rows each).
- Live pull completes within 100ms p95; on exceedance, cache
  fallback returns last block with `stale: true`.
- Cached block is refreshed on every successful live pull.
"""

from __future__ import annotations

import asyncio
import statistics
import time

import pytest

from loam.orchestrator import Orchestrator
from loam.orchestrator.ipc import IPCClient
from loam.scope_of_work import ScopeRuntime, ScopeSpec
from loam.scope_of_work.spec import Budget, ReversibilityClass


def _make_spec(goal: str, *, owner: str = "rune") -> ScopeSpec:
    return ScopeSpec(
        goal=goal,
        constraints=(),
        budget=Budget(tokens=1000),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(),
        observers=(),
        escalation_triggers=(),
        owner_persona=owner,
    )


@pytest.mark.asyncio
async def test_monitor_starts_with_orchestrator(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        assert o.monitor is not None
        assert o.monitor._task is not None
        assert not o.monitor._task.done()


@pytest.mark.asyncio
async def test_pyee_events_flow_in_real_time(tmp_config):
    """Create a scope; the monitor's internal subscription must see
    the subsequent state transitions."""
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        assert o.scope_runtime is not None
        seen = []

        def callback(event):
            seen.append(getattr(event, "kind", None))

        o.scope_runtime.subscribe_all(callback)
        proj = await o.scope_runtime.create(_make_spec("test flow"))
        await o.scope_runtime.start(proj.scope_id)
        # Give the event loop a chance to fan out.
        await asyncio.sleep(0.05)
        assert "scope_created" in seen
        assert "state_transitioned" in seen


@pytest.mark.asyncio
async def test_awareness_block_shape(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        assert o.scope_runtime is not None
        proj = await o.scope_runtime.create(_make_spec("test awareness"))
        await o.scope_runtime.start(proj.scope_id)

        block = await o.get_awareness(turn_id="t1")

        # Six categories present
        for cat in (
            "active",
            "pending_decision",
            "stuck",
            "recently_finished",
            "escalated",
            "failed",
        ):
            assert cat in block, f"missing category {cat}"
            assert isinstance(block[cat], list)
            assert len(block[cat]) <= 5, "≤5 rows per category"
        assert block["turn_id"] == "t1"
        assert "stale" in block


@pytest.mark.asyncio
async def test_awareness_via_ipc(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        assert o.scope_runtime is not None
        await o.scope_runtime.create(_make_spec("for ipc"))
        client = IPCClient(tmp_config.socket_path)
        await client.connect()
        try:
            block = await client.call("awareness", {"turn_id": "ipc-1"})
            assert block["turn_id"] == "ipc-1"
            assert block["stale"] is False
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_awareness_p95_under_100ms(tmp_config):
    """Brief D4: live pull within 100ms p95 on representative workload."""
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        assert o.scope_runtime is not None
        # Representative workload: 10 active scopes.
        for i in range(10):
            p = await o.scope_runtime.create(_make_spec(f"scope {i}"))
            await o.scope_runtime.start(p.scope_id)

        samples: list[float] = []
        for i in range(100):
            t0 = time.perf_counter()
            block = await o.get_awareness(turn_id=f"t{i}")
            samples.append((time.perf_counter() - t0) * 1000.0)
            assert block["stale"] is False

        p95 = statistics.quantiles(samples, n=20)[18]
        # Record for D10.
        tmp_config.root_dir.joinpath("awareness_latency_samples.txt").write_text(
            "\n".join(f"{s:.3f}" for s in samples)
        )
        assert p95 < 100.0, f"awareness p95 {p95:.3f}ms exceeds 100ms"


@pytest.mark.asyncio
async def test_awareness_cache_fallback_on_timeout(tmp_config, monkeypatch):
    """When the live pull exceeds the 100ms ceiling, fall back to the
    cached block with stale=True."""
    from loam.orchestrator.config import with_overrides

    cfg = with_overrides(tmp_config, awareness_pull_timeout_ms=1)  # 1ms: guaranteed miss

    orch = Orchestrator(cfg)
    async with orch.running() as o:
        # Seed the cache with a fresh pull under a generous timeout.
        o.config = tmp_config  # temporarily use the generous config for seed
        seed = await o.get_awareness(turn_id="seed")
        assert seed["stale"] is False
        # Restore the 1ms ceiling.
        o.config = cfg

        # Now force a timeout path by stubbing the monitor's snapshot
        # to sleep 50ms (guaranteed > 1ms ceiling).
        original = o.monitor.on_user_prompt

        def slow(turn_id: str | None = None):
            time.sleep(0.05)
            return original(turn_id=turn_id)

        monkeypatch.setattr(o.monitor, "on_user_prompt", slow)
        block = await o.get_awareness(turn_id="after-timeout")
        assert block["stale"] is True
        assert "cache_age_ms" in block


@pytest.mark.asyncio
async def test_awareness_cache_refresh_on_success(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        block1 = await o.get_awareness(turn_id="a")
        assert block1["stale"] is False
        t1 = o._awareness_cache_at
        await asyncio.sleep(0.03)
        block2 = await o.get_awareness(turn_id="b")
        assert block2["stale"] is False
        t2 = o._awareness_cache_at
        assert t2 is not None and t1 is not None
        assert t2 > t1  # cache was refreshed


@pytest.mark.asyncio
async def test_awareness_empty_block_when_no_cache_and_timeout(tmp_config, monkeypatch):
    from loam.orchestrator.config import with_overrides

    cfg = with_overrides(tmp_config, awareness_pull_timeout_ms=1)
    orch = Orchestrator(cfg)
    async with orch.running() as o:
        # Don't seed the cache.
        assert o._awareness_cache is None

        def slow(turn_id: str | None = None):
            time.sleep(0.05)
            raise RuntimeError("forced")

        monkeypatch.setattr(o.monitor, "on_user_prompt", slow)
        block = await o.get_awareness(turn_id="x")
        assert block["stale"] is True
        assert block["active"] == []
        assert "stale_reason" in block
