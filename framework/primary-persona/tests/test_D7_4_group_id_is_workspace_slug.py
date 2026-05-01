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

"""AC-D7.4 — ``group_id == workspace slug`` for both read and write.

Outcome (from amendment #33 plan §4 AC-D7.4): every memory-system
retrieval issued by the primary-persona layer and every memory-system
episode written by the layer carries the workspace slug in its
``group_ids`` / ``group_id`` argument.

Includes the parity test against the canonical
``workspace_bootstrap.adapters.first_run_scaffold.workspace_slug``
per the governing plan §3 constraint 2 (test-fixture admission for
cross-component imports). The parity test mirrors the precedent set
by ``hands-off-lifecycle/tests/test_first_run.py::
test_AC7_workspace_slug_parity_with_workspace_bootstrap``.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from loam.primary_persona.context_composer import ComposedContextPayload
from loam.primary_persona.memory_consumer import (
    TurnAggregator,
    WorkspaceSlugUnrepresentableError,
    register_memory_retrieval,
    resolve_workspace_slug,
)
from loam.primary_persona.session_start_gate import compose_session_fields

from _helpers_d7 import FakeMemoryClient, seed_baseline_workspace


@pytest.mark.asyncio
async def test_D7_4_read_and_write_both_carry_slug(tmp_path: Path) -> None:
    """Drive both the retrieval path and the write path; inspect
    every recorded call; assert each carries the slug."""
    workspace_root = tmp_path / "Demo.Workspace.V2"  # mixed case + dots
    seed_baseline_workspace(workspace_root)
    slug = resolve_workspace_slug(workspace_root)
    assert slug == "demo-workspace-v2"

    client = FakeMemoryClient(
        search_result={
            "query": "x",
            "results": [{"fact": "some recorded fact"}],
        }
    )
    composer = ComposedContextPayload(session_builder=compose_session_fields)
    register_memory_retrieval(
        composer, memory_client=client, workspace_slug=slug
    )
    composer.on_session_start(workspace_root)

    # Read path: UserPromptSubmit.
    composer.on_user_prompt_submit(prompt="any question")

    # Write path: turn-close aggregation.
    agg = TurnAggregator(memory_client=client, workspace_slug=slug)
    await agg.close_turn(
        turn_id="t1",
        user_message="u",
        persona_reply="p",
    )

    # Every search call carries the slug as the ONLY entry in
    # group_ids.
    assert client.search_calls, "search was not called"
    for call in client.search_calls:
        assert call.group_ids == [slug]

    # Every add_episode call carries the slug as its group_id.
    assert client.add_episode_calls, "add_episode was not called"
    for call in client.add_episode_calls:
        assert call.group_id == slug


def test_D7_4_slug_parity_with_canonical_workspace_bootstrap(
    tmp_path: Path,
) -> None:
    """Parity between ``memory_consumer.resolve_workspace_slug`` and
    the canonical ``workspace_bootstrap.adapters.first_run_scaffold.
    workspace_slug`` across a fixture set. If sanitisation semantics
    change in one primitive, they MUST change in the other — the
    precedent set by hands-off-lifecycle's parity test.

    If the canonical import is unavailable in the test environment
    (e.g., workspace-bootstrap not installed in this venv), the test
    skips with a diagnostic rather than silently passing.
    """
    try:
        from loam.workspace_bootstrap.adapters.first_run_scaffold import (  # type: ignore[import-not-found]
            workspace_slug as canonical_workspace_slug,
        )
    except ImportError:
        pytest.skip(
            "workspace_bootstrap not installed in this venv — parity "
            "check requires the canonical import"
        )

    fixtures = [
        "simple",
        "Mixed.Case",
        "with_under_scores",
        "UPPER-CASE-ONLY",
        "a---b",  # collapse runs
        "99-numbers-only",
    ]
    for name in fixtures:
        root = tmp_path / name
        local = resolve_workspace_slug(root)
        canon = canonical_workspace_slug(root)
        assert local == canon, (
            f"slug parity drift for basename {name!r}: "
            f"local={local!r}, canonical={canon!r}"
        )


def test_D7_4_slug_refuses_unrepresentable_basename(tmp_path: Path) -> None:
    """Basenames with zero surviving characters after sanitisation
    raise — matches the canonical's structural refusal."""
    root = tmp_path / "!!!"
    with pytest.raises(WorkspaceSlugUnrepresentableError):
        resolve_workspace_slug(root)
