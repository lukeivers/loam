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

"""Amendment #47 acceptance test — AC47.1.

After ``run_first_run_scaffold`` completes on a fresh-clone
workspace, ``<workspace>/.mcp.json`` exists and contains exactly
one entry under ``mcpServers`` (key ``memory-graphiti``) whose
``type`` is ``"http"`` and whose URL resolves to the per-workspace
port allocated in ``<pos_root>/memory.yaml`` (per amendment #29).

Per the umbrella plan §4b objective: "After this amendment lands,
Claude Code sessions discover and bind the memory-system's MCP
tools at session-start, making them callable as
``mcp__memory-graphiti__<tool>`` during turns."
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    run_first_run_scaffold,
)
from loam.workspace_bootstrap.adapters.mcp_json_writer import (
    MCP_JSON_FILENAME,
    MEMORY_GRAPHITI_SERVER_NAME,
    STREAMABLE_HTTP_PATH,
)


# FBE.7 (v0.1.0 foldback): the scaffold no longer writes ``.mcp.json``
# at v0.1.0 because ``memory-graphiti`` is no longer in
# ``_SERVICE_KINDS`` per Luke's 2026-05-03 ruling. The pure-function
# builders inside ``mcp_json_writer.py`` are still used by AC47.2's
# pure-function variants and will be re-wired by M-GMP post-v0.1.0.
# The scaffold-integration variants below are skipped at v0.1.0. See
# ``docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.md``.
pytestmark = pytest.mark.skip(
    reason=(
        "FBE.7 (v0.1.0 foldback): scaffold doesn't write .mcp.json at "
        "v0.1.0; M-GMP restores the writer's invocation post-v0.1.0."
    )
)


def _stub_tracker_seed_runner(**kwargs):
    """No-op tracker-seed runner so AC47 tests don't depend on the
    objective-tracker subsystem (already covered by amendment #39).

    Mirrors the shape ``tracker_seed.run_seed_synchronously``
    returns; AC47 only cares that the scaffold flow reaches the
    ``.mcp.json`` writer step.
    """
    from loam.workspace_bootstrap.adapters import tracker_seed

    return tracker_seed.TrackerSeedResult(
        seeded=False,
        reason="skipped_test_stub",
        classification="user",
        root_id=None,
        descendants_seeded=(),
        value_prop_source=None,
    )


def test_AC47_1_fresh_clone_writes_mcp_json_with_memory_graphiti_entry(
    tmp_path: Path,
) -> None:
    """Fresh-clone first-run writes ``<workspace>/.mcp.json``
    with exactly one ``mcpServers`` entry pointing at the
    workspace's allocated memory-sidecar port."""
    workspace = tmp_path / "alpha-ws"
    workspace.mkdir()
    pos_root = tmp_path / "pos-alpha"
    agents = tmp_path / "LaunchAgents-alpha"

    # Fresh-scaffold path: pos_root absent → write all the YAMLs
    # including the starter ``memory.yaml`` (port 8765 default).
    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    # AC47.1: file exists at workspace root.
    mcp_json_path = workspace / "workspace" / MCP_JSON_FILENAME
    assert mcp_json_path.exists(), (
        f"`.mcp.json` was not written; "
        f"ScaffoldResult.mcp_json_path={result.mcp_json_path!r}, "
        f"mcp_json_wrote={result.mcp_json_wrote!r}, "
        f"mcp_json_reason={result.mcp_json_reason!r}"
    )

    # ScaffoldResult surfaces the structured outcome.
    assert result.mcp_json_path == mcp_json_path.resolve()
    assert result.mcp_json_wrote is True
    assert result.mcp_json_reason == "fresh_write"

    # AC47.1: shape — exactly one mcpServers entry, ``memory-graphiti``,
    # with type "http" and URL pointing at the workspace's port.
    parsed = json.loads(mcp_json_path.read_text())
    assert isinstance(parsed, dict)
    servers = parsed.get("mcpServers")
    assert isinstance(servers, dict)
    assert MEMORY_GRAPHITI_SERVER_NAME in servers
    entry = servers[MEMORY_GRAPHITI_SERVER_NAME]
    assert entry["type"] == "http"
    # Default starter port from the scaffolded memory.yaml is 8765.
    expected_url = f"http://127.0.0.1:8765{STREAMABLE_HTTP_PATH}"
    assert entry["url"] == expected_url, (
        f"URL did not carry default starter port; got {entry['url']!r}"
    )


def test_AC47_1_url_port_reflects_workspace_specific_memory_yaml_port(
    tmp_path: Path,
) -> None:
    """A workspace whose ``memory.yaml`` declares a non-default
    port produces an `.mcp.json` URL with that port. Mirrors the
    AC29.3 isolation shape: per-workspace ``memory.yaml`` is the
    source of truth."""
    workspace = tmp_path / "beta-ws"
    workspace.mkdir()
    pos_root = tmp_path / "pos-beta"
    agents = tmp_path / "LaunchAgents-beta"

    # Pre-seed memory.yaml with a non-default port + a stub
    # bootstrap.yaml so partial_recovery=True respects the
    # operator-edited port (mirrors AC29.2 test fixture shape).
    pos_root.mkdir(parents=True, exist_ok=True)
    (pos_root / "memory.yaml").write_text(
        "launch: true\n"
        "host: 127.0.0.1\n"
        "port: 19876\n"
        "health_path: /health\n"
        "startup_timeout_s: 30\n"
        "poll_interval_s: 0.5\n"
    )
    (pos_root / "bootstrap.yaml").write_text("contributions: []\n")

    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
        partial_recovery=True,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    mcp_json_path = workspace / "workspace" / MCP_JSON_FILENAME
    assert mcp_json_path.exists()
    parsed = json.loads(mcp_json_path.read_text())
    entry = parsed["mcpServers"][MEMORY_GRAPHITI_SERVER_NAME]
    assert entry["url"] == f"http://127.0.0.1:19876{STREAMABLE_HTTP_PATH}", (
        f"URL did not propagate workspace-specific port 19876; "
        f"got {entry['url']!r}"
    )
