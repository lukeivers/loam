"""Top-level dispatcher for the unified ``loam`` CLI.

Routes ``loam <subcommand> ...`` to the registered subcommand. The
namespace is reserved for ``loam amend``, ``loam scope``, ``loam
status``, ``loam plot``, and similar future subcommands.

Plugin-supplied subcommand discovery uses the entry-point group
``loam.cli.subcommands`` (symmetric to workspace-bootstrap's
``loam.bootstrap.contributions`` discovery pattern). Each registered
entry-point resolves to a callable
``build_<verb>_subcommand(sub: argparse._SubParsersAction) -> None``;
``main`` invokes each builder so plugins (e.g. dev-sdlc) can extend
the verb tree without amending this module.

The ``loam amend`` subcommand is itself shipped by the dev-sdlc
plugin at ``plugins/dev-sdlc/tools/loam-amend/`` and resolves through
the entry-point-group discovery loop (the plugin's pyproject ships
``[project.entry-points."loam.cli.subcommands"] amend =
"loam_amend.cli:build_amend_subcommand"``). The dispatcher itself
stays canonical (it remains the public binary entry point for the
harness); subcommand-packages live in their owning components.

The dispatcher uses argparse with one subparser group (no extra
dependency); each subcommand contributes its own argparse subparser
via an entry-point-resolved builder.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import logging
import sys
from typing import Any, Callable

from loam_cli import __version__


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

    # Plugin-supplied subcommands (entry-point group
    # ``loam.cli.subcommands``). ``amend`` itself flows through this
    # same discovery path — the package lives in the Dev/SDLC plugin.
    # Each builder is invoked with the parser-level subparsers handle
    # so the builder can add its own named subparser; everything flows
    # through this single discovery path.
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
    # All subcommands (including ``amend``) set ``args.func`` on each
    # leaf parser via ``set_defaults`` per the builder contract.
    # Dispatch via that callable when present.
    func = getattr(args, "func", None)
    if callable(func):
        return func(args)
    parser.error(f"unknown subcommand: {args.subcommand}")
    return 2  # unreachable


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
