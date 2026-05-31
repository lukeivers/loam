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

"""loam user-state migration engine (slice P1.3).

Public surface:

    DeclaredMigration            -- a validated declared-migration record
    MigrationSchemaError         -- schema-validation failure (corrective msg)
    load_migration_file          -- validate one *.migration.yaml
    load_migration_dir           -- validate every file in the contract dir
    validate_migration_mapping   -- validate a parsed mapping

    AppliedCursor                -- the per-workspace applied-migration cursor
    read_cursor / write_cursor   -- cursor persistence
    cursor_path                  -- resolve <workspace>/.loam/migrations/.cursor

    MigrationSafetyEnvelope      -- composes the reversibility primitive's
                                    governance (backup / protection-floor /
                                    rollback) over a replay
    classify_migration           -- declared migration -> ReversibilityClass
    ProtectionFloorRefusal       -- a destructive migration was refused

    enumerate_pending            -- pending set in release-version order
    replay                       -- the wrapped, ordered, through-not-jump
                                    replay (the engine)
    ReplayResult                 -- replay outcome
    MigrationOrderError          -- unstamped pending migration

BOUNDARY (plan §2 / §10): this migrates USER-STATE (the workspace's `.loam/`).
``framework/self-upgrade/`` migrates the framework CODEBASE -- a different
concern, never conflated or reused here.
"""

from __future__ import annotations

from .cursor import (
    AppliedCursor,
    cursor_path,
    read_cursor,
    write_cursor,
)
from .envelope import (
    MigrationSafetyEnvelope,
    ProtectionFloorRefusal,
    classify_migration,
)
from .replay import (
    MigrationOrderError,
    ReplayResult,
    enumerate_pending,
    replay,
)
from .schema import (
    DeclaredMigration,
    MigrationSchemaError,
    load_migration_dir,
    load_migration_file,
    validate_migration_mapping,
)

__all__ = [
    "AppliedCursor",
    "DeclaredMigration",
    "MigrationOrderError",
    "MigrationSafetyEnvelope",
    "MigrationSchemaError",
    "ProtectionFloorRefusal",
    "ReplayResult",
    "classify_migration",
    "cursor_path",
    "enumerate_pending",
    "load_migration_dir",
    "load_migration_file",
    "read_cursor",
    "replay",
    "validate_migration_mapping",
    "write_cursor",
]
