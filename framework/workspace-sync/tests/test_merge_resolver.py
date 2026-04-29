"""AC.WS.4, AC.WS.6, AC.WS.12 — MergeResolver tests (lifted shape)."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from loam.workspace_sync.merge_resolver import (
    BudgetExhausted,
    MergeResolver,
    MergeVerdict,
    ResolverBudget,
    ResolverFailure,
    build_prompt,
)


class StubLLMClient:
    """Test double returning canned MergeVerdicts."""

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
    with pytest.raises(ValueError):
        MergeVerdict(
            resolution="inferred-merged",
            rationale="x",
            confidence=0.5,
        )


def test_resolve_per_conflict_budget_smoke() -> None:
    stub = StubLLMClient([(_verdict(), 200)])
    resolver = MergeResolver(stub, ResolverBudget(per_conflict_token_budget=5_000))
    verdict = resolver.resolve(
        path="x.py", canonical_text="a", workspace_text="b"
    )
    assert verdict.resolution == "inferred-accept-canonical"
    assert resolver.cumulative_used == 200
    assert resolver.call_count == 1


def test_cumulative_budget_exhaustion() -> None:
    stub = StubLLMClient([(_verdict(), 50_000)] * 3)
    resolver = MergeResolver(
        stub,
        ResolverBudget(
            per_conflict_token_budget=5_000,
            cumulative_token_budget=100_000,
        ),
    )
    resolver.resolve(path="a.py", canonical_text="a", workspace_text="b")
    resolver.resolve(path="b.py", canonical_text="a", workspace_text="b")
    with pytest.raises(BudgetExhausted):
        resolver.resolve(path="c.py", canonical_text="a", workspace_text="b")


def test_resolver_failure_translation() -> None:
    class ExplodingClient:
        def invoke(self, prompt: str, response_model: type[BaseModel]):
            raise RuntimeError("kaboom")

    resolver = MergeResolver(ExplodingClient())
    with pytest.raises(ResolverFailure):
        resolver.resolve(path="x.py", canonical_text="a", workspace_text="b")


def test_build_prompt_includes_path_and_both_sides() -> None:
    p = build_prompt(
        path="hello.py",
        canonical_text="canonical_body",
        workspace_text="workspace_body",
        prior_text=None,
    )
    assert "hello.py" in p
    assert "canonical_body" in p
    assert "workspace_body" in p
    assert "MergeVerdict" in p
