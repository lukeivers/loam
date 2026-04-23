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


def test_T15_frozen_baseline_field_defaults_false(tmp_path: Path) -> None:
    """T15 — a component without ``frozen_baseline`` defaults to False,
    preserving backward compatibility with pre-amendment-#23 manifests."""
    m = load_manifest(FIXTURES / "valid-minimal.yaml")
    assert m.components[0].frozen_baseline is False


def test_T15_frozen_baseline_field_accepted(tmp_path: Path) -> None:
    """T15 — a component declaring ``frozen_baseline: true`` parses,
    and the field surfaces on the ComponentEntry."""
    manifest = tmp_path / "frozen.yaml"
    manifest.write_text(
        """schema_version: 1
amendment:
  number: 23
  slug: frozen
  title: "frozen"
baseline: abcdef0
plan: docs/rebuild/plans/frozen.md
components:
  - name: hands-off-lifecycle
    seal_test: hands-off-lifecycle/tests/test_cross_cutting.py
    sidecar: hands-off-lifecycle/tests/SEAL_COMMIT
    frozen_baseline: true
""",
        encoding="utf-8",
    )
    m = load_manifest(manifest)
    assert m.components[0].frozen_baseline is True


def test_T15_frozen_baseline_field_rejects_non_bool(tmp_path: Path) -> None:
    """T15 — a non-boolean value for ``frozen_baseline`` raises InvalidField."""
    manifest = tmp_path / "bad-frozen.yaml"
    manifest.write_text(
        """schema_version: 1
amendment:
  number: 23
  slug: frozen
  title: "frozen"
baseline: abcdef0
plan: docs/rebuild/plans/frozen.md
components:
  - name: x
    seal_test: x/tests/t.py
    sidecar: x/tests/SEAL_COMMIT
    frozen_baseline: "yes"
""",
        encoding="utf-8",
    )
    with pytest.raises(InvalidField):
        load_manifest(manifest)
