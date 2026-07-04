# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""Regression: the IN-SESSION injected-leg path produces a REAL review with
NO nested `claude -p` subprocess, and preserves two-phase artifact-blindness.

Why this test exists: the default critic leg is a nested `claude -p`
subprocess that HANGS when the tool is invoked from inside an interactive
Claude session (its most common invocation, via the /adversarial-review
skill), fail-softing to REVIEW INCONCLUSIVE with no actual review. The fix
routes the in-session path around the subprocess: the caller supplies each
critic phase from a FRESH Task subagent, replayed through the real
pipeline. This test proves that path yields a genuine, validated,
blocking review WITHOUT ever touching the subprocess — so it cannot
silently regress back to the hanging path.
"""
from __future__ import annotations

import pytest
from conftest import finding_block

import adversarial_review.critic as critic_mod
from adversarial_review import (
    emit_derive_prompt,
    emit_diff_prompt,
    render_report,
    replay_model_fn,
    run_insession_standard,
)
from adversarial_review.insession import ReplayExhausted
from adversarial_review.verdict import Disposition


@pytest.fixture(autouse=True)
def _forbid_nested_subprocess(monkeypatch):
    """Make the default nested-subprocess critic leg EXPLODE if reached.

    The in-session path must never fall through to the subprocess. If a
    future change breaks the injected-leg seam and the pipeline reaches
    the default leg, this raises instead of silently spawning (or hanging)
    a nested `claude -p`.
    """

    def _boom(*_a, **_k):  # noqa: ANN002, ANN003
        raise AssertionError(
            "the in-session path must NOT invoke run_isolated_critic "
            "(nested `claude -p`) — the model legs are caller-supplied"
        )

    monkeypatch.setattr(critic_mod, "run_isolated_critic", _boom)


def test_AR_insession_injected_leg_yields_real_blocking_review(
    nontrivial_artifact, objective
):
    # The two legs a FRESH derive subagent + a FRESH diff subagent produce.
    # The diff quotes REAL artifact text so it validates deterministically
    # (anchor present) and blocks — a genuine review, not INCONCLUSIVE.
    derived = (
        "SPEC: a defensible model sources every material assumption and "
        "stress-tests each against a downside scenario."
    )
    diff_raw = finding_block(
        location='SECTION 3: "the churn rate is assumed constant at 2%"',
        severity="HIGH",
        scenario='the assumption "the churn rate is assumed constant at 2%" '
        "is never stress-tested against the downside, so the model fails its "
        "objective of stress-testing every material assumption.",
    )

    result = run_insession_standard(
        nontrivial_artifact,
        objective,
        derived_spec=derived,
        diff_raw=diff_raw,
    )

    # A real review ran (NOT the fail-soft REVIEW-INCONCLUSIVE path).
    assert result.ran is True
    # The finding validated against ground truth and holds the boundary.
    assert result.verdict.disposition is Disposition.BLOCK
    assert any(f.blocks() for f in result.verdict.findings), (
        "the deterministically-validated finding should block"
    )
    # And it renders as an actual review with the substance in it.
    report = render_report(result, "revenue-model.md")
    assert "VERDICT: BLOCK" in report
    assert "churn rate" in report
    assert "REVIEW INCONCLUSIVE" not in report


def test_AR_insession_unavailable_leg_is_inconclusive_not_false_pass(
    nontrivial_artifact, objective
):
    # A genuinely-unavailable derive leg (None) must render INCONCLUSIVE,
    # never a clean bill — the fail-soft contract is preserved on the
    # injected path too.
    result = run_insession_standard(
        nontrivial_artifact,
        objective,
        derived_spec=None,  # type: ignore[arg-type]
        diff_raw="ignored",
    )
    assert result.ran is False
    assert result.verdict.disposition is Disposition.SUSPECT
    report = render_report(result, "x.md")
    assert "REVIEW INCONCLUSIVE" in report
    # The fallback names the in-session backend as the usable path.
    assert "insession" in report


def test_AR_insession_derive_prompt_is_artifact_blind(nontrivial_artifact, objective):
    # The distinctive artifact line the diff phase later quotes.
    anchor = "the churn rate is assumed constant at 2%"
    assert anchor in nontrivial_artifact  # sanity: it IS in the artifact

    derive_prompt = emit_derive_prompt(objective)
    # DERIVE is artifact-blind: the artifact text is absent (AC.AR.3).
    assert anchor not in derive_prompt
    assert nontrivial_artifact.strip() not in derive_prompt

    # The artifact only enters at the DIFF phase, AFTER the derivation.
    diff_prompt = emit_diff_prompt(
        nontrivial_artifact, objective, "SPEC: derived earlier."
    )
    assert anchor in diff_prompt
    assert "SPEC: derived earlier." in diff_prompt


def test_AR_replay_model_fn_returns_in_call_order_then_exhausts():
    leg = replay_model_fn(["first", "second"])
    assert leg("prompt-a") == "first"
    assert leg("prompt-b") == "second"
    with pytest.raises(ReplayExhausted):
        leg("prompt-c")
