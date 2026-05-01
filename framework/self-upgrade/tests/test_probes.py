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

"""D4 — pre-upgrade probe run tests."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

from loam.self_upgrade.paths import Paths
from loam.self_upgrade.probes import (
    ProbeBundle,
    collect_pre_probe,
    post_upgrade_probe_hashes,
)


def _write_empty_sqlite_with_events_table(p: Path) -> None:
    """Write a SQLite DB shaped enough that the sealed components can
    open it without seeding synthetic events — the stores initialise
    their own tables on open.
    """
    p.parent.mkdir(parents=True, exist_ok=True)
    # Create an empty file; each sealed store's __init__ will create
    # its schema on connect.
    p.touch()


@pytest.fixture
def seeded_base(tmp_path: Path, monkeypatch) -> Paths:
    """Set up a base dir with actual sealed-component-compatible DBs.
    The stores create their schemas on open.
    """
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()

    # scope-of-work: let EventStore create its schema
    from loam.scope_of_work.store import EventStore as SowStore
    SowStore(str(p.scope_of_work_db))

    # objective-tracker
    from loam.objective_tracker.store import EventStore as ObjStore
    ObjStore(str(p.objective_tracker_db))

    # orchestrator
    from loam.orchestrator.local_state import LocalStateStore
    LocalStateStore(str(p.orchestrator_db))

    # degradation
    from loam.dormancy.state import DegradationStore
    DegradationStore(str(p.degradation_db))

    # aggregator: small sqlite with schema
    from tests.test_aggregator_probes import _seed_sqlite_aggregator
    _seed_sqlite_aggregator(p.aggregator_db.with_suffix(".sqlite"))
    # Leave the .duckdb absent so the probe falls through to .sqlite

    return p


def test_collect_pre_probe_runs_every_adapter(seeded_base: Paths) -> None:
    bundle = collect_pre_probe(seeded_base, "pos-v2-v0.2.0")
    assert set(bundle.records.keys()) == {
        "memory",
        "scope_of_work",
        "objective_tracker",
        "orchestrator",
        "degradation",
        "primary_persona",
        "aggregator",
    }


def test_collect_pre_probe_marks_skipped_for_missing(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("POS_BASE_DIR", str(tmp_path))
    p = Paths.from_env()
    bundle = collect_pre_probe(p, "pos-v2-v0.2.0")
    for comp in ("memory", "scope_of_work", "objective_tracker",
                 "orchestrator", "degradation", "aggregator"):
        assert bundle.records[comp].status in ("skipped", "error"), \
            f"{comp}: {bundle.records[comp].detail}"
    assert bundle.records["primary_persona"].status == "ok"


def test_scope_of_work_probe_ok(seeded_base: Paths) -> None:
    bundle = collect_pre_probe(seeded_base, "pos-v2-v0.2.0")
    rec = bundle.records["scope_of_work"]
    assert rec.status == "ok", rec.detail
    assert "probe_state_hash" in rec.payload


def test_orchestrator_probe_ok(seeded_base: Paths) -> None:
    bundle = collect_pre_probe(seeded_base, "pos-v2-v0.2.0")
    rec = bundle.records["orchestrator"]
    assert rec.status == "ok", rec.detail
    assert "histogram" in rec.payload or "total" in rec.payload


def test_degradation_probe_ok(seeded_base: Paths) -> None:
    bundle = collect_pre_probe(seeded_base, "pos-v2-v0.2.0")
    rec = bundle.records["degradation"]
    assert rec.status == "ok", rec.detail
    assert "schema_version" in rec.payload


def test_aggregator_probe_ok(seeded_base: Paths) -> None:
    bundle = collect_pre_probe(seeded_base, "pos-v2-v0.2.0")
    rec = bundle.records["aggregator"]
    assert rec.status == "ok", rec.detail
    assert "queries" in rec.payload
    assert "hash" in rec.payload


def test_probe_bundle_saves_and_round_trips(tmp_path: Path, seeded_base: Paths) -> None:
    bundle = collect_pre_probe(seeded_base, "pos-v2-v0.2.0")
    out = tmp_path / "pre-probe.json"
    bundle.save(out)
    data = json.loads(out.read_text())
    assert data["tag"] == "pos-v2-v0.2.0"
    assert "records" in data
    assert data["records"]["primary_persona"]["status"] == "ok"


def test_post_upgrade_hashes_stable(seeded_base: Paths) -> None:
    h1 = post_upgrade_probe_hashes(seeded_base)
    h2 = post_upgrade_probe_hashes(seeded_base)
    assert h1 == h2


def test_post_upgrade_hashes_change_after_write(seeded_base: Paths) -> None:
    h1 = post_upgrade_probe_hashes(seeded_base)
    # Touch the scope_of_work file
    seeded_base.scope_of_work_db.write_bytes(b"different bytes")
    h2 = post_upgrade_probe_hashes(seeded_base)
    assert h1["scope_of_work"] != h2["scope_of_work"]
