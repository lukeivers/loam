# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.CDX.2 (WS-D2) — with ``codex`` uninstalled, a review whose CRITIC role is
``(claude, codex)`` completes on the Claude leg and NAMES the missing ``codex``
leg; never an unmarked clean bill.

The fail-soft is the REAL path: ``shutil.which`` returns ``None`` (codex not on
PATH), so ``run_codex_critic`` returns ``None`` and WS-D1's
``run_critic_registry`` records ``codex`` as a MISSING leg. The Claude leg is a
deterministic stub (the suite stays offline — no real spawn)."""
from __future__ import annotations

from conftest import finding_block, make_stub_critic, make_unavailable_critic

from adversarial_review import codex
from adversarial_review.manual import render_report, review_text
from adversarial_review.registry import ModelLeg, ModelRoleRegistry, Role

_ARTIFACT = (
    "# Pricing rationale\n\n"
    "The $49 tier is asserted CDX2_ANCHOR as the profit-maximizing price with "
    "no elasticity analysis and no competitor comparison in the document.\n"
    "Every other section is complete and internally consistent.\n"
)
_OBJECTIVE = "a defensible pricing rationale: the price is justified by analysis."


def _dual_leg_registry(claude_fn) -> ModelRoleRegistry:
    """CRITIC = (claude-stub, real codex leg)."""
    return ModelRoleRegistry(
        legs={
            Role.CRITIC: (
                ModelLeg("claude", claude_fn),
                codex.codex_leg(),
            )
        }
    )


def test_AC_CDX_2_codex_absent_review_completes_claude_only(monkeypatch):
    monkeypatch.setattr(codex.shutil, "which", lambda _bin: None)
    monkeypatch.delenv("PATH", raising=False)  # belt: nothing resolvable
    claude_finding = finding_block(
        'the price line "CDX2_ANCHOR"',
        "HIGH",
        'the $49 price "CDX2_ANCHOR" is asserted with no elasticity analysis.',
    )
    registry = _dual_leg_registry(make_stub_critic(claude_finding))

    result = review_text(_ARTIFACT, _OBJECTIVE, registry=registry)

    assert result.ran is True  # the claude leg carried the review
    assert result.missing_legs == ("codex",)
    assert "claude" in result.legs_used


def test_AC_CDX_2_render_names_the_missing_codex_leg(monkeypatch):
    monkeypatch.setattr(codex.shutil, "which", lambda _bin: None)
    claude_finding = finding_block(
        'the price line "CDX2_ANCHOR"',
        "HIGH",
        'the price "CDX2_ANCHOR" lacks any elasticity analysis.',
    )
    registry = _dual_leg_registry(make_stub_critic(claude_finding))

    result = review_text(_ARTIFACT, _OBJECTIVE, registry=registry)
    report = render_report(result, "pricing-rationale.md")

    # The missing leg is NAMED in the rendered output — not an unmarked clean bill.
    assert "codex" in report
    assert "MISSING" in report


def test_AC_CDX_2_all_legs_unavailable_is_inconclusive_not_clean(monkeypatch):
    # Both legs down: claude stub unavailable + codex absent -> REVIEW
    # INCONCLUSIVE (SUSPECT), never a false PASS.
    monkeypatch.setattr(codex.shutil, "which", lambda _bin: None)
    registry = _dual_leg_registry(make_unavailable_critic())

    result = review_text(_ARTIFACT, _OBJECTIVE, registry=registry)

    assert result.ran is False
    assert "codex" in result.missing_legs


def test_AC_CDX_2_run_codex_critic_returns_none_when_absent(monkeypatch):
    # The unit fail-soft: which->None => None, no spawn attempted.
    monkeypatch.setattr(codex.shutil, "which", lambda _bin: None)

    def _boom(*a, **k):  # subprocess must NOT be reached
        raise AssertionError("subprocess.run called though codex is absent")

    monkeypatch.setattr(codex.subprocess, "run", _boom)
    assert codex.run_codex_critic("any prompt") is None
