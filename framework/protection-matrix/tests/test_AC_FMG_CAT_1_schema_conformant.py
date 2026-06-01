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

"""AC.FMG-CAT.1 — the catalogue exists and is schema-conformant.

The shipped manifest parses, and every row carries every required §5 field
with a value in its declared enum. Pins the artefact + shape, not the parser
internals.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from loam.protection_matrix.catalogue import (
    CLASSES,
    DEFAULT_ON_VALUES,
    GUARD_KINDS,
    SchemaError,
    default_catalogue_path,
    load_catalogue,
)


def test_shipped_catalogue_parses_and_is_schema_conformant() -> None:
    """The real shipped catalogue loads + every row is enum-valid."""
    cat = load_catalogue()
    assert cat.source_path == default_catalogue_path()
    assert cat.source_path.is_file()
    assert cat.rows, "the catalogue must have at least one row"
    for row in cat.rows:
        assert row.id.startswith("FM."), row.id
        assert row.guard_kind in GUARD_KINDS, (row.id, row.guard_kind)
        assert row.default_on in DEFAULT_ON_VALUES, (row.id, row.default_on)
        assert row.klass in CLASSES, (row.id, row.klass)
        # every required string field is present + non-empty (except the
        # legitimately-empty guard_ref / proportionality_note).
        assert row.name
        assert row.description
        assert row.source
        assert row.guard
        assert row.verification


def test_row_ids_are_unique() -> None:
    cat = load_catalogue()
    ids = [r.id for r in cat.rows]
    assert len(ids) == len(set(ids)), "row ids must be unique"


def test_a_missing_required_field_is_rejected(tmp_path: Path) -> None:
    """A row missing a required §5 field raises SchemaError."""
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        textwrap.dedent(
            """\
            schema_version: 1
            rows:
              - id: FM.X
                name: x
                # description missing
                source: s
                guard: g
                guard_kind: none
                guard_ref: ""
                default_on: NONE
                class: floor
                proportionality_note: ""
                verification: v
            """
        ),
        encoding="utf-8",
    )
    with pytest.raises(SchemaError):
        load_catalogue(bad)


def test_an_out_of_enum_value_is_rejected(tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text(
        textwrap.dedent(
            """\
            schema_version: 1
            rows:
              - id: FM.X
                name: x
                description: d
                source: s
                guard: g
                guard_kind: WIDGET
                guard_ref: ""
                default_on: NONE
                class: floor
                proportionality_note: ""
                verification: v
            """
        ),
        encoding="utf-8",
    )
    with pytest.raises(SchemaError):
        load_catalogue(bad)
