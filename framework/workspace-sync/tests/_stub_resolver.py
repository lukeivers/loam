"""Test-side stub merge-resolver factory.

Loaded by `cli.main` via
``--merge-resolver-module workspace_sync.tests._stub_resolver`` (or
the bare path; the CLI's ``importlib.import_module`` accepts both).

The stub returns canned ``MergeVerdict`` instances per call. Tests
configure the stub's queue via ``set_canned_verdicts`` before
invoking the CLI; if the queue is empty, the stub returns a default
``inferred-merged`` verdict with deterministic content.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from workspace_sync.merge_resolver import (
    MergeResolver,
    MergeVerdict,
    ResolverBudget,
)


_QUEUE: deque[MergeVerdict] = deque()
_INVOCATIONS: list[dict[str, Any]] = []


def set_canned_verdicts(verdicts: list[MergeVerdict]) -> None:
    """Replace the canned-verdict queue (call from tests before
    invoking the CLI)."""
    _QUEUE.clear()
    _QUEUE.extend(verdicts)


def reset() -> None:
    """Reset both the queue and the invocation log."""
    _QUEUE.clear()
    _INVOCATIONS.clear()


def invocations() -> list[dict[str, Any]]:
    """Return the list of (path, canonical_text, workspace_text,
    prior_text) the resolver has been called with this test."""
    return list(_INVOCATIONS)


class _StubLLMClient:
    """Duck-typed ``LLMClient`` returning canned verdicts."""

    def invoke(
        self,
        prompt: str,
        response_model: type,
    ) -> tuple[Any, int]:
        # Pull next canned verdict; fall back to a default if empty.
        if _QUEUE:
            verdict = _QUEUE.popleft()
        else:
            verdict = MergeVerdict(
                resolution="inferred-merged",
                merged_content="<stub-default-merged-content>\n",
                rationale="stub default verdict",
                confidence=0.99,
            )
        return verdict, 100  # 100 tokens per call (arbitrary)


def build_merge_resolver(
    *, budget: ResolverBudget | None = None
) -> MergeResolver:
    """Factory shape per cli._load_merge_resolver expectations."""
    # Wrap _StubLLMClient with a custom MergeResolver subclass that
    # records the invocation arguments before delegating to the
    # canned-verdict logic. The recording is what makes the stub
    # useful for tests asserting "resolver was called with X".
    client = _StubLLMClient()
    resolver = _RecordingMergeResolver(
        client, budget or ResolverBudget()
    )
    return resolver


class _RecordingMergeResolver(MergeResolver):
    def resolve(
        self,
        *,
        path: str,
        canonical_text: str,
        workspace_text: str,
        prior_text: str | None = None,
    ) -> MergeVerdict:
        _INVOCATIONS.append(
            {
                "path": path,
                "canonical_text": canonical_text,
                "workspace_text": workspace_text,
                "prior_text": prior_text,
            }
        )
        return super().resolve(
            path=path,
            canonical_text=canonical_text,
            workspace_text=workspace_text,
            prior_text=prior_text,
        )
