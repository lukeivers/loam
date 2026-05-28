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

"""AC.KP0.5 — per-hook latency observable.

The chain logs per-contributor wall-clock latency + the per-turn total
to a structured (JSON-line) latency log, so the per-turn budget can be
reasoned about from loam's OWN numbers (the design's $0/45ms are
claude-mem's, not loam's — RF-5).

Method is the builder's call (ODD §1.1): verified at both the
``run_chain``/``_write_latency_log`` layer and the CLI entry-point layer
(the log path resolves and a line lands after a real subprocess run).
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


def _good(_envelope: dict):
    return "CTX"


def test_AC_KP0_5_chain_result_carries_per_contributor_latency():
    """Each contributor result carries a non-negative latency_ms and the
    chain carries a total — the per-turn budget is reasoned from these."""
    result = run_chain(
        "UserPromptSubmit",
        {},
        [Contributor("a", _good), Contributor("b", _good)],
    )
    assert len(result.results) == 2
    for r in result.results:
        assert r.latency_ms >= 0.0
    assert result.total_latency_ms >= 0.0


def test_AC_KP0_5_latency_log_line_written_with_per_hook_numbers():
    """A JSON line lands in the latency log carrying the event, the
    per-turn total, and per-contributor name+status+latency_ms."""
    with tempfile.TemporaryDirectory() as td:
        log = os.path.join(td, "nested", "hook-latency.log")
        run_chain(
            "UserPromptSubmit",
            {},
            [Contributor("a", _good)],
            latency_log_path=log,
        )
        assert os.path.exists(log)
        lines = [l for l in Path(log).read_text().splitlines() if l.strip()]
        assert len(lines) == 1
        rec = json.loads(lines[0])
        assert rec["event"] == "UserPromptSubmit"
        assert "total_latency_ms" in rec
        assert rec["contributors"][0]["name"] == "a"
        assert "latency_ms" in rec["contributors"][0]
        assert rec["contributors"][0]["status"] == "ok"


def test_AC_KP0_5_cli_run_writes_latency_log():
    """A real CLI subprocess run resolves the latency-log path (via the
    KEEP_PACE_LATENCY_LOG override) and appends a line — latency is
    observable end-to-end, not just in-process."""
    with tempfile.TemporaryDirectory() as td:
        log = os.path.join(td, "hook-latency.log")
        env = dict(os.environ)
        env["KEEP_PACE_LATENCY_LOG"] = log
        envelope = json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "hi"})
        proc = subprocess.run(
            [sys.executable, str(KEEP_PACE_DIR / "user_prompt_submit.py")],
            input=envelope.encode(),
            capture_output=True,
            env=env,
            timeout=20,
        )
        assert proc.returncode == 0
        assert os.path.exists(log), "CLI run did not write the latency log"
        rec = json.loads(Path(log).read_text().splitlines()[0])
        assert rec["event"] == "UserPromptSubmit"
        # KP0 ships zero contributors — the log proves the chain ran and
        # is observable even with an empty contributor list.
        assert isinstance(rec["contributors"], list)
        assert rec["total_latency_ms"] >= 0.0


def test_AC_KP0_5_default_latency_log_path_resolves_under_scratch():
    """The default log path resolves under the workspace .scratch dir
    (a gitignored runtime artefact, never committed source)."""
    from chain_runner import default_latency_log_path

    p = default_latency_log_path({"workspace": {"project_dir": "/tmp/ws"}})
    assert p is not None
    assert ".scratch" in p
    assert p.endswith("hook-latency.log")
