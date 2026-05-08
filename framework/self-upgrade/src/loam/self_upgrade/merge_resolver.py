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

"""Clause-(h) LLM-mediated merge resolver.

Per-conflict resolver that asks the LLM to decide between accepting
canonical content, preserving workspace content, or producing a
synthesised three-way merge. The verdict is structured (Pydantic-typed)
and carries a free-text rationale + a 0.0–1.0 confidence score that the
audit log surfaces low-confidence-first for human review.

Budgeting (BB D-1 locks):
  - per_conflict_token_budget: 5_000  (workspace-tunable via
    ~/.loam/upgrade-config.yaml)
  - cumulative_token_budget:  100_000  (workspace-tunable)

Failure modes:
  - ``BudgetExhausted`` — cumulative ceiling hit; halt-and-resume.
  - ``ResolverFailure`` — LLM call failed (network, schema-reject,
    timeout). Fail-closed; clause-(h) returns failed → rollback.

The resolver is duck-typed against any object exposing
``invoke(prompt: str, response_model: type[BaseModel]) -> tuple[BaseModel, int]``
where the int is the token cost of the call. A ``StubLLMClient`` for
tests appears in ``self-upgrade/tests/conftest.py``. The production
adapter wraps ``ClaudePrintLLMClient`` (memory-system) — wired in
``cli.py`` at ``cmd_upgrade`` time.
"""

from __future__ import annotations

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, model_validator


class MergeVerdict(BaseModel):
    """Structured response from the LLM merge resolver."""

    model_config = ConfigDict(extra="forbid")

    resolution: Literal[
        "inferred-accept-canonical",
        "inferred-accept-workspace",
        "inferred-merged",
    ]
    merged_content: str | None = None
    rationale: str
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _merged_requires_content(self) -> "MergeVerdict":
        if self.resolution == "inferred-merged":
            if self.merged_content is None or self.merged_content == "":
                raise ValueError(
                    "resolution=inferred-merged requires non-empty "
                    "merged_content"
                )
        if self.rationale.strip() == "":
            raise ValueError("rationale must be non-empty")
        return self


class ResolverBudget(BaseModel):
    """Per-conflict and cumulative token budgets (BB D-1 defaults)."""

    model_config = ConfigDict(extra="forbid")

    per_conflict_token_budget: int = Field(default=5_000, gt=0)
    cumulative_token_budget: int = Field(default=100_000, gt=0)


class BudgetExhausted(Exception):
    """Raised when a resolver call would exceed the cumulative ceiling."""

    def __init__(self, message: str, *, used: int, ceiling: int) -> None:
        super().__init__(message)
        self.used = used
        self.ceiling = ceiling


class ResolverFailure(Exception):
    """Raised on LLM call failure (network, schema-reject, timeout).

    Fail-closed: clause-(h) treats this as a verifier failure and
    triggers the existing rollback path. The framework MUST NOT
    silently treat a resolver failure as accept-canonical or
    accept-workspace.
    """


class LLMClient(Protocol):
    """Duck-typed surface the resolver expects.

    ``invoke(prompt, response_model)`` runs the LLM call and parses the
    result against ``response_model`` (Pydantic). Returns a tuple of the
    parsed model + the token cost of the call. Implementations raise
    ``ResolverFailure`` for any failure mode that should fail-close
    clause-(h).
    """

    def invoke(
        self,
        prompt: str,
        response_model: type[BaseModel],
    ) -> tuple[BaseModel, int]:
        ...


def build_prompt(
    *,
    path: str,
    canonical_text: str,
    workspace_text: str,
    prior_text: str | None,
) -> str:
    """Build the resolver prompt for a single conflict.

    The prompt instructs the LLM to choose between accept-canonical,
    accept-workspace, or merged; to provide a rationale; and to score
    confidence. The response shape is ``MergeVerdict``.
    """
    parts = [
        "You are resolving a three-way merge conflict in a pOS v2 workspace.",
        "",
        f"File path: {path}",
        "",
        "## Canonical (release) content:",
        "```",
        canonical_text,
        "```",
        "",
        "## Workspace (operator-edited) content:",
        "```",
        workspace_text,
        "```",
    ]
    if prior_text is not None:
        parts.extend([
            "",
            "## Prior-release content (the common ancestor):",
            "```",
            prior_text,
            "```",
        ])
    parts.extend([
        "",
        "Choose ONE of three resolutions:",
        "  - inferred-accept-canonical: take canonical; workspace edit was redundant or superseded.",
        "  - inferred-accept-workspace: keep workspace; canonical's change does not apply here.",
        "  - inferred-merged: synthesise a merge that preserves both intents (provide merged_content).",
        "",
        "Return a MergeVerdict JSON with: resolution, merged_content (string or null), rationale, confidence (0.0-1.0).",
        "Confidence reflects how certain you are the resolution preserves both sides' intent.",
    ])
    return "\n".join(parts)


class MergeResolver:
    """Per-conflict resolver with cumulative budget tracking."""

    def __init__(
        self,
        llm_client: LLMClient,
        budget: ResolverBudget | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.budget = budget or ResolverBudget()
        self._cumulative_used: int = 0
        self._call_count: int = 0

    @property
    def cumulative_used(self) -> int:
        return self._cumulative_used

    @property
    def call_count(self) -> int:
        return self._call_count

    def resolve(
        self,
        *,
        path: str,
        canonical_text: str,
        workspace_text: str,
        prior_text: str | None = None,
    ) -> MergeVerdict:
        """Invoke the LLM resolver for one conflict.

        Raises:
            BudgetExhausted: cumulative ceiling already met or would be
                exceeded by this call's per-conflict budget.
            ResolverFailure: LLM call failed (network, schema-reject,
                timeout).
        """
        # Pre-flight: cumulative budget gate. If we cannot fund a full
        # per-conflict call without exceeding the ceiling, halt.
        projected = self._cumulative_used + self.budget.per_conflict_token_budget
        if self._cumulative_used >= self.budget.cumulative_token_budget:
            raise BudgetExhausted(
                f"cumulative ceiling reached: {self._cumulative_used} >= "
                f"{self.budget.cumulative_token_budget}",
                used=self._cumulative_used,
                ceiling=self.budget.cumulative_token_budget,
            )
        if projected > self.budget.cumulative_token_budget:
            raise BudgetExhausted(
                f"cumulative ceiling would be exceeded: {self._cumulative_used} + "
                f"{self.budget.per_conflict_token_budget} > "
                f"{self.budget.cumulative_token_budget}",
                used=self._cumulative_used,
                ceiling=self.budget.cumulative_token_budget,
            )

        prompt = build_prompt(
            path=path,
            canonical_text=canonical_text,
            workspace_text=workspace_text,
            prior_text=prior_text,
        )
        try:
            verdict, tokens = self.llm_client.invoke(prompt, MergeVerdict)
        except ResolverFailure:
            raise
        except Exception as exc:  # noqa: BLE001 — translate to ResolverFailure
            raise ResolverFailure(
                f"resolver call failed for {path}: {type(exc).__name__}: {exc}"
            ) from exc

        if not isinstance(verdict, MergeVerdict):
            raise ResolverFailure(
                f"resolver returned wrong type for {path}: "
                f"{type(verdict).__name__}"
            )

        self._cumulative_used += int(tokens)
        self._call_count += 1
        return verdict
