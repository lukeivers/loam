# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.LAYERED.3 + AC.LAYERED.4 — collision-handling halts the scaffold
rather than overwriting operator artefacts or silently picking a
winner across plugins.

Per ``docs/plans/v0-1-7-cycle-3-layered-skill-discovery.md`` §4
+ parent ``docs/plans/v0-1-7-personas-pm-layered-skills.md``:

- AC.LAYERED.3 — workspace-local override collision: operator pre-
  authored ``<workspace>/.claude/skills/<name>/`` as a non-symlink
  directory; scaffold raises ``PluginSkillCollisionError``.
  Operator-precedence preserved (the directory is not overwritten).

- AC.LAYERED.4 — cross-plugin collision: two plugins ship a skill with
  the same name; scaffold raises ``PluginSkillCollisionError`` with a
  ``kind=plugin_skill_cross_plugin_collision`` discriminator naming both
  plugins. Operator (or plugin maintainer) renames one of them.

Existing symlinks (whether pointing at the correct source or
elsewhere) are left untouched — those are also operator decisions
(e.g., the operator manually pointed the symlink at a fork). Only
non-symlink collisions raise.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    PluginSkillCollisionError,
    _symlink_plugin_skills,
)


def _make_plugin_with_skills(
    plugins_root: Path,
    plugin_name: str,
    skill_names: list[str],
) -> None:
    plugin_dir = plugins_root / plugin_name
    skills_dir = plugin_dir / "skills"
    skills_dir.mkdir(parents=True)
    for name in skill_names:
        skill_dir = skills_dir / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: test {name}\n---\n\nbody\n"
        )


# ---- AC.LAYERED.3 — workspace-local override collisions ---------------


def test_collision_with_workspace_local_directory_raises(
    tmp_path: Path,
) -> None:
    """Operator pre-authored ``.claude/skills/memory-recall/`` as a
    real directory (workspace-local override). Scaffold halts with
    ``PluginSkillCollisionError``."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_skills(plugins, "loam-skills", ["memory-recall"])

    # Operator-authored skill at the target path
    skills_dir = workspace / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    operator_skill = skills_dir / "memory-recall"
    operator_skill.mkdir()
    operator_skill_md = operator_skill / "SKILL.md"
    operator_skill_md.write_text(
        "---\nname: memory-recall\ndescription: my override\n---\n"
    )

    with pytest.raises(PluginSkillCollisionError) as exc_info:
        _symlink_plugin_skills(workspace)
    assert "plugin_skill_workspace_override_collision" in str(
        exc_info.value
    )
    assert "memory-recall" in str(exc_info.value)
    # Operator dir + file are preserved (operator-precedence).
    assert operator_skill.is_dir()
    assert not operator_skill.is_symlink()
    assert operator_skill_md.is_file()
    assert (
        "my override" in operator_skill_md.read_text()
    )


def test_collision_with_workspace_local_regular_file_raises(
    tmp_path: Path,
) -> None:
    """Operator pre-authored a regular file at the target path —
    treated the same as a directory collision."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_skills(plugins, "loam-skills", ["memory-recall"])

    skills_dir = workspace / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    rogue_file = skills_dir / "memory-recall"
    rogue_file.write_text(
        "# operator put a regular file here for some reason\n"
    )

    with pytest.raises(PluginSkillCollisionError):
        _symlink_plugin_skills(workspace)
    # File still present.
    assert rogue_file.is_file()
    assert not rogue_file.is_symlink()


def test_existing_symlink_pointing_at_correct_source_is_idempotent(
    tmp_path: Path,
) -> None:
    """Existing symlink to the plugin source — leave alone, no error."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_skills(plugins, "loam-skills", ["memory-recall"])

    plugin_skill = plugins / "loam-skills" / "skills" / "memory-recall"
    skills_dir = workspace / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    target = skills_dir / "memory-recall"
    target.symlink_to(plugin_skill.resolve())

    # Should NOT raise; should NOT recreate.
    written = _symlink_plugin_skills(workspace)
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
    _make_plugin_with_skills(plugins, "loam-skills", ["memory-recall"])

    fork_path = tmp_path / "fork" / "memory-recall"
    fork_path.mkdir(parents=True)
    (fork_path / "SKILL.md").write_text(
        "---\nname: memory-recall\ndescription: my fork\n---\n"
    )

    skills_dir = workspace / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    target = skills_dir / "memory-recall"
    target.symlink_to(fork_path)

    # No error; symlink unchanged.
    written = _symlink_plugin_skills(workspace)
    assert written == ()
    assert target.is_symlink()
    # Still pointing at the fork.
    assert target.resolve() == fork_path.resolve()


# ---- AC.LAYERED.4 — cross-plugin collisions ----------------------------


def test_cross_plugin_collision_raises(tmp_path: Path) -> None:
    """Two plugins ship the same skill name — scaffold halts with
    ``PluginSkillCollisionError`` whose body names both plugins."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    # Both plugins ship "shared-skill"
    _make_plugin_with_skills(plugins, "plugin-a", ["shared-skill"])
    _make_plugin_with_skills(plugins, "plugin-b", ["shared-skill"])

    with pytest.raises(PluginSkillCollisionError) as exc_info:
        _symlink_plugin_skills(workspace)
    assert "plugin_skill_cross_plugin_collision" in str(exc_info.value)
    assert "shared-skill" in str(exc_info.value)
    # Both plugin names surfaced for operator triage.
    assert "plugin-a" in str(exc_info.value)
    assert "plugin-b" in str(exc_info.value)


def test_cross_plugin_collision_first_wins_then_raises(
    tmp_path: Path,
) -> None:
    """Cross-plugin collision is detected on the SECOND plugin's
    pass — by the time the exception fires, the first plugin's
    skills have already been symlinked. Scaffold-halt is the
    operator's signal to fix the plugin-tier collision before
    re-running."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    # Plugin-a (alphabetically first) — ships `shared-skill` + a
    # unique `a-only-skill`.
    _make_plugin_with_skills(
        plugins, "plugin-a", ["shared-skill", "a-only-skill"]
    )
    # Plugin-b — ships the same `shared-skill` (collision).
    _make_plugin_with_skills(plugins, "plugin-b", ["shared-skill"])

    with pytest.raises(PluginSkillCollisionError):
        _symlink_plugin_skills(workspace)

    # Plugin-a's skills are already symlinked at the time of raise —
    # this is fine; the operator's resolution (rename one) will
    # converge to a clean state on the next scaffold run.
    skills_dir = workspace / ".claude" / "skills"
    assert (skills_dir / "shared-skill").is_symlink()
    assert (skills_dir / "shared-skill").resolve() == (
        plugins / "plugin-a" / "skills" / "shared-skill"
    ).resolve()
    assert (skills_dir / "a-only-skill").is_symlink()


def test_cross_plugin_collision_against_existing_symlink_target(
    tmp_path: Path,
) -> None:
    """If a previous run already symlinked plugin-a's skill, a NEW
    plugin-b shipping the same skill name still raises on the next
    run — the cross-plugin discipline applies whether the target
    already exists as a symlink or not."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_skills(plugins, "plugin-a", ["shared-skill"])

    # First run — clean.
    _symlink_plugin_skills(workspace)
    target = workspace / ".claude" / "skills" / "shared-skill"
    assert target.is_symlink()

    # Now plugin-b ships the same skill name.
    _make_plugin_with_skills(plugins, "plugin-b", ["shared-skill"])

    # Second run raises.
    with pytest.raises(PluginSkillCollisionError) as exc_info:
        _symlink_plugin_skills(workspace)
    assert "plugin_skill_cross_plugin_collision" in str(exc_info.value)
    # Existing symlink to plugin-a is still present.
    assert target.is_symlink()
    assert target.resolve() == (
        plugins / "plugin-a" / "skills" / "shared-skill"
    ).resolve()
