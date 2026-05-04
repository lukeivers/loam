"""AC.OREK.3 — Four-stage workflow with structured per-stage artefacts.

- Each stage is a pure function (input → output, no global state).
- Stage 1 (init) produces ExtractionConfig + writes config.yaml.
- Stage 2 (analyze) produces AnalysisPlan + writes plan.yaml.
- Stage 3 (generate) produces RawACs + writes raw-acs.yaml.
- Stage 4 (verify) produces ContractDraft + writes contract-draft.{md,yaml}.
- Each stage is invocable independently (--stage flag).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    AnalysisPlan,
    ContractDraft,
    ExtractionConfig,
    RawACs,
    analyze_repo,
    default_budget,
    generate_raw_acs,
    init_extraction,
    verify_contract,
)
from loam_odd_extractor.cli import main as cli_main


FIXED_TS = "2026-05-04T12:00:00+00:00"


def test_stage_1_init_produces_config(
    fixture_repo: Path, workspace_root: Path
) -> None:
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    assert isinstance(config, ExtractionConfig)
    assert config.repo_path == fixture_repo.resolve()
    assert config.dry_run is True
    assert config.created_at == FIXED_TS
    config_path = (
        workspace_root.resolve()
        / ".loam"
        / "extractions"
        / config.repo_id
        / "config.yaml"
    )
    assert config_path.exists()
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert data["repo_id"] == config.repo_id


def test_stage_2_analyze_produces_plan(
    fixture_repo: Path, workspace_root: Path
) -> None:
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    plan = analyze_repo(config=config, timestamp=FIXED_TS)
    assert isinstance(plan, AnalysisPlan)
    assert plan.extraction_id == config.repo_id
    # Cycle 1: zero adapters → all paths in unhandled_paths.
    assert plan.slices == []
    assert len(plan.unhandled_paths) >= 1  # README + main.py + lib.py
    # .git and __pycache__ should be skipped.
    for p in plan.unhandled_paths:
        assert ".git" not in p.parts
        assert "__pycache__" not in p.parts
    plan_path = (
        workspace_root.resolve()
        / ".loam"
        / "extractions"
        / config.repo_id
        / "plan.yaml"
    )
    assert plan_path.exists()


def test_stage_3_generate_produces_raw_acs(
    fixture_repo: Path, workspace_root: Path
) -> None:
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    plan = analyze_repo(config=config, timestamp=FIXED_TS)
    raw = generate_raw_acs(config=config, plan=plan, timestamp=FIXED_TS)
    assert isinstance(raw, RawACs)
    assert raw.acs == []  # zero adapters
    # unhandled_paths carried forward from plan
    assert len(raw.unhandled_paths) == len(plan.unhandled_paths)
    raw_path = (
        workspace_root.resolve()
        / ".loam"
        / "extractions"
        / config.repo_id
        / "raw-acs.yaml"
    )
    assert raw_path.exists()


def test_stage_4_verify_produces_contract_draft(
    fixture_repo: Path, workspace_root: Path
) -> None:
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    plan = analyze_repo(config=config, timestamp=FIXED_TS)
    raw = generate_raw_acs(config=config, plan=plan, timestamp=FIXED_TS)
    draft = verify_contract(config=config, raw=raw, timestamp=FIXED_TS)
    assert isinstance(draft, ContractDraft)
    assert draft.ac_count == 0
    assert draft.unhandled_count == len(raw.unhandled_paths)
    assert draft.markdown_path.exists()
    assert draft.sidecar_path.exists()
    md_text = draft.markdown_path.read_text(encoding="utf-8")
    # Required markdown anchors per F2 RF gap #3.
    assert "<!-- ACS_TABLE_HERE -->" in md_text
    assert "<!-- COVERAGE_GAPS_HERE -->" in md_text
    assert "DRAFT" in md_text


def test_stages_invocable_independently_via_cli(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """--stage init / --stage analyze / etc. each run only one stage."""
    rc = cli_main(
        [
            str(fixture_repo),
            "--workspace-root",
            str(workspace_root),
            "--stage",
            "init",
        ]
    )
    assert rc == 0
    repo_id_dir = next(
        (workspace_root / ".loam" / "extractions").iterdir()
    )
    # Only config.yaml should land at this point.
    assert (repo_id_dir / "config.yaml").exists()
    assert not (repo_id_dir / "plan.yaml").exists()

    rc = cli_main(
        [
            str(fixture_repo),
            "--workspace-root",
            str(workspace_root),
            "--stage",
            "analyze",
        ]
    )
    assert rc == 0
    assert (repo_id_dir / "plan.yaml").exists()
    assert not (repo_id_dir / "raw-acs.yaml").exists()


def test_stages_are_pure_no_global_state(
    fixture_repo: Path, workspace_root: Path, tmp_path: Path
) -> None:
    """Running stage functions twice with fresh inputs produces
    independent outputs in independent workspaces — no shared state."""
    other_workspace = tmp_path / "other-workspace"
    other_workspace.mkdir()

    config_a = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    config_b = init_extraction(
        repo_path=fixture_repo,
        workspace_root=other_workspace,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    # Same repo_id (same source path) but different workspace roots.
    assert config_a.repo_id == config_b.repo_id
    assert config_a.workspace_root != config_b.workspace_root
    # Both config.yaml files exist independently.
    assert (
        workspace_root.resolve()
        / ".loam"
        / "extractions"
        / config_a.repo_id
        / "config.yaml"
    ).exists()
    assert (
        other_workspace.resolve()
        / ".loam"
        / "extractions"
        / config_b.repo_id
        / "config.yaml"
    ).exists()
