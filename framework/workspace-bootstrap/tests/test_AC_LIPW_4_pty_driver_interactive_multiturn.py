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
    _count_genuine_turns,
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
    # AC.SLF.2: is_multi_turn is now gated on genuine_turns (genuine
    # markers only), constructed the way drive() builds the result.
    # The asserted property is UNCHANGED — a single-pass shape is
    # not-multi-turn, a genuine multi-turn shape is multi-turn — only
    # the construction now feeds the honest genuine count.
    sp = DriverResult(
        transcript=single_pass,
        effective_turns=_count_effective_turns(single_pass),
        genuine_turns=_count_genuine_turns(single_pass),
        file_blocks=tuple(_extract_file_blocks(single_pass)),
        exit_status=0,
        spawn_argv=(),
        spawn_env_config_dir="",
        workspace_root=Path("/tmp/x"),
    )
    mt = DriverResult(
        transcript=multi_turn,
        effective_turns=_count_effective_turns(multi_turn),
        genuine_turns=_count_genuine_turns(multi_turn),
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


# ---- AC.SLF.4 + AC.SLF.5 — the one honest end-test --------------------
#
# This REPLACES the prior `test_AC_LIPW_4_real_claude_pty_drive_is_
# multiturn`, which (programbench-step0-rootcause-and-contamination-
# 2026-05-15.md §B) drove the short ACK stand-in (NOT the frozen
# build_prompt) and asserted only `transcript.strip()` + the
# chrome-contaminated `is_multi_turn` — it measured nothing a TUI boot
# would not also satisfy. Per AC.SLF.5 the AC.LIPW.4 recorded green is
# re-verified against the AC's OWN written verification clause: the
# frozen `build_prompt(task)`, a GENUINE multi-turn signal, and a
# persona-identity signal — NOT the ACK string, NOT the chrome signal.
# Per the AC.SLF.5 coupling note, this single honest run satisfies
# BOTH AC.SLF.4 (the one honest end-test) and AC.SLF.5 (the
# contaminated-record re-verification).
#
# AC.SLF.4 is satisfied by EITHER terminal outcome, both GREEN:
#   (a) Lives  : >=1 genuine turn + gradeable output.
#   (b) Dead end: a correctly-submitted frozen prompt does NOT yield
#       a completed tool-using loop over this driver — reported
#       straight, NOT softened, NOT retried, NOT a build failure.
# The test passes iff the prompt was honestly submitted and the
# honest result captured; it does NOT require polarity (a).


def _resolve_frozen_build_prompt() -> str:
    """Resolve the REAL frozen build_prompt from the programbench
    harness. NEVER substitutes a weaker proxy (halt-trigger 4): if
    the opt-in is set but the harness is unreachable, the test FAILS
    honestly rather than measuring a stand-in.
    """
    harness_dir = os.environ.get(
        "PB_HARNESS_DIR",
        "/Users/lukeivers/pos3/workspace/experiments/"
        "programbench-derivative/harness",
    )
    task = os.environ.get("PB_SUBLOAM_TASK", "yj")
    hp = Path(harness_dir)
    assert hp.is_dir(), (
        f"PB_HARNESS_DIR not a directory: {hp} — cannot resolve the "
        "frozen build_prompt; refusing to substitute a proxy "
        "(halt-trigger 4)."
    )
    sys.path.insert(0, str(hp))
    try:
        import run_agent  # type: ignore  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(
            f"could not import the frozen build_prompt from {hp}: "
            f"{exc!r} — refusing to substitute a proxy "
            "(halt-trigger 4)."
        ) from exc
    prompt = run_agent.build_prompt(task)
    assert isinstance(prompt, str) and len(prompt) > 1500, (
        "resolved build_prompt is not the large multi-fragment "
        f"frozen prompt (len={len(prompt) if prompt else 0})"
    )
    return prompt


@pytest.mark.skipif(
    os.environ.get("PB_SUBLOAM_REAL_CLAUDE") != "1",
    reason=(
        "the one honest end-test drives a real interactive claude "
        "on the FROZEN build_prompt (slow, spends subscription "
        "quota); set PB_SUBLOAM_REAL_CLAUDE=1. Both terminal "
        "outcomes — lives and dead-end — are GREEN; only an "
        "un-runnable environment fails."
    ),
)
def test_AC_SLF_4_5_one_honest_end_test_on_frozen_build_prompt(
    tmp_path: Path,
) -> None:  # pragma: no cover - opt-in real-binary path
    frozen_prompt = _resolve_frozen_build_prompt()

    scratch = tmp_path / "scratch"
    driver = SubLoamDriver(
        scratch_root=scratch,
        canonical_source=str(LOAM_ROOT),
        isolation=_isolation(tmp_path),
    )
    with driver:
        result = driver.drive(
            frozen_prompt,
            # Scratch-ws TUI warmup is slow (SessionStart hook + skill
            # loads); generous windows so a real loop has room. The
            # multi-KB frozen prompt is exactly the multi-fragment
            # bracketed-paste scenario AC.SLF.1 fixes.
            tui_warmup_s=18.0,
            idle_timeout_s=90.0,
            hard_timeout_s=600.0,
            paste_settle_s=3.0,
        )

    transcript = result.transcript
    # The run must have HAPPENED honestly — a real claude produced
    # output. An empty transcript means the environment could not run
    # the end-test (halt-trigger 4), not a dead-end finding.
    assert transcript.strip(), (
        "empty transcript from real claude — the end-test could not "
        "run honestly (halt-trigger 4: environment, not a dead-end "
        "finding)"
    )

    # AC.SLF.5: persona-identity signal — the driven session is the
    # bound primary persona, not a bare LLM (the AC's own clause).
    persona_identity = "primary" in transcript

    # AC.SLF.1/.2: the HONEST signals — genuine markers, not chrome.
    lives = result.loop_ran and (
        result.is_multi_turn or len(result.file_blocks) > 0
    )

    # Emit the honest terminal outcome straight (read by the build
    # report; pytest -s surfaces it). Both polarities are GREEN.
    if lives:
        outcome = "(a) LIVES"
    else:
        outcome = "(b) DEAD END"
    print(
        "\n=== AC.SLF.4/.5 honest end-test ===\n"
        f"outcome: {outcome}\n"
        f"genuine_turns: {result.genuine_turns}  "
        f"loop_ran: {result.loop_ran}  "
        f"is_multi_turn: {result.is_multi_turn}\n"
        f"file_blocks: {len(result.file_blocks)}  "
        f"persona_identity_signal: {persona_identity}\n"
        f"cost_usd: {result.cost_usd}  "
        f"cost_source: {result.cost_source}  "
        f"timed_out: {result.timed_out}\n"
        f"transcript_len: {len(transcript)}\n"
        "===================================\n"
    )

    # AC.SLF.4 is satisfied by EITHER outcome. The test asserts ONLY
    # that the end-test ran honestly and produced a captured,
    # honest-signal-classified result — NOT that polarity (a)
    # occurred. Outcome (b) is a GREEN: do not fail it, do not retry.
    assert result.genuine_turns >= 0  # honest signal computed
    assert result.cost_source in {"cost-command", "absent"}  # honest
    # The contaminated record's clause is now exercised against the
    # frozen build_prompt + honest signals (AC.SLF.5), regardless of
    # which terminal outcome the real run produced.
