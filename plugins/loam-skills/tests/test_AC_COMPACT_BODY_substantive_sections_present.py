"""AC.COMPACT.BODY — strategic-compact SKILL body carries the
substantive content the SKILL graduates from: three-options
decision rubric + decision rule + activation triggers +
composition section naming the source memory rule.

Per ``docs/plans/strategic-compact-skill-graduation.md`` §2: the
body IS the operative content the persona consults when the
decision surface fires. Each section must be present + named +
substantive enough for the persona to apply the rubric without
referring back to the plan-doc or the source memory rule.
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SKILL_MD = (
    REPO_ROOT
    / "plugins"
    / "loam-skills"
    / "skills"
    / "strategic-compact"
    / "SKILL.md"
)


def _load_body() -> str:
    text = SKILL_MD.read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n.*?\n---\s*\n(.*)\Z", text, re.DOTALL)
    assert match, (
        f"AC.COMPACT.BODY: SKILL.md frontmatter must be delimited "
        f"by `---` lines; got non-matching shape in {SKILL_MD}."
    )
    return match.group(1)


def test_AC_COMPACT_BODY_three_options_named() -> None:
    """The three options (continue / /compact / /clear) are each
    named as section content, with cost-shape + when-to-pick
    discussion per option.

    The substance moved from the memory rule's "The three options"
    section. The persona reading this SKILL must be able to walk
    the rubric option-by-option without referring back.
    """
    body = _load_body().lower()

    # Each option must be named as a section or section-like header.
    # Continue is the "no compaction, no clear" option; /compact and
    # /clear are the two slash-command options.
    assert "continue" in body, (
        "AC.COMPACT.BODY: 'continue' (the no-compact-no-clear option) "
        "must be named in the body."
    )
    assert "/compact" in body, (
        "AC.COMPACT.BODY: `/compact` option must be named in the body."
    )
    assert "/clear" in body, (
        "AC.COMPACT.BODY: `/clear` option must be named in the body."
    )

    # Each option carries a cost-shape discussion. Accept either the
    # "Cost shape:" sub-header convention from the memory rule or the
    # word "cost" in proximity to each option's discussion.
    assert "cost shape" in body or body.count("cost") >= 3, (
        "AC.COMPACT.BODY: each of the three options must carry a "
        "cost-shape discussion so the persona can name the trade-"
        "off when surfacing the recommendation."
    )

    # Each option carries a when-to-pick discussion.
    assert "when to pick" in body, (
        "AC.COMPACT.BODY: each option must carry a 'when to pick' "
        "discussion so the decision rule has concrete branches."
    )


def test_AC_COMPACT_BODY_decision_rule_present() -> None:
    """The decision rule (the four-branch IF table from the memory
    rule) is present in the body, either as a code block or as
    equivalent prose."""
    body = _load_body()
    # The decision rule has four branches keyed on context-window
    # utilization + session-arc state. Look for the substring markers
    # of each branch.
    body_lower = body.lower()
    assert "decision rule" in body_lower or "the decision rule" in body_lower, (
        "AC.COMPACT.BODY: a 'decision rule' section / header must "
        "be present so the persona can walk the four branches."
    )
    # The four branches reference context-window utilization
    # thresholds (60%, 85%) and session-arc state (continuing,
    # complete/drifting).
    assert "60" in body and "85" in body, (
        "AC.COMPACT.BODY: the decision rule must name the 60% and "
        "85% context-window utilization thresholds per the memory "
        "rule's rubric."
    )
    assert (
        "arc continuing" in body_lower
        or "session-arc continuing" in body_lower
    ), (
        "AC.COMPACT.BODY: the decision rule must reference the "
        "session-arc state (continuing vs complete/drifting) as the "
        "second branch axis."
    )


def test_AC_COMPACT_BODY_activation_triggers_section_present() -> None:
    """An activation-triggers section names the three concrete
    patterns that bring the decision into surface (owner question /
    persona-detected context-pressure / major arc close)."""
    body = _load_body()
    body_lower = body.lower()
    # Accept either an explicit "activation" header or the trigger
    # patterns listed under a "when to use" header.
    has_activation_surface = (
        "activation" in body_lower
        or "triggers" in body_lower
        or "when to use" in body_lower
    )
    assert has_activation_surface, (
        "AC.COMPACT.BODY: an activation-triggers section must be "
        "present (the three patterns: owner question / persona-"
        "detected context-pressure / major arc close)."
    )
    # The three concrete trigger patterns must be named substantively.
    assert (
        "should i /compact" in body_lower
        or "should i /clear" in body_lower
        or "owner question" in body_lower
    ), (
        "AC.COMPACT.BODY: the owner-question trigger pattern must "
        "be named (the 'should I /compact?' / 'should I /clear?' "
        "shape from the memory rule)."
    )
    assert "context" in body_lower and (
        "pressure" in body_lower or "tight" in body_lower
    ), (
        "AC.COMPACT.BODY: the persona-detected context-pressure "
        "trigger must be named (the 'context-feeling-tight' shape "
        "from the memory rule)."
    )
    assert (
        "arc" in body_lower
        and ("close" in body_lower or "complete" in body_lower)
    ), (
        "AC.COMPACT.BODY: the major-arc-close trigger must be "
        "named (release ships / plan-doc ratification cycle "
        "completes / build cycle seals)."
    )


def test_AC_COMPACT_BODY_composition_names_source_memory_rule() -> None:
    """A composition section names the source memory rule as the
    substance-source (per the memory-becomes-index, SKILL-becomes-
    operative graduation pattern)."""
    body = _load_body()
    body_lower = body.lower()
    assert "composition" in body_lower or "composes with" in body_lower, (
        "AC.COMPACT.BODY: a 'Composition' / 'Composes with' section "
        "must be present so the SKILL's compositional surface is "
        "operator-discoverable."
    )
    # The source memory rule MUST be named — that's the graduation
    # provenance the SKILL inherits from.
    assert "feedback_compact_clear_decision_heuristic" in body, (
        "AC.COMPACT.BODY: the composition section must name the "
        "source memory rule `feedback_compact_clear_decision_"
        "heuristic.md` as the substance-source (per the graduation "
        "pattern: memory-becomes-index; SKILL-becomes-operative)."
    )
    # The precompact-hook sibling SKILL is the compositional pair —
    # both surfaces should be cross-referenced.
    assert "precompact-hook" in body_lower, (
        "AC.COMPACT.BODY: the composition section must name the "
        "`precompact-hook` sibling SKILL (the structural-enforcement-"
        "at-compaction-time companion to this decision-discipline)."
    )


def test_AC_COMPACT_BODY_owner_class_constraint_named_in_body() -> None:
    """The owner-class-only constraint is named in the body, not just
    the frontmatter — the body IS the operative source the persona
    reads on SKILL load."""
    body = _load_body()
    body_lower = body.lower()
    # Accept any of these phrasings.
    constraint_markers = (
        "owner-class only",
        "owner discretion",
        "owner-discretion",
        "not autonomous-agent",
        "not for autonomous-clear",
        "not autonomous",
    )
    matched = any(marker in body_lower for marker in constraint_markers)
    assert matched, (
        "AC.COMPACT.BODY: the owner-class-only constraint must be "
        "named in the body (the source memory rule's bounding rule "
        "at lines 106-111 + D-COMPACT.TRIGGER ratified ruling). "
        f"Looked for any of {constraint_markers}."
    )
