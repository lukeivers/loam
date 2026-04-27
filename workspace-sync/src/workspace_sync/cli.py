"""External CLI: ``pos-sync`` (and ``pos-workspace-sync`` alias).

Authored fresh. The B-mode entry point: an operator runs ``pos-sync``
(no flags from inside a configured workspace, post-#58 / β.1) or
``pos-sync --canonical <path>`` (the explicit form, byte-identical
to today) and the framework pulls canonical changes into the
workspace under the three-class envelope.

Argparse:

  pos-sync [--canonical <path-or-url>]   optional post-β.1; falls
                                         through to sync-config.yaml
           [--ref <commit-or-tag>]       default: HEAD
           [--workspace <path>]          default: cwd
           [--dry-run]                   print plan; no apply
           [--merge-resolver-module M]   factory; default
                                         workspace_sync._resolver_client
           [--budget-tokens N]           cumulative-ceiling override
           [--auto-accept]               opt-in fast-path past confirm
           [--confidence-floor F]        default 0.90 (BB D-2)

Workspace-root derivation (Hard Constraint #12, no symlink resolution):

  1. ``--workspace <path>`` if supplied AND a directory.
  2. Else ``Path.cwd()`` if it contains ``.pos/sync-protected.yaml``.
  3. Else ``Path.cwd()`` if it contains ``.git/`` (fresh first-run).
  4. Else: halt with structured argument-validation error naming
     both fall-through conditions (AC.WS.1).

Canonical-source resolution (β.1, AC.β.1):

  Precedence (highest → lowest):
  1. ``--canonical <path-or-url>`` CLI flag.
  2. ``<workspace>/.pos/sync-config.yaml``'s ``canonical_source:``.
  3. ``~/.pos/sync-config.yaml``'s ``canonical_source:``.
  4. Halt with structured error naming all three fall-through paths.

  When the resolved string is a URL (``http(s)://`` or ``git@``),
  ``ensure_cache_clone`` clones to ``~/.pos/canonical-cache/<repo-id>/``
  and runs ``git fetch --all --tags`` (always-fetch per D-β.1 LOCKED).
  When it is an absolute POSIX path, it is used directly (back-compat
  with #56's pos-sync invocation pattern).
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
from .canonical_cache import CanonicalCacheError, ensure_cache_clone
from .conflict_detection import detect_b_shape_conflicts
from .conflict_report import (
    ConflictReport,
    Resolution,
)
from .merge_helper import (
    check_inferred_resolution_invariants,
    resolve_inferred_conflicts,
    stage_canonical_at_ref,
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
from .sync_config import (
    canonical_source_kind,
    load_sync_config,
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

    # Stage resolved content for accept-canonical-flavored verdicts.
    # α-hotfix-2 #60 (Bug A + Bug B): the merge_helper NN branches
    # stage their own content (α-hotfix #59), but the LLM-resolver
    # INFERRED_ACCEPT_CANONICAL path and the Class-B ACCEPT_UPSTREAM
    # path don't — close them here using the centralized
    # stage_canonical_at_ref primitive (renamed + made public from
    # merge_helper's _stage_canonical_for_nn_match).
    #
    # Pre-α-hotfix-2: Bug A read `pass` (the comment "do nothing
    # extra" was wrong — clean_writes contains only conflict-detector
    # canonical-clean writes, NOT paths the resolver later resolved
    # as accept-canonical). Bug B did `clean_writes.append(...)`
    # AFTER stage_canonical_clean_writes had already run, so the
    # append was a no-op.
    if halt_exception is None:
        for entry in report.conflicts:
            if (
                entry.resolution is Resolution.INFERRED_ACCEPT_CANONICAL
                and entry.resolved_content_path is None
            ):
                # LLM-resolver returned accept-canonical (NOT via NN
                # fast-path — those entries already populated
                # resolved_content_path in #59). Stage canonical's
                # HEAD content now.
                staged = stage_canonical_at_ref(
                    entry=entry,
                    canonical_root=canonical_root,
                    canonical_ref=resolved_ref,
                    workspace_root=workspace_root,
                    sync_ref=resolved_ref,
                    write_merged=lambda p, c: _write_merged_to_staging(
                        staging_path, p, c
                    ),
                )
                if not staged:
                    # cli.py runs AFTER the resolver helper — there
                    # is no fallback. Failing closed (discard +
                    # exit 2) is correct; the alternative is re-
                    # introducing the verdict-without-stage bug on
                    # the very path this primitive is meant to close.
                    discard_staging(staging_path)
                    print(
                        f"[workspace-sync] failed to stage canonical "
                        f"content for {entry.path} "
                        f"(binary or unreadable at "
                        f"{resolved_ref}); halting.",
                        file=sys.stderr,
                    )
                    return 2
            elif entry.resolution is Resolution.ACCEPT_UPSTREAM:
                # Class-B operator-prefers-canonical branch. Stage
                # canonical's HEAD content explicitly. Pre-α-hotfix-2
                # this branch did clean_writes.append AFTER
                # stage_canonical_clean_writes had already run — a
                # no-op that left the workspace file untouched.
                staged = stage_canonical_at_ref(
                    entry=entry,
                    canonical_root=canonical_root,
                    canonical_ref=resolved_ref,
                    workspace_root=workspace_root,
                    sync_ref=resolved_ref,
                    write_merged=lambda p, c: _write_merged_to_staging(
                        staging_path, p, c
                    ),
                )
                if not staged:
                    discard_staging(staging_path)
                    print(
                        f"[workspace-sync] failed to stage canonical "
                        f"content for Class-B path {entry.path} "
                        f"(binary or unreadable at "
                        f"{resolved_ref}); halting.",
                        file=sys.stderr,
                    )
                    return 2

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
        required=False,
        default=None,
        type=str,
        help=(
            "Canonical source: an absolute path to a local git working "
            "tree, an http(s) URL, or a git@-style SSH spec. Optional "
            "post-β.1: when absent, pos-sync reads canonical_source from "
            "<workspace>/.pos/sync-config.yaml or ~/.pos/sync-config.yaml. "
            "When passed, the CLI flag overrides the config-file value."
        ),
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

    # β.1 (AC.β.1): canonical-source precedence chain.
    #   CLI flag > workspace-local sync-config.yaml > ~/-rooted > halt.
    try:
        sync_cfg = load_sync_config(workspace_root)
    except Exception as exc:
        print(
            f"[workspace-sync] sync-config.yaml load failed: {exc}",
            file=sys.stderr,
        )
        return 2

    canonical_source_str = (
        args.canonical
        if args.canonical is not None
        else sync_cfg.canonical_source
    )
    if canonical_source_str is None:
        parser.error(
            "no canonical source: pass --canonical <path-or-url>, OR "
            "set canonical_source: in <workspace>/.pos/sync-config.yaml, "
            "OR set canonical_source: in ~/.pos/sync-config.yaml"
        )
        return 2  # unreachable; parser.error raises SystemExit(2)

    # β.1 (D-β.1 LOCKED): URL-vs-local-path discrimination.
    try:
        kind = canonical_source_kind(canonical_source_str)
    except ValueError as exc:
        print(f"[workspace-sync] {exc}", file=sys.stderr)
        return 2

    if kind == "url":
        try:
            canonical_input_path = ensure_cache_clone(
                canonical_source_str, ref=args.ref
            )
        except CanonicalCacheError as exc:
            print(
                f"[workspace-sync] canonical cache failed: {exc}",
                file=sys.stderr,
            )
            return 2
    else:  # "local"
        canonical_input_path = Path(canonical_source_str)

    # Canonical resolution (AC.WS.1).
    try:
        canonical = resolve_canonical(
            canonical_input_path,
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

    # Resolver factory. β.1 (HALT-FOUND #2 closure): the
    # ``_resolver_client.py:292`` docstring promised file-tunable
    # budgets; β.1 wires the precedence chain.
    #   CLI flag (--budget-tokens) > workspace-local file
    #     > ~/-rooted file > ResolverBudget defaults.
    if args.budget_tokens is not None:
        budget_override = ResolverBudget(
            cumulative_token_budget=args.budget_tokens
        )
    elif (
        sync_cfg.cumulative_token_budget is not None
        or sync_cfg.per_conflict_token_budget is not None
    ):
        budget_kwargs: dict[str, int] = {}
        if sync_cfg.cumulative_token_budget is not None:
            budget_kwargs["cumulative_token_budget"] = (
                sync_cfg.cumulative_token_budget
            )
        if sync_cfg.per_conflict_token_budget is not None:
            budget_kwargs["per_conflict_token_budget"] = (
                sync_cfg.per_conflict_token_budget
            )
        budget_override = ResolverBudget(**budget_kwargs)
    else:
        budget_override = None
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
