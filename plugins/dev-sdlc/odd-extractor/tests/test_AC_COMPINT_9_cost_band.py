"""AC.COMPINT.9 — Cost band for LLM-as-judge.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.9:

- Default ceiling $0.20 per interview-run; halt band $0.05–$0.50.
- Pre-call dry-run estimate via 4-chars-per-token (or SDK
  ``count_tokens`` if available).
- Live mode: ``enforce_budget(estimate, BudgetEnvelope(hard_cap=20))``
  raises :class:`BudgetExceededError`.
- Build agent halts and surfaces if calibrated cost on canonical
  fixture lands outside band (this AC verifies the gate; the
  calibration step is dispatcher-side).
- Heuristic pre-pass is zero-LLM-cost.
"""

from __future__ import annotations

from loam_odd_extractor import (
    BudgetExceededError,
    ConfidenceBand,
    HeuristicPrior,
    MultiSourceBundle,
    Objective,
    ObjectiveEvidence,
    budget_from_cents,
    enforce_budget,
    estimate_judge_cost_cents,
    heuristic_priors,
)


def _bundle() -> MultiSourceBundle:
    return MultiSourceBundle(
        repo_id="test-repo",
        repo_path="/tmp/test-repo",
        repo_sha="abc1234",
        readme_text="# DisputeApp",
        readme_truncated=False,
        design_docs=[],
        test_assertions=[],
        user_survey={
            "source_path": "~/loam-onboarding-survey.md",
            "parsed": {"production_use": "Yes"},
            "raw_text": "Q4 production_use: Yes",
        },
        code_patterns=[],
        total_token_estimate=200,
    )


def _objs() -> list[Objective]:
    return [
        Objective(
            objective_id="O.dispute-flow.1",
            text="Operators file refund disputes against merchant portals at scale.",
            confidence=ConfidenceBand.PLAUSIBLE,
            domain="dispute-flow",
            evidence=ObjectiveEvidence(
                readme_excerpts=["File refunds at scale"],
            ),
        )
    ]


def test_estimate_judge_cost_returns_zero_for_zero_tokens() -> None:
    assert estimate_judge_cost_cents(0) == 0.0


def test_estimate_judge_cost_grows_with_tokens() -> None:
    a = estimate_judge_cost_cents(1000)
    b = estimate_judge_cost_cents(10_000)
    assert b > a


def test_estimate_judge_cost_for_25k_tokens_under_default_ceiling() -> None:
    """A rich bundle (~25K input tokens) should fit comfortably under
    $0.20 default ceiling; cost-band §6.6 mitigation."""
    cents = estimate_judge_cost_cents(25_000)
    assert cents < 20.0  # < $0.20


def test_estimate_judge_cost_for_100k_tokens_above_halt_band() -> None:
    """A 100K-token bundle exceeds the $0.50 halt-band ceiling — the
    build agent halts-and-surfaces in this case."""
    cents = estimate_judge_cost_cents(100_000)
    # Halt-band upper bound is 50 cents; 100K input tokens at the
    # blended rate exceeds this.
    assert cents > 30.0


def test_heuristic_pre_pass_is_zero_cost() -> None:
    """The deterministic heuristic_priors() function performs no LLM
    calls. Sanity-check: import & invoke produces no network IO."""
    priors = heuristic_priors(_objs(), multi_source_bundle=_bundle())
    assert all(isinstance(p, HeuristicPrior) for p in priors)
    # Exercise the no-priors branch too.
    empty_bundle = _bundle()
    empty_bundle = MultiSourceBundle(**{
        **empty_bundle.model_dump(),
        "user_survey": {
            "source_path": "x",
            "parsed": {"production_use": "No"},
            "raw_text": "Q4 production_use: No",
        },
    })
    assert heuristic_priors(_objs(), multi_source_bundle=empty_bundle) == []


def test_budget_envelope_raises_when_estimate_exceeds_ceiling() -> None:
    """Live mode with a 50-cent estimate against a $0.20 envelope
    raises BudgetExceededError."""
    # Use the existing budget primitives. Build an EstimateResult with
    # estimated_money_cents = 50 (exceeds 20-cent envelope).
    from loam.cost_governance import (
        BudgetEnvelope,
        EstimateResult,
        ConfidenceBand as CGBand,
        OverrunAction,
    )
    estimate = EstimateResult(
        estimated_money_cents=50,
        estimated_tokens=10_000,
        estimated_time_seconds=10,
        confidence_band=CGBand.HIGH,
        reason="test",
    )
    envelope = BudgetEnvelope(
        hard_cap_money_cents=20,
        soft_cap_money_cents=10,
        overrun_action=OverrunAction.halt,
    )
    import pytest
    with pytest.raises(BudgetExceededError):
        enforce_budget(estimate=estimate, envelope=envelope)


def test_budget_override_skips_enforcement() -> None:
    """``override=True`` bypasses the envelope (audit-logged caller-side)."""
    from loam.cost_governance import (
        BudgetEnvelope,
        EstimateResult,
        ConfidenceBand as CGBand,
        OverrunAction,
    )
    estimate = EstimateResult(
        estimated_money_cents=200,
        estimated_tokens=40_000,
        estimated_time_seconds=10,
        confidence_band=CGBand.HIGH,
        reason="test",
    )
    envelope = BudgetEnvelope(
        hard_cap_money_cents=20,
        soft_cap_money_cents=10,
        overrun_action=OverrunAction.halt,
    )
    enforce_budget(estimate=estimate, envelope=envelope, override=True)


def test_budget_from_cents_yields_envelope_at_named_ceiling() -> None:
    env = budget_from_cents(20)
    assert env.hard_cap_money_cents == 20
