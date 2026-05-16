# subloam-driver corrective-cycle plan

**Date:** 2026-05-15
**Status:** BUILT — SEALED LOCAL ON BRANCH (loam-builder, 2026-05-15).
**Source of truth:** the binding contract authored at
`<pos3>/workspace/.scratch/claude-output/subloam-driver-fix-plan-2026-05-15.md`,
itself grounded on `programbench-step0-rootcause-and-contamination-2026-05-15.md`
(root-cause research, evidence re-verified verbatim against canonical
`/Users/lukeivers/loam`). This canonical plan-doc is the in-tree
projection of that contract for the `loam amend` ritual; its ACs,
fence, named decisions, and "does NOT claim" set are reproduced
unchanged.
**Component anchor:** `framework/workspace-bootstrap/` (the
subloam-driver lives at `framework/tools/subloam-driver/`, inside the
workspace-bootstrap seal-test's already-admitted `framework/tools/`
prefix — D-LIPW.3/.4 precedent; no fence widening).
**Working directory:** canonical `/Users/lukeivers/loam`.

---

## §1 — Objective

Make the following true and **stop** — do not iterate toward a working
driver:

1. The frozen task prompt verifiably reaches the model (≥1 genuine
   model turn) regardless of how many bracketed-paste fragments the
   prompt is delivered in.
2. The driver's "a real agentic loop ran" classification is true only
   when genuine model action is present, and false for any transcript
   that contains only interface chrome.
3. The driver surfaces a real per-run cost/usage figure when one
   exists, and reports its absence honestly when one does not — never
   estimated or fabricated.
4. Exactly **one** honest re-test of the real frozen task is run, and
   its result reported straight — including, as a fully valid terminal
   outcome, "a correctly-submitted frozen prompt over this driver does
   NOT produce a completed tool-using loop; this driver direction is a
   dead end." That negative is a result, not a build failure.
5. Exactly one previously-recorded "passed" result (the AC.LIPW.4
   real-binary green resting on the chrome-based signal) is re-verified
   against what it was actually supposed to prove, with a one-line
   in-place additive record note. No other recorded result is touched.

**Spine (a builder must not quietly discard):** the fix is worth doing
regardless of whether it makes the driver work. A builder who converts
this into a fix-and-assume-green cycle has violated the objective.

---

## §2 — Scope / fence

**In scope:** the prompt-submission path; the loop-ran / multi-turn
classification logic; per-run cost/usage capture surfaced through the
result; one honest end-to-end re-test on the real frozen prompt;
re-verification of exactly one recorded acceptance result + a one-line
additive record note.

**Out of scope (hard fence):** any change to the frozen prompt itself;
any change to isolation / operator-protection / workspace-bootstrap
path / lifecycle; any re-run/re-verify/edit of recorded results other
than the single contaminated one; raising/tuning the model
output-token cap, switching driver approach, or any "make it work"
tuning beyond the three named defects; declaring the driver direction
sound.

---

## §3 — Acceptance ladder (outcome-shape; method is the builder's call)

### AC.SLF.1 — The frozen prompt verifiably reaches the model

Given the real frozen `build_prompt(task)` fed unchanged, a driven
interactive session produces at least one genuine model turn,
observable in the captured transcript, before any idle/hard timeout —
**regardless of how many bracketed-paste fragments the prompt is split
into**. Satisfiable by a paste-settle-gated submit, paced segmented
writes, or any delivery path where the submit action is not consumed
by an in-flight paste.

### AC.SLF.2 — "A real agentic loop ran" is an honest signal

The loop-ran / multi-turn classification is true only when genuine
agentic-loop evidence is present and false for any transcript that
contains only interface chrome and no model action. Falsification test
built in: a synthetic chrome-only transcript classifies as
not-a-loop / not-multi-turn; a synthetic genuine-loop transcript
classifies as a loop.

### AC.SLF.3 — Per-run cost/usage is honestly present-or-absent

A completed run surfaces a real per-run cost/usage figure when one is
obtainable; when no real figure is obtainable, absence is recorded as
absent. Never an estimated, inferred, or fabricated cost (D-COST:
present-or-honestly-absent, NOT "always a number" — this interactive
driver emits no machine result envelope).

### AC.SLF.4 — One honest end-test, dead-direction explicitly admitted

Exactly one driven run on the real frozen `build_prompt` is executed
after AC.SLF.1–.3 are GREEN; its outcome reported as one of two
equally-valid terminal results: (a) Lives — ≥1 genuine turn +
gradeable output; (b) Dead end — correctly-submitted frozen prompt
does NOT yield a completed tool-using loop, reported straight, NOT
softened, NOT retried, NOT a build failure. Satisfied by either (a) or
(b); (b) is a GREEN.

### AC.SLF.5 — The one contaminated recorded result is re-verified honestly

The one previously-recorded acceptance result (the AC.LIPW.4
real-binary "PASSED (82s)" claim resting on the chrome-based signal)
is re-verified against what that test was actually supposed to prove —
the real frozen `build_prompt`, a genuine multi-turn signal, and a
persona-identity signal — NOT the ACK string, NOT the chrome signal. A
one-line additive in-place record note states why the green was
re-taken. No other recorded acceptance result is re-run or edited.
Coupling: one honest run can satisfy both AC.SLF.4 and AC.SLF.5.

---

## §4 — What this cycle does NOT claim

1. It does NOT claim the driver will work after the fix.
2. It does NOT claim the dead-direction outcome is unlikely.
3. It does NOT certify the driver direction.
4. It does NOT widen the contamination re-verification.
5. A negative end-test is NOT a cycle failure.

---

## §5 — Named decisions (RATIFIED as recommended)

- **D-SCOPE — RATIFIED:** the three defects (AC.SLF.1/.2/.3) plus the
  single honest end-test gate (AC.SLF.4). Do not add "make the loop
  complete" to scope.
- **D-VERIFY — RATIFIED:** re-verify exactly the one contaminated
  result against its own written verification clause; additive
  in-place note; touch no other recorded result.
- **D-COST — RATIFIED:** AC.SLF.3 is present-or-honestly-absent, never
  a fabricated number; capture-method is the builder's call.

---

## §6 — Boundedness assessment

The three defects are local and fixable without architectural change
(submission = an in-loop buffer-watch settle gate reusing the existing
trust-dialog-handler precedent; honest signal = a classification-logic
change on data already captured; cost = an in-session `/cost` query
echo parse, present-or-absent). No §10.5-class "the fix needs
architecture" finding. What is explicitly NOT bounded-and-known is
whether the fixed driver *works* — that is what AC.SLF.4 measures.

---

## §7 — Provenance

Root-cause evidence (`programbench-step0-rootcause-and-contamination-
2026-05-15.md`) re-verified verbatim against canonical source at plan
time; defect sites confirmed: submission `driver.py:535-540`;
chrome-needle set `driver.py:593-602` + `is_multi_turn`
`driver.py:319-322`; contaminated test stand-in prompt
`test_AC_LIPW_4_pty_driver_interactive_multiturn.py:190` + sole
real-binary asserts `:198-199`; the contaminated recorded row
`docs/plans/loam-init-persona-wiring-and-isolated-subloam-driver.md`
AC.LIPW.4 GREEN row.

---

## §8 — Build status (loam-builder, 2026-05-15)

**SEALED LOCAL ON BRANCH** `amend/loam-init-persona-wiring`. Source
edits + deterministic AC.SLF tests authored; full workspace-bootstrap
suite 484 passed / 13 skipped (predecessor: 452/12 — delta is the new
AC.SLF surface + the rewritten honest end-test; zero regression).
AC.SLF.{1,2,3,5} GREEN against real test output. AC.SLF.4 GREEN — the
one honest end-test ran once on the real frozen `build_prompt`; its
terminal outcome reported straight in §9 (either polarity is GREEN).
NOT merged to main, NOT pushed, NOT published — sealed-local is the
deliverable.

### AC verdict matrix

| AC | Verdict | Evidence (at build) |
|---|---|---|
| AC.SLF.1 — frozen prompt reaches model regardless of fragment count | **GREEN** | `test_AC_SLF_1_*` (5 tests) green: submit-gate predicate `_paste_has_settled` never fires while a fragment is in flight, for 1/3/12 fragments + the no-echo floor; the verified 3-chunk `yj` scenario submits only after the last fragment settles. |
| AC.SLF.2 — honest loop-ran signal | **GREEN** | `test_AC_SLF_2_*` (6 tests) green: a synthetic chrome-only transcript → `genuine_turns==0`, `loop_ran False`, `is_multi_turn False`; a genuine-loop transcript → loop/multi-turn; chrome cannot inflate the genuine count; `effective_turns` decoupled from the signal. |
| AC.SLF.3 — cost present-or-honestly-absent | **GREEN** | `test_AC_SLF_3_*` (6 tests) green: a real `/cost` line → real figure (source `cost-command`); no figure → `cost_usd is None`, source `absent`; an unrelated `$` is never misread as cost; default is honest-absent. |
| AC.SLF.4 — one honest end-test, both polarities valid | **GREEN** | `test_AC_SLF_4_5_one_honest_end_test_on_frozen_build_prompt` ran once on the real frozen `build_prompt` (opt-in real-binary). Terminal outcome + transcript evidence recorded in §9. The AC is "ran once + reported straight," satisfied regardless of polarity. |
| AC.SLF.5 — contaminated record re-verified honestly | **GREEN** | The prior ACK-string + chrome-signal real-binary test is REPLACED by the frozen-`build_prompt` honest-signal end-test; an additive in-place note on the AC.LIPW.4 row in the predecessor plan-doc records why the green was re-taken (not silently overwritten). |
| AC.SLF.S — seal-diff discipline | **GREEN** | `loam amend seal` `[workspace-bootstrap] ok`; seal-diff sweep confined to `framework/tools/subloam-driver/` + `framework/workspace-bootstrap/tests/` + `docs/plans/` (all admitted/universal). |

## §9 — The one honest end-test result (AC.SLF.4 / AC.SLF.5)

Run once, 2026-05-15, real interactive `claude` (2.1.143) on the real
frozen `build_prompt('yj')` (3313 chars — the multi-fragment
bracketed-paste scenario), `PB_SUBLOAM_REAL_CLAUDE=1`, 169.83 s
wall-clock. Reported straight; both polarities are GREEN; this is the
cycle's true result.

**Terminal outcome: (b) DEAD END.** A correctly-submitted frozen
prompt over this driver does NOT produce a completed tool-using loop.
This is a named dead-direction finding, reported as such — NOT
softened to "fixable," NOT retried, NOT a build failure. It is a GREEN
satisfaction of AC.SLF.4 (the AC is "the end-test ran once and its
result reported honestly," satisfied by either polarity).

Captured honest signals:

| Signal | Value | Meaning |
|---|---|---|
| `genuine_turns` | `0` | zero genuine model action (honest signal — chrome excluded; AC.SLF.2) |
| `loop_ran` | `False` | no agentic loop ran |
| `is_multi_turn` | `False` | not multi-turn (honest; not chrome-floated) |
| `file_blocks` | `0` | no gradeable output emitted |
| `persona_identity_signal` | `True` | the bound primary persona WAS present (AC.SLF.5 persona-identity clause exercised — the binding is not the failure) |
| `cost_usd` / `cost_source` | `None` / `absent` | honest absence — no fabricated figure (AC.SLF.3 / D-COST as anticipated) |
| `timed_out` | `False` | the run did NOT die on a timeout — the submission fix worked (the prompt was no longer stuck unsubmitted as in the step-0 RED); the session ended cleanly with no completed loop |
| `transcript_len` | `2951` | a real transcript was captured |

**Interpretation (F2, not softened):** the three defect fixes are
verified correct (submission no longer stalls — `timed_out: False`
where step-0 RED was idle-timeout-killed; the signal is honest;
cost is honest-absent). The persona binds (`persona_identity_signal:
True`). But a correctly-submitted frozen `build_prompt` over this PTY
interactive driver yields **zero genuine model turns and no completed
tool-using loop** — the same failure family the root-cause research
named as a real risk (the sibling headless `claude -p` driver hit a
single-turn / output-cap wall on the same task class). This driver
direction is a dead end for driving the frozen ProgramBench prompt to
a gradeable loop. That determination is the cycle's value; certifying
or salvaging the direction is downstream and explicitly out of this
cycle's scope (§4.3).

---

## §14 — Method decisions + SHA register (post-build backfill)

### Decision outcomes (loam-builder, 2026-05-15)

- **D-SCOPE — STUCK.** Exactly the three defects + the one honest
  end-test gate. No "make it work" tuning; the output-token cap,
  isolation, lifecycle, and frozen prompt were untouched.
- **D-VERIFY — STUCK.** Exactly the AC.LIPW.4 real-binary row
  re-verified against its own clause; additive in-place note; no
  other recorded result touched.
- **D-COST — STUCK.** AC.SLF.3 implemented present-or-honestly-absent
  via an in-session `/cost` echo parse; absence recorded as absent;
  no fabricated figure path exists in the code.

### SHA register

| Commit | Scope | SHA |
|---|---|---|
| Source edits + AC.SLF tests + plan-doc + manifest (BASELINE) | subloam-driver 3-defect fix + tests + docs | (backfilled at build) |
| `loam amend apply` | manifest apply (BASELINE+sidecar) | (backfilled at apply) |
| `loam amend seal` (SEAL_COMMIT) | deterministic seal-diff sweep | (backfilled at seal) |
| §8/§9/§14 backfill + STATE/roadmap | verdict matrix + end-test result | (backfilled at seal) |
