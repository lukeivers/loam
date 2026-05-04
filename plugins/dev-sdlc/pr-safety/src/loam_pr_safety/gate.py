"""Per-band gating engine for loam-pr-safety.

Per AC.PRSG.4 + plan-doc §6 — runs the 3-band × 4-shape × 3-profile
decision matrix.

Pre-emption order:

    HARD_BLOCK > SURFACE_DECISION > DOCS_ONLY > PASS

A diff that touches multiple bands fires the highest pre-empt:

    VERIFIED + anything → HARD_BLOCK
    PLAUSIBLE + HYPOTHESISED → SURFACE_DECISION
    PLAUSIBLE + novel → SURFACE_DECISION (consolidated batch)
    HYPOTHESISED + novel → SURFACE_DECISION (novel pre-empts
                          DOCS_ONLY since novel introduces an
                          unmapped surface)

Per AC.PRSG.8 — production-stake demands ``requires_ratification=True``
on every SURFACE_DECISION. Dev / research default to
``requires_ratification=False`` unless the caller passes
``require_ratification=True`` (the ``--require-ratification`` CLI
flag).

Cycle 1 simplification (per plan-doc §10 F2 RF gap #4):
"VERIFIED-touched ≡ regression-suspect" by default. The engine
cannot run the underlying test in-process; reviewer ratifies via
``--override`` (override flow) to let it through.
"""

from __future__ import annotations

from loam_odd_extractor.bands import ConfidenceBand

from loam_pr_safety.spec import (
    ClassificationResult,
    GateAction,
    GateDecision,
    TouchedAC,
)


_PRODUCTION_STAKE = "production-stake"
_DEV = "dev"
_RESEARCH = "research"


def _has_band(touched_acs: list[TouchedAC], band: ConfidenceBand) -> bool:
    return any(t.ac.confidence is band for t in touched_acs)


def _build_pm_pairs_plausible(
    touched_acs: list[TouchedAC],
    extraction_id: str,
) -> list[tuple[str, str]]:
    """Build PM batch pairs for PLAUSIBLE-touched ACs.

    Per Decision Q (one-question-at-a-time) — the gate constructs
    the batch shape; the caller (CLI) decides whether to enqueue
    via ``RatificationBatch.from_banded_acs`` + ``surface_next_questions_batch(n=1)``.

    Provenance string per Surface #8 of v0.1.8 Cycle 2 plan-doc:
    ``f"pr-safety:plausible:{extraction_id}:{ac_id}"``.
    """
    pairs: list[tuple[str, str]] = []
    for t in touched_acs:
        if t.ac.confidence is not ConfidenceBand.PLAUSIBLE:
            continue
        question = (
            f"PR diff touches PLAUSIBLE AC {t.ac.ac_id}: "
            f"{t.ac.text}\n\n"
            f"Touch kind: {t.touch_kind}; "
            f"hunks: {len(t.touched_hunks)}.\n\n"
            f"Ratify (proceed) or escalate (block)?"
        )
        prov = (
            f"pr-safety:plausible:{extraction_id}:{t.ac.ac_id}"
        )
        pairs.append((question, prov))
    return pairs


def _build_pm_pairs_novel(
    novel_count: int,
    extraction_id: str,
) -> list[tuple[str, str]]:
    """Build PM batch pairs for novel candidates.

    One consolidated question per novel-only batch — promote the
    candidate(s) to PLAUSIBLE / HYPOTHESISED / skip. Cycle 2+ may
    refine to per-novel-candidate questions.
    """
    if novel_count == 0:
        return []
    question = (
        f"PR diff introduces {novel_count} novel candidate(s) — "
        f"diff lines not mapped to any AC.\n\n"
        f"Promote to PLAUSIBLE / HYPOTHESISED / skip?"
    )
    prov = f"pr-safety:novel:{extraction_id}"
    return [(question, prov)]


def decide(
    classification: ClassificationResult,
    *,
    safety_profile: str,
    extraction_id: str = "",
    require_ratification: bool = False,
) -> GateDecision:
    """Run the decision matrix.

    Per AC.PRSG.4 + plan-doc §6.

    Parameters:
      classification — output of :func:`loam_pr_safety.classifier.classify`.
      safety_profile — one of ``{production-stake, dev, research}``.
      extraction_id — for PM batch provenance strings (best-effort).
      require_ratification — when ``True`` under dev/research, forces
        ``requires_ratification=True`` on SURFACE_DECISION (the
        ``--require-ratification`` CLI flag). Ignored under
        production-stake (already True).

    Returns :class:`GateDecision`.
    """
    is_prodstake = safety_profile == _PRODUCTION_STAKE

    has_verified = _has_band(
        classification.touched_acs, ConfidenceBand.VERIFIED
    )
    has_plausible = _has_band(
        classification.touched_acs, ConfidenceBand.PLAUSIBLE
    )
    has_hypothesised = _has_band(
        classification.touched_acs, ConfidenceBand.HYPOTHESISED
    )
    has_novel = bool(classification.novel)

    # ---- Pre-emption: HARD_BLOCK first --------------------------------

    if has_verified:
        # VERIFIED-touched (Cycle 1 simplification: regression-suspect
        # by default).
        verified_ac_ids = [
            t.ac.ac_id
            for t in classification.touched_acs
            if t.ac.confidence is ConfidenceBand.VERIFIED
        ]
        reason = (
            f"HARD_BLOCK — diff touches VERIFIED AC(s): "
            f"{', '.join(verified_ac_ids)}. "
            f"Cycle 1 treats VERIFIED-touched as regression-suspect; "
            f"reviewer ratifies via `--override` flag with "
            f"`Loam-Override:` trailer to let through."
        )
        decision = GateDecision(
            action=GateAction.HARD_BLOCK,
            requires_ratification=True,
            touched_acs=classification.touched_acs,
            novel=classification.novel,
            safety_profile=safety_profile,
            reason=reason,
            pm_batch_pairs=[],
            audit_payload={
                "decision": GateAction.HARD_BLOCK.value,
                "verified_ac_ids": verified_ac_ids,
                "novel_count": len(classification.novel),
            },
        )
        return decision

    # ---- SURFACE_DECISION: PLAUSIBLE OR novel ------------------------

    if has_plausible or has_novel:
        # Build consolidated PM batch — PLAUSIBLE questions + novel
        # questions in one batch.
        plausible_pairs = _build_pm_pairs_plausible(
            classification.touched_acs, extraction_id
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

        plausible_ac_ids = [
            t.ac.ac_id
            for t in classification.touched_acs
            if t.ac.confidence is ConfidenceBand.PLAUSIBLE
        ]
        reason_parts: list[str] = []
        if plausible_ac_ids:
            reason_parts.append(
                f"PLAUSIBLE AC(s) touched: {', '.join(plausible_ac_ids)}"
            )
        if has_novel:
            reason_parts.append(
                f"{len(classification.novel)} novel candidate(s)"
            )
        if has_hypothesised:
            hypoth_ac_ids = [
                t.ac.ac_id
                for t in classification.touched_acs
                if t.ac.confidence is ConfidenceBand.HYPOTHESISED
            ]
            reason_parts.append(
                f"HYPOTHESISED AC(s) touched (annotation): "
                f"{', '.join(hypoth_ac_ids)}"
            )
        reason = (
            f"SURFACE_DECISION — {'; '.join(reason_parts)}. "
            f"Profile {safety_profile} → "
            f"requires_ratification={req_ratification}."
        )

        return GateDecision(
            action=GateAction.SURFACE_DECISION,
            requires_ratification=req_ratification,
            touched_acs=classification.touched_acs,
            novel=classification.novel,
            safety_profile=safety_profile,
            reason=reason,
            pm_batch_pairs=pm_batch_pairs,
            audit_payload={
                "decision": GateAction.SURFACE_DECISION.value,
                "plausible_ac_ids": plausible_ac_ids,
                "novel_count": len(classification.novel),
            },
        )

    # ---- DOCS_ONLY: HYPOTHESISED touched, no VERIFIED, no PLAUSIBLE,
    #      no novel.
    if has_hypothesised:
        hypoth_ac_ids = [
            t.ac.ac_id
            for t in classification.touched_acs
            if t.ac.confidence is ConfidenceBand.HYPOTHESISED
        ]
        reason = (
            f"DOCS_ONLY — diff touches HYPOTHESISED AC(s): "
            f"{', '.join(hypoth_ac_ids)}. Annotation only; no block."
        )
        return GateDecision(
            action=GateAction.DOCS_ONLY,
            requires_ratification=False,
            touched_acs=classification.touched_acs,
            novel=classification.novel,
            safety_profile=safety_profile,
            reason=reason,
            pm_batch_pairs=[],
            audit_payload={
                "decision": GateAction.DOCS_ONLY.value,
                "hypothesised_ac_ids": hypoth_ac_ids,
            },
        )

    # ---- PASS: untouched ---------------------------------------------

    return GateDecision(
        action=GateAction.PASS,
        requires_ratification=False,
        touched_acs=[],
        novel=[],
        safety_profile=safety_profile,
        reason="PASS — no AC touched; no novel candidates.",
        pm_batch_pairs=[],
        audit_payload={
            "decision": GateAction.PASS.value,
        },
    )
