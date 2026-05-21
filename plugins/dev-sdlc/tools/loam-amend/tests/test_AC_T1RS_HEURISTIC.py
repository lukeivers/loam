"""AC.T1RS.HEURISTIC.{1,2,3,4} — tightened three-strategy seal-commit
attribution heuristic.

Per amendment #143 Scope A + §14 D-T1RS.HEURISTIC: the existing
narrow ``--grep=^chore(seals): --grep=<slug> --all-match`` strategy
misses sealed plan-docs whose seal-commit subject names a different
slug than the plan-doc filename. Three-strategy fallback chain
(narrow / body / amendment-n) recovers ~13 plan-docs at canonical
HEAD. Ambiguous + no-signal cases preserve the §134 halt-trigger #5
contract verbatim.

ACs verified here:
- AC.T1RS.HEURISTIC.1 — Strategy 2 recovers body-slug attribution
  (``amendment-22-foo.md`` + seal ``chore(seals): foo seal — ...``).
- AC.T1RS.HEURISTIC.2 — Strategy 2/3 recovers ``amendment #NN`` -style
  attribution.
- AC.T1RS.HEURISTIC.3 — no-signal plan-docs stay in-flight (negative
  case; §134 contract).
- AC.T1RS.HEURISTIC.4 — multi-match in ANY strategy → ambiguous
  bucket (§134 contract).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from loam_amend.plan_archive import (
    _find_seal_commit_for_slug,
    sweep_sealed_plan_docs,
)


def _git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=check,
    )


_MARKER_COUNTER = {"n": 0}


def _commit_seal_with_subject(repo: Path, subject: str) -> str:
    """Commit a fake seal commit with ``subject`` as the subject line.

    The subject line MUST start with ``chore(seals):`` for the
    heuristic to match. Different from
    ``test_AC_FBMT1_APS_3_retroactive_sweep._commit_seal``: that
    helper formats the message as ``chore(seals): <slug> ...`` —
    here we want full control over the subject.
    """
    _MARKER_COUNTER["n"] += 1
    n = _MARKER_COUNTER["n"]
    marker = repo / f".marker-{n}"
    marker.write_text(f"marker {n}\n", encoding="utf-8")
    _git(repo, "add", "--", str(marker.relative_to(repo)))
    _git(repo, "commit", "-m", subject)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.invalid")
    _git(repo, "config", "user.name", "test")
    plans = repo / "docs" / "plans"
    plans.mkdir(parents=True)
    return repo


def test_AC_T1RS_HEURISTIC_1_body_slug_strategy_recovers_pre134_attribution(
    tmp_path,
):
    """Strategy 2 (body-slug) recovers ``amendment-22-foo.md`` whose
    seal commit subject is ``chore(seals): foo seal — ...`` (body-
    slug-only attribution, no ``amendment-22-`` prefix).
    """
    repo = _init_repo(tmp_path)
    plans = repo / "docs" / "plans"
    (plans / "amendment-22-foo.md").write_text("# foo\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc seeded")
    # Seal commit attributes via body-slug only.
    _commit_seal_with_subject(
        repo, "chore(seals): foo seal — fixture body-slug-only"
    )

    # The narrow strategy alone returns empty (no ``amendment-22-foo``
    # in the seal subject). Strategy 2 picks it up.
    shas, strategy = _find_seal_commit_for_slug(repo, "amendment-22-foo")
    assert shas, "Strategy 2 must recover body-slug attribution"
    assert strategy == "body", f"expected strategy=body, got {strategy}"

    # The sweep moves it.
    result = sweep_sealed_plan_docs(repo)
    moved_names = {old.name for old, _ in result.moved}
    assert "amendment-22-foo.md" in moved_names
    assert "body" in result.moved_by_strategy
    assert "amendment-22-foo.md" in result.moved_by_strategy["body"]


def test_AC_T1RS_HEURISTIC_2_amendment_n_strategy_recovers_hash_attribution(
    tmp_path,
):
    """Strategy 3 (``amendment #NN``) recovers a plan-doc whose seal
    commit subject does NOT contain the slug body but DOES contain
    ``amendment #50``.
    """
    repo = _init_repo(tmp_path)
    plans = repo / "docs" / "plans"
    (plans / "amendment-50-bar.md").write_text("# bar\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc seeded")
    # Seal commit attributes via amendment-NN hash but NOT via
    # ``bar`` body-slug. Subject MUST start with ``chore(seals):``.
    _commit_seal_with_subject(
        repo,
        "chore(seals): something-unrelated seal — closes amendment #50",
    )

    # Narrow: no match. Body: no match (no ``bar`` in subject).
    # amendment-n: match.
    shas, strategy = _find_seal_commit_for_slug(repo, "amendment-50-bar")
    assert shas, "Strategy 3 must recover amendment-N attribution"
    assert strategy == "amendment-n", (
        f"expected strategy=amendment-n, got {strategy}"
    )

    result = sweep_sealed_plan_docs(repo)
    moved_names = {old.name for old, _ in result.moved}
    assert "amendment-50-bar.md" in moved_names
    assert "amendment-n" in result.moved_by_strategy
    assert "amendment-50-bar.md" in result.moved_by_strategy["amendment-n"]


def test_AC_T1RS_HEURISTIC_3_no_signal_stays_in_flight(tmp_path):
    """A plan-doc with NO matching commits in any strategy stays in
    ``docs/plans/`` (§134 halt-trigger #5 contract preserved)."""
    repo = _init_repo(tmp_path)
    plans = repo / "docs" / "plans"
    (plans / "amendment-99-untracked.md").write_text(
        "# untracked\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc seeded")
    # No seal commit created. Strategies all return empty.

    shas, strategy = _find_seal_commit_for_slug(
        repo, "amendment-99-untracked"
    )
    assert shas == [], "no strategy should match"
    assert strategy is None

    result = sweep_sealed_plan_docs(repo)
    moved_names = {old.name for old, _ in result.moved}
    in_flight_names = {p.name for p in result.in_flight}
    assert "amendment-99-untracked.md" not in moved_names
    assert "amendment-99-untracked.md" in in_flight_names
    # File still in docs/plans/.
    assert (repo / "docs" / "plans" / "amendment-99-untracked.md").exists()


def test_AC_T1RS_HEURISTIC_4_multi_match_in_strategy_stays_ambiguous(
    tmp_path,
):
    """Multi-match in ANY single strategy → ambiguous bucket; §134
    halt-trigger #5 contract preserved verbatim by amendment #143."""
    repo = _init_repo(tmp_path)
    plans = repo / "docs" / "plans"
    (plans / "amendment-77-multimatch.md").write_text(
        "# multimatch\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc seeded")
    # TWO seal commits attributing via body-slug — multi-match in
    # Strategy 2.
    _commit_seal_with_subject(
        repo, "chore(seals): multimatch seal — first attribution"
    )
    _commit_seal_with_subject(
        repo, "chore(seals): multimatch seal — second attribution"
    )

    shas, strategy = _find_seal_commit_for_slug(
        repo, "amendment-77-multimatch"
    )
    assert len(shas) == 2, f"expected 2 matches, got {len(shas)}"
    assert strategy == "body"

    result = sweep_sealed_plan_docs(repo)
    moved_names = {old.name for old, _ in result.moved}
    ambig_names = {p.name for p in result.ambiguous}
    assert "amendment-77-multimatch.md" not in moved_names
    assert "amendment-77-multimatch.md" in ambig_names
    # File still in docs/plans/.
    assert (
        repo / "docs" / "plans" / "amendment-77-multimatch.md"
    ).exists()


def test_AC_T1RS_HEURISTIC_builder_plan_companions_excluded(tmp_path):
    """D-T1RS.HEURISTIC.4: ``.builder-plan.md`` companions are
    filtered out of the sweep candidate set."""
    repo = _init_repo(tmp_path)
    plans = repo / "docs" / "plans"
    (plans / "amendment-44-baz.md").write_text("# baz\n", encoding="utf-8")
    (plans / "amendment-44-baz.builder-plan.md").write_text(
        "# baz builder\n", encoding="utf-8"
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "fixture: plan-doc + companion seeded")
    _commit_seal_with_subject(
        repo, "chore(seals): amendment-44-baz — full slug attribution"
    )

    result = sweep_sealed_plan_docs(repo)
    moved_names = {old.name for old, _ in result.moved}
    assert "amendment-44-baz.md" in moved_names
    # Companion is NOT in any bucket (filtered before classification).
    assert "amendment-44-baz.builder-plan.md" not in moved_names
    in_flight_names = {p.name for p in result.in_flight}
    assert "amendment-44-baz.builder-plan.md" not in in_flight_names
    ambig_names = {p.name for p in result.ambiguous}
    assert "amendment-44-baz.builder-plan.md" not in ambig_names
