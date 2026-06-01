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

"""AC.UPGR.2 — the auto-upgrade COMPOSES the sealed engine + envelope.

The auto-upgrade applies pending migrations by INVOKING the sealed
``loam migrate`` engine wrapped in the existing ``reversibility-primitive``
backup-verify-rollback envelope — NOT a re-implemented apply path. The trigger
is a THIN consumer: the safety envelope (backup-first, protection-floor,
rollback-on-failure) is INHERITED, never re-built (plan §8.3 — the #1
boundary-leak risk).

Proven two ways:
  (1) the module routes the replay THROUGH the sealed ``replay.replay`` taking
      a sealed ``MigrationSafetyEnvelope`` over a sealed ``ReversibilityStore``
      (a spy on the sealed replay confirms the auto-upgrade hands it a real
      MigrationSafetyEnvelope — no parallel apply path);
  (2) the inherited rollback-on-failure fires: a failing migration leaves the
      seeded user-state restored to its pre-upgrade bytes, with NO advanced
      cursor — the envelope's work, not the trigger's.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
ORCH_SCRIPTS = REPO_ROOT / "framework" / "orchestrator" / "scripts"
if str(ORCH_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(ORCH_SCRIPTS))

import auto_upgrade  # noqa: E402
from auto_upgrade import run_auto_upgrade  # noqa: E402

from loam.state_migration_engine.envelope import MigrationSafetyEnvelope  # noqa: E402
from loam.state_migration_engine.cursor import read_cursor  # noqa: E402

# The package ``__init__`` re-exports ``replay`` as a name, shadowing the
# submodule attribute; the real module is the one registered in sys.modules.
# Patch THAT object so the production module's lazy ``from ...replay import
# replay`` (which resolves the same module object) picks up the spy.
import importlib  # noqa: E402

engine_replay = importlib.import_module("loam.state_migration_engine.replay")


def _write_migration(directory: Path, *, slug: str, version: str, operation: str = "structural-only", creates=None) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    doc = {
        "slug": slug,
        "operation": operation,
        "reversible": True,
        "removes_user_state": False,
        "idempotent": True,
        "version": version,
    }
    if creates is not None:
        doc["creates"] = creates
    (directory / f"{slug}.migration.yaml").write_text(
        yaml.safe_dump(doc, sort_keys=False), encoding="utf-8"
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


def test_AC_UPGR_2_routes_through_sealed_replay_with_real_envelope(
    tmp_path: Path, monkeypatch
) -> None:
    """The auto-upgrade hands the SEALED ``replay.replay`` a real
    ``MigrationSafetyEnvelope`` — proving it composes the sealed wrapped path,
    not a re-implemented apply/backup loop."""
    ws = tmp_path / "ws"
    _seed_cursor(ws, applied_version="v0.1.0", applied_slugs=["m1"])
    md = tmp_path / "docs" / "state-migrations"
    _write_migration(md, slug="m1", version="v0.1.0", operation="no-op")
    _write_migration(md, slug="m2", version="v0.2.0", creates=[".loam/user-model/"])

    captured: dict = {}
    real_replay = engine_replay.replay

    def _spy_replay(workspace_root, *, migrations_dir, envelope, target_version=None):
        captured["envelope"] = envelope
        captured["workspace_root"] = Path(workspace_root)
        return real_replay(
            workspace_root,
            migrations_dir=migrations_dir,
            envelope=envelope,
            target_version=target_version,
        )

    # The module imports ``replay`` lazily from the engine; patch the engine's
    # symbol so the auto-upgrade's own import resolves to the spy.
    monkeypatch.setattr(engine_replay, "replay", _spy_replay)

    res = run_auto_upgrade(ws, migrations_dir=md)

    # The sealed replay was invoked with a REAL sealed envelope (the safety
    # primitive), against the workspace the auto-upgrade was asked to migrate.
    assert isinstance(captured.get("envelope"), MigrationSafetyEnvelope)
    assert captured["workspace_root"] == ws.resolve() or captured["workspace_root"] == ws
    # The sealed replay actually applied the pending migration (composed path).
    assert res.applied == ["m2"]
    assert read_cursor(ws).applied_version == "v0.2.0"
    assert (ws / ".loam" / "user-model").is_dir()


def test_AC_UPGR_2_inherited_rollback_restores_on_failure(
    tmp_path: Path, monkeypatch
) -> None:
    """A migration failure is rolled back BY THE INHERITED ENVELOPE: the
    seeded user-state returns to its pre-upgrade bytes and the cursor is NOT
    advanced — the trigger re-implements no rollback of its own."""
    ws = tmp_path / "ws"
    _seed_cursor(ws, applied_version="v0.1.0", applied_slugs=["m1"])
    # Real seeded user-state that must survive a rolled-back replay intact.
    ep = ws / ".loam" / "memory" / "episodes"
    ep.mkdir(parents=True, exist_ok=True)
    (ep / "ep-001.md").write_text("real user episode — must survive rollback", encoding="utf-8")

    md = tmp_path / "docs" / "state-migrations"
    _write_migration(md, slug="m1", version="v0.1.0", operation="no-op")
    _write_migration(md, slug="m2", version="v0.2.0", creates=[".loam/user-model/"])

    # Force the sealed apply step to raise mid-replay — the SEALED replay's own
    # try/except triggers the envelope.restore (inherited rollback).
    def _boom(migration, workspace_root):
        raise RuntimeError("simulated migration failure")

    monkeypatch.setattr(engine_replay, "_apply_declarative_step", _boom)

    res = run_auto_upgrade(ws, migrations_dir=md)

    # The inherited envelope rolled the workspace back.
    assert res.rolled_back is True
    assert res.applied == []
    # The cursor was NOT advanced (still at the pre-upgrade version).
    assert read_cursor(ws).applied_version == "v0.1.0"
    # The seeded user-state survived the rollback intact.
    assert (ep / "ep-001.md").read_text() == "real user episode — must survive rollback"
    # No half-migrated artefact left behind.
    assert not (ws / ".loam" / "user-model").exists()


def test_AC_UPGR_2_no_local_apply_or_backup_reimplementation() -> None:
    """The trigger module re-implements no apply/replay/backup path: it carries
    no filesystem-mutating copy/snapshot/rmtree of its own — every such step is
    delegated to the sealed engine + envelope (plan §8.3 boundary)."""
    source = Path(auto_upgrade.__file__).read_text()
    # The module must NOT itself shutil-copy / rmtree / mkdir user-state, nor
    # re-walk the migration apply vocabulary — those are the sealed engine's.
    for forbidden in ("shutil.copytree", "shutil.rmtree", "structural-only", "_apply_declarative_step"):
        assert forbidden not in source, (
            f"auto_upgrade.py re-implements a sealed path ({forbidden!r}); it "
            "must COMPOSE the engine/envelope, not duplicate it (plan §8.3)."
        )
    # It DOES compose the sealed surfaces by name.
    for composed in ("replay", "MigrationSafetyEnvelope", "ReversibilityStore", "enumerate_pending"):
        assert composed in source, f"expected the auto-upgrade to compose {composed!r}"
