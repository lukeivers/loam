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

"""AC.DMP.1 — every dispatched subagent's composed context bundle
carries a memory tier in which decision records relevant to the task
text are injected whole (per the AC.SRF.3 contract), within the tier's
named budget; the bundle's fail-soft contract is preserved — a
degraded or empty memory tier never blocks or aborts a dispatch.

Memory recall cycle, Slice 4.
"""

from __future__ import annotations

from pathlib import Path

from loam.frame_kernel.bundle import (
    MICROKERNEL_PRIME_MARKER,
    compose_bundle,
)
from loam.primary_persona.decision_ledger import write_decision
from loam.primary_persona.file_memory import memory_dir_for_workspace


def _fixture_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    (ws / "kernel").mkdir(parents=True)
    (ws / "kernel" / "loam-microkernel.md").write_text(
        "# loam microkernel\nIF dispatched THEN honor the fence.\n",
        encoding="utf-8",
    )
    return ws


def test_AC_DMP_1_relevant_record_injected_whole(tmp_path: Path) -> None:
    ws = _fixture_workspace(tmp_path)
    mem = memory_dir_for_workspace(ws)
    write_decision(
        mem,
        question="How large is the Tilth raise ask?",
        ruling="$750,000 at $4M post-money valuation",
        reasoning="AI-era raises differ; comp-heavy is fine founder-led.",
        entities=("Tilth", "Alan", "raise", "valuation"),
        aliases=("the raise",),
        source="telegram message 14053, 2026-06-07",
        workstream="tilth",
    )
    bundle = compose_bundle(
        {
            "workspace": {"project_dir": str(ws)},
            "prompt": "plan the Tilth raise workstream for next week",
        }
    )
    # Three-tier shape preserved (fence: tier order byte-for-byte).
    assert bundle.index(MICROKERNEL_PRIME_MARKER) < bundle.index(
        "=== active workstream context ==="
    ) < bundle.index("=== relevant memory ===")
    # The ruling arrives WHOLE in the memory tier (AC.SRF.3 contract).
    assert "$750,000" in bundle
    assert "AI-era raises differ" in bundle
    assert "telegram message 14053" in bundle


def test_AC_DMP_1_open_record_rides_along(tmp_path: Path) -> None:
    ws = _fixture_workspace(tmp_path)
    mem = memory_dir_for_workspace(ws)
    write_decision(
        mem,
        question="Who is Aaron in the deal?",
        ruling="(open)",
        reasoning="Owner has not ruled yet.",
        entities=("Aaron", "deal"),
        source="test",
        status="open",
    )
    bundle = compose_bundle(
        {
            "workspace": {"project_dir": str(ws)},
            "prompt": "summarize the git safety protocol work",
        }
    )
    assert "Who is Aaron in the deal?" in bundle, (
        "AC.DMP.1: an open ruling reaches dispatched agents without an "
        "explicit query"
    )


def test_AC_DMP_1_degraded_tier_never_aborts(tmp_path: Path) -> None:
    # Fail-soft preserved (AC.SACH.4 byte-for-byte in outcome): no
    # store, no ledger, even a malformed envelope — compose_bundle
    # still returns a three-tier bundle, never raises.
    ws = _fixture_workspace(tmp_path)
    bundle = compose_bundle(
        {"workspace": {"project_dir": str(ws)}, "prompt": "anything"}
    )
    assert MICROKERNEL_PRIME_MARKER in bundle
    assert "=== relevant memory ===" in bundle

    for envelope in (None, {}, {"workspace": "not-a-dict"}, []):
        out = compose_bundle(envelope)
        assert "=== relevant memory ===" in out


def test_AC_DMP_1_tier_within_named_budget(tmp_path: Path) -> None:
    ws = _fixture_workspace(tmp_path)
    mem = memory_dir_for_workspace(ws)
    for i in range(10):
        write_decision(
            mem,
            question=f"Budget probe ruling {i} about widgets?",
            ruling=f"Widget ruling {i}",
            reasoning="x" * 2000,
            entities=("widgets", "probe"),
            source="test",
        )
    bundle = compose_bundle(
        {
            "workspace": {"project_dir": str(ws)},
            "prompt": "work on the widgets probe plan",
        }
    )
    from loam.primary_persona.keep_pace.retrieval import INJECTION_CHAR_CAP

    memory_tier = bundle.split("=== relevant memory ===", 1)[1]
    assert len(memory_tier) <= INJECTION_CHAR_CAP + 200, (
        "AC.DMP.1: the memory tier honors the named retrieval budget"
    )
