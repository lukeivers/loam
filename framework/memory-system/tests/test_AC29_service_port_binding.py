"""Amendment #29 acceptance tests — memory-system port-binding surface.

AC29.1 — the FastMCP server's configured port reflects the
``GRAPHITI_SERVICE_PORT`` env var, not a hardcoded constant. Two
distinct values produce two distinct ``mcp.settings.port`` values.

AC29.4 — two memory-system subprocess instances on 127.0.0.1 with
distinct ``GRAPHITI_SERVICE_PORT`` values bind their declared ports
concurrently without either raising ``[Errno 48] address already in
use``. Subprocess-bind-only shape per owner ruling 2026-04-24 — no
full graphiti init, no Ollama, no claude CLI.
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from src import service


# ---- AC29.1 ---------------------------------------------------------


def test_AC29_1_service_port_reflects_env_var_across_distinct_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Constructing the FastMCP server under two distinct
    ``GRAPHITI_SERVICE_PORT`` env values yields two distinct
    ``settings.port`` values. Proves the port is sourced from the env
    var rather than a host-global constant."""
    monkeypatch.setenv("GRAPHITI_SERVICE_HOST", "127.0.0.1")

    monkeypatch.setenv("GRAPHITI_SERVICE_PORT", "18765")
    mcp_a = service._build_mcp()
    assert mcp_a.settings.port == 18765

    monkeypatch.setenv("GRAPHITI_SERVICE_PORT", "18766")
    mcp_b = service._build_mcp()
    assert mcp_b.settings.port == 18766

    assert mcp_a.settings.port != mcp_b.settings.port


# ---- AC29.4 ---------------------------------------------------------


def _free_port() -> int:
    """Ask the OS for a free ephemeral port and return it. The socket
    is closed before return so a child process can bind the same port
    without collision (brief TOCTOU window is acceptable for a test)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


_SUBPROCESS_SCRIPT = textwrap.dedent(
    """\
    import asyncio
    import sys

    # Stub graphiti construction so the subprocess does not need
    # Kuzu / Ollama / an embedder to come up; AC29.4 is bind-only
    # per owner ruling 2026-04-24.
    from src import factory, service

    class _FakeLLM:
        model = "stub"
        class _Tracker:
            def get_usage(self): return {}
            def get_total_usage(self):
                class _U:
                    input_tokens = 0
                    output_tokens = 0
                return _U()
        token_tracker = _Tracker()

    class _FakeEmbedder:
        class _Cfg:
            embedding_dim = 1
        config = _Cfg()

    class _FakeGraphiti:
        llm_client = _FakeLLM()
        embedder = _FakeEmbedder()
        async def build_indices_and_constraints(self): return None
        async def close(self): return None

    async def _fake_make(): return _FakeGraphiti()
    factory.make_graphiti = _fake_make
    factory.load_env = lambda path=None: None
    service.make_graphiti = _fake_make
    service.load_env = lambda path=None: None

    async def _run():
        mcp = service._build_mcp()
        # Announce bind success to stdout so the test can detect it,
        # then run the transport until the parent kills us.
        print(f"READY port={mcp.settings.port}", flush=True)
        await mcp.run_streamable_http_async()

    asyncio.run(_run())
    """
)


def _spawn_and_wait_ready(
    port: int, *, timeout_s: float = 15.0
) -> subprocess.Popen:
    """Spawn a bind-only subprocess and wait for its READY line."""
    env = os.environ.copy()
    env["GRAPHITI_SERVICE_HOST"] = "127.0.0.1"
    env["GRAPHITI_SERVICE_PORT"] = str(port)
    # Run under the memory-system src tree so ``from src import ...``
    # resolves the same package the regular service does.
    memory_system_root = Path(__file__).resolve().parent.parent
    proc = subprocess.Popen(
        [sys.executable, "-u", "-c", _SUBPROCESS_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=str(memory_system_root),
        text=True,
    )
    deadline = time.monotonic() + timeout_s
    expected = f"READY port={port}"
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            stdout, stderr = proc.communicate(timeout=1.0)
            raise RuntimeError(
                f"subprocess exited early: rc={proc.returncode} "
                f"stdout={stdout!r} stderr={stderr!r}"
            )
        line = proc.stdout.readline() if proc.stdout else ""
        if expected in line:
            return proc
        time.sleep(0.05)
    # Timeout — kill and collect.
    proc.kill()
    stdout, stderr = proc.communicate(timeout=2.0)
    raise RuntimeError(
        f"subprocess did not announce READY within {timeout_s}s; "
        f"stdout={stdout!r} stderr={stderr!r}"
    )


def _wait_for_port_bound(port: int, *, timeout_s: float = 10.0) -> None:
    """Poll ``127.0.0.1:port`` until a fresh bind raises ``OSError``
    (meaning the subprocess has actually bound the port — the READY
    announcement fires before the transport starts listening, so the
    caller must wait before asserting liveness).

    Raises ``AssertionError`` if the port never becomes bound within
    ``timeout_s``."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
        except OSError:
            # Bind raised — port is held by the subprocess.
            s.close()
            return
        else:
            s.close()
            time.sleep(0.1)
    raise AssertionError(
        f"port {port} never became bound within {timeout_s}s"
    )


def test_AC29_4_two_subprocesses_bind_distinct_ports_without_eaddrinuse() -> None:
    """Spawn two memory-system subprocess instances with distinct
    ``GRAPHITI_SERVICE_PORT`` values. Both must reach READY concurrently
    and both declared ports must be bound; neither subprocess exits
    with ``EADDRINUSE``."""
    port_a = _free_port()
    port_b = _free_port()
    assert port_a != port_b, "two sequential _free_port() calls returned the same value"

    proc_a: subprocess.Popen | None = None
    proc_b: subprocess.Popen | None = None
    try:
        proc_a = _spawn_and_wait_ready(port_a)
        proc_b = _spawn_and_wait_ready(port_b)
        # Both subprocesses reached READY; poll until their transports
        # have actually bound the declared ports (READY announces
        # before ``run_streamable_http_async`` enters the listening
        # state). Both binds holding concurrently is the AC: neither
        # subprocess exited with EADDRINUSE and both own their ports.
        _wait_for_port_bound(port_a)
        _wait_for_port_bound(port_b)
        # Confirm neither subprocess exited (an EADDRINUSE would have
        # killed the relevant process at bind time).
        assert proc_a.poll() is None, (
            f"subprocess A exited unexpectedly: rc={proc_a.returncode}"
        )
        assert proc_b.poll() is None, (
            f"subprocess B exited unexpectedly: rc={proc_b.returncode}"
        )
    finally:
        for p in (proc_a, proc_b):
            if p is not None and p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=5.0)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait(timeout=2.0)
