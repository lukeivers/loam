"""Shared test helpers for AC.GAPAN.* tests.

Builds canonical Objective / BackingMap / evidence-row substrate so
each gap-analysis test can compose minimal fixture shapes inline.
"""

from __future__ import annotations

import datetime as _dt

from loam_odd_extractor import (
    AugmentedObjectiveSet,
    BackingMap,
    BackingMapEntry,
    ConfidenceBand,
    EvidenceRowRef,
    Objective,
    ObjectiveEvidence,
)


def make_objective(
    domain: str = "dispute-flow",
    idx: int = 1,
    band: ConfidenceBand = ConfidenceBand.PLAUSIBLE,
) -> Objective:
    """Make an Objective with band-appropriate evidence."""
    if band is ConfidenceBand.VERIFIED:
        ev = ObjectiveEvidence(
            readme_excerpts=["File refunds at scale"],
            test_name_refs=["test_dispute_filing"],
            repo_sha="abc123",
        )
    elif band is ConfidenceBand.PLAUSIBLE:
        ev = ObjectiveEvidence(
            readme_excerpts=["File refunds at scale"],
        )
    else:  # HYPOTHESISED
        ev = ObjectiveEvidence(
            rationale="LLM inferred this objective from route shape patterns.",
        )
    return Objective(
        objective_id=f"O.{domain}.{idx}",
        text=f"Operators perform {domain} workflow at scale, variant {idx}.",
        confidence=band,
        domain=domain,
        evidence=ev,
    )


def make_aug_set(
    objectives: list[Objective],
    extraction_id: str = "repo-1",
    audit_path: str = "/tmp/audit-log",
) -> AugmentedObjectiveSet:
    return AugmentedObjectiveSet(
        extraction_id=extraction_id,
        augmented_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        interview_audit_path=audit_path,
        objectives=objectives,
    )


def make_row(
    *,
    path: str,
    line: int = 42,
    line_end: int | None = None,
    kind: str = "route",
    confidence: str = "STRONG",
    language: str = "jsts",
) -> EvidenceRowRef:
    end = line_end if line_end is not None else line + 5
    return EvidenceRowRef(
        evidence_row_id=f"{kind}:{path}:{line}",
        kind=kind,
        path=path,
        line_range=(line, end),
        confidence=confidence,
        language=language,
    )


def make_raw_dict(
    *,
    path: str,
    line: int = 42,
    line_end: int | None = None,
    kind: str = "route",
    language: str = "jsts",
) -> dict:
    """Adapter-output shape (BandedAC dict) — what evidence-rows.yaml carries."""
    end = line_end if line_end is not None else line + 5
    return {
        "ac_id": f"{kind}:{path}:{line}",
        "kind": kind,
        "path": path,
        "line_range": [line, end],
        "language": language,
    }


def make_backing_map(
    entries: list[BackingMapEntry],
    extraction_id: str = "repo-1",
) -> BackingMap:
    total_rows = sum(len(e.evidence_rows) for e in entries)
    return BackingMap(
        extraction_id=extraction_id,
        entries=entries,
        orphan_rows=[],
        created_at=_dt.datetime.now(_dt.timezone.utc).isoformat(),
        model_id="(test)",
        cost_actual_cents=0.0,
        total_evidence_rows=total_rows,
        objective_count=len(entries),
        unmatched_objective_ids=[],
    )
