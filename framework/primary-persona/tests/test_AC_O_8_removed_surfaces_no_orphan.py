"""AC.O.8 — Removed surfaces are gone; no orphan code.

The deleted symbols (``OnboardingQuestion``, ``ONBOARDING_QUESTIONS``,
``persist_elicitation_transcript``, ``OnboardingTranscriptError``,
``_normalise_dev_intent``, ``_DEV_INTENT_YES``, ``_DEV_INTENT_NO``,
``_is_complete_transcript``, ``_validate_transcript_shape``) are
not importable from ``primary_persona.onboarding`` (or, equivalently
in this test layer, ``src.onboarding``). No production module
references the removed names. No test in the suite references the
removed names.

Plan: docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype.md
"""

from __future__ import annotations

import importlib
from pathlib import Path


# ---- removed-symbol catalogue ---------------------------------------

REMOVED_NAMES = (
    # ---- locked-plan AC.O.8 catalogue ----
    "OnboardingQuestion",
    "ONBOARDING_QUESTIONS",
    "persist_elicitation_transcript",
    "OnboardingTranscriptError",
    "_normalise_dev_intent",
    "_DEV_INTENT_YES",
    "_DEV_INTENT_NO",
    "_is_complete_transcript",
    "_validate_transcript_shape",
    # ---- AC.O.8 re-extension (per ODD §4.1, build-time discovery) ----
    # The five observability event helpers below were emitted only
    # by ``persist_elicitation_transcript``; with that function
    # removed they had no remaining caller and no backing AC. Per
    # ODD §2.5 reverse-direction (every code path must trace back to
    # an AC), they are deleted as part of the rewrite.
    "onboarding_question_event",
    "onboarding_answer_event",
    "onboarding_writeback_event",
    "onboarding_dev_intent_question_event",
    "onboarding_dev_intent_answer_event",
)


# ---- importability ---------------------------------------------------


def test_AC_O_8_removed_names_not_importable_from_onboarding_module():
    """Each removed symbol is not an attribute on
    ``primary_persona.onboarding`` (resolved via the local ``src``
    package alias used by the test layer)."""
    onboarding = importlib.import_module("src.onboarding")
    for name in REMOVED_NAMES:
        assert not hasattr(onboarding, name), (
            f"removed symbol {name!r} still on onboarding module"
        )


def test_AC_O_8_removed_names_not_importable_from_package_root():
    """Each removed symbol is not exposed by the package's top-level
    ``__init__.py`` either."""
    pkg = importlib.import_module("src")
    for name in REMOVED_NAMES:
        assert not hasattr(pkg, name), (
            f"removed symbol {name!r} still re-exported from package root"
        )


# ---- source / test sweep --------------------------------------------


def _scan_files_for_names(directory: Path, allowed_files: set[str]) -> dict[str, list[str]]:
    """Return mapping {file_name: [missing-allowed-names-found]}."""
    results: dict[str, list[str]] = {}
    for py in directory.glob("*.py"):
        if py.name in allowed_files:
            continue
        text = py.read_text()
        hits = [name for name in REMOVED_NAMES if name in text]
        if hits:
            results[py.name] = hits
    return results


def test_AC_O_8_no_test_references_removed_symbols():
    """Walk ``primary-persona/tests/``; assert no test file
    references the removed symbol names. The AC.O.8 test file
    itself is exempted (it lists the names as constants for the
    sweep)."""
    tests_dir = Path(__file__).resolve().parent
    hits = _scan_files_for_names(
        tests_dir,
        allowed_files={
            # The AC.O.8 test catalogues the removed names.
            Path(__file__).name,
        },
    )
    assert hits == {}, (
        f"test files still reference removed symbols: {hits}"
    )


def test_AC_O_8_no_src_module_references_removed_symbols():
    """Walk ``primary-persona/src/``; assert no production module
    references the removed symbol names."""
    src_dir = Path(__file__).resolve().parent.parent / "src"
    hits = _scan_files_for_names(src_dir, allowed_files=set())
    assert hits == {}, (
        f"src modules still reference removed symbols: {hits}"
    )
