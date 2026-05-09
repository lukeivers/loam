"""``loam release <version>`` argparse builder + dispatcher (AC.V060.1).

Registered with the unified ``loam`` CLI dispatcher's
``loam.cli.subcommands`` entry-point group via the ``loam-cli``
package's pyproject (sibling to the dev-sdlc plugin's ``amend``
adapter). Per the M6a builder contract, :func:`build_release_subcommand`
accepts an :class:`argparse._SubParsersAction` + adds a ``release``
parser that wires :func:`dispatch` as ``args.func``.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from loam_cli.release import runner


def build_release_subcommand(
    sub: argparse._SubParsersAction,
) -> None:
    """Register the ``release`` subcommand on *sub*.

    Per AC.V060.1 the surface is::

        loam release <version> [--dry-run] [--release]

    Where ``<version>`` is the literal tag name (e.g., ``v0.6.0``);
    ``--dry-run`` runs every gate + reports without acting; and
    ``--release`` adds ``gh release create`` to the publish action.
    """
    p = sub.add_parser(
        "release",
        help=(
            "publish a sealed version: pre-publish gates + tag + push "
            "+ optional GitHub Release + post-ship review"
        ),
        description=(
            "Concrete release process for the loam framework. "
            "Verifies pre-publish gates (HARD smoke GREEN, ACs "
            "verified, STATE.md updated, clean tree, branch == main, "
            "seal commit reachable from HEAD), creates the annotated "
            "tag at the seal commit, pushes branch + tag to the "
            "origin remote, optionally creates the GitHub Release "
            "with auto-generated notes, then surfaces a post-ship "
            "review block naming the next scope."
        ),
    )
    p.add_argument(
        "version",
        help=(
            "the version literal to publish (matches the tag name; "
            "e.g., 'v0.6.0')"
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "run every pre-publish gate + report verdicts without "
            "creating the tag, pushing, or invoking gh"
        ),
    )
    p.add_argument(
        "--release",
        dest="create_release",
        action="store_true",
        help=(
            "after tag + push, create a GitHub Release with "
            "auto-generated notes via gh release create"
        ),
    )
    p.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help=(
            "repository root override (default: cwd). Tests use this "
            "to point at a temporary fixture; production invocations "
            "are expected to run from the canonical loam repo."
        ),
    )
    p.set_defaults(func=dispatch)


def dispatch(args: argparse.Namespace) -> int:
    """Run the matched ``loam release`` invocation.

    Returns the exit code from :func:`runner.run`. Tests can either
    call this directly with a synthetic ``argparse.Namespace`` or
    drive the full ``loam release`` parser surface.
    """
    repo_root = (args.repo_root or Path.cwd()).resolve()
    outcome = runner.run(
        repo_root,
        args.version,
        dry_run=args.dry_run,
        create_release=args.create_release,
    )
    return outcome.rc
