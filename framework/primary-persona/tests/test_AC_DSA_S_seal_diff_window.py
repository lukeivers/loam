"""AC.DSA.S — seal-diff discipline.

``git diff --name-only BASELINE..SEAL_COMMIT`` shows only paths under:
``framework/primary-persona/src/``,
``framework/primary-persona/tests/``,
``framework/primary-persona/pyproject.toml`` (if dependency add
needed; expected: no add — pytest is already a test dep), and the
universal-paths admissions (``docs/rebuild/plans/``, ``CLAUDE.md``,
``docs/odd-in-loam.md``, ``docs/odd-methodology.md``,
``docs/rebuild/FUTURE_IDEAS.md``, ``docs/rebuild/FUTURE_IDEAS_DRAFT.md``).
Anything outside this set is a halt condition.

Smoke test: this file declares the AC; the ``test_no_sealed_amendments``
seal-diff test in the same directory enforces the actual fence (its
allowlist is the source of truth post-#52). This AC's test verifies
the AC is declared and behaviour-count is consistent.
"""

from __future__ import annotations

from pathlib import Path


def test_AC_DSA_S_seal_diff_test_file_present() -> None:
    """The component-level seal-diff fence test exists alongside this
    AC's per-AC verification (the actual diff happens in the
    cross-cutting test_no_sealed_amendments)."""
    fence_test = Path(__file__).parent / "test_no_sealed_amendments.py"
    assert fence_test.exists()


def test_AC_DSA_S_amendment_74_paths_are_under_primary_persona() -> None:
    """Every amendment-#74 source / test file lives under the
    primary-persona fence. (Static check on the build agent's
    authored set.)"""
    pp_root = Path(__file__).parent.parent  # framework/primary-persona
    src = pp_root / "src" / "loam" / "primary_persona" / "dispatch_wrapper.py"
    assert src.exists()
    # Per-AC test files exist.
    for ac_norm in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "S"]:
        # Permissive glob — file may have any descriptor suffix.
        matches = list(
            (pp_root / "tests").glob(f"test_AC_DSA_{ac_norm}_*.py")
        )
        assert len(matches) >= 1, (
            f"missing per-AC test for AC.DSA.{ac_norm}"
        )
