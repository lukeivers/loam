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

"""AC46.5 (part 2) — ``build_supervisor_stanza`` carries the persona's
SessionStart inner hook post-self-retire.

Mirrors the part-1 test for ``build_first_run_stanza`` but exercises
the supervisor stanza (the post-Phase-6 shape). Same ordering applies:
probe (supervisor) → persona → loam-mode.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import build_supervisor_stanza  # noqa: E402


def _persona_inner_hook_stub(loam_root: Path) -> dict:
    return {
        "type": "command",
        "command": (
            f"{loam_root}/.venv/bin/python "
            "-m loam.primary_persona.cli session-start"
        ),
        "async": False,
        "timeout": 5,
    }


def _loam_mode_inner_hook_stub(loam_root: Path) -> dict:
    return {
        "type": "command",
        "command": (
            f"{loam_root}/.venv/bin/python -m loam_mode.cli session-start"
        ),
        "async": False,
        "timeout": 5,
    }


def test_AC46_5_supervisor_stanza_carries_persona_inner_hook(
    tmp_path: Path,
) -> None:
    """Supervisor stanza carries persona inner hook second (after
    supervisor / pos_session_start.py), loam-mode third."""
    extras = [
        _persona_inner_hook_stub(tmp_path),
        _loam_mode_inner_hook_stub(tmp_path),
    ]
    stanza = build_supervisor_stanza(tmp_path, extra_inner_hooks=extras)
    inner = stanza["hooks"]
    assert len(inner) == 3
    # First inner hook: supervisor (pos_session_start.py).
    assert "pos_session_start.py" in inner[0]["command"]
    # Second: persona.
    assert "primary_persona.cli session-start" in inner[1]["command"]
    # Third: loam-mode.
    assert "loam_mode.cli session-start" in inner[2]["command"]
