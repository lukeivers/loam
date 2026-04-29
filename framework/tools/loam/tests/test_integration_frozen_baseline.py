"""T16 — integration: ``apply`` honours ``frozen_baseline: true`` by
skipping the module-top BASELINE literal bump while still advancing the
sidecar and widening admissions. Introduced with amendment #23 so the
hands-off-lifecycle frozen-H19 BASELINE is expressible in the manifest.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import yaml

from loam_cli.amend.commands.apply import run as apply_run
from loam_cli.amend.seal_diff import read_entries


def _seed_component(repo: Path, name: str, original_baseline: str) -> None:
    comp_dir = repo / name
    (comp_dir / "tests").mkdir(parents=True)
    (comp_dir / "tests" / "test_no_sealed_amendments.py").write_text(
        f'''"""Seal-diff test."""

BASELINE = "{original_baseline}"


def test_only_{name}_changed():
    allowed_prefixes = (
        "{name}/",
    )
    allowed_files: set[str] = set()
    assert True
''',
        encoding="utf-8",
    )
    (comp_dir / "tests" / "SEAL_COMMIT").write_text(
        f"{original_baseline}\n", encoding="utf-8"
    )


def _commit(repo: Path, message: str) -> str:
    subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=repo, check=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def test_T16_frozen_baseline_preserves_baseline_literal(
    scratch_repo: Path,
) -> None:
    """``apply`` with ``frozen_baseline: true`` must leave the module-top
    BASELINE literal untouched while still advancing the sidecar and
    applying any declared tuple widenings."""
    repo = scratch_repo
    frozen_value = "3780603"
    _seed_component(repo, "frozen-comp", frozen_value)
    _seed_component(repo, "floating-comp", "0000000")
    baseline_sha = _commit(repo, "seed components")

    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "amendment": {
                    "number": 23,
                    "slug": "frozen-test",
                    "title": "frozen baseline test",
                },
                "baseline": baseline_sha,
                "plan": "docs/rebuild/plans/frozen-test.md",
                "components": [
                    {
                        "name": "frozen-comp",
                        "seal_test": "frozen-comp/tests/test_no_sealed_amendments.py",
                        "sidecar": "frozen-comp/tests/SEAL_COMMIT",
                        "frozen_baseline": True,
                    },
                    {
                        "name": "floating-comp",
                        "seal_test": "floating-comp/tests/test_no_sealed_amendments.py",
                        "sidecar": "floating-comp/tests/SEAL_COMMIT",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    rc = apply_run(manifest_path, dry_run=False)
    assert rc == 0

    # Frozen component: BASELINE literal preserved.
    frozen_test = repo / "frozen-comp" / "tests" / "test_no_sealed_amendments.py"
    frozen_text = frozen_test.read_text(encoding="utf-8")
    assert f'BASELINE = "{frozen_value}"' in frozen_text, (
        f"frozen-comp BASELINE should still be {frozen_value}; "
        f"found: {frozen_text}"
    )

    # Frozen component: sidecar STILL advances (fidelity: sidecar always
    # tracks the amendment window's SEAL; the frozen-BASELINE change only
    # affects the literal inside the test).
    frozen_sidecar = (
        repo / "frozen-comp" / "tests" / "SEAL_COMMIT"
    ).read_text(encoding="utf-8").strip()
    assert frozen_sidecar == baseline_sha

    # Frozen component: allowed_prefixes still widens with partner admission
    # (floating-comp/).
    frozen_prefixes = read_entries(frozen_test, "allowed_prefixes")
    assert "floating-comp/" in frozen_prefixes

    # Floating component: BASELINE literal is bumped to manifest baseline
    # (control case — default behaviour unchanged).
    floating_test = (
        repo / "floating-comp" / "tests" / "test_no_sealed_amendments.py"
    )
    floating_text = floating_test.read_text(encoding="utf-8")
    assert (
        f'BASELINE = "{baseline_sha[:7]}"' in floating_text
        or f'BASELINE = "{baseline_sha}"' in floating_text
    )


def test_T16_frozen_baseline_idempotent(scratch_repo: Path) -> None:
    """Running ``apply`` twice against a frozen-baseline manifest produces
    no additional diff — idempotency is preserved for the extended field."""
    repo = scratch_repo
    frozen_value = "3780603"
    _seed_component(repo, "frozen-comp", frozen_value)
    baseline_sha = _commit(repo, "seed")

    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "amendment": {
                    "number": 23,
                    "slug": "frozen-test",
                    "title": "frozen baseline idempotency",
                },
                "baseline": baseline_sha,
                "plan": "docs/rebuild/plans/frozen-test.md",
                "components": [
                    {
                        "name": "frozen-comp",
                        "seal_test": "frozen-comp/tests/test_no_sealed_amendments.py",
                        "sidecar": "frozen-comp/tests/SEAL_COMMIT",
                        "frozen_baseline": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    apply_run(manifest_path, dry_run=False)
    first = (
        repo / "frozen-comp" / "tests" / "test_no_sealed_amendments.py"
    ).read_text(encoding="utf-8")
    first_sidecar = (
        repo / "frozen-comp" / "tests" / "SEAL_COMMIT"
    ).read_text(encoding="utf-8")
    apply_run(manifest_path, dry_run=False)
    second = (
        repo / "frozen-comp" / "tests" / "test_no_sealed_amendments.py"
    ).read_text(encoding="utf-8")
    second_sidecar = (
        repo / "frozen-comp" / "tests" / "SEAL_COMMIT"
    ).read_text(encoding="utf-8")
    assert first == second
    assert first_sidecar == second_sidecar
