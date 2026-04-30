"""Sub-plan B — AC.B2.

When workspace-bootstrap's first-run scaffold runs, the resulting
``.claude/settings.json`` includes a SessionStart hook entry that
calls the loam-mode session-start command. The exact surface is the
builder's call (loam-mode session-start as the second inner hook of
the multi-contributor envelope amendment #45 generalises the stanza
to).

The seam being tested: ``build_loam_mode_inner_hook`` returns the
inner-hook dict that hands-off-lifecycle's stanza builders compose
into the SessionStart envelope.
"""

from __future__ import annotations

from pathlib import Path

from loam_mode.session_start import build_loam_mode_inner_hook


def test_AC_B2_inner_hook_targets_loam_mode_session_start(tmp_path: Path) -> None:
    """The inner hook's command invokes the loam-mode CLI's
    ``session-start`` subcommand under the workspace venv's Python."""
    hook = build_loam_mode_inner_hook(tmp_path)
    assert hook["type"] == "command"
    assert "loam_mode.cli session-start" in hook["command"]
    assert str(tmp_path / ".venv" / "bin" / "python") in hook["command"]


def test_AC_B2_inner_hook_synchronous_and_short_timeout(tmp_path: Path) -> None:
    """Per halt-finding-2 §4 sketch: ``async: false`` (additional
    context must be in stdout before Claude Code reads it) and
    ``timeout: 5`` (sub-second I/O; cap a hung filesystem)."""
    hook = build_loam_mode_inner_hook(tmp_path)
    assert hook["async"] is False
    assert hook["timeout"] == 5


def test_AC_B2_inner_hook_keys_match_claude_code_schema(tmp_path: Path) -> None:
    """Schema parity with hands-off-lifecycle's other stanza inner
    hooks: same keys, same types."""
    hook = build_loam_mode_inner_hook(tmp_path)
    assert set(hook.keys()) == {"type", "command", "async", "timeout"}
    assert isinstance(hook["command"], str)
    assert isinstance(hook["timeout"], int)


def test_AC_B2_inner_hook_composable_into_first_run_stanza(tmp_path: Path) -> None:
    """The seam: pass the loam-mode hook to
    ``build_first_run_stanza`` and confirm a 2-inner-hook envelope
    results. This is the AC.B2 outcome — SessionStart hook
    'installs' the selector."""
    import sys

    # Post-M6b.0: this test file is at
    # plugins/dev-sdlc/tools/loam-mode/tests/<name>.py (parents[5] = workspace).
    # Pre-M6b.0 it was at framework/tools/loam-mode/tests/ (parents[4] = workspace).
    WORKSPACE_ROOT = Path(__file__).resolve().parents[5]
    HOOKS_DIR = WORKSPACE_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
    sys.path.insert(0, str(HOOKS_DIR))
    from first_run_settings import build_first_run_stanza  # noqa: E402

    loam_hook = build_loam_mode_inner_hook(tmp_path)
    stanza = build_first_run_stanza(tmp_path, extra_inner_hooks=[loam_hook])
    inner = stanza["hooks"]
    assert len(inner) == 2
    assert inner[1] == loam_hook


def test_AC_B2_inner_hook_composable_into_supervisor_stanza(tmp_path: Path) -> None:
    """The post-self-retire seam: same inner hook composes into
    ``build_supervisor_stanza`` so every Claude Code session
    post-first-run runs loam-mode session-start."""
    import sys

    # Post-M6b.0: this test file is at
    # plugins/dev-sdlc/tools/loam-mode/tests/<name>.py (parents[5] = workspace).
    # Pre-M6b.0 it was at framework/tools/loam-mode/tests/ (parents[4] = workspace).
    WORKSPACE_ROOT = Path(__file__).resolve().parents[5]
    HOOKS_DIR = WORKSPACE_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
    sys.path.insert(0, str(HOOKS_DIR))
    from first_run_settings import build_supervisor_stanza  # noqa: E402

    loam_hook = build_loam_mode_inner_hook(tmp_path)
    stanza = build_supervisor_stanza(tmp_path, extra_inner_hooks=[loam_hook])
    inner = stanza["hooks"]
    assert len(inner) == 2
    assert "pos_session_start.py" in inner[0]["command"]
    assert inner[1] == loam_hook
