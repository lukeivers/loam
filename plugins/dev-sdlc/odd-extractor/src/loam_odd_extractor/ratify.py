"""Ratification workflow — typed actions + apply.

Per AC.BANDS.4 + AC.BANDS.5 + AC.BANDS.6 (v0.1.8 Cycle 2 plan-doc §4):

- :class:`RatificationAction` — frozen dataclass; in-memory only;
  one of four kinds: ``promote`` / ``demote`` / ``edit`` / ``reject``.
- :func:`promote` / :func:`demote` / :func:`edit` / :func:`reject`
  — factory functions that enforce per-action invariants at
  construction time. AC.BANDS.5 in particular: ``promote`` from
  PLAUSIBLE to VERIFIED requires ``explicit_yes=True`` (Decision I:
  silent promotion forbidden).
- :func:`apply_ratification_action` — applies an action to a
  banded-AC list (typically loaded from a ContractDraft sidecar);
  writes an audit-log entry; updates ratification-state.yaml.
- :func:`enqueue_ratification_batch` — composes with
  ``framework/per-project-pm/`` (the secondary fence) to enqueue a
  ratification batch through the PM's decision-queue.

Composition with PM (AC.BANDS.7): the persona-side flow is

  1. ``enqueue_ratification_batch(draft, banded_acs, pm_runtime)``
     enqueues N decision-queue entries (one per pending AC).
  2. ``pm.surface_next_questions_batch(n=1)`` (respecting
     ``onboarding_mode``) returns one :class:`SurfacedQuestion`.
  3. Persona relays question; user replies.
  4. ``pm.record_response(audit_path, response_text)`` closes the
     PM-side loop.
  5. Persona parses the user's response into a structured
     :class:`RatificationAction`.
  6. ``apply_ratification_action(...)`` applies + audits +
     advances ratification-state.yaml.

Step (5)'s natural-language → :class:`RatificationAction` parser is
persona-side work (out of Cycle 2 scope per parent plan §7); Cycle
2 ships the typed primitive at (1) + (6).
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .bands import BandedAC, ConfidenceBand, Evidence
from .errors import RatificationRefusedError
from .observability import write_audit_entry
from .ratification_state import (
    CompletedAction,
    PendingTarget,
    RatificationState,
    RatificationStateV2,
    initialise_ratification_state,
    load_ratification_state,
    save_ratification_state,
)
from .spec import (
    BackingMap,
    Capability,
    Constraint,
    Objective,
)
from .state import extraction_dir


# ---- Action kinds + factories --------------------------------------


ActionKind = Literal["promote", "demote", "edit", "reject"]


@dataclass(frozen=True)
class RatificationAction:
    """Typed ratification action (in-memory only).

    Per plan-doc §5 Surface #5 — frozen dataclass (NOT Pydantic);
    factory-function-enforced invariants. Direct construction with
    field values bypasses factory-level checks; production callers
    use :func:`promote` / :func:`demote` / :func:`edit` /
    :func:`reject`.

    Fields:

    - ``kind`` — one of four action kinds.
    - ``ac_id`` — required, non-empty; the AC's stable identifier.
    - ``from_band`` / ``to_band`` — set for promote/demote; ``None``
      for edit/reject.
    - ``edit_text`` — set for edit; the new AC text.
    - ``reject_reason`` — set for reject; human-readable rationale.
    - ``explicit_yes`` — required ``True`` for PLAUSIBLE→VERIFIED
      promotion (Decision I); default ``False``.
    """

    kind: ActionKind
    ac_id: str
    from_band: ConfidenceBand | None = None
    to_band: ConfidenceBand | None = None
    edit_text: str | None = None
    reject_reason: str | None = None
    explicit_yes: bool = False


def promote(
    *,
    ac_id: str,
    from_band: ConfidenceBand,
    to_band: ConfidenceBand,
    explicit_yes: bool = False,
) -> RatificationAction:
    """Construct a promote action.

    Per AC.BANDS.5: ``from_band=PLAUSIBLE`` + ``to_band=VERIFIED``
    requires ``explicit_yes=True``; raises
    :class:`RatificationRefusedError` otherwise. Other promotions
    (HYPOTHESISED→PLAUSIBLE, HYPOTHESISED→VERIFIED) are
    default-allow.

    Validates that ``to_band`` is "higher" than ``from_band`` per
    the implicit ordering HYPOTHESISED < PLAUSIBLE < VERIFIED.
    """
    if not ac_id:
        raise RatificationRefusedError("promote: ac_id must be non-empty")
    order = {
        ConfidenceBand.HYPOTHESISED: 0,
        ConfidenceBand.PLAUSIBLE: 1,
        ConfidenceBand.VERIFIED: 2,
    }
    if order[to_band] <= order[from_band]:
        raise RatificationRefusedError(
            f"promote: to_band ({to_band.value}) must be higher than "
            f"from_band ({from_band.value}); use demote() instead"
        )
    if (
        from_band is ConfidenceBand.PLAUSIBLE
        and to_band is ConfidenceBand.VERIFIED
        and not explicit_yes
    ):
        raise RatificationRefusedError(
            f"promote: PLAUSIBLE→VERIFIED requires explicit_yes=True "
            f"per Decision I (default-no on silent promotion); "
            f"ac_id={ac_id!r}"
        )
    return RatificationAction(
        kind="promote",
        ac_id=ac_id,
        from_band=from_band,
        to_band=to_band,
        explicit_yes=explicit_yes,
    )


def demote(
    *,
    ac_id: str,
    from_band: ConfidenceBand,
    to_band: ConfidenceBand,
) -> RatificationAction:
    """Construct a demote action. Default-allow (no explicit_yes
    needed); demotion is asymmetric per Decision I — only promotion
    to VERIFIED is gated.

    Validates that ``to_band`` is "lower" than ``from_band``.
    """
    if not ac_id:
        raise RatificationRefusedError("demote: ac_id must be non-empty")
    order = {
        ConfidenceBand.HYPOTHESISED: 0,
        ConfidenceBand.PLAUSIBLE: 1,
        ConfidenceBand.VERIFIED: 2,
    }
    if order[to_band] >= order[from_band]:
        raise RatificationRefusedError(
            f"demote: to_band ({to_band.value}) must be lower than "
            f"from_band ({from_band.value}); use promote() instead"
        )
    return RatificationAction(
        kind="demote",
        ac_id=ac_id,
        from_band=from_band,
        to_band=to_band,
    )


def edit(*, ac_id: str, edit_text: str) -> RatificationAction:
    """Construct an edit action — modify an AC's prose without
    changing its band."""
    if not ac_id:
        raise RatificationRefusedError("edit: ac_id must be non-empty")
    if not edit_text or not edit_text.strip():
        raise RatificationRefusedError(
            "edit: edit_text must be non-empty"
        )
    return RatificationAction(
        kind="edit",
        ac_id=ac_id,
        edit_text=edit_text,
    )


def reject(*, ac_id: str, reject_reason: str) -> RatificationAction:
    """Construct a reject action — drop an AC from the contract
    draft entirely."""
    if not ac_id:
        raise RatificationRefusedError(
            "reject: ac_id must be non-empty"
        )
    if not reject_reason or not reject_reason.strip():
        raise RatificationRefusedError(
            "reject: reject_reason must be non-empty"
        )
    return RatificationAction(
        kind="reject",
        ac_id=ac_id,
        reject_reason=reject_reason,
    )


# ---- Apply ----------------------------------------------------------


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def apply_ratification_action(
    action: RatificationAction,
    *,
    banded_acs: list[BandedAC],
    workspace_root: Path,
    repo_id: str,
    pm_audit_path: str | None = None,
    timestamp: str | None = None,
) -> list[BandedAC]:
    """Apply ``action`` to ``banded_acs``; return the updated list.

    Per AC.BANDS.6 — writes one audit-log entry under
    ``<workspace>/.loam/extractions/<repo-id>/audit-log/`` with
    ``event_kind="ratification_<kind>"`` (e.g. ``ratification_promote``).
    The entry's ``pm_audit_path`` field cross-references the PM-side
    ``record_response`` audit entry that backs this action (relative
    path; ``None`` for system-internal actions like resume).

    Per AC.BANDS.5 — applies a *second* check at apply time
    (defense in depth): if ``action.kind == "promote"`` with
    PLAUSIBLE→VERIFIED bands and ``explicit_yes=False``, raises
    :class:`RatificationRefusedError`. Factory-level enforcement is
    primary; apply-level is the fallback for callers that bypass the
    factory.

    Updates :class:`ratification_state.RatificationState`:

    - Removes ``action.ac_id`` from ``pending_acs``.
    - Appends a :class:`CompletedAction` to ``completed_actions``.
    - Clears ``in_flight_action`` if it matches ``action.ac_id``.

    Returns a new list (never mutates ``banded_acs`` in place).
    """
    # Defense-in-depth check on PLAUSIBLE→VERIFIED.
    if (
        action.kind == "promote"
        and action.from_band is ConfidenceBand.PLAUSIBLE
        and action.to_band is ConfidenceBand.VERIFIED
        and not action.explicit_yes
    ):
        raise RatificationRefusedError(
            f"apply_ratification_action: PLAUSIBLE→VERIFIED requires "
            f"explicit_yes=True per Decision I; ac_id={action.ac_id!r}"
        )

    # Locate the AC.
    target_idx: int | None = None
    for i, ac in enumerate(banded_acs):
        if ac.ac_id == action.ac_id:
            target_idx = i
            break
    if target_idx is None and action.kind != "reject":
        raise RatificationRefusedError(
            f"apply_ratification_action: ac_id {action.ac_id!r} not "
            f"found in banded_acs"
        )

    new_banded = list(banded_acs)
    if action.kind == "promote" or action.kind == "demote":
        # Replace confidence; preserve text + backing_files; require
        # the caller to have validated that the new band's evidence
        # block is consistent. For Cycle 2, we rebuild evidence as a
        # placeholder if the band changes — per-band evidence rules
        # require the kind field to match. The persona is responsible
        # for collecting fresh evidence on promotion (e.g., running
        # the test) and supplying it via a follow-up action.
        target = new_banded[target_idx]
        new_evidence = _evidence_placeholder_for(action.to_band, target)
        new_banded[target_idx] = BandedAC(
            ac_id=target.ac_id,
            text=target.text,
            confidence=action.to_band,
            evidence=new_evidence,
            backing_files=target.backing_files,
        )
    elif action.kind == "edit":
        target = new_banded[target_idx]
        new_banded[target_idx] = BandedAC(
            ac_id=target.ac_id,
            text=action.edit_text,
            confidence=target.confidence,
            evidence=target.evidence,
            backing_files=target.backing_files,
        )
    elif action.kind == "reject":
        if target_idx is not None:
            new_banded.pop(target_idx)

    ext_dir = extraction_dir(workspace_root, repo_id)

    # Audit-log entry.
    ts = timestamp if timestamp is not None else _now_iso()
    notes_parts: list[str] = []
    if action.from_band is not None and action.to_band is not None:
        notes_parts.append(
            f"from={action.from_band.value} "
            f"to={action.to_band.value}"
        )
    if action.kind == "edit":
        notes_parts.append(
            f"edit_text_len={len(action.edit_text or '')}"
        )
    if action.kind == "reject":
        notes_parts.append(
            f"reject_reason={action.reject_reason!r}"
        )
    if action.explicit_yes:
        notes_parts.append("explicit_yes=true")
    if pm_audit_path:
        notes_parts.append(f"pm_audit_path={pm_audit_path}")

    write_audit_entry(
        ext_dir,
        event_kind=f"ratification_{action.kind}",
        extraction_id=repo_id,
        artefact_path=None,
        notes=" ".join(notes_parts) if notes_parts else "",
        timestamp=ts,
    )

    # Update ratification-state.yaml. Loader returns V2 (auto-migrated
    # from v1 if needed); we mutate the V2 surface so v0.2.3 callers
    # observe the back-compat fields correctly.
    state = load_ratification_state(ext_dir)
    if state is not None:
        if action.ac_id in state.pending_acs:
            state.pending_acs = [
                a for a in state.pending_acs if a != action.ac_id
            ]
        if state.in_flight_action == action.ac_id:
            state.in_flight_action = None
        # v0.2.3 v2 surface — drop matching pending_targets too.
        state.pending_targets = [
            pt for pt in state.pending_targets
            if pt.target_id != action.ac_id
        ]
        if state.in_flight_target == action.ac_id:
            state.in_flight_target = None
        if action.ac_id in state.altitude_index:
            state.altitude_index.pop(action.ac_id)
        state.completed_actions.append(
            CompletedAction(
                ac_id=action.ac_id,
                action_kind=action.kind,
                applied_at=ts,
            )
        )
        save_ratification_state(ext_dir, state, timestamp=ts)

    return new_banded


def _evidence_placeholder_for(
    band: ConfidenceBand,
    target: BandedAC,
) -> Evidence:
    """Build a band-consistent evidence placeholder when promoting/
    demoting. The new evidence preserves citations + repo_sha +
    rationale where compatible; otherwise emits a minimum-viable
    structure that satisfies the per-band invariants.

    For VERIFIED, the persona must collect the test pin separately
    before promotion (Cycle 2 leaves this to the persona; v0.2.0+
    automates it). The placeholder uses ``repo_sha="pending"`` +
    keeps the prior citations so the round-trip ValidationError
    flags missing real data immediately at construction time.

    The returned evidence is band-valid (passes the model_validator
    on construction) so the caller can build a new :class:`BandedAC`
    without raising.
    """
    prior = target.evidence
    if band is ConfidenceBand.VERIFIED:
        return Evidence(
            kind="test",
            citations=prior.citations or ["pending: persona must record test pin"],
            repo_sha=prior.repo_sha or "pending",
            rationale=prior.rationale,
        )
    if band is ConfidenceBand.PLAUSIBLE:
        return Evidence(
            kind="source",
            citations=prior.citations or ["pending: persona must record source citation"],
            repo_sha=prior.repo_sha,
            rationale=prior.rationale,
        )
    # HYPOTHESISED
    return Evidence(
        kind="inference",
        citations=prior.citations,
        repo_sha=prior.repo_sha,
        rationale=prior.rationale or "pending: persona must record inference rationale",
    )


# ---- Enqueue (PM-mediated batch) -----------------------------------


def _question_for_banded_ac(ac: BandedAC) -> str:
    """Compose the user-facing question text for one banded AC."""
    return (
        f"Ratify AC {ac.ac_id} (currently {ac.confidence.value}): "
        f"{ac.text}\n\n"
        f"Evidence kind: {ac.evidence.kind}; "
        f"citations: {ac.evidence.citations or '(none)'}; "
        f"repo_sha: {ac.evidence.repo_sha or '(none)'}; "
        f"rationale: {ac.evidence.rationale or '(none)'}.\n\n"
        f"Reply with: promote / demote / edit / reject (and a "
        f"reason or new text where applicable). Note: PLAUSIBLE→VERIFIED "
        f"requires explicit confirmation."
    )


def _provenance_for(extraction_id: str, ac_id: str) -> str:
    """Provenance format per plan-doc §5 Surface #8."""
    return f"odd-extract:{extraction_id}:{ac_id}"


def enqueue_ratification_batch(
    *,
    extraction_id: str,
    banded_acs: list[BandedAC],
    workspace_root: Path,
    pm_runtime,  # PMRuntime — duck-typed to avoid circular import
    pm_handle: str,
    draft_path: str,
    timestamp: str | None = None,
) -> int:
    """Enqueue one PM decision-queue entry per banded AC.

    Per AC.BANDS.7 — composes with
    ``framework/per-project-pm/src/loam/per_project_pm/runtime.py``'s
    :meth:`PMRuntime.enqueue_decision`. Each enqueued entry carries
    a provenance string of shape
    ``f"odd-extract:{extraction_id}:{ac_id}"`` (plan-doc §5 Surface #8)
    so the persona can route the user's response back to the correct
    AC.

    Initialises (or no-op if exists) the ratification-state.yaml at
    ``<workspace>/.loam/extractions/<repo-id>/`` with the pending-AC
    list. Returns the count of newly-enqueued items.

    Idempotent: if the ratification-state already lists the AC as
    completed (``completed_actions`` carries the ac_id), the AC is
    skipped — re-running enqueue against an in-flight ratification
    only enqueues the still-pending ones.
    """
    ext_dir = extraction_dir(workspace_root, extraction_id)

    # Load existing state to skip already-completed ACs.
    existing = load_ratification_state(ext_dir)
    completed_ids: set[str] = set()
    if existing is not None:
        completed_ids = {ca.ac_id for ca in existing.completed_actions}

    pending_ac_ids: list[str] = []
    enqueued_count = 0
    for ac in banded_acs:
        if ac.ac_id in completed_ids:
            continue
        pending_ac_ids.append(ac.ac_id)
        pm_runtime.enqueue_decision(
            _question_for_banded_ac(ac),
            provenance=_provenance_for(extraction_id, ac.ac_id),
        )
        enqueued_count += 1

    # Initialise (or update) ratification-state.yaml.
    state = initialise_ratification_state(
        ext_dir,
        extraction_id=extraction_id,
        draft_path=draft_path,
        pm_handle=pm_handle,
        pending_acs=pending_ac_ids,
        timestamp=timestamp,
    )
    # If state existed, update its pending list to reflect newly
    # enqueued items.
    if existing is not None:
        existing_pending = set(state.pending_acs)
        new_pending = list(state.pending_acs)
        existing_targets = {pt.target_id for pt in state.pending_targets}
        for ac_id in pending_ac_ids:
            if ac_id not in existing_pending:
                new_pending.append(ac_id)
            if ac_id not in existing_targets:
                state.pending_targets.append(
                    PendingTarget(target_id=ac_id, altitude="banded_ac")
                )
                state.altitude_index[ac_id] = "banded_ac"
        state.pending_acs = new_pending
        save_ratification_state(ext_dir, state, timestamp=timestamp)

    return enqueued_count


# ====================================================================
# v0.2.3 Cycle 2 — Objective-altitude ratification (AC.OBJRAT.*)
# ====================================================================
#
# Per sub-plan-doc §3 AC.OBJRAT.{1..8} + §7 method-decision register.
# Parallel set of factories + apply path operating on Cycle-1 typed
# rows (Objective / Constraint / Capability). v0.1.8 BandedAC paths
# above are PRESERVED unchanged.

ObjectiveAltitude = Literal["objective", "constraint", "capability"]
ObjectiveActionKind = Literal["promote", "demote", "edit", "reject"]

# Per sub-plan-doc §3 AC.OBJRAT.2 + §7 — assertion-verb regex used by
# the test-asserts-outcome heuristic at PLAUSIBLE→VERIFIED.
import re as _re  # local alias to avoid shadowing
_OUTCOME_VERB_RE = _re.compile(
    r"\b(should|expects?|delivers?|creates?|rejects?|completes?|"
    r"handles?|files?|displays?|allows?|prevents?|confirms?)\b",
    _re.IGNORECASE,
)


@dataclass(frozen=True)
class ObjectiveRatificationAction:
    """Typed altitude-tagged ratification action.

    Per sub-plan-doc §3 AC.OBJRAT.1 — frozen dataclass mirroring v0.1.8
    :class:`RatificationAction`; factory-function-enforced invariants.
    Carries an explicit ``altitude`` tag so the apply path dispatches
    to the right typed-row list.

    ``backing_evidence_cited`` lists the evidence_row_ids the persona
    cited as backing for a PLAUSIBLE→VERIFIED objective promotion.
    Required for that one promotion case; ``None`` otherwise.
    """

    kind: ObjectiveActionKind
    target_id: str
    altitude: ObjectiveAltitude
    from_band: ConfidenceBand | None = None
    to_band: ConfidenceBand | None = None
    edit_text: str | None = None
    reject_reason: str | None = None
    explicit_yes: bool = False
    backing_evidence_cited: tuple[str, ...] | None = None


# ---- Common factory helper -----------------------------------------


_BAND_ORDER = {
    ConfidenceBand.HYPOTHESISED: 0,
    ConfidenceBand.PLAUSIBLE: 1,
    ConfidenceBand.VERIFIED: 2,
}


def _validate_promotion_bands(
    *,
    altitude: ObjectiveAltitude,
    target_id: str,
    from_band: ConfidenceBand,
    to_band: ConfidenceBand,
    explicit_yes: bool,
    backing_evidence_cited: list[str] | tuple[str, ...] | None,
) -> None:
    """Promotion-direction + Decision-I gate (factory-side primary)."""
    if not target_id:
        raise RatificationRefusedError(
            f"promote_{altitude}: target_id must be non-empty"
        )
    if _BAND_ORDER[to_band] <= _BAND_ORDER[from_band]:
        raise RatificationRefusedError(
            f"promote_{altitude}: to_band ({to_band.value}) must be "
            f"higher than from_band ({from_band.value}); use "
            f"demote_{altitude}() instead"
        )
    if (
        from_band is ConfidenceBand.PLAUSIBLE
        and to_band is ConfidenceBand.VERIFIED
    ):
        if not explicit_yes:
            raise RatificationRefusedError(
                f"promote_{altitude}: PLAUSIBLE→VERIFIED requires "
                f"explicit_yes=True per Decision I; "
                f"target_id={target_id!r}"
            )
        if altitude == "objective":
            # AC.OBJRAT.2 — objective P→V also requires backing-evidence.
            if not backing_evidence_cited:
                raise RatificationRefusedError(
                    f"promote_objective: PLAUSIBLE→VERIFIED requires "
                    f"backing_evidence_cited (non-empty list of "
                    f"backing-map evidence_row_ids); "
                    f"target_id={target_id!r}"
                )


def _validate_demotion_bands(
    *,
    altitude: ObjectiveAltitude,
    target_id: str,
    from_band: ConfidenceBand,
    to_band: ConfidenceBand,
) -> None:
    if not target_id:
        raise RatificationRefusedError(
            f"demote_{altitude}: target_id must be non-empty"
        )
    if _BAND_ORDER[to_band] >= _BAND_ORDER[from_band]:
        raise RatificationRefusedError(
            f"demote_{altitude}: to_band ({to_band.value}) must be "
            f"lower than from_band ({from_band.value}); use "
            f"promote_{altitude}() instead"
        )


# ---- Objective factories -------------------------------------------


def promote_objective(
    *,
    target_id: str,
    from_band: ConfidenceBand,
    to_band: ConfidenceBand,
    explicit_yes: bool = False,
    backing_evidence_cited: list[str] | tuple[str, ...] | None = None,
) -> ObjectiveRatificationAction:
    """Promote an :class:`Objective`'s band per AC.OBJRAT.1 + AC.OBJRAT.2."""
    _validate_promotion_bands(
        altitude="objective",
        target_id=target_id,
        from_band=from_band,
        to_band=to_band,
        explicit_yes=explicit_yes,
        backing_evidence_cited=backing_evidence_cited,
    )
    cited = (
        tuple(backing_evidence_cited)
        if backing_evidence_cited is not None
        else None
    )
    return ObjectiveRatificationAction(
        kind="promote",
        target_id=target_id,
        altitude="objective",
        from_band=from_band,
        to_band=to_band,
        explicit_yes=explicit_yes,
        backing_evidence_cited=cited,
    )


def demote_objective(
    *,
    target_id: str,
    from_band: ConfidenceBand,
    to_band: ConfidenceBand,
) -> ObjectiveRatificationAction:
    """Demote an :class:`Objective`'s band per AC.OBJRAT.3.

    Asymmetric per Decision I — no explicit_yes gate, no backing
    requirement. Audit-log carries any prior backing for the v→p
    signal.
    """
    _validate_demotion_bands(
        altitude="objective",
        target_id=target_id,
        from_band=from_band,
        to_band=to_band,
    )
    return ObjectiveRatificationAction(
        kind="demote",
        target_id=target_id,
        altitude="objective",
        from_band=from_band,
        to_band=to_band,
    )


def edit_objective(
    *, target_id: str, edit_text: str
) -> ObjectiveRatificationAction:
    """Edit an :class:`Objective`'s text without changing its band."""
    if not target_id:
        raise RatificationRefusedError(
            "edit_objective: target_id must be non-empty"
        )
    if not edit_text or not edit_text.strip():
        raise RatificationRefusedError(
            "edit_objective: edit_text must be non-empty"
        )
    return ObjectiveRatificationAction(
        kind="edit",
        target_id=target_id,
        altitude="objective",
        edit_text=edit_text,
    )


def reject_objective(
    *, target_id: str, reject_reason: str
) -> ObjectiveRatificationAction:
    """Drop an :class:`Objective` from the contract draft."""
    if not target_id:
        raise RatificationRefusedError(
            "reject_objective: target_id must be non-empty"
        )
    if not reject_reason or not reject_reason.strip():
        raise RatificationRefusedError(
            "reject_objective: reject_reason must be non-empty"
        )
    return ObjectiveRatificationAction(
        kind="reject",
        target_id=target_id,
        altitude="objective",
        reject_reason=reject_reason,
    )


# ---- Constraint factories (AC.OBJRAT.5) ----------------------------


def promote_constraint(
    *,
    target_id: str,
    from_band: ConfidenceBand,
    to_band: ConfidenceBand,
    explicit_yes: bool = False,
) -> ObjectiveRatificationAction:
    """Promote a :class:`Constraint`'s band per AC.OBJRAT.5.

    Constraints bound the solution space rather than deliver outcomes;
    no backing-map evidence required (per master plan §6 + sub-plan-doc
    §7). The Decision-I explicit_yes gate at PLAUSIBLE→VERIFIED still
    applies.
    """
    _validate_promotion_bands(
        altitude="constraint",
        target_id=target_id,
        from_band=from_band,
        to_band=to_band,
        explicit_yes=explicit_yes,
        backing_evidence_cited=None,
    )
    return ObjectiveRatificationAction(
        kind="promote",
        target_id=target_id,
        altitude="constraint",
        from_band=from_band,
        to_band=to_band,
        explicit_yes=explicit_yes,
    )


def demote_constraint(
    *,
    target_id: str,
    from_band: ConfidenceBand,
    to_band: ConfidenceBand,
) -> ObjectiveRatificationAction:
    """Demote a :class:`Constraint`'s band per AC.OBJRAT.5."""
    _validate_demotion_bands(
        altitude="constraint",
        target_id=target_id,
        from_band=from_band,
        to_band=to_band,
    )
    return ObjectiveRatificationAction(
        kind="demote",
        target_id=target_id,
        altitude="constraint",
        from_band=from_band,
        to_band=to_band,
    )


def edit_constraint(
    *, target_id: str, edit_text: str
) -> ObjectiveRatificationAction:
    if not target_id:
        raise RatificationRefusedError(
            "edit_constraint: target_id must be non-empty"
        )
    if not edit_text or not edit_text.strip():
        raise RatificationRefusedError(
            "edit_constraint: edit_text must be non-empty"
        )
    return ObjectiveRatificationAction(
        kind="edit",
        target_id=target_id,
        altitude="constraint",
        edit_text=edit_text,
    )


def reject_constraint(
    *, target_id: str, reject_reason: str
) -> ObjectiveRatificationAction:
    if not target_id:
        raise RatificationRefusedError(
            "reject_constraint: target_id must be non-empty"
        )
    if not reject_reason or not reject_reason.strip():
        raise RatificationRefusedError(
            "reject_constraint: reject_reason must be non-empty"
        )
    return ObjectiveRatificationAction(
        kind="reject",
        target_id=target_id,
        altitude="constraint",
        reject_reason=reject_reason,
    )


# ---- Capability factories (AC.OBJRAT.5) ----------------------------


def promote_capability(
    *,
    target_id: str,
    from_band: ConfidenceBand,
    to_band: ConfidenceBand,
    explicit_yes: bool = False,
) -> ObjectiveRatificationAction:
    """Promote a :class:`Capability`'s band per AC.OBJRAT.5.

    Apply-path validates that the capability's ``serves`` linkages
    resolve and that no served objective is HYPOTHESISED-band
    (anti-pattern: a capability cannot be verified above the objective
    it serves).
    """
    _validate_promotion_bands(
        altitude="capability",
        target_id=target_id,
        from_band=from_band,
        to_band=to_band,
        explicit_yes=explicit_yes,
        backing_evidence_cited=None,
    )
    return ObjectiveRatificationAction(
        kind="promote",
        target_id=target_id,
        altitude="capability",
        from_band=from_band,
        to_band=to_band,
        explicit_yes=explicit_yes,
    )


def demote_capability(
    *,
    target_id: str,
    from_band: ConfidenceBand,
    to_band: ConfidenceBand,
) -> ObjectiveRatificationAction:
    _validate_demotion_bands(
        altitude="capability",
        target_id=target_id,
        from_band=from_band,
        to_band=to_band,
    )
    return ObjectiveRatificationAction(
        kind="demote",
        target_id=target_id,
        altitude="capability",
        from_band=from_band,
        to_band=to_band,
    )


def edit_capability(
    *, target_id: str, edit_text: str
) -> ObjectiveRatificationAction:
    if not target_id:
        raise RatificationRefusedError(
            "edit_capability: target_id must be non-empty"
        )
    if not edit_text or not edit_text.strip():
        raise RatificationRefusedError(
            "edit_capability: edit_text must be non-empty"
        )
    return ObjectiveRatificationAction(
        kind="edit",
        target_id=target_id,
        altitude="capability",
        edit_text=edit_text,
    )


def reject_capability(
    *, target_id: str, reject_reason: str
) -> ObjectiveRatificationAction:
    if not target_id:
        raise RatificationRefusedError(
            "reject_capability: target_id must be non-empty"
        )
    if not reject_reason or not reject_reason.strip():
        raise RatificationRefusedError(
            "reject_capability: reject_reason must be non-empty"
        )
    return ObjectiveRatificationAction(
        kind="reject",
        target_id=target_id,
        altitude="capability",
        reject_reason=reject_reason,
    )


# ---- Apply path -----------------------------------------------------


def is_test_asserts_outcome(
    test_text: str,
    *,
    domain_tokens: list[str] | tuple[str, ...] = (),
) -> bool:
    """Test-asserts-outcome heuristic per sub-plan-doc §3 AC.OBJRAT.2.

    A test row qualifies when (a) its assertion text matches an
    outcome verb (should/expects/delivers/creates/rejects/completes
    /...) AND (b) it has at least one domain-noun overlap with the
    objective's domain tokens. Borderline cases (verb match but no
    domain overlap, or vice versa) → ``False`` (PLAUSIBLE-with-rationale).

    Returns ``True`` if the heuristic considers the test outcome-shaped.
    """
    if not test_text:
        return False
    if not _OUTCOME_VERB_RE.search(test_text):
        return False
    if not domain_tokens:
        return True
    blob = test_text.lower()
    for token in domain_tokens:
        if not token:
            continue
        if str(token).lower() in blob:
            return True
    return False


def _tokens_from_text(text: str) -> list[str]:
    return [t for t in _re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2]


def _resolve_p_to_v_evidence(
    *,
    target_id: str,
    cited_ids: tuple[str, ...] | list[str] | None,
    backing_map: BackingMap | None,
    objectives: list[Objective],
    repo_sha: str | None = None,
) -> None:
    """Defense-in-depth check at apply time per AC.OBJRAT.2.

    Refuses via :class:`RatificationRefusedError` naming any missing,
    insufficient, or stale-against-repo_sha citation. Each cited row
    must resolve to a STRONG-confidence backing-map entry for
    ``target_id`` OR be a ``kind="test"`` row passing the
    test-asserts-outcome heuristic at the current ``repo_sha``.
    """
    if not cited_ids:
        raise RatificationRefusedError(
            f"apply_objective_ratification_action: "
            f"PLAUSIBLE→VERIFIED on objective {target_id!r} requires "
            f"non-empty backing_evidence_cited"
        )
    if backing_map is None:
        raise RatificationRefusedError(
            f"apply_objective_ratification_action: "
            f"PLAUSIBLE→VERIFIED on objective {target_id!r} requires "
            f"a backing_map (none supplied)"
        )

    # Find the entry for this objective.
    entry = None
    for e in backing_map.entries:
        if e.objective_id == target_id:
            entry = e
            break
    if entry is None:
        raise RatificationRefusedError(
            f"apply_objective_ratification_action: backing_map has no "
            f"entry for objective {target_id!r}"
        )

    by_id = {r.evidence_row_id: r for r in entry.evidence_rows}
    objective = next(
        (o for o in objectives if o.objective_id == target_id), None
    )
    domain_tokens: list[str] = []
    if objective is not None:
        domain_tokens = list(set(
            _tokens_from_text(objective.domain)
            + _tokens_from_text(objective.text)
        ))
    for cited in cited_ids:
        ref = by_id.get(cited)
        if ref is None:
            raise RatificationRefusedError(
                f"apply_objective_ratification_action: cited evidence "
                f"row {cited!r} is not in backing_map entry for "
                f"{target_id!r} (stale citation)"
            )
        if ref.confidence == "STRONG":
            continue
        if ref.kind == "test":
            # Test-asserts-outcome heuristic.
            text_blob = (ref.symbol_name or "") + " " + cited
            if is_test_asserts_outcome(
                text_blob, domain_tokens=domain_tokens
            ):
                continue
        raise RatificationRefusedError(
            f"apply_objective_ratification_action: cited evidence "
            f"row {cited!r} is WEAK and not test-asserts-outcome; "
            f"insufficient backing for VERIFIED on {target_id!r}"
        )


def apply_objective_ratification_action(
    action: ObjectiveRatificationAction,
    *,
    objectives: list[Objective] | None = None,
    constraints: list[Constraint] | None = None,
    capabilities: list[Capability] | None = None,
    backing_map: BackingMap | None = None,
    workspace_root: Path,
    repo_id: str,
    pm_audit_path: str | None = None,
    timestamp: str | None = None,
) -> dict[str, list]:
    """Apply ``action``; return ``{"objectives", "constraints",
    "capabilities"}`` with the updated lists.

    Per AC.OBJRAT.{1,2,3,4,5}:

    - PLAUSIBLE→VERIFIED on an :class:`Objective` re-checks
      ``backing_evidence_cited`` against ``backing_map`` (defense in
      depth — even if the factory was bypassed).
    - :class:`Capability` promotions resolve ``serves`` linkages
      against the objectives list; refuses on dangling references or
      H-band served objectives.
    - Audit-log entry written with event_kind
      ``ratification_<altitude>_<kind>`` (12 kinds total).

    The ``objectives`` / ``constraints`` / ``capabilities`` arguments
    correspond to the typed lists in the v0.2.3 contract draft. Pass
    only the altitude you mutate; the others may be ``None`` (returned
    unchanged-as-empty in the output dict).

    Returns a new mapping; never mutates input lists.
    """
    objs = list(objectives or [])
    cons = list(constraints or [])
    caps = list(capabilities or [])

    altitude = action.altitude
    target_id = action.target_id

    # Defense-in-depth Decision-I gate.
    if (
        action.kind == "promote"
        and action.from_band is ConfidenceBand.PLAUSIBLE
        and action.to_band is ConfidenceBand.VERIFIED
        and not action.explicit_yes
    ):
        raise RatificationRefusedError(
            f"apply_objective_ratification_action: PLAUSIBLE→VERIFIED "
            f"requires explicit_yes=True per Decision I; "
            f"target_id={target_id!r}"
        )

    # Defense-in-depth backing-evidence gate (objective-altitude only).
    if (
        action.kind == "promote"
        and altitude == "objective"
        and action.from_band is ConfidenceBand.PLAUSIBLE
        and action.to_band is ConfidenceBand.VERIFIED
    ):
        _resolve_p_to_v_evidence(
            target_id=target_id,
            cited_ids=action.backing_evidence_cited,
            backing_map=backing_map,
            objectives=objs,
        )

    # Locate target.
    if altitude == "objective":
        target_idx = next(
            (i for i, o in enumerate(objs) if o.objective_id == target_id),
            None,
        )
        target_list = objs
    elif altitude == "constraint":
        target_idx = next(
            (i for i, k in enumerate(cons) if k.constraint_id == target_id),
            None,
        )
        target_list = cons
    elif altitude == "capability":
        target_idx = next(
            (i for i, c in enumerate(caps) if c.capability_id == target_id),
            None,
        )
        target_list = caps
    else:  # pragma: no cover — Literal-enforced
        raise RatificationRefusedError(
            f"apply_objective_ratification_action: unknown altitude "
            f"{altitude!r}"
        )

    if target_idx is None and action.kind != "reject":
        raise RatificationRefusedError(
            f"apply_objective_ratification_action: target_id "
            f"{target_id!r} not found at altitude {altitude!r}"
        )

    # Capability serves-validator (AC.OBJRAT.5).
    if (
        altitude == "capability"
        and action.kind == "promote"
        and target_idx is not None
    ):
        cap = caps[target_idx]
        obj_index = {o.objective_id: o for o in objs}
        for ref in cap.serves:
            if ref not in obj_index:
                raise RatificationRefusedError(
                    f"apply_objective_ratification_action: capability "
                    f"{target_id!r} references unknown objective "
                    f"{ref!r}"
                )
            served = obj_index[ref]
            if (
                action.to_band is ConfidenceBand.VERIFIED
                and served.confidence is ConfidenceBand.HYPOTHESISED
            ):
                raise RatificationRefusedError(
                    f"apply_objective_ratification_action: capability "
                    f"{target_id!r} cannot be promoted to VERIFIED "
                    f"while served objective {ref!r} is HYPOTHESISED"
                )

    # Apply the mutation.
    if action.kind in ("promote", "demote"):
        target = target_list[target_idx]
        if altitude == "objective":
            new_obj = target.model_copy(
                update={"confidence": action.to_band}
            )
            objs[target_idx] = new_obj
        # NOTE: Constraint + Capability models in Cycle 1 don't carry a
        # confidence field; banding for those altitudes is tracked
        # via ratification-state-v2 alone (the typed model unchanged).
    elif action.kind == "edit":
        target = target_list[target_idx]
        if altitude == "objective":
            objs[target_idx] = target.model_copy(
                update={"text": action.edit_text}
            )
        elif altitude == "constraint":
            cons[target_idx] = target.model_copy(
                update={"text": action.edit_text}
            )
        elif altitude == "capability":
            caps[target_idx] = target.model_copy(
                update={"text": action.edit_text}
            )
    elif action.kind == "reject":
        if target_idx is not None:
            target_list.pop(target_idx)

    ext_dir = extraction_dir(workspace_root, repo_id)
    ts = timestamp if timestamp is not None else _now_iso()

    # Build audit-log payload (estimate field carries structured data).
    estimate_payload: dict[str, Any] = {
        "target_id": target_id,
        "altitude": altitude,
        "band_before": (
            action.from_band.value if action.from_band else None
        ),
        "band_after": (
            action.to_band.value if action.to_band else None
        ),
        "explicit_yes": bool(action.explicit_yes),
        "backing_evidence_cited": (
            list(action.backing_evidence_cited)
            if action.backing_evidence_cited
            else None
        ),
        "pm_audit_path": pm_audit_path,
        "reject_reason": action.reject_reason,
        "edit_text_len": (
            len(action.edit_text) if action.edit_text is not None else None
        ),
    }
    write_audit_entry(
        ext_dir,
        event_kind=f"ratification_{altitude}_{action.kind}",
        extraction_id=repo_id,
        artefact_path=None,
        estimate=estimate_payload,
        notes=f"{altitude}:{action.kind}:{target_id}",
        timestamp=ts,
    )

    # Update ratification-state.yaml v2 if present.
    state_v2 = _load_state_v2(ext_dir)
    if state_v2 is not None:
        # Remove from pending_targets if present.
        state_v2.pending_targets = [
            pt for pt in state_v2.pending_targets if pt.target_id != target_id
        ]
        if state_v2.in_flight_target == target_id:
            state_v2.in_flight_target = None
        state_v2.completed_actions.append(
            CompletedAction(
                ac_id=target_id,
                action_kind=action.kind,
                applied_at=ts,
            )
        )
        # Drop altitude index entry (terminal state).
        if target_id in state_v2.altitude_index:
            state_v2.altitude_index.pop(target_id)
        save_ratification_state(ext_dir, state_v2, timestamp=ts)

    return {
        "objectives": objs,
        "constraints": cons,
        "capabilities": caps,
    }


def _load_state_v2(ext_dir: Path) -> "RatificationStateV2 | None":
    """Load the v2 state if present; converts v1 transparently."""
    raw = load_ratification_state(ext_dir)
    if raw is None:
        return None
    if isinstance(raw, RatificationStateV2):
        return raw
    # Should not happen — load_ratification_state is the single
    # authoritative migrating loader and always returns v2 on read.
    return None


# ---- Altitude-tagged enqueue extension (AC.OBJRAT.7) ---------------


def _provenance_for_altitude(
    extraction_id: str, altitude: ObjectiveAltitude, target_id: str
) -> str:
    """Per sub-plan-doc §7 — additive altitude-tagged provenance."""
    return f"odd-extract:{extraction_id}:{altitude}:{target_id}"


def _question_for_objective(o: Objective) -> str:
    return (
        f"Ratify Objective {o.objective_id} (currently "
        f"{o.confidence.value}; domain={o.domain}): {o.text}\n\n"
        f"Reply with: promote / demote / edit / reject (and a reason "
        f"or new text where applicable). PLAUSIBLE→VERIFIED requires "
        f"explicit confirmation AND backing-evidence citations."
    )


def _question_for_constraint(k: Constraint) -> str:
    return (
        f"Ratify Constraint {k.constraint_id} (bounds={k.bounds_kind}): "
        f"{k.text}\n\nReply with: promote / demote / edit / reject. "
        f"PLAUSIBLE→VERIFIED requires explicit confirmation."
    )


def _question_for_capability(c: Capability) -> str:
    serves = ", ".join(c.serves)
    return (
        f"Ratify Capability {c.capability_id} (serves: {serves}): "
        f"{c.text}\n\nReply with: promote / demote / edit / reject. "
        f"PLAUSIBLE→VERIFIED requires explicit confirmation; capability "
        f"cannot promote above any served objective's band."
    )


def enqueue_objective_ratification_batch(
    *,
    extraction_id: str,
    objectives: list[Objective] | None = None,
    constraints: list[Constraint] | None = None,
    capabilities: list[Capability] | None = None,
    workspace_root: Path,
    pm_runtime,  # PMRuntime — duck-typed
    pm_handle: str,
    draft_path: str,
    timestamp: str | None = None,
) -> int:
    """Enqueue altitude-tagged ratification questions per AC.OBJRAT.7.

    Each PM ``enqueue_decision`` call gets a provenance string of
    shape ``odd-extract:{extraction_id}:{altitude}:{target_id}`` —
    additive to the v0.1.8 shape (extra colon-separated segment;
    PM-side schema untouched).

    Idempotent: skips items whose target_id already appears in
    ``completed_actions`` of the persisted ratification-state.
    """
    ext_dir = extraction_dir(workspace_root, extraction_id)

    existing = load_ratification_state(ext_dir)
    completed_ids: set[str] = set()
    if existing is not None:
        completed_ids = {ca.ac_id for ca in existing.completed_actions}

    pending: list[PendingTarget] = []
    enqueued = 0

    for o in objectives or []:
        if o.objective_id in completed_ids:
            continue
        pending.append(
            PendingTarget(
                target_id=o.objective_id, altitude="objective"
            )
        )
        pm_runtime.enqueue_decision(
            _question_for_objective(o),
            provenance=_provenance_for_altitude(
                extraction_id, "objective", o.objective_id
            ),
        )
        enqueued += 1
    for k in constraints or []:
        if k.constraint_id in completed_ids:
            continue
        pending.append(
            PendingTarget(
                target_id=k.constraint_id, altitude="constraint"
            )
        )
        pm_runtime.enqueue_decision(
            _question_for_constraint(k),
            provenance=_provenance_for_altitude(
                extraction_id, "constraint", k.constraint_id
            ),
        )
        enqueued += 1
    for c in capabilities or []:
        if c.capability_id in completed_ids:
            continue
        pending.append(
            PendingTarget(
                target_id=c.capability_id, altitude="capability"
            )
        )
        pm_runtime.enqueue_decision(
            _question_for_capability(c),
            provenance=_provenance_for_altitude(
                extraction_id, "capability", c.capability_id
            ),
        )
        enqueued += 1

    state = initialise_ratification_state(
        ext_dir,
        extraction_id=extraction_id,
        draft_path=draft_path,
        pm_handle=pm_handle,
        pending_acs=[pt.target_id for pt in pending],
        timestamp=timestamp,
    )
    # Always express altitude-tagging via v2 state shape.
    if isinstance(state, RatificationStateV2):
        existing_targets = {pt.target_id for pt in state.pending_targets}
        for pt in pending:
            if pt.target_id not in existing_targets:
                state.pending_targets.append(pt)
                state.altitude_index[pt.target_id] = pt.altitude
        save_ratification_state(ext_dir, state, timestamp=timestamp)

    return enqueued


def parse_altitude_provenance(
    provenance: str,
) -> tuple[str, ObjectiveAltitude | None, str]:
    """Decompose an altitude-tagged provenance string.

    Accepts:
    - ``odd-extract:{extraction_id}:{altitude}:{target_id}`` (v0.2.3)
    - ``odd-extract:{extraction_id}:{ac_id}`` (v0.1.8 legacy; altitude
      returned as ``None``).
    """
    if not provenance.startswith("odd-extract:"):
        raise ValueError(
            f"parse_altitude_provenance: not an odd-extract provenance: "
            f"{provenance!r}"
        )
    parts = provenance.split(":", 3)
    # parts[0] = "odd-extract"
    if len(parts) < 3:
        raise ValueError(
            f"parse_altitude_provenance: malformed provenance "
            f"{provenance!r}"
        )
    extraction_id = parts[1]
    if len(parts) == 3:
        # legacy v0.1.8
        return extraction_id, None, parts[2]
    altitude_seg = parts[2]
    target_id = parts[3]
    if altitude_seg in ("objective", "constraint", "capability"):
        return extraction_id, altitude_seg, target_id  # type: ignore[return-value]
    # Unknown altitude segment — preserve full tail as target_id, return None.
    return extraction_id, None, f"{altitude_seg}:{target_id}"
