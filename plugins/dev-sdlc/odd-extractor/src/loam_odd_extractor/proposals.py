"""Re-extraction proposal generation for incremental-mode watch.

Per AC.WATCH.3 (v0.2.0 Cycle 1) — for each `OutOfDateAC` from the
diff_classifier output, generate a structured proposal carrying:

  - `ac_id`
  - `current_evidence` — the prior contract's evidence block
  - `proposed_new_evidence` — fresh evidence with current `repo_sha`
    pin (None for orphaned-AC proposals)
  - `confidence_band` — preserved from prior; Decision I default-no
    forbids silent promotion
  - `drift_kind` — `citation_line_changed` / `backing_file_changed`
    / `orphaned`
  - `affected_files` — files that triggered the drift detection

Cycle 1 simplification: re-extraction does NOT re-invoke the v0.1.8
full-mode workflow inline (that would require adapter integration
which is heavy). Instead, the proposal carries fresh-evidence
metadata (current `repo_sha`, refreshed line ranges where derivable)
and the reviewer ratifies via PM. The full-mode re-invocation is
left to the reviewer's response (e.g., "ratify with re-extracted
evidence"). The persona-side flow re-invokes `analyze_repo` /
`generate_raw_acs` / `verify_contract` scoped to `affected_files` if
the response requires it.

Per F2 RF gap #10 (plan-doc §10) — Cycle 1's full-mode (v0.1.8)
ships zero language adapters that produce real ACs in non-fixture
cases; the synthetic-banded-contract.yaml fixture is hand-authored.
The smoke against synthetic prior-contract uses hand-authored
proposed evidence; the engine path that re-invokes verify_contract
is exercised but the evidence content is fixture-driven.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .bands import BandedAC, ConfidenceBand, Evidence
from .diff_classifier import (
    EvidenceClassification,
    OrphanedAC,
    OutOfDateAC,
)


DriftKind = Literal[
    "citation_line_changed", "backing_file_changed", "orphaned"
]


@dataclass(frozen=True)
class IncrementalProposal:
    """One re-extraction proposal for an AC that drifted.

    Frozen dataclass — `IncrementalProposal` instances are immutable
    once constructed; mutation happens by building a new instance.

    Fields:

    - `ac` — the AC's typed banded representation (preserved from
      prior contract for reviewer reference + domain inference).
    - `ac_id` — convenience accessor; equals `ac.ac_id`.
    - `current_evidence` — the prior contract's evidence block.
    - `proposed_new_evidence` — fresh evidence with current
      `repo_sha`; `None` for orphaned-AC proposals.
    - `confidence_band` — preserved from prior (Decision I).
    - `drift_kind` — one of the three discriminants.
    - `affected_files` — sorted, deduplicated list of files that
      triggered drift detection.
    """

    ac: BandedAC
    current_evidence: Evidence
    proposed_new_evidence: Evidence | None
    confidence_band: ConfidenceBand
    drift_kind: DriftKind
    affected_files: tuple[str, ...] = field(default_factory=tuple)

    @property
    def ac_id(self) -> str:
        return self.ac.ac_id


@dataclass(frozen=True)
class IncrementalProposalSet:
    """The full set of proposals for one watch run.

    Per AC.WATCH.3 — carries the metadata needed for downstream
    domain-batching + PM enqueue + audit-log entries.
    """

    extraction_id: str
    proposals: tuple[IncrementalProposal, ...]
    prior_repo_sha: str | None
    current_repo_sha: str
    generated_at: str  # ISO 8601 with timezone

    @property
    def proposal_count(self) -> int:
        return len(self.proposals)


def _propose_for_out_of_date(
    out_of_date: OutOfDateAC,
    *,
    current_repo_sha: str,
) -> IncrementalProposal:
    """Generate a proposal for an out-of-date AC.

    Cycle 1 builds proposed evidence by:

      - Preserving the prior `kind` (test/source/inference) — band
        determines kind; band is preserved.
      - Setting `repo_sha` to the current HEAD SHA (the watch's
        observed `to_sha`).
      - Preserving citations + rationale verbatim from prior — the
        reviewer ratifies whether the citations need updating; the
        watch doesn't speculate on new line ranges. (A future
        amendment may add citation-range refresh from diff hunks;
        Cycle 1 keeps the citations stable so reviewer revises
        explicitly when desired.)

    This is a structural placeholder — the per-band evidence
    invariants are preserved (PLAUSIBLE keeps `kind=source` +
    citations; VERIFIED keeps `kind=test` + repo_sha + citations;
    HYPOTHESISED keeps `kind=inference` + rationale).
    """
    prior_evidence = out_of_date.ac.evidence
    band = out_of_date.ac.confidence
    # Per-band evidence reconstruction — bands enforce invariants
    # via Pydantic model_validator; we satisfy them by preserving
    # the prior kind + filling SHA where applicable.
    if band is ConfidenceBand.VERIFIED:
        proposed = Evidence(
            kind="test",
            citations=prior_evidence.citations,
            repo_sha=current_repo_sha,
            rationale=prior_evidence.rationale,
        )
    elif band is ConfidenceBand.PLAUSIBLE:
        proposed = Evidence(
            kind="source",
            citations=prior_evidence.citations,
            repo_sha=current_repo_sha,
            rationale=prior_evidence.rationale,
        )
    else:  # HYPOTHESISED
        proposed = Evidence(
            kind="inference",
            citations=prior_evidence.citations,
            repo_sha=current_repo_sha,
            rationale=prior_evidence.rationale,
        )
    return IncrementalProposal(
        ac=out_of_date.ac,
        current_evidence=prior_evidence,
        proposed_new_evidence=proposed,
        confidence_band=band,
        drift_kind=out_of_date.drift_kind,
        affected_files=tuple(
            sorted({str(p) for p in out_of_date.affected_files})
        ),
    )


def _propose_for_orphan(orphan: OrphanedAC) -> IncrementalProposal:
    """Generate a proposal for an orphaned AC (file deleted).

    No `proposed_new_evidence` — reviewer's options are
    keep / reject / re-extract-with-new-evidence. The proposal
    surfaces the missing files so the reviewer has context.
    """
    return IncrementalProposal(
        ac=orphan.ac,
        current_evidence=orphan.ac.evidence,
        proposed_new_evidence=None,
        confidence_band=orphan.ac.confidence,
        drift_kind="orphaned",
        affected_files=tuple(
            sorted({str(p) for p in orphan.missing_files})
        ),
    )


def generate_proposals(
    classification: EvidenceClassification,
    *,
    extraction_id: str,
    prior_repo_sha: str | None,
    current_repo_sha: str,
    generated_at: str,
) -> IncrementalProposalSet:
    """Generate the full proposal set from a classification result.

    Per AC.WATCH.3 — one proposal per out-of-date AC + one proposal
    per orphan AC. Still-current ACs do NOT generate proposals.

    Returns a sorted (by ac_id) tuple of proposals so the output is
    deterministic for fixed input.
    """
    proposals: list[IncrementalProposal] = []
    for ood in classification.out_of_date:
        proposals.append(
            _propose_for_out_of_date(
                ood,
                current_repo_sha=current_repo_sha,
            )
        )
    for orphan in classification.orphaned:
        proposals.append(_propose_for_orphan(orphan))
    # Sort by ac_id for determinism — load-bearing for AC.WATCH.4
    # idempotency check (same input → same proposal order → same
    # domain-grouping → same enqueue).
    proposals.sort(key=lambda p: p.ac_id)
    return IncrementalProposalSet(
        extraction_id=extraction_id,
        proposals=tuple(proposals),
        prior_repo_sha=prior_repo_sha,
        current_repo_sha=current_repo_sha,
        generated_at=generated_at,
    )
