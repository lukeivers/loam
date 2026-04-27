"""Sub-plan B — AC.B3.

Dev-mode CLAUDE.md fragment is loaded only in dev sessions.

Two CLAUDE.md surfaces exist:
  - The base CLAUDE.md (always loaded by Claude Code per its built-in
    behaviour).
  - A dev-extension surface (``CLAUDE.dev.md``) that auto-loads only
    when the selector returns ``"dev"``.

The dev-extension surface is loaded via the SessionStart hook's
output (the loam-mode emit) in ``"dev"`` sessions and is silently
absent in ``"user"`` sessions.
"""

from __future__ import annotations

from pathlib import Path

from loam_mode.session_start import emit_session_start_context


def _scaffold_workspace(tmp_path: Path, dev_intent: str | None) -> Path:
    """Build a fixture workspace with the given dev_intent answer."""
    ws = tmp_path / "ws"
    (ws / "personas" / "primary").mkdir(parents=True)
    contract_lines = ["handle: primary", "is_primary: true"]
    if dev_intent is not None:
        contract_lines.append(f"dev_intent: {dev_intent}")
    (ws / "personas" / "primary" / "contract.yaml").write_text(
        "\n".join(contract_lines) + "\n",
        encoding="utf-8",
    )
    return ws


def test_AC_B3_dev_extension_loaded_in_dev_session(tmp_path: Path) -> None:
    """dev_intent=yes → emitter returns the dev-extension content."""
    ws = _scaffold_workspace(tmp_path, "yes")
    (ws / "CLAUDE.dev.md").write_text(
        "# DEV MODE corpus\nload-bearing dev content here.\n",
        encoding="utf-8",
    )
    payload = emit_session_start_context(ws)
    assert "DEV MODE corpus" in payload
    assert "load-bearing dev content" in payload


def test_AC_B3_dev_extension_silent_in_user_session(tmp_path: Path) -> None:
    """dev_intent=no → emitter returns empty string (CLAUDE.dev.md
    content does NOT leak to user sessions even if the file exists)."""
    ws = _scaffold_workspace(tmp_path, "no")
    (ws / "CLAUDE.dev.md").write_text(
        "# DEV MODE corpus\nshould-not-appear-in-user-session\n",
        encoding="utf-8",
    )
    payload = emit_session_start_context(ws)
    assert payload == ""


def test_AC_B3_dev_extension_silent_when_dev_intent_absent(tmp_path: Path) -> None:
    """dev_intent absent → user mode (per locked owner ruling
    D-MASTER.4) → empty payload."""
    ws = _scaffold_workspace(tmp_path, None)
    (ws / "CLAUDE.dev.md").write_text(
        "should-not-appear-when-intent-absent\n",
        encoding="utf-8",
    )
    payload = emit_session_start_context(ws)
    assert payload == ""


def test_AC_B3_dev_extension_filename_configurable(tmp_path: Path) -> None:
    """``dev_extension_filename`` parameter lets callers point at a
    different fragment file. Production calls leave it default
    (``CLAUDE.dev.md``); tests can substitute alternate fixtures."""
    ws = _scaffold_workspace(tmp_path, "yes")
    (ws / "alt-extension.md").write_text(
        "alt-extension-marker\n", encoding="utf-8"
    )
    payload = emit_session_start_context(
        ws, dev_extension_filename="alt-extension.md"
    )
    assert "alt-extension-marker" in payload
