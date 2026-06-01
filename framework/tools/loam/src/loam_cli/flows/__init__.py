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

"""Defined-workflow system — flow definitions, the persisted position
cursor, the pause-if-lost structural check, and the re-injection hook.

Plan: ``docs/plans/defined-workflow-system-and-position-cursor-plan.md``
(P2.3). Builds the structural answer to the FM.PROCESS-DRIFT failure
class (process-deviation-under-pressure): a real multi-step process is
written as a FLOW with an explicit current-POSITION cursor that survives
context-loss, and "if you cannot say where you are, PAUSE" becomes a
structural gate rather than prose.

Four composable pieces, behind one tight fence (plan §1):

  - ``format`` — the FLOW-DEFINITION format (AC.FLOWDEF.*): a
    YAML-frontmatter + Markdown-body artefact carrying BOTH a
    machine-walkable node graph and human-followable narrative.
  - ``cursor`` — the PERSISTED POSITION CURSOR (AC.CURSOR.*): a
    ``{flow, step, branch-state, updated-at}`` record, write /
    advance / resolve / stale-detect.
  - ``pause`` — the PAUSE-IF-LOST structural check (AC.PAUSE.*): a
    positive-resolution gate — lost is the DEFAULT until position is
    positively re-established.
  - ``reinject`` — the re-injection hook entry-point (AC.REINJECT.1,
    outcome-altitude): reads the cursor from disk and emits the
    position block (or the PAUSE directive) into ``additionalContext``
    at a real context-loss point, the way Claude Code invokes it.

The ``cli`` module registers the ``loam flow`` verb (the production
entry-point) with the unified ``loam`` CLI dispatcher.
"""

from __future__ import annotations

from loam_cli.flows.cursor import (
    Cursor,
    CursorResolution,
    advance_cursor,
    read_cursor,
    resolve_cursor,
    write_cursor,
)
from loam_cli.flows.format import (
    FlowDefinition,
    FlowParseError,
    parse_flow_definition,
    validate_flow_definition,
)
from loam_cli.flows.pause import PauseDecision, position_check

__all__ = [
    "Cursor",
    "CursorResolution",
    "FlowDefinition",
    "FlowParseError",
    "PauseDecision",
    "advance_cursor",
    "parse_flow_definition",
    "position_check",
    "read_cursor",
    "resolve_cursor",
    "validate_flow_definition",
    "write_cursor",
]
