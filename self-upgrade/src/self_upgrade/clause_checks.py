"""D6 — post-upgrade clause verification (a)–(g).

Each of the seven clauses from v1.1 R1 has a concrete check returning
``ClauseResult`` (either passed or failed with a reason). The framework
runs them in a fixed order; any failure triggers rollback in the caller.

The checks are duck-typed against whatever the caller passes in so
tests can substitute synthetic component instances. In production, the
caller is ``upgrade.py`` which constructs the live instances.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .aggregator_probes import aggregator_probe_hash, run_aggregator_probes
from .manifest import ChangeKind, Manifest, verify_file_against
from .paths import Paths


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
) -> ClauseBundle:
    """Run every clause check. Does not short-circuit: every clause is
    evaluated and reported even when an earlier one fails, because the
    full bundle is what the upgrade report contains."""
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
    return bundle
