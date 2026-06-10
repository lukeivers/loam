"""AC.KDOC.2 — novelty-claim retraction (KEEL adoption program Phase 1).

No file in the live docs tree (docs/ + plugins/*/docs/, excluding
docs/archive/ + docs/plans/sealed/) asserts ODD novelty / "not in
training data" / unprecedented; the archived derivation doc carries a
dated retraction note; ancestry is named in the rewritten spec.
Plan: docs/plans/keel-adoption-program.md §5.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

# Claim-shaped patterns (assertions of novelty, not quoted mentions of
# the retired claim — quoted forms like `ODD is "genuinely new"` in
# plan/retraction prose are mentions, not assertions).
NOVELTY_PATTERNS = [
    re.compile(r"ODD is genuinely new"),
    re.compile(r"not in (?:my|the) training data", re.I),
    re.compile(
        r"(?:ODD|Objective-Driven Design) (?:is|was)[^.\n]{0,40}unprecedented",
        re.I,
    ),
]

EXCLUDED_PREFIXES = ("docs/archive/", "docs/plans/sealed/")


def _live_docs() -> list[Path]:
    files = list((REPO_ROOT / "docs").rglob("*.md"))
    files += list((REPO_ROOT / "plugins").glob("*/docs/**/*.md"))
    files += list((REPO_ROOT / "plugins").glob("*/odd-extractor/docs/**/*.md"))
    out = []
    for p in files:
        rel = p.relative_to(REPO_ROOT).as_posix()
        if rel.startswith(EXCLUDED_PREFIXES):
            continue
        out.append(p)
    return out


def test_no_live_doc_asserts_odd_novelty() -> None:
    offenders = []
    for p in _live_docs():
        text = p.read_text(encoding="utf-8", errors="ignore")
        for pat in NOVELTY_PATTERNS:
            for m in pat.finditer(text):
                rel = p.relative_to(REPO_ROOT).as_posix()
                offenders.append(f"{rel}: {m.group(0)[:60]}")
    assert offenders == [], f"live novelty claims found: {offenders}"


def test_archived_derivation_doc_carries_dated_retraction() -> None:
    archived = REPO_ROOT / "docs" / "archive" / "odd-llm-grounding-derivation.md"
    assert archived.exists(), "archived derivation doc missing"
    text = archived.read_text(encoding="utf-8")
    assert "RETRACTION" in text, "retraction note missing"
    assert "2026-06-10" in text, "retraction note is not dated"


def test_ancestry_named_in_rewritten_spec() -> None:
    spec = (
        REPO_ROOT / "plugins" / "dev-sdlc" / "docs" / "odd-methodology.md"
    ).read_text(encoding="utf-8")
    for ancestor in ("KAOS", "Ulwick", "Adzic", "Meyer"):
        assert ancestor in spec, f"ancestor {ancestor} not named in spec"
