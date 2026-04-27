"""T6 — tests/SEAL_COMMIT sidecar read/write."""

from __future__ import annotations

from pathlib import Path

from pos_amend.sidecar import read_sidecar, write_sidecar


def test_T6_write_sidecar_creates_file(tmp_path: Path) -> None:
    p = tmp_path / "SEAL_COMMIT"
    changed = write_sidecar(p, "abcdef0")
    assert changed is True
    assert p.read_text(encoding="utf-8") == "abcdef0\n"


def test_T6_write_sidecar_idempotent(tmp_path: Path) -> None:
    p = tmp_path / "SEAL_COMMIT"
    p.write_text("abcdef0\n", encoding="utf-8")
    changed = write_sidecar(p, "abcdef0")
    assert changed is False


def test_T6_write_sidecar_overwrites(tmp_path: Path) -> None:
    p = tmp_path / "SEAL_COMMIT"
    p.write_text("aaaaaaa\n", encoding="utf-8")
    changed = write_sidecar(p, "bbbbbbb")
    assert changed is True
    assert p.read_text(encoding="utf-8") == "bbbbbbb\n"


def test_read_sidecar_absent(tmp_path: Path) -> None:
    assert read_sidecar(tmp_path / "missing") == ""


def test_read_sidecar_strips_whitespace(tmp_path: Path) -> None:
    p = tmp_path / "SEAL_COMMIT"
    p.write_text("  abcdef0  \n\n", encoding="utf-8")
    assert read_sidecar(p) == "abcdef0"
