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

"""AC.RVL.3 — the per-turn injected set is bounded ONLY by the byte budget
(best-first, drop-whole on overflow); no count truncation silently decides
which records inject.

Merges many relevant hits (more than the legacy count of 5) through the
production merge + render path and asserts (a) the merged set is NOT cut at 5
by the count backstop, (b) the rendered block respects the byte budget, and
(c) raising the byte budget admits MORE records — no count wall behind it.
"""

from __future__ import annotations

from loam.primary_persona.keep_pace.retrieval import (
    DEFAULT_TOP_N,
    _merge_by_score,
    _render_injection,
)

_N = 20  # > the legacy count of 5, < the DEFAULT_TOP_N backstop


def _hits(n: int) -> list[dict]:
    # Distinct descending scores so ordering is deterministic; short pointers.
    return [
        {"path": f"/x/r{i}.md", "title": f"r{i}", "pointer": f"pointer {i}", "score": 100.0 - i}
        for i in range(n)
    ]


def test_AC_RVL_3_merge_not_cut_at_five_by_count_backstop() -> None:
    # The count backstop is DEFAULT_TOP_N (raised); a normal-volume merge of
    # _N < backstop records survives whole — the count does not cut at 5.
    merged = _merge_by_score(_hits(_N), [], top_n=DEFAULT_TOP_N)
    assert len(merged) == _N, (
        f"the raised count backstop must not cut {_N} records; got {len(merged)}"
    )
    assert _N > 5 and _N < DEFAULT_TOP_N


def test_AC_RVL_3_injection_cut_is_byte_budget_driven() -> None:
    merged = _merge_by_score(_hits(_N), [], top_n=DEFAULT_TOP_N)
    # Size a budget that admits ~8 lines — above the legacy 5, below _N.
    line = "  - pointer 0 [source: /x/r0.md]"
    tight_cap = (len(line) + 1) * 8
    block = _render_injection(merged, cap=tight_cap)
    n = block.count("\n  - ")
    assert 5 < n < _N, f"the byte budget must cut above 5 and below the full set; got {n}"
    assert len(block) <= tight_cap, "the rendered block must respect the byte budget"


def test_AC_RVL_3_raising_budget_admits_more_no_count_wall() -> None:
    merged = _merge_by_score(_hits(_N), [], top_n=DEFAULT_TOP_N)
    line = "  - pointer 0 [source: /x/r0.md]"
    small = _render_injection(merged, cap=(len(line) + 1) * 8)
    large = _render_injection(merged, cap=(len(line) + 1) * (_N + 4))
    assert large.count("\n  - ") > small.count("\n  - "), (
        "raising the byte budget must admit more records — no count wall behind it"
    )
    # With ample budget every record injects (bounded only by the byte budget).
    assert large.count("\n  - ") == _N


def test_AC_RVL_3_drop_whole_never_half_on_overflow() -> None:
    # A record that would overflow the remaining budget is dropped WHOLE — the
    # block never contains a truncated pointer.
    merged = _merge_by_score(_hits(_N), [], top_n=DEFAULT_TOP_N)
    line = "  - pointer 0 [source: /x/r0.md]"
    block = _render_injection(merged, cap=(len(line) + 1) * 8)
    for rendered_line in block.split("\n")[1:]:  # skip the header
        assert rendered_line.strip().startswith("- pointer "), (
            f"every emitted line is a complete pointer; got {rendered_line!r}"
        )
