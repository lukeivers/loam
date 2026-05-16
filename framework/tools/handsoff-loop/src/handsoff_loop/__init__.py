"""handsoff-loop — the real orchestrated hands-off loop, packaged.

This package is loam's own build methodology run for the user, as a
single primary-persona-invocable capability:

    plain-language intent
        -> intake (elicit-the-minimum, plain-language acceptance,
           one approval gate)              [AC.B.1 .. AC.B.4]
        -> freeze a machine-checkable acceptance, hash-pinned,
           sub-agent-unseen                [AC.A.2]
        -> decompose into scoped sub-tasks (probe-proven pattern,
           NOT re-proved here)             [AC.FOUND.0, AC.A.1]
        -> dispatch real `claude -p` sub-agents, /goal drives the
           keep-going leg                  [AC.A.1, AC.A.4(i)]
        -> independent tool-executing judge + anti-overfit held-out
           check decides "done"            [AC.A.3]
        -> honest done / dead verdict      [AC.A.4, AC.B.5]

AC.FOUND.0 (fence guard): the decompose -> scoped-dispatch -> judge
loop is taken as ESTABLISHED by the Tier-0 probe. Nothing in this
package re-proves it at unit scale; the package COMPOSES the proven
mechanism and tests only the two open unknowns (packaging fidelity =
Phase A, intent->checkable-done = Phase B).

NO Anthropic API key: every model call is a real `claude` binary
subprocess, default Sonnet (feedback_no_anthropic_api_key).
"""

from __future__ import annotations

from .verify import FrozenAcceptance, VerifyResult, freeze_acceptance, verify
from .intake import IntakeOutcome, derive_acceptance_from_intent
from .goal_drive import GoalDriveSpec, build_goal_drive_argv
from .orchestrator import (
    HandsoffResult,
    PhaseVerdict,
    SubTask,
    run_handsoff_loop,
)

__all__ = [
    "FrozenAcceptance",
    "VerifyResult",
    "freeze_acceptance",
    "verify",
    "IntakeOutcome",
    "derive_acceptance_from_intent",
    "GoalDriveSpec",
    "build_goal_drive_argv",
    "HandsoffResult",
    "PhaseVerdict",
    "SubTask",
    "run_handsoff_loop",
]
