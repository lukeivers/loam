# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

from .canonical import (
    CanonicalPullError,
    StagingResolution,
    resolve_canonical_to_staging,
)
from .clause_checks import resolve_clause_h_inferred
from .config import AutoUpdateMode, UpgradeConfig
from .conflict_detection import detect_conflicts
from .conflict_report import (
    ConflictReport,
    Resolution,
    load_conflict_report,
    save_conflict_report,
)
from .manifest import Manifest, load_manifest
from .merge_resolver import (
    BudgetExhausted,
    MergeResolver,
    ResolverBudget,
    ResolverFailure,
)
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
from .state import audit_yaml_path, load_state
from .sync_protected import (
    SyncProtected,
    load_sync_protected,
    write_default_if_absent,
)
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

    # Canonical-as-source pull (clause-(h) AC.H.1). Resolve
    # canonical_path → (staging_dir, manifest). The argparse mutex
    # group already guarantees exactly one of --canonical / --staging-dir.
    canonical_resolution: StagingResolution | None = None
    if args.canonical:
        try:
            canonical_resolution = resolve_canonical_to_staging(
                Path(args.canonical),
                tag=args.tag,
                manifest_path=Path(args.manifest) if args.manifest else None,
            )
        except CanonicalPullError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        manifest = canonical_resolution.manifest
        staging_dir = canonical_resolution.staging_dir
    else:
        if not args.manifest:
            print(
                "error: --manifest is required when --staging-dir is used",
                file=sys.stderr,
            )
            return 2
        manifest = load_manifest(args.manifest)
        if manifest.release_tag != args.tag:
            print(
                f"error: manifest release_tag={manifest.release_tag!r} "
                f"disagrees with CLI tag={args.tag!r}",
                file=sys.stderr,
            )
            return 2
        staging_dir = Path(args.staging_dir)

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

    # AC.HFX.3: audit lands at the workspace-local path
    # (`<workspace>/.pos/upgrade/<tag>/audit.yaml`) when invoked
    # via --canonical (clause-(h)-eligible mode); legacy
    # --staging-dir continues writing at the global
    # `~/.loam/framework/history/<tag>-conflicts.yaml` per Hard
    # Constraint 5 backward-compat.
    if canonical_resolution is not None:
        conflicts_yaml = audit_yaml_path(live_root, manifest.release_tag)
    else:
        conflicts_yaml = paths.conflicts_yaml(manifest.release_tag)

    # AC.HFX.2 auto-discovery: when --conflicts-from is not
    # supplied, look for a prior state.yaml at the workspace's
    # `.pos/upgrade/state.yaml`. If the prior state matches the
    # current tag and points at an existing audit.yaml, load that
    # audit as the starting report. The clause-(h) helper's
    # already-non-PENDING-skip branch makes the resolver call-count
    # zero on the second invocation.
    if args.conflicts_from and Path(args.conflicts_from).exists():
        report = load_conflict_report(args.conflicts_from)
    elif canonical_resolution is not None:
        prior = load_state(live_root)
        if (
            prior is not None
            and prior.upgrade_tag == manifest.release_tag
            and Path(prior.audit_path).exists()
        ):
            report = load_conflict_report(prior.audit_path)

    # Clause-(h) pre-stage hook — runs ONLY when --canonical mode is
    # active and an LLM merge resolver has been wired by the caller.
    # When inactive, the legacy conflict-resolution path is preserved
    # byte-identical (Hard Constraint #5 backward-compat).
    if canonical_resolution is not None and args.merge_resolver_module:
        try:
            resolver = _load_merge_resolver(args.merge_resolver_module)
            sp = _load_or_seed_sync_protected(live_root)
            resolve_clause_h_inferred(
                report=report,
                sync_protected=sp,
                canonical_root=canonical_resolution.staging_dir,
                workspace_root=live_root,
                resolver=resolver,
            )
        except BudgetExhausted as exc:
            paths.history.mkdir(parents=True, exist_ok=True)
            save_conflict_report(report, conflicts_yaml)
            print(
                f"upgrade halted: clause-(h) budget exhausted "
                f"({exc.used} >= {exc.ceiling}). Audit at:",
                file=sys.stderr,
            )
            print(f"  {conflicts_yaml}", file=sys.stderr)
            print(
                "  (raise the cumulative ceiling or hand-resolve the "
                "deferred conflicts.)",
                file=sys.stderr,
            )
            return 3
        except ResolverFailure as exc:
            paths.history.mkdir(parents=True, exist_ok=True)
            save_conflict_report(report, conflicts_yaml)
            print(
                f"upgrade halted: clause-(h) resolver failure: {exc}",
                file=sys.stderr,
            )
            print(f"  audit at: {conflicts_yaml}", file=sys.stderr)
            return 3

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
        staging_dir=staging_dir,
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


def _load_merge_resolver(module_path: str) -> MergeResolver:
    """Import ``module_path:build_merge_resolver`` and call it.

    Returns a ``MergeResolver`` instance — the caller wires its LLM
    client + budget at construction time. Used by the clause-(h)
    pre-stage hook.
    """
    import importlib

    module_name, _, attr = module_path.partition(":")
    attr = attr or "build_merge_resolver"
    mod = importlib.import_module(module_name)
    factory = getattr(mod, attr)
    resolver = factory()
    if not isinstance(resolver, MergeResolver):
        raise TypeError(
            f"{module_path}: factory must return MergeResolver, "
            f"got {type(resolver).__name__}"
        )
    return resolver


def _load_or_seed_sync_protected(workspace_root: Path) -> SyncProtected:
    """Return the workspace's sync-protected envelope, writing the
    default template if absent (clause-(h) AC.H.10 first-run path)."""
    target = write_default_if_absent(workspace_root)
    return load_sync_protected(target)


# ---- main ----------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pos",
        description="pOS self-upgrade CLI — invoke from a staging directory.",
    )
    parser.add_argument(
        "--pos-base-dir",
        default=None,
        help="Override ~/.loam base dir (testing).",
    )
    sub = parser.add_subparsers(dest="command")

    # upgrade
    up = sub.add_parser("upgrade", help="Execute a release upgrade.")
    up.add_argument("tag", help="Release tag, e.g. pos-v2-v0.2.0")
    up.add_argument(
        "--manifest",
        default=None,
        help=(
            "Path to the release's pos-release.yml. Required with "
            "--staging-dir; optional with --canonical (defaults to "
            "<canonical>/self-upgrade/manifests/<tag>.yaml)."
        ),
    )
    # Mutually-exclusive source group: --canonical (clause-(h) pull
    # from a local canonical git tree) OR --staging-dir (pre-unpacked
    # release tree). Exactly one must be supplied.
    src_group = up.add_mutually_exclusive_group(required=True)
    src_group.add_argument(
        "--staging-dir",
        default=None,
        help="Staging dir containing the unpacked new release tree.",
    )
    src_group.add_argument(
        "--canonical",
        default=None,
        help=(
            "Local canonical git working tree to pull the release from. "
            "Implies clause-(h) pre-stage merge resolution when paired "
            "with --merge-resolver-module."
        ),
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
        "--merge-resolver-module",
        default=None,
        help=(
            "Import path for the clause-(h) merge-resolver factory "
            "(format: 'pkg.mod' or 'pkg.mod:build_merge_resolver'). "
            "Activates clause-(h) pre-stage resolver pass when paired "
            "with --canonical."
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
