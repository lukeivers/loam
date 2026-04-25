"""Sub-plan B — AC.B.S (companion to amendment #45's AC.45.S).

B's emitter + tests live under ``tools/loam-mode/`` per H19's
admitted ``tools`` bucket; no other dev-discipline scope is widened.

This is a sub-plan-B-side companion to the amendment-#45 seal-diff
test. Where AC.45.S asserts the cross-component diff window stays
inside hands-off-lifecycle/ + tools/loam-mode/ + plans/, AC.B.S
asserts the loam-mode side specifically.
"""

from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_AC_B_S_session_start_module_present() -> None:
    """B's emitter module exists at the agreed path."""
    p = (
        REPO_ROOT
        / "tools"
        / "loam-mode"
        / "src"
        / "loam_mode"
        / "session_start.py"
    )
    assert p.is_file(), (
        f"AC.B.S: session_start.py expected at {p}; the dev-discipline "
        "tools/loam-mode admission is the only loam-mode-side surface."
    )


def test_AC_B_S_no_sealed_component_imports_in_emitter() -> None:
    """B's emitter does NOT import from primary-persona, workspace-
    bootstrap, hands-off-lifecycle, or any other sealed component
    at module-import time. The dev-discipline §2 framing requires
    composition AROUND sealed code, not coupling INTO it.
    """
    p = (
        REPO_ROOT
        / "tools"
        / "loam-mode"
        / "src"
        / "loam_mode"
        / "session_start.py"
    )
    src = p.read_text(encoding="utf-8")
    forbidden = (
        "from primary_persona",
        "import primary_persona",
        "from workspace_bootstrap",
        "import workspace_bootstrap",
        "from objective_tracker",
        "import objective_tracker",
        # Hands-off-lifecycle is per-instance (the helper imports
        # FROM us, not vice versa).
        "from first_run_settings",
        "import first_run_settings",
    )
    for marker in forbidden:
        assert marker not in src, (
            f"AC.B.S: emitter must not couple into sealed components; "
            f"found {marker!r}"
        )


def test_AC_B_S_loam_mode_cli_session_start_subcommand_registered() -> None:
    """The ``loam-mode session-start`` CLI subcommand is registered
    (the seam hands-off-lifecycle's stanza builders compose against)."""
    from loam_mode.cli import build_parser

    parser = build_parser()
    # Inspect the subparsers for the session-start name.
    subparsers_actions = [
        a for a in parser._actions
        if a.__class__.__name__ == "_SubParsersAction"
    ]
    assert subparsers_actions, "CLI must expose subparsers"
    names = set(subparsers_actions[0].choices.keys())
    assert "session-start" in names
