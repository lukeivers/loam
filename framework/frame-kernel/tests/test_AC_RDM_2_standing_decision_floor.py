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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.RDM.2 — given a real-shape envelope with NO derivable task text,
in a workspace whose decision ledger is populated, the memory tier
renders the STANDING FLOOR: open + recent ruled decision records WHOLE
(question/ruling/reasoning/source/status), newest-first, within the
existing injection char budget. With an empty/absent ledger the tier
degrades to the existing markers byte-identically as before.
"""

from __future__ import annotations

from pathlib import Path

from loam.frame_kernel.bundle import (
    MICROKERNEL_PRIME_MARKER,
    compose_bundle,
)
from loam.primary_persona.decision_ledger import write_decision
from loam.primary_persona.file_memory import memory_dir_for_workspace

_MEMORY_UNAVAILABLE_MARKER = "[memory unavailable — no live store or query]"


def _fixture_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    (ws / "kernel").mkdir(parents=True)
    (ws / "kernel" / "loam-microkernel.md").write_text(
        "# loam microkernel\nIF dispatched THEN honor the fence.\n",
        encoding="utf-8",
    )
    return ws


def _no_task_text_envelope(ws: Path) -> dict:
    # Real-shape: common fields only, and a transcript_path that does
    # not exist — task text is NOT derivable by construction.
    return {
        "session_id": "s-1",
        "transcript_path": str(ws / "no-such-transcript.jsonl"),
        "cwd": str(ws),
        "agent_id": "a-1",
        "agent_type": "general-purpose",
        "hook_event_name": "SubagentStart",
    }


def test_AC_RDM_2_floor_carries_ruled_and_open_records_whole(
    tmp_path: Path,
) -> None:
    ws = _fixture_workspace(tmp_path)
    mem = memory_dir_for_workspace(ws)
    write_decision(
        mem,
        question="How large is the Tilth raise ask?",
        ruling="$750,000 at $4M post-money valuation",
        reasoning="AI-era raises differ; comp-heavy is fine founder-led.",
        entities=("Tilth", "raise"),
        source="telegram message 14053, 2026-06-07",
        workstream="tilth",
    )
    write_decision(
        mem,
        question="Who signs the lease?",
        ruling="(open)",
        reasoning="Owner has not ruled yet.",
        entities=("lease",),
        source="test",
        status="open",
    )

    bundle = compose_bundle(_no_task_text_envelope(ws))

    assert MICROKERNEL_PRIME_MARKER in bundle
    memory_tier = bundle.split("=== relevant memory ===", 1)[1]
    assert _MEMORY_UNAVAILABLE_MARKER not in memory_tier, (
        "AC.RDM.2: a populated ledger must produce the standing floor, "
        "not the degraded marker"
    )
    # The ruled record arrives WHOLE (AC.SRF.3 contract).
    assert "$750,000 at $4M post-money valuation" in memory_tier
    assert "AI-era raises differ" in memory_tier
    assert "telegram message 14053" in memory_tier
    # The open question rides along.
    assert "Who signs the lease?" in memory_tier


def test_AC_RDM_2_no_ledger_degrades_byte_identically(
    tmp_path: Path,
) -> None:
    ws = _fixture_workspace(tmp_path)
    bundle = compose_bundle(_no_task_text_envelope(ws))
    memory_tier = bundle.split("=== relevant memory ===", 1)[1].strip()
    assert memory_tier == _MEMORY_UNAVAILABLE_MARKER, (
        "AC.RDM.2: with no ledger the tier must degrade to the existing "
        "marker exactly as before"
    )


def test_AC_RDM_2_floor_respects_injection_budget(tmp_path: Path) -> None:
    ws = _fixture_workspace(tmp_path)
    mem = memory_dir_for_workspace(ws)
    for i in range(8):
        write_decision(
            mem,
            question=f"Open budget probe {i}?",
            ruling="(open)",
            reasoning="y" * 3000,
            entities=("probe",),
            source="test",
            status="open",
        )
        write_decision(
            mem,
            question=f"Ruled budget probe {i}?",
            ruling=f"ruling {i}",
            reasoning="x" * 3000,
            entities=("probe",),
            source="test",
        )

    bundle = compose_bundle(_no_task_text_envelope(ws))

    from loam.primary_persona.keep_pace.retrieval import INJECTION_CHAR_CAP

    memory_tier = bundle.split("=== relevant memory ===", 1)[1]
    assert len(memory_tier) <= INJECTION_CHAR_CAP + 200, (
        "AC.RDM.2: the standing floor honors the existing injection "
        "budget (no second budget to drift)"
    )
    # And it still renders the floor, not the degraded marker.
    assert _MEMORY_UNAVAILABLE_MARKER not in memory_tier


def test_AC_RDM_2_fail_soft_never_raises(tmp_path: Path) -> None:
    # Degenerate envelopes still compose a three-tier bundle (AC.SACH.4
    # posture unchanged).
    for envelope in (None, {}, {"cwd": ""}, []):
        out = compose_bundle(envelope)
        assert "=== relevant memory ===" in out
