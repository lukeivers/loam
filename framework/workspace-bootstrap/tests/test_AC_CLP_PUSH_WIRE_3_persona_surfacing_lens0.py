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

"""AC.CLP-PUSH-WIRE.3 / AC.CLP-PUSH.4 (claude-leverage-program Slice 4b).

The persona surfaces newly-arrived leverage knowledge per the Lens 0
substance/vocabulary rule: the SUBSTANCE (what arrived + what it lets
the user do) is exposed at every vocabulary level; only the WORDS adapt
to the user's known terms. It is NOT a raw changelog dump (bare titles
+ hash with no "what this does for you"), and a stale signal is never
silently dropped.

This is satisfied by a deterministic surfacing-rule artefact in the
workspace-bootstrap fence (where the wiring that brings the pack in
lives), NOT a primary-persona spine edit — the conditional
primary-persona manifest component is therefore not needed and is
removed at apply (fence equal to the work).
"""

from __future__ import annotations

from loam.workspace_bootstrap.adapters.marketplace_wiring import (
    SURFACING_VOCAB_PLAIN,
    SURFACING_VOCAB_TECHNICAL,
    ArrivedKnowledge,
    surface_arrived_knowledge,
)


def _arrived() -> ArrivedKnowledge:
    return ArrivedKnowledge(
        skill_titles=(
            "Run web research across many sources at once",
            "Schedule a recurring check without writing a cron job",
        ),
        generated_ts="2026-06-14T00:00:00Z",
        content_hash="abcdef0123456789",
    )


def test_WIRE_3_substance_exposed_in_plain_vocab() -> None:
    """At the plain (non-technical) vocab level the SUBSTANCE is
    present — what each new capability lets the user DO appears — so the
    surfacing exposes what arrived, not merely that something did."""
    out = surface_arrived_knowledge(_arrived(), vocab=SURFACING_VOCAB_PLAIN)
    assert "Run web research across many sources at once" in out
    assert "Schedule a recurring check without writing a cron job" in out


def test_WIRE_3_plain_vocab_drops_coined_platform_terms() -> None:
    """Lens 0: adapt the VOCABULARY. The plain surfacing carries no
    coined / platform-internal terms (marketplace, plugin, skills-pack,
    content-hash) the user has not shown they know — substance stays,
    jargon goes."""
    out = surface_arrived_knowledge(
        _arrived(), vocab=SURFACING_VOCAB_PLAIN
    ).lower()
    for jargon in ("marketplace", "plugin", "skills-pack", "content-hash"):
        assert jargon not in out


def test_WIRE_3_not_a_raw_changelog_dump() -> None:
    """The surfacing ties arrival to user-facing capability — it is not
    a bare changelog dump (a hash + version line with no 'what this does
    for you'). The plain surfacing leads with the benefit framing, and
    the bare 12-char content hash does NOT appear as the surfaced
    payload."""
    out = surface_arrived_knowledge(_arrived(), vocab=SURFACING_VOCAB_PLAIN)
    # Benefit framing present (the "what this does for you" leg).
    assert "get more out of AI" in out
    # Raw hash is not dumped at the plain level.
    assert "abcdef012345" not in out


def test_WIRE_3_technical_vocab_exposes_same_substance() -> None:
    """At the technical vocab level the SAME substance (the skill
    titles) is exposed; platform vocabulary is permitted for a user who
    has shown they know it (Lens 0 — adapt words, never hide
    substance)."""
    out = surface_arrived_knowledge(
        _arrived(), vocab=SURFACING_VOCAB_TECHNICAL
    )
    assert "Run web research across many sources at once" in out
    assert "Schedule a recurring check without writing a cron job" in out


def test_WIRE_3_stale_signal_never_silently_dropped() -> None:
    """A stale-entry signal carried from the corpus (the
    stale-never-silently-current rule, propagated through the pack) is
    always surfaced — never dropped — so the user-facing surface never
    presents stale-as-current."""
    arrived = ArrivedKnowledge(
        skill_titles=("Use the newest model routing",),
        generated_ts="2026-06-14T00:00:00Z",
        content_hash="abcdef0123456789",
        stale_note="one source was last checked 90 days ago",
    )
    plain = surface_arrived_knowledge(arrived, vocab=SURFACING_VOCAB_PLAIN)
    technical = surface_arrived_knowledge(
        arrived, vocab=SURFACING_VOCAB_TECHNICAL
    )
    assert "last checked 90 days ago" in plain
    assert "last checked 90 days ago" in technical
