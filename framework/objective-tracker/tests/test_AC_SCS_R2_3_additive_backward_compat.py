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

"""AC.SCS-R2.3 — existing tracker records unchanged by the schema
addition (additive, default-preserving — amendment-38 D8 round-trip
precedent).

Plan: docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.md
§5 Family AC.SCS-R2.*; §15 backwards-compat verification.

Outcome (verbatim from §5 AC.SCS-R2.3):

  Existing tracker records authored before R2 are unchanged by the
  schema addition (additive, default-preserving — amendment-38 D8
  round-trip precedent).

Verification (verbatim from §5):

  Run the amendment-38-style backward-compat + D8 round-trip suite
  against pre-R2 fixtures; assert byte/semantic stability.

Method note (D-SCS-R2.build.1): the owner-pending widening adds one
enum value + the `active↔owner_pending` / `owner_pending→{achieved,
abandoned}` legal transitions. No pre-R2 transition is removed or
altered; status is persisted as TEXT and the projection folds
`to_status` generically — so a pre-R2 event stream replays to the
identical projection post-widening. This mirrors AC38.2/AC38.5
(existing suite + round-trip unchanged by an additive widening).
"""

from __future__ import annotations

from loam.objective_tracker.policies import (
    LEGAL_TRANSITIONS,
    TERMINAL_STATES,
    is_legal,
)
from loam.objective_tracker.projection import project
from loam.objective_tracker.spec import ObjectiveStatus
from tests.conftest import make_child_spec, make_user_root_spec


async def _seed_pre_r2_population(rt) -> dict[str, str]:
    """Drive a population through ONLY pre-R2 lifecycle transitions
    (proposed→active→{achieved|abandoned}, re_open). No owner_pending."""
    root = await rt.create(make_user_root_spec(goal="alpha"))
    await rt.start(root.objective_id)
    await rt.evaluate_criterion(
        root.objective_id, criterion_id="root-c1", result="met"
    )
    await rt.mark_achieved(root.objective_id, evidence="done")

    child_root = await rt.create(make_user_root_spec(goal="beta"))
    child = await rt.create(make_child_spec(parent_id=child_root.objective_id))
    await rt.start(child_root.objective_id)
    await rt.start(child.objective_id)
    await rt.mark_abandoned(child.objective_id, rationale="superseded")
    return {
        "alpha": root.objective_id,
        "beta": child_root.objective_id,
        "child": child.objective_id,
    }


def test_AC_SCS_R2_3_pre_r2_transitions_all_still_legal() -> None:
    """Every pre-R2 legal transition is still legal post-widening
    (additive: no transition removed or altered)."""
    pre_r2_legal = {
        (ObjectiveStatus.proposed, ObjectiveStatus.active),
        (ObjectiveStatus.proposed, ObjectiveStatus.abandoned),
        (ObjectiveStatus.active, ObjectiveStatus.achieved),
        (ObjectiveStatus.active, ObjectiveStatus.abandoned),
        (ObjectiveStatus.achieved, ObjectiveStatus.active),
        (ObjectiveStatus.abandoned, ObjectiveStatus.active),
    }
    for frm, to in pre_r2_legal:
        assert is_legal(frm, to), (
            f"pre-R2 transition {frm.value}→{to.value} regressed"
        )


def test_AC_SCS_R2_3_terminal_set_unchanged() -> None:
    """The terminal set is exactly the pre-R2 set — owner_pending did
    NOT join it (an open loop awaiting the owner is not closed)."""
    assert TERMINAL_STATES == {
        ObjectiveStatus.achieved,
        ObjectiveStatus.abandoned,
    }


def test_AC_SCS_R2_3_no_pre_r2_state_gained_unexpected_transitions() -> None:
    """proposed/achieved/abandoned out-edges are byte-identical to
    pre-R2; only `active` gained one out-edge (→owner_pending) and the
    new `owner_pending` source was added — strictly additive."""
    assert LEGAL_TRANSITIONS[ObjectiveStatus.proposed] == {
        ObjectiveStatus.active,
        ObjectiveStatus.abandoned,
    }
    assert LEGAL_TRANSITIONS[ObjectiveStatus.achieved] == {
        ObjectiveStatus.active,
    }
    assert LEGAL_TRANSITIONS[ObjectiveStatus.abandoned] == {
        ObjectiveStatus.active,
    }
    # active: pre-R2 {achieved, abandoned} PLUS owner_pending (R2) PLUS
    # blocked (WMS increment 2 — same additive precedent: the `active`
    # source gains one out-edge to the new non-terminal lifecycle member;
    # no pre-existing out-edge is removed or altered, AC.WI.1). The
    # proposed / achieved / abandoned out-edges above stay byte-identical.
    assert LEGAL_TRANSITIONS[ObjectiveStatus.active] == {
        ObjectiveStatus.achieved,
        ObjectiveStatus.abandoned,
        ObjectiveStatus.owner_pending,
        ObjectiveStatus.blocked,
    }


async def test_AC_SCS_R2_3_pre_r2_population_round_trips_unchanged(
    tracker,
) -> None:
    """D8-style round-trip: a pre-R2 event stream replays to the
    identical projection post-widening (status/goal/parentage stable)."""
    ids = await _seed_pre_r2_population(tracker)

    expected = {
        ids["alpha"]: ObjectiveStatus.achieved,
        ids["beta"]: ObjectiveStatus.active,
        ids["child"]: ObjectiveStatus.abandoned,
    }
    for oid, want_status in expected.items():
        proj = tracker.get(oid)
        assert proj is not None
        assert proj.status == want_status
        # Replay the raw event stream into a fresh projection — must
        # fold to the same status (event-sourcing fidelity, D8).
        events = tracker.store.events_for(oid)
        replayed = project(oid, events)
        assert replayed.status == want_status, (
            f"{oid}: replay drifted {replayed.status} != {want_status}"
        )


async def test_AC_SCS_R2_3_pre_r2_records_never_carry_owner_pending(
    tracker,
) -> None:
    """A population driven only through pre-R2 transitions never lands
    in owner_pending — the new state is opt-in, default-preserving."""
    ids = await _seed_pre_r2_population(tracker)
    for oid in ids.values():
        proj = tracker.get(oid)
        assert proj is not None
        assert proj.status != ObjectiveStatus.owner_pending
