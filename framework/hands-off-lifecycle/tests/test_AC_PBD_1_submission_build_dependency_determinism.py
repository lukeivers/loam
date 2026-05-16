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

"""AC.PBD.1 — the submission build's dependency step is deterministic.

The dependency-acquisition convention conveyed to the arm specifies a
FIXED, reproducible dependency set (pinned exact versions), so the
same submission resolves to the same dependency-gated outcome every
build instead of varying by install luck.

Deterministic structural assertion (no real claude spawn): the
single prompt template BOTH arms construct their prompt from carries
a dependency convention that requires EXACT version pinning. The
mechanism (pin vs vendor vs hash-lock) is the builder's call — this
asserts the OUTCOME (a deterministic dependency contract is conveyed),
not a specific shell construct.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / "framework" / "tools" / "programbench-revival"
ISO = ROOT / "framework" / "tools" / "loam-spawn-isolation"
sys.path.insert(0, str(ISO / "src"))
sys.path.insert(0, str(V2 / "src"))


def test_AC_PBD_1_convention_requires_deterministic_pinned_deps() -> None:
    from programbench_revival import arms

    # The convention reaches the arm through the SAME single prompt
    # template both arms format (parity seam, AC.PBD.3) — assert the
    # rendered prompt, not an internal constant name.
    prompt = arms._ARM_DIRECTIVE.format(statement="recreate the tool")

    low = prompt.lower()
    # A deterministic dependency contract is conveyed: dependencies,
    # if installed, must be pinned to an exact version so the same
    # submission resolves to the same dependency set.
    assert "dependency" in low
    assert "exact version" in low
    assert "reproducible" in low
    # The convention names a reproducible-build motivation (the same
    # submission builds the same way) — not a one-off install.
    assert "same submission" in low or "every time it is built" in low
    # An example pin form is shown so the agent has a concrete
    # deterministic pattern to follow (a method exemplar, not the
    # only satisfying method).
    assert "==" in prompt
