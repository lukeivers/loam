"""T1, T2, T3 — manifest parse + validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from pos_amend.manifest import (
    InvalidField,
    Manifest,
    MissingField,
    UnknownSchemaVersion,
    load_manifest,
)


FIXTURES = Path(__file__).parent / "fixtures"


def test_T1_manifest_parser_accepts_valid_minimal() -> None:
    m = load_manifest(FIXTURES / "valid-minimal.yaml")
    assert isinstance(m, Manifest)
    assert m.number == 99
    assert m.slug == "test-minimal"
    assert m.baseline == "abcdef0"
    assert len(m.components) == 1
    assert m.components[0].name == "example"
    assert m.components[0].extra_allowed_prefixes == ()


def test_T1_manifest_parser_accepts_valid_multi_component() -> None:
    m = load_manifest(FIXTURES / "valid-multi-component.yaml")
    assert len(m.components) == 2
    names = [c.name for c in m.components]
    assert names == ["alpha", "beta"]
    assert m.universal_paths.prefixes == ("docs/rebuild/plans/",)
    assert m.universal_paths.files == ("CLAUDE.md",)
    assert m.narrative is not None
    assert "test narrative block" in m.narrative.body


def test_T2_manifest_parser_rejects_unknown_schema_version() -> None:
    with pytest.raises(UnknownSchemaVersion) as exc_info:
        load_manifest(FIXTURES / "invalid-unknown-schema-version.yaml")
    assert "schema_version" in str(exc_info.value)


def test_T3_manifest_parser_rejects_missing_required_field() -> None:
    with pytest.raises(MissingField) as exc_info:
        load_manifest(FIXTURES / "invalid-missing-number.yaml")
    assert "number" in str(exc_info.value)


def test_T3_manifest_parser_rejects_non_hex_baseline(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        """schema_version: 1
amendment:
  number: 1
  slug: x
  title: "x"
baseline: "not-a-sha"
plan: docs/rebuild/plans/x.md
components:
  - name: a
    seal_test: a/tests/t.py
    sidecar: a/tests/SEAL_COMMIT
""",
        encoding="utf-8",
    )
    with pytest.raises(InvalidField):
        load_manifest(bad)
