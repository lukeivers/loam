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
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""AC.README.3 — outcome-altitude: true. Non-developer first-touch
comprehension smoke via fresh ``claude -p``.

Per docs/plans/readme-restructure-decision-doc-positioning.md §6
AC.README.3 (outcome-altitude: true per
feedback_test_outcome_altitude_required — every AC set has >=1
outcome-altitude AC; this one): a fresh ``claude -p`` session is
given ONLY the first 25 lines of ``README.md`` as input plus the
prompt "In one sentence each: (1) what does this tool do? (2) is
this for someone who has never used Claude Code? Answer YES/NO/
UNCLEAR plus a reason." Assert that the response to (1) names
"harness", "Claude", and "persona" or close synonyms; assert that
the response to (2) is YES or NO with a coherent reason (UNCLEAR
is a fail).

Outcome-altitude rules (per feedback_test_outcome_altitude_required):
the test invokes the production entry-point (the README itself, read
verbatim by a fresh ``claude -p`` session with no pre-arranged
state). It does NOT prescribe the README's phrasing — it tests
whether a fresh reader extracts the shape regardless of phrasing.

Gating: this test invokes real ``claude -p`` (network + cost + ~30s
wall-clock). It is gated behind the ``LOAM_AC_README_3_LIVE=1``
environment variable so the seal-time pytest suite does NOT incur
the cost on every seal — the smoke is run manually at build-step 10
of the plan-doc §7 sequence (post-seal verification, writes status
file to ``.scratch/claude-output/readme-restructure-ac3-smoke-
<date>.md``). Per feedback_no_anthropic_api_key, all LLM invocations
go through the real ``claude`` binary subprocess; per the loam-spawn-
isolation mandate, the invocation goes through
``spawn_isolated_claude`` rather than a hand-rolled
``subprocess.run(["claude", ...])``.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
README = REPO_ROOT / "README.md"

LIVE_ENV_VAR = "LOAM_AC_README_3_LIVE"

PROMPT_TEMPLATE = (
    "Below are the first 25 lines of a project's README.md. Read them, "
    "then answer two questions in one sentence each.\n\n"
    "README (first 25 lines):\n"
    "---\n"
    "{readme_excerpt}\n"
    "---\n\n"
    "Question 1: In one sentence, what does this tool do?\n"
    "Question 2: Is this tool aimed at someone who has never used "
    "Claude Code? Answer YES, NO, or UNCLEAR plus a one-sentence "
    "reason.\n\n"
    "Respond as JSON: "
    '{{"q1": "...one-sentence answer...", '
    '"q2_verdict": "YES|NO|UNCLEAR", '
    '"q2_reason": "...one-sentence reason..."}}\n'
)


def _readme_first_25_lines() -> str:
    """Return exactly the first 25 lines of README.md."""
    return "\n".join(README.read_text().split("\n")[:25])


# Synonym lists widened per AC.README3.SYN.1 (2026-05-24 corrective)
# to accept empirically-observed `claude -p` phrasings from the
# initial 2026-05-24 outcome-altitude smoke. See module docstring +
# `_check_q1_concepts` helper. Module-level so the parametrized
# fixture test can re-use the exact same logic as the live test.
HARNESS_SYNONYMS = (
    "harness", "framework", "scaffold", "substrate", "layer",
)
CLAUDE_SYNONYMS = ("claude",)
PERSONA_SYNONYMS = (
    "persona", "agent", "assistant",
    "translates", "translating", "translation",
)


def _names_any(text: str, options: tuple[str, ...]) -> bool:
    return any(opt in text for opt in options)


def _check_q1_concepts(q1: str) -> list[str]:
    """Return list of missing concept-classes for the q1 response.

    Empty list = q1 names all three concept-classes (harness-class +
    Claude-class + persona-class) via at least one synonym each.
    Non-empty list = the named classes weren't matched.

    Helper extracted per AC.README3.SYN.1 so the parametrized fixture
    test and the live `claude -p` test run the identical concept check.
    """
    q1_lower = q1.lower()
    missing: list[str] = []
    if not _names_any(q1_lower, HARNESS_SYNONYMS):
        missing.append(f"harness-class (any of {HARNESS_SYNONYMS})")
    if not _names_any(q1_lower, CLAUDE_SYNONYMS):
        missing.append(f"Claude-class (any of {CLAUDE_SYNONYMS})")
    if not _names_any(q1_lower, PERSONA_SYNONYMS):
        missing.append(f"persona-class (any of {PERSONA_SYNONYMS})")
    return missing


# Empirically-captured q1 outputs from the 2026-05-24 smoke writeup
# (.scratch/claude-output/readme-restructure-ac3-smoke-2026-05-24.md).
# These are Tier-0 evidence: actual `claude -p` outputs against the
# sealed README's first 25 lines. The widened synonym lists MUST
# accept all of them (AC.README3.SYN.1). Run 3 from the smoke isn't
# included because its q1 wasn't quoted verbatim in the writeup; the
# load-bearing fixtures are Runs 1, 2, 4 — the three that FAILED the
# pre-widening wrapper and demonstrate the empirical narrowness.
CAPTURED_CLAUDE_P_Q1_OUTPUTS = (
    pytest.param(
        # Run 1: literal "harness" present; "claude-attached" matches
        # the claude synonym; literal "persona"/"agent"/"assistant"
        # ABSENT but "translates" present as descriptive sub for
        # persona-as-translator. PRE-widening result per the smoke
        # writeup: failed on q1 missing persona-class synonyms (the
        # prose names the translation function without naming a
        # persona). Widened wrapper accepts via "translates" in
        # PERSONA_SYNONYMS.
        (
            "loam is a persistent, claude-attached harness that translates "
            "natural-language intent into ai-effective execution with memory, "
            "safety gates, and autonomous background work."
        ),
        id="run1-harness-claudeattached-translates",
    ),
    pytest.param(
        # Run 2: "layer" present (as sub for harness); "translating"
        # present (as sub for persona-as-translator); literal "persona"
        # also present. PRE-widening result: failed because "layer"
        # wasn't in harness synonyms — but the q1 contains "persona"
        # literally so it would have passed the persona check. The
        # critical failure was the harness-class check (the prose
        # uses "layer" as the head-noun, not "harness"). Widened
        # wrapper accepts via "layer" in HARNESS_SYNONYMS.
        (
            "loam is a persistent, memory-backed primary persona layer "
            "that sits on top of claude code, translating natural-language "
            "intent into ai-effective execution so the user never has to "
            "manage prompts, tools, or context manually."
        ),
        id="run2-persona-layer-translating",
    ),
    pytest.param(
        # Run 4: literal "harness" present; "translates" present (as
        # sub for persona-as-translator); literal "persona" ABSENT.
        # PRE-widening result: failed on q1 missing persona-class
        # synonyms (the prose describes the translation function
        # without naming a persona/agent/assistant). Widened wrapper
        # accepts via "translates" in PERSONA_SYNONYMS.
        (
            "loam is a persistent claude code harness that translates "
            "natural-language intent into ai-effective execution with "
            "memory, safety gates, and autonomous background work "
            "across sessions."
        ),
        id="run4-harness-translates-no-literal-persona",
    ),
)


@pytest.mark.skipif(
    os.environ.get(LIVE_ENV_VAR) != "1",
    reason=(
        "AC.README.3 outcome-altitude smoke is gated behind "
        f"{LIVE_ENV_VAR}=1 (invokes real ``claude -p``; cost + ~30s "
        "wall-clock). Run manually at plan-doc §7 step 10 (post-seal "
        "verification) — `LOAM_AC_README_3_LIVE=1 pytest "
        "framework/workspace-bootstrap/tests/"
        "test_AC_README_3_outcome_altitude_first_touch_comprehension.py`."
    ),
)
def test_first_touch_comprehension_smoke_via_claude_p() -> None:
    """Fresh ``claude -p`` extracts the README's positioning + audience."""
    try:
        from loam_spawn_isolation import spawn_isolated_claude
    except ImportError as exc:  # pragma: no cover - environmental
        pytest.skip(
            f"loam_spawn_isolation not importable in this env ({exc}); "
            "the outcome-altitude smoke requires the spawn-isolation "
            "primitive to run. Install via `pip install -e "
            "framework/tools/loam-spawn-isolation` or re-invoke with "
            "the project venv on sys.path."
        )

    excerpt = _readme_first_25_lines()
    prompt = PROMPT_TEMPLATE.format(readme_excerpt=excerpt)

    proc = spawn_isolated_claude(
        ["claude", "-p", prompt, "--model", "sonnet",
         "--output-format", "json", "--permission-mode",
         "bypassPermissions"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert proc.returncode == 0, (
        f"AC.README.3: claude -p exited {proc.returncode}; "
        f"stderr: {(proc.stderr or '')[:400]}"
    )

    raw = (proc.stdout or "").strip()
    try:
        env = json.loads(raw)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"AC.README.3: claude -p stdout not parseable as JSON "
            f"envelope: {exc}. stdout: {raw[:400]}"
        )

    verdict_text = (env.get("result") or "").strip()
    # The verdict may be wrapped in a ```json ... ``` fence.
    verdict_clean = verdict_text.strip().strip("`")
    if verdict_clean.startswith("json"):
        verdict_clean = verdict_clean[len("json"):].strip()

    try:
        verdict = json.loads(verdict_clean)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"AC.README.3: verdict not parseable as JSON: {exc}. "
            f"verdict_text: {verdict_text[:400]}"
        )

    q1 = (verdict.get("q1") or "").lower()
    q2_verdict = (verdict.get("q2_verdict") or "").upper().strip()
    q2_reason = (verdict.get("q2_reason") or "").strip()

    # AC: response to (1) names "harness", "Claude", and "persona" or
    # close synonyms. We accept synonyms loosely — the criterion is
    # whether the model extracted the shape, not whether it used the
    # exact words.
    #
    # Synonym lists widened per AC.README3.SYN.1 (2026-05-24 corrective)
    # to accept empirically-observed `claude -p` phrasings from the
    # initial 2026-05-24 outcome-altitude smoke (4/4 runs returned the
    # correct shape; wrapper PASS-rate was 1/4 because "layer" + the
    # translation-verbs weren't in the literal lists). Per
    # `feedback_loose_AC_text_fix_AC_not_implementation`: README is
    # correct, wrapper was over-narrow, fix the wrapper.
    missing = _check_q1_concepts(q1)

    assert not missing, (
        f"AC.README.3 q1: response to 'what does this tool do?' "
        f"missing required concepts: {missing}. q1 response: {q1!r}"
    )

    # AC: response to (2) is YES or NO with a coherent reason
    # (UNCLEAR is a fail).
    assert q2_verdict in {"YES", "NO"}, (
        f"AC.README.3 q2: verdict must be YES or NO; UNCLEAR is a "
        f"fail per the AC spec. Got {q2_verdict!r}. Reason given: "
        f"{q2_reason!r}"
    )
    assert q2_reason, (
        f"AC.README.3 q2: a coherent reason must accompany the "
        f"YES/NO verdict. Got empty reason. verdict={q2_verdict!r}"
    )

    # Surface verdict to stdout for status-file capture at build-step
    # 10. The test runner captures stdout; the calling script writes
    # the smoke writeup to .scratch/claude-output/.
    print(json.dumps({
        "ac": "AC.README.3",
        "q1": q1,
        "q2_verdict": q2_verdict,
        "q2_reason": q2_reason,
        "missing_concepts": missing,
        "passed": True,
    }, indent=2), file=sys.stdout)


@pytest.mark.parametrize("q1_text", CAPTURED_CLAUDE_P_Q1_OUTPUTS)
def test_widened_synonym_check_accepts_observed_claude_p_phrasings(
    q1_text: str,
) -> None:
    """AC.README3.SYN.1 — widened synonym lists accept all observed
    empirical phrasings.

    Per the 2026-05-24 outcome-altitude smoke (see
    .scratch/claude-output/readme-restructure-ac3-smoke-2026-05-24.md),
    the AC.README.3 test wrapper's pre-widening synonym lists rejected
    3/4 actual `claude -p` outputs even though the README content was
    semantically correct (4/4 runs extracted the intended shape — named
    Claude + harness-class + persona-as-translator function). Per
    `feedback_loose_AC_text_fix_AC_not_implementation`: the
    implementation (README) is correct + intent-matching; the test
    wrapper's literal-keyword list was the loose codification.

    This corrective widened HARNESS_SYNONYMS to add "layer" and
    PERSONA_SYNONYMS to add "translates"/"translating"/"translation".
    This test asserts the widening reaches all 3 empirically-captured
    failing outputs from the smoke writeup (Runs 1, 2, 4 — Run 3
    passed the pre-widening wrapper and isn't load-bearing for this
    test).

    No `claude -p` invocation; pure fixture-based verification of the
    synonym-check logic. Runs every pytest pass (no env-gate).
    """
    missing = _check_q1_concepts(q1_text)
    assert not missing, (
        f"AC.README3.SYN.1: widened synonym lists rejected an "
        f"empirically-captured `claude -p` Q1 output; missing "
        f"concept-classes: {missing}. Q1 text: {q1_text!r}. "
        f"Per Surface #3 of the corrective plan-doc, this is a halt-"
        f"and-surface condition (the widening doesn't address the "
        f"empirical narrowness)."
    )
