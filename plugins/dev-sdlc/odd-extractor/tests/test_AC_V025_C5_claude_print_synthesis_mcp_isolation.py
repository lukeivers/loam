"""Acceptance tests for v0.2.5 corrective C5 —
claude -p subprocess MCP-isolation flags (odd-extractor synthesis half).

Closes:
- AC.V025-C5.2 — odd-extractor ``ClaudePrintAnthropicShimClient``
  argv carries ``--strict-mcp-config --mcp-config <abs path>``
  BEFORE ``-p`` for every ``messages.create(...)`` invocation.
- AC.V025-C5.3 (synthesis half) — empty MCP config tempfile
  decodes to exactly ``{"mcpServers": {}}``.

Why this matters: without these flags, the child claude inherits the
parent session's MCP server config including the telegram MCP. The
telegram loader at
``~/.claude/plugins/cache/claude-plugins-official/telegram/0.0.6/server.ts:60-78``
SIGTERMs any prior PID-file holder via its dedup branch. Result: every
synthesis call that forks ``claude -p`` kills the parent session's
telegram bot. Owner ruling 2026-05-05 (Telegram 10196): subprocess
invocations must launch without telegram.

The fix mirrors the precedent at
``framework/workspace-sync/src/loam/workspace_sync/_resolver_client.py``
(AC.WSα.8, verified 2026-04-27) and the memory-system half
(``framework/memory-system/src/claude_print_client.py``).

Tests use ``subprocess.run`` mocking — no real ``claude -p`` spawns.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest import mock


def _fake_claude_binary(tmp_path: Path) -> str:
    """Materialise a fake claude binary on disk so ``shutil.which``-style
    resolution paths through ``binary_path=`` work without monkeypatching.
    """
    p = tmp_path / "claude_fake"
    p.write_text("#!/bin/sh\nexit 0\n")
    p.chmod(0o755)
    return str(p)


def _envelope_bytes() -> bytes:
    """A minimal valid claude -p --output-format json envelope."""
    return json.dumps(
        {
            "type": "result",
            "result": "{}",
            "total_cost_usd": 0.0,
            "is_error": False,
            "usage": {"input_tokens": 5, "output_tokens": 5},
        }
    ).encode()


def test_AC_V025_C5_2_synthesis_argv_carries_strict_mcp_config_flags(
    tmp_path: Path,
) -> None:
    """``_invoke_claude_print`` argv carries
    ``--strict-mcp-config --mcp-config <path>`` before ``-p``.
    """
    from loam_odd_extractor.claude_print_synthesis_client import (
        ClaudePrintAnthropicShimClient,
    )

    fake_binary = _fake_claude_binary(tmp_path)
    client = ClaudePrintAnthropicShimClient(binary_path=fake_binary)

    captured: dict[str, list[str]] = {}

    def _fake_run(argv, **_kwargs):
        captured["argv"] = list(argv)
        completed = mock.MagicMock()
        completed.returncode = 0
        completed.stdout = _envelope_bytes()
        completed.stderr = b""
        return completed

    with mock.patch(
        "loam_odd_extractor.claude_print_synthesis_client.subprocess.run",
        side_effect=_fake_run,
    ):
        client.messages.create(
            model="claude-sonnet-4-5",
            system="sys-prompt",
            messages=[{"role": "user", "content": "hi"}],
        )

    argv = captured["argv"]
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
    # --mcp-config's path argument follows immediately
    assert mcp_idx + 1 < len(argv), "--mcp-config has no following arg"
    config_path = argv[mcp_idx + 1]
    assert isinstance(config_path, str) and config_path.startswith("/"), (
        f"--mcp-config path must be absolute: {config_path!r}"
    )


def test_AC_V025_C5_3_synthesis_empty_mcp_config_payload(tmp_path: Path) -> None:
    """The path passed via ``--mcp-config`` from the synthesis client MUST
    point at a JSON file whose decoded content is exactly
    ``{"mcpServers": {}}``.
    """
    from loam_odd_extractor.claude_print_synthesis_client import (
        ClaudePrintAnthropicShimClient,
    )

    fake_binary = _fake_claude_binary(tmp_path)
    client = ClaudePrintAnthropicShimClient(binary_path=fake_binary)

    captured: dict[str, list[str]] = {}

    def _fake_run(argv, **_kwargs):
        captured["argv"] = list(argv)
        completed = mock.MagicMock()
        completed.returncode = 0
        completed.stdout = _envelope_bytes()
        completed.stderr = b""
        return completed

    with mock.patch(
        "loam_odd_extractor.claude_print_synthesis_client.subprocess.run",
        side_effect=_fake_run,
    ):
        client.messages.create(
            system="",
            messages=[{"role": "user", "content": "q"}],
        )

    argv = captured["argv"]
    mcp_idx = argv.index("--mcp-config")
    config_path = argv[mcp_idx + 1]

    assert os.path.exists(config_path), (
        f"empty MCP config tempfile missing: {config_path}"
    )
    with open(config_path) as fh:
        decoded = json.load(fh)
    assert decoded == {"mcpServers": {}}, (
        f"empty MCP config payload must be exactly "
        f'{{"mcpServers": {{}}}}; got {decoded!r}'
    )


def test_AC_V025_C5_3_synthesis_helper_writes_empty_mcp_config() -> None:
    """Direct unit-test on ``_write_empty_mcp_config()`` — payload contract
    in isolation from client construction.
    """
    from loam_odd_extractor.claude_print_synthesis_client import (
        _EMPTY_MCP_CONFIG,
        _write_empty_mcp_config,
    )

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
