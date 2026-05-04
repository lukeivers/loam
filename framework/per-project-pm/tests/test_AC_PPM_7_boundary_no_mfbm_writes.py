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

"""AC.PPM.7 — PM does NOT write to M-FBM episode store or .claude/skills.

Per parent plan §5 + cycle-2 plan §4 Surface #8:
  - Full PM lifecycle (load → enqueue → surface) produces zero writes
    to <workspace>/workspace/.loam/memory/.
  - Zero writes to <workspace>/.claude/skills/.
  - Verified via canary files + directory-listing comparison.

This is the PM/M-FBM boundary test: it verifies the design-note's
boundary claim is structurally enforced.
"""

from __future__ import annotations

import os
from pathlib import Path


def _snapshot(dir_path: Path) -> dict[str, tuple[int, int]]:
    """Map from relative-path → (size, mtime_ns) for every file in dir."""
    if not dir_path.exists():
        return {}
    snap: dict[str, tuple[int, int]] = {}
    for root, _dirs, files in os.walk(dir_path):
        for name in files:
            full = Path(root) / name
            rel = str(full.relative_to(dir_path))
            stat = full.stat()
            snap[rel] = (stat.st_size, stat.st_mtime_ns)
    return snap


def test_pm_lifecycle_does_not_write_to_mfbm_episode_store(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    # Pre-create the M-FBM episode store with a canary file.
    mfbm_dir = workspace_root / "workspace" / ".loam" / "memory"
    (mfbm_dir / "episodes" / "test-slug" / "2026-05-04").mkdir(parents=True)
    canary = mfbm_dir / "episodes" / "test-slug" / "2026-05-04" / "canary.md"
    canary.write_text("CANARY — must not be modified by PM lifecycle.")

    pre = _snapshot(mfbm_dir)
    assert pre, "snapshot must be non-empty for the test to be meaningful"

    # Full PM lifecycle.
    from loam.per_project_pm.runtime import PMRuntime

    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    for i in range(3):
        runtime.enqueue_decision(f"Q{i}", provenance="boundary-test")
    while runtime.surface_next_question() is not None:
        pass

    post = _snapshot(mfbm_dir)
    # Every file in pre is unchanged in post; no new files added.
    assert pre == post, (
        f"M-FBM episode store changed during PM lifecycle. "
        f"pre keys: {set(pre)}, post keys: {set(post)}, "
        f"diffs: {[k for k in pre if pre.get(k) != post.get(k)]}"
    )


def test_pm_lifecycle_does_not_write_to_claude_skills(
    authored_pm: tuple[Path, str],
) -> None:
    workspace_root, pm_name = authored_pm
    skills_dir = workspace_root / ".claude" / "skills"
    skills_dir.mkdir(parents=True)
    canary = skills_dir / "canary-skill" / "SKILL.md"
    canary.parent.mkdir()
    canary.write_text("CANARY SKILL — must not be modified by PM lifecycle.")

    pre = _snapshot(skills_dir)
    assert pre

    from loam.per_project_pm.runtime import PMRuntime

    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    for i in range(3):
        runtime.enqueue_decision(f"Q{i}", provenance="boundary-test")
    while runtime.surface_next_question() is not None:
        pass

    post = _snapshot(skills_dir)
    assert pre == post, (
        f".claude/skills/ changed during PM lifecycle. "
        f"diffs: {[k for k in pre if pre.get(k) != post.get(k)]}"
    )


def test_pm_writes_only_under_pm_dir(authored_pm: tuple[Path, str]) -> None:
    """All writes during a PM lifecycle land under the PM's own state dir."""
    workspace_root, pm_name = authored_pm
    # Snapshot the entire workspace except the PM dir; assert unchanged.
    pm_dir = workspace_root / "workspace" / ".loam" / "pms" / pm_name
    workspace_dir = workspace_root / "workspace"
    # Build a snapshot of everything under workspace/ excluding the PM
    # dir.
    pre: dict[str, tuple[int, int]] = {}
    for root, _dirs, files in os.walk(workspace_dir):
        root_path = Path(root)
        if pm_dir in [root_path, *root_path.parents]:
            continue
        for name in files:
            full = root_path / name
            rel = str(full.relative_to(workspace_dir))
            stat = full.stat()
            pre[rel] = (stat.st_size, stat.st_mtime_ns)

    from loam.per_project_pm.runtime import PMRuntime

    runtime = PMRuntime.from_workspace(workspace_root, pm_name)
    runtime.enqueue_decision("Boundary-test")
    runtime.surface_next_question()

    post: dict[str, tuple[int, int]] = {}
    for root, _dirs, files in os.walk(workspace_dir):
        root_path = Path(root)
        if pm_dir in [root_path, *root_path.parents]:
            continue
        for name in files:
            full = root_path / name
            rel = str(full.relative_to(workspace_dir))
            stat = full.stat()
            post[rel] = (stat.st_size, stat.st_mtime_ns)

    assert pre == post, (
        f"Write outside PM dir detected. "
        f"new/changed keys: "
        f"{[k for k in post if post.get(k) != pre.get(k)]}"
    )
