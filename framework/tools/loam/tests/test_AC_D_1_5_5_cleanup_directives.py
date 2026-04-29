"""AC.D.1.5.5 — manifest ``cleanup_directives:`` block triggers
retroactive BASELINE/SEAL_COMMIT revert.

Plan: ``docs/rebuild/plans/d-migration-1-5.md`` AC.D.1.5.5.
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import yaml

from loam_cli.amend.commands.apply import run as apply_run
from loam_cli.amend.manifest import (
    CleanupDirective,
    InvalidField,
    load_manifest,
)


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _seed(repo: Path, name: str, baseline_lit: str, seal_value: str) -> None:
    comp = repo / "framework" / name
    (comp / "src").mkdir(parents=True)
    (comp / "tests").mkdir(parents=True)
    (comp / "src" / "code.py").write_text("def foo(): return 1\n", encoding="utf-8")
    (comp / "tests" / "SEAL_COMMIT").write_text(f"{seal_value}\n", encoding="utf-8")
    (comp / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            f'''
            BASELINE = "{baseline_lit}"

            def test_x():
                allowed_prefixes = ("framework/{name}/",)
                allowed_files: set[str] = set()
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )


def test_cleanup_directive_writes_pre_baseline_and_sidecar_back(
    scratch_repo: Path,
) -> None:
    """A manifest with a ``cleanup_directives:`` block reverts the
    named component's BASELINE literal + SEAL_COMMIT sidecar to the
    declared pre-bump values, AFTER the standard component loop."""
    repo = scratch_repo
    # Seed at "advanced" state — BASELINE + sidecar both at "ffffff".
    _seed(repo, "alpha", baseline_lit="fffffff", seal_value="ffffffe")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed alpha (advanced state)")
    head_sha = _git(repo, "rev-parse", "HEAD")

    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "amendment": {
                    "number": 200,
                    "slug": "cleanup-test",
                    "title": "cleanup test",
                },
                "baseline": head_sha,
                "plan": "docs/rebuild/plans/cleanup-test.md",
                "components": [
                    {
                        "name": "alpha",
                        "seal_test": "framework/alpha/tests/test_no_sealed_amendments.py",
                        "sidecar": "framework/alpha/tests/SEAL_COMMIT",
                    },
                ],
                "cleanup_directives": [
                    {
                        "comp_name": "alpha",
                        "pre_baseline": "1234567",
                        "pre_seal_commit": "abcdef0",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0

    alpha_test = (
        repo / "framework" / "alpha" / "tests" / "test_no_sealed_amendments.py"
    ).read_text()
    # BASELINE should be reverted to "1234567" (the cleanup target).
    assert 'BASELINE = "1234567"' in alpha_test, (
        f"BASELINE should be reverted to 1234567: {alpha_test}"
    )
    alpha_sidecar = (
        repo / "framework" / "alpha" / "tests" / "SEAL_COMMIT"
    ).read_text().strip()
    assert alpha_sidecar == "abcdef0"


def test_cleanup_directive_idempotent(scratch_repo: Path) -> None:
    """Re-running apply on the same manifest produces no additional
    changes once the cleanup-target values are in place."""
    repo = scratch_repo
    _seed(repo, "beta", baseline_lit="fffffff", seal_value="ffffffe")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed beta")
    head_sha = _git(repo, "rev-parse", "HEAD")

    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "amendment": {
                    "number": 201,
                    "slug": "cleanup-idempotent",
                    "title": "idempotent cleanup",
                },
                "baseline": head_sha,
                "plan": "docs/rebuild/plans/cleanup-idempotent.md",
                "components": [
                    {
                        "name": "beta",
                        "seal_test": "framework/beta/tests/test_no_sealed_amendments.py",
                        "sidecar": "framework/beta/tests/SEAL_COMMIT",
                    },
                ],
                "cleanup_directives": [
                    {
                        "comp_name": "beta",
                        "pre_baseline": "9876543",
                        "pre_seal_commit": "fedcba0",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    rc1 = apply_run(manifest_path, dry_run=False)
    assert rc1 == 0
    text1 = (
        repo / "framework" / "beta" / "tests" / "test_no_sealed_amendments.py"
    ).read_text()
    side1 = (repo / "framework" / "beta" / "tests" / "SEAL_COMMIT").read_text()

    rc2 = apply_run(manifest_path, dry_run=False)
    assert rc2 == 0
    text2 = (
        repo / "framework" / "beta" / "tests" / "test_no_sealed_amendments.py"
    ).read_text()
    side2 = (repo / "framework" / "beta" / "tests" / "SEAL_COMMIT").read_text()

    assert text1 == text2
    assert side1 == side2


def test_manifest_parses_cleanup_directives(tmp_path: Path) -> None:
    """The manifest loader parses ``cleanup_directives:`` blocks
    into ``CleanupDirective`` records with SHA validation."""
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "amendment": {
                    "number": 62,
                    "slug": "test-cleanup-parse",
                    "title": "test cleanup parse",
                },
                "baseline": "1111111",
                "plan": "docs/rebuild/plans/test.md",
                "components": [
                    {
                        "name": "alpha",
                        "seal_test": "framework/alpha/tests/test_no_sealed_amendments.py",
                        "sidecar": "framework/alpha/tests/SEAL_COMMIT",
                    },
                ],
                "cleanup_directives": [
                    {
                        "comp_name": "alpha",
                        "pre_baseline": "abc1234",
                        "pre_seal_commit": "def5678",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    parsed = load_manifest(manifest)
    assert len(parsed.cleanup_directives) == 1
    d = parsed.cleanup_directives[0]
    assert isinstance(d, CleanupDirective)
    assert d.comp_name == "alpha"
    assert d.pre_baseline == "abc1234"
    assert d.pre_seal_commit == "def5678"


def test_manifest_rejects_invalid_cleanup_directive_sha(tmp_path: Path) -> None:
    """A ``cleanup_directives`` entry with a non-SHA value rejects."""
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "amendment": {
                    "number": 62,
                    "slug": "test",
                    "title": "test",
                },
                "baseline": "1111111",
                "plan": "docs/rebuild/plans/test.md",
                "components": [
                    {
                        "name": "alpha",
                        "seal_test": "framework/alpha/tests/test_no_sealed_amendments.py",
                        "sidecar": "framework/alpha/tests/SEAL_COMMIT",
                    },
                ],
                "cleanup_directives": [
                    {
                        "comp_name": "alpha",
                        "pre_baseline": "not-a-sha-with-bad-chars",
                        "pre_seal_commit": "def5678",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    try:
        load_manifest(manifest)
        assert False, "expected InvalidField"
    except InvalidField:
        pass


def test_manifest_without_cleanup_directives_defaults_empty(
    tmp_path: Path,
) -> None:
    """v1 manifests without ``cleanup_directives:`` parse with the
    default empty tuple — backwards-compat."""
    manifest = tmp_path / "manifest.yaml"
    manifest.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "amendment": {
                    "number": 1,
                    "slug": "t",
                    "title": "t",
                },
                "baseline": "1111111",
                "plan": "docs/rebuild/plans/t.md",
                "components": [
                    {
                        "name": "alpha",
                        "seal_test": "framework/alpha/tests/test_no_sealed_amendments.py",
                        "sidecar": "framework/alpha/tests/SEAL_COMMIT",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    parsed = load_manifest(manifest)
    assert parsed.cleanup_directives == ()
