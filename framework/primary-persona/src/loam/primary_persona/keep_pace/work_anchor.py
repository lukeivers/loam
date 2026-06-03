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

"""KP1 — the work-anchored retrieval key.

This is the load-bearing correction (design §1 fix #1): the retrieval
key is NOT the typed prompt alone. It is the **work-anchored key** —

    prompt + active-objective text + active-subgoal + last-turn topic

— so a vague prompt ("continue the batch", "keep going") still
retrieves against the live WORK via the objective anchor (the term the
bare prompt cannot supply). This is the direct fix for tonight's
failure: the persona forgetting on-file context while actively working
on the related topic.

Key construction (AC.KP1.2):
  - all four components contribute to the query when present;
  - the query degrades gracefully (still functions) when a component
    is absent — e.g. no last-turn topic on the first turn, or a prompt
    that is itself vague (the objective anchor carries it).

Term-weighting (Surface #7 / D-KP1.2): the objective term is weighted
EQUALLY with the other three anchor terms at MVP (one BM25 OR-token
set), NOT dominantly — ``w_s`` rotation-capping is a post-MVP KP4
concern. If objective-term over-domination is observed in smoke the
builder down-weights and records; none observed at build.

Trivial-prompt skip (AC.KP1.4): greetings / acks / bare confirmations
are skipped (no retrieval, no noise). A genuinely vague-but-working
prompt ("continue") is NOT trivial — it carries work intent and the
objective anchor is exactly what rescues it.

Stdlib-only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# Reuse the FTS tokenization discipline established in
# ``file_memory._tokenize_for_fts`` (token-level sanitization,
# OR-of-tokens, min-len 2, stopword drop) — KP1's corpus index uses
# the same FTS5 query shape, so the same tokenizer keeps them aligned.
_TOKEN_CONTENT_RE = re.compile(r"[A-Za-z0-9_]+")

_STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "of", "to", "in", "on", "for", "at", "by",
        "is", "are", "was", "were", "be", "do", "does", "did",
        "what", "how", "this", "that", "it", "and", "or", "with",
    }
)


# AC.RQ80.1 (#80 anchor-flood de-flood) — the PROMPT-RELATIVE anchor cap. The
# prompt tokens (the user's topical signal) are NEVER capped — always included
# in full; the standing-context ANCHOR (objective + subgoal) is bounded so it
# stops FLOODING the OR-query and crowding the focused topical rule out of the
# top-5. Measured (Tier-0, live pos3 corpus): an 8-token topical prompt became
# an 80-token query (72 generic objective words), letting every objective-
# mentioning omnibus doc match on every turn and burying the focused rule at
# rank ~12-14.
#
# The cap is PROMPT-RELATIVE because the anchor's job changes with prompt
# strength: a RICH topical prompt needs the anchor TIGHT (the prompt carries
# retrieval; the anchor must not flood); a VAGUE prompt ("continue the batch")
# needs the anchor LOOSER (the anchor is the ONLY retrieval signal — the
# AC.KP1.6 cold-walk rescue). So the anchor budget is:
#
#     anchor_cap = max(MIN_ANCHOR_FLOOR, MAX_QUERY_TOKENS - len(prompt_tokens))
#
# A rich 8-token prompt → max(4, 10-8) = 4 anchor tokens (de-flooded; live P@5
# 0.0 → 0.133). A vague 2-token prompt → max(4, 10-2) = 8 anchor tokens (the
# objective anchor still surfaces the litrpg canon doc — AC.KP1.6 preserved).
# The anchor is CAPPED, NOT DELETED (AC.RQ80.3): MIN_ANCHOR_FLOOR keeps >= 1
# anchor token present whenever the anchor has tokens. The cap is drawn
# ROUND-ROBIN across anchor components so every component contributes its
# leading token first (AC.KP1.2 graceful degradation). NAMED, tunable constants:
# raising MAX_QUERY_TOKENS or MIN_ANCHOR_FLOOR re-admits more anchor (the flood)
# — reversibility; MIN_ANCHOR_FLOOR is the lower rail that forbids deleting the
# anchor.
MAX_QUERY_TOKENS = 10
MIN_ANCHOR_FLOOR = 4


def tokenize(text: str) -> list[str]:
    """Token-sanitize ``text`` into the FTS5 OR-token survivors.

    Same discipline as ``file_memory._tokenize_for_fts``: split on
    whitespace, extract alnum/_ runs per token, lowercase, drop
    len<2, drop stopwords, dedupe preserving first-occurrence order.
    """
    survivors: list[str] = []
    seen: set[str] = set()
    for ws_token in text.split():
        for run in _TOKEN_CONTENT_RE.findall(ws_token):
            tok = run.lower()
            if len(tok) < 2 or tok in _STOPWORDS or tok in seen:
                continue
            seen.add(tok)
            survivors.append(tok)
    return survivors


# ---- trivial-prompt detection (AC.KP1.4) ---------------------------

# Bare social / acknowledgement prompts that carry no work intent.
# Matched on the WHOLE normalised prompt (not a substring) so "continue"
# is never trivial — it carries work intent the objective anchor
# rescues (the AC.KP1.6 case).
_TRIVIAL_WHOLE: frozenset[str] = frozenset(
    {
        "hi", "hey", "hello", "yo", "sup",
        "thanks", "thank you", "ty", "thx",
        "ok", "okay", "k", "kk", "cool", "nice", "great", "good",
        "yes", "no", "yep", "nope", "yeah", "sure",
        "got it", "gotcha", "understood", "ack", "noted",
        "lol", "haha", "nvm",
        "bye", "cya", "later", "gn", "good night", "morning",
    }
)


def is_trivial_prompt(prompt: str) -> bool:
    """``True`` when ``prompt`` is a greeting / ack / bare confirmation.

    AC.KP1.4: a trivial prompt is skipped (no retrieval). Detection is
    on the normalised whole prompt — lowercased, stripped of trailing
    punctuation/emoji-ish runs — so "Thanks!" / "ok." are caught but
    "continue the batch" (work intent) is not. A vague-but-working
    "continue" / "keep going" is deliberately NOT trivial (AC.KP1.6).
    """
    norm = prompt.strip().lower()
    # Strip trailing punctuation runs ("ok!!", "thanks.").
    norm = re.sub(r"[\s\.\!\?\,\;\:]+$", "", norm).strip()
    if not norm:
        return True
    return norm in _TRIVIAL_WHOLE


# ---- the work-anchored key (AC.KP1.2) ------------------------------


@dataclass
class WorkAnchor:
    """The four work-anchored key components (AC.KP1.2).

    Any component may be empty; the key degrades gracefully (the
    surviving components still form a query). ``objective_texts`` and
    ``subgoals`` are read fresh from the OBJECTIVES register each turn
    (AC.KP5.5 binding); ``last_topic`` is the prior turn's topic the
    caller threads in (empty on the first turn).
    """

    prompt: str
    objective_texts: list[str] = field(default_factory=list)
    subgoals: list[str] = field(default_factory=list)
    last_topic: str = ""

    def query_tokens(self) -> list[str]:
        """Build the deduped OR-token query from all four components.

        AC.KP1.2: every present component contributes its tokens; an
        absent component contributes nothing (graceful degradation).

        AC.RQ80.1 (#80 anchor-flood de-flood): the PROMPT + LAST-TOPIC
        tokens (the user's topical signal) are always included in full;
        the ANCHOR tokens (objective + subgoal — the standing-context
        rotation key) are CAPPED to the leading :data:`MAX_ANCHOR_TOKENS`
        distinct survivors so the standing objective vocabulary stops
        FLOODING the OR-query and crowding the focused topical rule out
        of the top-5. The anchor is bounded, NOT deleted (AC.RQ80.3):
        when the anchor has tokens, >= 1 survives, so the AC.KP1.6
        vague-"continue" objective-rescue still fires.
        """
        merged: list[str] = []
        seen: set[str] = set()

        def _extend(text: str) -> None:
            for tok in tokenize(text):
                if tok not in seen:
                    seen.add(tok)
                    merged.append(tok)

        # Prompt tokens — the user's topical signal — are NEVER capped.
        _extend(self.prompt)
        prompt_token_count = len(merged)

        # Anchor tokens (objective + subgoal) — the standing-context
        # rotation key — are CAPPED so they do not flood the query
        # (AC.RQ80.1). The cap is PROMPT-RELATIVE: a rich prompt leaves a
        # small anchor budget (de-flood); a vague prompt leaves a larger
        # budget (the anchor is the only retrieval signal). The budget is
        # drawn ROUND-ROBIN across the anchor components (each objective
        # text + each subgoal) so that, when the cap is reached, EVERY
        # component still contributes its leading token(s) before any
        # single component's tail consumes the budget — preserving the
        # AC.KP1.2 "every present component contributes" graceful-
        # degradation invariant. Anchor token order within the merged
        # query is otherwise not load-bearing (the corpus index OR-joins
        # the set).
        anchor_cap = max(
            MIN_ANCHOR_FLOOR, MAX_QUERY_TOKENS - prompt_token_count
        )
        anchor_seen: set[str] = set(seen)
        component_token_lists: list[list[str]] = []
        for obj in self.objective_texts:
            component_token_lists.append(tokenize(obj))
        for sg in self.subgoals:
            # Subgoal slugs are hyphen/underscore-joined; tokenize
            # splits them into their words.
            component_token_lists.append(
                tokenize(sg.replace("-", " ").replace("_", " "))
            )

        anchor_added = 0
        round_idx = 0
        while anchor_added < anchor_cap and component_token_lists:
            progressed = False
            for toks in component_token_lists:
                if round_idx >= len(toks):
                    continue
                progressed = True
                tok = toks[round_idx]
                if tok not in anchor_seen:
                    anchor_seen.add(tok)
                    if tok not in seen:
                        seen.add(tok)
                        merged.append(tok)
                        anchor_added += 1
                        if anchor_added >= anchor_cap:
                            break
            if not progressed:
                break
            round_idx += 1

        # Last-turn topic (the continuity signal) is also a topical
        # signal the bare prompt may lack — included in full like the
        # prompt, after the bounded anchor.
        _extend(self.last_topic)
        return merged

    def components_present(self) -> dict[str, bool]:
        """Which of the four key components contributed tokens.

        AC.KP1.2 verification surface: a test asserts all four
        contribute when present and the query still functions when one
        is absent.
        """
        return {
            "prompt": bool(tokenize(self.prompt)),
            "objective": any(tokenize(o) for o in self.objective_texts),
            "subgoal": any(
                tokenize(sg.replace("-", " ").replace("_", " "))
                for sg in self.subgoals
            ),
            "last_topic": bool(tokenize(self.last_topic)),
        }
