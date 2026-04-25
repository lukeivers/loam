"""Command-line entry point for ``pos-amend``.

Subcommand surface (v1): ``validate``, ``apply`` (with ``--dry-run``),
``seal``. See the plan doc for rationale on the minimal surface.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pos_amend import __version__
from pos_amend.commands import apply as apply_cmd
from pos_amend.commands import seal as seal_cmd
from pos_amend.commands import validate as validate_cmd


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pos-amend",
        description="Amendment-dispatch tooling for pos-v2.",
    )
    parser.add_argument(
        "--version", action="version", version=f"pos-amend {__version__}"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="schema-lint a manifest")
    p_validate.add_argument("manifest", type=Path)

    p_apply = sub.add_parser(
        "apply", help="apply (or dry-run) a manifest to the tree"
    )
    p_apply.add_argument("manifest", type=Path)
    p_apply.add_argument(
        "--dry-run",
        action="store_true",
        help="simulate; report missing admissions without mutating",
    )

    p_seal = sub.add_parser(
        "seal",
        help=(
            "finalise an amendment cycle (advance sidecars + narrative, "
            "run touched + sweep tests, create deterministic seal commit, "
            "verify post-seal apply --dry-run)"
        ),
    )
    p_seal.add_argument("manifest", type=Path)
    p_seal.add_argument(
        "--no-finalize",
        action="store_true",
        help=(
            "preserve pre-extension behaviour: advance sidecars + "
            "append narrative only; do not stage, run tests, sweep, "
            "commit, or verify"
        ),
    )
    p_seal.add_argument(
        "--scoped-sweep",
        action="store_true",
        help=(
            "restrict cross-component sweep to manifest-listed "
            "components (default: sweep every sealed component in "
            "the workspace)"
        ),
    )
    p_seal.add_argument(
        "--plan-doc",
        type=Path,
        default=None,
        help=(
            "plan doc path; when set, append the deterministic "
            "`### Commit SHAs` subsection under §14 and create a "
            "`docs(plans): record amendment #N commit SHAs ...` "
            "follow-up commit (per AC.D-sa.7)"
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "validate":
        return validate_cmd.run(args.manifest)
    if args.command == "apply":
        return apply_cmd.run(args.manifest, dry_run=args.dry_run)
    if args.command == "seal":
        return seal_cmd.run(
            args.manifest,
            no_finalize=args.no_finalize,
            scoped_sweep=args.scoped_sweep,
            plan_doc=args.plan_doc,
        )
    parser.error(f"unknown command: {args.command}")
    return 2  # unreachable
