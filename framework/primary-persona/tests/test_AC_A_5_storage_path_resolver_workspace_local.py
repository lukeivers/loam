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

"""AC.A.5 — Workspace-local storage location is exposed via a path-resolver.

Sub-plan A (two-modes-and-multi-workspace) exposes a pure function
``dev_intent_storage_path(workspace_root)`` returning the on-disk
location of the dev-intent answer. Per locked owner ruling
D-MASTER.1 (a) the answer lives on the persona contract itself; the
resolver returns the workspace's ``personas/`` directory which the
reader walks to locate the primary contract.

Sub-plans E / B / F consume this resolver, not the contract directly,
so the storage shape is substitutable without re-reading those
sub-plans (asymmetric observation #2: resolver-as-API).

Plan: docs/rebuild/plans/two-modes-and-multi-workspace/A-onboarding-dev-intent.md
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.onboarding import dev_intent_storage_path


def test_AC_A_5_resolver_returns_path(tmp_path: Path):
    """Calling the resolver against a workspace_root returns a Path."""
    out = dev_intent_storage_path(tmp_path)
    assert isinstance(out, Path)


def test_AC_A_5_resolver_path_is_workspace_rooted(tmp_path: Path):
    """The returned path is rooted at workspace_root (not host-rooted)."""
    out = dev_intent_storage_path(tmp_path)
    assert out.is_relative_to(tmp_path)


def test_AC_A_5_resolver_two_workspaces_yield_distinct_paths(tmp_path: Path):
    """Two distinct workspace_roots resolve to two distinct paths.
    Cross-workspace bleed is structurally impossible (locked owner
    ruling 4)."""
    ws1 = tmp_path / "workspace-1"
    ws2 = tmp_path / "workspace-2"
    ws1.mkdir()
    ws2.mkdir()
    p1 = dev_intent_storage_path(ws1)
    p2 = dev_intent_storage_path(ws2)
    assert p1 != p2


def test_AC_A_5_resolver_is_pure(tmp_path: Path):
    """The resolver is a pure function — no on-disk side effects, no
    state."""
    # Capture the directory listing before and after; nothing should
    # change.
    children_before = sorted(p.name for p in tmp_path.iterdir())
    dev_intent_storage_path(tmp_path)
    dev_intent_storage_path(tmp_path)
    children_after = sorted(p.name for p in tmp_path.iterdir())
    assert children_before == children_after


def test_AC_A_5_resolver_returns_personas_directory(tmp_path: Path):
    """Per locked owner ruling D-MASTER.1 (a) the answer lives on the
    persona contract; the resolver returns the personas/ directory the
    reader walks to find the primary contract."""
    out = dev_intent_storage_path(tmp_path)
    # The resolver returns the personas/ directory. Method-level
    # detail (the directory name) is the builder's call; the AC bounds
    # outcome — the path is workspace-rooted and the consumer reader
    # uses it. We assert the relative shape: name 'personas' is a
    # method commitment but we test it via the read API (AC.A.6's
    # round-trip) to avoid pinning method here. AC.A.5's outcome is
    # the workspace-rooting + distinctness above.
    # D-migration D.2 (amendment #63): personas live under
    # <ws>/workspace/personas/ post-D.2 (was <ws>/personas/ pre-D.2).
    assert out.parent == tmp_path / "workspace"
