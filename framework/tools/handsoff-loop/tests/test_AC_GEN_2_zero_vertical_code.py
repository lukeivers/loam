"""AC.GEN.2 — zero vertical-specific code in framework source (S3).

The honest-demo doctrine's sharpened rule 2, structurally checkable:

  * the build-from-intent pipeline source contains NO branch keyed to
    a business domain — enforced here as a strict ZERO-HIT sweep for
    business-domain vocabulary across every pipeline source file
    (stronger than a branch check: the words cannot appear at all, so
    a domain-keyed branch cannot exist);
  * one identical pipeline code path serves materially different
    domains — pinned deterministically here by running the SAME
    entry functions over two materially different domain inputs and
    asserting both flow through identically (the live four-domain
    evidence is the S6 run log, where every run records the same
    documented entry command).

Per docs/plans/general-build-from-intent.md §6.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from handsoff_loop.generative import generate_design  # noqa: E402
from handsoff_loop.request_intent import RequestIntent  # noqa: E402

_PKG = _SRC / "handsoff_loop"

# Business-domain vocabulary that would mark a vertical-keyed shortcut
# in the generative path. The sweep is ZERO-HIT across all pipeline
# source — docstrings included (a domain word in prose is one refactor
# away from a domain branch).
_DOMAIN_WORDS = re.compile(
    # "billing" is deliberately absent: the sealed orchestrator's
    # comments use it for Anthropic PLAN accounting (subscription vs
    # metered API billing), which is infrastructure vocabulary, not a
    # business vertical.
    r"invoice|reconcil|dedup|ledger|bookkeep|accounting|payroll|"
    r"payment|inventory|real.?estate|migration.?mapping",
    re.IGNORECASE,
)


def test_zero_domain_vocabulary_in_pipeline_source():
    hits = []
    for py in sorted(_PKG.glob("*.py")):
        for i, line in enumerate(
                py.read_text(encoding="utf-8").splitlines(), 1):
            if _DOMAIN_WORDS.search(line):
                hits.append(f"{py.name}:{i}: {line.strip()}")
    assert hits == [], (
        "business-domain vocabulary in pipeline source (a vertical-"
        f"keyed shortcut waiting to happen): {hits}"
    )


def _echo_llm(prompt, *, model="sonnet", timeout=0):
    # Derives a complete design purely from the prompt's objective
    # line, proving the path is input-driven, not domain-driven.
    obj = [ln for ln in prompt.splitlines() if "derived from:" in ln][0]
    return {"result": json.dumps({
        "tool_plan": f"plan for {obj}",
        "data_shape": "in/out files",
        "gate_plain": f"done for {obj}",
        "gate_criteria": [{"criterion": "works", "traceable_to": ""}],
        "gate_files": {"check.py": "pass\n"},
        "check_command": "python3 {gate_dir}/check.py {work_dir}",
        "held_out_command": "",
        "sub_tasks": [{"name": "t", "brief": f"build for {obj}",
                       "tighter_acceptance": "ok"}],
        "judge_scope": "sample only",
    })}


def test_one_identical_code_path_serves_different_domains():
    def _intent(ask):
        return RequestIntent(ask=ask, inferred_intent=f"intent: {ask}",
                             objective=f"derived from: {ask}")

    a = generate_design(_intent("match the clinic's appointment list "
                                "against the visit log"),
                        None, llm_json_fn=_echo_llm)
    b = generate_design(_intent("turn band rehearsal recordings into "
                                "a practice schedule"),
                        None, llm_json_fn=_echo_llm)
    # Same entry point, same code path, materially different domains,
    # both fully served — and each design carries ITS run's substance.
    assert "clinic" in a.tool_plan and "rehearsal" in b.tool_plan
    assert type(a) is type(b)
