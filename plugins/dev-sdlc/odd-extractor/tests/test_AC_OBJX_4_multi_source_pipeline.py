"""AC.OBJX.4 — Multi-source input pipeline.

- README-rich / README-thin / README-absent fixture variants
  populate the bundle correctly.
- Survey present/absent variants flow through.
- README cap (50KB) truncates with marker.
- Test assertions filtered from adapter rows by evidence kind.
- Code patterns gathered from non-test adapter rows.
- Token estimate populated.
"""

from __future__ import annotations

from pathlib import Path

from loam_odd_extractor import collect_multi_source_inputs


def _stub_evidence_rows() -> list[dict]:
    return [
        {
            "ac_id": "AC.RUBY.1",
            "text": "tests dispute filing flow",
            "confidence": "VERIFIED",
            "evidence": {
                "kind": "test",
                "citations": ["spec/disputes_spec.rb::it files disputes"],
                "repo_sha": "abc1234",
            },
            "backing_files": [],
        },
        {
            "ac_id": "AC.JSTS.1",
            "text": "Express GET /disputes route",
            "confidence": "PLAUSIBLE",
            "evidence": {
                "kind": "source",
                "citations": ["src/routes/disputes.js:42"],
            },
            "backing_files": [],
        },
        {
            "ac_id": "AC.RUBY.2",
            "text": "Inferred dispute domain",
            "confidence": "HYPOTHESISED",
            "evidence": {
                "kind": "inference",
                "rationale": "rails-shape pattern",
                "citations": [],
            },
            "backing_files": [],
        },
    ]


def test_readme_rich_fixture_populates_bundle(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text(
        "# DisputeApp\n\nFile refund disputes at scale against merchant portals.",
        encoding="utf-8",
    )
    docs = repo / "docs"
    docs.mkdir()
    (docs / "architecture.md").write_text(
        "# Architecture\n\nServerless dispute pipeline.",
        encoding="utf-8",
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    bundle = collect_multi_source_inputs(
        repo,
        workspace,
        repo_id="r1",
        evidence_rows=_stub_evidence_rows(),
    )
    assert bundle.readme_text is not None
    assert "DisputeApp" in bundle.readme_text
    assert bundle.readme_truncated is False
    assert len(bundle.design_docs) == 1
    assert bundle.design_docs[0]["heading"] == "Architecture"
    assert len(bundle.test_assertions) == 1
    assert bundle.test_assertions[0]["ac_id"] == "AC.RUBY.1"
    assert len(bundle.code_patterns) == 2
    assert bundle.total_token_estimate > 0


def test_readme_thin_fixture(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("# Tiny\n", encoding="utf-8")
    workspace = tmp_path / "ws"
    workspace.mkdir()
    bundle = collect_multi_source_inputs(
        repo, workspace, repo_id="r1", evidence_rows=_stub_evidence_rows()
    )
    assert bundle.readme_text is not None
    assert bundle.readme_truncated is False
    assert bundle.design_docs == []


def test_readme_absent_fixture(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    workspace = tmp_path / "ws"
    workspace.mkdir()
    bundle = collect_multi_source_inputs(
        repo, workspace, repo_id="r1", evidence_rows=[]
    )
    assert bundle.readme_text is None
    assert bundle.readme_truncated is False
    assert bundle.design_docs == []


def test_readme_oversized_truncated_with_marker(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    big = "x" * (60 * 1024)  # 60KB
    (repo / "README.md").write_text(big, encoding="utf-8")
    workspace = tmp_path / "ws"
    workspace.mkdir()
    bundle = collect_multi_source_inputs(
        repo, workspace, repo_id="r1", evidence_rows=[]
    )
    assert bundle.readme_truncated is True
    assert bundle.readme_text is not None
    assert "truncated" in bundle.readme_text.lower()


def test_design_doc_file_cap(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    docs = repo / "docs"
    docs.mkdir()
    # Drop 25 design docs; cap is 20.
    for i in range(25):
        (docs / f"d{i:02d}.md").write_text(
            f"# Doc {i}\n", encoding="utf-8"
        )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    bundle = collect_multi_source_inputs(
        repo, workspace, repo_id="r1", evidence_rows=[]
    )
    assert len(bundle.design_docs) == 20


def test_evidence_rows_partition_into_tests_and_code_patterns(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    workspace = tmp_path / "ws"
    workspace.mkdir()
    bundle = collect_multi_source_inputs(
        repo, workspace, repo_id="r1",
        evidence_rows=_stub_evidence_rows(),
    )
    assert len(bundle.test_assertions) == 1
    assert len(bundle.code_patterns) == 2
    # Code patterns include both source + inference kinds.
    kinds = {c["evidence_kind"] for c in bundle.code_patterns}
    assert kinds == {"source", "inference"}


def test_survey_absent_returns_none(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("LOAM_ONBOARDING_SURVEY", raising=False)
    repo = tmp_path / "repo"
    repo.mkdir()
    workspace = tmp_path / "ws"
    workspace.mkdir()
    # Use a redirect for HOME to avoid the real ~/loam-onboarding-survey.md
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    bundle = collect_multi_source_inputs(
        repo, workspace, repo_id="r1", evidence_rows=[]
    )
    assert bundle.user_survey is None or bundle.user_survey.get(
        "raw_text", ""
    ) == ""


def test_survey_workspace_local_takes_precedence(
    tmp_path: Path, monkeypatch
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    loam_dir = repo / ".loam"
    loam_dir.mkdir()
    survey = loam_dir / "onboarding-survey.md"
    survey.write_text(
        "# Survey\n\n## 1. Language\nRuby/Rails\n", encoding="utf-8"
    )
    workspace = tmp_path / "ws"
    workspace.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "fake-home"))
    bundle = collect_multi_source_inputs(
        repo, workspace, repo_id="r1", evidence_rows=[]
    )
    assert bundle.user_survey is not None
    assert "Ruby" in bundle.user_survey["raw_text"]
