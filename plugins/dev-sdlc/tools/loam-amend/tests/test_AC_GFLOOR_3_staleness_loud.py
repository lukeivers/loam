"""AC.GFLOOR.3 — floor staleness is loud, never silent.

Per ``docs/plans/seal-guard-sweep-floor.md`` §4:

- In a registry-carrying repo: a registry pattern resolving to zero
  tracked files halts the seal with a diagnostic naming the stale
  pattern; an empty fence-discovery result also halts. (A
  present-but-malformed registry is the same degradation class and
  halts too — the floor must never silently shrink.)
- In a registry-LESS repo (synthetic fixtures, derived workspaces
  using the published plugin): empty discovery proceeds with a
  printed note — no false halt.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from loam_amend.cli import main as cli_main

from test_seal import (
    _git,
    _make_amendment_commit,
    _write_manifest,
    sealed_repo,  # noqa: F401 — pytest fixture
)
from test_AC_GFLOOR_2_registry_targets_run import _write_registry


def test_AC_GFLOOR_3_zero_match_pattern_halts_naming_it(
    sealed_repo, capsys
) -> None:
    """A registry pattern matching no tracked file halts the seal,
    names the stale pattern, and leaves no seal commit."""
    repo = sealed_repo
    _write_registry(repo, ["guards/test_AC_MOVED_ELSEWHERE_*.py"])

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=933,
        slug="gfloor-3-stale",
        seal_description="gfloor-3 stale",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="gfloor3a")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc != 0
    out = capsys.readouterr().out
    assert "HALT: guard-floor-stale" in out
    assert "guards/test_AC_MOVED_ELSEWHERE_*.py" in out
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head == amendment_sha


def _registryless_fenceless_repo(tmp_path: Path) -> Path:
    """A young workspace: one component whose seal-test file is NOT
    fence-named (so fence discovery is legitimately empty), no
    registry."""
    repo = tmp_path / "workspace"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "loam amend test")
    (repo / ".gitignore").write_text(
        "__pycache__/\n*.pyc\n", encoding="utf-8"
    )
    (repo / "CLAUDE.md").write_text("# fixture\n", encoding="utf-8")
    comp = repo / "framework" / "alpha"
    (comp / "tests").mkdir(parents=True)
    (comp / "src").mkdir()
    (comp / "src" / "__init__.py").write_text("\n", encoding="utf-8")
    (comp / "tests" / "SEAL_COMMIT").write_text(
        "0000000000000000000000000000000000000000\n", encoding="utf-8"
    )
    # Seal-test file carrying the dry-run admission tuples but NOT
    # named test_no_sealed_amendments.py / test_cross_cutting.py.
    (comp / "tests" / "test_admissions.py").write_text(
        textwrap.dedent(
            """
            allowed_prefixes = (
                "framework/alpha/",
                "docs/plans/",
            )
            allowed_files = (
                "CLAUDE.md",
            )


            def test_admissions_ok():
                assert True
            """
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: fenceless young repo")
    return repo


def _write_fenceless_manifest(repo: Path, number: int, slug: str) -> Path:
    plans_dir = repo / "docs" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = plans_dir / f"amendment-{number}-{slug}.manifest.yaml"
    baseline = _git(repo, "rev-parse", "HEAD").stdout.strip()
    manifest_path.write_text(
        textwrap.dedent(
            f"""
            schema_version: 1
            amendment:
              number: {number}
              slug: {slug}
              title: "fixture amendment {number}"
            baseline: {baseline}
            plan: docs/plans/amendment-{number}-{slug}.md
            components:
              - name: alpha
                seal_test: framework/alpha/tests/test_admissions.py
                sidecar: framework/alpha/tests/SEAL_COMMIT
            """
        ).lstrip(),
        encoding="utf-8",
    )
    rel = manifest_path.relative_to(repo)
    _git(repo, "add", "--", str(rel))
    _git(repo, "commit", "-q", "-m", f"fixture: amendment-{number} manifest")
    return manifest_path


def test_AC_GFLOOR_3_registryless_empty_floor_proceeds_with_note(
    tmp_path: Path, capsys
) -> None:
    """A registry-less repo with zero fence tests seals green with a
    printed empty-floor note — never a false halt."""
    repo = _registryless_fenceless_repo(tmp_path)
    manifest_path = _write_fenceless_manifest(repo, 934, "gfloor-3-young")
    _make_amendment_commit(repo, "alpha", payload="gfloor3b")

    rc = cli_main(["seal", str(manifest_path)])
    out = capsys.readouterr().out
    assert "guard floor: no floor members discovered" in out
    assert rc == 0
    body = _git(repo, "log", "--format=%B").stdout
    assert "chore(seals):" in body


def test_AC_GFLOOR_3_registry_carrying_repo_with_no_fence_tests_halts(
    tmp_path: Path, capsys
) -> None:
    """The same fenceless repo WITH a registry is floor-enforcing:
    empty fence discovery halts loudly."""
    repo = _registryless_fenceless_repo(tmp_path)
    # Registry whose pattern resolves (the admissions test) — the
    # halt must come from the EMPTY FENCE DISCOVERY leg.
    _write_registry(repo, ["framework/alpha/tests/test_admissions.py"])
    manifest_path = _write_fenceless_manifest(repo, 935, "gfloor-3-enforced")
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="gfloor3c")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc != 0
    out = capsys.readouterr().out
    assert "HALT: guard-floor-stale" in out
    assert "fence-test discovery returned ZERO" in out
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head == amendment_sha


def test_AC_GFLOOR_3_malformed_registry_halts(sealed_repo, capsys) -> None:
    """A present-but-malformed registry halts (same never-silently-
    shrink class as staleness)."""
    repo = sealed_repo
    reg = repo / "docs" / "plans" / "guard-floor.yaml"
    reg.parent.mkdir(parents=True, exist_ok=True)
    reg.write_text("schema_version: 99\npatterns: []\n", encoding="utf-8")
    _git(repo, "add", "--", "docs/plans/guard-floor.yaml")
    _git(repo, "commit", "-q", "-m", "fixture: malformed registry")

    manifest_path = _write_manifest(
        repo,
        components=["alpha"],
        number=936,
        slug="gfloor-3-malformed",
        seal_description="gfloor-3 malformed",
    )
    amendment_sha = _make_amendment_commit(repo, "alpha", payload="gfloor3d")

    rc = cli_main(["seal", str(manifest_path)])
    assert rc != 0
    out = capsys.readouterr().out
    assert "HALT: guard-floor-registry-invalid" in out
    head = _git(repo, "rev-parse", "HEAD").stdout.strip()
    assert head == amendment_sha
