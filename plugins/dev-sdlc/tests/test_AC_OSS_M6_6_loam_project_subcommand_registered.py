"""AC.OSS-M6.6 — `loam project ...` registered as subcommand of
unified `loam` CLI (plugin-side coverage).

This file covers the plugin's side of the AC: the subcommand
builder is reachable + registers the five verbs. The
`loam_cli`-side coverage (entry-point-group resolution path)
lives in `framework/tools/loam/tests/test_AC_OSS_M6_6_loam_cli_subcommand_discovery.py`.
"""

from __future__ import annotations

import argparse
import importlib.metadata
from pathlib import Path

from loam.plugins.dev_sdlc.cli import build_project_subcommand


def test_subcommand_builder_registered_via_entry_point() -> None:
    eps = importlib.metadata.entry_points(
        group="loam.cli.subcommands"
    )
    matches = [ep for ep in eps if ep.name == "project"]
    assert matches, (
        "expected entry-point 'project' in group "
        "'loam.cli.subcommands'"
    )
    target = matches[0].load()
    assert target is build_project_subcommand


def test_build_project_subcommand_registers_five_verbs() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    build_project_subcommand(sub)
    # Render help and assert each verb mentioned.
    rendered = parser.format_help()
    assert "project" in rendered

    args = parser.parse_args(["project", "--help"]) if False else None
    # Inspect `_subparsers_action`'s choices.
    sp_action = next(
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    )
    project_parser = sp_action.choices["project"]
    project_sub = next(
        a
        for a in project_parser._actions
        if isinstance(a, argparse._SubParsersAction)
    )
    assert set(project_sub.choices.keys()) == {
        "new",
        "status",
        "advance",
        "list",
        "gate",
    }


def test_loam_project_new_creates_project(tmp_path: Path) -> None:
    """End-to-end: `loam project new` (parsed via argparse, dispatched
    via the registered builder) creates a project directory."""
    parser = argparse.ArgumentParser(prog="loam")
    sub = parser.add_subparsers(dest="cmd", required=True)
    build_project_subcommand(sub)
    args = parser.parse_args(
        [
            "project",
            "new",
            "test-proj",
            "--workspace-root",
            str(tmp_path),
        ]
    )
    rc = args.func(args)
    assert rc == 0
    assert (tmp_path / "projects" / "test-proj").is_dir()
