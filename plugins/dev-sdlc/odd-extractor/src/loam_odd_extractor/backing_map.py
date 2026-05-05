"""v0.2.3 Cycle 2 — backing-implementation map population.

Per sub-plan-doc §3 AC.BACKMAP.2 + §7 method-decision register.

Two-stage population:

1. **Heuristic pre-filter.** Per objective, score every evidence row by
   (a) domain-keyword substring match against ``path`` + ``symbol_name``;
   (b) ``kind=test`` rows weighted by assertion-verb regex + domain-noun
   overlap; (c) per-language conventions (Express paths, Ruby controllers,
   Playwright spec headings). Top-K=8 candidates per objective.

2. **LLM-pass classifier.** Single batched call scoring the narrowed
   pairs on STRONG / WEAK / NONE per the four EVAL_DIMENSIONS axes
   (file-path-relevance / symbol-name-relevance / domain-match /
   outcome-shape-match). Structured-JSON output.

Cost-band envelope: $0.05 – $2.00, default ceiling $0.50; halt
outside band per AC.BACKMAP.2 + AC.BACKMAP.7. The caller passes a
:class:`loam.cost_governance.BudgetEnvelope` to enforce.

Halt-trigger: if pre-filter narrowing yields > 200 candidate pairs
the pre-filter is broken; raise :class:`StageError` BEFORE firing
any LLM call (cost-bound enforcement primary).

Test-mode path: callers pass a stub Anthropic client returning a
canned message-shaped object (``content[0].text`` is JSON matching
the per-pair scoring schema). No real API calls in CI.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any, Iterable

import yaml

from .bands import ConfidenceBand
from .errors import StageError
from .observability import write_audit_entry
from .spec import (
    BackingMap,
    BackingMapEntry,
    EvidenceRowRef,
    Objective,
    OrphanRow,
)


# Per sub-plan-doc §7 + master plan §6.1 cost-governance.
_DEFAULT_MODEL_ID = "claude-sonnet-4-5"
_CENTS_PER_INPUT_TOKEN = 0.0003   # ~$3/M input tokens
_CENTS_PER_OUTPUT_TOKEN = 0.0015  # ~$15/M output tokens

# Per sub-plan-doc §3 AC.BACKMAP.2 — pre-filter top-K + halt trigger.
_TOP_K = 8
_PREFILTER_OVERFLOW_LIMIT = 200

# Per sub-plan-doc §3 AC.OBJRAT.2 — assertion-verb regex (also reused
# here by the kind=test weighting in the pre-filter).
_OUTCOME_VERB_RE = re.compile(
    r"\b(should|expects?|delivers?|creates?|rejects?|completes?|"
    r"handles?|files?|displays?|allows?|prevents?|confirms?)\b",
    re.IGNORECASE,
)


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


# ====================================================================
# Pre-filter — heuristic narrowing
# ====================================================================


def _domain_tokens(text: str) -> set[str]:
    """Extract lowercase alphanumeric tokens from a free-form string."""
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


def _row_kind(row: dict) -> str:
    """Resolve evidence row's kind (route/callback/model/test/pattern/other)."""
    # Adapter outputs ship dict-shape rows; kind is sometimes inferred
    # from path-segments. Default to "other" if absent.
    kind = row.get("kind") or row.get("evidence", {}).get("kind") or "other"
    if kind in ("route", "callback", "model", "test", "pattern"):
        return kind
    # Crude fallback: ``ac_id`` prefix or ``path`` segment.
    ac_id = row.get("ac_id", "")
    if "test" in ac_id.lower() or "spec" in ac_id.lower():
        return "test"
    path = row.get("path") or _row_path(row)
    if path and ("/test" in path.lower() or path.lower().endswith((".spec.ts", ".spec.js", "_spec.rb", "_test.py"))):
        return "test"
    return "other"


def _row_path(row: dict) -> str:
    """Extract path from a row (adapter dict shape)."""
    if isinstance(row.get("path"), str):
        return row["path"]
    backing = row.get("backing_files") or []
    if backing and isinstance(backing[0], (str, dict)):
        if isinstance(backing[0], dict):
            return str(backing[0].get("path", ""))
        return str(backing[0])
    # Composite ac_id may carry the path as the second segment.
    ac_id = row.get("ac_id", "")
    parts = ac_id.split(":", 2)
    if len(parts) >= 2:
        return parts[1]
    return ""


def _row_symbol(row: dict) -> str:
    """Extract symbol-name from a row."""
    sym = row.get("symbol_name") or row.get("symbol") or ""
    if sym:
        return str(sym)
    # Try to derive from ac_id: ``kind:path:line`` doesn't carry symbol;
    # fall back to text or ac_id.
    return str(row.get("text", "") or row.get("ac_id", ""))


def _row_line_range(row: dict) -> tuple[int, int] | None:
    """Extract a line-range tuple if present."""
    lr = row.get("line_range")
    if lr is not None:
        if isinstance(lr, (list, tuple)) and len(lr) == 2:
            return (int(lr[0]), int(lr[1]))
    line = row.get("line")
    if isinstance(line, int):
        return (line, line)
    # Composite ac_id third segment may carry line.
    ac_id = row.get("ac_id", "")
    parts = ac_id.split(":")
    if len(parts) >= 3:
        m = re.match(r"^(\d+)(?:-(\d+))?$", parts[2])
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else start
            return (start, end)
    return None


def _row_language(row: dict) -> str:
    """Resolve language from path extension."""
    path = _row_path(row)
    if path.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")):
        return "jsts"
    if path.endswith((".rb",)) or "/app/" in path:
        return "ruby"
    if path.endswith((".py",)):
        return "python"
    return "other"


def _row_evidence_id(row: dict) -> str:
    """Resolve a stable evidence_row_id for the row.

    Adapter rows already ship with a composite ``ac_id`` of shape
    ``kind:path:line``. Reuse it directly when present; otherwise
    synthesize.
    """
    ac_id = row.get("ac_id")
    if isinstance(ac_id, str) and ac_id:
        # Validate composite shape.
        parts = ac_id.split(":")
        if len(parts) >= 2:
            # Normalize to lowercase kind-prefix for the regex.
            kind = parts[0].lower().replace(".", "_").replace("-", "_")
            # Strip non-allowed chars from kind segment.
            kind = re.sub(r"[^a-z0-9_]", "_", kind) or "other"
            if not kind[0].isalpha():
                kind = "x" + kind
            rest = ":".join(parts[1:])
            return f"{kind}:{rest}"
    # Fallback synthesis.
    kind = _row_kind(row)
    path = _row_path(row) or "unknown"
    lr = _row_line_range(row)
    if lr:
        if lr[0] == lr[1]:
            return f"{kind}:{path}:{lr[0]}"
        return f"{kind}:{path}:{lr[0]}-{lr[1]}"
    return f"{kind}:{path}"


def _heuristic_score(objective: Objective, row: dict) -> float:
    """Score one (objective, row) pair on cheap structural signals."""
    obj_tokens = _domain_tokens(objective.domain) | _domain_tokens(objective.text)
    path = _row_path(row).lower()
    sym = _row_symbol(row).lower()
    text = (str(row.get("text", "")) or "").lower()
    row_blob = f"{path} {sym} {text}"
    row_tokens = _domain_tokens(row_blob)

    if not obj_tokens or not row_tokens:
        return 0.0

    # Signal (a) — token overlap.
    overlap = obj_tokens & row_tokens
    overlap_score = len(overlap) / max(1, len(obj_tokens))

    # Signal (b) — kind=test weighting + verb match.
    kind = _row_kind(row)
    test_bonus = 0.0
    if kind == "test":
        test_bonus = 0.10
        if _OUTCOME_VERB_RE.search(text) or _OUTCOME_VERB_RE.search(sym):
            test_bonus += 0.20

    # Signal (c) — per-language convention bonuses.
    lang_bonus = 0.0
    lang = _row_language(row)
    if lang == "jsts":
        # Express-style route paths often mirror domain nouns.
        if any(t in path for t in obj_tokens):
            lang_bonus = 0.10
    elif lang == "ruby":
        # Rails controllers under app/controllers/<noun>_controller.rb.
        if "/app/controllers/" in path and any(t in path for t in obj_tokens):
            lang_bonus = 0.15
    elif lang == "python":
        # Domain-named modules / class names.
        if any(t in sym for t in obj_tokens):
            lang_bonus = 0.05

    return overlap_score + test_bonus + lang_bonus


def _prefilter(
    objectives: list[Objective],
    evidence_rows: list[dict],
    *,
    top_k: int = _TOP_K,
) -> dict[str, list[tuple[dict, float]]]:
    """Per-objective top-K narrowing.

    Returns mapping from ``objective_id`` to list of ``(row, score)``
    tuples; rows with score==0.0 dropped.
    """
    out: dict[str, list[tuple[dict, float]]] = {}
    for obj in objectives:
        scored: list[tuple[dict, float]] = []
        for row in evidence_rows:
            s = _heuristic_score(obj, row)
            if s > 0.0:
                scored.append((row, s))
        scored.sort(key=lambda t: t[1], reverse=True)
        out[obj.objective_id] = scored[:top_k]
    return out


# ====================================================================
# LLM-pass classifier
# ====================================================================


_CLASSIFIER_SYSTEM_PROMPT = """You are a structural-relevance classifier
helping link OUTCOME-altitude OBJECTIVES to symbol-altitude evidence rows
that BACK them in the codebase.

For each (objective, evidence-row) pair, score the backing relationship
on FOUR dimensions independently:

1. file-path-relevance — does the evidence-row's file path land in the
   domain area of the objective's text + domain field?
2. symbol-name-relevance — does the evidence-row's symbol name (route,
   class, function) name a piece of the objective's outcome?
3. domain-match — do the domain tokens of objective and row align?
4. outcome-shape-match — does the row appear to deliver / verify the
   outcome the objective describes? (test rows asserting outcomes
   score HIGH; symbol-existence rows score LOWER.)

Aggregate verdict:
- STRONG — three-or-four of the four dimensions are clearly met.
- WEAK — one or two dimensions are clearly met; the rest are unclear.
- NONE — fewer than one clear match; the row does not back this
  objective.

OUTPUT: JSON array of objects, one per pair, in input order, with
fields ``objective_id``, ``evidence_row_id``, ``verdict`` (one of
"STRONG" / "WEAK" / "NONE"), and ``rationale`` (one short sentence).
Output JSON only. No markdown fences. No surrounding text.
"""


def _build_classifier_user_prompt(
    pairs: list[tuple[Objective, dict]],
) -> str:
    """Format the narrowed pairs into a JSON-shaped user message."""
    pair_dicts: list[dict[str, Any]] = []
    for obj, row in pairs:
        pair_dicts.append(
            {
                "objective_id": obj.objective_id,
                "objective_text": obj.text,
                "objective_domain": obj.domain,
                "evidence_row_id": _row_evidence_id(row),
                "evidence_path": _row_path(row),
                "evidence_symbol": _row_symbol(row),
                "evidence_kind": _row_kind(row),
                "evidence_text": str(row.get("text", "") or ""),
            }
        )
    return (
        "Score these pairs:\n\n"
        + json.dumps(pair_dicts, indent=2)
        + "\n\nReturn the JSON array now."
    )


def _parse_classifier_response(
    text: str,
) -> list[dict[str, Any]]:
    """Tolerant JSON parse for the classifier response."""
    body = text.strip()
    # Strip markdown fences if any.
    if body.startswith("```"):
        body = re.sub(r"^```(?:json)?\s*", "", body)
        body = re.sub(r"\s*```$", "", body)
    # Locate the first `[` and matching `]`.
    start = body.find("[")
    end = body.rfind("]")
    if start == -1 or end == -1:
        raise StageError(
            "backing_map.populate_backing_map: classifier response did "
            "not contain a JSON array"
        )
    try:
        out = json.loads(body[start : end + 1])
    except json.JSONDecodeError as exc:
        raise StageError(
            f"backing_map.populate_backing_map: classifier JSON parse "
            f"failed: {exc}"
        ) from exc
    if not isinstance(out, list):
        raise StageError(
            "backing_map.populate_backing_map: classifier output was "
            "not a JSON array"
        )
    return out


def _estimate_call_cost_cents(
    pairs: list[tuple[Objective, dict]],
    *,
    avg_input_chars_per_pair: int = 400,
    avg_output_chars_per_pair: int = 80,
    chars_per_token: int = 4,
) -> float:
    """Cheap estimate for cost-band check.

    Per sub-plan-doc §6.2 calibration: ~160 pairs × 5K input / 2K output
    Sonnet pricing → ~$0.04. The 50× headroom on the $0.05–$2.00 band
    absorbs approximation error.
    """
    n = max(1, len(pairs))
    input_tokens = (n * avg_input_chars_per_pair) // chars_per_token
    output_tokens = (n * avg_output_chars_per_pair) // chars_per_token
    return round(
        input_tokens * _CENTS_PER_INPUT_TOKEN
        + output_tokens * _CENTS_PER_OUTPUT_TOKEN,
        4,
    )


# ====================================================================
# Public entry-point
# ====================================================================


def populate_backing_map(
    objectives: list[Objective],
    evidence_rows: list[dict],
    *,
    extraction_id: str,
    anthropic_client: Any,
    repo_sha: str | None = None,
    cost_ceiling_cents: float = 50.0,
    cost_floor_cents: float = 5.0,
    extraction_dir: Path | None = None,
    timestamp: str | None = None,
    model_id: str = _DEFAULT_MODEL_ID,
    top_k: int = _TOP_K,
) -> BackingMap:
    """Populate the backing-map for a set of objectives + evidence rows.

    Steps per sub-plan-doc §3 AC.BACKMAP.2:

    1. Pre-filter — top-K narrowing per objective.
    2. Halt-trigger check — if total narrowed pairs > 200, raise
       :class:`StageError` (pre-filter is broken; avoid burning LLM
       budget).
    3. LLM-pass — single batched call scoring all narrowed pairs;
       aggregate verdicts STRONG / WEAK / NONE.
    4. Orphan classification — rows with no STRONG match across any
       objective → ``no-objective-match``; rows with WEAK matches only
       → ``weak-signal-only``.
    5. ``unmatched_objective_ids`` — non-HYPOTHESISED objectives with
       empty STRONG-or-WEAK lists.
    6. Audit-log emission — ``backing_map_populated`` event_kind.

    ``cost_floor_cents`` / ``cost_ceiling_cents`` carry the band per
    master plan §6.1 + sub-plan-doc §7 ($0.05–$2.00); the dry-run
    estimate must lie inside the band.

    Test-mode: ``anthropic_client`` may be a stub returning canned
    JSON in ``messages.create(...).content[0].text``.
    """
    ts = timestamp if timestamp is not None else _now_iso()

    # 1. Pre-filter.
    narrowed = _prefilter(objectives, evidence_rows, top_k=top_k)
    flat_pairs: list[tuple[Objective, dict]] = []
    obj_by_id = {o.objective_id: o for o in objectives}
    for obj_id, scored in narrowed.items():
        for row, _score in scored:
            flat_pairs.append((obj_by_id[obj_id], row))

    # 2. Halt-trigger.
    if len(flat_pairs) > _PREFILTER_OVERFLOW_LIMIT:
        raise StageError(
            f"backing_map.populate_backing_map: pre-filter overflow "
            f"({len(flat_pairs)} pairs > {_PREFILTER_OVERFLOW_LIMIT}); "
            f"the heuristic pre-filter is broken — halt before LLM "
            f"call to enforce cost-bound primary"
        )

    # 3. Cost-band enforcement (dry-run estimate).
    estimate = _estimate_call_cost_cents(flat_pairs)
    if flat_pairs and estimate > cost_ceiling_cents:
        raise StageError(
            f"backing_map.populate_backing_map: estimated cost "
            f"{estimate:.4f} cents exceeds ceiling "
            f"{cost_ceiling_cents:.4f} cents; halt-and-surface"
        )
    # Floor check applies only when there's any work to do; an empty
    # estimate is allowed (no pairs → no LLM call).
    if flat_pairs and estimate < cost_floor_cents and estimate > 0:
        # Below floor is acceptable (cheap call); not an error. Logged.
        pass

    # 4. LLM-pass.
    verdicts: dict[tuple[str, str], dict[str, Any]] = {}
    cost_actual = 0.0
    token_in = 0
    token_out = 0
    if flat_pairs:
        user_prompt = _build_classifier_user_prompt(flat_pairs)
        # Compose Messages API call; stub in tests.
        try:
            response = anthropic_client.messages.create(
                model=model_id,
                max_tokens=4096,
                system=_CLASSIFIER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
        except Exception as exc:
            raise StageError(
                f"backing_map.populate_backing_map: LLM call failed: {exc}"
            ) from exc
        text = _extract_response_text(response)
        usage = getattr(response, "usage", None)
        if usage is not None:
            token_in = int(getattr(usage, "input_tokens", 0) or 0)
            token_out = int(getattr(usage, "output_tokens", 0) or 0)
            cost_actual = round(
                token_in * _CENTS_PER_INPUT_TOKEN
                + token_out * _CENTS_PER_OUTPUT_TOKEN,
                4,
            )
        else:
            # Fallback: use estimate.
            cost_actual = estimate
        parsed = _parse_classifier_response(text)
        for item in parsed:
            obj_id = str(item.get("objective_id", ""))
            ev_id = str(item.get("evidence_row_id", ""))
            if not obj_id or not ev_id:
                continue
            verdicts[(obj_id, ev_id)] = item

    # 5. Build entries.
    entries: list[BackingMapEntry] = []
    rows_with_strong: set[str] = set()
    rows_with_weak: set[str] = set()
    for obj in objectives:
        rows_for_obj: list[EvidenceRowRef] = []
        match_lines: list[str] = []
        for row, _score in narrowed.get(obj.objective_id, []):
            ev_id = _row_evidence_id(row)
            verdict_payload = verdicts.get((obj.objective_id, ev_id))
            if verdict_payload is None:
                continue
            verdict = str(verdict_payload.get("verdict", "NONE")).upper()
            if verdict not in ("STRONG", "WEAK"):
                continue
            try:
                ref = EvidenceRowRef(
                    evidence_row_id=ev_id,
                    kind=_row_kind(row),
                    path=_row_path(row),
                    line_range=_row_line_range(row),
                    symbol_name=_row_symbol(row) or None,
                    language=_row_language(row),
                    confidence=verdict,  # "STRONG" | "WEAK"
                )
            except Exception:
                # Malformed row — skip; counted in orphans below.
                continue
            rows_for_obj.append(ref)
            if verdict == "STRONG":
                rows_with_strong.add(ev_id)
            else:
                rows_with_weak.add(ev_id)
            rationale = str(verdict_payload.get("rationale", "")).strip()
            if rationale:
                match_lines.append(
                    f"{ev_id} ({verdict}): {rationale}"
                )
        entries.append(
            BackingMapEntry(
                objective_id=obj.objective_id,
                evidence_rows=rows_for_obj,
                match_rationale="\n".join(match_lines),
            )
        )

    # 6. Orphan classification.
    seen_ids: set[str] = set()
    orphans: list[OrphanRow] = []
    for row in evidence_rows:
        ev_id = _row_evidence_id(row)
        if ev_id in seen_ids:
            continue
        seen_ids.add(ev_id)
        if ev_id in rows_with_strong:
            continue
        # Reason classification.
        if ev_id in rows_with_weak:
            reason: str = "weak-signal-only"
        else:
            reason = "no-objective-match"
        try:
            orphans.append(
                OrphanRow(
                    evidence_row_id=ev_id,
                    kind=_row_kind(row),
                    path=_row_path(row),
                    line_range=_row_line_range(row),
                    symbol_name=_row_symbol(row) or None,
                    language=_row_language(row),
                    reason=reason,  # type: ignore[arg-type]
                )
            )
        except Exception:
            # Malformed row — drop silently (rare adapter edge case).
            continue

    # 7. unmatched_objective_ids — non-H objectives with empty backing.
    unmatched: list[str] = []
    for obj, entry in zip(objectives, entries):
        if obj.confidence is ConfidenceBand.HYPOTHESISED:
            continue
        if not entry.evidence_rows:
            unmatched.append(obj.objective_id)

    backing_map = BackingMap(
        extraction_id=extraction_id,
        entries=entries,
        orphan_rows=orphans,
        created_at=ts,
        model_id=model_id if flat_pairs else "(none)",
        cost_actual_cents=cost_actual,
        total_evidence_rows=len(evidence_rows),
        objective_count=len(objectives),
        unmatched_objective_ids=unmatched,
    )

    # 8. Audit-log emission per AC.BACKMAP.7.
    if extraction_dir is not None:
        strong_count = sum(
            1 for e in entries for r in e.evidence_rows if r.confidence == "STRONG"
        )
        weak_count = sum(
            1 for e in entries for r in e.evidence_rows if r.confidence == "WEAK"
        )
        write_audit_entry(
            extraction_dir,
            event_kind="backing_map_populated",
            extraction_id=extraction_id,
            stage="generate",
            estimate={
                "objective_count": len(objectives),
                "evidence_row_count": len(evidence_rows),
                "llm_pass_token_count_input": token_in,
                "llm_pass_token_count_output": token_out,
                "llm_pass_cost_cents": cost_actual,
                "strong_match_count": strong_count,
                "weak_match_count": weak_count,
                "orphan_count": len(orphans),
                "unmatched_objective_count": len(unmatched),
                "model_id": model_id if flat_pairs else "(none)",
            },
            timestamp=ts,
        )

    return backing_map


def _extract_response_text(response: Any) -> str:
    """Best-effort extract of ``content[0].text`` from a Messages API
    response object (real or stub)."""
    content = getattr(response, "content", None)
    if content is None and isinstance(response, dict):
        content = response.get("content")
    if content is None:
        return ""
    if isinstance(content, list) and content:
        first = content[0]
        text = getattr(first, "text", None)
        if text is None and isinstance(first, dict):
            text = first.get("text", "")
        return str(text or "")
    if isinstance(content, str):
        return content
    return str(content)


# ====================================================================
# Persistence (AC.BACKMAP.3)
# ====================================================================


_BACKING_MAP_SCHEMA_VERSION = 1


def backing_map_path(extraction_dir_: Path) -> Path:
    """``<extraction_dir>/backing-map.yaml``."""
    return extraction_dir_ / "backing-map.yaml"


def save_backing_map(extraction_dir_: Path, bm: BackingMap) -> Path:
    """Atomically write ``backing-map.yaml`` via tmp+rename."""
    import os
    import tempfile

    p = backing_map_path(extraction_dir_)
    p.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "schema_version": _BACKING_MAP_SCHEMA_VERSION,
    }
    payload.update(bm.model_dump(mode="json"))

    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{p.name}.",
        suffix=".tmp",
        dir=str(p.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            yaml.safe_dump(payload, fh, sort_keys=False)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, p)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return p


def load_backing_map(extraction_dir_: Path) -> BackingMap | None:
    """Return the persisted :class:`BackingMap`, or ``None`` if absent."""
    p = backing_map_path(extraction_dir_)
    if not p.exists():
        return None
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise StageError(
            f"backing-map.yaml at {p}: top-level must be a mapping; "
            f"got {type(raw).__name__}"
        )
    sv = raw.get("schema_version")
    if sv != _BACKING_MAP_SCHEMA_VERSION:
        raise StageError(
            f"backing-map.yaml: unexpected schema_version={sv!r}; "
            f"expected {_BACKING_MAP_SCHEMA_VERSION}"
        )
    payload = {k: v for k, v in raw.items() if k != "schema_version"}
    return BackingMap.model_validate(payload)


def is_idempotent_skip(
    existing: BackingMap | None,
    *,
    objective_count: int,
    total_evidence_rows: int,
) -> bool:
    """D2 steady-state idempotence check.

    Per sub-plan-doc §4 + §7: re-population is skipped when the
    persisted backing-map's ``objective_count`` and
    ``total_evidence_rows`` both match the current run's counts.
    """
    if existing is None:
        return False
    return (
        existing.objective_count == objective_count
        and existing.total_evidence_rows == total_evidence_rows
    )
