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

"""Amendment #47 acceptance test — AC47.2.

Re-running first-run on a workspace whose ``.mcp.json`` contains
pre-existing user-added MCP server entries deep-merges the
``memory-graphiti`` entry without removing or modifying user
entries. Other top-level keys are also preserved.

Idempotency add-on: a second scaffold invocation against an
already-current ``.mcp.json`` produces a byte-equal output
(``reason="already_current"``, no mtime churn).
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
    write_mcp_json,
)


def _stub_tracker_seed_runner(**kwargs):
    from loam.workspace_bootstrap.adapters import tracker_seed

    return tracker_seed.TrackerSeedResult(
        seeded=False,
        reason="skipped_test_stub",
        classification="user",
        root_id=None,
        descendants_seeded=(),
        value_prop_source=None,
    )


@pytest.mark.skip(
    reason=(
        "FBE.7 (v0.1.0 foldback): scaffold doesn't write .mcp.json at "
        "v0.1.0 (memory-graphiti retired from _SERVICE_KINDS); the "
        "deep-merge contract is exercised by the pure-function tests "
        "below (write_mcp_json direct invocation). M-GMP restores the "
        "scaffold-integration variant post-v0.1.0. See "
        "docs/rebuild/plans/v0-1-0-foldback-scope-expansion-fbe7.md."
    )
)
def test_AC47_2_deep_merge_preserves_user_entries(
    tmp_path: Path,
) -> None:
    """User-authored ``mcpServers`` entries + user-authored
    top-level keys survive the scaffold's deep-merge. The
    framework adds ``memory-graphiti`` without disturbing the
    user's content."""
    workspace = tmp_path / "alpha-ws"
    workspace.mkdir()
    pos_root = tmp_path / "pos-alpha"
    agents = tmp_path / "LaunchAgents-alpha"

    # Pre-write a user-authored .mcp.json with an unrelated MCP
    # server entry + a top-level key the framework does not
    # recognise. The merge must preserve both.
    user_authored = {
        "mcpServers": {
            "my-tool": {
                "type": "stdio",
                "command": "/usr/local/bin/my-tool",
                "args": ["--flag"],
            }
        },
        "_user_comment": "this top-level key is mine",
    }
    target = workspace / "workspace" / MCP_JSON_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(user_authored, indent=2) + "\n")

    # Run the scaffold (fresh, with starter memory.yaml).
    run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    parsed = json.loads(target.read_text())

    # AC47.2: user's MCP server entry is unchanged.
    assert "my-tool" in parsed["mcpServers"]
    assert parsed["mcpServers"]["my-tool"] == {
        "type": "stdio",
        "command": "/usr/local/bin/my-tool",
        "args": ["--flag"],
    }
    # AC47.2: framework's memory-graphiti entry is added.
    assert MEMORY_GRAPHITI_SERVER_NAME in parsed["mcpServers"]
    assert parsed["mcpServers"][MEMORY_GRAPHITI_SERVER_NAME]["type"] == "http"
    # AC47.2: user's top-level key is unchanged.
    assert parsed["_user_comment"] == "this top-level key is mine"


def test_AC47_2_idempotent_no_op_on_already_current_content(
    tmp_path: Path,
) -> None:
    """A second writer invocation on an already-current
    ``.mcp.json`` produces ``reason="already_current"``,
    ``wrote=False``, and the on-disk bytes are unchanged."""
    workspace = tmp_path / "alpha-ws"
    workspace.mkdir()

    # First write: from scratch.
    first = write_mcp_json(
        workspace_root=workspace, host="127.0.0.1", port=8765
    )
    assert first.wrote is True
    assert first.reason == "fresh_write"

    target = workspace / "workspace" / MCP_JSON_FILENAME
    bytes_after_first = target.read_bytes()

    # Second write: same input → already_current.
    second = write_mcp_json(
        workspace_root=workspace, host="127.0.0.1", port=8765
    )
    assert second.wrote is False
    assert second.reason == "already_current"
    assert target.read_bytes() == bytes_after_first


def test_AC47_2_re_merge_overwrites_stale_memory_graphiti_entry(
    tmp_path: Path,
) -> None:
    """If a stale ``memory-graphiti`` entry is on disk (e.g. an
    older port), re-running deep-merge replaces it with the
    current value while leaving any sibling user entry alone.
    The framework owns the identity of the ``memory-graphiti``
    key; the user owns every other key."""
    workspace = tmp_path / "alpha-ws"
    workspace.mkdir()

    stale = {
        "mcpServers": {
            "memory-graphiti": {
                "type": "http",
                "url": "http://127.0.0.1:8000/mcp",
            },
            "my-tool": {"type": "stdio", "command": "/bin/echo"},
        }
    }
    target = workspace / "workspace" / MCP_JSON_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(stale, indent=2) + "\n")

    result = write_mcp_json(
        workspace_root=workspace, host="127.0.0.1", port=19876
    )
    assert result.wrote is True
    assert result.reason == "merged"

    parsed = json.loads(target.read_text())
    # Framework entry replaced.
    assert (
        parsed["mcpServers"]["memory-graphiti"]["url"]
        == "http://127.0.0.1:19876/mcp"
    )
    # User's sibling entry preserved.
    assert parsed["mcpServers"]["my-tool"] == {
        "type": "stdio",
        "command": "/bin/echo",
    }
