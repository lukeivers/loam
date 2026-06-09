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

"""AC.PSI.1 — derived-not-stored plan-state.

For each registered project with a plans dir, the production
derivation produces, FRESH from disk + the git ref graph, the set of
plan-docs with per-plan identity and build-state — never from a plan's
own prose status line. Sealing a slice in the real repo and
re-deriving changes the reported state with NO doc edit.

Method is the builder's call (ODD §1.1); these tests exercise the
outcome against a fixture git repo registered through the same
``ProjectStateSpec`` registry seam the production registry uses.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam_cli.audit.plan_state import (
    BUILD_STATE_PARTIAL,
    BUILD_STATE_PENDING,
    BUILD_STATE_SEALED,
    derive_all_plan_states,
    derive_plan_states,
)
from loam_cli.audit.registry import ProjectStateSpec


def _registry_for(repo: Path) -> dict[str, ProjectStateSpec]:
    """A one-project registry pointing at the fixture repo (the same
    spec shape the production ``PROJECT_REGISTRY`` carries)."""
    return {
        "fixture": ProjectStateSpec(
            name="fixture",
            repo_root=repo,
            derive=lambda root: None,  # plan-state never calls derive
        )
    }


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   capture_output=True)


def _commit(repo: Path, subject: str) -> None:
    _git(repo, "commit", "--allow-empty", "-q", "-m", subject)


def _seed_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "docs" / "plans").mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")
    _commit(repo, "seed")
    return repo


def test_AC_PSI_1_state_flips_on_seal_with_no_doc_edit(tmp_path: Path) -> None:
    """The headline outcome: a plan moves no-build-evidence →
    partially-sealed → sealed purely through repo events (an apply
    commit; the sealed-archive narrative) with the plan-doc bytes
    untouched."""
    repo = _seed_repo(tmp_path)
    reg = _registry_for(repo)
    slug = "fbm-fixture-cycle"
    doc = repo / "docs" / "plans" / f"{slug}.md"
    doc.write_text("# Fixture cycle plan\n\nbody\n", encoding="utf-8")
    original_bytes = doc.read_bytes()

    derived = derive_plan_states("fixture", registry=reg)
    assert derived is not None
    by_slug = {p.slug: p for p in derived}
    assert by_slug[slug].build_state == BUILD_STATE_PENDING
    assert by_slug[slug].title == "Fixture cycle plan"
    assert by_slug[slug].seal_evidence == ()

    # An apply commit lands (the loam-amend subject shape) — NO doc edit.
    _commit(repo, f"chore(amend): {slug} manifest+apply — comp bump to abc1234")
    derived = derive_plan_states("fixture", registry=reg)
    by_slug = {p.slug: p for p in derived}
    assert by_slug[slug].build_state == BUILD_STATE_PARTIAL
    assert len(by_slug[slug].seal_evidence) == 1
    assert slug in by_slug[slug].seal_evidence[0]

    # The seal narrative lands in the sealed archive — still no doc edit.
    sealed_dir = repo / "docs" / "plans" / "sealed"
    sealed_dir.mkdir()
    (sealed_dir / f"{slug}.md").write_text(
        "# Fixture cycle plan\n\nnarrative\n", encoding="utf-8"
    )
    _commit(repo, f"chore(seals): {slug} — comp at abc1234")
    derived = derive_plan_states("fixture", registry=reg)
    by_slug = {p.slug: p for p in derived}
    assert by_slug[slug].build_state == BUILD_STATE_SEALED
    assert by_slug[slug].in_sealed_archive
    assert len(by_slug[slug].seal_evidence) == 2

    # The active plan-doc was never edited across all three states.
    assert doc.read_bytes() == original_bytes


def test_AC_PSI_1_prose_status_line_is_ignored(tmp_path: Path) -> None:
    """A plan whose own prose claims SEALED but with zero git evidence
    reports no-build-evidence — state comes from the ref graph, never
    the status line (the exact 06-09 drift surface)."""
    repo = _seed_repo(tmp_path)
    reg = _registry_for(repo)
    doc = repo / "docs" / "plans" / "prose-liar.md"
    doc.write_text(
        "# Prose liar plan\n\n**Status:** SEALED, shipped, all done.\n",
        encoding="utf-8",
    )
    derived = derive_plan_states("fixture", registry=reg)
    by_slug = {p.slug: p for p in derived}
    assert by_slug["prose-liar"].build_state == BUILD_STATE_PENDING


def test_AC_PSI_1_slug_prefix_never_claims_sibling_evidence(
    tmp_path: Path,
) -> None:
    """``…-1`` must not absorb ``…-1b``'s apply/seal evidence (the
    subject match is slug-exact, boundary-checked)."""
    repo = _seed_repo(tmp_path)
    reg = _registry_for(repo)
    plans = repo / "docs" / "plans"
    (plans / "check-1.md").write_text("# one\n", encoding="utf-8")
    (plans / "check-1b.md").write_text("# one-b\n", encoding="utf-8")
    _commit(repo, "chore(amend): check-1b manifest+apply — bump")
    derived = derive_plan_states("fixture", registry=reg)
    by_slug = {p.slug: p for p in derived}
    assert by_slug["check-1b"].build_state == BUILD_STATE_PARTIAL
    assert by_slug["check-1"].build_state == BUILD_STATE_PENDING


def test_AC_PSI_1_unregistered_none_and_no_plans_dir_empty(
    tmp_path: Path,
) -> None:
    """The registry contract mirrors ``derive_project_state``: an
    unregistered name is a clean ``None``; a registered project with
    no plans dir derives empty (D6 fail-soft)."""
    repo = tmp_path / "noplans"
    repo.mkdir()
    reg = {
        "bare": ProjectStateSpec(
            name="bare", repo_root=repo, derive=lambda root: None
        )
    }
    assert derive_plan_states("unknown", registry=reg) is None
    assert derive_plan_states("bare", registry=reg) == ()
    # derive_all skips nothing silently-wrong: the bare project is
    # present with an empty tuple.
    assert derive_all_plan_states(registry=reg) == {"bare": ()}
