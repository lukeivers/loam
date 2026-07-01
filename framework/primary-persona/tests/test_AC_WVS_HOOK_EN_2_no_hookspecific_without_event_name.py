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

"""AC.WVS-HOOK-EN.2 / AC.WVS-HOOK-EN.4 — no hookSpecificOutput when
hook_event_name is absent; exception/fail-closed path integrity.

AC.WVS-HOOK-EN.2: When ``hook_event_name`` is absent from the envelope (or
is not a non-empty string), ``run()`` returns ``{}`` — no ``hookSpecificOutput``
— regardless of which return path fires. Emitting a malformed partial dict is
worse than emitting nothing (D-EN.3).

AC.WVS-HOOK-EN.4: When an exception fires inside the ``try`` block (exception/
fail-closed path), the except handler returns a correct dict when the event
name is known (hookSpecificOutput + hookEventName), or ``{}`` when unknown.
Always exits 0.

Plan: docs/plans/wvs-hook-event-name-fix.md §5.
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest.mock
from pathlib import Path

import pytest

import loam.primary_persona.hooks_work_visibility as hook_mod


# ---- AC.WVS-HOOK-EN.2 — no hookSpecificOutput without event name ----


_NO_EVENT_NAME_ENVELOPES = [
    pytest.param({}, id="empty-envelope"),
    pytest.param({"garbage": True}, id="garbage-no-event"),
    pytest.param({"hook_event_name": ""}, id="empty-string-event"),
    pytest.param({"hook_event_name": None}, id="none-event"),
    pytest.param({"hook_event_name": 42}, id="int-event"),
    pytest.param(
        {"workspace": {"project_dir": "/some/path"}},
        id="has-workspace-no-event",
    ),
]


@pytest.mark.parametrize("envelope", _NO_EVENT_NAME_ENVELOPES)
def test_AC_WVS_HOOK_EN_2_no_hookspecificoutput_when_event_name_absent(
    envelope: dict,
) -> None:
    """AC.WVS-HOOK-EN.2 — any envelope without a non-empty string
    hook_event_name produces {} from run() (no hookSpecificOutput).

    Emitting hookSpecificOutput without hookEventName would repeat the
    production bug; the correct fallback is the empty dict.
    """
    output = hook_mod.run(envelope)
    assert output == {}, (
        f"Expected {{}} but got {output!r} for envelope {envelope!r}. "
        "A partial hookSpecificOutput without hookEventName is the bug we fixed."
    )


# ---- AC.WVS-HOOK-EN.4 — exception path ----


def test_AC_WVS_HOOK_EN_4_exception_path_with_event_name_present(
    tmp_path: Path,
) -> None:
    """AC.WVS-HOOK-EN.4 (event name present) — when an exception fires
    inside run()'s try block, the except handler still returns a well-formed
    hookSpecificOutput with hookEventName. Never raises.

    Triggers the exception by patching _resolve_workspace_root to raise.
    """
    envelope = {
        "hook_event_name": "PostToolUse",
        "workspace": {"project_dir": str(tmp_path)},
    }
    with unittest.mock.patch.object(
        hook_mod, "_resolve_workspace_root", side_effect=RuntimeError("injected")
    ):
        output = hook_mod.run(envelope)

    assert "hookSpecificOutput" in output
    hso = output["hookSpecificOutput"]
    assert hso["hookEventName"] == "PostToolUse"
    assert hso["additionalContext"] == ""


def test_AC_WVS_HOOK_EN_4_exception_path_with_event_name_absent() -> None:
    """AC.WVS-HOOK-EN.4 (event name absent) — when an exception fires and
    hook_event_name is not in the envelope, the except handler returns {}.
    Never raises.
    """
    envelope = {"workspace": {"project_dir": "/some/path"}}  # no hook_event_name
    with unittest.mock.patch.object(
        hook_mod, "_resolve_workspace_root", side_effect=RuntimeError("injected")
    ):
        output = hook_mod.run(envelope)

    assert output == {}


def test_AC_WVS_HOOK_EN_4_cli_exits_zero_no_event_name(tmp_path: Path) -> None:
    """AC.WVS-HOOK-EN.4 (CLI exit 0) — the CLI always exits 0 even when
    hook_event_name is absent. The output is valid JSON ({}).
    """
    component_root = Path(hook_mod.__file__).resolve().parents[3]
    hook_path = component_root / "hooks" / "work_visibility_hook.py"
    assert hook_path.exists(), f"hook script not found at {hook_path}"

    envelope = json.dumps({"cwd": str(tmp_path)})  # no hook_event_name
    proc = subprocess.run(
        [sys.executable, str(hook_path)],
        input=envelope,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    payload = json.loads(proc.stdout)
    assert payload == {}
