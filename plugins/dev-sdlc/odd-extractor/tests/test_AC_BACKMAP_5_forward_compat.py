"""AC.BACKMAP.5 — Forward-compat for v0.2.4 gap-analysis + v0.2.5
negative-alignment.

- OrphanRow.reason enum accepts three values (extensible carrier).
- unmatched_objective_ids populated for non-HYPOTHESISED objectives
  with empty backing.
- HYPOTHESISED-band objectives do NOT enter unmatched_objective_ids
  even with empty backing.
"""

from __future__ import annotations

from pathlib import Path


from loam_odd_extractor import (
    ConfidenceBand,
    Objective,
    ObjectiveEvidence,
    OrphanRow,
    populate_backing_map,
)


def test_orphan_row_three_reason_values() -> None:
    for reason in (
        "no-objective-match",
        "weak-signal-only",
        "anti-feature-candidate",
    ):
        row = OrphanRow(
            evidence_row_id=f"pattern:src/x_{reason}.js:1",
            kind="pattern",
            path=f"src/x_{reason}.js",
            reason=reason,  # type: ignore[arg-type]
        )
        assert row.reason == reason


class _StubResp:
    def __init__(self, payload):
        import json
        text = json.dumps(payload)
        self.content = [type("B", (), {"text": text})()]
        self.usage = type("U", (), {"input_tokens": 100, "output_tokens": 50})()


class _StubClient:
    def __init__(self, payload):
        self._resp = _StubResp(payload)
        self.messages = self
        self.invocations = 0

    def create(self, **kwargs):
        self.invocations += 1
        return self._resp


def test_unmatched_excludes_hypothesised(tmp_path: Path) -> None:
    """HYPOTHESISED objectives with empty backing don't enter
    unmatched_objective_ids.
    """
    objectives = [
        Objective(
            objective_id="O.plausible.1",
            text="Plausible-band outcome present in the codebase",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=ObjectiveEvidence(
                readme_excerpts=["x"],
            ),
            domain="plausible",
        ),
        Objective(
            objective_id="O.hypothesised.1",
            text="Hypothesised forward-looking outcome not yet built",
            confidence=ConfidenceBand.HYPOTHESISED,
            evidence=ObjectiveEvidence(
                rationale="LLM inferred from comments alone",
            ),
            domain="hypothesised",
        ),
    ]
    rows = [
        {
            "ac_id": "pattern:src/util.js:1",
            "kind": "pattern",
            "path": "src/util.js",
            "symbol": "util",
            "text": "unrelated",
        },
    ]
    client = _StubClient([])  # no STRONG/WEAK matches
    bm = populate_backing_map(
        objectives, rows, extraction_id="t",
        anthropic_client=client, extraction_dir=tmp_path,
    )
    # Plausible objective has no backing → unmatched.
    # Hypothesised has no backing → NOT unmatched.
    assert "O.plausible.1" in bm.unmatched_objective_ids
    assert "O.hypothesised.1" not in bm.unmatched_objective_ids


def test_unmatched_objective_ids_empty_when_all_matched(tmp_path: Path) -> None:
    """When every objective gets a STRONG match, unmatched is empty."""
    objectives = [
        Objective(
            objective_id="O.dispute.1",
            text="Operators file disputes through the merchant portal",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=ObjectiveEvidence(readme_excerpts=["dispute"]),
            domain="dispute",
        ),
    ]
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
        objectives, rows, extraction_id="t",
        anthropic_client=client, extraction_dir=tmp_path,
    )
    assert bm.unmatched_objective_ids == []


def test_orphan_reason_open_for_extension() -> None:
    """The Literal carries 3 values today; future cycles may add more.

    This test asserts the current 3 are accepted (not that the enum is
    closed at compile time — the Literal grows additively).
    """
    valid = ("no-objective-match", "weak-signal-only", "anti-feature-candidate")
    for r in valid:
        OrphanRow(
            evidence_row_id="pattern:x.js",
            kind="pattern",
            path="x.js",
            reason=r,  # type: ignore[arg-type]
        )
