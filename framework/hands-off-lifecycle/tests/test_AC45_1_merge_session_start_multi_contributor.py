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

"""Amendment #45 — AC.45.1.

``merge_session_start`` accepts a multi-inner-hook envelope (zero or
more contributors) and composes it into the resulting
``.claude/settings.json`` such that the final
``hooks["SessionStart"]`` list contains all contributor inner-hooks
in the order supplied. Existing single-contributor callers remain
byte-identical (regression-safe).

Maps to AC.PO.1 (multi-contributor SessionStart composition is a
queryable harness primitive — translation burden absorbed) +
AC.PO.2 (toolkit expanded).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import (  # noqa: E402
    build_first_run_stanza,
    build_supervisor_stanza,
    merge_session_start,
)


@pytest.fixture
def fresh_workspace(tmp_path: Path) -> Path:
    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    (ws / "hands-off-lifecycle" / "hooks").mkdir(parents=True)
    (ws / "orchestrator" / "scripts").mkdir(parents=True)
    return ws


def test_AC45_1_zero_extra_contributors_byte_identical_to_pre_amendment(
    fresh_workspace: Path,
) -> None:
    """AC.45.1 backwards-compat: zero contributors produces a stanza
    byte-identical to the pre-amendment-#45 single-inner-hook shape.
    """
    settings_path = fresh_workspace / ".claude" / "settings.json"

    # New code path — extra_inner_hooks=None default.
    stanza_default = build_first_run_stanza(fresh_workspace)
    merge_session_start(settings_path=settings_path, new_entry=stanza_default)

    data = json.loads(settings_path.read_text())
    inner = data["hooks"]["SessionStart"][0]["hooks"]
    assert len(inner) == 1, (
        "AC.45.1: zero extras must produce exactly one inner hook"
    )
    assert inner[0]["command"].endswith("first-run.sh")
    # Outer envelope shape preserved.
    assert data["hooks"]["SessionStart"][0]["matcher"] == ""


def test_AC45_1_one_extra_contributor_appended_in_order(
    fresh_workspace: Path,
) -> None:
    """AC.45.1: one extra inner hook is appended after the base, in
    the order supplied. Caller controls order; the function does not
    re-sort."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    extra = {
        "type": "command",
        "command": "/usr/bin/echo loam-mode-stub",
        "async": False,
        "timeout": 5,
    }
    stanza = build_first_run_stanza(
        fresh_workspace,
        extra_inner_hooks=[extra],
    )
    merge_session_start(settings_path=settings_path, new_entry=stanza)
    data = json.loads(settings_path.read_text())
    inner = data["hooks"]["SessionStart"][0]["hooks"]
    assert len(inner) == 2
    # Base (first-run.sh) FIRST.
    assert inner[0]["command"].endswith("first-run.sh")
    # Extra contributor SECOND.
    assert inner[1]["command"] == "/usr/bin/echo loam-mode-stub"


def test_AC45_1_multiple_contributors_compose_in_order(
    fresh_workspace: Path,
) -> None:
    """AC.45.1: any number of extra contributors compose; the function
    is generic over N>=0."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    extras = [
        {
            "type": "command",
            "command": f"/usr/bin/echo extra-{i}",
            "async": False,
            "timeout": 5,
        }
        for i in range(3)
    ]
    stanza = build_supervisor_stanza(
        fresh_workspace,
        extra_inner_hooks=extras,
    )
    merge_session_start(settings_path=settings_path, new_entry=stanza)
    data = json.loads(settings_path.read_text())
    inner = data["hooks"]["SessionStart"][0]["hooks"]
    # Base (supervisor) + 3 extras = 4 inner hooks.
    assert len(inner) == 4
    assert "pos_session_start.py" in inner[0]["command"]
    for i in range(3):
        assert inner[i + 1]["command"] == f"/usr/bin/echo extra-{i}"


def test_AC45_1_outer_session_start_remains_single_entry(
    fresh_workspace: Path,
) -> None:
    """AC.45.1: the OUTER ``hooks.SessionStart`` list still carries
    exactly one envelope entry — multi-contributor lives in the INNER
    ``hooks`` array, not by appending more outer entries. This
    preserves the Claude Code schema shape callers depend on."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    stanza = build_first_run_stanza(
        fresh_workspace,
        extra_inner_hooks=[
            {"type": "command", "command": "/bin/true", "async": False, "timeout": 5}
        ],
    )
    merge_session_start(settings_path=settings_path, new_entry=stanza)
    data = json.loads(settings_path.read_text())
    assert len(data["hooks"]["SessionStart"]) == 1
    assert isinstance(data["hooks"]["SessionStart"][0]["hooks"], list)
