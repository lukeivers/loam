# Intake natural-language-handling fix (4 bugs caught by the loam 1.0 acceptance smoke)

Working directory: `/Users/lukeivers/loam-wt-intakefix` (isolated worktree,
branch `plan/intake-nl-handling-fix`, off `main` at `e222c1d1`).

## 1. Source of the work

The loam 1.0 acceptance smoke (`docs/experiments/loam-1.0-acceptance-smoke-run.md`,
top-line **NOT-READY**) drove the real production `loam init` + first-run intake
through three role-played non-technical users and caught FOUR real production
bugs in the intake's natural-language handling. All four live in a single file:
`framework/workspace-bootstrap/src/loam/workspace_bootstrap/translate_in_intake.py`.

This amendment fixes the four bugs, adds an AC + test per bug proving the
natural-language case now passes, then RE-RUNS the smoke to verify the
prime-objective verdict moved.

## 2. Fence (single-component)

`framework/workspace-bootstrap/` only. The fix is entirely within
`translate_in_intake.py` + its tests. Seal-test: `framework/workspace-bootstrap/
tests/test_no_sealed_amendments.py` (BASELINE `cc512b1f`). The re-run only
EXECUTES the smoke harness at `framework/tools/loam-acceptance-smoke/` — no edits
to it. The updated run-report lands at `docs/experiments/` (universal-admitted).

## 3. Halt-and-surface BEFORE build

- A bug whose real fix needs a component beyond workspace-bootstrap → surface.
- Any `claude -p` in the re-run that can't be spawn-isolated → HALT.
- The re-run revealing a regression or a new failure → surface honestly.

## 4. The four bugs + evidence (from the run-report)

1. **BUG 1 — proposal echo pastes the raw reply.** `_propose_end_intent`
   re-wraps the ENTIRE answer into the template slot, producing
   *"Help the user reliably Oh, that's an easy one — …"*. Assumes a SHORT
   phrase; real humans answer in a sentence or two.
2. **BUG 2 — natural affirmations misread.** `_is_yes`/`_is_no` match only a
   bare token or `token + " "`. `"Yeah, that'd actually help…"` → first token
   `"yeah,"` (trailing comma) matches neither → `_is_yes` returns False → the
   deep-research path never fired (the AC.SMOKE.3 gate failure). Same bug read
   `"yes, basically!"` as a correction, not a confirm.
3. **BUG 3 — brittle idea-vacuum classifier.** `_looks_empty` keys on
   substrings like `"don't know"`; `"I don't even know where to start"` (inserted
   "even") breaks the substring → variant B misclassified as PARTIAL.
4. **BUG 4 — unresolved role-noun slot.** `_leverage_from_role` pastes the full
   multi-sentence role description into the `{role}` noun position
   (*"…for a I'm a paralegal at a small litigation firm — …"*).

## 5. Acceptance criteria (each fix → a NAMED AC + a test on the NL case)

- **AC.INTAKE-ECHO.1** — the proposal distills the user's reply to a short
  intent phrase; a multi-sentence stop/start answer does NOT appear verbatim in
  `objective_text`. Test: variant-A's real raw reply in → the whole reply is not
  a substring of the proposal; the proposal stays bounded.
- **AC.INTAKE-AFFIRM.1** — natural affirmations with leading/trailing
  punctuation are recognized: `_is_yes("Yeah, that'd actually help…") is True`;
  `_is_yes("yes, basically!") is True`; negatives still negative; a true
  correction ("no, it's actually X") still routes to the correction branch.
- **AC.INTAKE-VACUUM.1** — the idea-vacuum classifier is robust to natural
  phrasings: `_looks_empty("Honestly? I don't even know where to start…") is
  True`; variant-B's real raw reply routes to `IdeaRichness.EMPTY`.
- **AC.INTAKE-ROLE.1** — the role slot resolves to a NOUN: variant-C's real
  multi-sentence role description in → the leverage-close text does NOT contain
  the raw multi-sentence blob; a concise role noun is used.

Outcome-altitude: the smoke RE-RUN drives the real `loam init` + intake on the
fixed code through three role-played users — the prime-objective verdict is the
real proof; the four unit ACs are the regression floor.

## 6. Build steps

1. Fix `_is_yes`/`_is_no` (BUG 2): normalize the first word-token (strip
   surrounding punctuation) before matching the YES/NO sets; keep the
   correction branch reachable.
2. Widen the idea-vacuum signal (BUG 3): match on normalized-token / word
   boundaries so inserted words ("even") don't break the signal; add natural
   "no idea where to start" / "do my job" style phrasings.
3. Distill the proposal (BUG 1): extract a SHORT intent phrase (first clause /
   bounded summarization) for `objective_text`, never the whole reply.
4. Extract a role NOUN (BUG 4): reduce the described role to a concise noun
   before the `{role}` substitution in `_leverage_from_role` + the seeded
   objective text.
5. Author the four AC tests (one file) on the real raw replies from the report.
6. Component suite + seal-fence green; `loam amend validate` → `apply` → `seal`.
7. Re-run the smoke; produce an updated run-report with the new grid + verdict.

## 7. Constraints

- Do NOT push, do NOT merge — owner-gated. Stop at local seal + updated report.
- Stay in the workspace-bootstrap fence for the fix.
- Every re-run `claude -p` spawn-isolated; no API key; throwaway temp home;
  never write live `~/.claude` or live loam/pos3 state; self-cleaning.

## 8. In-flight halt triggers

Out-of-fence drift; a fix needing a second component; ODD violation; an AC
unsatisfiable without method-in-AC; a re-run regression or new failure; any
un-isolatable `claude -p`.
