"""Completeness — heuristic pre-pass + LLM-as-judge missing-objective detector.

Per v0.2.4 Cycle 1 sub-plan-doc §3 AC.COMPINT.2 + AC.COMPINT.3 +
AC.COMPINT.9:

- :func:`heuristic_priors` — deterministic, zero-LLM-cost pre-pass
  that surfaces three baseline ABSENT-objective patterns. Feeds the
  LLM-judge.

- :func:`flag_missing_objectives` — LLM-as-judge call (Anthropic
  Messages API; lazy-imported via ``synthesis``-style stub-friendly
  contract). System prompt injects the lean-grounding §altitudes +
  §self-checks verbatim. Cap-of-5 enforcement on prompt-side
  + post-validation truncation. Cost-budget integration via
  :class:`loam.cost_governance.BudgetEnvelope` +
  :class:`BudgetExceededError`.

The two functions compose: :func:`heuristic_priors` runs first
(zero-cost; deterministic), its output threads into the LLM-judge
prompt as priors, the LLM may augment / downgrade / filter, and the
final cap-of-5 candidates feed the interview loop.

Banding rule (sub-plan-doc §6 + master plan §9): user-added
objectives default to PLAUSIBLE confidence (interview audit-log
entry serves as ``survey_line_refs`` evidence; satisfies PLAUSIBLE
invariant cleanly per §7).
"""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from .errors import StageError
from .spec import (
    FlaggedMissing,
    HeuristicPrior,
    MultiSourceBundle,
    Objective,
)


# ---- Constants ----------------------------------------------------

# Per sub-plan-doc §3 AC.COMPINT.2 — cap-of-5 candidates per run.
MAX_FLAGGED_CANDIDATES = 5

# Per sub-plan-doc §3 AC.COMPINT.9 — Anthropic Sonnet (default).
_DEFAULT_MODEL_ID = "claude-sonnet-4-5"

# Per sub-plan-doc §3 AC.COMPINT.9 — cost band; rate constants
# mirror :mod:`synthesis` for symmetry.
_CENTS_PER_INPUT_TOKEN = 0.0003   # ~$3/M input tokens
_CENTS_PER_OUTPUT_TOKEN = 0.0015  # ~$15/M output tokens
_OUTPUT_TOKEN_RATIO = 0.2

# Compliance/audit substring patterns (case-insensitive).
_COMPLIANCE_KEYWORDS = (
    "soc-2", "soc 2", "soc2",
    "hipaa", "pci", "pci-dss", "gdpr",
    "compliance", "audit trail", "audit log",
)

# Domain labels signalling security-objective presence.
_SECURITY_DOMAINS = ("auth", "security", "audit", "access-control", "authn", "authz")
# Domain labels signalling compliance-objective presence.
_COMPLIANCE_DOMAINS = ("compliance", "audit")
# Domain labels signalling persistence-objective presence.
_PERSISTENCE_DOMAINS = ("persistence", "data-write", "storage", "data")

# Data-modify route shapes.
_DATA_MODIFY_METHODS = re.compile(r"\b(POST|PUT|DELETE|PATCH)\b", re.IGNORECASE)


# ---- Helpers -------------------------------------------------------


def _domain_present(objectives: list[Objective], domains: tuple[str, ...]) -> bool:
    """Returns True if any objective's ``domain`` field contains any
    of the named substring tokens (case-insensitive)."""
    for o in objectives:
        d = (o.domain or "").lower()
        for needle in domains:
            if needle in d:
                return True
    return False


def _survey_text(bundle: MultiSourceBundle) -> str:
    """Concatenated raw-text + parsed values from the survey bundle."""
    if not bundle.user_survey:
        return ""
    parts: list[str] = []
    raw = bundle.user_survey.get("raw_text", "")
    if raw:
        parts.append(raw)
    parsed = bundle.user_survey.get("parsed") or {}
    if isinstance(parsed, dict):
        for v in parsed.values():
            if isinstance(v, str):
                parts.append(v)
    return "\n".join(parts).lower()


def _survey_indicates_production(bundle: MultiSourceBundle) -> bool:
    """Survey signals production stake.

    Heuristic-1 keys on this. Looks at parsed survey
    ``production_use`` / ``production_stake`` field set to ``Yes`` /
    ``true`` / ``y`` (case-insensitive); falls back to substring
    match on raw_text.
    """
    if not bundle.user_survey:
        return False
    parsed = bundle.user_survey.get("parsed") or {}
    if isinstance(parsed, dict):
        for key in ("production_use", "production_stake", "in_production"):
            v = parsed.get(key)
            if isinstance(v, bool) and v:
                return True
            if isinstance(v, str) and v.strip().lower() in (
                "yes", "y", "true", "production"
            ):
                return True
    raw = (bundle.user_survey.get("raw_text") or "").lower()
    # Conservative substring — explicit "production_use: yes" or
    # "in production" type phrases.
    if "production_use" in raw and "yes" in raw:
        return True
    if "in production" in raw or "production stake" in raw:
        return True
    return False


def _survey_mentions_compliance(bundle: MultiSourceBundle) -> list[str]:
    """List of compliance keywords found in the survey body, in order."""
    text = _survey_text(bundle)
    if not text:
        return []
    found: list[str] = []
    for kw in _COMPLIANCE_KEYWORDS:
        if kw in text and kw not in found:
            found.append(kw)
    return found


def _data_modify_routes(bundle: MultiSourceBundle) -> list[str]:
    """Return code-pattern refs whose ``text`` mentions a data-modify HTTP method."""
    out: list[str] = []
    for c in bundle.code_patterns:
        if not isinstance(c, dict):
            continue
        text = str(c.get("text") or "")
        if _DATA_MODIFY_METHODS.search(text):
            ac_id = str(c.get("ac_id") or "")
            label = ac_id if ac_id else text[:60]
            out.append(label)
    # Also scan test_assertions in case adapters emit route info under
    # the test bundle (defensive — most adapters don't).
    return out


# ---- Public — heuristic pre-pass ----------------------------------


def heuristic_priors(
    objectives: list[Objective],
    *,
    multi_source_bundle: MultiSourceBundle,
) -> list[HeuristicPrior]:
    """Deterministic missing-objective heuristic pre-pass.

    Per sub-plan-doc §3 AC.COMPINT.3: three baseline patterns surface
    structural gaps. The LLM-judge consumes these as priors; it may
    confirm + augment, downgrade, or filter.

    Patterns (ranked by priority):

    1. ``production-stake-no-security-objective`` — survey indicates
       production-use AND no security-domain objective.
    2. ``survey-compliance-no-compliance-objective`` — survey body
       mentions a compliance keyword AND no compliance-domain
       objective.
    3. ``data-modify-routes-no-persistence-objective`` — code-patterns
       include POST/PUT/DELETE/PATCH AND no persistence-domain
       objective.

    Returns: list of :class:`HeuristicPrior` (zero..three entries; one
    per fired pattern). No false-positive minimization here — the
    LLM-judge does that.
    """
    out: list[HeuristicPrior] = []

    # Pattern 1 — production-stake without security objective.
    if _survey_indicates_production(multi_source_bundle) and not _domain_present(
        objectives, _SECURITY_DOMAINS
    ):
        evidence: list[str] = []
        if multi_source_bundle.user_survey:
            sp = multi_source_bundle.user_survey.get("source_path")
            if sp:
                evidence.append(f"survey:{sp}")
        out.append(
            HeuristicPrior(
                pattern_id="production-stake-no-security-objective",
                prior_text=(
                    "Production-stake repo lacks any security-domain "
                    "objective; an audit/access-control outcome is "
                    "likely missing from the extracted set."
                ),
                priority="high",
                evidence_refs=evidence,
            )
        )

    # Pattern 2 — compliance keyword in survey, no compliance objective.
    found_keywords = _survey_mentions_compliance(multi_source_bundle)
    if found_keywords and not _domain_present(objectives, _COMPLIANCE_DOMAINS):
        evidence = [f"survey-keyword:{kw}" for kw in found_keywords[:3]]
        out.append(
            HeuristicPrior(
                pattern_id="survey-compliance-no-compliance-objective",
                prior_text=(
                    "Survey mentions compliance terms "
                    f"({', '.join(found_keywords[:3])}) but no "
                    "compliance/audit-domain objective is present in "
                    "the extracted set."
                ),
                priority="high",
                evidence_refs=evidence,
            )
        )

    # Pattern 3 — data-modify routes without persistence objective.
    routes = _data_modify_routes(multi_source_bundle)
    if routes and not _domain_present(objectives, _PERSISTENCE_DOMAINS):
        out.append(
            HeuristicPrior(
                pattern_id="data-modify-routes-no-persistence-objective",
                prior_text=(
                    f"Repo exposes {len(routes)} data-modify routes "
                    "(POST/PUT/DELETE/PATCH) but no persistence/data-"
                    "write objective is present; persistence outcome "
                    "may be missing."
                ),
                priority="medium",
                evidence_refs=routes[:5],
            )
        )

    return out


# ---- LLM-judge prompt ---------------------------------------------

_LLM_JUDGE_SYSTEM_PROMPT = """You are an ODD completeness-interview auditor.
You are given a list of OBJECTIVES already extracted from a target
codebase, plus a multi-source bundle (README, design docs, tests,
survey, code patterns), plus deterministic HEURISTIC PRIORS naming
likely-missing-objective patterns. Your job is to flag MISSING-but-
EXPECTED objectives the synthesis pass did not surface.

CRITICAL ALTITUDE RULE — every flagged candidate MUST satisfy these
five self-checks (from the ODD lean grounding doc):

1. Outcome-or-fact? Outcome → candidate; fact → reject.
2. Implementation-swap. Could the same statement describe the system
   if rewritten in a different language with different libraries?
   Yes → candidate. No → reject.
3. Builder-method. Could a different builder produce a different
   shape that meets the same statement? Yes → loose enough.
4. Observable-from-outside. Verifiable without reading code? Yes →
   candidate.
5. User-purpose. Names purpose / value-to-someone? Yes → candidate.

REJECTED ALTITUDE DRIFT MODES:

- Symbol-as-AC: "Route GET /foo exists" — implementation, not
  objective.
- Function-name-as-AC: "Function processOrder() exists" —
  implementation.
- Feature-as-objective: "App has CSV upload" — capability, not
  objective. The OUTCOME the CSV upload SERVES is the objective.
- Constraint-as-objective: "System must be SOC-2-compliant" —
  constraint, not objective. The OUTCOME the compliance enables
  ("audit trail identifies who initiated each dispute") is the
  objective.
- Gap-as-objective: "Missing test coverage" is a finding, not an
  objective.

You will be given:
- EXISTING OBJECTIVES — what synthesis already extracted.
- HEURISTIC PRIORS — deterministic flags from the pre-pass; treat as
  hints, not guarantees. You may CONFIRM (emit a candidate aligned
  with the prior), DOWNGRADE (lower priority), or FILTER (drop) any
  prior. You may ALSO emit candidates the priors didn't name.
- MULTI-SOURCE BUNDLE — README, design docs, tests, survey, code
  patterns.

OUTPUT — a single JSON object with one key, ``flagged``, whose value
is a list of objects:

{
  "flagged": [
    {
      "candidate_text": "<>=20 char outcome statement>",
      "reasoning": "<why this is missing AND outcome-altitude>",
      "evidence_refs": ["<source-ref>", ...],
      "priority": "high" | "medium" | "low",
      "domain": "<lowercase domain hint>"
    }
  ]
}

CAP: emit AT MOST 5 candidates. If you have more, rank by priority
and keep only the top 5. ``candidate_text`` must be >= 20 characters.
Emit ONLY the JSON. No surrounding prose, no markdown code fence."""


def _format_existing_objectives(objectives: list[Objective]) -> str:
    if not objectives:
        return "(none — extracted set is empty)"
    parts: list[str] = []
    for o in objectives:
        parts.append(
            f"- {o.objective_id} (domain={o.domain}, "
            f"confidence={o.confidence.value}): {o.text}"
        )
    return "\n".join(parts)


def _format_priors(priors: list[HeuristicPrior]) -> str:
    if not priors:
        return "(none — heuristic pre-pass surfaced no priors)"
    parts: list[str] = []
    for p in priors:
        ev = "; ".join(p.evidence_refs[:3]) if p.evidence_refs else "(none)"
        parts.append(
            f"- pattern={p.pattern_id} priority={p.priority} "
            f"evidence={ev}\n  prior_text: {p.prior_text}"
        )
    return "\n".join(parts)


def _format_bundle(bundle: MultiSourceBundle) -> str:
    parts: list[str] = []
    parts.append(f"# Repo {bundle.repo_id} ({bundle.repo_path})")
    parts.append("")
    parts.append("## README")
    if bundle.readme_text:
        parts.append("```")
        parts.append(bundle.readme_text[:8000])
        parts.append("```")
    else:
        parts.append("(none)")
    parts.append("")
    parts.append("## Design docs")
    if bundle.design_docs:
        for d in bundle.design_docs[:10]:
            parts.append(f"### {d.get('path','')}")
            text = (d.get("text") or "")[:2000]
            parts.append(text)
            parts.append("")
    else:
        parts.append("(none)")
    parts.append("")
    parts.append("## User survey")
    if bundle.user_survey:
        raw = (bundle.user_survey.get("raw_text") or "")[:4000]
        parts.append(f"source: {bundle.user_survey.get('source_path','')}")
        parts.append(raw)
    else:
        parts.append("(none)")
    parts.append("")
    parts.append("## Test assertions (sample)")
    for t in bundle.test_assertions[:30]:
        parts.append(f"- {t.get('ac_id','')}: {t.get('text','')}")
    parts.append("")
    parts.append("## Code patterns (sample)")
    for c in bundle.code_patterns[:30]:
        parts.append(f"- {c.get('ac_id','')}: {c.get('text','')}")
    return "\n".join(parts)


def _format_user_prompt(
    objectives: list[Objective],
    priors: list[HeuristicPrior],
    bundle: MultiSourceBundle,
) -> str:
    return "\n\n".join(
        [
            "# EXISTING OBJECTIVES",
            _format_existing_objectives(objectives),
            "# HEURISTIC PRIORS",
            _format_priors(priors),
            "# MULTI-SOURCE BUNDLE",
            _format_bundle(bundle),
            (
                "Now emit the JSON object per the schema in the system "
                "prompt. Outcome-altitude only. CAP AT 5 CANDIDATES."
            ),
        ]
    )


# ---- Cost estimation ----------------------------------------------


def estimate_judge_cost_cents(token_count: int) -> float:
    """Dry-run cost estimate per AC.COMPINT.9.

    Mirrors :func:`synthesis.estimate_synthesis_cost_cents`; cents
    (float) using input + output-ratio blend.
    """
    if token_count <= 0:
        return 0.0
    input_cost = token_count * _CENTS_PER_INPUT_TOKEN
    output_tokens = int(token_count * _OUTPUT_TOKEN_RATIO)
    output_cost = output_tokens * _CENTS_PER_OUTPUT_TOKEN
    return round(input_cost + output_cost, 4)


# ---- LLM-judge -----------------------------------------------------


def _strip_code_fence(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _parse_judge_json(raw: str) -> dict[str, Any]:
    cleaned = _strip_code_fence(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise StageError(
            f"flag_missing_objectives: LLM response is not valid JSON "
            f"({exc}); raw[:200]={cleaned[:200]!r}"
        ) from exc
    if not isinstance(data, dict):
        raise StageError(
            f"flag_missing_objectives: response root must be a JSON "
            f"object; got {type(data).__name__}"
        )
    return data


def _validate_flagged_rows(
    payload: dict[str, Any],
) -> list[FlaggedMissing]:
    flagged_raw = payload.get("flagged") or []
    if not isinstance(flagged_raw, list):
        raise StageError(
            "flag_missing_objectives: 'flagged' must be a list"
        )
    out: list[FlaggedMissing] = []
    for i, row in enumerate(flagged_raw):
        if not isinstance(row, dict):
            raise StageError(
                f"flag_missing_objectives: flagged[{i}] must be an "
                f"object"
            )
        try:
            out.append(FlaggedMissing.model_validate(row))
        except ValidationError as exc:
            raise StageError(
                f"flag_missing_objectives: flagged[{i}] "
                f"ValidationError: {exc}"
            ) from exc
    return out


_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _truncate_to_cap(rows: list[FlaggedMissing]) -> list[FlaggedMissing]:
    """Cap-of-5 enforcement; preserves priority order, then input order."""
    if len(rows) <= MAX_FLAGGED_CANDIDATES:
        return rows
    indexed = list(enumerate(rows))
    indexed.sort(
        key=lambda pair: (
            _PRIORITY_ORDER.get(pair[1].priority, 3),
            pair[0],
        )
    )
    keep = indexed[:MAX_FLAGGED_CANDIDATES]
    keep.sort(key=lambda pair: pair[0])
    return [r for _, r in keep]


def flag_missing_objectives(
    objectives: list[Objective],
    *,
    multi_source_bundle: MultiSourceBundle,
    anthropic_client: Any,
    priors: list[HeuristicPrior] | None = None,
    model_id: str = _DEFAULT_MODEL_ID,
    max_tokens: int = 4000,
) -> list[FlaggedMissing]:
    """LLM-as-judge missing-objective detector.

    Per sub-plan-doc §3 AC.COMPINT.2: structured JSON response with
    cap-of-5 candidates. ``priors`` defaults to deriving from
    :func:`heuristic_priors` when omitted (callers wanting to skip
    pre-pass pass an explicit empty list).

    Caller is responsible for cost-budget enforcement at AC.COMPINT.9
    altitude (the budget envelope is checked at the CLI handler level
    via :func:`budget.enforce_budget`); this function does not raise
    :class:`BudgetExceededError`.

    Tests inject ``anthropic_client=<stub>`` returning a canned
    Message-shaped response (``content[0].text`` is JSON matching
    :class:`FlaggedMissing` rows). No real API in CI.
    """
    if anthropic_client is None:
        raise StageError(
            "flag_missing_objectives: anthropic_client is required (pass "
            "a real Anthropic client or a stub for tests). The "
            "completeness layer never makes implicit network calls."
        )

    use_priors = priors if priors is not None else heuristic_priors(
        objectives, multi_source_bundle=multi_source_bundle
    )

    user_prompt = _format_user_prompt(
        objectives, use_priors, multi_source_bundle
    )

    try:
        response = anthropic_client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": _LLM_JUDGE_SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                },
            ],
            messages=[{"role": "user", "content": user_prompt}],
        )
    except TypeError:
        response = anthropic_client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            system=_LLM_JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

    raw_text = ""
    try:
        block = response.content[0]
        raw_text = getattr(block, "text", None) or block["text"]
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise StageError(
            f"flag_missing_objectives: response shape lacks "
            f".content[0].text ({exc}); cannot extract LLM output"
        ) from exc

    payload = _parse_judge_json(raw_text)
    flagged = _validate_flagged_rows(payload)
    return _truncate_to_cap(flagged)


# ---- Default Anthropic client construction -------------------------


def build_default_anthropic_client() -> Any:  # pragma: no cover (subprocess)
    """Construct the production-default subscription-routed synthesis client.

    Per v0.2.5 corrective C4-pivot — no Anthropic SDK; no API key.
    Mirrors :func:`synthesis.build_default_anthropic_client`. Returns a
    :class:`ClaudePrintAnthropicShimClient` routing through ``claude -p``
    against the user's Claude Max subscription. NO ANTHROPIC_API_KEY
    consulted.
    """
    from .claude_print_synthesis_client import (
        ClaudeBinaryMissingError,
        build_default_synthesis_client,
    )

    try:
        return build_default_synthesis_client()
    except ClaudeBinaryMissingError as exc:
        raise StageError(
            "completeness: claude CLI not found on PATH. Install Claude "
            "Code (https://docs.anthropic.com/claude-code) so the "
            "`claude` binary resolves on this process's PATH. v0.2.5 "
            "corrective C4-pivot: completeness routes through `claude -p` "
            "subscription auth — NO ANTHROPIC_API_KEY required."
        ) from exc
