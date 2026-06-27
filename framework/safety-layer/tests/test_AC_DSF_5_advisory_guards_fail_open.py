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

"""AC.DSF.5 (b) — regression guard: advisory guards keep failing OPEN.

The keystone (a) is that the floor destructive gate fails CLOSED. The
other half of AC.DSF.5 is that introducing the per-gate fail-policy
field does NOT regress the existing sealed advisory guards: each one
DECLARES ``FAIL_POLICY = FailPolicy.FAIL_OPEN`` and, on its own
internal fault, still ALLOWS (exit 0, no deny envelope) — the
``D-SECHK.FAIL-OPEN`` convention, preserved. A blanket fail-closed flip
would block all work on any advisory guard's first bug; this proves it
was not flipped.

Both halves are checked at the real entry-point: the declared field is
read off the actual guard module, and the fail-open behaviour is
exercised by driving the real hook as a separate process.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


_HOOKS_DIR = Path(__file__).resolve().parent.parent / "hooks"

ADVISORY_HOOKS = (
    "dangerous_flag_guard",
    "secret_pattern_guard",
    "config_write_guard",
    "wd_discipline_guard",
)


if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

import _fail_policy as FP  # noqa: E402


def _load_guard(name: str) -> ModuleType:
    """Import a guard module by path. Its top level inserts the hooks dir
    on sys.path and binds ``FAIL_POLICY`` — no ``main()`` runs at import.
    Registered in sys.modules so any module-level introspection resolves."""
    if str(_HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(_HOOKS_DIR))
    mod_name = f"{name}_under_test"
    path = _HOOKS_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)
    return mod


def _invoke(name: str, stdin: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(_HOOKS_DIR / f"{name}.py")],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return proc.returncode, proc.stdout


@pytest.mark.parametrize("name", ADVISORY_HOOKS)
def test_advisory_guard_declares_fail_open(name: str) -> None:
    """Each advisory guard declares the FAIL_OPEN policy field — it does
    NOT opt into FAIL_CLOSED."""
    guard = _load_guard(name)
    assert hasattr(guard, "FAIL_POLICY"), f"{name} must declare FAIL_POLICY"
    assert guard.FAIL_POLICY is FP.FailPolicy.FAIL_OPEN


@pytest.mark.parametrize("name", ADVISORY_HOOKS)
def test_advisory_guard_fails_open_on_non_json(name: str) -> None:
    """Non-JSON stdin (a fault) -> exit 0, no deny envelope (fail-open)."""
    rc, out = _invoke(name, "definitely not json {{{")
    assert rc == 0
    assert out == ""


@pytest.mark.parametrize("name", ADVISORY_HOOKS)
def test_advisory_guard_fails_open_on_non_dict_tool_input(
    name: str, tmp_path: Path
) -> None:
    """A malformed envelope (non-dict tool_input) -> exit 0, no deny."""
    envelope = json.dumps(
        {
            "cwd": str(tmp_path),
            "tool_name": "Bash",
            "tool_input": "not-a-dict",
        }
    )
    rc, out = _invoke(name, envelope)
    assert rc == 0
    assert out == ""
