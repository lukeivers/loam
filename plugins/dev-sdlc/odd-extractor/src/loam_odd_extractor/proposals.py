"""Re-extraction proposal generation for incremental-mode watch.

Per AC.WATCHOBJ.2 (v0.2.3 Cycle 3) — for each :class:`OutOfDateObjective`
or :class:`OrphanedObjective` from the diff_classifier output,
generate a structured proposal carrying:

  - ``objective_id``
  - ``current_evidence`` — the prior objective's ObjectiveEvidence block
  - ``proposed_new_evidence`` — fresh ObjectiveEvidence with current
    ``repo_sha`` (None for orphaned)
  - ``confidence_band`` — preserved from prior; Decision I default-no
    forbids silent promotion
  - ``drift_kind`` — `evidence_row_line_changed` /
    `evidence_row_file_changed` / `evidence_row_path_missing` /
    `orphaned`
  - ``affected_rows`` — :class:`EvidenceRowRef` instances triggering
    drift detection

Cycle 3 reframe: v0.2.0's BandedAC-altitude :class:`IncrementalProposal`
is replaced with the objective-altitude :class:`IncrementalProposal`.
The proposal still carries ``proposed_new_evidence`` so the reviewer
can ratify a fresh repo_sha pin without re-running synthesis. The
backing-map row updates flow through Cycle 2's backing-map
re-population (out of cycle 3 scope).

Per F2 RF gap #10 (v0.2.0) — full-mode adapter ships zero real-AC
production for non-fixture cases; fixture-driven smoke validates the
wiring + altitude shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .bands import ConfidenceBand
from .diff_classifier import (
    EvidenceClassification,
    OrphanedObjective,
    OutOfDateObjective,
)
from .spec import EvidenceRowRef, Objective, ObjectiveEvidence


DriftKind = Literal[
    "evidence_row_line_changed",
    "evidence_row_file_changed",
    "evidence_row_path_missing",
    "orphaned",
]


@dataclass(frozen=True)
class IncrementalProposal:
    """One re-extraction proposal for an objective that drifted.

    Per AC.WATCHOBJ.2 — at objective altitude. Frozen dataclass;
    immutable once constructed.

    Fields:

    - ``objective`` — the prior :class:`Objective` (preserved verbatim
      for reviewer reference + domain inference).
    - ``objective_id`` — convenience accessor.
    - ``current_evidence`` — the prior ObjectiveEvidence block.
    - ``proposed_new_evidence`` — fresh ObjectiveEvidence with
      refreshed ``repo_sha``; ``None`` for orphaned proposals.
    - ``confidence_band`` — preserved from prior (Decision I default-no
      forbids silent promotion).
    - ``drift_kind`` — discriminant.
    - ``affected_rows`` — :class:`EvidenceRowRef` instances triggering
      drift detection.
    """

    objective: Objective
    current_evidence: ObjectiveEvidence
    proposed_new_evidence: ObjectiveEvidence | None
    confidence_band: ConfidenceBand
    drift_kind: DriftKind
    affected_rows: tuple[EvidenceRowRef, ...] = field(default_factory=tuple)

    @property
    def objective_id(self) -> str:
        return self.objective.objective_id

    @property
    def affected_files(self) -> tuple[str, ...]:
        """Sorted unique paths from affected_rows."""
        return tuple(sorted({r.path for r in self.affected_rows}))


@dataclass(frozen=True)
class IncrementalProposalSet:
    """The full set of proposals for one watch run.

    Per AC.WATCHOBJ.2 — carries metadata for downstream domain-batching
    + PM enqueue + audit-log entries.
    """

    extraction_id: str
    proposals: tuple[IncrementalProposal, ...]
    prior_repo_sha: str | None
    current_repo_sha: str
    generated_at: str  # ISO 8601 with timezone

    @property
    def proposal_count(self) -> int:
        return len(self.proposals)


def _refresh_evidence(
    prior: ObjectiveEvidence, *, current_repo_sha: str
) -> ObjectiveEvidence:
    """Return a copy of the prior evidence with ``repo_sha`` refreshed.

    All other fields preserved verbatim. Per Cycle 1 multi-source
    evidence shape — readme_excerpts / design_doc_refs /
    test_name_refs / survey_line_refs / code_pattern_refs / rationale
    survive intact.
    """
    return ObjectiveEvidence(
        readme_excerpts=list(prior.readme_excerpts),
        design_doc_refs=list(prior.design_doc_refs),
        test_name_refs=list(prior.test_name_refs),
        survey_line_refs=list(prior.survey_line_refs),
        code_pattern_refs=list(prior.code_pattern_refs),
        repo_sha=current_repo_sha,
        rationale=prior.rationale,
    )


def _propose_for_out_of_date(
    out_of_date: OutOfDateObjective,
    *,
    current_repo_sha: str,
) -> IncrementalProposal:
    """Generate a proposal for an out-of-date objective.

    Cycle 3 builds proposed evidence by:

      - Preserving multi-source evidence verbatim.
      - Refreshing ``repo_sha`` to the watch's observed ``to_sha``.
      - Per-band evidence rules enforced through ObjectiveEvidence
        construction (the reviewer ratifies whether the rows need
        updating; the watch doesn't speculate on new line ranges).
    """
    proposed = _refresh_evidence(
        out_of_date.objective.evidence,
        current_repo_sha=current_repo_sha,
    )
    return IncrementalProposal(
        objective=out_of_date.objective,
        current_evidence=out_of_date.objective.evidence,
        proposed_new_evidence=proposed,
        confidence_band=out_of_date.objective.confidence,
        drift_kind=out_of_date.drift_kind,
        affected_rows=out_of_date.affected_rows,
    )


def _propose_for_orphan(orphan: OrphanedObjective) -> IncrementalProposal:
    """Generate a proposal for an orphaned objective.

    No ``proposed_new_evidence`` — the reviewer's options are
    keep / reject / re-extract-with-new-evidence.
    """
    return IncrementalProposal(
        objective=orphan.objective,
        current_evidence=orphan.objective.evidence,
        proposed_new_evidence=None,
        confidence_band=orphan.objective.confidence,
        drift_kind="orphaned",
        affected_rows=orphan.missing_evidence_rows,
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

    Per AC.WATCHOBJ.2 — one proposal per out-of-date objective + one
    per orphan. Still-current objectives produce no proposals.

    Returns proposals sorted by objective_id for determinism (load-
    bearing for AC.RELSMOKE.2 idempotency).
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
    proposals.sort(key=lambda p: p.objective_id)
    return IncrementalProposalSet(
        extraction_id=extraction_id,
        proposals=tuple(proposals),
        prior_repo_sha=prior_repo_sha,
        current_repo_sha=current_repo_sha,
        generated_at=generated_at,
    )
