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

"""AC.RVL.7 (OUTCOME-ALTITUDE) — production ``retrieve()``, no pre-arranged
retrieval state.

Given a fixture corpus where MORE records clear the relevance floor than the
legacy count of 5, the production entry-point injects records beyond the 6th
and the cut is BYTE-BUDGET-driven — not a count wall at 5. A cue whose only
matches clear no floor (a token present in nothing) surfaces an EMPTY block.

Drives the real resolver from an empty starting state (a freshly-written
on-disk corpus; no seeded ranking): work-anchor -> corpus search (floor,
no count) -> merge (backstop no-op) -> render (byte budget).
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace import retrieval as R
from loam.primary_persona.keep_pace.retrieval import RetrievalConfig, retrieve

_N = 12  # > the legacy count of 5


def _write_corpus(memory_dir: Path, n: int) -> None:
    memory_dir.mkdir(parents=True, exist_ok=True)
    # Each doc carries its OWN rare token so every doc is a strong (df=1) match
    # that clears the relevance floor; the prompt ORs all the tokens.
    for i in range(n):
        (memory_dir / f"feedback_rule_{i}.md").write_text(
            f"# widgetronic{i} directive\n\n"
            f"The widgetronic{i} directive governs subsystem {i}.\n",
            encoding="utf-8",
        )


def _config(tmp_path: Path, memory_dir: Path) -> RetrievalConfig:
    return RetrievalConfig(
        workspace_root=tmp_path,
        memory_dir=memory_dir,
        claude_homes=(),
        objectives_home=tmp_path / "no-obj",
    )


def _prompt(n: int) -> str:
    return "surface the widgetronic directives " + " ".join(
        f"widgetronic{i}" for i in range(n)
    )


def _n_lines(block: str) -> int:
    return block.count("\n  - ")


def test_AC_RVL_7_more_than_five_inject_not_cut_at_five(tmp_path: Path) -> None:
    memory_dir = tmp_path / "corpus"
    _write_corpus(memory_dir, _N)
    block = retrieve(prompt=_prompt(_N), config=_config(tmp_path, memory_dir))
    assert block, "the production surface produced no injection for a relevant query"
    n = _n_lines(block)
    # The injected set contains records BEYOND the 6th — the count backstop did
    # NOT cut at the legacy 5.
    assert n > 6, f"expected records beyond the 6th; only {n} injected (count wall?)"
    assert n == _N, f"all {_N} floor-clearing records fit the byte budget; got {n}"


def test_AC_RVL_7_cut_is_byte_budget_driven_not_count(
    tmp_path: Path, monkeypatch
) -> None:
    """The cut is the BYTE budget: a smaller budget admits fewer records, a
    larger one admits more — and the smaller cut still lands ABOVE 5, so it is
    the byte budget cutting, never a count wall at 5."""
    memory_dir = tmp_path / "corpus"
    _write_corpus(memory_dir, _N)
    cfg = _config(tmp_path, memory_dir)

    # Measure a single rendered pointer line's cost to size a byte budget that
    # cuts strictly between 6 and _N.
    full = retrieve(prompt=_prompt(_N), config=cfg)
    per_line = len(full) // max(_n_lines(full), 1)
    tight_cap = per_line * 8  # room for ~8 lines — above 5, below _N

    monkeypatch.setattr(R, "INJECTION_CHAR_CAP", tight_cap)
    tight = retrieve(prompt=_prompt(_N), config=cfg)
    n_tight = _n_lines(tight)
    assert 5 < n_tight < _N, (
        f"the byte budget must cut ABOVE the legacy 5 and below the full set; "
        f"got {n_tight} at cap {tight_cap}"
    )
    assert len(tight) <= tight_cap

    # Raising the budget admits MORE records — no count wall behind the budget.
    monkeypatch.setattr(R, "INJECTION_CHAR_CAP", per_line * (_N + 4))
    loose = retrieve(prompt=_prompt(_N), config=cfg)
    assert _n_lines(loose) > n_tight, "raising the byte budget must admit more"


def test_AC_RVL_7_floorless_cue_surfaces_empty(tmp_path: Path) -> None:
    """A cue whose only matches clear no floor (a token present in nothing)
    surfaces an EMPTY block — empty-OK, never a forced top-1."""
    memory_dir = tmp_path / "corpus"
    _write_corpus(memory_dir, _N)
    block = retrieve(
        prompt="quixotropic nonexistent token that matches nothing at all",
        config=_config(tmp_path, memory_dir),
    )
    assert block == "", f"a no-floor-clearing cue must surface empty; got {block!r}"
