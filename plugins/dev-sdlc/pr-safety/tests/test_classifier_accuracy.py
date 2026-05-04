"""Classifier accuracy on synthetic test set (AC.PRSG.3 — ≥90% bar).

Per master plan §7.1 — most-load-bearing risk of Cycle 1. Halt-trigger
fires below threshold.

Synthetic test set: ≥10 diffs spanning all 4 shapes — VERIFIED-touch /
PLAUSIBLE-touch / HYPOTHESISED-touch / novel-only / mixed / refactor-
shaped. Each diff has a known-correct expected classification; we
measure (true-positive-rate + true-negative-rate) / 2 across the set.

Accuracy formula (per plan-doc §4 AC.PRSG.3):

    accuracy = correct_predictions / total_predictions

Where each prediction is one (diff, contract, expected_outcome) tuple.
We measure at the AC-touch level: for each AC in the contract, did
the classifier correctly classify it as touched-or-not? Plus: did the
classifier correctly identify the novel-candidate set?

Bar: accuracy ≥ 0.90 across the test set. Below → halt-trigger fires
(:class:`ClassifierAccuracyError` raised; build halts for AST-aware
extension).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_pr_safety import (
    BandedContract,
    ClassifierAccuracyError,
    Diff,
    DiffEntry,
    Hunk,
    classify,
)
from loam_odd_extractor.bands import (
    BandedAC,
    ConfidenceBand,
    Evidence,
)


# ---- Reusable fixture contract --------------------------------------


def _contract() -> BandedContract:
    """A 5-AC banded contract for classifier tests.

    AC.A — VERIFIED, app/a.py:10-20.
    AC.B — VERIFIED, app/b.py:50-60 (test-citation only).
    AC.C — PLAUSIBLE, src/c.py:100-150.
    AC.D — HYPOTHESISED, src/d.py (backing only, no citations).
    AC.E — VERIFIED, file-level only (no line range).
    """
    return BandedContract(
        extraction_id="synthetic-accuracy-test",
        repo_path=Path("/synthetic"),
        repo_sha="abc1234",
        created_at="2026-05-04T00:00:00+00:00",
        acs=[
            BandedAC(
                ac_id="AC.A",
                text="A — VERIFIED with line range",
                confidence=ConfidenceBand.VERIFIED,
                evidence=Evidence(
                    kind="test",
                    citations=[
                        "app/a.py:10-20",
                        "tests/test_a.py::test_a",
                    ],
                    repo_sha="abc1234",
                ),
                backing_files=["app/a.py", "tests/test_a.py"],
            ),
            BandedAC(
                ac_id="AC.B",
                text="B — VERIFIED with backing files",
                confidence=ConfidenceBand.VERIFIED,
                evidence=Evidence(
                    kind="test",
                    citations=[
                        "tests/test_b.py::test_b",
                        "app/b.py:50-60",
                    ],
                    repo_sha="abc1234",
                ),
                backing_files=["app/b.py", "tests/test_b.py"],
            ),
            BandedAC(
                ac_id="AC.C",
                text="C — PLAUSIBLE",
                confidence=ConfidenceBand.PLAUSIBLE,
                evidence=Evidence(
                    kind="source",
                    citations=["src/c.py:100-150"],
                ),
                backing_files=["src/c.py"],
            ),
            BandedAC(
                ac_id="AC.D",
                text="D — HYPOTHESISED",
                confidence=ConfidenceBand.HYPOTHESISED,
                evidence=Evidence(
                    kind="inference",
                    rationale="Inferred from comment patterns.",
                ),
                backing_files=["src/d.py"],
            ),
            BandedAC(
                ac_id="AC.E",
                text="E — VERIFIED, file-level citation only",
                confidence=ConfidenceBand.VERIFIED,
                evidence=Evidence(
                    kind="test",
                    citations=[
                        "tests/test_e.py::test_e",
                        "app/e.py:1-200",
                    ],
                    repo_sha="abc1234",
                ),
                backing_files=["app/e.py", "tests/test_e.py"],
            ),
        ],
    )


def _diff(*entries: tuple[str, list[Hunk]]) -> Diff:
    return Diff(
        from_sha="aaa",
        to_sha="bbb",
        entries=[
            DiffEntry(file_path=Path(p), hunks=list(hunks))
            for p, hunks in entries
        ],
    )


def _h(start: int, lines: int = 1) -> Hunk:
    return Hunk(
        old_start=start, old_lines=lines,
        new_start=start, new_lines=lines,
    )


# ---- Synthetic test set ---------------------------------------------


def _test_set() -> list[tuple[str, Diff, set[str], int]]:
    """Return [(name, diff, expected_touched_ac_ids, expected_novel_count), ...]."""
    return [
        # 1. Strict line-overlap on AC.A (VERIFIED). Touch: {AC.A}.
        (
            "verified_strict_line_overlap_a",
            _diff(("app/a.py", [_h(15, 2)])),
            {"AC.A"},
            0,
        ),
        # 2. Outside AC.A line range but in AC.A backing file → not
        # touched per Cycle 1 spec; not novel either (file is mapped).
        (
            "verified_a_outside_range",
            _diff(("app/a.py", [_h(40, 2)])),
            set(),
            0,
        ),
        # 3. Strict line-overlap on AC.C (PLAUSIBLE).
        (
            "plausible_c_line_overlap",
            _diff(("src/c.py", [_h(120, 5)])),
            {"AC.C"},
            0,
        ),
        # 4. Backing-file match on AC.D (HYPOTHESISED, no citations).
        (
            "hypothesised_d_backing_file",
            _diff(("src/d.py", [_h(1, 10)])),
            {"AC.D"},
            0,
        ),
        # 5. Novel-only — file is in no AC's citations or backing files.
        (
            "novel_only",
            _diff(("app/totally_new.py", [_h(1, 20)])),
            set(),
            1,
        ),
        # 6. Mixed — VERIFIED + novel.
        (
            "mixed_verified_a_plus_novel",
            _diff(
                ("app/a.py", [_h(12, 3)]),
                ("app/new.py", [_h(1, 5)]),
            ),
            {"AC.A"},
            1,
        ),
        # 7. Refactor-shaped — same line moved within range.
        # AC.B citation: app/b.py:50-60. Diff hits line 55 (still in
        # range) — should be touched.
        (
            "refactor_within_range",
            _diff(("app/b.py", [_h(55, 1)])),
            {"AC.B"},
            0,
        ),
        # 8. Wide-range AC.E — touch within 1-200.
        (
            "verified_e_wide_range",
            _diff(("app/e.py", [_h(150, 3)])),
            {"AC.E"},
            0,
        ),
        # 9. Plausible C edge of range — line 100 (start boundary).
        (
            "plausible_c_edge_start",
            _diff(("src/c.py", [_h(100, 1)])),
            {"AC.C"},
            0,
        ),
        # 10. Plausible C edge of range — line 150 (end boundary).
        (
            "plausible_c_edge_end",
            _diff(("src/c.py", [_h(150, 1)])),
            {"AC.C"},
            0,
        ),
        # 11. Multi-AC touch — modify two cited files in one diff.
        (
            "multi_a_and_c",
            _diff(
                ("app/a.py", [_h(15, 2)]),
                ("src/c.py", [_h(125, 5)]),
            ),
            {"AC.A", "AC.C"},
            0,
        ),
        # 12. Empty diff — untouched, no novel.
        (
            "empty_diff",
            _diff(),
            set(),
            0,
        ),
    ]


def test_classifier_accuracy_at_least_90_percent():
    """Every synthetic diff classified correctly → accuracy ≥ 0.90.

    "Correctly classified" measured at the (touch_id_set, novel_count)
    level. A test case is correct iff:
      - The set of touched AC ids EXACTLY matches expected.
      - The novel count EXACTLY matches expected.
    """
    contract = _contract()
    test_cases = _test_set()
    correct = 0
    incorrect_cases: list[str] = []
    for name, diff, expected_touched, expected_novel in test_cases:
        result = classify(diff, contract)
        actual_touched = {t.ac.ac_id for t in result.touched_acs}
        actual_novel = len(result.novel)
        if actual_touched == expected_touched and actual_novel == expected_novel:
            correct += 1
        else:
            incorrect_cases.append(
                f"{name}: expected touched={expected_touched} "
                f"novel={expected_novel}; got touched={actual_touched} "
                f"novel={actual_novel}"
            )
    accuracy = correct / len(test_cases)
    if accuracy < 0.90:
        # Halt-trigger fires per master plan §7.1.
        raise ClassifierAccuracyError(
            f"Classifier accuracy {accuracy:.0%} below 90% bar. "
            f"Failures:\n" + "\n".join(incorrect_cases)
        )
    assert accuracy >= 0.90, (
        f"Classifier accuracy {accuracy:.0%} below 90% bar. "
        f"Failures:\n" + "\n".join(incorrect_cases)
    )


def test_classifier_accuracy_test_set_covers_all_shapes():
    """Per plan-doc §4 AC.PRSG.3 — synthetic test set covers all 4
    shapes (verified-touch / plausible-touch / hypothesised-touch /
    novel-only) + mixed shapes.
    """
    test_cases = _test_set()
    assert len(test_cases) >= 10, (
        f"synthetic test set has {len(test_cases)} cases; need ≥10"
    )
    # Inspect names — at least one of each shape:
    names = [t[0] for t in test_cases]
    assert any("verified" in n for n in names)
    assert any("plausible" in n for n in names)
    assert any("hypothesised" in n for n in names)
    assert any("novel" in n for n in names)
    assert any("mixed" in n for n in names)


def test_classifier_accuracy_deterministic():
    """Same (diff, contract) input → same classification output."""
    contract = _contract()
    test_cases = _test_set()
    runs = []
    for _ in range(3):
        run = []
        for name, diff, _e, _n in test_cases:
            r = classify(diff, contract)
            run.append(
                (
                    name,
                    sorted(t.ac.ac_id for t in r.touched_acs),
                    sorted(t.touch_kind for t in r.touched_acs),
                    len(r.novel),
                    r.untouched,
                )
            )
        runs.append(run)
    assert runs[0] == runs[1] == runs[2]
