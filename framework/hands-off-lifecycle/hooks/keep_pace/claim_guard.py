# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Claim-vs-stored-state guard (FBM correctness cycle, Slice 2 —
AC.CLG.1–4).

The live layer the roadmap's MM1 named for the KP9 draft-gate seam:
when an outbound draft asserts WORK-STATE — positive ("X is
built/sealed/shipped") or NEGATIVE ("X isn't planned / doesn't
exist") — this module verifies the assertion against ground truth
(the Slice-1 plan-state query, which itself rides the git ref graph)
and produces a MODEL-FACING steer naming the claim AND the
contradicting evidence before the draft is sent (D2 ★: STEER, never
block).

Detection is DETERMINISTIC-ONLY (D4 — a small assertion grammar over
the work-state vocabulary; no LLM, no API call, anywhere in the send
path). The grammar is deliberately NARROW: it targets claims about
plans/builds/seals, not general fact-checking — precision is a
first-class AC (AC.CLG.3: true claims + ordinary prose pass
un-steered; alarm fatigue defeats the guard as surely as silence).

Verification semantics (each branch maps to a named AC):

  * NEGATIVE claim, subject resolves to stored state → CONTRADICTION
    steer carrying the plan's real identity + build-state + seal
    evidence (AC.CLG.1). For a negative about EXISTENCE/PLANNING any
    match contradicts (a plan-doc exists); for a negative about BUILD
    ("isn't built/sealed") only build evidence contradicts — a plan
    with no build evidence makes "isn't built" TRUE, so it passes.
  * NEGATIVE EXISTENCE claim, subject resolves to NOTHING → the
    scoped-honest steer (AC.CLG.2): prompt the "not found in
    <searched>; <unsearched> unchecked" form instead of a bare
    eternal negative. Ordinary unresolvable prose is not steered
    (no claim detected → no query → no steer).
  * POSITIVE claim the ground truth CONFIRMS → pass, no steer
    (AC.CLG.3). A positive BUILD claim is contradicted only when
    every resolved match has NO build evidence (claims built, ground
    truth shows zero apply/seal commits — the clear over-claim);
    a partially-built match passes (evidence exists; flagging the
    approximately-right claim is the alarm-fatigue failure mode).
  * Any internal error (import failure, query failure) → the CALLER
    fails open (AC.CLG.4): :func:`check_claims` lets boundary errors
    propagate to the gate's fail-open envelope; the gate yields PASS.

Cross-component reach: the ground-truth query is a LAZY import of the
primary-persona plan-state surface inside the call (the same
fail-soft discipline ``user_prompt_submit.py``'s contributors use —
D-KP9.1 self-containment: no import-time cross-component dependency
in a live hook). Stdlib-only at module level.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable, Optional


# ====================================================================
# Detection — the deterministic work-state assertion grammar (D4)
# ====================================================================

# The work-state vocabulary. BUILD-class terms assert build progress;
# the EXISTENCE class asserts that a plan/decision exists at all.
_BUILD_TERMS = (
    "planned",
    "built",
    "sealed",
    "shipped",
    "published",
    "merged",
    "implemented",
)
_TERMS_ALT = "|".join(_BUILD_TERMS)

# Negative shapes (the 2026-06-09 class — "wasn't planned"):
#   is not / isn't / was never / has not been + <work-state term>
#   there is no plan / no plan exists / no plan for / no record of
#   doesn't exist / never existed
_NEG_PATTERNS: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    (
        "neg-verb",
        re.compile(
            r"\b(?:is|are|was|were|has|have)\s+(?:not|never)\s+"
            rf"(?:been\s+)?(?:{_TERMS_ALT})\b",
            re.IGNORECASE,
        ),
    ),
    (
        "neg-contraction",
        re.compile(
            r"\b(?:isn't|aren't|wasn't|weren't|hasn't|haven't)\s+"
            rf"(?:been\s+)?(?:{_TERMS_ALT})\b",
            re.IGNORECASE,
        ),
    ),
    (
        "neg-never",
        re.compile(rf"\bnever\s+(?:{_TERMS_ALT})\b", re.IGNORECASE),
    ),
    (
        "neg-no-plan",
        re.compile(
            r"\b(?:there\s+(?:is|are|was|were)\s+no\s+"
            r"(?:plan|plans|decision|record)s?\b"
            r"|no\s+(?:plan|plans|decision|record)s?\s+"
            r"(?:exists?|existed|for|of|on\s+file)\b)",
            re.IGNORECASE,
        ),
    ),
    (
        "neg-not-exist",
        re.compile(
            r"\b(?:doesn't|does\s+not|didn't|did\s+not)\s+exist\b"
            r"|\bnever\s+existed\b",
            re.IGNORECASE,
        ),
    ),
)

# Positive shapes ("X is built / has been sealed / was shipped"):
_POS_PATTERNS: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    (
        "pos-verb",
        re.compile(
            rf"\b(?:is|are|was|were)\s+(?:already\s+)?(?:{_TERMS_ALT})\b",
            re.IGNORECASE,
        ),
    ),
    (
        "pos-perfect",
        re.compile(
            rf"\b(?:has|have)\s+(?:already\s+)?been\s+(?:{_TERMS_ALT})\b",
            re.IGNORECASE,
        ),
    ),
)

# Existence-class detector: a negative claim is the canonical
# ETERNAL-NEGATIVE shape (AC.CLG.2 fires on unresolvable subjects)
# when it denies PLANNING or EXISTENCE — not when it denies build
# progress (an unverifiable "isn't built yet" is not the poison shape).
_EXISTENCE_RE = re.compile(
    r"\bplanned\b|\bexist|\bno\s+(?:plan|plans|decision|record)\b"
    r"|\bthere\s+(?:is|are|was|were)\s+no\b",
    re.IGNORECASE,
)

# Sentence splitter — the claim's subject is scoped to its sentence.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


@dataclass(frozen=True)
class WorkStateClaim:
    """One detected work-state assertion.

    ``polarity``        — ``"positive"`` / ``"negative"``.
    ``subject``         — the claim's sentence minus the matched claim
                          span (the topic the query resolves).
    ``snippet``         — the matched assertion text (for the steer).
    ``sentence``        — the full sentence (for the steer's context).
    ``existence_class`` — True when a negative claim denies existence/
                          planning (the AC.CLG.2 eternal-negative
                          shape).
    """

    polarity: str
    subject: str
    snippet: str
    sentence: str
    existence_class: bool


@dataclass(frozen=True)
class ClaimSteer:
    """One model-facing steer (label + detail). The gate wraps these
    into its ``GateReason`` shape; this module stays import-light so
    the gate's lazy sibling import cannot cycle."""

    label: str
    detail: str


def detect_work_state_claims(text: str) -> list[WorkStateClaim]:
    """Detect work-state assertions in ``text`` (AC.CLG.1 detection —
    deterministic, D4; one claim per matched assertion, scoped to its
    sentence). Ordinary prose with no work-state assertion yields
    ``[]`` (AC.CLG.3 — and no ground-truth query ever runs for it)."""
    claims: list[WorkStateClaim] = []
    for sentence in _SENTENCE_SPLIT_RE.split(text or ""):
        sentence = sentence.strip()
        if not sentence:
            continue
        matched_spans: list[tuple[int, int]] = []

        def _scan(
            patterns: tuple[tuple[str, "re.Pattern[str]"], ...],
            polarity: str,
        ) -> None:
            for _label, pat in patterns:
                for m in pat.finditer(sentence):
                    span = (m.start(), m.end())
                    # A span already claimed by an earlier (more
                    # specific) pattern is not re-reported.
                    if any(
                        s < span[1] and span[0] < e
                        for s, e in matched_spans
                    ):
                        continue
                    matched_spans.append(span)
                    snippet = m.group(0)
                    subject = (
                        sentence[: span[0]] + " " + sentence[span[1]:]
                    ).strip()
                    claims.append(
                        WorkStateClaim(
                            polarity=polarity,
                            subject=subject,
                            snippet=snippet,
                            sentence=sentence,
                            existence_class=(
                                polarity == "negative"
                                and bool(_EXISTENCE_RE.search(snippet))
                            ),
                        )
                    )

        # Negative patterns scan FIRST: "is not planned" must claim its
        # span before the positive "is … planned" shape could (the
        # positive grammar requires the term adjacent to the verb, but
        # span-priority keeps the rule airtight).
        _scan(_NEG_PATTERNS, "negative")
        _scan(_POS_PATTERNS, "positive")
    return claims


# ====================================================================
# Verification — ground truth via the Slice-1 plan-state query
# ====================================================================


def _default_query(topic: str) -> dict[str, Any]:
    """The production ground-truth query: the Slice-1 plan-state
    surface (which consumes the loam-cli git-derived index). LAZY
    cross-component import per the D-KP9.1 hook discipline; an
    import/runtime failure propagates to the gate's fail-open
    envelope (AC.CLG.4)."""
    from loam.primary_persona.keep_pace.plans_state import (  # type: ignore[import-not-found]  # noqa: WPS433
        query_plan_state,
    )

    return query_plan_state(topic)


def _has_build_evidence(match: dict[str, Any]) -> bool:
    return str(match.get("build_state", "")) in (
        "sealed",
        "partially-sealed",
    )


def _evidence_line(match: dict[str, Any]) -> str:
    """One ground-truth evidence line for a steer (model-facing —
    slugs/SHAs are allowed here per AC.KP9.4; the user never sees
    this text)."""
    title = str(match.get("title", "") or match.get("slug", ""))
    state = str(match.get("build_state", ""))
    evidence = tuple(match.get("seal_evidence", ()) or ())
    tail = f"; evidence: {evidence[0]}" if evidence else ""
    return f"{title!r} is on file with build-state {state}{tail}"


def _contradiction_steer(
    claim: WorkStateClaim, matches: list[dict[str, Any]]
) -> ClaimSteer:
    """AC.CLG.1 — the steer names the claim AND the contradicting
    evidence (the reconciliation memory: evidence, not authority, is
    what resolves the conflict)."""
    cited = "; ".join(_evidence_line(m) for m in matches[:2])
    return ClaimSteer(
        label="claim-contradicts-stored-state",
        detail=(
            f"draft asserts {claim.snippet!r} (in: {claim.sentence!r}) "
            f"but ground truth shows {cited} — verify against the real "
            f"records (plan-docs + git) before asserting."
        ),
    )


def _scoped_negative_steer(
    claim: WorkStateClaim, result: dict[str, Any]
) -> ClaimSteer:
    """AC.CLG.2 — an unresolvable flat negative gets the warning
    light: prompt the scoped-honest form, never a silent pass."""
    searched = ", ".join(result.get("searched", ())) or "no surface"
    unsearched = ", ".join(result.get("unsearched", ()))
    return ClaimSteer(
        label="unverified-flat-negative",
        detail=(
            f"draft makes a flat negative existence claim "
            f"({claim.snippet!r} in: {claim.sentence!r}) that could not "
            f"be resolved against ground truth — state it scoped "
            f"(searched: {searched}) and name what was NOT checked "
            f"({unsearched}) instead of a bare 'doesn't exist'."
        ),
    )


def check_claims(
    text: str,
    *,
    query: Optional[Callable[[str], dict[str, Any]]] = None,
) -> list[ClaimSteer]:
    """Verify every detected work-state claim against ground truth and
    return the model-facing steers (AC.CLG.1–3).

    ``query`` is the test seam; production lazy-imports the Slice-1
    plan-state query. Boundary errors (import failure, query failure)
    PROPAGATE — the gate's fail-open envelope converts them to a PASS
    verdict (AC.CLG.4); this function adds no LLM/API call (D4).
    """
    claims = detect_work_state_claims(text)
    if not claims:
        return []
    query_fn = query if query is not None else _default_query
    steers: list[ClaimSteer] = []
    for claim in claims:
        if not claim.subject.strip():
            # A claim with no extractable subject is unverifiable
            # against any topic — ordinary prose protection (AC.CLG.3).
            continue
        result = query_fn(claim.subject)
        matches = list(result.get("matches", ()) or ())
        if claim.polarity == "negative":
            if claim.existence_class:
                if matches:
                    steers.append(_contradiction_steer(claim, matches))
                else:
                    steers.append(_scoped_negative_steer(claim, result))
            else:
                # Build-class negative ("isn't built/sealed"):
                # contradicted only by real build evidence; a
                # no-evidence match makes the claim TRUE → pass.
                contradicted = [m for m in matches if _has_build_evidence(m)]
                if contradicted:
                    steers.append(
                        _contradiction_steer(claim, contradicted)
                    )
        else:
            # Positive claim: contradicted only when the subject
            # resolves AND every match lacks build evidence (claims
            # built/sealed, ground truth shows none). Confirmed or
            # unresolved positives pass (AC.CLG.3 precision).
            if matches and not any(_has_build_evidence(m) for m in matches):
                if claim.snippet.lower().endswith("planned"):
                    # "X is planned" + a plan-doc on file = CONFIRMED
                    # (existence is the claim; the doc is the proof).
                    continue
                steers.append(_contradiction_steer(claim, matches))
    return steers
