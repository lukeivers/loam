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

"""AC.BLOCK-ENFORCE.* — the framework ↔ user-state boundary holds,
structurally (gate 9, the twin of gate-7 `check_migration_declared`).

The gate `check_boundary_respected` reads the DECLARED ALLOWLIST
(`docs/design/adr/user-state-homes.yaml`) — the single source of truth
shared with the boundary ADR (AC.BLOCK-ENFORCE.4) — and goes RED when
framework code writes user-state to a path OUTSIDE the two legal homes.

Test families:
  - AC.BLOCK-ENFORCE.1 — the gate is a member of ALL_GATES + run_all
    invokes it (composes in the release-gate spine).
  - AC.BLOCK-ENFORCE.2 — a clean tree (framework writes user-state only
    to the two homes) is GREEN (no false-positive on legitimate writes).
  - ★ AC.BLOCK-ENFORCE.3 (outcome-altitude: true) — a PLANTED real
    violation is CAUGHT at the real `loam release` gate entry-point
    (`run_all`), no pre-arranged in-memory state. A STUB unit test of an
    inner classifier does NOT satisfy this AC.
  - AC.BLOCK-ENFORCE.4 — the gate reads the SAME allowlist the ADR
    describes; changing the allowlist changes both (one rule, no drift).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_cli.release import gates

# The canonical loam repo root (4 parents up: tests/ → tools/loam →
# tools → framework → loam(repo)).
REPO_ROOT = Path(__file__).resolve().parents[4]

ALLOWLIST_REL = "docs/design/adr/user-state-homes.yaml"


# --------------------------------------------------------------------
# Fixtures — a minimal repo carrying the allowlist + a framework tree.
# --------------------------------------------------------------------


def _write_allowlist(repo: Path) -> None:
    """Copy the REAL canonical allowlist into the fixture repo so the
    gate reads the same declaration the ADR describes."""
    src = REPO_ROOT / ALLOWLIST_REL
    dst = repo / ALLOWLIST_REL
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def _git_init(repo: Path) -> None:
    """Minimal git init so the run_all pass (which invokes git-backed
    gates like check_clean_tree / check_branch_main) does not crash —
    those gates are not the subject of these tests, only the boundary
    verdict in the same pass is."""
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(
        ["git", "config", "user.email", "boundary-test@example.invalid"],
        cwd=repo,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "boundary test"], cwd=repo, check=True
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=repo, check=True
    )


@pytest.fixture
def clean_repo(tmp_path: Path) -> Path:
    """A fixture repo with the allowlist + a framework module that writes
    user-state ONLY to a legal home (the legitimate shape)."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    _write_allowlist(repo)
    # A framework module whose output is user-state landing in a LEGAL
    # home — exactly establish_loam_layout's shape (framework code writing
    # user-state under <workspace>/.loam/). Must NOT trip the gate.
    mod = repo / "framework" / "workspace-bootstrap" / "src" / "legit.py"
    mod.parent.mkdir(parents=True, exist_ok=True)
    mod.write_text(
        "from pathlib import Path\n\n"
        "def establish(workspace_root):\n"
        "    loam = Path(workspace_root) / '.loam'\n"
        "    (loam / 'migrations' / '.cursor').write_text('', encoding='utf-8')\n",
        encoding="utf-8",
    )
    return repo


@pytest.fixture
def planted_violation_repo(clean_repo: Path) -> Path:
    """The clean repo PLUS a planted real boundary violation: a framework
    module that writes a per-user file (user-state) to a path OUTSIDE the
    two homes — under framework/ itself. The literal leak shape the gate
    exists to catch."""
    bad = clean_repo / "framework" / "leaky-component" / "src" / "leak.py"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_text(
        "from pathlib import Path\n\n"
        "def persist_user_profile(repo_root):\n"
        "    # BOUNDARY VIOLATION: framework code writing user-state\n"
        "    # (OBJECTIVES.md) to a path OUTSIDE ~/.claude/ and <ws>/.loam/.\n"
        "    target = Path(repo_root) / 'framework' / 'leaky-component' / 'OBJECTIVES.md'\n"
        "    target.write_text('user objectives here', encoding='utf-8')\n",
        encoding="utf-8",
    )
    return clean_repo


# --------------------------------------------------------------------
# AC.BLOCK-ENFORCE.1 — composes in the release-gate spine.
# --------------------------------------------------------------------


def test_AC_BLOCK_ENFORCE_1_gate_in_all_gates_and_run_all() -> None:
    """The boundary gate is a member of ALL_GATES and run_all invokes it
    (the gate-7 shape — one report, no parallel CI)."""
    assert gates.check_boundary_respected in gates.ALL_GATES
    # gate 9: gate-7 migration + gate-8 substrate-audit precede it.
    assert len(gates.ALL_GATES) == 11
    # run_all returns a verdict for the boundary gate.
    results = gates.run_all(REPO_ROOT, "v0.0.0")
    names = [r.name for r in results]
    assert "boundary-respected" in names
    assert len(results) == 11


# --------------------------------------------------------------------
# AC.BLOCK-ENFORCE.2 — clean tree GREEN, no false-positive.
# --------------------------------------------------------------------


def test_AC_BLOCK_ENFORCE_2_clean_tree_is_green(clean_repo: Path) -> None:
    """Framework code writing user-state ONLY to a legal home does NOT
    trip the gate."""
    res = gates.check_boundary_respected(clean_repo, "v0.0.0")
    assert res.ok is True, res.message
    assert res.name == "boundary-respected"


def test_AC_BLOCK_ENFORCE_2b_real_canonical_tree_is_green() -> None:
    """The REAL current canonical tree is GREEN — the legitimate
    framework→user-state writes (establish_loam_layout, gates.py,
    cost-governance) do NOT trip the gate. Halt-trigger 3 guard: if this
    goes RED, a PRE-EXISTING real leak exists and must be surfaced, not
    hidden."""
    res = gates.check_boundary_respected(REPO_ROOT, "v0.0.0")
    assert res.ok is True, (
        "PRE-EXISTING boundary leak in the real tree — surface it "
        f"(do NOT widen the allowlist to hide it): {res.message}"
    )


# --------------------------------------------------------------------
# ★ AC.BLOCK-ENFORCE.3 (outcome-altitude: true) — planted violation
#   CAUGHT at the real run_all entry-point, no pre-arranged state.
# --------------------------------------------------------------------


def test_AC_BLOCK_ENFORCE_3_planted_violation_caught_at_run_all(
    planted_violation_repo: Path,
) -> None:
    """outcome-altitude: drive the REAL release-gate entry-point
    (`run_all`) against a tree carrying a planted real violation. The
    boundary gate's verdict in that pass must be RED, with a corrective
    hint naming the offending path AND the legal homes.

    No pre-arranged in-memory state: run_all derives everything from the
    tree on disk. A STUB unit test of an inner classifier does NOT
    satisfy this AC — this invokes the production gate flow."""
    results = gates.run_all(planted_violation_repo, "v0.0.0")
    by_name = {r.name: r for r in results}
    assert "boundary-respected" in by_name
    verdict = by_name["boundary-respected"]

    # CAUGHT: the boundary gate goes RED in the real run_all pass.
    assert verdict.ok is False, (
        "the real run_all pass must catch the planted boundary "
        f"violation; got GREEN: {verdict.message}"
    )
    # The hint names the offending path.
    assert "OBJECTIVES.md" in verdict.message
    assert "leaky-component" in verdict.message
    # The hint names the legal homes so the operator can correct.
    assert ".loam" in verdict.message
    assert ".claude" in verdict.message


def test_AC_BLOCK_ENFORCE_3b_complement_clean_at_run_all(
    clean_repo: Path,
) -> None:
    """The complement at the real entry-point: a clean tree's boundary
    verdict in run_all is GREEN — proving the catch is real detection,
    not a blanket reject."""
    results = gates.run_all(clean_repo, "v0.0.0")
    by_name = {r.name: r for r in results}
    assert by_name["boundary-respected"].ok is True, by_name[
        "boundary-respected"
    ].message


# --------------------------------------------------------------------
# AC.BLOCK-ENFORCE.4 — gate reads the SAME allowlist the ADR describes.
# --------------------------------------------------------------------


def test_AC_BLOCK_ENFORCE_4_gate_reads_declared_allowlist(
    planted_violation_repo: Path,
) -> None:
    """The legal-home set the gate enforces is sourced from the declared
    allowlist (one source, no drift). Mutating the allowlist to ADD the
    leak's location as a legal home flips the verdict GREEN — proving the
    gate reads the file, not a hardcoded parallel rule."""
    # Baseline: planted violation is RED.
    red = gates.check_boundary_respected(planted_violation_repo, "v0.0.0")
    assert red.ok is False

    # Mutate ONLY the declared allowlist to admit the leak's home.
    allowlist = planted_violation_repo / ALLOWLIST_REL
    body = allowlist.read_text(encoding="utf-8")
    body += (
        "\n  - id: test-extra\n"
        "    path: \"framework/leaky-component/\"\n"
        "    scope: workspace-scoped\n"
        "    description: test-only extra home (AC.BLOCK-ENFORCE.4 proof)\n"
    )
    allowlist.write_text(body, encoding="utf-8")

    # Same tree, mutated allowlist → GREEN. The gate read the file.
    green = gates.check_boundary_respected(planted_violation_repo, "v0.0.0")
    assert green.ok is True, (
        "changing the declared allowlist must change the gate's verdict — "
        f"the gate must read the file, not a hardcoded rule: {green.message}"
    )


def test_AC_BLOCK_ENFORCE_4b_allowlist_is_the_real_canonical_file() -> None:
    """The allowlist the ADR cites and the gate reads is one real tracked
    file at the canonical path."""
    allowlist = REPO_ROOT / ALLOWLIST_REL
    assert allowlist.is_file()
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ALLOWLIST_REL],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    # tracked once committed; before commit this is informational only.
    body = allowlist.read_text(encoding="utf-8")
    assert ".claude" in body and ".loam" in body
