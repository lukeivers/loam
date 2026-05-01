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

"""Amendment #45 — AC.45.3.

``build_supervisor_stanza`` emits a multi-inner-hook envelope when
``extra_inner_hooks`` is supplied. The supervisor command is the
FIRST inner hook (so ``_verify_self_retire``'s ``inner[0]`` check
still passes); the loam-mode-selector is the SECOND (when
registered). Existing supervisor-stanza tests remain green for the
single-contributor case (AC.45.5 backwards-compat).
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import build_supervisor_stanza  # noqa: E402


def test_AC45_3_supervisor_stanza_default_single_inner(tmp_path: Path) -> None:
    """No extras → single inner hook (supervisor)."""
    stanza = build_supervisor_stanza(tmp_path)
    assert stanza["matcher"] == ""
    assert len(stanza["hooks"]) == 1
    cmd = stanza["hooks"][0]["command"]
    assert "pos_session_start.py" in cmd
    assert ".venv/bin/python" in cmd
    assert stanza["hooks"][0]["timeout"] == 20


def test_AC45_3_supervisor_stanza_first_inner_is_supervisor(
    tmp_path: Path,
) -> None:
    """The supervisor entry remains FIRST so ``_verify_self_retire``'s
    ``inner[0]['command']`` check still passes."""
    extra = {
        "type": "command",
        "command": "/path/to/loam-mode-stub",
        "async": False,
        "timeout": 5,
    }
    stanza = build_supervisor_stanza(tmp_path, extra_inner_hooks=[extra])
    assert len(stanza["hooks"]) == 2
    assert "pos_session_start.py" in stanza["hooks"][0]["command"]
    assert stanza["hooks"][1] == extra


def test_AC45_3_supervisor_stanza_loam_mode_appended(tmp_path: Path) -> None:
    """The loam-mode contributor composes with the supervisor stanza
    (the post-self-retire shape) — every Claude Code session post-
    first-run still gets the loam-mode emit alongside the supervisor."""
    from loam_mode.session_start import build_loam_mode_inner_hook

    loam_hook = build_loam_mode_inner_hook(tmp_path)
    stanza = build_supervisor_stanza(tmp_path, extra_inner_hooks=[loam_hook])
    assert len(stanza["hooks"]) == 2
    assert "pos_session_start.py" in stanza["hooks"][0]["command"]
    assert "loam_mode.cli session-start" in stanza["hooks"][1]["command"]
