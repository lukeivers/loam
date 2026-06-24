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

"""AC.E2E.1 (outcome-altitude: true) — answer-correctness strictly up
on contradiction items, no regression on the control set.

Invokes the REAL retrieval+answer path (the live ``FileMemoryStore``
seeded fresh per item — NO pre-arranged index state) over the frozen
QA-over-memory probe set, scored by the BLIND judge. The gain on
contradiction items must be strictly positive (the SUP filter stops the
persona answering off the stale record) and the control set must not
regress. This is the gate that proves "intelligence stopped operating
off bad memory," not just "retrieval changed."

outcome-altitude: true — production entry-point, no seeded state.
"""

from __future__ import annotations

import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent.parent / "eval"
if str(_EVAL.parent) not in sys.path:
    sys.path.insert(0, str(_EVAL.parent))

from eval import harness  # noqa: E402


def test_AC_E2E_1_gain_on_contradiction_strictly_up_no_control_regression():
    res = harness.run_gate_c()
    assert res.n_contradiction > 0, "no contradiction items in the probe set"
    assert res.gain_on_contradiction > 0, (
        "answer-correctness must be STRICTLY up on contradiction items "
        f"(AC.E2E.1); pre={res.pre_correct_contradiction} "
        f"post={res.post_correct_contradiction}"
    )
    assert res.gain_on_control >= 0, (
        "the control set must NOT regress (AC.E2E.1); "
        f"pre={res.pre_correct_control} post={res.post_correct_control}"
    )


def test_AC_E2E_1_outcome_altitude_real_entrypoint_no_seeded_state():
    """The gate runs against a freshly-constructed live store per item
    (the production retrieval entry-point) with no pre-arranged index
    state — every score derives from a real search call."""
    items = harness.load_qa_items()
    # A real production search must run and return content for at least
    # one contradiction item (proves the entry-point is exercised live).
    contradiction = [it for it in items if it["arm"] == "contradiction"]
    assert contradiction
    import tempfile
    from loam.primary_persona.file_memory import FileMemoryStore

    item = contradiction[0]
    with tempfile.TemporaryDirectory() as td:
        memory_dir = Path(td) / "memory"
        store = FileMemoryStore(memory_dir=memory_dir)
        harness._seed_qa(store, memory_dir, item)
        ans = harness._post_change_answer(store, item["prompt"])
        assert harness.normalize(item["canonical_answer"]) in harness.normalize(ans), (
            "the real retrieval+answer path must surface the current "
            f"fact for {item['id']}; got answer={ans!r}"
        )
