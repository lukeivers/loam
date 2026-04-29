"""``loam-mode`` CLI entry point.

Subcommands:
  - ``audit`` — run the partition audit (AC.F5). Exit 0 if clean,
    non-zero with a diagnostic block otherwise.
  - ``select`` — print the selected corpus for a given mode (AC.F2
    debug helper). Not load-bearing for B's mechanism; B calls the
    Python API directly.
  - ``session-start`` — emit the SessionStart additionalContext
    payload for the current workspace's mode (AC.B3 + AC.B4).
    Always exits 0 (AC.B5 fail-soft).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from loam_mode.audit import audit_partition
from loam_mode.manifest import load_manifest
from loam_mode.selector import select_corpus
from loam_mode.session_start import cli_session_start


_DEFAULT_MANIFEST_REL = "docs/rebuild/dev-mode-manifest.yaml"


def _resolve_workspace(
    workspace: Path | None,
) -> Path:
    if workspace is not None:
        return workspace.resolve()
    return Path.cwd().resolve()


def _resolve_manifest(
    manifest: Path | None, workspace_root: Path
) -> Path:
    if manifest is not None:
        return manifest.resolve()
    return (workspace_root / _DEFAULT_MANIFEST_REL).resolve()


def _cmd_audit(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    manifest_path = _resolve_manifest(args.manifest, workspace_root)
    manifest = load_manifest(manifest_path)
    report = audit_partition(manifest, workspace_root)
    sys.stdout.write(report.format_diagnostic() + "\n")
    return 0 if report.is_clean else 1


def _cmd_select(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    manifest_path = _resolve_manifest(args.manifest, workspace_root)
    manifest = load_manifest(manifest_path)
    paths = select_corpus(manifest, workspace_root, args.mode)
    for p in paths:
        sys.stdout.write(p + "\n")
    return 0


def _cmd_session_start(args: argparse.Namespace) -> int:
    workspace_root = _resolve_workspace(args.workspace)
    return cli_session_start(workspace_root=workspace_root)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="loam-mode",
        description="loam dev-mode auto-load partition CLI.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_audit = sub.add_parser(
        "audit",
        help="Run the partition audit (AC.F5).",
    )
    p_audit.add_argument("--workspace", type=Path, default=None)
    p_audit.add_argument("--manifest", type=Path, default=None)
    p_audit.set_defaults(func=_cmd_audit)

    p_select = sub.add_parser(
        "select",
        help="Print the corpus for a given mode (AC.F2 helper).",
    )
    p_select.add_argument("--workspace", type=Path, default=None)
    p_select.add_argument("--manifest", type=Path, default=None)
    p_select.add_argument("mode", choices=["user", "dev"])
    p_select.set_defaults(func=_cmd_select)

    p_ss = sub.add_parser(
        "session-start",
        help=(
            "Emit the SessionStart additionalContext payload for the "
            "workspace's current mode (AC.B3 + AC.B4). Always exits 0 "
            "per AC.B5 fail-soft."
        ),
    )
    p_ss.add_argument("--workspace", type=Path, default=None)
    p_ss.set_defaults(func=_cmd_session_start)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
