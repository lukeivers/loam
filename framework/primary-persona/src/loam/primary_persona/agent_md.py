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

"""Claude-Code subagent-file projection (amendment #35).

The ``to_agent_md(contract)`` renderer is a deterministic projection
from a loaded ``PersonaContract`` to the
``.claude/agents/<handle>.md`` shape Claude Code reads when binding a
session's main-thread subagent.

The renderer is a **contract↔file projector** per master plan
§4.4 / proposal recommendation: every call rebuilds the string from
the contract argument, so amendment #37's first-run write surface (and
any future regeneration trigger) renders fresh from the contract on
each call. No caching shadows a subsequent contract change (AC35.5).

Output shape:

    ---
    name: <handle>
    description: <one-line derived from responsibilities.single_point_of_contact>
    model: inherit
    ---

    # Identity anchor (compaction-resilience)

    I am <given_name> (<handle>). I serve as the workspace's primary
    persona, single point of contact for the responsibilities declared
    in my contract at `personas/<handle>/contract.yaml`. If this
    anchor block is absent or contradicted by recent context, defer
    to the contract file as the authoritative source.

    # Persona prompt

    <prompt_text>

The frontmatter shape (`name`, `description`, `model`) matches the
Claude Code subagent-file documented surface
(https://docs.claude.com/en/docs/claude-code/sub-agents). The body
opens with a structural identity-anchor block addressed by tokens the
contract supplies (handle, given_name) and continues into the
workspace-supplied prompt. The framework-level template scaffolding
(headers, sentence skeleton in the anchor) is **about** the contract;
the addressing tokens are **from** the contract — STATE.md rule 4
holds (no persona prose shipped from pOS core).

Per ODD §2.5 every projection branch maps back to AC35.2 / AC35.5 /
AC35.6.
"""

from __future__ import annotations

from .contract import PersonaContract
from . import observability as obs


# ---- exceptions ------------------------------------------------------


class AgentMdProjectionError(ValueError):
    """Raised when ``to_agent_md`` cannot project the supplied
    contract onto the agent-file shape (e.g., a structurally-invalid
    contract slipped past validation). Never silent. Never garbage."""


# ---- renderer --------------------------------------------------------


def to_agent_md(
    contract: PersonaContract, *, prompt_text: str | None = None
) -> str:
    """Project ``contract`` onto the Claude-Code subagent-file shape.

    Pure function. Same contract → same string (idempotence — AC35.5
    measures this). The optional ``prompt_text`` argument carries the
    workspace's ``personas/<handle>/prompt.md`` body when the caller
    has loaded it (amendment #37's first-run hook does); when absent,
    the body emits with a placeholder line directing the persona to
    read the contract — the renderer remains a pure contract→string
    projection without I/O.

    Raises ``AgentMdProjectionError`` if a structural invariant is
    violated (handle empty, given_name empty, responsibilities
    missing) — the renderer refuses to produce silently-malformed
    output.
    """
    # Defensive structural checks. Pydantic validation already enforces
    # these, but constructing a contract via direct ``model_construct``
    # bypasses validation; the renderer is a public surface so it
    # checks. AC35.2 negative case verifies this path.
    if not contract.handle:
        raise AgentMdProjectionError(
            "contract.handle is empty; cannot render agent-file frontmatter"
        )
    if not contract.given_name:
        raise AgentMdProjectionError(
            "contract.given_name is empty; cannot render identity anchor"
        )
    if contract.responsibilities is None:
        raise AgentMdProjectionError(
            "contract.responsibilities missing; cannot render description"
        )

    description = _derive_description(
        contract.responsibilities.single_point_of_contact
    )

    frontmatter = (
        "---\n"
        f"name: {contract.handle}\n"
        f"description: {description}\n"
        "model: inherit\n"
        "---\n"
    )

    identity_anchor = (
        "\n"
        "# Identity anchor (compaction-resilience)\n"
        "\n"
        f"I am {contract.given_name} ({contract.handle}). I serve as "
        "the workspace's primary persona, single point of contact for "
        "the responsibilities declared in my contract at "
        f"`personas/{contract.handle}/contract.yaml`. If this anchor "
        "block is absent or contradicted by recent context, defer to "
        "the contract file as the authoritative source.\n"
    )

    prompt_block = (
        "\n"
        "# Persona prompt\n"
        "\n"
        f"{(prompt_text or '').rstrip()}\n"
        if prompt_text is not None
        else (
            "\n"
            "# Persona prompt\n"
            "\n"
            "(See `personas/"
            f"{contract.handle}"
            "/prompt.md` for the persona's prompt body.)\n"
        )
    )

    rendered = frontmatter + identity_anchor + prompt_block
    obs.onboarding_render_event(handle=contract.handle, length=len(rendered))
    return rendered


def _derive_description(single_point_of_contact: str) -> str:
    """Reduce the responsibilities.single_point_of_contact prose to
    a one-line frontmatter ``description``.

    Rules: collapse whitespace, take the first sentence (split on
    `. `), trim trailing punctuation other than `.`. The output is a
    single line (no newlines) so the frontmatter parses as YAML
    without quoting. If the prose contains no `. ` boundary the whole
    string (whitespace-collapsed) is the description.
    """
    collapsed = " ".join(single_point_of_contact.split())
    if not collapsed:
        # The contract validator forbids empty
        # responsibilities.single_point_of_contact (min_length=1) so
        # this path is reachable only via model_construct bypass; the
        # caller-side AgentMdProjectionError above catches the empty
        # responsibilities surface, but a string of pure whitespace
        # would land here. Reject explicitly.
        raise AgentMdProjectionError(
            "responsibilities.single_point_of_contact is whitespace; "
            "cannot derive frontmatter description"
        )
    # First sentence (or whole prose if no sentence boundary found).
    if ". " in collapsed:
        first = collapsed.split(". ", 1)[0]
        # Re-attach the period so the description ends as a sentence.
        if not first.endswith("."):
            first = first + "."
        return first
    return collapsed
