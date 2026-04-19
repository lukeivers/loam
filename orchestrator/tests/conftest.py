"""Shared pytest fixtures for orchestrator tests."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import pytest

from pos_orchestrator.config import OrchestratorConfig


_BOOTSTRAP_CONTENT = '''"""Test-only bootstrap — no-op register()."""

def register(orchestrator):
    return None
'''


def _short_socket_path() -> Path:
    """AF_UNIX on macOS caps path length at 104 bytes; pytest's
    tmp_path often exceeds it. Put the socket under /tmp with a short
    unique name."""
    base = Path(tempfile.gettempdir())
    name = f"pos-{uuid.uuid4().hex[:12]}.sock"
    return base / name


@pytest.fixture
def tmp_config(tmp_path: Path) -> OrchestratorConfig:
    """Build an OrchestratorConfig rooted at tmp_path with a no-op
    bootstrap written in place. Socket is placed in /tmp to stay
    under the AF_UNIX 104-byte path cap on macOS."""
    root = tmp_path / "pos"
    root.mkdir(parents=True, exist_ok=True)
    (root / "bootstrap.py").write_text(_BOOTSTRAP_CONTENT)
    sock = _short_socket_path()
    cfg = OrchestratorConfig(
        root_dir=root,
        socket_path=sock,
        heartbeat_interval_seconds=0.05,  # fast for tests
        sigterm_grace_seconds=1.0,
    )
    yield cfg
    # Clean up stray socket file.
    try:
        if sock.exists():
            sock.unlink()
    except Exception:
        pass


@pytest.fixture
def tmp_config_no_bootstrap(tmp_path: Path) -> OrchestratorConfig:
    root = tmp_path / "pos"
    root.mkdir(parents=True, exist_ok=True)
    sock = _short_socket_path()
    cfg = OrchestratorConfig(
        root_dir=root,
        socket_path=sock,
        heartbeat_interval_seconds=0.05,
        sigterm_grace_seconds=1.0,
        require_bootstrap=False,
    )
    yield cfg
    try:
        if sock.exists():
            sock.unlink()
    except Exception:
        pass
