"""Acceptance tests for v0.2.5 corrective C5 —
claude -p subprocess MCP-isolation flags (memory-system half).

Closes:
- AC.V025-C5.1 — memory-system claude_print_client argv carries
  ``--strict-mcp-config --mcp-config <abs path>`` BEFORE ``-p`` for
  both the construction-time OAuth probe AND every per-call
  ``_generate_response`` invocation.
- AC.V025-C5.3 (memory-system half) — empty MCP config tempfile
  decodes to exactly ``{"mcpServers": {}}``.

Why this matters: without these flags, the child claude inherits the
parent session's MCP server config including the telegram MCP. The
telegram loader at
``~/.claude/plugins/cache/claude-plugins-official/telegram/0.0.6/server.ts:60-78``
SIGTERMs any prior PID-file holder via its dedup branch. Result: every
memory-system ingest that forks ``claude -p`` kills the parent
session's telegram bot. Owner ruling 2026-05-05 (Telegram 10196):
subprocess invocations must launch without telegram.

The fix mirrors the precedent at
``framework/workspace-sync/src/loam/workspace_sync/_resolver_client.py``
(AC.WSα.8, verified 2026-04-27).

Tests use the same subprocess-mocking infrastructure as
``test_claude_print_client.py`` — no real ``claude -p`` spawns.
"""

from __future__ import annotations

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from graphiti_core.prompts.models import Message
from pydantic import BaseModel, Field


class _SmallResponse(BaseModel):
    kind: str = Field(description="what kind")
    count: int = Field(description="how many")


def _envelope(result_text: str) -> str:
    return json.dumps(
        {
            "type": "result",
            "result": result_text,
            "total_cost_usd": 0.0,
            "is_error": False,
        }
    )


class _FakeProc:
    def __init__(self, stdout: str = "", stderr: str = "") -> None:
        self._stdout = stdout.encode()
        self._stderr = stderr.encode()
        self.returncode = 0

    async def communicate(self) -> tuple[bytes, bytes]:
        return self._stdout, self._stderr


def _make_exec_mock(stdout: str, stderr: str = "") -> MagicMock:
    proc = _FakeProc(stdout=stdout, stderr=stderr)
    return AsyncMock(return_value=proc)


# ---- AC.V025-C5.1 — generate-call argv carries MCP-isolation flags --


def test_AC_V025_C5_1_generate_argv_carries_strict_mcp_config_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_generate_response`` argv carries
    ``--strict-mcp-config --mcp-config <path>`` before ``-p``.
    """
    from src.claude_print_client import ClaudePrintLLMClient

    exec_mock = _make_exec_mock(_envelope('{"kind":"x","count":1}'))
    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            client = ClaudePrintLLMClient(skip_auth_probe=True)
            asyncio.run(
                client._generate_response(
                    [Message(role="user", content="hi")],
                    response_model=_SmallResponse,
                )
            )

    argv = exec_mock.await_args.args
    assert "--strict-mcp-config" in argv, (
        f"argv missing --strict-mcp-config: {argv}"
    )
    assert "--mcp-config" in argv, f"argv missing --mcp-config: {argv}"
    assert "-p" in argv, f"argv missing -p: {argv}"

    p_idx = argv.index("-p")
    strict_idx = argv.index("--strict-mcp-config")
    mcp_idx = argv.index("--mcp-config")
    assert strict_idx < p_idx, (
        f"--strict-mcp-config (idx {strict_idx}) must precede -p (idx {p_idx})"
    )
    assert mcp_idx < p_idx, (
        f"--mcp-config (idx {mcp_idx}) must precede -p (idx {p_idx})"
    )
    # --mcp-config takes a path argument immediately following
    assert mcp_idx + 1 < len(argv), "--mcp-config has no following arg"
    config_path = argv[mcp_idx + 1]
    assert isinstance(config_path, str) and config_path.startswith("/"), (
        f"--mcp-config path must be absolute: {config_path!r}"
    )


def test_AC_V025_C5_1_probe_argv_carries_strict_mcp_config_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_probe_claude_authenticated`` argv carries
    ``--strict-mcp-config --mcp-config <path>`` before ``-p``.

    The probe is its own ``claude -p`` fork (construction-time OAuth
    check) — it MUST also be MCP-isolated, otherwise just constructing
    the client kills the parent telegram bot before any real call.
    """
    from src.claude_print_client import ClaudePrintLLMClient

    exec_mock = _make_exec_mock(_envelope("hello"))
    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            # No skip_auth_probe — let the probe fire so we capture its argv.
            ClaudePrintLLMClient()

    assert exec_mock.await_count == 1, (
        f"probe should fire exactly once; awaited {exec_mock.await_count}"
    )
    argv = exec_mock.await_args.args
    assert "--strict-mcp-config" in argv, (
        f"probe argv missing --strict-mcp-config: {argv}"
    )
    assert "--mcp-config" in argv, f"probe argv missing --mcp-config: {argv}"
    assert "-p" in argv, f"probe argv missing -p: {argv}"

    p_idx = argv.index("-p")
    strict_idx = argv.index("--strict-mcp-config")
    mcp_idx = argv.index("--mcp-config")
    assert strict_idx < p_idx
    assert mcp_idx < p_idx


# ---- AC.V025-C5.3 — empty MCP config tempfile contents -------------


def test_AC_V025_C5_3_empty_mcp_config_tempfile_decodes_to_empty_servers_map() -> None:
    """The path passed via ``--mcp-config`` MUST point at a JSON file
    whose decoded content is exactly ``{"mcpServers": {}}``.
    """
    from src.claude_print_client import ClaudePrintLLMClient

    exec_mock = _make_exec_mock(_envelope('{"kind":"x","count":0}'))
    with patch("src.claude_print_client.shutil.which", return_value="/bin/claude"):
        with patch(
            "src.claude_print_client.asyncio.create_subprocess_exec",
            new=exec_mock,
        ):
            client = ClaudePrintLLMClient(skip_auth_probe=True)
            asyncio.run(
                client._generate_response(
                    [Message(role="user", content="q")],
                    response_model=_SmallResponse,
                )
            )

    argv = exec_mock.await_args.args
    mcp_idx = argv.index("--mcp-config")
    config_path = argv[mcp_idx + 1]

    # Resolve and read the file the subprocess WOULD have read.
    assert os.path.exists(config_path), f"empty MCP config tempfile missing: {config_path}"
    with open(config_path) as fh:
        decoded = json.load(fh)
    assert decoded == {"mcpServers": {}}, (
        f"empty MCP config payload must be exactly "
        f'{{"mcpServers": {{}}}}; got {decoded!r}'
    )


def test_AC_V025_C5_3_helper_writes_empty_mcp_config_payload() -> None:
    """Direct unit-test on ``_write_empty_mcp_config()`` — abstracts
    the helper from any client construction so the payload contract
    is tested in isolation.
    """
    from src.claude_print_client import _EMPTY_MCP_CONFIG, _write_empty_mcp_config

    path = _write_empty_mcp_config()
    try:
        assert os.path.exists(path)
        assert path.endswith(".json")
        with open(path) as fh:
            decoded = json.load(fh)
        assert decoded == {"mcpServers": {}}
        assert decoded == _EMPTY_MCP_CONFIG
    finally:
        try:
            os.unlink(path)
        except OSError:
            pass
