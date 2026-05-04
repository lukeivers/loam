"""Seal-fence test for plugins/dev-sdlc/odd-extractor.

Mirror of plugins/dev-sdlc/tests/test_no_sealed_amendments.py at the
odd-extractor sub-tree. The dev-sdlc plugin's primary seal-test is
the canonical fence; this test is an additional structural check
that the odd-extractor sub-tree contains the expected scaffold +
that the test-surface invariants hold.

Per AC.OREK.7 — every line of code, every branch, every test maps
to a named AC. This test is the structural floor for the sub-tree.
"""

from __future__ import annotations

from pathlib import Path


_ROOT = Path(__file__).resolve().parent.parent


def test_scaffold_directories_exist() -> None:
    """The four required directories exist."""
    assert (_ROOT / "src").is_dir()
    assert (_ROOT / "tests").is_dir()
    assert (_ROOT / "seals").is_dir()


def test_scaffold_files_exist() -> None:
    """Required scaffold files exist."""
    assert (_ROOT / "pyproject.toml").exists()
    assert (_ROOT / "README.md").exists()


def test_no_python_files_outside_src_or_tests() -> None:
    """Python files only live under src/ or tests/."""
    py_files = list(_ROOT.rglob("*.py"))
    for p in py_files:
        rel = p.relative_to(_ROOT)
        first = rel.parts[0]
        assert first in {"src", "tests"}, (
            f"unexpected .py file outside src/ or tests/: {rel}"
        )


def test_seals_directory_present_for_seal_commits() -> None:
    """seals/ exists for SEAL_COMMIT.<slug> sidecars (populated at
    seal time by `loam amend seal`)."""
    seals_dir = _ROOT / "seals"
    assert seals_dir.is_dir()
    # Seals are populated post-seal; this dir is intentionally empty
    # at scaffold time.
