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

from pathlib import Path
from typing import Any, Callable

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


def resolve_inferred_conflicts(
    *,
    report: ConflictReport,
    sync_protected: SyncProtected,
    canonical_root: Path,
    workspace_root: Path,
    resolver: MergeResolver,
    write_merged: Callable[[str, str], str] | None = None,
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

            # Class C: LLM-mediated resolution (AC.WS.4).
            canonical_text = _read_text_or_none(canonical_root / entry.path)
            workspace_text = _read_text_or_none(workspace_root / entry.path)
            prior_text: str | None = None  # not currently exposed by snapshot

            if canonical_text is None or workspace_text is None:
                # Binary or missing file — resolver cannot help. Mark
                # PENDING so the legacy hand-resolve path remains.
                deferred_count += 1
                continue

            with otel_span(
                "pos.sync.merge_gate.resolution",
                {
                    "pos.sync.merge_gate.path": entry.path,
                    "pos.sync.merge_gate.canonical_sha": entry.new_release_sha256 or "",
                    "pos.sync.merge_gate.workspace_sha": entry.installed_sha256 or "",
                },
            ):
                verdict = resolver.resolve(
                    path=entry.path,
                    canonical_text=canonical_text,
                    workspace_text=workspace_text,
                    prior_text=prior_text,
                )

            entry.resolution = _verdict_to_resolution(verdict)
            entry.rationale = verdict.rationale
            entry.confidence = verdict.confidence

            if entry.resolution is Resolution.INFERRED_MERGED:
                # Persist merged content somewhere the staging apply
                # can read.
                if write_merged is not None:
                    entry.resolved_content_path = write_merged(
                        entry.path, verdict.merged_content or ""
                    )
                else:
                    merged_dir = (
                        workspace_root
                        / ".pos"
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
            }
        )
        if halt_reason is not None:
            summary_attrs["pos.sync.merge_gate.halt_reason"] = halt_reason
        with otel_span(
            "pos.sync.merge_gate.summary", summary_attrs
        ):
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
                status = SyncStatus.SUCCESS

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
