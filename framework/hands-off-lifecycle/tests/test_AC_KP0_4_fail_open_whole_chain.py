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

"""AC.KP0.4 — fail-open-whole-chain on hook timeout/crash.

A deliberately-failing (raising) or sleeping-past-budget contributor
must NOT break the chain: the turn proceeds (the hook exits 0), and any
well-behaved contributor still injects its context. This is the
structural guarantee that a broken memory hook never breaks the live
session.

Also exercises AC.KP.S.1's structural half: the chain is allow/proceed
by default; no contributor failure mode can wedge the session.

Method is the builder's call (ODD §1.1): verified at both the in-process
``run_chain`` layer and the CLI entry-point layer (a subprocess that must
exit 0 even when its stdin is garbage).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOOKS_DIR = REPO_ROOT / "framework" / "hands-off-lifecycle" / "hooks"
KEEP_PACE_DIR = HOOKS_DIR / "keep_pace"
sys.path.insert(0, str(KEEP_PACE_DIR))

from chain_runner import (  # noqa: E402
    Contributor,
    run_chain,
)


def _raising(_envelope: dict):
    raise RuntimeError("deliberate contributor crash")


def _sleeping(_envelope: dict):
    time.sleep(5.0)  # well past any sane per-hook budget
    return "should-never-be-injected"


def _good(_envelope: dict):
    return "GOOD_CONTEXT"


def _non_string(_envelope: dict):
    return {"not": "a string"}


def test_AC_KP0_4_raising_contributor_chain_still_proceeds():
    """A contributor that raises is isolated; the chain returns cleanly
    and a sibling good contributor still injects."""
    result = run_chain(
        "UserPromptSubmit",
        {},
        [Contributor("crasher", _raising), Contributor("good", _good)],
    )
    statuses = {r.name: r.status for r in result.results}
    assert statuses["crasher"] == "error"
    assert statuses["good"] == "ok"
    assert "GOOD_CONTEXT" in result.merged_context()


def test_AC_KP0_4_sleeping_contributor_times_out_chain_proceeds():
    """A contributor sleeping past its per-hook budget is abandoned
    (status=timeout); the chain still finishes and a good sibling
    still injects. The turn is never blocked on the wedged hook."""
    start = time.monotonic()
    result = run_chain(
        "UserPromptSubmit",
        {},
        [Contributor("sleeper", _sleeping), Contributor("good", _good)],
        per_hook_timeout_s=0.3,
        per_turn_budget_s=2.0,
    )
    elapsed = time.monotonic() - start
    statuses = {r.name: r.status for r in result.results}
    assert statuses["sleeper"] == "timeout"
    assert statuses["good"] == "ok"
    # The sleeper slept 5s but the chain returned well under that.
    assert elapsed < 2.5, f"chain blocked on wedged hook: {elapsed:.2f}s"
    assert "should-never-be-injected" not in result.merged_context()
    assert "GOOD_CONTEXT" in result.merged_context()


def test_AC_KP0_4_non_string_contributor_isolated():
    """A contributor returning a non-string is a bug; it is isolated as
    an error, not injected, and the chain proceeds."""
    result = run_chain(
        "UserPromptSubmit",
        {},
        [Contributor("bad", _non_string), Contributor("good", _good)],
    )
    statuses = {r.name: r.status for r in result.results}
    assert statuses["bad"] == "error"
    assert "GOOD_CONTEXT" in result.merged_context()


def test_AC_KP0_4_per_turn_budget_skips_remaining():
    """Once the per-turn budget is crossed, remaining contributors are
    skipped (status=skipped-budget) rather than run — the whole chain is
    bounded, not just each hop."""
    result = run_chain(
        "UserPromptSubmit",
        {},
        [
            Contributor("slow1", _sleeping),
            Contributor("slow2", _sleeping),
            Contributor("good", _good),
        ],
        per_hook_timeout_s=0.4,
        per_turn_budget_s=0.5,
    )
    statuses = [r.status for r in result.results]
    # At least one later contributor must be skipped by the budget.
    assert "skipped-budget" in statuses


def test_AC_KP0_4_run_chain_never_raises_on_garbage_contributors():
    """A non-callable / malformed contributor object must not crash the
    runner — the whole-chain guarantee holds even against a bad chain."""
    bogus = object()  # no .name, no .fn
    result = run_chain("UserPromptSubmit", {}, [bogus, Contributor("good", _good)])
    # The good one still ran; the runner did not raise.
    assert "GOOD_CONTEXT" in result.merged_context()


def _run_cli(entry: str, stdin_bytes: bytes, env_extra: dict | None = None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, str(KEEP_PACE_DIR / entry)],
        input=stdin_bytes,
        capture_output=True,
        env=env,
        timeout=20,
    )
    return proc


def test_AC_KP0_4_user_prompt_submit_cli_exits_0_on_garbage_stdin():
    """The UserPromptSubmit CLI entry must exit 0 even on garbage stdin
    (fail-open) — a malformed envelope never breaks the turn."""
    proc = _run_cli("user_prompt_submit.py", b"not json at all {{{")
    assert proc.returncode == 0
    # Nothing injected on a no-contributor / bad-input chain (silent).
    assert proc.stdout.strip() == b""


def test_AC_KP0_4_pre_tool_use_cli_exits_0_on_garbage_stdin():
    """The PreToolUse CLI entry must exit 0 (allow the tool) on garbage
    stdin — a broken memory hook never blocks a tool call."""
    proc = _run_cli("pre_tool_use.py", b"\x00\x01 not json")
    assert proc.returncode == 0


def test_AC_KP0_4_user_prompt_submit_cli_exits_0_on_empty_stdin():
    """Empty stdin → clean exit, no injection."""
    proc = _run_cli("user_prompt_submit.py", b"")
    assert proc.returncode == 0
    assert proc.stdout.strip() == b""
