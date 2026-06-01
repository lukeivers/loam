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

"""AC.UPGR.1 — auto-detect a stale applied-migration cursor.

When a workspace's applied-migration cursor is BEHIND the migrations shipped
with the installed loam version, the auto-detect path NOTICES the gap — reads
the cursor, enumerates the pending declared migrations in release-version
order — WITHOUT the user running anything. A fresh / up-to-date workspace
yields an empty pending set (nothing to surface).

Composes the SEALED engine's own pending-set computation (read_cursor →
load_migration_dir → enumerate_pending); the detection half mutates no
user-state.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
ORCH_SCRIPTS = REPO_ROOT / "framework" / "orchestrator" / "scripts"
if str(ORCH_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ORCH_SCRIPTS))

from auto_upgrade import detect_pending, run_auto_upgrade  # noqa: E402


def _write_migration(directory: Path, *, slug: str, version: str, operation: str = "no-op") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{slug}.migration.yaml").write_text(
        yaml.safe_dump(
            {
                "slug": slug,
                "operation": operation,
                "reversible": True,
                "removes_user_state": False,
                "idempotent": True,
                "version": version,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _seed_cursor(ws: Path, *, applied_version: str, applied_slugs: list[str]) -> None:
    cur = ws / ".loam" / "migrations" / ".cursor"
    cur.parent.mkdir(parents=True, exist_ok=True)
    cur.write_text(
        yaml.safe_dump(
            {"applied_version": applied_version, "applied_slugs": applied_slugs},
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def test_AC_UPGR_1_behind_cursor_is_detected(tmp_path: Path) -> None:
    """A workspace at version N with shipped migrations N+1..N+k detects the
    pending set in release-version order — without the user running migrate."""
    ws = tmp_path / "ws"
    _seed_cursor(ws, applied_version="v0.1.0", applied_slugs=["m1"])

    md = tmp_path / "docs" / "state-migrations"
    _write_migration(md, slug="m1", version="v0.1.0")  # already applied
    _write_migration(md, slug="m2", version="v0.2.0")
    _write_migration(md, slug="m3", version="v0.3.0")

    pending = detect_pending(ws, migrations_dir=md)

    # Exactly the unapplied migrations, in release-version order.
    assert [m.slug for m in pending] == ["m2", "m3"]


def test_AC_UPGR_1_up_to_date_cursor_detects_nothing(tmp_path: Path) -> None:
    """A workspace whose cursor already covers every shipped migration yields
    an empty pending set (no false-positive auto-upgrade)."""
    ws = tmp_path / "ws"
    _seed_cursor(ws, applied_version="v0.3.0", applied_slugs=["m1", "m2", "m3"])

    md = tmp_path / "docs" / "state-migrations"
    _write_migration(md, slug="m1", version="v0.1.0")
    _write_migration(md, slug="m2", version="v0.2.0")
    _write_migration(md, slug="m3", version="v0.3.0")

    assert detect_pending(ws, migrations_dir=md) == []


def test_AC_UPGR_1_fresh_workspace_detects_all_pending(tmp_path: Path) -> None:
    """A fresh workspace (no cursor yet) reads as the empty cursor and detects
    every shipped migration as pending — never an error on absent state."""
    ws = tmp_path / "fresh"
    ws.mkdir()

    md = tmp_path / "docs" / "state-migrations"
    _write_migration(md, slug="m1", version="v0.1.0")
    _write_migration(md, slug="m2", version="v0.2.0")

    pending = detect_pending(ws, migrations_dir=md)
    assert [m.slug for m in pending] == ["m1", "m2"]


def test_AC_UPGR_1_run_reports_detected_flag(tmp_path: Path) -> None:
    """run_auto_upgrade surfaces the detection outcome: detected=True when a
    gap exists, detected=False on an up-to-date workspace (a quiet session)."""
    ws = tmp_path / "ws"
    _seed_cursor(ws, applied_version="v0.1.0", applied_slugs=["m1"])
    md = tmp_path / "docs" / "state-migrations"
    _write_migration(md, slug="m1", version="v0.1.0")
    _write_migration(md, slug="m2", version="v0.2.0")

    res = run_auto_upgrade(ws, migrations_dir=md)
    assert res.detected is True

    # After the upgrade the same workspace is up-to-date → a second run is quiet.
    res2 = run_auto_upgrade(ws, migrations_dir=md)
    assert res2.detected is False
    assert res2.surface is None
