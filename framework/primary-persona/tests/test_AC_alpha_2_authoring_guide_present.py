"""AC.α.2 — Two-class corpus authoring guide present at canonical path.

Per plan §4 AC.α.2, the file
``docs/rebuild/capability-corpus/AUTHORING.md`` exists and carries:

  - A *Class A — Anthropic-canonical reference* section naming the
    deterministic-projection contract, the required sections per
    Class A doc (Surface, Inputs/outputs, Composition notes,
    [user-intent phrasings], Source — with source_url +
    source_fetch_ts).
  - A *Class A-prime — pos-v2 harness primitives* section naming
    the same shape applied to pos-v2 component docs.
  - A *Class B — best-practices wisdom* section naming the
    synthesis-and-curation contract; required sections (Pattern,
    Conditions, Failure modes, [primitive: <name>] cross-references,
    Trust marker — with sources_count, validation_count,
    supersession_chain, owner_acked).
  - A *Cross-class* section naming the paired-fetch convention.
  - A *No-cross-class-write* invariant.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AUTHORING_MD = (
    REPO_ROOT / "docs" / "rebuild" / "capability-corpus" / "AUTHORING.md"
)


def _body() -> str:
    return AUTHORING_MD.read_text()


def test_AC_alpha_2_authoring_guide_exists():
    assert AUTHORING_MD.is_file(), (
        f"AUTHORING.md missing at {AUTHORING_MD}"
    )
    assert _body().strip() != ""


def test_AC_alpha_2_class_a_section_present():
    """Class A (Anthropic-canonical reference) section is present."""
    body = _body()
    assert "Class A" in body
    # The deterministic-projection contract is named.
    assert "deterministic projection" in body.lower()


def test_AC_alpha_2_class_a_required_sections_named():
    """The Class A required-sections list names Surface,
    Inputs/outputs, Composition notes, [user-intent phrasings],
    Source (with source_url + source_fetch_ts)."""
    body = _body()
    for required in (
        "Surface",
        "Inputs/outputs",
        "Composition notes",
        "[user-intent phrasings]",
        "Source",
        "source_url",
        "source_fetch_ts",
    ):
        assert required in body, (
            f"Class A schema field {required!r} missing from AUTHORING.md"
        )


def test_AC_alpha_2_class_a_prime_section_present():
    """Class A-prime (pos-v2 harness primitives) section is present
    naming the same shape applied to pos-v2 component docs."""
    body = _body()
    assert "Class A-prime" in body
    # Sourced from pos-v2's own component docs.
    assert "harness" in body.lower()


def test_AC_alpha_2_class_b_section_present():
    """Class B (best-practices wisdom) section is present naming
    the synthesis-and-curation contract."""
    body = _body()
    assert "Class B" in body
    assert "synthesis" in body.lower() or "curation" in body.lower()


def test_AC_alpha_2_class_b_required_sections_named():
    """The Class B required-sections list names Pattern, Conditions,
    Failure modes, cross-reference syntax, and the Trust marker
    fields (sources_count, validation_count, supersession_chain,
    owner_acked)."""
    body = _body()
    for required in (
        "Pattern",
        "Conditions",
        "Failure modes",
        "[primitive:",
        "Trust marker",
        "sources_count",
        "validation_count",
        "supersession_chain",
        "owner_acked",
    ):
        assert required in body, (
            f"Class B schema field {required!r} missing from AUTHORING.md"
        )


def test_AC_alpha_2_cross_class_paired_fetch_section_present():
    """The Cross-class section names the paired-fetch convention."""
    body = _body()
    assert "Cross-class" in body
    assert "paired-fetch" in body.lower() or "paired fetch" in body.lower()


def test_AC_alpha_2_no_cross_class_write_invariant_named():
    """The No-cross-class-write invariant is documented as a
    structural rule (Class A's δ-projection refresh never writes to
    Class B; Class B's accrual channels never write to Class A)."""
    body = _body()
    assert "No-cross-class-write" in body
    # The invariant body must name the directional rule.
    lower = body.lower()
    assert "never writes" in lower or "never write" in lower
