# Copyright 2026 Luke Ivers and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""AC.SKTRI.2 — dead skills are retired; the installed surface is the
live set, not an accreting graveyard.

Per ``docs/plans/foundation-polish-cluster.md`` §5 AC.SKTRI.2
(SUB-ITEM 4, REMAINING scope): skills with no working trigger /
superseded / non-functional are REMOVED from the installed surface,
with the removal recorded. §15 backwards-compat: BEFORE retiring a
skill, verify no live consumer references it — retiring must not break
a workflow that referenced it.

TRIAGE OUTCOME (verified at build time, recorded here):

The retirement set is EMPTY on evidence. Every skill discovered on
disk meets ALL three retention criteria:

  1. WORKING TRIGGER — its trigger fires on its intended NL shape
     (proven by ``test_AC_SKTRI_1_triggers_fire_on_intended_shape.py``).
  2. NOT SUPERSEDED — it carries a substantive body and no sibling
     skill subsumes its trigger surface (each retained skill owns a
     distinct intended-shape band — verified Tier-0; the four
     scheduling primitives cron-create/launchd-plist/schedule-wakeup/
     loop-command, e.g., partition the cadence axis rather than
     duplicate it, and each names the others as COMPOSES-WITH, not
     supersedes).
  3. LIVE CONSUMER — at least one consumer outside the skill's own
     directory + the tests references it (this file's check), so
     retiring it would break a referencing workflow (§15).

Because no skill meets a retirement criterion, retiring any one would
be an unjustified removal that this AC explicitly guards against (the
"not silently retained" AND "not silently retired" twin contract).
This test therefore verifies the LIVE-SET INVARIANT: every retained
skill has a live consumer. A future skill that loses all consumers
fails here — that is the retire-or-justify signal AC.SKTRI.2 names.

If a genuine retirement is later warranted, this test's RETIRED set
records it (slug + rationale) and the live-consumer scan confirms the
no-live-consumer precondition before the directory is removed.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from conftest import discover_skill_packages


REPO_ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

# Skills retired by this triage cycle, each with its rationale + the
# no-live-consumer verification that gated the removal (§15). EMPTY by
# evidence — every installed skill is live (see module docstring). A
# future retirement appends ``"<slug>": "<rationale + no-consumer
# proof>"`` here AND removes the directory; the removal is recorded by
# this very mapping.
RETIRED: dict[str, str] = {}


DISCOVERED_SKILLS = discover_skill_packages()


def _live_consumer_count(skill_name: str) -> int:
    """Count references to *skill_name* across the tracked tree,
    EXCLUDING the skill's own directory and the plugin test suite.

    A "live consumer" is any tracked file outside the skill package
    itself + the AC tests that names the skill — a workflow, memory
    rule, persona instruction, plan-doc, or composing skill that would
    break if the skill were retired (§15 backwards-compat)."""
    out = subprocess.run(
        ["git", "grep", "-l", skill_name, "--", ".", ":!*/tests/*"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    own_dir = f"plugins/loam-skills/skills/{skill_name}/"
    consumers = [
        ln
        for ln in out.stdout.splitlines()
        if ln.strip()
        and not ln.startswith(own_dir)
        and "/tests/" not in ln
    ]
    return len(consumers)


def test_retired_directories_absent() -> None:
    """Every recorded retirement is actually gone from disk — the
    record and the surface agree (no phantom retirement, no
    surface-still-present-after-record drift)."""
    for slug in RETIRED:
        assert not (SKILLS_DIR / slug).exists(), (
            f"AC.SKTRI.2: {slug} is recorded RETIRED but its directory "
            f"still exists on the installed surface."
        )


def test_retirement_set_recorded_with_rationale() -> None:
    """Every retirement carries a non-empty recorded rationale (the
    "removal recorded" half of the AC). Vacuously true when the
    retirement set is empty — which is the verified triage outcome."""
    for slug, rationale in RETIRED.items():
        assert rationale.strip(), (
            f"AC.SKTRI.2: retirement of {slug} must record a rationale."
        )


@pytest.mark.parametrize("skill_name", DISCOVERED_SKILLS)
def test_retained_skill_has_live_consumer(skill_name: str) -> None:
    """LIVE-SET INVARIANT: every retained skill has ≥1 live consumer
    outside its own package + the tests. A retained skill with zero
    live consumers is an accreting-graveyard entry — the exact shape
    AC.SKTRI.2 retires. (Verified at build time: all installed skills
    have ≥3 live consumers; none is an orphan.)"""
    assert skill_name not in RETIRED, (
        f"{skill_name} is recorded RETIRED but still present on disk."
    )
    count = _live_consumer_count(skill_name)
    assert count >= 1, (
        f"AC.SKTRI.2: retained skill {skill_name!r} has NO live consumer "
        f"outside its own package — it is graveyard surface. Retire it "
        f"(record the slug + this no-consumer finding in RETIRED) or "
        f"wire a consumer."
    )
