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

"""Test-side stub merge-resolver factory.

Loaded by `cli.main` via
``--merge-resolver-module workspace_sync.tests._stub_resolver`` (or
the bare path; the CLI's ``importlib.import_module`` accepts both).

The stub returns canned ``MergeVerdict`` instances per call. Tests
configure the stub's queue via ``set_canned_verdicts`` before
invoking the CLI; if the queue is empty, the stub returns a default
``inferred-merged`` verdict with deterministic content.

A.2 (FUTURE_IDEAS_DRAFT Bundle A.2): ``MergeResolver.resolve()`` now
runs ``classify → deterministic-merge → verify → fallback``. For
existing CLI tests that pre-queue a ``MergeVerdict`` (expecting the
old single-call generator path), the stub auto-responds to the
classifier call with ``mergeable=False`` so the resolver routes
straight to the generator fallback — preserving the old behaviour
that the queued ``MergeVerdict`` becomes the final result. Tests
that want to exercise the A.2 deterministic path explicitly can
queue ``ClassifierVerdict`` / ``VerifierVerdict`` instances; the
stub returns the next-typed verdict that matches the requested
``response_model``.
"""

from __future__ import annotations

from collections import deque
from typing import Any

from pydantic import BaseModel

from loam.workspace_sync.merge_resolver import (
    ClassifierVerdict,
    MergeResolver,
    MergeVerdict,
    ResolverBudget,
    VerifierVerdict,
)


_QUEUE: deque[BaseModel] = deque()
_INVOCATIONS: list[dict[str, Any]] = []


def set_canned_verdicts(verdicts: list[BaseModel]) -> None:
    """Replace the canned-verdict queue (call from tests before
    invoking the CLI). Accepts any of MergeVerdict, ClassifierVerdict,
    or VerifierVerdict; the stub returns each entry when the
    resolver requests the matching response_model."""
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
    """Duck-typed ``LLMClient`` returning canned verdicts.

    A.2: returns a matching verdict for the requested
    ``response_model``. When the queue is empty and the resolver
    asks for a ``ClassifierVerdict``, returns ``mergeable=False``
    (route to generator fallback). When asked for a
    ``VerifierVerdict`` and queue is empty, returns ``verified=True``
    (accept the deterministic merge). When asked for a
    ``MergeVerdict`` and queue is empty, returns the legacy
    default ``inferred-merged`` verdict so existing tests that
    don't pre-queue specific values keep working.
    """

    def invoke(
        self,
        prompt: str,
        response_model: type,
    ) -> tuple[Any, int]:
        # Look for a queued verdict of the requested model type.
        matching_index: int | None = None
        for idx, item in enumerate(_QUEUE):
            if isinstance(item, response_model):
                matching_index = idx
                break
        if matching_index is not None:
            # Remove the matched item (preserve order of others).
            items = list(_QUEUE)
            verdict = items.pop(matching_index)
            _QUEUE.clear()
            _QUEUE.extend(items)
            return verdict, 100

        # No matching queued verdict — synthesize a default that
        # routes A.2 sensibly. mergeable=False on the classifier
        # path preserves the pre-A.2 behaviour: tests that queue
        # only MergeVerdicts route straight to the generator
        # fallback (where the queued MergeVerdict is consumed).
        if response_model is ClassifierVerdict:
            return (
                ClassifierVerdict(
                    mergeable=False,
                    strategy="none",
                    reason="stub default: route to fallback",
                ),
                10,
            )
        if response_model is VerifierVerdict:
            return (
                VerifierVerdict(verified=True, concerns=[]),
                20,
            )
        # MergeVerdict default — used when no test-queued verdict
        # is available for the generator path. Same content as
        # pre-A.2 so any existing test that didn't pre-queue keeps
        # the same default-verdict behaviour.
        return (
            MergeVerdict(
                resolution="inferred-merged",
                merged_content="<stub-default-merged-content>\n",
                rationale="stub default verdict",
                confidence=0.99,
            ),
            100,
        )


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
