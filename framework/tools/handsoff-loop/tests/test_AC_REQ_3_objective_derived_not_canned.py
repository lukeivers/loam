"""AC.REQ.3 — the objective is derived per-run; no canned objective.

  * the stated objective for any run is derived from that run's ask
    and echoes its specifics;
  * two different asks produce two different stated objectives;
  * NO objective text exists in the pipeline source — the pipeline's
    own files contain no pre-written objective sentence a run could
    fall back to (the June-8 hardcoded-objective failure, made
    structurally impossible);
  * canonical loam's executable source contains ZERO references to
    the retired `loam_autoroute` artifact.  (The plan-doc that ordered
    the retirement names the artifact by name — prose about retiring
    it is the record OF the retirement, not a dependency on it; the
    sweep therefore covers the source trees, where a reference could
    actually revive the shortcut.)

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.request_intent import understand_request  # noqa: E402

_REPO = Path(__file__).resolve().parents[4]
_PKG_DIR = _SRC / "handsoff_loop"


def _echoing_llm(prompt, *, model="sonnet", timeout=0):
    ask = prompt.split('"""')[1]
    return {"result": json.dumps({
        "inferred_intent": f"intent for: {ask}",
        "objective": f"objective derived from: {ask}",
        "questions": [],
        "form_factor": "cli",
        "form_factor_plain": "",
    })}


def test_two_different_asks_two_different_objectives():
    a = understand_request("reconcile the bank statement lines",
                           llm_json_fn=_echoing_llm)
    b = understand_request("merge three customer lists into one",
                           llm_json_fn=_echoing_llm)
    assert a.objective != b.objective
    assert "bank statement" in a.objective
    assert "customer lists" in b.objective


def test_no_objective_text_in_pipeline_source():
    """The pipeline source carries no pre-written run objective.

    `RequestIntent.objective` has exactly one assignment path — the
    parsed live read.  Structural AST check: no call in the module
    passes a non-empty STRING LITERAL as an `objective=` keyword, so
    there is nothing canned for a run to fall back to.
    """
    import ast

    tree = ast.parse(
        (_PKG_DIR / "request_intent.py").read_text(encoding="utf-8"))
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "objective" and isinstance(
                        kw.value, ast.Constant) and kw.value.value:
                    offenders.append(ast.dump(kw.value))
    assert offenders == [], (
        f"canned objective literal(s) in pipeline source: {offenders}"
    )


def test_zero_autoroute_references_in_canonical_source():
    """grep the executable source trees for the retired artifact."""
    hits = subprocess.run(
        ["grep", "-rl", "--exclude-dir=__pycache__", "loam_autoroute",
         str(_REPO / "framework"), str(_REPO / "plugins")],
        capture_output=True, text=True,
    ).stdout.strip().splitlines()
    # This test file names the artifact in order to assert its absence
    # everywhere else; it is the only admissible hit.
    hits = [h for h in hits if not h.endswith(Path(__file__).name)]
    assert hits == [], f"retired loam_autoroute referenced by: {hits}"
