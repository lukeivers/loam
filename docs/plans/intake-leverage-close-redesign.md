# Intake leverage-close redesign + smoke variant-B day-derived hardening

Working directory: `/Users/lukeivers/loam-wt-close` (isolated worktree, branch
`plan/intake-leverage-close-redesign`, off `main` at `519147db` — the merged
intake NL-handling fixes, amendments #164+#165).

## 1. Source of the work

The loam 1.0 acceptance smoke's first fix-round (amendments #164+#165) fixed the
four natural-language bugs, but the SECOND re-run
(`docs/experiments/loam-1.0-acceptance-smoke-rerun2.md`, top-line **NOT-READY**)
surfaced a DEEPER layer: the leverage-CLOSE itself fails four prime-objective
judge dimensions across all three variants —

  - `four-step-loop-ran` — the close never cleanly surfaces the inferred intent
    as a checkable hypothesis before closing (legs 3-4 absent on the
    day-derived + idea-vacuum paths; on the CLEAR/PARTIAL path the close ignores
    a correction).
  - `closed-on-one-thing` — the close presents a 2-3 item menu, not ONE landed
    stop/start.
  - `no-over-engineering` — the START-disposition close over-promises automation
    ("happens reliably without you having to push it forward each time") rather
    than proposing right-sized, opt-in.
  - `learned-this-person` — the close uses generic "status updates / formatting
    / chasing" instead of the person's NAMED items.

These are NOT open design forks. The TARGET behavior is the owner's
already-specified onboarding design (the prime-objective four-step loop:
infer → propose → SURFACE-AND-CHECK → adjust; close on ONE thing; no
interrogation; don't over-engineer). This cycle implements the close to that
spec, adds an AC + test per close behavior, then RE-RUNS the smoke to verify the
prime-objective verdict moved.

A SEPARATE, smaller change (its own fence) tightens the smoke's variant-B
persona script so it reliably exercises the day-derived path (it sampled a
pure-vacuum opener last run and routed — correctly given that input — to
research, tripping the featherlight gate; harness non-determinism, not a loam
bug).

## 2. Fences (two components — declared multi-component)

1. **workspace-bootstrap** — the close redesign. Entirely within
   `framework/workspace-bootstrap/src/loam/workspace_bootstrap/translate_in_intake.py`
   + its tests. Seal-test:
   `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`.
2. **loam-acceptance-smoke** — variant-B persona-script hardening. Entirely
   within `framework/tools/loam-acceptance-smoke/src/loam_acceptance_smoke/variants.py`
   (the machine-consumed `persona_brief`) + its human mirror
   `scripts/variant_b_claims_adjuster.md` + a test asserting the script reliably
   yields a day-with-nameable-pain opener. Seal-test:
   `framework/tools/loam-acceptance-smoke/tests/test_no_sealed_amendments.py`.

The re-run only EXECUTES the smoke harness — the updated run-report lands at
`docs/experiments/` (universal-admitted).

## 3. Halt-and-surface BEFORE build

- A genuine design fork in the close (reasonable people differ) → surface,
  don't guess.
- A close-fix needing a component beyond these two → surface.
- Any `claude -p` in the re-run that can't be spawn-isolated → HALT.
- The re-run revealing a regression or non-converging pattern → surface
  honestly.

## 4. The five close behaviors + evidence (from rerun2)

1. **Surface-and-check before closing.** The inferred intent must appear as a
   checkable hypothesis ("It sounds like you want X — is that right?") on EVERY
   path. Today only the CLEAR/PARTIAL path surfaces it (`confirm_proposal`); the
   day-derived ladder + idea-vacuum ladder jump from describe_work/research
   straight to a close. (AC: four-step-loop-ran.)
2. **Land on ONE thing.** The close picks the single highest-leverage stop/start
   and lands it; it does NOT present a list. Today `first_run_intake_cli` /
   `transcript_blob` render EVERY `leverage_ideas` entry as a co-equal `>> `
   close line → the menu. (AC: closed-on-one-thing.)
3. **Opt-in-only automation framing.** No "happens reliably without you having
   to push it forward each time." The recurring/elaborate version stays an
   opt-in suggestion (the existing `one_level_up_offer`), not the default the
   close commits to. (AC: no-over-engineering.)
4. **Person-specific.** The close uses the person's NAMED items (their tasks /
   words), not generic "status updates / formatting / chasing". (AC:
   learned-this-person.)
5. **Negated-correction distillation.** Variant A's "it's not that I have
   trouble starting it" distilled the NEGATED clause. A negated correction must
   distill the ASSERTED intent ("I want you to write them for me"), not the
   negated one. (AC: AC.INTAKE-ECHO.1 hardening — same family, refinement.)

## 5. Acceptance criteria (each close behavior → a NAMED AC + a test)

New close-design AC family **AC.ONCLOSE.\*** (the demonstrate-leverage close's
prime-objective quality; ladders up from AC.ONINTAKE.6, which only required
≥1 person-specific idea — these tighten WHAT a good close is):

- **AC.ONCLOSE.1 — surface-and-check on every path.** Before the leverage
  close, the inferred end-intent is surfaced as a checkable hypothesis the user
  can confirm/correct, on the CLEAR/PARTIAL path AND on the day-derived ladder
  AND on the idea-vacuum-after-research path. Test: each path's transcript
  contains a confirm/check turn naming the inferred intent before the close.
- **AC.ONCLOSE.2 — exactly ONE landed close idea.** A completed intake produces
  exactly ONE primary leverage idea (the landed stop/start) in
  `leverage_ideas` — research findings and supporting context are folded INTO
  that one idea or carried on the result for the seed, NOT emitted as additional
  co-equal close ideas. Test: `len(result.leverage_ideas) == 1` for every path
  (idea-rich / day-derived / idea-vacuum-with-research).
- **AC.ONCLOSE.3 — no over-promised automation.** The close text does NOT claim
  unattended/recurring automation ("happens reliably without you having to push
  it forward"); recurring stays the opt-in `one_level_up_offer`. Test: the close
  text contains no over-promise phrase; the opt-in offer is present and marked
  optional.
- **AC.ONCLOSE.4 — person-specific named item.** The close references the
  user's NAMED item/role (the distilled stop/start item, or the day-derived
  named pain), not generic-assistant boilerplate ("status updates / formatting /
  the chasing" as the headline offer). Test: the close references the named item
  and does NOT lead with the generic triad.
- **AC.ONCLOSE.5 — negated correction distills the asserted intent.** A
  correction phrased as a negation ("it's not that I have trouble starting it —
  I want you to write them for me") distills the ASSERTED span, not the negated
  one; the close + seed reference the asserted intent. Test: variant-A's real
  negated correction in → the close references the writing/draft-for-me intent,
  not "trouble starting".

Plus the **smoke** AC:

- **AC.SMOKE.6 — variant B reliably day-derived.** Variant B's persona brief
  reliably yields a FIRST stop/start answer that describes the day AND names a
  concrete pain (so it routes to the day-derived PARTIAL path, not the
  pure-vacuum path). Test: the brief instructs a day-with-named-pain opener; a
  classifier check on a representative B opener returns non-EMPTY. (Does NOT
  loosen AC.SMOKE.3.)

## 6. Build steps (order)

1. workspace-bootstrap close redesign in `translate_in_intake.py`:
   (a) rewrite `_leverage_from_intent` to a single person-specific, non-over-
   promising close referencing the named item (AC.ONCLOSE.3/.4);
   (b) add a surface-and-check confirm step to the day-derived ladder +
   the idea-vacuum-after-research path (AC.ONCLOSE.1), and collapse the close to
   ONE landed idea, folding research/role findings into the result for the seed
   rather than as extra close ideas (AC.ONCLOSE.2);
   (c) fix negated-correction distillation so the asserted intent is distilled
   (AC.ONCLOSE.5).
2. workspace-bootstrap tests: one test file per AC (AC.ONCLOSE.1-5).
3. loam-acceptance-smoke: tighten variant-B `persona_brief` + the
   `scripts/variant_b_claims_adjuster.md` mirror so the opener reliably names a
   day-pain; add the AC.SMOKE.6 test.
4. Run touched tests locally (both components).
5. `loam amend validate` → `loam amend apply` → `loam amend seal` for each
   component (declared multi-component; manifest each correctly).
6. Backfill apply/seal SHAs into this plan-doc §8 + STATE.md.
7. RE-RUN the smoke (outcome-altitude); produce the updated run-report; honest
   verdict.

## 7. Out of scope

- The deep-role-research provider internals (separate sealed component).
- The seed-writer / orchestrator contract — the close still produces
  `leverage_ideas` + `seeded_objective_text`; only the SHAPE (one idea, surfaced
  hypothesis) changes.
- Loosening AC.SMOKE.3 to paper over variant-B non-determinism.

## 8. Apply / seal SHAs (backfilled at cycle close)

(populated post-seal)
