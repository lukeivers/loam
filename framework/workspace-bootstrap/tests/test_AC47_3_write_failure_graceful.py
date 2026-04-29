"""Amendment #47 acceptance test — AC47.3.

Write failure is graceful: malformed pre-existing ``.mcp.json``
preserves user content; IO/permissions error skips the write
without raising. In both cases the scaffold completes; the
SessionStart hook proceeds; the session degrades to "no memory
MCP tools" rather than failing closed.

Mirrors amendment #37 AC37.4's failure-class shape (graceful
degradation when an additive scaffold step cannot complete).
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


def test_AC47_3_malformed_existing_file_is_preserved_not_overwritten(
    tmp_path: Path,
) -> None:
    """A pre-existing ``.mcp.json`` with invalid JSON is left
    untouched. The writer surfaces ``reason=
    "skipped_malformed_existing"``; the user's bytes are
    preserved verbatim."""
    workspace = tmp_path / "alpha-ws"
    workspace.mkdir()

    malformed = workspace / "workspace" / MCP_JSON_FILENAME
    malformed.parent.mkdir(parents=True, exist_ok=True)
    bad_text = "{ this is not valid json :::"
    malformed.write_text(bad_text)

    result = write_mcp_json(
        workspace_root=workspace, host="127.0.0.1", port=8765
    )

    assert result.wrote is False
    assert result.reason == "skipped_malformed_existing"
    # User's bytes survive.
    assert malformed.read_text() == bad_text


def test_AC47_3_non_dict_root_existing_file_is_preserved(
    tmp_path: Path,
) -> None:
    """A pre-existing ``.mcp.json`` whose top-level is a JSON
    array (or any non-object) is left untouched. The writer
    surfaces ``reason="skipped_malformed_existing"``."""
    workspace = tmp_path / "alpha-ws"
    workspace.mkdir()

    target = workspace / "workspace" / MCP_JSON_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    array_root = "[1, 2, 3]"
    target.write_text(array_root)

    result = write_mcp_json(
        workspace_root=workspace, host="127.0.0.1", port=8765
    )

    assert result.wrote is False
    assert result.reason == "skipped_malformed_existing"
    assert target.read_text() == array_root


def test_AC47_3_permission_denied_is_graceful(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An IO/permissions failure during the write surfaces a
    structured ``reason="skipped_io_error"``; no exception
    propagates; the scaffold proceeds.

    Simulates the failure by monkeypatching ``os.replace`` to
    raise ``PermissionError`` — the same kind of failure
    chmod-denied workspace dirs surface in production. (We do
    not chmod the real tmp_path so test cleanup remains clean
    on every CI host.)
    """
    workspace = tmp_path / "alpha-ws"
    workspace.mkdir()

    # Patch os.replace inside mcp_json_writer to simulate
    # permission-denied during the atomic-rename step.
    from loam.workspace_bootstrap.adapters import mcp_json_writer as mjw

    def fake_replace(*args, **kwargs):
        raise PermissionError(13, "Permission denied", str(args[1]))

    monkeypatch.setattr(mjw.os, "replace", fake_replace)

    result = mjw.write_mcp_json(
        workspace_root=workspace, host="127.0.0.1", port=8765
    )

    assert result.wrote is False
    assert result.reason == "skipped_io_error"
    # No `.mcp.json` was produced (the rename failed before final
    # placement). The .tmp leak is cleaned up by the writer's
    # exception handler; verify no leftover .mcp.json.* files
    # accumulate.
    target = workspace / "workspace" / MCP_JSON_FILENAME
    assert not target.exists()


def test_AC47_3_scaffold_completes_when_writer_skips(
    tmp_path: Path,
) -> None:
    """When the writer skips (malformed pre-existing file),
    the scaffold completes (``ran=True``) and the structured
    outcome propagates to ``ScaffoldResult.mcp_json_reason``.
    The scaffold does not raise; SessionStart proceeds."""
    workspace = tmp_path / "alpha-ws"
    workspace.mkdir()
    pos_root = tmp_path / "pos-alpha"
    agents = tmp_path / "LaunchAgents-alpha"

    # Pre-write a malformed .mcp.json the scaffold's writer must
    # leave alone.
    target = workspace / "workspace" / MCP_JSON_FILENAME
    target.parent.mkdir(parents=True, exist_ok=True)
    bad_text = "not valid json"
    target.write_text(bad_text)

    result = run_first_run_scaffold(
        pos_root=pos_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=agents,
        workspace_root=workspace,
        tracker_seed_runner=_stub_tracker_seed_runner,
    )

    assert result.ran is True
    assert result.mcp_json_wrote is False
    assert result.mcp_json_reason == "skipped_malformed_existing"
    # User's malformed file is preserved.
    assert target.read_text() == bad_text
