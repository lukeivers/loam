"""Amendment #45 — AC.45.4.

Sub-plan B's AC.B1-B5 are satisfied by this amendment's seam.
Specifically: B's emitter at
``tools/loam-mode/src/loam_mode/session_start.py`` produces the
inner-hook stanza; the contributor registry surface (the
``extra_inner_hooks`` parameter on ``build_first_run_stanza`` /
``build_supervisor_stanza``) is consumed by ``merge_session_start``
via the multi-inner-hook envelope.

This test verifies the seam — that the integration shape works
end-to-end. Detailed AC.B1-B5 behavioural coverage lives in
``tools/loam-mode/tests/test_AC_B*_*.py``.
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


def test_AC45_4_emitter_module_importable() -> None:
    """B's emitter module loads without raising."""
    from loam_mode.session_start import (  # noqa: F401
        build_loam_mode_inner_hook,
        compute_session_mode,
        emit_session_start_context,
        read_dev_intent_safe,
    )


def test_AC45_4_seam_first_run_inner_hook_end_to_end(tmp_path: Path) -> None:
    """The end-to-end seam: B's ``build_loam_mode_inner_hook`` →
    hands-off-lifecycle's ``extra_inner_hooks`` → ``merge_session_start``
    → a settings.json carrying both inner hooks."""
    from loam_mode.session_start import build_loam_mode_inner_hook

    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    settings_path = ws / ".claude" / "settings.json"

    loam_hook = build_loam_mode_inner_hook(ws)
    stanza = build_first_run_stanza(ws, extra_inner_hooks=[loam_hook])
    merge_session_start(settings_path=settings_path, new_entry=stanza)

    data = json.loads(settings_path.read_text())
    inner = data["hooks"]["SessionStart"][0]["hooks"]
    assert len(inner) == 2
    assert inner[0]["command"].endswith("first-run.sh")
    assert "loam_mode.cli session-start" in inner[1]["command"]


def test_AC45_4_seam_supervisor_inner_hook_end_to_end(tmp_path: Path) -> None:
    """Same end-to-end seam through the supervisor stanza (post-self-
    retire shape) — every Claude Code session after first-run still
    sees the loam-mode emit."""
    from loam_mode.session_start import build_loam_mode_inner_hook

    ws = tmp_path / "pos-v2"
    (ws / ".claude").mkdir(parents=True)
    settings_path = ws / ".claude" / "settings.json"

    loam_hook = build_loam_mode_inner_hook(ws)
    stanza = build_supervisor_stanza(ws, extra_inner_hooks=[loam_hook])
    merge_session_start(settings_path=settings_path, new_entry=stanza)

    data = json.loads(settings_path.read_text())
    inner = data["hooks"]["SessionStart"][0]["hooks"]
    assert len(inner) == 2
    assert "pos_session_start.py" in inner[0]["command"]
    assert "loam_mode.cli session-start" in inner[1]["command"]


def test_AC45_4_seam_command_uses_workspace_venv_python(tmp_path: Path) -> None:
    """B's emitter is invoked via the workspace venv's Python (per
    halt-finding-2 §4 + amendment #45 plan §1) — the command embeds
    ``<root>/.venv/bin/python``."""
    from loam_mode.session_start import build_loam_mode_inner_hook

    hook = build_loam_mode_inner_hook(tmp_path)
    expected_python = str(tmp_path / ".venv" / "bin" / "python")
    assert expected_python in hook["command"]
    assert "loam_mode.cli session-start" in hook["command"]
