"""v0.2.4 Cycle 2 — Gap analysis.

Per sub-plan-doc §3 AC.GAPAN.{3,4,5} + §7 method-decision register:

- :func:`analyze_gaps` — pure function over (augmented_objectives,
  backing_map, evidence_rows, extraction_id) → :class:`GapInventory`.
  No I/O. Deterministic. No LLM call.
- :func:`_classify_confidence` — STRONG/WEAK rule per AC.GAPAN.4.
- :func:`save_gap_inventory` / :func:`load_gap_inventory` — atomic
  persistence at ``<extraction_dir>/gap-inventory.yaml`` per
  AC.GAPAN.5; idempotent on no-change (content-hash sans
  ``analyzed_at``).

The two gap categories per master plan §3 v0.2.4 + sub-plan-doc §1:

a. ``objective_without_verified_backing`` — backing-map entry empty
   OR all evidence-rows WEAK OR HYPOTHESISED-with-no-rows.
b. ``implementation_orphan`` — evidence-rows the backing-map did not
   match to any objective (orphans). Same-source-file orphans
   collapse into a single Gap per AC.GAPAN.3 §7.

Negative-alignment (the third category) is OUT OF SCOPE per Luke
2026-05-05; carved to v0.2.6+. The forward-compat field
:attr:`Gap.negative_alignment_evidence` carries the seam (always
``None`` at v0.2.4 per AC.GAPAN.8).
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import yaml

from .bands import ConfidenceBand
from .observability import write_audit_entry
from .spec import (
    AugmentedObjectiveSet,
    BackingMap,
    EvidenceRowRef,
    Gap,
    GapInventory,
    GapSummary,
)


_GAP_INVENTORY_FILENAME = "gap-inventory.yaml"
_GAP_INVENTORY_SCHEMA_VERSION = 1


# ====================================================================
# Persistence path helpers (AC.GAPAN.5)
# ====================================================================


def gap_inventory_path(extraction_dir_: Path) -> Path:
    """``<extraction_dir>/gap-inventory.yaml``.

    Mirrors :func:`backing_map.backing_map_path` precedent.
    """
    return extraction_dir_ / _GAP_INVENTORY_FILENAME


# ====================================================================
# Slug helpers (gap_id construction; AC.GAPAN.1 regex compliance)
# ====================================================================


_SLUG_BAD_CHARS = re.compile(r"[^a-z0-9_-]+")


def _slugify(value: str) -> str:
    """Lowercase + collapse non-``[a-z0-9_-]`` runs into ``-``.

    Used for both objective-id derived gap-ids (category-a) and
    file-derived gap-ids (category-b). Resulting slug satisfies
    the ``[a-z0-9_-]+`` portion of the gap_id regex.
    """
    s = value.lower()
    s = _SLUG_BAD_CHARS.sub("-", s)
    s = s.strip("-_")
    return s or "row"


# ====================================================================
# Confidence rule (AC.GAPAN.4)
# ====================================================================


def _is_test_or_config_kind(kind: str) -> bool:
    """``test`` is the canonical test-row kind; pattern rows under
    config-shape paths are downgraded by :func:`_classify_orphan_kinds`.
    """
    return kind == "test"


def _classify_confidence_category_a(
    *,
    band: ConfidenceBand,
    rows_present: bool,
    all_rows_weak: bool,
) -> str:
    """STRONG/WEAK rule for category-a (objective_without_verified_backing).

    STRONG when:
      - V/P band + empty backing (objective is V or P AND no rows present).

    WEAK when:
      - HYPOTHESISED band (regardless of rows).
      - V/P band + rows present but all WEAK (no STRONG row backs the
        objective).

    Per AC.GAPAN.4 + sub-plan-doc §1 Pin 2.
    """
    if band is ConfidenceBand.HYPOTHESISED:
        return "WEAK"
    # V/P band:
    if not rows_present:
        return "STRONG"
    # rows_present and all_rows_weak:
    if all_rows_weak:
        return "WEAK"
    # If we got here, the objective has at least one STRONG row →
    # there's no gap; caller filters before calling.
    raise AssertionError(
        "_classify_confidence_category_a called on a non-gap objective"
    )


def _classify_confidence_category_b(
    *,
    has_non_test_or_config_row: bool,
) -> str:
    """STRONG/WEAK rule for category-b (implementation_orphan).

    STRONG when at least one orphan row in the cluster is NOT a
    test/config row (production code dominates per sub-plan-doc §1).
    WEAK when all rows in the cluster are test/config-only.

    Per AC.GAPAN.4 + sub-plan-doc §1 Pin 2.
    """
    return "STRONG" if has_non_test_or_config_row else "WEAK"


def _classify_confidence(
    *,
    category: str,
    band: ConfidenceBand | None = None,
    rows_present: bool | None = None,
    all_rows_weak: bool | None = None,
    has_non_test_or_config_row: bool | None = None,
) -> str:
    """Dispatch to the per-category rule. Public-ish helper for tests.

    Per AC.GAPAN.4 — keeps both rules in one named symbol so tests
    can table-drive across all branches.
    """
    if category == "objective_without_verified_backing":
        if band is None or rows_present is None or all_rows_weak is None:
            raise ValueError(
                "category-a confidence rule requires band + rows_present "
                "+ all_rows_weak"
            )
        return _classify_confidence_category_a(
            band=band,
            rows_present=rows_present,
            all_rows_weak=all_rows_weak,
        )
    if category == "implementation_orphan":
        if has_non_test_or_config_row is None:
            raise ValueError(
                "category-b confidence rule requires "
                "has_non_test_or_config_row"
            )
        return _classify_confidence_category_b(
            has_non_test_or_config_row=has_non_test_or_config_row,
        )
    raise ValueError(f"unknown gap category: {category!r}")


# ====================================================================
# Evidence-row dict → EvidenceRowRef coercion
# ====================================================================


def _coerce_row_to_ref(row: dict, default_language: str = "other") -> EvidenceRowRef:
    """Coerce a raw evidence-row dict (BandedAC shape) to an
    :class:`EvidenceRowRef`.

    Adapter outputs land in evidence-rows.yaml as plain dicts under
    ``acs:``. The dict shape (BandedAC) carries ``ac_id`` + ``kind``
    + ``path`` + optional ``line_range`` + optional ``symbol_name``.
    The ``ac_id`` field is the composite ``kind:path:line`` slug
    that :class:`EvidenceRowRef.evidence_row_id` validates against.

    Confidence on orphan refs defaults to ``WEAK`` — orphans are by
    definition not strongly tied to any objective (they're un-claimed).
    """
    line_range = row.get("line_range")
    if line_range is not None and isinstance(line_range, list):
        # YAML serialises tuples as lists — coerce to 2-tuple of ints.
        line_range = tuple(int(x) for x in line_range[:2])
    return EvidenceRowRef(
        evidence_row_id=row.get("ac_id") or row.get("evidence_row_id") or "pattern:unknown",
        kind=row.get("kind") or "other",
        path=row.get("path") or "unknown",
        line_range=line_range,
        symbol_name=row.get("symbol_name"),
        language=row.get("language") or default_language,
        confidence="WEAK",
    )


# ====================================================================
# Pure-function gap analysis (AC.GAPAN.3)
# ====================================================================


def analyze_gaps(
    *,
    augmented_objectives: AugmentedObjectiveSet,
    backing_map: BackingMap,
    evidence_rows: list[dict],
    extraction_id: str,
    analyzed_at: str | None = None,
    audit_path: str | None = None,
) -> GapInventory:
    """Produce a :class:`GapInventory` from the typed substrate.

    Per sub-plan-doc §3 AC.GAPAN.3:

    - Pure function. No I/O. Deterministic. No LLM call.
    - Iterates objectives → category-a Gaps when backing entry is
      empty / all-rows-WEAK / HYPOTHESISED-with-no-rows.
    - Iterates evidence-rows → category-b Gaps for orphans (rows the
      backing-map did not match to any objective). Same-source-file
      orphans collapse per §7 ("same-file collapses unless distinct
      symbols").
    - Confidence per :func:`_classify_confidence`.
    - ``analyzed_at`` defaults to ``_now_iso()``; tests inject for
      determinism.
    - ``audit_path`` defaults to ``"(unset)"``; CLI fills with the
      canonical audit-log dir.
    """
    if analyzed_at is None:
        analyzed_at = _dt.datetime.now(_dt.timezone.utc).isoformat()

    # Build objective-id → Objective lookup for the augmented set.
    aug_by_id = {o.objective_id: o for o in augmented_objectives.objectives}

    # Build objective-id → BackingMapEntry lookup.
    bm_by_id = {e.objective_id: e for e in backing_map.entries}

    # ---- Category A: objectives_without_verified_backing ---------
    # An objective is a category-a gap when:
    #   (1) backing entry exists but evidence_rows is empty (V/P band
    #       + empty-backing → STRONG; HYPOTHESISED + empty → WEAK).
    #   (2) backing entry exists with rows but ALL rows are WEAK.
    #   (3) backing entry is missing entirely (treated identically to
    #       (1) — empty backing).
    category_a_gaps: list[Gap] = []
    for obj_id, obj in aug_by_id.items():
        entry = bm_by_id.get(obj_id)
        rows = entry.evidence_rows if entry is not None else []
        rows_present = bool(rows)
        if rows_present:
            all_rows_weak = all(r.confidence == "WEAK" for r in rows)
            # Has STRONG row → fully backed; not a gap.
            if not all_rows_weak:
                continue
        else:
            all_rows_weak = False  # vacuous
        confidence = _classify_confidence(
            category="objective_without_verified_backing",
            band=obj.confidence,
            rows_present=rows_present,
            all_rows_weak=all_rows_weak,
        )
        if rows_present:
            reason = (
                "all backing-map evidence rows are WEAK "
                f"(no STRONG row backs this {obj.confidence.value} objective)"
            )
        elif obj.confidence is ConfidenceBand.HYPOTHESISED:
            reason = (
                "objective is HYPOTHESISED with no backing-map evidence "
                "rows; backing relationship has not been established"
            )
        else:
            reason = (
                f"{obj.confidence.value} objective has empty backing-map "
                "entry; no implementation evidence rows are claimed by it"
            )
        rationale = (
            f"Objective {obj.objective_id} ({obj.confidence.value}) "
            f"flagged as backing gap — {reason}."
        )
        gap_id = f"G.BACKING.{_slugify(obj_id)}"
        category_a_gaps.append(
            Gap(
                gap_id=gap_id,
                category="objective_without_verified_backing",
                confidence=confidence,
                objective_id=obj_id,
                evidence_rows=list(rows),
                rationale=rationale,
                negative_alignment_evidence=None,
            )
        )

    # ---- Category B: implementation_orphans ----------------------
    # An evidence-row is an orphan when no backing-map entry's
    # ``evidence_rows`` references it. Orphans are clustered by
    # source-file (same-file collapse per §7); each cluster yields
    # one Gap.
    claimed_row_ids: set[str] = set()
    for entry in backing_map.entries:
        for r in entry.evidence_rows:
            claimed_row_ids.add(r.evidence_row_id)

    # Coerce raw evidence-row dicts → EvidenceRowRef + filter to
    # orphans.
    orphan_refs: list[EvidenceRowRef] = []
    for row in evidence_rows:
        # Adapters emit ``ac_id`` (BandedAC); fall back to
        # ``evidence_row_id`` for already-typed inputs.
        row_id = row.get("ac_id") or row.get("evidence_row_id")
        if not row_id:
            continue
        if row_id in claimed_row_ids:
            continue
        try:
            ref = _coerce_row_to_ref(row)
        except Exception:
            # Defensive — adapter row that doesn't satisfy the regex
            # is dropped rather than crashing the analysis.
            continue
        orphan_refs.append(ref)

    # Cluster orphans by source-file path. Sorted iteration for
    # determinism per AC.GAPAN.3.
    clusters: dict[str, list[EvidenceRowRef]] = {}
    for ref in orphan_refs:
        clusters.setdefault(ref.path, []).append(ref)

    category_b_gaps: list[Gap] = []
    for path in sorted(clusters.keys()):
        cluster_rows = clusters[path]
        # Has any non-test/non-config row?
        has_non_test = any(
            not _is_test_or_config_kind(r.kind) for r in cluster_rows
        )
        confidence = _classify_confidence(
            category="implementation_orphan",
            has_non_test_or_config_row=has_non_test,
        )
        gap_id = f"G.ORPHAN.{_slugify(path)}"
        kinds_summary = ", ".join(
            sorted({r.kind for r in cluster_rows})
        )
        rationale = (
            f"Implementation orphan cluster at source-file {path!r} "
            f"({len(cluster_rows)} unclaimed evidence row(s); kinds: "
            f"{kinds_summary}); group-key=path:{path}."
        )
        category_b_gaps.append(
            Gap(
                gap_id=gap_id,
                category="implementation_orphan",
                confidence=confidence,
                objective_id=None,
                evidence_rows=list(cluster_rows),
                rationale=rationale,
                negative_alignment_evidence=None,
            )
        )

    gaps = category_a_gaps + category_b_gaps
    summary = GapSummary(
        category_a_count=sum(
            1 for g in gaps
            if g.category == "objective_without_verified_backing"
        ),
        category_b_count=sum(
            1 for g in gaps if g.category == "implementation_orphan"
        ),
        strong_count=sum(1 for g in gaps if g.confidence == "STRONG"),
        weak_count=sum(1 for g in gaps if g.confidence == "WEAK"),
        total=len(gaps),
    )
    return GapInventory(
        schema_version=1,
        extraction_id=extraction_id,
        analyzed_at=analyzed_at,
        audit_path=audit_path or "(unset)",
        gaps=gaps,
        summary=summary,
    )


# ====================================================================
# Halt-on-degenerate (AC.GAPAN.4 calibration anchor)
# ====================================================================


def is_degenerate_distribution(inventory: GapInventory) -> bool:
    """100%-STRONG or 100%-WEAK on a non-trivial inventory.

    Per AC.GAPAN.4 calibration anchor: when the ``mixed/`` fixture
    produces 100%-STRONG or 100%-WEAK, the rule is mis-calibrated and
    the dispatch must halt + surface. ``total<2`` is not degenerate
    (a single gap can't span both confidences). Returns ``True`` when
    a halt-and-surface is warranted.
    """
    if inventory.summary.total < 2:
        return False
    s = inventory.summary.strong_count
    w = inventory.summary.weak_count
    return s == 0 or w == 0


# ====================================================================
# Persistence + idempotence (AC.GAPAN.5)
# ====================================================================


def _content_hash_payload(inventory: GapInventory) -> dict[str, Any]:
    """Subset of the inventory used for content-hash comparison.

    Per sub-plan-doc §6.5 mitigation: ``analyzed_at`` always changes,
    so byte-identical re-write is impossible. Idempotence holds over
    everything BUT ``analyzed_at``; the persistence layer skips writes
    when the content-hash matches.
    """
    return inventory.model_dump(
        mode="json",
        exclude={"analyzed_at"},
        exclude_none=True,
    )


def _atomic_write_yaml(path: Path, data: dict[str, Any]) -> None:
    """Atomic tmp+rename write. Mirrors backing_map.save_backing_map."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(data, fh, sort_keys=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def save_gap_inventory(
    inventory: GapInventory,
    extraction_dir_: Path,
    *,
    skip_on_no_change: bool = True,
) -> tuple[Path, bool]:
    """Persist the gap inventory atomically.

    Per AC.GAPAN.5:

    - Writes to ``<extraction_dir>/gap-inventory.yaml`` via tmp+rename.
    - Schema-versioned at v1.
    - Idempotent on no-change: when ``skip_on_no_change`` and a prior
      inventory exists with matching content-hash (sans
      ``analyzed_at``), the write is skipped and the prior file is
      left untouched.

    Returns ``(path, wrote)`` — ``wrote=True`` when the file was
    (re)written; ``wrote=False`` when the no-change skip-write fired.
    """
    p = gap_inventory_path(extraction_dir_)

    # Idempotence check — load existing + compare hash.
    if skip_on_no_change and p.exists():
        try:
            existing = load_gap_inventory(extraction_dir_)
        except Exception:
            existing = None
        if existing is not None:
            new_hash = _content_hash_payload(inventory)
            existing_hash = _content_hash_payload(existing)
            if new_hash == existing_hash:
                return p, False

    payload: dict[str, Any] = {
        "schema_version": _GAP_INVENTORY_SCHEMA_VERSION,
    }
    payload.update(inventory.model_dump(mode="json", exclude_none=True))
    _atomic_write_yaml(p, payload)
    return p, True


def load_gap_inventory(extraction_dir_: Path) -> GapInventory | None:
    """Round-trip-load the gap inventory, or ``None`` if absent."""
    p = gap_inventory_path(extraction_dir_)
    if not p.exists():
        return None
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(
            f"gap-inventory.yaml at {p}: top-level must be a mapping; "
            f"got {type(raw).__name__}"
        )
    sv = raw.get("schema_version")
    if sv != _GAP_INVENTORY_SCHEMA_VERSION:
        raise ValueError(
            f"gap-inventory.yaml: unexpected schema_version={sv!r}; "
            f"expected {_GAP_INVENTORY_SCHEMA_VERSION}"
        )
    payload = {k: v for k, v in raw.items() if k != "schema_version"}
    return GapInventory.model_validate(payload)


# ====================================================================
# Audit-log emit helpers (AC.GAPAN.6)
# ====================================================================


def emit_start_audit(
    extraction_dir_: Path,
    *,
    extraction_id: str,
    augmented_objective_count: int,
    backing_map_objective_count: int,
    evidence_row_count: int,
    timestamp: str | None = None,
) -> Path:
    """Emit ``gap_analysis_start`` audit-log entry (AC.GAPAN.6)."""
    return write_audit_entry(
        extraction_dir_,
        event_kind="gap_analysis_start",
        extraction_id=extraction_id,
        estimate={
            "extraction_id": extraction_id,
            "augmented_objective_count": augmented_objective_count,
            "backing_map_objective_count": backing_map_objective_count,
            "evidence_row_count": evidence_row_count,
        },
        timestamp=timestamp,
    )


def emit_persisted_audit(
    extraction_dir_: Path,
    *,
    extraction_id: str,
    inventory: GapInventory,
    gap_inventory_path_str: str,
    timestamp: str | None = None,
) -> Path:
    """Emit ``gap_inventory_persisted`` audit-log entry."""
    s = inventory.summary
    return write_audit_entry(
        extraction_dir_,
        event_kind="gap_inventory_persisted",
        extraction_id=extraction_id,
        artefact_path=gap_inventory_path_str,
        estimate={
            "extraction_id": extraction_id,
            "gap_count": s.total,
            "category_a_count": s.category_a_count,
            "category_b_count": s.category_b_count,
            "strong_count": s.strong_count,
            "weak_count": s.weak_count,
            "gap_inventory_path": gap_inventory_path_str,
        },
        timestamp=timestamp,
    )


def emit_end_audit(
    extraction_dir_: Path,
    *,
    extraction_id: str,
    duration_ms: int,
    timestamp: str | None = None,
) -> Path:
    """Emit ``gap_analysis_end`` audit-log entry."""
    return write_audit_entry(
        extraction_dir_,
        event_kind="gap_analysis_end",
        extraction_id=extraction_id,
        estimate={
            "extraction_id": extraction_id,
            "duration_ms": duration_ms,
        },
        timestamp=timestamp,
    )


# ====================================================================
# Stdout summary rendering (AC.GAPAN.7)
# ====================================================================


def render_stdout_summary(inventory: GapInventory) -> str:
    """Render the per-CLI stdout summary (AC.GAPAN.7).

    Lists per-category counts, per-confidence counts, and the top-3
    example gap_ids per category. Builder's-call prose template per
    sub-plan-doc Lens 3.
    """
    s = inventory.summary
    lines: list[str] = []
    lines.append(f"Gap inventory for {inventory.extraction_id}")
    lines.append(f"  Total gaps:       {s.total}")
    lines.append(
        f"    objectives without verified backing: {s.category_a_count}"
    )
    lines.append(
        f"    implementation orphans:              {s.category_b_count}"
    )
    lines.append(f"  By confidence:")
    lines.append(f"    STRONG: {s.strong_count}")
    lines.append(f"    WEAK:   {s.weak_count}")
    if s.total == 0:
        lines.append("  (no gaps surfaced)")
        return "\n".join(lines)
    a_examples = [
        g.gap_id for g in inventory.gaps
        if g.category == "objective_without_verified_backing"
    ][:3]
    b_examples = [
        g.gap_id for g in inventory.gaps
        if g.category == "implementation_orphan"
    ][:3]
    if a_examples:
        lines.append("  Example objectives-without-verified-backing:")
        for gid in a_examples:
            lines.append(f"    - {gid}")
    if b_examples:
        lines.append("  Example implementation-orphans:")
        for gid in b_examples:
            lines.append(f"    - {gid}")
    return "\n".join(lines)
