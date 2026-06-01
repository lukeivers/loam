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

"""AC.UM.FENCE.1 — cells move ONLY by explicit statement (the MVP fence).

The LATER auto-learn engine (AIM-4 behavioural signal counters) is proven
ABSENT: a sequence of behavioural-signal turns through the live read-path
leaves the matrix byte-for-byte unchanged; only an explicit override
(AC.UM.OVR.*) moves a cell. This is the fence made mechanical.
"""

from __future__ import annotations

from pathlib import Path

from loam.primary_persona.keep_pace import interaction_model as im
from loam.workspace_bootstrap.seed_writer import render_interaction_model


def _seed(tmp_path: Path) -> Path:
    (tmp_path / "INTERACTION-MODEL.md").write_text(
        render_interaction_model() + "\n", encoding="utf-8"
    )
    return tmp_path


def test_AC_UM_FENCE_1_behavioural_turns_do_not_move_a_cell(
    tmp_path: Path,
) -> None:
    """Driving a sequence of behavioural-signal turns (engagement, bounce,
    confusion, terseness) through the read-path leaves the matrix
    byte-for-byte unchanged — no behavioural signal writes a cell."""
    home = _seed(tmp_path)
    matrix_path = home / "INTERACTION-MODEL.md"
    before = matrix_path.read_text()

    cfg = im.InteractionModelConfig(claude_home=home)
    contrib = im.build_interaction_model_contributor(cfg)

    # A barrage of turns that, in the LATER engine, would be behavioural
    # signals (deep technical prompts, terse acks, confusion markers,
    # repeated bounces). In N4 they only READ — none writes.
    behavioural_prompts = [
        "give me the full implementation details and the stack trace",
        "i don't understand any of this, too technical",
        "ok",
        "k",
        "wait what does that even mean",
        "go deeper, show me everything",
        "stop explaining so much",
    ]
    for p in behavioural_prompts:
        contrib({"prompt": p})

    after = matrix_path.read_text()
    assert after == before, (
        "a behavioural-signal turn moved a cell — the AIM-4 auto-learn "
        "fence is breached"
    )


def test_AC_UM_FENCE_1_only_explicit_override_moves_a_cell(
    tmp_path: Path,
) -> None:
    """The ONLY path that changes the matrix is the explicit override —
    contrasted against the behavioural read-path which never does."""
    home = _seed(tmp_path)
    matrix_path = home / "INTERACTION-MODEL.md"
    before = matrix_path.read_text()

    # Read-path turns: no change.
    contrib = im.build_interaction_model_contributor(
        im.InteractionModelConfig(claude_home=home)
    )
    contrib({"prompt": "deep technical question about the build"})
    assert matrix_path.read_text() == before

    # Explicit override: THIS moves the cell.
    im.apply_override(
        area="code-and-builds",
        axis="technical-exposure",
        value="deep",
        claude_home=home,
    )
    assert matrix_path.read_text() != before


def test_AC_UM_FENCE_1_no_behavioural_instrumentation_surface() -> None:
    """N4 ships ZERO behavioural instrumentation — the module exposes no
    signal-counter / hysteresis / drift-judge / consolidation / distress
    CALLABLE or ATTRIBUTE (the AIM-4..8 engine is OUT). Verified against
    the module's public symbols (not its prose, which legitimately NAMES
    what is deferred)."""
    public = [name for name in dir(im) if not name.startswith("__")]
    banned_fragments = (
        "signal",
        "hysteresis",
        "drift",
        "consolidat",
        "fast_down",
        "distress",
        "counter",
    )
    for name in public:
        low = name.lower()
        for frag in banned_fragments:
            assert frag not in low, (
                f"N4 module exposes a LATER-engine symbol {name!r} "
                f"(matched {frag!r}) — the MVP fence is breached"
            )
