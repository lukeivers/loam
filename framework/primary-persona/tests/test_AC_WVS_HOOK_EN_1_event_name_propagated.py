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

"""AC.WVS-HOOK-EN.1 / AC.WVS-HOOK-EN.3 — hookEventName propagated from
envelope to hookSpecificOutput.

AC.WVS-HOOK-EN.1: For each of the 4 registered event types
(SessionStart / PreCompact / UserPromptSubmit / PostToolUse) and the
normal return path (workspace root resolvable, in-context block returned),
when ``hook_event_name`` is present in the envelope, ``run()`` returns a
dict with ``hookSpecificOutput.hookEventName == envelope["hook_event_name"]``.

AC.WVS-HOOK-EN.3: When the envelope carries a valid ``hook_event_name``
but the workspace root cannot be resolved (workspace-root-missing path),
``run()`` still returns ``hookSpecificOutput`` with the correct
``hookEventName`` (and empty ``additionalContext``).

Plan: docs/plans/wvs-hook-event-name-fix.md §5.
"""

from __future__ import annotations

import pytest
from pathlib import Path

import loam.primary_persona.hooks_work_visibility as hook_mod

_REGISTERED_EVENTS = [
    "SessionStart",
    "PreCompact",
    "UserPromptSubmit",
    "PostToolUse",
]


@pytest.mark.parametrize("event_name", _REGISTERED_EVENTS)
def test_AC_WVS_HOOK_EN_1_event_name_in_hookspecificoutput_normal_path(
    event_name: str, tmp_path: Path
) -> None:
    """AC.WVS-HOOK-EN.1 — normal return path (workspace root resolvable).

    For each registered event type, hookSpecificOutput.hookEventName must
    equal the envelope's hook_event_name. Regression for the production bug
    where hookEventName was absent and Claude Code rejected the output.
    """
    envelope = {
        "hook_event_name": event_name,
        "workspace": {"project_dir": str(tmp_path)},
    }
    output = hook_mod.run(envelope)

    assert "hookSpecificOutput" in output, (
        f"hookSpecificOutput missing for event {event_name!r} — "
        "this is the production bug: Claude Code rejects output without it"
    )
    hso = output["hookSpecificOutput"]
    assert "hookEventName" in hso, (
        f"hookEventName missing from hookSpecificOutput for event {event_name!r} — "
        "Claude Code requires this field"
    )
    assert hso["hookEventName"] == event_name, (
        f"hookEventName {hso['hookEventName']!r} != envelope event {event_name!r}"
    )
    assert "additionalContext" in hso, (
        "additionalContext field must still be present alongside hookEventName"
    )


@pytest.mark.parametrize("event_name", _REGISTERED_EVENTS)
def test_AC_WVS_HOOK_EN_3_event_name_propagated_on_root_missing_path(
    event_name: str,
) -> None:
    """AC.WVS-HOOK-EN.3 — workspace-root-missing return path.

    When the envelope carries a valid hook_event_name but neither
    workspace.project_dir nor cwd is present, run() returns hookSpecificOutput
    with hookEventName equal to the event name and empty additionalContext.
    """
    envelope = {"hook_event_name": event_name}  # no workspace / cwd
    output = hook_mod.run(envelope)

    assert "hookSpecificOutput" in output, (
        f"hookSpecificOutput missing on root-missing path for event {event_name!r}"
    )
    hso = output["hookSpecificOutput"]
    assert hso["hookEventName"] == event_name
    assert hso["additionalContext"] == ""
