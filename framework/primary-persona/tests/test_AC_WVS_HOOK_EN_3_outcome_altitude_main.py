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

"""AC.WVS-HOOK-EN.5 ★ (outcome-altitude) — realistic UserPromptSubmit
envelope through main(), the exact production failure.

Drives the complete production entry-point (main()) with a UserPromptSubmit
envelope carrying a non-empty work-visibility state. The stdout JSON must have
``hookSpecificOutput.hookEventName == "UserPromptSubmit"`` and
``additionalContext`` non-empty.

outcome-altitude:true: this test drives the real production entry-point
(main() — the identical path Claude Code takes when spawning the hook) with
a realistic envelope. No scaffolding beyond the envelope shape. The in-context
block is non-empty because tmp_path is a fresh workspace that the aggregator
populates with the idle-state line (nothing running → still produces a block).

STUB-class tests DO NOT satisfy this AC.

Plan: docs/plans/wvs-hook-event-name-fix.md §5.
"""

from __future__ import annotations

import io
import json
import sys
import unittest.mock
from pathlib import Path

import loam.primary_persona.hooks_work_visibility as hook_mod
from loam.primary_persona.work_visibility_presenters import IN_CONTEXT_MARKER

from _helpers_d40 import FakeTrackerClient, make_projection


def test_AC_WVS_HOOK_EN_5_outcome_altitude_userpromptsubmit_main(
    tmp_path: Path,
) -> None:
    """AC.WVS-HOOK-EN.5 ★ — the exact production failure path.

    A realistic UserPromptSubmit envelope (workspace root + hook_event_name)
    carrying a non-empty work-visibility state is fed through main() — the
    same function Claude Code calls when it spawns the hook binary. The
    stdout JSON must satisfy the hookEventName contract.

    This is the regression test that would have caught the production bug:
    main() reads the envelope from stdin, calls run(), and prints the output.
    Before the fix, hookEventName was absent and Claude Code rejected it.
    """
    # A realistic envelope: the workspace points to tmp_path (a fresh dir
    # the aggregator will render as "nothing running" — still non-empty).
    envelope = {
        "hook_event_name": "UserPromptSubmit",
        "workspace": {"project_dir": str(tmp_path)},
    }

    # Capture stdout from main() — same as Claude Code capturing the hook's
    # stdout. Feed the envelope via stdin.
    captured = io.StringIO()
    stdin_data = json.dumps(envelope)

    with (
        unittest.mock.patch("sys.stdin", io.StringIO(stdin_data)),
        unittest.mock.patch("sys.stdout", captured),
    ):
        exit_code = hook_mod.main()

    # Fail-closed: always exits 0 (AC.WVS-FRESH.2).
    assert exit_code == 0, f"main() must exit 0 (fail-closed); got {exit_code}"

    # The stdout must be valid JSON.
    raw = captured.getvalue()
    assert raw, "main() must print something to stdout"
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"main() printed invalid JSON: {raw!r}") from exc

    # The output must carry hookSpecificOutput with hookEventName.
    assert "hookSpecificOutput" in payload, (
        f"hookSpecificOutput missing from payload {payload!r}. "
        "This is the exact production bug: Claude Code rejects this output."
    )
    hso = payload["hookSpecificOutput"]
    assert "hookEventName" in hso, (
        f"hookEventName missing from hookSpecificOutput {hso!r}. "
        "Claude Code error: hookSpecificOutput is missing required field hookEventName."
    )
    assert hso["hookEventName"] == "UserPromptSubmit", (
        f"hookEventName {hso['hookEventName']!r} != 'UserPromptSubmit'"
    )

    # The additionalContext must be non-empty (tmp_path is a real workspace;
    # the aggregator produces a block even with no active tasks).
    assert "additionalContext" in hso, "additionalContext field must be present"
    assert hso["additionalContext"], (
        "additionalContext must be non-empty — the aggregator always produces "
        "a block for a valid workspace (idle state still renders)"
    )
    # The in-context marker confirms the block comes from the real presenter.
    assert IN_CONTEXT_MARKER in hso["additionalContext"], (
        f"IN_CONTEXT_MARKER {IN_CONTEXT_MARKER!r} not found in additionalContext — "
        "the presenter did not run, or the block is malformed"
    )


def test_AC_WVS_HOOK_EN_5_outcome_altitude_with_active_work(
    tmp_path: Path,
) -> None:
    """AC.WVS-HOOK-EN.5 ★ — production path with genuine active work state.

    Drives the FULL main() path with a non-trivial work state (1 active task +
    1 owner-pending task) injected via in_context_block's tracker_factory kwarg
    — patched at the presenter module level so the lazy import inside run()
    picks it up. Confirms (a) hookEventName propagates, and (b) additionalContext
    carries the live work state (not just the idle render).
    """
    envelope = {
        "hook_event_name": "UserPromptSubmit",
        "workspace": {"project_dir": str(tmp_path)},
    }

    fake_tracker = FakeTrackerClient(
        query_result=(
            make_projection("t1", status="active"),
            make_projection("t2", status="owner_pending"),
        )
    )

    import loam.primary_persona.work_visibility_presenters as presenters_mod

    # Wrap in_context_block so it always uses the fake tracker, regardless
    # of the tracker_factory kwarg the caller provides.
    _real_in_context_block = presenters_mod.in_context_block

    def _fake_in_context_block(workspace_root, **kwargs):
        return _real_in_context_block(
            workspace_root, tracker_factory=lambda: fake_tracker
        )

    captured = io.StringIO()
    stdin_data = json.dumps(envelope)

    with (
        unittest.mock.patch("sys.stdin", io.StringIO(stdin_data)),
        unittest.mock.patch("sys.stdout", captured),
        unittest.mock.patch.object(
            presenters_mod,
            "in_context_block",
            _fake_in_context_block,
        ),
    ):
        exit_code = hook_mod.main()

    assert exit_code == 0
    payload = json.loads(captured.getvalue())
    assert "hookSpecificOutput" in payload
    hso = payload["hookSpecificOutput"]
    assert hso["hookEventName"] == "UserPromptSubmit"
    assert IN_CONTEXT_MARKER in hso["additionalContext"]
    # Active work state renders into the block.
    assert "working on 1" in hso["additionalContext"].lower()
