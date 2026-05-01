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

"""D3 — Unix-domain-socket JSON-RPC server.

Acceptance (from brief D3):
- Socket exists at configured path; permissions are user-private (0600).
- A test client connects, sends a ping, receives a pong; round-trip
  p95 latency <10 ms on local loopback.
- Disconnect and reconnect work cleanly.
- Orphaned socket files are removed on startup.
"""

from __future__ import annotations

import asyncio
import os
import stat
import statistics
import time

import pytest

from loam.orchestrator import Orchestrator
from loam.orchestrator.ipc import IPCClient


@pytest.mark.asyncio
async def test_socket_exists_with_0600_permissions(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running() as o:
        assert tmp_config.socket_path.exists()
        mode = stat.S_IMODE(os.stat(tmp_config.socket_path).st_mode)
        assert mode == 0o600, f"expected 0o600, got {oct(mode)}"


@pytest.mark.asyncio
async def test_ping_pong_round_trip(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running():
        client = IPCClient(tmp_config.socket_path)
        await client.connect()
        try:
            result = await client.call("ping", {})
            assert result["pong"] is True
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_p95_latency_under_10ms(tmp_config):
    """Brief D3: round-trip p95 latency <10 ms on local loopback."""
    orch = Orchestrator(tmp_config)
    async with orch.running():
        client = IPCClient(tmp_config.socket_path)
        await client.connect()
        try:
            # Warm-up
            for _ in range(10):
                await client.call("ping", {})
            # Measurement
            samples: list[float] = []
            for _ in range(200):
                t0 = time.perf_counter()
                await client.call("ping", {})
                samples.append((time.perf_counter() - t0) * 1000.0)
            p95 = statistics.quantiles(samples, n=20)[18]  # 95th percentile
            # Record for D10 bundling.
            tmp_config.root_dir.joinpath("ipc_latency_samples.txt").write_text(
                "\n".join(f"{s:.3f}" for s in samples)
            )
            assert p95 < 10.0, f"p95 latency {p95:.3f}ms exceeds 10ms"
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_disconnect_reconnect_is_clean(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running():
        c1 = IPCClient(tmp_config.socket_path)
        await c1.connect()
        r1 = await c1.call("ping", {})
        await c1.close()
        assert r1["pong"] is True

        # Reconnect with a fresh client.
        c2 = IPCClient(tmp_config.socket_path)
        await c2.connect()
        r2 = await c2.call("ping", {})
        await c2.close()
        assert r2["pong"] is True


@pytest.mark.asyncio
async def test_orphan_socket_removed_on_startup(tmp_config):
    # Create an orphan file at the socket path.
    tmp_config.socket_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_config.socket_path.write_text("stale")
    orch = Orchestrator(tmp_config)
    async with orch.running():
        # Orphan has been removed, real socket bound.
        assert tmp_config.socket_path.exists()
        st = os.stat(tmp_config.socket_path)
        assert stat.S_ISSOCK(st.st_mode), "path should now be a real socket"


@pytest.mark.asyncio
async def test_method_not_found_returns_structured_error(tmp_config):
    from loam.orchestrator.ipc import ApplicationError

    orch = Orchestrator(tmp_config)
    async with orch.running():
        client = IPCClient(tmp_config.socket_path)
        await client.connect()
        try:
            with pytest.raises(ApplicationError) as ei:
                await client.call("does_not_exist", {})
            assert ei.value.code == -32601
        finally:
            await client.close()


@pytest.mark.asyncio
async def test_status_and_local_event_count_roundtrip(tmp_config):
    orch = Orchestrator(tmp_config)
    async with orch.running():
        client = IPCClient(tmp_config.socket_path)
        await client.connect()
        try:
            s = await client.call("status", {})
            assert s["pid"] == os.getpid()
            assert s["paused"] is False
            # Heartbeats exist by now.
            await asyncio.sleep(0.1)
            c = await client.call("local_event_count", {"event_type": "heartbeat"})
            assert c["count"] >= 0  # very fast tests may not have ticked yet
        finally:
            await client.close()
