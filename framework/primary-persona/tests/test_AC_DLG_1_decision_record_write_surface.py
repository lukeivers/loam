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

"""AC.DLG.1 — a production write surface persists an owner ruling as a
structured decision record at ruling time — entities + aliases,
question, ruling, reasoning, source message pointer, workstream,
status — machine-readable, in the workspace memory tree,
append-not-rewrite (supersession marks, never edits-in-place), atomic.

Memory recall cycle, Slice 3.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.decision_ledger import (
    decisions_dir,
    iter_decisions,
    read_decision,
    supersede_decision,
    write_decision,
)
from loam.primary_persona.supersession import read_supersession


def _write_tilth(mem: Path, **overrides) -> dict:
    kwargs = dict(
        question="How large is the Tilth raise ask?",
        ruling="$750,000 at $4M post-money valuation (~19% to Alan)",
        reasoning=(
            "AI-era raises differ: a comp-heavy raise is not a red flag "
            "when there is no army to fund — the founders are the build."
        ),
        entities=("Tilth", "Alan", "Eric", "raise", "valuation"),
        aliases=("the raise", "newco", "$750k"),
        source="telegram message 14053, 2026-06-07",
        workstream="tilth",
        date="2026-06-07",
    )
    kwargs.update(overrides)
    return write_decision(mem, **kwargs)


def test_AC_DLG_1_record_round_trips_machine_readable(tmp_path: Path) -> None:
    res = _write_tilth(tmp_path)
    path = Path(res["path"])
    assert path.is_file()
    assert decisions_dir(tmp_path) == path.parent
    rec = read_decision(path)
    assert rec is not None
    assert rec.question == "How large is the Tilth raise ask?"
    assert "$750,000" in rec.ruling
    assert "AI-era raises differ" in rec.reasoning
    assert rec.entities == ("Tilth", "Alan", "Eric", "raise", "valuation")
    assert "the raise" in rec.aliases
    assert rec.source == "telegram message 14053, 2026-06-07"
    assert rec.workstream == "tilth"
    assert rec.status == "ruled"
    assert rec.date == "2026-06-07"


def test_AC_DLG_1_append_not_rewrite_same_question(tmp_path: Path) -> None:
    first = _write_tilth(tmp_path)
    second = _write_tilth(tmp_path, ruling="$400,000 (hypothetical revision)")
    assert first["path"] != second["path"], (
        "a new ruling on the same question is a NEW record file"
    )
    assert Path(first["path"]).is_file(), "the old record is never removed"
    assert len(iter_decisions(tmp_path)) == 2


def test_AC_DLG_1_supersession_marks_never_edits(tmp_path: Path) -> None:
    old = _write_tilth(tmp_path)
    new = _write_tilth(tmp_path, ruling="$900,000 (newer ruling)")
    old_body_before = Path(old["path"]).read_text(encoding="utf-8")

    supersede_decision(old["path"], new["path"])

    rec = read_decision(old["path"])
    assert rec is not None and rec.status == "superseded"
    mark = read_supersession(old["path"])
    assert mark is not None and new["path"] in mark["superseded-by"]
    # Content beyond the mark preserved (never edited in place).
    assert "AI-era raises differ" in Path(old["path"]).read_text(
        encoding="utf-8"
    )
    assert old_body_before.split("---", 2)[2] in Path(
        old["path"]
    ).read_text(encoding="utf-8")


def test_AC_DLG_1_record_can_supersede_corpus_rule(tmp_path: Path) -> None:
    # AC.DLG.3 leg lives here at the write surface: ``supersedes``
    # marks a corpus document via the SEALED supersession mechanism.
    corpus_rule = tmp_path / "feedback_old_rule.md"
    corpus_rule.write_text(
        "# Old rule\nAlways ask before deciding raises.\n", encoding="utf-8"
    )
    res = _write_tilth(tmp_path, supersedes=(corpus_rule,))
    mark = read_supersession(corpus_rule)
    assert mark is not None
    assert res["path"] in mark["superseded-by"]
    assert "Always ask before deciding" in corpus_rule.read_text(
        encoding="utf-8"
    ), "corpus content preserved byte-for-byte beyond the mark"


def test_AC_DLG_1_no_tmp_residue_after_write(tmp_path: Path) -> None:
    _write_tilth(tmp_path)
    leftovers = list(decisions_dir(tmp_path).glob("*.tmp"))
    assert leftovers == [], "atomic write must leave no tmp residue"
