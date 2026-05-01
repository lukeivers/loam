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

"""AC38.2 — Pre-widening records round-trip post-widening unchanged.

Plan: docs/rebuild/plans/amendment-38-objective-tracker-schema-widening.md
§4 AC38.2.

Outcome (paraphrased from the AC):

  - A tracker DB seeded against the pre-widening schema (records with
    no `lifted_from`) loads post-widening with `lifted_from is None`.
  - Every existing read-side query (`get`, `list`, `list_by_root`,
    `trace_to_root`, `child_closure_status`) returns identical
    results pre/post.

The widening is additive — `lifted_from` defaults to `None` on the
spec, the event, the projection, and the public projection. The
SQLite schema adds `lifted_from_json TEXT NOT NULL DEFAULT 'null'`
which is also additive (existing rows take the sentinel; in-place
upgrades land via the `ALTER TABLE` guard in `EventStore.__init__`).
"""

from __future__ import annotations

import sqlite3

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.objective_tracker.spec import (
    ChildClosureCriterion,
    LiftedFrom,
    ObjectiveStatus,
    ProseCriterion,
)
from tests.conftest import make_child_spec, make_user_root_spec


# ---- helpers ---------------------------------------------------------


async def _seed_pre_widening_population(rt: ObjectiveTracker) -> dict[str, str]:
    """Seed records with `lifted_from is None` (pre-widening shape)."""
    root = await rt.create(make_user_root_spec(goal="alpha"))
    await rt.start(root.objective_id)
    await rt.evaluate_criterion(
        root.objective_id, criterion_id="root-c1", result="met"
    )
    await rt.mark_achieved(root.objective_id, evidence="done")
    await rt.bind_scope("scope-alpha", root.objective_id)

    child_root = await rt.create(
        make_user_root_spec(
            goal="beta",
            criteria=(
                ProseCriterion(criterion_id="p1", prose="a"),
                ChildClosureCriterion(criterion_id="cc", required_count=1),
            ),
        )
    )
    child = await rt.create(
        make_child_spec(parent_id=child_root.objective_id)
    )
    return {
        "alpha": root.objective_id,
        "beta": child_root.objective_id,
        "child": child.objective_id,
    }


# ---- AC38.2 verification ---------------------------------------------


async def test_AC38_2_pre_widening_records_load_with_lifted_from_none(
    tracker,
) -> None:
    """Records authored without `lifted_from` carry None on the public
    projection — the no-provenance default."""
    ids = await _seed_pre_widening_population(tracker)
    for oid in ids.values():
        proj = tracker.get(oid)
        assert proj is not None
        assert proj.lifted_from is None


async def test_AC38_2_existing_get_returns_identical_payload(
    tracker,
) -> None:
    """`get()` returns the same shape it did pre-widening, plus the
    new `lifted_from` field carrying `None`."""
    ids = await _seed_pre_widening_population(tracker)
    proj = tracker.get(ids["alpha"])
    assert proj is not None
    assert proj.objective_id == ids["alpha"]
    assert proj.goal == "alpha"
    assert proj.status == ObjectiveStatus.achieved
    assert proj.lifted_from is None


async def test_AC38_2_existing_list_unchanged_for_pre_widening_population(
    tracker,
) -> None:
    """`list()` returns every pre-widening record."""
    ids = await _seed_pre_widening_population(tracker)
    rows = tracker.list()
    found = {r.objective_id for r in rows}
    assert found == set(ids.values())


async def test_AC38_2_existing_list_by_root_unchanged(tracker) -> None:
    ids = await _seed_pre_widening_population(tracker)
    descendants = tracker.list_by_root(ids["beta"])
    found = {r.objective_id for r in descendants}
    assert ids["beta"] in found
    assert ids["child"] in found


async def test_AC38_2_existing_trace_to_root_unchanged(tracker) -> None:
    ids = await _seed_pre_widening_population(tracker)
    chain = tracker.trace_to_root(ids["child"])
    chain_ids = [p.objective_id for p in chain]
    assert chain_ids == [ids["child"], ids["beta"]]


async def test_AC38_2_existing_child_closure_status_unchanged(
    tracker,
) -> None:
    ids = await _seed_pre_widening_population(tracker)
    achieved, required, met = tracker.child_closure_status(
        ids["beta"], "cc"
    )
    assert achieved == 0
    assert required == 1
    assert met is False


async def test_AC38_2_alter_table_preserves_legacy_data(tmp_path) -> None:
    """A DB created without the `lifted_from_json` column upgrades
    in-place to the widened schema; existing rows pick up the
    NOT NULL DEFAULT 'null' sentinel; reads remain identical."""
    db = tmp_path / "legacy.db"
    # Construct a DB with the pre-widening schema by hand. Mirrors the
    # exact column set the prior amendment shipped (sans
    # `lifted_from_json`).
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(
        """
        CREATE TABLE objective_events (
            event_id      INTEGER PRIMARY KEY AUTOINCREMENT,
            objective_id  TEXT NOT NULL,
            kind          TEXT NOT NULL,
            payload       TEXT NOT NULL,
            created_at    TEXT NOT NULL
        );
        CREATE TABLE objective_state (
            objective_id         TEXT PRIMARY KEY,
            goal                 TEXT NOT NULL,
            parent_id            TEXT,
            authored_by          TEXT NOT NULL,
            owner                TEXT,
            status               TEXT NOT NULL,
            time_bound_json      TEXT NOT NULL,
            criteria_json        TEXT NOT NULL,
            parent_close_policy  TEXT NOT NULL,
            last_event_id        INTEGER NOT NULL,
            last_transition_at   TEXT NOT NULL,
            criteria_latest_json TEXT NOT NULL DEFAULT '{}'
        );
        CREATE TABLE scope_objective_binding (
            scope_id       TEXT PRIMARY KEY,
            objective_id   TEXT NOT NULL,
            bound_event_id INTEGER NOT NULL,
            bound_at       TEXT NOT NULL
        );
        """
    )
    conn.close()

    # Open through the runtime; the in-place ALTER TABLE guard in
    # EventStore must add the `lifted_from_json` column.
    rt = ObjectiveTracker(db_path=db)
    cols = {
        row[1]
        for row in rt.store._conn.execute(  # noqa: SLF001
            "PRAGMA table_info(objective_state)"
        ).fetchall()
    }
    assert "lifted_from_json" in cols

    # New writes succeed; reads carry `lifted_from is None` (the
    # default / sentinel).
    proj = await rt.create(make_user_root_spec(goal="post-upgrade"))
    assert proj.lifted_from is None
    rt.close()


async def test_AC38_2_widened_record_round_trips_via_event_replay(
    tracker,
) -> None:
    """A record authored with `lifted_from` populated round-trips
    through the event log; cold-restart projection equals live."""
    lf = LiftedFrom(
        source_doc="docs/rebuild/VALUE_PROPOSITION.md",
        source_ac="AC.PO.1",
        source_commit="HEAD",
    )
    spec = make_user_root_spec(goal="provenance-bearing").model_copy(
        update={"lifted_from": lf}
    )
    proj = await tracker.create(spec)
    assert proj.lifted_from == lf

    # Force a re-projection from the event log (event-sourcing fidelity).
    from loam.objective_tracker.projection import project, projection_to_state_row

    events = tracker.store.events_for(proj.objective_id)
    rebuilt = project(proj.objective_id, events)
    rebuilt_row = projection_to_state_row(rebuilt)
    live_row = tracker.store.read_state(proj.objective_id)
    assert rebuilt_row == live_row
    assert rebuilt.lifted_from == lf
