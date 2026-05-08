"""AC.COMPINT.11 — Component tests on 3+ synthetic fixtures.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.11:

Three fixtures under
``plugins/dev-sdlc/odd-extractor/tests/fixtures/completeness-interview/``:

1. ``clean-codebase/`` — extracted set "complete"; 0 heuristic priors;
   0 LLM-flagged; user confirms all. Augmented == extracted +
   ``source="extracted"``.
2. ``eric-shape/`` — set lacks security objective; production_use=Yes
   + SOC-2 mention. Heuristic-1 + Heuristic-2 fire; LLM-judge
   promotes to flagged; user adds → ``source="added_by_user"``
   (rewrite path) or ``source="flagged_by_persona"`` (accept path).
3. ``persona-flagged/`` — set lacks data-persistence objective;
   POST/PUT/DELETE evidence rows. Heuristic-3 fires; LLM-judge
   confirms; user accepts → ``source="flagged_by_persona"``.

Each exercises full pipeline: heuristic pre-pass → LLM-judge (stub)
→ PM-batch interview → persistence → audit-log.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any

import yaml

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    ConfidenceBand,
    MultiSourceBundle,
    Objective,
    flag_missing_objectives,
    heuristic_priors,
    load_augmented_objectives,
    run_interview,
)

from _compint_pm_stub import StubPM


_FIXTURE_ROOT = (
    Path(__file__).parent / "fixtures" / "completeness-interview"
)


def _load_fixture_objectives(fixture_name: str) -> tuple[str, list[Objective]]:
    path = _FIXTURE_ROOT / fixture_name / "objectives.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    extraction_id = raw["extraction_id"]
    objs = [Objective.model_validate(d) for d in raw.get("objectives", [])]
    return extraction_id, objs


def _load_fixture_survey(fixture_name: str) -> dict | None:
    path = _FIXTURE_ROOT / fixture_name / "survey.md"
    if not path.exists():
        return None
    return {
        "source_path": str(path),
        "parsed": _parse_survey_text(path.read_text(encoding="utf-8")),
        "raw_text": path.read_text(encoding="utf-8"),
    }


def _parse_survey_text(text: str) -> dict:
    parsed: dict = {}
    for line in text.splitlines():
        ls = line.strip()
        if "production_use" in ls.lower() and ":" in ls:
            val = ls.split(":", 1)[1].strip()
            parsed["production_use"] = val
    return parsed


def _load_fixture_code_patterns(fixture_name: str) -> list[dict]:
    path = _FIXTURE_ROOT / fixture_name / "code-patterns.yaml"
    if not path.exists():
        return []
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return raw.get("code_patterns", []) or []


def _make_bundle(fixture_name: str) -> MultiSourceBundle:
    return MultiSourceBundle(
        repo_id=fixture_name,
        repo_path=str(_FIXTURE_ROOT / fixture_name),
        repo_sha="fixture-sha-1234567",
        readme_text=f"# {fixture_name} fixture",
        readme_truncated=False,
        design_docs=[],
        test_assertions=[],
        user_survey=_load_fixture_survey(fixture_name),
        code_patterns=_load_fixture_code_patterns(fixture_name),
        total_token_estimate=200,
    )


# ---- Stub Anthropic client ----------------------------------------


class _StubBlock:
    def __init__(self, text: str):
        self.type = "text"
        self.text = text


class _StubResponse:
    def __init__(self, text: str):
        self.content = [_StubBlock(text)]
        self.usage = type("Usage", (), {"input_tokens": 100, "output_tokens": 50})()


class _StubAnthropic:
    def __init__(self, response_json: dict[str, Any]):
        self.captured: list[dict] = []

        outer = self

        class _M:
            def create(self, **kwargs):
                outer.captured.append(kwargs)
                return _StubResponse(json.dumps(response_json))

        self.messages = _M()


# ---- Per-fixture sub-tests ----------------------------------------


def test_clean_codebase_fixture_zero_priors_zero_flagged_user_confirms_all(tmp_path: Path) -> None:
    extraction_id, objs = _load_fixture_objectives("clean-codebase")
    bundle = _make_bundle("clean-codebase")

    # Heuristic pre-pass — should be empty.
    priors = heuristic_priors(objs, multi_source_bundle=bundle)
    assert priors == [], (
        "Clean-codebase fixture should yield 0 heuristic priors"
    )

    # LLM-judge stub returning empty flagged.
    client = _StubAnthropic({"flagged": []})
    flagged = flag_missing_objectives(
        objs,
        multi_source_bundle=bundle,
        anthropic_client=client,
        priors=priors,
    )
    assert flagged == []

    # Run interview — user confirms all.
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    aug = AugmentedObjectiveSet(
        extraction_id=extraction_id,
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=objs,
    )
    answers = iter(["1"] * len(objs) + ["no"])

    def producer(sq):
        return next(answers)

    result = run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id=extraction_id,
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )
    # Augmented == extracted, all source=extracted.
    assert len(result.objectives) == len(objs)
    assert all(o.source == "extracted" for o in result.objectives)


def test_eric_shape_fixture_heuristic_fires_user_adds_audit_objective(tmp_path: Path) -> None:
    extraction_id, objs = _load_fixture_objectives("eric-shape")
    bundle = _make_bundle("eric-shape")

    priors = heuristic_priors(objs, multi_source_bundle=bundle)
    pattern_ids = {p.pattern_id for p in priors}
    assert "production-stake-no-security-objective" in pattern_ids
    assert "survey-compliance-no-compliance-objective" in pattern_ids

    # LLM-judge stub returning audit-trail candidate.
    client = _StubAnthropic(
        {
            "flagged": [
                {
                    "candidate_text": (
                        "Audit trail identifies who initiated each "
                        "dispute filing for SOC-2 CC6 compliance."
                    ),
                    "reasoning": (
                        "Survey mentions SOC-2 + production-stake; no "
                        "audit-domain objective in the extracted set."
                    ),
                    "evidence_refs": ["survey:Q5"],
                    "priority": "high",
                    "domain": "audit",
                }
            ]
        }
    )
    flagged = flag_missing_objectives(
        objs,
        multi_source_bundle=bundle,
        anthropic_client=client,
        priors=priors,
    )
    assert len(flagged) == 1

    # Run interview — user accepts the flagged candidate (Shape (b)(1)).
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    aug = AugmentedObjectiveSet(
        extraction_id=extraction_id,
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=objs,
    )
    answers = iter(["1"] * len(objs) + ["1", "no"])  # confirm all + accept flagged + no free-form

    def producer(sq):
        return next(answers)

    result = run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id=extraction_id,
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )
    persona_flagged = [o for o in result.objectives if o.source == "flagged_by_persona"]
    assert len(persona_flagged) == 1
    assert persona_flagged[0].confidence == ConfidenceBand.PLAUSIBLE
    assert "audit" in persona_flagged[0].domain.lower()


def test_persona_flagged_fixture_heuristic_3_fires_user_accepts_persistence(tmp_path: Path) -> None:
    extraction_id, objs = _load_fixture_objectives("persona-flagged")
    bundle = _make_bundle("persona-flagged")

    priors = heuristic_priors(objs, multi_source_bundle=bundle)
    pattern_ids = {p.pattern_id for p in priors}
    assert "data-modify-routes-no-persistence-objective" in pattern_ids

    client = _StubAnthropic(
        {
            "flagged": [
                {
                    "candidate_text": (
                        "Dispute filings persist durably across "
                        "application restarts and survive process kills."
                    ),
                    "reasoning": (
                        "POST/PUT/DELETE routes exist but no persistence-"
                        "domain objective covers durability."
                    ),
                    "evidence_refs": ["AC.JSTS.1", "AC.JSTS.3"],
                    "priority": "medium",
                    "domain": "persistence",
                }
            ]
        }
    )
    flagged = flag_missing_objectives(
        objs,
        multi_source_bundle=bundle,
        anthropic_client=client,
        priors=priors,
    )
    assert len(flagged) == 1

    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    aug = AugmentedObjectiveSet(
        extraction_id=extraction_id,
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=objs,
    )
    answers = iter(["1", "1", "no"])  # confirm O.api.1 + accept flagged + no free-form

    def producer(sq):
        return next(answers)

    result = run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id=extraction_id,
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )
    persona_flagged = [o for o in result.objectives if o.source == "flagged_by_persona"]
    assert len(persona_flagged) == 1
    assert "persistence" in persona_flagged[0].domain.lower()


def test_full_pipeline_writes_augmented_objectives_yaml_for_eric_shape(tmp_path: Path) -> None:
    """End-to-end persistence verification: file lands at the canonical
    path and round-trips through ``load_augmented_objectives``."""
    extraction_id, objs = _load_fixture_objectives("eric-shape")
    bundle = _make_bundle("eric-shape")
    priors = heuristic_priors(objs, multi_source_bundle=bundle)
    client = _StubAnthropic(
        {
            "flagged": [
                {
                    "candidate_text": (
                        "Audit trail identifies who initiated each "
                        "dispute for compliance review."
                    ),
                    "reasoning": "Production-stake + SOC-2.",
                    "evidence_refs": ["survey:Q5"],
                    "priority": "high",
                    "domain": "audit",
                }
            ]
        }
    )
    flagged = flag_missing_objectives(
        objs,
        multi_source_bundle=bundle,
        anthropic_client=client,
        priors=priors,
    )
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    aug = AugmentedObjectiveSet(
        extraction_id=extraction_id,
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=objs,
    )
    answers = iter(["1", "1", "1", "no"])

    def producer(sq):
        return next(answers)

    run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id=extraction_id,
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )

    on_disk = load_augmented_objectives(ext_dir)
    assert on_disk is not None
    assert on_disk.extraction_id == "eric-shape"
    assert any(o.source == "flagged_by_persona" for o in on_disk.objectives)
    assert any(o.domain.lower() == "audit" for o in on_disk.objectives)


def test_full_pipeline_emits_complete_audit_log_for_eric_shape(tmp_path: Path) -> None:
    """All 7 audit event_kinds present (start/end + at least one of
    each per-action kind that fires for this fixture's flow)."""
    extraction_id, objs = _load_fixture_objectives("eric-shape")
    bundle = _make_bundle("eric-shape")
    priors = heuristic_priors(objs, multi_source_bundle=bundle)
    client = _StubAnthropic(
        {
            "flagged": [
                {
                    "candidate_text": (
                        "Audit trail identifies who initiated each "
                        "dispute for compliance review."
                    ),
                    "reasoning": "Production-stake + SOC-2.",
                    "evidence_refs": ["survey:Q5"],
                    "priority": "high",
                    "domain": "audit",
                }
            ]
        }
    )
    flagged = flag_missing_objectives(
        objs,
        multi_source_bundle=bundle,
        anthropic_client=client,
        priors=priors,
    )
    ext_dir = tmp_path / "ext"
    ext_dir.mkdir()
    pm = StubPM(audit_root=ext_dir / "audit-log")
    aug = AugmentedObjectiveSet(
        extraction_id=extraction_id,
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=str(ext_dir / "audit-log"),
        objectives=objs,
    )

    # Confirm both extracted + accept flagged + free-form-add a new one.
    free = "the system continues to serve queued requests for at least 60 seconds after a graceful shutdown signal"
    answers = iter(["1", "1", "1", free])

    def producer(sq):
        return next(answers)

    run_interview(
        workspace_root=tmp_path,
        extraction_dir_=ext_dir,
        extraction_id=extraction_id,
        pm=pm,
        augmented_set_in=aug,
        flagged_missing=flagged,
        response_producer=producer,
    )

    audit_dir = ext_dir / "audit-log"
    assert audit_dir.exists()
    seen_kinds: set[str] = set()
    for f in audit_dir.iterdir():
        if f.is_file() and f.name.endswith(".yaml"):
            payload = yaml.safe_load(f.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                seen_kinds.add(payload.get("event_kind", ""))
    assert "completeness_interview_start" in seen_kinds
    assert "completeness_interview_end" in seen_kinds
    assert "objective_confirmed" in seen_kinds
    assert "objective_flagged_by_persona" in seen_kinds
    assert "objective_added_by_user" in seen_kinds
