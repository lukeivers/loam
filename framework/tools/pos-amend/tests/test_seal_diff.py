"""T7 + T8 — allowed_prefixes / allowed_files binding widening."""

from __future__ import annotations

from pathlib import Path

import pytest

from pos_amend.seal_diff import BindingNotFound, read_entries, widen_binding


_TUPLE_FILE = '''"""Seal-diff test."""

def test_only_example_changed():
    allowed_prefixes = (
        "example/",
        "data/",
    )
    allowed_files = {"docs/odd-in-loam.md"}
    assert True
'''

_EMPTY_SET_FILE = '''"""Seal-diff test."""

def test_only_example_changed():
    allowed_prefixes = ("example/",)
    allowed_files: set[str] = set()
    assert True
'''


def test_T7_widen_allowed_prefixes_tuple(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text(_TUPLE_FILE, encoding="utf-8")
    changed, new, added = widen_binding(
        p, "allowed_prefixes", ["docs/rebuild/plans/", "new-component/"], mode="tuple"
    )
    assert changed is True
    assert added == ["docs/rebuild/plans/", "new-component/"]
    # Existing entries preserved, new entries appended (sorted among new).
    assert new == ["example/", "data/", "docs/rebuild/plans/", "new-component/"]
    text = p.read_text(encoding="utf-8")
    assert '"docs/rebuild/plans/"' in text
    assert '"new-component/"' in text
    entries = read_entries(p, "allowed_prefixes")
    assert entries == new


def test_T7_widen_allowed_files_set(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text(_TUPLE_FILE, encoding="utf-8")
    changed, new, added = widen_binding(
        p, "allowed_files", ["CLAUDE.md"], mode="set"
    )
    assert changed is True
    assert added == ["CLAUDE.md"]
    assert set(new) == {"docs/odd-in-loam.md", "CLAUDE.md"}


def test_T7_widen_handles_empty_set(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text(_EMPTY_SET_FILE, encoding="utf-8")
    changed, new, added = widen_binding(
        p, "allowed_files", ["CLAUDE.md"], mode="set"
    )
    assert changed is True
    assert new == ["CLAUDE.md"]
    text = p.read_text(encoding="utf-8")
    assert 'set()' not in text
    assert '"CLAUDE.md"' in text


def test_T8_widen_binding_idempotent(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text(_TUPLE_FILE, encoding="utf-8")
    widen_binding(
        p, "allowed_prefixes", ["docs/rebuild/plans/"], mode="tuple"
    )
    first = p.read_text(encoding="utf-8")
    changed, _new, added = widen_binding(
        p, "allowed_prefixes", ["docs/rebuild/plans/"], mode="tuple"
    )
    assert changed is False
    assert added == []
    second = p.read_text(encoding="utf-8")
    assert first == second


def test_widen_raises_on_missing_binding(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text("def t(): pass\n", encoding="utf-8")
    with pytest.raises(BindingNotFound):
        widen_binding(p, "allowed_prefixes", ["x/"], mode="tuple")


def test_read_entries_from_tuple(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text(_TUPLE_FILE, encoding="utf-8")
    assert read_entries(p, "allowed_prefixes") == ["example/", "data/"]
    assert read_entries(p, "allowed_files") == ["docs/odd-in-loam.md"]


def test_read_entries_from_empty_set(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text(_EMPTY_SET_FILE, encoding="utf-8")
    assert read_entries(p, "allowed_files") == []


_NO_FILES_BINDING_FILE = '''"""Seal-diff test without allowed_files."""

def test_only_example_changed():
    allowed_prefixes = (
        "example/",
        "data/",
    )
    assert True
'''


def test_widen_synthesizes_allowed_files_binding_when_missing(
    tmp_path: Path,
) -> None:
    p = tmp_path / "t.py"
    p.write_text(_NO_FILES_BINDING_FILE, encoding="utf-8")
    changed, new, added = widen_binding(
        p,
        "allowed_files",
        ["CLAUDE.md"],
        mode="set",
        create_if_missing_after="allowed_prefixes",
    )
    assert changed is True
    assert added == ["CLAUDE.md"]
    assert new == ["CLAUDE.md"]
    text = p.read_text(encoding="utf-8")
    assert 'allowed_files = {"CLAUDE.md"}' in text
    assert 'allowed_prefixes = (' in text


def test_widen_raises_when_anchor_also_missing(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text("def t(): pass\n", encoding="utf-8")
    with pytest.raises(BindingNotFound):
        widen_binding(
            p,
            "allowed_files",
            ["x.md"],
            mode="set",
            create_if_missing_after="allowed_prefixes",
        )
