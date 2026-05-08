"""AC.V025-1.3 — Demotion-guard cascades to dependent capabilities.

Per v0.2.5.1 corrective (F-VERIFY-ORPHAN closure): when the band-rule
guards drop an objective from synthesis, capabilities whose ``serves``
references the dropped objective are also dropped (cascade-drop). If
a capability has multi-objective ``serves`` and ≥1 reference survives,
the capability is retained with the surviving references.

Three+1 unit tests cover the algorithm:

- ``test_cascade_drops_capability_with_only_dropped_serves``
  — single-``serves`` capability pointing at a dropped objective is
  removed; verify still emits no orphan-halt.
- ``test_cascade_filters_multi_serves_retains_survivors``
  — multi-``serves`` capability with one dropped + one surviving
  reference retains the surviving reference; capability stays.
- ``test_cascade_helper_unit_handles_non_dict_rows``
  — direct unit on the helper; non-dict input rows pass through so
  per-row Pydantic validation can surface them with a clean error.
- ``test_verify_still_strict_on_dangling_reference_in_static_contract``
  — verify-stage AC.OBJX.10 strictness UNCHANGED for genuinely
  dangling references in a manually-edited contract.

Replays the exact failure shape from Eric's run on rd-automation:

  C.state-diff.1 → dropped O.verification.1
  C.dry-run.1   → dropped O.simulation.1
"""

from __future__ import annotations

import logging

import pytest

from loam_odd_extractor.errors import StageError
from loam_odd_extractor.synthesis import (
    _cascade_drop_orphan_capabilities,
    _validate_rows,
)


def _surviving_objective_dict(oid: str, *, domain: str = "verification") -> dict:
    """Build a synthesis-shape objective dict that survives both
    band-rule guards (VERIFIED with two-source rule satisfied)."""
    return {
        "objective_id": oid,
        "text": (
            "Operators verify contract changes against the captured "
            "objective set, replacing manual review."
        ),
        "confidence": "VERIFIED",
        "domain": domain,
        "evidence": {
            "test_name_refs": ["tests/test_verify.py::test_thing"],
            "readme_excerpts": ["README mentions verification"],
            "design_doc_refs": ["docs/design.md mentions verification"],
            "survey_line_refs": [],
            "code_pattern_refs": [],
            "repo_sha": "abc123",
            "rationale": None,
        },
    }


def _drop_target_objective_dict(oid: str, *, domain: str = "verification") -> dict:
    """Build a synthesis-shape objective dict the band-rule guards will
    DROP (PLAUSIBLE with zero sources of evidence + no rationale + no
    code patterns)."""
    return {
        "objective_id": oid,
        "text": (
            "Verification of contract changes that has no real evidence "
            "to support its existence at any band."
        ),
        "confidence": "PLAUSIBLE",
        "domain": domain,
        "evidence": {
            "test_name_refs": [],
            "readme_excerpts": [],
            "design_doc_refs": [],
            "survey_line_refs": [],
            "code_pattern_refs": [],
            "repo_sha": None,
            "rationale": None,
        },
    }


def _capability_dict(cap_id: str, serves: list[str]) -> dict:
    """Build a synthesis-shape capability dict for cascade tests."""
    return {
        "capability_id": cap_id,
        "text": "Capability serving the named objective(s).",
        "serves": serves,
        "evidence": {
            "readme_excerpts": ["readme mentions capability"],
            "design_doc_refs": [],
            "test_name_refs": [],
            "survey_line_refs": [],
            "code_pattern_refs": [],
            "repo_sha": None,
            "rationale": None,
        },
    }


def test_cascade_drops_capability_with_only_dropped_serves(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Cascade-drop replay of Eric's C.state-diff.1 → O.verification.1
    failure. The objective is dropped (PLAUSIBLE band with ZERO
    sources of evidence + no rationale + no code patterns). The
    capability points only at the dropped objective; the cascade
    drops the capability before per-row Pydantic validation.
    """
    dropped_obj = _drop_target_objective_dict("O.verification.1")
    survives_obj = _surviving_objective_dict("O.kept.1", domain="kept")
    cap = _capability_dict("C.state-diff.1", ["O.verification.1"])

    payload = {
        "objectives": [dropped_obj, survives_obj],
        "constraints": [],
        "capabilities": [cap],
    }

    caplog.set_level(logging.WARNING, logger="loam_odd_extractor.synthesis")
    objectives, _constraints, capabilities = _validate_rows(
        payload, repo_sha="abc123"
    )

    obj_ids = [o.objective_id for o in objectives]
    assert "O.verification.1" not in obj_ids, (
        f"Dropped objective must be removed; got obj_ids={obj_ids}"
    )
    assert "O.kept.1" in obj_ids
    cap_ids = [c.capability_id for c in capabilities]
    assert "C.state-diff.1" not in cap_ids, (
        f"Capability with only-dropped serves must be cascade-dropped; "
        f"got cap_ids={cap_ids}"
    )
    log_msgs = [r.getMessage() for r in caplog.records]
    assert any(
        "C.state-diff.1" in m and "O.verification.1" in m for m in log_msgs
    ), (
        f"WARN log must name dropped capability + dropped objective; "
        f"got: {log_msgs}"
    )


def test_cascade_filters_multi_serves_retains_survivors(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Multi-`serves` capability with one dropped + one surviving
    reference retains the surviving reference; capability stays."""
    dropped_obj = _drop_target_objective_dict("O.dropped.1", domain="dropped")
    survives_obj = _surviving_objective_dict("O.kept.1", domain="kept")
    cap = _capability_dict("C.multi.1", ["O.dropped.1", "O.kept.1"])

    payload = {
        "objectives": [dropped_obj, survives_obj],
        "constraints": [],
        "capabilities": [cap],
    }

    caplog.set_level(logging.WARNING, logger="loam_odd_extractor.synthesis")
    objectives, _constraints, capabilities = _validate_rows(
        payload, repo_sha="abc123"
    )

    obj_ids = [o.objective_id for o in objectives]
    assert "O.dropped.1" not in obj_ids
    assert "O.kept.1" in obj_ids

    cap_ids = [c.capability_id for c in capabilities]
    assert "C.multi.1" in cap_ids, (
        "Multi-serves cap must be retained when at least one obj survives"
    )
    retained_cap = [c for c in capabilities if c.capability_id == "C.multi.1"][
        0
    ]
    assert retained_cap.serves == ["O.kept.1"], (
        f"Surviving serves filter must drop O.dropped.1 from "
        f"serves; got {retained_cap.serves}"
    )
    log_msgs = [r.getMessage() for r in caplog.records]
    assert any(
        "C.multi.1" in m and "O.dropped.1" in m for m in log_msgs
    ), f"WARN log must name multi-serves cascade; got: {log_msgs}"


def test_cascade_helper_unit_handles_non_dict_rows() -> None:
    """Direct unit test on _cascade_drop_orphan_capabilities — non-dict
    rows in the input lists pass through unchanged so per-row Pydantic
    validation can surface them with a clean error."""
    objectives_raw = [
        {"objective_id": "O.kept.1", "text": "x"},
        "not-a-dict-objective",
    ]
    capabilities_raw = [
        {"capability_id": "C.kept.1", "serves": ["O.kept.1"]},
        "also-not-a-dict",
        42,
    ]
    result = _cascade_drop_orphan_capabilities(
        objectives_raw=objectives_raw,
        capabilities_raw=capabilities_raw,
    )
    # Non-dict capability rows pass through (per-row validation
    # downstream will surface them with a clean error).
    assert "also-not-a-dict" in result
    assert 42 in result
    cap_dicts = [r for r in result if isinstance(r, dict)]
    assert len(cap_dicts) == 1
    assert cap_dicts[0]["capability_id"] == "C.kept.1"


def test_verify_still_strict_on_dangling_reference_in_static_contract() -> None:
    """AC.OBJX.10 verify-stage strictness UNCHANGED. A SynthesisResult
    with a Capability pointing at a non-existent Objective still raises
    StageError at verify time. The cascade only fires inside the
    synthesis-layer parsing path; once typed rows are constructed, the
    referential-integrity check at verify is the contract."""
    from loam_odd_extractor import (
        Capability,
        CapabilityEvidence,
        ConfidenceBand,
        Objective,
        ObjectiveEvidence,
        SynthesisResult,
    )
    from loam_odd_extractor.verify import _check_capability_references

    obj = Objective(
        objective_id="O.kept.1",
        text=(
            "Operators verify contract changes against the captured "
            "objective set, replacing manual review."
        ),
        confidence=ConfidenceBand.VERIFIED,
        domain="verification",
        evidence=ObjectiveEvidence(
            test_name_refs=["tests/t.py::test_thing"],
            readme_excerpts=["readme"],
            design_doc_refs=["docs/d.md"],
            rationale="r",
            repo_sha="abc",
        ),
    )
    cap = Capability(
        capability_id="C.dangle.1",
        text="Dangles into the void.",
        serves=["O.nonexistent.1"],
        evidence=CapabilityEvidence(readme_excerpts=["readme"]),
    )
    sr = SynthesisResult(
        extraction_id="x",
        objectives=[obj],
        constraints=[],
        capabilities=[cap],
        raw_response="{}",
        token_count_input=0,
        token_count_output=0,
        cost_actual_cents=0.0,
        model_id="test",
        created_at="2026-05-08T00:00:00+00:00",
    )
    with pytest.raises(StageError, match="O.nonexistent.1"):
        _check_capability_references(sr)
