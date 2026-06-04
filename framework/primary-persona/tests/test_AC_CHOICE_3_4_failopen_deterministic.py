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

"""AC.CHOICE.3 / AC.CHOICE.4 — fail-open-on-error + deterministic-no-LLM.

AC.CHOICE.3: any matrix error (missing file, unreadable, malformed cell)
degrades the resolver to the openness default lens-set WITHOUT raising —
the per-turn surface proceeds exactly as a fail-open turn does. The
resolver NEVER wedges the turn (mirrors load_interaction_model's
contract).

AC.CHOICE.4: the resolver makes NO model/LLM call and performs NO store
mutation on the per-turn path — it is a deterministic read over the #34
cell (D-WMS6.2, mirroring classify_area). Determinism is verified by
repeated identical reads + the absence of any spawn-isolation / LLM
import on the resolver path.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loam.primary_persona.keep_pace import lens_choice as lc


def test_AC_CHOICE_3_garbled_matrix_failopen_no_raise(tmp_path: Path) -> None:
    # A wholly-garbled matrix file: the resolver degrades to a non-empty
    # default and does NOT raise.
    (tmp_path / "INTERACTION-MODEL.md").write_text(
        "}{ this is not a matrix at all ][ <<<", encoding="utf-8"
    )
    chosen = lc.resolve_lens_set(claude_home=tmp_path)
    assert chosen, "garbled matrix did not fail open to a non-empty default"


def test_AC_CHOICE_3_unreadable_dir_failopen(tmp_path: Path) -> None:
    # claude_home points at a path with no readable matrix — fail open,
    # never raise.
    missing = tmp_path / "does-not-exist"
    chosen = lc.resolve_lens_set(claude_home=missing)
    assert chosen


def test_AC_CHOICE_3_unrecognised_value_failopen_to_exposure(
    tmp_path: Path,
) -> None:
    # A work-tracking/preferred-lens cell carrying a value NOT in the
    # vocabulary degrades to the exposure-derived default (never empty),
    # not to a raise (RF #5 — the over-fit floor).
    (tmp_path / "INTERACTION-MODEL.md").write_text(
        "## work-tracking\n"
        "preferred-lens: { value: holographic-gantt, confidence: high, "
        "evidence: [] }\n",
        encoding="utf-8",
    )
    chosen = lc.resolve_lens_set(claude_home=tmp_path)
    assert chosen, "unrecognised lens value did not degrade to a default"


def test_AC_CHOICE_4_deterministic_repeated_reads_identical(
    tmp_path: Path,
) -> None:
    (tmp_path / "INTERACTION-MODEL.md").write_text(
        "## work-tracking\n"
        "preferred-lens: { value: projects, confidence: high, evidence: [] }\n",
        encoding="utf-8",
    )
    first = lc.resolve_lens_set(claude_home=tmp_path)
    for _ in range(5):
        assert lc.resolve_lens_set(claude_home=tmp_path) == first


def test_AC_CHOICE_4_no_llm_import_on_resolver_path() -> None:
    # The resolver source must not reach for an LLM / spawn-isolation
    # seam (D-WMS6.2 — no model call on the hot path). A static check on
    # the module source is the cheapest faithful guard.
    src = Path(lc.__file__).read_text(encoding="utf-8")
    for forbidden in (
        "spawn_isolated_claude",
        "claude_print_client",
        "anthropic",
        "ClaudeWorkIntentExtractor",
    ):
        assert forbidden not in src, (
            f"resolver path imports {forbidden!r} — LLM on the hot path "
            "(D-WMS6.2 violation)"
        )


def test_AC_CHOICE_4_no_store_mutation_on_read(tmp_path: Path) -> None:
    # The resolver writes nothing on a read — the matrix file is byte-for-
    # byte untouched after a resolve (no side-effect on the per-turn path).
    matrix = (
        "## work-tracking\n"
        "preferred-lens: { value: projects, confidence: high, evidence: [] }\n"
    )
    path = tmp_path / "INTERACTION-MODEL.md"
    path.write_text(matrix, encoding="utf-8")
    before = path.read_text()
    lc.resolve_lens_set(claude_home=tmp_path)
    assert path.read_text() == before
