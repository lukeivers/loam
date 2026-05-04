"""AC.BANDS.3 — odd-methodology.md carries the band semantics extension.

Content-grep test: load the doc; assert every required content marker
is present (band names; field names; CLI verb; cross-reference back
to §4 re-extension pattern). Not a prose-quality test.
"""

from __future__ import annotations

from pathlib import Path

import pytest


_DOC_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "docs"
    / "odd-methodology.md"
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    return _DOC_PATH.read_text(encoding="utf-8")


def test_doc_exists() -> None:
    """The methodology doc lives at the expected path."""
    assert _DOC_PATH.exists(), (
        f"odd-methodology.md not found at {_DOC_PATH}"
    )


def test_doc_has_band_section_heading(doc_text: str) -> None:
    """A new section appended for confidence bands."""
    assert (
        "## 11. Confidence bands for derived ACs" in doc_text
        or "## 11 Confidence bands for derived ACs" in doc_text
    ), "doc must add a §11 heading covering confidence bands"


def test_doc_names_three_bands_verbatim(doc_text: str) -> None:
    """Each band name is spelled exactly as the enum value."""
    assert "VERIFIED" in doc_text
    assert "PLAUSIBLE" in doc_text
    assert "HYPOTHESISED" in doc_text


def test_doc_names_evidence_field_names(doc_text: str) -> None:
    """The doc cross-references the Pydantic field names verbatim."""
    assert "evidence.kind" in doc_text or "`evidence.kind`" in doc_text
    assert (
        "evidence.citations" in doc_text
        or "`evidence.citations`" in doc_text
    )
    assert (
        "evidence.repo_sha" in doc_text
        or "`evidence.repo_sha`" in doc_text
    )
    assert (
        "evidence.rationale" in doc_text
        or "`evidence.rationale`" in doc_text
    )


def test_doc_names_evidence_kind_values(doc_text: str) -> None:
    """The discriminator values are spelled verbatim."""
    assert '"test"' in doc_text
    assert '"source"' in doc_text
    assert '"inference"' in doc_text


def test_doc_names_ratification_cli_verb(doc_text: str) -> None:
    """The CLI verb is named verbatim so cross-references work."""
    assert "loam odd-extract ratify" in doc_text


def test_doc_names_action_kinds(doc_text: str) -> None:
    """Each of the four ratification action kinds is named."""
    for kind in ("promote", "demote", "edit", "reject"):
        assert kind in doc_text, (
            f"doc must name the '{kind}' ratification action kind"
        )


def test_doc_names_decision_i_default_no(doc_text: str) -> None:
    """The PLAUSIBLE→VERIFIED default-no rule is explicit + named."""
    assert "PLAUSIBLE" in doc_text and "VERIFIED" in doc_text
    assert (
        "explicit" in doc_text.lower()
        and "default-no" in doc_text.lower()
    ), (
        "doc must spell out PLAUSIBLE→VERIFIED requires explicit "
        "confirmation per Decision I (default-no)"
    )


def test_doc_cross_references_re_extension_section(doc_text: str) -> None:
    """The §4 re-extension pattern is cross-referenced."""
    # Either the explicit "§4" reference or "re-extension" being
    # mentioned in the bands section is acceptable.
    assert "re-extension" in doc_text.lower(), (
        "doc must cross-reference re-extension pattern (§4)"
    )


def test_doc_names_soc2_audit_floor(doc_text: str) -> None:
    """The audit-log requirement carries the SOC-2 floor + Decision P."""
    assert "SOC-2" in doc_text or "audit" in doc_text.lower()
    assert "Decision P" in doc_text or "decision p" in doc_text.lower()


def test_doc_names_pm_one_question_at_a_time(doc_text: str) -> None:
    """The PM mediation + one-question-at-a-time discipline is named."""
    assert "one-question-at-a-time" in doc_text or "decision queue" in doc_text.lower()
    assert "PM" in doc_text or "per-project" in doc_text.lower()


def test_doc_names_bands_module_path(doc_text: str) -> None:
    """The doc points readers at the structural enforcement module."""
    assert (
        "bands.py" in doc_text
        or "loam_odd_extractor.bands" in doc_text
    )
