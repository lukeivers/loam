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

"""AC.MGRL.4 — a pre-registration artefact exists, fixing the task set, the
metric definitions, what "better" means, and the theory-vs-generic
discriminator; each concrete enough to apply without further judgment.

The git-ancestry half of the AC (the pre-reg commit is an ancestor of the
first scored-run commit) is verified at seal/result time from the git ref
graph per PRE_REGISTRATION §5 + plan §9 — it is recorded in the result doc,
not asserted in a unit test (the first scored-run commit does not exist at
build time). This test pins the CONTENT half: the four fixed items are
present and concrete.
"""

from __future__ import annotations

from pathlib import Path

_PREREG = Path(__file__).resolve().parent.parent / "experiment" / "PRE_REGISTRATION.md"
_TASKSET = Path(__file__).resolve().parent.parent / "experiment" / "task_set.json"


def test_AC_MGRL_4_pre_registration_artefact_exists():
    assert _PREREG.exists()
    assert _TASKSET.exists()


def test_AC_MGRL_4_fixes_the_four_required_items():
    text = _PREREG.read_text()
    # (1) the task set is fixed
    assert "task_set.json" in text and "FROZEN" in text
    # (2) the metric definitions
    assert "## §2 The metric" in text and "correct" in text
    # (3) what "better" means
    assert 'what "better" means' in text or "Aggregate quality delta" in text
    # (4) the theory-vs-generic discriminator
    assert "discriminator" in text
    assert "gain_on_flagged" in text and "gain_on_unflagged" in text


def test_AC_MGRL_4_verdict_rule_is_concrete_enough_to_apply():
    # The verdict rule must be applicable without further judgment (a fixed
    # rule mapping the computed quantities to a verdict).
    text = _PREREG.read_text()
    assert "THEORY-PREDICTION CONFIRMED" in text
    assert "GENERIC-LIFT-ONLY" in text
    assert "NULL" in text
