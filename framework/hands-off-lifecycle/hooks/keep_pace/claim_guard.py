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


# ====================================================================
# Decision-state assertions (AC.DCG.1–2 — memory recall cycle, Slice 5)
# ====================================================================
#
# The guard's ground truth WIDENS to the decision ledger: a draft
# asserting a question is OPEN / undecided / never-decided about a
# subject resolvable to a ``status: ruled`` decision record draws a
# model-facing steer carrying the record's ruling + source evidence —
# settled questions cannot be silently re-opened (the second half of
# the 2026-06-09 $750k failure surface). True decision-state claims
# (genuinely-open questions called open) and ordinary prose pass with
# no steer (AC.DCG.2). Same contracts as the work-state class:
# deterministic detection, steer-not-block, fail-open at the gate
# wrapper, NO LLM/API call.

# Open-state shapes: "is (still) an open question/decision/
# contradiction/item/issue", "remains undecided/unresolved/unsettled",
# "up in the air". Bare "is open" is NOT a decision-state claim (a
# door, a PR, a port can be open) — the open-noun or an
# undecided-class adjective is required.
_OPEN_STATE_RE = re.compile(
    r"\b(?:is|are|remains?|stays?)\s+(?:still\s+)?(?:an?\s+)?"
    r"(?:open\s+(?:question|item|decision|contradiction|issue)"
    r"|undecided|unresolved|unsettled|up\s+in\s+the\s+air)\b",
    re.IGNORECASE,
)

# Never-decided shapes: "we never decided", "was never decided",
# "hasn't been decided", "haven't decided", "no decision/ruling on X".
# "no decision needed/required" is NOT a decision-state claim (it
# asserts the absence of a question, not an open one).
_NEVER_DECIDED_RE = re.compile(
    r"\b(?:(?:we|you|i)\s+(?:have\s+)?never\s+decided"
    r"|was\s+never\s+decided"
    r"|has(?:n't| not)\s+been\s+decided"
    r"|have(?:n't| not)\s+decided"
    r"|no\s+(?:decision|ruling)\b(?!\s+(?:needed|required|necessary)))",
    re.IGNORECASE,
)

_SUBJECT_TOKEN_RE = re.compile(r"[A-Za-z0-9_$]+")


@dataclass(frozen=True)
class DecisionStateClaim:
    """One detected decision-state assertion (open/undecided/
    never-decided), scoped to its sentence like
    :class:`WorkStateClaim`."""

    subject: str
    snippet: str
    sentence: str


def detect_decision_state_claims(text: str) -> list[DecisionStateClaim]:
    """Deterministic decision-state detection (AC.DCG.1). Ordinary
    prose with no open/undecided assertion yields ``[]`` and no
    ledger query ever runs for it (AC.DCG.2)."""
    claims: list[DecisionStateClaim] = []
    for sentence in _SENTENCE_SPLIT_RE.split(text or ""):
        sentence = sentence.strip()
        if not sentence:
            continue
        for pat in (_OPEN_STATE_RE, _NEVER_DECIDED_RE):
            m = pat.search(sentence)
            if not m:
                continue
            subject = (
                sentence[: m.start()] + " " + sentence[m.end():]
            ).strip()
            claims.append(
                DecisionStateClaim(
                    subject=subject,
                    snippet=m.group(0),
                    sentence=sentence,
                )
            )
            break  # one decision-state claim per sentence
    return claims


def _default_ledger_query(subject: str) -> list[Any]:
    """The production decision-ledger ground truth: the persona's
    sealed ``search_decisions`` over the live workspace memory tree
    (resolved from the hook's runtime cwd — the same workspace-identity
    convention the gate's sibling hooks use). LAZY cross-component
    import per the D-KP9.1 hook discipline; failures propagate to the
    fail-open wrapper."""
    from pathlib import Path as _Path

    from loam.primary_persona.decision_ledger import (  # type: ignore[import-not-found]  # noqa: WPS433
        search_decisions,
    )
    from loam.primary_persona.file_memory import (  # type: ignore[import-not-found]  # noqa: WPS433
        memory_dir_for_workspace,
    )

    tokens = [t for t in _SUBJECT_TOKEN_RE.findall(subject) if len(t) > 1]
    if not tokens:
        return []
    return search_decisions(
        memory_dir_for_workspace(_Path.cwd()), tokens
    )


# --------------------------------------------------------------------
# Question-identity filter (AC.DCGID.1–4, dcg-question-identity-match;
# owner ruling D-DCGID.1) — contradiction-detection must match QUESTION
# IDENTITY, not shared claim-language.
# --------------------------------------------------------------------
#
# The pre-fix overlap counted EVERY shared declared-vocabulary token,
# so a genuinely-OPEN question false-positived against an UNRELATED
# ruled record on generic claim-language + a ubiquitous domain token
# (live-ledger Tier-0: the open "Which model runs substantive loam
# build work…" question resolved the unrelated FBM co-citation ruled
# record on {and, happens, loam, what}). The fix counts a shared token
# toward identity only when it is DISTINCTIVE: neither a generic
# stopword (AC.DCGID.1a) NOR corpus-ubiquitous (AC.DCGID.1b — its
# full-ledger declared-vocab document-frequency exceeds the ubiquity
# cutoff; this is what drops "loam" without hardcoding domain
# knowledge). Threshold stays >= 2 (AC.DCGID.2/.3); recall on real
# same-question reopens is preserved (their distinctive identity tokens
# survive both filters). Stopword set is domain-agnostic English
# function words + decision-state claim-language.

# AC.DCGID.1a — generic stopwords + decision-state claim-language that
# carry no question-identity signal. Domain-agnostic (no workspace
# nouns here — corpus-ubiquity, AC.DCGID.1b, handles domain tokens).
_IDENTITY_STOPWORDS: frozenset[str] = frozenset(
    {
        # English function words
        "the", "and", "what", "which", "on", "of", "to", "in", "an",
        "for", "is", "are", "was", "were", "be", "been", "it", "its",
        "that", "this", "our", "their", "his", "her", "both", "up",
        "see", "we", "you", "they", "do", "does", "did", "about",
        "how", "why", "when", "where", "who", "whom", "than", "with",
        "from", "as", "at", "or", "not", "no", "so", "but", "if", "by",
        "will", "would", "can", "could", "should", "has", "have", "had",
        "whether", "there", "here", "any", "all", "some", "more", "most",
        "into", "out", "over", "after", "before", "during", "then",
        "now", "also", "just", "only", "very", "really",
        # decision-state claim-language (the words the detector keys on —
        # never identity-bearing)
        "question", "questions", "undecided", "unresolved", "unsettled",
        "open", "still", "remains", "remain", "decided", "decision",
        "ruling", "happens", "happen", "happened",
    }
)

# AC.DCGID.1b — a token whose declared-vocab document-frequency across
# the full ledger is at or below this fraction of records is
# distinctive; above it the token is corpus-ubiquitous (e.g. "loam")
# and carries no question-identity signal.
_UBIQUITY_FRACTION = 0.4


def _ledger_corpus_frequency() -> dict[str, int]:
    """AC.DCGID.1b — declared-vocabulary document frequency over the
    FULL live ledger (entities + aliases + question + workstream of
    every non-superseded record). LAZY cross-component read per the
    D-KP9.1 hook discipline; any failure propagates to the fail-open
    wrapper (AC.DCGID.4 — a frequency-read error never blocks a send).
    Returns ``{token: record_count}`` plus a ``"__nrec__"`` total."""
    from pathlib import Path as _Path

    from loam.primary_persona.decision_ledger import (  # type: ignore[import-not-found]  # noqa: WPS433
        iter_decisions,
    )
    from loam.primary_persona.file_memory import (  # type: ignore[import-not-found]  # noqa: WPS433
        memory_dir_for_workspace,
    )

    freq: dict[str, int] = {}
    nrec = 0
    for rec in iter_decisions(memory_dir_for_workspace(_Path.cwd())):
        if getattr(rec, "status", "") == "superseded":
            continue
        nrec += 1
        for tok in _record_declared_tokens(rec):
            freq[tok] = freq.get(tok, 0) + 1
    freq["__nrec__"] = nrec
    return freq


def _record_declared_tokens(record: Any) -> set:
    """The record's DECLARED vocabulary (entities + aliases + question +
    workstream) as a lowercased >=2-char token set — the encode-time
    index the ledger's design makes load-bearing."""
    declared: set = set()
    for field in ("entities", "aliases"):
        for value in getattr(record, field, ()) or ():
            declared |= {
                t.lower()
                for t in _SUBJECT_TOKEN_RE.findall(str(value))
                if len(t) > 1
            }
    for field in ("question", "workstream"):
        declared |= {
            t.lower()
            for t in _SUBJECT_TOKEN_RE.findall(
                str(getattr(record, field, "") or "")
            )
            if len(t) > 1
        }
    return declared


def _distinctive_tokens(
    tokens: set, corpus_frequency: Optional[dict[str, int]]
) -> set:
    """AC.DCGID.1 — keep only identity-bearing tokens: drop generic
    stopwords (1a) and corpus-ubiquitous tokens (1b). When
    ``corpus_frequency`` is ``None`` (no ledger reachable) only the
    stopword filter applies — fail-soft toward the prior behaviour for
    the ubiquity leg, never raising."""
    out = {t for t in tokens if t not in _IDENTITY_STOPWORDS}
    if not corpus_frequency:
        return out
    nrec = corpus_frequency.get("__nrec__", 0)
    if nrec <= 0:
        return out
    cutoff = _UBIQUITY_FRACTION * nrec
    return {t for t in out if corpus_frequency.get(t, 0) <= cutoff}


def _reopened_ruling_steer(
    claim: DecisionStateClaim, record: Any
) -> ClaimSteer:
    """AC.DCG.1 — the steer carries the ruling + its source evidence
    (model-facing; the user never sees this text)."""
    return ClaimSteer(
        label="decision-claim-contradicts-ledger",
        detail=(
            f"draft asserts {claim.snippet!r} (in: {claim.sentence!r}) "
            f"but the decision ledger holds a RULED record: "
            f"question {record.question!r}; ruling {record.ruling!r}; "
            f"source {record.source!r} — this question is settled; "
            f"cite the ruling instead of re-opening it."
        ),
    )


def check_decision_claims(
    text: str,
    *,
    ledger_query: Optional[Callable[[str], list[Any]]] = None,
) -> list[ClaimSteer]:
    """Verify decision-state assertions against the decision ledger
    (AC.DCG.1–2). A claim whose subject resolves to a ``status:
    ruled`` record steers with the ruling + source; a genuinely-open
    subject (``status: open`` record, or no record at all) passes —
    the guard fires ONLY on re-opened settled questions. Boundary
    errors propagate to the gate's fail-open envelope; no LLM/API
    call (the send hot path)."""
    claims = detect_decision_state_claims(text)
    if not claims:
        return []
    query_fn = ledger_query if ledger_query is not None else _default_ledger_query
    # AC.DCGID.1b — full-ledger declared-vocab document frequency for
    # the ubiquity filter. Fail-soft (AC.DCGID.4): an unreachable ledger
    # yields None so the identity filter degrades to the stopword leg
    # rather than raising into the send path. The production read is
    # used unless a test seam overrode the query (synthetic ledger ⇒ no
    # live corpus available, stopword leg suffices for the seam tests).
    corpus_frequency: Optional[dict[str, int]] = None
    if ledger_query is None:
        try:
            corpus_frequency = _ledger_corpus_frequency()
        except BaseException:  # noqa: BLE001 — AC.DCGID.4 fail-soft
            corpus_frequency = None
    steers: list[ClaimSteer] = []
    for claim in claims:
        if not claim.subject.strip():
            continue
        subject_tokens = {
            t.lower()
            for t in _SUBJECT_TOKEN_RE.findall(claim.subject)
            if len(t) > 1
        }
        records = list(query_fn(claim.subject) or ())
        # Best-match-first (the search is score-ordered): when the
        # subject's best-resolving record is OPEN, the question is
        # genuinely open — pass, even if a weaker ruled record shares
        # a stray token (the live-ledger FP shape caught at build
        # time: "activation timing" resolving a different ruled
        # record on the single common token "activation").
        for record in records:
            overlap = _declared_vocab_overlap(
                record, subject_tokens, corpus_frequency=corpus_frequency
            )
            # AC.DCGID.1–3 — "resolvable to" requires >= 2 QUESTION-
            # IDENTITY (distinctive) token matches: a generic-claim-
            # language or ubiquitous-token brush is not resolution; a
            # shared DISTINCTIVE-token cluster (a real same-question
            # reopen) still clears the bar.
            if overlap < 2:
                continue
            if getattr(record, "status", "") == "ruled":
                steers.append(_reopened_ruling_steer(claim, record))
            break  # the best real resolution decides; open => pass
    return steers


def _declared_vocab_overlap(
    record: Any,
    subject_tokens: set,
    *,
    corpus_frequency: Optional[dict[str, int]] = None,
) -> int:
    """AC.DCGID.1 — QUESTION-IDENTITY overlap: distinct DISTINCTIVE-token
    matches between the subject and the record's DECLARED vocabulary
    (entities + aliases + question + workstream — the encode-time index,
    per the ledger's design). A token counts only when it survives the
    identity filter (:func:`_distinctive_tokens`): not a generic
    stopword (1a) and not corpus-ubiquitous (1b). ``corpus_frequency``
    ``None`` degrades to the stopword leg only (fail-soft, AC.DCGID.4)."""
    declared = _record_declared_tokens(record)
    shared = declared & subject_tokens
    return len(_distinctive_tokens(shared, corpus_frequency))


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
