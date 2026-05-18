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

"""AC.SCS-R1.1 + AC.SCS-R1.4 — the objective-tracker becomes the
seeded+backfilled open-loop register; an EXISTING, already-initialized,
never-seeded workspace gets its tracker backfilled via the PRODUCTION
update entry-point with NO pre-arranged tracker state.

Plan: docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.md
§5 Family AC.SCS-R1.*; AC.SCS-R1.4 is the designated outcome-altitude
AC (§5 ladder-up; `feedback_test_outcome_altitude_required`).

Outcomes (verbatim from §5):

  AC.SCS-R1.1: The workspace objective-tracker, after the R1 mechanism
  runs, contains the open owner-facing decisions + the sequenced dev
  queue as objectives chained to the workspace value-prop root.

  AC.SCS-R1.4 (outcome-altitude: true): An existing, already-
  initialized, never-seeded workspace, run through the production
  update entry-point with no pre-arranged tracker state, ends with its
  objective-tracker populated (the open-loop register present) —
  fresh-clone-only does NOT satisfy this.

Verification (verbatim from §5):

  R1.1: Query the tracker via the production projection API after the
  mechanism; assert the open-loop set is present + parented.

  R1.4: Invoke the production workspace-update entry-point against a
  workspace fixture that was initialized BEFORE the R1 mechanism
  existed and has 0 tracker rows; assert post-run the tracker is
  non-empty + parented. No test-pre-seeded state.

Method note (D-SCS-R1.build.1): the production update entry-point is
``tracker_seed.backfill_tracker_for_existing_workspace`` — it composes
the same classify→load→path→seed pipeline the first-run scaffold uses,
but bypasses the ``already_scaffolded`` short-circuit (that
short-circuit IS the defect: it stops the seed from ever running for an
already-scaffolded workspace). The AC pins the existing-workspace
outcome; the verb is the method (§5 method-in-AC test: YES).

OUTCOME-ALTITUDE DISCIPLINE (`feedback_test_outcome_altitude_required`):
``test_AC_SCS_R1_4_existing_unseeded_workspace_backfilled_via_production_entry``
invokes the real production entry-point against a workspace with NO
pre-arranged tracker state (0 rows verified BEFORE the call; the call
is the only thing that populates it). No stub seed runner, no
pre-seeded fixture — the exact defect's inverse.
"""

from __future__ import annotations

from pathlib import Path

from loam.objective_tracker import ObjectiveFilter, ObjectiveTracker
from loam.workspace_bootstrap.adapters.tracker_seed import (
    FRAMEWORK_VALUE_PROP_RELPATH,
    ROOT_OBJECTIVE_ID,
    SPEC_DOC_RELPATH,
    _SPEC_TIER_PHASES,
    backfill_tracker_for_existing_workspace,
    tracker_db_path_for,
)


def _make_existing_unseeded_dev_workspace(tmp_path: Path) -> Path:
    """An EXISTING, already-initialized workspace whose tracker was
    NEVER seeded — the exact defect state (a workspace scaffolded
    before the tracker-seed existed / before this mechanism ran).

    It carries the canonical VALUE_PROPOSITION.md + a dev-intent
    contract (so classification resolves pos-v2-dev), but its tracker
    DB has ZERO rows. No pre-arranged tracker state — the backfill
    call is the only thing that may populate it.
    """
    workspace = tmp_path / "existing-unseeded-ws"
    workspace.mkdir()
    (workspace / "docs").mkdir(parents=True)
    framework_vp = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "docs"
        / "VALUE_PROPOSITION.md"
    )
    (workspace / FRAMEWORK_VALUE_PROP_RELPATH).write_text(
        framework_vp.read_text()
    )
    _seed_dev_intent_contract(workspace)
    return workspace


def _seed_dev_intent_contract(workspace: Path) -> None:
    """Persona contract with ``dev_intent: yes`` so classify_workspace
    reads "pos-v2-dev". (Mirrors the AC39_1 helper — this is workspace
    INITIALIZATION state, NOT tracker pre-seeding.)"""
    from loam.primary_persona.contract import PersonaContract
    from loam.primary_persona.onboarding import dev_intent_storage_path

    persona_dir = dev_intent_storage_path(workspace) / "primary"
    persona_dir.mkdir(parents=True)
    contract = PersonaContract.model_validate(
        {
            "handle": "primary",
            "given_name": "Primary",
            "contract_version": "1.0.0",
            "responsibilities": {
                "single_point_of_contact": "Coordinator.",
                "context_holder": "Holds context.",
                "escalation_judge": "Decides surfacing.",
            },
            "authority_boundary": {
                "tier_a": "defer",
                "tier_b": "defer",
                "tier_c": "execute",
                "tier_d": "execute",
            },
            "escalation_taxonomy": {"categories": ["x"]},
            "severity_vocabulary": {"labels": ["a", "b"]},
            "is_starter": False,
            "is_primary": True,
            "dev_intent": "yes",
        }
    )
    (persona_dir / "contract.yaml").write_text(contract.to_yaml())


def _tracker_row_count(db_path: Path) -> int:
    if not db_path.exists():
        return 0
    tracker = ObjectiveTracker(db_path)
    try:
        return len(tracker.query_projection_view())
    finally:
        tracker.close()


def test_AC_SCS_R1_4_existing_unseeded_workspace_backfilled_via_production_entry(
    tmp_path: Path,
) -> None:
    """OUTCOME-ALTITUDE (AC.SCS-R1.4). An existing, already-initialized,
    never-seeded workspace, run through the PRODUCTION update
    entry-point with NO pre-arranged tracker state, ends with its
    objective-tracker populated + parented. The defect's exact inverse.
    """
    workspace = _make_existing_unseeded_dev_workspace(tmp_path)
    db_path = tracker_db_path_for(workspace)

    # No pre-arranged state — verify 0 rows BEFORE the production call.
    assert _tracker_row_count(db_path) == 0, (
        "fixture must have NO pre-arranged tracker state — the backfill "
        "call is the only thing that may populate it"
    )

    # The production update entry-point — no stub runner, no pre-seed.
    result = backfill_tracker_for_existing_workspace(workspace)

    assert result.seeded is True
    assert result.reason == "fresh_seed", (
        "an existing never-seeded workspace must take the fresh_seed "
        f"path, got {result.reason!r}"
    )

    # Post-run: tracker is non-empty + the register is parented.
    tracker = ObjectiveTracker(db_path)
    try:
        all_proj = tracker.query_projection_view()
        ids = {p.objective_id for p in all_proj}
        assert ids, "AC.SCS-R1.4 — tracker must be non-empty post-backfill"
        assert ROOT_OBJECTIVE_ID in ids, "value-prop root must be present"

        root = tracker.get(ROOT_OBJECTIVE_ID)
        assert root is not None
        assert root.parent_id is None, "the value-prop root is a true root"

        # Every spec-tier descendant present + chained to the root.
        for suffix, _ac, _prose in _SPEC_TIER_PHASES:
            child = tracker.get(f"spec-{suffix}")
            assert child is not None, f"spec-{suffix} descendant missing"
            assert child.parent_id == ROOT_OBJECTIVE_ID, (
                f"spec-{suffix} must be chained to the value-prop root"
            )
    finally:
        tracker.close()


def test_AC_SCS_R1_1_backfilled_register_present_and_parented(
    tmp_path: Path,
) -> None:
    """AC.SCS-R1.1 — after the R1 mechanism the tracker contains the
    open-loop register as objectives chained to the workspace
    value-prop root, queryable via the production projection API."""
    workspace = _make_existing_unseeded_dev_workspace(tmp_path)
    backfill_tracker_for_existing_workspace(workspace)

    tracker = ObjectiveTracker(tracker_db_path_for(workspace))
    try:
        # Production projection API + the amendment-38 filter — the
        # register is discoverable as the value-prop-rooted tree.
        vp_rooted = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=FRAMEWORK_VALUE_PROP_RELPATH)
        )
        assert any(p.objective_id == ROOT_OBJECTIVE_ID for p in vp_rooted), (
            "AC.SCS-R1.1 — the value-prop root must be present + queryable"
        )
        spec_rooted = tracker.query_projection_view(
            ObjectiveFilter(lifted_from_source_doc=SPEC_DOC_RELPATH)
        )
        assert {p.objective_id for p in spec_rooted} == {
            f"spec-{s}" for s, _a, _p in _SPEC_TIER_PHASES
        }, "AC.SCS-R1.1 — the sequenced register descendants must be present"
        for p in spec_rooted:
            assert p.parent_id == ROOT_OBJECTIVE_ID
    finally:
        tracker.close()


def test_AC_SCS_R1_4_backfill_is_idempotent_no_clobber(
    tmp_path: Path,
) -> None:
    """Halt-trigger 1 / AC.SCS-R1.4 no-clobber: a second backfill is a
    no-op (query-then-skip, amendment-39 already_seeded precedent) and
    a user-edited record is left untouched."""
    workspace = _make_existing_unseeded_dev_workspace(tmp_path)
    first = backfill_tracker_for_existing_workspace(workspace)
    assert first.reason == "fresh_seed"

    db_path = tracker_db_path_for(workspace)

    # Simulate a user edit to a register record between backfills:
    # transition the root to active via the production API. The second
    # backfill must NOT clobber this.
    import asyncio

    async def _user_edits_root() -> None:
        tracker = ObjectiveTracker(db_path)
        try:
            await tracker.start(ROOT_OBJECTIVE_ID, rationale="user took it up")
        finally:
            tracker.close()

    asyncio.run(_user_edits_root())

    second = backfill_tracker_for_existing_workspace(workspace)
    assert second.reason == "already_seeded", (
        "a second backfill must be an idempotent no-op (no re-create)"
    )
    assert second.descendants_seeded == ()

    tracker = ObjectiveTracker(db_path)
    try:
        root = tracker.get(ROOT_OBJECTIVE_ID)
        assert root is not None
        # The user edit survived — not clobbered back to proposed.
        assert root.status.value == "active", (
            "AC.SCS-R1.4 — backfill must not clobber a user-edited record"
        )
    finally:
        tracker.close()
