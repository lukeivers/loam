"""AC.D.1.5.3 — ``pos-amend apply --dry-run`` surfaces per-component
rename-only verdict in the preview output.

Plan: ``docs/rebuild/plans/d-migration-1-5.md`` AC.D.1.5.3.
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


def _seed_at_old(repo: Path, name: str, baseline: str) -> None:
    comp = repo / name
    (comp / "src").mkdir(parents=True)
    (comp / "tests").mkdir(parents=True)
    (comp / "src" / "code.py").write_text("def foo(): return 1\n", encoding="utf-8")
    (comp / "tests" / "SEAL_COMMIT").write_text(f"{baseline}\n", encoding="utf-8")
    (comp / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            f'''
            BASELINE = "{baseline}"

            def test_x():
                allowed_prefixes = ("{name}/",)
                allowed_files: set[str] = set()
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )


def _rename_to_new(repo: Path, name: str, new_seal: str) -> None:
    (repo / "framework").mkdir(exist_ok=True)
    _git(repo, "mv", name, f"framework/{name}")
    (repo / "framework" / name / "tests" / "SEAL_COMMIT").write_text(
        f"{new_seal}\n", encoding="utf-8"
    )
    (repo / "framework" / name / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            f'''
            BASELINE = "{new_seal}"

            def test_x():
                allowed_prefixes = ("framework/{name}/",)
                allowed_files: set[str] = set()
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )


def test_dry_run_reports_rename_only_true_and_false(
    scratch_repo: Path, capsys
) -> None:
    """The --dry-run preview surfaces ``rename-only: True`` for a
    rename-only component and ``rename-only: False`` for a
    substantive component."""
    repo = scratch_repo

    # alpha = rename-only.
    _seed_at_old(repo, "alpha", "aaaaaaa")
    # delta = substantive (lives at post-rename layout, code edit).
    delta = repo / "framework" / "delta"
    (delta / "src").mkdir(parents=True)
    (delta / "tests").mkdir(parents=True)
    (delta / "src" / "code.py").write_text("def foo(): return 1\n", encoding="utf-8")
    (delta / "tests" / "SEAL_COMMIT").write_text("ddddddd\n", encoding="utf-8")
    (delta / "tests" / "test_no_sealed_amendments.py").write_text(
        textwrap.dedent(
            '''
            BASELINE = "ddddddd"

            def test_x():
                allowed_prefixes = ("framework/delta/",)
                allowed_files: set[str] = set()
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed both components")
    baseline_sha = _git(repo, "rev-parse", "HEAD")

    # Rename alpha (rename-only window) and edit delta source
    # (substantive window).
    _rename_to_new(repo, "alpha", "aaaaaaa")
    (delta / "src" / "code.py").write_text("def foo(): return 2\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "rename alpha + edit delta")

    manifest_path = repo / "manifest.yaml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "amendment": {
                    "number": 101,
                    "slug": "preview-test",
                    "title": "preview test",
                },
                "baseline": baseline_sha,
                "plan": "docs/rebuild/plans/preview-test.md",
                "components": [
                    {
                        "name": "alpha",
                        "seal_test": "framework/alpha/tests/test_no_sealed_amendments.py",
                        "sidecar": "framework/alpha/tests/SEAL_COMMIT",
                    },
                    {
                        "name": "delta",
                        "seal_test": "framework/delta/tests/test_no_sealed_amendments.py",
                        "sidecar": "framework/delta/tests/SEAL_COMMIT",
                    },
                ],
                "universal_paths": {
                    "prefixes": [],
                    "files": [],
                },
            }
        ),
        encoding="utf-8",
    )

    apply_run(manifest_path, dry_run=True)
    captured = capsys.readouterr()
    out = captured.out

    # Block layout: each component appears under [<name>] with a
    # `rename-only:` line beneath it.
    assert "[alpha]" in out
    assert "[delta]" in out

    # Find each block's rename-only line.
    blocks = out.split("[")
    alpha_block = next((b for b in blocks if b.startswith("alpha]")), "")
    delta_block = next((b for b in blocks if b.startswith("delta]")), "")
    assert "rename-only: True" in alpha_block, (
        f"alpha should be rename-only; preview was:\n{alpha_block}"
    )
    assert "rename-only: False" in delta_block, (
        f"delta should NOT be rename-only; preview was:\n{delta_block}"
    )
