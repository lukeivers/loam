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

"""AC.SRF.3 — the per-turn injection budget accommodates at least three
whole structured records (a named, tunable ~5KB-class constant); small
structured hits are injected WHOLE — ruling + reasoning + source
pointer — never truncated to a one-line pointer; the dispatch-bundle
memory tier honors the same whole-record contract within its own named
budget. A record that does not fit the remaining budget is dropped
whole, never half-emitted.

Memory recall cycle, Slice 2.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace import retrieval as kp_retrieval
from loam.primary_persona.keep_pace.retrieval import _render_injection
from loam.primary_persona import memory_consumer
from loam.primary_persona.memory_consumer import _render_retrieval
from loam.primary_persona import file_memory


# A representative whole decision record — ruling + reasoning + source
# pointer — sized like a real ledger record (~1.2KB).
_RECORD_TEXT = (
    "question: How large is the Tilth raise?\n"
    "ruling: $750,000\n"
    "reasoning: "
    + ("Sized against the runway model and the hiring plan. " * 18)
    + "\nsource: discord message 1514065518493958214"
)


def test_AC_SRF_3_budgets_are_named_and_5kb_class() -> None:
    # The named, tunable constants — sized for >= 3 whole records.
    assert kp_retrieval.INJECTION_CHAR_CAP >= 3 * (len(_RECORD_TEXT) + 100)
    assert memory_consumer.MEMORY_RETRIEVAL_CHAR_CAP >= 3 * (
        len(_RECORD_TEXT) + 100
    )
    # The file-backed contributor's mirror stays in lockstep.
    assert (
        file_memory.MEMORY_RETRIEVAL_CHAR_CAP
        == memory_consumer.MEMORY_RETRIEVAL_CHAR_CAP
    )


def test_AC_SRF_3_keep_pace_three_whole_records_fit() -> None:
    hits = [
        {
            "pointer": f"record {i}",
            "path": f"/m/decisions/r{i}.md",
            "score": 1.0,
            "_whole_record": True,
            "record_text": _RECORD_TEXT,
        }
        for i in range(3)
    ]
    block = _render_injection(hits, cap=kp_retrieval.INJECTION_CHAR_CAP)
    assert block.count("ruling: $750,000") == 3, (
        "AC.SRF.3: the budget must accommodate three whole records"
    )
    assert block.count("source: discord message") == 3, (
        "AC.SRF.3: records carry their source pointer whole"
    )


def test_AC_SRF_3_keep_pace_record_never_half_emitted() -> None:
    # A cap too small for the record: the record drops WHOLE and the
    # remaining budget keeps filling with pointer lines — never a
    # truncated record fragment.
    hits = [
        {
            "pointer": "big record",
            "path": "/m/decisions/big.md",
            "score": 2.0,
            "_whole_record": True,
            "record_text": _RECORD_TEXT,
        },
        {"pointer": "small pointer", "path": "/m/small.md", "score": 1.0},
    ]
    cap = len(_RECORD_TEXT) // 2  # cannot fit the record
    block = _render_injection(hits, cap=cap)
    assert "ruling: $750,000" not in block, (
        "AC.SRF.3: a record that does not fit must drop whole"
    )
    assert "reasoning:" not in block, "no half-emitted record fragment"
    assert "small pointer" in block, (
        "pointer lines keep filling the remaining budget"
    )


def test_AC_SRF_3_dispatch_render_records_arrive_whole() -> None:
    out = _render_retrieval(
        {
            "query": "tilth raise",
            "results": [],
            "episodes": [
                {
                    "episode_uuid": "ep-1",
                    "name": "context-ep",
                    "content": "Related discussion about the raise.",
                    "group_id": "g",
                    "valid_at": None,
                    "path": "/m/e.md",
                },
            ],
            "records": [
                {
                    "name": "tilth-raise-size",
                    "path": "/m/decisions/tilth-raise.md",
                    "record_text": _RECORD_TEXT,
                },
            ],
        },
        cap=memory_consumer.MEMORY_RETRIEVAL_CHAR_CAP,
    )
    # The whole record — ruling + reasoning + source — present verbatim.
    assert "ruling: $750,000" in out
    assert "source: discord message 1514065518493958214" in out
    assert "=== record: tilth-raise-size (/m/decisions/tilth-raise.md) ===" in out
    # Records render FIRST (highest signal density).
    assert out.index("=== record:") < out.index("- [episode]")


def test_AC_SRF_3_dispatch_render_record_never_half_emitted() -> None:
    out = _render_retrieval(
        {
            "query": "x",
            "results": [],
            "episodes": [],
            "records": [
                {
                    "name": "too-big",
                    "path": "/m/d/big.md",
                    "record_text": _RECORD_TEXT * 10,
                },
            ],
        },
        cap=1000,  # cannot fit the record
    )
    assert "ruling: $750,000" not in out, (
        "AC.SRF.3: an oversized record drops whole, never truncates"
    )
