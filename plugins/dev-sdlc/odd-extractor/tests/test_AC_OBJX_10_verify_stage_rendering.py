"""AC.OBJX.10 — Output schema reshape (verify-stage rendering).

- ``contract-draft.md`` contains all altitude sections (Objectives,
  Constraints, Capabilities, Evidence rows, §self-checks audit).
- ``contract-draft.yaml`` carries typed lists (objectives,
  constraints, capabilities) AND legacy ``acs:`` field.
- Cross-reference validation: dangling ``Capability.serves`` raises
  StageError.
- §self-checks audit table appears in the rendered markdown.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam_odd_extractor import (
    AnalysisPlan,
    Capability,
    CapabilityEvidence,
    ConfidenceBand,
    Constraint,
    ConstraintEvidence,
    Objective,
    ObjectiveEvidence,
    StageError,
    SynthesisResult,
    default_budget,
    extraction_dir,
    generate_raw_acs,
    init_extraction,
    verify_contract,
)


FIXED_TS = "2026-05-04T12:00:00+00:00"


def _bare_synthesis(repo_id: str) -> SynthesisResult:
    return SynthesisResult(
        extraction_id=repo_id,
        objectives=[
            Objective(
                objective_id="O.dispute-flow.1",
                text=(
                    "Operators file refund disputes against merchant "
                    "portals at scale, replacing manual portal clickwork."
                ),
                confidence=ConfidenceBand.PLAUSIBLE,
                domain="dispute-flow",
                evidence=ObjectiveEvidence(
                    readme_excerpts=["files refunds at scale"],
                ),
            )
        ],
        constraints=[
            Constraint(
                constraint_id="K.compliance.1",
                text="System satisfies SOC-2 audit-trail floor",
                bounds_kind="compliance",
                evidence=ConstraintEvidence(readme_excerpts=["soc2"]),
            )
        ],
        capabilities=[
            Capability(
                capability_id="C.csv-upload.1",
                text="CSV upload + validation pipeline",
                serves=["O.dispute-flow.1"],
                evidence=CapabilityEvidence(readme_excerpts=["csv"]),
            )
        ],
        created_at=FIXED_TS,
    )


def _setup(fixture_repo, workspace_root):
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    plan = AnalysisPlan(
        extraction_id=config.repo_id,
        slices=[],
        unhandled_paths=[],
        created_at=FIXED_TS,
    )
    raw = generate_raw_acs(config=config, plan=plan, timestamp=FIXED_TS)
    return config, raw


def test_verify_renders_all_altitude_sections(
    fixture_repo: Path, workspace_root: Path
) -> None:
    config, raw = _setup(fixture_repo, workspace_root)
    synthesis = _bare_synthesis(config.repo_id)
    verify_contract(
        config=config, raw=raw, synthesis=synthesis, timestamp=FIXED_TS
    )
    ext_dir = extraction_dir(workspace_root, config.repo_id)
    md = (ext_dir / "contract-draft.md").read_text(encoding="utf-8")
    assert "## Objectives" in md
    assert "## Constraints" in md
    assert "## Capabilities" in md
    assert "## Evidence rows" in md
    assert "§self-checks audit" in md


def test_sidecar_carries_typed_lists_and_legacy_acs(
    fixture_repo: Path, workspace_root: Path
) -> None:
    config, raw = _setup(fixture_repo, workspace_root)
    synthesis = _bare_synthesis(config.repo_id)
    verify_contract(
        config=config, raw=raw, synthesis=synthesis, timestamp=FIXED_TS
    )
    ext_dir = extraction_dir(workspace_root, config.repo_id)
    sidecar = yaml.safe_load(
        (ext_dir / "contract-draft.yaml").read_text(encoding="utf-8")
    )
    assert "objectives" in sidecar
    assert "constraints" in sidecar
    assert "capabilities" in sidecar
    assert "acs" in sidecar  # legacy compat
    assert len(sidecar["objectives"]) == 1
    assert len(sidecar["constraints"]) == 1
    assert len(sidecar["capabilities"]) == 1
    assert len(sidecar["acs"]) == 1


def test_dangling_capability_reference_raises_stage_error(
    fixture_repo: Path, workspace_root: Path
) -> None:
    config, raw = _setup(fixture_repo, workspace_root)
    # Synthesis with capability whose serves doesn't resolve.
    synthesis = SynthesisResult(
        extraction_id=config.repo_id,
        objectives=[
            Objective(
                objective_id="O.dispute-flow.1",
                text=(
                    "Operators file refund disputes against merchant "
                    "portals at scale."
                ),
                confidence=ConfidenceBand.PLAUSIBLE,
                domain="dispute-flow",
                evidence=ObjectiveEvidence(readme_excerpts=["x"]),
            )
        ],
        capabilities=[
            Capability(
                capability_id="C.csv-upload.1",
                text="x",
                serves=["O.does-not-exist.1"],
                evidence=CapabilityEvidence(readme_excerpts=["x"]),
            )
        ],
        created_at=FIXED_TS,
    )
    with pytest.raises(StageError) as exc:
        verify_contract(
            config=config, raw=raw, synthesis=synthesis, timestamp=FIXED_TS
        )
    assert "unknown objective" in str(exc.value)


def test_self_checks_audit_table_rendered(
    fixture_repo: Path, workspace_root: Path
) -> None:
    config, raw = _setup(fixture_repo, workspace_root)
    synthesis = _bare_synthesis(config.repo_id)
    verify_contract(
        config=config, raw=raw, synthesis=synthesis, timestamp=FIXED_TS
    )
    ext_dir = extraction_dir(workspace_root, config.repo_id)
    md = (ext_dir / "contract-draft.md").read_text(encoding="utf-8")
    # Audit table headers.
    assert "row_id" in md and "classification" in md and "decision" in md


def test_altitude_report_persisted_in_sidecar(
    fixture_repo: Path, workspace_root: Path
) -> None:
    config, raw = _setup(fixture_repo, workspace_root)
    synthesis = _bare_synthesis(config.repo_id)
    verify_contract(
        config=config, raw=raw, synthesis=synthesis, timestamp=FIXED_TS
    )
    ext_dir = extraction_dir(workspace_root, config.repo_id)
    sidecar = yaml.safe_load(
        (ext_dir / "contract-draft.yaml").read_text(encoding="utf-8")
    )
    assert "altitude_report" in sidecar
    rep = sidecar["altitude_report"]
    assert rep["total_rows"] == 3  # 1 obj + 1 cstr + 1 cap
