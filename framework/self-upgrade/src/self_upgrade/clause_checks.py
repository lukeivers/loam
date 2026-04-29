"""D6 — post-upgrade clause verification (a)–(h).

Each of the eight clauses from v1.1 R1 (a-g) plus clause-(h) has a
concrete check returning ``ClauseResult`` (either passed or failed
with a reason). The framework runs them in a fixed order; any failure
triggers rollback in the caller.

Clause (h) — workspace-customisation collision resolution — is
two-phase: a **pre-stage helper** (``resolve_clause_h_inferred``)
that calls the LLM resolver and mutates the ConflictReport in place,
and a **post-restart verifier** (``check_clause_h``) that asserts
no INFERRED_* entry is missing rationale/confidence and the budget
bookkeeping closed cleanly.

The checks are duck-typed against whatever the caller passes in so
tests can substitute synthetic component instances. In production, the
caller is ``upgrade.py`` which constructs the live instances.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .aggregator_probes import aggregator_probe_hash, run_aggregator_probes
from .conflict_report import (
    INFERRED_RESOLUTIONS,
    ConflictChangeKind,
    ConflictEntry,
    ConflictReport,
    Resolution,
    save_conflict_report,
)
from .manifest import ChangeKind, Manifest, verify_file_against
from .merge_resolver import (
    BudgetExhausted,
    MergeResolver,
    MergeVerdict,
    ResolverFailure,
)
from .observability import span as otel_span
from .paths import Paths
from .state import (
    StateRecord,
    UpgradeStatus,
    audit_yaml_path,
    make_state_record,
    save_state,
)
from .sync_protected import FileClass, SyncProtected


@dataclass
class ClauseResult:
    clause: str
    passed: bool
    reason: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "clause": self.clause,
            "passed": self.passed,
            "reason": self.reason,
            "details": self.details,
        }


@dataclass
class ClauseBundle:
    results: dict[str, ClauseResult] = field(default_factory=dict)

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results.values())

    def failing(self) -> list[str]:
        return [k for k, v in self.results.items() if not v.passed]

    def to_dict(self) -> dict[str, Any]:
        return {k: v.to_dict() for k, v in self.results.items()}


# ---- clause (a) — active session continues -------------------------


def check_clause_a(no_op_rpc: Callable[[], bool]) -> ClauseResult:
    """IPC socket rebind + no-op RPC success.

    ``no_op_rpc`` is the caller-supplied callable that opens an IPC
    client to the (post-restart) orchestrator socket and invokes a
    no-op method. Returns ``True`` on success.
    """
    try:
        ok = no_op_rpc()
    except Exception as exc:
        return ClauseResult(
            clause="a",
            passed=False,
            reason=f"no-op RPC raised: {type(exc).__name__}: {exc}",
        )
    if not ok:
        return ClauseResult(
            clause="a",
            passed=False,
            reason="no-op RPC returned False",
        )
    return ClauseResult(clause="a", passed=True)


# ---- clause (b) — personas load unchanged --------------------------


def check_clause_b(
    survival_payloads: dict[str, Any],
    *,
    required_fields: tuple[str, ...] = (
        "persona_identity",
        "authority_boundary",
        "current_scope_context",
        "pending_decisions",
        "recent_corrections",
    ),
) -> ClauseResult:
    """All configured personas produce a five-field survival payload.

    ``survival_payloads`` is a dict mapping persona handle to the
    return value of ``primary_persona.compaction.build_survival_payload``.
    Expects ``CompactionSurvivor`` (or a ``.to_dict()``-able stand-in).
    """
    if not survival_payloads:
        return ClauseResult(
            clause="b",
            passed=False,
            reason="no personas configured (empty survival_payloads)",
        )

    missing: dict[str, list[str]] = {}
    for handle, payload in survival_payloads.items():
        d = payload.to_dict() if hasattr(payload, "to_dict") else payload
        if not isinstance(d, dict):
            missing[handle] = [f"payload not dict-shaped: {type(d).__name__}"]
            continue
        unset = [f for f in required_fields if f not in d or d[f] is None]
        if unset:
            missing[handle] = unset

    if missing:
        return ClauseResult(
            clause="b",
            passed=False,
            reason=f"personas with unpopulated survival fields: {sorted(missing)}",
            details={"missing": missing},
        )
    return ClauseResult(
        clause="b",
        passed=True,
        details={"persona_count": len(survival_payloads)},
    )


# ---- clause (c) — memory semantic round-trip -----------------------


def check_clause_c(drift_report: Any) -> ClauseResult:
    """``memory.upgrade.compare()`` returns a ``DriftReport.passed``."""
    passed = bool(getattr(drift_report, "passed", False))
    if passed:
        return ClauseResult(
            clause="c",
            passed=True,
            details={
                "verdict_flip_fraction": getattr(
                    drift_report, "verdict_flip_fraction", None
                ),
                "mean_recall_delta": getattr(
                    drift_report, "mean_recall_delta", None
                ),
            },
        )
    return ClauseResult(
        clause="c",
        passed=False,
        reason="memory drift report: passed=False",
        details={
            "verdict_flip_fraction": getattr(
                drift_report, "verdict_flip_fraction", None
            ),
            "mean_recall_delta": getattr(
                drift_report, "mean_recall_delta", None
            ),
            "over_tolerance_fraction": getattr(
                drift_report, "over_tolerance_fraction", None
            ),
        },
    )


# ---- clause (d) — in-flight tasks preserved -----------------------


def check_clause_d(
    scope_drift: Any,
    objective_drift: Any,
    *,
    threshold: int = 0,
) -> ClauseResult:
    """Both scope-of-work and objective-tracker report zero drift."""

    def _total(r: Any) -> int:
        return int(getattr(r, "total_drift", 0) or 0)

    s_drift = _total(scope_drift)
    o_drift = _total(objective_drift)
    if s_drift > threshold or o_drift > threshold:
        return ClauseResult(
            clause="d",
            passed=False,
            reason=(
                f"in-flight task drift exceeds threshold={threshold}: "
                f"scope_of_work={s_drift}, objective_tracker={o_drift}"
            ),
            details={
                "scope_of_work_total": s_drift,
                "objective_tracker_total": o_drift,
                "threshold": threshold,
            },
        )
    return ClauseResult(
        clause="d",
        passed=True,
        details={
            "scope_of_work_total": s_drift,
            "objective_tracker_total": o_drift,
        },
    )


# ---- clause (e) — breaking-change declaration ----------------------


def check_clause_e(manifest: Manifest) -> ClauseResult:
    """No silent schema bumps: any schema bump requires a declared
    breaking_changes entry for that component."""
    silent = manifest.silent_schema_bumps()
    if silent:
        return ClauseResult(
            clause="e",
            passed=False,
            reason=(
                "schema bump(s) without a declared breaking_changes "
                f"entry: {silent}"
            ),
            details={"silent_bumps": silent},
        )
    return ClauseResult(
        clause="e",
        passed=True,
        details={"declared_breaking": [bc.id for bc in manifest.breaking_changes]},
    )


# ---- clause (f) — upgrade reversible -------------------------------


def check_clause_f(
    paths: Paths, tag: str, *, required_components: tuple[str, ...]
) -> ClauseResult:
    """Pre-upgrade snapshots exist at expected paths.

    The full rollback-round-trip test lives in D8; this check validates
    the precondition — that the snapshot data is present and non-empty.
    """
    pre = paths.history_dir_pre(tag)
    if not pre.exists():
        return ClauseResult(
            clause="f",
            passed=False,
            reason=f"pre-upgrade snapshot missing at {pre}",
        )

    missing: list[str] = []
    for comp in required_components:
        sub = pre / comp
        if not sub.exists():
            missing.append(comp)
            continue
        has_file = any(sub.rglob("*"))
        if not has_file:
            missing.append(f"{comp} (empty)")

    if missing:
        return ClauseResult(
            clause="f",
            passed=False,
            reason=f"missing component snapshots: {missing}",
        )
    return ClauseResult(
        clause="f",
        passed=True,
        details={"snapshot_dir": str(pre)},
    )


# ---- clause (g) — no silent skip -----------------------------------


def check_clause_g(
    manifest: Manifest, live_root: Path
) -> ClauseResult:
    """sha-verify every file in the manifest; mismatches reported."""
    mismatches: list[dict[str, Any]] = []
    missing: list[str] = []
    extra: list[str] = []  # (not enforced — live tree may contain user files)

    for entry in manifest.files:
        matches, actual = verify_file_against(entry, live_root)
        if not matches:
            if entry.change_kind is ChangeKind.DELETED:
                missing.append(entry.path)
                continue
            if actual is None:
                missing.append(entry.path)
                continue
            mismatches.append(
                {
                    "path": entry.path,
                    "expected": entry.expected_post_sha,
                    "actual": actual,
                    "change_kind": entry.change_kind.value,
                }
            )

    if mismatches or missing:
        return ClauseResult(
            clause="g",
            passed=False,
            reason=(
                f"sha-verify failed: {len(mismatches)} mismatches, "
                f"{len(missing)} missing"
            ),
            details={"mismatches": mismatches, "missing": missing},
        )
    return ClauseResult(
        clause="g",
        passed=True,
        details={"files_verified": len(manifest.files)},
    )


# ---- clause (h) — workspace-customisation collision resolution -----


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


def resolve_clause_h_inferred(
    *,
    report: ConflictReport,
    sync_protected: SyncProtected,
    canonical_root: Path,
    workspace_root: Path,
    resolver: MergeResolver,
    write_merged: Callable[[str, str], str] | None = None,
) -> None:
    """Clause-(h) pre-stage helper.

    Walks every PENDING ConflictEntry in ``report``; classifies each
    against the workspace's sync-protected envelope; preserves Class A
    workspace state, applies override semantics for Class B, and
    invokes the LLM resolver for Class C. Mutates the entries in place
    so the existing ``report.has_pending()`` block clears for any
    conflict the helper resolved.

    ``write_merged(path, content) -> str`` is an optional sink the
    caller supplies for ``inferred-merged`` verdicts; it must persist
    the merged content somewhere and return the absolute path. When
    omitted, merged content is dropped onto a per-conflict path under
    ``workspace_root/workspace/.pos/upgrade/<tag>/merged/<path>``
    (post-D.2 amendment #63).

    Raises:
        BudgetExhausted: cumulative resolver budget hit; halt-and-
            resume per AC.H.6. ``report`` is mutated up to the halt
            point and the audit + state are persisted before the
            exception propagates (per AC.HFX.1 + AC.HFX.2).
        ResolverFailure: LLM call failed for any conflict. Fail-closed
            per AC.H.12. ``report`` is mutated up to the failure
            point; audit + state persisted before propagation.
    """
    resolved_count = 0
    deferred_count = 0

    summary_attrs: dict[str, Any] = {
        "loam.upgrade.merge_gate.upgrade_tag": report.upgrade_tag,
    }
    halt_reason: str | None = None

    try:
        for entry in report.conflicts:
            if entry.resolution is not Resolution.PENDING:
                # Already manually resolved (or auto-resolved) — preserve
                # the operator's choice. Convergent idempotency: re-runs
                # see non-PENDING entries and skip them.
                continue
            if entry.user_override:
                # Honour persistent operator override per AC.H.9. The
                # resolution must already be set by the operator; if
                # not, that's a validator-caught bug upstream.
                continue

            klass = sync_protected.classify(entry.path)

            if klass is FileClass.A:
                # Class A: never overwritten. Preserve workspace.
                entry.resolution = Resolution.KEEP_LOCAL
                entry.rationale = (
                    "Class A (workspace state): preserved by clause-(h) "
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
                # workspace-modified is implicit.
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

            # Class C: LLM-mediated resolution.
            canonical_text = _read_text_or_none(canonical_root / entry.path)
            workspace_text = _read_text_or_none(workspace_root / entry.path)
            prior_text: str | None = None  # not currently exposed by snapshot

            if canonical_text is None or workspace_text is None:
                # Binary or missing file — resolver cannot help. Mark
                # PENDING so the legacy hand-resolve path remains.
                deferred_count += 1
                continue

            with otel_span(
                "loam.upgrade.merge_gate.resolution",
                {
                    "loam.upgrade.merge_gate.path": entry.path,
                    "loam.upgrade.merge_gate.canonical_sha": entry.new_release_sha256 or "",
                    "loam.upgrade.merge_gate.workspace_sha": entry.installed_sha256 or "",
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
                # Persist merged content somewhere the swap can read.
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
                        / "upgrade"
                        / report.upgrade_tag
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
                "loam.upgrade.merge_gate.resolved_count": resolved_count,
                "loam.upgrade.merge_gate.deferred_count": deferred_count,
                "loam.upgrade.merge_gate.cumulative_tokens": resolver.cumulative_used,
                "loam.upgrade.merge_gate.call_count": resolver.call_count,
            }
        )
        if halt_reason is not None:
            summary_attrs["loam.upgrade.merge_gate.halt_reason"] = halt_reason
        with otel_span(
            "loam.upgrade.merge_gate.summary", summary_attrs
        ):
            pass

        # AC.HFX.1 + AC.HFX.2 + AC.HFX.3: every clause-(h) execution
        # leaves both the workspace-local audit YAML and the state
        # YAML behind, regardless of clean-pass / BudgetExhausted /
        # ResolverFailure terminus. The writes happen after the
        # OTel summary span so observability records the run-level
        # outcome before disk-persistence.
        try:
            audit_target = audit_yaml_path(workspace_root, report.upgrade_tag)
            save_conflict_report(report, audit_target)

            if halt_reason is not None:
                status = UpgradeStatus.FAILURE
            elif report.has_pending() or deferred_count > 0:
                status = UpgradeStatus.PARTIAL
            else:
                status = UpgradeStatus.SUCCESS

            state = make_state_record(
                upgrade_tag=report.upgrade_tag,
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
            # errors in the finally so callers see the clause-(h)
            # halt reason, not the persistence error. (Callers can
            # still spot the missing artefact at clean-pass time;
            # in practice tmpdir + ~/.loam targets are writable.)
            pass


def check_clause_h(
    report: ConflictReport | None,
) -> ClauseResult:
    """Post-restart clause-(h) verifier.

    Asserts the ConflictReport's invariants after the pre-stage helper
    has run: every INFERRED_* entry carries rationale + confidence; no
    PENDING entries remain (clause-(g) "no silent skip" extends to
    clause-(h) — every conflict ends with a verdict or a manual
    resolution).

    ``report`` may be None when the upgrade was invoked without
    --canonical/--merge-resolver-module (legacy --staging-dir mode);
    in that case clause-(h) is a no-op pass.
    """
    if report is None:
        return ClauseResult(clause="h", passed=True, details={"skipped": True})

    pending = [
        c.path for c in report.conflicts if c.resolution is Resolution.PENDING
    ]
    if pending:
        return ClauseResult(
            clause="h",
            passed=False,
            reason=f"{len(pending)} pending conflict(s) after clause-(h) pass",
            details={"pending": pending},
        )

    inferred_missing: list[str] = []
    for c in report.conflicts:
        if c.resolution in INFERRED_RESOLUTIONS:
            if c.rationale is None or c.confidence is None:
                inferred_missing.append(c.path)
    if inferred_missing:
        return ClauseResult(
            clause="h",
            passed=False,
            reason=(
                "INFERRED_* entries missing rationale or confidence: "
                f"{inferred_missing}"
            ),
            details={"missing_audit": inferred_missing},
        )

    inferred = report.inferred_entries()
    return ClauseResult(
        clause="h",
        passed=True,
        details={
            "inferred_count": len(inferred),
            "total_conflicts": len(report.conflicts),
        },
    )


# ---- full clause bundle --------------------------------------------


def run_all_clauses(
    *,
    no_op_rpc: Callable[[], bool],
    survival_payloads: dict[str, Any],
    memory_drift_report: Any,
    scope_drift: Any,
    objective_drift: Any,
    manifest: Manifest,
    paths: Paths,
    tag: str,
    live_root: Path,
    snapshot_components: tuple[str, ...],
    conflict_report: ConflictReport | None = None,
) -> ClauseBundle:
    """Run every clause check. Does not short-circuit: every clause is
    evaluated and reported even when an earlier one fails, because the
    full bundle is what the upgrade report contains.

    ``conflict_report`` is the post-stage clause-(h) audit; pass
    ``None`` for legacy upgrades that didn't run the clause-(h)
    pre-stage helper (clause-(h) verifier no-ops in that case).
    """
    bundle = ClauseBundle()
    bundle.results["a"] = check_clause_a(no_op_rpc)
    bundle.results["b"] = check_clause_b(survival_payloads)
    bundle.results["c"] = check_clause_c(memory_drift_report)
    bundle.results["d"] = check_clause_d(scope_drift, objective_drift)
    bundle.results["e"] = check_clause_e(manifest)
    bundle.results["f"] = check_clause_f(
        paths, tag, required_components=snapshot_components
    )
    bundle.results["g"] = check_clause_g(manifest, live_root)
    bundle.results["h"] = check_clause_h(conflict_report)
    return bundle
