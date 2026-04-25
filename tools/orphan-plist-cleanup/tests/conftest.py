"""Shared fixtures for orphan-plist-cleanup tests.

Provides a ``launch_agents_dir`` fixture that builds a tmp_path
shaped like ``~/Library/LaunchAgents/`` populated with a known mix
of orphan, namespaced, and unrelated plist files. Tests inspect the
directory after detector / remediator runs to verify ACs.
"""

from __future__ import annotations

from pathlib import Path

import pytest


# A mix that exercises every classification arm.
SAMPLE_FILES: dict[str, str] = {
    # ORPHAN_V2 (pre-#6 pos-v2 single-segment) — AC1, AC3, AC4 targets
    "com.pos-v2.memory-graphiti.plist": "<plist v2 orphan body/>",
    "com.pos-v2.orchestrator.plist": "<plist v2 orphan body/>",
    # ORPHAN_V1 (pre-pos-v2 v1 shape) — AC1 target
    "com.pos.orchestrator.plist": "<plist v1 orphan body/>",
    # NAMESPACED_V2 (workspace-slug-namespaced — AC5 positive guard)
    "com.pos-v2.alpha.memory-graphiti.plist": "<plist namespaced body/>",
    "com.pos-v2.alpha.orchestrator.plist": "<plist namespaced body/>",
    # NOT_POS_V2 — unrelated user/system plists
    "com.apple.something.plist": "<plist apple body/>",
    "com.example.user.daemon.plist": "<plist user body/>",
    # Non-plist file in the directory — must be ignored
    "README.txt": "not a plist",
}


@pytest.fixture
def launch_agents_dir(tmp_path: Path) -> Path:
    """Build a tmp directory shaped like ~/Library/LaunchAgents/.

    Returns the directory path; tests can populate or inspect it.
    """
    agents = tmp_path / "LaunchAgents"
    agents.mkdir()
    for name, content in SAMPLE_FILES.items():
        (agents / name).write_text(content)
    return agents


@pytest.fixture
def empty_launch_agents_dir(tmp_path: Path) -> Path:
    """An empty LaunchAgents-shaped directory for the "no orphans"
    path."""
    agents = tmp_path / "LaunchAgents-empty"
    agents.mkdir()
    return agents
