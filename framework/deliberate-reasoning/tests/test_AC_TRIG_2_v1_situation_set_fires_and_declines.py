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

"""AC.TRIG.2 — the v1 situation set (UNBOUNDED_OP / REPEAT_FAILED /
MACHINE_IRREVERSIBLE / HIGH_BLAST_RADIUS) is present, and each member fires on
its constructed POSITIVE fixture and declines its constructed NEGATIVE fixture,
scored WITHOUT any LLM call (the floor is LLM-free by construction).

Each signal is tested at the detector level (signals.py) AND through the gate
so the firing is observable as a recorded Trigger.
"""

from __future__ import annotations

import sys

from loam.deliberate_reasoning.gate import GateSignals, Trigger, evaluate_gate
from loam.deliberate_reasoning.signals import (
    PendingAction,
    ResultClass,
    SituationSignal,
    ToolCallRecord,
    ToolResultRing,
    detect_situation_signals,
)


# ---- UNBOUNDED_OP --------------------------------------------------------

def test_AC_TRIG_2_unbounded_op_positive_fires():
    action = PendingAction(
        tool_name="Bash",
        command="grep -E 'foo.*bar' giant.log",
        target_path="giant.log",
        target_size_bytes=1_000_000,
    )
    assert SituationSignal.UNBOUNDED_OP in detect_situation_signals(action)
    assert Trigger.UNBOUNDED_OP in evaluate_gate(
        GateSignals(pending_action=action)
    ).triggers


def test_AC_TRIG_2_unbounded_op_negative_declines():
    # A bounded search (piped to head) over the same target is NOT unbounded.
    action = PendingAction(
        tool_name="Bash",
        command="grep -E 'foo.*bar' giant.log | head -20",
        target_path="giant.log",
        target_size_bytes=1_000_000,
    )
    assert SituationSignal.UNBOUNDED_OP not in detect_situation_signals(action)


# ---- REPEAT_FAILED -------------------------------------------------------

def test_AC_TRIG_2_repeat_failed_positive_fires():
    action = PendingAction(
        tool_name="Bash", command="grep -E 'needle' haystack.txt", target_path="haystack.txt"
    )
    ring = ToolResultRing(
        records=(
            ToolCallRecord(
                arg_shape_key=action.arg_shape_key(),
                result_class=ResultClass.FAILURE,
            ),
        )
    )
    assert SituationSignal.REPEAT_FAILED in detect_situation_signals(action, ring)
    assert Trigger.REPEAT_FAILED in evaluate_gate(
        GateSignals(pending_action=action, result_ring=ring)
    ).triggers


def test_AC_TRIG_2_repeat_failed_negative_declines():
    # A first-time action (empty ring) is not a repeat.
    action = PendingAction(
        tool_name="Bash", command="grep -E 'needle' haystack.txt", target_path="haystack.txt"
    )
    assert SituationSignal.REPEAT_FAILED not in detect_situation_signals(
        action, ToolResultRing()
    )
    # And a prior SUCCESS of the same shape is not a failed-repeat.
    ring = ToolResultRing(
        records=(
            ToolCallRecord(
                arg_shape_key=action.arg_shape_key(),
                result_class=ResultClass.SUCCESS,
            ),
        )
    )
    assert SituationSignal.REPEAT_FAILED not in detect_situation_signals(action, ring)


# ---- MACHINE_IRREVERSIBLE ------------------------------------------------

def test_AC_TRIG_2_machine_irreversible_positive_fires():
    # A write OUTSIDE the safe scratch/tmp set is machine-irreversible.
    action = PendingAction(tool_name="Write", target_path="/Users/luke/important.txt")
    assert SituationSignal.MACHINE_IRREVERSIBLE in detect_situation_signals(action)
    assert Trigger.MACHINE_IRREVERSIBLE in evaluate_gate(
        GateSignals(pending_action=action)
    ).triggers


def test_AC_TRIG_2_machine_irreversible_negative_declines():
    # A write to the safe scratch set is NOT machine-irreversible.
    action = PendingAction(tool_name="Write", target_path="/tmp/throwaway.txt")
    assert SituationSignal.MACHINE_IRREVERSIBLE not in detect_situation_signals(action)


# ---- HIGH_BLAST_RADIUS ---------------------------------------------------

def test_AC_TRIG_2_high_blast_radius_positive_fires():
    action = PendingAction(tool_name="Bash", command="rm -rf build/")
    assert SituationSignal.HIGH_BLAST_RADIUS in detect_situation_signals(action)
    assert Trigger.HIGH_BLAST_RADIUS in evaluate_gate(
        GateSignals(pending_action=action)
    ).triggers


def test_AC_TRIG_2_high_blast_radius_negative_declines():
    # A single-file, non-recursive, non-sensitive action is not high-blast.
    action = PendingAction(tool_name="Bash", command="rm one-file.txt", target_path="one-file.txt")
    assert SituationSignal.HIGH_BLAST_RADIUS not in detect_situation_signals(action)


# ---- LLM-free by construction --------------------------------------------

def test_AC_TRIG_2_situation_floor_is_llm_free():
    # The structural floor imports no LLM client. Check the IMPORT lines (not
    # prose: the docstring legitimately names "anthropic" to say it is NOT
    # used). A real import would appear as an import statement.
    import loam.deliberate_reasoning.signals as sig_mod

    import_lines = [
        ln
        for ln in open(sig_mod.__file__).read().splitlines()
        if ln.lstrip().startswith(("import ", "from "))
    ]
    joined = "\n".join(import_lines).lower()
    assert "claude_print_client" not in joined
    assert "anthropic" not in joined
    # And no anthropic module was pulled into sys.modules by importing signals.
    assert "anthropic" not in sys.modules
