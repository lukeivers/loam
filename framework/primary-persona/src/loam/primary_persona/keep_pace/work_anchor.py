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
        Surface #7: the objective tokens are weighted EQUALLY with the
        others — they are merged into one OR-token set, not boosted.
        """
        merged: list[str] = []
        seen: set[str] = set()

        def _extend(text: str) -> None:
            for tok in tokenize(text):
                if tok not in seen:
                    seen.add(tok)
                    merged.append(tok)

        _extend(self.prompt)
        for obj in self.objective_texts:
            _extend(obj)
        for sg in self.subgoals:
            # Subgoal slugs are hyphen/underscore-joined; tokenize
            # splits them into their words.
            _extend(sg.replace("-", " ").replace("_", " "))
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
