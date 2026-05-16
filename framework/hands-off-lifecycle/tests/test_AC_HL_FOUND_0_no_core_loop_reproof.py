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

"""AC.FOUND.0 — fence guard: the build does NOT re-prove the core loop.

Plan: docs/plans/handsoff-loop-real-build.md (§3 AC.FOUND.0)

The decompose -> scoped-dispatch -> independent-judge -> frozen-verify
loop is established by the Tier-0 probe.  This AC verifies an ABSENCE:
the packaged orchestrator COMPOSES the proven mechanism and adds no
step that re-runs/re-proves it at unit scale (re-running the §6 probe
inside this build is a named scope violation).

Deterministic (static-source assertion; no real claude).
"""

from __future__ import annotations

from pathlib import Path

PKG = (
    Path(__file__).resolve().parents[3]
    / "framework" / "tools" / "handsoff-loop" / "src" / "handsoff_loop"
)


def test_orchestrator_composes_not_reproves() -> None:
    """The orchestrator docstring + code assert composition, not re-proof.

    Satisfiable by any structure that (a) names the probe result as
    established and (b) contains no csvkit / probe-re-run step — not
    method-bound.
    """
    src = (PKG / "orchestrator.py").read_text(encoding="utf-8")
    low = src.lower()
    # (a) the fence guard is explicit in the module.
    assert "ac.found.0" in low, (
        "orchestrator must explicitly name AC.FOUND.0 as the fence "
        "guard so a future builder cannot silently add a re-proof step"
    )
    assert "not re-prov" in low or "not re-prove" in low, (
        "orchestrator must state it does NOT re-prove the core loop"
    )
    # (b) no probe artefact / re-run smuggled in anywhere in the pkg.
    forbidden = ("csvkit", "verify_test.py builder", "re-run the probe",
                 "/tmp/handsoff-probe")
    for mod in PKG.glob("*.py"):
        text = mod.read_text(encoding="utf-8").lower()
        for needle in forbidden:
            assert needle not in text, (
                f"{mod.name} contains {needle!r} — that is the probe "
                f"being re-run inside the build (AC.FOUND.0 violation)"
            )


def test_no_unit_scale_reproof_test_exists() -> None:
    """No sibling test re-proves decompose->dispatch->judge at unit scale.

    The only AC test files for this build are the FOUND.0 guard, the
    A.* / B.* packaging+intake ACs, the two phase end-tests, C.1, and
    the seal-diff window — none of which re-establishes the core loop.
    """
    here = Path(__file__).parent
    hl_tests = sorted(p.name for p in here.glob("test_AC_HL_*.py"))
    # Sanity: the FOUND.0 guard is itself the absence-verifier; the
    # presence of a "core loop lives at unit scale" re-proof test
    # would be the violation.
    for name in hl_tests:
        assert "reprove_core" not in name and "core_loop_lives" not in name, (
            f"{name} looks like a core-loop re-proof — AC.FOUND.0 "
            f"forbids re-establishing the probe result in this build"
        )
