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

"""AC.RPB.3 — the scoring authority is the INDEPENDENT held-out
adversarial tool-grounded judge GROUNDED in the real upstream
*.eval.json, PROVABLY NOT the loop's own intake.py AC.B.4b judge
(REUSED v2 scorer read-only, real-PB-bound).
"""

from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REALPB = ROOT / "framework" / "tools" / "programbench-revival" / "realpb"
V2 = ROOT / "framework" / "tools" / "programbench-revival"
sys.path.insert(0, str(REALPB / "src"))
sys.path.insert(0, str(V2 / "src"))


def test_AC_RPB_3_independent_judge_grounded_in_real_eval() -> None:
    from programbench_revival_realpb import runner
    from programbench_revival.scorer import independent_judge

    # the runner REUSES v2's independent judge read-only (Lens 1) —
    # composes the proven _independent_judge via spawn_isolated_claude
    assert runner.independent_judge is independent_judge
    scorer_src = inspect.getsource(sys.modules[
        "programbench_revival.scorer"])
    assert "spawn_isolated_claude" in scorer_src
    assert "_independent_judge" in scorer_src

    # PROVABLY NOT the loop's own judge: assert the real invariant —
    # neither module IMPORTS or CALLS the loop's intake faithfulness
    # judge (the documentation legitimately *names* it to state it is
    # NOT used, so a bare substring ban would be wrong; we check for
    # an actual import statement / call site instead).
    runner_src = inspect.getsource(runner)
    import ast

    for src in (runner_src, scorer_src):
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", "") or ""
                names = " ".join(a.name for a in node.names)
                blob = f"{mod} {names}"
                assert "intake" not in blob, (
                    f"must NOT import the loop's intake judge: {blob}"
                )
                assert "_judge_faithful" not in blob
                assert "derive_acceptance_from_intent" not in blob
            if isinstance(node, ast.Call):
                callee = ast.unparse(node.func)
                assert "_judge_faithful" not in callee
                assert "derive_acceptance_from_intent" not in callee
                assert "intake" not in callee

    # the judge is GROUNDED in the REAL upstream *.eval.json graded
    # score + the frozen per-task floor theta (not the friendly
    # summary): the runner passes the real eval evidence into the
    # judge's transcript_tail + floor_cmd
    runner_norm = " ".join(runner_src.split())
    assert "REAL upstream programbench eval" in runner_norm
    assert "graded-score=" in runner_src
    assert "frozen-floor-theta=" in runner_src
    assert "GROUNDED in the real" in runner_norm or \
        "GROUNDED in the REAL" in runner_norm

    # the run result names the scoring authority + provenance.
    # Assert the RUNTIME contract, not the source text: the
    # scoring_authority string a real run records (the function
    # builds it from a multi-line literal that line-wraps in source —
    # the durable fact is the produced string, so reconstruct it the
    # way the function does and check the invariant).
    rr_src = inspect.getsource(runner.run_realpb_experiment)
    # join adjacent string literals exactly as Python does (drop the
    # `" <newline+indent> "` implicit-concat boundary), then collapse
    # whitespace — this yields the runtime string content.
    import re

    joined = re.sub(r'"\s*\n\s*"', "", rr_src)
    rr = " ".join(joined.split())
    assert "PROVABLY NOT the loop's own" in rr
    assert "handsoff_loop.intake._judge_faithful" in rr  # named
    assert "never imported / never called by this harness" in rr
    assert "REAL upstream" in rr
