# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.PERSONAS.7 — collision-handling on existing non-symlink file at
``<workspace>/.claude/agents/<name>.md`` halts the scaffold rather
than overwrites the operator's file.

Per ``docs/rebuild/plans/v0-1-7-personas-pm-layered-skills.md`` §5
AC.PERSONAS.7 + Surface #2: operator-precedence is preserved
structurally. A workspace-authored agent file at the target path
beats the plugin's offering; the scaffold raises
``PluginAgentCollisionError`` so the operator either renames their
file or deletes it to accept the plugin agent.

Existing symlinks (whether pointing at the correct source or
elsewhere) are left untouched — those are also operator decisions
(e.g., the operator manually pointed the symlink at a fork of the
plugin agent). Only NON-symlink collisions raise.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    PluginAgentCollisionError,
    _symlink_plugin_agents,
)


def _make_plugin_with_agents(
    plugins_root: Path,
    plugin_name: str,
    agent_names: list[str],
) -> None:
    plugin_dir = plugins_root / plugin_name
    agents_dir = plugin_dir / "agents"
    agents_dir.mkdir(parents=True)
    for name in agent_names:
        (agents_dir / f"{name}.md").write_text(
            f"---\nname: {name}\ndescription: test {name}\n---\n\nbody\n"
        )


def test_collision_with_regular_file_raises(tmp_path: Path) -> None:
    """Operator pre-authored ``.claude/agents/loam-builder.md`` as a
    regular file. Scaffold halts with ``PluginAgentCollisionError``."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_agents(plugins, "dev-sdlc", ["loam-builder"])

    # Operator-authored file at the target path
    agents_dir = workspace / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    operator_file = agents_dir / "loam-builder.md"
    operator_file.write_text("# operator's own loam-builder\n")

    with pytest.raises(PluginAgentCollisionError) as exc_info:
        _symlink_plugin_agents(workspace)
    assert "plugin_agent_collision" in str(exc_info.value)
    assert "loam-builder" in str(exc_info.value)
    # File is preserved (operator-precedence).
    assert operator_file.is_file()
    assert not operator_file.is_symlink()
    assert (
        operator_file.read_text() == "# operator's own loam-builder\n"
    )


def test_existing_symlink_pointing_at_correct_source_is_idempotent(
    tmp_path: Path,
) -> None:
    """Existing symlink to the plugin source — leave alone, no error."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_agents(plugins, "dev-sdlc", ["loam-builder"])

    plugin_agent = plugins / "dev-sdlc" / "agents" / "loam-builder.md"
    agents_dir = workspace / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    target = agents_dir / "loam-builder.md"
    target.symlink_to(plugin_agent.resolve())

    # Should NOT raise; should NOT recreate.
    written = _symlink_plugin_agents(workspace)
    assert written == ()  # nothing new written
    assert target.is_symlink()


def test_existing_symlink_pointing_elsewhere_is_left_alone(
    tmp_path: Path,
) -> None:
    """Operator pointed the symlink at a fork — operator-precedence
    leaves it alone; no error.

    This is operator's explicit decision (manual symlink to a fork);
    the scaffold respects it.
    """
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_agents(plugins, "dev-sdlc", ["loam-builder"])

    fork_path = tmp_path / "fork" / "loam-builder.md"
    fork_path.parent.mkdir()
    fork_path.write_text(
        "---\nname: loam-builder\ndescription: my fork\n---\n"
    )

    agents_dir = workspace / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    target = agents_dir / "loam-builder.md"
    target.symlink_to(fork_path)

    # No error; symlink unchanged.
    written = _symlink_plugin_agents(workspace)
    assert written == ()
    assert target.is_symlink()
    # Still pointing at the fork.
    assert target.resolve() == fork_path.resolve()


def test_collision_with_directory_raises(tmp_path: Path) -> None:
    """Operator pre-authored a directory at the target path —
    treated the same as a regular-file collision."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_agents(plugins, "dev-sdlc", ["loam-builder"])

    agents_dir = workspace / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    rogue_dir = agents_dir / "loam-builder.md"
    rogue_dir.mkdir()  # operator-authored directory at target

    with pytest.raises(PluginAgentCollisionError):
        _symlink_plugin_agents(workspace)
    # Directory still present.
    assert rogue_dir.is_dir()
