"""AC.V060.1 — `loam release` CLI verb registers + dispatches.

Verifies that the `release` subcommand (a) appears under the unified
`loam` CLI's subparser choices via the `loam.cli.subcommands` entry-
point group, (b) parses `<version> [--dry-run] [--release]` correctly,
(c) routes to the runner via `args.func`. Per the dispatch-brief's
SPECIFIC-CLAIMS-VERIFIED rule, every claim about the CLI surface is
checked by an actual parser invocation rather than asserted.
"""

from __future__ import annotations

import argparse

import loam_cli.cli as cli_mod
from loam_cli.release.cli import build_release_subcommand, dispatch


def test_release_appears_in_top_level_loam_parser() -> None:
    """`loam release` is registered via the entry-point discovery
    loop; the parser's subparser choices include `release`."""
    parser = cli_mod._build_parser()
    sp = next(
        a for a in parser._actions
        if isinstance(a, argparse._SubParsersAction)
    )
    assert "release" in sp.choices, (
        "expected 'release' in loam top-level subparser choices; "
        "ensure the loam-cli package is editable-installed (the "
        "release entry-point is shipped by loam-cli's pyproject)"
    )


def test_release_help_includes_dry_run_and_release_flags() -> None:
    """`loam release --help` exposes both `--dry-run` and `--release`
    per the AC.V060.1 surface spec."""
    parser = cli_mod._build_parser()
    sp = next(
        a for a in parser._actions
        if isinstance(a, argparse._SubParsersAction)
    )
    release_parser = sp.choices["release"]
    flag_names = {
        opt
        for action in release_parser._actions
        for opt in getattr(action, "option_strings", [])
    }
    assert "--dry-run" in flag_names
    assert "--release" in flag_names


def test_release_parses_version_positional_and_flags() -> None:
    """A complete invocation `loam release v0.6.0 --dry-run --release`
    parses with `args.func == dispatch` + populated namespace."""
    parser = cli_mod._build_parser()
    args = parser.parse_args(
        ["release", "v0.6.0", "--dry-run", "--release"]
    )
    assert args.version == "v0.6.0"
    assert args.dry_run is True
    assert args.create_release is True
    assert callable(args.func)
    # The leaf-set func IS the release dispatcher.
    assert args.func is dispatch


def test_build_release_subcommand_attaches_named_subparser() -> None:
    """The builder, called directly with a synthetic `_SubParsersAction`,
    adds a `release` subparser. Smoke-test against an isolated parser
    so the test doesn't depend on plugin discovery."""
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="subcommand", required=True)
    build_release_subcommand(sub)
    sp = next(
        a for a in parser._actions
        if isinstance(a, argparse._SubParsersAction)
    )
    assert "release" in sp.choices
