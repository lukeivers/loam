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

"""AC.PBR.3 — the scoring authority is the INDEPENDENT held-out
adversarial tool-grounded judge, PROVABLY NOT the loop's own
intake.py AC.B.4b faithfulness judge.

Outcome under test (not method): the harness's scorer composes the
proven independent-judge shape via the mandated spawn_isolated_claude
surface, is grounded in the executed check command (not the friendly
summary), and NEVER imports/calls handsoff_loop.intake._judge_faithful
/ derive_acceptance_from_intent anywhere in the harness.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PBR = ROOT / "framework" / "tools" / "programbench-revival"
sys.path.insert(0, str(PBR / "src"))


def _code_only(py: Path) -> str:
    """Source with docstrings + comments stripped — so an assertion
    cannot trip on an anti-pattern NAMED in prose (the test must
    check the real code, the ODD-correct precise outcome, not
    incidental documentation substrings)."""
    tree = ast.parse(py.read_text())
    # drop module/class/func docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef,
                             ast.AsyncFunctionDef, ast.ClassDef)):
            body = getattr(node, "body", [])
            if (body and isinstance(body[0], ast.Expr)
                    and isinstance(body[0].value, ast.Constant)
                    and isinstance(body[0].value.value, str)):
                body.pop(0)
    return ast.unparse(tree)


def test_AC_PBR_3_scorer_uses_mandated_isolation_surface() -> None:
    from programbench_revival import scorer

    src = (PBR / "src" / "programbench_revival"
           / "scorer.py").read_text()
    code = _code_only(PBR / "src" / "programbench_revival"
                       / "scorer.py")
    # composes the proven independent-judge SHAPE via the mandated
    # isolation surface (Lens 1) — never a hand-rolled subprocess.run
    assert "from loam_spawn_isolation import spawn_isolated_claude" \
        in code
    assert "spawn_isolated_claude(" in code
    # the real CODE never hand-rolls a raw claude subprocess.run
    assert 'subprocess.run' not in code, (
        "scorer must spawn ONLY through spawn_isolated_claude — no "
        "hand-rolled subprocess.run in code"
    )
    assert hasattr(scorer, "independent_judge")
    # adversarial / held-out framing + grounded in the check command
    assert "INDEPENDENT, adversarial verification analyst" in src
    assert "EXACT floor check" in src
    assert "NOT the arm's friendly summary" in src


def test_AC_PBR_3_provably_not_the_loop_own_judge() -> None:
    """The harness must NEVER import or call the loop's own AC.B.4b
    faithfulness judge (intake._judge_faithful) or
    derive_acceptance_from_intent — anywhere in the package CODE
    (docstrings/comments may NAME the forbidden path to explain the
    constraint; the real-outcome assertion is on the parsed code)."""
    pkg = PBR / "src" / "programbench_revival"
    for py in pkg.glob("*.py"):
        tree = ast.parse(py.read_text())
        # no import of the loop's intake module / its judge symbols
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                assert "handsoff_loop.intake" not in mod, (
                    f"{py.name} imports the loop's intake module — "
                    f"AC.PBR.3 forbids the loop's own judge as scorer"
                )
                for alias in node.names:
                    assert alias.name not in (
                        "_judge_faithful",
                        "derive_acceptance_from_intent",
                    ), (f"{py.name} imports the loop's own judge "
                        f"path {alias.name!r} — AC.PBR.3 forbids it")
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert "handsoff_loop.intake" not in alias.name
            # no CALL to the loop's own judge symbols
            if isinstance(node, ast.Call):
                fn = node.func
                name = (fn.id if isinstance(fn, ast.Name)
                        else getattr(fn, "attr", ""))
                assert name not in (
                    "_judge_faithful",
                    "derive_acceptance_from_intent",
                ), (f"{py.name} CALLS the loop's own judge {name!r} — "
                    f"AC.PBR.3 forbids it as the scoring authority")


def test_AC_PBR_3_judge_tags_are_the_four_definite_tags() -> None:
    """The independent judge classifies into exactly one of the four
    definite tags (faithful / checkable-but-wrong / honest-negative /
    indeterminate) — a definite per-arm-task disposition."""
    src = (PBR / "src" / "programbench_revival"
           / "scorer.py").read_text()
    for tag in ("FAITHFUL", "CHECKABLE-BUT-WRONG",
                "HONEST-NEGATIVE", "INDETERMINATE"):
        assert tag in src
