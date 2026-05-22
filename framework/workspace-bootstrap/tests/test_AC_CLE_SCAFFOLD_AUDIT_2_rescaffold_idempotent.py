# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.CLE.SCAFFOLD-AUDIT.2 — the operator rescaffold-skills CLI verb,
run against a pre-existing workspace missing some plugin-shipped
SKILL symlinks, ends with all plugin-shipped SKILLs symlinked AND any
pre-existing operator-customized SKILL directories (non-symlink dirs
at the target path) untouched — the rescaffold raises
``PluginSkillCollisionError`` rather than overwriting (per
AC.LAYERED.3).

Per amendment #144 Scope C: pos3 was scaffolded pre-v0.1.7 + scaffold
is idempotent, so pos3's ``.claude/skills/`` carries only the manual
handsoff-loop symlink it added today, NOT the plugin-shipped SKILLs
canonical loam now ships. The rescaffold verb IS the operator
recovery path; this test exercises the partial-set-completion +
operator-override-preservation semantics.
"""

from __future__ import annotations

import pytest
from pathlib import Path

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    PluginSkillCollisionError,
)
from loam.workspace_bootstrap.workspace_cli import rescaffold_skills


def _author_plugin_with_skills(
    plugins_root: Path, plugin_name: str, skill_names: list[str]
) -> None:
    plugin_dir = plugins_root / plugin_name
    skills_dir = plugin_dir / "skills"
    skills_dir.mkdir(parents=True)
    for name in skill_names:
        skill_dir = skills_dir / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: test {name}\n---\n",
            encoding="utf-8",
        )


def test_AC_CLE_SCAFFOLD_AUDIT_2_rescaffold_completes_partial_symlink_set(
    tmp_path: Path,
) -> None:
    """Rescaffold against a workspace with ONLY a manual handsoff-loop
    symlink (the pos3 state) → all plugin-shipped SKILLs are
    symlinked + the pre-existing correct symlink survives untouched."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _author_plugin_with_skills(
        plugins,
        "loam-skills",
        ["handsoff-loop", "memory-recall", "scope-decompose"],
    )

    # Mimic the pos3 state: ``.claude/skills/handsoff-loop`` was
    # manually symlinked but the other two plugin SKILLs are missing
    # entirely.
    skills_dir = workspace / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    handsoff_source = plugins / "loam-skills" / "skills" / "handsoff-loop"
    (skills_dir / "handsoff-loop").symlink_to(handsoff_source.resolve())

    pre_count = sum(1 for _ in skills_dir.iterdir())
    assert pre_count == 1

    written = rescaffold_skills(workspace)
    # Two new symlinks (memory-recall + scope-decompose); the existing
    # handsoff-loop symlink is left alone.
    assert sorted(written) == sorted(
        [
            "<workspace>/.claude/skills/memory-recall",
            "<workspace>/.claude/skills/scope-decompose",
        ]
    )

    post_targets = sorted(p.name for p in skills_dir.iterdir())
    assert post_targets == ["handsoff-loop", "memory-recall", "scope-decompose"]

    # Pre-existing handsoff-loop symlink survived untouched.
    handsoff = skills_dir / "handsoff-loop"
    assert handsoff.is_symlink()
    assert handsoff.resolve() == handsoff_source.resolve()


def test_AC_CLE_SCAFFOLD_AUDIT_2_rescaffold_idempotent_on_full_set(
    tmp_path: Path,
) -> None:
    """Rescaffold against a workspace where every plugin-shipped
    SKILL is already symlinked → returns empty (no new writes); the
    existing symlinks survive untouched."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _author_plugin_with_skills(
        plugins, "loam-skills", ["handsoff-loop", "memory-recall"]
    )

    # First rescaffold — registers both.
    first_pass = rescaffold_skills(workspace)
    assert len(first_pass) == 2

    # Second rescaffold — idempotent: no new writes.
    second_pass = rescaffold_skills(workspace)
    assert second_pass == ()


def test_AC_CLE_SCAFFOLD_AUDIT_2_rescaffold_collides_on_non_symlink_override(
    tmp_path: Path,
) -> None:
    """Rescaffold against a workspace with a NON-symlink directory at
    a target path → raises PluginSkillCollisionError per AC.LAYERED.3.
    Operator resolves explicitly; the operator-authored content is
    NEVER overwritten."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _author_plugin_with_skills(
        plugins, "loam-skills", ["handsoff-loop"]
    )

    # The operator pre-authored a workspace-local handsoff-loop SKILL
    # directory (not a symlink — a real dir with content). Rescaffold
    # MUST refuse to overwrite.
    skills_dir = workspace / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    operator_local = skills_dir / "handsoff-loop"
    operator_local.mkdir()
    (operator_local / "SKILL.md").write_text(
        "operator-authored content\n", encoding="utf-8"
    )

    with pytest.raises(PluginSkillCollisionError) as exc_info:
        rescaffold_skills(workspace)
    assert "handsoff-loop" in str(exc_info.value)

    # The operator-authored file survived untouched.
    assert operator_local.is_dir() and not operator_local.is_symlink()
    assert (
        operator_local / "SKILL.md"
    ).read_text(encoding="utf-8") == "operator-authored content\n"


def test_AC_CLE_SCAFFOLD_AUDIT_2_rescaffold_cli_verb_dispatches(
    tmp_path: Path,
) -> None:
    """The ``loam workspace rescaffold-skills`` argparse subcommand is
    registered + dispatches to the rescaffold function. Composes the
    CLI plumbing with the underlying primitive."""
    import argparse
    from loam.workspace_bootstrap.workspace_cli import (
        build_workspace_subcommand,
    )

    parser = argparse.ArgumentParser(prog="loam-test")
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_workspace_subcommand(sub)

    # Set up a workspace + plugins.
    workspace = tmp_path / "ws"
    workspace.mkdir()
    plugins = workspace / "plugins"
    plugins.mkdir()
    _author_plugin_with_skills(plugins, "loam-skills", ["handsoff-loop"])

    args = parser.parse_args(
        ["workspace", "rescaffold-skills", str(workspace)]
    )
    assert callable(args.func)
    rc = args.func(args)
    assert rc == 0
    # Verify side-effect — the symlink landed.
    assert (
        workspace / ".claude" / "skills" / "handsoff-loop"
    ).is_symlink()
