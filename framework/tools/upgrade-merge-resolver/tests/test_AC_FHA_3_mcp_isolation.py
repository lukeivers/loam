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

"""AC.FHA.3 — claude -p MCP-isolation invariant for upgrade-merge-resolver.

Mirrors the workspace-sync invariant test at
``framework/workspace-sync/tests/test_resolver_client_mcp_isolation.py``
because the same invariant binds every loam-spawned ``claude -p``
subprocess. The v0.2.5 incident — child ``claude -p`` killing the
parent's Telegram MCP — proved the flag-set is load-bearing.

Verified:

  1. argv carries ``--strict-mcp-config`` + ``--mcp-config <path>`` and
     both precede ``-p``.
  2. The path resolves to a file whose JSON content is exactly
     ``{"mcpServers": {}}`` (zero-server isolation).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest import mock

from pydantic import BaseModel

from loam.upgrade_merge_resolver import _ClaudePrintResolverClient


class _DummyVerdict(BaseModel):
    resolution: str
    rationale: str
    confidence: float


def _fake_claude_binary(tmp_path: Path) -> str:
    """Materialise a fake claude binary on disk; never invoked
    end-to-end since subprocess.run is mocked, but the resolver
    constructor checks the binary exists."""
    p = tmp_path / "claude_fake"
    p.write_text("#!/bin/sh\nexit 0\n")
    p.chmod(0o755)
    return str(p)


def test_AC_FHA_3_argv_carries_strict_mcp_config_flags(tmp_path: Path) -> None:
    """argv carries --strict-mcp-config + --mcp-config <path> before -p."""
    fake_binary = _fake_claude_binary(tmp_path)
    client = _ClaudePrintResolverClient(binary_path=fake_binary)

    captured: dict[str, list[str]] = {}

    def _fake_run(argv, **_kwargs):
        captured["argv"] = list(argv)
        completed = mock.MagicMock()
        completed.returncode = 0
        completed.stdout = (
            b'{"result": "{\\"resolution\\": \\"r\\", '
            b'\\"rationale\\": \\"r\\", '
            b'\\"confidence\\": 0.9}", '
            b'"is_error": false, '
            b'"usage": {"input_tokens": 10, "output_tokens": 10}}'
        )
        completed.stderr = b""
        return completed

    with mock.patch(
        "loam.upgrade_merge_resolver.subprocess.run",
        side_effect=_fake_run,
    ):
        client.invoke("hello", _DummyVerdict)

    argv = captured["argv"]
    assert "--strict-mcp-config" in argv, (
        f"argv missing --strict-mcp-config: {argv}"
    )
    assert "--mcp-config" in argv, f"argv missing --mcp-config: {argv}"
    strict_idx = argv.index("--strict-mcp-config")
    mcp_idx = argv.index("--mcp-config")
    p_idx = argv.index("-p")
    assert strict_idx < p_idx, (
        f"--strict-mcp-config (idx {strict_idx}) must precede -p "
        f"(idx {p_idx})"
    )
    assert mcp_idx < p_idx, (
        f"--mcp-config (idx {mcp_idx}) must precede -p (idx {p_idx})"
    )
    path = argv[mcp_idx + 1]
    assert Path(path).exists(), (
        f"--mcp-config path {path} must point at an existing file"
    )


def test_AC_FHA_3_empty_mcp_config_file_contains_empty_servers(
    tmp_path: Path,
) -> None:
    """The --mcp-config file holds exactly {'mcpServers': {}}."""
    fake_binary = _fake_claude_binary(tmp_path)
    client = _ClaudePrintResolverClient(binary_path=fake_binary)
    path = client._empty_mcp_config_path
    content = json.loads(Path(path).read_text())
    assert content == {"mcpServers": {}}, (
        f"empty MCP config must isolate the subprocess; got {content}"
    )
