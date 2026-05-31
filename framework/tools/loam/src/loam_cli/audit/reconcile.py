"""The FBM stored-claim-vs-truth entry point (AC.SOL-RECONCILE.*).

The subsumption: the SAME comparator that detects a doc's stale status
ALSO detects a stored FBM memory claim that contradicts current ground
truth — ONE detector, two callers (roadmap §6 redundancy note: build
as one mechanism, two entry points, not two parallel tracks). This is
the second caller; it passes a stored claim instead of a doc claim
through :func:`comparator.compare_claim`.

Scope (per plan §10 item 4): a CHECKABLE stored claim — one that names
a verifiable ground-truth fact (a component's built/dark status). A
stored episode that carries no checkable status is OUT of scope (it is
surfaced, owner rules — ``feedback_notes_and_users_are_pointers``); the
fold is "one comparator, two callers", not "the comparator handles all
of memory".

The reconcile OUTPUT is dated + scoped to the check, never stored as an
eternal claim (AC.SOL-RECONCILE.2 —
``feedback_notes_and_users_are_pointers_evidence_resolves``: a memory
must never store an eternal negative; the reconcile result is a dated,
scoped finding, so it cannot itself become the next stale claim).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from loam_cli.audit.comparator import ClaimedStatus, Divergence, compare_claim
from loam_cli.audit.record import StateOfLoam


@dataclass(frozen=True)
class StoredClaim:
    """A checkable stored-memory claim.

    *component* names the subject the claim is about; *claim_token* is
    the asserted status (``"dark"`` / ``"live"`` / ...); *episode_id*
    identifies the stored episode for provenance.
    """

    component: str
    claim_token: str
    episode_id: str


@dataclass(frozen=True)
class ReconcileFinding:
    """A dated, scoped reconcile finding (AC.SOL-RECONCILE.2).

    NEVER an eternal claim: it carries the date the check ran + the
    scope (which episode, which component) so the finding cannot become
    the next stale claim. *divergence* is ``None`` when the stored claim
    agrees with ground truth (reconciled clean).
    """

    episode_id: str
    component: str
    checked_on: str
    divergence: Divergence | None

    @property
    def diverged(self) -> bool:
        return self.divergence is not None

    def render(self) -> str:
        if self.divergence is None:
            return (
                f"[{self.checked_on}] episode {self.episode_id}: claim about "
                f"{self.component} RECONCILES with ground truth (no divergence "
                f"as of this dated check)."
            )
        return (
            f"[{self.checked_on}] episode {self.episode_id}: DIVERGENCE — "
            f"{self.divergence.detail}"
        )


def reconcile_stored_claim(
    claim: StoredClaim,
    record: StateOfLoam,
    *,
    checked_on: str | None = None,
) -> ReconcileFinding:
    """Reconcile one checkable stored claim against the derived record.

    Routes the stored claim through the SAME
    :func:`comparator.compare_claim` the doc-status caller uses — the
    subsumption (AC.SOL-RECONCILE.1). Returns a dated, scoped
    :class:`ReconcileFinding` (AC.SOL-RECONCILE.2); the finding carries
    a divergence iff the stored claim contradicts ground truth.

    *checked_on* defaults to today's ISO date — the dated scope that
    keeps the finding from becoming an eternal negative.
    """
    when = checked_on or date.today().isoformat()
    divergence = compare_claim(
        ClaimedStatus(
            component=claim.component,
            claim_token=claim.claim_token,
            source=f"FBM-episode:{claim.episode_id}",
        ),
        record,
    )
    return ReconcileFinding(
        episode_id=claim.episode_id,
        component=claim.component,
        checked_on=when,
        divergence=divergence,
    )
