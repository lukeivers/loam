# Copyright 2026 Luke Ivers and contributors
# SPDX-License-Identifier: Apache-2.0
"""AC.AR.13 (P10) — review output carries no stakeholder-reaction-prediction
framing; the critic/judge prompts carry the internal-lens clause; a lint flags
stakeholder-prediction text."""
from __future__ import annotations

from adversarial_review.critic import (
    INTERNAL_LENS_CLAUSE,
    derive_prompt,
    diff_prompt,
    has_stakeholder_prediction,
)
from adversarial_review.seed import ReviewInputs


def _inputs() -> ReviewInputs:
    return ReviewInputs("artifact", "objective", "methodology", "protocol")


def test_AC_AR_13_prompts_carry_internal_lens_clause():
    assert INTERNAL_LENS_CLAUSE in derive_prompt(_inputs())
    assert INTERNAL_LENS_CLAUSE in diff_prompt(_inputs(), "spec")


def test_AC_AR_13_lint_flags_stakeholder_prediction():
    assert has_stakeholder_prediction(
        "The investor will think this is weak and be put off."
    )
    assert has_stakeholder_prediction("how the client will receive the deck")
    assert has_stakeholder_prediction("the reader will feel confused here")


def test_AC_AR_13_lint_passes_survivability_language():
    # Internal-survivability framing is fine; only stakeholder-reaction
    # prediction is flagged.
    assert not has_stakeholder_prediction(
        "The artifact fails its objective: the load claim is unsourced."
    )
    assert not has_stakeholder_prediction(
        "This does not survive attack because section 3 contradicts section 1."
    )
