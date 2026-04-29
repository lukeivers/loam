"""``pos-publish-framework-only`` console-script entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loam.publish_framework_only.synth import (
    SynthesisError,
    synthesise_framework_only,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pos-publish-framework-only",
        description=(
            "Synthesise the `framework-only` branch on canonical pos-v2 "
            "from a `pos-v2` commit. The synthesised branch's tree "
            "promotes `framework/<entry>` to root + carries top-level "
            "docs (CLAUDE.md, CLAUDE.dev.md, README.md, docs/). "
            "Workspaces produced by `pos-new-workspace --from "
            "<canonical>` clone this branch, eliminating the "
            "`framework/framework/<comp>/` doubling failure class."
        ),
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=Path.cwd(),
        help=(
            "Path to canonical pos-v2 (default: cwd). Must be a git "
            "working tree or bare repo."
        ),
    )
    parser.add_argument(
        "--source",
        default="HEAD",
        help=(
            "Source ref/SHA to synthesise from (default: HEAD). "
            "Typically `pos-v2` or a specific commit SHA."
        ),
    )
    parser.add_argument(
        "--target-ref",
        default="refs/heads/framework-only",
        help=(
            "Fully-qualified ref to advance (default: "
            "refs/heads/framework-only)."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the success summary line (errors still print).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = synthesise_framework_only(
            args.repo,
            source=args.source,
            target_ref=args.target_ref,
        )
    except SynthesisError as exc:
        print(f"[pos-publish-framework-only] {exc}", file=sys.stderr)
        return 1
    if not args.quiet:
        if result.no_op:
            print(
                f"[pos-publish-framework-only] no-op: "
                f"{result.target_ref} already at "
                f"{result.framework_only_sha[:7]} "
                f"(source: {result.source_sha[:7]})",
                file=sys.stderr,
            )
        else:
            print(
                f"[pos-publish-framework-only] advanced "
                f"{result.target_ref} → "
                f"{result.framework_only_sha[:7]} "
                f"(source: {result.source_sha[:7]})",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())
