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
from typing import Literal

from .bands import BandedAC, ConfidenceBand, Evidence
from .errors import RatificationRefusedError
from .observability import write_audit_entry
from .ratification_state import (
    CompletedAction,
    RatificationState,
    initialise_ratification_state,
    load_ratification_state,
    save_ratification_state,
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

    # Update ratification-state.yaml.
    state = load_ratification_state(ext_dir)
    if state is not None:
        if action.ac_id in state.pending_acs:
            state.pending_acs = [
                a for a in state.pending_acs if a != action.ac_id
            ]
        if state.in_flight_action == action.ac_id:
            state.in_flight_action = None
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
        for ac_id in pending_ac_ids:
            if ac_id not in existing_pending:
                new_pending.append(ac_id)
        state.pending_acs = new_pending
        save_ratification_state(ext_dir, state, timestamp=timestamp)

    return enqueued_count
