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

"""AC.LIPW.4 — a programmatic driver can stand up a fresh
persona-active loam instance and drive an INTERACTIVE `claude`
session in it to completion with a supplied first-user-turn prompt,
capturing the full multi-turn transcript and any emitted FILE blocks
— exercising the persona + agentic loop (observably multi-turn),
NOT single-pass `claude -p` codegen.

Plan: docs/plans/loam-init-persona-wiring-and-isolated-subloam-driver.md
Ladders to AC.PO.2 (harness-toolkit — a reusable real-loam driver).

Verification (outcome-shape): the driver, given the frozen
`build_prompt(task)`, returns a transcript with >1 effective turn +
distinguishable from a `run_raw_llm`-shape single-pass output. The
real-`claude`-binary turn-boundary detection is exercised by the
opt-in integration test (PB_SUBLOAM_REAL_CLAUDE=1); the structural
contract (PTY harness, multi-turn detection, FILE-block extraction,
production bootstrap with service_bootstrap NOT True) is exercised
unconditionally with a stub claude.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[3]
        / "framework"
        / "tools"
        / "subloam-driver"
        / "src"
    ),
)

from subloam_driver import (  # noqa: E402
    DriverResult,
    IsolationConfig,
    SubLoamDriver,
)
from subloam_driver.driver import (  # noqa: E402
    _count_effective_turns,
    _extract_file_blocks,
)

LOAM_ROOT = Path(__file__).resolve().parents[3]


def _isolation(tmp_path: Path) -> IsolationConfig:
    return IsolationConfig(
        claude_config_dir=tmp_path / ".claude-home",
        empty_mcp_config_path=tmp_path / "empty.mcp.json",
        workspace_slug="pb-subloam-test",
    )


# ---- structural contract (unconditional) ----------------------------


def test_AC_LIPW_4_multiturn_detection_distinguishes_single_pass() -> None:
    """A single-pass `claude -p`-shape output (one block, no
    interactive turn markers) is NOT multi-turn; an interactive
    multi-turn transcript IS."""
    single_pass = "FILE: a.py\nprint('x')\n"  # run_raw_llm shape
    multi_turn = (
        "> implement the task\n"
        "⏺ I'll restate this as objective + constraints.\n"
        "assistant: decomposing into a build-test loop\n"
        "tool_use: write a.py\n"
        "tool_result: ok\n"
        "⏺ tests pass; iterating\n"
    )
    sp = DriverResult(
        transcript=single_pass,
        effective_turns=_count_effective_turns(single_pass),
        file_blocks=tuple(_extract_file_blocks(single_pass)),
        exit_status=0,
        spawn_argv=(),
        spawn_env_config_dir="",
        workspace_root=Path("/tmp/x"),
    )
    mt = DriverResult(
        transcript=multi_turn,
        effective_turns=_count_effective_turns(multi_turn),
        file_blocks=tuple(_extract_file_blocks(multi_turn)),
        exit_status=0,
        spawn_argv=(),
        spawn_env_config_dir="",
        workspace_root=Path("/tmp/x"),
    )
    assert sp.is_multi_turn is False
    assert mt.is_multi_turn is True


def test_AC_LIPW_4_file_blocks_extracted_for_grading() -> None:
    transcript = (
        "some preamble\n"
        "FILE: solution.py\n"
        "def f():\n    return 1\n"
        "FILE: helper.py\n"
        "X = 2\n"
    )
    blocks = _extract_file_blocks(transcript)
    assert len(blocks) == 2
    assert blocks[0].startswith("FILE: solution.py")
    assert blocks[1].startswith("FILE: helper.py")


def test_AC_LIPW_4_driver_uses_production_bootstrap_never_service_true(
    tmp_path: Path,
) -> None:
    """The driver stands the instance up via the production bootstrap
    path and MUST NOT pass service_bootstrap=True (plan §3 Part 2
    sub-component 3 — service-isolation relies on the False default)."""
    seen: dict = {}

    def fake_bootstrap(**kwargs):
        seen.update(kwargs)
        (kwargs["new_ws_path"]).mkdir(parents=True, exist_ok=True)
        return object()

    driver = SubLoamDriver(
        scratch_root=tmp_path / "scratch",
        canonical_source=str(LOAM_ROOT),
        isolation=_isolation(tmp_path),
        bootstrap_fn=fake_bootstrap,
    )
    ws = driver.create_instance()
    driver.close()
    assert ws.name == "pb-subloam-test"
    # service_bootstrap NEVER passed True (omitted => production
    # False default).
    assert seen.get("service_bootstrap", False) is False
    assert "service_bootstrap" not in seen or seen["service_bootstrap"] is False


def test_AC_LIPW_4_drive_requires_instance_first(tmp_path: Path) -> None:
    driver = SubLoamDriver(
        scratch_root=tmp_path / "scratch",
        canonical_source=str(LOAM_ROOT),
        isolation=_isolation(tmp_path),
        bootstrap_fn=lambda **k: None,
    )
    with pytest.raises(RuntimeError):
        driver.drive("hello")


# ---- real-claude-binary integration (opt-in, load-bearing) ----------


@pytest.mark.skipif(
    os.environ.get("PB_SUBLOAM_REAL_CLAUDE") != "1",
    reason=(
        "real-claude PTY integration is opt-in (slow, spends "
        "subscription quota); set PB_SUBLOAM_REAL_CLAUDE=1. Halt-"
        "trigger 3 / §10.3: this is the load-bearing build-time "
        "unknown — whether an interactive PTY-driven claude binds "
        "the scaffolded persona surface."
    ),
)
def test_AC_LIPW_4_real_claude_pty_drive_is_multiturn(
    tmp_path: Path,
) -> None:  # pragma: no cover - opt-in real-binary path
    scratch = tmp_path / "scratch"
    driver = SubLoamDriver(
        scratch_root=scratch,
        canonical_source=str(LOAM_ROOT),
        isolation=_isolation(tmp_path),
    )
    with driver:
        result = driver.drive(
            "Say the single word ACK and then stop.",
            # The scratch-ws TUI warmup is slow (SessionStart hook +
            # ~19 skill loads); give it room before sending, and a
            # generous idle window after for the agentic loop.
            tui_warmup_s=18.0,
            idle_timeout_s=45.0,
            hard_timeout_s=240.0,
        )
    assert result.transcript.strip(), "empty transcript from real claude"
    assert result.is_multi_turn, (
        "interactive PTY-driven claude did not produce a multi-turn "
        "transcript — halt-trigger 3"
    )
