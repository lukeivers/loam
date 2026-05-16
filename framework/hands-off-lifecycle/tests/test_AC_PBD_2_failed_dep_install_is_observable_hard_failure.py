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

"""AC.PBD.2 — a failed dependency install is an observable hard build
failure (never a silent `2>/dev/null || true`-class swallow).

The yj/figlet evidence showed every arm's agent-authored
`compile.sh` installed deps with `pip3 install --quiet ...
2>/dev/null || true`, swallowing every install failure so a
dependency-gated test family passed/failed by luck under amd64
emulation. The convention conveyed to the arm must FORBID that
swallow construct on the dependency step and require the build to
fail loud (non-zero exit propagating to the upstream
`compile_failed => 0` contract — no new outcome semantics, no
interactive prompt, no retry-to-green).

Deterministic structural assertion (no real claude spawn).
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / "framework" / "tools" / "programbench-revival"
ISO = ROOT / "framework" / "tools" / "loam-spawn-isolation"
sys.path.insert(0, str(ISO / "src"))
sys.path.insert(0, str(V2 / "src"))


def test_AC_PBD_2_convention_forbids_silent_swallow_requires_fail_loud(
) -> None:
    from programbench_revival import arms

    prompt = arms._ARM_DIRECTIVE.format(statement="recreate the tool")
    low = prompt.lower()

    # The exact swallow constructs the yj/figlet compile.sh used are
    # named and forbidden on the dependency-install step.
    assert "2>/dev/null" in prompt
    assert "|| true" in prompt
    assert "|| :" in prompt
    # "never ... continue / suppress" — the swallow is forbidden, not
    # merely discouraged.
    assert "must fail loud" in low
    assert "exit non-zero" in low or "non-zero" in low
    assert (
        "do not suppress install errors and continue" in low
        or "must report itself as one" in low
    )
    # No interactive recovery / retry-to-green is introduced (the
    # zero-interaction one-shot contract AC.RPB.1 / honest-negative-
    # first-class AC.RPB.7 are unchanged): a loud failure is a
    # non-pass BY CONSTRUCTION, explicitly "no retry".
    assert "no retry" in low
    assert "ask" in low  # "there is no one to ask"
