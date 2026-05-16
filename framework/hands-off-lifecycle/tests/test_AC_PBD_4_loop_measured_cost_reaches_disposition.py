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

"""AC.PBD.4 — the loop arm's MEASURED cost reaches the disposition.

The loop CLI emits its result as a PRETTY-PRINTED multi-line
`json.dumps({... "cost_usd": ... }, indent=2)` envelope on stdout
(handsoff_loop/cli.py). The prior `run_loam_arm` cost parse scanned
for a single line that both `startswith("{")` AND contained
`"cost_usd"` — STRUCTURALLY impossible against an `indent=2` object,
so a measured cost was silently lost to `null` on every loam
disposition (Tier-0: yj disposition loam cost_usd=None while baseline
cost_usd=0.97955...). This asserts that, given the loop's ACTUAL
emitted shape carrying a measured cost, that cost is recovered (no
lossy reduction to null).

The robust cost-capture seam (full structured read vs the fragile
line scan) is the builder's call — this asserts the OUTCOME against
the loop's real output shape, not the parse mechanism.
"""

from __future__ import annotations

import inspect
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
V2 = ROOT / "framework" / "tools" / "programbench-revival"
ISO = ROOT / "framework" / "tools" / "loam-spawn-isolation"
sys.path.insert(0, str(ISO / "src"))
sys.path.insert(0, str(V2 / "src"))


def _loop_envelope(cost) -> str:
    """The loop CLI's ACTUAL emitted result shape — a pretty-printed
    multi-line object (handsoff_loop/cli.py json.dumps(..., indent=2)
    with cost_usd as a top-level key)."""
    return json.dumps(
        {
            "reached_done": True,
            "human_loop_driving": False,
            "cost_usd": cost,
            "wall_clock_s": 123.4,
            "sub_tasks": [{"name": "deliver_yj", "done": True}],
            "behavioral_gated": False,
            "refine_attempts": 0,
            "refine_bound": 2,
            "refine_stop_reason": "done",
            "refine_log": [],
        },
        indent=2,
    )


def _extract_cost_reader():
    """Lift the cost-capture structured reader out of run_loam_arm so
    the loop's real emitted shape can be exercised without a real
    claude/loop spawn (most AC.PBD.* are deterministic)."""
    from programbench_revival import arms

    src = inspect.getsource(arms.run_loam_arm)
    m = re.search(
        r"(    def _last_json_object.*?\n        return result\n)",
        src,
        re.S,
    )
    assert m, "structured cost reader not found in run_loam_arm"
    body = "from __future__ import annotations\n" + "\n".join(
        ln[4:] for ln in m.group(1).splitlines()
    )
    ns: dict = {"json": json}
    exec(compile(body, "<cost-reader>", "exec"), ns)  # noqa: S102
    return ns["_last_json_object"]


def test_AC_PBD_4_measured_cost_recovered_from_real_loop_shape(
) -> None:
    reader = _extract_cost_reader()
    # realistic loop stdout: progress chatter, then the pretty
    # envelope, then a trailing newline
    stdout = (
        "starting loop...\n"
        "sub-agent working\n" + _loop_envelope(0.4673925) + "\n"
    )
    env = reader(stdout)
    assert env is not None
    assert env.get("cost_usd") == 0.4673925

    # Regression proof: the OLD single-line scan returns None on this
    # exact (real) shape — the silent measurement loss this AC fixes.
    old = None
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and "cost_usd" in line:
            old = json.loads(line).get("cost_usd")
            break
    assert old is None  # the defect: a measured cost was dropped


def test_AC_PBD_4_fragile_single_line_scan_is_gone() -> None:
    from programbench_revival import arms

    src = inspect.getsource(arms.run_loam_arm)
    # Strip comment lines (a comment may legitimately QUOTE the old
    # construct to document why it was removed); assert the fragile
    # construct is absent from the EXECUTABLE source only.
    code_only = "\n".join(
        ln for ln in src.splitlines()
        if not ln.lstrip().startswith("#")
    )
    norm = " ".join(code_only.split())
    assert (
        'startswith("{") and "cost_usd" in line' not in norm
    ), "the fragile single-line cost scan must be removed"
    # the robust structured reader IS the cost path now
    assert "_last_json_object" in norm
    assert 'envelope.get("cost_usd")' in norm
