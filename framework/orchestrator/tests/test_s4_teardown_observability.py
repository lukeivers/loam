"""Amendment #26 — teardown observability retrofit (orchestrator).

Covers the seven orchestrator teardown sites retrofitted per tightened
CDC 2:

- supervisor.py:268 — MemorySupervisor.stop (logger + CancelledError split)
- ipc.py:116        — IPCServer.stop writer-close loop (logger)
- ipc.py:248        — IPCClient.close writer (logger)
- orchestrator.py:224 — _shutdown heartbeat (span.add_event)
- orchestrator.py:233 — _shutdown monitor.stop timeout+exception split
- orchestrator.py:239 — _shutdown ipc_server.stop (span.add_event)
- orchestrator.py:246 — _shutdown scope_runtime.close (span.add_event)
- orchestrator.py:287 — Orchestrator.close local_state (logger)

The span.add_event sites emit on ``self._process_span``; this test
replaces the span with a recording stub and asserts the event fires.
The logger.debug sites use caplog at the module logger.
"""

from __future__ import annotations

import asyncio
import logging

import pytest


class _RecordingSpan:
    def __init__(self):
        self.events: list[tuple[str, dict]] = []

    def add_event(self, name, attributes=None):
        self.events.append((name, dict(attributes or {})))

    # Cover the orchestrator observability helpers' usage patterns.
    def set_attribute(self, *_a, **_k):
        pass

    def end(self):
        pass


# ---- logger-emission sites --------------------------------------


def test_s4_supervisor_stop_logger_on_broad_exception(caplog):
    """MemorySupervisor.stop — the await-probe-task RuntimeError path
    emits a DEBUG log record; CancelledError remains silent."""
    from loam.orchestrator.supervisor import (
        MemorySupervisor,
        SupervisorConfig,
    )

    async def _raising_probe():
        raise RuntimeError("synthetic probe failure — amendment #26")

    async def _probe_getme():
        return None

    sup = MemorySupervisor(
        probe=_probe_getme,
        config=SupervisorConfig(),
    )

    async def _run():
        # Install a completed-with-RuntimeError task so await raises.
        task = asyncio.create_task(_raising_probe())
        await asyncio.sleep(0)  # let it raise
        sup._probe_task = task
        sup._stop.set()
        with caplog.at_level(
            logging.DEBUG, logger="loam.orchestrator.supervisor"
        ):
            await sup.stop()

    asyncio.run(_run())

    matching = [
        r for r in caplog.records
        if r.name == "loam.orchestrator.supervisor"
        and r.message == "supervisor_stop_probe_task_failed"
    ]
    assert len(matching) == 1
    assert matching[0].exc_info is not None


def test_s4_ipc_client_close_logger_on_broad_exception(caplog):
    """IPCClient.close — writer.close() raises; logger emits DEBUG."""
    from loam.orchestrator.ipc import IPCClient

    client = IPCClient(tmp_path=None) if False else IPCClient.__new__(IPCClient)
    # Manually seed the fields we need.
    client._socket_path = None  # type: ignore[assignment]
    client._reader = None
    client._counter = 0
    client._lock = asyncio.Lock()

    class _W:
        def close(self):
            raise RuntimeError("synthetic")

        async def wait_closed(self):
            return None

    client._writer = _W()  # type: ignore[assignment]

    async def _run():
        with caplog.at_level(logging.DEBUG, logger="loam.orchestrator.ipc"):
            await client.close()

    asyncio.run(_run())

    matching = [
        r for r in caplog.records
        if r.name == "loam.orchestrator.ipc"
        and r.message == "ipc_client_close_writer_failed"
    ]
    assert len(matching) == 1


def test_s4_ipc_server_stop_writer_logger_on_broad_exception(caplog):
    """IPCServer.stop — per-client writer.close() raises; logger emits
    DEBUG for each failing writer."""
    from loam.orchestrator.ipc import IPCServer

    server = IPCServer.__new__(IPCServer)
    server._server = None
    server._socket_path = pytest.importorskip("pathlib").Path("/tmp/no-such-socket-amendment-26.sock")
    server._socket_mode = 0o600
    server._handlers = {}

    class _W:
        def close(self):
            raise RuntimeError("synthetic")

    server._clients = {_W()}  # type: ignore[assignment]

    async def _run():
        with caplog.at_level(logging.DEBUG, logger="loam.orchestrator.ipc"):
            await server.stop()

    asyncio.run(_run())

    matching = [
        r for r in caplog.records
        if r.name == "loam.orchestrator.ipc"
        and r.message == "ipc_server_stop_writer_close_failed"
    ]
    assert len(matching) == 1


def test_s4_orchestrator_close_local_state_logger(tmp_config, caplog):
    """Orchestrator.close — local_state.close() raises; logger emits
    DEBUG."""
    from loam.orchestrator import Orchestrator

    orch = Orchestrator(tmp_config)

    class _RaisingLocalState:
        def close(self):
            raise RuntimeError("synthetic local_state close failure")

    orch.local_state = _RaisingLocalState()  # type: ignore[assignment]

    with caplog.at_level(
        logging.DEBUG, logger="loam.orchestrator.orchestrator"
    ):
        orch.close()

    matching = [
        r for r in caplog.records
        if r.name == "loam.orchestrator.orchestrator"
        and r.message == "orchestrator_close_local_state_failed"
    ]
    assert len(matching) == 1


# ---- span.add_event sites --------------------------------------


@pytest.mark.parametrize(
    "site,setup,expected_event",
    [
        (
            "heartbeat",
            "heartbeat",
            "loam.orchestrator.heartbeat_stop_exception",
        ),
        (
            "monitor_stop_exception",
            "monitor_exc",
            "loam.orchestrator.monitor_stop_exception",
        ),
        (
            "monitor_stop_timeout",
            "monitor_timeout",
            "loam.orchestrator.monitor_stop_timeout",
        ),
        (
            "ipc_server",
            "ipc_server",
            "loam.orchestrator.ipc_server_stop_exception",
        ),
        (
            "scope_runtime",
            "scope_runtime",
            "loam.orchestrator.scope_runtime_close_exception",
        ),
    ],
)
def test_s4_shutdown_site_emits_span_event(
    tmp_config, site, setup, expected_event
):
    """Each of the five _shutdown broad-catch sites emits a named event
    on ``self._process_span`` when the guarded call raises."""
    from loam.orchestrator import Orchestrator

    orch = Orchestrator(tmp_config)
    recording_span = _RecordingSpan()
    orch._process_span = recording_span  # type: ignore[assignment]

    # Prepare orch state per site.
    if setup == "heartbeat":
        async def _raising_heartbeat():
            raise RuntimeError("synthetic heartbeat failure")

        async def _run():
            task = asyncio.create_task(_raising_heartbeat())
            await asyncio.sleep(0)
            orch._heartbeat_task = task
            await orch._shutdown(clean=False)

        asyncio.run(_run())
    elif setup == "monitor_exc":
        class _RaisingMonitor:
            async def stop(self):
                raise RuntimeError("synthetic monitor failure")

        orch.monitor = _RaisingMonitor()  # type: ignore[assignment]

        async def _run():
            await orch._shutdown(clean=False)

        asyncio.run(_run())
    elif setup == "monitor_timeout":
        import dataclasses

        class _SlowMonitor:
            async def stop(self):
                await asyncio.sleep(3600.0)

        # OrchestratorConfig is a frozen dataclass; replace() clones
        # with the short grace so wait_for times out promptly.
        orch.config = dataclasses.replace(
            orch.config, sigterm_grace_seconds=0.05
        )
        orch.monitor = _SlowMonitor()  # type: ignore[assignment]

        async def _run():
            await orch._shutdown(clean=False)

        asyncio.run(_run())
    elif setup == "ipc_server":
        class _RaisingIPC:
            async def stop(self):
                raise RuntimeError("synthetic ipc stop failure")

        orch.ipc_server = _RaisingIPC()  # type: ignore[assignment]

        async def _run():
            await orch._shutdown(clean=False)

        asyncio.run(_run())
    elif setup == "scope_runtime":
        class _RaisingScopeRuntime:
            def close(self):
                raise RuntimeError("synthetic scope_runtime close failure")

        orch.scope_runtime = _RaisingScopeRuntime()  # type: ignore[assignment]

        async def _run():
            await orch._shutdown(clean=False)

        asyncio.run(_run())
    else:
        raise AssertionError(f"unknown setup {setup!r}")

    event_names = [name for name, _ in recording_span.events]
    assert expected_event in event_names, (
        f"expected {expected_event} in {event_names}"
    )
