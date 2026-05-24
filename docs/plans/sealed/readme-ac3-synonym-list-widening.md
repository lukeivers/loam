# Doc-only test wrapper widening — AC.README.3 synonym lists (corrective)

2026-05-24. Corrective to predecessor cycle
`readme-restructure-decision-doc-positioning` (sealed at `a39d5ce`).
Per builder halt-and-surface D-build.README.2 + the smoke writeup
at `.scratch/claude-output/readme-restructure-ac3-smoke-2026-05-24.md`:
the AC.README.3 test wrapper's literal-keyword synonym lists were
over-narrow vs actual `claude -p` phrasing variance. 4/4 live runs
returned semantically-correct shape; wrapper PASS-rate was 1/4 (25%)
because "layer" (sub for harness) and "translates"/"translating"/
"translation" (descriptive sub for persona-as-translator) weren't
in the literal keyword lists.

Per `feedback_loose_AC_text_fix_AC_not_implementation`: the
implementation (README) is correct and intent-matching; the test
wrapper's literal-keyword list is the loose codification. This
corrective widens the wrapper, NOT the README.

Two changes (one cycle, one AC, scope = single test file only):

1. Widen `harness_synonyms` tuple in
   `framework/workspace-bootstrap/tests/test_AC_README_3_outcome_altitude_first_touch_comprehension.py`
   to add `"layer"`.

2. Widen `persona_synonyms` tuple in the same file to add
   `"translates"`, `"translating"`, `"translation"`.

3. Add a new parametrized test function
   `test_widened_synonym_check_accepts_observed_claude_p_phrasings`
   in the same file that replays the 4 captured Q1 outputs from
   the 2026-05-24 smoke writeup as inline fixtures and asserts the
   widened synonym check passes for all 4. The new test runs every
   pytest pass (no env-gate, no `claude -p` invocation).

What does NOT change: the README content (already empirically
correct); the AC.README.3 prompt template; the `claude_synonyms`
tuple (4/4 runs named "claude" literally); the Q2 verdict logic;
the env-gated live `claude -p` test (`LOAM_AC_README_3_LIVE=1`
behaviour preserved).

AC.README3.SYN.1 — widened synonym lists accept all 4 captured
outputs. Parametrized test function in the AC.README.3 wrapper
file asserts pass on the 4 empirical Q1 outputs from the
2026-05-24 smoke. Method-in-AC test passed (alternative widening
shapes that pass all 4 satisfy the AC).

Composes with: predecessor cycle's AC.README.3 (this corrective
restores wrapper fidelity to the outcome-target); Lens-4
prompt-scope-confidence (high confidence — Tier-0 empirical
outputs literally show the exact keywords); LOOSE-AC-TEXT-FIX-AC
(implementation correct, wrapper loose, fix wrapper);
LOCKED-DESIGN-NOT-LICENSE (predecessor wrapper revisitable;
builder halt is the trigger).

Single-component fence: framework/workspace-bootstrap/. The
edited test file lives inside the anchor. NOT merged to main,
NOT pushed, NOT tagged. NO Anthropic API key — corrective is
test-fixture-based, no `claude -p` invocation needed (the
captured outputs from the 2026-05-24 smoke are the empirical
evidence). No version bump (version derives at release-time
per feedback_version_numbers_at_release_time).
