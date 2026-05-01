"""AC.D.1.5.1 — rename-only detection helper unit tests.

Plan: ``docs/rebuild/plans/d-migration-1-5.md`` AC.D.1.5.1.

Fixture shape: a tmp git repo with two component-shaped trees
(``alpha/`` and ``framework/alpha/``) staged across two commits
to simulate a rename window. The helper is invoked directly with
specific old-path + new-path + baseline + head SHAs.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_amend.rename_detection import is_rename_only


def _git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def _make_component(repo: Path, comp_path: str, files: dict[str, str]) -> None:
    base = repo / comp_path
    for rel, content in files.items():
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def test_pure_rename_only_returns_true(scratch_repo: Path) -> None:
    """A window where every component file is an R100 rename + a
    bookkeeping A/D pair (SEAL_COMMIT + test_no_sealed_amendments.py)
    classifies as rename-only."""
    repo = scratch_repo
    # Seed pre-rename state under bare alpha/ path.
    _make_component(
        repo,
        "alpha",
        {
            "src/__init__.py": "# alpha\n",
            "src/code.py": "def foo():\n    return 1\n",
            "tests/SEAL_COMMIT": "0000000000000000000000000000000000000000\n",
            "tests/test_no_sealed_amendments.py": (
                'BASELINE = "0000000"\n\n'
                'def test_x(): pass\n'
            ),
        },
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed alpha")
    baseline = _git(repo, "rev-parse", "HEAD")

    # Now perform the rename: git mv alpha/ framework/alpha/, then
    # rewrite the bookkeeping files (SEAL_COMMIT + seal-test) as
    # apply-step bookkeeping does.
    (repo / "framework").mkdir(exist_ok=True)
    _git(repo, "mv", "alpha", "framework/alpha")
    # Rewrite bookkeeping (apply-step would do the same).
    (repo / "framework" / "alpha" / "tests" / "SEAL_COMMIT").write_text(
        "1111111111111111111111111111111111111111\n", encoding="utf-8"
    )
    (repo / "framework" / "alpha" / "tests" / "test_no_sealed_amendments.py").write_text(
        'BASELINE = "1111111"\n\ndef test_x(): pass\n',
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "rename alpha → framework/alpha")
    head = _git(repo, "rev-parse", "HEAD")

    verdict = is_rename_only(
        repo,
        baseline=baseline,
        head=head,
        old_path="alpha/",
        new_path="framework/alpha/",
    )
    assert verdict is True


def test_modify_returns_false(scratch_repo: Path) -> None:
    """A window with a content edit on a source file (not a rename)
    classifies as substantive."""
    repo = scratch_repo
    _make_component(
        repo,
        "beta",
        {
            "src/code.py": "def foo():\n    return 1\n",
            "tests/SEAL_COMMIT": "0000000000000000000000000000000000000000\n",
            "tests/test_no_sealed_amendments.py": (
                'BASELINE = "0000000"\n\ndef test_x(): pass\n'
            ),
        },
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed beta")
    baseline = _git(repo, "rev-parse", "HEAD")

    # Modify the source file in place — pure M, no rename.
    (repo / "beta" / "src" / "code.py").write_text(
        "def foo():\n    return 2\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "edit beta/src/code.py")
    head = _git(repo, "rev-parse", "HEAD")

    verdict = is_rename_only(
        repo,
        baseline=baseline,
        head=head,
        old_path="beta/",
        new_path="framework/beta/",
    )
    assert verdict is False


def test_partial_rename_returns_false(scratch_repo: Path) -> None:
    """A rename plus a content edit on the moved file (similarity <
    100%) classifies as substantive (R<100 = substantive content edit
    during rename)."""
    repo = scratch_repo
    # Make a substantial source file so we can edit it without falling
    # off the 99% similarity threshold.
    body = "\n".join(f"def fn_{i}():\n    return {i}" for i in range(50))
    _make_component(
        repo,
        "gamma",
        {
            "src/big.py": body + "\n",
            "tests/SEAL_COMMIT": "0000000000000000000000000000000000000000\n",
            "tests/test_no_sealed_amendments.py": (
                'BASELINE = "0000000"\n\ndef test_x(): pass\n'
            ),
        },
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed gamma")
    baseline = _git(repo, "rev-parse", "HEAD")

    # Move + edit big.py with a substantial change so similarity drops
    # below 100% (R<100).
    (repo / "framework").mkdir(exist_ok=True)
    _git(repo, "mv", "gamma", "framework/gamma")
    new_body = "\n".join(
        f"def renamed_{i}():\n    return {i * 10}" for i in range(50)
    )
    (repo / "framework" / "gamma" / "src" / "big.py").write_text(
        new_body + "\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "rename gamma + edit big.py")
    head = _git(repo, "rev-parse", "HEAD")

    verdict = is_rename_only(
        repo,
        baseline=baseline,
        head=head,
        old_path="gamma/",
        new_path="framework/gamma/",
    )
    assert verdict is False


def test_unwhitelisted_AD_returns_false(scratch_repo: Path) -> None:
    """An A/D pair whose leaf is NOT a bookkeeping file (e.g. a real
    new source file) classifies as substantive."""
    repo = scratch_repo
    _make_component(
        repo,
        "delta",
        {
            "src/code.py": "def foo():\n    return 1\n",
            "tests/SEAL_COMMIT": "0000000000000000000000000000000000000000\n",
            "tests/test_no_sealed_amendments.py": (
                'BASELINE = "0000000"\n\ndef test_x(): pass\n'
            ),
        },
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed delta")
    baseline = _git(repo, "rev-parse", "HEAD")

    # Rename + add a brand new test file (not bookkeeping).
    (repo / "framework").mkdir(exist_ok=True)
    _git(repo, "mv", "delta", "framework/delta")
    (repo / "framework" / "delta" / "tests" / "test_new_feature.py").write_text(
        "def test_new(): assert True\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "rename + new test")
    head = _git(repo, "rev-parse", "HEAD")

    verdict = is_rename_only(
        repo,
        baseline=baseline,
        head=head,
        old_path="delta/",
        new_path="framework/delta/",
    )
    assert verdict is False


def test_bookkeeping_AD_pairs_admitted(scratch_repo: Path) -> None:
    """A/D pairs limited to bookkeeping leaf names (SEAL_COMMIT,
    test_no_sealed_amendments.py, test_cross_cutting.py) plus R100
    renames classify as rename-only."""
    repo = scratch_repo
    _make_component(
        repo,
        "epsilon",
        {
            "src/code.py": "def foo():\n    return 1\n",
            "tests/SEAL_COMMIT": "aaa\n",
            "tests/test_cross_cutting.py": (
                'BASELINE = "aaa"\n\ndef test_x(): pass\n'
            ),
        },
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed epsilon")
    baseline = _git(repo, "rev-parse", "HEAD")

    (repo / "framework").mkdir(exist_ok=True)
    _git(repo, "mv", "epsilon", "framework/epsilon")
    # Rewrite only the cross_cutting bookkeeping files. SEAL_COMMIT +
    # test_cross_cutting.py both get their leaves renamed in place
    # (apply-step bookkeeping).
    (repo / "framework" / "epsilon" / "tests" / "SEAL_COMMIT").write_text(
        "bbb\n", encoding="utf-8"
    )
    (repo / "framework" / "epsilon" / "tests" / "test_cross_cutting.py").write_text(
        'BASELINE = "bbb"\n\ndef test_x(): pass\n',
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "rename + bookkeeping advance")
    head = _git(repo, "rev-parse", "HEAD")

    verdict = is_rename_only(
        repo,
        baseline=baseline,
        head=head,
        old_path="epsilon/",
        new_path="framework/epsilon/",
    )
    assert verdict is True


def test_empty_diff_returns_false(scratch_repo: Path) -> None:
    """An empty diff window (no changes inside the component) returns
    False — preserves pre-D.1.5 apply semantics where empty windows
    still get BASELINE + SEAL_COMMIT advanced to ``manifest.baseline``.
    """
    repo = scratch_repo
    _make_component(
        repo,
        "zeta",
        {
            "src/code.py": "def foo():\n    return 1\n",
        },
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed zeta")
    baseline = _git(repo, "rev-parse", "HEAD")
    head = baseline  # No changes in window.

    verdict = is_rename_only(
        repo,
        baseline=baseline,
        head=head,
        old_path="zeta/",
        new_path="framework/zeta/",
    )
    assert verdict is False


def test_pure_add_returns_false(scratch_repo: Path) -> None:
    """A pure-A window (e.g. component duplicated rather than
    renamed) returns False — there's no rename evidence, so the
    rename-only verdict can't apply. HC#4 (false-positive worse
    than false-negative)."""
    repo = scratch_repo
    _make_component(
        repo,
        "eta",
        {
            "src/code.py": "def foo():\n    return 1\n",
        },
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "seed eta")
    baseline = _git(repo, "rev-parse", "HEAD")

    # Duplicate (not move) eta to framework/eta.
    (repo / "framework" / "eta" / "src").mkdir(parents=True)
    (repo / "framework" / "eta" / "src" / "code.py").write_text(
        "def foo():\n    return 1\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "duplicate eta")
    head = _git(repo, "rev-parse", "HEAD")

    verdict = is_rename_only(
        repo,
        baseline=baseline,
        head=head,
        old_path="eta/",
        new_path="framework/eta/",
    )
    assert verdict is False
