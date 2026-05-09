"""v0.2.4 Cycle 3 — Build-next ranking core.

Per sub-plan-doc §3 AC.BLDNXT.{1..9} + AC.PERSONA-PULL.{1..4}:

- :func:`score_candidates` — pure-function ranking entry point.
  Reads :class:`GapInventory` + :class:`AugmentedObjectiveSet` +
  optional survey-text + optional interview-added objective IDs;
  produces a :class:`BuildNextRecommendation`. Deterministic when
  no LLM-judge is invoked.
- :func:`_score_candidate` — composite-score formula
  (gap-confidence × priority-match × estimated-impact).
- :func:`_compute_priority_match` — signal hierarchy: survey >
  interview > keyword > llm_judge > none.
- :func:`_classify_estimated_impact` — deterministic category-base +
  bonuses (no LLM cost).
- :func:`_assert_informative_not_prescriptive` — denylist enforcer
  (AC.BLDNXT.6).
- :func:`save_recommendation` — atomic dual write
  (build-next.md + build-next.yaml) with idempotent skip-on-no-change.
- :func:`load_recommendation` — round-trip load.
- :func:`render_stdout_summary` — per-CLI stdout summary.

The ranking module **never** instructs ("you should…", "you must…",
"we recommend…"). The persona invokes via the CLI flag, the report
surfaces gaps + matched priorities + factor breakdowns, and the
operator chooses what to build. AC.BLDNXT.6 enforces this with a
module-level denylist + word-boundary check on every emitted text
surface.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable

import yaml

from .errors import OddExtractorError, StageError
from .observability import write_audit_entry
from .spec import (
    AugmentedObjectiveSet,
    BuildNextCandidate,
    BuildNextRecommendation,
    Gap,
    GapInventory,
    Objective,
)


# ====================================================================
# Filenames + schema
# ====================================================================


_BUILD_NEXT_YAML_FILENAME = "build-next.yaml"
_BUILD_NEXT_MD_FILENAME = "build-next.md"
_BUILD_NEXT_SCHEMA_VERSION = 1

# Default ranking parameters (sub-plan-doc §14).
DEFAULT_LIMIT = 10
DEFAULT_LLM_JUDGE_BUDGET_CENTS = 10  # $0.10
LLM_JUDGE_HALT_LOWER_CENTS = 2       # $0.02 lower halt band
LLM_JUDGE_HALT_UPPER_CENTS = 30      # $0.30 upper halt band
LLM_JUDGE_INVOCATION_CAP = 5         # AC.BLDNXT.3


# ====================================================================
# Persistence path helpers
# ====================================================================


def build_next_yaml_path(extraction_dir_: Path) -> Path:
    """``<extraction_dir>/build-next.yaml``."""
    return extraction_dir_ / _BUILD_NEXT_YAML_FILENAME


def build_next_md_path(extraction_dir_: Path) -> Path:
    """``<extraction_dir>/build-next.md``."""
    return extraction_dir_ / _BUILD_NEXT_MD_FILENAME


# ====================================================================
# Informative-not-prescriptive denylist (AC.BLDNXT.6)
# ====================================================================


# Module-level seed — sub-plan-doc §14 method-decision register.
# Word-boundary case-insensitive. Phrases ranked by frequency LLMs
# emit them in rationale prose. Opt-in LLM-judge pass behind
# LOAM_BUILD_NEXT_LLM_DENYLIST=1 catches novel phrasings (default
# off; cost-bounded; v0.2.5 calibration may flip default).
_PRESCRIPTIVE_DENYLIST = (
    "you should",
    "you must",
    "we recommend",
    "the next step is",
    "i suggest",
    "you need to",
    "must implement",
    "should implement",
    "build this next",
    "do this first",
)

# Compile once — case-insensitive, word-boundary on edges. ``re.escape``
# keeps multi-word phrases robust; the trailing/leading boundaries
# match either start/end of string or a non-word character.
_DENYLIST_RE = re.compile(
    r"(?<![A-Za-z])(?:" + "|".join(re.escape(p) for p in _PRESCRIPTIVE_DENYLIST) + r")(?![A-Za-z])",
    re.IGNORECASE,
)


def _assert_informative_not_prescriptive(text: str, *, surface: str) -> None:
    """Raise :class:`OddExtractorError` on prescriptive-phrase hit.

    Per AC.BLDNXT.6 — the rationale + stdout + ``build-next.md`` MUST
    avoid imperative-mood phrasing. ``surface`` is included in the
    error message for triage (which output surface tripped which
    phrase).
    """
    m = _DENYLIST_RE.search(text)
    if m is None:
        return
    raise OddExtractorError(
        f"build_next: prescriptive phrase {m.group()!r} found in "
        f"{surface!r} surface (informative-not-prescriptive contract "
        f"per AC.BLDNXT.6 violated). Rephrase as a finding, not a "
        f"directive."
    )


# ====================================================================
# Estimated-impact factor (AC.BLDNXT.2; deterministic, no LLM)
# ====================================================================


# Category bases — sub-plan-doc §14.
_CATEGORY_A_IMPACT_BASE = 0.8
_CATEGORY_B_IMPACT_BASE = 0.5
_INTERVIEW_BONUS = 0.1   # added when source objective.source == "added_by_user"
_CLUSTER_BONUS = 0.1     # added when category-b orphan cluster size >= 3
_CLUSTER_THRESHOLD = 3


def _orphan_cluster_size(gap: Gap) -> int:
    """Count of evidence_rows in this orphan-gap's cluster."""
    return len(gap.evidence_rows)


def _classify_estimated_impact(
    gap: Gap,
    *,
    objective: Objective | None,
) -> float:
    """Deterministic estimated-impact factor per AC.BLDNXT.2.

    Category-a base 0.8 + interview-bonus 0.1 if mapped objective's
    source is ``added_by_user``. Category-b base 0.5 + cluster-bonus
    0.1 when orphan cluster size ≥3. Result clamped to [0.0, 1.0].
    """
    if gap.category == "objective_without_verified_backing":
        impact = _CATEGORY_A_IMPACT_BASE
        if objective is not None and objective.source == "added_by_user":
            impact += _INTERVIEW_BONUS
    else:  # implementation_orphan
        impact = _CATEGORY_B_IMPACT_BASE
        if _orphan_cluster_size(gap) >= _CLUSTER_THRESHOLD:
            impact += _CLUSTER_BONUS
    # Clamp.
    return max(0.0, min(1.0, impact))


# ====================================================================
# Gap-confidence factor (AC.BLDNXT.2)
# ====================================================================


def _gap_confidence_factor(gap: Gap) -> float:
    """STRONG=1.0; WEAK=0.5 per AC.BLDNXT.2."""
    if gap.confidence == "STRONG":
        return 1.0
    if gap.confidence == "WEAK":
        return 0.5
    raise AssertionError(  # pragma: no cover (Pydantic Literal blocks)
        f"_gap_confidence_factor: unexpected confidence={gap.confidence!r}"
    )


# ====================================================================
# Priority-match heuristic + LLM-judge for borderline (AC.BLDNXT.3)
# ====================================================================


# Tokenization pattern — alphanumerics + hyphens; lowercase for
# matching. ``-`` preserved so multi-word concepts like "audit-trail"
# count as one token.
_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9-]*", re.IGNORECASE)
# Stopwords intentionally trimmed — gap-rationale text is short and
# already-keyword-dense; aggressive stoplisting drops too much signal.
_STOPWORDS = frozenset({
    "the", "and", "for", "with", "from", "this", "that", "have",
    "has", "are", "was", "were", "but", "not", "all", "any", "any",
    "via", "into", "when", "their", "such", "user", "users",
    "objective", "objectives", "gap", "gaps", "evidence", "kinds",
    "rows", "row", "category", "weak", "strong", "src", "tests",
})


def _tokenize(text: str) -> set[str]:
    """Lowercase token set; stopwords removed; min length 3."""
    if not text:
        return set()
    out: set[str] = set()
    for m in _TOKEN_RE.finditer(text):
        tok = m.group().lower()
        if len(tok) < 3:
            continue
        if tok in _STOPWORDS:
            continue
        out.add(tok)
    return out


def _extract_survey_priority_keywords(survey_text: str | None) -> set[str]:
    """Pull priority-keywords from survey text.

    Survey shape per AC.ONBOARD.15: H2-section markdown; Q11/Q12
    typically carry "what should the system always do?" / "what should
    it never do?" priorities. Best-effort: tokenize the entire survey
    text. The signal-strength check downstream uses overlap counts;
    Q11/Q12 specificity is implicit (their tokens dominate priorities).
    """
    if not survey_text:
        return set()
    return _tokenize(survey_text)


def _read_interview_added_objective_ids(
    audit_log_dir_: Path,
) -> set[str]:
    """Walk audit-log dir for ``objective_added_by_user`` entries.

    Returns the set of ``estimate.objective_id`` values from any
    audit entry whose ``event_kind`` is ``objective_added_by_user``.
    Best-effort — missing entries / parse failures yield empty set.
    """
    if not audit_log_dir_.exists() or not audit_log_dir_.is_dir():
        return set()
    out: set[str] = set()
    for entry_path in sorted(audit_log_dir_.iterdir()):
        if not entry_path.is_file() or not entry_path.suffix == ".yaml":
            continue
        try:
            data = yaml.safe_load(entry_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if data.get("event_kind") != "objective_added_by_user":
            continue
        est = data.get("estimate") or {}
        if not isinstance(est, dict):
            continue
        oid = est.get("objective_id")
        if isinstance(oid, str) and oid:
            out.add(oid)
    return out


def _gap_keyword_tokens(gap: Gap) -> set[str]:
    """Tokens from the gap rationale + objective_id slug."""
    tokens = _tokenize(gap.rationale)
    if gap.objective_id:
        # Slug-tokens of the objective_id (split on punct).
        tokens |= _tokenize(gap.objective_id.replace(".", " "))
    return tokens


def _objective_text_tokens(obj: Objective | None) -> set[str]:
    if obj is None:
        return set()
    return _tokenize(obj.text)


def _compute_priority_match_deterministic(
    gap: Gap,
    *,
    objective: Objective | None,
    survey_keywords: set[str],
    interview_added_objective_ids: set[str],
) -> tuple[float | None, str]:
    """Deterministic part of the priority-match signal.

    Per sub-plan-doc §3 AC.BLDNXT.3 signal hierarchy:

    1. ``survey`` — survey keyword overlap with gap-rationale tokens.
       ≥2 distinct overlaps → factor 1.0; ≥1 → factor 0.5.
    2. ``interview`` — gap touches an interview-added objective →
       factor 1.0.
    3. ``keyword`` — gap-rationale tokens overlap objective-text
       tokens ≥3 → factor 0.5.
    4. ``none`` — when none of the above and no survey context.

    Returns ``(factor, signal)``. Factor is ``None`` when the survey
    is absent (degenerate); the caller substitutes 1.0 in the
    composite formula AND surfaces ``signal="none"`` per AC.BLDNXT.3.

    Borderline gating for the LLM-judge tier is delegated to the
    public :func:`_compute_priority_match` wrapper, which inspects
    the survey-overlap count to decide whether to invoke the judge.
    """
    gap_tokens = _gap_keyword_tokens(gap)

    # Survey signal — when survey present.
    if survey_keywords:
        overlap = gap_tokens & survey_keywords
        if len(overlap) >= 2:
            return 1.0, "survey"
        if len(overlap) >= 1:
            return 0.5, "survey"
        # Survey present but zero overlap → fall through to interview/keyword.

    # Interview signal — when this gap maps to an objective the user
    # explicitly added during the completeness interview.
    if (
        gap.objective_id is not None
        and gap.objective_id in interview_added_objective_ids
    ):
        return 1.0, "interview"

    # Keyword signal — overlap with the objective's own text.
    obj_tokens = _objective_text_tokens(objective)
    if obj_tokens and len(gap_tokens & obj_tokens) >= 3:
        return 0.5, "keyword"

    # No deterministic signal.
    if not survey_keywords:
        # Survey absent → degenerate path. Caller substitutes 1.0
        # priority_match_factor in composite.
        return None, "none"
    return 0.0, "none"


def _is_borderline_for_llm_judge(
    gap: Gap,
    *,
    survey_keywords: set[str],
) -> bool:
    """Heuristic: should the LLM-judge tier-break this gap?

    Borderline = survey present AND survey-overlap is exactly 1
    distinct token. Below 1 = no signal (none); ≥2 = clear-survey
    (already 1.0). The LLM-judge consumes only the borderline middle
    band; total invocation cap is enforced upstream.
    """
    if not survey_keywords:
        return False
    overlap = _gap_keyword_tokens(gap) & survey_keywords
    return len(overlap) == 1


def _llm_judge_priority_match(
    gap: Gap,
    *,
    objective: Objective | None,
    survey_text: str,
    anthropic_client: Any,
    model_id: str = "claude-sonnet-4-5",
    max_tokens: int = 400,
) -> tuple[float, str]:
    """LLM-as-judge priority-match for borderline gaps (AC.BLDNXT.3).

    Returns ``(factor, rationale_phrase)``. Factor ∈ {0.0, 0.5, 1.0}
    per the structured-JSON contract. Lean grounding inject keeps the
    judge altitude-aware; temperature=0 for determinism on a per-model
    basis.

    Tests inject ``anthropic_client=<stub>`` returning a canned
    Message-shape (``content[0].text`` is JSON ``{factor, rationale_phrase}``).
    No real API in CI.
    """
    if anthropic_client is None:
        raise StageError(
            "_llm_judge_priority_match: anthropic_client is required."
        )

    system_prompt = (
        "You are a priority-match judge for an ODD reverse-engineering "
        "build-next ranking. Given (a) a gap finding from a target "
        "codebase analysis and (b) the operator's stated priorities "
        "from an onboarding survey, decide how strongly the gap "
        "matches the priorities.\n\n"
        "Output a SINGLE JSON object with two keys:\n"
        "  - factor: 0.0 (no match) | 0.5 (partial / inferred match) | "
        "1.0 (strong match)\n"
        "  - rationale_phrase: <30-80 chars naming WHICH priority "
        "intersects WHICH gap concept>\n\n"
        "DO NOT use prescriptive phrasing in the rationale_phrase — "
        "do NOT say 'you should', 'you must', 'we recommend', or "
        "similar. Phrase as a finding ('this gap aligns with priority "
        "X', 'priority Y intersects gap Z').\n\n"
        "Output ONLY the JSON; no surrounding prose, no markdown fence."
    )
    user_prompt = (
        "# Gap finding\n"
        f"- gap_id: {gap.gap_id}\n"
        f"- category: {gap.category}\n"
        f"- confidence: {gap.confidence}\n"
        f"- rationale: {gap.rationale}\n"
    )
    if objective is not None:
        user_prompt += (
            f"- objective_id: {objective.objective_id}\n"
            f"- objective_text: {objective.text}\n"
            f"- objective_domain: {objective.domain}\n"
        )
    user_prompt += "\n# Operator priorities (survey)\n"
    user_prompt += "```\n"
    user_prompt += survey_text[:4000]
    user_prompt += "\n```\n"
    user_prompt += (
        "\nDecide factor + rationale_phrase. Output JSON only."
    )

    try:
        response = anthropic_client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            temperature=0,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_prompt}],
        )
    except TypeError:
        response = anthropic_client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

    raw_text = ""
    try:
        block = response.content[0]
        raw_text = getattr(block, "text", None) or block["text"]
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise StageError(
            f"_llm_judge_priority_match: response shape lacks "
            f".content[0].text ({exc})"
        ) from exc

    # Strip code fence if present.
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise StageError(
            f"_llm_judge_priority_match: response is not valid JSON: "
            f"{exc}; raw[:200]={cleaned[:200]!r}"
        ) from exc
    if not isinstance(data, dict):
        raise StageError(
            "_llm_judge_priority_match: response root must be JSON object"
        )
    factor = data.get("factor")
    rationale_phrase = data.get("rationale_phrase") or ""
    if factor not in (0.0, 0.5, 1.0):
        # Coerce numeric near-values; reject otherwise.
        try:
            f = float(factor)
        except (TypeError, ValueError):
            raise StageError(
                f"_llm_judge_priority_match: factor must be 0.0/0.5/1.0; "
                f"got {factor!r}"
            )
        # Bucket to nearest valid factor.
        if f <= 0.25:
            factor = 0.0
        elif f <= 0.75:
            factor = 0.5
        else:
            factor = 1.0
    if not isinstance(rationale_phrase, str):
        rationale_phrase = str(rationale_phrase)
    # Denylist guard on the LLM-emitted phrase.
    _assert_informative_not_prescriptive(
        rationale_phrase, surface="llm_judge.rationale_phrase"
    )
    return float(factor), rationale_phrase


# ====================================================================
# Composite + tie-break (AC.BLDNXT.2)
# ====================================================================


def _score_candidate(
    gap: Gap,
    *,
    objective: Objective | None,
    priority_match_factor: float | None,
) -> tuple[float, float, float]:
    """Return ``(composite_score, gap_confidence_factor, estimated_impact_factor)``.

    Composite formula per AC.BLDNXT.2:

        composite = gap_confidence × priority_match × estimated_impact

    With ``priority_match=1.0`` substituted when None
    (degenerate-survey path). All factors clamped to [0.0, 1.0]; the
    product is therefore guaranteed ∈ [0.0, 1.0].
    """
    gc = _gap_confidence_factor(gap)
    impact = _classify_estimated_impact(gap, objective=objective)
    pm = priority_match_factor if priority_match_factor is not None else 1.0
    composite = gc * pm * impact
    # Clamp residual floating-point overshoot.
    composite = max(0.0, min(1.0, composite))
    return composite, gc, impact


_CATEGORY_RANK = {
    "objective_without_verified_backing": 0,
    "implementation_orphan": 1,
}
_CONFIDENCE_RANK = {"STRONG": 0, "WEAK": 1}


def _load_bearing_signal(
    gap: Gap, *, objective: Objective | None
) -> tuple[int, int]:
    """Compute a 2-tuple load-bearing signal for tie-breaking.

    Per AC.V041.3 (build-next tie-breaker beyond alphabetical):

    1. **Orphan cluster size** (``len(gap.evidence_rows)``) — for
       category-b ``implementation_orphan`` gaps, more unclaimed
       evidence rows means more load-bearing. Zero for typical
       category-a gaps where evidence_rows is empty.
    2. **Objective text length** — for category-a
       ``objective_without_verified_backing`` gaps, the originating
       objective's text length is a deterministic load-bearing
       proxy (longer = more specific/load-bearing). Zero when
       objective is None (orphan with no resolved objective).

    Both factors are negated at the call site so larger values rank
    *first* in lexicographic min-sort. Composes lexicographically:
    cluster-size first (discriminates category-b ties), then
    objective-text-length (discriminates category-a ties), then the
    existing alphabetical fallback (still last).

    The empirical motivation is the v0.4.0 C4 ProgramBench Task 2
    failure: ``error-handling`` vs ``formatting`` candidates tied
    on composite_score AND category AND confidence; alphabetical
    selected the less-load-bearing ``error-handling``. With the
    objective-text-length signal, ``formatting`` (the longer, more
    specific objective text) wins.
    """
    cluster_size = len(gap.evidence_rows) if gap.evidence_rows else 0
    obj_text_len = (
        len(objective.text) if objective is not None and objective.text else 0
    )
    return (cluster_size, obj_text_len)


def _tiebreak_key(
    c: BuildNextCandidate,
    gap: Gap,
    *,
    objective: Objective | None = None,
) -> tuple:
    """Tie-break key per AC.BLDNXT.2 + AC.V041.3.

    Hierarchy (negated factors sort larger first under min-sort):

    1. ``-composite_score`` — primary ranking signal (AC.BLDNXT.2).
    2. ``_CATEGORY_RANK[category]`` — category-a > category-b.
    3. ``_CONFIDENCE_RANK[gap.confidence]`` — STRONG > WEAK.
    4. **``-orphan_cluster_size``** — more evidence rows = more
       load-bearing (AC.V041.3 sub-fix #3 first signal).
    5. **``-objective_text_length``** — longer objective text = more
       specific/load-bearing (AC.V041.3 sub-fix #3 second signal).
    6. ``c.gap_id`` — lex alphabetical (final fallback only).

    Steps 4+5 are NEW at v0.4.1 per AC.V041.3. They sit between the
    existing v0.2.4 C3 hierarchy (steps 1-3) and the alphabetical
    final fallback (step 6) so:

    - When all of composite_score / category / confidence tie, the
      load-bearing signals discriminate before alphabetical fires.
    - When even those signals tie (extremely unlikely), alphabetical
      remains the deterministic final fallback.

    Per ODD §2.5 method-altitude: the method (cluster-size,
    text-length) is named in the docstring + the AC text but the AC
    contracts the OUTCOME (a non-alphabetical signal beats
    alphabetical when the other dimensions tie), not the specific
    factor combination.
    """
    cluster_size, obj_text_len = _load_bearing_signal(
        gap, objective=objective
    )
    return (
        -c.composite_score,
        _CATEGORY_RANK[c.category],
        _CONFIDENCE_RANK[gap.confidence],
        -cluster_size,
        -obj_text_len,
        c.gap_id,
    )


# ====================================================================
# Rationale rendering (AC.BLDNXT.6 informative-not-prescriptive)
# ====================================================================


def _render_rationale(
    gap: Gap,
    *,
    objective: Objective | None,
    priority_match_factor: float | None,
    priority_match_signal: str,
    estimated_impact_factor: float,
    llm_judge_phrase: str | None,
) -> str:
    """2-4 sentence rationale per Pin 2 (AC.BLDNXT.6).

    Phrases findings as observations; never imperatives. Includes the
    HYPOTHESISED prefix per AC.PERSONA-PULL.3 when the source objective
    is HYPOTHESISED.
    """
    parts: list[str] = []

    # AC.PERSONA-PULL.3 — HYPOTHESISED prefix.
    if (
        objective is not None
        and objective.confidence.value == "HYPOTHESISED"
    ):
        parts.append(
            "Backing-confidence reflects HYPOTHESISED band — "
            "ratify via interview before treating as final priority "
            "signal."
        )

    # Sentence 1: name the gap finding.
    if gap.category == "objective_without_verified_backing":
        if objective is not None:
            parts.append(
                f"This gap surfaces {objective.objective_id} ("
                f"{objective.confidence.value}, domain "
                f"{objective.domain!r}); backing-confidence is "
                f"{gap.confidence}."
            )
        else:
            parts.append(
                f"This gap surfaces an objective without verified "
                f"backing; backing-confidence is {gap.confidence}."
            )
    else:  # implementation_orphan
        cluster_size = _orphan_cluster_size(gap)
        parts.append(
            f"This gap surfaces an implementation orphan cluster "
            f"({cluster_size} unclaimed evidence row(s)); "
            f"backing-confidence is {gap.confidence}."
        )

    # Sentence 2: priority-match signal.
    if priority_match_signal == "survey":
        parts.append(
            "This gap matches your stated survey priorities — "
            "survey-keyword overlap is the matching signal."
        )
    elif priority_match_signal == "interview":
        parts.append(
            "This gap maps to an objective you added during the "
            "completeness interview — interview source is the matching "
            "signal."
        )
    elif priority_match_signal == "keyword":
        parts.append(
            "This gap shares vocabulary with the underlying objective "
            "— keyword overlap is the matching signal."
        )
    elif priority_match_signal == "llm_judge":
        # Use the judge's rationale phrase (already denylist-checked).
        if llm_judge_phrase:
            parts.append(
                f"Priority-match (LLM-judge): {llm_judge_phrase}."
            )
        else:
            parts.append(
                "Priority-match assessed by LLM-judge for a borderline "
                "survey-keyword overlap."
            )
    else:
        # signal == "none"
        if priority_match_factor is None:
            parts.append(
                "No survey context available; priority-match degenerate "
                "to none. Ranking falls back to gap-confidence × "
                "estimated-impact."
            )
        else:
            parts.append(
                "No clear priority-match found; this gap surfaces from "
                "structural analysis alone."
            )

    # Sentence 3: estimated-impact note.
    impact_note = (
        f"Estimated-impact factor is {estimated_impact_factor:.2f} "
    )
    if gap.category == "objective_without_verified_backing":
        impact_note += "(category-a base 0.80"
        if (
            objective is not None
            and objective.source == "added_by_user"
        ):
            impact_note += " + interview-bonus 0.10"
        impact_note += ")."
    else:
        impact_note += "(category-b base 0.50"
        if _orphan_cluster_size(gap) >= _CLUSTER_THRESHOLD:
            impact_note += " + cluster-bonus 0.10"
        impact_note += ")."
    parts.append(impact_note)

    rationale = " ".join(parts)
    # Defensive denylist check on the assembled rationale.
    _assert_informative_not_prescriptive(rationale, surface="rationale")
    return rationale


# ====================================================================
# Public scoring entry point (AC.BLDNXT.{2,3,4,5})
# ====================================================================


def score_candidates(
    *,
    gap_inventory: GapInventory,
    augmented_objectives: AugmentedObjectiveSet,
    survey_text: str | None,
    extraction_id: str,
    audit_path: str,
    limit: int = DEFAULT_LIMIT,
    interview_added_objective_ids: Iterable[str] | None = None,
    anthropic_client: Any | None = None,
    llm_judge_invocation_cap: int = LLM_JUDGE_INVOCATION_CAP,
    analyzed_at: str | None = None,
) -> BuildNextRecommendation:
    """Produce a :class:`BuildNextRecommendation` from typed substrate.

    Per sub-plan-doc §3 AC.BLDNXT.{2,3,4,5}:

    - Pure function modulo optional LLM-judge call (anthropic_client
      injected by caller; tests pass a stub).
    - Deterministic when no LLM-judge is invoked (survey present with
      ≥2 overlap or absent, no borderline cases).
    - Halt-and-surface when survey present at either canonical path
      AND every candidate's deterministic signal is ``none`` AND no
      LLM-judge tier-breaker is configured (signal-detection broken).
    - Result is sorted by composite-score desc + tie-break.
    - ``truncated_count`` reports underlying-list size minus
      ``limit``.

    Caller responsibilities:

    - Resolve survey-text from disk (lazy-import via
      ``multi_source._read_user_survey``).
    - Resolve ``interview_added_objective_ids`` from the audit-log
      (use :func:`_read_interview_added_objective_ids`).
    - Pass ``anthropic_client=None`` to disable the LLM-judge tier
      (deterministic-only ranking).
    """
    if analyzed_at is None:
        analyzed_at = _dt.datetime.now(_dt.timezone.utc).isoformat()

    if limit < 1:
        raise OddExtractorError(
            f"score_candidates: limit must be >= 1; got {limit}"
        )

    aug_by_id = {
        o.objective_id: o for o in augmented_objectives.objectives
    }

    survey_keywords = _extract_survey_priority_keywords(survey_text)
    survey_present = bool(survey_keywords)
    interview_ids = (
        set(interview_added_objective_ids)
        if interview_added_objective_ids is not None
        else set()
    )

    # Degenerate flag: survey absent AND no interview-priority signal.
    degenerate_survey = (not survey_present) and (not interview_ids)

    candidates: list[BuildNextCandidate] = []
    # AC.V041.3: pairs carry the resolved Objective for the
    # _tiebreak_key load-bearing signal (objective text length).
    candidate_gap_pairs: list[
        tuple[BuildNextCandidate, Gap, Objective | None]
    ] = []
    llm_judge_invocations = 0

    for gap in gap_inventory.gaps:
        objective = (
            aug_by_id.get(gap.objective_id)
            if gap.objective_id is not None
            else None
        )

        # Priority-match signal (deterministic tier).
        det_factor, det_signal = _compute_priority_match_deterministic(
            gap,
            objective=objective,
            survey_keywords=survey_keywords,
            interview_added_objective_ids=interview_ids,
        )

        signal = det_signal
        priority_match_factor = det_factor
        llm_judge_phrase: str | None = None

        # LLM-judge tier — borderline + budget remaining.
        if (
            anthropic_client is not None
            and survey_present
            and det_signal == "survey"
            and det_factor == 0.5
            and llm_judge_invocations < llm_judge_invocation_cap
            and _is_borderline_for_llm_judge(
                gap, survey_keywords=survey_keywords
            )
        ):
            try:
                judge_factor, judge_phrase = _llm_judge_priority_match(
                    gap,
                    objective=objective,
                    survey_text=survey_text or "",
                    anthropic_client=anthropic_client,
                )
                signal = "llm_judge"
                priority_match_factor = judge_factor
                llm_judge_phrase = judge_phrase
                llm_judge_invocations += 1
            except (StageError, OddExtractorError):
                # Fall back to deterministic factor if judge fails;
                # surface invocation count regardless.
                pass

        # Convert None → degenerate-path None (preserved on candidate).
        # Deterministic path emits None signal=none when survey absent.
        composite, gc, impact = _score_candidate(
            gap,
            objective=objective,
            priority_match_factor=priority_match_factor,
        )

        rationale = _render_rationale(
            gap,
            objective=objective,
            priority_match_factor=priority_match_factor,
            priority_match_signal=signal,
            estimated_impact_factor=impact,
            llm_judge_phrase=llm_judge_phrase,
        )

        candidate = BuildNextCandidate(
            gap_id=gap.gap_id,
            composite_score=round(composite, 6),
            gap_confidence_factor=round(gc, 6),
            priority_match_factor=(
                round(priority_match_factor, 6)
                if priority_match_factor is not None
                else None
            ),
            estimated_impact_factor=round(impact, 6),
            priority_match_signal=signal,  # type: ignore[arg-type]
            rationale=rationale,
            category=gap.category,
            objective_id=gap.objective_id,
        )
        candidates.append(candidate)
        candidate_gap_pairs.append((candidate, gap, objective))

    # Halt-and-surface check: survey present AND every candidate's
    # signal collapsed to "none" AND no LLM-judge tier-breaker active.
    # This indicates broken signal detection per AC.BLDNXT.3 halt
    # trigger.
    if (
        survey_present
        and candidates
        and all(c.priority_match_signal == "none" for c in candidates)
    ):
        raise OddExtractorError(
            "build_next: signal-detection collapse — survey is present "
            f"but every candidate's priority_match_signal is 'none' "
            f"({len(candidates)} candidates). Halt-and-surface per "
            f"AC.BLDNXT.3 — signal-detection appears broken."
        )

    # Sort + tie-break (AC.V041.3 — objective passed for load-bearing
    # signal).
    candidate_gap_pairs.sort(
        key=lambda triple: _tiebreak_key(
            triple[0], triple[1], objective=triple[2]
        )
    )
    sorted_candidates = [c for c, _g, _o in candidate_gap_pairs]

    underlying_count = len(sorted_candidates)
    if underlying_count > limit:
        kept = sorted_candidates[:limit]
        truncated_count = underlying_count - limit
    else:
        kept = sorted_candidates
        truncated_count = 0

    return BuildNextRecommendation(
        schema_version=1,
        extraction_id=extraction_id,
        analyzed_at=analyzed_at,
        audit_path=audit_path,
        degenerate_survey=degenerate_survey,
        candidates=kept,
        truncated_count=truncated_count,
        llm_judge_invocations=llm_judge_invocations,
    )


# ====================================================================
# Markdown renderer (AC.BLDNXT.5)
# ====================================================================


_MD_CLOSING_LINE = (
    "Persona invokes via `loam odd-extract <repo> --build-next` on "
    "user-question-trigger such as 'what should I build next?'. "
    "Recommendations are informative findings — not directives."
)


def _render_markdown(
    rec: BuildNextRecommendation,
    *,
    inventory_summary_text: str | None = None,
) -> str:
    """Render the human-readable ``build-next.md`` text.

    Per AC.BLDNXT.5 + AC.PERSONA-PULL.2: header (analyzed_at + degenerate
    flag + summary), per-candidate ``### Rank K — <gap_id>`` block with
    score + factor breakdown + rationale, closing pull-point line.
    """
    lines: list[str] = []
    lines.append(f"# Build-next recommendation for `{rec.extraction_id}`")
    lines.append("")
    lines.append(f"- analyzed_at: `{rec.analyzed_at}`")
    lines.append(f"- candidate_count: {len(rec.candidates)}")
    if rec.truncated_count:
        lines.append(
            f"- truncated_count: {rec.truncated_count} "
            f"(underlying list exceeded `--limit`)"
        )
    lines.append(f"- llm_judge_invocations: {rec.llm_judge_invocations}")
    if rec.degenerate_survey:
        lines.append(
            "- **degenerate_survey: true** — no survey context found "
            "at either canonical path "
            "(`<repo>/.loam/onboarding-survey.md` or "
            "`~/loam-onboarding-survey.md`) and no interview-added "
            "objectives. Priority-match falls back to gap-confidence × "
            "estimated-impact."
        )
    else:
        lines.append("- degenerate_survey: false")
    lines.append("")

    if inventory_summary_text:
        lines.append("## Source gap-inventory summary")
        lines.append("")
        for sl in inventory_summary_text.splitlines():
            lines.append(sl)
        lines.append("")

    if not rec.candidates:
        lines.append("## Ranked candidates")
        lines.append("")
        lines.append("(no candidates surfaced; gap inventory is empty)")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(_MD_CLOSING_LINE)
        return "\n".join(lines) + "\n"

    lines.append("## Ranked candidates")
    lines.append("")
    for k, c in enumerate(rec.candidates, start=1):
        lines.append(f"### Rank {k} — `{c.gap_id}`")
        lines.append("")
        lines.append(f"- composite_score: **{c.composite_score:.4f}**")
        lines.append(
            f"- gap_confidence_factor: {c.gap_confidence_factor:.2f}"
        )
        if c.priority_match_factor is None:
            lines.append(
                "- priority_match_factor: _none_ "
                "(degenerate-survey path; substituted as 1.0 in composite)"
            )
        else:
            lines.append(
                f"- priority_match_factor: {c.priority_match_factor:.2f}"
            )
        lines.append(
            f"- estimated_impact_factor: {c.estimated_impact_factor:.2f}"
        )
        lines.append(
            f"- priority_match_signal: `{c.priority_match_signal}`"
        )
        lines.append(f"- category: `{c.category}`")
        if c.objective_id:
            lines.append(f"- objective_id: `{c.objective_id}`")
        lines.append("")
        lines.append(c.rationale)
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(_MD_CLOSING_LINE)
    return "\n".join(lines) + "\n"


# ====================================================================
# Persistence (AC.BLDNXT.5 atomic dual-write + AC.BLDNXT.4 idempotence)
# ====================================================================


def _content_hash_payload(rec: BuildNextRecommendation) -> dict[str, Any]:
    """Subset used for idempotence hash (excludes ``analyzed_at``)."""
    return rec.model_dump(
        mode="json",
        exclude={"analyzed_at"},
        exclude_none=True,
    )


def _atomic_write(path: Path, content: str | bytes) -> None:
    """Atomic tmp+rename write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    try:
        if isinstance(content, str):
            mode = "w"
            data = content
        else:
            mode = "wb"
            data = content
        with os.fdopen(fd, mode, encoding="utf-8" if mode == "w" else None) as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_path, str(path))
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def save_recommendation(
    rec: BuildNextRecommendation,
    extraction_dir_: Path,
    *,
    inventory_summary_text: str | None = None,
    skip_on_no_change: bool = True,
) -> tuple[Path, Path, bool]:
    """Persist build-next.yaml + build-next.md atomically.

    Per AC.BLDNXT.5 + AC.BLDNXT.4:

    - Both surfaces written atomically; failure leaves no partial.
    - Schema-versioned at v1.
    - Idempotent on no-change: existing yaml content-hash sans
      ``analyzed_at`` matches → skip both writes; existing files
      untouched.

    Returns ``(yaml_path, md_path, wrote)``.
    """
    yaml_p = build_next_yaml_path(extraction_dir_)
    md_p = build_next_md_path(extraction_dir_)

    if skip_on_no_change and yaml_p.exists():
        try:
            existing = load_recommendation(extraction_dir_)
        except Exception:
            existing = None
        if existing is not None:
            new_hash = _content_hash_payload(rec)
            old_hash = _content_hash_payload(existing)
            if new_hash == old_hash:
                return yaml_p, md_p, False

    payload: dict[str, Any] = {"schema_version": _BUILD_NEXT_SCHEMA_VERSION}
    payload.update(rec.model_dump(mode="json", exclude_none=False))

    yaml_text = yaml.safe_dump(payload, sort_keys=False)
    md_text = _render_markdown(
        rec, inventory_summary_text=inventory_summary_text
    )
    # Denylist guard on the assembled markdown.
    _assert_informative_not_prescriptive(md_text, surface="build-next.md")

    _atomic_write(yaml_p, yaml_text)
    _atomic_write(md_p, md_text)
    return yaml_p, md_p, True


def load_recommendation(
    extraction_dir_: Path,
) -> BuildNextRecommendation | None:
    """Round-trip-load build-next.yaml, or ``None`` if absent."""
    p = build_next_yaml_path(extraction_dir_)
    if not p.exists():
        return None
    raw = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(
            f"build-next.yaml at {p}: top-level must be a mapping; "
            f"got {type(raw).__name__}"
        )
    sv = raw.get("schema_version")
    if sv != _BUILD_NEXT_SCHEMA_VERSION:
        raise ValueError(
            f"build-next.yaml: unexpected schema_version={sv!r}; "
            f"expected {_BUILD_NEXT_SCHEMA_VERSION}"
        )
    payload = {k: v for k, v in raw.items() if k != "schema_version"}
    return BuildNextRecommendation.model_validate(payload)


# ====================================================================
# Audit-log emit helpers (AC.BLDNXT.8)
# ====================================================================


def emit_build_next_start_audit(
    extraction_dir_: Path,
    *,
    extraction_id: str,
    gap_count: int,
    survey_present: bool,
    interview_priority_count: int,
    llm_judge_budget_cents: int,
    timestamp: str | None = None,
) -> Path:
    """Emit ``build_next_start`` audit-log entry (AC.BLDNXT.8)."""
    return write_audit_entry(
        extraction_dir_,
        event_kind="build_next_start",
        extraction_id=extraction_id,
        estimate={
            "extraction_id": extraction_id,
            "gap_count": gap_count,
            "survey_present": survey_present,
            "interview_priority_count": interview_priority_count,
            "llm_judge_budget_cents": llm_judge_budget_cents,
        },
        timestamp=timestamp,
    )


def emit_build_next_persisted_audit(
    extraction_dir_: Path,
    *,
    extraction_id: str,
    rec: BuildNextRecommendation,
    build_next_md_path_str: str,
    build_next_yaml_path_str: str,
    timestamp: str | None = None,
) -> Path:
    """Emit ``build_next_persisted`` audit-log entry."""
    return write_audit_entry(
        extraction_dir_,
        event_kind="build_next_persisted",
        extraction_id=extraction_id,
        artefact_path=build_next_yaml_path_str,
        estimate={
            "extraction_id": extraction_id,
            "candidate_count": len(rec.candidates),
            "truncated_count": rec.truncated_count,
            "llm_judge_invocations": rec.llm_judge_invocations,
            "degenerate_survey": rec.degenerate_survey,
            "build_next_md_path": build_next_md_path_str,
            "build_next_yaml_path": build_next_yaml_path_str,
        },
        timestamp=timestamp,
    )


def emit_build_next_end_audit(
    extraction_dir_: Path,
    *,
    extraction_id: str,
    duration_ms: int,
    total_cost_cents: float,
    timestamp: str | None = None,
) -> Path:
    """Emit ``build_next_end`` audit-log entry."""
    return write_audit_entry(
        extraction_dir_,
        event_kind="build_next_end",
        extraction_id=extraction_id,
        estimate={
            "extraction_id": extraction_id,
            "duration_ms": duration_ms,
            "total_cost_cents": total_cost_cents,
        },
        timestamp=timestamp,
    )


# ====================================================================
# Stdout summary (AC.PERSONA-PULL.1)
# ====================================================================


def render_stdout_summary(rec: BuildNextRecommendation) -> str:
    """Render the per-CLI stdout summary.

    Lists per-candidate gap_id + composite_score + signal + a
    truncated rationale. Header flags degenerate-survey explicitly.

    Persona invokes via `loam odd-extract <repo> --build-next` on
    user-question-trigger such as 'what should I build next?'.
    """
    lines: list[str] = []
    lines.append(f"Build-next recommendation for {rec.extraction_id}")
    lines.append(f"  analyzed_at:           {rec.analyzed_at}")
    lines.append(f"  candidate_count:       {len(rec.candidates)}")
    if rec.truncated_count:
        lines.append(
            f"  truncated_count:       {rec.truncated_count} "
            f"(underlying list exceeded --limit)"
        )
    lines.append(f"  llm_judge_invocations: {rec.llm_judge_invocations}")
    if rec.degenerate_survey:
        lines.append(
            "  degenerate_survey:     true (no survey context found; "
            "ranking falls back to gap-confidence × estimated-impact)"
        )
    else:
        lines.append("  degenerate_survey:     false")

    if not rec.candidates:
        lines.append("  (no candidates surfaced; gap inventory is empty)")
        text = "\n".join(lines)
        _assert_informative_not_prescriptive(text, surface="stdout-summary")
        return text

    lines.append("")
    lines.append("  Ranked candidates:")
    for k, c in enumerate(rec.candidates, start=1):
        lines.append(
            f"    {k:>2}. {c.gap_id} "
            f"score={c.composite_score:.4f} "
            f"signal={c.priority_match_signal}"
        )
    text = "\n".join(lines)
    _assert_informative_not_prescriptive(text, surface="stdout-summary")
    return text


# ====================================================================
# Cost-band check (AC.BLDNXT.7)
# ====================================================================


def estimate_build_next_cost_cents(
    *,
    gap_count: int,
    survey_present: bool,
) -> float:
    """Pre-flight cost estimate for the LLM-judge tier.

    Per sub-plan-doc §14: ~$0.02 per LLM-judge invocation; cap-of-5
    invocations per run; survey-absent path makes zero LLM calls.
    Conservative upper-bound: cap × per-call estimate. Used for the
    pre-flight halt-band check at AC.BLDNXT.7.
    """
    if not survey_present or gap_count == 0:
        return 0.0
    # Each LLM-judge call ~$0.02 (Sonnet pricing on a ~400-token
    # response × ~2k-token bundle prompt; bounded by the structured
    # JSON contract). Cap-of-5 → conservative upper-bound $0.10.
    estimated_invocations = min(LLM_JUDGE_INVOCATION_CAP, gap_count)
    return round(estimated_invocations * 2.0, 2)  # cents


def check_build_next_cost_band(
    *,
    estimated_cost_cents: float,
    budget_cents: float = float(DEFAULT_LLM_JUDGE_BUDGET_CENTS),
) -> None:
    """Halt-on-band check per AC.BLDNXT.7.

    Pre-flight estimate exceeding the upper halt band ($0.30) raises
    :class:`OddExtractorError`. Estimates below the lower band
    ($0.02) when survey is present + gaps exist also halt (sanity —
    something is wrong with the pre-flight estimator).
    """
    if estimated_cost_cents > LLM_JUDGE_HALT_UPPER_CENTS:
        raise OddExtractorError(
            f"build_next: pre-flight cost estimate "
            f"{estimated_cost_cents:.2f}¢ exceeds upper halt band "
            f"({LLM_JUDGE_HALT_UPPER_CENTS}¢). Halt-and-surface per "
            f"AC.BLDNXT.7."
        )
    if estimated_cost_cents > budget_cents:
        raise OddExtractorError(
            f"build_next: pre-flight cost estimate "
            f"{estimated_cost_cents:.2f}¢ exceeds configured budget "
            f"{budget_cents:.2f}¢. Pass --budget-cents to override."
        )
