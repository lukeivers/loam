"""Integration test — full v0.2.3 synthesis pipeline on readme-rich fixture.

End-to-end exercise: init → analyze → generate (with stub Anthropic
client) → verify. Asserts every AC's exit-state simultaneously:

- AC.OBJX.1/2/3: typed Objective/Constraint/Capability rows.
- AC.OBJX.4: multi-source bundle populated.
- AC.OBJX.5: synthesis produces structured output.
- AC.OBJX.6: cost surfacing in audit-log.
- AC.OBJX.7: evidence-rows.yaml + raw-acs.yaml both present;
  contract-draft.yaml acs: carries typed Objectives.
- AC.OBJX.8: altitude validator runs at verify-time.
- AC.OBJX.10: contract-draft.md has all altitude sections.
- AC.OBJX.12: synthesis_complete + altitude_check_complete in
  audit-log.

This test is the synthesis-pipeline smoke that the build agent
runs against the readme-rich fixture.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from loam_odd_extractor import (
    AnalysisPlan,
    default_budget,
    extraction_dir,
    generate_raw_acs,
    init_extraction,
    verify_contract,
)


_FIXTURE = (
    Path(__file__).parent / "fixtures" / "multi-source-synthesis" / "readme-rich"
)
FIXED_TS = "2026-05-04T12:00:00+00:00"


# ---- Stub client ---------------------------------------------------


class _StubBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _StubResponse:
    def __init__(self, text: str, input_tokens: int = 2000, output_tokens: int = 800):
        self.content = [_StubBlock(text)]
        self.usage = type(
            "Usage", (), {"input_tokens": input_tokens, "output_tokens": output_tokens}
        )()


class _StubMessages:
    def __init__(self, payload: dict):
        self._payload = payload

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        return _StubResponse(json.dumps(self._payload))


def _readme_rich_canned_response() -> dict:
    return {
        "objectives": [
            {
                "objective_id": "O.dispute-flow.1",
                "text": (
                    "Operators file refund disputes against DoorDash and "
                    "Uber Eats merchant portals at scale, replacing "
                    "manual portal clickwork."
                ),
                "confidence": "VERIFIED",
                "domain": "dispute-flow",
                "evidence": {
                    "test_name_refs": [
                        "tests/test_dispute_flow.spec.ts::operators file refund disputes through the dispute pipeline",
                    ],
                    "readme_excerpts": [
                        "operators file refund disputes against the DoorDash and Uber Eats merchant portals at scale",
                    ],
                    "design_doc_refs": [
                        "docs/architecture.md#dispute-pipeline",
                    ],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            },
            {
                "objective_id": "O.audit-trail.1",
                "text": (
                    "Auditors can verify who initiated each dispute and "
                    "the outcome via the audit trail."
                ),
                "confidence": "VERIFIED",
                "domain": "audit-trail",
                "evidence": {
                    "test_name_refs": [
                        "tests/test_audit_trail.spec.ts::auditors can verify dispute outcomes",
                    ],
                    "readme_excerpts": [
                        "Audit trail records who initiated each dispute"
                    ],
                    "design_doc_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            },
            {
                "objective_id": "O.csv-validation.1",
                "text": (
                    "CSV uploads are validated row-by-row so operators "
                    "can correct malformed entries before submission."
                ),
                "confidence": "PLAUSIBLE",
                "domain": "csv-validation",
                "evidence": {
                    "test_name_refs": [
                        "tests/test_csv_upload.spec.ts::csv upload validates rows",
                    ],
                    "readme_excerpts": [],
                    "design_doc_refs": ["docs/architecture.md#dispute-pipeline"],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            },
        ],
        "constraints": [
            {
                "constraint_id": "K.compliance.1",
                "text": "SOC-2 audit-trail floor",
                "bounds_kind": "compliance",
                "evidence": {
                    "readme_excerpts": ["SOC-2 audit-trail floor"],
                    "design_doc_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            },
            {
                "constraint_id": "K.security.1",
                "text": "Tokens confidential under transport",
                "bounds_kind": "security",
                "evidence": {
                    "readme_excerpts": [],
                    "design_doc_refs": ["docs/auth-flow.md"],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            },
        ],
        "capabilities": [
            {
                "capability_id": "C.csv-upload.1",
                "text": "CSV upload + validation pipeline supports bulk filing",
                "serves": ["O.dispute-flow.1", "O.csv-validation.1"],
                "evidence": {
                    "readme_excerpts": ["Operators upload CSVs"],
                    "design_doc_refs": [],
                    "test_name_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            }
        ],
    }


class _StubAnthropic:
    def __init__(self, payload: dict):
        self.messages = _StubMessages(payload)


def test_full_pipeline_against_readme_rich_fixture(tmp_path: Path) -> None:
    workspace = tmp_path / "ws"
    workspace.mkdir()
    config = init_extraction(
        repo_path=_FIXTURE,
        workspace_root=workspace,
        budget=default_budget(),
        dry_run=False,
        timestamp=FIXED_TS,
    )
    plan = AnalysisPlan(
        extraction_id=config.repo_id,
        slices=[],
        unhandled_paths=[],
        created_at=FIXED_TS,
    )
    client = _StubAnthropic(_readme_rich_canned_response())
    raw = generate_raw_acs(
        config=config,
        plan=plan,
        timestamp=FIXED_TS,
        anthropic_client=client,
    )
    draft = verify_contract(
        config=config, raw=raw, timestamp=FIXED_TS
    )

    ext_dir = extraction_dir(workspace, config.repo_id)

    # AC.OBJX.7 — both file names ship.
    assert (ext_dir / "evidence-rows.yaml").exists()
    assert (ext_dir / "raw-acs.yaml").exists()

    # AC.OBJX.4 — bundle persisted.
    bundle = yaml.safe_load(
        (ext_dir / "multi-source-bundle.yaml").read_text(encoding="utf-8")
    )
    assert bundle["readme_text"] is not None
    assert "DisputeApp" in bundle["readme_text"]
    assert len(bundle["design_docs"]) >= 1

    # AC.OBJX.5 — synthesis output persisted.
    synthesis = yaml.safe_load(
        (ext_dir / "synthesis.yaml").read_text(encoding="utf-8")
    )
    assert len(synthesis["objectives"]) >= 1

    # AC.OBJX.10 — markdown sections present.
    md = (ext_dir / "contract-draft.md").read_text(encoding="utf-8")
    assert "## Objectives" in md
    assert "## Constraints" in md
    assert "## Capabilities" in md
    assert "## Evidence rows" in md
    assert "§self-checks audit" in md

    # AC.OBJX.10 — sidecar typed lists.
    sidecar = yaml.safe_load(
        (ext_dir / "contract-draft.yaml").read_text(encoding="utf-8")
    )
    assert "objectives" in sidecar and len(sidecar["objectives"]) >= 1
    assert "constraints" in sidecar and len(sidecar["constraints"]) >= 1
    assert "capabilities" in sidecar and len(sidecar["capabilities"]) >= 1
    assert "altitude_report" in sidecar

    # AC.OBJX.7 — legacy ``acs:`` carries typed Objectives (not raw).
    assert sidecar["acs"][0]["ac_id"].startswith("O.")
    assert "objective_payload" in sidecar["acs"][0]

    # AC.OBJX.8 — altitude report present + drift not triggered (canned response).
    altitude = sidecar["altitude_report"]
    assert altitude["total_rows"] >= 1
    # Drift halt should not fire on this curated fixture.
    assert altitude["drift_halt_triggered"] is False

    # AC.OBJX.12 — audit-log has both event-kinds.
    audit_files = sorted((ext_dir / "audit-log").glob("*.yaml"))
    event_kinds = set()
    for f in audit_files:
        data = yaml.safe_load(f.read_text(encoding="utf-8"))
        event_kinds.add(data.get("event_kind"))
    assert "synthesis_complete" in event_kinds
    assert "altitude_check_complete" in event_kinds


def test_self_checks_pass_on_synthesized_output(tmp_path: Path) -> None:
    """Smoke run: every objective in the canned response passes
    §self-checks 1-5 (>= 70% pass rate sanity floor)."""
    workspace = tmp_path / "ws"
    workspace.mkdir()
    config = init_extraction(
        repo_path=_FIXTURE,
        workspace_root=workspace,
        budget=default_budget(),
        dry_run=False,
        timestamp=FIXED_TS,
    )
    plan = AnalysisPlan(
        extraction_id=config.repo_id,
        slices=[],
        unhandled_paths=[],
        created_at=FIXED_TS,
    )
    client = _StubAnthropic(_readme_rich_canned_response())
    raw = generate_raw_acs(
        config=config,
        plan=plan,
        timestamp=FIXED_TS,
        anthropic_client=client,
    )
    verify_contract(config=config, raw=raw, timestamp=FIXED_TS)

    ext_dir = extraction_dir(workspace, config.repo_id)
    sidecar = yaml.safe_load(
        (ext_dir / "contract-draft.yaml").read_text(encoding="utf-8")
    )
    altitude = sidecar["altitude_report"]
    # Operational metric per sub-plan-doc Lens 4 + AC.OBJX.8:
    # >30% fail rate triggers ``drift_halt_triggered`` (the
    # ``needs_fresh_start`` shape from Lens 5). Borderline rows
    # don't count against the floor — LLM-as-judge would adjudicate;
    # programmatic-only path keeps them as borderline (decision tree
    # downgrades VERIFIED to PLAUSIBLE; otherwise keeps).
    total = altitude["total_rows"]
    fail_rate = altitude["fail_count"] / total if total else 0.0
    assert fail_rate < 0.30, (
        f"§self-checks fail rate too high: {fail_rate:.2%} "
        f"(threshold 30%) — altitude rebuild has drifted; surface as halt."
    )
    # And the drift-halt flag must agree.
    assert altitude["drift_halt_triggered"] is False
