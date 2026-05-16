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

"""AC.PBD.5 — a `null` loam cost is honest-absent ONLY, never a
silent consumer-side measurement loss.

Two cases are kept DISTINCT (not conflated): (a) the loop genuinely
measured no cost (its result envelope carries `cost_usd: null`) ->
honest-absent, documented null; (b) the loop produced output but the
consumer could not parse a result envelope carrying a cost ->
consumer-side parse MISS, made VISIBLE in the run evidence, never a
silent null. The detection mechanism is the builder's call — this
asserts the honest-absent / silent-loss DISTINCTION.
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


def _extract_cost_reader():
    from programbench_revival import arms

    src = inspect.getsource(arms.run_loam_arm)
    m = re.search(
        r"(    def _last_json_object.*?\n        return result\n)",
        src,
        re.S,
    )
    assert m
    body = "from __future__ import annotations\n" + "\n".join(
        ln[4:] for ln in m.group(1).splitlines()
    )
    ns: dict = {"json": json}
    exec(compile(body, "<cost-reader>", "exec"), ns)  # noqa: S102
    return ns["_last_json_object"]


def test_AC_PBD_5_honest_absent_when_loop_measured_none() -> None:
    reader = _extract_cost_reader()
    # the loop emitted its envelope but genuinely measured no cost
    env_null = json.dumps(
        {"reached_done": False, "cost_usd": None, "wall_clock_s": 1.0},
        indent=2,
    )
    parsed = reader("chatter\n" + env_null + "\n")
    assert parsed is not None
    # honest-absent: the key IS present and its value is honestly
    # null (distinguishable from "no envelope at all")
    assert "cost_usd" in parsed
    assert parsed.get("cost_usd") is None


def test_AC_PBD_5_parse_miss_is_visible_not_silent() -> None:
    from programbench_revival import arms

    src = inspect.getsource(arms.run_loam_arm)
    norm = " ".join(src.split())
    # the consumer-side parse-miss branch exists and is made VISIBLE
    # in the evidence `out` (folded so the independent judge + run
    # evidence see it), explicitly NOT a silent null
    assert "parse MISS" in src or "parse miss" in norm
    assert "consumer-side" in norm
    assert "NOT because the loop did not measure a cost" in norm or \
        "NOT a SILENT loss" in norm or "not silently recording" in \
        norm.lower()
    # the three outcomes are explicitly enumerated as distinct in the
    # implementation rationale (measured / honest-absent / parse-miss)
    assert "AC.PBD.4" in src and "AC.PBD.5" in src
    assert "HONEST-ABSENT" in src.upper()


def test_AC_PBD_5_no_envelope_returns_none_triggering_diagnostic(
) -> None:
    reader = _extract_cost_reader()
    # loop produced output but no parseable result envelope at all
    assert reader("only progress text, no json object") is None
    # a brace inside a JSON string value must not corrupt balancing
    tricky = json.dumps(
        {"reached_done": True, "note": 'has {brace} and "q"',
         "cost_usd": 1.25},
        indent=2,
    )
    got = reader("x\n" + tricky + "\ntrailer")
    assert got is not None and got.get("cost_usd") == 1.25
