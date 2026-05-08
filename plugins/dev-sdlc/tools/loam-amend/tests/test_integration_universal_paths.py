"""T13 — integration: apply the universal-paths retrofit against a
fixture tree and assert every component's admissions widened."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from loam_amend.commands.apply import run as apply_run
from loam_amend.seal_diff import read_entries


_COMPONENTS = ("alpha", "beta", "gamma")
_UNIVERSAL_PREFIXES = ("docs/plans/",)
_UNIVERSAL_FILES = (
    "CLAUDE.md",
    "docs/odd-in-loam.md",
    "docs/odd-methodology.md",
    "docs/FUTURE_IDEAS.md",
)


def _build_tree(repo: Path) -> str:
    for comp in _COMPONENTS:
        comp_dir = repo / comp
        (comp_dir / "tests").mkdir(parents=True)
        (comp_dir / "tests" / "test_no_sealed_amendments.py").write_text(
            f'''"""Seal-diff test."""

BASELINE = "0000000"


def test_only_{comp}_changed():
    allowed_prefixes = (
        "{comp}/",
        "data/",
    )
    allowed_files: set[str] = set()
    assert True
''',
            encoding="utf-8",
        )
        (comp_dir / "tests" / "SEAL_COMMIT").write_text("0000000\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", "components v0"], cwd=repo, check=True
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _write_retrofit_manifest(repo: Path, baseline: str) -> Path:
    manifest_path = repo / "manifest.yaml"
    data = {
        "schema_version": 1,
        "amendment": {
            "number": 22,
            "slug": "universal-paths-retrofit",
            "title": "universal paths retrofit",
        },
        "baseline": baseline,
        "plan": "docs/plans/retrofit.md",
        "components": [
            {
                "name": c,
                "seal_test": f"{c}/tests/test_no_sealed_amendments.py",
                "sidecar": f"{c}/tests/SEAL_COMMIT",
            }
            for c in _COMPONENTS
        ],
        "universal_paths": {
            "prefixes": list(_UNIVERSAL_PREFIXES),
            "files": list(_UNIVERSAL_FILES),
        },
    }
    manifest_path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return manifest_path


def test_T13_universal_paths_retrofit_widens_all_components(
    scratch_repo: Path,
) -> None:
    repo = scratch_repo
    baseline_sha = _build_tree(repo)
    manifest_path = _write_retrofit_manifest(repo, baseline_sha)
    # Run apply (real, not dry-run).
    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0
    # Every component's allowed_prefixes now contains the universal
    # prefix, and allowed_files the universal files.
    for comp in _COMPONENTS:
        test_path = repo / comp / "tests" / "test_no_sealed_amendments.py"
        prefixes = read_entries(test_path, "allowed_prefixes")
        files = read_entries(test_path, "allowed_files")
        for up in _UNIVERSAL_PREFIXES:
            assert up in prefixes, (
                f"{comp}: universal prefix {up!r} not admitted. "
                f"Actual: {prefixes!r}"
            )
        for uf in _UNIVERSAL_FILES:
            assert uf in files, (
                f"{comp}: universal file {uf!r} not admitted. "
                f"Actual: {files!r}"
            )
        # BASELINE was bumped to manifest baseline.
        text = test_path.read_text(encoding="utf-8")
        assert f'BASELINE = "{baseline_sha[:7]}"' in text or f'BASELINE = "{baseline_sha}"' in text
        # Sidecar was written to manifest baseline (empty-diff window).
        sidecar = (repo / comp / "tests" / "SEAL_COMMIT").read_text(
            encoding="utf-8"
        ).strip()
        assert sidecar == baseline_sha


def test_T13_retrofit_is_idempotent(scratch_repo: Path) -> None:
    repo = scratch_repo
    baseline_sha = _build_tree(repo)
    manifest_path = _write_retrofit_manifest(repo, baseline_sha)
    apply_run(manifest_path, dry_run=False)
    # Snapshot tree state.
    first_state = {}
    for comp in _COMPONENTS:
        p = repo / comp / "tests" / "test_no_sealed_amendments.py"
        first_state[comp] = p.read_text(encoding="utf-8")
    apply_run(manifest_path, dry_run=False)
    for comp in _COMPONENTS:
        p = repo / comp / "tests" / "test_no_sealed_amendments.py"
        assert p.read_text(encoding="utf-8") == first_state[comp]
