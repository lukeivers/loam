# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKILLS-BUG.2 — workspace-bootstrap pre-creates
``<workspace>/.claude/skills/.gitkeep`` at first-run.

Per ``docs/rebuild/plans/v0-1-6-production-safety-and-base-skills.md``
§5 AC.SKILLS-BUG.2: the first-run scaffold pre-creates the directory
+ a zero-byte ``.gitkeep`` so Claude Code's live-change-detection
picks up new SKILL.md files added later WITHOUT requiring a session
restart. Per Anthropic's documented live-change semantics: a NEW
top-level skills directory needs session restart, but new files
inside an EXISTING directory are picked up live. Pre-creating at
scaffold time guarantees the directory exists from session-zero.

Idempotent: an existing ``.gitkeep`` (even with non-zero bytes from
operator edits) is left untouched.
"""

from __future__ import annotations

from pathlib import Path

from loam.workspace_bootstrap.adapters.first_run_scaffold import (
    _write_skills_gitkeep,
    run_first_run_scaffold,
)


def test_skills_gitkeep_pre_created_on_fresh_scaffold(tmp_path: Path) -> None:
    """A fresh scaffold creates the directory + zero-byte .gitkeep."""
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    pos_root = tmp_path / "loam"

    run_first_run_scaffold(
        pos_root=pos_root,
        workspace_root=workspace_root,
        platform_override="macos",
        service_bootstrap=False,
        service_manager_dir_override=tmp_path / "LaunchAgents",
    )

    skills_dir = workspace_root / ".claude" / "skills"
    gitkeep = skills_dir / ".gitkeep"
    assert skills_dir.is_dir(), "skills/ dir was not created"
    assert gitkeep.is_file(), ".gitkeep sentinel was not authored"
    assert gitkeep.stat().st_size == 0, ".gitkeep should be zero bytes"


def test_skills_gitkeep_idempotent(tmp_path: Path) -> None:
    """Running _write_skills_gitkeep against an already-created
    .gitkeep does NOT overwrite — operator edits survive."""
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    skills_dir = workspace_root / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    gitkeep = skills_dir / ".gitkeep"
    gitkeep.write_text("# operator edit\n")

    wrote = _write_skills_gitkeep(workspace_root)
    assert wrote is False, "should be a no-op on existing .gitkeep"
    assert gitkeep.read_text() == "# operator edit\n", (
        "operator edits should survive idempotent re-runs"
    )


def test_skills_gitkeep_returns_true_on_first_write(tmp_path: Path) -> None:
    """First write returns True (signaling the path was authored)."""
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    wrote = _write_skills_gitkeep(workspace_root)
    assert wrote is True
    assert (workspace_root / ".claude" / "skills" / ".gitkeep").is_file()
