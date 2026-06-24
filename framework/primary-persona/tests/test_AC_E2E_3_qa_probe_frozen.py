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

"""AC.E2E.3 — the QA probe set is frozen pre-build (CONTENT half); its
commit is a git ancestor of the first scored-run commit (ancestry half,
verified at result time from the git ref graph per PRE_REGISTRATION §5).
"""

from __future__ import annotations

import json
from pathlib import Path

_QA = (
    Path(__file__).resolve().parent.parent
    / "eval"
    / "probes"
    / "e2e_qa_over_memory.json"
)


def test_AC_E2E_3_qa_probe_set_frozen_and_concrete():
    data = json.loads(_QA.read_text(encoding="utf-8"))
    assert data["_meta"].get("timestamps_frozen_pre_build") is True
    items = data["items"]
    assert items
    arms = {it["arm"] for it in items}
    assert arms == {"contradiction", "control"}, (
        f"the QA set must carry both arms; got {arms}"
    )
    # Every item carries a normalized canonical answer + a current record.
    for it in items:
        assert it["canonical_answer"]
        assert it["current_record"] is not None
        if it["arm"] == "contradiction":
            assert it["stale_record"] is not None, (
                f"contradiction item {it['id']} must seed a stale record"
            )


def test_AC_E2E_3_has_both_arms_for_no_regression_measurement():
    data = json.loads(_QA.read_text(encoding="utf-8"))
    n_contra = sum(1 for it in data["items"] if it["arm"] == "contradiction")
    n_ctrl = sum(1 for it in data["items"] if it["arm"] == "control")
    assert n_contra >= 5, "need a meaningful contradiction arm"
    assert n_ctrl >= 5, "need a control arm to measure no-regression"
