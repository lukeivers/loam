"""Lazy-projection trigger — entry point the loam-mode session-start
emitter calls each session.

Per plan §6 constraint 13 (read-only consumer of A's signal) + §6
constraint 14 (idempotency-as-guard):

- Reads the workspace's ``dev_intent`` answer via loam-mode's
  ``read_dev_intent_safe`` (already in dev-discipline territory; no
  sealed-component import).
- If ``dev_intent != "yes"`` returns immediately — the trigger is a
  no-op on user-mode workspaces.
- If dev-mode, runs ``run_phases`` against the workspace's tracker
  DB. The phases are themselves idempotent via ``lifted_from``, so
  the call is cheap on already-projected workspaces.

Fail-soft contract: every exception is caught + recorded in the
result; the trigger never raises out to the caller (the loam-mode
emitter's AC.B5 fail-soft contract extends through this trigger).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from loam.heavy_b_migrate.runner import RunReport, run_phases


TRACKER_DB_FILENAME = "objective_tracker.sqlite"


@dataclass(frozen=True)
class TriggerResult:
    """Outcome of one ``run_if_dev_intent`` call.

    ``ran`` — True iff the phase runner was invoked.
    ``skipped_reason`` — populated when ``ran`` is False
        (``"not-dev-intent"`` / ``"absent-or-no"`` / ``"error: ..."``).
    ``run_report`` — the ``RunReport`` from the runner when it ran;
        None otherwise.
    """

    ran: bool
    skipped_reason: str | None
    run_report: RunReport | None


def run_if_dev_intent(workspace_root: Path | str) -> TriggerResult:
    """Run the phase migration if the workspace is dev-intent.

    Idempotency-by-`lifted_from` handles the "already projected" case
    inside the phases — no separate sentinel check is needed.

    Never raises: every exception is caught and surfaced in the result.
    The loam-mode session-start emitter relies on this fail-soft
    contract (AC.B5 extended).
    """
    try:
        return _run_if_dev_intent_inner(Path(workspace_root))
    except Exception as exc:  # noqa: BLE001 — fail-soft per §6 constraint 13/14
        return TriggerResult(
            ran=False,
            skipped_reason=f"error: {type(exc).__name__}: {exc}",
            run_report=None,
        )


def _run_if_dev_intent_inner(workspace_root: Path) -> TriggerResult:
    # Late import — avoid coupling heavy-b-migrate's import graph to
    # loam-mode at package-load time. Both tools are dev-discipline so
    # the import does not cross a sealed-component fence; the lateness
    # is purely about install-time independence.
    from loam_mode.session_start import read_dev_intent_safe

    intent = read_dev_intent_safe(workspace_root)
    if intent != "yes":
        return TriggerResult(
            ran=False,
            skipped_reason="not-dev-intent" if intent == "no" else "absent-or-no",
            run_report=None,
        )

    tracker_db = workspace_root / TRACKER_DB_FILENAME
    if not tracker_db.exists():
        # Tracker not yet seeded — workspace-bootstrap (#39) hasn't run
        # yet on this checkout. Skip; the next first-run scaffold will
        # seed and the next session will project.
        return TriggerResult(
            ran=False,
            skipped_reason="tracker-not-seeded",
            run_report=None,
        )

    report = run_phases(workspace_root, tracker_db)
    return TriggerResult(ran=True, skipped_reason=None, run_report=report)
