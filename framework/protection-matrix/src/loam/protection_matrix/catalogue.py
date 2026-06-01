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

"""The catalogue loader + schema validator (AC.FMG-CAT.1).

Parses ``data/failure-mode-guard-matrix.yaml`` into typed :class:`GuardRow`
objects and validates every row against the plan-§5 schema (every required
field present, every enum-valued field in its declared enum). The ``gap``
field is DERIVED by the check (:mod:`check`), never authored in the YAML.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


# --- the plan-§5 enums (the contract) --------------------------------------

GUARD_KINDS = frozenset(
    {
        "hook",
        "release-gate",
        "odd",
        "memory",
        "comparator",
        "persona-discipline",
        "none",
    }
)
DEFAULT_ON_VALUES = frozenset({"YES", "NO-PROGRAMMATIC", "NONE"})
CLASSES = frozenset({"floor", "proportional"})

# Required §5 fields on every row. ``proportionality_note`` is required as a
# key (may be empty for floor rows); ``gap`` is derived, never authored.
REQUIRED_FIELDS = (
    "id",
    "name",
    "description",
    "source",
    "guard",
    "guard_kind",
    "guard_ref",
    "default_on",
    "class",
    "proportionality_note",
    "verification",
)

# Guard kinds for which a resolvable guard_ref is REQUIRED (AC.FMG-CAT.2 — a
# real, citable guard). persona-discipline / none rows are unverifiable by
# construction and carry an empty guard_ref legitimately.
GUARD_REF_REQUIRED_KINDS = frozenset(
    {"hook", "release-gate", "comparator", "memory"}
)


class SchemaError(ValueError):
    """A catalogue row violates the plan-§5 schema."""


@dataclass(frozen=True)
class GuardRow:
    """One catalogue row — a failure mode × its guard (plan §5)."""

    id: str
    name: str
    description: str
    source: str
    guard: str
    guard_kind: str
    guard_ref: str
    default_on: str
    klass: str  # ``class`` is a Python keyword; mapped from the YAML key.
    proportionality_note: str
    verification: str

    @property
    def is_floor(self) -> bool:
        return self.klass == "floor"

    @property
    def guard_ref_required(self) -> bool:
        """True iff this row's kind obligates a resolvable guard_ref."""
        return self.guard_kind in GUARD_REF_REQUIRED_KINDS


@dataclass(frozen=True)
class Catalogue:
    """The parsed, schema-validated catalogue."""

    schema_version: int
    rows: tuple[GuardRow, ...]
    source_path: Path

    @property
    def floor_rows(self) -> tuple[GuardRow, ...]:
        return tuple(r for r in self.rows if r.is_floor)


def default_catalogue_path() -> Path:
    """The shipped catalogue path, relative to this package.

    Resolves ``framework/protection-matrix/data/failure-mode-guard-matrix.yaml``
    from the installed package location (package is at
    ``framework/protection-matrix/src/loam/protection_matrix``; the data dir
    is a sibling of ``src``).
    """
    return (
        Path(__file__).resolve().parents[3]
        / "data"
        / "failure-mode-guard-matrix.yaml"
    )


def _validate_row(raw: Any, index: int) -> GuardRow:
    if not isinstance(raw, dict):
        raise SchemaError(
            f"row {index}: expected a mapping, got {type(raw).__name__}"
        )
    missing = [f for f in REQUIRED_FIELDS if f not in raw]
    if missing:
        raise SchemaError(
            f"row {index} (id={raw.get('id', '?')!r}): missing required "
            f"field(s): {missing}"
        )
    rid = raw["id"]
    if not isinstance(rid, str) or not rid.startswith("FM."):
        raise SchemaError(
            f"row {index}: id must be a scope-descriptive 'FM.*' string, "
            f"got {rid!r}"
        )
    gk = raw["guard_kind"]
    if gk not in GUARD_KINDS:
        raise SchemaError(
            f"row {rid}: guard_kind {gk!r} not in {sorted(GUARD_KINDS)}"
        )
    # YAML 1.1 reads a bare ``YES`` as boolean True (and ``NO`` as False).
    # default_on is an enum STRING — coerce the boolean that an unquoted
    # ``YES`` in the YAML produces back to its canonical token so a maintainer
    # who writes ``default_on: YES`` (the natural form) is not tripped.
    do = raw["default_on"]
    if do is True:
        do = "YES"
    elif do is False:
        do = "NO"  # not a valid enum value -> rejected below with a clear msg.
    if do not in DEFAULT_ON_VALUES:
        raise SchemaError(
            f"row {rid}: default_on {raw['default_on']!r} not in "
            f"{sorted(DEFAULT_ON_VALUES)}"
        )
    cls = raw["class"]
    if cls not in CLASSES:
        raise SchemaError(
            f"row {rid}: class {cls!r} not in {sorted(CLASSES)}"
        )
    # guard_ref is a string (possibly empty for persona-discipline/none).
    gref = raw["guard_ref"]
    if not isinstance(gref, str):
        raise SchemaError(
            f"row {rid}: guard_ref must be a string, got "
            f"{type(gref).__name__}"
        )
    return GuardRow(
        id=rid,
        name=str(raw["name"]),
        description=str(raw["description"]),
        source=str(raw["source"]),
        guard=str(raw["guard"]),
        guard_kind=gk,
        guard_ref=gref,
        default_on=do,
        klass=cls,
        proportionality_note=str(raw["proportionality_note"]),
        verification=str(raw["verification"]),
    )


def load_catalogue(path: Path | None = None) -> Catalogue:
    """Load + schema-validate the catalogue (AC.FMG-CAT.1).

    Raises :class:`SchemaError` if the file does not parse, the top-level
    shape is wrong, or any row violates the plan-§5 schema. Row ids must be
    unique.
    """
    catalogue_path = path or default_catalogue_path()
    if not catalogue_path.is_file():
        raise SchemaError(
            f"catalogue not found at {catalogue_path}. The protection-matrix "
            f"data file must ship with the package."
        )
    try:
        data = yaml.safe_load(catalogue_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise SchemaError(
            f"catalogue at {catalogue_path} does not parse: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise SchemaError(
            f"catalogue top-level must be a mapping, got "
            f"{type(data).__name__}"
        )
    sv = data.get("schema_version")
    if not isinstance(sv, int):
        raise SchemaError(
            f"catalogue schema_version must be an integer, got {sv!r}"
        )
    rows_raw = data.get("rows")
    if not isinstance(rows_raw, list) or not rows_raw:
        raise SchemaError(
            "catalogue 'rows' must be a non-empty list"
        )
    rows = tuple(_validate_row(r, i) for i, r in enumerate(rows_raw))
    seen: set[str] = set()
    for r in rows:
        if r.id in seen:
            raise SchemaError(f"duplicate row id: {r.id}")
        seen.add(r.id)
    return Catalogue(
        schema_version=sv, rows=rows, source_path=catalogue_path
    )
