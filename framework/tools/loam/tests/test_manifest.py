"""T1, T2, T3 — manifest parse + validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_cli.amend.manifest import (
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


# ----------------------------------------------------------------------
# Schema v2 — ``objectives`` block parsing (AC.D-pa.1, AC.D-pa.4)
# ----------------------------------------------------------------------


def test_T16_schema_v2_with_objectives_block_parses() -> None:
    """A schema_version 2 manifest carrying an ``objectives`` block
    parses end-to-end; entries surface on the Manifest dataclass."""
    m = load_manifest(FIXTURES / "valid-with-objectives.yaml")
    assert m.schema_version == 2
    assert len(m.objectives) == 2
    e0 = m.objectives[0]
    assert e0.goal == "Demonstrate schema v2 objectives entry"
    assert e0.parent_root is True
    assert e0.parent_id is None
    assert e0.lifted_from.source_doc == (
        "docs/rebuild/plans/test-with-objectives.md"
    )
    assert e0.lifted_from.source_ac == "AC.test.1"
    e1 = m.objectives[1]
    assert e1.parent_root is False
    assert e1.parent_id == "value-prop-root"


def test_T16_schema_v1_with_objectives_block_rejected(tmp_path: Path) -> None:
    """A schema_version 1 manifest carrying ``objectives`` rejects.
    AC.D-pa.4 backward-compat invariant — v1 must not carry the block."""
    bad = tmp_path / "v1-with-objectives.yaml"
    bad.write_text(
        """schema_version: 1
amendment:
  number: 1
  slug: x
  title: "x"
baseline: abcdef0
plan: docs/rebuild/plans/x.md
components:
  - name: a
    seal_test: a/tests/t.py
    sidecar: a/tests/SEAL_COMMIT
objectives:
  - goal: "..."
    parent_root: true
    acceptance_criteria:
      - kind: prose
        criterion_id: AC.x.1
        prose: "..."
    time_bound:
      evergreen: true
    authored_by: "user"
    lifted_from:
      source_doc: "docs/rebuild/plans/x.md"
      source_ac: "AC.x.1"
""",
        encoding="utf-8",
    )
    with pytest.raises(InvalidField):
        load_manifest(bad)


def test_T16_schema_v2_without_objectives_block_rejected(
    tmp_path: Path,
) -> None:
    """A schema_version 2 manifest missing ``objectives`` rejects."""
    bad = tmp_path / "v2-no-objectives.yaml"
    bad.write_text(
        """schema_version: 2
amendment:
  number: 1
  slug: x
  title: "x"
baseline: abcdef0
plan: docs/rebuild/plans/x.md
components:
  - name: a
    seal_test: a/tests/t.py
    sidecar: a/tests/SEAL_COMMIT
""",
        encoding="utf-8",
    )
    with pytest.raises(MissingField):
        load_manifest(bad)


def test_T16_objectives_entry_requires_parent_id_xor_parent_root(
    tmp_path: Path,
) -> None:
    """An entry must declare exactly one of parent_id / parent_root.
    Both unset rejects, both set rejects."""
    base = """schema_version: 2
amendment:
  number: 1
  slug: x
  title: "x"
baseline: abcdef0
plan: docs/rebuild/plans/x.md
components:
  - name: a
    seal_test: a/tests/t.py
    sidecar: a/tests/SEAL_COMMIT
objectives:
  - goal: "g"
    {parent_clause}
    acceptance_criteria:
      - kind: prose
        criterion_id: AC.x.1
        prose: "p"
    time_bound:
      evergreen: true
    authored_by: "user"
    lifted_from:
      source_doc: "x.md"
      source_ac: "AC.x.1"
"""
    # neither set → MissingField
    neither = tmp_path / "neither.yaml"
    neither.write_text(
        base.format(parent_clause=""),
        encoding="utf-8",
    )
    with pytest.raises(MissingField):
        load_manifest(neither)

    # both set → InvalidField
    both = tmp_path / "both.yaml"
    both.write_text(
        base.format(
            parent_clause='parent_id: "value-prop-root"\n    parent_root: true'
        ),
        encoding="utf-8",
    )
    with pytest.raises(InvalidField):
        load_manifest(both)


def test_T16_objectives_entry_rejects_source_commit_in_lifted_from(
    tmp_path: Path,
) -> None:
    """``source_commit`` is reserved for the seal step; manifest authors
    must not set it (per the manifest-loader's reserved-key check)."""
    bad = tmp_path / "with-source-commit.yaml"
    bad.write_text(
        """schema_version: 2
amendment:
  number: 1
  slug: x
  title: "x"
baseline: abcdef0
plan: docs/rebuild/plans/x.md
components:
  - name: a
    seal_test: a/tests/t.py
    sidecar: a/tests/SEAL_COMMIT
objectives:
  - goal: "g"
    parent_root: true
    acceptance_criteria:
      - kind: prose
        criterion_id: AC.x.1
        prose: "p"
    time_bound:
      evergreen: true
    authored_by: "user"
    lifted_from:
      source_doc: "x.md"
      source_ac: "AC.x.1"
      source_commit: "deadbeef"
""",
        encoding="utf-8",
    )
    with pytest.raises(InvalidField):
        load_manifest(bad)


def test_T16_v1_manifest_objectives_tuple_empty() -> None:
    """A v1 manifest without an objectives block exposes an empty
    ``objectives`` tuple — round-trip-clean for downstream consumers."""
    m = load_manifest(FIXTURES / "valid-minimal.yaml")
    assert m.objectives == ()
    m2 = load_manifest(FIXTURES / "valid-multi-component.yaml")
    assert m2.objectives == ()
