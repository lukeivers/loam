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

"""AC.SFC.S (outcome-altitude) — a REAL sync composes the REAL fragment.

A sync exercised through the production ``pos-sync`` entry-point
(``cli.main``) against a fixture workspace composes the REAL
frame-kernel SubagentStart + SubagentStop fragment blocks into the
fixture's ``.claude/settings.json``; a pre-existing user ``Stop`` hook +
a ``statusLine`` key survive byte-untouched; a SECOND real sync is
idempotent — all asserted by READING the resulting settings.json.

outcome-altitude: true

No STUB-class test of the compose function satisfies this AC; only the
real sync -> auto-compose end-to-end path does. The composer fires
AUTOMATICALLY on the fast-forward terminal-success path of the real
sync (it is not invoked directly by this test).
"""

from __future__ import annotations

import json
from pathlib import Path

from loam.workspace_sync.cli import main as cli_main

# The REAL frame-kernel fragment lives at the canonical repo root,
# four parents up from this test file
# (framework/workspace-sync/tests/<this>).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_REAL_FRAGMENT = (
    _REPO_ROOT
    / "framework"
    / "frame-kernel"
    / "hooks"
    / "settings.fragment.json"
)

USER_STOP_GROUP = {
    "matcher": "",
    "hooks": [{"type": "command", "command": "echo my-real-stop-hook"}],
}
STATUSLINE = {"type": "command", "command": "echo my-real-status"}


def _seed_user_settings(fixture_ws: Path) -> Path:
    claude = fixture_ws / ".claude"
    claude.mkdir(parents=True, exist_ok=True)
    settings_path = claude / "settings.json"
    settings_path.write_text(
        json.dumps(
            {
                "statusLine": STATUSLINE,
                "hooks": {"Stop": [USER_STOP_GROUP]},
            },
            indent=2,
        )
        + "\n"
    )
    return settings_path


def test_AC_SFC_S_real_sync_composes_real_frame_kernel_fragment(
    make_framework_workspace, advance_canonical
):
    # The REAL frame-kernel fragment must exist (load-bearing input).
    assert _REAL_FRAGMENT.exists(), (
        f"real frame-kernel fragment missing at {_REAL_FRAGMENT}"
    )
    real_fragment_text = _REAL_FRAGMENT.read_text()

    # Build a fixture workspace whose synced framework/ carries the REAL
    # frame-kernel fragment at its real path.
    fixture_ws, canonical_root = make_framework_workspace(
        canonical_files={
            "README.md": "# canonical v1\n",
            "frame-kernel/hooks/settings.fragment.json": real_fragment_text,
        },
    )
    settings_path = _seed_user_settings(fixture_ws)

    # Advance canonical so the sync fast-forwards (a real HEAD-advance).
    advance_canonical(
        canonical_root,
        {"README.md": "# canonical v2\n"},
        message="advance for FF sync",
    )

    # Run the production entry-point end-to-end. The composer fires
    # automatically on the fast-forward terminal-success path.
    rc = cli_main(["--workspace", str(fixture_ws)])
    assert rc == 0

    settings = json.loads(settings_path.read_text())
    hooks = settings["hooks"]

    # (a) frame-kernel SubagentStart + SubagentStop composed, loam-tagged,
    #     ${LOAM_REPO}-resolved.
    assert "SubagentStart" in hooks
    assert "SubagentStop" in hooks
    start_group = hooks["SubagentStart"][0]
    stop_group = hooks["SubagentStop"][0]
    assert "_loam" in start_group
    assert start_group["_loam"]["component"] == "frame-kernel"
    assert "_loam" in stop_group
    start_cmd = start_group["hooks"][0]["command"]
    stop_cmd = stop_group["hooks"][0]["command"]
    assert "${LOAM_REPO}" not in start_cmd
    assert "${LOAM_REPO}" not in stop_cmd
    # Resolved to point at the synced framework tree.
    assert str(fixture_ws / "framework" / "frame-kernel") in start_cmd
    assert "subagent_start_context.py" in start_cmd
    assert "subagent_stop_frame_check.py" in stop_cmd

    # (b) the user Stop hook + statusLine survive byte-untouched.
    assert settings["statusLine"] == STATUSLINE
    assert hooks["Stop"] == [USER_STOP_GROUP]

    # (c) a SECOND real sync is idempotent (no duplicates).
    advance_canonical(
        canonical_root,
        {"README.md": "# canonical v3\n"},
        message="advance again",
    )
    rc2 = cli_main(["--workspace", str(fixture_ws)])
    assert rc2 == 0

    settings2 = json.loads(settings_path.read_text())
    hooks2 = settings2["hooks"]
    assert len(hooks2["SubagentStart"]) == 1, "no duplicate SubagentStart"
    assert len(hooks2["SubagentStop"]) == 1, "no duplicate SubagentStop"
    # User content still untouched after the second sync.
    assert settings2["statusLine"] == STATUSLINE
    assert hooks2["Stop"] == [USER_STOP_GROUP]
