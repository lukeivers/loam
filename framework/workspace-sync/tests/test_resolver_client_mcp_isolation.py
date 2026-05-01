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

"""AC.WSα.8 — α.3 MCP-isolated subprocess invocation.

The resolver's ``claude -p`` subprocess MUST run with MCP isolation
so it does not load the parent session's MCP servers (preventing
bun-process contention with the user's telegram MCP /
memory-graphiti MCP, etc.). Verified by:

  1. argv shape carries ``--strict-mcp-config`` + ``--mcp-config <path>``
     before ``-p``.
  2. The path file contains exactly ``{"mcpServers": {}}``.

D-3 RE-LOCKED 2026-04-27 — uses MCP-isolation flags rather than
``--bare`` (which is auth-incompatible with Claude Max OAuth).
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from unittest import mock

import pytest

from loam.workspace_sync._resolver_client import (
    _ClaudePrintResolverClient,
)
from loam.workspace_sync.merge_resolver import ResolverFailure


def _fake_claude_binary(tmp_path: Path) -> str:
    """Materialise a fake claude binary on disk.

    The shell wrapper exits 0 and emits a minimal envelope so
    we can intercept argv via subprocess mock without hitting a
    real binary. Returns the absolute path.
    """
    p = tmp_path / "claude_fake"
    p.write_text("#!/bin/sh\nexit 0\n")
    p.chmod(0o755)
    return str(p)


def test_argv_carries_strict_mcp_config_flags(tmp_path: Path) -> None:
    """AC.WSα.8: every invoke() carries --strict-mcp-config + --mcp-config <path>."""
    fake_binary = _fake_claude_binary(tmp_path)
    client = _ClaudePrintResolverClient(binary_path=fake_binary)

    captured: dict[str, list[str]] = {}

    def _fake_run(argv, **_kwargs):
        captured["argv"] = list(argv)
        # Return an envelope that decodes valid (avoid downstream parse errors).
        completed = mock.MagicMock()
        completed.returncode = 0
        completed.stdout = b'{"result": "{\\"resolution\\": \\"inferred-accept-canonical\\", \\"rationale\\": \\"r\\", \\"confidence\\": 0.9}", "is_error": false, "usage": {"input_tokens": 10, "output_tokens": 10}}'
        completed.stderr = b""
        return completed

    from loam.workspace_sync.merge_resolver import MergeVerdict

    with mock.patch("loam.workspace_sync._resolver_client.subprocess.run", side_effect=_fake_run):
        client.invoke("hello", MergeVerdict)

    argv = captured["argv"]
    # Must contain --strict-mcp-config + --mcp-config <path>, in order,
    # before -p (which is the print-mode binding flag).
    assert "--strict-mcp-config" in argv
    assert "--mcp-config" in argv
    strict_idx = argv.index("--strict-mcp-config")
    mcp_idx = argv.index("--mcp-config")
    p_idx = argv.index("-p")
    assert strict_idx < p_idx, "--strict-mcp-config must precede -p"
    assert mcp_idx < p_idx, "--mcp-config must precede -p"
    # The argument immediately after --mcp-config is the path.
    path = argv[mcp_idx + 1]
    assert Path(path).exists(), f"--mcp-config path {path} must point at an existing file"


def test_empty_mcp_config_file_contains_empty_servers(tmp_path: Path) -> None:
    """AC.WSα.8: the path file holds exactly {"mcpServers": {}}."""
    fake_binary = _fake_claude_binary(tmp_path)
    client = _ClaudePrintResolverClient(binary_path=fake_binary)
    path = client._empty_mcp_config_path
    content = json.loads(Path(path).read_text())
    assert content == {"mcpServers": {}}
