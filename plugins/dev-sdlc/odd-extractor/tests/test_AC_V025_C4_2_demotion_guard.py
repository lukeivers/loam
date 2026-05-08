"""AC.V025-C4.2 — band-demotion guard unit test.

Per v0.2.5 corrective C4 plan-doc §2:

The synthesis LLM does not reliably produce VERIFIED-banded objectives
that satisfy the two-source rule (AC.OBJX.5 — VERIFIED requires evidence
in tests AND in either readme_excerpts OR design_doc_refs). The Pydantic
validator at :class:`spec.Objective` correctly raises ``ValidationError``
on this shape. The band-demotion guard at
:func:`synthesis._apply_band_demotion_guard` normalizes the band BEFORE
validation rather than letting the entire synthesis stage exit 2 on a
recoverable mismatch.

This test feeds raw payloads through the production parser (``_validate_rows``
— the integration point being preserved) and verifies the guard's behavior
without mocking the validator.

Pre-arrangement detection rubric (per
``plugins/dev-sdlc/skills/odd-test-altitude-discipline/SKILL.md``):

- Production entry-point invoked? YES — ``_validate_rows`` is the
  production parser called from ``synthesize_objectives``.
- No state pre-arranged that production would produce? YES — only
  the LLM payload shape (raw dict) is constructed, NOT the validated
  Objective instances.
- Asserts on production-produced artefacts? YES — asserts on the
  list of Objective instances ``_validate_rows`` returns.
- No SDK / client mocking? YES — no ``anthropic`` / ``Anthropic``
  mocking; this is a parser-level unit test that bypasses the LLM
  call entirely.

Classified as STUB-class per the SKILL (canonical for unit tests of
internal helpers); paired with AC.V025-C4.3's OUTCOME-class test that
exercises the full CLI surface against the live API.
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

from loam_odd_extractor.bands import ConfidenceBand
from loam_odd_extractor.synthesis import (
    _apply_band_demotion_guard,
    _validate_rows,
)


# ---- Helper: payload-shape constructors ----------------------------


def _verified_no_two_sources_row(
    *,
    objective_id: str = "O.dispute-flow.1",
    text: str = (
        "Operators file refund disputes against merchant portals at "
        "scale, replacing manual portal clickwork."
    ),
    domain: str = "dispute-flow",
    repo_sha: str = "abc1234",
) -> dict[str, Any]:
    """Construct a row in the F8 BLOCKER shape — VERIFIED + tests +
    repo_sha but missing BOTH readme_excerpts AND design_doc_refs.

    This is the exact shape the production LLM has been observed
    producing (per v0.2.5 corrective C3 build report — F8 surface).
    """
    return {
        "objective_id": objective_id,
        "text": text,
        "confidence": "VERIFIED",
        "domain": domain,
        "evidence": {
            "test_name_refs": ["tests/x.spec.ts::it files disputes"],
            "readme_excerpts": [],
            "design_doc_refs": [],
            "survey_line_refs": [],
            "code_pattern_refs": [],
            "repo_sha": repo_sha,
            "rationale": None,
        },
    }


def _verified_with_two_sources_row(
    *,
    objective_id: str = "O.dispute-flow.2",
    text: str = (
        "Auditors trace each dispute back to operator and timestamp "
        "for compliance review."
    ),
    domain: str = "audit",
) -> dict[str, Any]:
    """Construct a row that genuinely satisfies the VERIFIED two-source
    rule — tests AND readme_excerpts both populated. The guard MUST
    NOT touch this row.
    """
    return {
        "objective_id": objective_id,
        "text": text,
        "confidence": "VERIFIED",
        "domain": domain,
        "evidence": {
            "test_name_refs": ["tests/audit.spec.ts::it traces"],
            "readme_excerpts": ["audit trail identifies who did what"],
            "design_doc_refs": [],
            "survey_line_refs": [],
            "code_pattern_refs": [],
            "repo_sha": "abc1234",
            "rationale": None,
        },
    }


def _plausible_row(
    *,
    objective_id: str = "O.audit.1",
) -> dict[str, Any]:
    """Construct a PLAUSIBLE row — guard MUST NOT touch (only VERIFIED
    rows are guarded).
    """
    return {
        "objective_id": objective_id,
        "text": (
            "Customers receive timely refund decisions within the "
            "merchant SLA window."
        ),
        "confidence": "PLAUSIBLE",
        "domain": "refund-sla",
        "evidence": {
            "test_name_refs": [],
            "readme_excerpts": ["Refund decisions within SLA"],
            "design_doc_refs": [],
            "survey_line_refs": [],
            "code_pattern_refs": [],
            "repo_sha": None,
            "rationale": None,
        },
    }


def _hypothesised_row(
    *,
    objective_id: str = "O.future.1",
) -> dict[str, Any]:
    """Construct a HYPOTHESISED row — guard MUST NOT touch (only
    VERIFIED rows are guarded).
    """
    return {
        "objective_id": objective_id,
        "text": (
            "System could integrate with external KYC providers for "
            "dispute escalation."
        ),
        "confidence": "HYPOTHESISED",
        "domain": "future",
        "evidence": {
            "test_name_refs": [],
            "readme_excerpts": [],
            "design_doc_refs": [],
            "survey_line_refs": [],
            "code_pattern_refs": ["src/foo.ts:42"],
            "repo_sha": None,
            "rationale": "code patterns suggest KYC integration seam",
        },
    }


# ---- AC.V025-C4.2 — guard demotes VERIFIED-without-two-sources -----


def test_AC_V025_C4_2_demotes_verified_missing_both_readme_and_design(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Guard demotes VERIFIED-banded row missing BOTH readme_excerpts
    AND design_doc_refs to PLAUSIBLE.

    The pre-fix shape: LLM emits VERIFIED row with tests + repo_sha but
    no readme/design-doc evidence. Pydantic validator raises ValidationError.
    With the guard: the row is rewritten to PLAUSIBLE in-place; the
    validator accepts (PLAUSIBLE rule allows survey-only OR readme/design-doc
    single-source — but this row has tests-only which doesn't satisfy
    PLAUSIBLE either, so it still raises on PLAUSIBLE rule). Test the
    guard's behavior in isolation first.
    """
    objectives_raw = [_verified_no_two_sources_row()]

    with caplog.at_level(logging.WARNING, logger="loam_odd_extractor.synthesis"):
        demotion_count = _apply_band_demotion_guard(objectives_raw)

    # Demotion happened.
    assert demotion_count == 1, (
        f"Guard must demote 1 row; got {demotion_count}"
    )

    # Row's band rewritten in-place.
    assert objectives_raw[0]["confidence"] == "PLAUSIBLE", (
        f"Guard must rewrite confidence to PLAUSIBLE; got "
        f"{objectives_raw[0]['confidence']!r}"
    )

    # Demotion logged with the objective_id.
    log_messages = [r.message for r in caplog.records]
    assert any("O.dispute-flow.1" in m for m in log_messages), (
        f"Guard must log the objective_id; got messages: {log_messages}"
    )
    assert any(
        "VERIFIED-band without two sources" in m for m in log_messages
    ), (
        f"Guard log must name the band-rule reason; got messages: "
        f"{log_messages}"
    )


def test_AC_V025_C4_2_does_not_demote_verified_with_readme(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Guard MUST NOT demote a VERIFIED row that has readme_excerpts."""
    objectives_raw = [_verified_with_two_sources_row()]

    with caplog.at_level(logging.WARNING, logger="loam_odd_extractor.synthesis"):
        demotion_count = _apply_band_demotion_guard(objectives_raw)

    assert demotion_count == 0
    assert objectives_raw[0]["confidence"] == "VERIFIED"
    # No demotion warning logged.
    assert not any(
        "demoting" in r.message for r in caplog.records
    ), "Guard must not log demotion when no demotion happens"


def test_AC_V025_C4_2_does_not_demote_verified_with_design_doc(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Guard MUST NOT demote a VERIFIED row that has design_doc_refs
    (single-side of the OR is sufficient).
    """
    row = _verified_with_two_sources_row()
    # Move the evidence from readme_excerpts to design_doc_refs.
    row["evidence"]["readme_excerpts"] = []
    row["evidence"]["design_doc_refs"] = ["docs/architecture.md#audit"]

    with caplog.at_level(logging.WARNING, logger="loam_odd_extractor.synthesis"):
        demotion_count = _apply_band_demotion_guard([row])

    assert demotion_count == 0
    assert row["confidence"] == "VERIFIED"


def test_AC_V025_C4_2_does_not_touch_plausible_or_hypothesised_rows(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Guard targets ONLY VERIFIED rows. PLAUSIBLE and HYPOTHESISED
    rows pass through unchanged regardless of evidence shape.
    """
    objectives_raw = [
        _plausible_row(),
        _hypothesised_row(),
    ]

    with caplog.at_level(logging.WARNING, logger="loam_odd_extractor.synthesis"):
        demotion_count = _apply_band_demotion_guard(objectives_raw)

    assert demotion_count == 0
    assert objectives_raw[0]["confidence"] == "PLAUSIBLE"
    assert objectives_raw[1]["confidence"] == "HYPOTHESISED"


def test_AC_V025_C4_2_handles_mixed_payload(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Guard correctly demotes only the offending VERIFIED rows in a
    mixed payload; leaves compliant VERIFIED + PLAUSIBLE +
    HYPOTHESISED rows untouched.
    """
    # Make IDs unique across rows.
    bad = _verified_no_two_sources_row(objective_id="O.bad.1")
    good_v = _verified_with_two_sources_row(objective_id="O.good.1")
    p = _plausible_row(objective_id="O.plausible.1")
    h = _hypothesised_row(objective_id="O.hypoth.1")
    objectives_raw = [bad, good_v, p, h]

    with caplog.at_level(logging.WARNING, logger="loam_odd_extractor.synthesis"):
        demotion_count = _apply_band_demotion_guard(objectives_raw)

    assert demotion_count == 1, (
        f"Only the bad VERIFIED row should be demoted; got {demotion_count}"
    )
    assert bad["confidence"] == "PLAUSIBLE"
    assert good_v["confidence"] == "VERIFIED"
    assert p["confidence"] == "PLAUSIBLE"
    assert h["confidence"] == "HYPOTHESISED"


# ---- AC.V025-C4.2 — integration with _validate_rows (no validator mocks) ---


def test_AC_V025_C4_2_validate_rows_accepts_demoted_row_with_survey_evidence(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Integration probe: a VERIFIED row missing two sources but with
    survey_line_refs survives demotion — the guard rewrites it to
    PLAUSIBLE, the validator accepts because the PLAUSIBLE rule allows
    survey-only single-source.

    This verifies the guard composes correctly with the validator
    without mocking the validator (the integration point being
    preserved per the dispatch brief).
    """
    row = _verified_no_two_sources_row()
    # Add survey evidence so the demoted row satisfies PLAUSIBLE rule.
    row["evidence"]["survey_line_refs"] = [
        "operator survey line 12: 'we file disputes daily'"
    ]
    payload = {
        "objectives": [row],
        "constraints": [],
        "capabilities": [],
    }

    with caplog.at_level(logging.WARNING, logger="loam_odd_extractor.synthesis"):
        objectives, constraints, capabilities = _validate_rows(
            payload, repo_sha="abc1234"
        )

    # No StageError raised — validator accepted the demoted PLAUSIBLE row.
    assert len(objectives) == 1
    assert objectives[0].confidence == ConfidenceBand.PLAUSIBLE, (
        f"Validator must produce PLAUSIBLE-banded Objective post-demotion; "
        f"got {objectives[0].confidence}"
    )
    # Demotion logged.
    log_messages = [r.message for r in caplog.records]
    assert any("demoting" in m for m in log_messages), (
        f"Demotion must be logged; got messages: {log_messages}"
    )


def test_AC_V025_C4_2_validate_rows_demoted_row_without_any_evidence_is_dropped(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A VERIFIED row with ONLY tests (no readme/design-doc/survey) is
    demoted to PLAUSIBLE by the first-pass guard; the second-pass
    PLAUSIBLE-no-single-source guard then DROPS the row (no rationale,
    no code patterns to support HYPOTHESISED).

    Per v0.2.5 corrective C4-pivot (AC.V025-C4P.5 extension): the
    second-pass guard at :func:`synthesis._apply_plausible_demotion_or_drop_guard`
    handles the band-rule-violation surface area uncovered by the first
    pass. Rows with literally zero evidence cannot satisfy any band
    structurally; dropping is the only safe action (vs raising, which
    would cascade-fail the entire synthesis stage).

    Pre-pivot: validator raised StageError; entire synthesis exited 2.
    Post-pivot: row is dropped with a logged warning; remaining
    objectives validate cleanly.
    """
    row = _verified_no_two_sources_row()
    # No survey, no readme, no design-doc. After first-pass demotion to
    # PLAUSIBLE the second-pass guard drops this row (no rationale, no
    # code patterns).
    payload = {
        "objectives": [row],
        "constraints": [],
        "capabilities": [],
    }

    with caplog.at_level(logging.WARNING, logger="loam_odd_extractor.synthesis"):
        objectives, constraints, capabilities = _validate_rows(
            payload, repo_sha="abc1234"
        )

    # Row was dropped — no objectives surface.
    assert len(objectives) == 0, (
        f"Row with no single-source evidence must be dropped by the "
        f"second-pass guard; got {len(objectives)} objectives"
    )
    # Drop logged.
    log_messages = [r.message for r in caplog.records]
    assert any("DROPPING" in m for m in log_messages), (
        f"Drop must be logged; got messages: {log_messages}"
    )


def test_AC_V025_C4_2_validate_rows_passthrough_for_compliant_verified() -> None:
    """A VERIFIED row that genuinely satisfies the two-source rule
    passes through unchanged — the guard is a no-op for compliant input.
    """
    row = _verified_with_two_sources_row()
    payload = {
        "objectives": [row],
        "constraints": [],
        "capabilities": [],
    }

    objectives, constraints, capabilities = _validate_rows(
        payload, repo_sha=None
    )

    assert len(objectives) == 1
    assert objectives[0].confidence == ConfidenceBand.VERIFIED
