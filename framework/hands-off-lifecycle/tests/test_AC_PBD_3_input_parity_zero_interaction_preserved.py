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

"""AC.PBD.3 — input parity + the zero-interaction one-shot contract
are preserved.

The dependency convention is conveyed BYTE-IDENTICALLY to both arms
through the SAME single prompt both arms already receive; the harness
NEVER post-edits, patches, or inspects either arm's produced
`compile.sh`/work dir to enforce determinism (that intuitive fix
would silently violate the binding zero-interaction parity invariant,
AC.RPB.1 — the dominant design risk). The convention does NOT touch
the frozen per-task `statement` bytes in tasks.json (so the frozen
task-set content hash is unchanged).

Deterministic structural assertion (no real claude spawn).
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REALPB = ROOT / "framework" / "tools" / "programbench-revival" / "realpb"
V2 = ROOT / "framework" / "tools" / "programbench-revival"
ISO = ROOT / "framework" / "tools" / "loam-spawn-isolation"
sys.path.insert(0, str(ISO / "src"))
sys.path.insert(0, str(REALPB / "src"))
sys.path.insert(0, str(V2 / "src"))


def test_AC_PBD_3_convention_byte_identical_to_both_arms() -> None:
    from programbench_revival import arms

    # The convention block has NO format placeholders, so formatting
    # the per-task statement leaves the convention bytes UNCHANGED and
    # IDENTICAL across arms/tasks (byte-level input parity).
    import string

    fields = [
        t[1]
        for t in string.Formatter().parse(
            arms._SUBMISSION_BUILD_DEP_CONVENTION)
        if t[1] is not None
    ]
    assert fields == []

    # Both arms construct their single prompt from the SAME template.
    # Render the prompt as each arm does and assert the appended
    # convention substring is byte-identical between them.
    p_baseline = arms._ARM_DIRECTIVE.format(statement="task ALPHA")
    p_loam = arms._ARM_DIRECTIVE.format(statement="task BETA")
    conv = arms._SUBMISSION_BUILD_DEP_CONVENTION
    assert conv in p_baseline
    assert conv in p_loam
    assert p_baseline[-len(conv):] == p_loam[-len(conv):] == conv

    # Source proof both arm entry points format the SAME directive
    # template (the parity seam) — not a per-arm divergent prompt.
    arms_src = inspect.getsource(arms)
    assert arms_src.count("_ARM_DIRECTIVE.format(statement=") >= 2


def test_AC_PBD_3_no_harness_post_edit_of_produced_compile_sh() -> None:
    from programbench_revival import arms

    arms_src = inspect.getsource(arms)
    # No harness code path writes/patches/inspects an arm's PRODUCED
    # compile.sh to enforce the dep contract. The only filesystem
    # writes into a work dir are the setup-files write and the frozen
    # spec — never a compile.sh edit.
    assert "compile.sh" not in arms_src or (
        # if the token appears it is ONLY in the parity-rationale
        # comment, never as a write/patch target
        ".write_text" not in arms_src.split("compile.sh")[0][-200:]
    )
    # The harness never opens/edits a produced compile.sh by name.
    assert 'open("compile.sh"' not in arms_src
    assert "/ \"compile.sh\"" not in arms_src
    assert "'compile.sh'" not in arms_src.replace(
        "# ", "")  # not used as a path literal


def test_AC_PBD_3_frozen_task_statement_bytes_untouched() -> None:
    # The convention lives in the directive template, NOT in the
    # frozen per-task `statement` bytes — so tasks.json content (and
    # therefore its pinned content hash) is unchanged by this cycle.
    tasks_json = REALPB / "tasks" / "tasks.json"
    doc = json.loads(tasks_json.read_text(encoding="utf-8"))
    for t in doc["tasks"]:
        # the deterministic-dep convention text is NOT injected into
        # any frozen statement (it is conveyed via the directive
        # template instead)
        assert "pin every dependency" not in t["statement"].lower()
        assert "2>/dev/null" not in t["statement"]
