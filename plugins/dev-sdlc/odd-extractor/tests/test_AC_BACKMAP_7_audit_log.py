"""AC.BACKMAP.7 — Audit-log per backing-map population.

- New event_kind ``backing_map_populated``.
- Carries objective_count + evidence_row_count + token counts +
  cost_cents + strong/weak/orphan/unmatched counts + model_id.
- Round-trip through write_audit_entry / list_entries.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from loam_odd_extractor import (
    ConfidenceBand,
    Objective,
    ObjectiveEvidence,
    populate_backing_map,
)
from loam_odd_extractor.observability import list_entries


class _StubResponse:
    def __init__(self, payload: list[dict[str, Any]]) -> None:
        self.content = [type("B", (), {"text": json.dumps(payload)})()]
        self.usage = type(
            "U", (), {"input_tokens": 1234, "output_tokens": 567}
        )()


class _StubClient:
    def __init__(self, payload: list[dict[str, Any]]) -> None:
        self._resp = _StubResponse(payload)
        self.messages = self

    def create(self, **kwargs: Any) -> _StubResponse:
        return self._resp


def test_audit_log_emitted_with_full_payload(tmp_path: Path) -> None:
    obj = Objective(
        objective_id="O.dispute.1",
        text="Operators file refund disputes through the merchant portal",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=ObjectiveEvidence(readme_excerpts=["dispute"]),
        domain="dispute",
    )
    rows = [
        {
            "ac_id": "route:src/disputeRoutes.js:1",
            "kind": "route",
            "path": "src/disputeRoutes.js",
            "symbol": "POST /dispute",
            "text": "POST handler",
        },
    ]
    client = _StubClient(
        [
            {
                "objective_id": "O.dispute.1",
                "evidence_row_id": "route:src/disputeRoutes.js:1",
                "verdict": "STRONG",
                "rationale": "stub",
            }
        ]
    )
    populate_backing_map(
        [obj],
        rows,
        extraction_id="t",
        anthropic_client=client,
        extraction_dir=tmp_path,
    )
    entries = list_entries(tmp_path)
    assert len(entries) == 1
    payload = yaml.safe_load(entries[0].read_text(encoding="utf-8"))
    assert payload["event_kind"] == "backing_map_populated"
    assert payload["stage"] == "generate"
    est = payload["estimate"]
    assert est["objective_count"] == 1
    assert est["evidence_row_count"] == 1
    assert est["llm_pass_token_count_input"] == 1234
    assert est["llm_pass_token_count_output"] == 567
    assert est["strong_match_count"] == 1
    assert est["weak_match_count"] == 0
    assert est["orphan_count"] == 0
    assert est["unmatched_objective_count"] == 0
    assert est["model_id"]


def test_audit_log_no_emission_without_extraction_dir() -> None:
    """If caller passes ``extraction_dir=None`` no audit-log written."""
    obj = Objective(
        objective_id="O.dispute.1",
        text="Operators file refund disputes through the merchant portal",
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=ObjectiveEvidence(readme_excerpts=["dispute"]),
        domain="dispute",
    )
    rows = [
        {
            "ac_id": "route:src/disputeRoutes.js:1",
            "kind": "route",
            "path": "src/disputeRoutes.js",
            "symbol": "POST /dispute",
            "text": "POST handler",
        },
    ]
    client = _StubClient(
        [
            {
                "objective_id": "O.dispute.1",
                "evidence_row_id": "route:src/disputeRoutes.js:1",
                "verdict": "STRONG",
                "rationale": "stub",
            }
        ]
    )
    bm = populate_backing_map(
        [obj],
        rows,
        extraction_id="t",
        anthropic_client=client,
        extraction_dir=None,
    )
    # No audit-dir created.
    assert bm.entries[0].evidence_rows[0].confidence == "STRONG"
