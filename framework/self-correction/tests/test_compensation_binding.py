"""CR13 — compensation-path binding registered at scope construction."""

from __future__ import annotations

from loam.self_correction import (
    CorrectionEpisode,
    EpisodeState,
    RecordType,
    SelfCorrectionController,
    build_trigger_from_user_report,
)
from loam.self_correction.spec import CorrectionTrigger, TriggerSource


async def test_CR13_register_called_before_activate(
    controller: SelfCorrectionController,
) -> None:
    order: list[str] = []

    async def create_scope(spec, scope_id):
        order.append("create")

    async def register_comp(params):
        order.append("register")
        assert params["handle"] == "self_correction.revert_structural_remedy"

    async def activate(params):
        order.append("activate")

    controller.create_scope_fn = create_scope
    controller.register_compensation_fn = register_comp
    controller.activate_fn = activate

    tr = build_trigger_from_user_report(
        description="binding order test",
        related_scope_id=None,
        reporter="eve",
    )
    await controller.intake(tr)
    assert order == ["create", "register", "activate"]


async def test_CR13_compensation_handler_returns_remedy_records(
    controller: SelfCorrectionController,
) -> None:
    # Seed an episode with a structural_remedy record.
    controller.store.insert_trigger(
        CorrectionTrigger(
            trigger_id="trig-cmp", source=TriggerSource.user_reported
        )
    )
    controller.store.insert_episode(
        CorrectionEpisode(
            episode_id="ep-cmp",
            trigger_id="trig-cmp",
            correction_scope_id="scope-cmp",
            failure_class="cmp",
            state=EpisodeState.running,
        )
    )
    controller.store.insert_record(
        episode_id="ep-cmp",
        record_type=RecordType.structural_remedy,
        payload={
            "episode_id": "ep-cmp",
            "change_description": "Added validator for gate-refusal prefix",
            "artefact_path": "/path/to/file.py",
            "at": "2026-04-20T12:00:00+00:00",
        },
    )

    result = await controller.compensation_handler(scope_id="scope-cmp")
    assert result["ok"] is True
    assert result["episode_id"] == "ep-cmp"
    assert len(result["remedy_records"]) == 1
    assert result["remedy_records"][0]["record_type"] == "structural_remedy"
