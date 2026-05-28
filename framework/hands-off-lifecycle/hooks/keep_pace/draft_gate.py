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

"""KP9 — the abstraction-voice + constraint-check draft-to-send gate.

This is the structural fix for the two recurring outbound failures the
keep-pace design names (design §1 fix #2):

  - **The jargon / mechanism leak** — a user-facing reply that surfaces
    a file path, a ``.md`` name, an internal ID, a commit SHA, a §-doc
    pointer, or an un-introduced ALLCAPS token. The persona is a
    translation layer (CLAUDE.md Lens 2); a leak is a translation
    failure. The per-prompt read-hook (KP1) structurally cannot catch
    this — it runs BEFORE the reply is generated.
  - **The mid-draft self-contradiction** — a reply about to contradict
    an on-file rule/fact while actively working on the related topic.
    This is tonight's failure. KP1 raises the probability the right
    memory is in context; it cannot check the GENERATED text. KP9
    Layer C does (design §1 fix #2 — "the catch the prompt-hook
    structurally cannot make").

Two deterministic layers (no judge — the post-MVP KP10 ``claude -p``
register judge attaches at the reserved pre-filter hook-point, Surface
#4):

  - **Layer 1 — jargon / abstraction-voice lint** (AC.KP9.1). Reuses
    the deterministic jargon-leak logic established in
    ``handsoff_loop.intake`` (the AC.PBF.3 token-boundary discipline)
    EXTRACTED here (D-KP9.1: extract a self-contained module, do NOT
    import across the component boundary from a live hook, and do NOT
    mutate the translation-discipline SKILL), extended to the
    abstraction-first default the SKILL names: file paths, ``.md`` /
    source-file names, AC-IDs, commit SHAs, §-doc pointers, and
    un-introduced ALLCAPS internal tokens.

  - **Layer C — draft-vs-active-constraint check** (AC.KP9.2). Flags a
    draft that contradicts an active high-salience constraint-memory.
    Per RF-4 the active-constraint set is scoped NARROW for the MVP
    (D-KP9.2): the explicitly-tagged seeded canon rules + sealed
    rulings in :data:`SEEDED_CONSTRAINTS`, NOT the whole corpus.
    Over-flagging is fail-open (annoying, non-blocking); a missed
    contradiction re-arms tonight's failure, so the narrow set is
    chosen for precision and expanded only when KP10's judge lands.

The gate routes EVERY user-facing surface (AC.KP9.3) — persona
free-text, drift proposals, the SessionStart summary, any
miss-recovery — via :func:`gate`, which takes the draft + a surface
kind. Gate feedback is MODEL-FACING ONLY (AC.KP9.4): the block/flag
reasons are returned for the model/hook stderr, never rendered as a
user-visible "your reply was blocked" message (that itself is a
mechanism leak). The gate FAILS OPEN: any internal error yields a
PASS verdict so a broken gate can never block a send (composes with
the chain's fail-open-whole-chain guarantee, AC.KP0.4 / AC.KP.S.1).

Stdlib-only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional


# ====================================================================
# Verdict model
# ====================================================================


class Verdict(str, Enum):
    """The gate's three outcomes.

    - ``PASS``  — the draft is clean; send it.
    - ``BLOCK`` — a Layer 1 deterministic jargon/leak class is present;
      the draft must not be sent to the user as-is (it leaks internal
      mechanism). Deterministic, low-risk.
    - ``FLAG``  — a Layer C draft-vs-constraint contradiction is
      detected; surface it model-facing so the draft is corrected
      before send. Higher-risk relevance judgement on a
      deterministic-only budget; fail-open if uncertain.
    """

    PASS = "pass"
    BLOCK = "block"
    FLAG = "flag"


@dataclass
class GateReason:
    """One model-facing reason the gate did not pass a draft.

    ``layer`` is ``"L1"`` (jargon lint) or ``"LC"`` (constraint check);
    ``label`` names the leak class or the violated constraint;
    ``detail`` is the model-facing explanation (NEVER user-rendered —
    AC.KP9.4).
    """

    layer: str
    label: str
    detail: str


@dataclass
class GateResult:
    """The gate outcome for one draft (AC.KP9.4 — model-facing only).

    ``verdict`` is the worst outcome across both layers (BLOCK beats
    FLAG beats PASS). ``reasons`` carry the model-facing explanations.
    ``blocked()`` / ``flagged()`` / ``passed()`` are convenience
    predicates. ``model_facing_report()`` renders the reasons for the
    model / hook stderr — it is NEVER shown to the user.
    """

    verdict: Verdict
    reasons: list[GateReason] = field(default_factory=list)

    def passed(self) -> bool:
        return self.verdict == Verdict.PASS

    def blocked(self) -> bool:
        return self.verdict == Verdict.BLOCK

    def flagged(self) -> bool:
        return self.verdict == Verdict.FLAG

    def model_facing_report(self) -> str:
        """Render reasons for the MODEL (stderr / hook reason).

        AC.KP9.4: this is model-facing only. The user never sees it —
        a "your reply was blocked by the register judge" string would
        itself be the mechanism leak this gate exists to prevent.
        """
        if not self.reasons:
            return ""
        head = {
            Verdict.BLOCK: "[keep-pace draft-gate] BLOCK — rewrite before send:",
            Verdict.FLAG: "[keep-pace draft-gate] FLAG — check before send:",
            Verdict.PASS: "[keep-pace draft-gate] notes:",
        }[self.verdict]
        lines = [head]
        for r in self.reasons:
            lines.append(f"  - ({r.layer}/{r.label}) {r.detail}")
        return "\n".join(lines)


# ====================================================================
# Layer 1 — deterministic jargon / abstraction-voice lint (AC.KP9.1)
# ====================================================================
#
# D-KP9.1: the jargon-leak logic is EXTRACTED here (a self-contained
# module in the hook home) rather than imported from
# ``handsoff_loop.intake`` — a live session hook must not take a
# cross-component runtime import that could fail to load and wedge the
# turn, and the translation-discipline SKILL is prose (not importable).
# The pattern shapes mirror ``intake._JARGON_PATTERNS`` (the AC.PBF.3
# token-boundary discipline: match a genuine jargon TOKEN, never a
# naive substring inside an ordinary word) and EXTEND it to the
# abstraction-first leak classes the translation-discipline SKILL
# names: file paths, source/`.md` file names, AC-IDs, commit SHAs,
# §-doc pointers, and un-introduced ALLCAPS internal tokens.
#
# Neither ``intake.py`` nor the SKILL is mutated (§15 backwards-compat).

_LAYER1_PATTERNS: tuple[tuple[str, "re.Pattern[str]"], ...] = (
    # --- abstraction-first leak classes (the SKILL's anti-pattern list) ---
    # Absolute / home / repo-relative file paths ("/Users/...", a
    # "framework/.../x.py" path). A path is never the user-facing answer
    # (SKILL item 5) — behaviour first, path as parenthetical reference.
    (
        "file-path",
        re.compile(
            r"(?:^|\s|`)(?:/|~/|\./)?(?:[\w.-]+/){1,}[\w.-]+"
            r"\.(?:py|md|json|ya?ml|txt|sh|toml|cfg|ini|sqlite)\b"
        ),
    ),
    # Absolute filesystem path even without an extension ("/Users/foo/bar").
    ("abs-path", re.compile(r"(?:^|\s|`)(?:/Users/|/home/|~/)[\w./-]+")),
    # A bare source/`.md` file name ("file_memory.py", "OBJECTIVES.md",
    # "settings.json") — a file name pretending to be the answer
    # (SKILL items 5 + 6).
    (
        "file-name",
        re.compile(
            r"\b[\w-]+\.(?:py|md|json|ya?ml|toml|cfg|ini|sqlite)\b"
        ),
    ),
    # Acceptance-ID token (AC.KP9.1, AC.PBF.3) — the real ID shape, NOT
    # the bare "ac." ending an ordinary word ("Mac."). Mirrors
    # intake._JARGON_PATTERNS exactly.
    ("ac-id", re.compile(r"\bAC\.[A-Za-z0-9]")),
    # Bare commit SHA — a 7-40 char hex run presented as reference the
    # user must look up (SKILL item 1). Matched as a standalone hex
    # token so ordinary words / decimals do not trip.
    ("commit-sha", re.compile(r"(?<![\w.])[0-9a-f]{7,40}(?![\w.])")),
    # §-doc pointer ("see §14", "§3.5") — a pointer demanding a click
    # instead of carrying the answer (SKILL item 3).
    ("doc-section-pointer", re.compile(r"§\s*\d")),
    # --- the loam-process jargon tokens (mirrored from intake.py,
    #     token-boundary discipline) ---
    ("acceptance-criterion",
     re.compile(r"\bacceptance criteri(?:on|a)\b", re.IGNORECASE)),
    ("pytest", re.compile(r"\bpytest\b", re.IGNORECASE)),
    ("exit-code", re.compile(r"\bexit code\b", re.IGNORECASE)),
    ("manifest", re.compile(r"\bmanifest\b", re.IGNORECASE)),
    # `seal` in its loam amendment/manifest/commit collocation, NOT the
    # ordinary English verb ("seal the envelope") — mirrors intake.py.
    ("seal",
     re.compile(
         r"\bseal(?:s|ed|ing)?\b[\s\w]{0,24}"
         r"\b(?:amendment|manifest|commit|component|cycle)\b"
         r"|\b(?:amendment|manifest|component|cycle)\s+seal",
         re.IGNORECASE)),
    ("ODD", re.compile(r"\bODD\b")),
    ("machine-checkable",
     re.compile(r"\bmachine[- ]checkable\b", re.IGNORECASE)),
    # Internal scoring / mechanism tokens the SessionStart self-report
    # must not surface (AC.KP7.3 composes on this): "w_s", "ARC-promoted",
    # "objective-match", "additionalContext", "BM25", "FTS5".
    ("internal-mechanism",
     re.compile(
         r"\b(?:w_[a-z]|ARC-promoted|objective-match|additionalContext"
         r"|BM25|FTS5|additional_context)\b")),
    # Loam-internal abbreviations the SKILL flags (F3/F4/M5/M-FBM/FIDRAFT)
    # when un-introduced — an un-spelled internal acronym token.
    ("internal-abbrev",
     re.compile(r"\b(?:M-FBM|FIDRAFT|M5|F[0-9])\b")),
)

# Common ALLCAPS words that are ordinary English, not internal tokens —
# these never trip the un-introduced-ALLCAPS class.
_ALLCAPS_ALLOWLIST: frozenset[str] = frozenset(
    {
        "I", "A", "OK", "TLDR", "TL", "DR", "FAQ", "ASAP", "FYI",
        "AM", "PM", "USA", "UK", "EU", "US", "ID", "OS", "URL", "API",
        "PDF", "HTML", "CSS", "JSON", "YAML", "CLI", "AI", "UTC", "CDT",
        "CST", "EST", "PST", "AKA", "ETA", "DIY", "TBD", "NA", "NASA",
        "RSVP", "VIP", "PIN", "ATM", "GPS", "FBI", "CEO", "CTO", "HR",
    }
)

# An ALLCAPS run of >=2 letters (optionally with digits / underscores).
_ALLCAPS_RE = re.compile(r"\b[A-Z][A-Z0-9_]{1,}\b")


def _allcaps_leaks(text: str) -> list[str]:
    """Return un-introduced ALLCAPS internal tokens in ``text``.

    An ALLCAPS token is a leak unless it is in the ordinary-English
    allowlist. This is the SKILL's "abbreviations unfamiliar to the
    user / un-introduced internal tokens" class made deterministic.
    First-occurrence-deduped.
    """
    hits: list[str] = []
    seen: set[str] = set()
    for m in _ALLCAPS_RE.finditer(text):
        tok = m.group(0)
        if tok in _ALLCAPS_ALLOWLIST or tok in seen:
            continue
        # An all-digit run can't reach here (\b[A-Z] anchor), but guard
        # tokens that are a single allowlisted letter + digits ("A1").
        seen.add(tok)
        hits.append(tok)
    return hits


def layer1_lint(text: str) -> list[GateReason]:
    """Layer 1 — deterministic jargon / abstraction-voice lint.

    AC.KP9.1: returns one :class:`GateReason` per leak class present
    (file path, ``.md``/source file name, AC-ID, commit SHA, §-pointer,
    loam-process jargon, internal mechanism token, un-introduced
    ALLCAPS). An empty list means the draft is clean at Layer 1.

    Deterministic + token-boundary (AC.PBF.3 discipline): an ordinary
    word that merely contains a forbidden substring does NOT trip.
    """
    reasons: list[GateReason] = []
    for label, pat in _LAYER1_PATTERNS:
        m = pat.search(text)
        if m:
            reasons.append(
                GateReason(
                    layer="L1",
                    label=label,
                    detail=(
                        f"draft surfaces an internal {label} token "
                        f"({m.group(0).strip()!r}) the user did not ask "
                        f"for — translate to plain language (answer "
                        f"first, artefact as optional reference)."
                    ),
                )
            )
    for tok in _allcaps_leaks(text):
        reasons.append(
            GateReason(
                layer="L1",
                label="un-introduced-allcaps",
                detail=(
                    f"draft surfaces an un-introduced internal token "
                    f"{tok!r} — spell it out in plain language on first "
                    f"use or drop it."
                ),
            )
        )
    return reasons


# ====================================================================
# Layer C — draft-vs-active-constraint check (AC.KP9.2)
# ====================================================================
#
# D-KP9.2 / RF-4: the active-constraint set is scoped NARROW for the
# MVP — the explicitly-tagged seeded canon rules + sealed rulings
# below, NOT the whole corpus. A constraint is a positive ASSERTION
# (the thing that is true on file) plus the set of tokens that signal a
# draft is TALKING ABOUT that assertion (``topic_tokens``) and the set
# of tokens whose presence near a negation indicates the draft is
# CONTRADICTING it (``violation_tokens``). The contradiction test is
# deterministic: the draft must be on-topic AND assert the negated form
# of the constraint.
#
# This mirrors KP5's ``SEEDED_OBJECTIVES`` posture (in-source seed,
# expanded later) — it is the small, precision-first set RF-4
# recommends. Over-flag is fail-open; the narrow set keeps false
# positives low while still catching the seeded tonight-failure case.


@dataclass
class Constraint:
    """One active high-salience constraint-memory (canon rule / ruling).

    ``slug``           — scope-descriptive id of the rule.
    ``assertion``      — the thing that is true on file (plain text).
    ``topic_tokens``   — the draft must mention >=1 of these to be
                         "about" this constraint (lowercased).
    ``correct_value``  — the value the draft SHOULD carry for the keyed
                         fact (lowercased token(s)).
    ``violation_values`` — values that CONTRADICT ``correct_value`` for
                         the same keyed fact (lowercased). A draft
                         on-topic that asserts one of these (and NOT the
                         correct value) is flagged.
    ``kind``           — ``"canon"`` (a litrpg canon rule) or
                         ``"ruling"`` (a sealed loam ruling).
    """

    slug: str
    assertion: str
    topic_tokens: tuple[str, ...]
    correct_value: tuple[str, ...]
    violation_values: tuple[str, ...]
    kind: str = "canon"


# The seeded narrow active-constraint set (RF-4). These are the
# explicitly-tagged canon rules + sealed rulings — the precision-first
# floor. Expanded only when KP10's judge lands. The litrpg canon rule
# below is the seeded tonight-failure case AC.KP9.2 exercises (a draft
# placing Aaron at his own pod contradicts the canon rule that Aaron is
# at Priya's pod — the exact ch1->ch2 continuity rule recently sealed in
# the litrpg workstream).
SEEDED_CONSTRAINTS: tuple[Constraint, ...] = (
    Constraint(
        slug="litrpg-aaron-at-priyas-pod",
        assertion=(
            "In the LitRPG continuity, Aaron works at Priya's pod, not his "
            "own pod (chapter-1 to chapter-2 continuity)."
        ),
        topic_tokens=("aaron", "pod"),
        correct_value=("priya", "priya's"),
        violation_values=("his own", "own pod", "aaron's pod", "his pod"),
        kind="canon",
    ),
    Constraint(
        slug="litrpg-no-metaphysical-overreach-personification",
        assertion=(
            "LitRPG prose must not personify abstractions with "
            "metaphysical-overreach (e.g. 'the silence was older than "
            "them') — a sealed editor catch class."
        ),
        topic_tokens=("silence", "darkness", "void", "time", "space"),
        correct_value=(),
        violation_values=("was older", "remembered", "knew", "wanted",
                          "decided", "chose"),
        kind="canon",
    ),
    Constraint(
        slug="loam-no-anthropic-api-key",
        assertion=(
            "Every loam LLM call goes through the claude subscription "
            "subprocess; there is NO Anthropic API key and no pip-installed "
            "anthropic SDK (sealed ruling)."
        ),
        topic_tokens=("anthropic", "api", "llm", "model", "claude"),
        correct_value=("subscription", "subprocess"),
        violation_values=("api key", "api_key", "anthropic sdk",
                          "pip install anthropic", "ANTHROPIC_API_KEY"),
        kind="ruling",
    ),
)


_NEGATION_NEAR = re.compile(
    r"\b(?:not|no|never|isn't|aren't|wasn't|doesn't|don't|won't|can't)\b",
    re.IGNORECASE,
)


def _mentions_any(text_low: str, tokens: tuple[str, ...]) -> bool:
    return any(t in text_low for t in tokens if t)


def layerC_check(
    text: str,
    constraints: Optional[tuple[Constraint, ...]] = None,
) -> list[GateReason]:
    """Layer C — flag a draft that contradicts an active constraint.

    AC.KP9.2: a draft that is ON-TOPIC for a seeded constraint (mentions
    one of its ``topic_tokens``) AND asserts a ``violation_value`` for
    the keyed fact — while NOT carrying the ``correct_value`` — is
    flagged. A draft that carries the correct value, or never touches
    the topic, passes.

    D-KP9.2 / RF-4: the constraint set is the narrow seeded set
    (precision-first). Returns one :class:`GateReason` per violated
    constraint. Deterministic.
    """
    cset = constraints if constraints is not None else SEEDED_CONSTRAINTS
    low = text.lower()
    reasons: list[GateReason] = []
    for c in cset:
        if not _mentions_any(low, c.topic_tokens):
            continue
        carries_correct = _mentions_any(low, c.correct_value)
        asserts_violation = _mentions_any(low, c.violation_values)
        if not asserts_violation:
            # For the personification class the violation tokens are
            # verbs that only contradict when applied to the abstraction
            # (topic mentioned + violation verb present). Already handled
            # by asserts_violation. If neither correct nor violation
            # value appears, the draft is on-topic but not asserting the
            # keyed fact — no contradiction.
            continue
        if carries_correct and c.correct_value:
            # The draft carries the correct value; a stray violation
            # token (e.g. quoting the rule itself) is not a contradiction.
            continue
        reasons.append(
            GateReason(
                layer="LC",
                label=c.slug,
                detail=(
                    f"draft appears to contradict an on-file {c.kind} "
                    f"rule: {c.assertion} — re-check before send."
                ),
            )
        )
    return reasons


# ====================================================================
# The gate (AC.KP9.3 routes every surface; AC.KP9.4 fail-open)
# ====================================================================


# Surface kinds the gate routes (AC.KP9.3) — every user-facing surface,
# not just persona free-text. The kind is advisory (the same two layers
# run for all); it is recorded for the model-facing report + future
# per-surface tuning.
SURFACE_KINDS: frozenset[str] = frozenset(
    {
        "persona-free-text",
        "drift-proposal",
        "session-start-summary",
        "miss-recovery",
    }
)


def gate(
    draft: str,
    *,
    surface_kind: str = "persona-free-text",
    constraints: Optional[tuple[Constraint, ...]] = None,
) -> GateResult:
    """Run the draft-to-send gate over ``draft`` (AC.KP9.1-.4).

    Routes EVERY user-facing surface (AC.KP9.3) — ``surface_kind`` names
    which one (advisory; the same two layers run for all). Runs Layer 1
    (jargon lint) then Layer C (constraint check). The verdict is the
    worst outcome: BLOCK (any Layer 1 leak) > FLAG (any Layer C
    contradiction) > PASS.

    FAIL-OPEN (AC.KP9.4 / AC.KP.S.1): any internal error yields a PASS —
    a broken gate must NEVER block a send. The block/flag reasons are
    model-facing only (see :meth:`GateResult.model_facing_report`); the
    user never sees a "your reply was blocked" message (that itself is a
    mechanism leak).
    """
    try:
        if not isinstance(draft, str):
            return GateResult(verdict=Verdict.PASS)
        l1 = layer1_lint(draft)
        lc = layerC_check(draft, constraints=constraints)
        reasons = l1 + lc
        if l1:
            verdict = Verdict.BLOCK
        elif lc:
            verdict = Verdict.FLAG
        else:
            verdict = Verdict.PASS
        return GateResult(verdict=verdict, reasons=reasons)
    except BaseException:  # noqa: BLE001 — fail-open; never block a send
        return GateResult(verdict=Verdict.PASS)


# ====================================================================
# Post-MVP KP10 pre-filter hook-point (Surface #4 — reserved, not built)
# ====================================================================


def is_plausibly_technical(draft: str) -> bool:
    """Cheap deterministic pre-filter for the post-MVP KP10 judge.

    Surface #4: the Layer-2 ``claude -p`` register judge (post-MVP
    KP10) runs ONLY when this cheap pre-filter flags the draft as
    plausibly-technical, then fails open + logs to tune. KP9 reserves
    this hook-point so KP10 attaches without re-wiring; KP9 itself does
    NOT call a judge. A draft is "plausibly technical" if Layer 1 found
    any leak OR the draft mentions a constraint topic — the cheap signal
    that a semantic judge might be worth its cost.
    """
    try:
        if layer1_lint(draft):
            return True
        low = draft.lower()
        for c in SEEDED_CONSTRAINTS:
            if _mentions_any(low, c.topic_tokens):
                return True
        return False
    except BaseException:  # noqa: BLE001 — fail-open: never claim technical on error
        return False


# ====================================================================
# KP0-chain PreToolUse contributor (STAGED live wiring import target)
# ====================================================================


# Tool names whose payload carries an outbound user-facing draft the
# gate routes (AC.KP9.3). The live wiring resolves the draft text from
# the matching tool's input. STAGED — the registration onto the KP0
# PreToolUse chain is part of the GATED live wiring (RF-6), NOT done in
# this cycle.
USER_FACING_TOOL_HINTS: tuple[str, ...] = (
    "reply",      # mcp telegram reply
    "send",       # generic send surfaces
    "create_draft",
)


def _extract_draft_from_envelope(envelope: dict) -> tuple[str, str]:
    """Best-effort extract (draft_text, surface_kind) from a PreToolUse
    envelope. Returns ("", kind) when no user-facing draft is present.

    Fail-soft: any shape mismatch yields an empty draft (the contributor
    then no-ops, the turn proceeds). Stdlib-only.
    """
    try:
        tool_name = str(envelope.get("tool_name", "") or "").lower()
        tool_input = envelope.get("tool_input")
        if not isinstance(tool_input, dict):
            return "", "persona-free-text"
        is_user_facing = any(h in tool_name for h in USER_FACING_TOOL_HINTS)
        if not is_user_facing:
            return "", "persona-free-text"
        # Common draft-carrying fields across reply/send/draft tools.
        for key in ("message", "text", "body", "content", "reply"):
            val = tool_input.get(key)
            if isinstance(val, str) and val.strip():
                return val, "persona-free-text"
        return "", "persona-free-text"
    except BaseException:  # noqa: BLE001 — fail-soft
        return "", "persona-free-text"


def build_draft_gate_contributor() -> Callable[[dict], Optional[str]]:
    """Return the KP0 PreToolUse-chain ``Contributor.fn``-compatible
    callable (shape ``fn(envelope: dict) -> Optional[str]``).

    The STAGED live wiring registers this on the
    ``framework/hands-off-lifecycle/hooks/keep_pace/pre_tool_use.py``
    ``contributors()`` list — that registration is the GATED live step
    (RF-6), NOT done in this cycle.

    The contributor extracts any outbound user-facing draft from the
    PreToolUse envelope and runs the gate. On BLOCK/FLAG it returns the
    MODEL-FACING report (AC.KP9.4) for the chain to surface to the model
    (stderr / additionalContext), NEVER a user-visible message. On PASS
    (or no draft) it returns ``None`` (silent). Fail-soft: any error
    yields ``None`` so the chain's fail-open guarantee holds.
    """

    def contributor(envelope: dict) -> Optional[str]:
        try:
            if not isinstance(envelope, dict):
                return None
            draft, surface_kind = _extract_draft_from_envelope(envelope)
            if not draft.strip():
                return None
            result = gate(draft, surface_kind=surface_kind)
            if result.passed():
                return None
            return result.model_facing_report() or None
        except BaseException:  # noqa: BLE001 — fail-soft; chain fail-open
            return None

    return contributor
