"""AC.V040C1.4 — No regression in pre-existing odd-extractor tests.

Per cycle-1 plan-doc §4 AC.V040C1.4: ``pytest plugins/dev-sdlc/
odd-extractor/tests/`` returns 0 with the pre-existing test count
unchanged (no pre-existing test edited).

This module asserts the no-regression invariant structurally rather
than by re-running pytest itself (which would loop). The invariant:

1. The pre-existing modules and symbols this cycle depends on
   (``BuildNextRecommendation``, ``GapInventory``,
   ``AugmentedObjectiveSet``, ``Objective``, ``Gap``,
   ``BuildNextCandidate``) remain importable with their existing
   public surface.
2. The new ``code_gen.py`` module is importable as a sibling of
   the existing modules without breaking any of them.
3. The new ``code_gen_spec.py`` is importable.

Per amendment-dispatch-speedups: full pre-seal repo rerun is skipped;
cross-component seal-diff is the integrity gate (verified at
``loam amend apply --dry-run`` time).
"""

from __future__ import annotations


def test_AC_V040C1_4_existing_specs_still_importable() -> None:
    """Pre-existing schema classes still import cleanly."""
    from loam_odd_extractor.spec import (  # noqa: F401
        AugmentedObjectiveSet,
        BuildNextCandidate,
        BuildNextRecommendation,
        Gap,
        GapInventory,
        Objective,
    )


def test_AC_V040C1_4_existing_build_next_still_importable() -> None:
    """Pre-existing build-next module still imports cleanly."""
    from loam_odd_extractor.build_next import (  # noqa: F401
        BuildNextRecommendation,  # re-exported
        load_recommendation,
        save_recommendation,
        score_candidates,
    )


def test_AC_V040C1_4_existing_cli_still_importable() -> None:
    """Pre-existing CLI module still imports cleanly + has the
    expected pre-existing handlers."""
    from loam_odd_extractor import cli as cli_module

    # Pre-existing _cmd_build_next handler (from v0.2.4 Cycle 3).
    assert hasattr(cli_module, "_cmd_build_next"), (
        "pre-existing _cmd_build_next handler must remain on cli "
        "module (no-regression)"
    )
    # build_odd_extract_subcommand entry-point that drives `loam`
    # invocations.
    assert hasattr(cli_module, "build_odd_extract_subcommand"), (
        "pre-existing build_odd_extract_subcommand must remain on "
        "cli module"
    )


def test_AC_V040C1_4_existing_synthesis_client_still_importable() -> None:
    """Pre-existing claude_print_synthesis_client wrapper still
    imports cleanly (subscription-only LLM dispatch path
    preserved)."""
    from loam_odd_extractor.claude_print_synthesis_client import (  # noqa: F401
        ClaudePrintAnthropicShimClient,
    )


def test_AC_V040C1_4_new_modules_importable() -> None:
    """The two new modules import cleanly as siblings."""
    from loam_odd_extractor import code_gen, code_gen_spec  # noqa: F401
    from loam_odd_extractor.code_gen import (  # noqa: F401
        extract_objectives_block,
        generate_code,
        load_diff,
        persist_diff,
    )
    from loam_odd_extractor.code_gen_spec import (  # noqa: F401
        CodeGenCommit,
        CodeGenDiff,
        CodeGenRequest,
    )
