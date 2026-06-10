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

"""AC.SACH.3 — the bundle carries a workstream-context tier reflecting
the current workstream, AND a memory tier reflecting workspace-scoped
relevant memory.

Both tiers are asserted PRESENT. The workstream tier names the current
workstream (resolver STUBBED to current-workstream for 1a — D-SACH.3;
project-keying is the deferred P-layer). The memory tier carries >=0
retrieved entries from the workspace-scoped store, present as a tier
even when empty (RF-2: tier-presence + current-workstream reflection,
NOT project discrimination).
"""

from __future__ import annotations

from pathlib import Path

from conftest import make_envelope

from loam.frame_kernel.bundle import compose_bundle


def test_workstream_tier_present_and_reflects_current_workstream(
    real_kernel_workspace: Path,
) -> None:
    """With a known active workstream on disk, the bundle's workstream
    tier names it (D-SACH.3 stub: reads the work-streams STATE pointer)."""
    # Post-D.2 workspace-state layout: the pointer lives under
    # ``<workspace>/workspace/.pos/`` (the resolver routes through
    # ``workspace_paths.pos_subdir`` per AC.D.2.5). Mechanical fixture
    # path-construction per the d2 test's fixture allowance.
    pos_dir = real_kernel_workspace / "workspace" / ".pos"
    pos_dir.mkdir(parents=True, exist_ok=True)
    (pos_dir / "active-workstream").write_text(
        "loam-realignment\n", encoding="utf-8"
    )

    bundle = compose_bundle(make_envelope(real_kernel_workspace))
    assert "=== active workstream context ===" in bundle
    assert "loam-realignment" in bundle


def test_workstream_tier_present_even_when_no_active_workstream(
    real_kernel_workspace: Path,
) -> None:
    """The workstream tier is PRESENT even when no active workstream is
    set — it degrades to a none-marker, never disappears (so the bundle
    shape is stable for downstream slices, RF-2)."""
    bundle = compose_bundle(make_envelope(real_kernel_workspace))
    assert "=== active workstream context ===" in bundle
    assert "[no active workstream]" in bundle


def test_memory_tier_present_when_no_live_store(
    real_kernel_workspace: Path,
) -> None:
    """The memory tier is PRESENT even when the workspace has no live
    memory-graphiti substrate — it degrades to an empty/unavailable
    marker, never disappears (AC.SACH.3: '>=0 entries, present as a tier
    even when empty')."""
    bundle = compose_bundle(
        make_envelope(real_kernel_workspace, task_text="ship slice 1a")
    )
    assert "=== relevant memory ===" in bundle
    # No .mcp.json -> build_live_mcp_memory_client returns None -> empty
    # marker (the honest no-substrate state).
    assert "[no relevant memory for this dispatch]" in bundle


def test_memory_tier_reflects_workspace_scoped_store(
    real_kernel_workspace: Path, monkeypatch,
) -> None:
    """With a live store wired (a fake MemoryClient via the persona's
    REUSED retrieval path), the memory tier reflects workspace-scoped
    results seeded with the dispatch task text (D-SACH.4). Verifies the
    REUSE of memory_consumer's search(query, group_ids=[slug]) contract
    — not a new mechanism."""
    captured: dict = {}

    class _FakeClient:
        async def search(self, *, query, group_ids, num_results, center_node_uuid):
            captured["query"] = query
            captured["group_ids"] = group_ids
            return {"results": [{"fact": "frame-kernel is the realignment keystone"}]}

        async def add_episode(self, **kw):  # pragma: no cover - unused
            return {}

    # Wire the fake client in at the persona factory the bundle reuses.
    import loam.frame_kernel.bundle as bundle_mod
    from loam.primary_persona import mcp_memory_client as live_mod

    monkeypatch.setattr(
        live_mod, "build_live_mcp_memory_client",
        lambda workspace_root: _FakeClient(),
    )
    # The bundle imports the factory inside _render_memory_tier; patch
    # the source module so the late import picks up the fake.
    _ = bundle_mod  # ensure module import path is live

    bundle = compose_bundle(
        make_envelope(real_kernel_workspace, task_text="what is frame-kernel")
    )
    assert "=== relevant memory ===" in bundle
    # The reused retrieval path rendered the workspace-scoped fact.
    assert "frame-kernel is the realignment keystone" in bundle
    # Query seeded with the dispatch task text (D-SACH.4).
    assert captured["query"] == "what is frame-kernel"
    # group_ids is the workspace slug list (REUSE of the persona's
    # group_ids=[workspace_slug] convention).
    assert isinstance(captured["group_ids"], list) and captured["group_ids"]
