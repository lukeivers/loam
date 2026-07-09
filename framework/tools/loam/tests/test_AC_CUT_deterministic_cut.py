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

"""AC.CUT.* — deterministic, machine-enforced release cut (audit Class A).

A gate in run_all recomputes class + number from repo state per
docs/release-versioning-policy.md and REDs when the content class != the
version being cut. MAJOR stays owner-gated.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam_cli.release import cut, gates


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "cut-test@example.invalid"],
        cwd=path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "cut test"], cwd=path, check=True
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=path, check=True
    )


def _commit(path: Path, fname: str, content: str, msg: str) -> None:
    (path / fname).write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", fname], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=path, check=True)


# --------------------------------------------------------------------
# AC.CUT.1 — recompute class + number from repo state
# --------------------------------------------------------------------


def test_AC_CUT_1_feat_computes_minor() -> None:
    r = cut.compute_cut(
        Path("."),
        published_override="v1.11.0",
        commit_messages_override=["feat(x): add a capability", "fix: y"],
    )
    assert r.klass == "MINOR"
    assert r.expected_version == "v1.12.0"


def test_AC_CUT_1_fixes_only_compute_patch() -> None:
    r = cut.compute_cut(
        Path("."),
        published_override="v1.11.0",
        commit_messages_override=["fix: a", "docs: b", "chore: c"],
    )
    assert r.klass == "PATCH"
    assert r.expected_version == "v1.11.1"


# --------------------------------------------------------------------
# AC.CUT.2 / AC.CUT.3 — RED on mismatch, GREEN on match
# --------------------------------------------------------------------


def test_AC_CUT_3_green_when_target_matches_computed() -> None:
    r = gates.check_deterministic_cut(
        Path("."),
        "v1.12.0",
        origin_published="v1.11.0",
        commit_messages_override=["feat: capability"],
    )
    assert r.ok is True
    assert "confirmed" in r.message


def test_AC_CUT_2_red_when_target_mismatches_with_hint() -> None:
    r = gates.check_deterministic_cut(
        Path("."),
        "v1.11.1",  # PATCH target
        origin_published="v1.11.0",
        commit_messages_override=["feat: capability"],  # MINOR content
    )
    assert r.ok is False
    # Hint names BOTH computed + target.
    assert "v1.12.0" in r.message
    assert "v1.11.1" in r.message


# --------------------------------------------------------------------
# AC.CUT.4 (outcome-altitude) — through run_all, both directions
# --------------------------------------------------------------------


def _scaffold_cut_repo(
    tmp_path: Path, published: str, unreleased_commits: list[tuple[str, str]]
) -> Path:
    """A repo tagged *published* on a base commit, then *unreleased_commits*
    (fname, message) on top. No origin remote (origin read returns None;
    the gate falls back to the local tag)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _commit(repo, "base.txt", "base", "chore: base")
    subprocess.run(["git", "tag", published], cwd=repo, check=True)
    for fname, msg in unreleased_commits:
        _commit(repo, fname, msg, msg)
    return repo


def test_AC_CUT_4_outcome_altitude_minor_content_patch_target(
    tmp_path: Path,
) -> None:
    """A cut whose content warrants MINOR (a feat) but whose target is a
    PATCH bump REDs through run_all."""
    repo = _scaffold_cut_repo(
        tmp_path, "v1.11.0", [("cap.txt", "feat: new capability")]
    )
    results = gates.run_all(repo, "v1.11.1")  # PATCH target
    by_name = {r.name: r for r in results}
    assert by_name["deterministic-cut"].ok is False
    assert "v1.12.0" in by_name["deterministic-cut"].message


def test_AC_CUT_4_outcome_altitude_patch_content_minor_target(
    tmp_path: Path,
) -> None:
    """The inverse: only fixes but a MINOR target REDs through run_all."""
    repo = _scaffold_cut_repo(
        tmp_path, "v1.11.0", [("fix.txt", "fix: a defect")]
    )
    results = gates.run_all(repo, "v1.12.0")  # MINOR target
    by_name = {r.name: r for r in results}
    assert by_name["deterministic-cut"].ok is False
    assert "v1.11.1" in by_name["deterministic-cut"].message


# --------------------------------------------------------------------
# AC.CUT.5 — local/origin disagreement HARD HALT + indeterminate degrade
# --------------------------------------------------------------------


def test_AC_CUT_5_local_origin_disagreement_hard_halt() -> None:
    r = gates.check_deterministic_cut(
        Path("."),
        "v1.12.0",
        local_published="v1.12.0",   # locally sealed, unpushed
        origin_published="v1.11.0",
        commit_messages_override=["feat: x"],
    )
    assert r.ok is False
    assert "disagreement" in r.message


def test_AC_CUT_5_indeterminate_degrades_green(tmp_path: Path) -> None:
    """No published tag anywhere -> pass-with-caveat, never a false RED."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _commit(repo, "f.txt", "x", "feat: x")
    r = gates.check_deterministic_cut(repo, "v1.0.0")
    assert r.ok is True
    assert "fail-safe" in r.message or "caveat" in r.message


# --------------------------------------------------------------------
# AC.CUT.6 — MAJOR is owner-gated (never auto-RED); breaking surfaces note
# --------------------------------------------------------------------


def test_AC_CUT_6_major_target_owner_gated_not_red() -> None:
    r = gates.check_deterministic_cut(
        Path("."),
        "v2.0.0",  # MAJOR bump of v1.11.0
        origin_published="v1.11.0",
        commit_messages_override=["feat!: a breaking capability"],
    )
    assert r.ok is True
    assert "owner-gated" in r.message


def test_AC_CUT_6_breaking_marker_surfaces_note_on_minor() -> None:
    r = gates.check_deterministic_cut(
        Path("."),
        "v1.12.0",  # MINOR absorbs the breaking change per policy
        origin_published="v1.11.0",
        commit_messages_override=["feat!: breaking but rides a minor"],
    )
    assert r.ok is True
    assert "breaking" in r.message.lower()
