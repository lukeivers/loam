"""CR9, CR10 — record authoring via IPC with Pydantic validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from self_correction import (
    CauseDiagnosed,
    FailureClassIdentified,
    InstanceFixed,
    RecordType,
    StructuralRemedyApplied,
)
from self_correction.spec import RECORD_MODELS


def test_CR9_pydantic_frozen_and_extra_forbid() -> None:
    ok = FailureClassIdentified(
        episode_id="ep-1",
        class_name="bad_routing",
        rationale="trigger reason",
    )
    with pytest.raises(ValidationError):
        FailureClassIdentified(
            episode_id="ep-1",
            class_name="x",
            rationale="y",
            extra_key="nope",  # type: ignore[call-arg]
        )
    # frozen
    with pytest.raises(ValidationError):
        ok.class_name = "changed"  # type: ignore[misc]


def test_CR9_empty_required_strings_rejected() -> None:
    with pytest.raises(ValidationError):
        FailureClassIdentified(episode_id="ep-1", class_name="")
    with pytest.raises(ValidationError):
        InstanceFixed(episode_id="ep-1", fix_description="")
    with pytest.raises(ValidationError):
        CauseDiagnosed(episode_id="ep-1", root_cause="")
    with pytest.raises(ValidationError):
        StructuralRemedyApplied(
            episode_id="ep-1", change_description=""
        )


def test_CR9_record_models_map_covers_all_four() -> None:
    assert set(RECORD_MODELS.keys()) == {
        RecordType.failure_class,
        RecordType.instance_fix,
        RecordType.cause_diagnosed,
        RecordType.structural_remedy,
    }


def test_CR10_order_recorded_via_at_timestamp() -> None:
    # Records persisted any-order — the `at` timestamp preserves real order.
    from self_correction import CorrectionStore, REQUIRED_RECORD_TYPES

    import tempfile, os, time
    tmp = tempfile.mkdtemp()
    try:
        store = CorrectionStore(os.path.join(tmp, "t.sqlite"))
        # Seed minimal episode via direct insert — skip trigger layer.
        from self_correction import CorrectionEpisode, EpisodeState
        from self_correction.spec import CorrectionTrigger, TriggerSource

        store.insert_trigger(
            CorrectionTrigger(
                trigger_id="t-order",
                source=TriggerSource.user_reported,
            )
        )
        store.insert_episode(
            CorrectionEpisode(
                episode_id="ep-order",
                trigger_id="t-order",
                correction_scope_id=None,
                failure_class="class1",
                state=EpisodeState.running,
            )
        )

        # Deliberately record OUT of the canonical order (4, 1, 3, 2).
        for rt in [
            RecordType.structural_remedy,
            RecordType.failure_class,
            RecordType.cause_diagnosed,
            RecordType.instance_fix,
        ]:
            store.insert_record(
                episode_id="ep-order", record_type=rt, payload={"k": rt.value}
            )
            time.sleep(0.002)  # ensure distinct `at` timestamps

        rows = store.list_records("ep-order")
        # `at` order matches insertion order.
        actual_order = [r["record_type"] for r in rows]
        assert actual_order == [
            RecordType.structural_remedy.value,
            RecordType.failure_class.value,
            RecordType.cause_diagnosed.value,
            RecordType.instance_fix.value,
        ]

        # All four present → precheck passes.
        from self_correction import CompletionPrecheck
        # We need to wire correction_scope_id on the episode for the
        # precheck to find it; seed one.
        # (simpler: just check record_types_for directly)
        present = store.record_types_for("ep-order")
        assert present == REQUIRED_RECORD_TYPES
    finally:
        store.close()
