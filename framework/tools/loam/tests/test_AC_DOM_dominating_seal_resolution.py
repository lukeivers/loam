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

"""AC.DOM.* — right tag target via ancestor-dominance (audit Class D).

The release tool resolves a version's tag target as the seal that
DOMINATES every other seal named in that version's roadmap §2 row,
replacing the fragile last-in-row text-parse.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_cli.release import gates

# The canonical repo root (five parents up from this test file), used by
# the real-row regression (AC.DOM.4 second leg).
CANONICAL_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "dom-test@example.invalid"],
        cwd=path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "dom test"], cwd=path, check=True
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=path, check=True
    )


def _commit(path: Path, fname: str, content: str, msg: str) -> str:
    (path / fname).write_text(content, encoding="utf-8")
    subprocess.run(["git", "add", fname], cwd=path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", msg], cwd=path, check=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _row(version: str, *seals: str) -> str:
    seal_cells = "; ".join(f"seal `{s}`" for s in seals)
    return (
        "# Release Roadmap\n\n## §2 Shipped\n\n"
        "| Version | Objective | Anchor |\n|---|---|---|\n"
        f"| {version} | objective | Multi-cycle: {seal_cells} |\n"
    )


def _linear_chain(repo: Path) -> tuple[str, str, str]:
    """c1 -> c2 -> c3 on main; returns the three SHAs in order."""
    _init_repo(repo)
    c1 = _commit(repo, "f.txt", "1", "feat: c1")
    c2 = _commit(repo, "f.txt", "2", "feat: c2")
    c3 = _commit(repo, "f.txt", "3", "feat: c3")
    return c1, c2, c3


def test_AC_DOM_1_resolves_dominating_seal(tmp_path: Path) -> None:
    """AC.DOM.1 — among a row's seals, the tag target is the one that has
    every other row-seal as an ancestor."""
    repo = tmp_path / "repo"
    repo.mkdir()
    c1, c2, c3 = _linear_chain(repo)
    body = _row("v1.0.0", c1, c2, c3)
    res = gates.resolve_tag_target(repo, body, "v1.0.0")
    assert res.reason == "dominates"
    assert res.sha == c3


def test_AC_DOM_2_no_dominator_halts(tmp_path: Path) -> None:
    """AC.DOM.2 — a row whose seals span divergent history (no single
    dominator) resolves to a halt (no tag target) and the gate REDs."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    base = _commit(repo, "f.txt", "base", "feat: base")
    # Two divergent branches off base; neither dominates the other.
    a = _commit(repo, "a.txt", "a", "feat: branch-a")
    subprocess.run(["git", "checkout", "-q", base], cwd=repo, check=True)
    subprocess.run(
        ["git", "checkout", "-q", "-b", "divergent"], cwd=repo, check=True
    )
    b = _commit(repo, "b.txt", "b", "feat: branch-b")
    body = _row("v1.0.0", a, b)
    res = gates.resolve_tag_target(repo, body, "v1.0.0")
    assert res.reason == "no-dominator"
    assert res.sha is None

    (repo / "docs").mkdir()
    (repo / "docs" / "release-roadmap.md").write_text(body, encoding="utf-8")
    gate = gates.check_seal_dominance(repo, "v1.0.0")
    assert gate.ok is False
    assert "NONE dominates" in gate.message


def test_AC_DOM_3_single_seal_backward_compatible(tmp_path: Path) -> None:
    """AC.DOM.3 — a single-seal row resolves to that seal (vacuous
    dominance) with no git object lookup (the norm today)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    # No git init at all — a single-seal row must resolve without touching
    # the object store.
    body = _row("v1.0.0", "abc1234")
    res = gates.resolve_tag_target(repo, body, "v1.0.0")
    assert res.reason == "single"
    assert res.sha == "abc1234"


def test_AC_DOM_4_outcome_altitude_non_dominating_first_sha(
    tmp_path: Path,
) -> None:
    """AC.DOM.4 (outcome-altitude) — given a row where a NON-dominating
    SHA appears FIRST (the last-in-row / first-line fragility shape), the
    resolver returns the dominating seal, never the early first SHA."""
    repo = tmp_path / "repo"
    repo.mkdir()
    c1, c2, c3 = _linear_chain(repo)
    # Row order [c1, c3, c2]: c1 is first and NON-dominating; the OLD
    # seals[-1] would have returned c2 (also non-dominating). Dominance
    # returns c3 regardless of order.
    body = _row("v1.0.0", c1, c3, c2)
    res = gates.resolve_tag_target(repo, body, "v1.0.0")
    assert res.sha == c3
    assert res.sha != c1  # never the early first SHA
    assert res.sha != c2  # never the last-in-row parse result


@pytest.mark.parametrize("version", ["v1.10.0", "v1.11.0"])
def test_AC_DOM_4_real_row_matches_published_tag(version: str) -> None:
    """AC.DOM.4 (outcome-altitude, real-row leg) — on the canonical tree,
    the resolver's tag target equals ``git rev-list -1 <tag>`` for each
    real published version. Skips when the tag/roadmap is absent (isolated
    checkout / CI)."""
    roadmap = CANONICAL_ROOT / "docs" / "release-roadmap.md"
    if not roadmap.is_file():
        pytest.skip("canonical roadmap not present")
    tag_proc = subprocess.run(
        ["git", "rev-list", "-1", version],
        cwd=CANONICAL_ROOT,
        capture_output=True,
        text=True,
    )
    if tag_proc.returncode != 0 or not tag_proc.stdout.strip():
        pytest.skip(f"tag {version} not present on this checkout")
    tag_commit = tag_proc.stdout.strip()
    body = roadmap.read_text(encoding="utf-8")
    res = gates.resolve_tag_target(CANONICAL_ROOT, body, version)
    assert res.sha is not None
    # The resolver returns an abbreviated SHA from the row; confirm the
    # published tag commit resolves to it (prefix match via rev-parse).
    resolved_full = subprocess.run(
        ["git", "rev-parse", res.sha],
        cwd=CANONICAL_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert resolved_full == tag_commit


def test_AC_DOM_5_dominance_enforced_in_run_all(
    staged_repo: Path, fixture_version: str
) -> None:
    """AC.DOM.5 — the dominance check rides the mandatory run_all pass: a
    no-dominator row makes run_all's seal-dominance verdict RED."""
    # Rewrite the fixture's version row to name two divergent seals.
    _init_repo_noop = None  # staged_repo already a git repo
    base = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=staged_repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    a = _commit(staged_repo, "a.txt", "a", "feat: a")
    subprocess.run(["git", "checkout", "-q", base], cwd=staged_repo, check=True)
    subprocess.run(
        ["git", "checkout", "-q", "-b", "divergent"],
        cwd=staged_repo,
        check=True,
    )
    b = _commit(staged_repo, "b.txt", "b", "feat: b")
    subprocess.run(["git", "checkout", "-q", "main"], cwd=staged_repo, check=True)
    roadmap = staged_repo / "docs" / "release-roadmap.md"
    body = roadmap.read_text(encoding="utf-8")
    lines = []
    for line in body.splitlines(keepends=True):
        if line.startswith(f"| {fixture_version} "):
            line = (
                f"| {fixture_version} | next outcome shape | "
                f"Multi-cycle: seal `{a}`; seal `{b}` |\n"
            )
        lines.append(line)
    roadmap.write_text("".join(lines), encoding="utf-8")
    subprocess.run(["git", "add", "docs/"], cwd=staged_repo, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "divergent seals"],
        cwd=staged_repo,
        check=True,
    )
    results = gates.run_all(staged_repo, fixture_version)
    by_name = {r.name: r for r in results}
    assert "seal-dominance" in by_name
    assert by_name["seal-dominance"].ok is False


def test_AC_DOM_6_single_resolver_invariant() -> None:
    """AC.DOM.6 — no tag-target site selects via the last-in-row parse: the
    fragile ``_extract_seal_sha`` is gone and no release-package source
    carries the literal last-in-row index."""
    # The fragile function no longer exists.
    assert not hasattr(gates, "_extract_seal_sha")
    # The dominating resolver is the single source.
    assert callable(gates.resolve_tag_target)
    release_dir = (
        CANONICAL_ROOT
        / "framework"
        / "tools"
        / "loam"
        / "src"
        / "loam_cli"
        / "release"
    )
    if not release_dir.is_dir():
        pytest.skip("release package source not present")
    offenders = []
    for py in release_dir.glob("*.py"):
        if "seals[-1]" in py.read_text(encoding="utf-8"):
            offenders.append(py.name)
    assert offenders == [], (
        f"release-package source still carries the last-in-row parse: "
        f"{offenders}"
    )
