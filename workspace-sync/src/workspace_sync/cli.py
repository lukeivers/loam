"""External CLI: ``pos-sync`` (and ``pos-workspace-sync`` alias).

Authored fresh. The B-mode entry point: an operator runs ``pos-sync
--canonical <path>`` from a workspace clone and the framework pulls
canonical changes into the workspace under the three-class envelope.

Argparse:

  pos-sync --canonical <path>
           [--ref <commit-or-tag>]      default: HEAD
           [--workspace <path>]         default: cwd
           [--dry-run]                  print plan; no apply
           [--merge-resolver-module M]  factory; default
                                        workspace_sync._resolver_client
           [--budget-tokens N]          cumulative-ceiling override
           [--auto-accept]              opt-in fast-path past confirm
           [--confidence-floor F]       default 0.90 (BB D-2)

Workspace-root derivation (Hard Constraint #12, no symlink resolution):

  1. ``--workspace <path>`` if supplied AND a directory.
  2. Else ``Path.cwd()`` if it contains ``.pos/sync-protected.yaml``.
  3. Else ``Path.cwd()`` if it contains ``.git/`` (fresh first-run).
  4. Else: halt with structured argument-validation error naming
     both fall-through conditions (AC.WS.1).
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

from ._audit import confirmed_by_operator, summarize_audit_for_operator
from .canonical import (
    CanonicalPullError,
    resolve_canonical,
)
from .conflict_detection import detect_b_shape_conflicts
from .conflict_report import (
    ConflictReport,
    Resolution,
)
from .merge_helper import (
    check_inferred_resolution_invariants,
    resolve_inferred_conflicts,
)
from .merge_resolver import (
    BudgetExhausted,
    MergeResolver,
    ResolverBudget,
    ResolverFailure,
)
from .observability import span as otel_span
from .staging import (
    apply_staging_atomically,
    discard_staging,
    stage_canonical_clean_writes,
    stage_resolved_content,
    staging_root,
)
from .state import (
    SyncStatus,
    audit_yaml_path,
    load_state,
    make_state_record,
    save_state,
    state_yaml_path,
)
from .sync_protected import (
    SyncProtected,
    load_sync_protected,
    write_default_if_absent,
)


# ---- workspace-root derivation -------------------------------------


class WorkspaceRootError(Exception):
    """Raised when the CLI cannot derive a workspace root."""


def derive_workspace_root(
    *,
    workspace_arg: Path | None,
    cwd: Path | None = None,
) -> Path:
    """Per Hard Constraint #12.

    No symlink resolution. ``Path.cwd()`` (or ``cwd`` injected for
    tests) is the live root unless ``workspace_arg`` overrides.
    """
    cwd = cwd if cwd is not None else Path.cwd()

    if workspace_arg is not None:
        if not workspace_arg.exists() or not workspace_arg.is_dir():
            raise WorkspaceRootError(
                f"--workspace {workspace_arg} is not an existing directory"
            )
        return workspace_arg

    if (cwd / ".pos" / "sync-protected.yaml").exists():
        return cwd
    if (cwd / ".git").exists():
        return cwd

    raise WorkspaceRootError(
        f"workspace root not derivable from cwd={cwd}: neither "
        ".pos/sync-protected.yaml (existing workspace) nor .git/ "
        "(fresh first-run) is present. Pass --workspace <path> to "
        "specify explicitly."
    )


# ---- merge-resolver factory loading --------------------------------


def _load_merge_resolver(
    module_spec: str,
    *,
    budget: ResolverBudget | None = None,
) -> MergeResolver:
    """Load + invoke the merge-resolver factory at ``module_spec``.

    ``module_spec`` is ``pkg.mod`` (factory name defaults to
    ``build_merge_resolver``) or ``pkg.mod:factory_name``. The factory
    is invoked with ``budget=budget`` if it accepts the kwarg, else
    no-arg.
    """
    if ":" in module_spec:
        mod_name, factory_name = module_spec.split(":", 1)
    else:
        mod_name = module_spec
        factory_name = "build_merge_resolver"

    module = importlib.import_module(mod_name)
    factory = getattr(module, factory_name, None)
    if factory is None:
        raise ResolverFailure(
            f"merge-resolver module {mod_name} lacks factory "
            f"{factory_name!r}"
        )

    # Try invoking with budget kwarg; fall back to no-arg if the
    # factory does not accept it.
    try:
        resolver = factory(budget=budget)
    except TypeError:
        resolver = factory()

    if not isinstance(resolver, MergeResolver):
        raise ResolverFailure(
            f"merge-resolver factory returned {type(resolver).__name__}; "
            "expected MergeResolver"
        )
    return resolver


# ---- main flow ----------------------------------------------------


def _seed_default_envelope(workspace_root: Path) -> SyncProtected:
    """First-run seeding (AC.WS.10): write default sync-protected.yaml
    if absent; load + validate either way (framework-floor refusal is
    the structural enforcement)."""
    target = write_default_if_absent(workspace_root)
    return load_sync_protected(target)


def _ref_already_applied(
    workspace_root: Path, resolved_ref: str
) -> bool:
    """Idempotency fast-path (AC.WS.8).

    If state.yaml records the same sync_ref with status=SUCCESS, we
    can no-op. Conservatively: any other status means re-run. The
    workspace-perturbation-since-state-yaml case is not yet detected
    (would require per-path snapshotting); the resolver runs again
    and the helper's already-non-PENDING short-circuit handles
    convergence.
    """
    state = load_state(workspace_root)
    if state is None:
        return False
    return (
        state.sync_ref == resolved_ref
        and state.status is SyncStatus.SUCCESS
    )


def _execute_sync(
    *,
    canonical_root: Path,
    resolved_ref: str,
    workspace_root: Path,
    sync_protected: SyncProtected,
    resolver: MergeResolver,
    auto_accept: bool,
    confidence_floor: float,
    dry_run: bool,
) -> int:
    """Execute the full sync pipeline. Returns CLI exit code.

    Stage / detect / resolve / confirm / apply / discard fan-out.
    """
    # Detect (B-shape).
    prior_state = load_state(workspace_root)
    report, clean_writes = detect_b_shape_conflicts(
        canonical_path=canonical_root,
        ref=resolved_ref,
        workspace_root=workspace_root,
        sync_protected=sync_protected,
        prior_state=prior_state,
    )

    # Stage canonical-clean writes.
    staging_path = stage_canonical_clean_writes(
        canonical_path=canonical_root,
        ref=resolved_ref,
        workspace_root=workspace_root,
        paths_to_apply=clean_writes,
    )

    # Run the resolver pass over PENDING conflicts.
    halt_exception: Exception | None = None
    try:
        resolve_inferred_conflicts(
            report=report,
            sync_protected=sync_protected,
            canonical_root=canonical_root,
            workspace_root=workspace_root,
            resolver=resolver,
            write_merged=lambda p, c: _write_merged_to_staging(
                staging_path, p, c
            ),
            # Bundle α (#57) — pass the resolved canonical ref so
            # α.1 ancestor-detection can walk canonical's history
            # for each Class-C conflict.
            canonical_ref=resolved_ref,
        )
    except (BudgetExhausted, ResolverFailure) as exc:
        halt_exception = exc

    # Stage resolved content for INFERRED_ACCEPT_CANONICAL entries.
    if halt_exception is None:
        for entry in report.conflicts:
            if entry.resolution is Resolution.INFERRED_ACCEPT_CANONICAL:
                # Resolver said "accept canonical" — clean-writes path
                # already staged the canonical; do nothing extra.
                pass
            elif entry.resolution is Resolution.ACCEPT_UPSTREAM:
                # Class-B operator-prefers-canonical branch. Stage
                # canonical content explicitly.
                clean_writes.append(entry.path)

    # If we halted, fail closed: discard staging, audit + state are
    # already persisted by the helper's finally block.
    if halt_exception is not None:
        discard_staging(staging_path)
        print(
            f"[workspace-sync] halted: {type(halt_exception).__name__}: "
            f"{halt_exception}",
            file=sys.stderr,
        )
        print(
            f"[workspace-sync] audit:  {audit_yaml_path(workspace_root, resolved_ref)}",
            file=sys.stderr,
        )
        print(
            f"[workspace-sync] state:  {state_yaml_path(workspace_root)}",
            file=sys.stderr,
        )
        return 2

    # Verify invariants (AC.WS.5 + AC.WS.12 structural).
    passed, reason = check_inferred_resolution_invariants(report)
    if not passed:
        discard_staging(staging_path)
        print(
            f"[workspace-sync] invariant check failed: {reason}",
            file=sys.stderr,
        )
        return 2

    # Dry-run path.
    if dry_run:
        print(summarize_audit_for_operator(report))
        print(
            f"\n[workspace-sync] dry-run: staging at {staging_path} preserved "
            "for inspection; no apply.",
            file=sys.stderr,
        )
        return 0

    # Confirm-or-discard gate (AC.WS.7).
    summary = summarize_audit_for_operator(report)
    all_floor_met = all(
        c.confidence is None or c.confidence >= confidence_floor
        for c in report.conflicts
    )
    if confirmed_by_operator(
        summary,
        auto_accept=auto_accept,
        all_confidences_meet_floor=all_floor_met,
    ):
        apply_staging_atomically(staging_path, workspace_root)
        # Clean up staging post-apply.
        discard_staging(staging_path)

        # Persist a final SUCCESS state.yaml (the helper wrote a
        # PARTIAL/SUCCESS state earlier; we re-stamp on confirmed
        # apply so re-runs against the same ref short-circuit).
        final_state = make_state_record(
            sync_ref=resolved_ref,
            workspace_root=workspace_root,
            total_conflicts=len(report.conflicts),
            resolved_count=sum(
                1 for c in report.conflicts
                if c.resolution is not Resolution.PENDING
            ),
            deferred_count=sum(
                1 for c in report.conflicts
                if c.resolution is Resolution.PENDING
            ),
            cumulative_tokens_used=resolver.cumulative_used,
            status=SyncStatus.SUCCESS,
            halt_reason=None,
        )
        save_state(final_state, workspace_root)

        with otel_span(
            "pos.sync.applied",
            {
                "pos.sync.ref": resolved_ref,
                "pos.sync.conflict_count": len(report.conflicts),
            },
        ):
            pass
        print(f"[workspace-sync] applied: {resolved_ref}", file=sys.stderr)
        return 0
    else:
        discard_staging(staging_path)
        with otel_span(
            "pos.sync.discarded",
            {"pos.sync.ref": resolved_ref},
        ):
            pass
        print("[workspace-sync] discarded.", file=sys.stderr)
        return 0


def _write_merged_to_staging(
    staging_path: Path, rel_path: str, content: str
) -> str:
    """Helper: stage_resolved_content + return absolute path."""
    stage_resolved_content(staging_path, rel_path, content)
    return str(Path(staging_path) / rel_path)


# ---- argparse ------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pos-sync",
        description=(
            "pOS v2 workspace-sync — pull canonical changes into a "
            "workspace clone under the three-class envelope (A=preserve, "
            "B=operator-preference, C=LLM-resolved)."
        ),
    )
    parser.add_argument(
        "--canonical",
        required=True,
        type=Path,
        help="Local canonical git working tree to pull from.",
    )
    parser.add_argument(
        "--ref",
        default="HEAD",
        help="Commit, tag, or branch to pull (default: HEAD).",
    )
    parser.add_argument(
        "--workspace",
        default=None,
        type=Path,
        help="Workspace root; default: cwd (per Hard Constraint #12).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned operations + audit; no apply.",
    )
    parser.add_argument(
        "--merge-resolver-module",
        default="workspace_sync._resolver_client",
        help=(
            "Import path for the merge-resolver factory (format: "
            "'pkg.mod' or 'pkg.mod:build_merge_resolver'). Default "
            "uses workspace-sync's bundled claude-print client."
        ),
    )
    parser.add_argument(
        "--budget-tokens",
        type=int,
        default=None,
        help=(
            "Cumulative resolver budget override. Default 100_000 "
            "(BB D-1 / plan §11 D-2)."
        ),
    )
    parser.add_argument(
        "--auto-accept",
        action="store_true",
        help=(
            "Opt-in fast-path: apply without operator confirmation when "
            "every inferred verdict's confidence meets the floor "
            "(default 0.90)."
        ),
    )
    parser.add_argument(
        "--confidence-floor",
        type=float,
        default=0.90,
        help=(
            "Minimum confidence for --auto-accept (default 0.90 per "
            "BB D-2 lock)."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Workspace-root derivation (Hard Constraint #12).
    try:
        workspace_root = derive_workspace_root(workspace_arg=args.workspace)
    except WorkspaceRootError as exc:
        parser.error(str(exc))
        return 2  # unreachable; parser.error raises SystemExit(2)

    # Canonical resolution (AC.WS.1).
    try:
        canonical = resolve_canonical(
            args.canonical,
            ref=args.ref,
        )
    except CanonicalPullError as exc:
        print(f"[workspace-sync] {exc}", file=sys.stderr)
        return 2

    # Idempotency fast-path (AC.WS.8).
    if _ref_already_applied(workspace_root, canonical.ref):
        print(
            f"[workspace-sync] already applied at ref {canonical.ref}; no-op.",
            file=sys.stderr,
        )
        return 0

    # Default envelope seeding + load (AC.WS.10).
    try:
        sync_protected = _seed_default_envelope(workspace_root)
    except Exception as exc:
        print(
            f"[workspace-sync] sync-protected.yaml load failed: {exc}",
            file=sys.stderr,
        )
        return 2

    # Resolver factory.
    budget_override = (
        ResolverBudget(cumulative_token_budget=args.budget_tokens)
        if args.budget_tokens is not None
        else None
    )
    try:
        resolver = _load_merge_resolver(
            args.merge_resolver_module, budget=budget_override
        )
    except (ResolverFailure, ImportError) as exc:
        print(
            f"[workspace-sync] resolver factory load failed: {exc}",
            file=sys.stderr,
        )
        return 2

    with otel_span(
        "pos.sync.started",
        {
            "pos.sync.ref": canonical.ref,
            "pos.sync.canonical_path": str(canonical.canonical_path),
            "pos.sync.workspace_root": str(workspace_root),
            "pos.sync.dry_run": args.dry_run,
        },
    ):
        return _execute_sync(
            canonical_root=canonical.canonical_path,
            resolved_ref=canonical.ref,
            workspace_root=workspace_root,
            sync_protected=sync_protected,
            resolver=resolver,
            auto_accept=args.auto_accept,
            confidence_floor=args.confidence_floor,
            dry_run=args.dry_run,
        )


if __name__ == "__main__":
    sys.exit(main())
