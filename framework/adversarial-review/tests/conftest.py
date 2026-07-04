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

"""Shared test fixtures + the deterministic stub critic.

The stub stands in for the isolated real spawn at the model boundary (the
frame_judge test posture): tests exercise the REAL seed assembly, REAL
finding parsing, REAL validation, REAL verdict + REAL calibration scoring,
and stub ONLY the model leg — so the suite is deterministic + offline.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Put the package src on path (the package is not pip-installed in the
# test env; this mirrors the sealed frame_judge/spawn-isolation test setup).
_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# A DERIVE-phase prompt carries this marker; a DIFF-phase prompt carries
# the accomplished-failure marker. The stub routes on these so it does not
# depend on call order.
_DERIVE_MARKER = "You do NOT see the artifact yet"
_DIFF_MARKER = "This artifact SHIPPED and was torn apart"


def make_stub_critic(diff_findings_text: str, *, derived_spec: str = "SPEC: the artifact must do X, Y, Z."):
    """Build a stub model_fn returning a spec on derive, findings on diff.

    ``diff_findings_text`` is the raw text the DIFF phase returns (one or
    more ``FINDING ... END`` blocks, in the critic's output shape).
    """

    def _stub(prompt: str):
        if _DERIVE_MARKER in prompt:
            return derived_spec
        if _DIFF_MARKER in prompt:
            return diff_findings_text
        return derived_spec

    return _stub


def make_unavailable_critic():
    """A stub whose model leg is unavailable (returns None) — REVIEW INCONCLUSIVE."""

    def _stub(prompt: str):
        return None

    return _stub


def finding_block(location: str, severity: str, scenario: str) -> str:
    """Assemble one FINDING block in the critic's output shape."""
    return (
        "FINDING\n"
        f"location: {location}\n"
        f"severity: {severity}\n"
        f"scenario: {scenario}\n"
        "END"
    )


@pytest.fixture
def nontrivial_artifact() -> str:
    """A >400-char artifact carrying a distinctive quotable anchor line."""
    return (
        "# Quarterly revenue model\n\n"
        "The model projects revenue of $4.2M in FY27 based on a 12% MoM "
        "growth assumption held flat for 18 months.\n"
        "SECTION 3: the churn rate is assumed constant at 2% and is never "
        "stress-tested against the downside scenario.\n"
        "The discount rate used is 8% with no sensitivity analysis.\n"
        "Appendix A lists the input assumptions but omits the source for "
        "the 12% growth figure entirely.\n"
        "The conclusion asserts the plan is fully funded through FY29.\n"
    )


@pytest.fixture
def objective() -> str:
    return (
        "A defensible quarterly revenue model that a CFO could rely on: "
        "every material assumption sourced and stress-tested."
    )
