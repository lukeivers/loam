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

"""AC.SUP.6 — anachronism firewall (CONTENT half).

The supersession probe set's seed timestamps are FIXED before the change
is built, and the probe-set commit is a git ancestor of the first
scored-run commit. This test pins the CONTENT half: the frozen probe set
+ the pre-registration exist and carry concrete frozen timestamps. The
GIT-ANCESTRY half (the pre-reg commit is an ancestor of the first
scored-run commit) is verified at result time from the git ref graph per
PRE_REGISTRATION §5, not asserted here (the first scored-run commit does
not exist at build time — mirrors AC.MGRL.4).
"""

from __future__ import annotations

import json
from pathlib import Path

_EVAL = Path(__file__).resolve().parent.parent / "eval"
_PREREG = _EVAL / "PRE_REGISTRATION.md"
_TRIPLES = _EVAL / "probes" / "sup_contradiction_triples.json"
_QA = _EVAL / "probes" / "e2e_qa_over_memory.json"
_RCT = _EVAL / "probes" / "rct_heldout_split.json"


def test_AC_SUP_6_prereg_and_probe_sets_exist():
    assert _PREREG.exists(), "pre-registration artefact missing"
    assert _TRIPLES.exists()
    assert _QA.exists()
    assert _RCT.exists()


def test_AC_SUP_6_prereg_fixes_the_required_items():
    text = _PREREG.read_text(encoding="utf-8")
    assert "FROZEN" in text
    assert "Currentness@1" in text and "1.0" in text
    assert "ZERO TOLERANCE" in text
    assert "ancestor" in text  # the git-ancestry firewall is named
    # The RCT drop rule is concrete enough to apply without judgment.
    assert "EARNED" in text and "NOT-EARNED" in text
    assert "straddles zero" in text


def test_AC_SUP_6_probe_timestamps_are_frozen_concrete():
    data = json.loads(_TRIPLES.read_text(encoding="utf-8"))
    assert data["_meta"].get("timestamps_frozen_pre_build") is True
    triples = data["triples"]
    assert triples
    for t in triples:
        # Every triple carries concrete ISO timestamps (the seed times
        # the firewall freezes).
        assert "T" in t["stale"]["valid_from"]
        assert "T" in t["stale"]["valid_to"]
        assert "T" in t["current"]["valid_from"]
        assert "T" in t["as_of"]
        assert t["fact_type"] in {
            "decision_ruling",
            "personal_fact",
            "version_state_fact",
            "config_fact",
        }


def test_AC_SUP_6_all_four_fact_types_covered():
    data = json.loads(_TRIPLES.read_text(encoding="utf-8"))
    types = {t["fact_type"] for t in data["triples"]}
    assert types == {
        "decision_ruling",
        "personal_fact",
        "version_state_fact",
        "config_fact",
    }, f"all four real supersession fact-types must be covered; got {types}"
