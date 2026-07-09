# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.MRR.3 (outcome-altitude) — a configured-but-unavailable leg is named;
the review proceeds on the remaining legs, never an unmarked clean bill.

With the CRITIC role configured to two legs — one available (produces a
finding), one unavailable (its model returns None, the Codex-absent shape) —
the review proceeds on the available leg, tags every finding with its leg, and
NAMES the missing leg. If EVERY configured leg is unavailable the verdict is
SUSPECT / REVIEW INCONCLUSIVE (the existing floor) and the missing legs are
still named. Also asserts the registry resolves all three named roles.
"""
from __future__ import annotations

from conftest import finding_block, make_stub_critic

from adversarial_review import (
    DEFAULT_LEG_NAME,
    DEFAULT_REGISTRY,
    Disposition,
    ModelLeg,
    ModelRoleRegistry,
    Role,
    render_report,
    review_text,
)


def _unavailable(_prompt: str):
    return None


def test_AC_MRR_3_proceeds_and_names_missing_leg(nontrivial_artifact, objective):
    diff = finding_block(
        location='SECTION 3: "the churn rate is assumed constant at 2%"',
        severity="HIGH",
        scenario='the churn rate "the churn rate is assumed constant at 2%" '
        "is never stress-tested, so the model fails its objective.",
    )
    registry = ModelRoleRegistry(
        legs={
            Role.CRITIC: (
                ModelLeg("claude", make_stub_critic(diff)),  # available
                ModelLeg("codex", _unavailable),  # configured but unavailable
            )
        }
    )
    result = review_text(nontrivial_artifact, objective, registry=registry)

    # The review PROCEEDED on the available leg (not INCONCLUSIVE).
    assert result.ran is True
    assert result.verdict.findings
    for f in result.verdict.findings:
        assert f.leg == "claude"
    assert result.legs_used == ("claude",)
    # The missing leg is named — never silently dropped.
    assert result.missing_legs == ("codex",)
    report = render_report(result, "revenue-model.md")
    assert "codex" in report
    assert "MISSING" in report  # named as a configured-but-absent leg


def test_AC_MRR_3_missing_leg_named_even_on_a_PASS(nontrivial_artifact, objective):
    # The AC's literal target — "never an unmarked CLEAN BILL" — is the PASS
    # disposition. A MEDIUM validated finding is substantive but non-blocking
    # -> PASS; the missing leg must STILL be named (not just on a BLOCK). This
    # pins the render's disposition-independence against a future regression
    # that gated the model-legs block on `blocking`.
    diff = finding_block(
        location='SECTION 3: "the churn rate is assumed constant at 2%"',
        severity="MEDIUM",
        scenario='the churn rate "the churn rate is assumed constant at 2%" '
        "carries no downside stress test — a material-but-non-blocking gap.",
    )
    registry = ModelRoleRegistry(
        legs={
            Role.CRITIC: (
                ModelLeg("claude", make_stub_critic(diff)),  # available, MEDIUM
                ModelLeg("codex", _unavailable),  # configured but unavailable
            )
        }
    )
    result = review_text(nontrivial_artifact, objective, registry=registry)

    # A non-BLOCK verdict (the clean-bill shape the AC guards) that STILL runs.
    assert result.ran is True
    assert result.verdict.disposition is Disposition.PASS
    assert result.missing_legs == ("codex",)
    report = render_report(result, "revenue-model.md")
    assert "codex" in report
    assert "MISSING" in report  # a PASS is never an UNMARKED clean bill


def test_AC_MRR_3_all_legs_unavailable_is_inconclusive_not_clean(
    nontrivial_artifact, objective
):
    registry = ModelRoleRegistry(
        legs={
            Role.CRITIC: (
                ModelLeg("claude", _unavailable),
                ModelLeg("codex", _unavailable),
            )
        }
    )
    result = review_text(nontrivial_artifact, objective, registry=registry)
    # Every configured leg down -> REVIEW INCONCLUSIVE, never a clean bill.
    assert result.ran is False
    assert set(result.missing_legs) == {"claude", "codex"}
    report = render_report(result, "revenue-model.md")
    assert "REVIEW INCONCLUSIVE" in report
    # A non-default missing leg is present, so the missing legs are named.
    assert "codex" in report


def test_AC_MRR_3_registry_resolves_all_three_named_roles():
    # The objective's role vocabulary: writer / critic / judge all resolve to
    # a leg (the default registry maps each to the default Claude leg).
    for role in (Role.WRITER, Role.CRITIC, Role.JUDGE):
        legs = DEFAULT_REGISTRY.legs_for(role)
        assert legs, f"{role} resolved to no leg"
        assert DEFAULT_REGISTRY.resolve(role).name == DEFAULT_LEG_NAME
    # An empty registry still resolves every role to the default leg.
    empty = ModelRoleRegistry()
    assert empty.resolve(Role.CRITIC).name == DEFAULT_LEG_NAME
    assert empty.resolve(Role.JUDGE).fn is None
