# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.LAYERED.2 — workspace-bootstrap symlinks plugin-shipped skill
directories (``plugins/<plugin>/skills/<name>/``) into
``<workspace>/.claude/skills/<name>`` at first-run.

Per ``docs/plans/v0-1-7-cycle-3-layered-skill-discovery.md`` §4
+ parent ``docs/plans/v0-1-7-personas-pm-layered-skills.md``
§5 AC.LAYERED.2: the first-run scaffold scans every plugin under the
resolved plugins/ root, walks each ``<plugin>/skills/<name>/``
directory containing a ``SKILL.md``, and creates a symlink at
``<workspace>/.claude/skills/<name>`` pointing at the plugin skill
directory's absolute path.

Symlinks (not copies) so plugin updates propagate without re-bootstrap.
Idempotent: existing symlinks pointing at the correct source are left
untouched. Plugins-root resolution covers both canonical pos-v2
(``<workspace>/plugins/``) and derived workspaces
(``<workspace>/framework/plugins/`` per the D-architecture nesting).

The symlink targets the skill DIRECTORY (not the SKILL.md file) because
skills can ship companion files (scripts/, references/, templates/)
that the Anthropic discovery walk needs intact.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    _symlink_plugin_skills,
)


def _make_plugin_with_skills(
    plugins_root: Path,
    plugin_name: str,
    skill_names: list[str],
) -> None:
    """Helper — author a plugin tree with the listed skill directories,
    each containing a SKILL.md."""
    plugin_dir = plugins_root / plugin_name
    skills_dir = plugin_dir / "skills"
    skills_dir.mkdir(parents=True)
    for name in skill_names:
        skill_dir = skills_dir / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: test {name}\n---\n\nbody\n"
        )


def test_symlink_plugin_skills_canonical_layout(tmp_path: Path) -> None:
    """Symlinks every skill directory from each plugin to .claude/skills/."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()

    _make_plugin_with_skills(
        plugins,
        "loam-skills",
        [
            "memory-recall",
            "scope-decompose",
            "dispatch-with-gates",
            "onboarding-conversation",
            "session-handoff",
            "translation-discipline",
            "audit-block-on-telegram",
            "owner-decision-summary",
        ],
    )

    written = _symlink_plugin_skills(workspace)

    skills_dir = workspace / ".claude" / "skills"
    assert skills_dir.is_dir()
    for handle in (
        "memory-recall",
        "scope-decompose",
        "dispatch-with-gates",
        "onboarding-conversation",
        "session-handoff",
        "translation-discipline",
        "audit-block-on-telegram",
        "owner-decision-summary",
    ):
        target = skills_dir / handle
        assert target.is_symlink(), (
            f"{handle} should be a symlink"
        )
        # Symlink resolves to the plugin SKILL DIRECTORY (not file).
        assert target.resolve() == (
            plugins / "loam-skills" / "skills" / handle
        ).resolve()
        # SKILL.md is reachable through the symlink (whole-directory
        # symlink preserves companion files).
        assert (target / "SKILL.md").is_file()
    # Returned tuple matches the count of skills symlinked.
    assert len(written) == 8


def test_symlink_plugin_skills_derived_layout(tmp_path: Path) -> None:
    """Derived-workspace layout — same behavior, different source path."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "framework" / "plugins"
    plugins.mkdir(parents=True)

    _make_plugin_with_skills(
        plugins, "loam-skills", ["memory-recall", "scope-decompose"]
    )

    written = _symlink_plugin_skills(workspace)

    skills_dir = workspace / ".claude" / "skills"
    for handle in ("memory-recall", "scope-decompose"):
        target = skills_dir / handle
        assert target.is_symlink()
        assert target.resolve() == (
            plugins / "loam-skills" / "skills" / handle
        ).resolve()
    assert len(written) == 2


def test_symlink_plugin_skills_idempotent(tmp_path: Path) -> None:
    """Running twice does not duplicate or rewrite symlinks."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_skills(plugins, "loam-skills", ["memory-recall"])

    written_first = _symlink_plugin_skills(workspace)
    target = workspace / ".claude" / "skills" / "memory-recall"
    first_inode = target.lstat().st_ino

    written_second = _symlink_plugin_skills(workspace)
    second_inode = target.lstat().st_ino

    # First run wrote the symlink.
    assert len(written_first) == 1
    # Second run returned empty tuple (nothing new written).
    assert len(written_second) == 0
    # Symlink inode unchanged — confirms we didn't recreate it.
    assert first_inode == second_inode


def test_symlink_plugin_skills_no_plugins_returns_empty(
    tmp_path: Path,
) -> None:
    """Workspace without any plugins/ tree returns empty tuple."""
    workspace = tmp_path / "ws"
    workspace.mkdir()

    written = _symlink_plugin_skills(workspace)
    assert written == ()


def test_symlink_plugin_skills_plugin_without_skills_dir(
    tmp_path: Path,
) -> None:
    """Plugin without a skills/ subdirectory is skipped silently."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    # Plugin with NO skills/ subdir
    (plugins / "agents-only-plugin").mkdir()
    # Plugin WITH skills/
    _make_plugin_with_skills(plugins, "loam-skills", ["memory-recall"])

    written = _symlink_plugin_skills(workspace)

    target = workspace / ".claude" / "skills" / "memory-recall"
    assert target.is_symlink()
    assert len(written) == 1


def test_symlink_plugin_skills_walks_all_plugins(tmp_path: Path) -> None:
    """Multiple plugins each contribute their skills."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _make_plugin_with_skills(plugins, "loam-skills", ["memory-recall"])
    _make_plugin_with_skills(
        plugins, "hypothetical-plugin", ["domain-specific-skill"]
    )

    written = _symlink_plugin_skills(workspace)

    skills_dir = workspace / ".claude" / "skills"
    assert (skills_dir / "memory-recall").is_symlink()
    assert (skills_dir / "domain-specific-skill").is_symlink()
    assert len(written) == 2


def test_symlink_plugin_skills_skips_flat_file_skills(
    tmp_path: Path,
) -> None:
    """Flat-file ``<plugin>/skills/<name>.md`` shapes are NOT
    auto-symlinked. Anthropic discovery is per-directory; flat-file
    skills are out of fence for the auto-symlinking layer.

    Mirrors the historical pre-promotion shape of
    `plugins/dev-sdlc/skills/start-project.md` (which existed at
    v0.1.0 ship; promoted to subdirectory shape by amendment-
    A-PROMOTE-START-PROJECT, slug
    `loam-skills-start-project-discoverable`). The flat-file
    skip-contract remains exercised against a realistic input shape
    — no real-tree flat-shape SKILL exists post-promotion."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    plugin_skills = plugins / "dev-sdlc" / "skills"
    plugin_skills.mkdir(parents=True)
    # Flat-file skill — should be skipped.
    (plugin_skills / "start-project.md").write_text(
        "---\nname: start-project\n---\n"
    )
    # Directory-shape skill — should be picked up.
    proper_skill = plugin_skills / "proper-skill"
    proper_skill.mkdir()
    (proper_skill / "SKILL.md").write_text(
        "---\nname: proper-skill\n---\n"
    )

    written = _symlink_plugin_skills(workspace)

    skills_dir = workspace / ".claude" / "skills"
    # Flat-file skill not symlinked.
    assert not (skills_dir / "start-project").exists()
    assert not (skills_dir / "start-project.md").exists()
    # Directory-shape skill IS symlinked.
    assert (skills_dir / "proper-skill").is_symlink()
    assert len(written) == 1


def test_symlink_plugin_skills_skips_dirs_without_skill_md(
    tmp_path: Path,
) -> None:
    """A directory under <plugin>/skills/ that does NOT contain
    SKILL.md is not auto-symlinked (silently skipped — not a
    discoverable skill)."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    plugin_skills = plugins / "loam-skills" / "skills"
    plugin_skills.mkdir(parents=True)
    # Directory without SKILL.md — not a skill.
    junk = plugin_skills / "not-a-skill"
    junk.mkdir()
    (junk / "README.md").write_text("just docs")
    # Real skill.
    real = plugin_skills / "memory-recall"
    real.mkdir()
    (real / "SKILL.md").write_text("---\nname: memory-recall\n---\n")

    written = _symlink_plugin_skills(workspace)

    skills_dir = workspace / ".claude" / "skills"
    assert not (skills_dir / "not-a-skill").exists()
    assert (skills_dir / "memory-recall").is_symlink()
    assert len(written) == 1


def test_symlink_plugin_skills_companion_files_reachable(
    tmp_path: Path,
) -> None:
    """Skills with companion files (scripts/, references/) — companion
    files are reachable through the directory-symlink. This is why
    we symlink the directory, not the file."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    plugin_skills = plugins / "loam-skills" / "skills"
    plugin_skills.mkdir(parents=True)
    skill = plugin_skills / "rich-skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("---\nname: rich-skill\n---\n")
    scripts = skill / "scripts"
    scripts.mkdir()
    (scripts / "helper.py").write_text("# helper\n")
    refs = skill / "references"
    refs.mkdir()
    (refs / "api.md").write_text("# api ref\n")

    _symlink_plugin_skills(workspace)

    target = workspace / ".claude" / "skills" / "rich-skill"
    # SKILL.md + companion files all reachable through the symlink.
    assert (target / "SKILL.md").is_file()
    assert (target / "scripts" / "helper.py").is_file()
    assert (target / "references" / "api.md").is_file()
