"""Amendment #45 — AC.45.2.

``build_first_run_stanza`` emits a multi-inner-hook envelope when
``extra_inner_hooks`` is supplied. The first-run shim is the FIRST
inner hook (preserving its self-retire path); the loam-mode-selector
inner hook is the SECOND (and remains across self-retire — i.e.
``build_supervisor_stanza`` also receives it; AC.45.3 covers that).

Both invoke at SessionStart per Claude Code's hook fan-out semantics
on the inner ``hooks: [...]`` array.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import build_first_run_stanza  # noqa: E402


def test_AC45_2_first_run_stanza_default_single_inner(tmp_path: Path) -> None:
    """No extras supplied → single inner hook (first-run.sh).
    Backwards-compat preserved."""
    stanza = build_first_run_stanza(tmp_path)
    assert stanza["matcher"] == ""
    assert isinstance(stanza["hooks"], list)
    assert len(stanza["hooks"]) == 1
    assert stanza["hooks"][0]["command"].endswith("first-run.sh")
    # Existing shape contract preserved.
    assert stanza["hooks"][0]["type"] == "command"
    assert stanza["hooks"][0]["async"] is False
    assert stanza["hooks"][0]["timeout"] == 60


def test_AC45_2_first_run_stanza_first_inner_is_first_run_shim(
    tmp_path: Path,
) -> None:
    """When extras are supplied, the first-run shim remains FIRST so
    the self-retire path (which detects via ``inner[0]['command']``)
    keeps working."""
    extra = {
        "type": "command",
        "command": "/path/to/loam-mode-stub",
        "async": False,
        "timeout": 5,
    }
    stanza = build_first_run_stanza(tmp_path, extra_inner_hooks=[extra])
    assert len(stanza["hooks"]) == 2
    assert stanza["hooks"][0]["command"].endswith("first-run.sh")
    assert stanza["hooks"][1] == extra


def test_AC45_2_first_run_stanza_loam_mode_appended(tmp_path: Path) -> None:
    """The loam-mode session-start command (the canonical AC.45.2
    contributor) appears as the second inner hook."""
    from loam_mode.session_start import build_loam_mode_inner_hook

    loam_hook = build_loam_mode_inner_hook(tmp_path)
    stanza = build_first_run_stanza(tmp_path, extra_inner_hooks=[loam_hook])
    assert len(stanza["hooks"]) == 2
    assert stanza["hooks"][0]["command"].endswith("first-run.sh")
    assert "loam_mode.cli session-start" in stanza["hooks"][1]["command"]
    # Sub-second I/O — 5s timeout cap per AC.B5 + halt-finding-2 §3.
    assert stanza["hooks"][1]["timeout"] == 5
