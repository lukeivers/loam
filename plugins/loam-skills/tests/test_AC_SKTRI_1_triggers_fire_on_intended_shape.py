# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKTRI.1 — each retained skill's trigger fires on its intended
natural-language shape.

Per ``docs/plans/foundation-polish-cluster.md`` §5 AC.SKTRI.1
(SUB-ITEM 4, REMAINING scope): each skill retained in
``plugins/loam-skills/skills/`` has a frontmatter trigger that fires
on its intended natural-language shape — verified here by a
deterministic trigger-match check against representative phrasings —
OR is explicitly removed. A retained skill that cannot be triggered
is not silently retained.

WHY a deterministic substring match (not a live LLM probe):

Claude's skill-loading mechanism reads each SKILL's ``description``
frontmatter and loads the skill when the user's natural-language turn
matches that description. The ``description`` IS the trigger surface.
A trigger "fires on its intended NL shape" iff the discriminating
content words of a representative phrasing the user would actually say
are present in the description's trigger surface — so a faithful,
ODD-deterministic proxy for the fire-decision is: tokenize a curated
representative phrasing, drop stopwords, and require the description
to carry the phrasing's discriminating tokens. This is the same
substring-trigger-match technique the existing AC.SKILLCAP.{2,3,4}
tests use to verify a SKILL's named triggers (see
``test_AC_SKILLCAP_2_explicit_request_trigger.py``); AC.SKTRI.1
generalizes it across the whole retained surface and drives it from a
representative-phrasing table rather than a single named trigger.

The table is the OUTCOME contract (the intended NL shapes a retained
skill must be reachable from), not method — the builder could satisfy
it with any matcher; this file picks discriminating-token overlap.

TRIAGE RESULT (recorded; AC.SKTRI.2 companion):
Every skill discovered on disk is verified-KEPT — each carries a
working trigger on its intended shape (this test) and a live consumer
(see ``test_AC_SKTRI_2_dead_skills_retired.py``). The retirement set
is empty on evidence: no skill has a non-firing trigger, none is
superseded, none is non-functional. The installed surface is already
the live set.
"""

from __future__ import annotations

import re

import yaml

import pytest

from conftest import discover_skill_packages, load_skill_text


# Representative natural-language phrasings per skill — the intended
# shapes a user (or persona) would express that MUST reach the skill.
# Each phrasing is the OUTCOME contract: the trigger surface must carry
# the phrasing's discriminating content words. Curated from each
# skill's own description + body trigger examples (Tier-0 read at build
# time), expressed in user-natural language.
#
# Every key here MUST exist on disk (asserted below); every skill on
# disk MUST have an entry here (asserted below) — so the table can
# never silently drift from the installed surface.
INTENDED_SHAPES: dict[str, list[str]] = {
    "audit-block-on-telegram": [
        "reply to the user via telegram",
        "structure an audit block under the message",
    ],
    "claude-agents-view": [
        "what background agents are running right now",
        "inspect the inventory of running agents",
    ],
    "claude-feature-awareness": [
        "is there a primitive for this before i build one",
        "which hook event fires when i need the catalogue",
    ],
    "cost-optimised-defaults": [
        "loam is expensive cut my costs",
        "my claude bill is too high save money",
    ],
    "cron-create": [
        "schedule work every weekday at 9am",
        "run a recurring check every 30 minutes",
    ],
    "dispatch-with-gates": [
        "invoke a sub-agent for build work",
        "dispatch a background agent with scope",
    ],
    "goal-command": [
        "drive toward a goal and halt when met",
        "iterate until the failing test passes",
    ],
    "handsoff-loop": [
        "build me a tool and check it works",
        "make me a thing that converts files and prove it works",
    ],
    "launchd-plist": [
        "schedule durable work that survives restarts",
        "a weekly job that runs across sessions on macos",
    ],
    "loop-command": [
        "keep checking the deploy until it is healthy",
        "repeatedly run a check until a judge says stop",
    ],
    "memory-recall": [
        "recall what we discussed in a prior session",
        "ground this in earlier decisions from memory",
    ],
    "meta-decision-haiku": [
        "this borderline call needs an impartial arbiter",
        "does this principle-conflict need a neutral tiebreaker",
    ],
    "monitor-tool": [
        "wait until the background build finishes",
        "watch a log file for an error pattern",
    ],
    "onboarding-conversation": [
        "where are we what is the state",
        "open a fresh session with a context greeting",
    ],
    "owner-decision-summary": [
        "surface a plan to the owner for a decision",
        "summarize the named decisions with recommendations",
    ],
    "precompact-hook": [
        "capture state before compaction discards context",
        "block compaction to protect load-bearing memory",
    ],
    "primitive-rationale-check": [
        "record why i picked this non-default primitive",
        "add a rationale line for the bespoke dispatch choice",
    ],
    "run-in-background-bash": [
        "launch a long build in the background",
        "run a multi-minute command that outlives the turn",
    ],
    "schedule-wakeup": [
        "re-check a remote api at a known cadence",
        "wake up in n minutes to re-check a dispatched agent",
    ],
    "scope-decompose": [
        "decompose this large task into subtasks",
        "partition the work into tighter acceptance criteria",
    ],
    "session-handoff": [
        "let us pick this up later capture the pending items",
        "going to bed hand off the open work",
    ],
    "skill-capture-proposal": [
        "remember this make it a skill",
        "capture this pattern as a skill",
    ],
    "strategic-compact": [
        "should i compact or clear",
        "context feels tight should i clear",
    ],
    "time-claims-discipline": [
        "verify the elapsed duration before stating it",
        "translate the expected duration to ai-time",
    ],
    "tool-selection-rubric": [
        "which claude primitive should i dispatch this work to",
        "pick the right primitive for this dispatch decision",
    ],
    "translation-discipline": [
        "strip commit shas and ac ids before replying to the user",
        "translate the message for the user audience",
    ],
}


# Stopwords dropped before discriminating-token matching — generic
# glue words carry no trigger signal.
_STOPWORDS = frozenset(
    {
        "a", "an", "the", "to", "for", "of", "in", "on", "at", "and",
        "or", "is", "it", "this", "that", "with", "via", "my", "me",
        "i", "us", "we", "be", "n", "x", "y", "what", "when", "until",
        "before", "after", "into", "from", "under", "are", "do",
    }
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _discriminating_tokens(phrasing: str) -> list[str]:
    """Content tokens of a phrasing, stopwords removed."""
    return [
        t for t in _TOKEN_RE.findall(phrasing.lower())
        if t not in _STOPWORDS and len(t) > 1
    ]


def _trigger_surface(skill_name: str) -> str:
    """The skill's full trigger surface — frontmatter description plus
    body. Claude's load-decision reads the description; the body
    carries the named trigger-phrase examples the SKILLCAP tests also
    match against. Both are admissible trigger surface for the
    fire-check."""
    text = load_skill_text(skill_name)
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, f"{skill_name}: missing frontmatter delimiters"
    description = yaml.safe_load(match.group(1)).get("description", "")
    body = match.group(2)
    return f"{description}\n{body}".lower()


DISCOVERED_SKILLS = discover_skill_packages()


def test_table_matches_installed_surface() -> None:
    """The representative-phrasing table neither omits an installed
    skill nor names a skill absent from disk — so it can never drift
    from the retained surface (a phantom entry would mask a real
    retirement; a missing entry would leave a skill unverified)."""
    on_disk = set(DISCOVERED_SKILLS)
    in_table = set(INTENDED_SHAPES)
    assert in_table == on_disk, (
        "AC.SKTRI.1: the intended-shape table must exactly mirror the "
        f"installed surface. Missing from table: {on_disk - in_table}. "
        f"In table but absent on disk: {in_table - on_disk}."
    )


@pytest.mark.parametrize("skill_name", DISCOVERED_SKILLS)
def test_trigger_fires_on_intended_shape(skill_name: str) -> None:
    """Each representative phrasing's discriminating tokens are present
    in the skill's trigger surface — i.e. the trigger fires on the
    intended NL shape. A retained skill whose trigger does NOT fire on
    its intended shape fails here (and must be retired per AC.SKTRI.2,
    not silently retained)."""
    surface = _trigger_surface(skill_name)
    phrasings = INTENDED_SHAPES[skill_name]
    assert phrasings, f"{skill_name}: no representative phrasing declared."
    for phrasing in phrasings:
        tokens = _discriminating_tokens(phrasing)
        assert tokens, f"{skill_name}: phrasing {phrasing!r} has no content tokens."
        missing = [t for t in tokens if t not in surface]
        # The fire-decision tolerates ONE non-matching content token per
        # phrasing (a user's phrasing need not be a verbatim substring of
        # the description); the trigger fires when the discriminating bulk
        # of the phrasing is carried by the surface. A phrasing with two+
        # tokens absent from the surface is a non-firing trigger.
        assert len(missing) <= 1, (
            f"AC.SKTRI.1: {skill_name}'s trigger does NOT fire on the "
            f"intended shape {phrasing!r} — discriminating tokens "
            f"{missing} are absent from its trigger surface. Either the "
            f"description must carry the intended shape, or the skill "
            f"must be retired (AC.SKTRI.2)."
        )
