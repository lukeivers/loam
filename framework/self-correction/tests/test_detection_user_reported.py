"""CR5 — user-reported IPC trigger with primary-persona caller identity (ruling #4)."""

from __future__ import annotations

import pytest
from pos_orchestrator.ipc import ApplicationError

from self_correction import (
    SelfCorrectionController,
    TriggerSource,
    build_trigger_from_user_report,
)


def test_CR5_build_trigger_shape() -> None:
    tr = build_trigger_from_user_report(
        description="Eve's escalation routing missed my Tier 1 note",
        related_scope_id="scope-abc",
        reporter="eve",
    )
    assert tr.source == TriggerSource.user_reported
    assert tr.scope_id == "scope-abc"
    assert tr.reporter == "eve"
    assert tr.failure_class_hint == "user_reported"


def test_CR5_caller_authorization_accepts_primary_persona(
    controller: SelfCorrectionController,
) -> None:
    # Does not raise.
    controller.authorize_user_report_caller("eve")
    controller.authorize_user_report_caller("primary-persona")


def test_CR5_caller_authorization_refuses_non_primary(
    controller: SelfCorrectionController,
) -> None:
    with pytest.raises(ApplicationError) as excinfo:
        controller.authorize_user_report_caller("some-specialist")
    assert excinfo.value.code == -32602
    assert "primary persona" in str(excinfo.value).lower()


def test_CR5_empty_allowlist_is_fail_closed(tmp_path) -> None:
    from self_correction import CorrectionConfig, CorrectionStore
    controller = SelfCorrectionController(
        store=CorrectionStore(tmp_path / "fail_closed.sqlite"),
        config=CorrectionConfig(),
        allowed_user_report_callers=frozenset(),  # empty
    )
    with pytest.raises(ApplicationError):
        controller.authorize_user_report_caller("eve")
