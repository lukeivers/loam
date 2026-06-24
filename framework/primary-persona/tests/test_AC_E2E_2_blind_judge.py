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

"""AC.E2E.2 — the judge is BLIND to the arm and the hypothesis; its
inputs structurally exclude the arm label (mirrors AC.MGRL.5).
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

_EVAL = Path(__file__).resolve().parent.parent / "eval"
if str(_EVAL.parent) not in sys.path:
    sys.path.insert(0, str(_EVAL.parent))

from eval import harness  # noqa: E402


def test_AC_E2E_2_judge_signature_excludes_arm_or_hypothesis():
    params = list(inspect.signature(harness.score_answer).parameters)
    assert params == ["prompt", "answer", "canonical_answer"], (
        f"judge signature must be (prompt, answer, canonical_answer); "
        f"got {params}"
    )
    for forbidden in ("arm", "hypothesis", "pre", "post", "supersession", "filter"):
        assert forbidden not in params


def test_AC_E2E_2_judge_scores_identically_regardless_of_arm():
    # The same answer text scores identically no matter which arm
    # produced it — there is no arm channel to influence the score.
    s1 = harness.score_answer("q", "Luke lives in Apple Valley", "apple valley")
    s2 = harness.score_answer("q", "Luke lives in Apple Valley", "apple valley")
    assert s1 == s2 == 1
    assert harness.score_answer("q", "Luke lives in Lubbock", "apple valley") == 0
