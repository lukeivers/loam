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

"""AC.SCS-G.{1,2,3,4} — first-run↔update parity registry: single
discoverable surface, idempotent replay, R1 backfill registered
through it, non-silent gap surfacing.

Plan: docs/plans/session-clear-safety-tracker-register-and-first-run-update-parity.md
§5 Family AC.SCS-G.*; §6 halt-triggers; §4 AC.PO.2 (G is the reusable
harness primitive).

Outcomes (verbatim from §5):

  AC.SCS-G.1: Every state-mutating first-run/setup step that
  participates in the parity contract is discoverable from a single
  registry surface (the workspace-update process can enumerate "what
  must also run on update").

  AC.SCS-G.2: The workspace-update process, run against an existing
  workspace, replays each registered step's update-path, and replay is
  idempotent (a second run is a no-op, no clobber of user-authored
  state).

  AC.SCS-G.3: The R1 tracker-seed/backfill is registered through the G
  mechanism (the parity registry is the path by which an existing
  workspace's tracker gets backfilled — G is the structural home, R1
  is its first registered consumer); the AC.SCS-R1.4 outcome-altitude
  run goes through G.

  AC.SCS-G.4: A registered step whose update-path is absent or fails
  surfaces the gap explicitly (the update process does not silently
  skip — the failure class being fixed cannot recur as a silent skip).

Method note (D-SCS-G.build.*): a NEW lightweight registry (D-SCS.2
RATIFIED — explicitly NOT `first-run-inventory.yaml`, whose
already_scaffolded re-run-noop IS the defect). The AC pins the
*single discoverable surface* / *idempotent replay* / *non-silent gap*
outcomes; the registry shape (dict + dataclass + driver) is the method
(§5 method-in-AC test: YES per AC).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam.objective_tracker import ObjectiveTracker
from loam.workspace_bootstrap.adapters.parity_registry import (
    TRACKER_BACKFILL_STEP_NAME,
    ParityStep,
    ParityStepCollisionError,
    discover_parity_steps,
    register_default_parity_steps,
    register_parity_step,
    replay_parity_steps,
    unregister_parity_step,
)
from loam.workspace_bootstrap.adapters.tracker_seed import (
    FRAMEWORK_VALUE_PROP_RELPATH,
    ROOT_OBJECTIVE_ID,
    tracker_db_path_for,
)


@pytest.fixture
def clean_extra_step():
    """Register a uniquely-named test step; unregister after so the
    module-level registry is not polluted across tests. The built-in
    `tracker-backfill` step is left in place (it is registered at
    import time and is the AC.SCS-G.3 subject)."""
    added: list[str] = []

    def _add(step: ParityStep) -> None:
        register_parity_step(step)
        added.append(step.name)

    yield _add
    for name in added:
        unregister_parity_step(name)


def _make_existing_unseeded_dev_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "existing-ws-g"
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
    return workspace


# ---- AC.SCS-G.1 — single discoverable surface ------------------------


def test_AC_SCS_G_1_added_step_discoverable_without_discoverer_change(
    clean_extra_step,
) -> None:
    """A new state-mutating step added to the registry is enumerated
    by the discovery mechanism with NO code change to the discoverer
    — registration is the only action."""
    before = {s.name for s in discover_parity_steps()}
    sentinel = ParityStep(
        name="test-fixture-step",
        update_path=lambda ws: "ran",
        description="fixture",
    )
    clean_extra_step(sentinel)
    after = {s.name for s in discover_parity_steps()}
    assert "test-fixture-step" in after
    assert before <= after, "registration must be purely additive"


def test_AC_SCS_G_1_duplicate_name_raises_not_silent_overwrite(
    clean_extra_step,
) -> None:
    """Two steps under the same name raise — a silent overwrite would
    make the single-discoverable-surface contract lie."""
    clean_extra_step(ParityStep(name="dup-step", update_path=lambda ws: 1))
    with pytest.raises(ParityStepCollisionError):
        register_parity_step(ParityStep(name="dup-step", update_path=lambda ws: 2))


# ---- AC.SCS-G.3 — R1 backfill registered through G -------------------


def test_AC_SCS_G_3_tracker_backfill_registered_at_import() -> None:
    """R1's tracker backfill is discoverable through the G registry
    (registered at import time — not a one-off bypass)."""
    names = {s.name for s in discover_parity_steps()}
    assert TRACKER_BACKFILL_STEP_NAME in names, (
        "AC.SCS-G.3 — R1 backfill must be a G-registered step"
    )
    step = next(
        s for s in discover_parity_steps()
        if s.name == TRACKER_BACKFILL_STEP_NAME
    )
    assert step.update_path is not None, (
        "the tracker-backfill step must carry a wired update-path"
    )


def test_AC_SCS_G_3_register_default_is_idempotent() -> None:
    """`register_default_parity_steps` is idempotent — a defensive
    re-call before replay does not raise a collision."""
    register_default_parity_steps()
    register_default_parity_steps()  # must not raise
    names = [s.name for s in discover_parity_steps()]
    assert names.count(TRACKER_BACKFILL_STEP_NAME) == 1


def test_AC_SCS_G_3_R1_backfill_outcome_routes_through_G(
    tmp_path: Path,
) -> None:
    """AC.SCS-G.3 + AC.SCS-R1.4-through-G: replaying the parity steps
    against an existing unseeded workspace backfills its tracker via
    the G discovery+replay path (not a one-off bypass)."""
    workspace = _make_existing_unseeded_dev_workspace(tmp_path)
    db_path = tracker_db_path_for(workspace)

    # No pre-arranged tracker state.
    tracker = ObjectiveTracker(db_path) if db_path.exists() else None
    if tracker is not None:
        try:
            assert tracker.query_projection_view() == ()
        finally:
            tracker.close()

    report = replay_parity_steps(workspace)

    assert report.ok, f"replay must be clean; gaps={report.gaps}"
    backfill_outcome = next(
        o for o in report.outcomes if o.name == TRACKER_BACKFILL_STEP_NAME
    )
    assert backfill_outcome.status == "replayed"
    # The tracker is populated THROUGH the G replay path.
    tracker = ObjectiveTracker(db_path)
    try:
        ids = {p.objective_id for p in tracker.query_projection_view()}
        assert ROOT_OBJECTIVE_ID in ids, (
            "AC.SCS-G.3 — R1 backfill outcome must route through G "
            "(tracker populated via replay_parity_steps)"
        )
    finally:
        tracker.close()


# ---- AC.SCS-G.2 — idempotent replay, no clobber ----------------------


def test_AC_SCS_G_2_double_replay_is_noop_no_clobber(tmp_path: Path) -> None:
    """Run the workspace-update replay twice against the same existing
    workspace: first run applies the registered step, second run is a
    no-op, user-authored content untouched."""
    workspace = _make_existing_unseeded_dev_workspace(tmp_path)
    db_path = tracker_db_path_for(workspace)

    first = replay_parity_steps(workspace)
    assert first.ok
    first_backfill = next(
        o for o in first.outcomes if o.name == TRACKER_BACKFILL_STEP_NAME
    )
    assert first_backfill.result.reason == "fresh_seed"

    # User edits a register record between replays.
    import asyncio

    async def _user_edit() -> None:
        t = ObjectiveTracker(db_path)
        try:
            await t.start(ROOT_OBJECTIVE_ID, rationale="user took it up")
        finally:
            t.close()

    asyncio.run(_user_edit())

    second = replay_parity_steps(workspace)
    assert second.ok
    second_backfill = next(
        o for o in second.outcomes if o.name == TRACKER_BACKFILL_STEP_NAME
    )
    assert second_backfill.result.reason == "already_seeded", (
        "AC.SCS-G.2 — second replay must be an idempotent no-op"
    )

    t = ObjectiveTracker(db_path)
    try:
        root = t.get(ROOT_OBJECTIVE_ID)
        assert root is not None and root.status.value == "active", (
            "AC.SCS-G.2 — replay must not clobber user-authored state"
        )
    finally:
        t.close()


# ---- AC.SCS-G.4 — non-silent gap surfacing ---------------------------


def test_AC_SCS_G_4_failing_update_path_surfaced_not_swallowed(
    clean_extra_step,
) -> None:
    """A registered step whose update-path raises is surfaced as a
    NON-silent gap (report.ok False, step in gaps, error class
    recorded) — not swallowed; remaining steps still replay."""

    def _boom(ws: Path):
        raise RuntimeError("deliberate update-path failure")

    clean_extra_step(ParityStep(name="failing-step", update_path=_boom))

    report = replay_parity_steps(Path("/tmp/does-not-matter"))

    assert report.ok is False, "AC.SCS-G.4 — a failing step must not be clean"
    assert "failing-step" in report.gaps
    failed = next(o for o in report.outcomes if o.name == "failing-step")
    assert failed.status == "failed"
    assert "RuntimeError" in failed.detail
    assert "deliberate update-path failure" in failed.detail
    # The failure class being fixed (silent skip) cannot recur: the
    # gap is explicit in the structured report.


def test_AC_SCS_G_4_absent_update_path_surfaced_not_swallowed(
    clean_extra_step,
) -> None:
    """A step registered as participating in the parity contract but
    with NO wired update-path is surfaced as an explicit 'absent' gap,
    never silently skipped."""
    clean_extra_step(ParityStep(name="unwired-step", update_path=None))

    report = replay_parity_steps(Path("/tmp/does-not-matter"))

    assert report.ok is False
    assert "unwired-step" in report.gaps
    absent = next(o for o in report.outcomes if o.name == "unwired-step")
    assert absent.status == "absent"
    assert "no wired update-path" in absent.detail


def test_AC_SCS_G_4_one_broken_step_does_not_strand_the_rest(
    clean_extra_step,
) -> None:
    """A broken step is surfaced but the remaining registered steps
    still replay (one gap does not abort the whole update process)."""
    ran: list[str] = []

    clean_extra_step(
        ParityStep(
            name="broken",
            update_path=lambda ws: (_ for _ in ()).throw(ValueError("x")),
        )
    )
    clean_extra_step(
        ParityStep(
            name="healthy-after-broken",
            update_path=lambda ws: ran.append("healthy") or "ok",
        )
    )

    report = replay_parity_steps(Path("/tmp/x"))

    assert "broken" in report.gaps
    assert "healthy" in ran, (
        "AC.SCS-G.4 — a broken step must not strand the remaining steps"
    )
    healthy = next(
        o for o in report.outcomes if o.name == "healthy-after-broken"
    )
    assert healthy.status == "replayed"
