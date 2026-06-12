"""AC.BANDS.3 — the band semantics are documented and cross-references
work, asserted at their CURRENT canonical homes.

Content-grep test, post-KEEL-P1: the methodology rewrite (`d9f2b3cb`,
1,264→360 lines, sealed) RESTATED band semantics in
``odd-methodology.md`` §6 ("Check-kinds and evidence grades") and
EXPLICITLY relocated the extractor mechanics (evidence-field rules,
ratification workflow, promotion asymmetry) to the extractor's own
``docs/adapter-conventions.md``. This test follows the content to
those homes (broken-suite-family-fixes D-SUITEFIX.3): every
pre-rewrite marker is still asserted — band names + bands.py pointer
+ re-extension cross-reference in the methodology doc; evidence
fields, ratify CLI verb, action kinds, default-no, SOC-2/Decision P,
PM mediation in adapter-conventions.md — and the relocation pointer
itself is asserted, so deleting EITHER home still trips the guard.
Not a prose-quality test.
"""

from __future__ import annotations

from pathlib import Path

import pytest


_DOCS_ROOT = Path(__file__).resolve().parent.parent.parent / "docs"
_DOC_PATH = _DOCS_ROOT / "odd-methodology.md"
_CONVENTIONS_PATH = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "adapter-conventions.md"
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    return _DOC_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def conventions_text() -> str:
    return _CONVENTIONS_PATH.read_text(encoding="utf-8")


def test_doc_exists() -> None:
    """Both canonical band-documentation homes live at their paths."""
    assert _DOC_PATH.exists(), (
        f"odd-methodology.md not found at {_DOC_PATH}"
    )
    assert _CONVENTIONS_PATH.exists(), (
        f"adapter-conventions.md not found at {_CONVENTIONS_PATH} — "
        f"the methodology doc names it as the home of the extractor "
        f"band mechanics (KEEL-P1 relocation)"
    )


def test_doc_has_band_section_heading(doc_text: str) -> None:
    """The methodology doc carries the post-KEEL band section."""
    assert "## 6. Check-kinds and evidence grades" in doc_text, (
        "doc must carry the §6 check-kinds / evidence-grades section "
        "(the KEEL-P1 restatement of confidence bands)"
    )


def test_doc_points_at_relocated_extractor_mechanics(
    doc_text: str,
) -> None:
    """The methodology doc cross-references the relocation home, so
    the two-doc split stays discoverable from the canonical spec."""
    assert "adapter-conventions.md" in doc_text, (
        "doc must point readers at adapter-conventions.md for the "
        "extractor band mechanics (evidence-field rules, ratification "
        "workflow, promotion asymmetry)"
    )


def test_doc_names_three_bands_verbatim(doc_text: str) -> None:
    """Each extractor band name is spelled exactly as the enum value."""
    assert "VERIFIED" in doc_text
    assert "PLAUSIBLE" in doc_text
    assert "HYPOTHESISED" in doc_text


def test_conventions_doc_names_evidence_field_names(
    conventions_text: str,
) -> None:
    """The relocated home cross-references the Pydantic field names
    verbatim."""
    assert "evidence.kind" in conventions_text
    assert "evidence.citations" in conventions_text
    assert "evidence.repo_sha" in conventions_text
    assert "evidence.rationale" in conventions_text


def test_conventions_doc_names_evidence_kind_values(
    conventions_text: str,
) -> None:
    """The discriminator values are spelled verbatim in the relocated
    home."""
    assert '"test"' in conventions_text
    assert '"source"' in conventions_text
    assert '"inference"' in conventions_text


def test_conventions_doc_names_ratification_cli_verb(
    conventions_text: str,
) -> None:
    """The CLI verb is named verbatim so cross-references work."""
    assert "loam odd-extract ratify" in conventions_text


def test_conventions_doc_names_action_kinds(
    conventions_text: str,
) -> None:
    """Each of the four ratification action kinds is named."""
    for kind in ("promote", "demote", "edit", "reject"):
        assert kind in conventions_text, (
            f"adapter-conventions.md must name the '{kind}' "
            f"ratification action kind"
        )


def test_conventions_doc_names_decision_i_default_no(
    conventions_text: str,
) -> None:
    """The PLAUSIBLE→VERIFIED default-no rule is explicit + named."""
    assert (
        "PLAUSIBLE" in conventions_text
        and "VERIFIED" in conventions_text
    )
    assert "default-no" in conventions_text.lower(), (
        "adapter-conventions.md must spell out the silent-promotion "
        "default-no rule (Decision I)"
    )


def test_doc_cross_references_re_extension_section(doc_text: str) -> None:
    """The re-extension pattern is cross-referenced in the
    methodology doc (§4 territory)."""
    assert "re-extension" in doc_text.lower(), (
        "doc must cross-reference the re-extension pattern (§4)"
    )


def test_conventions_doc_names_soc2_audit_floor(
    conventions_text: str,
) -> None:
    """The audit-log requirement carries the SOC-2 floor + Decision P."""
    assert "SOC-2" in conventions_text
    assert "Decision P" in conventions_text


def test_conventions_doc_names_pm_one_question_at_a_time(
    conventions_text: str,
) -> None:
    """The PM mediation + one-question-at-a-time discipline is named."""
    assert (
        "one-question-at-a-time" in conventions_text
        or "decision queue" in conventions_text.lower()
    )
    assert (
        "PM" in conventions_text
        or "per-project" in conventions_text.lower()
    )


def test_doc_names_bands_module_path(doc_text: str) -> None:
    """The methodology doc points readers at the structural
    enforcement module."""
    assert (
        "bands.py" in doc_text
        or "loam_odd_extractor.bands" in doc_text
    )
