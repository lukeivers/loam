"""AC.KDOC.4 — dormant-gates archive note (KEEL adoption program Phase 1).

A dated archive note exists naming both gates + the verdict's three
reasons + the salvaged dispatch contract-carriage component; no live
doctrine doc implies write-time structural enforcement is active
(closes the implementation-fidelity audit's D1 doctrine half — the
doctrine-surface scope is the AC's "doctrine half" clause; historical
plan/research records under docs/plans/ document the gates' build and
are not doctrine). Plan: docs/plans/keel-adoption-program.md §5.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
NOTE = (
    REPO_ROOT / "docs" / "archive" / "dormant-write-time-gates-2026-06-10.md"
)


def test_note_exists_and_is_dated() -> None:
    assert NOTE.exists(), "dormant-gates archive note missing"
    assert "2026-06-10" in NOTE.read_text(encoding="utf-8")


def test_note_names_both_gates() -> None:
    text = NOTE.read_text(encoding="utf-8")
    assert "objective_binding_gate.py" in text
    assert "tdd_guard.py" in text


def test_note_carries_the_three_reasons() -> None:
    flat = re.sub(r"\s+", " ", NOTE.read_text(encoding="utf-8"))
    assert "completion-time" in flat and "write-time" in flat, (
        "reason (a): completion-time vs write-time missing"
    )
    assert "produced with both gates dormant" in flat or (
        "produced with them off" in flat
    ), "reason (b): record-produced-with-them-off missing"
    assert "worst state" in flat, (
        "reason (c): built+sealed+dormant-is-the-worst-state missing"
    )


def test_note_names_the_salvaged_component() -> None:
    flat = re.sub(r"\s+", " ", NOTE.read_text(encoding="utf-8"))
    assert "dispatch contract-carriage" in flat
    assert "dispatch_setup_hook.py" in flat
    assert "Cycle A" in flat


def test_no_doctrine_doc_implies_active_write_time_enforcement() -> None:
    """Doctrine surfaces (docs root, docs/design, plugins/*/docs) carry
    zero references to the archived gates outside the archive note, and
    the spec states plainly that no write-time enforcement is active."""
    doctrine: list[Path] = list((REPO_ROOT / "docs").glob("*.md"))
    doctrine += list((REPO_ROOT / "docs" / "design").rglob("*.md"))
    doctrine += list((REPO_ROOT / "plugins").glob("*/docs/**/*.md"))
    offenders = []
    for p in doctrine:
        text = p.read_text(encoding="utf-8", errors="ignore")
        if "objective_binding_gate" in text or "tdd_guard" in text:
            offenders.append(p.relative_to(REPO_ROOT).as_posix())
    assert offenders == [], (
        f"doctrine docs still reference the archived gates: {offenders}"
    )
    spec = (
        REPO_ROOT / "plugins" / "dev-sdlc" / "docs" / "odd-methodology.md"
    ).read_text(encoding="utf-8")
    flat = re.sub(r"\s+", " ", spec)
    assert "no active write-time structural enforcement" in flat, (
        "spec must state no write-time structural enforcement is active"
    )
