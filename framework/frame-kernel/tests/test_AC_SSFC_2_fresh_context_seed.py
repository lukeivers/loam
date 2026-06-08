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

"""AC.SSFC.2 — the judge is seeded with the microkernel + the subagent's
stated objective + its result, and NOT with the parent conversation.

The test captures the seed the judge path assembles and asserts it
contains the microkernel prime-marker + the stated objective + the
result, and asserts a parent-conversation marker is ABSENT from the seed.
The load-bearing fresh-context guarantee (D-SSFC.5): the check must run
in a frame the polluted conversation cannot reach.
"""

from __future__ import annotations

from pathlib import Path

from conftest import make_stop_envelope, write_transcript

from loam.frame_kernel import frame_judge as fj
from loam.frame_kernel.bundle import MICROKERNEL_PRIME_MARKER

# A token that, if present in the seed, would prove the parent
# conversation leaked in. It is NEVER written into the transcript's
# objective/result fields — it stands in for the polluted parent context.
_PARENT_CONVERSATION_MARKER = "PARENT-CONVERSATION-CONTENT-MUST-NOT-LEAK"


def test_seed_contains_microkernel_objective_result(
    real_kernel_workspace: Path,
) -> None:
    """The assembled seed carries the microkernel prime-marker + the
    stated objective + the result."""
    transcript = write_transcript(
        real_kernel_workspace / "t.jsonl",
        objective="OBJECTIVE-MARKER-write-the-spec",
        result="RESULT-MARKER-the-spec-is-written",
        consequential=True,
    )
    ctx = fj.parse_stop_envelope(
        make_stop_envelope(real_kernel_workspace, transcript)
    )
    result = fj.read_subagent_result(ctx)
    seed = fj.assemble_seed(result)

    assert MICROKERNEL_PRIME_MARKER in seed, "microkernel must seed the judge"
    assert "OBJECTIVE-MARKER-write-the-spec" in seed, (
        "the stated objective must seed the judge"
    )
    assert "RESULT-MARKER-the-spec-is-written" in seed, (
        "the subagent result must seed the judge"
    )
    # The seed is the REAL on-disk microkernel (no fixture stand-in).
    assert "THREE ROLES" in seed


def test_parent_conversation_absent_from_seed(
    real_kernel_workspace: Path,
) -> None:
    """The seed assembly reads ONLY the objective + result + microkernel
    — a parent-conversation marker injected into the envelope (but not
    the objective/result) never reaches the seed."""
    envelope = make_stop_envelope(
        real_kernel_workspace,
        write_transcript(
            real_kernel_workspace / "t.jsonl",
            objective="clean objective",
            result="clean result",
            consequential=True,
        ),
    )
    # Smuggle a parent-conversation field onto the envelope. The seed
    # assembly must NOT read it (only transcript_path/workspace are seed
    # sources).
    envelope["parent_conversation"] = _PARENT_CONVERSATION_MARKER
    envelope["messages"] = [{"role": "user", "content": _PARENT_CONVERSATION_MARKER}]

    ctx = fj.parse_stop_envelope(envelope)
    result = fj.read_subagent_result(ctx)
    seed = fj.assemble_seed(result)

    assert _PARENT_CONVERSATION_MARKER not in seed, (
        "the fresh-context guarantee FAILED: parent-conversation content "
        "leaked into the judge seed"
    )


def test_seed_blocks_are_exactly_three(real_kernel_workspace: Path) -> None:
    """The seed is exactly the three delimited blocks (microkernel,
    objective, result) — no fourth conversation block."""
    transcript = write_transcript(
        real_kernel_workspace / "t.jsonl",
        objective="o",
        result="r",
        consequential=True,
    )
    ctx = fj.parse_stop_envelope(
        make_stop_envelope(real_kernel_workspace, transcript)
    )
    seed = fj.assemble_seed(fj.read_subagent_result(ctx))

    assert MICROKERNEL_PRIME_MARKER in seed
    assert fj.SEED_OBJECTIVE_MARKER in seed
    assert fj.SEED_RESULT_MARKER in seed
    # No parent-transcript delimiter exists in the module at all.
    assert "parent" not in seed.lower()


def test_missing_objective_degrades_not_invents(
    real_kernel_workspace: Path,
) -> None:
    """No recoverable objective -> the named degraded marker, NOT an
    invented objective (plan §8 trigger #4)."""
    import json

    # A transcript with only an assistant result, no user objective.
    transcript = real_kernel_workspace / "no_obj.jsonl"
    transcript.write_text(
        json.dumps(
            {
                "type": "assistant",
                "message": {
                    "role": "assistant",
                    "content": [{"type": "text", "text": "some result"}],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    ctx = fj.parse_stop_envelope(
        make_stop_envelope(real_kernel_workspace, transcript)
    )
    result = fj.read_subagent_result(ctx)
    assert result.objective == fj.SEED_OBJECTIVE_MISSING_MARKER
