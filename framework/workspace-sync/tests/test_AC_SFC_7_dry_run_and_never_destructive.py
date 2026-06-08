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

"""AC.SFC.7 — dry-run + never-destructive.

``--dry-run-compose`` reports the would-add/would-remove plan and
writes nothing; a malformed/unparseable existing settings.json causes
the compose to surface an error and write nothing (never a destructive
overwrite).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from loam.workspace_sync.fragment_composer import (
    MalformedSettingsError,
    compose_settings_fragments,
)

FRAGMENT = {
    "_comment": "c",
    "hooks": {
        "SubagentStart": [
            {
                "matcher": "",
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            "${LOAM_REPO}/framework/frame-kernel/hooks/"
                            "subagent_start_context.py"
                        ),
                        "timeout": 10,
                    }
                ],
            }
        ]
    },
}


def _ws_with_fragment(tmp_path: Path) -> Path:
    ws = tmp_path / "ws"
    frag = (
        ws / "framework" / "frame-kernel" / "hooks"
        / "settings.fragment.json"
    )
    frag.parent.mkdir(parents=True)
    frag.write_text(json.dumps(FRAGMENT))
    return ws


def test_AC_SFC_7_dry_run_writes_nothing_when_file_absent(tmp_path):
    ws = _ws_with_fragment(tmp_path)
    settings_path = ws / ".claude" / "settings.json"

    plan = compose_settings_fragments(
        ws, dry_run=True, emit_summary=False
    )
    # The plan reports the would-add entry.
    assert len(plan.added) == 1
    # Nothing was written.
    assert not settings_path.exists(), (
        "--dry-run-compose must write nothing"
    )


def test_AC_SFC_7_dry_run_leaves_existing_file_byte_identical(tmp_path):
    ws = _ws_with_fragment(tmp_path)
    claude = ws / ".claude"
    claude.mkdir(parents=True)
    seeded = json.dumps(
        {"statusLine": {"x": 1}, "hooks": {"Stop": []}}, indent=2
    )
    (claude / "settings.json").write_text(seeded)

    before = (claude / "settings.json").read_bytes()
    plan = compose_settings_fragments(
        ws, dry_run=True, emit_summary=False
    )
    assert len(plan.added) == 1
    after = (claude / "settings.json").read_bytes()
    assert before == after, (
        "dry-run must leave the existing settings.json byte-identical"
    )


def test_AC_SFC_7_malformed_settings_halts_and_does_not_overwrite(
    tmp_path,
):
    ws = _ws_with_fragment(tmp_path)
    claude = ws / ".claude"
    claude.mkdir(parents=True)
    malformed = "{ this is not valid json"
    (claude / "settings.json").write_text(malformed)

    before = (claude / "settings.json").read_bytes()
    with pytest.raises(MalformedSettingsError):
        compose_settings_fragments(ws, emit_summary=False)

    after = (claude / "settings.json").read_bytes()
    assert before == after, (
        "a malformed settings.json must be left byte-identical "
        "(never a destructive overwrite)"
    )
