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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

"""AC.A.1 — packaged invocability (one persona-invocable capability).

Plan: docs/plans/handsoff-loop-real-build.md (§3 AC.A.1)

The orchestration is invocable by the primary persona as a SINGLE
capability — no human hand-driving decompose/dispatch/judge.
Satisfiable by a skill, a plugin, a composed wiring, or another
packaging (multiple methods — scope is tight, not method-bound).
This build's method: a CLI (`handsoff-loop`) + a delegating SKILL.

Deterministic structural test (no real claude — the real-task run is
the AC.A.4 phase end-test).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PKG_SRC = ROOT / "framework" / "tools" / "handsoff-loop" / "src"
SKILL = (
    ROOT / "plugins" / "loam-skills" / "skills" / "handsoff-loop"
    / "SKILL.md"
)

sys.path.insert(0, str(PKG_SRC))


def test_single_entrypoint_describe_runs() -> None:
    """`handsoff-loop describe` returns the capability contract.

    The persona invokes ONE command; this proves the single
    capability surface exists and self-describes.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "handsoff_loop.cli", "describe"],
        cwd=str(PKG_SRC), capture_output=True, text=True,
        env={"PYTHONPATH": str(PKG_SRC), "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0, proc.stderr
    contract = json.loads(proc.stdout)
    assert contract["capability"] == "handsoff-loop"
    # AC.FOUND.0 is structurally carried in the contract.
    assert any("AC.FOUND.0" in c for c in contract["composes"])
    # Phases A/B/C are the named capability surface.
    assert set(contract["phases"]) == {"A", "B", "C"}


def test_skill_bundle_delegates_not_reimplements() -> None:
    """The SKILL is the persona packaging and delegates to the CLI.

    A capability the persona invokes as one unit (VALUE_PROPOSITION
    harness test).  The SKILL must reference the CLI, not re-implement
    decompose/dispatch/judge in markdown.
    """
    body = SKILL.read_text(encoding="utf-8")
    assert "handsoff-loop run" in body, "SKILL must invoke the CLI"
    assert "handsoff-loop describe" in body
    assert body.startswith("---"), "SKILL needs frontmatter to auto-surface"
    assert "description:" in body.split("---")[1]


def test_run_subcommand_has_no_human_loop_driving_surface() -> None:
    """`run` exposes objective+frozen+dirs only — no per-turn human knob.

    AC.A.1: no human hand-drives the loop.  The CLI surface must not
    expose a "next turn" / "approve sub-task" interactive knob; the
    loop is driven by /goal + the orchestrator, not the operator.
    """
    cli_src = (PKG_SRC / "handsoff_loop" / "cli.py").read_text()
    assert "--objective" in cli_src and "--frozen" in cli_src
    for forbidden in ("--next-turn", "--approve-subtask",
                      "input(", "--step"):
        assert forbidden not in cli_src, (
            f"{forbidden!r} is a human-loop-driving surface — AC.A.1 "
            f"requires no human driving decompose/dispatch/judge"
        )
