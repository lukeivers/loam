"""Diff-classifier accuracy aggregate test.

Per master plan §7.1 + plan-doc §4 AC.WATCH.2 + §10 F2 RF #1:
classifier accuracy ≥90% on a synthetic test set spanning all 3
classifications (still-current / out-of-date / orphaned) and the 4
drift shapes (line-edit / file-rename / file-delete / refactor-move).

Halt-trigger: <90% accuracy → AST-aware extension required.

The test set is built programmatically (10+ pairs) so it stays
co-located with the test file rather than living as on-disk
fixtures.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from loam_odd_extractor.diff_classifier import classify_evidence

from _incremental_helpers import (  # type: ignore[import-not-found]
    commit_changes,
    init_git_repo,
    make_hypothesised_ac,
    make_plausible_ac,
)


Expected = Literal["still_current", "out_of_date", "orphaned"]


@dataclass(frozen=True)
class _Case:
    name: str
    setup_files: dict[str, str]
    drift_files: dict[str, str | None]  # None = delete
    backing_files: list[str]
    citations: list[str]
    contract_created_at: str
    expected: Expected


def _build_cases(tmp_path: Path) -> list[tuple[_Case, Path]]:
    """Build 10 synthetic prior-contract + repo-state pairs.

    Returns a list of (case, repo_path) tuples; each repo_path is a
    fresh tmp git-repo seeded per the case definition.
    """
    cases: list[_Case] = [
        _Case(
            name="01-no-drift",
            setup_files={"a.py": "print(1)\n"},
            drift_files={},
            backing_files=["a.py"],
            citations=["a.py:1-1"],
            # created_at AFTER any commit → still_current.
            contract_created_at="2099-01-01T00:00:00+00:00",
            expected="still_current",
        ),
        _Case(
            name="02-single-line-edit",
            setup_files={"app/payment/charge.rb": "code1\nline2\nline3\n"},
            drift_files={
                "app/payment/charge.rb": "code1\nline2_modified\nline3\n"
            },
            backing_files=["app/payment/charge.rb"],
            citations=["app/payment/charge.rb:1-3"],
            contract_created_at="2020-01-01T00:00:00+00:00",
            expected="out_of_date",
        ),
        _Case(
            name="03-file-rename",
            setup_files={"app/old_name.rb": "code\n"},
            drift_files={
                "app/old_name.rb": None,
                "app/new_name.rb": "code\n",
            },
            backing_files=["app/old_name.rb"],
            citations=["app/old_name.rb:1-1"],
            contract_created_at="2020-01-01T00:00:00+00:00",
            expected="orphaned",
        ),
        _Case(
            name="04-file-delete",
            setup_files={"app/legacy/old.rb": "old\n"},
            drift_files={"app/legacy/old.rb": None},
            backing_files=["app/legacy/old.rb"],
            citations=["app/legacy/old.rb:1-1"],
            contract_created_at="2020-01-01T00:00:00+00:00",
            expected="orphaned",
        ),
        _Case(
            name="05-refactor-move",
            setup_files={
                "app/util.rb": (
                    "def a\n  1\nend\n\ndef b\n  2\nend\n"
                )
            },
            drift_files={
                "app/util.rb": (
                    "def b\n  2\nend\n\ndef a\n  1\nend\n"
                )
            },
            backing_files=["app/util.rb"],
            citations=["app/util.rb:1-3"],
            contract_created_at="2020-01-01T00:00:00+00:00",
            expected="out_of_date",  # accepts false-positive on refactor (RF #1)
        ),
        _Case(
            name="06-whitespace-only",
            setup_files={"app/x.rb": "code\n"},
            drift_files={"app/x.rb": "code\n\n"},  # added blank line
            backing_files=["app/x.rb"],
            citations=["app/x.rb:1-1"],
            contract_created_at="2020-01-01T00:00:00+00:00",
            expected="out_of_date",  # whitespace counts as drift (RF #4)
        ),
        _Case(
            name="07-comment-only",
            setup_files={"app/y.rb": "code\n"},
            drift_files={"app/y.rb": "code # added comment\n"},
            backing_files=["app/y.rb"],
            citations=["app/y.rb:1-1"],
            contract_created_at="2020-01-01T00:00:00+00:00",
            expected="out_of_date",
        ),
        _Case(
            name="08-no-drift-multi-file",
            setup_files={
                "app/a.rb": "code_a\n",
                "app/b.rb": "code_b\n",
            },
            drift_files={},
            backing_files=["app/a.rb", "app/b.rb"],
            citations=["app/a.rb:1-1", "app/b.rb:1-1"],
            contract_created_at="2099-01-01T00:00:00+00:00",
            expected="still_current",
        ),
        _Case(
            name="09-orphaned-with-new-file",
            setup_files={"app/old.rb": "old\n"},
            drift_files={
                "app/old.rb": None,
                "app/new.rb": "new\n",
            },
            backing_files=["app/old.rb"],
            citations=["app/old.rb:1-1"],
            contract_created_at="2020-01-01T00:00:00+00:00",
            expected="orphaned",
        ),
        _Case(
            name="10-test-citation-stale",
            setup_files={
                "app/x.rb": "code\n",
                "tests/test_x.rb": "describe X\nend\n",
            },
            drift_files={},
            # Test-citation: classifier treats as file-existence
            # only; file unchanged → still_current.
            backing_files=["app/x.rb", "tests/test_x.rb"],
            citations=[
                "tests/test_x.rb::test_x",
                "app/x.rb:1-1",
            ],
            contract_created_at="2099-01-01T00:00:00+00:00",
            expected="still_current",
        ),
    ]
    out: list[tuple[_Case, Path]] = []
    for case in cases:
        case_repo = tmp_path / case.name
        init_git_repo(case_repo, files=case.setup_files)
        if case.drift_files:
            commit_changes(
                case_repo, files=case.drift_files, message="evolve"
            )
        out.append((case, case_repo))
    return out


def _classify_one(case: _Case, repo: Path) -> Expected:
    ac = make_plausible_ac(
        ac_id="AC.MIX.1",
        backing_files=case.backing_files,
        citations=case.citations,
    )
    classification = classify_evidence(
        prior_acs=[ac],
        repo_path=repo,
        contract_created_at=case.contract_created_at,
    )
    if classification.orphaned_count >= 1:
        return "orphaned"
    if classification.out_of_date_count >= 1:
        return "out_of_date"
    return "still_current"


def test_synthetic_test_set_at_least_10_cases(tmp_path: Path) -> None:
    """Per AC.WATCH.2 — synthetic test set has ≥10 cases."""
    cases = _build_cases(tmp_path)
    assert len(cases) >= 10


def test_classifier_accuracy_at_least_90_percent(
    tmp_path: Path,
) -> None:
    """Halt-trigger: <90% accuracy → AST-aware extension."""
    cases = _build_cases(tmp_path)
    correct = 0
    misclassified: list[tuple[str, Expected, Expected]] = []
    for case, repo in cases:
        actual = _classify_one(case, repo)
        if actual == case.expected:
            correct += 1
        else:
            misclassified.append((case.name, case.expected, actual))
    accuracy = correct / len(cases)
    msg = (
        f"accuracy={accuracy:.2%} ({correct}/{len(cases)}); "
        f"misclassified={misclassified}"
    )
    assert accuracy >= 0.90, msg


def test_each_classification_bucket_exercised(
    tmp_path: Path,
) -> None:
    """Test set covers all 3 classifications + 4 drift shapes."""
    cases = _build_cases(tmp_path)
    expected_buckets = {c.expected for c, _ in cases}
    assert expected_buckets == {
        "still_current",
        "out_of_date",
        "orphaned",
    }


def test_classifier_deterministic_across_runs(
    tmp_path: Path,
) -> None:
    """Run the entire test set twice; same results both times."""
    cases1 = _build_cases(tmp_path / "run1")
    cases2 = _build_cases(tmp_path / "run2")
    actuals1 = [_classify_one(c, r) for c, r in cases1]
    actuals2 = [_classify_one(c, r) for c, r in cases2]
    assert actuals1 == actuals2
