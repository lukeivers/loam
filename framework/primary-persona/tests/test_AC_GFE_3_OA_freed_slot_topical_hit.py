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

"""AC.GFE.3 — OUTCOME-ALTITUDE (``outcome-altitude: true``): the freed slot goes
to a real topical hit.

The direct proof of Stage 1a's objective, over the PRODUCTION retrieval path
with NO pre-arranged retrieval state:

  - PRODUCTION entry-point: the live resolver ``_resolve_live_config`` (the exact
    callable the UserPromptSubmit contributor uses) feeds the production
    ``retrieve`` — not a hand-built config. ``Path.home`` is redirected to a
    fixture tree so the resolver reads a fixture ``~/.claude`` the way it reads
    the live one; the corpus index does not exist until ``retrieve`` builds it;
    objectives fall back to the in-source SEED (no OBJECTIVES.md written).
  - The fixture stages the exact starvation the redesign removes: a constitutional
    ``CLAUDE.md`` AND a topical feedback doc both match the query.

Outcome:
  - With the carve ACTIVE (S1a default), the ranked block carries the TOPICAL
    hit and contains NO constitutional (CLAUDE.md) hit — regardless of how many
    hits return (no fixed-K assumption).
  - With the reversibility lever flipped ON, the constitutional hit reappears in
    the ranked block — proving it WAS competing for the slot the topical hit now
    holds (the freed slot), and that the carve is what freed it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.primary_persona.keep_pace import retrieval as _retrieval
from loam.primary_persona.keep_pace.retrieval import _resolve_live_config, retrieve

from _helpers_keep_pace import write_corpus

# Distinctive, rare tokens so both docs match the query strongly (high IDF) and
# rank above the silent-on-no-match floor without depending on a slot count.
_QUERY = "how do I run the widget calibration protocol"
_CLAUDE_POINTER = "Widget Calibration Constitution"
_TOPICAL_POINTER = "Widget calibration protocol notes"


def _stage_fixture(tmp_home: Path) -> dict:
    """Build a fixture ``~/.claude`` tree shaped exactly as the live resolver
    reads it, and return the UserPromptSubmit envelope that drives it.

    Layout:
      <tmp_home>/.claude/CLAUDE.md                         (constitution)
      <tmp_home>/.claude/projects/<slug>/memory/feedback_widget.md  (topical)

    The slug is derived from the workspace root the SAME way
    ``_resolve_live_config`` derives it, so the resolver finds the fixture
    memory dir with no pre-arranged retrieval state.
    """
    claude_home = tmp_home / ".claude"
    claude_home.mkdir(parents=True, exist_ok=True)
    (claude_home / "CLAUDE.md").write_text(
        f"# {_CLAUDE_POINTER}\n\n"
        "The widget calibration protocol governs every widget calibration run.\n",
        encoding="utf-8",
    )

    workspace_root = tmp_home / "ws"
    workspace_root.mkdir(parents=True, exist_ok=True)
    slug = "-" + str(workspace_root).strip("/").replace("/", "-")
    memory_dir = claude_home / "projects" / slug / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    # Seed the shared distractor corpus so BM25's IDF is meaningful (a
    # single-doc corpus collapses IDF to ~0 and the silent-on-no-match floor
    # drops everything — the sparse-regime artefact, not the production world).
    write_corpus(memory_dir)
    (memory_dir / "feedback_widget.md").write_text(
        f"# {_TOPICAL_POINTER}\n\n"
        "The widget calibration protocol requires a torque check on each "
        "widget before the run.\n",
        encoding="utf-8",
    )
    return {"prompt": _QUERY, "workspace": {"project_dir": str(workspace_root)}}


def test_AC_GFE_3_freed_slot_goes_to_topical_hit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tmp_home = tmp_path / "home"
    tmp_home.mkdir()
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_home))
    monkeypatch.delenv("LOAM_WORKSPACE_ROOT", raising=False)
    envelope = _stage_fixture(tmp_home)

    # --- carve ACTIVE (S1a default): topical hit present, constitution absent.
    cfg = _resolve_live_config(envelope)
    assert cfg.claude_homes == ()  # the resolver carved the floor out
    block = retrieve(prompt=_QUERY, config=cfg)
    assert _TOPICAL_POINTER in block  # the topical fact holds the slot
    assert _CLAUDE_POINTER not in block  # no constitutional hit, any count

    # --- lever ON: the constitution reappears in the ranked block, proving it
    # was competing for the slot (the freed slot) — the carve is what freed it.
    monkeypatch.setattr(_retrieval, "RANK_CONSTITUTIONAL_FLOOR", True)
    cfg_on = _resolve_live_config(envelope)
    assert cfg_on.claude_homes == (tmp_home / ".claude",)
    block_on = retrieve(prompt=_QUERY, config=cfg_on)
    assert _CLAUDE_POINTER in block_on
