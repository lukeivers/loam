"""AC.OBJX.12 — Audit-log per synthesis call.

- ``synthesis_complete`` event-kind written with required fields.
- ``altitude_check_complete`` event-kind written with required
  fields.
- Both event-kinds round-trip through the audit-log YAML schema
  (no schema-version bump per Cycle 1 substrate-preservation).
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from loam_odd_extractor import (
    ConfidenceBand,
    MultiSourceBundle,
    Objective,
    ObjectiveEvidence,
    SynthesisResult,
    AnalysisPlan,
    default_budget,
    extraction_dir,
    generate_raw_acs,
    init_extraction,
    synthesize_objectives,
    verify_contract,
)


FIXED_TS = "2026-05-04T12:00:00+00:00"


# ---- Stub client (re-used pattern) ---------------------------------


class _StubBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _StubResponse:
    def __init__(self, text: str, input_tokens: int = 100, output_tokens: int = 50):
        self.content = [_StubBlock(text)]
        self.usage = type(
            "Usage", (), {"input_tokens": input_tokens, "output_tokens": output_tokens}
        )()


class _StubMessages:
    def __init__(self, payload: dict):
        self._payload = payload

    def create(self, **kwargs):  # type: ignore[no-untyped-def]
        return _StubResponse(json.dumps(self._payload))


class _StubClient:
    def __init__(self, payload: dict):
        self.messages = _StubMessages(payload)


def _good_payload() -> dict:
    return {
        "objectives": [
            {
                "objective_id": "O.dispute-flow.1",
                "text": (
                    "Operators file refund disputes against merchant "
                    "portals at scale, replacing manual portal clickwork."
                ),
                "confidence": "PLAUSIBLE",
                "domain": "dispute-flow",
                "evidence": {
                    "readme_excerpts": ["files refunds at scale"],
                    "design_doc_refs": [],
                    "test_name_refs": [],
                    "survey_line_refs": [],
                    "code_pattern_refs": [],
                    "repo_sha": None,
                    "rationale": None,
                },
            }
        ],
        "constraints": [],
        "capabilities": [],
    }


def _bundle() -> MultiSourceBundle:
    return MultiSourceBundle(
        repo_id="test-repo",
        repo_path="/tmp/test",
        readme_text="# x\nFile refunds at scale.",
        readme_truncated=False,
        design_docs=[],
        test_assertions=[],
        user_survey=None,
        code_patterns=[],
        total_token_estimate=200,
    )


def test_synthesis_complete_audit_entry_written(
    fixture_repo: Path, workspace_root: Path
) -> None:
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    ext_dir = extraction_dir(workspace_root, config.repo_id)
    client = _StubClient(_good_payload())
    synthesize_objectives(
        _bundle(),
        extraction_id=config.repo_id,
        repo_sha="abc1234",
        anthropic_client=client,
        extraction_dir=ext_dir,
        timestamp=FIXED_TS,
    )
    audit_dir = ext_dir / "audit-log"
    entries = sorted(audit_dir.glob("*.yaml"))
    found_synthesis = False
    for e in entries:
        data = yaml.safe_load(e.read_text(encoding="utf-8"))
        if data.get("event_kind") == "synthesis_complete":
            found_synthesis = True
            est = data.get("estimate") or {}
            assert "source_list" in est
            assert "token_count_input" in est
            assert "token_count_output" in est
            assert "cost_actual_cents" in est
            assert "objective_count_by_band" in est
            assert "constraint_count" in est
            assert "capability_count" in est
            assert "model_id" in est
            break
    assert found_synthesis, (
        "AC.OBJX.12 — synthesis_complete event-kind missing from audit-log"
    )


def test_altitude_check_complete_audit_entry_written(
    fixture_repo: Path, workspace_root: Path
) -> None:
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    ext_dir = extraction_dir(workspace_root, config.repo_id)
    plan = AnalysisPlan(
        extraction_id=config.repo_id,
        slices=[], unhandled_paths=[], created_at=FIXED_TS,
    )
    raw = generate_raw_acs(config=config, plan=plan, timestamp=FIXED_TS)
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
                evidence=ObjectiveEvidence(readme_excerpts=["files refunds"]),
            )
        ],
        capabilities=[],
        created_at=FIXED_TS,
    )
    verify_contract(
        config=config, raw=raw, synthesis=synthesis, timestamp=FIXED_TS
    )
    audit_dir = ext_dir / "audit-log"
    entries = sorted(audit_dir.glob("*.yaml"))
    found = False
    for e in entries:
        data = yaml.safe_load(e.read_text(encoding="utf-8"))
        if data.get("event_kind") == "altitude_check_complete":
            found = True
            est = data.get("estimate") or {}
            assert "total_rows" in est
            assert "pass_count" in est
            assert "fail_count" in est
            assert "borderline_count" in est
            assert "pass_rate" in est
            assert "drift_halt_triggered" in est
            break
    assert found, "AC.OBJX.12 — altitude_check_complete missing"


def test_audit_log_entries_round_trip_yaml_schema(
    fixture_repo: Path, workspace_root: Path
) -> None:
    """Schema_version preserved at 1 (no bump per Cycle 1 framing)."""
    config = init_extraction(
        repo_path=fixture_repo,
        workspace_root=workspace_root,
        budget=default_budget(),
        dry_run=True,
        timestamp=FIXED_TS,
    )
    ext_dir = extraction_dir(workspace_root, config.repo_id)
    client = _StubClient(_good_payload())
    synthesize_objectives(
        _bundle(),
        extraction_id=config.repo_id,
        anthropic_client=client,
        extraction_dir=ext_dir,
        timestamp=FIXED_TS,
    )
    audit_dir = ext_dir / "audit-log"
    for e in sorted(audit_dir.glob("*.yaml")):
        data = yaml.safe_load(e.read_text(encoding="utf-8"))
        assert data["schema_version"] == 1
