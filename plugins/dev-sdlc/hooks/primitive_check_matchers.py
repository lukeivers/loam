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

"""Matcher data for the dispatch-time primitive-check guard
(claude-leverage program, DOCTRINE slice, D-DOC.4).

Each row pairs a deterministic regex that detects a bespoke-equivalent
work-shape in a dispatch prompt with:

  * ``corpus_entry`` — the path of the capability-corpus entry naming
    the native primitive the bespoke shape re-implements. This is a
    POINTER, not a capability claim: the row carries NO facts about the
    primitive, only the path where the facts live (the corpus is the
    single refresh-kept claims surface — D-CLP.5 lesson).
  * ``primitive`` — the short native-primitive name, used only to phrase
    the deny/warn reason and the one-line fix. Not a capability claim;
    a label.
  * ``tier`` — ``"deny"`` for a high-precision bespoke-build match
    (build-verb + primitive-shape), ``"warn"`` for a lower-confidence
    match. Two-tier posture per D-DOC.2.

The fire path reads NO files and makes NO network/LLM call — it runs
these compiled regexes against the prompt string. The corpus is
consulted at TEST time by the coverage guard (AC.CLP-DOC.8), never at
fire time (AC.CLP-DOC.7). The coverage guard asserts every
``corpus_entry`` here resolves to a real file and every ``claude-code/``
corpus entry is either covered by a row here or named in
``COVERAGE_EXCLUSIONS`` — so a refresh-added corpus entry without
coverage turns the dev-sdlc suite red rather than drifting silently.

Stdlib only (re).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# The capability-corpus root, relative to the repo root. The coverage
# guard resolves rows against ``<repo>/<CORPUS_CLAUDE_CODE_DIR>``.
CORPUS_CLAUDE_CODE_DIR = "docs/capability-corpus/claude-code"


@dataclass(frozen=True)
class MatcherRow:
    """One bespoke-equivalent detection row.

    ``pattern`` is a compiled, case-insensitive regex. ``corpus_entry``
    is the workspace-relative path of the corpus entry this row points
    at. ``primitive`` is the native-primitive label for the reason
    text. ``tier`` is ``"deny"`` or ``"warn"``.
    """

    name: str
    pattern: re.Pattern
    corpus_entry: str
    primitive: str
    tier: str


def _c(pattern: str) -> re.Pattern:
    return re.compile(pattern, re.IGNORECASE)


# Bespoke-build verbs — the dispatch is asking an agent to CONSTRUCT
# something (not merely use it). A bespoke-equivalent match requires a
# build verb co-occurring with a primitive-shape pattern, so that
# "use the schedule primitive" does NOT match while "build a scheduler"
# does. The verb set is a non-capturing alternation reused across rows.
_BUILD_VERB = (
    r"(?:build|write|implement|create|author|roll\s+(?:my|your|our)\s+own|"
    r"hand-?roll|make|construct|set\s+up|design|code\s+up|stand\s+up)"
)


# The matcher rows. Each ``deny`` row is build-verb + primitive-shape
# in proximity; each ``warn`` row is the primitive-shape alone (lower
# confidence — the dispatch mentions the shape but may not be building
# a bespoke equivalent).
ROWS: tuple[MatcherRow, ...] = (
    # --- schedule.md : bespoke scheduler / cron / recurring-remote ---
    MatcherRow(
        name="bespoke-scheduler",
        pattern=_c(
            _BUILD_VERB
            + r"\b[^.\n]{0,40}\b(?:scheduler|cron(?:\s*job)?|"
            + r"recurring\s+(?:task|job|agent)|scheduled\s+(?:task|job))"
        ),
        corpus_entry=f"{CORPUS_CLAUDE_CODE_DIR}/schedule.md",
        primitive="/schedule (scheduled remote routine)",
        tier="deny",
    ),
    MatcherRow(
        name="scheduler-shape",
        pattern=_c(
            r"\b(?:cron(?:\s*job)?|recurring\s+(?:task|job)|"
            r"every\s+(?:day|week|morning|monday|hour|night)\b)"
        ),
        corpus_entry=f"{CORPUS_CLAUDE_CODE_DIR}/schedule.md",
        primitive="/schedule (scheduled remote routine)",
        tier="warn",
    ),
    # --- loop.md : bespoke polling / cadence loop ---
    MatcherRow(
        name="bespoke-poll-loop",
        pattern=_c(
            _BUILD_VERB
            + r"\b[^.\n]{0,40}\b(?:poll(?:ing)?\s+loop|"
            + r"(?:re-?check|poll)[^.\n]{0,30}\bevery\b[^.\n]{0,20}"
            + r"(?:minute|hour|second)|cadence\s+loop|"
            + r"loop\s+that\s+(?:re-?checks|polls|re-?runs))"
        ),
        corpus_entry=f"{CORPUS_CLAUDE_CODE_DIR}/loop.md",
        primitive="/loop (in-session recurring execution)",
        tier="deny",
    ),
    MatcherRow(
        name="poll-loop-shape",
        pattern=_c(
            r"\b(?:keep\s+(?:checking|polling)|poll\s+(?:for|every)|"
            r"re-?check[^.\n]{0,20}\bevery\b)"
        ),
        corpus_entry=f"{CORPUS_CLAUDE_CODE_DIR}/loop.md",
        primitive="/loop (in-session recurring execution)",
        tier="warn",
    ),
    # --- goal.md : bespoke keep-going / drive-to-goal loop ---
    # The keep-going work-shape /goal covers: drive a single task to a
    # checkable success predicate and halt when met. The deny row is
    # build-verb + a keep-going-shape phrase in proximity; the warn row
    # is the keep-going shape alone (D-ADOPT.2 two-tier posture). The
    # keep-going lexicon is deliberately NARROW — it requires an
    # explicit drive-to-done / keep-going-until / re-run-until /
    # continuation-loop / Stop-hook-re-fire phrase, NOT a bare "loop"
    # (which would over-match the /loop and orchestrator shapes the
    # sibling rows already cover, and flag every loop in prose). The
    # cadence "loop" shape stays the loop.md rows' jurisdiction; this
    # row keys on the halt-on-checkable-outcome shape /goal uniquely
    # expresses.
    MatcherRow(
        name="bespoke-keep-going-loop",
        pattern=_c(
            _BUILD_VERB
            + r"\b[^.\n]{0,40}\b(?:"
            + r"keep[\s-]+going[^.\n]{0,20}until|"
            + r"drives?[^.\n]{0,20}\bto[\s-]+(?:done|goal|completion|"
            + r"a[\s-]+(?:passing|checkable|success))|"
            + r"re-?run[^.\n]{0,20}until[^.\n]{0,20}(?:done|pass|green)|"
            + r"(?:iterate|loop)[^.\n]{0,20}until[^.\n]{0,20}"
            + r"(?:the[\s-]+)?(?:test|check|build|goal|predicate)|"
            + r"continuation[\s-]+(?:loop|driver)|"
            + r"stop[\s-]+hook[^.\n]{0,20}re-?fires?|"
            + r"drive-?to-?(?:goal|done|outcome)[\s-]+(?:loop|driver))"
        ),
        corpus_entry=f"{CORPUS_CLAUDE_CODE_DIR}/goal.md",
        primitive="/goal (drive-to-checkable-outcome with autonomous halt)",
        tier="deny",
    ),
    MatcherRow(
        name="keep-going-shape",
        pattern=_c(
            r"\b(?:keep[\s-]+going[^.\n]{0,20}until|"
            r"drive[\s-]+(?:it[\s-]+)?to[\s-]+(?:done|goal|completion)|"
            r"re-?run[^.\n]{0,20}until[^.\n]{0,20}(?:done|pass|green)|"
            r"iterate[^.\n]{0,20}until[^.\n]{0,20}"
            r"(?:the[\s-]+)?(?:test|check|build|goal|passes?))"
        ),
        corpus_entry=f"{CORPUS_CLAUDE_CODE_DIR}/goal.md",
        primitive="/goal (drive-to-checkable-outcome with autonomous halt)",
        tier="warn",
    ),
    # --- background-agents.md : bespoke orchestrator / dispatch loop ---
    MatcherRow(
        name="bespoke-orchestrator",
        pattern=_c(
            _BUILD_VERB
            + r"\b[^.\n]{0,40}\b(?:orchestrator|dispatch\s+loop|"
            + r"(?:sub-?)?agent\s+(?:pool|manager|spawner|queue)|"
            + r"background[\s-]+(?:task\s+)?(?:runner|manager|queue))"
        ),
        corpus_entry=f"{CORPUS_CLAUDE_CODE_DIR}/background-agents.md",
        primitive="background-agent dispatch (Task / run_in_background / Monitor)",
        tier="deny",
    ),
    MatcherRow(
        name="background-watch-shape",
        pattern=_c(
            r"\b(?:wait\s+until[^.\n]{0,30}(?:finishes|completes|done)|"
            r"watch[^.\n]{0,20}(?:log|process|output)\s+(?:for|until)|"
            r"stream[^.\n]{0,20}events)"
        ),
        corpus_entry=f"{CORPUS_CLAUDE_CODE_DIR}/background-agents.md",
        primitive="background-agent dispatch (Task / run_in_background / Monitor)",
        tier="warn",
    ),
    # --- hooks.md : bespoke lifecycle interception ---
    MatcherRow(
        name="bespoke-lifecycle-interceptor",
        pattern=_c(
            _BUILD_VERB
            + r"\b[^.\n]{0,40}\b(?:lifecycle\s+(?:interceptor|handler)|"
            + r"(?:custom\s+)?(?:tool-?call|session|prompt)\s+interceptor|"
            + r"wrapper\s+that\s+(?:fires|intercepts|runs)\s+(?:before|after)\b)"
        ),
        corpus_entry=f"{CORPUS_CLAUDE_CODE_DIR}/hooks.md",
        primitive="Claude Code hook event (settings.json-registered handler)",
        tier="deny",
    ),
    MatcherRow(
        name="lifecycle-shape",
        pattern=_c(
            r"\b(?:fire\s+(?:a\s+)?handler\s+(?:before|after|when)|"
            r"intercept\s+(?:every|each)\s+(?:tool|prompt|session))"
        ),
        corpus_entry=f"{CORPUS_CLAUDE_CODE_DIR}/hooks.md",
        primitive="Claude Code hook event (settings.json-registered handler)",
        tier="warn",
    ),
)


# Corpus entries deliberately NOT covered by a matcher row, each with a
# named reason. The coverage guard (AC.CLP-DOC.8) admits an uncovered
# ``claude-code/`` corpus entry ONLY if it appears here — otherwise the
# suite goes red. Empty today: all four current ``claude-code/`` entries
# (hooks, loop, schedule, background-agents) have rows above.
COVERAGE_EXCLUSIONS: dict[str, str] = {}


def all_corpus_entries_referenced() -> set[str]:
    """The set of corpus-entry paths referenced by ROWS."""
    return {row.corpus_entry for row in ROWS}
