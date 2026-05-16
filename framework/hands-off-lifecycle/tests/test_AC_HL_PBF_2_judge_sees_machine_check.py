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

"""AC.PBF.2 — the faithfulness judge assesses the MACHINE check, not
just the plain summary.

Plan: pos3 phase-b-fix-plan-2026-05-16.md §4 AC.PBF.2
Evidence base: phase-b-hardening-2026-05-16.md I3/I6 — proxy/plumbing
checks the loop's OWN judge rubber-stamped because it was shown only
the friendly plain "done", never the machine check command underneath.

Outcome under test (not method): the independent faithfulness check's
verdict is derived from an assessment that INCLUDES the actual derived
machine check command (and its spec), evaluated adversarially for the
proxy/plumbing failure mode. A verdict produced WITHOUT the machine
form in evidence does not satisfy the AC. Either polarity
(faithful=true / false) is AC-satisfying — the AC is "the judge
assessed the real test", not "the judge said yes".

This is the information-trust-ordering inversion: judge the
ground-truth artefact (the actual check command), not the loop's own
self-narrated summary. The judge process itself is unchanged.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(
    0, str(ROOT / "framework" / "tools" / "handsoff-loop" / "src")
)

from handsoff_loop import intake as I  # noqa: E402


def _run_capturing_faith_prompt(monkeypatch, *, check_command: str,
                                spec: str, judge_verdict: str):
    """Drive a full real-path run with the claude subprocess stubbed,
    capturing the exact faithfulness-judge prompt the loop builds."""
    captured: dict[str, str] = {}

    def fake(prompt: str, *, model: str = "sonnet",
             timeout: int = 300) -> dict:
        if "List ONLY the few missing" in prompt:
            return {"result": "Which photos?\nWhat does safe mean?"}
        if "Produce TWO things" in prompt:
            return {
                "result": (
                    "Done when your photos are safe and backed up.\n"
                    "---\n"
                    '{"check_command": ' + repr(check_command).replace(
                        "'", '"') + ', "spec": '
                    + repr(spec).replace("'", '"') + "}"
                )
            }
        if "Adversarial faithfulness check" in prompt:
            captured["faith"] = prompt
            return {"result": judge_verdict}
        return {"result": ""}

    monkeypatch.setattr(I, "_claude_json", fake)
    out = I.derive_acceptance_from_intent(
        intent="make sure my photos are safe",
        under_specification=["implicit constraints"],
        approval_fn=lambda p: True,
        elicit_answer_fn=lambda q: "a vague layperson answer",
        run_model=True,
    )
    return out, captured.get("faith", "")


def test_AC_PBF_2_faith_prompt_carries_the_machine_check_command(
    monkeypatch,
) -> None:
    """The defect being closed: the faithfulness prompt previously
    interpolated only intent + plain_acceptance and NEVER the machine
    form. It must now carry the literal derived check command + spec."""
    proxy_cmd = "[ -f ~/Library/cloudkit.db ]"
    out, faith_prompt = _run_capturing_faith_prompt(
        monkeypatch,
        check_command=proxy_cmd,
        spec="presence test for a one-time setup file",
        judge_verdict='{"faithful": false, "reason": "stale proxy"}',
    )
    assert faith_prompt, "the faithfulness judge must have been invoked"
    assert proxy_cmd in faith_prompt, (
        "the judge MUST see the actual derived machine check command"
    )
    assert "presence test for a one-time setup file" in faith_prompt, (
        "the judge MUST see the machine spec"
    )


def test_AC_PBF_2_faith_prompt_asks_the_proxy_plumbing_question(
    monkeypatch,
) -> None:
    """It is not enough to show the command — the judge must be asked
    the adversarial proxy/plumbing question ('could this exit 0 while
    the user's real outcome is unmet?')."""
    _out, faith_prompt = _run_capturing_faith_prompt(
        monkeypatch,
        check_command="gmail_cleanup.py --validate",
        spec="dry-run validate flag",
        judge_verdict='{"faithful": false, "reason": "dry-run proxy"}',
    )
    low = faith_prompt.lower()
    assert "proxy" in low or "plumbing" in low
    assert "exit 0" in low
    assert "not what i asked for" in low or "actual outcome" in low


def test_AC_PBF_2_judge_either_polarity_preserved(monkeypatch) -> None:
    """The AC is satisfied by EITHER verdict. A proxy check that the
    judge (now seeing the command) catches yields faithful=False; a
    genuine check yields faithful=True. Both are AC-satisfying — there
    is no retry-to-green path."""
    out_neg, _ = _run_capturing_faith_prompt(
        monkeypatch,
        check_command="[ -f ~/.cloudkit.db ]",
        spec="stale presence test",
        judge_verdict='{"faithful": false, "reason": "proxy caught"}',
    )
    assert out_neg.approved is True
    assert out_neg.faithful is False
    assert out_neg.faithfulness_reason

    out_pos, _ = _run_capturing_faith_prompt(
        monkeypatch,
        check_command="python3 verify_photos_uploaded.py --count 20000",
        spec="verifies all photos actually uploaded",
        judge_verdict='{"faithful": true, "reason": "verifies outcome"}',
    )
    assert out_pos.approved is True
    assert out_pos.faithful is True


def test_AC_PBF_2_unparseable_judge_is_false_not_retried(
    monkeypatch,
) -> None:
    """An unparseable judge verdict yields faithful=False with the
    reason recorded — no retry path (the already-existing
    either-polarity behaviour must survive the fix)."""
    out, _ = _run_capturing_faith_prompt(
        monkeypatch,
        check_command="test -s out.txt",
        spec="x",
        judge_verdict="the model rambled and emitted no json",
    )
    assert out.faithful is False
    assert "unparseable" in out.faithfulness_reason.lower()
