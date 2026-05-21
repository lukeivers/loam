# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.WS.4, AC.WS.6, AC.WS.12 — MergeResolver tests (lifted shape).

A.2 update: ``.resolve()`` now runs classifier-first; tests that
exercise the generator path queue a ``mergeable=False`` classifier
verdict ahead of the generator verdict to route through the
fallback. The contracts asserted (budget tracking, type
translation, prompt content) are unchanged.
"""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from loam.workspace_sync.merge_resolver import (
    BudgetExhausted,
    ClassifierVerdict,
    MergeResolver,
    MergeVerdict,
    ResolverBudget,
    ResolverFailure,
    build_prompt,
)


class StubLLMClient:
    """Test double returning canned verdicts (any Pydantic model)."""

    def __init__(self, queued: list[tuple[BaseModel, int]]) -> None:
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


def _classifier_no() -> ClassifierVerdict:
    """Classifier verdict that routes straight to the generator path."""
    return ClassifierVerdict(
        mergeable=False,
        strategy="none",
        reason="test: route to generator fallback",
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
    # Classifier-no (50 tokens) → generator returns accept-canonical
    # (150 tokens). Total 200 tokens billed; one call counted (the
    # MergeVerdict-producing call; classifier alone doesn't count).
    stub = StubLLMClient(
        [(_classifier_no(), 50), (_verdict(), 150)]
    )
    resolver = MergeResolver(
        stub, ResolverBudget(per_conflict_token_budget=5_000)
    )
    verdict = resolver.resolve(
        path="x.py", canonical_text="a", workspace_text="b"
    )
    assert verdict.resolution == "inferred-accept-canonical"
    assert resolver.cumulative_used == 200
    assert resolver.call_count == 1


def test_cumulative_budget_exhaustion() -> None:
    # Each resolve = classifier-no (1 token) + generator (50_000).
    # After two resolves, cumulative used = 100_002 > ceiling.
    stub = StubLLMClient(
        [
            (_classifier_no(), 1),
            (_verdict(), 50_000),
            (_classifier_no(), 1),
            (_verdict(), 50_000),
            (_classifier_no(), 1),
            (_verdict(), 50_000),
        ]
    )
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
    # An exploding classifier call no longer fails the resolve —
    # A.2 catches classifier failures and falls back to the
    # generator path. So we exhaust both calls here to surface
    # the failure end-to-end.
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
