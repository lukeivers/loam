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

"""AC.DOGFOOD.1 — the build-workflow runs on the system.

The build-workflow is expressed as a real flow definition in the format
(it validates, AC.FLOWDEF.2), and its cursor (today's hand-maintained
build-cursor.md) is driven as a persisted cursor: a cursor read off the
flow resolves to the SAME position the manual build-cursor.md block
names today.
"""

from __future__ import annotations

import re
from pathlib import Path

from loam_cli.flows.cursor import read_cursor, resolve_cursor
from loam_cli.flows.format import parse_flow_definition
from loam_cli.flows.pause import position_check

REPO_ROOT = Path(__file__).resolve().parents[4]
FLOW_DEF = REPO_ROOT / "docs" / "flows" / "loam-vnext-build.flow.md"
FLOW_CURSOR = REPO_ROOT / "docs" / "flows" / "loam-vnext-build.cursor.yaml"
MANUAL_CURSOR = REPO_ROOT / "docs" / "plans" / "build-cursor.md"


def test_AC_DOGFOOD_1_build_workflow_validates_and_cursor_resolves() -> None:
    """AC.DOGFOOD.1 — the dogfood flow validates and its persisted
    cursor resolves to the same position the manual build-cursor.md
    block names today (slice P1.3, step 5 INTEGRATE+RECORD)."""
    # The flow definition validates (AC.FLOWDEF.2 against the real file).
    definition = parse_flow_definition(FLOW_DEF.read_text(encoding="utf-8"))
    assert definition.flow == "loam-vnext-build"

    # The persisted cursor read off disk resolves positively.
    cursor = read_cursor(FLOW_CURSOR)
    assert cursor is not None
    resolution = resolve_cursor(cursor, definition)
    assert resolution.resolved, resolution.reason

    # It resolves to step 5 INTEGRATE+RECORD (the machine-graph node
    # integrate_record) — the SAME step the manual build-cursor.md names.
    assert resolution.step == "integrate_record"

    # Cross-check against the manual cursor block's STEP line: it names
    # "5 INTEGRATE+RECORD". The persisted cursor must agree.
    manual = MANUAL_CURSOR.read_text(encoding="utf-8")
    step_line = re.search(r"STEP:\s*(.+)", manual)
    assert step_line is not None
    assert "INTEGRATE+RECORD" in step_line.group(1)
    assert "INTEGRATE+RECORD" in resolution.step_name

    # And the manual block names slice P1.3 — the persisted cursor's
    # branch-state carries the same slice.
    assert "P1.3" in cursor.branch_state

    # The pause-check passes (a positive one-sentence restatement).
    decision = position_check(resolution)
    assert not decision.paused
    assert "loam-vnext-build" in decision.one_sentence
