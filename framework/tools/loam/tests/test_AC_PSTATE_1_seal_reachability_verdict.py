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

"""AC.PSTATE.1 — the seal-reachability sealed verdict
(plan-state-false-partial-fix, D-PSTATE.1).

A plan-doc living in ``docs/plans/`` (NOT in the sealed archive) whose
newest slug-named evidence commit in the HEAD-reachable subject history
is a completed ``chore(seals): <slug>`` commit derives ``sealed``,
purely from the git ref graph, with its evidence carried — never
``partially-sealed`` (the 2026-06-11 false-dispatch-premise defect).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam_cli.audit.plan_state import (
    BUILD_STATE_PARTIAL,
    BUILD_STATE_SEALED,
    derive_plan_states,
)
from loam_cli.audit.registry import ProjectStateSpec


def _registry_for(repo: Path) -> dict[str, ProjectStateSpec]:
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


def test_AC_PSTATE_1_newest_seal_evidence_derives_sealed_without_archive(
    tmp_path: Path,
) -> None:
    """The headline outcome: apply + seal commits in HEAD history, doc
    NEVER archived → ``sealed`` (was: ``partially-sealed`` forever)."""
    repo = _seed_repo(tmp_path)
    reg = _registry_for(repo)
    slug = "legacy-narrative-cycle"
    (repo / "docs" / "plans" / f"{slug}.md").write_text(
        "# Legacy narrative cycle\n\nbody\n", encoding="utf-8"
    )
    _commit(repo, f"chore(amend): {slug} manifest+apply — comp bump to abc1234")

    # Mid-cycle checkpoint: apply landed, no seal yet → partial.
    derived = derive_plan_states("fixture", registry=reg)
    by_slug = {p.slug: p for p in derived}
    assert by_slug[slug].build_state == BUILD_STATE_PARTIAL

    # The seal commit lands (legacy narrative target — NOTHING written
    # to docs/plans/sealed/). The verdict flips purely via the ref graph.
    _commit(repo, f"chore(seals): {slug} — comp at abc1234")
    derived = derive_plan_states("fixture", registry=reg)
    by_slug = {p.slug: p for p in derived}
    assert by_slug[slug].build_state == BUILD_STATE_SEALED
    assert not by_slug[slug].in_sealed_archive
    assert len(by_slug[slug].seal_evidence) == 2
    # Evidence is newest-first; the seal commit leads.
    assert "chore(seals): " in by_slug[slug].seal_evidence[0]


def test_AC_PSTATE_1_seal_subject_boundary_never_claims_sibling(
    tmp_path: Path,
) -> None:
    """``…-1b``'s seal never promotes ``…-1`` (the slug-exact boundary
    match carries through to the sealed verdict)."""
    repo = _seed_repo(tmp_path)
    reg = _registry_for(repo)
    plans = repo / "docs" / "plans"
    (plans / "verdict-1.md").write_text("# one\n", encoding="utf-8")
    (plans / "verdict-1b.md").write_text("# one-b\n", encoding="utf-8")
    _commit(repo, "chore(seals): verdict-1b — comp at abc1234")
    derived = derive_plan_states("fixture", registry=reg)
    by_slug = {p.slug: p for p in derived}
    assert by_slug["verdict-1b"].build_state == BUILD_STATE_SEALED
    assert by_slug["verdict-1"].build_state == "no-build-evidence"
