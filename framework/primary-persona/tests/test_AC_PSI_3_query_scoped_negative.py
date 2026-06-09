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

"""AC.PSI.3 — the production query entry point answers "what stored
plan/decision state exists matching this topic?" over the derived
index (plan-docs incl. sealed archive + seal-commit evidence),
returning matches with their build-state and an EXPLICITLY-SCOPED
empty result (what was searched) on no match — never a bare "nothing
exists".

Query mechanics are the builder's call; these tests pin the outcome
shapes (match-with-state; scoped-negative; honest-unavailable).
"""

from __future__ import annotations

from dataclasses import dataclass

from loam.primary_persona.keep_pace.plans_state import query_plan_state


@dataclass(frozen=True)
class _Plan:
    project: str
    slug: str
    title: str
    doc_path: str
    build_state: str
    seal_evidence: tuple[str, ...]
    in_sealed_archive: bool


_FIXTURE = {
    "loam": (
        _Plan(
            project="loam",
            slug="subagent-migration-cutover",
            title="claude-p to subagent migration cutover",
            doc_path="docs/plans/subagent-migration-cutover.md",
            build_state="partially-sealed",
            seal_evidence=(
                "abc1234 chore(amend): subagent-migration-cutover manifest+apply",
            ),
            in_sealed_archive=False,
        ),
        _Plan(
            project="loam",
            slug="telemetry-export-archive",
            title="telemetry export archive",
            doc_path="docs/plans/sealed/telemetry-export-archive.md",
            build_state="sealed",
            seal_evidence=("def5678 chore(seals): telemetry-export-archive — x",),
            in_sealed_archive=True,
        ),
    )
}


def test_AC_PSI_3_topic_match_returns_state_and_evidence() -> None:
    """The 06-09 shape: asking about the subagent migration finds the
    plan WITH its real build-state + seal evidence — including across
    the sealed archive."""
    result = query_plan_state(
        "the subagent migration work", derive=lambda: _FIXTURE
    )
    assert result["matches"], "the in-flight plan must match the topic"
    top = result["matches"][0]
    assert top["slug"] == "subagent-migration-cutover"
    assert top["build_state"] == "partially-sealed"
    assert top["seal_evidence"]

    archived = query_plan_state(
        "telemetry export archive", derive=lambda: _FIXTURE
    )
    assert archived["matches"]
    assert archived["matches"][0]["in_sealed_archive"] is True
    assert archived["matches"][0]["build_state"] == "sealed"


def test_AC_PSI_3_no_match_is_explicitly_scoped_never_bare() -> None:
    """An empty result names exactly what WAS searched and what was
    NOT — the dated-scoped-negative form, never a bare nothing."""
    result = query_plan_state(
        "underwater basket weaving relaunch", derive=lambda: _FIXTURE
    )
    assert result["matches"] == []
    assert result["searched"], "the empty result must name what was searched"
    assert any("loam" in s for s in result["searched"])
    assert any("sealed archive" in s for s in result["searched"])
    assert result["unsearched"], "the honest gap must be named"


def test_AC_PSI_3_generic_tokens_do_not_resolve_everything() -> None:
    """A generic work-vocabulary topic ('the plan', 'the build work')
    must NOT match every plan — the precision the claim guard's
    no-alarm-fatigue budget rides on."""
    result = query_plan_state("the plan for the build work", derive=lambda: _FIXTURE)
    assert result["matches"] == []


def test_AC_PSI_3_unavailable_derivation_is_honestly_scoped() -> None:
    """When the index derivation is unavailable, the result must NOT
    claim plan-docs were searched (that would be the same lie one
    level up): searched is empty, unsearched names the unavailable
    index."""

    def _boom() -> dict:
        raise RuntimeError("no loam_cli here")

    result = query_plan_state("anything at all", derive=_boom)
    assert result["matches"] == []
    assert result["searched"] == ()
    assert any("unavailable" in s for s in result["unsearched"])
