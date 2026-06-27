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

"""AC.SBB.3 — artifact-cleanliness.

A generated project carries a correct ``.gitignore`` covering harness
runtime state (``.scratch/``, workspace memory queues, tracker
``.sqlite``) + secrets + ``.env``, AND a pre-commit sweep prevents those
paths from entering the artifact even under ``git add -A``.

The sweep is exercised against a REAL temporary git repository — no git
behaviour is stubbed."""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam.secure_build_baseline.artifact_sweep import (
    is_broad_stage_command,
    offending_paths,
)
from loam.secure_build_baseline.gitignore_template import (
    REQUIRED_FLOOR_ENTRIES,
    missing_floor_entries,
    render_gitignore,
)


def _git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")


# --- the floor .gitignore content (AC.SBB.3 part 1) --------------------


def test_floor_gitignore_covers_runtime_state_and_secrets() -> None:
    text = render_gitignore()
    for required in (".scratch/", ".env", "*.pem"):
        assert required in text
    # SQLite tracker DBs + memory queues covered.
    assert "*.sqlite" in text
    assert any("memory" in e for e in REQUIRED_FLOOR_ENTRIES)


def test_missing_floor_entries_empty_gitignore_lists_all() -> None:
    assert missing_floor_entries("") == list(REQUIRED_FLOOR_ENTRIES)
    assert missing_floor_entries(None) == list(REQUIRED_FLOOR_ENTRIES)


def test_missing_floor_entries_complete_gitignore_lists_none() -> None:
    assert missing_floor_entries(render_gitignore()) == []


# --- the broad-stage detector + sweep (AC.SBB.3 part 2) ----------------


def test_is_broad_stage_command_detects_add_all_and_commit_a() -> None:
    assert is_broad_stage_command("git add -A")
    assert is_broad_stage_command("git add .")
    assert is_broad_stage_command("git add --all")
    assert is_broad_stage_command("git commit -am 'wip'")
    assert is_broad_stage_command("git commit -a")


def test_is_broad_stage_command_ignores_targeted_add() -> None:
    assert not is_broad_stage_command("git add src/app.py")
    assert not is_broad_stage_command("git status")
    assert not is_broad_stage_command("git commit -m 'targeted'")


def test_sweep_flags_unignored_runtime_state(tmp_path: Path) -> None:
    """A repo with .scratch/ + .env present and NO .gitignore: the sweep
    reports them as offending (they would enter the artifact under
    ``git add -A``)."""
    repo = tmp_path / "dirty"
    _init_repo(repo)
    (repo / ".scratch").mkdir()
    (repo / ".scratch" / "tmp.txt").write_text("x", encoding="utf-8")
    (repo / ".env").write_text("TOKEN=abc\n", encoding="utf-8")
    (repo / "app.db.sqlite").write_text("", encoding="utf-8")

    off = offending_paths(repo)
    assert ".scratch" in off
    assert ".env" in off
    assert any(p.endswith(".sqlite") for p in off)


def test_sweep_passes_when_gitignore_covers_runtime_state(tmp_path: Path) -> None:
    """The same runtime-state paths, with the floor .gitignore in place, are
    NOT offending — git ignores them, so they cannot enter the artifact
    even under ``git add -A``."""
    repo = tmp_path / "clean"
    _init_repo(repo)
    (repo / ".gitignore").write_text(render_gitignore(), encoding="utf-8")
    (repo / ".scratch").mkdir()
    (repo / ".scratch" / "tmp.txt").write_text("x", encoding="utf-8")
    (repo / ".env").write_text("TOKEN=abc\n", encoding="utf-8")
    (repo / "app.db.sqlite").write_text("", encoding="utf-8")

    assert offending_paths(repo) == []


def test_sweep_allows_env_example(tmp_path: Path) -> None:
    """A `.env.example` documentation file is NOT offending even unignored."""
    repo = tmp_path / "sample"
    _init_repo(repo)
    (repo / ".env.example").write_text("TOKEN=\n", encoding="utf-8")
    assert offending_paths(repo) == []


def test_git_add_all_after_sweep_clean_does_not_stage_runtime_state(
    tmp_path: Path,
) -> None:
    """End-to-end: with the floor .gitignore in place, a real ``git add -A``
    does NOT stage the runtime-state paths (the property the sweep guards)."""
    repo = tmp_path / "e2e"
    _init_repo(repo)
    (repo / ".gitignore").write_text(render_gitignore(), encoding="utf-8")
    (repo / "src.py").write_text("x = 1\n", encoding="utf-8")
    (repo / ".scratch").mkdir()
    (repo / ".scratch" / "junk").write_text("j", encoding="utf-8")
    (repo / ".env").write_text("S=1\n", encoding="utf-8")

    _git(repo, "add", "-A")
    staged = subprocess.run(
        ["git", "-C", str(repo), "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()
    assert "src.py" in staged
    assert ".gitignore" in staged
    assert not any(s.startswith(".scratch") for s in staged)
    assert ".env" not in staged
