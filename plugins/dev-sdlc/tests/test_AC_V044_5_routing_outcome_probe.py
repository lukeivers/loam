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

"""AC.V044.5 — routing outcome-altitude probe (outcome-altitude AC).

Per ``docs/plans/v0-4-4-subagent-personas-routing-and-priming.md``
§4 AC.V044.5: a real downstream amendment cycle (or, per the
v0.4.4 build cycle, a real typed-dispatch probe) reports brief-
length delta + cycle-quality verdict in a writeup at the canonical
path. This test asserts the artefact exists + carries the verdict
+ records both brief lengths.

Skip-by-default unless ``LOAM_V044_OUTCOME_PROBE_SHIPPED=1`` —
the probe ships ASYNC after v0.4.4 seals (per D-V044.4 builder
ruling: ASYNC OK; default per dispatch-brief). The env var marks
the probe as "ready to assert"; CI without the probe shipped
skips gracefully so the test gate doesn't false-fail.

This is the outcome-altitude AC (`outcome-altitude: true` per
the plan-doc). The probe invokes a real typed dispatch
(``subagent_type: loam-*``) and observes brief-length reduction
+ cycle quality. STUB-class tests are not valid for this AC per
``feedback_test_outcome_altitude_required``.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest


CANONICAL_REPO_ROOT = Path(__file__).resolve().parents[3]
PROBE_PATH = (
    CANONICAL_REPO_ROOT
    / "workspace"
    / ".scratch"
    / "claude-output"
    / "v0-4-4-routing-probe.md"
)

# Alternative path the plan-doc references; the build cycle ships
# the probe at one of these two paths. Test accepts either.
PROBE_PATH_ALT = (
    CANONICAL_REPO_ROOT
    / "workspace"
    / ".scratch"
    / "claude-output"
    / "v0-4-4-routing-outcome-probe.md"
)


ENV_VAR = "LOAM_V044_OUTCOME_PROBE_SHIPPED"


def _probe_path() -> Path | None:
    if PROBE_PATH.is_file():
        return PROBE_PATH
    if PROBE_PATH_ALT.is_file():
        return PROBE_PATH_ALT
    return None


def _probe_present() -> bool:
    return _probe_path() is not None


@pytest.mark.skipif(
    os.environ.get(ENV_VAR) != "1",
    reason=(
        f"{ENV_VAR}!=1 — outcome-probe is async per D-V044.4 "
        "builder ruling; the probe ships post-seal and the env var "
        "marks the probe as ready to assert. Skipping until set."
    ),
)
def test_AC_V044_5_probe_artefact_exists() -> None:
    """The outcome-altitude probe artefact exists at one of the
    canonical paths."""
    assert _probe_present(), (
        f"AC.V044.5: probe artefact must exist at {PROBE_PATH} or "
        f"{PROBE_PATH_ALT} when {ENV_VAR}=1."
    )


@pytest.mark.skipif(
    os.environ.get(ENV_VAR) != "1",
    reason=(
        f"{ENV_VAR}!=1 — outcome-probe is async; skipping."
    ),
)
def test_AC_V044_5_probe_records_verdict_band() -> None:
    """The probe artefact carries a verdict-band line (GREEN /
    YELLOW / RED)."""
    path = _probe_path()
    assert path is not None
    text = path.read_text(encoding="utf-8")
    band_present = any(
        band in text for band in ("GREEN", "YELLOW", "RED")
    )
    assert band_present, (
        "AC.V044.5: probe must record a verdict band (GREEN / "
        "YELLOW / RED)."
    )


@pytest.mark.skipif(
    os.environ.get(ENV_VAR) != "1",
    reason=(
        f"{ENV_VAR}!=1 — outcome-probe is async; skipping."
    ),
)
def test_AC_V044_5_probe_records_both_brief_lengths() -> None:
    """The probe records both brief lengths (typed vs general-
    purpose) so the delta is reproducible."""
    path = _probe_path()
    assert path is not None
    text = path.read_text(encoding="utf-8")
    text_lower = text.lower()
    # Loose check: the probe mentions the comparison + has at least
    # two numeric lengths cited (lines / words / chars).
    assert "brief" in text_lower, (
        "AC.V044.5: probe must reference 'brief' (the artefact "
        "being measured)."
    )
    # Numeric digits appear at least twice (representing two
    # measurements). This is a soft check; the probe writeup is
    # the load-bearing artefact and a human reviews verdict
    # quality.
    digit_runs = sum(1 for ch in text if ch.isdigit())
    assert digit_runs >= 4, (
        "AC.V044.5: probe must record numeric brief lengths for "
        "the comparison (typed vs general-purpose)."
    )


@pytest.mark.skipif(
    os.environ.get(ENV_VAR) != "1",
    reason=(
        f"{ENV_VAR}!=1 — outcome-probe is async; skipping."
    ),
)
def test_AC_V044_5_probe_names_comparison_dispatch() -> None:
    """The probe names which dispatch was used as the typed-
    dispatch test case (so the comparison is auditable)."""
    path = _probe_path()
    assert path is not None
    text = path.read_text(encoding="utf-8")
    # The probe must reference at least one typed persona handle as
    # the dispatch under test.
    typed_handles = (
        "loam-builder",
        "loam-plan-author",
        "loam-researcher",
        "loam-reviewer",
        "loam-documenter",
    )
    assert any(h in text for h in typed_handles), (
        "AC.V044.5: probe must name the typed persona used in the "
        "comparison dispatch (one of loam-builder / loam-plan-author "
        "/ loam-researcher / loam-reviewer / loam-documenter)."
    )
