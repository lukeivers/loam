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

"""AC.CLP-ADOPT.3 — a cadence-shaped in-session request routes to
``/loop`` per the catalogue, observable in the skill record.

Per D-ADOPT.3: ``/loop``'s adoption surface is the EXISTING catalogue —
the ``loop-command`` SKILL (the trigger surface Claude reads to load the
skill) + the ``docs/capability-corpus/claude-code/loop.md`` corpus entry
(the refresh-kept claims surface). NO new ``/loop`` mechanism is built
in Slice 3; this test verifies the catalogue routing works: a
cadence-shaped request reaches ``/loop`` and the corpus entry carries
the ``/goal`` sibling-disambiguation Slice 3 added (so the persona
consulting the catalogue can tell ``/loop`` from ``/goal``).

The routing check is a deterministic trigger-match (the same technique
the AC.SKTRI.1 / AC.SKILLCAP tests use): a cadence-shaped phrasing's
discriminating content words must be present in the ``loop-command``
trigger surface — i.e. the trigger fires on the cadence shape. This is
an ODD-deterministic proxy for Claude's load-decision (the description
IS the trigger surface), not a live LLM probe.

The "observable in the skill record" requirement is satisfied two ways,
both checked here: (1) the routing is observable in the ``loop-command``
SKILL's trigger surface (the cadence phrasing reaches it); (2) the
``loop.md`` corpus entry — the catalogue the persona consults — now
names ``/goal`` as the sibling, so the routing decision (loop vs goal)
is observable in the catalogue record.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from conftest import load_skill_text


REPO_ROOT = Path(__file__).resolve().parents[3]
CORPUS = REPO_ROOT / "docs" / "capability-corpus" / "claude-code"


# Cadence-shaped in-session requests — the "check X every N minutes" /
# "poll until Y" shapes that MUST route to /loop per the catalogue.
_CADENCE_PHRASINGS = [
    "check the deploy every 5 minutes",
    "keep checking until it is healthy",
    "run this check on a cadence",
    "repeatedly check every minute",
]

_STOPWORDS = frozenset(
    {
        "a", "an", "the", "to", "for", "of", "in", "on", "at", "and",
        "or", "is", "it", "this", "that", "with", "via", "my", "me",
        "i", "us", "we", "be", "n", "x", "y", "what", "when", "until",
        "before", "after", "into", "from", "under", "are", "do", "every",
    }
)
_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _discriminating_tokens(phrasing: str) -> list[str]:
    return [
        t for t in _TOKEN_RE.findall(phrasing.lower())
        if t not in _STOPWORDS and len(t) > 1
    ]


def _loop_trigger_surface() -> str:
    text = load_skill_text("loop-command")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, "loop-command: missing frontmatter delimiters"
    description = yaml.safe_load(match.group(1)).get("description", "")
    body = match.group(2)
    return f"{description}\n{body}".lower()


def test_AC_CLP_ADOPT_3_cadence_request_routes_to_loop() -> None:
    """Each cadence-shaped phrasing's discriminating tokens are present
    in the loop-command trigger surface — the cadence request routes to
    /loop per the catalogue."""
    surface = _loop_trigger_surface()
    for phrasing in _CADENCE_PHRASINGS:
        tokens = _discriminating_tokens(phrasing)
        assert tokens, f"phrasing {phrasing!r} has no content tokens"
        missing = [t for t in tokens if t not in surface]
        # The fire-decision tolerates ONE non-matching content token per
        # phrasing (a user's phrasing need not be a verbatim substring of
        # the description); a phrasing with two+ tokens absent is a
        # non-firing trigger — the cadence shape would NOT route to /loop.
        assert len(missing) <= 1, (
            f"AC.CLP-ADOPT.3: the cadence request {phrasing!r} does NOT "
            f"route to /loop — discriminating tokens {missing} are absent "
            f"from the loop-command trigger surface. The catalogue "
            f"routing for the cadence shape is broken."
        )


def test_AC_CLP_ADOPT_3_loop_corpus_names_goal_sibling() -> None:
    """The loop.md corpus entry — the catalogue the persona consults to
    pick the primitive — carries the reciprocal /goal disambiguation
    Slice 3 added, so the routing decision (/loop vs /goal) is
    observable in the catalogue record (D-ADOPT.3 + AC.CLP-ADOPT.4)."""
    loop_md = (CORPUS / "loop.md").read_text(encoding="utf-8")
    assert "/goal" in loop_md, (
        "AC.CLP-ADOPT.3: loop.md must name /goal as the sibling so the "
        "catalogue makes the /loop-vs-/goal routing decision observable"
    )
    # The disambiguation must state the halt-criterion distinction (the
    # load-bearing difference the persona routes on), not merely mention
    # the word /goal.
    lowered = loop_md.lower()
    assert "sibling" in lowered and (
        "halt" in lowered or "reach a state" in lowered
    ), (
        "AC.CLP-ADOPT.3: the loop.md /goal disambiguation must state the "
        "halt-criterion distinction (iteration-is-the-work vs "
        "reach-a-state), the basis the persona routes on"
    )
