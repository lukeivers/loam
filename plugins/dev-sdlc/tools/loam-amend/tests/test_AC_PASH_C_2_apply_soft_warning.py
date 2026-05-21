"""AC.PASH.C.2 — `loam amend apply` emits a soft stderr warning on unstaged outside-partition changes.

Per amendment #142 Scope C (closes FIDRAFT 334). `loam amend apply`
(real-apply, not dry-run) emits a soft stderr warning when the
working tree carries tracked-but-unstaged changes that would NOT
land in the apply commit (because apply does NOT `git add -A`); the
warning does NOT block apply.

Verifies:
- (a) return code unchanged vs the clean-tree control case (typically 0),
- (b) captured stderr contains the warning string,
- (c) the apply commit still lands,
- (d) the warning does NOT fire on a clean tree (false-positive
  check per D-PASH.WARN-PRECISION),
- (e) the warning does NOT fire when the unstaged change is INSIDE
  the partition's admitted union (precise-form check).

Plan: docs/plans/amendment-142-plan-author-skill-hygiene-merged.md §4
AC.PASH.C.2; outcome-altitude: false.
"""

from __future__ import annotations

import io
import subprocess
import sys
import textwrap
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import yaml

from loam_amend.commands.apply import run as apply_run


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _seed_component(
    repo: Path, name: str, baseline_value: str = "0000000"
) -> None:
    """Seed a component under framework/<name>/ with seal-test + sidecar."""
    comp = repo / "framework" / name
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
                    "framework/{name}/",
                )
                allowed_files: set[str] = set()
                assert True
            '''
        ).lstrip(),
        encoding="utf-8",
    )


def _author_manifest(
    repo: Path,
    *,
    baseline_sha: str,
    name: str,
    slug: str,
) -> Path:
    manifest_path = repo / f"{slug}.manifest.yaml"
    manifest_doc: dict = {
        "schema_version": 1,
        "amendment": {
            "number": 99,
            "slug": slug,
            "title": f"{slug} test",
        },
        "baseline": baseline_sha,
        "plan": f"docs/plans/{slug}.md",
        "components": [
            {
                "name": name,
                "seal_test": f"framework/{name}/tests/test_no_sealed_amendments.py",
                "sidecar": f"framework/{name}/tests/SEAL_COMMIT",
            }
        ],
    }
    manifest_path.write_text(yaml.safe_dump(manifest_doc), encoding="utf-8")
    return manifest_path


def _run_apply_capturing_stderr(
    manifest_path: Path,
) -> tuple[int, str, str]:
    """Invoke apply_run with stdout + stderr captured. Returns
    (rc, stdout, stderr)."""
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = apply_run(manifest_path, dry_run=False)
    return rc, stdout_buf.getvalue(), stderr_buf.getvalue()


def test_AC_PASH_C_2_warning_fires_on_unstaged_outside_partition(
    scratch_repo: Path,
) -> None:
    """Tracked-but-unstaged change OUTSIDE partition → stderr warning,
    apply still succeeds (non-blocking)."""
    repo = scratch_repo
    _seed_component(repo, "alpha", baseline_value="aaaaaaa")
    # Also seed an unrelated tracked file OUTSIDE the partition.
    (repo / "unrelated").mkdir(parents=True, exist_ok=True)
    (repo / "unrelated" / "stranger.py").write_text(
        "y = 1\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed alpha + unrelated")

    # Edit alpha to give the apply real work.
    (repo / "framework" / "alpha" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit alpha")
    baseline_sha = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_manifest(
        repo, baseline_sha=baseline_sha, name="alpha", slug="pash-c-2"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "manifest commit")

    # NOW: dirty the tree OUTSIDE the partition (tracked-but-unstaged).
    (repo / "unrelated" / "stranger.py").write_text(
        "y = 2\n", encoding="utf-8"
    )
    # Do NOT `git add` — leave the change tracked-but-unstaged.

    pre_apply_head = _git(repo, "rev-parse", "HEAD")
    rc, stdout, stderr = _run_apply_capturing_stderr(manifest_path)

    # (a) Return code unchanged (typically 0).
    assert rc == 0, f"apply rc unexpectedly non-zero: {rc}; stderr={stderr!r}"

    # (b) Warning emitted to stderr.
    assert "warning" in stderr.lower() and "tracked-but-unstaged" in stderr, (
        "expected stderr warning about tracked-but-unstaged changes "
        f"outside partition; got stderr={stderr!r}"
    )
    assert "unrelated/stranger.py" in stderr, (
        "warning should name the offending path; "
        f"got stderr={stderr!r}"
    )

    # (c) Apply commit still lands.
    post_apply_head = _git(repo, "rev-parse", "HEAD")
    assert post_apply_head != pre_apply_head, (
        "apply commit should land even with the warning"
    )


def test_AC_PASH_C_2_no_warning_on_clean_tree(scratch_repo: Path) -> None:
    """No tracked-but-unstaged changes → no warning (false-positive
    check per D-PASH.WARN-PRECISION)."""
    repo = scratch_repo
    _seed_component(repo, "beta", baseline_value="bbbbbbb")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed beta")

    (repo / "framework" / "beta" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit beta")
    baseline_sha = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_manifest(
        repo, baseline_sha=baseline_sha, name="beta", slug="pash-c-2-clean"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "manifest commit")

    rc, stdout, stderr = _run_apply_capturing_stderr(manifest_path)
    assert rc == 0
    assert "tracked-but-unstaged" not in stderr, (
        "false-positive warning on clean tree; "
        f"stderr={stderr!r}"
    )


def test_AC_PASH_C_2_no_warning_on_unstaged_INSIDE_partition(
    scratch_repo: Path,
) -> None:
    """Tracked-but-unstaged change INSIDE the partition's admitted
    union → no warning (precise-form check per
    D-PASH.WARN-PRECISION). Mid-edit cycles where the operator is
    actively editing the component must NOT trigger noise."""
    repo = scratch_repo
    _seed_component(repo, "gamma", baseline_value="ggggggg")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed gamma")

    (repo / "framework" / "gamma" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit gamma")
    baseline_sha = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_manifest(
        repo,
        baseline_sha=baseline_sha,
        name="gamma",
        slug="pash-c-2-inside",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "manifest commit")

    # Now dirty INSIDE the partition — the component's own tree.
    (repo / "framework" / "gamma" / "src" / "code.py").write_text(
        "def foo():\n    return 3\n", encoding="utf-8"
    )
    # Leave tracked-but-unstaged.

    rc, stdout, stderr = _run_apply_capturing_stderr(manifest_path)
    assert rc == 0
    # The change is inside `framework/gamma/` — admitted via the
    # partner-prefix derivation; precise-form warning must NOT fire.
    assert "tracked-but-unstaged" not in stderr, (
        "precise-form false-positive: change INSIDE partition should "
        f"NOT trigger warning; stderr={stderr!r}"
    )


def test_AC_PASH_C_2_no_warning_on_untracked_files(
    scratch_repo: Path,
) -> None:
    """Untracked files do NOT trigger the warning (Scope C cares
    only about tracked-but-unstaged — untracked files require an
    explicit `git add` and the operator is presumed in control)."""
    repo = scratch_repo
    _seed_component(repo, "delta", baseline_value="ddddddd")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed delta")

    (repo / "framework" / "delta" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit delta")
    baseline_sha = _git(repo, "rev-parse", "HEAD")

    manifest_path = _author_manifest(
        repo,
        baseline_sha=baseline_sha,
        name="delta",
        slug="pash-c-2-untracked",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "manifest commit")

    # Untracked file outside the partition.
    (repo / "scratch.txt").write_text("transient\n", encoding="utf-8")

    rc, stdout, stderr = _run_apply_capturing_stderr(manifest_path)
    assert rc == 0
    assert "tracked-but-unstaged" not in stderr, (
        f"untracked file should not trigger warning; stderr={stderr!r}"
    )
