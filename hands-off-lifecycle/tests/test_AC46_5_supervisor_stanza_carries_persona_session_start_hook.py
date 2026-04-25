"""AC46.5 (part 2) — ``build_supervisor_stanza`` carries the persona's
SessionStart inner hook post-self-retire.

Mirrors the part-1 test for ``build_first_run_stanza`` but exercises
the supervisor stanza (the post-Phase-6 shape). Same ordering applies:
probe (supervisor) → persona → loam-mode.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HOOKS_DIR = REPO_ROOT / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import build_supervisor_stanza  # noqa: E402


def _persona_inner_hook_stub(pos_v2_root: Path) -> dict:
    return {
        "type": "command",
        "command": (
            f"{pos_v2_root}/.venv/bin/python "
            "-m primary_persona.cli session-start"
        ),
        "async": False,
        "timeout": 5,
    }


def _loam_mode_inner_hook_stub(pos_v2_root: Path) -> dict:
    return {
        "type": "command",
        "command": (
            f"{pos_v2_root}/.venv/bin/python -m loam_mode.cli session-start"
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
