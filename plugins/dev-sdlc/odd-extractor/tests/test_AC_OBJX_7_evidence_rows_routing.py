"""AC.OBJX.7 — Adapter-output reshape (evidence-rows routing).

- Generate stage writes ``evidence-rows.yaml`` with adapter rows.
- Generate stage also writes the legacy ``raw-acs.yaml`` alias (same
  content) for v0.1.9 PR-safety + v0.1.8 test substrate compat.
- ``contract-draft.yaml acs:`` carries typed ``Objective`` rows
  (NOT symbol-altitude evidence rows) when synthesis is present.
- ``contract-draft.yaml acs:`` falls back to evidence-rows shape
  when no synthesis is present (test path).
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor import (
    AnalysisPlan,
    ConfidenceBand,
    Capability,
    CapabilityEvidence,
    Objective,
    ObjectiveEvidence,
    Slice,
    SynthesisResult,
    default_budget,
    extraction_dir,
    generate_raw_acs,
    init_extraction,
    verify_contract,
)
from loam_odd_extractor.registry import (
    register_adapter,
)
from loam_odd_extractor.spec import RawACs


FIXED_TS = "2026-05-04T12:00:00+00:00"


class _StubAdapter:
    """A stub adapter that emits 3 BandedAC dicts for the slice."""

    name = "stub-jsts"
    extensions = (".js", ".ts")

    def supports(self, repo_path: Path) -> bool:
        return True

    def claim_paths(self, repo_path: Path):
        return [(repo_path / "src" / f"{n}.js") for n in ("a", "b", "c")]

    def extract(self, repo_path: Path, plan):
        return RawACs(
            extraction_id="x",
            acs=[
                {
                    "ac_id": "AC.STUB.1",
                    "text": "Express GET /a route",
                    "confidence": "PLAUSIBLE",
                    "evidence": {
                        "kind": "source",
                        "citations": ["src/a.js:1"],
                    },
                    "backing_files": ["src/a.js"],
                },
                {
                    "ac_id": "AC.STUB.2",
                    "text": "Express GET /b route",
                    "confidence": "PLAUSIBLE",
                    "evidence": {
                        "kind": "source",
                        "citations": ["src/b.js:1"],
                    },
                    "backing_files": ["src/b.js"],
                },
                {
                    "ac_id": "AC.STUB.3",
                    "text": "Express GET /c route",
                    "confidence": "PLAUSIBLE",
                    "evidence": {
                        "kind": "source",
                        "citations": ["src/c.js:1"],
                    },
                    "backing_files": ["src/c.js"],
                },
            ],
            unhandled_paths=[],
            per_slice_costs={},
            created_at=FIXED_TS,
        )


def test_evidence_rows_yaml_carries_adapter_output(
    fixture_repo: Path, workspace_root: Path
) -> None:
    register_adapter(_StubAdapter())

    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=False,
        timestamp=FIXED_TS,
    )
    plan = AnalysisPlan(
        extraction_id=config.repo_id,
        slices=[
            Slice(
                slice_id="s1",
                adapter_name="stub-jsts",
                paths=[],
            )
        ],
        unhandled_paths=[],
        created_at=FIXED_TS,
    )
    raw = generate_raw_acs(
        config=config, plan=plan, timestamp=FIXED_TS
    )

    ext_dir = extraction_dir(workspace_root, config.repo_id)
    evidence_path = ext_dir / "evidence-rows.yaml"
    assert evidence_path.exists(), (
        "AC.OBJX.7 — evidence-rows.yaml must exist"
    )
    payload = yaml.safe_load(evidence_path.read_text(encoding="utf-8"))
    assert len(payload["acs"]) == 3
    ac_ids = {row["ac_id"] for row in payload["acs"]}
    assert ac_ids == {"AC.STUB.1", "AC.STUB.2", "AC.STUB.3"}


def test_legacy_raw_acs_yaml_alias_preserved(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """v0.1.9 PR-safety + v0.1.8 substrate read raw-acs.yaml; we keep it."""
    register_adapter(_StubAdapter())

    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=False,
        timestamp=FIXED_TS,
    )
    plan = AnalysisPlan(
        extraction_id=config.repo_id,
        slices=[Slice(slice_id="s1", adapter_name="stub-jsts", paths=[])],
        unhandled_paths=[],
        created_at=FIXED_TS,
    )
    generate_raw_acs(config=config, plan=plan, timestamp=FIXED_TS)

    ext_dir = extraction_dir(workspace_root, config.repo_id)
    legacy_path = ext_dir / "raw-acs.yaml"
    new_path = ext_dir / "evidence-rows.yaml"
    assert legacy_path.exists()
    assert new_path.exists()
    # Same content.
    assert legacy_path.read_text() == new_path.read_text()


def test_contract_draft_acs_carries_typed_objectives_when_synthesis_present(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """When synthesis emits Objectives, legacy ``acs:`` carries typed rows."""
    register_adapter(_StubAdapter())

    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=False,
        timestamp=FIXED_TS,
    )
    plan = AnalysisPlan(
        extraction_id=config.repo_id,
        slices=[Slice(slice_id="s1", adapter_name="stub-jsts", paths=[])],
        unhandled_paths=[],
        created_at=FIXED_TS,
    )
    raw = generate_raw_acs(
        config=config, plan=plan, timestamp=FIXED_TS
    )

    # Hand-crafted SynthesisResult — bypass the LLM call here.
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
                evidence=ObjectiveEvidence(
                    readme_excerpts=["files refund disputes at scale"],
                ),
            ),
        ],
        constraints=[],
        capabilities=[
            Capability(
                capability_id="C.csv-upload.1",
                text="CSV upload pipeline",
                serves=["O.dispute-flow.1"],
                evidence=CapabilityEvidence(readme_excerpts=["csv"]),
            )
        ],
        created_at=FIXED_TS,
    )
    verify_contract(
        config=config, raw=raw, synthesis=synthesis, timestamp=FIXED_TS
    )

    # v0.2.3 Cycle 3 — legacy `acs:` retired; objectives.yaml is canonical.
    ext_dir = extraction_dir(workspace_root, config.repo_id)
    objs_data = yaml.safe_load(
        (ext_dir / "objectives.yaml").read_text(encoding="utf-8")
    )
    assert len(objs_data["objectives"]) == 1
    assert objs_data["objectives"][0]["objective_id"] == "O.dispute-flow.1"
    assert len(objs_data["capabilities"]) == 1


def test_contract_draft_acs_falls_back_to_raw_when_no_synthesis(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Empty synthesis path: legacy ``acs:`` carries raw evidence rows."""
    register_adapter(_StubAdapter())
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=False,
        timestamp=FIXED_TS,
    )
    plan = AnalysisPlan(
        extraction_id=config.repo_id,
        slices=[Slice(slice_id="s1", adapter_name="stub-jsts", paths=[])],
        unhandled_paths=[],
        created_at=FIXED_TS,
    )
    raw = generate_raw_acs(
        config=config, plan=plan, timestamp=FIXED_TS
    )
    verify_contract(config=config, raw=raw, timestamp=FIXED_TS)

    # v0.2.3 Cycle 3 — when synthesis empty, objectives.yaml has empty
    # objectives. Evidence rows still in evidence-rows.yaml (canonical
    # since Cycle 1 OBJX.7).
    ext_dir = extraction_dir(workspace_root, config.repo_id)
    objs_data = yaml.safe_load(
        (ext_dir / "objectives.yaml").read_text(encoding="utf-8")
    )
    assert objs_data["objectives"] == []
    assert objs_data["capabilities"] == []
    # Evidence rows present in evidence-rows.yaml.
    evidence_rows = yaml.safe_load(
        (ext_dir / "evidence-rows.yaml").read_text(encoding="utf-8")
    )
    assert len(evidence_rows["acs"]) == 3
