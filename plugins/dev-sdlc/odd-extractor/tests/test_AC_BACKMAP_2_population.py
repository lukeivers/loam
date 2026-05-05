"""AC.BACKMAP.2 — populate_backing_map heuristic pre-filter +
LLM-pass classifier.

- Stub Anthropic client returning canned scores.
- Assert pre-filter narrowing → top-K=8.
- Assert single batched LLM invocation.
- Assert STRONG / WEAK / NONE classification → entry / orphan split.
- Assert cost-band envelope enforcement (estimate-vs-ceiling halt).
- Assert >200-pair pre-filter halt before LLM fires.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from loam_odd_extractor import (
    ConfidenceBand,
    Objective,
    ObjectiveEvidence,
    populate_backing_map,
    StageError,
)


class _StubResponse:
    """Stub Anthropic Messages API response shape."""

    def __init__(self, json_payload: list[dict[str, Any]], *, in_tok: int = 1000, out_tok: int = 200) -> None:
        text = json.dumps(json_payload)
        self.content = [type("Block", (), {"text": text})()]
        self.usage = type("Usage", (), {"input_tokens": in_tok, "output_tokens": out_tok})()


class _StubMessages:
    def __init__(self, response: _StubResponse) -> None:
        self._response = response
        self.invocations = 0

    def create(self, **kwargs: Any) -> _StubResponse:
        self.invocations += 1
        self.last_kwargs = kwargs
        return self._response


class _StubClient:
    def __init__(self, response: _StubResponse) -> None:
        self.messages = _StubMessages(response)


def _build_plausible_objective(oid: str, domain: str, text: str) -> Objective:
    return Objective(
        objective_id=oid,
        text=text,
        confidence=ConfidenceBand.PLAUSIBLE,
        evidence=ObjectiveEvidence(
            readme_excerpts=[f"README mentions {domain}"],
            rationale=None,
        ),
        domain=domain,
    )


def _build_evidence_rows() -> list[dict]:
    """3 dispute-domain rows + 2 unrelated."""
    return [
        {
            "ac_id": "route:src/routes/disputeRoutes.js:42",
            "kind": "route",
            "path": "src/routes/disputeRoutes.js",
            "symbol": "POST /dispute",
            "text": "POST handler for filing dispute",
            "line_range": [42, 47],
        },
        {
            "ac_id": "test:tests/dispute-flow.spec.ts:10",
            "kind": "test",
            "path": "tests/dispute-flow.spec.ts",
            "symbol": "operator files dispute",
            "text": "operator files dispute should complete",
            "line_range": [10, 30],
        },
        {
            "ac_id": "model:src/models/Dispute.js:5",
            "kind": "model",
            "path": "src/models/Dispute.js",
            "symbol": "Dispute",
            "text": "Dispute mongoose schema",
            "line_range": [5, 50],
        },
        {
            "ac_id": "pattern:src/util/log.js:1",
            "kind": "pattern",
            "path": "src/util/log.js",
            "symbol": "logger",
            "text": "logger utility",
            "line_range": [1, 20],
        },
        {
            "ac_id": "pattern:src/util/format.js:1",
            "kind": "pattern",
            "path": "src/util/format.js",
            "symbol": "format",
            "text": "format helpers",
            "line_range": [1, 20],
        },
    ]


def test_populate_basic_strong_weak_none(tmp_path: Path) -> None:
    obj = _build_plausible_objective(
        "O.dispute-flow.1",
        "dispute",
        "Operators file refund disputes through the merchant portal",
    )
    rows = _build_evidence_rows()
    # Stub returns: route+test STRONG, model WEAK, others NONE
    stub_payload: list[dict[str, Any]] = []
    for row in rows:
        ev_id = row["ac_id"]
        if "disputeRoutes" in row["path"]:
            verdict = "STRONG"
        elif "dispute-flow.spec" in row["path"]:
            verdict = "STRONG"
        elif "Dispute.js" in row["path"]:
            verdict = "WEAK"
        else:
            verdict = "NONE"
        stub_payload.append(
            {
                "objective_id": "O.dispute-flow.1",
                "evidence_row_id": ev_id,
                "verdict": verdict,
                "rationale": "stub",
            }
        )

    client = _StubClient(_StubResponse(stub_payload))
    bm = populate_backing_map(
        [obj],
        rows,
        extraction_id="test",
        anthropic_client=client,
        extraction_dir=tmp_path,
    )
    # 1 LLM invocation.
    assert client.messages.invocations == 1
    assert len(bm.entries) == 1
    entry = bm.entries[0]
    confidences = [r.confidence for r in entry.evidence_rows]
    assert confidences.count("STRONG") == 2
    assert confidences.count("WEAK") == 1
    # 3 orphans: WEAK-only (Dispute.js) + 2 no-objective-match (util/*).
    assert len(bm.orphan_rows) == 3
    reasons = sorted(o.reason for o in bm.orphan_rows)
    assert reasons == [
        "no-objective-match",
        "no-objective-match",
        "weak-signal-only",
    ]


def test_populate_kind_test_weighting(tmp_path: Path) -> None:
    """kind=test rows with assertion-verb get a pre-filter bonus."""
    obj = _build_plausible_objective(
        "O.refund.1", "refund", "Operators receive refunds"
    )
    # Only one test row + many irrelevant; pre-filter must include the test.
    rows = [
        {
            "ac_id": "test:tests/refund.spec.ts:1",
            "kind": "test",
            "path": "tests/refund.spec.ts",
            "symbol": "refund flow",
            "text": "operator should receive refund",
            "line_range": [1, 20],
        },
    ]
    stub_payload = [
        {
            "objective_id": "O.refund.1",
            "evidence_row_id": rows[0]["ac_id"],
            "verdict": "STRONG",
            "rationale": "verb+domain",
        }
    ]
    client = _StubClient(_StubResponse(stub_payload))
    bm = populate_backing_map(
        [obj], rows, extraction_id="t", anthropic_client=client,
        extraction_dir=tmp_path,
    )
    assert len(bm.entries[0].evidence_rows) == 1
    assert bm.entries[0].evidence_rows[0].kind == "test"


def test_populate_cost_ceiling_halt(tmp_path: Path) -> None:
    """Estimated cost above ceiling → StageError (no LLM call)."""
    obj = _build_plausible_objective(
        "O.x.1", "x", "X domain outcome description text"
    )
    rows = _build_evidence_rows()
    client = _StubClient(_StubResponse([]))
    with pytest.raises(StageError) as excinfo:
        populate_backing_map(
            [obj],
            rows,
            extraction_id="t",
            anthropic_client=client,
            extraction_dir=tmp_path,
            cost_ceiling_cents=0.0001,  # absurdly low
        )
    assert "ceiling" in str(excinfo.value).lower()
    assert client.messages.invocations == 0


def test_populate_prefilter_overflow_halt(tmp_path: Path) -> None:
    """>200 narrowed pairs → halt before LLM call."""
    # Generate 30 objectives × 8 top-K = 240 narrowed pairs.
    objectives = [
        _build_plausible_objective(
            f"O.dom-{i}.1",
            f"domain{i}",
            f"Outcome {i} satisfies a domain need text",
        )
        for i in range(30)
    ]
    # Each row has the domain token in its text so heuristic finds them.
    rows = []
    for i in range(30):
        for j in range(10):
            rows.append(
                {
                    "ac_id": f"route:src/routes/domain{i}_route_{j}.js:{j}",
                    "kind": "route",
                    "path": f"src/routes/domain{i}_route_{j}.js",
                    "symbol": f"domain{i} handler",
                    "text": f"domain{i} route handler",
                    "line_range": [j, j + 5],
                }
            )
    client = _StubClient(_StubResponse([]))
    with pytest.raises(StageError) as excinfo:
        populate_backing_map(
            objectives,
            rows,
            extraction_id="t",
            anthropic_client=client,
            extraction_dir=tmp_path,
        )
    assert "pre-filter overflow" in str(excinfo.value)
    assert client.messages.invocations == 0


def test_populate_top_k_narrowing(tmp_path: Path) -> None:
    """K=8 narrowing per objective."""
    obj = _build_plausible_objective(
        "O.dom.1", "domain",
        "Outcome about domain that is observed externally"
    )
    # 20 matching rows → K=8 should narrow.
    rows = []
    for j in range(20):
        rows.append(
            {
                "ac_id": f"route:src/routes/domain_handler_{j}.js:1",
                "kind": "route",
                "path": f"src/routes/domain_handler_{j}.js",
                "symbol": f"domain handler {j}",
                "text": f"domain handler {j}",
                "line_range": [j, j + 5],
            }
        )

    captured: list[int] = []

    class _CountClient:
        def __init__(self) -> None:
            self.messages = self

        def create(self, **kwargs: Any) -> _StubResponse:
            user_text = kwargs["messages"][0]["content"]
            data = json.loads(user_text[user_text.find("[") : user_text.rfind("]") + 1])
            captured.append(len(data))
            return _StubResponse([
                {
                    "objective_id": "O.dom.1",
                    "evidence_row_id": d["evidence_row_id"],
                    "verdict": "WEAK",
                    "rationale": "stub",
                }
                for d in data
            ])

    client = _CountClient()
    bm = populate_backing_map(
        [obj], rows, extraction_id="t",
        anthropic_client=client, extraction_dir=tmp_path,
    )
    # Top-K narrowed to 8 pairs for 1 objective.
    assert captured == [8]
    assert len(bm.entries[0].evidence_rows) == 8


def test_populate_no_pairs_no_llm_call(tmp_path: Path) -> None:
    """If the pre-filter narrows to 0 pairs, no LLM call fires."""
    obj = _build_plausible_objective(
        "O.alpha.1", "alpha",
        "Alpha-domain outcome with no evidence overlap"
    )
    rows = [
        {
            "ac_id": "pattern:foo/bar.js:1",
            "kind": "pattern",
            "path": "foo/bar.js",
            "symbol": "unrelated",
            "text": "completely unrelated",
            "line_range": [1, 5],
        },
    ]
    client = _StubClient(_StubResponse([]))
    bm = populate_backing_map(
        [obj], rows, extraction_id="t",
        anthropic_client=client, extraction_dir=tmp_path,
    )
    assert client.messages.invocations == 0
    # Empty backing → orphan + unmatched signal.
    assert bm.entries[0].evidence_rows == []
    assert "O.alpha.1" in bm.unmatched_objective_ids
    assert len(bm.orphan_rows) == 1
