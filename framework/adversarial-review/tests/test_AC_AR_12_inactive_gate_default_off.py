# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.12 (INACTIVE) — with the activation switch OFF (default), the gate is a
no-op and never blocks a real boundary; the manual entry works regardless; when
explicitly activated the gate fires and blocks on a BLOCK verdict."""
from __future__ import annotations

from conftest import finding_block, make_stub_critic

from adversarial_review.activation import ACTIVATION_TOKEN, gate_active
from adversarial_review.gate import GateOutcome, gate_review
from adversarial_review.manual import review_text


def test_AC_AR_12_gate_default_off(monkeypatch, tmp_path):
    # Point the activation file at a nonexistent path -> inactive.
    monkeypatch.setenv(
        "ADVERSARIAL_REVIEW_ACTIVATION_FILE", str(tmp_path / "nope.activation")
    )
    assert gate_active() is False
    diff = finding_block('"boundary"', "CRITICAL", 'a "boundary" flaw.')
    decision = gate_review(
        "artifact crossing " * 40,
        "objective",
        "proposal.md",
        model_fn=make_stub_critic(diff),
    )
    # Inactive -> did NOT fire, did NOT block, regardless of a would-be BLOCK.
    assert decision.outcome is GateOutcome.NOT_FIRED_INACTIVE
    assert decision.blocked is False
    assert decision.review is None


def test_AC_AR_12_manual_works_while_gate_inactive(monkeypatch, tmp_path, nontrivial_artifact, objective):
    monkeypatch.setenv(
        "ADVERSARIAL_REVIEW_ACTIVATION_FILE", str(tmp_path / "nope.activation")
    )
    diff = finding_block('"churn rate"', "HIGH", 'the "churn rate" is untested.')
    # Manual path never consults activation — it always runs.
    result = review_text(nontrivial_artifact, objective, model_fn=make_stub_critic(diff))
    assert result.ran is True
    assert result.verdict.findings


def test_AC_AR_12_activated_gate_fires_and_blocks(monkeypatch, tmp_path):
    act = tmp_path / "on.activation"
    act.write_text(ACTIVATION_TOKEN, encoding="utf-8")
    monkeypatch.setenv("ADVERSARIAL_REVIEW_ACTIVATION_FILE", str(act))
    assert gate_active() is True
    diff = finding_block(
        '"a validated boundary flaw phrase"',
        "CRITICAL",
        'the "a validated boundary flaw phrase" breaks the objective.',
    )
    artifact = "This artifact contains a validated boundary flaw phrase in its body. " * 8
    decision = gate_review(
        artifact, "objective", "proposal.md", model_fn=make_stub_critic(diff)
    )
    assert decision.outcome is GateOutcome.BLOCK
    assert decision.blocked is True


def test_AC_AR_12_gate_does_not_fire_on_scratch(monkeypatch, tmp_path):
    act = tmp_path / "on.activation"
    act.write_text(ACTIVATION_TOKEN, encoding="utf-8")
    monkeypatch.setenv("ADVERSARIAL_REVIEW_ACTIVATION_FILE", str(act))
    diff = finding_block('"x"', "CRITICAL", 'a "x" flaw.')
    decision = gate_review(
        "artifact " * 40,
        "objective",
        "workspace/.scratch/draft-notes.md",
        model_fn=make_stub_critic(diff),
    )
    assert decision.outcome is GateOutcome.NOT_FIRED_NOT_A_BOUNDARY
    assert decision.blocked is False


def test_AC_AR_12_wrong_token_stays_inactive(monkeypatch, tmp_path):
    act = tmp_path / "wrong.activation"
    act.write_text("not the token", encoding="utf-8")
    monkeypatch.setenv("ADVERSARIAL_REVIEW_ACTIVATION_FILE", str(act))
    assert gate_active() is False
