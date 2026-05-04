"""AC.PRSI.7 — Provenance-traceable PR description template installer
+ render_pr_description gate-mode rendering."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_odd_extractor.bands import (
    BandedAC,
    ConfidenceBand,
    Evidence,
)

from loam_pr_safety.installers import (
    InstallConflictError,
    install_pr_template,
    render_pr_description,
)
from loam_pr_safety.spec import (
    CandidateAC,
    GateAction,
    GateDecision,
    Hunk,
    TouchedAC,
)


def _setup_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    return repo


def _setup_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / ".loam").mkdir()
    return ws


def test_install_creates_pr_template(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)

    result = install_pr_template(repo, workspace_root=ws)
    assert result.action == "created"
    canonical = repo / ".github" / "pull_request_template.md"
    secondary = repo / ".loam" / "pr-safety" / "pr_description.template.md"
    assert canonical.exists()
    assert secondary.exists()
    content = canonical.read_text(encoding="utf-8")
    assert "loam-pr-safety:managed:" in content
    assert "{{LOAM_PR_SAFETY_GATE_DECISION}}" in content
    assert "{{LOAM_PR_SAFETY_TOUCHED_ACS}}" in content


def test_install_pr_template_idempotent(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    r1 = install_pr_template(repo, workspace_root=ws)
    r2 = install_pr_template(repo, workspace_root=ws)
    assert r1.action == "created"
    assert r2.action == "noop"


def test_install_pr_template_halts_on_conflict(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".github" / "pull_request_template.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "## Existing template\n\nLeftover content.\n",
        encoding="utf-8",
    )

    with pytest.raises(InstallConflictError):
        install_pr_template(repo, workspace_root=ws)


def test_install_pr_template_force_replaces(tmp_path: Path) -> None:
    repo = _setup_repo(tmp_path)
    ws = _setup_workspace(tmp_path)
    target = repo / ".github" / "pull_request_template.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Existing\n", encoding="utf-8")

    r = install_pr_template(repo, workspace_root=ws, force=True)
    assert r.action == "force-replaced"
    assert r.backup_path is not None
    assert r.backup_path.exists()


def _build_synth_decision(
    bands: list[ConfidenceBand],
    *,
    novel_count: int = 0,
) -> GateDecision:
    """Build a synthetic GateDecision for render testing."""
    touched: list[TouchedAC] = []
    for i, band in enumerate(bands):
        # BandedAC's per-band evidence rules:
        # VERIFIED → kind='test' + repo_sha required.
        # PLAUSIBLE → kind='source' acceptable.
        # HYPOTHESISED → kind='inference' + rationale required.
        if band is ConfidenceBand.VERIFIED:
            evidence = Evidence(
                kind="test",
                citations=[
                    f"tests/test_synth_{i}.py::test_synth_{i + 1}",
                ],
                repo_sha="abc1234567890def",
                rationale=None,
            )
        elif band is ConfidenceBand.HYPOTHESISED:
            evidence = Evidence(
                kind="inference",
                citations=[],
                repo_sha=None,
                rationale=f"Inferred {i}",
            )
        else:
            evidence = Evidence(
                kind="source",
                citations=[f"src/file{i}.py:10-20"],
                repo_sha=None,
                rationale=None,
            )
        ac = BandedAC(
            ac_id=f"AC.SYNTH.{i + 1}",
            text=f"Synthetic AC {i + 1} description with provenance",
            confidence=band,
            evidence=evidence,
            backing_files=[f"src/file{i}.py"],
        )
        touched.append(
            TouchedAC(ac=ac, touch_kind="citation_line", touched_hunks=[])
        )
    novel = [
        CandidateAC(
            file_path=Path(f"src/novel{i}.py"),
            hunks=[
                Hunk(
                    old_start=1,
                    old_lines=0,
                    new_start=1,
                    new_lines=5,
                    added_lines=[f"line{j}" for j in range(5)],
                    removed_lines=[],
                )
            ],
        )
        for i in range(novel_count)
    ]
    return GateDecision(
        action=GateAction.HARD_BLOCK
        if any(b is ConfidenceBand.VERIFIED for b in bands)
        else GateAction.SURFACE_DECISION,
        requires_ratification=True,
        touched_acs=touched,
        novel=novel,
        safety_profile="dev",
        reason="synthetic test decision",
    )


def test_render_basic_decision(tmp_path: Path) -> None:
    ws = _setup_workspace(tmp_path)
    decision = _build_synth_decision(
        [ConfidenceBand.VERIFIED, ConfidenceBand.PLAUSIBLE]
    )

    md = render_pr_description(
        decision, workspace_root=ws, repo_id="some-repo-id"
    )

    assert "Gate decision: HARD_BLOCK" in md
    assert "ACs touched (2)" in md
    assert "AC.SYNTH.1" in md
    assert "AC.SYNTH.2" in md
    # Sections present.
    assert "ACs touched" in md
    assert "Audit-log excerpt" in md


def test_render_with_novel_candidates(tmp_path: Path) -> None:
    ws = _setup_workspace(tmp_path)
    decision = _build_synth_decision(
        [ConfidenceBand.PLAUSIBLE], novel_count=2
    )

    md = render_pr_description(
        decision, workspace_root=ws, repo_id="some-repo-id"
    )

    assert "Novel candidates (2)" in md
    assert "src/novel0.py" in md


def test_render_with_audit_log_entries(tmp_path: Path) -> None:
    ws = _setup_workspace(tmp_path)
    # Plant an audit-log entry for this repo-id.
    audit_dir = ws / ".loam" / "pr-safety" / "audit-log"
    audit_dir.mkdir(parents=True, exist_ok=True)
    (audit_dir / "2026-05-04-0001.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "event_kind": "gate_decision",
                "timestamp": "2026-05-04T12:00:00+00:00",
                "repo_id": "some-repo-id",
                "repo_sha": "abc123",
                "diff_range": "x..y",
                "safety_profile": "dev",
                "decision": "HARD_BLOCK",
                "requires_ratification": True,
                "touched_acs": ["AC.X.1"],
                "novel_count": 0,
                "reason": "test",
                "owner": None,
                "rationale": None,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    decision = _build_synth_decision([ConfidenceBand.VERIFIED])
    md = render_pr_description(
        decision, workspace_root=ws, repo_id="some-repo-id"
    )

    assert "2026-05-04-0001.yaml" in md
    assert "gate_decision" in md


def test_render_with_override_history(tmp_path: Path) -> None:
    ws = _setup_workspace(tmp_path)
    # Plant an override overlay.
    od = ws / ".loam" / "pr-safety" / "contract-overrides" / "some-repo-id"
    od.mkdir(parents=True, exist_ok=True)
    (od / "override-1.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "kind": "replace_verified",
                "original_ac_id": "AC.OLD.1",
                "rationale": "Necessary refactor",
                "owner": "luke <l@x.com>",
                "commit_sha": "abcdef0123",
                "repo_sha": "deadbeef",
                "applied_at": "2026-05-04T12:00:00+00:00",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    decision = _build_synth_decision([ConfidenceBand.PLAUSIBLE])
    md = render_pr_description(
        decision, workspace_root=ws, repo_id="some-repo-id"
    )

    assert "Override history (1)" in md
    assert "AC.OLD.1" in md
    assert "Necessary refactor" in md
    assert "abcdef01" in md  # truncated commit SHA
