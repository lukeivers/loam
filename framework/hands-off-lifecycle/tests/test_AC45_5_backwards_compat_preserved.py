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

"""Amendment #45 — AC.45.5.

Backwards-compat: amendment #32 (session-start context-load gate)
and amendment #37 (default-agent wiring) test suites stay green.
The contributor registry preserves their existing inner-hook
semantics. Zero-or-one-contributor produces IDENTICAL output to the
pre-amendment code path.

This test file's job is to assert the bytes-level invariant
directly. The full #32 + #37 suites stay green via the regular test
run; AC.45.5 here is the codified guarantee that the new
``extra_inner_hooks=None`` default branch is byte-identical to the
pre-amendment shape.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import (  # noqa: E402
    build_first_run_stanza,
    build_supervisor_stanza,
    merge_session_start,
)


def test_AC45_5_first_run_stanza_bytes_unchanged_default_path(
    tmp_path: Path,
) -> None:
    """Default call (``extra_inner_hooks=None``) must produce the
    SAME stanza dict as the pre-amendment shape — same keys, same
    inner-hook count, same command, same timeout, same async flag.
    """
    stanza = build_first_run_stanza(tmp_path)
    expected = {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": str(
                    tmp_path
                    / "hands-off-lifecycle"
                    / "hooks"
                    / "first-run.sh"
                ),
                "async": False,
                "timeout": 60,
            }
        ],
    }
    assert stanza == expected


def test_AC45_5_supervisor_stanza_bytes_unchanged_default_path(
    tmp_path: Path,
) -> None:
    """Default supervisor stanza must produce the SAME dict as the
    pre-amendment shape."""
    stanza = build_supervisor_stanza(tmp_path)
    expected_python = str(tmp_path / ".venv" / "bin" / "python")
    expected_script = str(
        tmp_path / "framework" / "orchestrator" / "scripts" / "pos_session_start.py"
    )
    expected = {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": f"{expected_python} {expected_script}",
                "async": False,
                "timeout": 20,
            }
        ],
    }
    assert stanza == expected


def test_AC45_5_amendment_32_settings_shape_preserved(tmp_path: Path) -> None:
    """Amendment #32 (session-start context-load gate) consumed the
    pre-amendment-#37 shape. The default merge path must still
    produce the schema #32 expects: a single SessionStart entry with
    a single inner hook pointing at first-run.sh / pos_session_start.py.
    """
    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    settings_path = ws / ".claude" / "settings.json"

    stanza = build_first_run_stanza(ws)
    merge_session_start(settings_path=settings_path, new_entry=stanza)

    data = json.loads(settings_path.read_text())
    assert "hooks" in data
    assert "SessionStart" in data["hooks"]
    assert len(data["hooks"]["SessionStart"]) == 1
    inner = data["hooks"]["SessionStart"][0]["hooks"]
    assert len(inner) == 1
    assert inner[0]["command"].endswith("first-run.sh")


def test_AC45_5_amendment_37_agent_merge_unaffected_by_extras(
    tmp_path: Path,
) -> None:
    """Amendment #37's ``agent_handle`` merge must still apply when
    the stanza carries multiple inner hooks. The agent field is a
    top-level setting orthogonal to the SessionStart inner-hook list.
    """
    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    settings_path = ws / ".claude" / "settings.json"

    extra = {
        "type": "command",
        "command": "/usr/bin/echo extra",
        "async": False,
        "timeout": 5,
    }
    stanza = build_first_run_stanza(ws, extra_inner_hooks=[extra])
    merge_session_start(
        settings_path=settings_path,
        new_entry=stanza,
        agent_handle="primary",
    )
    data = json.loads(settings_path.read_text())
    # AC37.1 still holds.
    assert data["agent"] == "primary"
    # Multi-inner-hook envelope still in place.
    inner = data["hooks"]["SessionStart"][0]["hooks"]
    assert len(inner) == 2


def test_AC45_5_repeat_merge_does_not_back_up_pos_v2_owned_multi_inner(
    tmp_path: Path,
) -> None:
    """A second merge over a stanza we wrote (multi-inner-hook
    shape) does NOT trigger the user-stanza backup path. The
    expanded ``_is_pos_v2_owned`` predicate recognises the new
    contributor commands."""
    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    settings_path = ws / ".claude" / "settings.json"

    extra = {
        "type": "command",
        "command": (
            f"{ws / '.venv' / 'bin' / 'python'} -m loam_mode.cli session-start"
        ),
        "async": False,
        "timeout": 5,
    }
    # First merge: writes the multi-inner-hook envelope.
    stanza1 = build_first_run_stanza(ws, extra_inner_hooks=[extra])
    result1 = merge_session_start(settings_path=settings_path, new_entry=stanza1)
    assert result1.prior_session_start_displaced is False
    assert result1.backup_path is None

    # Second merge over the same file: still pos-v2-owned, no backup.
    stanza2 = build_supervisor_stanza(ws, extra_inner_hooks=[extra])
    result2 = merge_session_start(settings_path=settings_path, new_entry=stanza2)
    assert result2.prior_session_start_displaced is False, (
        "AC.45.5: a multi-inner-hook stanza we authored must NOT be "
        "treated as user-authored on re-merge."
    )
    assert result2.backup_path is None
