"""D8 — rollback: success path + clean-failure path.

Whole-upgrade atomic. On any clause failure post-upgrade OR on user
invocation of ``pos rollback``:

1. Revert symlink to the prior release tree.
2. Restore every substrate snapshot (memory + four SQLite + DuckDB).
3. Restart orchestrator on the prior release (if it had been stopped).
4. Emit ``loam.upgrade.rolled_back`` OTel span.
5. Write ``<tag>-rolled-back.json`` history record.

Failed-rollback path (prototype-only per Luke's ruling) is covered by
``scripts/destructive_test_runbook.sh``; this module just writes the
``<tag>-rollback-failed.json`` and surfaces the Tier 1 notification.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .observability import span as otel_span
from .orchestrator_control import atomic_symlink_swap
from .paths import Paths
from .snapshot import restore_substrate_snapshots, substrate_components


@dataclass
class RollbackReport:
    tag: str
    prior_tag: str | None
    failing_clauses: list[str] = field(default_factory=list)
    clause_details: dict[str, Any] = field(default_factory=dict)
    steps_completed: list[str] = field(default_factory=list)
    steps_failed: list[dict[str, str]] = field(default_factory=list)
    success: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "prior_tag": self.prior_tag,
            "failing_clauses": self.failing_clauses,
            "clause_details": self.clause_details,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "success": self.success,
        }


class RollbackFailed(RuntimeError):
    """Raised when rollback itself fails — the framework is in an
    undefined state and manual recovery is required."""

    def __init__(self, report: RollbackReport) -> None:
        super().__init__(
            f"rollback failed for {report.tag}; "
            f"{len(report.steps_failed)} steps failed"
        )
        self.report = report


def rollback(
    *,
    paths: Paths,
    tag: str,
    prior_tag: str | None,
    failing_clauses: list[str],
    clause_details: dict[str, Any],
    restart_orchestrator: Callable[[], None] | None = None,
) -> RollbackReport:
    """Execute the rollback sequence.

    ``restart_orchestrator`` is the caller-supplied function that runs
    launchctl kickstart against the restored tree. Pass ``None`` when
    the orchestrator was not stopped during the upgrade attempt (e.g.
    rollback invoked before the symlink swap).
    """
    report = RollbackReport(
        tag=tag,
        prior_tag=prior_tag,
        failing_clauses=failing_clauses,
        clause_details=clause_details,
    )

    with otel_span(
        "loam.upgrade.rolled_back",
        {
            "loam.upgrade.tag": tag,
            "loam.upgrade.prior_tag": prior_tag or "",
            "loam.upgrade.failing_clauses": ",".join(failing_clauses),
        },
    ):
        # Step 1: revert symlink to prior release
        if prior_tag is not None:
            try:
                prior_release = paths.release_dir(prior_tag)
                if prior_release.exists():
                    atomic_symlink_swap(paths.current_link, prior_release)
                    report.steps_completed.append("symlink_reverted")
                else:
                    report.steps_failed.append(
                        {
                            "step": "symlink_revert",
                            "error": f"prior release dir missing: {prior_release}",
                        }
                    )
            except Exception as exc:
                report.steps_failed.append(
                    {"step": "symlink_revert", "error": str(exc)}
                )

        # Step 2: restore every substrate snapshot
        try:
            restore_substrate_snapshots(paths, tag)
            report.steps_completed.append("substrates_restored")
        except Exception as exc:
            report.steps_failed.append(
                {"step": "substrate_restore", "error": str(exc)}
            )

        # Step 3: restart orchestrator on prior tree
        if restart_orchestrator is not None:
            try:
                restart_orchestrator()
                report.steps_completed.append("orchestrator_restarted")
            except Exception as exc:
                report.steps_failed.append(
                    {"step": "orchestrator_restart", "error": str(exc)}
                )

        report.success = not report.steps_failed

    # Write the history record
    target = (
        paths.rolled_back_json(tag)
        if report.success
        else paths.history / f"{tag}-rollback-failed.json"
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report.to_dict(), indent=2, default=str))

    if not report.success:
        raise RollbackFailed(report)
    return report
