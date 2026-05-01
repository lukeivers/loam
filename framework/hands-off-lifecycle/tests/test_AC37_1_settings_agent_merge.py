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

"""Amendment #37 — AC37.1 — first-run merges ``"agent": "<handle>"`` into
``.claude/settings.json``.

Plan §4 AC37.1 outcomes:

  - ``<workspace>/.claude/settings.json`` contains ``"agent":
    "<handle>"`` at the top level after the merge.
  - Pre-existing keys (the SessionStart hook from amendment #32 + any
    user-set keys) are preserved unchanged.
  - The ``<handle>`` value matches the handle the merge call passed.
  - When ``settings.json`` does not exist, the merge creates it with
    the ``"agent"`` field plus the SessionStart stanza.

Maps to v1.0 line 153 (persona present every session — Claude Code
default-agent binding) → AC.PO.1.
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


# ---- AC37.1 — agent merge on fresh settings.json ---------------------


def test_AC37_1_agent_merged_on_fresh_settings(fresh_workspace: Path) -> None:
    """Fresh first-run merge writes ``"agent": "<handle>"`` alongside
    the SessionStart stanza when settings.json does not pre-exist."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    assert not settings_path.exists()

    stanza = build_first_run_stanza(fresh_workspace)
    result = merge_session_start(
        settings_path=settings_path,
        new_entry=stanza,
        agent_handle="primary",
    )

    assert result.wrote is True
    data = json.loads(settings_path.read_text())
    assert data["agent"] == "primary", (
        "AC37.1: settings.json must carry the resolved handle as a "
        "top-level 'agent' field"
    )
    # The SessionStart stanza is still in place — the agent merge does
    # not displace the hook stanza.
    assert (
        data["hooks"]["SessionStart"][0]["hooks"][0]["command"].endswith(
            "first-run.sh"
        )
    )


def test_AC37_1_agent_merged_with_custom_handle(fresh_workspace: Path) -> None:
    """The ``<handle>`` written matches the resolved handle exactly —
    not normalised, not defaulted."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    stanza = build_first_run_stanza(fresh_workspace)
    merge_session_start(
        settings_path=settings_path,
        new_entry=stanza,
        agent_handle="iris",
    )
    data = json.loads(settings_path.read_text())
    assert data["agent"] == "iris"


def test_AC37_1_existing_user_keys_preserved_under_agent_merge(
    fresh_workspace: Path,
) -> None:
    """Pre-existing user-authored top-level keys remain unchanged when
    the agent merge writes ``"agent"``. AC37.1 second outcome —
    "pre-existing keys ... are preserved unchanged"."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "env": {"MY_USER_VAR": "42"},
                "permissions": {"allow": ["Read(//**)"]},
                "hooks": {
                    "PreToolUse": [
                        {"type": "command", "command": "/bin/true"}
                    ]
                },
            },
            indent=2,
        )
    )

    stanza = build_first_run_stanza(fresh_workspace)
    merge_session_start(
        settings_path=settings_path,
        new_entry=stanza,
        agent_handle="primary",
    )

    data = json.loads(settings_path.read_text())
    assert data["agent"] == "primary"
    # Pre-existing user keys preserved.
    assert data["env"] == {"MY_USER_VAR": "42"}
    assert data["permissions"] == {"allow": ["Read(//**)"]}
    assert data["hooks"]["PreToolUse"][0]["command"] == "/bin/true"
    # SessionStart populated with the new entry.
    assert (
        data["hooks"]["SessionStart"][0]["hooks"][0]["command"].endswith(
            "first-run.sh"
        )
    )


def test_AC37_1_agent_handle_none_leaves_field_untouched(
    fresh_workspace: Path,
) -> None:
    """``agent_handle=None`` (the unwiring path) leaves the ``"agent"``
    field exactly as it was — backwards-compat preservation. The AC's
    contract is "merges 'agent' on first-run"; absent agent_handle is
    pre-amendment-#37 caller behaviour and must be a no-op for the
    field."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "agent": "user-set-elsewhere",
                "hooks": {},
            },
            indent=2,
        )
    )

    stanza = build_first_run_stanza(fresh_workspace)
    merge_session_start(
        settings_path=settings_path,
        new_entry=stanza,
        # No agent_handle — backwards-compat path.
    )

    data = json.loads(settings_path.read_text())
    assert data["agent"] == "user-set-elsewhere", (
        "agent_handle=None must not touch the 'agent' field"
    )


def test_AC37_1_agent_overwrites_prior_value(fresh_workspace: Path) -> None:
    """When ``agent_handle`` is explicitly provided, the workspace's
    resolved handle is authoritative — pre-existing values are
    overwritten. This is the AC37.1 first-run-from-clone behaviour: the
    workspace-bootstrap-resolved handle wins."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "agent": "old-stale",
                "hooks": {},
            },
            indent=2,
        )
    )

    stanza = build_first_run_stanza(fresh_workspace)
    merge_session_start(
        settings_path=settings_path,
        new_entry=stanza,
        agent_handle="primary",
    )

    data = json.loads(settings_path.read_text())
    assert data["agent"] == "primary"


def test_AC37_1_self_retire_preserves_agent_field(fresh_workspace: Path) -> None:
    """At Phase 6 self-retire (``merge_session_start`` with the
    supervisor stanza), the agent field threads through and remains in
    settings.json. Pre-amendment-#37 callers (no agent_handle) leave the
    pre-existing ``"agent"`` value intact; amendment-#37 callers may
    pass agent_handle to refresh it."""
    settings_path = fresh_workspace / ".claude" / "settings.json"

    # Phase 3d / 4c first-run write — agent merged.
    merge_session_start(
        settings_path=settings_path,
        new_entry=build_first_run_stanza(fresh_workspace),
        agent_handle="primary",
    )

    # Phase 6 self-retire — supervisor stanza, agent re-merged.
    merge_session_start(
        settings_path=settings_path,
        new_entry=build_supervisor_stanza(fresh_workspace),
        agent_handle="primary",
    )

    data = json.loads(settings_path.read_text())
    assert data["agent"] == "primary"
    cmd = data["hooks"]["SessionStart"][0]["hooks"][0]["command"]
    assert "pos_session_start.py" in cmd


def test_AC37_1_preserved_user_keys_excludes_agent(fresh_workspace: Path) -> None:
    """The ``preserved_user_keys`` field reports the merge's preserved
    surface for the confirmation sentence; ``"agent"`` is the
    amendment-owned field, not a preserved-user-key, so it should not
    appear in that tuple even when the merge wrote it."""
    settings_path = fresh_workspace / ".claude" / "settings.json"
    settings_path.write_text(
        json.dumps(
            {"env": {"X": "1"}, "hooks": {}},
            indent=2,
        )
    )
    stanza = build_first_run_stanza(fresh_workspace)
    result = merge_session_start(
        settings_path=settings_path,
        new_entry=stanza,
        agent_handle="primary",
    )
    assert "agent" not in result.preserved_user_keys
    assert "env" in result.preserved_user_keys
