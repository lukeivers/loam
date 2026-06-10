"""AC.KDOC.5 — adapter tables + §14 relocated (KEEL Phase 1).

Adapter-table content lives under the extractor's package docs, not
the methodology spec; the old §14 (v0.2.3 multi-source banding rule)
lives in a changelog-class file. Plan:
docs/plans/keel-adoption-program.md §5.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SPEC = REPO_ROOT / "plugins" / "dev-sdlc" / "docs" / "odd-methodology.md"
ADAPTER_DOC = (
    REPO_ROOT
    / "plugins" / "dev-sdlc" / "odd-extractor" / "docs"
    / "adapter-conventions.md"
)
CHANGELOG = (
    REPO_ROOT / "plugins" / "dev-sdlc" / "docs"
    / "odd-methodology-CHANGELOG.md"
)


def test_adapter_doc_carries_the_tables() -> None:
    assert ADAPTER_DOC.exists(), "adapter-conventions.md missing"
    text = ADAPTER_DOC.read_text(encoding="utf-8")
    assert "Confidence band rules per Rails idiom" in text, "old §12 missing"
    assert "JS/TS/Playwright" in text, "old §13 missing"
    assert "Evidence requirements per band" in text, "old §11.2 missing"
    assert "ratification workflow" in text, "old §11.3 missing"


def test_spec_no_longer_carries_adapter_tables() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "Confidence band rules per Rails idiom" not in text
    assert "tree-sitter" not in text
    assert "Sidekiq" not in text


def test_changelog_carries_old_section_14() -> None:
    assert CHANGELOG.exists(), "odd-methodology-CHANGELOG.md missing"
    text = CHANGELOG.read_text(encoding="utf-8")
    assert "multi-source banding rule" in text, "§14 content missing"
    assert "ObjectiveEvidence" in text, "§14.2 evidence shape missing"


def test_spec_no_longer_carries_old_section_14() -> None:
    text = SPEC.read_text(encoding="utf-8")
    assert "ObjectiveEvidence" not in text
    assert "multi-source verified" not in text
