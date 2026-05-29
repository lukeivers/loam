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

"""Live-wiring activation — PreToolUse draft-gate contributor registered +
fires + chain stays FAIL-OPEN (never blocks a tool call).

This is the activation step the Cycle-3 KP9 build staged out of its fence
(RF-6): the registration onto the ``pre_tool_use.py`` ``contributors()``
surface. It ladders to the EXISTING staged ACs rather than naming a new
family:

  - AC.KP9.* — the KP9 draft-gate contributor is registered on the
    PreToolUse chain (the import target is the staged
    ``build_draft_gate_contributor`` factory). On a leaking draft it
    yields the model-facing report; on a clean draft it is silent.
  - AC.KP9.4 / AC.KP0.4 / AC.KP.S.1 — the wired chain NEVER blocks a tool
    call by erroring: a raising / slow gate still lets the tool proceed
    (the PreToolUse CLI exits 0 on every path), so a broken gate can never
    wedge the live session.

Method is the builder's call (ODD §1.1): verified at the registration
layer, the gate-fires layer (a draft carrying a path leak produces a
model-facing report through the wired contributor), and the CLI layer (a
real subprocess always exits 0 — allow the tool).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
KEEP_PACE_DIR = HOOKS_DIR / "keep_pace"
sys.path.insert(0, str(KEEP_PACE_DIR))

import pre_tool_use as ptu  # noqa: E402
from chain_runner import Contributor, run_chain  # noqa: E402


def test_AC_KP_WIRE_2_draft_gate_contributor_registered():
    """The PreToolUse ``contributors()`` surface is no longer empty: it
    registers the single staged KP9 draft-gate contributor."""
    registered = ptu.contributors()
    assert len(registered) == 1, f"expected 1 contributor, got {len(registered)}"
    assert registered[0].name == "kp9-draft-gate"
    assert isinstance(registered[0], Contributor)
    assert callable(registered[0].fn)


def test_AC_KP_WIRE_2_gate_fires_on_a_leaking_draft():
    """AC.KP9.* — a PreToolUse envelope carrying a user-facing draft with a
    deterministic Layer-1 leak (an absolute path) fires the wired gate and
    produces a NON-empty model-facing report (status=ok, context present).
    Proves the wiring routes a real outbound surface through the gate."""
    envelope = {
        "tool_name": "mcp__plugin_telegram_telegram__reply",
        "tool_input": {
            "message": "I edited /Users/lukeivers/loam/framework/foo.py for you."
        },
    }
    result = run_chain("PreToolUse", envelope, ptu.contributors())
    by_name = {r.name: r for r in result.results}
    gate = by_name["kp9-draft-gate"]
    assert gate.status == "ok", f"gate did not flag the path leak: {gate.status}"
    assert gate.context and gate.context.strip(), "no model-facing report produced"


def test_AC_KP_WIRE_2_gate_silent_on_a_clean_draft():
    """AC.KP9.* — a clean user-facing draft passes the gate silently
    (status=empty, no injection). The wired gate does not over-fire."""
    envelope = {
        "tool_name": "mcp__plugin_telegram_telegram__reply",
        "tool_input": {"message": "All set — your batch is moving along nicely."},
    }
    result = run_chain("PreToolUse", envelope, ptu.contributors())
    gate = {r.name: r for r in result.results}["kp9-draft-gate"]
    assert gate.status == "empty", f"clean draft should be silent, got {gate.status}"


def test_AC_KP_WIRE_2_chain_stays_fail_open_with_a_raising_wired_gate():
    """AC.KP9.4 / AC.KP0.4 / AC.KP.S.1 — even if the wired gate raises, the
    chain proceeds (no exception escapes); the tool is never blocked."""

    def _raises(_env):
        raise RuntimeError("wired gate blew up")

    result = run_chain(
        "PreToolUse",
        {"tool_name": "reply", "tool_input": {"message": "hi"}},
        [Contributor("kp9-draft-gate", _raises)],
    )
    assert {r.name: r.status for r in result.results}["kp9-draft-gate"] == "error"


def _run_cli(stdin_bytes: bytes, env_extra: dict | None = None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(KEEP_PACE_DIR / "pre_tool_use.py")],
        input=stdin_bytes,
        capture_output=True,
        env=env,
        timeout=30,
    )


def test_AC_KP_WIRE_2_cli_exits_0_allow_on_leaking_draft_real_wired_chain():
    """The PreToolUse CLI — now carrying the LIVE wired gate — exits 0
    (ALLOW the tool) even when the draft leaks. The gate is advisory
    (model-facing), never a tool-call block at the substrate (AC.KP9.4 /
    AC.KP0.4): a broken or firing gate never wedges a tool call."""
    envelope = json.dumps(
        {
            "tool_name": "mcp__plugin_telegram_telegram__reply",
            "tool_input": {"message": "see /Users/lukeivers/secret.md"},
        }
    ).encode()
    proc = _run_cli(envelope)
    assert proc.returncode == 0, proc.stderr.decode()[-2000:]


def test_AC_KP_WIRE_2_cli_exits_0_on_garbage_and_clean_real_wired_chain():
    """AC.KP0.4 — the wired CLI exits 0 on garbage stdin AND on a clean
    draft (allow the tool on every path)."""
    assert _run_cli(b"not json {{{").returncode == 0
    clean = json.dumps(
        {"tool_name": "reply", "tool_input": {"message": "looking good"}}
    ).encode()
    assert _run_cli(clean).returncode == 0
