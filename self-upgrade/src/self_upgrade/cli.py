"""D2 — External CLI: ``pos upgrade <tag>``.

The CLI runs as an **external process** from a staging directory. It
refuses to run from inside the live framework path — this is the
self-referential safety requirement: the orchestrator cannot upgrade
itself in-flight, so the CLI must be invoked from outside the live
tree.

Subcommands:

- ``pos upgrade <tag>``       — execute the full sequence
- ``pos upgrade <tag> --dry-run`` — print planned steps; no state change
- ``pos rollback <tag>``      — invoke explicit rollback
- ``pos status``              — current version, prior versions, last log

The CLI streams one line per stage. Each line ends with ``[ok <ms>ms]``
or ``[halt: <reason>]``. Non-TTY output is grep-friendly.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from .config import AutoUpdateMode, UpgradeConfig
from .conflict_detection import detect_conflicts
from .conflict_report import (
    ConflictReport,
    Resolution,
    load_conflict_report,
    save_conflict_report,
)
from .manifest import Manifest, load_manifest
from .notification import (
    ConfirmationDecision,
    notify_accepted,
    notify_and_apply_with_cancel_window,
    notify_rolled_back,
    notify_rollback_failed,
    notify_upgrade_available,
    wait_for_confirmation,
)
from .paths import Paths
from .upgrade import UpgradeResult, execute_upgrade


# ---- live-path safety check ----------------------------------------


def refuse_if_invoked_from_live_path(paths: Paths) -> str | None:
    """Return an error string if sys.executable is under current_link,
    else None.
    """
    try:
        live_real = paths.current_link.resolve()
    except (OSError, RuntimeError):
        return None
    try:
        exec_real = Path(sys.executable).resolve()
    except OSError:
        return None
    try:
        exec_real.relative_to(live_real)
    except ValueError:
        return None
    return (
        f"Refusing to run from inside the live framework path ({live_real}). "
        "Invoke from a staging directory instead (see operations docs)."
    )


# ---- dry-run renderer ----------------------------------------------


def dry_run_plan(manifest: Manifest, paths: Paths) -> list[str]:
    """Return human-readable lines describing what the upgrade would do.
    No side effects."""
    lines = [
        f"[dry-run] release_tag:       {manifest.release_tag}",
        f"[dry-run] commit_sha:        {manifest.commit_sha}",
        f"[dry-run] files in manifest: {len(manifest.files)}",
        f"[dry-run] component schemas: {len(manifest.component_schemas)}",
        f"[dry-run] breaking changes:  {len(manifest.breaking_changes)}",
        f"[dry-run] migrations:        {len(manifest.migrations)}",
        f"[dry-run] snapshot dir:      {paths.history_dir_pre(manifest.release_tag)}",
    ]
    silent = manifest.silent_schema_bumps()
    if silent:
        lines.append(
            f"[dry-run] WARNING: silent schema bumps detected: {silent} "
            "(upgrade will halt at clause e)"
        )
    if manifest.breaking_changes:
        lines.append("[dry-run] breaking changes to review:")
        for bc in manifest.breaking_changes:
            lines.append(f"  - {bc.id} ({bc.component}): {bc.description}")
    return lines


# ---- progress renderer ---------------------------------------------


def _stage_line(stage: str, verdict: str, elapsed_s: float) -> str:
    ms = elapsed_s * 1000
    if verdict == "ok":
        return f"  {stage:<22}[ok  {ms:>6.1f}ms]"
    return f"  {stage:<22}[{verdict}]"


# ---- main commands -------------------------------------------------


def cmd_upgrade(args: argparse.Namespace) -> int:
    paths = Paths.from_env(args.pos_base_dir)
    # Refuse if running from live path
    err = refuse_if_invoked_from_live_path(paths)
    if err:
        print(f"error: {err}", file=sys.stderr)
        return 2

    manifest = load_manifest(args.manifest)
    if manifest.release_tag != args.tag:
        print(
            f"error: manifest release_tag={manifest.release_tag!r} "
            f"disagrees with CLI tag={args.tag!r}",
            file=sys.stderr,
        )
        return 2

    config = UpgradeConfig.load_or_default(paths.upgrade_config)

    if args.dry_run:
        for line in dry_run_plan(manifest, paths):
            print(line)
        return 0

    # Conflict detection (structural clause-g enforcement)
    live_root = paths.current_link.resolve() if paths.current_link.exists() else paths.framework
    report = detect_conflicts(
        manifest, live_root, prior_tag=args.prior_tag
    )

    conflicts_yaml = paths.conflicts_yaml(manifest.release_tag)
    if args.conflicts_from and Path(args.conflicts_from).exists():
        report = load_conflict_report(args.conflicts_from)

    if report.has_abort():
        print("upgrade aborted via conflict report")
        return 0

    if report.has_pending():
        paths.history.mkdir(parents=True, exist_ok=True)
        save_conflict_report(report, conflicts_yaml)
        print(
            f"upgrade blocked: {len(report.unresolved_paths())} pending "
            "conflict(s). Resolve in:"
        )
        print(f"  {conflicts_yaml}")
        print(
            "  (resolution=skipped is structurally forbidden — "
            "choose accept-upstream, keep-local, three-way-merge, or abort.)"
        )
        return 3

    print(f"pos upgrade {manifest.release_tag}")

    def progress(stage: str, verdict: str, elapsed: float) -> None:
        print(_stage_line(stage, verdict, elapsed))

    # In production the CLI wires real adapters. For the dispatch
    # invocation Luke will run, adapters are supplied by the caller
    # via a pluggable module. Default here is the "not yet wired"
    # halt-and-signal, which surfaces cleanly to the user.
    if not args.adapters_module:
        print(
            "error: no adapters_module supplied. In production, wire the "
            "orchestrator IPC + memory harness + scope/objective upgrade "
            "surfaces here. See docs/cli-reference.md.",
            file=sys.stderr,
        )
        return 2

    adapters = _load_adapters(args.adapters_module)

    result = execute_upgrade(
        manifest=manifest,
        paths=paths,
        config=config,
        staging_dir=Path(args.staging_dir),
        prior_tag=args.prior_tag,
        adapters=adapters,
        progress=progress,
    )

    if result.accepted:
        print(f"upgrade accepted: {manifest.release_tag} "
              f"(total {result.duration_s:.1f}s)")
        print(f"report: {paths.accepted_json(manifest.release_tag)}")
        return 0

    # Rolled back or halted
    if result.rolled_back:
        print(f"upgrade rejected and rolled back: {result.halt_reason}")
        if result.rollback_success is False:
            print("ROLLBACK FAILED — manual recovery required")
            return 4
        return 1
    print(f"upgrade halted before swap: {result.halt_reason}")
    return 1


def cmd_rollback(args: argparse.Namespace) -> int:
    from .rollback import rollback, RollbackFailed

    paths = Paths.from_env(args.pos_base_dir)
    try:
        rollback(
            paths=paths,
            tag=args.tag,
            prior_tag=args.prior_tag,
            failing_clauses=[],
            clause_details={"invoked_via": "pos rollback"},
        )
        print(f"rollback complete for {args.tag}")
        return 0
    except RollbackFailed:
        print(f"ROLLBACK FAILED for {args.tag}", file=sys.stderr)
        return 4


def cmd_status(args: argparse.Namespace) -> int:
    paths = Paths.from_env(args.pos_base_dir)
    if paths.current_link.is_symlink():
        print(f"current: {paths.current_link.resolve()}")
    else:
        print("current: (no live link — framework not initialised)")
    if paths.history.exists():
        entries = sorted(paths.history.glob("*-accepted.json"))
        print(f"accepted releases: {len(entries)}")
        for e in entries[-5:]:
            print(f"  {e.stem}")
    return 0


# ---- adapter loader ------------------------------------------------


def _load_adapters(module_path: str) -> Any:
    """Import ``module_path:build_adapters`` and call it to get the
    adapter bundle."""
    import importlib

    module_name, _, attr = module_path.partition(":")
    attr = attr or "build_adapters"
    mod = importlib.import_module(module_name)
    factory = getattr(mod, attr)
    return factory()


# ---- main ----------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pos",
        description="pOS self-upgrade CLI — invoke from a staging directory.",
    )
    parser.add_argument(
        "--pos-base-dir",
        default=None,
        help="Override ~/.pos base dir (testing).",
    )
    sub = parser.add_subparsers(dest="command")

    # upgrade
    up = sub.add_parser("upgrade", help="Execute a release upgrade.")
    up.add_argument("tag", help="Release tag, e.g. pos-v2-v0.2.0")
    up.add_argument(
        "--manifest",
        required=True,
        help="Path to the release's pos-release.yml",
    )
    up.add_argument(
        "--staging-dir",
        required=True,
        help="Staging dir containing the unpacked new release tree",
    )
    up.add_argument(
        "--prior-tag",
        default=None,
        help="Tag of the previously-installed release (for rollback).",
    )
    up.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned steps; do not execute.",
    )
    up.add_argument(
        "--adapters-module",
        default=None,
        help=(
            "Import path for the live-adapter factory "
            "(format: 'pkg.mod' or 'pkg.mod:build_adapters')"
        ),
    )
    up.add_argument(
        "--conflicts-from",
        default=None,
        help="Path to an edited conflicts YAML to resume from.",
    )
    up.set_defaults(func=cmd_upgrade)

    # rollback
    rb = sub.add_parser("rollback", help="Roll back a release.")
    rb.add_argument("tag", help="Tag to roll back from.")
    rb.add_argument(
        "--prior-tag",
        default=None,
        help="Tag to roll back to.",
    )
    rb.set_defaults(func=cmd_rollback)

    # status
    st = sub.add_parser("status", help="Show current version and history.")
    st.set_defaults(func=cmd_status)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
