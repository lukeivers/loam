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

"""AC.EOTTR.3 — Trait-reflection verdicts are deterministic.

Outcome: ``evaluate_all_traits(assistant_text)`` is a pure function:
given identical input it returns identical output. The seven-trait
verdict list is invariant across runs in the same process AND across
fresh subprocesses (no clock, no random, no env-dependent state).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SAMPLE_TEXTS = [
    "dispatching agent in parallel; verified test result first.",
    "are you sure?",
    "",
    "noticed a stale section; pruning it.",
    "leverage point: one cheap probe opens disproportionate value.",
]


def test_AC_EOTTR_3_evaluate_all_traits_is_pure_in_same_process() -> None:
    """Calling ``evaluate_all_traits`` twice with the same input
    yields identical output."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        evaluate_all_traits,
    )

    for text in SAMPLE_TEXTS:
        first = evaluate_all_traits(text)
        second = evaluate_all_traits(text)
        assert first == second, f"non-deterministic verdict on {text!r}"


def test_AC_EOTTR_3_verdicts_match_across_fresh_subprocesses(
    tmp_path: Path,
) -> None:
    """Spawn a fresh Python subprocess (no shared in-memory state)
    and confirm the verdict list matches the in-process result for
    every sample text. This guards against module-level state, env
    vars, or any latent non-determinism."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        evaluate_all_traits,
    )

    script = (
        "import json, sys; "
        "from loam.primary_persona.end_of_turn_trait_reflection "
        "import evaluate_all_traits; "
        "text = sys.stdin.read(); "
        "print(json.dumps(evaluate_all_traits(text)))"
    )
    for text in SAMPLE_TEXTS:
        proc = subprocess.run(
            [sys.executable, "-c", script],
            input=text,
            capture_output=True,
            text=True,
            check=True,
        )
        subprocess_verdicts = json.loads(proc.stdout)
        in_process_verdicts = evaluate_all_traits(text)
        assert subprocess_verdicts == in_process_verdicts


def test_AC_EOTTR_3_verdict_payload_excludes_clock_state() -> None:
    """The verdicts list itself MUST NOT carry ts / random / env
    state — only ``trait`` / ``verdict`` / ``reason``. The envelope
    around it (returned by ``run_trait_reflection``) carries ``ts``;
    the verdict list does not."""
    from loam.primary_persona.end_of_turn_trait_reflection import (
        evaluate_all_traits,
    )

    verdicts = evaluate_all_traits("dispatching now.")
    for v in verdicts:
        assert set(v.keys()) == {"trait", "verdict", "reason"}
        assert "ts" not in v
