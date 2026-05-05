"""Per-band gating engine for loam-pr-safety.

Per AC.PRGATE.3 (v0.2.3 Cycle 3) — runs the decision matrix at
OBJECTIVE altitude.

Pre-emption order (preserved verbatim from v0.1.9 AC.PRSG.4):

    HARD_BLOCK > SURFACE_DECISION > DOCS_ONLY > PASS

A diff that touches multiple bands fires the highest pre-empt:

    VERIFIED + anything → HARD_BLOCK
    PLAUSIBLE + HYPOTHESISED → SURFACE_DECISION
    PLAUSIBLE + novel → SURFACE_DECISION (consolidated)
    HYPOTHESISED + novel → SURFACE_DECISION

Per AC.PRGATE.3 + v0.1.9 AC.PRSG.8 — production-stake honour:
``requires_ratification=True`` on every SURFACE_DECISION. Dev /
research default to ``False`` unless ``--require-ratification`` is
passed.

Reason text renders OBJECTIVE prose (not symbol-altitude AC IDs).
The reviewer reads outcome-shaped statements like "diff touches
VERIFIED objective O.dispute-flow.1: 'operators file refund disputes
against DoorDash + Uber Eats merchant portals at scale'; backing
rows: src/routes/disputeRoutes.js:42-58".
"""

from __future__ import annotations

from loam_odd_extractor.bands import ConfidenceBand

from loam_pr_safety.spec import (
    ClassificationResult,
    GateAction,
    GateDecision,
    TouchedObjective,
)


_PRODUCTION_STAKE = "production-stake"
_DEV = "dev"
_RESEARCH = "research"


def _has_band(
    touched_objectives: list[TouchedObjective], band: ConfidenceBand
) -> bool:
    return any(t.objective.confidence is band for t in touched_objectives)


def _format_backing_rows(touched: TouchedObjective) -> str:
    """Render the touched backing rows as a compact 'path:line-range'
    string for inclusion in reason text. AC.PRGATE.5 + AC.PRGATE.3
    both render objective-altitude provenance via this helper.
    """
    parts: list[str] = []
    for row in touched.touched_evidence_rows[:3]:
        if row.line_range:
            start, end = row.line_range
            if start == end:
                parts.append(f"{row.path}:{start}")
            else:
                parts.append(f"{row.path}:{start}-{end}")
        else:
            parts.append(row.path)
    if len(touched.touched_evidence_rows) > 3:
        parts.append(f"… ({len(touched.touched_evidence_rows) - 3} more)")
    return ", ".join(parts)


def _build_pm_pairs_plausible(
    touched_objectives: list[TouchedObjective],
    extraction_id: str,
) -> list[tuple[str, str]]:
    """Build PM batch pairs for PLAUSIBLE-touched objectives.

    Per AC.PRGATE.3 — one question per touched PLAUSIBLE objective.
    Provenance per master plan §3 Cycle 3:
    ``pr-safety:plausible-objective:{ext}:{obj_id}``.
    """
    pairs: list[tuple[str, str]] = []
    for t in touched_objectives:
        if t.objective.confidence is not ConfidenceBand.PLAUSIBLE:
            continue
        rows_str = _format_backing_rows(t)
        question = (
            f"PR diff touches PLAUSIBLE objective "
            f"{t.objective.objective_id}: {t.objective.text}\n\n"
            f"Domain: {t.objective.domain}\n"
            f"Touch kind: {t.touch_kind}; "
            f"backing rows touched: {rows_str}; "
            f"hunks: {len(t.touched_hunks)}.\n\n"
            f"Ratify (proceed) or escalate (block)?"
        )
        prov = (
            f"pr-safety:plausible-objective:{extraction_id}:"
            f"{t.objective.objective_id}"
        )
        pairs.append((question, prov))
    return pairs


def _build_pm_pairs_novel(
    novel_count: int,
    extraction_id: str,
) -> list[tuple[str, str]]:
    """Build PM batch pairs for novel diffs.

    Per AC.PRGATE.3 — Cycle 3 records audit-only at the gate; v0.2.4
    gap-analysis owns objective creation. The PM question surfaces
    the count for reviewer awareness.
    """
    if novel_count == 0:
        return []
    question = (
        f"PR diff introduces {novel_count} novel diff(s) — "
        f"hunks not mapped to any objective's backing-implementation "
        f"row.\n\n"
        f"Cycle 3 records this audit-only. v0.2.4 gap-analysis will "
        f"extract structured proposals; for now, surface for reviewer "
        f"awareness."
    )
    prov = f"pr-safety:novel-diff:{extraction_id}"
    return [(question, prov)]


def decide(
    classification: ClassificationResult,
    *,
    safety_profile: str,
    extraction_id: str = "",
    require_ratification: bool = False,
) -> GateDecision:
    """Run the decision matrix.

    Per AC.PRGATE.3.

    Parameters:
      classification — output of :func:`loam_pr_safety.classifier.classify`.
      safety_profile — one of ``{production-stake, dev, research}``.
      extraction_id — for PM batch provenance strings.
      require_ratification — when ``True`` under dev/research, forces
        ``requires_ratification=True`` on SURFACE_DECISION.

    Returns :class:`GateDecision`.
    """
    is_prodstake = safety_profile == _PRODUCTION_STAKE

    has_verified = _has_band(
        classification.touched_objectives, ConfidenceBand.VERIFIED
    )
    has_plausible = _has_band(
        classification.touched_objectives, ConfidenceBand.PLAUSIBLE
    )
    has_hypothesised = _has_band(
        classification.touched_objectives, ConfidenceBand.HYPOTHESISED
    )
    has_novel = bool(classification.novel)

    # ---- Pre-emption: HARD_BLOCK first --------------------------------

    if has_verified:
        verified_touched = [
            t
            for t in classification.touched_objectives
            if t.objective.confidence is ConfidenceBand.VERIFIED
        ]
        # Reason renders objective TEXT (not AC IDs).
        verified_summaries: list[str] = []
        for t in verified_touched:
            rows_str = _format_backing_rows(t)
            verified_summaries.append(
                f"{t.objective.objective_id}: '{t.objective.text}' "
                f"(backing rows: {rows_str})"
            )
        reason = (
            f"HARD_BLOCK — diff touches VERIFIED objective(s): "
            f"{'; '.join(verified_summaries)}. "
            f"VERIFIED-touched is regression-suspect by default; "
            f"reviewer ratifies via `--override` flag with "
            f"`Loam-Override:` trailer to let through."
        )
        decision = GateDecision(
            action=GateAction.HARD_BLOCK,
            requires_ratification=True,
            touched_objectives=classification.touched_objectives,
            novel=classification.novel,
            safety_profile=safety_profile,
            reason=reason,
            pm_batch_pairs=[],
            audit_payload={
                "decision": GateAction.HARD_BLOCK.value,
                "verified_objective_ids": [
                    t.objective.objective_id for t in verified_touched
                ],
                "novel_count": len(classification.novel),
            },
        )
        return decision

    # ---- SURFACE_DECISION: PLAUSIBLE OR novel -----------------------

    if has_plausible or has_novel:
        plausible_pairs = _build_pm_pairs_plausible(
            classification.touched_objectives, extraction_id
        )
        novel_pairs = _build_pm_pairs_novel(
            len(classification.novel), extraction_id
        )
        pm_batch_pairs = plausible_pairs + novel_pairs

        # Default requires_ratification per profile + flag.
        if is_prodstake:
            req_ratification = True
        elif require_ratification:
            req_ratification = True
        else:
            req_ratification = False

        plausible_touched = [
            t
            for t in classification.touched_objectives
            if t.objective.confidence is ConfidenceBand.PLAUSIBLE
        ]
        reason_parts: list[str] = []
        if plausible_touched:
            plausible_summaries = [
                f"{t.objective.objective_id}: '{t.objective.text[:80]}{'…' if len(t.objective.text) > 80 else ''}'"
                for t in plausible_touched
            ]
            reason_parts.append(
                f"PLAUSIBLE objective(s) touched: "
                f"{'; '.join(plausible_summaries)}"
            )
        if has_novel:
            reason_parts.append(
                f"{len(classification.novel)} novel diff(s)"
            )
        if has_hypothesised:
            hypoth_touched = [
                t
                for t in classification.touched_objectives
                if t.objective.confidence is ConfidenceBand.HYPOTHESISED
            ]
            hypoth_ids = [t.objective.objective_id for t in hypoth_touched]
            reason_parts.append(
                f"HYPOTHESISED objective(s) touched (annotation): "
                f"{', '.join(hypoth_ids)}"
            )
        reason = (
            f"SURFACE_DECISION — {'; '.join(reason_parts)}. "
            f"Profile {safety_profile} → "
            f"requires_ratification={req_ratification}."
        )

        return GateDecision(
            action=GateAction.SURFACE_DECISION,
            requires_ratification=req_ratification,
            touched_objectives=classification.touched_objectives,
            novel=classification.novel,
            safety_profile=safety_profile,
            reason=reason,
            pm_batch_pairs=pm_batch_pairs,
            audit_payload={
                "decision": GateAction.SURFACE_DECISION.value,
                "plausible_objective_ids": [
                    t.objective.objective_id for t in plausible_touched
                ],
                "novel_count": len(classification.novel),
            },
        )

    # ---- DOCS_ONLY: HYPOTHESISED touched, no V/P, no novel ---------

    if has_hypothesised:
        hypoth_touched = [
            t
            for t in classification.touched_objectives
            if t.objective.confidence is ConfidenceBand.HYPOTHESISED
        ]
        hypoth_ids = [t.objective.objective_id for t in hypoth_touched]
        reason = (
            f"DOCS_ONLY — diff touches HYPOTHESISED objective(s): "
            f"{', '.join(hypoth_ids)}. Annotation only; no block."
        )
        return GateDecision(
            action=GateAction.DOCS_ONLY,
            requires_ratification=False,
            touched_objectives=classification.touched_objectives,
            novel=classification.novel,
            safety_profile=safety_profile,
            reason=reason,
            pm_batch_pairs=[],
            audit_payload={
                "decision": GateAction.DOCS_ONLY.value,
                "hypothesised_objective_ids": hypoth_ids,
            },
        )

    # ---- PASS: untouched -------------------------------------------

    return GateDecision(
        action=GateAction.PASS,
        requires_ratification=False,
        touched_objectives=[],
        novel=[],
        safety_profile=safety_profile,
        reason="PASS — no objective touched; no novel diffs.",
        pm_batch_pairs=[],
        audit_payload={
            "decision": GateAction.PASS.value,
        },
    )
