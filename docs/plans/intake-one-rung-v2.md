# Intake one-rung leverage-ladder + default-ask close (the 1.0-finishing round)

Working directory: `/Users/lukeivers/loam-wt-onerung` (isolated worktree, branch
`plan/intake-one-rung-v2`, off `main` at `bdac5735` — the merged intake LLM-seam
amendments #172–#178).

Runner note (environment): the installed `loam` resolves to the SIBLING worktree
`/Users/lukeivers/loam`, so this worktree's tests run with this tree's `src` on
`PYTHONPATH` under homebrew `python3.13`:
`PYTHONPATH="$PWD/src" /opt/homebrew/opt/python@3.13/bin/python3.13 -m pytest …`
(the smoke component also needs the workspace-bootstrap `src` on the path).

## 1. Source of the work (owner ruling, Luke 13401 + 13403)

The 1.0 acceptance smoke's last gap is a JUDGE-vs-CONTRACT contradiction. The
`four-step-loop-ran` rubric demands leg 2 ("propose a healthy way to enable it")
show CONCRETE STRUCTURE (a recurring workflow / template / designed enablement
pattern), while `no-over-engineering` PASSES *because* loam proposed no structure
— the two dimensions demand opposite things on the SAME transcript (rerun12
variants A+B PARTIAL on `four-step-loop-ran`, PASS on `no-over-engineering`).

Owner ruling: the close's bar is RELATIVE. loam may ASK about moving EXACTLY ONE
rung up from the literal request — opt-in, ask-only, never two+ rungs
(doc → template = OK to ask; doc → workflow = too big a jump, forbidden). This
SHARPENS no-over-engineering (AC.ONCLOSE.3): "proportional" = one rung, ask-only.

**THE SIGNAL-GATE — DEFAULT IS TO ASK (owner-corrected, 13403, precise).** The
one-rung-up question is asked BY DEFAULT. The user's signal is a SUPPRESSOR
ONLY: change to NOT-asking ONLY when the user clearly signals one-off /
"no thanks" / overwhelmed-just-this-once / explicit decline. With NO clear
suppressing signal → ASK (the default). This is NOT "ask only when a recurrence
signal is present" — that would invert the default.

These are NOT open design forks; the target is the owner's ratified design. This
cycle implements it, adds an AC + test per rule, RE-RUNS the smoke, honest
verdict.

## 2. Fences (two components — declared multi-component amendment)

1. **workspace-bootstrap** — the leverage-ladder + one-rung default-ask close, the
   LLM intent-extractor activated as the PRODUCTION default, and disposition moved
   into the LLM extractor. Within
   `framework/workspace-bootstrap/src/loam/workspace_bootstrap/`
   (`translate_in_intake.py`, `intent_extract.py`, `first_run_intake.py`/CLI for
   the production-default activation) + its tests. Seal-test:
   `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`. BASELINE:
   the workspace-bootstrap sidecar HEAD (`f9ba2fe`).
2. **loam-acceptance-smoke** — the `four-step-loop-ran` judge-rubric
   contract-alignment. Within
   `framework/tools/loam-acceptance-smoke/src/loam_acceptance_smoke/judge.py` +
   a test. Seal-test:
   `framework/tools/loam-acceptance-smoke/tests/test_no_sealed_amendments.py`.
   BASELINE: the smoke sidecar HEAD (`625303cf`).

The re-run only EXECUTES the smoke harness; its run-report lands under
`docs/experiments/` (universal-admitted).

## 3. Halt-and-surface BEFORE / DURING build

- The one-rung ladder genuinely ambiguous for a request type (what IS rung+1?)
  needing an owner call → surface the specific case, do not guess.
- A fix needing a component beyond these two → surface.
- Any `claude -p` in the re-run that cannot be spawn-isolated → HALT.
- The re-run revealing a regression or non-converging pattern → surface honestly;
  never manufacture READY.
- An ODD violation in my work OR surrounding code → halt + surface.

## 4. The five rules → named ACs (each rule a NAMED AC + a test)

New family **AC.ONRUNG.\*** (the leverage-ladder one-rung default-ask close;
ladders up from AC.ONCLOSE.2/.3 — it SHARPENS "proportional" to "one rung,
ask-only, ask-by-default"):

- **AC.ONRUNG.1 — the leverage ladder + rung+1 read.** From the distilled
  request loam reads where it sits on a leverage ladder (doc → template →
  workflow → system; spreadsheet → reusable-formula → dashboard → pipeline;
  one-off-task → recurring-helper → automation) and computes EXACTLY rung+1.
  Test: representative requests at each starting rung yield a rung+1 that is the
  immediate next rung — NEVER rung+2 (a doc never yields "workflow"/"system").
- **AC.ONRUNG.2 — the close ASKS at most rung+1, opt-in, never rung+2+.** The
  close still LANDS the literal request as the ONE landed deliverable
  (AC.ONCLOSE.2 intact); the one-rung-up is a SINGLE OPTIONAL rider QUESTION
  (phrased as an ask the user can decline), not a second landed deliverable and
  not an assertion of structure. Test: `len(leverage_ideas) == 1`; the close text
  contains the rung+1 ask phrased opt-in; the close contains no rung+2 token for
  a rung-0 request.
- **AC.ONRUNG.3 — DEFAULT IS TO ASK; signal SUPPRESSES.** Absent a clear
  suppressing signal, the one-rung ask IS present. A clear one-off signal
  ("just this once", "no thanks", "I'm overwhelmed, just this one thing",
  "one-off", explicit decline) SUPPRESSES it (the close lands the one thing with
  NO rung+1 rider). Test: a neutral request → ask present; each suppressing
  signal → ask absent; the landed deliverable is present in BOTH cases.

Family **AC.INTENT.\*** activation + disposition migration:

- **AC.INTENT.5 — the LLM extractor is the PRODUCTION default.** The real
  `ClaudeIntentExtractor` is the default the production orchestrator resolves
  (replacing the built-but-off `DisabledIntentExtractor` default), so the
  four-step loop is LIVE in production, not only when a consumer registers it.
  The fail-soft regex fallback is RETAINED (onboarding never breaks if the call
  fails). Test: the production default is the Claude extractor; a forced
  extractor failure still completes the intake via the regex fallback.
- **AC.INTENT.6 — disposition is read by the LLM extractor (regex fallback).**
  STOP-vs-START disposition is read through the LLM extractor as the primary
  path, fail-soft to the deterministic `_detect_disposition` regex — retiring the
  keyword-regex disposition bug class as the SOLE reader. Test: the extractor's
  disposition read drives the close when present; on extractor failure the regex
  `_detect_disposition` still classifies; the prior AC.DISPOS.1 cases still hold
  via the fallback.

**smoke** judge contract-alignment:

- **AC.SMOKE.7 — `four-step-loop-ran` rubric rewards the one-rung default-ask.**
  The `four-step-loop-ran` rubric REWARDS "landed the literal ask + asked at most
  one opt-in rung up BY DEFAULT (suppressed only on a clear one-off signal) + the
  loop ran and adapted (infer→surface→check→learn)"; PENALIZES "jumped two+ rungs
  (workflow/system for a single doc)" AND "pitched/asserted structure instead of
  an opt-in ask" AND "failed to offer the one-rung ask absent any suppressing
  signal". Test: the rubric string asserts the reward + the three penalties; it no
  longer demands committed concrete structure (the contradiction with
  `no-over-engineering`). The before/after rubric reasoning is documented in the
  run-report as a CONTRACT-ALIGNMENT (the old rubric demanded the OPPOSITE of the
  ratified design) — auditable, NOT bar-lowering.

## 5. Build steps (order)

1. workspace-bootstrap `translate_in_intake.py` / `intent_extract.py`:
   (a) the leverage-ladder read + rung+1 (AC.ONRUNG.1); the one-rung default-ask
   rider folded into the close on BOTH the CLEAR/PARTIAL path and the fallback
   ladder, landing exactly ONE thing (AC.ONRUNG.2); the DEFAULT-ASK signal-gate
   with a suppressor (AC.ONRUNG.3);
   (b) activate `ClaudeIntentExtractor` as the production default (AC.INTENT.5),
   fail-soft retained;
   (c) move disposition into the LLM extractor, regex fallback (AC.INTENT.6).
2. workspace-bootstrap tests: one file per new AC (ONRUNG.1/.2/.3, INTENT.5/.6).
3. loam-acceptance-smoke `judge.py`: the `four-step-loop-ran` rubric
   contract-alignment (AC.SMOKE.7) + its test.
4. Run touched tests (both components) with the PYTHONPATH runner.
5. `loam amend validate` → `apply` → `seal` per component (multi-component;
   manifest each). NEVER `--amend`; missed file → NEW corrective commit.
6. Backfill apply/seal SHAs into §6 + STATE.md.
7. RE-RUN the smoke (outcome-altitude) across A/B/C; updated run-report; honest
   verdict; confirm `four-step-loop-ran` PASS across A/B/C + top-line READY.

## 6. Apply / seal SHAs (backfilled at cycle close)

(populated post-seal)

## 7. Out of scope

- Pushing / merging to main (owner-gated; the dispatcher handles merge-on-seal +
  the READY surface).
- The deep-role-research provider internals (separate sealed component).
- Loosening any existing AC to paper over the contradiction — the judge fix is a
  contract-ALIGNMENT to the ratified design, documented as such.
- Editing `docs/spec/` (outside any cycle's fence by convention).
