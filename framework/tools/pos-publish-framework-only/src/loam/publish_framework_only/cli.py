"""``pos-publish-framework-only`` console-script entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loam.publish_framework_only.synth import (
    SynthesisError,
    synthesise_framework_only,
)


# Default manifest location relative to the canonical repo root.
# Per AC.OSS-M2.5 + plan §10 D-build.M2.4: required parameter on
# ``synthesise_framework_only``; CLI defaults the value from the
# ``--repo`` argument so end-user CLI invocations don't change.
DEFAULT_MANIFEST_REL = (
    "framework/tools/pos-publish-framework-only/"
    "publish-mode-manifest.yaml"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pos-publish-framework-only",
        description=(
            "Synthesise the `framework-only` branch on canonical "
            "pos-v2 from a `pos-v2` commit. The synthesised branch's "
            "tree mirrors canonical's `framework/<comp>/` layout "
            "verbatim and carries top-level docs (CLAUDE.md, "
            "README.md, docs/, etc.) under the publish-mode "
            "partition manifest at "
            "framework/tools/pos-publish-framework-only/"
            "publish-mode-manifest.yaml. Workspaces produced by "
            "`pos-new-workspace --from <canonical>` clone this "
            "branch into `<workspace>/framework/<comp>/...` matching "
            "the documented install paths."
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
        "--manifest-path",
        type=Path,
        default=None,
        help=(
            "Path to the publish-mode partition manifest YAML "
            "(default: <repo>/" + DEFAULT_MANIFEST_REL + "). "
            "The manifest classifies every workspace path into "
            "public_only / dev_and_public / dev_only / "
            "excluded_from_publish; only public_only and "
            "dev_and_public ship in the synthetic tree."
        ),
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress the success summary line (errors still print).",
    )
    return parser


def _resolve_manifest_path(
    repo: Path, manifest_path: Path | None
) -> Path:
    """Default-resolve the manifest path against ``--repo``."""
    if manifest_path is not None:
        return manifest_path
    return repo / DEFAULT_MANIFEST_REL


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manifest_path = _resolve_manifest_path(args.repo, args.manifest_path)
    try:
        result = synthesise_framework_only(
            args.repo,
            manifest_path=manifest_path,
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
