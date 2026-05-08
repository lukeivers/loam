"""AC.WATCHOBJ.1 — diff_classifier consults backing-map at objective altitude.

Per v0.2.3 Cycle 3 sub-plan-doc §3 AC.WATCHOBJ.1.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.diff_classifier import (
    EvidenceClassification,
    OrphanedObjective,
    OutOfDateObjective,
    classify_evidence,
)
from loam_odd_extractor.spec import (
    BackingMap,
    BackingMapEntry,
    EvidenceRowRef,
    Objective,
    ObjectiveEvidence,
)


def _make_objective(repo_sha: str | None = None) -> Objective:
    return Objective(
        objective_id="O.auth.1",
        text="Operators authenticate with password length validation enforced.",
        confidence=ConfidenceBand.VERIFIED if repo_sha else ConfidenceBand.PLAUSIBLE,
        domain="auth",
        evidence=ObjectiveEvidence(
            readme_excerpts=["Auth supports password length"],
            test_name_refs=["tests/test_auth.py::test_password_length"]
            if repo_sha
            else [],
            design_doc_refs=[] if repo_sha else ["docs/auth.md"],
            repo_sha=repo_sha,
        ),
    )


def _make_backing_map(
    objective_id: str, path: str, line_range: tuple[int, int] | None
) -> BackingMap:
    rows = [
        EvidenceRowRef(
            evidence_row_id=f"route:{path}:1",
            kind="route",
            path=path,
            line_range=line_range,
        )
    ]
    return BackingMap(
        extraction_id="test",
        entries=[
            BackingMapEntry(
                objective_id=objective_id,
                evidence_rows=rows,
                match_rationale="test",
            )
        ],
        orphan_rows=[],
        created_at="2026-05-04T00:00:00+00:00",
    )


def _git_init(repo_path: Path) -> None:
    subprocess.run(["git", "-C", str(repo_path), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(repo_path), "config", "user.email", "test@example.com"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_path), "config", "user.name", "Test"],
        check=True,
    )


def _git_commit(repo_path: Path, msg: str) -> str:
    subprocess.run(["git", "-C", str(repo_path), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(repo_path), "commit", "-q", "-m", msg],
        check=True,
    )
    proc = subprocess.run(
        ["git", "-C", str(repo_path), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout.strip()


def test_orphan_when_evidence_row_path_missing(tmp_path: Path):
    """Backing-row path missing on disk → OrphanedObjective."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    (repo / "README.md").write_text("# repo\n")
    _git_commit(repo, "init")

    obj = _make_objective(repo_sha="abc")
    bm = _make_backing_map("O.auth.1", "missing/file.py", (1, 10))
    result = classify_evidence(
        prior_objectives=[obj],
        prior_backing_map=bm,
        repo_path=repo,
        contract_created_at="2026-01-01T00:00:00+00:00",
    )
    assert isinstance(result, EvidenceClassification)
    assert result.orphaned_count == 1
    assert isinstance(result.orphaned[0], OrphanedObjective)
    assert result.orphaned[0].objective.objective_id == "O.auth.1"


def test_still_current_when_no_changes(tmp_path: Path):
    """No drift → still_current."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    (repo / "auth.py").write_text("def f():\n    return 1\n")
    sha = _git_commit(repo, "init")

    obj = _make_objective(repo_sha=sha)
    bm = _make_backing_map("O.auth.1", "auth.py", (1, 2))
    result = classify_evidence(
        prior_objectives=[obj],
        prior_backing_map=bm,
        repo_path=repo,
        contract_created_at="2099-01-01T00:00:00+00:00",  # future → no commits since
    )
    assert result.still_current_count == 1
    assert result.out_of_date_count == 0
    assert result.orphaned_count == 0


def test_out_of_date_when_line_range_changed(tmp_path: Path):
    """Backing-row line_range modified between SHAs → out_of_date."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    (repo / "auth.py").write_text("def f():\n    return 1\n")
    prior_sha = _git_commit(repo, "init")

    # Modify lines in the range.
    (repo / "auth.py").write_text("def f():\n    return 'changed'\n")
    _git_commit(repo, "modify f")

    obj = _make_objective(repo_sha=prior_sha)
    bm = _make_backing_map("O.auth.1", "auth.py", (1, 2))
    result = classify_evidence(
        prior_objectives=[obj],
        prior_backing_map=bm,
        repo_path=repo,
        contract_created_at="2026-01-01T00:00:00+00:00",
    )
    assert result.out_of_date_count == 1
    ood = result.out_of_date[0]
    assert isinstance(ood, OutOfDateObjective)
    assert ood.drift_kind == "evidence_row_line_changed"
    assert ood.from_sha == prior_sha


def test_no_backing_rows_yields_still_current(tmp_path: Path):
    """HYPOTHESISED objective with empty backing-map entry → still_current."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git_init(repo)
    (repo / "README.md").write_text("# r\n")
    _git_commit(repo, "init")

    obj = Objective(
        objective_id="O.payments.1",
        text="Operators retry failed charges with exponential backoff.",
        confidence=ConfidenceBand.HYPOTHESISED,
        domain="payments",
        evidence=ObjectiveEvidence(
            rationale="Inferred from comments."
        ),
    )
    bm = BackingMap(
        extraction_id="t",
        entries=[
            BackingMapEntry(
                objective_id="O.payments.1",
                evidence_rows=[],
                match_rationale="(none)",
            )
        ],
        orphan_rows=[],
        created_at="2026-05-04T00:00:00+00:00",
    )
    result = classify_evidence(
        prior_objectives=[obj],
        prior_backing_map=bm,
        repo_path=repo,
        contract_created_at="2026-01-01T00:00:00+00:00",
    )
    assert result.still_current_count == 1
