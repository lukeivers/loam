"""AC46.5 (part 1) — ``build_first_run_stanza`` carries the persona's
SessionStart inner hook in the composed envelope.

Outcome (per umbrella plan §4a + builder plan §3 D-build.6): when the
stanza builder is invoked with ``extra_inner_hooks`` carrying the
persona inner-hook entry first and the loam-mode inner-hook entry
second, the resulting envelope's ``hooks`` array is:

    [first-run.sh, persona session-start, loam-mode session-start]

ordering: probe → persona → loam-mode.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
sys.path.insert(0, str(HOOKS_DIR))

from first_run_settings import build_first_run_stanza  # noqa: E402


def _persona_inner_hook_stub(loam_root: Path) -> dict:
    """Stand-in for the persona's inner hook so this test does not
    require primary_persona to be importable in the test venv. The
    stanza builder doesn't care about the dict's contents — it
    composes the structure mechanically."""
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


def test_AC46_5_first_run_stanza_carries_persona_inner_hook(
    tmp_path: Path,
) -> None:
    """When extra_inner_hooks carries [persona, loam-mode], the
    resulting envelope has three inner hooks in the order
    [first-run.sh, persona, loam-mode]."""
    extras = [
        _persona_inner_hook_stub(tmp_path),
        _loam_mode_inner_hook_stub(tmp_path),
    ]
    stanza = build_first_run_stanza(tmp_path, extra_inner_hooks=extras)
    inner = stanza["hooks"]
    assert len(inner) == 3
    assert inner[0]["command"].endswith("first-run.sh")
    assert "primary_persona.cli session-start" in inner[1]["command"]
    assert "loam_mode.cli session-start" in inner[2]["command"]


def test_AC46_5_first_run_stanza_persona_inner_hook_timeout_5s(
    tmp_path: Path,
) -> None:
    """Persona inner hook respects 5s timeout (matches loam-mode
    precedent + builder plan D-build.7)."""
    extras = [_persona_inner_hook_stub(tmp_path)]
    stanza = build_first_run_stanza(tmp_path, extra_inner_hooks=extras)
    persona_hook = stanza["hooks"][1]
    assert persona_hook["timeout"] == 5
    assert persona_hook["async"] is False
