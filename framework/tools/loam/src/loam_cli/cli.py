"""Top-level dispatcher for the unified ``loam`` CLI.

Routes ``loam <subcommand> ...`` to the registered subcommand. At M1g
sealing time the only registered subcommand is ``amend``; the
namespace below is reserved for future ``loam scope``, ``loam status``,
``loam plot``, etc. subcommands per ``loam-rename-decisions.md`` Tier-1
#6 ("subcommand under a unified ``loam`` top-level CLI — daily-driver
brand concentrator; future subcommands like ``loam scope new``,
``loam status`` live under the same umbrella").

At M6a, the dispatcher gains plugin-supplied subcommand discovery via
the NEW entry-point group ``loam.cli.subcommands`` (per
``docs/rebuild/plans/oss-v0-1-0-publish-dev-sdlc-plugin.md`` §10
D-build.M6.5; symmetric to workspace-bootstrap's
``loam.bootstrap.contributions`` discovery pattern). Each registered
entry-point resolves to a callable
``build_<verb>_subcommand(sub: argparse._SubParsersAction) -> None``;
``main`` invokes each builder so plugins (e.g. dev-sdlc) can extend
the verb tree without amending this module.

The dispatcher uses argparse with one subparser group (no extra
dependency); each subcommand contributes its own argparse subparser
via the subcommand package's ``cli`` module (built-in ``amend``) or
via an entry-point-resolved builder (plugin-shipped verbs).
"""

from __future__ import annotations

import argparse
import importlib.metadata
import logging
import sys
from typing import Any, Callable

from loam_cli import __version__
from loam_cli.amend import cli as amend_cli


_LOGGER = logging.getLogger(__name__)
_SUBCOMMAND_ENTRYPOINT_GROUP = "loam.cli.subcommands"


def _discover_subcommand_builders() -> (
    list[tuple[str, Callable[[argparse._SubParsersAction], None]]]
):
    """Return ``[(name, builder), ...]`` resolved from entry-points
    in group ``loam.cli.subcommands``.

    Each builder is a callable accepting an ``argparse._SubParsersAction``
    + responsible for adding its own subparser. Discovery is lazy
    (called once at parser-build time); installed-but-not-listed
    packages contribute simply by shipping the entry-point.

    Failure modes (entry-point load failure / not-callable result)
    are logged at WARNING and the offending entry-point is skipped —
    the unified CLI continues to serve built-in subcommands. Per
    plan §11 finding #2's mitigation: discovery failures must not
    break ``loam --version`` or ``loam amend ...``.
    """
    out: list[
        tuple[str, Callable[[argparse._SubParsersAction], None]]
    ] = []
    try:
        eps = importlib.metadata.entry_points(
            group=_SUBCOMMAND_ENTRYPOINT_GROUP
        )
    except Exception as exc:  # pragma: no cover — defensive
        _LOGGER.warning(
            "loam_cli: entry-point lookup failed for group %r: %s",
            _SUBCOMMAND_ENTRYPOINT_GROUP,
            exc,
        )
        return out
    for ep in eps:
        try:
            target: Any = ep.load()
        except Exception as exc:
            _LOGGER.warning(
                "loam_cli: entry-point %r failed to load: %s",
                ep.name,
                exc,
            )
            continue
        if not callable(target):
            _LOGGER.warning(
                "loam_cli: entry-point %r resolved to non-callable %r",
                ep.name,
                type(target).__name__,
            )
            continue
        out.append((ep.name, target))
    return out


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

    # Plugin-supplied subcommands (M6a — entry-point group
    # ``loam.cli.subcommands``). Each builder is invoked with the
    # parser-level subparsers handle so the builder can add its own
    # named subparser. ``loam amend`` is the only built-in; everything
    # else flows through this discovery path.
    for _name, builder in _discover_subcommand_builders():
        try:
            builder(sub)
        except Exception as exc:  # pragma: no cover — defensive
            _LOGGER.warning(
                "loam_cli: subcommand builder %r raised: %s",
                _name,
                exc,
            )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.subcommand == "amend":
        # Delegate to the amend subcommand's own dispatcher.
        return amend_cli.dispatch(args)
    # Plugin-shipped subcommands set ``args.func`` on each leaf parser
    # via ``set_defaults`` (per the M6a builder contract). Dispatch
    # via that callable when present.
    func = getattr(args, "func", None)
    if callable(func):
        return func(args)
    parser.error(f"unknown subcommand: {args.subcommand}")
    return 2  # unreachable


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
