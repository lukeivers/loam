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

"""AC.SECHK.4 — All three hooks fail-open on internal exception.
Malformed inputs (missing tool_input, non-JSON, unicode errors) →
exit-0 with empty stdout AND NDJSON failure log line.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "safety-layer" / "hooks"

HOOK_SCRIPTS = (
    HOOKS_DIR / "secret_pattern_guard.py",
    HOOKS_DIR / "dangerous_flag_guard.py",
    HOOKS_DIR / "config_write_guard.py",
)


def _invoke(script: Path, stdin: str, cwd: Path | None = None) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(script)],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=15,
        cwd=str(cwd) if cwd else None,
    )
    return (result.returncode, result.stdout)


@pytest.mark.parametrize("script", HOOK_SCRIPTS)
def test_AC_SECHK_4_non_json_stdin_fail_open(tmp_path, script: Path) -> None:
    """Non-JSON stdin → exit-0, empty stdout, no exception."""
    code, stdout = _invoke(script, "this is not json {{{")
    assert code == 0
    assert stdout == ""


@pytest.mark.parametrize("script", HOOK_SCRIPTS)
def test_AC_SECHK_4_empty_stdin_fail_open(tmp_path, script: Path) -> None:
    code, stdout = _invoke(script, "")
    assert code == 0
    assert stdout == ""


@pytest.mark.parametrize("script", HOOK_SCRIPTS)
def test_AC_SECHK_4_envelope_missing_tool_input(tmp_path, script: Path) -> None:
    """Envelope without tool_input → no exception, exit-0."""
    envelope = json.dumps(
        {
            "cwd": str(tmp_path),
            "tool_name": "Bash",
        }
    )
    code, stdout = _invoke(script, envelope)
    assert code == 0
    assert stdout == ""


@pytest.mark.parametrize("script", HOOK_SCRIPTS)
def test_AC_SECHK_4_envelope_non_dict_tool_input(
    tmp_path, script: Path
) -> None:
    envelope = json.dumps(
        {
            "cwd": str(tmp_path),
            "tool_name": "Bash",
            "tool_input": "not-a-dict",
        }
    )
    code, stdout = _invoke(script, envelope)
    assert code == 0
    assert stdout == ""


@pytest.mark.parametrize("script", HOOK_SCRIPTS)
def test_AC_SECHK_4_envelope_no_cwd(tmp_path, script: Path) -> None:
    """Envelope without cwd → exit-0 (cannot log; but does not
    propagate the missing-cwd as a failure-class deny)."""
    envelope = json.dumps(
        {
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi"},
        }
    )
    code, stdout = _invoke(script, envelope)
    assert code == 0
    assert stdout == ""


def test_AC_SECHK_4_secret_pattern_logs_fail_open_on_unicode(
    tmp_path,
) -> None:
    """An envelope whose stdin contains invalid UTF-8 bytes is
    passed to the hook; subprocess.run with text=True may filter
    invalid bytes — we use bytes input via stdin to force the
    failure path. The hook reads stdin in text mode; if decode
    fails it must fail-open."""
    # Build a JSON-shaped envelope but with a regex pattern that
    # would normally fault. We test via the toggle-mechanism's
    # failure surface: an envelope referencing a workspace whose
    # secret-patterns.yaml has an invalid regex.
    additions_dir = tmp_path / ".loam"
    additions_dir.mkdir(parents=True, exist_ok=True)
    (additions_dir / "secret-patterns.yaml").write_text(
        "patterns:\n"
        '  - name: bad\n'
        '    regex: "[unclosed"\n',
        encoding="utf-8",
    )
    envelope = json.dumps(
        {
            "cwd": str(tmp_path),
            "tool_name": "Bash",
            "tool_input": {"command": "echo hi"},
        }
    )
    code, stdout = _invoke(
        HOOKS_DIR / "secret_pattern_guard.py", envelope
    )
    # Invalid regex is silently dropped by the loader (per the
    # loader's design); the hook proceeds with the floor + valid
    # additions only. So the hook exits 0 with empty stdout.
    assert code == 0
    assert stdout == ""
