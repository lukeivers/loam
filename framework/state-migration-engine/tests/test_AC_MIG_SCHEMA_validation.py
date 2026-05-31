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

"""AC.MIG-SCHEMA.* — the declared migration contract is validated, not guessed."""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.state_migration_engine import (
    MigrationSchemaError,
    load_migration_dir,
    load_migration_file,
    validate_migration_mapping,
)

from .conftest import write_migration

# Repo root is four parents up from this test file
# (framework/state-migration-engine/tests/<file>).
REPO_ROOT = Path(__file__).resolve().parents[3]
LIVE_MIGRATIONS_DIR = REPO_ROOT / "docs" / "state-migrations"


def test_AC_MIG_SCHEMA_1_missing_field_rejected_wellformed_passes(
    tmp_path: Path,
) -> None:
    """A file missing a required field is REJECTED with a specific corrective
    message; a well-formed file PASSES."""
    # Missing `operation` (required).
    with pytest.raises(MigrationSchemaError) as exc:
        validate_migration_mapping({"slug": "x", "reversible": True})
    assert "operation" in str(exc.value)

    # Missing `slug`.
    with pytest.raises(MigrationSchemaError) as exc:
        validate_migration_mapping({"operation": "no-op", "reversible": True})
    assert "slug" in str(exc.value)

    # An operation outside the closed declarative vocabulary is rejected (D2).
    with pytest.raises(MigrationSchemaError) as exc:
        validate_migration_mapping(
            {"slug": "x", "operation": "rewrite-all", "reversible": True}
        )
    assert "vocabulary" in str(exc.value)

    # A well-formed file passes.
    m = validate_migration_mapping(
        {"slug": "ok", "operation": "no-op", "reversible": True}
    )
    assert m.slug == "ok"
    assert m.operation == "no-op"


def test_AC_MIG_SCHEMA_2_existing_files_all_validate() -> None:
    """Every existing file in docs/state-migrations/ validates under the
    formalized schema (faithfulness — no retro-breakage). The pre-existing
    six (the FBM quartet + layout + live) MUST all be present + valid; this
    slice's own declared migration (the seventh, authored at INTEGRATE) is
    expected too."""
    migrations = load_migration_dir(LIVE_MIGRATIONS_DIR)
    slugs = {m.slug for m in migrations}
    # The six authored before this slice must all validate (the faithfulness
    # bar — load_migration_dir raises on the FIRST malformed file, so a clean
    # load already proves every file validated).
    pre_existing = {
        "fbm-episode-salience-slice",
        "fbm-live-slice",
        "fbm-rank-normalize-slice",
        "fbm-rule-weighting-slice",
        "fbm-spread-salience-gate-fix-slice",
        "loam-layout-slice",
    }
    assert pre_existing <= slugs
    # This slice's own structural-only migration is the seventh.
    assert "migration-engine-and-release-gate-slice" in slugs
    # Every declared migration in the contract is non-destructive + reversible
    # (the never-delete invariant — the corpus is wholly non-destructive).
    for m in migrations:
        assert m.reversible is True
        assert m.removes_user_state is False


def test_AC_MIG_SCHEMA_3_effect_declared_not_inferred(tmp_path: Path) -> None:
    """The engine's planned effect derives SOLELY from the declared file:
    two identical declarations yield identical records regardless of any
    surrounding code diff (there is no diff input to the loader at all)."""
    d1 = tmp_path / "a"
    d2 = tmp_path / "b"
    write_migration(d1, slug="same", operation="structural-only", version="v0.1.0", creates=[".loam/x/"])
    write_migration(d2, slug="same", operation="structural-only", version="v0.1.0", creates=[".loam/x/"])
    m1 = load_migration_file(d1 / "same.migration.yaml")
    m2 = load_migration_file(d2 / "same.migration.yaml")
    # Effect-bearing fields are identical — the loader takes no code diff.
    assert (m1.slug, m1.operation, m1.creates, m1.removes_user_state) == (
        m2.slug,
        m2.operation,
        m2.creates,
        m2.removes_user_state,
    )
