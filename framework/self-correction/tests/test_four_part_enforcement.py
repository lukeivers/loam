"""CR7, CR8 — four-part structural enforcement.

The completion pre-check raises -32070 when record types are missing;
all four present → completion proceeds.
"""

from __future__ import annotations

from typing import Any

import pytest
from pos_orchestrator.ipc import ApplicationError

from self_correction import (
    CompletionPrecheck,
    CorrectionEpisode,
    CorrectionStore,
    EpisodeState,
    IPC_CORRECTION_INCOMPLETE_RECORDS,
    REQUIRED_RECORD_TYPES,
    RecordType,
    SelfCorrectionController,
    build_trigger_from_user_report,
)


def _seed_episode(store: CorrectionStore, *, scope_id: str) -> str:
    from self_correction.spec import CorrectionTrigger, TriggerSource

    trig = CorrectionTrigger(
        trigger_id="trig-seed",
        source=TriggerSource.user_reported,
        scope_id=scope_id,
    )
    store.insert_trigger(trig)
    ep = CorrectionEpisode(
        episode_id="ep-seed",
        trigger_id="trig-seed",
        correction_scope_id=scope_id,
        failure_class="something",
        state=EpisodeState.running,
    )
    store.insert_episode(ep)
    return "ep-seed"


def test_CR7_required_record_types_constant() -> None:
    # The four parts are structurally locked.
    assert REQUIRED_RECORD_TYPES == frozenset(
        {
            RecordType.failure_class,
            RecordType.instance_fix,
            RecordType.cause_diagnosed,
            RecordType.structural_remedy,
        }
    )


def test_CR7_precheck_raises_when_all_missing(store: CorrectionStore) -> None:
    _seed_episode(store, scope_id="scope-cr7-all")
    check = CompletionPrecheck(store=store)
    with pytest.raises(ApplicationError) as excinfo:
        check.run_or_raise(correction_scope_id="scope-cr7-all")
    assert excinfo.value.code == IPC_CORRECTION_INCOMPLETE_RECORDS
    assert "missing" in str(excinfo.value)


@pytest.mark.parametrize(
    "missing",
    [
        RecordType.failure_class,
        RecordType.instance_fix,
        RecordType.cause_diagnosed,
        RecordType.structural_remedy,
    ],
)
def test_CR7_precheck_raises_with_one_missing(
    store: CorrectionStore, missing: RecordType
) -> None:
    eid = _seed_episode(store, scope_id=f"scope-cr7-miss-{missing.value}")
    # Record the other three.
    for rt in REQUIRED_RECORD_TYPES - {missing}:
        store.insert_record(
            episode_id=eid, record_type=rt, payload={"placeholder": "x"}
        )
    check = CompletionPrecheck(store=store)
    with pytest.raises(ApplicationError) as excinfo:
        check.run_or_raise(
            correction_scope_id=f"scope-cr7-miss-{missing.value}"
        )
    assert excinfo.value.code == IPC_CORRECTION_INCOMPLETE_RECORDS
    assert missing.value in str(excinfo.value.data.get("missing", []))


def test_CR8_all_four_present_passes(store: CorrectionStore) -> None:
    eid = _seed_episode(store, scope_id="scope-cr8")
    for rt in REQUIRED_RECORD_TYPES:
        store.insert_record(
            episode_id=eid, record_type=rt, payload={"placeholder": "x"}
        )
    check = CompletionPrecheck(store=store)
    # Does not raise.
    check.run_or_raise(correction_scope_id="scope-cr8")


def test_CR7_precheck_noop_for_non_correction_scopes(store: CorrectionStore) -> None:
    # No episode for this scope → check is silent (returns None).
    check = CompletionPrecheck(store=store)
    check.run_or_raise(correction_scope_id="not-a-correction-scope")


async def test_CR7_request_complete_wraps_precheck(
    controller: SelfCorrectionController,
) -> None:
    tr = build_trigger_from_user_report(
        description="test",
        related_scope_id=None,
        reporter="eve",
    )
    result = await controller.intake(tr)
    assert result is not None

    # Attempt to complete without any records → precheck raises.
    async def mock_complete(scope_id: str) -> None:
        raise AssertionError(
            "complete_fn must NOT be called when precheck raises"
        )

    # Feed the correction_scope_id; precheck looks it up in the store.
    # Since the test fixture did not wire create_scope_fn, the episode
    # has None for correction_scope_id — the precheck short-circuits
    # (non-correction scope). So we also verify the structural path
    # by seeding a proper episode with a scope_id.
    eid = _seed_episode(controller.store, scope_id="scope-req-complete")
    with pytest.raises(ApplicationError) as excinfo:
        await controller.request_complete(
            correction_scope_id="scope-req-complete",
            complete_fn=mock_complete,
        )
    assert excinfo.value.code == IPC_CORRECTION_INCOMPLETE_RECORDS


async def test_CR8_request_complete_passes_with_all_records(
    controller: SelfCorrectionController,
) -> None:
    eid = _seed_episode(controller.store, scope_id="scope-req-ok")
    for rt in REQUIRED_RECORD_TYPES:
        controller.store.insert_record(
            episode_id=eid, record_type=rt, payload={"placeholder": "x"}
        )

    called: list[str] = []

    async def mock_complete(scope_id: str) -> None:
        called.append(scope_id)

    await controller.request_complete(
        correction_scope_id="scope-req-ok", complete_fn=mock_complete
    )
    assert called == ["scope-req-ok"]
    ep = controller.store.get_episode(eid)
    assert ep.state.value == "completed"
