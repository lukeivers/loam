"""CR4 — review-verdict IPC trigger (ruling #1)."""

from __future__ import annotations

from self_correction import (
    TriggerSource,
    build_trigger_from_review_verdict,
)


def test_CR4_fail_verdict_fires_trigger() -> None:
    tr = build_trigger_from_review_verdict(
        scope_id="scope-build-99",
        verdict="fail",
        reasons=["spec not satisfied", "missing test"],
        reporter="nora",
    )
    assert tr is not None
    assert tr.source == TriggerSource.review_verdict
    assert tr.reporter == "nora"
    assert tr.scope_id == "scope-build-99"
    assert tr.failure_class_hint == "review_verdict_fail"
    assert tr.raw_payload["verdict"] == "fail"
    assert tr.raw_payload["reasons"] == ["spec not satisfied", "missing test"]


def test_CR4_pass_verdict_does_not_fire() -> None:
    tr = build_trigger_from_review_verdict(
        scope_id="scope-99",
        verdict="pass",
        reasons=[],
        reporter="nora",
    )
    assert tr is None


def test_CR4_unknown_verdict_does_not_fire() -> None:
    tr = build_trigger_from_review_verdict(
        scope_id="scope-99",
        verdict="abstain",
        reasons=[],
        reporter="nora",
    )
    assert tr is None
