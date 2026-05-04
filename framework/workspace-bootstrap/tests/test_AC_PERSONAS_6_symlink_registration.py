# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.PERSONAS.6 — workspace-bootstrap symlinks plugin-shipped
subagent personas (``plugins/<plugin>/agents/<name>.md``) into
``<workspace>/.claude/agents/<name>.md`` at first-run.

Per ``docs/rebuild/plans/v0-1-7-personas-pm-layered-skills.md`` §5
AC.PERSONAS.6 + Surface #2: the first-run scaffold scans every
plugin under the resolved plugins/ root, walks each
``<plugin>/agents/*.md``, and creates a symlink at
``<workspace>/.claude/agents/<filename>`` pointing at the plugin
agent file's absolute path.

Symlinks (not copies) so plugin updates propagate without
re-bootstrap. Idempotent: existing symlinks are left untouched;
operator-authored non-symlink files at the target path raise
``PluginAgentCollisionError`` (per AC.PERSONAS.7 — separate test
file). Plugins-root resolution covers both canonical pos-v2
(``<workspace>/plugins/``) and derived workspaces
(``<workspace>/framework/plugins/`` per the D-architecture nesting).
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    _resolve_plugins_root,
    _symlink_plugin_agents,
)


def _make_plugin_with_agents(
    plugins_root: Path,
    plugin_name: str,
    agent_names: list[str],
) -> None:
    """Helper — author a plugin tree with the listed agent files."""
    plugin_dir = plugins_root / plugin_name
    agents_dir = plugin_dir / "agents"
    agents_dir.mkdir(parents=True)
    for name in agent_names:
        (agents_dir / f"{name}.md").write_text(
            f"---\nname: {name}\ndescription: test {name}\n---\n\nbody\n"
        )


def test_resolve_plugins_root_canonical_layout(tmp_path: Path) -> None:
    """Canonical pos-v2 layout — plugins/ at workspace root."""
    workspace = tmp_path / "ws"
    plugins = workspace / "plugins"
    plugins.mkdir(parents=True)

    resolved = _resolve_plugins_root(workspace)
    assert resolved == plugins


def test_resolve_plugins_root_derived_layout(tmp_path: Path) -> None:
    """Derived-workspace layout — plugins/ nested under framework/."""
    workspace = tmp_path / "ws"
    plugins = workspace / "framework" / "plugins"
    plugins.mkdir(parents=True)

    resolved = _resolve_plugins_root(workspace)
    assert resolved == plugins


def test_resolve_plugins_root_neither_present(tmp_path: Path) -> None:
    """No plugins/ in either location — returns None (not an error)."""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    resolved = _resolve_plugins_root(workspace)
    assert resolved is None


def test_resolve_plugins_root_canonical_wins_when_both_present(
    tmp_path: Path,
) -> None:
    """If both layouts exist (unusual), canonical takes precedence."""
    workspace = tmp_path / "ws"
    canonical = workspace / "plugins"
    derived = workspace / "framework" / "plugins"
    canonical.mkdir(parents=True)
    derived.mkdir(parents=True)

    resolved = _resolve_plugins_root(workspace)
    assert resolved == canonical


def test_symlink_plugin_agents_canonical_layout(tmp_path: Path) -> None:
    """Symlinks every agent file from each plugin to .claude/agents/."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()

    _make_plugin_with_agents(
        plugins,
        "dev-sdlc",
        [
            "loam-builder",
            "loam-plan-author",
            "loam-researcher",
            "loam-reviewer",
            "loam-documenter",
        ],
    )

    written = _symlink_plugin_agents(workspace)

    agents_dir = workspace / ".claude" / "agents"
    assert agents_dir.is_dir()
    for handle in (
        "loam-builder",
        "loam-plan-author",
        "loam-researcher",
        "loam-reviewer",
        "loam-documenter",
    ):
        target = agents_dir / f"{handle}.md"
        assert target.is_symlink(), (
            f"{handle}.md should be a symlink"
        )
        # Symlink resolves to the plugin agent file (use resolve()
        # rather than readlink() because the source is absolute).
        assert target.resolve() == (
            plugins / "dev-sdlc" / "agents" / f"{handle}.md"
        ).resolve()
    # Returned tuple is non-empty + matches the count of files
    # symlinked.
    assert len(written) == 5


def test_symlink_plugin_agents_derived_layout(tmp_path: Path) -> None:
    """Derived-workspace layout — same behavior, different source path."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "framework" / "plugins"
    plugins.mkdir(parents=True)

    _make_plugin_with_agents(
        plugins, "dev-sdlc", ["loam-builder", "loam-plan-author"]
    )

    written = _symlink_plugin_agents(workspace)

    agents_dir = workspace / ".claude" / "agents"
    for handle in ("loam-builder", "loam-plan-author"):
        target = agents_dir / f"{handle}.md"
        assert target.is_symlink()
        assert target.resolve() == (
            plugins / "dev-sdlc" / "agents" / f"{handle}.md"
        ).resolve()
    assert len(written) == 2


def test_symlink_plugin_agents_idempotent(tmp_path: Path) -> None:
    """Running twice does not duplicate or rewrite symlinks."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_agents(plugins, "dev-sdlc", ["loam-builder"])

    written_first = _symlink_plugin_agents(workspace)
    target = workspace / ".claude" / "agents" / "loam-builder.md"
    first_inode = target.lstat().st_ino

    written_second = _symlink_plugin_agents(workspace)
    second_inode = target.lstat().st_ino

    # First run wrote the symlink.
    assert len(written_first) == 1
    # Second run returned empty tuple (nothing new written).
    assert len(written_second) == 0
    # Symlink inode unchanged — confirms we didn't recreate it.
    assert first_inode == second_inode


def test_symlink_plugin_agents_no_plugins_returns_empty(
    tmp_path: Path,
) -> None:
    """Workspace without any plugins/ tree returns empty tuple."""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    written = _symlink_plugin_agents(workspace)
    assert written == ()


def test_symlink_plugin_agents_plugin_without_agents_dir(
    tmp_path: Path,
) -> None:
    """Plugin without an agents/ subdirectory is skipped silently."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    # Plugin with NO agents/ subdir
    (plugins / "loam-skills").mkdir()
    # Plugin WITH agents/
    _make_plugin_with_agents(plugins, "dev-sdlc", ["loam-builder"])

    written = _symlink_plugin_agents(workspace)

    target = workspace / ".claude" / "agents" / "loam-builder.md"
    assert target.is_symlink()
    assert len(written) == 1


def test_symlink_plugin_agents_walks_all_plugins(tmp_path: Path) -> None:
    """Multiple plugins each contribute their agents."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_agents(plugins, "dev-sdlc", ["loam-builder"])
    _make_plugin_with_agents(
        plugins, "hypothetical-plugin", ["specialist"]
    )

    written = _symlink_plugin_agents(workspace)

    agents_dir = workspace / ".claude" / "agents"
    assert (agents_dir / "loam-builder.md").is_symlink()
    assert (agents_dir / "specialist.md").is_symlink()
    assert len(written) == 2
