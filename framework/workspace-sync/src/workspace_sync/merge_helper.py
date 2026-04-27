"""Workspace-sync inferred-conflict resolution helper.

Salvaged (with caller-side rebadging) from
``self-upgrade/src/self_upgrade/clause_checks.py``: the four
clause-(h)-resident functions ``_read_text_or_none``,
``_verdict_to_resolution``, ``resolve_clause_h_inferred``, and
``check_clause_h``. Self-upgrade's seven-clause acceptance contract
is canonical-side-only (Architecture A); workspace-sync renames
these helpers to the workspace-side semantic:

  - ``resolve_clause_h_inferred`` → ``resolve_inferred_conflicts``
  - ``check_clause_h`` → ``check_inferred_resolution_invariants``
  - ``report.upgrade_tag`` → ``report.sync_ref`` (per the
    conflict_report.py rename)
  - merged-content drop directory:
      ``.pos/upgrade/<tag>/merged`` → ``.pos/sync/<ref>/merged``
  - OTel span names + attributes:
      ``pos.upgrade.merge_gate.*`` → ``pos.sync.merge_gate.*``

The structural semantics — Class-A passthrough, Class-B operator-
preference, Class-C resolver invocation, OTel-instrumented
per-conflict + summary spans, finally-block audit + state
persistence — carry over byte-for-byte. The workspace-data envelope
NEVER overwrites a Class-A path: there is no Resolution-enum value
authorising canonical-side overwrite of a Class-A entry. AC.WS.2
+ AC.WS.12 structural enforcement.

Hidden-coupling check (workspace-sync plan §10 trigger 6): the
lifted helpers do NOT reference ``paths.current_link``,
``paths.history``, ``Paths``, ``live_root``, or any A-mode
symlink-resolution surface. Verified by reading
``self-upgrade/src/self_upgrade/clause_checks.py`` lines 355-579
at HEAD ``caafdf0`` before lifting; no such references found.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any, Callable

from .ancestor_detection import (
    DEFAULT_DEPTH_CAP,
    AncestorCacheEntry,
    cache_path,
    load_cache,
    save_cache,
    walk_ancestors,
)
from .conflict_report import (
    ConflictChangeKind,
    ConflictEntry,
    ConflictReport,
    INFERRED_RESOLUTIONS,
    Resolution,
    save_conflict_report,
)
from .merge_resolver import (
    BudgetExhausted,
    MergeResolver,
    MergeVerdict,
    ResolverFailure,
)
from .observability import span as otel_span
from .state import (
    StateRecord,
    SyncStatus,
    audit_yaml_path,
    make_state_record,
    save_state,
)
from .sync_protected import FileClass, SyncProtected


class _FallthroughToGenerator(Exception):
    """Internal control-flow signal: α.2 deterministic chain declined.

    Carries the structured fallback_reason that lands in the audit's
    ``fallback_reason`` field. Caught immediately within the
    Class-C loop body and translated to a generator call.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _resolve_canonical_head_sha(canonical_path: Path, ref: str) -> str | None:
    """Resolve <ref> to a stable commit SHA on the canonical repo.

    Returns the full hex SHA on success, None on failure. Used to
    key the ancestor cache so a canonical-ref advance (HEAD moves
    forward) invalidates the cache wholesale.
    """
    try:
        completed = subprocess.run(  # noqa: S603 — argv constructed
            ["git", "-C", str(canonical_path), "rev-parse", ref],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            text=True,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    sha = completed.stdout.strip()
    return sha if sha else None


def _read_canonical_blob_at_ref(
    canonical_path: Path, ref: str, rel_path: str
) -> bytes | None:
    """Resolve ``<ref>:<rel_path>`` on the canonical repo to its blob bytes.

    Returns the blob's raw bytes on success, None on failure (path
    missing at ref, submodule, symlink, ref unresolvable, or
    subprocess error).

    α-hotfix #59 staging primitive: the α.1 NN ancestor-detection
    accept-canonical fast-path uses this to read canonical's HEAD
    content for the resolved path so the staging tree carries the
    file before ``apply_staging_atomically`` runs. Mirrors the
    shellout shape used by ``_resolve_canonical_head_sha`` above
    and by ``conflict_detection._git_show_bytes``.
    """
    try:
        completed = subprocess.run(  # noqa: S603 — argv constructed
            ["git", "-C", str(canonical_path), "show", f"{ref}:{rel_path}"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout


def stage_canonical_at_ref(
    *,
    entry: ConflictEntry,
    canonical_root: Path,
    canonical_ref: str,
    workspace_root: Path,
    sync_ref: str,
    write_merged: Callable[[str, str], str] | None,
) -> bool:
    """Stage canonical's HEAD content for an accept-canonical-flavored entry.

    α-hotfix #59 (originally `_stage_canonical_for_nn_match`):
    the α.1 NN ancestor-detection accept-canonical fast-path
    historically set the verdict but never staged content, causing
    ``apply_staging_atomically`` to silently no-op on the path.

    α-hotfix-2 #60 (renamed + made public): the SAME staging primitive
    is needed for two more accept-canonical-flavored verdicts that
    cli.py wires post-resolve:
      - ``INFERRED_ACCEPT_CANONICAL`` returned by the LLM resolver
        (not via NN fast-path; Bug A).
      - ``ACCEPT_UPSTREAM`` for Class-B operator-prefers-canonical
        entries (Bug B).
    Centralizing the contract here means future amendments cannot
    re-introduce a verdict-set-without-content-staged shape on any
    accept-canonical-flavored resolution.

    Reads canonical's HEAD content for ``entry.path`` via
    ``git show <ref>:<path>``, decodes UTF-8, and drops the content
    into staging via the supplied ``write_merged`` callable (or falls
    back to the same per-conflict merged path used by
    ``INFERRED_MERGED`` when ``write_merged`` is None, mirroring lines
    below for the ``INFERRED_MERGED`` case).

    Returns True on success (``entry.resolved_content_path`` is
    populated and the staging file exists), False on failure
    (binary content, missing path at ref, ref unresolvable). The
    caller decides halt-vs-fall-through:
      - merge_helper's NN branches: leave PENDING on False (legacy
        resolver path handles it).
      - cli.py post-resolve loop: the verdict is already sealed by
        the time we get here, so False means halt-and-discard
        (failing closed; the alternative is re-introducing the
        verdict-without-stage bug on the very path this primitive
        is meant to close).
    """
    canonical_bytes = _read_canonical_blob_at_ref(
        canonical_root, canonical_ref, entry.path
    )
    if canonical_bytes is None:
        return False
    try:
        canonical_text = canonical_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return False
    if write_merged is not None:
        entry.resolved_content_path = write_merged(entry.path, canonical_text)
    else:
        # Mirror the INFERRED_MERGED else-branch (write to per-
        # conflict merged path under workspace/.pos/sync/<ref>/merged/).
        # D-migration D.2 (amendment #63): workspace-state under
        # <workspace>/workspace/.pos/.
        from workspace_bootstrap.workspace_paths import pos_subdir

        merged_dir = pos_subdir(workspace_root) / "sync" / sync_ref / "merged"
        target = merged_dir / entry.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(canonical_text)
        entry.resolved_content_path = str(target)
    return True


def _read_text_or_none(path: Path) -> str | None:
    """Read UTF-8 text from path; return None if missing or binary."""
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _verdict_to_resolution(verdict: MergeVerdict) -> Resolution:
    """Map the resolver's structured verdict onto the closed Resolution
    enum extension. Defensive: the Literal in MergeVerdict already
    constrains the value-set, but the explicit map keeps the call
    sites readable."""
    if verdict.resolution == "inferred-accept-canonical":
        return Resolution.INFERRED_ACCEPT_CANONICAL
    if verdict.resolution == "inferred-accept-workspace":
        return Resolution.INFERRED_ACCEPT_WORKSPACE
    if verdict.resolution == "inferred-merged":
        return Resolution.INFERRED_MERGED
    raise ValueError(f"unrecognised verdict resolution: {verdict.resolution!r}")


def _try_deterministic_merge(
    *,
    entry: ConflictEntry,
    canonical_text: str,
    workspace_text: str,
    resolver: MergeResolver,
) -> MergeVerdict:
    """α.2 deterministic-merge-with-LLM-verify-gate (AC.WSα.3-.5).

    Implementation lands in Phase C of the build (this is a phase-B
    stub that always raises ``_FallthroughToGenerator`` so the
    Class-C branch behaves identically to #56's generator-only
    behaviour while α.1 is wired). The Phase-C implementation
    replaces this body with the classifier+primitive+verifier
    chain and only raises ``_FallthroughToGenerator`` on classifier-
    unknown / primitive-failed / verifier-rejected.

    Imports the classifier + verifier from
    ``workspace_sync.merge_primitives`` once that module lands.
    Returns the produced ``MergeVerdict`` on success.

    Phase-B placeholder behaviour: always raise with reason
    ``"alpha2-not-yet-implemented"`` so every Class-C conflict
    falls through to today's path. Phase C replaces.
    """
    try:
        from .merge_primitives import (
            MergeClassDeclined,
            classify_file,
            run_primitive,
            verify_merge,
        )
    except ImportError:
        # Phase-B fallback: module not yet authored.
        raise _FallthroughToGenerator("alpha2-not-yet-implemented")

    # Phase-C real chain.
    try:
        classification, classify_tokens = classify_file(
            llm_client=resolver.llm_client,
            path=entry.path,
            canonical_text=canonical_text,
            workspace_text=workspace_text,
        )
    except Exception as exc:  # noqa: BLE001
        raise _FallthroughToGenerator(
            f"primitive-failed: classifier raised {type(exc).__name__}: {exc}"
        )

    with otel_span(
        "pos.sync.merge_gate.classify",
        {
            "pos.sync.merge_gate.path": entry.path,
            "pos.sync.merge_gate.class": classification.merge_class,
            "pos.sync.merge_gate.tokens": classify_tokens,
            "pos.sync.merge_gate.classifier_confidence": classification.confidence,
        },
    ):
        pass

    if classification.merge_class == "unknown":
        raise _FallthroughToGenerator("classifier-unknown")

    try:
        merged_text, primitive_trace = run_primitive(
            classification.merge_class, canonical_text, workspace_text
        )
    except MergeClassDeclined as exc:
        raise _FallthroughToGenerator(f"primitive-failed: {exc}")

    try:
        verification, verify_tokens = verify_merge(
            llm_client=resolver.llm_client,
            path=entry.path,
            canonical_text=canonical_text,
            workspace_text=workspace_text,
            candidate_merged_text=merged_text,
            classification=classification,
            primitive_trace=primitive_trace,
        )
    except Exception as exc:  # noqa: BLE001
        raise _FallthroughToGenerator(
            f"primitive-failed: verifier raised {type(exc).__name__}: {exc}"
        )

    with otel_span(
        "pos.sync.merge_gate.verify",
        {
            "pos.sync.merge_gate.path": entry.path,
            "pos.sync.merge_gate.passed": verification.passed,
            "pos.sync.merge_gate.class_mismatch": verification.class_mismatch,
            "pos.sync.merge_gate.tokens": verify_tokens,
        },
    ):
        pass

    if not verification.passed:
        raise _FallthroughToGenerator("verifier-rejected")

    # Verifier passed. Set entry fields here (matches the path
    # where _try_deterministic_merge SUCCEEDED — caller checks
    # entry.classifier_class is not None to skip its own assignment).
    entry.classifier_class = classification.merge_class
    entry.deterministic_primitive = primitive_trace.operation
    entry.confidence = verification.confidence
    entry.rationale = (
        f"deterministic {classification.merge_class} merge "
        f"({primitive_trace.operation}); verifier passed at "
        f"{verification.confidence:.2f}"
    )
    if verification.concerns:
        entry.rationale = entry.rationale + f" — concerns: {verification.concerns}"

    return MergeVerdict(
        resolution="inferred-merged",
        merged_content=merged_text,
        rationale=entry.rationale,
        confidence=verification.confidence,
    )


def resolve_inferred_conflicts(
    *,
    report: ConflictReport,
    sync_protected: SyncProtected,
    canonical_root: Path,
    workspace_root: Path,
    resolver: MergeResolver,
    write_merged: Callable[[str, str], str] | None = None,
    canonical_ref: str | None = None,
    ancestor_depth_cap: int = DEFAULT_DEPTH_CAP,
) -> None:
    """Pre-stage helper: resolve every PENDING conflict against the
    workspace's three-class envelope.

    Walks every PENDING ``ConflictEntry`` in ``report``; classifies
    each against the workspace's sync-protected envelope; preserves
    Class A workspace state (KEEP_LOCAL, never overwritten — AC.WS.2),
    applies operator-preference semantics for Class B (AC.WS.3), and
    invokes the LLM resolver for Class C (AC.WS.4). Mutates entries
    in place so the existing ``report.has_pending()`` block clears
    for any conflict the helper resolved.

    Bundle α (#57) extension. The Class-C path now first tries
    α.1 ancestor-detection (workspace-content matches a canonical-
    history ancestor commit's blob → fast-path
    ``inferred-accept-canonical``; AC.WSα.1 + AC.WSα.2). On
    decline, α.2 deterministic-merge-with-LLM-verify-gate runs
    (classifier + per-class primitive + verifier; AC.WSα.3 through
    AC.WSα.5). On any α.2 step decline (classifier-unknown,
    primitive-failed, verifier-rejected) the existing LLM-generator
    path runs unchanged (AC.WSα.6 — preserves the correctness
    ceiling). The α.3 MCP-isolated subprocess (AC.WSα.8) is wired
    automatically through ``_resolver_client.py``.

    ``canonical_ref`` (optional) names the canonical ref the sync is
    pulling. When supplied, α.1 ancestor-detection is enabled (uses
    the ref to resolve a stable canonical-HEAD SHA for cache-keying
    and to drive the ``git log --all --follow`` walk on
    ``canonical_root``). When None, α.1 is disabled and the helper
    falls through to the existing Class-C path. ``ancestor_depth_cap``
    bounds the walk (default 200; D-1 LOCKED).

    ``write_merged(path, content) -> str`` is an optional sink the
    caller supplies for ``inferred-merged`` verdicts; it must persist
    the merged content somewhere and return the absolute path. When
    omitted, merged content is dropped onto a per-conflict path under
    ``workspace_root/.pos/sync/<ref>/merged/<path>``.

    Raises:
        BudgetExhausted: cumulative resolver budget hit; halt-and-
            resume per AC.WS.6. ``report`` is mutated up to the halt
            point and the audit + state are persisted before the
            exception propagates.
        ResolverFailure: LLM call failed for any conflict. Fail-closed
            per AC.WS.12. ``report`` is mutated up to the failure
            point; audit + state persisted before propagation.
    """
    resolved_count = 0
    deferred_count = 0

    summary_attrs: dict[str, Any] = {
        "pos.sync.merge_gate.sync_ref": report.sync_ref,
    }
    halt_reason: str | None = None

    # α.1 ancestor-detection cache. Loaded lazily on first Class-C
    # conflict; persisted at end-of-run via the finally block. Only
    # populated when canonical_ref is supplied (the helper's caller
    # owns the wiring; when None, α.1 is disabled and we fall through
    # to the existing Class-C path unchanged).
    _ancestor_cache_state: dict[str, Any] = {
        "cache": None,
        "canonical_head_sha": None,
        "loaded": False,
    }
    # Per-run counters (audit + summary span).
    ancestor_match_count = 0
    ancestor_walk_count = 0

    try:
        for entry in report.conflicts:
            if entry.resolution is not Resolution.PENDING:
                # Already manually resolved (or auto-resolved) — preserve
                # the operator's choice. Convergent idempotency: re-runs
                # see non-PENDING entries and skip them (AC.WS.8).
                continue
            if entry.user_override:
                # Honour persistent operator override per AC.WS.9. The
                # resolution must already be set by the operator; if
                # not, that's a validator-caught bug upstream.
                continue

            klass = sync_protected.classify(entry.path)

            if klass is FileClass.A:
                # Class A: never overwritten. Preserve workspace.
                # AC.WS.2 structural enforcement.
                entry.resolution = Resolution.KEEP_LOCAL
                entry.rationale = (
                    "Class A (workspace state): preserved by sync "
                    "envelope. No resolver call."
                )
                entry.confidence = 1.0
                resolved_count += 1
                continue

            if klass is FileClass.B:
                # Class B: operator-preference. Workspace wins when
                # workspace-modified; canonical wins when workspace
                # untouched. Detect by change_kind: if the conflict
                # was raised at all, workspace differs from prior, so
                # workspace-modified is implicit. AC.WS.3.
                if entry.change_kind in (
                    ConflictChangeKind.LOCAL_MODIFIED_ONLY,
                    ConflictChangeKind.UPSTREAM_MODIFIED_AND_LOCAL_MODIFIED,
                ):
                    entry.resolution = Resolution.KEEP_LOCAL
                    entry.rationale = (
                        "Class B (operator preference): workspace-modified "
                        "wins over canonical update."
                    )
                else:
                    entry.resolution = Resolution.ACCEPT_UPSTREAM
                    entry.rationale = (
                        "Class B (operator preference): workspace unchanged; "
                        "accept canonical."
                    )
                entry.confidence = 1.0
                resolved_count += 1
                continue

            # Class C: bundle-α extended path.
            #
            #   1. α.1 ancestor-detection (AC.WSα.1 + AC.WSα.2):
            #      walk canonical history for <path>; on
            #      content-match → fast-path
            #      INFERRED_ACCEPT_CANONICAL with confidence 1.0,
            #      no LLM call.
            #   2. α.2 deterministic-merge-with-LLM-verify-gate
            #      (AC.WSα.3 — .5): classify + per-class primitive
            #      + verifier; on pass → INFERRED_MERGED with the
            #      deterministic candidate.
            #   3. AC.WSα.6 fall-back: classifier-unknown OR
            #      primitive-failed OR verifier-rejected → existing
            #      LLM-generator path runs unchanged (preserves
            #      AC.WS.4 / AC.WS.12 correctness ceiling).

            # α.1: try ancestor fast-path FIRST (zero LLM cost on hit).
            if (
                canonical_ref is not None
                and entry.installed_sha256 is not None
                and entry.installed_sha256 != ""
            ):
                # Lazy-load cache on first Class-C conflict.
                if not _ancestor_cache_state["loaded"]:
                    head_sha = _resolve_canonical_head_sha(
                        canonical_root, canonical_ref
                    ) or canonical_ref
                    _ancestor_cache_state["canonical_head_sha"] = head_sha
                    _ancestor_cache_state["cache"] = load_cache(
                        workspace_root, report.sync_ref, head_sha
                    )
                    _ancestor_cache_state["loaded"] = True

                cache = _ancestor_cache_state["cache"]
                cached = cache.get(entry.path, entry.installed_sha256)
                if cached is not None:
                    # Cache hit: replay the prior walk's verdict.
                    if cached.ancestor_sha is not None:
                        # α-hotfix #59: stage canonical's HEAD content
                        # BEFORE sealing the verdict. If staging fails
                        # (binary file / missing at ref / ref
                        # unresolvable), leave the entry PENDING and
                        # let the legacy resolver path handle it —
                        # do NOT seal the verdict without staged
                        # content, or apply_staging_atomically will
                        # silently no-op on the path (the original
                        # bug).
                        staged = stage_canonical_at_ref(
                            entry=entry,
                            canonical_root=canonical_root,
                            canonical_ref=canonical_ref,
                            workspace_root=workspace_root,
                            sync_ref=report.sync_ref,
                            write_merged=write_merged,
                        )
                        if staged:
                            with otel_span(
                                "pos.sync.merge_gate.ancestor_check",
                                {
                                    "pos.sync.merge_gate.path": entry.path,
                                    "pos.sync.merge_gate.matched": True,
                                    "pos.sync.merge_gate.ancestor_sha": cached.ancestor_sha,
                                    "pos.sync.merge_gate.walk_depth": cached.walk_depth,
                                    "pos.sync.merge_gate.cache_hit": True,
                                },
                            ):
                                pass
                            entry.resolution = Resolution.INFERRED_ACCEPT_CANONICAL
                            entry.rationale = (
                                f"workspace path matches canonical-history "
                                f"ancestor at {cached.ancestor_sha[:7]}; "
                                "not edited"
                            )
                            entry.confidence = 1.0
                            entry.ancestor_match_sha = cached.ancestor_sha
                            ancestor_match_count += 1
                            resolved_count += 1
                            continue
                        # Stage failed: fall through to legacy path.
                        # Span emitted with matched=True but
                        # stage_failed=True for observability.
                        with otel_span(
                            "pos.sync.merge_gate.ancestor_check",
                            {
                                "pos.sync.merge_gate.path": entry.path,
                                "pos.sync.merge_gate.matched": True,
                                "pos.sync.merge_gate.ancestor_sha": cached.ancestor_sha,
                                "pos.sync.merge_gate.walk_depth": cached.walk_depth,
                                "pos.sync.merge_gate.cache_hit": True,
                                "pos.sync.merge_gate.stage_failed": True,
                            },
                        ):
                            pass
                    # Cached miss: don't re-walk; fall through to
                    # legacy resolver path. Span emitted for parity.
                    with otel_span(
                        "pos.sync.merge_gate.ancestor_check",
                        {
                            "pos.sync.merge_gate.path": entry.path,
                            "pos.sync.merge_gate.matched": False,
                            "pos.sync.merge_gate.walk_depth": cached.walk_depth,
                            "pos.sync.merge_gate.walk_short": cached.walk_short,
                            "pos.sync.merge_gate.cache_hit": True,
                        },
                    ):
                        pass
                else:
                    # Cache miss: walk now.
                    match, walk_depth, walk_short = walk_ancestors(
                        canonical_path=canonical_root,
                        ref=canonical_ref,
                        conflict_path=entry.path,
                        target_sha256=entry.installed_sha256,
                        depth_cap=ancestor_depth_cap,
                    )
                    ancestor_walk_count += 1
                    cache.put(
                        AncestorCacheEntry(
                            path=entry.path,
                            workspace_sha256=entry.installed_sha256,
                            ancestor_sha=(
                                match.commit_sha if match is not None else None
                            ),
                            walk_depth=walk_depth,
                            walk_short=walk_short,
                        )
                    )
                    if match is not None:
                        # α-hotfix #59: stage canonical's HEAD content
                        # BEFORE sealing the verdict (see cache-hit
                        # branch above for the full rationale).
                        staged = stage_canonical_at_ref(
                            entry=entry,
                            canonical_root=canonical_root,
                            canonical_ref=canonical_ref,
                            workspace_root=workspace_root,
                            sync_ref=report.sync_ref,
                            write_merged=write_merged,
                        )
                        if staged:
                            with otel_span(
                                "pos.sync.merge_gate.ancestor_check",
                                {
                                    "pos.sync.merge_gate.path": entry.path,
                                    "pos.sync.merge_gate.matched": True,
                                    "pos.sync.merge_gate.ancestor_sha": match.commit_sha,
                                    "pos.sync.merge_gate.walk_depth": walk_depth,
                                    "pos.sync.merge_gate.cache_hit": False,
                                },
                            ):
                                pass
                            entry.resolution = Resolution.INFERRED_ACCEPT_CANONICAL
                            entry.rationale = (
                                f"workspace path matches canonical-history "
                                f"ancestor at {match.short_sha}; not edited"
                            )
                            entry.confidence = 1.0
                            entry.ancestor_match_sha = match.commit_sha
                            ancestor_match_count += 1
                            resolved_count += 1
                            continue
                        # Stage failed: fall through to legacy path.
                        with otel_span(
                            "pos.sync.merge_gate.ancestor_check",
                            {
                                "pos.sync.merge_gate.path": entry.path,
                                "pos.sync.merge_gate.matched": True,
                                "pos.sync.merge_gate.ancestor_sha": match.commit_sha,
                                "pos.sync.merge_gate.walk_depth": walk_depth,
                                "pos.sync.merge_gate.cache_hit": False,
                                "pos.sync.merge_gate.stage_failed": True,
                            },
                        ):
                            pass
                    # No match: fall through to legacy path. Span
                    # captures walk metrics for observability.
                    with otel_span(
                        "pos.sync.merge_gate.ancestor_check",
                        {
                            "pos.sync.merge_gate.path": entry.path,
                            "pos.sync.merge_gate.matched": False,
                            "pos.sync.merge_gate.walk_depth": walk_depth,
                            "pos.sync.merge_gate.walk_short": walk_short,
                            "pos.sync.merge_gate.cache_hit": False,
                        },
                    ):
                        pass

            # α.1 declined (or disabled). Read both sides and proceed.
            canonical_text = _read_text_or_none(canonical_root / entry.path)
            workspace_text = _read_text_or_none(workspace_root / entry.path)
            prior_text: str | None = None  # not currently exposed by snapshot

            if canonical_text is None or workspace_text is None:
                # Binary or missing file — resolver cannot help. Mark
                # PENDING so the legacy hand-resolve path remains.
                deferred_count += 1
                continue

            # α.2 deterministic-merge-with-LLM-verify-gate (AC.WSα.3-.6).
            # On any decline, raise _FallthroughToGenerator with a
            # structured reason; the inner except block translates
            # to the legacy resolver path and records fallback_reason.
            verdict: MergeVerdict | None = None
            try:
                verdict = _try_deterministic_merge(
                    entry=entry,
                    canonical_text=canonical_text,
                    workspace_text=workspace_text,
                    resolver=resolver,
                )
            except _FallthroughToGenerator as fallthrough:
                entry.fallback_reason = fallthrough.reason
                with otel_span(
                    "pos.sync.merge_gate.resolution",
                    {
                        "pos.sync.merge_gate.path": entry.path,
                        "pos.sync.merge_gate.canonical_sha": entry.new_release_sha256 or "",
                        "pos.sync.merge_gate.workspace_sha": entry.installed_sha256 or "",
                        "pos.sync.merge_gate.fallback_reason": fallthrough.reason,
                    },
                ):
                    verdict = resolver.resolve(
                        path=entry.path,
                        canonical_text=canonical_text,
                        workspace_text=workspace_text,
                        prior_text=prior_text,
                    )

            assert verdict is not None  # one of the two paths sets it

            entry.resolution = _verdict_to_resolution(verdict)
            # If α.2 succeeded, _try_deterministic_merge already set
            # rationale/confidence/classifier_class/deterministic_primitive
            # on the entry (it just returns the verdict for type-flow).
            # If we fell through to the generator path, set them now.
            if entry.fallback_reason is not None or entry.classifier_class is None:
                entry.rationale = verdict.rationale
                entry.confidence = verdict.confidence

            if entry.resolution is Resolution.INFERRED_MERGED:
                # Persist merged content somewhere the staging apply
                # can read.
                # D-migration D.2 (amendment #63): workspace-state
                # under <workspace>/workspace/.pos/.
                if write_merged is not None:
                    entry.resolved_content_path = write_merged(
                        entry.path, verdict.merged_content or ""
                    )
                else:
                    from workspace_bootstrap.workspace_paths import pos_subdir

                    merged_dir = (
                        pos_subdir(workspace_root)
                        / "sync"
                        / report.sync_ref
                        / "merged"
                    )
                    target = merged_dir / entry.path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(verdict.merged_content or "")
                    entry.resolved_content_path = str(target)
            resolved_count += 1
    except BudgetExhausted as exc:
        halt_reason = f"budget_exhausted: {exc}"
        raise
    except ResolverFailure as exc:
        halt_reason = f"resolver_failure: {exc}"
        raise
    finally:
        summary_attrs.update(
            {
                "pos.sync.merge_gate.resolved_count": resolved_count,
                "pos.sync.merge_gate.deferred_count": deferred_count,
                "pos.sync.merge_gate.cumulative_tokens": resolver.cumulative_used,
                "pos.sync.merge_gate.call_count": resolver.call_count,
                "pos.sync.merge_gate.ancestor_match_count": ancestor_match_count,
                "pos.sync.merge_gate.ancestor_walk_count": ancestor_walk_count,
            }
        )
        if halt_reason is not None:
            summary_attrs["pos.sync.merge_gate.halt_reason"] = halt_reason
        with otel_span(
            "pos.sync.merge_gate.summary", summary_attrs
        ):
            pass

        # Persist the α.1 ancestor cache if we touched it. Failure
        # is non-fatal (mirrors the audit/state persistence-error
        # swallow below — cache is a performance optimisation, not
        # a correctness primitive).
        if _ancestor_cache_state["loaded"]:
            try:
                save_cache(
                    _ancestor_cache_state["cache"],
                    workspace_root,
                    report.sync_ref,
                )
            except Exception:  # noqa: BLE001
                pass

        # AC.WS.5 + AC.WS.8 + AC.WS.12: every sync execution leaves
        # both the workspace-local audit YAML and the state YAML
        # behind, regardless of clean-pass / BudgetExhausted /
        # ResolverFailure terminus. The writes happen after the
        # OTel summary span so observability records the run-level
        # outcome before disk-persistence.
        try:
            audit_target = audit_yaml_path(workspace_root, report.sync_ref)
            save_conflict_report(report, audit_target)

            if halt_reason is not None:
                status = SyncStatus.FAILURE
            elif report.has_pending() or deferred_count > 0:
                status = SyncStatus.PARTIAL
            else:
                # α-hotfix-2 #60 Bug D: the helper resolved cleanly
                # but the apply step has not run. cli.py post-apply
                # is the AUTHORITATIVE writer of SUCCESS — we write
                # NEEDS_APPLY here so the idempotency fast-path
                # (which requires status=SUCCESS) does not short-
                # circuit a re-run when staging was discarded
                # (e.g., --auto-accept floor not met). Pre-fix this
                # site wrote SUCCESS unconditionally → re-runs after
                # discard silently no-op'd via false-idempotency.
                status = SyncStatus.NEEDS_APPLY

            state = make_state_record(
                sync_ref=report.sync_ref,
                workspace_root=workspace_root,
                total_conflicts=len(report.conflicts),
                resolved_count=resolved_count,
                deferred_count=deferred_count,
                cumulative_tokens_used=resolver.cumulative_used,
                status=status,
                halt_reason=halt_reason,
            )
            save_state(state, workspace_root)
        except Exception:
            # Persistence failure must not mask the in-flight
            # BudgetExhausted / ResolverFailure exception that the
            # outer try-block is propagating. We swallow disk-write
            # errors in the finally so callers see the helper's
            # halt reason, not the persistence error. (Callers can
            # still spot the missing artefact at clean-pass time;
            # in practice tmpdir + ~/.pos targets are writable.)
            pass


def check_inferred_resolution_invariants(
    report: ConflictReport | None,
) -> tuple[bool, str | None]:
    """Post-pass invariant check.

    Asserts the ConflictReport's invariants after the resolver helper
    has run: every INFERRED_* entry carries rationale + confidence; no
    PENDING entries remain (the no-silent-skip rule extends to
    inferred resolutions — every conflict ends with a verdict or a
    manual resolution).

    Returns ``(passed: bool, reason: str | None)``. Caller decides
    halt-vs-continue semantics; the workspace-sync CLI treats a
    False return as a halt-and-surface signal (no apply).

    ``report`` may be None when the sync ran without --canonical
    (no conflicts to resolve); in that case the verifier is a no-op
    pass.
    """
    if report is None:
        return True, None

    pending = [
        c.path for c in report.conflicts if c.resolution is Resolution.PENDING
    ]
    if pending:
        return False, (
            f"{len(pending)} pending conflict(s) after resolver pass: "
            f"{pending}"
        )

    inferred_missing: list[str] = []
    for c in report.conflicts:
        if c.resolution in INFERRED_RESOLUTIONS:
            if c.rationale is None or c.confidence is None:
                inferred_missing.append(c.path)
    if inferred_missing:
        return False, (
            "INFERRED_* entries missing rationale or confidence: "
            f"{inferred_missing}"
        )

    return True, None
