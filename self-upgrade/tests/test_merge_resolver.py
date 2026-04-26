"""Clause-(h) AC.H.4/6/12 — MergeResolver tests."""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import BaseModel

from self_upgrade.merge_resolver import (
    BudgetExhausted,
    LLMClient,
    MergeResolver,
    MergeVerdict,
    ResolverBudget,
    ResolverFailure,
    build_prompt,
)


class StubLLMClient:
    """Test double that returns canned MergeVerdicts.

    Each call consumes the next entry from ``self.queued``; ``tokens``
    is the second element of each tuple. Out of entries → ResolverFailure.
    """

    def __init__(self, queued: list[tuple[MergeVerdict, int]]) -> None:
        self.queued = list(queued)
        self.calls: list[tuple[str, type[BaseModel]]] = []

    def invoke(
        self, prompt: str, response_model: type[BaseModel]
    ) -> tuple[BaseModel, int]:
        self.calls.append((prompt, response_model))
        if not self.queued:
            raise ResolverFailure("stub: out of canned verdicts")
        verdict, tokens = self.queued.pop(0)
        return verdict, tokens


def _verdict(
    resolution: str = "inferred-accept-canonical",
    *,
    rationale: str = "test rationale",
    confidence: float = 0.9,
    merged_content: str | None = None,
) -> MergeVerdict:
    return MergeVerdict(
        resolution=resolution,  # type: ignore[arg-type]
        merged_content=merged_content,
        rationale=rationale,
        confidence=confidence,
    )


def test_verdict_validates_confidence_range() -> None:
    with pytest.raises(ValueError):
        MergeVerdict(
            resolution="inferred-accept-canonical",
            rationale="x",
            confidence=1.5,
        )


def test_verdict_merged_requires_content() -> None:
    """AC.H.4: inferred-merged demands non-empty merged_content."""
    with pytest.raises(ValueError, match="merged_content"):
        MergeVerdict(
            resolution="inferred-merged",
            rationale="synth",
            confidence=0.8,
        )


def test_verdict_rationale_nonempty() -> None:
    with pytest.raises(ValueError, match="rationale"):
        MergeVerdict(
            resolution="inferred-accept-canonical",
            rationale="",
            confidence=0.9,
        )


def test_resolver_basic_call() -> None:
    """AC.H.4: resolver returns a structured verdict."""
    stub = StubLLMClient([(_verdict(), 200)])
    resolver = MergeResolver(stub)
    verdict = resolver.resolve(
        path="a.py",
        canonical_text="canonical",
        workspace_text="workspace",
    )
    assert verdict.resolution == "inferred-accept-canonical"
    assert resolver.cumulative_used == 200
    assert resolver.call_count == 1


def test_resolver_per_conflict_budget_default() -> None:
    """AC.H.6: per-conflict budget defaults to 5000."""
    budget = ResolverBudget()
    assert budget.per_conflict_token_budget == 5_000
    assert budget.cumulative_token_budget == 100_000


def test_resolver_cumulative_tracks() -> None:
    """AC.H.6: cumulative budget tracked across calls."""
    stub = StubLLMClient(
        [(_verdict(), 1000), (_verdict(), 500), (_verdict(), 800)]
    )
    resolver = MergeResolver(stub)
    for path in ("a.py", "b.py", "c.py"):
        resolver.resolve(
            path=path, canonical_text="x", workspace_text="y"
        )
    assert resolver.cumulative_used == 2300
    assert resolver.call_count == 3


def test_resolver_budget_exhausted_pre_flight() -> None:
    """AC.H.6: cumulative ceiling halts before next call."""
    stub = StubLLMClient([(_verdict(), 50_000)] * 3)
    # Cumulative ceiling small enough that one call lands; second halts.
    resolver = MergeResolver(
        stub,
        ResolverBudget(
            per_conflict_token_budget=50_000,
            cumulative_token_budget=60_000,
        ),
    )
    resolver.resolve(path="a.py", canonical_text="x", workspace_text="y")
    # 50k used; another 50k would exceed 60k ceiling.
    with pytest.raises(BudgetExhausted) as exc_info:
        resolver.resolve(path="b.py", canonical_text="x", workspace_text="y")
    assert exc_info.value.used == 50_000
    assert exc_info.value.ceiling == 60_000


def test_resolver_budget_exhausted_at_ceiling() -> None:
    """Cumulative-already-at-ceiling halts immediately."""
    stub = StubLLMClient([(_verdict(), 1)])
    resolver = MergeResolver(
        stub,
        ResolverBudget(
            per_conflict_token_budget=1, cumulative_token_budget=1
        ),
    )
    resolver.resolve(path="a.py", canonical_text="x", workspace_text="y")
    with pytest.raises(BudgetExhausted):
        resolver.resolve(path="b.py", canonical_text="x", workspace_text="y")


def test_resolver_failure_translates_unknown_exceptions() -> None:
    """AC.H.12: any exception from the LLM client → ResolverFailure."""

    class BoomClient:
        def invoke(
            self, prompt: str, response_model: type[BaseModel]
        ) -> tuple[BaseModel, int]:
            raise RuntimeError("network boom")

    resolver = MergeResolver(BoomClient())
    with pytest.raises(ResolverFailure, match="network boom"):
        resolver.resolve(path="a.py", canonical_text="x", workspace_text="y")


def test_resolver_failure_passes_through() -> None:
    """ResolverFailure raised by the client surfaces unchanged."""

    class FailClient:
        def invoke(
            self, prompt: str, response_model: type[BaseModel]
        ) -> tuple[BaseModel, int]:
            raise ResolverFailure("schema reject")

    resolver = MergeResolver(FailClient())
    with pytest.raises(ResolverFailure, match="schema reject"):
        resolver.resolve(path="a.py", canonical_text="x", workspace_text="y")


def test_build_prompt_carries_path_and_both_sides() -> None:
    prompt = build_prompt(
        path="self-upgrade/x.py",
        canonical_text="CANON",
        workspace_text="WORK",
        prior_text="PRIOR",
    )
    assert "self-upgrade/x.py" in prompt
    assert "CANON" in prompt
    assert "WORK" in prompt
    assert "PRIOR" in prompt
    assert "MergeVerdict" in prompt


def test_build_prompt_omits_prior_when_none() -> None:
    prompt = build_prompt(
        path="x.py",
        canonical_text="A",
        workspace_text="B",
        prior_text=None,
    )
    assert "Prior-release" not in prompt


def test_resolver_wrong_response_type_translates_to_failure() -> None:
    """If the client returns the wrong Pydantic class, ResolverFailure."""

    class WrongModel(BaseModel):
        x: int

    class WrongClient:
        def invoke(
            self, prompt: str, response_model: type[BaseModel]
        ) -> tuple[BaseModel, int]:
            return WrongModel(x=1), 100

    resolver = MergeResolver(WrongClient())
    with pytest.raises(ResolverFailure, match="wrong type"):
        resolver.resolve(path="a.py", canonical_text="x", workspace_text="y")
