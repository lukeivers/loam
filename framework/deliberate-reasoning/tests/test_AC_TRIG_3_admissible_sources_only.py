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

"""AC.TRIG.3 — the structural detectors read ADMISSIBLE sources only (tool
name, tool-argument structure, target path, recent tool-result metadata); no
detector reads the natural-language prompt or draft content. Any retained
NOVELTY-style label is verified to derive structurally, not from a prompt
keyword-scan.

Two structural guards:

(a) the structural inputs (PendingAction / ToolResultRing) carry NO prompt or
    draft field — the admissible-source contract is enforced by the dataclass
    SHAPE, so a detector physically cannot read conversation text;
(b) a detector handed adversarial conversation keywords (via the demoted
    keyword fields) but a SAFE pending action does not fire on the structural
    floor — the structural decision is independent of the keyword fields.
"""

from __future__ import annotations

import dataclasses

from loam.deliberate_reasoning.gate import GateSignals, evaluate_gate
from loam.deliberate_reasoning.signals import (
    PendingAction,
    ToolResultRing,
    detect_situation_signals,
)


def test_AC_TRIG_3_structural_inputs_carry_no_nl_prompt_or_draft():
    # The admissible-source contract: the structural inputs the detectors read
    # have NO prompt/draft field. Enforced by the dataclass shape (D-SIT.3).
    pa_fields = {f.name for f in dataclasses.fields(PendingAction)}
    ring_fields = {f.name for f in dataclasses.fields(ToolResultRing)}
    forbidden = {"prompt", "prompt_text", "draft", "draft_text", "conversation"}
    assert pa_fields.isdisjoint(forbidden), pa_fields & forbidden
    assert ring_fields.isdisjoint(forbidden), ring_fields & forbidden
    # The admissible PendingAction fields are exactly the structural set.
    assert pa_fields == {
        "tool_name",
        "command",
        "pattern",
        "target_path",
        "target_size_bytes",
    }


def test_AC_TRIG_3_adversarial_keywords_safe_action_does_not_fire_structurally():
    # The pending action is structurally safe; the keyword fields are stuffed
    # with adversarial hedge/stakes words. The structural floor must ignore
    # them entirely (it never reads them).
    safe_action = PendingAction(
        tool_name="Read", target_path="docs/x.md", target_size_bytes=1_000
    )
    assert detect_situation_signals(safe_action) == ()
    # Through the gate, with keyword opt-in OFF (default), no escalation.
    signals = GateSignals(
        pending_action=safe_action,
        draft_text="I'm not sure, maybe, probably, I think, unclear",
        prompt_text="critical high-stakes must be correct legal medical",
    )
    assert evaluate_gate(signals).escalate is False


def test_AC_TRIG_3_novelty_label_is_structurally_supplied_not_prompt_derived():
    # NOVELTY is set-membership on a caller-supplied task_class label; the gate
    # never derives that label from the prompt text. Proof: the label decides
    # novelty regardless of prompt content, and a None label carries no signal.
    # Same prompt text, different structural label => different novelty outcome.
    novel = GateSignals(
        task_class="brand-new-class",
        recent_task_classes=frozenset({"seen-a", "seen-b"}),
        prompt_text="identical prompt text",
    )
    not_novel = GateSignals(
        task_class="seen-a",
        recent_task_classes=frozenset({"seen-a", "seen-b"}),
        prompt_text="identical prompt text",
    )
    assert evaluate_gate(novel).escalate is True  # label drives it, not the prompt
    assert evaluate_gate(not_novel).escalate is False
    # And an unclassified turn carries no novelty signal at all.
    unclassified = GateSignals(prompt_text="identical prompt text")
    assert evaluate_gate(unclassified).escalate is False
