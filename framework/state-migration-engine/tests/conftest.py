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

"""Shared fixtures for the state-migration-engine tests.

Helpers to author declared-migration files + seed a workspace so each test
drives the real surfaces against a fresh temp instance (never live user-state).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from loam.reversibility_primitive import ReversibilityStore

from loam.state_migration_engine.envelope import MigrationSafetyEnvelope


def write_migration(
    directory: Path,
    *,
    slug: str,
    operation: str = "no-op",
    version: str | None = None,
    reversible: bool = True,
    removes_user_state: bool = False,
    idempotent: bool = True,
    creates: list[str] | None = None,
    extra: dict | None = None,
) -> Path:
    """Author a ``<slug>.migration.yaml`` under *directory*; return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    doc: dict = {
        "slug": slug,
        "operation": operation,
        "reversible": reversible,
        "removes_user_state": removes_user_state,
        "idempotent": idempotent,
    }
    if version is not None:
        doc["version"] = version
    if creates is not None:
        doc["creates"] = creates
    if extra:
        doc.update(extra)
    path = directory / f"{slug}.migration.yaml"
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return path


def seed_workspace(
    root: Path, *, episodes: dict[str, str] | None = None
) -> Path:
    """Seed a minimal ``.loam/`` workspace with real user-state.

    Creates ``.loam/memory/episodes/`` + ``.loam/migrations/`` and writes the
    given ``episodes`` (name -> body) so a test can assert the seeded state
    survives a replay intact.
    """
    loam = root / ".loam"
    (loam / "memory" / "episodes").mkdir(parents=True, exist_ok=True)
    (loam / "migrations").mkdir(parents=True, exist_ok=True)
    for name, body in (episodes or {}).items():
        (loam / "memory" / "episodes" / name).write_text(
            body, encoding="utf-8"
        )
    return loam


@pytest.fixture
def make_envelope(tmp_path: Path):
    """Factory: a MigrationSafetyEnvelope backed by a temp store + snapshot."""

    def _make(snapshot_root: Path | None = None) -> MigrationSafetyEnvelope:
        sroot = snapshot_root or (tmp_path / "snap")
        sroot.mkdir(parents=True, exist_ok=True)
        store = ReversibilityStore(sroot / "rev.sqlite")
        return MigrationSafetyEnvelope(store=store, snapshot_root=sroot)

    return _make
