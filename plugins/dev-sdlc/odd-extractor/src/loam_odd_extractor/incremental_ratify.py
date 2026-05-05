"""PM enqueue for incremental-mode proposals.

Per AC.WATCH.4 (v0.2.0 Cycle 1) — composes one
`pm_runtime.enqueue_decision(question_text, *, provenance)` call
per **domain-batch** (NOT per-AC).

Provenance string per enqueued question:
``odd-extract:incremental:<extraction_id>:<domain_slug>``.

Idempotent duplicate-skip: if a domain's proposal-set is byte-
identical to a previously-enqueued + still-pending question, the
second enqueue is a no-op.

Per Surface #2 (plan-doc §5) — no PM-side edits; this module
composes through the existing v0.1.7 Cycle 4
``PMRuntime.enqueue_decision`` API. Question-text shape carries the
type identity (mirroring the existing per-AC ratify-flow's
`_question_for_banded_ac`).
"""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import yaml

from .domain_batching import group_by_domain
from .proposals import IncrementalProposal, IncrementalProposalSet


# ---- result type ----------------------------------------------------


@dataclass(frozen=True)
class EnqueueResult:
    """Result of :func:`enqueue_incremental_proposals`."""

    enqueued_domains: tuple[str, ...]
    skipped_duplicates: tuple[str, ...]
    total_proposals: int

    @property
    def enqueued_count(self) -> int:
        return len(self.enqueued_domains)

    @property
    def skipped_count(self) -> int:
        return len(self.skipped_duplicates)


# ---- question-text shape -------------------------------------------


def _format_proposal_line(proposal: IncrementalProposal) -> str:
    """One bullet line per proposal in the domain-batch question.

    Format mirrors the master plan example shape:
      - AC.X.1 (PLAUSIBLE; citation-line-changed): a/b.rb:42-58 → a/b.rb:51-67
      - AC.X.2 (VERIFIED; backing-file-changed): a/c.rb (3 hunks)
      - AC.X.3 (HYPOTHESISED → orphaned): a/d.rb (file deleted)
    """
    band = proposal.confidence_band.value
    drift = proposal.drift_kind
    if drift == "orphaned":
        files = ", ".join(proposal.affected_files) or "(no files)"
        return (
            f"  - {proposal.ac_id} ({band} → orphaned): "
            f"{files} (file deleted)"
        )
    files = ", ".join(proposal.affected_files) or "(no files)"
    drift_label = drift.replace("_", "-")
    return (
        f"  - {proposal.ac_id} ({band}; {drift_label}): {files}"
    )


def _format_domain_question(
    *,
    domain: str,
    proposals: list[IncrementalProposal],
    prior_repo_sha: str | None,
    current_repo_sha: str,
) -> str:
    """Compose the user-facing question text for one domain-batch.

    Plan-doc §10 F2 RF #5: bound at 25 ACs with truncation suffix
    `... (and N more)`. Reviewer can request the full set via
    revise-flow.
    """
    truncate_at = 25
    n = len(proposals)
    visible = proposals[:truncate_at]
    truncated = n - len(visible)

    prior_short = (prior_repo_sha or "<no-sha>")[:8]
    curr_short = (current_repo_sha or "<no-sha>")[:8]

    lines: list[str] = []
    lines.append(
        f"Domain '{domain}' has {n} AC re-extraction "
        f"proposal{'s' if n != 1 else ''} (drift detected since "
        f"{prior_short} → {curr_short}):"
    )
    for p in visible:
        lines.append(_format_proposal_line(p))
    if truncated > 0:
        lines.append(
            f"  ... (and {truncated} more — request revise-flow "
            f"for full list)"
        )
    lines.append("")
    lines.append(
        "Reply with: ratify-all / revise-each / reject-all (or per-AC: "
        "AC.X.1=ratify AC.X.2=revise<text> AC.X.3=keep). Note: "
        "PLAUSIBLE→VERIFIED requires explicit confirmation per "
        "Decision I."
    )
    return "\n".join(lines)


def _provenance_for(extraction_id: str, domain: str) -> str:
    """Provenance string per AC.WATCH.4."""
    return f"odd-extract:incremental:{extraction_id}:{domain}"


# ---- duplicate detection -------------------------------------------


def _existing_pending_provenances(pm_dir: Path) -> set[str]:
    """Read the PM's `decision-queue.yaml` and return the set of
    provenance strings of still-pending questions.

    Returns empty set if the queue file is missing or malformed.
    Used for idempotent duplicate-skip detection.
    """
    queue_path = pm_dir / "decision-queue.yaml"
    if not queue_path.exists():
        return set()
    try:
        data = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    except yaml.YAMLError:
        return set()
    if not isinstance(data, dict):
        return set()
    queue = data.get("queue") or []
    if not isinstance(queue, list):
        return set()
    out: set[str] = set()
    for entry in queue:
        if not isinstance(entry, dict):
            continue
        prov = entry.get("provenance")
        if isinstance(prov, str) and prov:
            out.add(prov)
    return out


# ---- main entry-point -----------------------------------------------


def enqueue_incremental_proposals(
    *,
    proposal_set: IncrementalProposalSet,
    workspace_root: Path,
    pm_runtime,  # PMRuntime — duck-typed to avoid circular import
    pm_handle: str,
) -> EnqueueResult:
    """Enqueue one PM decision-question per domain-batch.

    Per AC.WATCH.4 — for each domain in `group_by_domain(proposals)`:

      - Compose the question text (one bullet per proposal in the
        domain).
      - Compose the provenance string
        (``odd-extract:incremental:<extraction_id>:<domain>``).
      - Check whether the provenance string is already in the PM's
        pending queue (idempotent duplicate-skip).
      - If not, call ``pm_runtime.enqueue_decision(question_text,
        provenance=...)``.

    Returns an :class:`EnqueueResult` with per-domain enqueue +
    skipped lists.

    Idempotent: re-running with the same proposal set against the
    same PM queue produces ``enqueued_domains=()`` +
    ``skipped_duplicates=<all domains>``.
    """
    if not proposal_set.proposals:
        return EnqueueResult(
            enqueued_domains=(),
            skipped_duplicates=(),
            total_proposals=0,
        )

    domain_buckets: OrderedDict[str, list[IncrementalProposal]] = (
        group_by_domain(list(proposal_set.proposals))
    )

    # Read existing PM queue's provenance strings for duplicate-skip.
    pm_dir = pm_runtime._pm_dir  # type: ignore[attr-defined]
    existing_provs = _existing_pending_provenances(pm_dir)

    enqueued: list[str] = []
    skipped: list[str] = []
    for domain, props in domain_buckets.items():
        prov = _provenance_for(proposal_set.extraction_id, domain)
        if prov in existing_provs:
            skipped.append(domain)
            continue
        question_text = _format_domain_question(
            domain=domain,
            proposals=props,
            prior_repo_sha=proposal_set.prior_repo_sha,
            current_repo_sha=proposal_set.current_repo_sha,
        )
        pm_runtime.enqueue_decision(question_text, provenance=prov)
        enqueued.append(domain)

    return EnqueueResult(
        enqueued_domains=tuple(enqueued),
        skipped_duplicates=tuple(skipped),
        total_proposals=len(proposal_set.proposals),
    )
