"""AC.BLDNXT.8 — Audit-log event_kinds.

Per v0.2.4 Cycle 3 sub-plan-doc §3 AC.BLDNXT.8:

- 3 additive event_kinds: build_next_start / build_next_persisted /
  build_next_end.
- Payloads via existing ``estimate`` field (no schema-version bump).
- ``BUILD_NEXT_EVENT_KINDS`` constant exported for introspection.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_odd_extractor.build_next import (
    emit_build_next_end_audit,
    emit_build_next_persisted_audit,
    emit_build_next_start_audit,
)
from loam_odd_extractor.observability import (
    BUILD_NEXT_EVENT_KINDS,
    list_entries,
)
from loam_odd_extractor import (
    BuildNextRecommendation,
    BuildNextCandidate,
)


def test_event_kinds_constant():
    assert BUILD_NEXT_EVENT_KINDS == (
        "build_next_start",
        "build_next_persisted",
        "build_next_end",
    )


def test_full_run_three_audit_entries(tmp_path: Path):
    extraction_dir = tmp_path / "ext"
    extraction_dir.mkdir()

    emit_build_next_start_audit(
        extraction_dir,
        extraction_id="ext1",
        gap_count=5,
        survey_present=True,
        interview_priority_count=2,
        llm_judge_budget_cents=10,
    )

    cand = BuildNextCandidate(
        gap_id="G.BACKING.x",
        composite_score=0.5,
        gap_confidence_factor=1.0,
        priority_match_factor=1.0,
        estimated_impact_factor=0.5,
        priority_match_signal="survey",
        rationale="x" * 50,
        category="objective_without_verified_backing",
        objective_id="O.x.1",
    )
    rec = BuildNextRecommendation(
        extraction_id="ext1",
        analyzed_at="2026-05-04T00:00:00+00:00",
        audit_path=str(extraction_dir / "audit-log"),
        candidates=[cand],
        truncated_count=0,
        llm_judge_invocations=2,
    )
    emit_build_next_persisted_audit(
        extraction_dir,
        extraction_id="ext1",
        rec=rec,
        build_next_md_path_str=str(extraction_dir / "build-next.md"),
        build_next_yaml_path_str=str(extraction_dir / "build-next.yaml"),
    )
    emit_build_next_end_audit(
        extraction_dir,
        extraction_id="ext1",
        duration_ms=42,
        total_cost_cents=4.0,
    )

    entries = list_entries(extraction_dir)
    assert len(entries) == 3
    kinds = []
    for ep in entries:
        data = yaml.safe_load(ep.read_text(encoding="utf-8"))
        kinds.append(data["event_kind"])
    assert kinds == [
        "build_next_start",
        "build_next_persisted",
        "build_next_end",
    ]


def test_persisted_payload_carries_required_fields(tmp_path: Path):
    extraction_dir = tmp_path / "ext"
    extraction_dir.mkdir()
    cand = BuildNextCandidate(
        gap_id="G.ORPHAN.foo",
        composite_score=0.3,
        gap_confidence_factor=0.5,
        priority_match_factor=None,
        estimated_impact_factor=0.6,
        priority_match_signal="none",
        rationale="x" * 50,
        category="implementation_orphan",
    )
    rec = BuildNextRecommendation(
        extraction_id="ext1",
        analyzed_at="2026-05-04T00:00:00+00:00",
        audit_path="/tmp/audit-log",
        candidates=[cand],
        truncated_count=2,
        llm_judge_invocations=0,
        degenerate_survey=True,
    )
    p = emit_build_next_persisted_audit(
        extraction_dir,
        extraction_id="ext1",
        rec=rec,
        build_next_md_path_str="/tmp/build-next.md",
        build_next_yaml_path_str="/tmp/build-next.yaml",
    )
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    est = data["estimate"]
    assert est["candidate_count"] == 1
    assert est["truncated_count"] == 2
    assert est["llm_judge_invocations"] == 0
    assert est["degenerate_survey"] is True
    assert est["build_next_md_path"] == "/tmp/build-next.md"
    assert est["build_next_yaml_path"] == "/tmp/build-next.yaml"


def test_start_payload_carries_survey_and_interview_counts(tmp_path: Path):
    extraction_dir = tmp_path / "ext"
    extraction_dir.mkdir()
    p = emit_build_next_start_audit(
        extraction_dir,
        extraction_id="ext1",
        gap_count=7,
        survey_present=False,
        interview_priority_count=0,
        llm_judge_budget_cents=10,
    )
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    est = data["estimate"]
    assert est["gap_count"] == 7
    assert est["survey_present"] is False
    assert est["interview_priority_count"] == 0
    assert est["llm_judge_budget_cents"] == 10


def test_end_payload_carries_duration_and_cost(tmp_path: Path):
    extraction_dir = tmp_path / "ext"
    extraction_dir.mkdir()
    p = emit_build_next_end_audit(
        extraction_dir,
        extraction_id="ext1",
        duration_ms=2500,
        total_cost_cents=2.5,
    )
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    est = data["estimate"]
    assert est["duration_ms"] == 2500
    assert est["total_cost_cents"] == 2.5
