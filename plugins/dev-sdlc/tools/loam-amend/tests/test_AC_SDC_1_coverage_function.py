"""AC.SDC.1 — the shared-doc-coverage function derives surface + guards +
uncovered set from the live repo.

Plan: ``docs/plans/shared-doc-guard-floor-coverage.md`` §2 / §4.

The function derives (a) the file-level universal-admitted doc surface
(prefixes excluded; the dev-mode docs/ <-> plugins/dev-sdlc/docs/ relocation
normalized), (b) for each surface doc its constant-anchored content-guard
tests, and (c) given a floor, the guards that floor does not cover.
"""

from __future__ import annotations

from pathlib import Path

from loam_amend.guard_floor import GuardFloor
from loam_amend.shared_doc_coverage import (
    find_uncovered_shared_doc_guards,
    shared_doc_guards,
    shared_doc_surface,
)

REPO_ROOT = Path(__file__).resolve().parents[5]

ODD = "plugins/dev-sdlc/docs/odd-methodology.md"


def test_surface_contains_shared_docs_and_excludes_prefix_spaces() -> None:
    surface = shared_doc_surface(REPO_ROOT)
    # File-level universal-admitted docs are present, incl. the dev-mode
    # normalized real path of the methodology doc.
    assert ODD in surface
    assert "docs/VALUE_PROPOSITION.md" in surface
    assert "CLAUDE.dev.md" in surface
    # Prefix spaces (universal_paths.prefixes) are NOT files on the surface.
    assert "docs/plans/" not in surface
    assert "docs/design/" not in surface


def test_guards_map_surface_docs_to_content_guards() -> None:
    guards = shared_doc_guards(REPO_ROOT)
    assert ODD in guards
    odd_guards = guards[ODD]
    assert "plugins/dev-sdlc/tests/test_AC_KDOC_1_methodology_rewrite.py" in odd_guards
    # A guard on the SAME shared doc from a DIFFERENT component is included.
    assert (
        "framework/primary-persona/tests/test_AC_RVL_8_cap_bias_checklist_line.py"
        in odd_guards
    )


def test_uncovered_computed_against_a_floor() -> None:
    # An empty floor covers nothing → every surface-doc guard is uncovered.
    empty = GuardFloor(fence_targets=[], sweep_targets=[], registry_present=True)
    uncovered = find_uncovered_shared_doc_guards(REPO_ROOT, empty)
    guards = shared_doc_guards(REPO_ROOT)
    total = sum(len(v) for v in guards.values())
    assert len(uncovered) == total > 0
    assert all(v.guard_test and v.doc for v in uncovered)
