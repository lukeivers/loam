"""T12 — narrative append with blank-line separator."""

from __future__ import annotations

from pathlib import Path

from pos_amend.narrative import append_narrative


def test_T12_append_creates_file(tmp_path: Path) -> None:
    target = tmp_path / "NARRATIVE"
    changed = append_narrative(target, "hello world")
    assert changed is True
    assert target.read_text(encoding="utf-8") == "hello world\n"


def test_T12_append_adds_blank_line_separator(tmp_path: Path) -> None:
    target = tmp_path / "NARRATIVE"
    target.write_text("existing\n", encoding="utf-8")
    changed = append_narrative(target, "appended")
    assert changed is True
    text = target.read_text(encoding="utf-8")
    assert text == "existing\n\nappended\n"


def test_T12_append_is_idempotent(tmp_path: Path) -> None:
    target = tmp_path / "NARRATIVE"
    append_narrative(target, "same body")
    changed = append_narrative(target, "same body")
    assert changed is False


def test_T12_append_with_trailing_newlines(tmp_path: Path) -> None:
    target = tmp_path / "NARRATIVE"
    target.write_text("existing\n\n\n\n", encoding="utf-8")
    append_narrative(target, "new")
    text = target.read_text(encoding="utf-8")
    # exactly one blank-line separator
    assert text == "existing\n\nnew\n"
