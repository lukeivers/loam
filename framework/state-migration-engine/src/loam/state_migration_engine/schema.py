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

"""Declared user-state migration SCHEMA + validator (AC.MIG-SCHEMA.*).

This formalises the contract ALREADY EMERGING in
``docs/state-migrations/*.migration.yaml`` (P1.1 / P1.2 + the FBM quartet)
into a validated shape. It does NOT invent a new schema — every field +
operation token recognised here was read off the six authored files; the
validator is faithful to them (AC.MIG-SCHEMA.2). If an authored file would
fail this validator the schema is wrong, not the file (plan halt-trigger 3).

A migration's *effect* is derived SOLELY from the declared file
(AC.MIG-SCHEMA.3, declared-not-guessed): the engine never reads a code diff
to infer what changed. The declared ``operation`` token + ``reversible`` /
``removes_user_state`` flags ARE the effect contract.

Boundary (plan §2 / §10): this validates files on the FRAMEWORK side
(``docs/state-migrations/``, tracked). It knows nothing about the
framework-codebase migrator (``framework/self-upgrade/``) — a different,
non-conflated concern.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Operation vocabulary — the DECLARED set, read off the six authored files.
#
#   no-op                       — fbm-live, fbm-rank-normalize, fbm-rule-weighting
#   structural-only             — loam-layout (creates absent home dirs)
#   schema-add-forward-additive — fbm-episode-salience (new optional field on
#                                 NEW writes; existing state untouched)
#   none-code-only              — fbm-spread-salience-gate-fix (code-only fix)
#
# Per D2 (declarative-only this slice) the vocabulary is CLOSED: a migration
# declaring a transform outside this set is REJECTED until the operation type
# is added behind the same envelope (the protection floor — plan §7 item 1).
# ---------------------------------------------------------------------------
DECLARATIVE_OPERATIONS: frozenset[str] = frozenset(
    {
        "no-op",
        "structural-only",
        "schema-add-forward-additive",
        "none-code-only",
    }
)

#: Operations that DECLARE a non-destructive forward effect on user-state
#: (they may create absent paths or add a field to new writes) but never
#: remove / compress / overwrite existing state. Everything in the closed
#: vocabulary is currently in this set — the declared corpus is wholly
#: non-destructive by construction (the never-delete invariant, plan §10).
NON_DESTRUCTIVE_OPERATIONS: frozenset[str] = DECLARATIVE_OPERATIONS

#: Required top-level keys every declared migration file must carry. These
#: three are present on ALL six authored files; their absence makes the
#: file's effect un-derivable (AC.MIG-SCHEMA.1).
REQUIRED_FIELDS: tuple[str, ...] = ("slug", "operation", "reversible")


@dataclass(frozen=True)
class DeclaredMigration:
    """A validated declared-migration record.

    The fields the engine reads to plan + order replay. ``raw`` keeps the
    full parsed mapping so human-provenance keys (``rationale``,
    ``predecessor``, ``followups`` …) survive without the engine needing a
    field for each. The engine derives its planned actions SOLELY from these
    declared fields (AC.MIG-SCHEMA.3) — never from a code diff.
    """

    slug: str
    operation: str
    reversible: bool
    removes_user_state: bool
    idempotent: bool
    #: Release-time version stamp (D1 — the replay-order key). ``None`` until
    #: the release-gate stamps it at release time; authoring-time files carry
    #: no version (feedback_version_numbers_at_release_time).
    version: str | None
    predecessor: str | None
    creates: tuple[str, ...]
    leaves_in_place: tuple[str, ...]
    source_path: Path | None
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def is_no_op(self) -> bool:
        """True when this migration declares no user-state mutation."""
        return self.operation in ("no-op", "none-code-only")


class MigrationSchemaError(ValueError):
    """A declared-migration file failed validation.

    Carries a specific corrective ``message`` (AC.MIG-SCHEMA.1) naming the
    offending file + field so the author can fix the declaration.
    """

    def __init__(self, message: str, *, source_path: Path | None = None) -> None:
        self.source_path = source_path
        prefix = f"{source_path}: " if source_path is not None else ""
        super().__init__(f"{prefix}{message}")


def _coerce_str_tuple(value: Any) -> tuple[str, ...]:
    """Coerce a path-list field (``creates`` / ``leaves_in_place``) to a
    tuple of strings, tolerating the ``[]`` / missing / single-string forms
    seen across the authored files."""
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if isinstance(value, (list, tuple)):
        return tuple(str(v) for v in value)
    raise MigrationSchemaError(
        f"expected a list of paths, got {type(value).__name__}"
    )


def validate_migration_mapping(
    data: Any, *, source_path: Path | None = None
) -> DeclaredMigration:
    """Validate a parsed migration mapping; return a DeclaredMigration.

    Rejects (AC.MIG-SCHEMA.1) with a specific corrective message:
      - a non-mapping document,
      - a missing required field (``slug`` / ``operation`` / ``reversible``),
      - an ``operation`` outside the closed declarative vocabulary (D2),
      - a non-boolean ``reversible`` / ``removes_user_state`` / ``idempotent``.

    A well-formed file PASSES and yields the typed record.
    """
    if not isinstance(data, dict):
        raise MigrationSchemaError(
            "migration file must be a YAML mapping at the top level",
            source_path=source_path,
        )

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        raise MigrationSchemaError(
            "missing required field(s): "
            + ", ".join(missing)
            + f" (every declared migration must carry {', '.join(REQUIRED_FIELDS)})",
            source_path=source_path,
        )

    slug = data["slug"]
    if not isinstance(slug, str) or not slug.strip():
        raise MigrationSchemaError(
            "`slug` must be a non-empty string (the scope-descriptive key)",
            source_path=source_path,
        )

    operation = data["operation"]
    if not isinstance(operation, str) or operation not in DECLARATIVE_OPERATIONS:
        raise MigrationSchemaError(
            f"`operation: {operation!r}` is not in the declared vocabulary "
            + "{"
            + ", ".join(sorted(DECLARATIVE_OPERATIONS))
            + "}. Per the declarative-only protection floor (D2) a transform "
            "outside this set must be added as a named operation type behind "
            "the safety envelope before it can be declared.",
            source_path=source_path,
        )

    def _as_bool(key: str, *, default: bool | None = None) -> bool:
        if key not in data:
            if default is not None:
                return default
            raise MigrationSchemaError(
                f"missing required boolean `{key}`", source_path=source_path
            )
        v = data[key]
        if not isinstance(v, bool):
            raise MigrationSchemaError(
                f"`{key}` must be a boolean, got {type(v).__name__}",
                source_path=source_path,
            )
        return v

    reversible = _as_bool("reversible")
    # `removes_user_state` defaults False when absent (the authored files that
    # omit it are all non-destructive); `idempotent` defaults True (a declared
    # forward-additive/no-op migration is idempotent by construction).
    removes_user_state = _as_bool("removes_user_state", default=False)
    idempotent = _as_bool("idempotent", default=True)

    version = data.get("version")
    if version is not None and not isinstance(version, str):
        raise MigrationSchemaError(
            "`version` (release-time stamp) must be a string when present",
            source_path=source_path,
        )

    predecessor = data.get("predecessor")
    if predecessor is not None and not isinstance(predecessor, str):
        raise MigrationSchemaError(
            "`predecessor` must be a string when present (human provenance)",
            source_path=source_path,
        )

    return DeclaredMigration(
        slug=slug,
        operation=operation,
        reversible=reversible,
        removes_user_state=removes_user_state,
        idempotent=idempotent,
        version=version,
        predecessor=predecessor,
        creates=_coerce_str_tuple(data.get("creates")),
        leaves_in_place=_coerce_str_tuple(data.get("leaves_in_place")),
        source_path=source_path,
        raw=dict(data),
    )


def load_migration_file(path: str | Path) -> DeclaredMigration:
    """Load + validate a single ``*.migration.yaml`` file."""
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise MigrationSchemaError(
            f"cannot read migration file: {exc}", source_path=p
        ) from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise MigrationSchemaError(
            f"not valid YAML: {exc}", source_path=p
        ) from exc
    return validate_migration_mapping(data, source_path=p)


def load_migration_dir(directory: str | Path) -> list[DeclaredMigration]:
    """Load + validate every ``*.migration.yaml`` under *directory*.

    Raises ``MigrationSchemaError`` on the FIRST malformed file (the contract
    home is small + author-curated; one bad file is a build-time stop, not a
    skip). Returns the validated records sorted by slug for determinism;
    replay ORDER is the engine's concern, not this loader's.
    """
    d = Path(directory)
    files = sorted(d.glob("*.migration.yaml"))
    return [load_migration_file(f) for f in files]
