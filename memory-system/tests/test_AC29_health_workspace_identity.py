"""Amendment #29 AC29.5 memory-system side — /health carries
workspace identity.

The memory-system's ``_impl_health`` includes a ``workspace_root``
field whose value is the process's ``POS_V2_WORKSPACE_ROOT`` env var.
Hands-off-lifecycle's phase-4b probe uses this field to verify the
responding sidecar belongs to the probing workspace (AC29.5 probe-
side tests live under ``hands-off-lifecycle/tests/``).
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from src import service


class _FakeGraphiti:
    """Minimal fake for ``_impl_health``. It only needs ``llm_client``
    and ``embedder`` attributes; no actual graph-traversal happens."""

    class _LLM:
        model = "fake-model"

    class _Embedder:
        class _Cfg:
            embedding_dim = 42

        config = _Cfg()

    llm_client = _LLM()
    embedder = _Embedder()


def test_AC29_5_health_response_carries_workspace_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_impl_health`` returns a dict whose ``workspace_root`` key
    mirrors the process's ``POS_V2_WORKSPACE_ROOT`` env var. AC29.5
    memory-system side — the identity field IS on the response body.
    Probe-side verification (mismatch-fails, match-succeeds) lives in
    ``hands-off-lifecycle/tests/test_AC29_health_workspace_probe.py``.
    """
    monkeypatch.setenv("POS_V2_WORKSPACE_ROOT", "/tmp/alpha-workspace")
    payload: dict[str, Any] = asyncio.run(service._impl_health(_FakeGraphiti()))
    assert payload["workspace_root"] == "/tmp/alpha-workspace"
