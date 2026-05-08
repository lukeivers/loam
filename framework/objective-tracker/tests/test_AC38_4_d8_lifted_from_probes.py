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

"""AC38.4 — D8 semantic round-trip harness covers `lifted_from`.

Plan: docs/plans/amendment-38-objective-tracker-schema-widening.md
§4 AC38.4.

Outcome (paraphrased from the AC):

  - Probe set covers the four shapes:
      1. `lifted_from` populated with all three keys.
      2. `lifted_from` populated without `source_commit`.
      3. `lifted_from is None` (explicit).
      4. `lifted_from` omitted at write time → loaded as None.
  - D8 harness drift report stays at zero for all four probe shapes
    under the existing threshold rule (`assert_no_drift(threshold=0)`).
  - Captured probe set survives JSON round-trip (matches
    `test_d8_upgrade_fidelity::test_round_trip_zero_drift` pattern).
"""

from __future__ import annotations

from loam.objective_tracker.runtime import ObjectiveTracker
from loam.objective_tracker.spec import LiftedFrom
from loam.objective_tracker.upgrade import (
    assert_no_drift,
    capture_pre_upgrade,
    captured_from_json,
    captured_to_json,
    replay_post_upgrade,
)
from tests.conftest import make_user_root_spec


VP_DOC = "docs/VALUE_PROPOSITION.md"


async def _seed_lifted_from_probes(rt: ObjectiveTracker) -> dict[str, str]:
    """Seed records covering every `lifted_from` shape the AC names."""
    out: dict[str, str] = {}

    # (1) populated with all three keys
    full_lf = LiftedFrom(
        source_doc=VP_DOC,
        source_ac="AC.PO.1",
        source_commit="abc1234",
    )
    out["full"] = (
        await rt.create(
            make_user_root_spec(goal="full-provenance").model_copy(
                update={"lifted_from": full_lf}
            )
        )
    ).objective_id

    # (2) populated without source_commit
    partial_lf = LiftedFrom(source_doc=VP_DOC, source_ac="AC.PO.2")
    out["partial"] = (
        await rt.create(
            make_user_root_spec(goal="partial-provenance").model_copy(
                update={"lifted_from": partial_lf}
            )
        )
    ).objective_id

    # (3) explicit None
    out["explicit_none"] = (
        await rt.create(
            make_user_root_spec(goal="explicit-none").model_copy(
                update={"lifted_from": None}
            )
        )
    ).objective_id

    # (4) omitted (default-None)
    out["omitted"] = (
        await rt.create(make_user_root_spec(goal="omitted-lifted_from"))
    ).objective_id

    return out


async def test_AC38_4_d8_round_trip_zero_drift_with_lifted_from(
    tmp_path,
) -> None:
    """The four `lifted_from` probe shapes pass D8 with zero drift."""
    db = tmp_path / "obj.db"
    rt = ObjectiveTracker(db_path=db)
    await _seed_lifted_from_probes(rt)
    captured = capture_pre_upgrade(
        rt.store, snapshot_to=tmp_path / "obj.snapshot.db"
    )
    rt.close()

    rt2 = ObjectiveTracker(db_path=db)
    report = replay_post_upgrade(rt2.store, captured)
    assert report.total_drift == 0, report.as_json()
    assert_no_drift(report, threshold=0)
    rt2.close()


async def test_AC38_4_captured_probes_json_round_trip(tmp_path) -> None:
    """The probe-set JSON round-trip preserves `lifted_from`."""
    db = tmp_path / "obj.db"
    rt = ObjectiveTracker(db_path=db)
    await _seed_lifted_from_probes(rt)
    captured = capture_pre_upgrade(rt.store)
    rt.close()

    js = captured_to_json(captured)
    rebuilt = captured_from_json(js)
    assert len(rebuilt.probes) == len(captured.probes)

    rt2 = ObjectiveTracker(db_path=db)
    report = replay_post_upgrade(rt2.store, rebuilt)
    assert report.total_drift == 0, report.as_json()
    rt2.close()


async def test_AC38_4_state_row_carries_lifted_from_json(tmp_path) -> None:
    """The projection cache row exposes `lifted_from_json` — the new
    column the D8 harness compares pre/post."""
    db = tmp_path / "obj.db"
    rt = ObjectiveTracker(db_path=db)
    ids = await _seed_lifted_from_probes(rt)

    full_row = rt.store.read_state(ids["full"])
    assert full_row is not None
    assert "lifted_from_json" in full_row
    assert VP_DOC in full_row["lifted_from_json"]

    none_row = rt.store.read_state(ids["explicit_none"])
    assert none_row is not None
    assert none_row["lifted_from_json"] == "null"

    omitted_row = rt.store.read_state(ids["omitted"])
    assert omitted_row is not None
    assert omitted_row["lifted_from_json"] == "null"

    rt.close()


async def test_AC38_4_d8_drift_detected_when_lifted_from_diverges(
    tmp_path,
) -> None:
    """Adding a new lifted_from-bearing record post-capture drifts the
    report — confirms the harness sees the new field on probe diff."""
    db = tmp_path / "obj.db"
    rt = ObjectiveTracker(db_path=db)
    await _seed_lifted_from_probes(rt)
    captured = capture_pre_upgrade(rt.store)

    new_lf = LiftedFrom(source_doc=VP_DOC, source_ac="AC.PO.NEW")
    new_proj = await rt.create(
        make_user_root_spec(goal="post-capture").model_copy(
            update={"lifted_from": new_lf}
        )
    )

    report = replay_post_upgrade(rt.store, captured)
    # The new record shows up as `extra_post`.
    assert new_proj.objective_id in report.extra_post
    rt.close()
