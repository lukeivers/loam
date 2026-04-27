"""AC.D.1.5.2 — ``pos-amend apply`` skips BASELINE + SEAL_COMMIT bump
on rename-only components; widening still applies.

Plan: ``docs/rebuild/plans/d-migration-1-5.md`` AC.D.1.5.2.
"""

from __future__ import annotations

import subprocess
import textwrap
from pathlib import Path

import yaml

from pos_amend.commands.apply import run as apply_run


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _seed_component_at_old_path(
    repo: Path, name: str, baseline_value: str = "0000000"
) -> None:
    """Seed a component under bare ``<name>/`` path."""
    comp = repo / name
    (comp / "src").mkdir(parents=True)
    (comp / "tests").mkdir(parents=True)
    (comp / "src" / "code.py").write_text(
        "def foo():\n    return 1\n", encoding="utf-8"
    )
    (comp / "tests" / "SEAL_COMMIT").write_text(
        f"{baseline_value}\n", encoding="utf-8"
    )
    (comp / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            f'''
            BASELINE = "{baseline_value}"

            def test_x():
                allowed_prefixes = (
                    "{name}/",
                )
                allowed_files: set[str] = set()
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )


def _rename_component(repo: Path, name: str, new_seal_value: str) -> None:
    """Apply-step bookkeeping: git mv <name>/ framework/<name>/, then
    rewrite SEAL_COMMIT + test_no_sealed_amendments.py."""
    (repo / "framework").mkdir(exist_ok=True)
    _git(repo, "mv", name, f"framework/{name}")
    (repo / "framework" / name / "tests" / "SEAL_COMMIT").write_text(
        f"{new_seal_value}\n", encoding="utf-8"
    )
    (repo / "framework" / name / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            f'''
            BASELINE = "{new_seal_value}"

            def test_x():
                allowed_prefixes = (
                    "framework/{name}/",
                )
                allowed_files: set[str] = set()
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )


def test_rename_only_skips_baseline_and_sidecar_bump(
    scratch_repo: Path,
) -> None:
    """Rename-only component: BASELINE literal + SEAL_COMMIT sidecar
    NOT advanced to manifest.baseline. Widening still runs."""
    repo = scratch_repo
    _seed_component_at_old_path(repo, "alpha", baseline_value="aaaaaaa")
    _seed_component_at_old_path(repo, "beta", baseline_value="bbbbbbb")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed components")
    pre_amend_sha = _git(repo, "rev-parse", "HEAD")

    # Rename both components — pure R100 + bookkeeping A/D pairs.
    _rename_component(repo, "alpha", new_seal_value="aaaaaaa")
    _rename_component(repo, "beta", new_seal_value="bbbbbbb")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "rename alpha + beta")
    amendment_sha = _git(repo, "rev-parse", "HEAD")

    # Manifest pinned to pre_amend_sha (the commit before the rename
    # commit). Diff window: pre_amend_sha..HEAD covers the rename.
    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "amendment": {
                    "number": 99,
                    "slug": "rename-only",
                    "title": "rename-only test",
                },
                "baseline": pre_amend_sha,
                "plan": "docs/rebuild/plans/rename-only.md",
                "components": [
                    {
                        "name": "alpha",
                        "seal_test": "framework/alpha/tests/test_no_sealed_amendments.py",
                        "sidecar": "framework/alpha/tests/SEAL_COMMIT",
                    },
                    {
                        "name": "beta",
                        "seal_test": "framework/beta/tests/test_no_sealed_amendments.py",
                        "sidecar": "framework/beta/tests/SEAL_COMMIT",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0

    # BASELINE literal in alpha's seal-test should still be at "aaaaaaa".
    alpha_test = (
        repo / "framework" / "alpha" / "tests" / "test_no_sealed_amendments.py"
    ).read_text(encoding="utf-8")
    assert 'BASELINE = "aaaaaaa"' in alpha_test, (
        f"alpha BASELINE should be preserved at aaaaaaa: {alpha_test}"
    )

    # SEAL_COMMIT sidecar should still be at "aaaaaaa".
    alpha_sidecar = (
        repo / "framework" / "alpha" / "tests" / "SEAL_COMMIT"
    ).read_text().strip()
    assert alpha_sidecar == "aaaaaaa"

    # Same for beta.
    beta_test = (
        repo / "framework" / "beta" / "tests" / "test_no_sealed_amendments.py"
    ).read_text(encoding="utf-8")
    assert 'BASELINE = "bbbbbbb"' in beta_test
    beta_sidecar = (
        repo / "framework" / "beta" / "tests" / "SEAL_COMMIT"
    ).read_text().strip()
    assert beta_sidecar == "bbbbbbb"

    # Widening: alpha's allowed_prefixes should now include the
    # cross-component partner admission (framework/beta/ + beta/).
    assert "framework/beta/" in alpha_test


def test_substantive_advances_baseline_and_sidecar(
    scratch_repo: Path,
) -> None:
    """Control case: a component with a substantive content edit
    (not a rename) gets BASELINE + SEAL_COMMIT advanced normally."""
    repo = scratch_repo
    # Seed under post-D.1 framework/<name>/ layout (no rename in window).
    comp = repo / "framework" / "delta"
    (comp / "src").mkdir(parents=True)
    (comp / "tests").mkdir(parents=True)
    (comp / "src" / "code.py").write_text(
        "def foo():\n    return 1\n", encoding="utf-8"
    )
    (comp / "tests" / "SEAL_COMMIT").write_text("0000000\n", encoding="utf-8")
    (comp / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            '''
            BASELINE = "0000000"

            def test_x():
                allowed_prefixes = (
                    "framework/delta/",
                )
                allowed_files: set[str] = set()
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed delta")
    baseline_sha = _git(repo, "rev-parse", "HEAD")

    # Edit code.py — substantive, not a rename.
    (comp / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit delta/src/code.py")

    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "amendment": {
                    "number": 100,
                    "slug": "substantive",
                    "title": "substantive test",
                },
                "baseline": baseline_sha,
                "plan": "docs/rebuild/plans/substantive.md",
                "components": [
                    {
                        "name": "delta",
                        "seal_test": "framework/delta/tests/test_no_sealed_amendments.py",
                        "sidecar": "framework/delta/tests/SEAL_COMMIT",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0

    delta_test = (comp / "tests" / "test_no_sealed_amendments.py").read_text()
    # BASELINE should advance to baseline_sha (substantive case).
    assert f'BASELINE = "{baseline_sha}"' in delta_test, (
        f"substantive amendment should bump BASELINE: {delta_test}"
    )

    delta_sidecar = (comp / "tests" / "SEAL_COMMIT").read_text().strip()
    assert delta_sidecar == baseline_sha
