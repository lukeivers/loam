"""AC.SFR.3 — loam-mode session-start emitter falls through to
``<workspace>/framework/CLAUDE.dev.md`` when the workspace-root copy
is absent.

Single-framework restructure (amendment #67). After the restructure,
``pos-new-workspace --from <canonical>`` clones canonical's
``framework-only`` synthetic branch into ``<workspace>/framework/``;
the workspace's ``CLAUDE.dev.md`` lives at
``<workspace>/framework/CLAUDE.dev.md``. The emitter probes the
workspace-root path first (preserving today's behaviour for workspaces
that scaffold their own copy) and falls through to the framework
location when absent.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from loam_mode.session_start import emit_session_start_context


def _seed_dev_persona(workspace_root: Path) -> None:
    """Write a primary persona contract with ``dev_intent: yes`` so the
    emitter selects dev-mode.
    """
    persona_dir = workspace_root / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text(
        yaml.safe_dump(
            {
                "is_primary": True,
                "dev_intent": "yes",
                "handle": "primary",
            }
        )
    )


def test_emit_session_start_context_falls_through_to_framework(
    tmp_path: Path,
) -> None:
    """Workspace-root CLAUDE.dev.md absent + framework copy present →
    emitter returns the framework copy's content.
    """
    workspace_root = tmp_path
    _seed_dev_persona(workspace_root)

    framework = workspace_root / "framework"
    framework.mkdir()
    (framework / "CLAUDE.dev.md").write_text(
        "# fixture dev extension from framework\n"
    )

    payload = emit_session_start_context(workspace_root)
    assert payload == "# fixture dev extension from framework\n"


def test_emit_session_start_context_prefers_workspace_root(
    tmp_path: Path,
) -> None:
    """When CLAUDE.dev.md exists at workspace root, the emitter uses
    it (and ignores any framework-side copy).
    """
    workspace_root = tmp_path
    _seed_dev_persona(workspace_root)

    (workspace_root / "CLAUDE.dev.md").write_text(
        "# fixture dev extension from workspace root\n"
    )
    framework = workspace_root / "framework"
    framework.mkdir()
    (framework / "CLAUDE.dev.md").write_text(
        "# fixture dev extension from framework (should not be returned)\n"
    )

    payload = emit_session_start_context(workspace_root)
    assert payload == "# fixture dev extension from workspace root\n"


def test_emit_session_start_context_diagnostic_when_neither_present(
    tmp_path: Path,
) -> None:
    """Dev mode with neither workspace-root nor framework copy → the
    emitter returns the fail-soft diagnostic line (AC.B5 carry-forward).
    """
    workspace_root = tmp_path
    _seed_dev_persona(workspace_root)

    payload = emit_session_start_context(workspace_root)
    assert payload.startswith("[loam-mode]")
    assert "CLAUDE.dev.md" in payload
    assert "unavailable" in payload


def test_emit_session_start_context_user_mode_returns_empty(
    tmp_path: Path,
) -> None:
    """User mode → empty payload (carry-forward of AC.B3); fall-through
    is irrelevant for the user-mode path.
    """
    workspace_root = tmp_path
    persona_dir = workspace_root / "workspace" / "personas" / "primary"
    persona_dir.mkdir(parents=True)
    (persona_dir / "contract.yaml").write_text(
        yaml.safe_dump(
            {"is_primary": True, "dev_intent": "no", "handle": "primary"}
        )
    )

    framework = workspace_root / "framework"
    framework.mkdir()
    (framework / "CLAUDE.dev.md").write_text(
        "# should not be returned in user mode\n"
    )

    payload = emit_session_start_context(workspace_root)
    assert payload == ""
