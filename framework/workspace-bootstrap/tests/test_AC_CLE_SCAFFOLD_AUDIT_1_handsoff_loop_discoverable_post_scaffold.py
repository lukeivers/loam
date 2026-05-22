# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.CLE.SCAFFOLD-AUDIT.1 — a fresh workspace scaffolded against a
plugins/ tree shipping ``handsoff-loop`` has
``<workspace>/.claude/skills/handsoff-loop/SKILL.md`` reachable
(symlink resolves) with content matching
``plugins/loam-skills/skills/handsoff-loop/SKILL.md``.

Per amendment #144 Scope C: the fresh-workspace closed-loop-engagement
gate. Without this discoverability, non-tech users in fresh workspaces
cannot engage the closed-loop methodology — the SKILL is unreachable
to Claude Code's matcher; the intent-classifier hook's
``additionalContext`` injection has no SKILL to route to.

Composes alongside the existing AC.LAYERED.2 test (which exercises
the general symlinking behaviour); this assertion specifically checks
the closed-loop SKILL's discoverability.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    _symlink_plugin_skills,
)


_HANDSOFF_SKILL_BODY = """---
name: handsoff-loop
description: When the user wants a buildable artifact, invoke the closed-loop methodology.
---

# handsoff-loop

Closed-loop build methodology.
"""


def _author_handsoff_loop_plugin(plugins_root: Path) -> Path:
    """Create a plugins/loam-skills/skills/handsoff-loop/SKILL.md
    file in the given plugins-root and return its absolute path."""
    plugin_dir = plugins_root / "loam-skills"
    skills_dir = plugin_dir / "skills"
    handsoff_dir = skills_dir / "handsoff-loop"
    handsoff_dir.mkdir(parents=True)
    skill_md = handsoff_dir / "SKILL.md"
    skill_md.write_text(_HANDSOFF_SKILL_BODY, encoding="utf-8")
    return skill_md


def test_AC_CLE_SCAFFOLD_AUDIT_1_handsoff_loop_symlinked_post_scaffold(
    tmp_path: Path,
) -> None:
    """After running ``_symlink_plugin_skills`` against a fresh
    workspace whose plugins/ tree ships handsoff-loop, the workspace's
    ``.claude/skills/handsoff-loop/SKILL.md`` resolves to the plugin
    source."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    source_skill_md = _author_handsoff_loop_plugin(plugins)

    written = _symlink_plugin_skills(workspace)

    # The symlinker returns the relative paths it registered.
    assert any("handsoff-loop" in p for p in written), (
        f"handsoff-loop not in written set: {written}"
    )

    # The workspace-side path resolves to a directory (the symlink
    # targets the SKILL directory; SKILL.md sits inside).
    workspace_handsoff_dir = workspace / ".claude" / "skills" / "handsoff-loop"
    assert workspace_handsoff_dir.is_symlink() or workspace_handsoff_dir.is_dir()

    # SKILL.md is reachable via the symlink.
    workspace_handsoff_skill_md = workspace_handsoff_dir / "SKILL.md"
    assert workspace_handsoff_skill_md.is_file(), (
        f"SKILL.md not reachable at {workspace_handsoff_skill_md}"
    )

    # Content matches the source — discovery walks the symlink.
    assert (
        workspace_handsoff_skill_md.read_text(encoding="utf-8")
        == source_skill_md.read_text(encoding="utf-8")
    )


def test_AC_CLE_SCAFFOLD_AUDIT_1_handsoff_loop_symlink_targets_plugin_path(
    tmp_path: Path,
) -> None:
    """The symlink target resolves to the plugin's handsoff-loop
    directory (not a copy) so plugin updates propagate without
    re-bootstrap."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _author_handsoff_loop_plugin(plugins)
    expected_target = (
        plugins / "loam-skills" / "skills" / "handsoff-loop"
    ).resolve()

    _symlink_plugin_skills(workspace)

    workspace_handsoff = workspace / ".claude" / "skills" / "handsoff-loop"
    assert workspace_handsoff.is_symlink()
    resolved = workspace_handsoff.resolve()
    assert resolved == expected_target
