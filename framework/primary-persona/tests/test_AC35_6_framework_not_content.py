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

"""AC35.6 — pOS core ships zero persona content.

The framework-tree scan continues to raise ``PersonaInCoreError`` if
any persona directory other than
``primary-persona/templates/persona-template/`` (with reserved handle
``example-persona``) appears in pOS-core paths. The renderer composes
agent-file content from the loaded contract at render time, not from
a string shipped in the framework. ``to_agent_md``'s output for a
fixture contract under ``tests/`` does not contain any string copied
from a hardcoded persona-prose constant inside the framework source.

Plan: docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding.md
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.agent_md import to_agent_md
from loam.primary_persona.contract import PersonaContract


# Unique sentinels — chosen to be lexically distinguishable from any
# template prose. If these strings appear in the renderer's output,
# they prove the prose came from the contract argument (not from a
# framework-level constant).
SENTINEL_GIVEN_NAME = "Zephyrine-Sentinel-Beacon"
SENTINEL_HANDLE = "sentinel-handle-x"
SENTINEL_RESPONSIBILITY = (
    "ZSB-CRITICAL-MARKER-9F4D — sole coordinator for sentinel-domain work."
)


def _sentinel_contract() -> PersonaContract:
    return PersonaContract.model_validate(
        {
            "handle": SENTINEL_HANDLE,
            "given_name": SENTINEL_GIVEN_NAME,
            "contract_version": "1.0.0",
            "responsibilities": {
                "single_point_of_contact": SENTINEL_RESPONSIBILITY,
                "context_holder": "Carries ongoing context across sessions.",
                "escalation_judge": "Decides when to surface to the user.",
            },
            "authority_boundary": {
                "tier_a": "defer",
                "tier_b": "defer",
                "tier_c": "execute",
                "tier_d": "execute",
            },
            "escalation_taxonomy": {"categories": ["sentinel-cat"]},
            "severity_vocabulary": {"labels": ["a", "b"]},
        }
    )


def test_AC35_6_renderer_output_carries_sentinels_from_contract():
    """Sentinel strings in the contract appear in `to_agent_md` output —
    proving the prose came from the contract argument, not from a
    framework-level constant."""
    contract = _sentinel_contract()
    rendered = to_agent_md(contract)
    assert SENTINEL_GIVEN_NAME in rendered
    assert SENTINEL_HANDLE in rendered
    # The description is derived from the first sentence of
    # responsibilities.single_point_of_contact; the sentinel marker
    # in that first sentence appears in the output.
    assert "ZSB-CRITICAL-MARKER-9F4D" in rendered


def test_AC35_6_renderer_output_does_not_contain_template_prose():
    """The renderer's output for a sentinel contract does NOT contain
    the persona-template's placeholder prose. Establishes that the
    template's content stays in the template tree and is never lifted
    into the renderer's output for arbitrary contracts."""
    contract = _sentinel_contract()
    rendered = to_agent_md(contract)
    # Template uses these placeholder strings; none should appear.
    template_placeholders = (
        "Describe, in one sentence, what this persona is the sole contact for.",
        "Describe, in one sentence, what ongoing context this persona maintains.",
        "Describe, in one sentence, what this persona decides to surface vs. handle.",
        "Example",  # template's placeholder given_name
    )
    for placeholder in template_placeholders:
        assert placeholder not in rendered, (
            f"renderer output contains template placeholder {placeholder!r} — "
            "framework-level template prose should not surface in renderer output"
        )


def test_AC35_6_existing_framework_tree_scan_still_passes():
    """The existing PersonaInCoreError surface (D2) continues to
    enforce — the only persona directory in pOS-core is the template
    with reserved handle `example-persona`."""
    from loam.primary_persona.loader import PersonaLoader

    # Construct against a sibling tmpfs workspace; the
    # `enforce_no_personas_in_core=True` default triggers the framework
    # scan. If a non-template persona snuck into pOS-core paths, this
    # call raises PersonaInCoreError; current state should pass.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        # Just instantiate; the constructor walks the tree.
        PersonaLoader(workspace_root=Path(tmp), enforce_no_personas_in_core=True)
    # No exception → AC35.6 invariant holds.


def test_AC35_6_renderer_source_does_not_carry_persona_prose_constants():
    """Inspect the renderer source: no string-literal carrying the
    lexical shape of persona prose (multi-sentence value-laden
    statements). The renderer composes from contract fields; the
    framework-level template scaffolding (anchor headers, sentence
    skeleton) speaks *about* the contract, not in any persona's voice.
    """
    src_path = (
        Path(__file__).resolve().parent.parent
        / "src" / "loam" / "primary_persona" / "agent_md.py"
    )
    text = src_path.read_text(encoding="utf-8")
    # Strip the Apache-2.0 license header (M8-corrective `6bef03b`
    # injected ``Luke Ivers`` as copyright owner; that's build-
    # metadata, not workspace-supplied persona content). The
    # AC.35.6 framework-not-content invariant is about persona
    # prose constants, not about the license header. Per
    # `feedback_loose_AC_text_fix_AC_not_implementation`: ODD §4
    # in-band rebaseline at C2-prime — the AC intent is preserved;
    # only the substring scope is tightened to exclude the
    # license header.
    text = _strip_apache_header(text)
    # Sentinels: the framework scaffolding explicitly speaks
    # *about* the persona ("I am <given_name>" with a placeholder)
    # rather than *as* the persona. Verify no hardcoded given_name
    # value or hardcoded responsibilities prose lives in the renderer.
    forbidden_substrings = (
        "Eve",   # ivers-corp's branding (and our test fixture)
        "Iris",  # any other test-fixture given_name
        "Luke",  # the user's name appears nowhere in framework source
        "personal-life operations",  # any concrete responsibility
    )
    for token in forbidden_substrings:
        assert token not in text, (
            f"renderer source carries content-shaped token {token!r} — "
            "framework-not-content invariant requires the renderer to "
            "compose from the contract, not from hardcoded persona prose"
        )


def _strip_apache_header(text: str) -> str:
    """Drop the leading Apache-2.0 license header (M8-corrective
    `6bef03b` injected). The header is a 14-line block ending at
    ``# limitations under the License.``; everything after that
    line is the source proper.
    """
    sentinel = "# limitations under the License."
    idx = text.find(sentinel)
    if idx < 0:
        return text
    return text[idx + len(sentinel):]
