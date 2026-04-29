"""Top-level dispatcher for the unified ``loam`` CLI.

Routes ``loam <subcommand> ...`` to the registered subcommand. At M1g
sealing time the only registered subcommand is ``amend``; the
namespace below is reserved for future ``loam scope``, ``loam status``,
``loam plot``, etc. subcommands per ``loam-rename-decisions.md`` Tier-1
#6 ("subcommand under a unified ``loam`` top-level CLI — daily-driver
brand concentrator; future subcommands like ``loam scope new``,
``loam status`` live under the same umbrella").

The dispatcher uses argparse with one subparser group (no extra
dependency); each subcommand contributes its own argparse subparser
via the subcommand package's ``cli`` module.
"""

from __future__ import annotations

import argparse
import sys

from loam_cli import __version__
from loam_cli.amend import cli as amend_cli


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loam",
        description=(
            "loam — unified top-level CLI. The framework's daily-driver "
            "shell-surface; subcommand routing via argparse subparsers."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"loam {__version__}",
    )

    sub = parser.add_subparsers(dest="subcommand", required=True)

    # ``loam amend`` — amendment-dispatch tooling. Subcommand surface
    # (validate, apply, seal, template, new-plan) carried forward from
    # the pre-rename ``pos-amend`` CLI per M1g.
    amend_subparser = sub.add_parser(
        "amend",
        help=(
            "amendment-dispatch tooling: validate / apply / seal / "
            "template / new-plan"
        ),
        # Re-use the parser-build from the amend module so help-text +
        # argument layout match exactly the pre-rename ``pos-amend``
        # surface (per AC.RNM-1g.2 functional-equivalence outcome).
        # Approach: ``amend_cli.attach_subparsers(amend_subparser)``
        # populates the ``loam amend`` subparser with the same arg
        # surface ``pos-amend`` had at its top level.
        add_help=True,
    )
    # Populate the amend subparser with its own subcommands.
    amend_cli.attach_subparsers(amend_subparser)

    # Future subcommand registrations live below this line. Per Tier-1
    # #6: ``loam scope new``, ``loam status``, ``loam plot create``,
    # etc. compose against the same dispatcher umbrella.

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.subcommand == "amend":
        # Delegate to the amend subcommand's own dispatcher.
        return amend_cli.dispatch(args)
    parser.error(f"unknown subcommand: {args.subcommand}")
    return 2  # unreachable


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
