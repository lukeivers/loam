"""T5 — BASELINE literal rewrite."""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_amend.baseline import (
    BaselineAmbiguous,
    BaselineNotFound,
    read_baseline,
    set_baseline,
)


_SAMPLE_FILE = '''"""Docstring."""

BASELINE = "abcdef0"
SEAL_COMMIT_PATH = Path(__file__).parent / "SEAL_COMMIT"


def _seal_commit() -> str:
    return "HEAD"
'''


def test_T5_set_baseline_rewrites_literal(tmp_path: Path) -> None:
    p = tmp_path / "test_no_sealed_amendments.py"
    p.write_text(_SAMPLE_FILE, encoding="utf-8")
    changed = set_baseline(p, "1234567")
    assert changed is True
    text = p.read_text(encoding="utf-8")
    assert 'BASELINE = "1234567"' in text
    assert 'BASELINE = "abcdef0"' not in text
    # The rest of the file is preserved.
    assert 'SEAL_COMMIT_PATH' in text
    assert 'def _seal_commit' in text


def test_T5_set_baseline_idempotent(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text(_SAMPLE_FILE, encoding="utf-8")
    changed = set_baseline(p, "abcdef0")
    assert changed is False


def test_read_baseline(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text(_SAMPLE_FILE, encoding="utf-8")
    assert read_baseline(p) == "abcdef0"


def test_baseline_not_found(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text("no BASELINE here\n", encoding="utf-8")
    with pytest.raises(BaselineNotFound):
        read_baseline(p)


def test_baseline_ambiguous(tmp_path: Path) -> None:
    p = tmp_path / "t.py"
    p.write_text(
        'BASELINE = "abcdef0"\nBASELINE = "1234567"\n', encoding="utf-8"
    )
    with pytest.raises(BaselineAmbiguous):
        read_baseline(p)
