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

"""Live-wiring activation — UserPromptSubmit contributors registered + fire
+ chain stays FAIL-OPEN.

This is the activation step the prior keep-pace cycles staged out of their
fences (D-KP1.1 / D-KP7.1, RF-6): the registration onto the
``user_prompt_submit.py`` ``contributors()`` surface. It ladders to the
EXISTING staged ACs rather than naming a new family:

  - AC.KP1.* — the KP1 work-anchored retrieval contributor is registered
    on the UserPromptSubmit chain (its import target is the staged
    ``build_keep_pace_contributor`` factory).
  - AC.KP7.2 — the KP7 #15174 re-assert contributor is registered on the
    same chain (the SessionStart-compact mitigation route).
  - AC.KP0.4 / AC.KP.S.1 — the wired chain stays fail-open-whole-chain: a
    raising / slow contributor still lets the turn proceed, so a broken
    memory contributor can never break the live session.

Method is the builder's call (ODD §1.1): verified at the ``contributors()``
registration layer (names + count), the contributor-fires layer (each
wrapper is invoked and isolates its own failure), and the CLI layer (a
real subprocess run against a cold workspace exits 0 — the live shape).
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

import user_prompt_submit as ups  # noqa: E402
from chain_runner import Contributor, run_chain  # noqa: E402


def test_AC_KP_WIRE_1_both_staged_contributors_registered():
    """The UserPromptSubmit ``contributors()`` surface is no longer empty:
    it registers exactly the two staged contributors (KP1 retrieval, KP7
    re-assert), in chain order, each a ``Contributor``."""
    registered = ups.contributors()
    assert len(registered) == 2, f"expected 2 contributors, got {len(registered)}"
    names = [c.name for c in registered]
    assert names == ["kp1-retrieval", "kp7-reassert"], names
    for c in registered:
        assert isinstance(c, Contributor)
        assert callable(c.fn)


def test_AC_KP_WIRE_1_contributors_fire_through_the_chain():
    """The registered contributors actually RUN when the chain executes:
    each produces a recorded ContributorResult (ok / empty / error /
    timeout — never absent). Proves the wiring is live, not inert."""
    result = run_chain(
        "UserPromptSubmit",
        {"prompt": "continue the litrpg batch"},
        ups.contributors(),
    )
    fired = {r.name for r in result.results}
    assert fired == {"kp1-retrieval", "kp7-reassert"}, fired
    # Every contributor produced a real status (it was invoked, not skipped
    # for being absent). skipped-budget is the only "didn't run" status and
    # must not appear on a fast 2-hop chain.
    for r in result.results:
        assert r.status in {"ok", "empty", "error", "timeout"}, r.status


def test_AC_KP_WIRE_1_chain_stays_fail_open_with_a_raising_wired_contributor():
    """AC.KP0.4 / AC.KP.S.1 — even if a WIRED contributor raises, the chain
    proceeds and a well-behaved sibling still injects. The wiring does not
    weaken the fail-open guarantee."""

    def _raises(_env):
        raise RuntimeError("wired contributor blew up")

    def _good(_env):
        return "STILL_HERE"

    result = run_chain(
        "UserPromptSubmit",
        {"prompt": "x"},
        [Contributor("kp1-retrieval", _raises), Contributor("good", _good)],
    )
    statuses = {r.name: r.status for r in result.results}
    assert statuses["kp1-retrieval"] == "error"
    assert "STILL_HERE" in result.merged_context()


def test_AC_KP_WIRE_1_chain_stays_fail_open_with_a_slow_wired_contributor():
    """AC.KP0.4 / AC.KP.S.1 — a wired contributor that sleeps past its
    per-hook budget is abandoned; the turn is never blocked."""

    def _slow(_env):
        time.sleep(5.0)
        return "never"

    def _good(_env):
        return "STILL_HERE"

    start = time.monotonic()
    result = run_chain(
        "UserPromptSubmit",
        {"prompt": "x"},
        [Contributor("kp1-retrieval", _slow), Contributor("good", _good)],
        per_hook_timeout_s=0.3,
        per_turn_budget_s=2.0,
    )
    elapsed = time.monotonic() - start
    statuses = {r.name: r.status for r in result.results}
    assert statuses["kp1-retrieval"] == "timeout"
    assert elapsed < 2.5, f"chain blocked on wedged wired hook: {elapsed:.2f}s"
    assert "STILL_HERE" in result.merged_context()
    assert "never" not in result.merged_context()


def _run_cli(stdin_bytes: bytes, env_extra: dict | None = None, cwd: str | None = None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(KEEP_PACE_DIR / "user_prompt_submit.py")],
        input=stdin_bytes,
        capture_output=True,
        env=env,
        cwd=cwd,
        timeout=30,
    )


def test_AC_KP_WIRE_1_cli_exits_0_with_real_wired_chain_cold_workspace():
    """The CLI entry — now carrying the LIVE wired contributors — exits 0
    on a real envelope in a cold workspace (no pre-arranged retrieval
    state, no live OBJECTIVES.md; the KP1 seed-fallback + KP7 surface run
    for real). The live shape: a healthy hook on a fresh machine."""
    with tempfile.TemporaryDirectory() as ws:
        envelope = json.dumps(
            {
                "prompt": "continue the litrpg batch",
                "workspace": {"project_dir": ws},
            }
        ).encode()
        proc = _run_cli(
            envelope,
            env_extra={
                "KEEP_PACE_PER_HOOK_TIMEOUT_S": "2.0",
                "KEEP_PACE_PER_TURN_BUDGET_S": "4.0",
            },
            cwd=ws,
        )
        assert proc.returncode == 0, proc.stderr.decode()[-2000:]
        # Any stdout must be a valid UserPromptSubmit hook envelope (or
        # empty on no-match). Never garbage — the live harness parses it.
        out = proc.stdout.decode().strip()
        if out:
            parsed = json.loads(out)
            assert parsed["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit"


def test_AC_KP_WIRE_1_cli_emits_latency_log_line_with_wired_contributors():
    """AC.KP0.5 — the wired chain writes a per-run latency line naming the
    two contributors, so the live per-turn budget is reasoned from real
    numbers (proves the wiring is exercised end-to-end through the CLI)."""
    with tempfile.TemporaryDirectory() as ws:
        log_path = Path(ws) / "latency.log"
        envelope = json.dumps({"prompt": "continue the litrpg batch"}).encode()
        proc = _run_cli(
            envelope,
            env_extra={
                "KEEP_PACE_LATENCY_LOG": str(log_path),
                "KEEP_PACE_PER_HOOK_TIMEOUT_S": "2.0",
                "KEEP_PACE_PER_TURN_BUDGET_S": "4.0",
            },
            cwd=ws,
        )
        assert proc.returncode == 0, proc.stderr.decode()[-2000:]
        assert log_path.exists(), "no latency log written by the wired chain"
        line = json.loads(log_path.read_text().strip().splitlines()[-1])
        logged = {c["name"] for c in line["contributors"]}
        assert logged == {"kp1-retrieval", "kp7-reassert"}, logged
