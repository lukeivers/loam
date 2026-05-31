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

"""AC.MIG-REPLAY.* — ordered cumulative replay through intermediates + cursor."""

from __future__ import annotations

from pathlib import Path

from loam.state_migration_engine import (
    AppliedCursor,
    enumerate_pending,
    load_migration_dir,
    read_cursor,
    replay,
)

from .conftest import seed_workspace, write_migration


def _author_chain(migrations_dir: Path) -> None:
    """Author a 3-migration chain at versions v0.1.0 / v0.2.0 / v0.3.0."""
    write_migration(migrations_dir, slug="m1", version="v0.1.0", operation="no-op")
    write_migration(migrations_dir, slug="m2", version="v0.2.0", operation="structural-only", creates=[".loam/user-model/"])
    write_migration(migrations_dir, slug="m3", version="v0.3.0", operation="no-op")


def test_AC_MIG_REPLAY_1_pending_set_correct_and_ordered(tmp_path: Path) -> None:
    """Given a cursor at N, the pending set is exactly N+1..N+k in a
    deterministic total order (release-version order, D1)."""
    md = tmp_path / "migrations"
    _author_chain(md)
    migrations = load_migration_dir(md)

    # Fresh cursor — all three pending, in version order.
    fresh = AppliedCursor()
    pending = enumerate_pending(fresh, migrations)
    assert [m.slug for m in pending] == ["m1", "m2", "m3"]

    # Cursor at v0.1.0 — only m2, m3 pending.
    at1 = AppliedCursor(applied_version="v0.1.0", applied_slugs=["m1"])
    pending = enumerate_pending(at1, migrations)
    assert [m.slug for m in pending] == ["m2", "m3"]

    # Bounded by target — N+1 only.
    pending = enumerate_pending(fresh, migrations, target_version="v0.1.0")
    assert [m.slug for m in pending] == ["m1"]


def test_AC_MIG_REPLAY_2_through_not_jump(tmp_path: Path) -> None:
    """Upgrading N->N+k applies EVERY intermediate in order, not only the
    target."""
    md = tmp_path / "migrations"
    _author_chain(md)
    ws = tmp_path / "ws"
    seed_workspace(ws)

    from loam.reversibility_primitive import ReversibilityStore
    from loam.state_migration_engine import MigrationSafetyEnvelope

    store = ReversibilityStore(tmp_path / "rev.sqlite")
    env = MigrationSafetyEnvelope(store=store, snapshot_root=tmp_path / "snap")

    result = replay(ws, migrations_dir=md, envelope=env, target_version="v0.3.0")
    # All three applied in order — m2 (the intermediate) is NOT skipped.
    assert result.applied == ["m1", "m2", "m3"]
    assert not result.rolled_back
    # m2's structural-only step created the declared path.
    assert (ws / ".loam" / "user-model").is_dir()


def test_AC_MIG_REPLAY_3_cursor_advance_and_rerun_noop(tmp_path: Path) -> None:
    """After a successful replay the cursor reads N+k; re-running is a clean
    no-op."""
    md = tmp_path / "migrations"
    _author_chain(md)
    ws = tmp_path / "ws"
    seed_workspace(ws)

    from loam.reversibility_primitive import ReversibilityStore
    from loam.state_migration_engine import MigrationSafetyEnvelope

    store = ReversibilityStore(tmp_path / "rev.sqlite")
    env = MigrationSafetyEnvelope(store=store, snapshot_root=tmp_path / "snap")

    first = replay(ws, migrations_dir=md, envelope=env)
    assert first.applied == ["m1", "m2", "m3"]

    cursor = read_cursor(ws)
    assert cursor.applied_version == "v0.3.0"
    assert cursor.applied_slugs == ["m1", "m2", "m3"]

    # Re-run — clean no-op, nothing re-applied.
    second = replay(ws, migrations_dir=md, envelope=env)
    assert second.applied == []
    assert not second.rolled_back
