"""Completeness interview — PM batch API consumer + question shapes.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.{4,5,6,7,8,10}:

- :func:`run_interview` — top-level entry; consumes the v0.1.7 PM
  batch API verbatim (zero PM-side edits). Enqueues one decision
  per existing-objective + flagged-missing candidate, surfaces them
  one at a time via ``surface_next_questions_batch(n=1)``, parses
  the user response, mutates the augmented set in memory, persists
  to disk after each ``record_response`` (per-response durability →
  resumability across ``/clear`` + restart).

- Question shapes (3) — confirm-existing / flag-missing-candidate /
  free-form-add. Numeric-prefix response parser. One re-ask cap on
  malformed; second malformed → defer + flag for human review.

- Persistence — augmented set at
  ``<workspace>/.loam/extractions/<repo-id>/augmented-objectives.yaml``;
  atomic tmp+rename. Round-trip via Pydantic ``model_dump`` /
  ``model_validate``.

- Audit-log — every interview action (start, confirmed, adjusted,
  flagged-out-of-scope, added-by-user, flagged-by-persona, end)
  emits a structured audit-log entry via
  :func:`observability.write_audit_entry`.
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterable, Protocol

import yaml

from .errors import OddExtractorError
from .observability import write_audit_entry
from .spec import (
    AugmentedObjectiveSet,
    FlaggedMissing,
    Objective,
    ObjectiveEvidence,
)
from .bands import ConfidenceBand


# ---- Persistence path helpers -------------------------------------


_AUGMENTED_FILENAME = "augmented-objectives.yaml"


def augmented_objectives_path(extraction_dir_: Path) -> Path:
    """``<extraction_dir>/augmented-objectives.yaml``.

    Mirrors :func:`backing_map.backing_map_path` precedent.
    """
    return extraction_dir_ / _AUGMENTED_FILENAME


# ---- Atomic write (tmp+rename) -------------------------------------


def _atomic_write_yaml(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)
        os.replace(tmp_name, str(path))
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


# ---- Persistence — load / save augmented set ----------------------


def save_augmented_objectives(
    augmented_set: AugmentedObjectiveSet,
    extraction_dir_: Path,
) -> Path:
    """Persist the augmented set atomically; returns the written path.

    Per AC.COMPINT.7 — atomic tmp+rename; idempotent on no-change.
    """
    path = augmented_objectives_path(extraction_dir_)
    payload = augmented_set.model_dump(mode="json")
    _atomic_write_yaml(path, payload)
    return path


def load_augmented_objectives(
    extraction_dir_: Path,
) -> AugmentedObjectiveSet | None:
    """Round-trip-load the augmented set, or ``None`` if absent."""
    path = augmented_objectives_path(extraction_dir_)
    if not path.exists():
        return None
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return AugmentedObjectiveSet.model_validate(raw)


# ---- Question-shape rendering -------------------------------------


# Provenance-prefix routing key per AC.COMPINT.4. Format:
# ``completeness_interview:<kind>:<id>``. The router uses this prefix
# to dispatch responses to the correct mutation handler.
_PROVENANCE_PREFIX = "completeness_interview"


def _provenance_key(kind: str, target_id: str) -> str:
    return f"{_PROVENANCE_PREFIX}:{kind}:{target_id}"


def render_confirm_existing(obj: Objective) -> str:
    """Shape (a) — confirm-existing-objective.

    Per AC.COMPINT.5: numeric-prefix response options.
    """
    return (
        f"Does this objective accurately describe what you want?\n\n"
        f"{obj.objective_id}: {obj.text}\n\n"
        f"  (1) yes-keep\n"
        f"  (2) yes-but-adjust-text [paste new text]\n"
        f"  (3) no-flag-out-of-scope\n"
        f"  (4) skip"
    )


def render_flag_missing_candidate(c: FlaggedMissing) -> str:
    """Shape (b) — flag-missing-candidate."""
    priority_letter = {"high": "H", "medium": "M", "low": "L"}.get(
        c.priority, "M"
    )
    return (
        f"Persona-flagged missing objective candidate "
        f"(priority={priority_letter}):\n\n"
        f"{c.candidate_text}\n\n"
        f"Reasoning: {c.reasoning}\n\n"
        f"  (1) yes-add-as-PLAUSIBLE\n"
        f"  (2) yes-but-rewrite [paste replacement text]\n"
        f"  (3) no-skip\n"
        f"  (4) defer"
    )


def render_free_form_add() -> str:
    """Shape (c) — free-form-add. Surfaced ONCE at end."""
    return (
        "Any objectives we missed? Answer with one or more outcome "
        "statements (or 'no'). One outcome per line; each must be at "
        "least 20 characters of plain-English description."
    )


# ---- Response parser ----------------------------------------------


_NUMERIC_PREFIX_RE = re.compile(r"^\s*\(?(\d+)\)?[\s.:-]*(.*)$", re.DOTALL)


class ParsedResponse:
    """Internal — parsed user response shape for the routing layer."""

    def __init__(
        self,
        *,
        choice: int | None,
        free_text: str,
        raw: str,
    ) -> None:
        self.choice = choice
        self.free_text = free_text
        self.raw = raw


def parse_response(raw: str) -> ParsedResponse:
    """Parse a user response string into ``(choice, free_text)``.

    - Numeric prefix (``1``, ``(1)``, ``1)``, ``1.``, ``1: ...``)
      captures the choice; remainder is free_text.
    - No numeric prefix → ``choice=None`` + free_text=raw.
    - Empty/whitespace-only → ``choice=None`` + free_text="".
    """
    if raw is None:
        return ParsedResponse(choice=None, free_text="", raw="")
    s = raw.strip()
    if not s:
        return ParsedResponse(choice=None, free_text="", raw=raw)
    m = _NUMERIC_PREFIX_RE.match(s)
    if m:
        try:
            choice = int(m.group(1))
        except ValueError:
            choice = None
        free_text = (m.group(2) or "").strip()
        return ParsedResponse(choice=choice, free_text=free_text, raw=raw)
    return ParsedResponse(choice=None, free_text=s, raw=raw)


# ---- Augmented-set mutators ----------------------------------------


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _next_user_added_id(
    objectives: Iterable[Objective], domain: str
) -> str:
    """Mint the next ``O.<domain>.<n>`` id that doesn't collide.

    Per AC.COMPINT.6: user-added objectives need stable IDs. Domain
    is normalised to a slug; ``n`` is the smallest integer >=1 that
    yields a non-colliding ID.
    """
    safe_domain = re.sub(r"[^a-z0-9-]+", "-", (domain or "user-added").lower())
    safe_domain = safe_domain.strip("-") or "user-added"
    used: set[str] = {o.objective_id for o in objectives}
    n = 1
    while True:
        candidate = f"O.{safe_domain}.{n}"
        if candidate not in used:
            return candidate
        n += 1


def _build_user_added_objective(
    *,
    text: str,
    domain: str,
    source: str,
    audit_path_relative: str,
    rationale: str,
    existing: Iterable[Objective],
) -> Objective:
    """Construct a PLAUSIBLE-band Objective from interview input.

    Per AC.COMPINT.6: PLAUSIBLE invariants require at least one of
    ``readme_excerpts`` / ``design_doc_refs`` / ``survey_line_refs``.
    The interview audit-log entry is the survey-line ref.
    """
    new_id = _next_user_added_id(existing, domain)
    return Objective(
        objective_id=new_id,
        text=text,
        confidence=ConfidenceBand.PLAUSIBLE,
        domain=re.sub(r"[^a-z0-9-]+", "-", (domain or "user-added").lower()).strip("-") or "user-added",
        source=source,  # type: ignore[arg-type]
        evidence=ObjectiveEvidence(
            survey_line_refs=[audit_path_relative],
            rationale=rationale,
        ),
    )


# ---- PM-handle resolution -----------------------------------------


def _scan_workspace_pms(workspace_root: Path) -> list[str]:
    """Return the list of PM handles (subdir names) under
    ``<workspace>/workspace/.loam/pms/``.

    Returns ``[]`` if the directory doesn't exist.
    """
    pm_root = workspace_root / "workspace" / ".loam" / "pms"
    if not pm_root.exists() or not pm_root.is_dir():
        return []
    return sorted(p.name for p in pm_root.iterdir() if p.is_dir())


def resolve_pm_handle(
    workspace_root: Path,
    explicit_handle: str | None,
) -> str:
    """Per sub-plan-doc §6.5: explicit > scan(one) > halt.

    Raises :class:`OddExtractorError` on zero (halt) or >1
    (explicit-required) so the CLI's existing
    ``except OddExtractorError`` catch produces a clean
    actionable error + exit code 2 (no Python traceback leaks
    to the user). v0.2.5 corrective C2 per the v0.2.5 HARD
    smoke RED finding F2.
    """
    if explicit_handle:
        return explicit_handle
    discovered = _scan_workspace_pms(workspace_root)
    if not discovered:
        raise OddExtractorError(
            "No PM authored under "
            f"{workspace_root}/workspace/.loam/pms/. Run `loam project "
            "init` to author one, or pass --pm-handle explicitly."
        )
    if len(discovered) > 1:
        raise OddExtractorError(
            f"Multiple PMs authored under {workspace_root}/workspace/"
            f".loam/pms/ ({', '.join(discovered)}); pass --pm-handle "
            "explicitly to disambiguate."
        )
    return discovered[0]


# ---- PM Protocol (test-friendly) -----------------------------------


class _PMProtocol(Protocol):
    """Structural protocol over the v0.1.7 PMRuntime surface we use.

    Tests can pass a stub matching this shape without importing
    :class:`loam.per_project_pm.PMRuntime`. The real runtime
    satisfies it structurally.
    """

    def enqueue_decision(
        self, question_text: str, *, provenance: str | None = None
    ) -> int: ...

    def surface_next_questions_batch(
        self, n: int | None = None
    ) -> tuple[Any, ...]: ...

    def record_response(
        self, surfaced_audit_path: Any, response_text: str
    ) -> Any: ...


# ---- Response router ----------------------------------------------


def _audit_path_relative_to_extraction_dir(
    audit_path: Any, extraction_dir_: Path
) -> str:
    """Best-effort relative-path string for audit refs."""
    try:
        ap = Path(audit_path)
    except (TypeError, ValueError):
        return str(audit_path)
    try:
        return str(ap.relative_to(extraction_dir_))
    except ValueError:
        return str(ap)


def _emit_audit(
    extraction_dir_: Path,
    *,
    event_kind: str,
    extraction_id: str,
    estimate: dict,
    notes: str = "",
) -> Path:
    """Wrap :func:`observability.write_audit_entry` for interview events."""
    return write_audit_entry(
        extraction_dir_,
        event_kind=event_kind,
        extraction_id=extraction_id,
        stage="generate",  # completeness lives logically in generate
        estimate=estimate,
        notes=notes,
    )


# Provenance keys used by the run loop's response-routing logic.
_KIND_CONFIRM = "confirm_existing"
_KIND_FLAG = "flag_missing"
_KIND_FREE_FORM = "free_form_add"


# ---- Main entry — run_interview -----------------------------------


# Type aliases for caller-injected response producers (test-time).
ResponseProducer = Callable[[Any], str]
"""Callback that takes a SurfacedQuestion-like object + returns the
user's response text. In CLI runtime this would relay the question
out to the user-visible channel and read the typed response back."""


def run_interview(
    *,
    workspace_root: Path,
    extraction_dir_: Path,
    extraction_id: str,
    pm: _PMProtocol,
    augmented_set_in: AugmentedObjectiveSet,
    flagged_missing: list[FlaggedMissing],
    response_producer: ResponseProducer,
) -> AugmentedObjectiveSet:
    """Run the completeness interview to completion (or until kill).

    Per sub-plan-doc §3 AC.COMPINT.4 + AC.COMPINT.6 + AC.COMPINT.10:

    - **Resumability:** if an ``augmented-objectives.yaml`` already
      exists at the canonical path AND its ``extraction_id`` matches,
      its objective list is the resume baseline (durability of
      per-response writes ensures we don't re-ask answered questions).
    - **One-question-at-a-time:** strictly enforced via
      ``surface_next_questions_batch(n=1)`` per loop iteration.
    - **Per-response durability:** augmented set is persisted after
      every mutation (not at end-of-batch) so a kill mid-interview
      leaves a recoverable state.
    - **Audit-log floor:** every action emits an audit-log entry.

    Inputs:

    - ``augmented_set_in`` — the starting augmented set; typically
      derived from the v0.2.3 ``objectives.yaml`` (each objective's
      ``source`` defaults to ``"extracted"``).
    - ``flagged_missing`` — output of
      :func:`completeness.flag_missing_objectives` (cap ≤ 5).
    - ``response_producer`` — caller-supplied callback that takes a
      :class:`SurfacedQuestion` and returns the user's response text.

    Returns the final :class:`AugmentedObjectiveSet`. The same value
    is also persisted at the canonical path on every mutation.
    """
    # Resume — if an augmented set already exists at the canonical
    # path with matching extraction_id, use it as baseline (its
    # objectives shadow ``augmented_set_in.objectives``). This
    # allows a re-invocation after kill to pick up the per-response
    # writes from the prior partial run.
    existing_on_disk = load_augmented_objectives(extraction_dir_)
    if (
        existing_on_disk is not None
        and existing_on_disk.extraction_id == extraction_id
    ):
        objectives_resume = list(existing_on_disk.objectives)
    else:
        objectives_resume = list(augmented_set_in.objectives)

    audit_root = extraction_dir_ / "audit-log"
    audit_path_str = str(audit_root)

    # Working augmented set; persisted after every mutation.
    set_now = AugmentedObjectiveSet(
        extraction_id=extraction_id,
        augmented_at=_now_iso(),
        interview_audit_path=audit_path_str,
        objectives=objectives_resume,
    )

    # Prior audit-log scan — find which (kind, target_id) pairs were
    # already-answered in a prior partial run (resume defence).
    answered_keys = _scan_answered_keys(audit_root)

    # ---- Emit start audit -----------------------------------------
    pre_count = len(set_now.objectives)
    flagged_count = len(flagged_missing)
    _emit_audit(
        extraction_dir_,
        event_kind="completeness_interview_start",
        extraction_id=extraction_id,
        estimate={
            "extraction_id": extraction_id,
            "objective_count_pre": pre_count,
            "flagged_missing_count": flagged_count,
        },
    )

    # Persist baseline so resume from here is well-defined.
    save_augmented_objectives(set_now, extraction_dir_)

    # ---- Build queue: confirm + flag + free-form -----------------
    # Track (kind, target_id) per enqueue so we can route responses
    # via the prefix — provenance carries the routing key.
    enqueue_plan: list[tuple[str, str, str]] = []  # (kind, target_id, text)
    for obj in list(set_now.objectives):
        if obj.source != "extracted":
            # Already user-added or persona-flagged: no need to
            # re-confirm.
            continue
        key = (_KIND_CONFIRM, obj.objective_id)
        if key in answered_keys:
            continue
        enqueue_plan.append(
            (_KIND_CONFIRM, obj.objective_id, render_confirm_existing(obj))
        )
    for i, c in enumerate(flagged_missing):
        target_id = f"flag-{i}"
        key = (_KIND_FLAG, target_id)
        if key in answered_keys:
            continue
        enqueue_plan.append(
            (_KIND_FLAG, target_id, render_flag_missing_candidate(c))
        )

    free_form_target = "free-form-add"
    free_form_key = (_KIND_FREE_FORM, free_form_target)
    if free_form_key not in answered_keys:
        enqueue_plan.append(
            (_KIND_FREE_FORM, free_form_target, render_free_form_add())
        )

    # Map flagged_missing index -> FlaggedMissing for routing.
    flagged_by_target: dict[str, FlaggedMissing] = {
        f"flag-{i}": c for i, c in enumerate(flagged_missing)
    }

    # ---- Enqueue all plan entries (the PM is FIFO; we surface 1
    # at a time below). Per AC.COMPINT.4 — read-only PM consumption.
    for kind, tid, text in enqueue_plan:
        provenance = _provenance_key(kind, tid)
        pm.enqueue_decision(text, provenance=provenance)

    # ---- Tally counters for end-event payload --------------------
    added_count = 0
    removed_count = 0
    adjusted_count = 0
    confirmed_count = 0
    flagged_persona_count = 0

    # ---- Drain queue one-at-a-time --------------------------------
    while True:
        batch = pm.surface_next_questions_batch(n=1)
        if not batch:
            break
        sq = batch[0]
        kind, target_id = _decode_provenance(getattr(sq, "provenance", None))
        if kind is None:
            # Skip unknown provenance — defensive (out-of-band enqueues).
            pm.record_response(getattr(sq, "audit_path", None), "skipped")
            continue

        # ---- Get response (with one re-ask cap) ------------------
        attempts = 0
        max_attempts = 2
        parsed: ParsedResponse | None = None
        response_text = ""
        while attempts < max_attempts:
            response_text = response_producer(sq)
            parsed = parse_response(response_text)
            if _response_is_well_formed(kind, parsed):
                break
            attempts += 1
        # Record response on the PM regardless — audit-log captures
        # what was said.
        recorded = pm.record_response(
            getattr(sq, "audit_path", None), response_text
        )
        recorded_audit = getattr(recorded, "audit_path", None)
        recorded_audit_relative = _audit_path_relative_to_extraction_dir(
            recorded_audit, extraction_dir_
        )

        if (
            parsed is None
            or not _response_is_well_formed(kind, parsed)
        ):
            # Defer slot — record an event and move on per AC.COMPINT.5
            # ("second malformed → defer slot + flag for human review").
            _emit_audit(
                extraction_dir_,
                event_kind="objective_flagged_out_of_scope",  # repurposed
                extraction_id=extraction_id,
                estimate={
                    "kind": "deferred_for_human_review",
                    "interview_kind": kind,
                    "target_id": target_id,
                    "response_audit_path": recorded_audit_relative,
                    "reason": "malformed_response_after_re_ask_cap",
                },
                notes="deferred_after_malformed_re_ask",
            )
            continue

        # ---- Route to handler -------------------------------------
        if kind == _KIND_CONFIRM:
            obj = _find_objective_by_id(set_now.objectives, target_id)
            if obj is None:
                continue
            choice = parsed.choice
            free = parsed.free_text
            if choice == 1:
                # Confirm-keep — no mutation; emit audit only.
                _emit_audit(
                    extraction_dir_,
                    event_kind="objective_confirmed",
                    extraction_id=extraction_id,
                    estimate={
                        "objective_id": target_id,
                        "response_audit_path": recorded_audit_relative,
                    },
                )
                confirmed_count += 1
            elif choice == 2:
                # Adjust-text — replace text in place; preserve source.
                if not free or len(free) < 20:
                    # Treat short adjustment as malformed → defer.
                    _emit_audit(
                        extraction_dir_,
                        event_kind="objective_flagged_out_of_scope",
                        extraction_id=extraction_id,
                        estimate={
                            "kind": "deferred_for_human_review",
                            "interview_kind": kind,
                            "target_id": target_id,
                            "response_audit_path": recorded_audit_relative,
                            "reason": "adjust_text_below_20_chars",
                        },
                        notes="deferred_short_adjust_text",
                    )
                else:
                    new_obj = obj.model_copy(update={"text": free})
                    set_now = _replace_objective(set_now, target_id, new_obj)
                    _emit_audit(
                        extraction_dir_,
                        event_kind="objective_adjusted",
                        extraction_id=extraction_id,
                        estimate={
                            "objective_id": target_id,
                            "old_text_len": len(obj.text),
                            "new_text_len": len(free),
                            "response_audit_path": recorded_audit_relative,
                        },
                    )
                    adjusted_count += 1
            elif choice == 3:
                # Flag-out-of-scope → remove.
                set_now = _remove_objective(set_now, target_id)
                _emit_audit(
                    extraction_dir_,
                    event_kind="objective_flagged_out_of_scope",
                    extraction_id=extraction_id,
                    estimate={
                        "objective_id": target_id,
                        "response_audit_path": recorded_audit_relative,
                        "rationale": free or "(none)",
                    },
                )
                removed_count += 1
            elif choice == 4:
                # Skip — no mutation.
                _emit_audit(
                    extraction_dir_,
                    event_kind="objective_confirmed",
                    extraction_id=extraction_id,
                    estimate={
                        "objective_id": target_id,
                        "response_audit_path": recorded_audit_relative,
                        "skipped": True,
                    },
                )
        elif kind == _KIND_FLAG:
            cand = flagged_by_target.get(target_id)
            if cand is None:
                continue
            choice = parsed.choice
            free = parsed.free_text
            if choice == 1:
                # Add as PLAUSIBLE; source=flagged_by_persona.
                new_obj = _build_user_added_objective(
                    text=cand.candidate_text,
                    domain=cand.domain or "user-added",
                    source="flagged_by_persona",
                    audit_path_relative=recorded_audit_relative,
                    rationale=cand.reasoning,
                    existing=set_now.objectives,
                )
                set_now = _append_objective(set_now, new_obj)
                _emit_audit(
                    extraction_dir_,
                    event_kind="objective_flagged_by_persona",
                    extraction_id=extraction_id,
                    estimate={
                        "objective_id": new_obj.objective_id,
                        "response_audit_path": recorded_audit_relative,
                        "candidate_text": cand.candidate_text,
                    },
                )
                flagged_persona_count += 1
            elif choice == 2:
                # Rewrite then add — source=added_by_user (user owns the text).
                if not free or len(free) < 20:
                    _emit_audit(
                        extraction_dir_,
                        event_kind="objective_flagged_out_of_scope",
                        extraction_id=extraction_id,
                        estimate={
                            "kind": "deferred_for_human_review",
                            "interview_kind": kind,
                            "target_id": target_id,
                            "response_audit_path": recorded_audit_relative,
                            "reason": "rewrite_below_20_chars",
                        },
                        notes="deferred_short_rewrite_text",
                    )
                else:
                    new_obj = _build_user_added_objective(
                        text=free,
                        domain=cand.domain or "user-added",
                        source="added_by_user",
                        audit_path_relative=recorded_audit_relative,
                        rationale=(
                            "user-added via completeness interview "
                            "(rewrite of persona-flagged candidate)"
                        ),
                        existing=set_now.objectives,
                    )
                    set_now = _append_objective(set_now, new_obj)
                    _emit_audit(
                        extraction_dir_,
                        event_kind="objective_added_by_user",
                        extraction_id=extraction_id,
                        estimate={
                            "objective_id": new_obj.objective_id,
                            "response_audit_path": recorded_audit_relative,
                            "text": free,
                        },
                    )
                    added_count += 1
            elif choice == 3:
                # Skip flagged candidate — no mutation, audit only.
                _emit_audit(
                    extraction_dir_,
                    event_kind="objective_flagged_out_of_scope",
                    extraction_id=extraction_id,
                    estimate={
                        "kind": "candidate_skipped",
                        "interview_kind": kind,
                        "target_id": target_id,
                        "response_audit_path": recorded_audit_relative,
                    },
                )
            elif choice == 4:
                # Defer — audit only.
                _emit_audit(
                    extraction_dir_,
                    event_kind="objective_flagged_out_of_scope",
                    extraction_id=extraction_id,
                    estimate={
                        "kind": "candidate_deferred",
                        "interview_kind": kind,
                        "target_id": target_id,
                        "response_audit_path": recorded_audit_relative,
                    },
                )
        elif kind == _KIND_FREE_FORM:
            # Parse one or more outcome-statements (one per line).
            text = parsed.raw if parsed.raw else ""
            if text.strip().lower() in ("no", "none", "(no)", "n"):
                # Trivial-no path; nothing added.
                _emit_audit(
                    extraction_dir_,
                    event_kind="objective_added_by_user",
                    extraction_id=extraction_id,
                    estimate={
                        "kind": "free_form_no_additions",
                        "response_audit_path": recorded_audit_relative,
                    },
                )
            else:
                lines = [
                    ln.strip()
                    for ln in text.splitlines()
                    if ln.strip() and len(ln.strip()) >= 20
                ]
                # Tolerate a single-line response without newline.
                if not lines and len(text.strip()) >= 20:
                    lines = [text.strip()]
                for ln in lines:
                    new_obj = _build_user_added_objective(
                        text=ln,
                        domain="user-added",
                        source="added_by_user",
                        audit_path_relative=recorded_audit_relative,
                        rationale="user-added via free-form-add",
                        existing=set_now.objectives,
                    )
                    set_now = _append_objective(set_now, new_obj)
                    _emit_audit(
                        extraction_dir_,
                        event_kind="objective_added_by_user",
                        extraction_id=extraction_id,
                        estimate={
                            "objective_id": new_obj.objective_id,
                            "response_audit_path": recorded_audit_relative,
                            "text": ln,
                        },
                    )
                    added_count += 1

        # Per-response durability (AC.COMPINT.10).
        save_augmented_objectives(set_now, extraction_dir_)

    # ---- End audit + final write ----------------------------------
    _emit_audit(
        extraction_dir_,
        event_kind="completeness_interview_end",
        extraction_id=extraction_id,
        estimate={
            "extraction_id": extraction_id,
            "objective_count_post": len(set_now.objectives),
            "added_count": added_count,
            "removed_count": removed_count,
            "adjusted_count": adjusted_count,
            "confirmed_count": confirmed_count,
            "flagged_persona_count": flagged_persona_count,
        },
    )
    save_augmented_objectives(set_now, extraction_dir_)
    return set_now


# ---- Helpers used by run_interview --------------------------------


def _decode_provenance(provenance: str | None) -> tuple[str | None, str]:
    """Pull (kind, target_id) out of a ``completeness_interview:K:T`` string."""
    if not provenance:
        return None, ""
    parts = provenance.split(":", 2)
    if len(parts) < 3 or parts[0] != _PROVENANCE_PREFIX:
        return None, ""
    return parts[1], parts[2]


def _response_is_well_formed(kind: str, parsed: ParsedResponse) -> bool:
    """A response is well-formed when it carries a numeric choice
    (for confirm/flag) OR free-text (for free-form-add)."""
    if kind == _KIND_FREE_FORM:
        # Free-form requires either "no" sentinel or >=20-char content.
        if parsed.choice is not None:
            return False
        text = parsed.free_text or parsed.raw or ""
        if text.strip().lower() in ("no", "none", "(no)", "n"):
            return True
        if len(text.strip()) >= 20:
            return True
        return False
    return parsed.choice in (1, 2, 3, 4)


def _find_objective_by_id(
    objectives: list[Objective], objective_id: str
) -> Objective | None:
    for o in objectives:
        if o.objective_id == objective_id:
            return o
    return None


def _replace_objective(
    s: AugmentedObjectiveSet, objective_id: str, new_obj: Objective
) -> AugmentedObjectiveSet:
    new_list = [
        new_obj if o.objective_id == objective_id else o
        for o in s.objectives
    ]
    return AugmentedObjectiveSet(
        extraction_id=s.extraction_id,
        augmented_at=_now_iso(),
        interview_audit_path=s.interview_audit_path,
        objectives=new_list,
    )


def _remove_objective(
    s: AugmentedObjectiveSet, objective_id: str
) -> AugmentedObjectiveSet:
    new_list = [o for o in s.objectives if o.objective_id != objective_id]
    return AugmentedObjectiveSet(
        extraction_id=s.extraction_id,
        augmented_at=_now_iso(),
        interview_audit_path=s.interview_audit_path,
        objectives=new_list,
    )


def _append_objective(
    s: AugmentedObjectiveSet, new_obj: Objective
) -> AugmentedObjectiveSet:
    return AugmentedObjectiveSet(
        extraction_id=s.extraction_id,
        augmented_at=_now_iso(),
        interview_audit_path=s.interview_audit_path,
        objectives=[*s.objectives, new_obj],
    )


def _scan_answered_keys(audit_root: Path) -> set[tuple[str, str]]:
    """Resume defence — scan extraction-dir audit-log for already-
    answered ``(kind, target_id)`` pairs.

    Per AC.COMPINT.10: re-invocation after a kill should not re-ask
    questions whose interview-side mutations were already audit-logged
    + persisted to disk.
    """
    out: set[tuple[str, str]] = set()
    if not audit_root.exists():
        return out
    for entry in audit_root.iterdir():
        if not entry.is_file() or not entry.name.endswith(".yaml"):
            continue
        try:
            payload = yaml.safe_load(entry.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        if not isinstance(payload, dict):
            continue
        kind_event = payload.get("event_kind")
        est = payload.get("estimate") or {}
        if not isinstance(est, dict):
            continue
        # confirm-existing routes to objective_confirmed / adjusted /
        # flagged_out_of_scope.
        if kind_event in (
            "objective_confirmed",
            "objective_adjusted",
        ):
            target = est.get("objective_id")
            if isinstance(target, str):
                out.add((_KIND_CONFIRM, target))
        if kind_event == "objective_flagged_out_of_scope":
            ik = est.get("interview_kind")
            tid = est.get("target_id")
            if isinstance(ik, str) and isinstance(tid, str):
                out.add((ik, tid))
            else:
                # Plain "remove" via choice (3) on confirm-existing.
                target = est.get("objective_id")
                if isinstance(target, str):
                    out.add((_KIND_CONFIRM, target))
        if kind_event == "objective_flagged_by_persona":
            # We don't easily recover the (flag-i) target_id from the
            # persisted record; rely on the per-response disk write
            # of the augmented set as the authoritative resume signal
            # for additions. This keeps free-form / flag re-ask
            # bounded by the in-flight queue rather than scan.
            pass
        if kind_event == "objective_added_by_user":
            kind_meta = est.get("kind")
            if kind_meta == "free_form_no_additions":
                out.add((_KIND_FREE_FORM, "free-form-add"))
            else:
                # Free-form additions complete the free-form slot.
                out.add((_KIND_FREE_FORM, "free-form-add"))
    return out
