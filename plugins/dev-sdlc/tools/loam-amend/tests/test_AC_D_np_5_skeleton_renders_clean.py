"""Tests for AC.D-np.5 — the skeleton template renders cleanly against a
fixture vars-file, byte-identical to a committed expected output.

Per `docs/rebuild/plans/pos-amend-new-plan-orchestration.md`:

    The post-extension ``tools/loam/templates/plan/dev-discipline.md``
    skeleton renders against a fixture vars-file (committed as test data)
    to produce byte-identical fixture-expected output. The fixture
    exercises every required + every optional variable with non-default
    values; the output proves the skeleton is rendering-clean (no
    unmatched placeholders, no missing sections, no malformed
    substitutions).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_amend.cli import main


FIXTURES = Path(__file__).parent / "fixtures" / "plan-skeleton"


def test_AC_D_np_5_skeleton_renders_byte_identical_to_fixture(
    tmp_path: Path,
) -> None:
    out = tmp_path / "rendered.md"
    rc = main(
        [
            "template",
            "render",
            "plan/dev-discipline",
            "--vars-file",
            str(FIXTURES / "vars.yaml"),
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    actual = out.read_text(encoding="utf-8")
    expected = (FIXTURES / "expected.md").read_text(encoding="utf-8")
    assert actual == expected, (
        "fixture render diverged from expected.md. If the divergence is "
        "intentional (e.g. skeleton structure changed), regenerate the "
        "expected fixture via:\n"
        "  loam amend template render plan/dev-discipline "
        "--vars-file tools/loam/tests/fixtures/plan-skeleton/vars.yaml "
        "--out tools/loam/tests/fixtures/plan-skeleton/expected.md "
        "--force"
    )


def test_AC_D_np_5_fixture_render_carries_all_section_headings() -> None:
    expected = (FIXTURES / "expected.md").read_text(encoding="utf-8")
    for section in (
        "## 1. Summary / TLDR",
        "## 2. Spec-objective placement",
        "## 3. Three-lens analysis",
        "## 4. Acceptance criteria (AC.FIX.x",
        "## 5. Behaviour-count check",
        "## 6. Hard constraints",
        "## 7. Out of scope",
        "## 8. Implementation order",
        "## 9. Bookkeeping surface",  # SECTION_9_HEADING fixture value
        "## 10. Halt triggers",
        "## 11. Decisions remaining",
        "## 12. Summary of named decisions",
        "## 13. Halt-and-surface findings",
        "## 14. Method-decision record",
        "## 15. References",
    ):
        assert section in expected, f"fixture-expected missing: {section}"


def test_AC_D_np_5_fixture_carries_section_14_subsection_scaffold() -> None:
    """The §14 subsection scaffold (`### D-build.x`, `### Test breakdown`,
    `### Backwards-compat verification`, `### Commit SHAs`, `### Dependents
    cleared to dispatch`) appears verbatim in the fixture-rendered output.
    """
    expected = (FIXTURES / "expected.md").read_text(encoding="utf-8")
    for subsection in (
        "### D-build.x",
        "### Test breakdown",
        "### Backwards-compat verification",
        "### Commit SHAs",
        "### Dependents cleared to dispatch",
    ):
        assert subsection in expected, f"§14 scaffold missing: {subsection}"


def test_AC_D_np_5_fixture_render_has_no_unmatched_placeholders() -> None:
    expected = (FIXTURES / "expected.md").read_text(encoding="utf-8")
    assert "{{" not in expected, "fixture has unmatched {{ placeholders"
