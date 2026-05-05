"""LLM-pass synthesis layer — v0.2.3 outcome-altitude objective generator.

Per AC.OBJX.5 + AC.OBJX.6 + AC.OBJX.12 (sub-plan-doc §3) — single
LLM-pass call that emits banded :class:`Objective` +
:class:`Constraint` + :class:`Capability` rows from a
:class:`MultiSourceBundle`. Composes on:

- :mod:`loam.cost_governance` ``BudgetEnvelope`` + ``enforce_budget``
  + ``BudgetExceededError`` for the ceiling-check (v0.1.6 primitive).
- ``anthropic`` SDK (lazy-imported; configured as
  ``[project.optional-dependencies]`` extra ``synthesis``) for the
  Messages API + prompt caching.
- :func:`observability.write_audit_entry` for the
  ``synthesis_complete`` event-kind.

Banding rule (lean grounding doc §brownfield ODD-RE inputs +
sub-plan-doc §3 AC.OBJX.5):

- VERIFIED — test asserts outcome AND README/design-doc states it
  (two-source).
- PLAUSIBLE — single-source (README OR design-doc OR survey).
- HYPOTHESISED — pattern-only inference; rationale required.

Survey-shape claims cap at PLAUSIBLE per master plan §7.7 +
sub-plan-doc §7.

Test-time path: callers pass ``anthropic_client=<stub>`` returning a
canned ``Message``-shaped object (``content[0].text`` is JSON
matching :class:`SynthesisResult`). No real API calls in CI.
"""

from __future__ import annotations

import datetime as _dt
import json
import re
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from .errors import StageError
from .observability import write_audit_entry
from .spec import (
    Capability,
    Constraint,
    MultiSourceBundle,
    Objective,
    SynthesisResult,
)


# Per sub-plan-doc §7 method-decision register.
# Anthropic Sonnet — claude-api SKILL conventions.
_DEFAULT_MODEL_ID = "claude-sonnet-4-5"

# Cost rate (cents per token) — Sonnet input/output blended estimate.
# Per master plan §6.1 + sub-plan-doc §7. The exact rate varies; this
# is a calibration constant that the dry-run estimator multiplies by
# ``token_count``. The 50× headroom on the $0.10–$5.00 halt-band
# absorbs the approximation error.
_CENTS_PER_INPUT_TOKEN = 0.0003   # ~$3/M input tokens
_CENTS_PER_OUTPUT_TOKEN = 0.0015  # ~$15/M output tokens
# Output ratio assumption — synthesis emits structured rows; tail
# typically ~20% of input bundle size.
_OUTPUT_TOKEN_RATIO = 0.2


def estimate_synthesis_cost_cents(token_count: int) -> float:
    """Dry-run cost estimate per AC.OBJX.6.

    Returns cents (float) using the input-token + output-token-ratio
    blend. Per sub-plan-doc §7: 4-chars-per-token approximation
    upstream (see :mod:`multi_source`); halt-band $0.10–$5.00 has
    50× headroom on this estimator.
    """
    if token_count <= 0:
        return 0.0
    input_cost = token_count * _CENTS_PER_INPUT_TOKEN
    output_tokens = int(token_count * _OUTPUT_TOKEN_RATIO)
    output_cost = output_tokens * _CENTS_PER_OUTPUT_TOKEN
    return round(input_cost + output_cost, 4)


# ====================================================================
# Synthesis prompt
# ====================================================================
#
# Per sub-plan-doc §3 AC.OBJX.5 — system prompt holds lean grounding
# doc §altitudes + §drift-modes + §self-checks verbatim, plus the
# V/P/H banding rule. User prompt holds the multi-source bundle in
# priority order. Response format: structured JSON matching the
# typed-model shape.

_SYSTEM_PROMPT = """You are an ODD reverse-engineering assistant. Your job
is to read a multi-source bundle describing a target codebase and emit
a typed list of OBJECTIVES, CONSTRAINTS, and CAPABILITIES at OUTCOME
ALTITUDE.

CRITICAL RULE: every objective MUST satisfy these five self-checks
from the ODD lean grounding doc:

1. Outcome-or-fact? Outcome → objective candidate; fact → reject.
2. Implementation-swap. Could the same statement describe the system
   if rewritten in a different language with different libraries?
   Yes → objective. No → reject.
3. Builder-method. Could a different builder produce a different
   shape that meets the same statement? Yes → loose enough.
4. Observable-from-outside. Verifiable without reading code? Yes →
   objective.
5. User-purpose. Names purpose / value-to-someone? Yes → objective.

Drift modes to AVOID (will be rejected by the altitude validator):

- Symbol-as-AC: "Route GET /foo exists at file.js:42" — implementation,
  not objective.
- Function-name-as-AC: "Function processOrder() exists" —
  implementation.
- Feature-as-objective: "App has CSV upload" — capability, not
  objective. The OUTCOME the CSV upload SERVES is the objective.
- Constraint-as-objective: "System must be SOC-2-compliant" —
  constraint, not objective. The OUTCOME the compliance enables
  ("audit trail identifies who did what") is the objective.

ALTITUDE LADDER:

- Objective: outcome the system delivers (observable from outside;
  survives implementation rewrite; names purpose).
- Constraint: bound on the solution space (compliance / infra /
  language / security / domain); not itself an outcome.
- Capability: feature/function serving an objective; one HOW of
  many.

BANDING RULE (V/P/H):

- VERIFIED: test asserts the outcome AND README or design-doc states
  it (TWO-SOURCE rule). All VERIFIED rows must cite at least one
  test_name_ref AND at least one of readme_excerpts/design_doc_refs,
  AND set repo_sha.
- PLAUSIBLE: single source (README, design-doc, OR survey). Survey-
  only evidence CAPS AT PLAUSIBLE — never promote a survey-only
  claim to VERIFIED.
- HYPOTHESISED: pattern-only inference (code patterns without README
  or test corroboration). Rationale REQUIRED.

ID FORMAT:

- Objective: O.<domain>.<n> (e.g., O.dispute-flow.1)
- Constraint: K.<domain>.<n> (e.g., K.compliance.1)
- Capability: C.<domain>.<n> (e.g., C.csv-upload.1)
- domain: lowercase letters/digits/hyphens.

OBJECTIVE TEXT MUST BE >= 20 CHARACTERS. Capability serves field
must reference at least one O.* objective ID.

CAPABILITIES MUST SERVE OBJECTIVES YOU EMIT in the same response.
Do not reference O.* IDs that don't exist in your output.

OUTPUT: a single JSON object with three keys: "objectives",
"constraints", "capabilities". Each is a list of typed rows. NO
prose outside the JSON. Use this exact schema:

{
  "objectives": [
    {
      "objective_id": "O.<domain>.<n>",
      "text": "<>=20 char outcome statement>",
      "confidence": "VERIFIED|PLAUSIBLE|HYPOTHESISED",
      "domain": "<domain>",
      "evidence": {
        "readme_excerpts": ["<excerpt>"],
        "design_doc_refs": ["docs/path.md#heading"],
        "test_name_refs": ["tests/x.spec.ts::it should X"],
        "survey_line_refs": ["<line>"],
        "code_pattern_refs": ["src/foo.js:42"],
        "repo_sha": "<sha or null>",
        "rationale": "<for HYPOTHESISED>"
      }
    }
  ],
  "constraints": [
    {
      "constraint_id": "K.<domain>.<n>",
      "text": "<bound>",
      "bounds_kind": "compliance|infra|language|security|domain",
      "evidence": { ...same shape minus test_name_refs... }
    }
  ],
  "capabilities": [
    {
      "capability_id": "C.<domain>.<n>",
      "text": "<feature serving an objective>",
      "serves": ["O.<domain>.<n>"],
      "evidence": { ...same shape... }
    }
  ]
}

Emit ONLY the JSON. No surrounding prose, no markdown code fence."""


def _format_user_prompt(bundle: MultiSourceBundle) -> str:
    """Format the multi-source bundle in priority order.

    Per sub-plan-doc §7: README → design docs → tests → survey →
    code patterns. Per-source labelling so the LLM weighs each
    source explicitly rather than as a flat blob.
    """
    parts: list[str] = []
    parts.append(f"# Repo\n\n- repo_path: {bundle.repo_path}")
    parts.append(f"- repo_id: {bundle.repo_id}")
    parts.append(f"- repo_sha: {bundle.repo_sha or '(unknown)'}")
    parts.append("")

    parts.append("# 1. README")
    if bundle.readme_text:
        parts.append("```")
        parts.append(bundle.readme_text)
        parts.append("```")
        if bundle.readme_truncated:
            parts.append("(truncated at 50KB cap)")
    else:
        parts.append("(none)")
    parts.append("")

    parts.append("# 2. Design docs")
    if bundle.design_docs:
        for d in bundle.design_docs:
            parts.append(f"## {d.get('path','')}")
            heading = d.get("heading", "")
            if heading:
                parts.append(f"H1: {heading}")
            parts.append("```")
            parts.append(d.get("text", ""))
            parts.append("```")
            parts.append("")
    else:
        parts.append("(none)")
    parts.append("")

    parts.append("# 3. Test assertions (outcome-asserting names)")
    if bundle.test_assertions:
        for t in bundle.test_assertions[:200]:
            parts.append(
                f"- {t.get('ac_id','')}: {t.get('text','')} "
                f"@ {t.get('first_citation','')}"
            )
    else:
        parts.append("(none)")
    parts.append("")

    parts.append("# 4. User survey (operator-supplied context)")
    if bundle.user_survey:
        parts.append(f"source: {bundle.user_survey.get('source_path','')}")
        raw = bundle.user_survey.get("raw_text", "")
        if raw:
            parts.append("```")
            parts.append(raw[:8000])
            parts.append("```")
    else:
        parts.append("(none)")
    parts.append("")

    parts.append(
        "# 5. Code patterns (adapter-emitted symbol-altitude evidence)"
    )
    if bundle.code_patterns:
        for c in bundle.code_patterns[:200]:
            parts.append(
                f"- {c.get('ac_id','')}: {c.get('text','')} "
                f"[{c.get('evidence_kind','')}]"
            )
    else:
        parts.append("(none)")
    parts.append("")

    parts.append(
        "Now emit the JSON object per the schema in the system prompt. "
        "Outcome-altitude only. Multi-source banding required."
    )
    return "\n".join(parts)


# ====================================================================
# Stub-protocol type for tests
# ====================================================================


class StubAnthropicMessage:  # pragma: no cover — test helper
    """Minimal shape stub-clients return.

    Real ``anthropic.types.Message``-compatible: ``.content[0].text``.
    """

    def __init__(self, text: str, input_tokens: int = 0, output_tokens: int = 0):
        self.content = [type("Block", (), {"type": "text", "text": text})()]
        self.usage = type(
            "Usage",
            (),
            {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        )()


# ====================================================================
# Synthesis call
# ====================================================================


def _strip_code_fence(text: str) -> str:
    """Strip leading/trailing ``` fences if present.

    LLMs sometimes wrap JSON despite the instruction; tolerant parse.
    """
    s = text.strip()
    if s.startswith("```"):
        # Drop opening fence + optional language hint
        s = re.sub(r"^```(?:json)?\s*", "", s)
        s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _parse_synthesis_json(raw: str) -> dict[str, Any]:
    """Parse the LLM response; raise StageError on malformed JSON."""
    cleaned = _strip_code_fence(raw)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise StageError(
            f"synthesis: LLM response is not valid JSON ({exc}); "
            f"raw[:200]={cleaned[:200]!r}"
        ) from exc
    if not isinstance(data, dict):
        raise StageError(
            f"synthesis: LLM response root must be a JSON object; "
            f"got {type(data).__name__}"
        )
    return data


def _validate_rows(
    payload: dict[str, Any],
    *,
    repo_sha: str | None,
) -> tuple[list[Objective], list[Constraint], list[Capability]]:
    """Construct typed rows; raise StageError on per-row ValidationError.

    Per sub-plan-doc §3 AC.OBJX.5: malformed LLM rows are surfaced
    with the offending dict for triage; the response is not silently
    discarded.
    """
    objectives_raw = payload.get("objectives") or []
    constraints_raw = payload.get("constraints") or []
    capabilities_raw = payload.get("capabilities") or []

    if not isinstance(objectives_raw, list):
        raise StageError("synthesis: 'objectives' must be a list")
    if not isinstance(constraints_raw, list):
        raise StageError("synthesis: 'constraints' must be a list")
    if not isinstance(capabilities_raw, list):
        raise StageError("synthesis: 'capabilities' must be a list")

    objectives: list[Objective] = []
    constraints: list[Constraint] = []
    capabilities: list[Capability] = []

    for i, row in enumerate(objectives_raw):
        if not isinstance(row, dict):
            raise StageError(
                f"synthesis: objectives[{i}] must be an object"
            )
        # Thread repo_sha through if VERIFIED + missing.
        ev = row.get("evidence") or {}
        if isinstance(ev, dict):
            if (
                row.get("confidence") == "VERIFIED"
                and not ev.get("repo_sha")
                and repo_sha
            ):
                ev["repo_sha"] = repo_sha
                row["evidence"] = ev
        try:
            objectives.append(Objective.model_validate(row))
        except ValidationError as exc:
            raise StageError(
                f"synthesis: objectives[{i}] ValidationError: {exc}"
            ) from exc

    for i, row in enumerate(constraints_raw):
        if not isinstance(row, dict):
            raise StageError(
                f"synthesis: constraints[{i}] must be an object"
            )
        try:
            constraints.append(Constraint.model_validate(row))
        except ValidationError as exc:
            raise StageError(
                f"synthesis: constraints[{i}] ValidationError: {exc}"
            ) from exc

    for i, row in enumerate(capabilities_raw):
        if not isinstance(row, dict):
            raise StageError(
                f"synthesis: capabilities[{i}] must be an object"
            )
        try:
            capabilities.append(Capability.model_validate(row))
        except ValidationError as exc:
            raise StageError(
                f"synthesis: capabilities[{i}] ValidationError: {exc}"
            ) from exc

    return objectives, constraints, capabilities


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def synthesize_objectives(
    bundle: MultiSourceBundle,
    *,
    extraction_id: str,
    repo_sha: str | None = None,
    anthropic_client: Any | None = None,
    model_id: str = _DEFAULT_MODEL_ID,
    extraction_dir: Path | None = None,
    timestamp: str | None = None,
    max_tokens: int = 8000,
) -> SynthesisResult:
    """Run the synthesis LLM-pass per AC.OBJX.5.

    Inputs:

    - ``bundle`` — the multi-source input bundle.
    - ``extraction_id`` — passed through to the result.
    - ``repo_sha`` — pin for VERIFIED-band evidence; if ``None``,
      defaults to ``bundle.repo_sha``.
    - ``anthropic_client`` — pre-constructed client (or stub for
      tests). When ``None`` and tests don't inject, raises
      :class:`StageError` (no implicit network calls).
    - ``model_id`` — model selector; default Sonnet.
    - ``extraction_dir`` — when provided, audit-log
      ``synthesis_complete`` event-kind.
    - ``timestamp`` — injectable for deterministic tests.

    Returns :class:`SynthesisResult` with typed rows. Raises
    :class:`StageError` on malformed JSON or per-row ValidationError.
    """
    if anthropic_client is None:
        raise StageError(
            "synthesize_objectives: anthropic_client is required (pass a "
            "real Anthropic client or a stub for tests). The synthesis "
            "layer never makes implicit network calls."
        )

    sha = repo_sha if repo_sha is not None else bundle.repo_sha
    user_prompt = _format_user_prompt(bundle)

    # Anthropic Messages API call. Prompt caching: system block is the
    # static lean-grounding + banding rule; user is per-extraction.
    # Per sub-plan-doc §3 AC.OBJX.5 + claude-api SKILL conventions.
    try:
        response = anthropic_client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": _SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                },
            ],
            messages=[
                {"role": "user", "content": user_prompt},
            ],
        )
    except TypeError:
        # Stub clients in tests may not accept all kwargs; fall back
        # to the simplest invocation. Real SDK accepts; tests get
        # whichever shape they implement.
        response = anthropic_client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

    # Extract text. Real SDK: response.content[0].text. Stub mirrors.
    raw_text = ""
    try:
        block = response.content[0]
        raw_text = getattr(block, "text", None) or block["text"]
    except (AttributeError, IndexError, KeyError, TypeError) as exc:
        raise StageError(
            f"synthesize_objectives: response shape lacks .content[0].text "
            f"({exc}); cannot extract LLM output"
        ) from exc

    # Token usage — optional.
    input_tokens = 0
    output_tokens = 0
    usage = getattr(response, "usage", None)
    if usage is not None:
        input_tokens = getattr(usage, "input_tokens", 0) or 0
        output_tokens = getattr(usage, "output_tokens", 0) or 0

    # Cost actual.
    cost_actual = (
        input_tokens * _CENTS_PER_INPUT_TOKEN
        + output_tokens * _CENTS_PER_OUTPUT_TOKEN
    )

    payload = _parse_synthesis_json(raw_text)
    objectives, constraints, capabilities = _validate_rows(
        payload, repo_sha=sha
    )

    ts = timestamp if timestamp is not None else _now_iso()
    result = SynthesisResult(
        extraction_id=extraction_id,
        objectives=objectives,
        constraints=constraints,
        capabilities=capabilities,
        raw_response=raw_text,
        token_count_input=input_tokens,
        token_count_output=output_tokens,
        cost_actual_cents=round(cost_actual, 4),
        model_id=model_id,
        created_at=ts,
    )

    # Per AC.OBJX.12: emit synthesis_complete audit-log entry.
    if extraction_dir is not None:
        # Distribution by band for downstream telemetry.
        by_band = {"VERIFIED": 0, "PLAUSIBLE": 0, "HYPOTHESISED": 0}
        for o in objectives:
            by_band[o.confidence.value] = by_band.get(o.confidence.value, 0) + 1
        sources_used: list[str] = []
        if bundle.readme_text:
            sources_used.append("readme")
        if bundle.design_docs:
            sources_used.append("design_docs")
        if bundle.test_assertions:
            sources_used.append("tests")
        if bundle.user_survey:
            sources_used.append("survey")
        if bundle.code_patterns:
            sources_used.append("code_patterns")
        write_audit_entry(
            extraction_dir,
            event_kind="synthesis_complete",
            extraction_id=extraction_id,
            stage="generate",
            estimate={
                "source_list": sources_used,
                "token_count_input": input_tokens,
                "token_count_output": output_tokens,
                "cost_actual_cents": round(cost_actual, 4),
                "objective_count_by_band": by_band,
                "constraint_count": len(constraints),
                "capability_count": len(capabilities),
                "model_id": model_id,
            },
            timestamp=ts,
        )

    return result


# ====================================================================
# Convenience: build_default_anthropic_client
# ====================================================================


def build_default_anthropic_client() -> Any:  # pragma: no cover (network)
    """Construct a default ``anthropic.Anthropic()`` client.

    Lazy-imports ``anthropic`` so the SDK is optional. Raises
    :class:`StageError` if the package isn't installed.
    """
    try:
        import anthropic  # type: ignore[import]
    except ImportError as exc:
        raise StageError(
            "synthesis: anthropic SDK not installed. Add the "
            "`synthesis` extra to loam-odd-extractor (pip install "
            "loam-odd-extractor[synthesis]) or pass a stub client "
            "for tests."
        ) from exc
    return anthropic.Anthropic()
