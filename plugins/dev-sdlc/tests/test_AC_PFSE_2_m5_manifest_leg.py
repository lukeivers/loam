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

"""AC.PFSE.2 (manifest leg) — M5 (the lens-conflict four-step process)
is a named primitive with a structural surface, declared advisory.

Per the D-PFSE.1 partition (plan §3.1, HALT-SURFACED, RF-1): the
four-step conflict process is NOT behaviourally enforced — steps 1-3
are interior cognition with no observable artefact, and an LLM-per-
action judge collides with the hook-latency budget. M5 ships as:
  (a) a named manifest primitive with `enforcement: advisory` (THIS leg);
  (b) the meta-decision-haiku arbiter SKILL (AC.PFSE.8, Slice D);
  (c) a recorded-conflict template carrying the four named steps
      (Slice D).

This test verifies the manifest leg: the M5 row exists and is declared
advisory, NOT enforced — the honest partition recorded in code.
"""

from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PLUGIN_HOOKS_DIR = REPO_ROOT / "plugins" / "dev-sdlc" / "hooks"
sys.path.insert(0, str(PLUGIN_HOOKS_DIR))

import principle_manifest_reader as reader  # noqa: E402


def test_AC_PFSE_2_m5_row_present() -> None:
    rows = reader.load_rows(REPO_ROOT)
    by_id = {r.id: r for r in rows}
    assert "M5" in by_id, (
        "AC.PFSE.2: the M5 conflict-resolution principle must be a "
        "named row in the manifest."
    )


def test_AC_PFSE_2_m5_declared_advisory_not_enforced() -> None:
    rows = reader.load_rows(REPO_ROOT)
    m5 = next(r for r in rows if r.id == "M5")
    assert m5.enforcement == "advisory", (
        f"AC.PFSE.2 / D-PFSE.1: M5 must be declared `advisory` (the "
        f"four-step process is interior cognition with no observable "
        f"artefact; behavioural enforcement is explicitly OUT). Got "
        f"{m5.enforcement!r}."
    )


def test_AC_PFSE_2_m5_mechanism_names_the_partition() -> None:
    """The M5 row's mechanism must record WHY it is advisory — the
    partition is the load-bearing decision and must be legible in the
    artefact, not only in the plan."""
    rows = reader.load_rows(REPO_ROOT)
    m5 = next(r for r in rows if r.id == "M5")
    lowered = m5.mechanism.lower()
    assert "interior cognition" in lowered or "no observable" in lowered, (
        "AC.PFSE.2: the M5 row mechanism must state the reason it is "
        "advisory (interior cognition / no observable artefact)."
    )
