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

"""AC.MIG-SAFE.* — backup / verify / roll back / idempotent / protection-floor.

These prove the replay composes the reversibility primitive's governance as a
LIBRARY CALL: classify_migration -> ReversibilityClass + ActivationGate.check.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.reversibility_primitive import ReversibilityStore
from loam.scope_of_work import ReversibilityClass

from loam.state_migration_engine import (
    AppliedCursor,
    MigrationSafetyEnvelope,
    ProtectionFloorRefusal,
    classify_migration,
    read_cursor,
    replay,
    validate_migration_mapping,
)

from .conftest import seed_workspace, write_migration


def _envelope(tmp_path: Path) -> MigrationSafetyEnvelope:
    store = ReversibilityStore(tmp_path / "rev.sqlite")
    return MigrationSafetyEnvelope(store=store, snapshot_root=tmp_path / "snap")


def test_AC_MIG_SAFE_1_backup_first(tmp_path: Path) -> None:
    """Before any migration mutates user-state a recoverable backup of .loam/
    exists."""
    ws = tmp_path / "ws"
    seed_workspace(ws, episodes={"e1.md": "seeded body"})
    env = _envelope(tmp_path)
    snap = env.snapshot(ws)
    # The snapshot carries the seeded episode verbatim.
    assert (snap / "memory" / "episodes" / "e1.md").read_text() == "seeded body"


def test_AC_MIG_SAFE_2_rollback_on_failure_no_cursor_advance(
    tmp_path: Path,
) -> None:
    """A failing migration rolls user-state back to the pre-replay snapshot
    AND the cursor is not advanced past the last-good migration."""
    md = tmp_path / "migrations"
    # m1 ok; m2 declares removes_user_state with no binding -> protection-floor
    # refusal mid-chain (a real in-chain failure).
    write_migration(md, slug="m1", version="v0.1.0", operation="no-op")
    write_migration(
        md,
        slug="m2",
        version="v0.2.0",
        operation="structural-only",
        creates=[".loam/user-model/"],
        removes_user_state=True,  # -> irreversible -> refused (no binding)
    )
    ws = tmp_path / "ws"
    seed_workspace(ws, episodes={"e1.md": "original"})
    env = _envelope(tmp_path)

    result = replay(ws, migrations_dir=md, envelope=env)
    assert result.rolled_back is True
    assert result.applied == []
    # Seeded state is intact (restored).
    assert (ws / ".loam" / "memory" / "episodes" / "e1.md").read_text() == "original"
    # m2's structural path was NOT left behind.
    assert not (ws / ".loam" / "user-model").exists()
    # Cursor not advanced.
    cursor = read_cursor(ws)
    assert cursor.applied_slugs == []
    assert cursor.applied_version is None


def test_AC_MIG_SAFE_3_idempotent_rerun(tmp_path: Path) -> None:
    """Re-running an already-applied replay does not double-apply or corrupt
    state."""
    md = tmp_path / "migrations"
    write_migration(md, slug="m1", version="v0.1.0", operation="structural-only", creates=[".loam/user-model/"])
    ws = tmp_path / "ws"
    seed_workspace(ws)
    env = _envelope(tmp_path)

    replay(ws, migrations_dir=md, envelope=env)
    # Cursor records exactly one slug.
    assert read_cursor(ws).applied_slugs == ["m1"]
    # Re-run twice more — still exactly one slug, no double-append.
    replay(ws, migrations_dir=md, envelope=env)
    replay(ws, migrations_dir=md, envelope=env)
    assert read_cursor(ws).applied_slugs == ["m1"]


def test_AC_MIG_SAFE_4_protection_floor_classification(tmp_path: Path) -> None:
    """A migration declaring it removes user-state is classed irreversible and
    refused by the reversibility activation gate unless a binding exists; a
    non-destructive one is fully_reversible and passes."""
    destructive = validate_migration_mapping(
        {"slug": "d", "operation": "structural-only", "reversible": True,
         "removes_user_state": True}
    )
    benign = validate_migration_mapping(
        {"slug": "b", "operation": "no-op", "reversible": True}
    )
    assert classify_migration(destructive) == ReversibilityClass.irreversible
    assert classify_migration(benign) == ReversibilityClass.fully_reversible

    env = _envelope(tmp_path)
    # Benign passes the gate.
    env.guard(benign, scope_id="migration-b")
    # Destructive with no compensation binding is REFUSED (composes the
    # primitive's ActivationGate -32050 fail-closed posture).
    with pytest.raises(ProtectionFloorRefusal):
        env.guard(destructive, scope_id="migration-d")


def test_AC_MIG_SAFE_4_binding_lets_destructive_pass(tmp_path: Path) -> None:
    """When a compensation binding is registered for the scope, the otherwise-
    refused destructive migration passes the gate (the primitive's R-class
    matrix, composed as a library call)."""
    from loam.reversibility_primitive import CompensationPathBinding

    env = _envelope(tmp_path)
    destructive = validate_migration_mapping(
        {"slug": "d", "operation": "structural-only", "reversible": True,
         "removes_user_state": True}
    )
    env.store.upsert_binding(
        CompensationPathBinding(
            scope_id="migration-d",
            handle="restore_snapshot",
            idempotency_key="k-d",
        )
    )
    # Now the gate passes (binding present).
    env.guard(destructive, scope_id="migration-d")
