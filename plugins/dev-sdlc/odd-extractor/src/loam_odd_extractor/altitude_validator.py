"""§self-checks 1-5 enforcement for v0.2.3 outcome-altitude rows.

Per AC.OBJX.8 (sub-plan-doc §3) — programmatic heuristics first;
LLM-as-judge invoked only for ``borderline`` rows. Composes with
Lens 5 ``EVAL_DIMENSIONS``: each §self-check is one named axis.

Self-checks (lean grounding doc §self-checks):

1. Outcome-or-fact? Outcome → keep; fact → drop.
2. Implementation-swap. Names a specific symbol/file/line → fail.
3. Builder-method. Could a different builder produce a different
   shape meeting the same statement? Fail if too tight.
4. Observable-from-outside. Verifiable without reading code? Fail
   if the statement is internal-only.
5. User-purpose. Names purpose / value-to-someone? Fail if no
   purpose statement.

Decision tree on failure (sub-plan-doc §3 + §7):

- §1 fail → drop (gap-as-objective / fact-as-objective).
- §2 fail → restate-as-capability if upstream supports, else drop
  (symbol-altitude content shouldn't survive).
- §3 fail → downgrade band (over-tight; less confidence).
- §4 fail → downgrade band (un-observable — band drops).
- §5 fail → drop unless VERIFIED evidence supports HYPOTHESISED
  retention (rare path).

Drift detection (Lens 5 ``needs_fresh_start``): >30% fail rate
across all rows → ``drift_halt_triggered=True``. Build agents
surface the halt; do NOT silently restart. Default threshold
overridable via ``fail_threshold`` parameter for tests.
"""

from __future__ import annotations

import re
from typing import Any

from .bands import ConfidenceBand
from .spec import (
    AltitudeCheckResult,
    Capability,
    Constraint,
    Objective,
    ValidationReport,
)


# ====================================================================
# Programmatic heuristics
# ====================================================================
#
# Per Lens 4 commitment (sub-plan-doc §2 + §6.10): keyword/regex
# heuristics gate cost. LLM-as-judge invoked only for borderline.

# Implementation-shape markers — file paths, line numbers, symbol
# names with parens, language keywords.
_IMPL_PATH_RE = re.compile(
    r"\b[\w/.-]+\.(py|js|ts|tsx|jsx|rb|go|rs|java|cs|cpp|c|h|md|yaml|yml|json|toml|html|css)\b"
    r"|\b\w+:\d+\b"  # file:line markers
)
_FUNC_CALL_RE = re.compile(r"\b\w+\(\)|\b(?:def|function|class)\s+\w+")
_HTTP_VERB_RE = re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/\S*\b")
_LIBRARY_NAME_RE = re.compile(
    r"\b(?:Express|Flask|Django|Rails|React|Vue|Angular|Pydantic|"
    r"FastAPI|Sinatra|Sidekiq|Celery|tree-sitter|pytest|jest|playwright)\b"
)

# Outcome-shape markers — verbs of action / observable behaviour.
_OUTCOME_VERB_RE = re.compile(
    r"\b(?:operators?|users?|customers?|admins?|auditors?|merchants?|"
    r"file|files|filed|files,|track|tracked|review|reviewed|approve|approved|"
    r"reject|rejected|reconcile|reconciled|verify|verified|access|accessed|"
    r"deliver|delivered|enable|enables?|enabled|allow|allows?|allowed|"
    r"replac|reduc|prevent|protect|comply|compliance|audit)\b",
    re.IGNORECASE,
)

# Purpose markers — "so that", "for", "to", "in order to".
_PURPOSE_RE = re.compile(
    r"\b(?:so that|in order to|to enable|to allow|to replace|to support|"
    r"for the purpose of|so they can|for compliance|for audit)\b",
    re.IGNORECASE,
)


def _check_outcome_or_fact(text: str) -> tuple[bool, str]:
    """§self-check 1: outcome (pass) vs fact (fail)."""
    # Heuristic: a statement of bare existence is fact-like.
    fact_phrases = [
        "exists at", "is at", "located at", "defined in", "lives in",
        "found at", "missing test", "no coverage", "no test",
        "function exists", "route exists", "class exists", "module exists",
    ]
    lower = text.lower()
    for phrase in fact_phrases:
        if phrase in lower:
            return False, f"fact-shape phrase: {phrase!r}"
    return True, ""


def _check_implementation_swap(text: str) -> tuple[bool, str]:
    """§self-check 2: survives implementation rewrite (pass).

    Fails if the statement names specific symbols / files / lines /
    libraries — those would NOT survive a different language/lib
    rewrite.
    """
    if _IMPL_PATH_RE.search(text):
        return False, "names file path / line marker"
    if _FUNC_CALL_RE.search(text):
        return False, "names function/class symbol"
    if _HTTP_VERB_RE.search(text):
        return False, "names HTTP verb + route"
    if _LIBRARY_NAME_RE.search(text):
        return False, "names specific library/framework"
    return True, ""


def _check_builder_method(text: str) -> tuple[bool, str]:
    """§self-check 3: builder-method-loose.

    Heuristic: explicit method-prescription phrases ("must use X",
    "by calling Y", "by importing Z") signal method-prescription
    rather than outcome. "via" alone is NOT flagged — "via the audit
    trail" is a perfectly fine outcome statement; only "via <code-
    like-symbol>" is implementation-shaped, and that's caught by §2.
    """
    bad = [
        "must use ", "by calling ", "by invoking ",
        "by importing ", "by extending ", "by inheriting ",
    ]
    lower = text.lower()
    for phrase in bad:
        if phrase in lower:
            return False, f"method-prescription phrase: {phrase!r}"
    return True, ""


def _check_observable_from_outside(text: str) -> tuple[bool, str]:
    """§self-check 4: observable from outside the codebase."""
    # Heuristic: internal-only language ("internally", "module-level",
    # "private", "stack", "memory") signals non-observable.
    bad = [
        "internally", "module-level", "private member", "private method",
        "private field", "memory layout", "stack frame", "in-memory only",
        "compiled", "during compile", "at parse time",
    ]
    lower = text.lower()
    for phrase in bad:
        if phrase in lower:
            return False, f"non-observable phrase: {phrase!r}"
    return True, ""


def _check_user_purpose(text: str) -> tuple[bool, str]:
    """§self-check 5: names purpose / value-to-someone."""
    # Outcome verbs OR purpose markers OR explicit user noun.
    if _OUTCOME_VERB_RE.search(text):
        return True, ""
    if _PURPOSE_RE.search(text):
        return True, ""
    return False, "no purpose marker / outcome verb"


_CHECKS: list[tuple[int, Any]] = [
    (1, _check_outcome_or_fact),
    (2, _check_implementation_swap),
    (3, _check_builder_method),
    (4, _check_observable_from_outside),
    (5, _check_user_purpose),
]


def _classify_text(text: str) -> tuple[str, int | None, str]:
    """Run §self-checks 1-5; return ``(classification, failed_check, reason)``.

    ``classification`` ∈ {"pass", "fail", "borderline"}.

    Borderline criterion: §self-check 5 (user-purpose) is the
    fuzziest; if 1-4 pass but 5 fails, classify as borderline rather
    than fail (LLM-as-judge gets the call). All other failures are
    "fail" outright.

    Failure-axis priority (when multiple checks fail): §2 > §1 > §3 >
    §4 > §5. §2 is the most specific signal (concrete file/line/
    library markers); §1 is a looser keyword heuristic. Picking the
    most-specific failure surfaces the strongest evidence of altitude
    drift to the decision tree (sub-plan-doc §3 AC.OBJX.8).
    """
    failures: list[tuple[int, str]] = []
    for n, fn in _CHECKS:
        ok, reason = fn(text)
        if not ok:
            failures.append((n, reason))
    if not failures:
        return "pass", None, ""
    # If the only failure is §5, this is borderline.
    if len(failures) == 1 and failures[0][0] == 5:
        return "borderline", 5, failures[0][1]
    # Otherwise prioritise the most-specific failure.
    priority_order = [2, 1, 3, 4, 5]
    by_n = {n: reason for n, reason in failures}
    for n in priority_order:
        if n in by_n:
            return "fail", n, by_n[n]
    # Unreachable — failures non-empty.
    n, reason = failures[0]
    return "fail", n, reason


# ====================================================================
# Decision tree
# ====================================================================


def _decide(
    classification: str,
    failed_check: int | None,
    *,
    band: str,
) -> tuple[str, str]:
    """Apply the §self-check decision tree per sub-plan-doc §3 + §7.

    Returns ``(decision, rationale)``.
    """
    if classification == "pass":
        return "keep", "all 5 self-checks passed"
    if classification == "borderline":
        # Borderline = §5-only failure; LLM-as-judge would adjudicate;
        # default to keep with downgrade if VERIFIED.
        if band == "VERIFIED":
            return "downgrade", (
                "borderline §5 user-purpose marker absent; "
                "downgrade VERIFIED→PLAUSIBLE"
            )
        return "keep", (
            "borderline §5 user-purpose; band already PLAUSIBLE/"
            "HYPOTHESISED — keep"
        )
    # fail — apply per-axis tree.
    if failed_check == 1:
        return "drop", "§1 fail — fact-as-objective; drop"
    if failed_check == 2:
        return "restate-as-capability", (
            "§2 fail — implementation-swap fail; restate as capability"
        )
    if failed_check == 3:
        return "downgrade", (
            "§3 fail — method-prescription; downgrade band"
        )
    if failed_check == 4:
        return "downgrade", (
            "§4 fail — non-observable; downgrade band"
        )
    if failed_check == 5:
        if band == "VERIFIED":
            return "drop", (
                "§5 fail at VERIFIED — purpose required; drop"
            )
        return "keep", (
            "§5 fail at non-VERIFIED — accept with rationale"
        )
    return "keep", "no decision rule matched (default-keep)"


# ====================================================================
# Public entry point
# ====================================================================


def validate_altitude(
    *,
    extraction_id: str,
    objectives: list[Objective],
    constraints: list[Constraint] | None = None,
    capabilities: list[Capability] | None = None,
    anthropic_client: Any | None = None,
    fail_threshold: float = 0.30,
) -> ValidationReport:
    """Run §self-checks 1-5 on every row; return :class:`ValidationReport`.

    Per AC.OBJX.8: programmatic heuristics + LLM-as-judge for
    borderline rows + decision tree on failure + drift-detection
    halt at >30% fail rate.

    The ``anthropic_client`` parameter is accepted but the v0.2.3
    Cycle 1 build uses programmatic-only adjudication (LLM-judge is
    a stub-extension point — Cycle 1 keeps cost bounded). When
    callers pass a client, the validator could in future delegate
    borderline rows to it; for now, programmatic heuristics gate
    every classification.

    Drift halt: when ``fail_count / total > fail_threshold``,
    ``drift_halt_triggered=True``. Caller surfaces, does not
    silently restart.
    """
    constraints = constraints or []
    capabilities = capabilities or []

    results: list[AltitudeCheckResult] = []
    pass_count = 0
    fail_count = 0
    borderline_count = 0
    dropped = 0
    downgraded = 0
    restated = 0

    def _process(
        row_id: str,
        kind: str,
        text: str,
        band: str,
    ) -> None:
        nonlocal pass_count, fail_count, borderline_count
        nonlocal dropped, downgraded, restated
        classification, failed_check, reason = _classify_text(text)
        decision, rationale = _decide(
            classification, failed_check, band=band
        )
        results.append(
            AltitudeCheckResult(
                row_id=row_id,
                row_kind=kind,  # type: ignore[arg-type]
                classification=classification,  # type: ignore[arg-type]
                failed_check=failed_check,
                decision=decision,  # type: ignore[arg-type]
                rationale=rationale or reason,
            )
        )
        if classification == "pass":
            pass_count += 1
        elif classification == "fail":
            fail_count += 1
        else:
            borderline_count += 1
        if decision == "drop":
            dropped += 1
        elif decision == "downgrade":
            downgraded += 1
        elif decision == "restate-as-capability":
            restated += 1

    for o in objectives:
        _process(o.objective_id, "objective", o.text, o.confidence.value)
    for k in constraints:
        _process(
            k.constraint_id, "constraint", k.text,
            ConfidenceBand.PLAUSIBLE.value,
        )
    for c in capabilities:
        # Capabilities aren't outcome-altitude; check is laxer (we
        # only flag drift-mode #4 / function-name-as-AC).
        _process(c.capability_id, "capability", c.text, "PLAUSIBLE")

    total = len(results)
    pass_rate = (pass_count / total) if total else 1.0
    fail_rate = (fail_count / total) if total else 0.0
    drift = fail_rate > fail_threshold

    return ValidationReport(
        extraction_id=extraction_id,
        total_rows=total,
        pass_count=pass_count,
        fail_count=fail_count,
        borderline_count=borderline_count,
        pass_rate=round(pass_rate, 4),
        dropped_count=dropped,
        downgraded_count=downgraded,
        restated_count=restated,
        drift_halt_triggered=drift,
        fail_threshold=fail_threshold,
        results=results,
    )
