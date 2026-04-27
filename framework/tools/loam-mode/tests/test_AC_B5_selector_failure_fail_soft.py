"""Sub-plan B — AC.B5.

Selector failure is fail-soft to user-mode.

If the selector raises (storage missing, YAML parse error, schema
mismatch), the SessionStart hook returns empty (user-mode) and
proceeds rather than blocking on selector error.

The exact OTel event-emission requirement from the original AC.B5
text was a method-prescription per
``feedback_loose_AC_text_fix_AC_not_implementation``; the load-
bearing OUTCOME is "session proceeds in user mode rather than
blocking". This test asserts the outcome shape; if a future
amendment adds an OTel emission it can extend this test.
"""

from __future__ import annotations

from pathlib import Path

from loam_mode.session_start import (
    cli_session_start,
    emit_session_start_context,
    read_dev_intent_safe,
)


def test_AC_B5_corrupt_contract_yaml_returns_absent(tmp_path: Path) -> None:
    """A malformed contract.yaml does NOT raise; ``read_dev_intent_safe``
    returns ``"absent"`` (user mode)."""
    (tmp_path / "personas" / "primary").mkdir(parents=True)
    (tmp_path / "personas" / "primary" / "contract.yaml").write_text(
        "::: this is not valid yaml :::\n[broken\n",
        encoding="utf-8",
    )
    # No exception.
    result = read_dev_intent_safe(tmp_path)
    assert result == "absent"


def test_AC_B5_missing_personas_dir_returns_absent(tmp_path: Path) -> None:
    """No personas directory at all → fail-soft to absent."""
    assert read_dev_intent_safe(tmp_path) == "absent"


def test_AC_B5_emit_returns_empty_on_corrupt_contract(tmp_path: Path) -> None:
    """``emit_session_start_context`` is fail-soft: corrupt
    contract.yaml + dev-extension on disk → still returns empty
    (user-mode default)."""
    (tmp_path / "personas" / "primary").mkdir(parents=True)
    (tmp_path / "personas" / "primary" / "contract.yaml").write_text(
        "::: broken yaml\n",
        encoding="utf-8",
    )
    (tmp_path / "CLAUDE.dev.md").write_text("dev content\n")
    payload = emit_session_start_context(tmp_path)
    assert payload == "", (
        "AC.B5: corrupt contract → fail-soft to user mode → empty "
        "payload (NOT raising; NOT leaking dev content)."
    )


def test_AC_B5_emit_returns_diagnostic_when_dev_extension_missing(
    tmp_path: Path,
) -> None:
    """Dev session, but ``CLAUDE.dev.md`` is missing → emitter
    returns a fail-soft diagnostic line rather than raising. Session
    proceeds; user-visible string explains what happened."""
    (tmp_path / "personas" / "primary").mkdir(parents=True)
    (tmp_path / "personas" / "primary" / "contract.yaml").write_text(
        "handle: primary\nis_primary: true\ndev_intent: yes\n",
        encoding="utf-8",
    )
    payload = emit_session_start_context(tmp_path)
    # Non-empty diagnostic line, not a raised exception.
    assert isinstance(payload, str)
    assert "loam-mode" in payload.lower() or "dev mode" in payload.lower()


def test_AC_B5_cli_returns_zero_on_every_path(
    tmp_path: Path,
    capsys,
) -> None:
    """The CLI subcommand returns 0 on every code path — a non-zero
    exit would block Claude Code's SessionStart fan-out, which AC.B5
    forbids."""
    # Path 1 — empty workspace.
    rc = cli_session_start(workspace_root=tmp_path)
    assert rc == 0

    # Path 2 — corrupt contract.
    (tmp_path / "personas" / "primary").mkdir(parents=True)
    (tmp_path / "personas" / "primary" / "contract.yaml").write_text(
        "::: broken yaml\n",
        encoding="utf-8",
    )
    rc = cli_session_start(workspace_root=tmp_path)
    assert rc == 0

    # Path 3 — dev workspace, dev-ext present.
    (tmp_path / "personas" / "primary" / "contract.yaml").write_text(
        "handle: primary\nis_primary: true\ndev_intent: yes\n",
        encoding="utf-8",
    )
    (tmp_path / "CLAUDE.dev.md").write_text("dev content\n")
    rc = cli_session_start(workspace_root=tmp_path)
    assert rc == 0
    out = capsys.readouterr().out
    assert "dev content" in out
