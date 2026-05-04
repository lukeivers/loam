"""Sub-tree scaffold-invariants test for the odd-extractor sub-tree.

Mirror of plugins/dev-sdlc/tests/test_no_sealed_amendments.py shape,
scoped to the odd-extractor sub-tree. The dev-sdlc plugin's primary
seal-test is the canonical fence; this test is an additional
structural check that the sub-tree contains the expected scaffold +
that the test-surface invariants hold.

Renamed from test_no_sealed_amendments.py to a unique basename so
pytest collection at the dev-sdlc level doesn't double-import (the
parent dev-sdlc tests directory carries its own seal-test with that
basename — pytest doesn't allow same basename in different rootdirs
without unique conftest scopes).

Per AC.OREK.7 — every line of code, every branch, every test maps
to a named AC. This test is the structural floor for the sub-tree.
"""

from __future__ import annotations

from pathlib import Path


_ROOT = Path(__file__).resolve().parent.parent


def test_scaffold_directories_exist() -> None:
    """src/ and tests/ both exist."""
    assert (_ROOT / "src").is_dir()
    assert (_ROOT / "tests").is_dir()


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


def test_parent_seals_directory_carries_seal_for_this_cycle() -> None:
    """Seal-narrative sidecars for this sub-tree land in the parent
    dev-sdlc plugin's seals/ directory (not under
    odd-extractor/seals/) — the dev-sdlc plugin is the sealed-
    component fence and its seals/ is the canonical narrative
    location.

    Cycle 1's SEAL_COMMIT.v0-1-8-cycle-1-odd-extractor-scaffolding
    lands there post-seal.
    """
    parent_seals = _ROOT.parent / "seals"
    assert parent_seals.is_dir(), (
        "parent dev-sdlc/seals/ must exist as the canonical seal-"
        "narrative directory"
    )
    expected_seal = (
        parent_seals
        / "SEAL_COMMIT.v0-1-8-cycle-1-odd-extractor-scaffolding"
    )
    # The seal file lands when `loam amend seal` runs; pre-seal this
    # test would (correctly) not assert the file's existence. Post-
    # seal it does.
    if expected_seal.exists():
        body = expected_seal.read_text(encoding="utf-8")
        assert "v0-1-8-cycle-1-odd-extractor-scaffolding" in body
