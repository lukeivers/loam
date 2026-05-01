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

"""Shared pytest fixtures for orchestrator tests."""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path

import pytest

from loam.orchestrator.config import OrchestratorConfig
from loam.scope_of_work import ScopeSpec
from loam.scope_of_work.spec import Budget, ReversibilityClass


def make_scope_spec(goal: str, *, owner: str = "rune", tokens: int = 1000) -> ScopeSpec:
    """Test helper — minimal ScopeSpec."""
    return ScopeSpec(
        goal=goal,
        constraints=(),
        budget=Budget(tokens=tokens),
        reversibility_class=ReversibilityClass.fully_reversible,
        success_criteria=(),
        observers=(),
        escalation_triggers=(),
        owner_persona=owner,
    )


_BOOTSTRAP_CONTENT = '''"""Test-only bootstrap — no-op register()."""

def register(orchestrator):
    return None
'''


def _short_socket_path() -> Path:
    """AF_UNIX on macOS caps path length at 104 bytes; pytest's
    tmp_path often exceeds it. Put the socket under /tmp with a short
    unique name."""
    base = Path(tempfile.gettempdir())
    name = f"pos-{uuid.uuid4().hex[:12]}.sock"
    return base / name


@pytest.fixture
def tmp_config(tmp_path: Path) -> OrchestratorConfig:
    """Build an OrchestratorConfig rooted at tmp_path. Socket is placed
    in /tmp to stay under the AF_UNIX 104-byte path cap on macOS.

    A no-op ``bootstrap.py`` is still written under ``pos_root`` so the
    workspace-bootstrap integration tests that exercise the
    ``WorkspaceBootstrapPyContribution`` adapter path find the expected
    file. The orchestrator itself does not load it post-amendment #7
    (docs/rebuild/components/orchestrator-bootstrap-unification/
    proposal.md), but keeping the fixture's on-disk shape stable avoids
    cross-suite churn.
    """
    root = tmp_path / "pos"
    root.mkdir(parents=True, exist_ok=True)
    (root / "bootstrap.py").write_text(_BOOTSTRAP_CONTENT)
    sock = _short_socket_path()
    cfg = OrchestratorConfig(
        root_dir=root,
        socket_path=sock,
        heartbeat_interval_seconds=0.05,  # fast for tests
        sigterm_grace_seconds=1.0,
    )
    yield cfg
    # Clean up stray socket file.
    try:
        if sock.exists():
            sock.unlink()
    except Exception:
        pass
