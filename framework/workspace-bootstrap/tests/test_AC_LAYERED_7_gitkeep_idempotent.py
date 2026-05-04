# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.LAYERED.7 — ``<workspace>/.claude/skills/.gitkeep`` is idempotent
across scaffold + symlink runs.

Per ``docs/rebuild/plans/v0-1-7-cycle-3-layered-skill-discovery.md`` §4
+ §7 Method choice 7: the v0.1.6 ``.gitkeep`` pre-create is preserved
across the Cycle 3 ``_symlink_plugin_skills`` flow. The skills
directory is created at scaffold time; the symlink loop afterwards
adds children but never touches the .gitkeep file.

This test extends the existing v0.1.6 AC.SKILLS-BUG.2 angle to confirm
that the Cycle 3 layer composes cleanly with the v0.1.6 .gitkeep
preservation.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    _symlink_plugin_skills,
    _write_skills_gitkeep,
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
            f"---\nname: {name}\n---\n"
        )


def test_gitkeep_preserved_after_symlink_run(tmp_path: Path) -> None:
    """Scaffold writes .gitkeep; symlink-run does not remove or
    rewrite it."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_skills(plugins, "loam-skills", ["memory-recall"])

    # Step 1 — emulate v0.1.6 .gitkeep pre-create.
    wrote = _write_skills_gitkeep(workspace)
    assert wrote is True
    gitkeep = workspace / ".claude" / "skills" / ".gitkeep"
    assert gitkeep.is_file()

    # Step 2 — Cycle 3 symlink-run.
    _symlink_plugin_skills(workspace)

    # .gitkeep still present + still empty.
    assert gitkeep.is_file()
    assert gitkeep.read_text() == ""


def test_gitkeep_with_operator_edits_preserved(tmp_path: Path) -> None:
    """Operator-edited .gitkeep (non-empty) survives both the
    scaffold's idempotent re-run AND the symlink-run."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_skills(plugins, "loam-skills", ["memory-recall"])

    skills_dir = workspace / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    gitkeep = skills_dir / ".gitkeep"
    operator_content = "# operator note: keep this dir\n"
    gitkeep.write_text(operator_content)

    # Idempotent scaffold call — should NOT touch operator-edited file.
    wrote = _write_skills_gitkeep(workspace)
    assert wrote is False
    assert gitkeep.read_text() == operator_content

    # Symlink-run — also should not touch the .gitkeep.
    _symlink_plugin_skills(workspace)
    assert gitkeep.read_text() == operator_content


def test_symlink_run_creates_skills_dir_if_missing(
    tmp_path: Path,
) -> None:
    """If `.claude/skills/` does not exist (i.e., scaffold's
    .gitkeep step did not run yet), the symlink-run still creates
    the directory before walking. Robustness — the symlink helper
    is order-independent w.r.t. the .gitkeep helper."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_skills(plugins, "loam-skills", ["memory-recall"])

    skills_dir = workspace / ".claude" / "skills"
    assert not skills_dir.exists()

    _symlink_plugin_skills(workspace)

    assert skills_dir.is_dir()
    assert (skills_dir / "memory-recall").is_symlink()
