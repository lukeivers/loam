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

"""AC.FLOWDEF.* — the flow-definition format.

  - AC.FLOWDEF.1 — a definition carries BOTH a machine-walkable node
    graph AND a non-empty human narrative, in one artefact.
  - AC.FLOWDEF.2 — the existing loam-vnext-build-workflow.md content
    (6 steps + 8 gates) is expressible without losing steps, gates, or
    branch points (round-trip).
  - AC.FLOWDEF.3 — a malformed definition (unreachable step, transition
    to an undeclared step, missing required field) is rejected with a
    corrective message naming the defect.
  - AC.FLOWDEF.4 (Fork C1) — a flat action-list is rejected as
    not-a-flow, not silently accepted as a flow.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loam_cli.flows.format import (
    FlowParseError,
    parse_flow_definition,
)

# Repo root: tests/ -> tools/loam -> tools -> framework -> loam(repo).
REPO_ROOT = Path(__file__).resolve().parents[4]
DOGFOOD_FLOW = REPO_ROOT / "docs" / "flows" / "loam-vnext-build.flow.md"


def _minimal_valid_flow() -> str:
    return (
        "---\n"
        "flow: t\n"
        "steps:\n"
        "  - id: a\n"
        "    transitions: [b]\n"
        "  - id: b\n"
        "    transitions: [c]\n"
        "  - id: c\n"
        "    transitions: []\n"
        "---\n"
        "# t\nhuman narrative present.\n"
    )


def test_AC_FLOWDEF_1_carries_machine_graph_and_human_narrative() -> None:
    """AC.FLOWDEF.1 — both halves present + the graph is walkable."""
    d = parse_flow_definition(_minimal_valid_flow())
    # Machine half: a walkable graph — every step reachable, every
    # transition targets a declared step.
    assert d.step_ids() == {"a", "b", "c"}
    for step in d.steps:
        for target in step.transitions:
            assert target in d.step_ids()
    # Human half: present + non-empty.
    assert d.body.strip()
    assert "human narrative" in d.body


def test_AC_FLOWDEF_1_empty_human_body_is_rejected() -> None:
    """AC.FLOWDEF.1 — a machine graph with NO human narrative is not a
    complete flow definition."""
    text = (
        "---\n"
        "flow: t\n"
        "steps:\n"
        "  - id: a\n    transitions: [b]\n"
        "  - id: b\n    transitions: [c]\n"
        "  - id: c\n    transitions: []\n"
        "---\n"
        "   \n"  # whitespace-only body.
    )
    with pytest.raises(FlowParseError) as exc:
        parse_flow_definition(text)
    assert "narrative" in str(exc.value).lower()


def test_AC_FLOWDEF_2_build_workflow_expressible_without_loss() -> None:
    """AC.FLOWDEF.2 — the build-workflow's 6 steps + 8 gates round-trip.

    The dogfood flow definition expresses the build-workflow
    (loam-vnext-build-workflow.md §2-§3: 6 work steps EXAMINE / DEFINE /
    BUILD / PROVE / INTEGRATE+RECORD / LOOP, and 8 gates G1-G7 + G★).
    Parsing it preserves all steps, all gates, and the branch points
    (BUILD branches to PROVE + the destructive-gate node; PROVE branches
    back to BUILD).
    """
    text = DOGFOOD_FLOW.read_text(encoding="utf-8")
    d = parse_flow_definition(text)

    # The 6 named work steps (the per-slice loop) are all present.
    work_steps = {
        "examine",
        "define",
        "build",
        "prove",
        "integrate_record",
        "loop",
    }
    assert work_steps <= d.step_ids()

    # The 8 gates G1-G7 + G★ are all present.
    gate_ids = {g.id for g in d.gates}
    assert gate_ids == {"G1", "G2", "G3", "G4", "G5", "G6", "G7", "G★"}

    # Branch points preserved: BUILD branches (to PROVE + the
    # destructive-gate node); PROVE branches back to BUILD on failure.
    build = d.get_step("build")
    prove = d.get_step("prove")
    assert build is not None and prove is not None
    assert len(build.transitions) > 1  # a real branch point.
    assert "prove" in build.transitions
    assert "build" in prove.transitions  # the PROVE-fails-to-BUILD edge.


@pytest.mark.parametrize(
    "bad_text,defect",
    [
        # Missing required field: no 'flow'.
        (
            "---\nsteps:\n  - id: a\n    transitions: []\n  - id: b\n"
            "    transitions: []\n  - id: c\n    transitions: []\n---\n"
            "# x\nbody.\n",
            "flow",
        ),
        # Transition to an undeclared step.
        (
            "---\nflow: t\nsteps:\n  - id: a\n    transitions: [zzz]\n"
            "  - id: b\n    transitions: []\n  - id: c\n"
            "    transitions: []\n---\n# t\nbody.\n",
            "zzz",
        ),
        # Unreachable step (orphan: c is reachable from nothing).
        (
            "---\nflow: t\nentry: a\nsteps:\n  - id: a\n"
            "    transitions: [b]\n  - id: b\n    transitions: []\n"
            "  - id: c\n    transitions: []\n---\n# t\nbody.\n",
            "reachable",
        ),
    ],
)
def test_AC_FLOWDEF_3_malformed_rejected_with_named_defect(
    bad_text: str, defect: str
) -> None:
    """AC.FLOWDEF.3 — each malformed definition is rejected with a
    message naming the defect, never silently accepted."""
    with pytest.raises(FlowParseError) as exc:
        parse_flow_definition(bad_text)
    assert defect in str(exc.value)


def test_AC_FLOWDEF_4_flat_action_list_rejected_as_not_a_flow() -> None:
    """AC.FLOWDEF.4 (Fork C1) — a flat action-list (no branch points, no
    gates, below the step floor) is NOT admitted as a flow."""
    flat = (
        "---\n"
        "flow: chores\n"
        "steps:\n"
        "  - id: a\n    name: do thing a\n    transitions: [b]\n"
        "  - id: b\n    name: do thing b\n    transitions: []\n"
        "---\n"
        "# chores\nA flat to-do list, not a process.\n"
    )
    with pytest.raises(FlowParseError) as exc:
        parse_flow_definition(flat)
    msg = str(exc.value).lower()
    assert "flat" in msg or ("not" in msg and "flow" in msg)


def test_AC_FLOWDEF_4_multistep_with_gate_is_admitted() -> None:
    """AC.FLOWDEF.4 — a real multi-step process WITH a gate IS admitted
    (the floor rejects flat lists, not real short flows)."""
    with_gate = (
        "---\n"
        "flow: tiny\n"
        "steps:\n"
        "  - id: a\n    transitions: [b]\n"
        "  - id: b\n    gate: true\n    transitions: []\n"
        "---\n"
        "# tiny\nTwo steps but one is a gate — a real decision flow.\n"
    )
    d = parse_flow_definition(with_gate)
    assert d.flow == "tiny"
