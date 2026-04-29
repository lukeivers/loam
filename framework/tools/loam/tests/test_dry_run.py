"""T9 + T10 — dry-run simulates seal-diff and exits clean/dirty correctly."""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from loam_cli.amend.commands.apply import run as apply_run
from loam_cli.amend.manifest import load_manifest


def _build_fake_component_tree(repo: Path, name: str, allowed_prefix: str) -> None:
    """Create a sealed-component-shaped tree under *repo* with a minimal
    seal-diff test whose allowed_prefixes admits *allowed_prefix*."""
    comp_dir = repo / name
    (comp_dir / "tests").mkdir(parents=True)
    (comp_dir / "src").mkdir(parents=True)
    test_py = comp_dir / "tests" / "test_no_sealed_amendments.py"
    test_py.write_text(
        f'''"""Seal-diff test."""

from __future__ import annotations

BASELINE = "0000000"


def test_only_{name}_changed():
    allowed_prefixes = (
        "{allowed_prefix}",
    )
    allowed_files: set[str] = set()
    assert True
''',
        encoding="utf-8",
    )
    # SEAL_COMMIT sidecar
    (comp_dir / "tests" / "SEAL_COMMIT").write_text("0000000\n", encoding="utf-8")
    # One source file so the component tree is non-empty.
    (comp_dir / "src" / "core.py").write_text("# component source\n", encoding="utf-8")


def _commit_all(repo: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(
        ["git", "commit", "-q", "-m", message], cwd=repo, check=True
    )
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def _write_manifest(
    repo: Path,
    baseline: str,
    components: list[str],
    *,
    extras_per_component: dict[str, list[str]] | None = None,
) -> Path:
    extras_per_component = extras_per_component or {}
    # Place manifest inside the repo but admit it via extra_allowed_files
    # on every component — real-world manifests live under
    # docs/rebuild/plans/ which is admitted by universal paths. This
    # fixture approximation keeps dry-run green on the manifest file itself.
    manifest_path = repo / "manifest.yaml"
    manifest = {
        "schema_version": 1,
        "amendment": {"number": 1, "slug": "test", "title": "t"},
        "baseline": baseline,
        "plan": "docs/rebuild/plans/test.md",
        "components": [
            {
                "name": c,
                "seal_test": f"{c}/tests/test_no_sealed_amendments.py",
                "sidecar": f"{c}/tests/SEAL_COMMIT",
                "extra_allowed_prefixes": extras_per_component.get(c, []),
                "extra_allowed_files": ["manifest.yaml"],
            }
            for c in components
        ],
    }
    manifest_path.write_text(yaml.safe_dump(manifest), encoding="utf-8")
    return manifest_path


def test_T9_dry_run_exits_clean_on_admitted_diff(scratch_repo: Path) -> None:
    repo = scratch_repo
    _build_fake_component_tree(repo, "alpha", "alpha/")
    baseline_sha = _commit_all(repo, "alpha v0")
    # Edit alpha/src/core.py — admitted by its own prefix.
    (repo / "alpha" / "src" / "core.py").write_text("# edited\n", encoding="utf-8")
    manifest_path = _write_manifest(repo, baseline_sha, ["alpha"])
    rc = apply_run(manifest_path, dry_run=True)
    assert rc == 0


def test_T10_dry_run_flags_unadmitted_path(scratch_repo: Path) -> None:
    repo = scratch_repo
    _build_fake_component_tree(repo, "alpha", "alpha/")
    _build_fake_component_tree(repo, "beta", "beta/")
    baseline_sha = _commit_all(repo, "alpha+beta v0")
    # Edit alpha/src + beta/src. Manifest lists only alpha, whose
    # allowed_prefixes does NOT admit beta/ — dry-run should flag.
    (repo / "alpha" / "src" / "core.py").write_text("# edit\n", encoding="utf-8")
    (repo / "beta" / "src" / "core.py").write_text("# edit\n", encoding="utf-8")
    manifest_path = _write_manifest(repo, baseline_sha, ["alpha"])
    rc = apply_run(manifest_path, dry_run=True)
    assert rc == 1


def test_T10_dry_run_names_offending_path(
    scratch_repo: Path, capsys
) -> None:
    repo = scratch_repo
    _build_fake_component_tree(repo, "alpha", "alpha/")
    baseline_sha = _commit_all(repo, "alpha v0")
    # Touch an existing file (tracked) outside alpha's admissions.
    # (Untracked files are ignored by the dry-run — they wouldn't land
    # in a `git commit` without explicit `git add`.)
    (repo / "README.md").write_text("edited outside alpha\n", encoding="utf-8")
    manifest_path = _write_manifest(repo, baseline_sha, ["alpha"])
    apply_run(manifest_path, dry_run=True)
    captured = capsys.readouterr()
    assert "README.md" in captured.out
    assert "MISSING_ADMISSION" in captured.out
