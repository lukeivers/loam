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

"""AC.PSTATE.2 — genuinely-in-flight behavior preserved
(plan-state-false-partial-fix).

The seal-reachability verdict (AC.PSTATE.1) must not over-promote:
(a) apply-only evidence stays ``partially-sealed``; (b) a NEW apply
after a prior seal (next cycle mid-flight) re-enters
``partially-sealed``; (c) no evidence stays ``no-build-evidence``;
(d) sealed-archive presence stays ``sealed`` regardless of evidence
order.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from loam_cli.audit.plan_state import (
    BUILD_STATE_PARTIAL,
    BUILD_STATE_PENDING,
    BUILD_STATE_SEALED,
    derive_plan_states,
)
from loam_cli.audit.registry import ProjectStateSpec


def _registry_for(repo: Path) -> dict[str, ProjectStateSpec]:
    return {
        "fixture": ProjectStateSpec(
            name="fixture",
            repo_root=repo,
            derive=lambda root: None,
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


def _state_of(repo: Path, slug: str) -> str:
    derived = derive_plan_states("fixture", registry=_registry_for(repo))
    return {p.slug: p for p in derived}[slug].build_state


def test_AC_PSTATE_2a_apply_only_stays_partial(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path)
    slug = "mid-cycle-plan"
    (repo / "docs" / "plans" / f"{slug}.md").write_text(
        "# mid cycle\n", encoding="utf-8"
    )
    _commit(repo, f"chore(amend): {slug} manifest+apply — comp bump to abc1234")
    assert _state_of(repo, slug) == BUILD_STATE_PARTIAL


def test_AC_PSTATE_2b_new_apply_after_prior_seal_reenters_partial(
    tmp_path: Path,
) -> None:
    """Multi-cycle honesty: cycle 1 sealed, cycle 2's apply landed but
    its seal has not — the plan is mid-flight again, not sealed."""
    repo = _seed_repo(tmp_path)
    slug = "multi-cycle-plan"
    (repo / "docs" / "plans" / f"{slug}.md").write_text(
        "# multi cycle\n", encoding="utf-8"
    )
    _commit(repo, f"chore(amend): {slug} apply — cycle 1")
    _commit(repo, f"chore(seals): {slug} — comp at abc1234")
    assert _state_of(repo, slug) == BUILD_STATE_SEALED
    # Cycle 2 opens: a NEW apply is now the newest evidence.
    _commit(repo, f"chore(amend): {slug} apply — cycle 2")
    assert _state_of(repo, slug) == BUILD_STATE_PARTIAL


def test_AC_PSTATE_2c_no_evidence_stays_pending(tmp_path: Path) -> None:
    repo = _seed_repo(tmp_path)
    (repo / "docs" / "plans" / "untouched-plan.md").write_text(
        "# untouched\n", encoding="utf-8"
    )
    assert _state_of(repo, "untouched-plan") == BUILD_STATE_PENDING


def test_AC_PSTATE_2d_archive_presence_seals_regardless_of_evidence_order(
    tmp_path: Path,
) -> None:
    """The archive arm is untouched: an archived plan is sealed even
    when its newest evidence is an apply (e.g., a doc-only follow-up
    apply after archiving)."""
    repo = _seed_repo(tmp_path)
    slug = "archived-plan"
    sealed_dir = repo / "docs" / "plans" / "sealed"
    sealed_dir.mkdir()
    (sealed_dir / f"{slug}.md").write_text("# archived\n", encoding="utf-8")
    _commit(repo, f"chore(seals): {slug} — comp at abc1234")
    _commit(repo, f"chore(amend): {slug} apply — follow-up")
    assert _state_of(repo, slug) == BUILD_STATE_SEALED
