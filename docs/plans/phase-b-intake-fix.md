# Phase-B intake fix — the ODD-shaped plan

**Date:** 2026-05-16 · **Status (corrected 2026-05-18 pre-publish, Tier-0):** SEALED — seal `ceb629b` (authoritative register; BASELINE `07f4d35`, plan+manifest `c1fbb03`, source-edit `a8ba467`, apply `e553e80`; STATE.md change-log 2026-05-16). The three named `intake.py` corrections + re-harden were built + LOCAL-sealed against the `workspace-bootstrap` fence and ship in this release push (`ceb629b` is an ancestor of the pushed `main` tip). The re-harden returned a definite evidence-backed honest-negative (2/7 faithful) — a valid §10.5 plan-success outcome, reported straight. _Prior state (superseded, retained for audit trail): "**Class:** ODD-shaped fix plan, plan-only (no code in this artefact)." Authored 2026-05-16 before the build; went stale at seal — corrected here pre-publish so the public artefact does not ship a false plan-only status._
**Contract input (the evidence base):** `pos3/.../phase-b-hardening-2026-05-16.md` — the honest-negative reliability test that returned **3/7 faithful** + one non-deterministic process crash.
**Built loop under repair:** canonical `/Users/lukeivers/loam`, `framework/tools/handsoff-loop/src/handsoff_loop/intake.py` (sealed `b33c0a8` on branch `amend/loam-init-persona-wiring`; build report `handsoff-loop-build-report-2026-05-16.md`).
**Owner-ratified sequence (Telegram 11403):** harden Phase B → fix → re-harden → THEN revive ProgramBench. This plan is the *fix* step.
**Prime objective it ladders to:** `framework/docs/VALUE_PROPOSITION.md` (the two tests).

---

## TL;DR (plain English, no jargon — lead)

1. **All three fixes are contained corrections, NOT a re-architecture.**
   Fix 2 (the load-bearing one) is the one the dispatch flagged as the
   risk: I read the actual source and the independent honesty-judge it
   would supposedly need is **already built, already independent,
   already isolated, already either-polarity** — the defect is purely
   that the already-derived machine check command is sitting in a local
   variable three lines above the judge and is *never handed to it*. The
   fix wires data that already exists into a judge that already exists.
   That is a contained correction, not a verification re-architecture.
2. **The honest-negative is still a valid outcome.** If the three
   contained fixes do not reach the ≥6/7 re-test bar, "still not
   reliable, here is the residual pattern" is a valid result that
   re-gates ProgramBench differently — it is NOT a signal to retry to
   green or to widen the fix into a re-architecture mid-build.
3. One fix touches behaviour the user could feel (fix 1 turns 2-in-7
   silent fake-approvals into honest "I couldn't pin this down" — a
   visible refusal where there used to be a false yes). That is the
   intended outcome, surfaced for owner awareness, not a decision.

---

## §1 — Objective

Make the built hands-off loop's *intake leg* stop manufacturing
fake-faithful "done"s, by closing the three named Phase-B
prerequisites in priority order, so that a re-run of the exact
phase-b-hardening 7-intent reliability protocol reaches **≥6 of 7
faithful** — *or* returns a definite honest-negative that names the
residual failure pattern (a valid §10.5-class outcome that re-gates
ProgramBench, not a build failure).

The three prerequisites (the hardening report's own priority order,
§"Three concrete intake fixes", lines 207–221):

1. **Refuse empty/broken done before approval.** The intake must not
   report a "done" as `approved=True` when it derived no usable / empty
   / unparsed / broken machine-checkable acceptance. (I2, I7: 2-of-7
   silent no-done-but-approved.)
2. **The faithfulness check must verify the underlying test, not the
   summary.** When the real goal is hard to verify the intake
   substitutes a cheap stand-in check that passes while the real goal
   is unmet, and the loop's own faithfulness judge rubber-stamps it
   *because that judge is shown only the friendly plain-English
   summary, never the machine check command underneath*. The fix: the
   faithfulness judge must assess the actual derived check command
   against the intent, not the prose. (I3, I6: 2-of-7
   checkable-but-wrong, both rubber-stamped by the loop's own judge.)
3. **Fix the crash.** A naive-substring jargon guard trips on the
   ordinary token "Mac." Make it deterministic and not crash on
   ordinary words. (I3 run 1: non-deterministic process crash.)

Fix 2 IS the information-trust-ordering frame applied to the loop's
own architecture: the loop currently trusts its own low-trust
self-report (the friendly plain summary) over the ground-truth
artefact (the actual machine check command). The fix inverts that
ordering — judge the ground truth, not the self-narrated summary.

This objective ladders to **both** VALUE_PROPOSITION tests: a loop
that freezes a wrong/empty "done" fails the primary-persona test
(the user's intent was NOT faithfully translated) and the harness
test (the toolkit item silently produces a poisoned contract).

## §2 — Fence (what this fix will and will not touch)

**In scope (the only surfaces this fix may mutate):**

- `framework/tools/handsoff-loop/src/handsoff_loop/intake.py` — the
  three named sites only:
  - the empty/broken-done gate, between derive and the approval call
    (currently `intake.py:213–235`);
  - the faithfulness-judge input + framing (currently
    `intake.py:238–262`);
  - the jargon-guard match logic (currently `intake.py:94–102`).
- The intake test surface that proves the three fixes
  (`framework/hands-off-lifecycle/tests/` — the existing
  `test_AC_HL_B1_B4_intake_structure.py` family, extended; new
  regression tests for the three sites). Both `framework/tools/` and
  `framework/hands-off-lifecycle/` are seal-admitted prefixes on this
  exact branch tip (verified against
  `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`
  `allowed_prefixes`).
- IF AND ONLY IF the SKILL bundle's prose describes the now-changed
  refuse/judge behaviour inaccurately after the fix: a one-line
  behavioural-doc correction in
  `plugins/loam-skills/skills/handsoff-loop/SKILL.md` (also
  seal-admitted). No logic lives there — it delegates to
  `derive_acceptance_from_intent` (verified, SKILL.md:53–54). This is a
  doc-truth touch, not a code site; named so a builder neither expands
  nor forgets it.

**Out of scope (explicit, so effort is not wasted):**

- **The core decompose→dispatch→judge loop.** Proven at unit scale
  (probe §6 / AC.FOUND.0). Re-running or re-proving it inside this fix
  is a scope violation. `verify.py` / `orchestrator.py` /
  `goal_drive.py` are NOT touched.
- **The §1a / §1c launch sites** (the other handsoff launch points
  named in the telegram-poller-isolation work). Out of this fence.
- **The Telegram-poller isolation** (sealed `b33c0a8`). Untouched. It
  HELD this run — the operator poller + session survived 28 isolated
  `claude -p` background spawns (hardening report §"Telegram-survival
  observation"). Recorded here as a **non-fence corroboration** of the
  prior seal; this plan does not test, re-test, or modify it.
- **The elicitation leg (AC.B.2).** It is the *durable* part — across
  all 7 intents it stayed at 3–4 bounded plain questions, recovered
  even the adversarially-thin I5 (hardening §"What worked"). Not a
  failure site; not touched.
- **ProgramBench itself.** Revival is downstream, gated on a green (or
  honest-negative-and-re-decided) re-harden. Not in this fence.
- Any token / access / channel / config change. Any `claude` argv,
  model, or isolation change. Publish, seal-policy, or
  canonical-`main` mutation. Plan-only artefact; the build it
  describes is a separate authorised effort.

## §3 — Containment finding (F2 — the load-bearing question, answered from source)

The dispatch's halt-trigger #1: *if fix 2 is not a contained
correction but requires re-architecting the loop's verification,
say so plainly and do not paper over it.* I read the actual source
(not the hardening report's prose alone — that is medium-trust). The
answer, grounded in `intake.py` line-by-line:

**Fix 2 is a contained correction. It does NOT require
re-architecture. Evidence (file:line):**

- The independent faithfulness judge **already exists**: `intake.py:239–262`
  runs a real `claude -p` subprocess (`_claude_json`, `intake.py:105–138`)
  that is a *separate process*, isolated (`inject_isolation` /
  `isolated_env`), default Sonnet, NO API key — exactly the independent
  judge fix 2 needs. It does not need to be built.
- It is **already either-polarity / no-retry-to-green**: an
  unparseable judge verdict yields `faithful=False` with the reason
  recorded (`intake.py:260–262`); there is no retry path.
- The machine check command the judge must assess **already exists in
  scope at the exact point the judge is constructed**: `mc` (with
  `mc["check_command"]` and `mc["spec"]`) is computed at
  `intake.py:213–222`, 18 lines *above* the faithfulness prompt at
  `intake.py:240`. It is a live local variable when the judge prompt
  is built.
- The **only defect** is the prompt body at `intake.py:240–252`: it
  interpolates `intent` + `plain_acceptance` and **never references
  `mc`**. The judge is structurally blind to the machine form not
  because the architecture forbids it but because two already-present
  pieces of data were never connected.

So the fix is: feed the already-derived `mc["check_command"]` (and
`mc["spec"]`) into the already-existing, already-independent,
already-isolated judge, with adversarial framing that asks the judge
to find the proxy/plumbing gap ("could this command exit 0 while the
user's actual outcome is unmet?"). **No new judge process, no new
isolation machinery, no change to the loop's verification spine, no
change to `verify.py`.** A contained correction to *what data an
existing judge sees and what it is asked* — which is precisely the
information-trust-ordering inversion the objective names.

Honest residual nuance (F2, surfaced not papered): there is a *design
seam* between intake's `machine_checkable` dict and the orchestrator's
`FrozenAcceptance.check_argv` (`verify.py:42–57`) — intake produces a
`check_command` *string*, the loop later consumes a `check_argv`
*list*; nothing in the read path forces intake's command to be the
one that is later frozen and run. This seam is **real but out of this
fence** — it is a loop-composition concern, not the Phase-B intake
faithfulness defect, and fix 2 does not depend on closing it (the
judge assesses the command intake derived; whether that exact command
is later frozen is a separate, downstream, ProgramBench-adjacent
question). Named here so it is not silently inherited as solved; it
is a candidate follow-on, explicitly not part of this plan's three
fixes. (Composes-with note: this is the §3 honest-negative-class
surfacing required by Lens 7 — disagreement named, evidence
file:line'd, alternative = separate follow-on, not scope creep here.)

## §4 — Acceptance ladder (outcome-shape, satisfiability-tested)

Every AC states an *observable outcome*, not a method. Each carries
its satisfiability-test note (**"can this AC be satisfied by a method
other than the one I have in mind?"** — yes ⇒ tight scope; no ⇒
method-in-AC, a Lens-3 violation). The honest-negative is a
**first-class valid outcome** for the lead phase AC by construction.

### AC.PBF.1 — Refuse empty/broken done before approval

The intake does NOT report `approved=True` when the derived plain
"done" is empty/whitespace-only, OR the machine check command is
empty, OR the machine-checkable JSON failed to parse. In any of those
states the outcome is a definite, evidence-carrying refusal (a
non-approved outcome with a recorded reason), surfaced *before* the
approval gate can return true — never a silent `approved=True` on
empty/garbage.

- *Ladders to:* both tests (a fake `approved=True` on no contract
  fails the harness test — the toolkit emitted a poisoned unit — and
  the primary-persona test — the user's intent was not translated at
  all).
- *Satisfiability:* satisfiable by a pre-gate validity guard, by a
  derive-retry-then-refuse, by a structured-output contract that
  cannot produce empty, by short-circuiting `approval_fn` — multiple
  methods; scope is tight, method is the builder's call.
- *Source it closes:* I2/I7 — `intake.py:213–222` empty-parse path +
  `intake.py:235` `approved = bool(approval_fn(plain_acceptance))`
  returning True on `""`.

### AC.PBF.2 — Faithfulness judge assesses the machine check, not the summary

The independent faithfulness check's verdict is derived from an
assessment that **includes the actual derived machine-checkable check
command** (and its spec), evaluated adversarially for the
proxy/plumbing failure mode ("could this check pass while the user's
real outcome is unmet?"). A faithfulness verdict that was produced
without the machine form in evidence does not satisfy this AC.

- *Ladders to:* both tests (this is translation-fidelity — the
  primary-persona test — enforced by an honest harness self-check —
  the harness test).
- *Satisfiability:* satisfiable by passing the check command into the
  existing judge prompt, by a second judge keyed on the command, by a
  round-trip "what would make this command exit 0" enumeration —
  multiple methods; the AC constrains *what the judge must have in
  evidence*, not how the judge is structured. Tight, not method-bound.
- *Honest-negative built in:* the judge returning `faithful=False`
  (correctly catching a proxy check) is an AC-satisfying outcome
  exactly as a `faithful=True` is — the AC is "the judge assessed the
  real test," not "the judge said yes."
- *Source it closes:* I3/I6 — `intake.py:240–252` faithfulness prompt
  interpolates only `intent` + `plain_acceptance`, never `mc`; the
  loop's-own-judge diverged from the independent judge on exactly
  these 2, both in the dangerous direction (hardening
  §"Loop's-own-judge divergence").

### AC.PBF.3 — Jargon guard is deterministic and does not trip on ordinary words

The plain-language jargon guard matches an acceptance-ID-class token,
not the bare substring inside ordinary English words. Specifically:
ordinary words that merely *contain* a forbidden substring (the
canonical case: "Mac." containing "ac.") do NOT raise; genuine jargon
tokens (a real `AC.<id>` reference, `pytest`, `exit code`, etc.) still
do. The guard's behaviour is deterministic — the same plain "done"
either always raises or never raises, independent of incidental
phrasing.

- *Ladders to:* the harness test (a toolkit item that
  non-deterministically hard-crashes the whole intake on benign plain
  English is not a usable toolkit item).
- *Satisfiability:* satisfiable by word-boundary regex, by tokenize +
  exact-token match, by a curated phrase list with boundaries, by
  scoped anchored patterns — multiple methods; the AC constrains the
  *observable* (benign words pass, real jargon fails,
  deterministically), not the matching technique. Tight.
- *Source it closes:* `intake.py:94–102` `assert_plain_language` —
  `[j for j in _JARGON_FORBIDDEN if j.lower() in low]` naive
  substring; **verified deterministically from source** by the planner:
  `assert_plain_language("Back up to your Mac.")` and
  `"Sign into iCloud on your Mac."` both RAISE `['AC.']`;
  `"save it to your Mac and done"` does NOT raise — confirming the
  trip is the substring `"ac."` (from the `"AC."` entry, lowercased)
  immediately followed by sentence-end, exactly as the hardening
  report claimed (hardening §"The process crash").

### AC.PBF.4 — No regression in the durable parts

The fix does not regress the parts the hardening test proved durable:
elicitation stays bounded (≤4 plain questions, AC.B.2), the single
plain-language approval gate stays exactly one (AC.B.3), genuine
jargon is still refused (the AC.B.3 guard still fires on real AC-IDs /
`pytest` / `exit code`), and the existing
`test_AC_HL_B1_B4_intake_structure.py` deterministic suite still
passes (adjusted only where a fix legitimately tightens behaviour —
e.g. an empty-input test now expecting refusal instead of approval —
with each adjustment recorded as a fix-driven tightening, not a
loosening to make a broken test pass).

- *Ladders to:* both tests (the durable translation behaviour the
  hardening report credited must survive the repair).
- *Satisfiability:* satisfiable by any fix that preserves the four
  observable invariants; not method-bound.

### AC.PBF.5 — The phase re-harden end-test (lead acceptance, §10.5 honest-negative valid)

A re-run of the **exact phase-b-hardening 7-intent reliability
protocol** — the same 7 intents (or an equivalently-varied set: 7
genuinely-vague non-technical intents across ≥7 domains, ≥5 distinct
kinds of under-specification, including one adversarially-thin
one-liner, none reusing the build's "spending" intent), **one run per
intent, no retry-to-pass**, scored by an **independent faithfulness
judge that is NOT the loop's own AC.B.4b judge** (a separate,
stricter, differently-framed held-out probe plus an evidence-grounded
read of each raw derived check command — the same Tier-0 independent
methodology the hardening test used) — produces a definite,
evidence-backed per-intent verdict table and reaches **≥6 of 7
faithful**.

**A definite "still not durably reliable — here is the residual
failure pattern and the evidence" is a valid, plan-success outcome
(§10.5-class), reported straight, NOT retried to green.** If the three
contained fixes do not reach ≥6/7, the correct response is the honest
residual-pattern report (which re-gates ProgramBench differently — see
§6), NOT widening the fix into a re-architecture mid-build, NOT
re-running intents until 6 pass, NOT weakening the bar.

- *Ladders to:* both tests jointly — this is the prime-objective-level
  check that the intake translation is now durably faithful.
- *Satisfiability:* the AC is "a definite, evidence-backed verdict on
  the 7-intent protocol at the ≥6/7 bar exists" — satisfiable by
  *either* polarity (≥6/7 reached, or a definite honest-negative with
  the residual pattern named) and by any independent
  dimension-grounded judging method that is not the loop's own judge.
  Not green-only, not method-bound.
- *Why ≥6/7 and not 7/7:* the hardening report itself documented that
  some gaps are mechanically unverifiable *for anyone* (I5
  "discussion-worthiness" — hardening per-intent table) and some
  FAITHFUL results carried cosmetic-only nits (I1 "steps", I4 "one
  sentence"). A 7/7 bar would force the re-test to grade
  unverifiable-for-anyone properties as failures, making the bar
  unfair for a structural reason (dispatch halt-trigger #2). ≥6/7 is
  the honest reliability floor that tolerates the one
  mechanically-unverifiable-for-anyone case without rewarding a real
  proxy/plumbing failure. **This is the §3-honest-negative-class
  surface for halt-trigger #2: the bar is set so it is a fair honest
  test; it is not weakened to be passable.**

### Ladder shape note (ODD self-check, inline)

PBF.1/.2/.3 are each strictly tighter than §1's objective (each pins
one named failure site to one observable). PBF.4 is the
non-regression floor. PBF.5 is the lead/phase-end acceptance, strictly
the union outcome §1 names, with the honest-negative as a first-class
satisfying polarity. No AC is of the form "X passes" where only green
satisfies it. None states method (each names ≥2 satisfying methods).
Decomposition stops here: a further split of any PBF.x adds only
coordination overhead without tightening the acceptance (Lens 5
stopping criterion).

## §5 — Named decisions (owner calls, recommendation-led)

**No genuine product decision surfaced that blocks the build.** The
three fixes and the ≥6/7 re-test bar are owner-ratified-in-spirit
(Telegram 11403 ratified the harden→fix→re-harden→ProgramBench
sequence and the hardening report's own three-fix priority order). The
two items below are surfaced for completeness and owner awareness,
recommendation-led — neither blocks build start.

### D-PBF-A — Fix 1's user-visible behaviour change (awareness, not a block)

Fix 1 converts the 2-in-7 silent `approved=True`-on-empty into an
honest refusal. **Recommendation:** ship it as a refusal (a clear "I
couldn't pin down a checkable 'done' for this — here's what was
missing" outcome) rather than an auto-retry, because a silent retry
re-introduces the rubber-stamp risk by another path and the user
seeing an honest "I couldn't do this cleanly" is the
primary-persona-test-correct behaviour. Owner can override toward
bounded-retry-then-refuse; default is refuse-with-reason. Not
plan-blocking — the build proceeds on the default.

### D-PBF-B — Re-harden intent set: same 7 vs equivalently-varied 7 (parameter, not a block)

**Recommendation:** re-run the **same 7 intents** from the hardening
report, because same-input re-test is the cleanest before/after
evidence (3/7 → ≥6/7 on identical inputs is unambiguous), and the
hardening report documents all 7 verbatim. The "equivalently-varied
set" clause in AC.PBF.5 exists only as a guard against the
theoretical objection that the model could have memorised the 7 —
which is implausible across a fix-build but named for completeness.
Owner can require a fresh varied set; default is same-7. Parameter,
not a blocker.

No other genuine owner calls surfaced.

## §6 — What this fix does NOT claim (F2, explicit)

1. **It does not claim the three fixes will reach ≥6/7.** AC.PBF.5 is
   constructed so a definite honest-negative is a valid outcome. The
   plan claims the fixes are *contained and the re-harden is a fair
   honest test* — it does **not** predict the verdict. Predicting "this
   will hit 6/7" would be the build-and-assume failure the discipline
   forbids.
2. **It does not claim intent→faithful-done is now a solved problem.**
   It claims three specific, source-located defects are contained and
   closeable. If the residual pattern after the fix is a *different*
   failure mode than the three named, that is a new finding for a new
   authorised effort — not silently absorbed into this fix.
3. **It does not claim the intake→loop check-command seam is closed**
   (§3 honest residual). That seam is real, named, out of fence, a
   candidate follow-on. This plan's fix 2 does not depend on it.
4. **It does not re-open or re-prove the core loop, the elicitation
   leg, or the Telegram-poller isolation.** The first two are
   established/durable; the third held under load this run and is
   recorded as corroboration only.
5. **It does not claim a green re-harden auto-revives ProgramBench.**
   If AC.PBF.5 retires positive (≥6/7), ProgramBench revival becomes
   the next authorised step on the ratified sequence. If it retires
   honest-negative, ProgramBench is **re-gated differently** — the
   residual pattern report informs whether ProgramBench can run on a
   bounded subset, or needs a further intake effort first. Either way
   the §10.5 outcome re-gates ProgramBench; it does not fake a pass to
   unblock it.

## §7 — Lens self-check (ODD §9-style, inline)

- **Lens 1 (Claude-leverage):** fix 2 composes the *already-present*
  `claude -p` independent-judge primitive — it adds no new judge
  machinery; it feeds existing ground-truth data into the existing
  Claude-subprocess judge. No re-implementation. Satisfied.
- **Lens 2 (harness + primary-persona):** all three fixes reduce the
  translation burden's failure mode (the user no longer gets a
  silently-wrong or empty "done" presented as approved) and harden a
  toolkit item the persona invokes as one capability. Both tests
  served.
- **Lens 3 (ODD authoring):** every AC outcome-shape with a
  satisfiability note; no method-in-AC; honest-negative is a
  constructed valid polarity, not an exception.
- **Lens 4 (scope ↔ confidence):** confidence that the three fix
  *outcomes* are right is high (source-verified), so the ACs are
  tightly scoped to the three sites; *method* is deliberately left to
  the builder (no fix technique prescribed). The one lower-confidence
  area (will ≥6/7 be reached) is left loose by construction — the
  honest-negative polarity.
- **Lens 5 (swarming):** decomposed into PBF.1/.2/.3 (independent,
  each a tighter acceptance on one site) + PBF.4 (regression floor) +
  PBF.5 (aggregate phase end-test). Stopping criterion hit — further
  split adds only coordination overhead. PBF.1/.2/.3 are
  parallelisable; PBF.5 depends on all three landing.
- **Lens 6 (conflict resolution):** the one latent conflict —
  scope-discipline (don't touch the intake→loop seam) vs ruthless
  feedback (the seam is a real defect) — resolved by the four-step
  process: named (§3), signals (blast radius: seam is downstream of
  this fence; reversibility: naming it is free, fixing it mid-build is
  not; information asymmetry: owner should know it exists), call
  (surface as named follow-on, do not extend scope), surfaced (§3 +
  §6.3). Not silently resolved.
- **Lens 7 (ruthless feedback):** the containment question answered
  from source not report-prose (§3); the seam disagreement named with
  file:line evidence and an alternative (follow-on, not scope creep);
  the ≥6/7-vs-7/7 bar fairness reasoned, not asserted (AC.PBF.5).
- **ODD scope:** every AC maps to §1's objective; no non-objective
  code is licensed (the fix touches three named sites + their tests +
  one conditional doc-truth line — nothing else). Plan-only honored;
  no code in this artefact.

## §8 — §10.5-class findings (F2 — surfaced, not papered)

- **Containment (the load-bearing one): RESOLVED POSITIVE from
  source.** Fix 2 is a contained correction (§3, file:line evidence).
  The dispatch's halt-trigger #1 did not fire — but I am stating the
  *basis* explicitly so it is auditable rather than asserted: the
  judge, its independence, its isolation, its either-polarity, and the
  data it needs all already exist in `intake.py`; only the wiring is
  missing. Had I found the judge needed to be rebuilt or the
  verification spine re-architected, this section would say so plainly
  and the plan would be shaped as a re-architecture, not three
  contained fixes. It does not, because the source does not support
  that.
- **The intake→loop check-command seam (named, out of fence).**
  `intake.py` emits a `check_command` string;
  `verify.py`/`orchestrator.py` consume a frozen `check_argv` list;
  nothing in the read path forces the judged command to be the frozen
  one. Real, but a loop-composition concern downstream of Phase-B
  intake faithfulness — a candidate follow-on, explicitly not one of
  the three fixes, explicitly not a fix-2 dependency.
- **Bar fairness (halt-trigger #2): the ≥6/7 bar is a fair honest
  test.** It is not weakened to be passable — it is set at the honest
  reliability floor that tolerates exactly the
  mechanically-unverifiable-for-anyone case the hardening report
  itself documented (I5 discussion-worthiness), and no more. 7/7 would
  be unfair *against* the fix for a structural reason (grading
  unverifiable-for-anyone properties as failures); ≥6/7 is the bar
  that makes the re-test honest in both directions.

No internal inconsistency found between the hardening report's
mechanism claims and the actual source — every report claim
(empty-approved, judge-blind-to-machine-form, Mac.-substring-crash)
was cross-checked against `intake.py` and confirmed at the cited
lines, with the crash reproduced deterministically by the planner.

---

*Plan authored 2026-05-16. Plan-only — no code in this artefact.
Builds on the sealed handsoff-loop intake + the phase-b-hardening
honest-negative; does not re-prove the core loop, the elicitation
leg, or the Telegram-poller isolation. Ready to build: three
contained fixes + a fair honest re-harden, honest-negative valid.*
