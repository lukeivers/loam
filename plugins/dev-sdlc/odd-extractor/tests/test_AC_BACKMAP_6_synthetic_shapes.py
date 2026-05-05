"""AC.BACKMAP.6 — Component tests against 3 synthetic backing-map fixtures.

- tight-1-to-1: 3 objectives + 5 rows; clean per-objective mapping.
- loose-multi-row: 2 objectives + 12 rows; multi-row + orphans.
- no-evidence-hypothesised: 4 mixed-band + 6 mostly-orphan rows.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from loam_odd_extractor import (
    BackingMap,
    ConfidenceBand,
    Objective,
    ObjectiveEvidence,
    populate_backing_map,
)


_FIXTURES_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "backing-map"
)


def _load_objectives(path: Path) -> list[Objective]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    out: list[Objective] = []
    for d in raw["objectives"]:
        ev = d["evidence"]
        out.append(
            Objective(
                objective_id=d["objective_id"],
                text=d["text"],
                confidence=ConfidenceBand(d["confidence"]),
                evidence=ObjectiveEvidence(
                    readme_excerpts=ev.get("readme_excerpts", []),
                    rationale=ev.get("rationale"),
                ),
                domain=d["domain"],
            )
        )
    return out


def _load_rows(path: Path) -> list[dict]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return list(raw["rows"])


class _FixtureClient:
    """Stub Anthropic client whose verdict mirrors a fixture-tuned rule:
    rows whose path matches an objective's domain → STRONG;
    rows whose symbol matches → WEAK; otherwise NONE.
    """

    def __init__(self) -> None:
        self.messages = self
        self.invocations = 0
        self.last_pairs: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.invocations += 1
        user_text = kwargs["messages"][0]["content"]
        start = user_text.find("[")
        end = user_text.rfind("]")
        pairs = json.loads(user_text[start : end + 1])
        self.last_pairs = pairs
        out: list[dict[str, Any]] = []
        for p in pairs:
            domain = p["objective_domain"]
            path = p["evidence_path"].lower()
            symbol = p["evidence_symbol"].lower()
            text = (p.get("evidence_text") or "").lower()
            if domain in path or domain in text:
                verdict = "STRONG"
            elif domain in symbol:
                verdict = "WEAK"
            else:
                verdict = "NONE"
            out.append(
                {
                    "objective_id": p["objective_id"],
                    "evidence_row_id": p["evidence_row_id"],
                    "verdict": verdict,
                    "rationale": "fixture-tuned",
                }
            )
        return type(
            "Resp",
            (),
            {
                "content": [type("Block", (), {"text": json.dumps(out)})()],
                "usage": type(
                    "Usage", (), {"input_tokens": 1000, "output_tokens": 200}
                )(),
            },
        )()


def _populate(fixture_dir: Path, tmp_path: Path) -> BackingMap:
    objs = _load_objectives(fixture_dir / "objectives.yaml")
    rows = _load_rows(fixture_dir / "evidence-rows.yaml")
    client = _FixtureClient()
    return populate_backing_map(
        objs,
        rows,
        extraction_id=fixture_dir.name,
        anthropic_client=client,
        extraction_dir=tmp_path,
    )


def test_tight_1_to_1_each_objective_has_strong(tmp_path: Path) -> None:
    bm = _populate(_FIXTURES_ROOT / "tight-1-to-1", tmp_path)
    assert len(bm.entries) == 3
    # Every entry has at least one STRONG match.
    for entry in bm.entries:
        strongs = [r for r in entry.evidence_rows if r.confidence == "STRONG"]
        assert len(strongs) >= 1, f"{entry.objective_id} has no STRONG"
    # Orphans contain the logger; util/log lands as orphan.
    orphan_paths = [o.path for o in bm.orphan_rows]
    assert "src/util/log.js" in orphan_paths


def test_loose_multi_row_majority_orphans(tmp_path: Path) -> None:
    bm = _populate(_FIXTURES_ROOT / "loose-multi-row", tmp_path)
    assert len(bm.entries) == 2
    # 4 util/* paths → orphans.
    util_orphans = [
        o for o in bm.orphan_rows if "/util/" in o.path
    ]
    assert len(util_orphans) == 4


def test_no_evidence_hypothesised_h_band_unmatched_excluded(
    tmp_path: Path,
) -> None:
    bm = _populate(
        _FIXTURES_ROOT / "no-evidence-hypothesised", tmp_path
    )
    # 2 H-band objectives shouldn't appear in unmatched_objective_ids
    # even though they have empty backing.
    assert "O.future-llm.1" not in bm.unmatched_objective_ids
    assert "O.future-export.1" not in bm.unmatched_objective_ids
    # 1 P-band has weak signal only — landed in unmatched only if
    # entry has zero rows (STRONG OR WEAK both included). The
    # alerts.1 P-band objective gets nothing → unmatched.
    assert "O.alerts.1" in bm.unmatched_objective_ids
