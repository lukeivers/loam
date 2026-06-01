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

"""The FLOW-DEFINITION format (AC.FLOWDEF.* — D1).

A flow definition is a SINGLE artefact carrying BOTH halves a real
multi-step process needs (plan §1 piece 1; D1):

  - a **machine-walkable node graph** — steps, transitions, branch /
    gate points — in a YAML front-matter block; and
  - a **human-followable narrative** — the prose a builder reads to
    actually follow the flow — in the Markdown body below the
    front-matter.

The on-disk shape is YAML front-matter delimited by ``---`` lines,
followed by the Markdown body::

    ---
    flow: loam-vnext-build
    title: loam v-next build
    steps:
      - id: examine
        name: EXAMINE
        transitions: [define]
      - id: define
        name: DEFINE
        transitions: [build]
      ...
    gates:
      - id: G2
        name: build-location decision
    ---
    # loam v-next build — the flow

    <human-followable narrative>

ACs proven here (method = builder's call per ODD §1.1):

  - **AC.FLOWDEF.1** — a definition carries a walkable graph AND a
    non-empty human narrative. ``validate_flow_definition`` asserts
    every step is reachable and every transition targets a declared
    step; ``FlowDefinition.body`` carries the prose.
  - **AC.FLOWDEF.2** — the existing ``loam-vnext-build-workflow.md``
    (6 steps + 8 gates) is expressible without loss. The format models
    steps + transitions + gates as first-class nodes; the dogfood flow
    definition round-trips all of them.
  - **AC.FLOWDEF.3** — a malformed definition (unreachable step,
    transition to an undeclared step, missing required field) is
    REJECTED with a corrective message naming the defect — never
    silently accepted.
  - **AC.FLOWDEF.4** (Fork C / C1) — a flat action-list (no branch /
    gate points, below the step threshold) is rejected as
    NOT-A-FLOW. The OUTCOME is asserted (flat checklists are not
    admitted as flows); the admission heuristic is the builder's call
    (the owner's anti-ceremony F2 constraint, plan §10 doubt 3).

Stdlib + PyYAML only (PyYAML is already a loam-cli dependency).
"""

from __future__ import annotations

from dataclasses import dataclass

import yaml

# AC.FLOWDEF.4 (Fork C1) — the not-a-flow floor. A real flow is a
# multi-step PROCESS with branch / gate points; a flat action-list is
# not a flow (the owner's anti-ceremony F2 constraint). The OUTCOME this
# constant enforces — "a flat action-list is not admitted as a flow" —
# is the AC; the specific number is the builder's chosen heuristic
# threshold (kept here, not in the AC, to avoid method-in-AC).
#
# A definition is admitted as a flow iff it has AT LEAST this many steps
# AND at least one branch point (a step with >1 transition) OR at least
# one gate. Anything below the floor is a flat checklist.
_MIN_FLOW_STEPS = 3


class FlowParseError(ValueError):
    """A flow definition is malformed (AC.FLOWDEF.3 / AC.FLOWDEF.4).

    The message names the specific defect (unreachable step, transition
    to an undeclared step, missing required field, or not-a-flow flat
    action-list) so the rejection is corrective, not opaque.
    """


@dataclass(frozen=True)
class FlowStep:
    """One step (work node) in a flow's machine-walkable graph."""

    id: str
    name: str
    transitions: tuple[str, ...] = ()
    gate: bool = False


@dataclass(frozen=True)
class FlowGate:
    """One gate (owner-decision point) declared by the flow."""

    id: str
    name: str


@dataclass(frozen=True)
class FlowDefinition:
    """A parsed, validated flow definition.

    ``steps`` is the machine-walkable graph (AC.FLOWDEF.1 machine half);
    ``body`` is the human-followable narrative (AC.FLOWDEF.1 human half).
    """

    flow: str
    title: str
    steps: tuple[FlowStep, ...]
    gates: tuple[FlowGate, ...] = ()
    body: str = ""
    entry: str = ""

    def step_ids(self) -> set[str]:
        return {s.id for s in self.steps}

    def get_step(self, step_id: str) -> FlowStep | None:
        for s in self.steps:
            if s.id == step_id:
                return s
        return None


_FRONT_MATTER_DELIM = "---"


def _split_front_matter(text: str) -> tuple[str, str]:
    """Split a YAML-front-matter + Markdown-body document.

    Returns (front_matter_yaml, markdown_body). Raises FlowParseError if
    the leading ``---`` front-matter fence is absent or unterminated
    (AC.FLOWDEF.3 — a structural defect is named, not silently allowed).
    """
    stripped = text.lstrip("﻿")  # tolerate a UTF-8 BOM.
    lines = stripped.splitlines()
    if not lines or lines[0].strip() != _FRONT_MATTER_DELIM:
        raise FlowParseError(
            "flow definition must open with a '---' YAML front-matter "
            "fence carrying the machine-walkable node graph (AC.FLOWDEF.1)"
        )
    for i in range(1, len(lines)):
        if lines[i].strip() == _FRONT_MATTER_DELIM:
            front = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :]).strip()
            return front, body
    raise FlowParseError(
        "flow definition front-matter is not terminated by a closing "
        "'---' fence (AC.FLOWDEF.3)"
    )


def _require(mapping: dict, key: str, where: str) -> object:
    if key not in mapping or mapping[key] in (None, ""):
        raise FlowParseError(
            f"{where}: missing required field '{key}' (AC.FLOWDEF.3)"
        )
    return mapping[key]


def parse_flow_definition(text: str) -> FlowDefinition:
    """Parse a flow-definition document into a FlowDefinition.

    Performs structural parse + the AC.FLOWDEF.3 / AC.FLOWDEF.4
    validations. Raises FlowParseError naming the defect on any
    malformed or not-a-flow input.
    """
    front, body = _split_front_matter(text)
    try:
        data = yaml.safe_load(front) if front.strip() else None
    except yaml.YAMLError as exc:  # malformed YAML front-matter.
        raise FlowParseError(
            f"flow definition front-matter is not valid YAML: {exc} "
            "(AC.FLOWDEF.3)"
        ) from exc
    if not isinstance(data, dict):
        raise FlowParseError(
            "flow definition front-matter must be a YAML mapping with "
            "'flow' + 'steps' (AC.FLOWDEF.3)"
        )

    flow = str(_require(data, "flow", "front-matter"))
    title = str(data.get("title") or flow)

    raw_steps = _require(data, "steps", "front-matter")
    if not isinstance(raw_steps, list) or not raw_steps:
        raise FlowParseError(
            "front-matter 'steps' must be a non-empty list of step "
            "mappings (AC.FLOWDEF.3)"
        )

    steps: list[FlowStep] = []
    seen_ids: set[str] = set()
    for idx, raw in enumerate(raw_steps):
        where = f"steps[{idx}]"
        if not isinstance(raw, dict):
            raise FlowParseError(
                f"{where}: each step must be a mapping (AC.FLOWDEF.3)"
            )
        sid = str(_require(raw, "id", where))
        if sid in seen_ids:
            raise FlowParseError(
                f"{where}: duplicate step id '{sid}' (AC.FLOWDEF.3)"
            )
        seen_ids.add(sid)
        sname = str(raw.get("name") or sid)
        raw_trans = raw.get("transitions") or []
        if not isinstance(raw_trans, list):
            raise FlowParseError(
                f"{where}: 'transitions' must be a list of step ids "
                "(AC.FLOWDEF.3)"
            )
        transitions = tuple(str(t) for t in raw_trans)
        gate_flag = bool(raw.get("gate", False))
        steps.append(
            FlowStep(
                id=sid,
                name=sname,
                transitions=transitions,
                gate=gate_flag,
            )
        )

    raw_gates = data.get("gates") or []
    if not isinstance(raw_gates, list):
        raise FlowParseError(
            "front-matter 'gates' must be a list of gate mappings "
            "(AC.FLOWDEF.3)"
        )
    gates: list[FlowGate] = []
    for idx, raw in enumerate(raw_gates):
        where = f"gates[{idx}]"
        if not isinstance(raw, dict):
            raise FlowParseError(
                f"{where}: each gate must be a mapping (AC.FLOWDEF.3)"
            )
        gid = str(_require(raw, "id", where))
        gname = str(raw.get("name") or gid)
        gates.append(FlowGate(id=gid, name=gname))

    entry = str(data.get("entry") or steps[0].id)

    definition = FlowDefinition(
        flow=flow,
        title=title,
        steps=tuple(steps),
        gates=tuple(gates),
        body=body,
        entry=entry,
    )
    validate_flow_definition(definition)
    return definition


def validate_flow_definition(definition: FlowDefinition) -> None:
    """Validate a FlowDefinition's graph + ceremony floor.

    Raises FlowParseError naming the defect on:
      - AC.FLOWDEF.1: an empty human-followable body, OR a transition
        targeting an undeclared step, OR an unreachable step.
      - AC.FLOWDEF.3: the malformed-graph cases above.
      - AC.FLOWDEF.4: a not-a-flow flat action-list (below the step
        floor and carrying no branch point and no gate).
    """
    step_ids = definition.step_ids()

    # AC.FLOWDEF.1 — the human half must be present + non-empty.
    if not definition.body.strip():
        raise FlowParseError(
            f"flow '{definition.flow}': the human-followable narrative "
            "body is empty; a flow definition carries BOTH a machine "
            "graph AND human-followable prose (AC.FLOWDEF.1)"
        )

    # AC.FLOWDEF.1 / .3 — every transition must target a declared step.
    for step in definition.steps:
        for target in step.transitions:
            if target not in step_ids:
                raise FlowParseError(
                    f"flow '{definition.flow}': step '{step.id}' "
                    f"transitions to undeclared step '{target}' "
                    "(AC.FLOWDEF.3)"
                )

    # AC.FLOWDEF.1 / .3 — the entry step must exist.
    if definition.entry not in step_ids:
        raise FlowParseError(
            f"flow '{definition.flow}': entry step '{definition.entry}' "
            "is not a declared step (AC.FLOWDEF.3)"
        )

    # AC.FLOWDEF.1 / .3 — every step must be reachable from entry (a
    # walkable graph: no orphaned step).
    reachable = _reachable_from(definition, definition.entry)
    orphans = sorted(step_ids - reachable)
    if orphans:
        raise FlowParseError(
            f"flow '{definition.flow}': step(s) {orphans} are not "
            f"reachable from entry '{definition.entry}'; every step "
            "must be reachable in the walkable graph (AC.FLOWDEF.1)"
        )

    # AC.FLOWDEF.4 (Fork C1) — the not-a-flow ceremony floor. A real
    # flow is a multi-step process with branch / gate points; a flat
    # action-list is not a flow.
    has_branch = any(len(s.transitions) > 1 for s in definition.steps)
    has_gate = bool(definition.gates) or any(
        s.gate for s in definition.steps
    )
    if len(definition.steps) < _MIN_FLOW_STEPS and not (
        has_branch or has_gate
    ):
        raise FlowParseError(
            f"flow '{definition.flow}': this is a flat action-list "
            f"({len(definition.steps)} step(s), no branch points, no "
            "gates), not a multi-step PROCESS — flat checklists are not "
            "admitted as flows (AC.FLOWDEF.4)"
        )


def _reachable_from(definition: FlowDefinition, entry: str) -> set[str]:
    """Return the set of step ids reachable from ``entry`` by walking
    declared transitions (breadth-first; cycle-safe via the visited
    set)."""
    reachable: set[str] = set()
    frontier = [entry]
    while frontier:
        current = frontier.pop()
        if current in reachable:
            continue
        reachable.add(current)
        step = definition.get_step(current)
        if step is None:
            continue
        for target in step.transitions:
            if target not in reachable:
                frontier.append(target)
    return reachable
