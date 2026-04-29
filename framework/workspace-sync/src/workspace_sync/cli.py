"""External CLI: ``pos-sync`` (and ``pos-workspace-sync`` alias).

D-migration D.3 (amendment #64) — git-merge architecture. The pre-D.3
bespoke resolve→stage→apply pipeline retired ~2400 LOC of source. The
new flow is a thin wrapper around git's mature merge tooling:

  1. Resolve canonical_source (URL → cache clone via
     ``ensure_cache_clone``; absolute path → use directly).
  2. Verify ``<workspace>/framework/`` is a git working tree.
  3. Configure (idempotently) the ``canonical`` remote in
     ``<workspace>/framework/.git/config``.
  4. ``git -C <ws>/framework fetch canonical``.
  5. Idempotency fast-path: if local ``HEAD`` already equals
     ``FETCH_HEAD``, exit 0 with outcome ``up-to-date``.
  6. ``git -C <ws>/framework merge --ff-only FETCH_HEAD`` —
     succeeds for ~all syncs (the workspace's framework is
     strictly behind canonical); record state + exit 0.
  7. On non-FF: ``git -C <ws>/framework merge FETCH_HEAD`` (no
     ``--ff-only``); on remaining unresolved conflicts, hand off
     each conflicted path to the existing ``MergeResolver``
     (LLM-mediated fallback); apply via ``git add`` + ``git
     commit -m '<resolver-summary>'``.

HC#6 structural promise: every git operation runs with ``-C
<workspace>/framework``. Files outside ``framework/`` are
structurally unreachable.

Argparse:

  pos-sync [--canonical <path-or-url>]   optional; falls through to
                                         <workspace>/workspace/.pos/
                                         sync-config.yaml or
                                         ~/.loam/sync-config.yaml.
           [--ref <commit-or-branch>]    default: <remote>/HEAD
           [--workspace <path>]          default: cwd
           [--merge-resolver-module M]   factory; default
                                         workspace_sync._resolver_client
           [--budget-tokens N]           cumulative-ceiling override
           [--auto-accept]               skip TTY confirm on fallback path
           [--confidence-floor F]        default 0.90 (BB D-2)

Workspace-root derivation:

  1. ``--workspace <path>`` if supplied AND a directory.
  2. Else ``Path.cwd()`` if it contains ``workspace/.pos/sync-protected.yaml``.
  3. Else ``Path.cwd()`` if it contains ``framework/.git/`` (post-D
     workspace).
  4. Else ``Path.cwd()`` if it contains ``.pos/sync-protected.yaml``
     (pre-D.2 back-compat).
  5. Else ``Path.cwd()`` if it contains ``.git/`` (fresh first-run).
  6. Else: halt with structured error.

Canonical-source resolution (β.1, AC.β.1):

  Precedence (highest → lowest):
  1. ``--canonical <path-or-url>`` CLI flag.
  2. ``<workspace>/workspace/.pos/sync-config.yaml``'s ``canonical_source:``.
  3. ``~/.loam/sync-config.yaml``'s ``canonical_source:``.
  4. Halt with structured error naming all three paths.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from ._audit import confirmed_by_operator, summarize_resolver_runs
from .canonical import CanonicalPullError, resolve_canonical
from .canonical_cache import CanonicalCacheError, ensure_cache_clone
from .merge_resolver import (
    BudgetExhausted,
    MergeResolver,
    MergeVerdict,
    ResolverBudget,
    ResolverFailure,
)
from .observability import span as otel_span
from .state import (
    SyncState,
    SyncOutcome,
    load_state,
    save_state,
    state_yaml_path,
)
from .sync_config import canonical_source_kind, load_sync_config


# ---- workspace-root derivation -------------------------------------


class WorkspaceRootError(Exception):
    """Raised when the CLI cannot derive a workspace root."""


def derive_workspace_root(
    *,
    workspace_arg: Path | None,
    cwd: Path | None = None,
) -> Path:
    """Derive the workspace root.

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

    # Post-D.2/D.3 layout: workspace-state under workspace/.
    if (cwd / "workspace" / ".pos" / "sync-protected.yaml").exists():
        return cwd
    # Post-D.3 layout: framework/ is a git working tree.
    if (cwd / "framework" / ".git").exists():
        return cwd
    # Pre-D.2 back-compat.
    if (cwd / ".pos" / "sync-protected.yaml").exists():
        return cwd
    if (cwd / ".git").exists():
        return cwd

    raise WorkspaceRootError(
        f"workspace root not derivable from cwd={cwd}: none of "
        "workspace/.pos/sync-protected.yaml (post-D.2), "
        "framework/.git/ (post-D.3), .pos/sync-protected.yaml "
        "(pre-D.2), or .git/ (fresh first-run) is present. Pass "
        "--workspace <path> to specify explicitly."
    )


# ---- merge-resolver factory loading --------------------------------


def _load_merge_resolver(
    module_spec: str,
    *,
    budget: ResolverBudget | None = None,
) -> MergeResolver:
    """Load + invoke the merge-resolver factory at ``module_spec``."""
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


# ---- git helpers (subprocess shellouts) ----------------------------


class GitError(Exception):
    """Raised on git invocation failure (non-zero exit)."""


def _git(
    framework_root: Path,
    args: list[str],
    *,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run ``git -C <framework_root> <args>`` and return the result."""
    argv = ["git", "-C", str(framework_root), *args]
    completed = subprocess.run(  # noqa: S603 — argv constructed
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=False,
        text=True,
    )
    if check and completed.returncode != 0:
        raise GitError(
            f"git {' '.join(args)} failed (exit "
            f"{completed.returncode}): "
            f"{(completed.stderr or '').strip()!r}"
        )
    return completed


def _ensure_framework_git_tree(workspace_root: Path) -> Path:
    """Verify ``<workspace>/framework/`` is a git working tree.

    Returns the framework root path. Raises ``WorkspaceRootError``
    with a structured message pointing at D.4's ``pos-new-workspace``
    when the tree is absent.
    """
    framework_root = workspace_root / "framework"
    if not framework_root.exists() or not framework_root.is_dir():
        raise WorkspaceRootError(
            f"<workspace>/framework/ does not exist at {framework_root}. "
            "Run `pos-new-workspace --from <repo> <new-ws-path>` to "
            "bootstrap a workspace, or `git clone <canonical> "
            f"{framework_root}` if you are migrating an existing "
            "workspace by hand."
        )
    if not (framework_root / ".git").exists():
        raise WorkspaceRootError(
            f"<workspace>/framework/ exists at {framework_root} but is "
            "not a git working tree (missing .git/). D.3's pos-sync "
            "requires framework/ to be a git clone of canonical. "
            "Run `pos-new-workspace --from <repo> <new-ws-path>` to "
            "bootstrap a fresh workspace, or `git clone <canonical> "
            f"{framework_root}` against an existing workspace."
        )
    return framework_root


def _configure_canonical_remote(
    framework_root: Path, canonical_url_or_path: str
) -> None:
    """Idempotently configure the ``canonical`` remote.

    If the remote does not exist, ``git remote add canonical <url>``.
    If it exists with a different URL, ``git remote set-url canonical
    <url>`` (config drift heals on every sync).
    """
    completed = _git(
        framework_root,
        ["config", "--get", "remote.canonical.url"],
        check=False,
    )
    if completed.returncode == 0:
        existing = (completed.stdout or "").strip()
        if existing == canonical_url_or_path:
            return
        _git(
            framework_root,
            ["remote", "set-url", "canonical", canonical_url_or_path],
        )
    else:
        _git(
            framework_root,
            ["remote", "add", "canonical", canonical_url_or_path],
        )


def _resolve_target_ref(framework_root: Path, ref_arg: str | None) -> str:
    """Resolve the merge target ref.

    When ``--ref`` is None, returns ``canonical/<current-local-branch>``
    so the merge fetches "the same branch on canonical." This mirrors
    what ``git pull`` defaults to. Otherwise returns the explicit ref
    (caller-supplied, may be a branch name, tag, or SHA).

    On a detached HEAD (rare for a workspace), falls back to
    ``FETCH_HEAD`` which references the just-fetched canonical-side
    HEAD.
    """
    if ref_arg is not None:
        return ref_arg
    branch = _git_current_branch(framework_root)
    if branch == "HEAD":
        return "FETCH_HEAD"
    return f"canonical/{branch}"


def _git_rev_parse(framework_root: Path, ref: str) -> str:
    """Resolve ``ref`` to a stable SHA. Raises ``GitError`` on failure."""
    completed = _git(framework_root, ["rev-parse", ref])
    return (completed.stdout or "").strip()


def _git_log_oneline(
    framework_root: Path, range_spec: str
) -> list[str]:
    """Return ``git log --oneline <range_spec>`` lines (empty list on error)."""
    completed = _git(
        framework_root,
        ["log", "--oneline", range_spec],
        check=False,
    )
    if completed.returncode != 0:
        return []
    return [
        ln
        for ln in (completed.stdout or "").splitlines()
        if ln.strip()
    ]


def _git_current_branch(framework_root: Path) -> str:
    """Return the current branch name, or 'HEAD' on detached state."""
    completed = _git(
        framework_root,
        ["symbolic-ref", "--short", "HEAD"],
        check=False,
    )
    if completed.returncode != 0:
        return "HEAD"
    return (completed.stdout or "").strip() or "HEAD"


def _git_conflicted_paths(framework_root: Path) -> list[str]:
    """Parse `git status --porcelain` for unresolved-conflict paths.

    Returns relative paths whose status code starts with one of UU,
    AA, DD (unmerged states).
    """
    completed = _git(framework_root, ["status", "--porcelain"], check=False)
    if completed.returncode != 0:
        return []
    paths: list[str] = []
    for line in (completed.stdout or "").splitlines():
        if not line:
            continue
        # Porcelain format: "XY <path>" where X+Y are status codes.
        code = line[:2]
        rest = line[3:]
        if code in ("UU", "AA", "DD", "AU", "UA", "DU", "UD"):
            paths.append(rest)
    return paths


# ---- LLM-resolver fallback -----------------------------------------


_PATH_SAFE_RE = re.compile(r"[^A-Za-z0-9._-]+")


def _sanitise_path_for_run_record(rel_path: str) -> str:
    """Map ``a/b/c.py`` → ``a__b__c.py`` for resolver-runs filenames."""
    return rel_path.replace("/", "__")


def _read_text_at_ref(
    framework_root: Path, ref: str, rel_path: str
) -> str | None:
    """Return the file's content at the given ref, or None if absent / binary."""
    completed = _git(
        framework_root,
        ["show", f"{ref}:{rel_path}"],
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout


def _record_resolver_run(
    workspace_root: Path,
    sync_sha: str,
    rel_path: str,
    verdict: MergeVerdict,
) -> Path:
    """Persist a per-conflict MergeVerdict at
    ``<workspace>/workspace/.pos/sync/resolver-runs/<sha>/<sanitised>.yaml``.
    Returns the written path.
    """
    from workspace_bootstrap.workspace_paths import pos_subdir

    target = (
        pos_subdir(workspace_root)
        / "sync"
        / "resolver-runs"
        / sync_sha
        / f"{_sanitise_path_for_run_record(rel_path)}.yaml"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(
            {
                "path": rel_path,
                "sync_sha": sync_sha,
                "verdict": verdict.model_dump(mode="json"),
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            },
            default_flow_style=False,
            sort_keys=False,
        )
    )
    return target


def _resolve_conflicts_via_llm(
    *,
    framework_root: Path,
    workspace_root: Path,
    target_sha: str,
    resolver: MergeResolver,
) -> list[tuple[str, MergeVerdict]]:
    """Iterate unresolved conflicts; invoke resolver per file.

    For each conflicted path:
      1. Read canonical content (FETCH_HEAD:<path>).
      2. Read workspace content (HEAD:<path>) — pre-merge state.
      3. Read merge-base content (merge-base canonical/HEAD HEAD:<path>) for
         prior_text.
      4. Invoke ``MergeResolver.resolve``.
      5. Write resolution to disk; ``git add <path>``.
      6. Append (path, verdict) to results.

    Returns the list of (rel_path, verdict). Raises
    ``BudgetExhausted`` / ``ResolverFailure`` on resolver halt.
    """
    paths = _git_conflicted_paths(framework_root)
    results: list[tuple[str, MergeVerdict]] = []

    if not paths:
        return results

    # Resolve merge-base once.
    base_completed = _git(
        framework_root,
        ["merge-base", "HEAD", target_sha],
        check=False,
    )
    base_sha = (
        (base_completed.stdout or "").strip()
        if base_completed.returncode == 0
        else None
    )

    for rel_path in paths:
        canonical_text = _read_text_at_ref(
            framework_root, target_sha, rel_path
        )
        # The pre-merge HEAD content lives in the index's stage 2 (ours)
        # entry during a conflicted merge; easier to read from the
        # working tree's pre-merge state by checking out stage 2.
        ours_completed = _git(
            framework_root,
            ["show", f":2:{rel_path}"],
            check=False,
        )
        workspace_text = (
            ours_completed.stdout if ours_completed.returncode == 0 else None
        )
        prior_text: str | None = None
        if base_sha:
            prior_text = _read_text_at_ref(framework_root, base_sha, rel_path)

        if canonical_text is None or workspace_text is None:
            raise ResolverFailure(
                f"could not read canonical or workspace content for "
                f"{rel_path} (binary file or missing). Halting fallback."
            )

        verdict = resolver.resolve(
            path=rel_path,
            canonical_text=canonical_text,
            workspace_text=workspace_text,
            prior_text=prior_text,
        )

        # Apply the verdict.
        if verdict.resolution == "inferred-accept-canonical":
            (framework_root / rel_path).write_text(canonical_text)
        elif verdict.resolution == "inferred-accept-workspace":
            (framework_root / rel_path).write_text(workspace_text)
        elif verdict.resolution == "inferred-merged":
            assert verdict.merged_content is not None  # noqa: S101 — Pydantic-enforced
            (framework_root / rel_path).write_text(verdict.merged_content)

        _git(framework_root, ["add", rel_path])
        results.append((rel_path, verdict))

    return results


# ---- main flow -----------------------------------------------------


def _execute_sync(
    *,
    workspace_root: Path,
    canonical_url_or_path: str,
    ref_arg: str | None,
    resolver_factory_module: str,
    resolver_budget: ResolverBudget | None,
    auto_accept: bool,
    confidence_floor: float,
) -> int:
    """Execute the full sync. Returns CLI exit code."""
    framework_root = _ensure_framework_git_tree(workspace_root)

    # Configure remote.
    try:
        _configure_canonical_remote(framework_root, canonical_url_or_path)
    except GitError as exc:
        print(
            f"[workspace-sync] failed to configure remote: {exc}",
            file=sys.stderr,
        )
        return 2

    # Fetch.
    try:
        _git(framework_root, ["fetch", "canonical"])
    except GitError as exc:
        print(f"[workspace-sync] git fetch failed: {exc}", file=sys.stderr)
        return 2

    # Resolve target ref.
    target_ref = _resolve_target_ref(framework_root, ref_arg)
    try:
        target_sha = _git_rev_parse(framework_root, target_ref)
    except GitError as exc:
        print(
            f"[workspace-sync] could not resolve target ref "
            f"{target_ref!r}: {exc}",
            file=sys.stderr,
        )
        return 2

    # Idempotency fast-path.
    try:
        head_sha = _git_rev_parse(framework_root, "HEAD")
    except GitError as exc:
        print(
            f"[workspace-sync] could not resolve HEAD: {exc}",
            file=sys.stderr,
        )
        return 2

    branch = _git_current_branch(framework_root)

    if head_sha == target_sha:
        print(
            f"[workspace-sync] up-to-date at {head_sha[:8]} (branch "
            f"{branch}); no-op.",
            file=sys.stderr,
        )
        save_state(
            SyncState(
                last_synced_sha=target_sha,
                last_synced_at=datetime.now(timezone.utc).isoformat(),
                last_branch=branch,
                last_outcome=SyncOutcome.UP_TO_DATE,
            ),
            workspace_root,
        )
        return 0

    # Capture pre-merge SHA for audit log range.
    pre_merge_sha = head_sha

    # Try fast-forward.
    ff_completed = _git(
        framework_root,
        ["merge", "--ff-only", target_sha],
        check=False,
    )

    if ff_completed.returncode == 0:
        # Fast-forward succeeded.
        new_head = _git_rev_parse(framework_root, "HEAD")
        log_lines = _git_log_oneline(
            framework_root, f"{pre_merge_sha}..{new_head}"
        )
        save_state(
            SyncState(
                last_synced_sha=new_head,
                last_synced_at=datetime.now(timezone.utc).isoformat(),
                last_branch=branch,
                last_outcome=SyncOutcome.FAST_FORWARD,
            ),
            workspace_root,
        )
        with otel_span(
            "loam.sync.fast_forward",
            {
                "loam.sync.from_sha": pre_merge_sha,
                "loam.sync.to_sha": new_head,
                "loam.sync.branch": branch,
            },
        ):
            pass
        print(
            f"[workspace-sync] fast-forwarded {branch}: "
            f"{pre_merge_sha[:8]} → {new_head[:8]} "
            f"({len(log_lines)} commit{'s' if len(log_lines) != 1 else ''}).",
            file=sys.stderr,
        )
        for line in log_lines:
            print(f"  {line}", file=sys.stderr)
        return 0

    # Non-FF fallback: try `git merge` (may auto-resolve some conflicts
    # via .gitattributes drivers; failing that, leave conflict markers
    # for the LLM resolver to handle).
    print(
        "[workspace-sync] fast-forward failed (workspace has commits "
        "ahead of canonical); falling back to merge + LLM resolver.",
        file=sys.stderr,
    )

    # Try plain merge first; if it succeeds (auto-resolved by git), commit + done.
    merge_completed = _git(
        framework_root,
        [
            "-c",
            "user.name=pos-sync",
            "-c",
            "user.email=pos-sync@local",
            "merge",
            "--no-ff",
            "--no-edit",
            target_sha,
        ],
        check=False,
    )
    if merge_completed.returncode == 0:
        # Git auto-resolved the merge.
        new_head = _git_rev_parse(framework_root, "HEAD")
        save_state(
            SyncState(
                last_synced_sha=new_head,
                last_synced_at=datetime.now(timezone.utc).isoformat(),
                last_branch=branch,
                last_outcome=SyncOutcome.MERGED,
            ),
            workspace_root,
        )
        print(
            f"[workspace-sync] merged (no LLM resolver needed): "
            f"{pre_merge_sha[:8]} + {target_sha[:8]} → {new_head[:8]}.",
            file=sys.stderr,
        )
        return 0

    # Conflicts present. Hand off to LLM resolver.
    try:
        resolver = _load_merge_resolver(
            resolver_factory_module, budget=resolver_budget
        )
    except (ResolverFailure, ImportError) as exc:
        print(
            f"[workspace-sync] resolver factory load failed: {exc}",
            file=sys.stderr,
        )
        # Abort the merge so the working tree returns to clean state.
        _git(framework_root, ["merge", "--abort"], check=False)
        return 2

    try:
        results = _resolve_conflicts_via_llm(
            framework_root=framework_root,
            workspace_root=workspace_root,
            target_sha=target_sha,
            resolver=resolver,
        )
    except (BudgetExhausted, ResolverFailure) as exc:
        print(
            f"[workspace-sync] LLM resolver halted: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        _git(framework_root, ["merge", "--abort"], check=False)
        save_state(
            SyncState(
                last_synced_sha=pre_merge_sha,
                last_synced_at=datetime.now(timezone.utc).isoformat(),
                last_branch=branch,
                last_outcome=SyncOutcome.RESOLVER_HALTED,
            ),
            workspace_root,
        )
        return 2

    if not results:
        # No conflicted paths but merge failed — unexpected state.
        print(
            "[workspace-sync] merge failed but no conflicted paths "
            "reported by `git status`. Aborting merge.",
            file=sys.stderr,
        )
        _git(framework_root, ["merge", "--abort"], check=False)
        return 2

    # Persist resolver-runs for audit + show summary.
    verdicts = [v for _, v in results]
    summary = summarize_resolver_runs(results)

    all_floor_met = all(
        v.confidence >= confidence_floor for v in verdicts
    )

    # TTY confirm gate.
    if not confirmed_by_operator(
        summary,
        auto_accept=auto_accept,
        all_confidences_meet_floor=all_floor_met,
    ):
        print(
            "[workspace-sync] resolver verdicts not confirmed; aborting "
            "merge to preserve pre-merge state.",
            file=sys.stderr,
        )
        _git(framework_root, ["merge", "--abort"], check=False)
        return 0

    # Commit the merge with the resolver's combined summary.
    commit_message = _build_merge_commit_message(target_sha, results)

    # The runs are recorded against the resulting merge commit's SHA;
    # we don't know that SHA until after `git commit`, so we record
    # against target_sha first, then re-key after commit.
    for rel_path, verdict in results:
        _record_resolver_run(
            workspace_root, target_sha, rel_path, verdict
        )

    commit_completed = _git(
        framework_root,
        [
            "-c",
            "user.name=pos-sync",
            "-c",
            "user.email=pos-sync@local",
            "commit",
            "-m",
            commit_message,
        ],
        check=False,
    )
    if commit_completed.returncode != 0:
        print(
            f"[workspace-sync] merge commit failed: "
            f"{(commit_completed.stderr or '').strip()!r}",
            file=sys.stderr,
        )
        _git(framework_root, ["merge", "--abort"], check=False)
        return 2

    new_head = _git_rev_parse(framework_root, "HEAD")
    save_state(
        SyncState(
            last_synced_sha=new_head,
            last_synced_at=datetime.now(timezone.utc).isoformat(),
            last_branch=branch,
            last_outcome=SyncOutcome.CONFLICT_FALLBACK,
        ),
        workspace_root,
    )
    print(
        f"[workspace-sync] merged with LLM resolver: "
        f"{pre_merge_sha[:8]} + {target_sha[:8]} → {new_head[:8]} "
        f"({len(results)} conflict{'s' if len(results) != 1 else ''} "
        "resolved).",
        file=sys.stderr,
    )
    return 0


def _build_merge_commit_message(
    target_sha: str, results: list[tuple[str, MergeVerdict]]
) -> str:
    """Shape the merge commit message from the resolver verdicts."""
    lines = [
        f"Merge canonical at {target_sha[:8]} (LLM-resolved)",
        "",
    ]
    for rel_path, verdict in results:
        lines.append(
            f"  - {rel_path}: {verdict.resolution} "
            f"(confidence {verdict.confidence:.2f}) — "
            f"{verdict.rationale.splitlines()[0][:80]}"
        )
    lines.append("")
    lines.append("Resolved by pos-sync (workspace_sync.cli) D.3.")
    return "\n".join(lines)


# ---- argparse ------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pos-sync",
        description=(
            "pOS v2 workspace-sync — pull canonical changes into "
            "<workspace>/framework/ via `git fetch + git merge "
            "--ff-only`. On non-fast-forward, fall back to `git "
            "merge` + LLM-mediated per-conflict resolver. The merge "
            "operates exclusively inside <workspace>/framework/; "
            "files under <workspace>/workspace/ are structurally "
            "untouchable (HC#6 of D-migration)."
        ),
    )
    parser.add_argument(
        "--canonical",
        required=False,
        default=None,
        type=str,
        help=(
            "Canonical source: an absolute path to a local git "
            "working tree, an http(s) URL, or a git@-style SSH spec. "
            "Optional: when absent, pos-sync reads canonical_source "
            "from <workspace>/workspace/.pos/sync-config.yaml or "
            "~/.loam/sync-config.yaml."
        ),
    )
    parser.add_argument(
        "--ref",
        default=None,
        help=(
            "Commit, tag, or branch to merge to. Default: "
            "canonical/HEAD (canonical's default branch)."
        ),
    )
    parser.add_argument(
        "--workspace",
        default=None,
        type=Path,
        help="Workspace root; default: cwd.",
    )
    parser.add_argument(
        "--merge-resolver-module",
        default="workspace_sync._resolver_client",
        help=(
            "Import path for the merge-resolver factory (format: "
            "'pkg.mod' or 'pkg.mod:build_merge_resolver'). Used "
            "only when `git merge` produces unresolved conflicts."
        ),
    )
    parser.add_argument(
        "--budget-tokens",
        type=int,
        default=None,
        help=(
            "Cumulative resolver budget override (only consumed on "
            "the LLM-fallback path). Default 100_000."
        ),
    )
    parser.add_argument(
        "--auto-accept",
        action="store_true",
        help=(
            "Opt-in fast-path: apply LLM-resolver verdicts without "
            "TTY confirmation when every verdict's confidence meets "
            "the floor (default 0.90). Only applies on the fallback "
            "path; fast-forward syncs do not invoke the resolver."
        ),
    )
    parser.add_argument(
        "--confidence-floor",
        type=float,
        default=0.90,
        help=(
            "Minimum confidence for --auto-accept on the fallback "
            "path (default 0.90)."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Workspace-root derivation.
    try:
        workspace_root = derive_workspace_root(workspace_arg=args.workspace)
    except WorkspaceRootError as exc:
        parser.error(str(exc))
        return 2  # unreachable

    # Fail-fast: framework/ must be a git working tree before we even
    # try to resolve canonical (the resolve can be expensive — URL
    # fetch — and a missing framework/ is the most common first-run
    # error post-D).
    try:
        _ensure_framework_git_tree(workspace_root)
    except WorkspaceRootError as exc:
        print(f"[workspace-sync] {exc}", file=sys.stderr)
        return 2

    # Canonical-source resolution.
    try:
        sync_cfg = load_sync_config(workspace_root)
    except Exception as exc:  # noqa: BLE001
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
            "set canonical_source: in <workspace>/workspace/.pos/"
            "sync-config.yaml, OR set canonical_source: in "
            "~/.loam/sync-config.yaml"
        )
        return 2  # unreachable

    try:
        kind = canonical_source_kind(canonical_source_str)
    except ValueError as exc:
        print(f"[workspace-sync] {exc}", file=sys.stderr)
        return 2

    # URL form: ensure cache clone is fresh; the cache directory's
    # absolute path becomes the remote URL on framework/.git.
    if kind == "url":
        try:
            cache_path = ensure_cache_clone(canonical_source_str, ref="HEAD")
        except CanonicalCacheError as exc:
            print(
                f"[workspace-sync] canonical cache failed: {exc}",
                file=sys.stderr,
            )
            return 2
        canonical_url_or_path = str(cache_path)
    else:
        canonical_url_or_path = canonical_source_str
        # Validate it's a git working tree (caller passed a local path).
        try:
            resolve_canonical(Path(canonical_url_or_path), ref="HEAD")
        except CanonicalPullError as exc:
            print(f"[workspace-sync] {exc}", file=sys.stderr)
            return 2

    # Resolver budget construction (only consumed on fallback path).
    if args.budget_tokens is not None:
        budget_override: ResolverBudget | None = ResolverBudget(
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

    with otel_span(
        "loam.sync.started",
        {
            "loam.sync.workspace_root": str(workspace_root),
            "loam.sync.canonical_source": canonical_url_or_path,
            "loam.sync.canonical_kind": kind,
            "loam.sync.ref_arg": args.ref or "canonical/HEAD",
        },
    ):
        return _execute_sync(
            workspace_root=workspace_root,
            canonical_url_or_path=canonical_url_or_path,
            ref_arg=args.ref,
            resolver_factory_module=args.merge_resolver_module,
            resolver_budget=budget_override,
            auto_accept=args.auto_accept,
            confidence_floor=args.confidence_floor,
        )


if __name__ == "__main__":
    sys.exit(main())
