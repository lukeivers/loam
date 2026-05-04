# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.BANDS.7 (PM-side) — RatificationBatch helper composes with
PMRuntime.

Per v0.1.8 Cycle 2 plan-doc §4 + §3 (per-project-pm secondary fence).

- ``RatificationBatch.from_banded_acs`` constructs from a list of
  banded-AC mappings.
- ``RatificationBatch.enqueue`` enqueues each pair via
  :meth:`PMRuntime.enqueue_decision`.
- Provenance string format ``odd-extract:{extraction_id}:{ac_id}``.
- Question text carries ac_id + current band.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.per_project_pm import PMRuntime, RatificationBatch


def _author_pm(workspace_root: Path, pm_name: str) -> None:
    pm_dir = workspace_root / "workspace" / ".loam" / "pms" / pm_name
    pm_dir.mkdir(parents=True)
    (pm_dir / "contract.yaml").write_text(
        yaml.safe_dump(
            {
                "schema_version": 1,
                "handle": pm_name,
                "project_name": "test",
                "project_kind": "general",
                "owner_name": "Tester",
                "workspace_root": str(workspace_root),
                "decision_surfacing_policy": {
                    "onboarding_mode": False,
                    "max_questions_per_turn": 1,
                    "cool_down_seconds": 0,
                    "require_owner_response": False,
                },
            }
        )
    )


@pytest.fixture
def tmp_workspace_with_pm(tmp_path: Path) -> tuple[Path, str]:
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "workspace").mkdir()
    pm_name = "rb-test-pm"
    _author_pm(ws, pm_name)
    return ws, pm_name


def _banded_ac_mappings() -> list[dict]:
    """Three banded-AC dicts — duck-typed input to
    RatificationBatch.from_banded_acs()."""
    return [
        {
            "ac_id": "AC.SYNTH.1",
            "text": "VERIFIED AC text",
            "confidence": "VERIFIED",
            "evidence": {
                "kind": "test",
                "citations": ["t.py::test_x"],
                "repo_sha": "abc1234",
            },
        },
        {
            "ac_id": "AC.SYNTH.2",
            "text": "PLAUSIBLE AC text",
            "confidence": "PLAUSIBLE",
            "evidence": {
                "kind": "source",
                "citations": ["src.py:1-10"],
            },
        },
        {
            "ac_id": "AC.SYNTH.3",
            "text": "HYPOTHESISED AC text",
            "confidence": "HYPOTHESISED",
            "evidence": {
                "kind": "inference",
                "citations": [],
                "rationale": "LLM inferred from comments.",
            },
        },
    ]


def test_from_banded_acs_constructs_three_pairs() -> None:
    batch = RatificationBatch.from_banded_acs(
        extraction_id="test-ext",
        banded_acs=_banded_ac_mappings(),
    )
    assert len(batch.pairs) == 3


def test_provenance_format(tmp_workspace_with_pm: tuple[Path, str]) -> None:
    """Provenance string format: odd-extract:{extraction_id}:{ac_id}."""
    ws, pm_name = tmp_workspace_with_pm
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)

    batch = RatificationBatch.from_banded_acs(
        extraction_id="my-ext-XYZ",
        banded_acs=_banded_ac_mappings(),
    )
    batch.enqueue(pm_runtime)

    queue_path = (
        ws / "workspace" / ".loam" / "pms" / pm_name / "decision-queue.yaml"
    )
    payload = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    queue = payload["queue"]
    expected = {
        "odd-extract:my-ext-XYZ:AC.SYNTH.1",
        "odd-extract:my-ext-XYZ:AC.SYNTH.2",
        "odd-extract:my-ext-XYZ:AC.SYNTH.3",
    }
    actual = {entry["provenance"] for entry in queue}
    assert actual == expected


def test_question_text_includes_ac_id_and_band(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    ws, pm_name = tmp_workspace_with_pm
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)

    batch = RatificationBatch.from_banded_acs(
        extraction_id="ext-text-test",
        banded_acs=_banded_ac_mappings(),
    )
    batch.enqueue(pm_runtime)

    queue_path = (
        ws / "workspace" / ".loam" / "pms" / pm_name / "decision-queue.yaml"
    )
    payload = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    by_provenance = {
        e["provenance"]: e["text"] for e in payload["queue"]
    }
    assert "AC.SYNTH.1" in by_provenance["odd-extract:ext-text-test:AC.SYNTH.1"]
    assert "VERIFIED" in by_provenance["odd-extract:ext-text-test:AC.SYNTH.1"]
    assert "PLAUSIBLE" in by_provenance["odd-extract:ext-text-test:AC.SYNTH.2"]
    assert "HYPOTHESISED" in by_provenance["odd-extract:ext-text-test:AC.SYNTH.3"]


def test_enqueue_returns_count(tmp_workspace_with_pm: tuple[Path, str]) -> None:
    ws, pm_name = tmp_workspace_with_pm
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)

    batch = RatificationBatch.from_banded_acs(
        extraction_id="ext-count-test",
        banded_acs=_banded_ac_mappings(),
    )
    count = batch.enqueue(pm_runtime)
    assert count == 3


def test_from_banded_acs_rejects_empty_extraction_id() -> None:
    with pytest.raises(ValueError):
        RatificationBatch.from_banded_acs(
            extraction_id="",
            banded_acs=_banded_ac_mappings(),
        )


def test_from_banded_acs_rejects_missing_ac_id() -> None:
    with pytest.raises(ValueError):
        RatificationBatch.from_banded_acs(
            extraction_id="ext",
            banded_acs=[
                {
                    "text": "x",
                    "confidence": "PLAUSIBLE",
                    "evidence": {"kind": "source", "citations": ["x"]},
                },
            ],
        )


def test_from_banded_acs_rejects_missing_text() -> None:
    with pytest.raises(ValueError):
        RatificationBatch.from_banded_acs(
            extraction_id="ext",
            banded_acs=[
                {
                    "ac_id": "AC.X",
                    "confidence": "PLAUSIBLE",
                    "evidence": {"kind": "source", "citations": ["x"]},
                },
            ],
        )


def test_from_banded_acs_rejects_missing_confidence() -> None:
    with pytest.raises(ValueError):
        RatificationBatch.from_banded_acs(
            extraction_id="ext",
            banded_acs=[
                {
                    "ac_id": "AC.X",
                    "text": "x",
                    "evidence": {"kind": "source", "citations": ["x"]},
                },
            ],
        )


def test_empty_banded_acs_produces_empty_batch() -> None:
    batch = RatificationBatch.from_banded_acs(
        extraction_id="ext",
        banded_acs=[],
    )
    assert batch.pairs == ()


def test_typed_bandedac_via_model_dump_works(
    tmp_workspace_with_pm: tuple[Path, str],
) -> None:
    """Composes with the odd-extractor's typed BandedAC: callers
    pass ``[ac.model_dump() for ac in banded_acs]`` and the helper
    consumes the dicts."""
    pytest.importorskip("loam_odd_extractor")
    from loam_odd_extractor import BandedAC, ConfidenceBand, Evidence

    ws, pm_name = tmp_workspace_with_pm
    pm_runtime = PMRuntime.from_workspace(ws, pm_name)

    typed = [
        BandedAC(
            ac_id="AC.T.1",
            text="typed AC",
            confidence=ConfidenceBand.PLAUSIBLE,
            evidence=Evidence(kind="source", citations=["x.py:1"]),
        )
    ]
    batch = RatificationBatch.from_banded_acs(
        extraction_id="typed-test",
        banded_acs=[t.model_dump() for t in typed],
    )
    count = batch.enqueue(pm_runtime)
    assert count == 1
