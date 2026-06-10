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

"""AC.DLG.2 — a turn that closes ruling-shaped with no corresponding
decision record draws a deterministic model-facing steer on the
existing turn-close seam (steer-not-block, fail-open, no LLM/API
call), and a session-start catch-up surfaces ruling-shaped turns since
the last sweep that still lack records. On a labeled sample of >=20
real turns the detector reaches >=80% precision with no steer on
ordinary prose.

The labeled sample below is drawn from the live pos3 turn corpus
(shapes preserved; content condensed/genericized where personal). The
two real failure cases ride verbatim-shaped: the 2026-06-07 Tilth
"go the higher route" turn and the 2026-06-09 "1. Agree with you" D2
ratification.

Memory recall cycle, Slice 3.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from loam.primary_persona.decision_ledger import (
    consume_pending_steer,
    decisions_dir,
    detect_and_flag_ruling_gap,
    is_ruling_shaped,
    run_catch_up_sweep,
    write_decision,
)
from loam.primary_persona.stop_emitter import (
    StopEnvelope,
    handle_stop_envelope,
)


# ---- the labeled real-turn sample (>= 20 turns) ----------------------
# (text, is_actually_a_ruling)
LABELED_TURNS: tuple[tuple[str, bool], ...] = (
    # -- rulings (positives) --
    (
        "Well… on the raise sounding like salary… I think raises in the "
        "AI era need to be different. There's an expectation that you "
        "can do more with less. It should go the higher route.",
        True,
    ),
    ("1. Agree with you", True),
    ("Approved. Ship the seal once the tests are green.", True),
    ("Let's go with the file-based store, drop the graph backend.", True),
    ("Go ahead with the deletion, the eval verdict stands.", True),
    ("My call: weekly cadence, not daily. Lock it in.", True),
    ("Yes, do it that way — one amendment, five slices.", True),
    ("Ratified. Build it.", True),
    ("Option 2. Proceed with the narrow fence.", True),
    ("Go for it, and keep the commits small.", True),
    # -- ordinary prose / non-rulings (negatives) --
    ("What's the current state of the memory build?", False),
    ("Can you summarize what the eval found?", False),
    ("How long until the seal lands?", False),
    ("Show me the failing test output.", False),
    ("Continue.", False),
    ("Thanks, that looks right so far.", False),
    ("Where did we land on the raise question? I forget.", False),
    ("Run the harness again and report the numbers.", False),
    ("What do you think — should we go with option 1 or option 2?", False),
    ("Is the dispatch still running?", False),
    ("Give me a status update on all three agents.", False),
    ("Read the plan doc top to bottom before you start.", False),
    (
        "I'm seeing the same Telegram drop again, third time today — "
        "can you check the channel health?",
        False,
    ),
    ("walk me through the fence rules for sealed components", False),
)


def test_AC_DLG_2_detector_precision_on_labeled_sample() -> None:
    assert len(LABELED_TURNS) >= 20
    flagged = [(t, label) for t, label in LABELED_TURNS if is_ruling_shaped(t)]
    assert flagged, "detector must flag at least the known rulings"
    true_pos = sum(1 for _, label in flagged if label)
    precision = true_pos / len(flagged)
    assert precision >= 0.80, (
        f"AC.DLG.2: precision {precision:.2f} < 0.80; flagged="
        f"{[(t[:40], label) for t, label in flagged]}"
    )
    # Recall floor on the named real failure cases: the two turns the
    # cycle exists to catch MUST flag.
    assert is_ruling_shaped(LABELED_TURNS[0][0]), "Tilth deixis turn"
    assert is_ruling_shaped("1. Agree with you"), "D2 ratification turn"


def test_AC_DLG_2_no_steer_on_ordinary_prose() -> None:
    for text, label in LABELED_TURNS:
        if not label and not is_ruling_shaped(text):
            continue  # fine
        if not label:
            pytest.fail(f"ordinary prose drew a flag: {text!r}")


def test_AC_DLG_2_envelope_metadata_never_trips_detector() -> None:
    enveloped = (
        '<channel source="plugin:discord:discord" chat_id="123" '
        'user="grassly" ts="2026-06-09T23:05:44.104Z">\n'
        "What's left on the build queue?\n</channel>"
    )
    assert not is_ruling_shaped(enveloped)


def test_AC_DLG_2_gap_flagged_and_steer_consumed_once(tmp_path: Path) -> None:
    flagged = detect_and_flag_ruling_gap(
        memory_dir=tmp_path,
        user_message="Approved. Ship the seal once the tests are green.",
        turn_started_at=time.time() - 60,
    )
    assert flagged
    steer = consume_pending_steer(tmp_path)
    assert "[decision-ledger]" in steer
    assert "Approved. Ship the seal" in steer, "steer carries the evidence"
    assert "decision record" in steer
    # Consume-on-read: second read is empty.
    assert consume_pending_steer(tmp_path) == ""


def test_AC_DLG_2_no_gap_when_record_written_during_turn(
    tmp_path: Path,
) -> None:
    turn_start = time.time() - 60
    write_decision(
        tmp_path,
        question="Seal timing?",
        ruling="Ship after green tests",
        reasoning="Owner approved at turn close.",
        entities=("seal",),
        source="test turn",
    )
    flagged = detect_and_flag_ruling_gap(
        memory_dir=tmp_path,
        user_message="Approved. Ship the seal once the tests are green.",
        turn_started_at=turn_start,
    )
    assert not flagged, "a record written during the turn closes the gap"
    assert consume_pending_steer(tmp_path) == ""


def test_AC_DLG_2_stop_seam_flags_ruling_turn(tmp_path: Path) -> None:
    # Through the EXISTING turn-close seam: a ruling-shaped turn closing
    # via handle_stop_envelope flags the steer (fail-open wrapper —
    # the stop pipeline itself proceeds regardless).
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(
        "\n".join(
            json.dumps(
                {"message": {"role": role, "content": content}}
            )
            for role, content in (
                ("user", "Ratified. Build it."),
                ("assistant", "Acknowledged — dispatching the build now."),
            )
        ),
        encoding="utf-8",
    )
    handle_stop_envelope(
        StopEnvelope(
            session_id="dlg2-test",
            transcript_path=str(transcript),
            cwd=str(tmp_path),
            stop_hook_active=False,
        ),
        tmp_path,
    )
    from loam.primary_persona.file_memory import memory_dir_for_workspace

    mem = memory_dir_for_workspace(tmp_path)
    steer = consume_pending_steer(mem)
    assert "[decision-ledger]" in steer
    assert "Ratified. Build it." in steer


def test_AC_DLG_2_catch_up_sweep_surfaces_missed_rulings(
    tmp_path: Path,
) -> None:
    ep_dir = tmp_path / "episodes" / "ws" / "2026-06-09"
    ep_dir.mkdir(parents=True)
    (ep_dir / "ruled-turn.md").write_text(
        "---\nname: turn/x\nsource: message\ngroup_id: ws\n---\n"
        "[user]\nApproved. Go with the narrow fence for the cycle.\n"
        "[assistant]\nProceeding with the narrow fence.\n",
        encoding="utf-8",
    )
    (ep_dir / "ordinary-turn.md").write_text(
        "---\nname: turn/y\nsource: message\ngroup_id: ws\n---\n"
        "[user]\nWhat's the status of the build?\n"
        "[assistant]\nAll green so far.\n",
        encoding="utf-8",
    )
    block = run_catch_up_sweep(tmp_path)
    assert "[decision-ledger] Catch-up" in block
    assert "narrow fence" in block
    assert "status of the build" not in block
    # The sweep marker advances: a second sweep with no new episodes
    # surfaces nothing.
    assert run_catch_up_sweep(tmp_path) == ""


def test_AC_DLG_2_sweep_silent_when_records_exist(tmp_path: Path) -> None:
    ep_dir = tmp_path / "episodes" / "ws" / "2026-06-09"
    ep_dir.mkdir(parents=True)
    write_decision(
        tmp_path,
        question="Fence width?",
        ruling="Narrow",
        reasoning="Owner approved.",
        entities=("fence",),
        source="test",
    )
    (ep_dir / "ruled-turn.md").write_text(
        "---\nname: turn/x\n---\n"
        "[user]\nApproved. Go with the narrow fence for the cycle.\n"
        "[assistant]\nProceeding.\n",
        encoding="utf-8",
    )
    assert run_catch_up_sweep(tmp_path) == ""


def test_AC_DLG_2_sweep_fail_soft_on_absent_store(tmp_path: Path) -> None:
    assert run_catch_up_sweep(tmp_path / "nowhere") == ""
    assert decisions_dir(tmp_path / "nowhere").exists() is False
