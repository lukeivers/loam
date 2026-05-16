# Loop goal-refinement — the ODD-shaped plan

**Date:** 2026-05-16 · **Class:** ODD-shaped evolution plan, plan-only (no code in this artefact)
**Binding foundation (NOT re-litigated):** `pos3/.../owner-steer-goal-refinement-2026-05-16.md` — Luke, Telegram 11408. The owner's product ruling: a non-tech user must accomplish what they want with AI; an unmeasurable goal must be REFINED toward measurable (interactively with the user OR self-refined); and when the real goal isn't directly measurable at all, pick a measurable goal ON THE PATH, get the user to agree, achieve it, then check in. Persona recommendations compose on top — they do not re-open the principle.
**Evidence base:** `phase-b-hardening-2026-05-16.md` (3/7 pre-fix) · `phase-b-fix-build-report-2026-05-16.md` (2/7 post-fix, sealed `ceb629b`) · `phase-b-fix-plan-2026-05-16.md` (the named seam).
**Source under evolution (all line refs verified against canonical `/Users/lukeivers/loam` HEAD `ce9d830`, branch `amend/loam-init-persona-wiring`):** `framework/tools/handsoff-loop/src/handsoff_loop/intake.py` (17,687 bytes, 392 lines, last touched in seal `ceb629b`).
**Prime objective it ladders to:** `framework/docs/VALUE_PROPOSITION.md` (the two tests).

---

## TL;DR (plain English, no jargon — lead)

1. **Contained evolution — YES, with one named prerequisite.** The
   refine/milestone behaviour is a *contained evolution* of the intake
   leg: it replaces one specific dead-end (the honest-refuse block) and
   adds one bounded loop-back around derive, on a leg that is already a
   single self-contained module with the independent judge it needs
   already built. It is NOT a loop re-architecture. **But** the
   milestone-on-the-path leg cannot be honestly *verified end-to-end*
   without the named intake→loop `check_command`/`check_argv` seam
   closed — because a "measurable milestone the user agreed to" is only
   real if the command the loop *actually runs* is the one the user
   agreed to. The seam moves from "candidate follow-on" (its status in
   the sealed fix plan) to **named in-scope prerequisite** for the
   milestone leg specifically. The interactive/self-refine legs do NOT
   need the seam and can land first.
2. **Where it hooks:** `intake.py:269-311` — the current
   `_derive_defects` honest-refuse block. Exactly where the loop today
   says "I can't pin this down" is where it instead enters refinement.
3. **Biggest design decision:** whether refinement is a *bounded
   re-derive loop inside intake* (recommended) or a *new
   orchestrator-level phase*. Recommendation: bounded loop inside
   intake — it keeps the durable elicitation leg untouched, reuses the
   already-built independent judge as the refinement oracle, and keeps
   "one approved unit" (D-UNIT) intact.
4. **One behaviour the user feels:** the single approval gate (AC.B.3)
   now sometimes presents a *measurable milestone on the path* and asks
   "is it OK if I aim at this first, then check back?" instead of
   presenting the full done. This is the owner's explicit design, not a
   new decision — surfaced for awareness.

---

## §1 — Objective

Evolve the hands-off loop's *intake leg* so that, when it cannot derive
a faithful machine-checkable "done" for the user's stated goal, it does
not dead-end at an honest refusal but instead **refines the goal toward
measurability** — first by a bounded interactive clarification with the
user, else by self-refining into measurable goal(s), and when the real
goal is not directly measurable at all, by deriving a **measurable
milestone on the path**, securing the user's plain-language agreement
to *that milestone*, achieving it, and **re-engaging a check-in** toward
the still-fuzzy ultimate aim — such that a re-run of the
phase-b-hardening 7-intent protocol shows the loop *refining* the
hard-to-verify intents into agreed measurable goals/milestones and
reaching faithful, **OR** returns a definite, evidence-backed
honest-negative naming, per intent class, which fuzzy goals cannot be
made measurable even on-the-path (a first-class valid §10.5 outcome —
the bar is honest, not gamed).

This objective ladders to **both** VALUE_PROPOSITION tests: a loop that
dead-ends on a fuzzy goal fails the primary-persona test (the
non-tech user's intent was not carried to AI-effective execution — it
was refused) and the harness test (the toolkit item terminates instead
of advancing the work the persona invoked it for). Refinement is the
translation layer doing its job at the exact point it currently gives
up.

**The transition this plan specifies (the owner's three-tier behaviour,
mapped to the source):**

| Today (`intake.py:269-311`) | After this evolution |
|---|---|
| derive fails → `_derive_defects` → honest refuse, `approved=False`, terminal | derive fails → enter refinement: (1) interactive clarify, (2) else self-refine, (3) else milestone-on-the-path + agreement + check-in |
| `faithful=False` (judge caught a proxy) → terminal `faithful=False` | `faithful=False` → same refinement entry (a proxy-check is a measurability failure, not a dead end) |
| one approval gate on the full "done" | one approval gate; its content may be a *milestone on the path* the user agrees to first |

## §2 — Fence (what this evolution will and will not touch)

**In scope (the only surfaces this evolution may mutate):**

- `framework/tools/handsoff-loop/src/handsoff_loop/intake.py` — the
  refine/milestone behaviour and its entry hook. Specifically the
  region `intake.py:231-391` (derive → defect-check → approval →
  faithfulness → return); the structural change is: the
  `_derive_defects` terminal-return (`intake.py:292-311`) and the
  `faithful=False` terminal become *entries into a bounded refinement
  construct*, not exits. The elicitation leg (`intake.py:202-229`) is
  reused, NOT modified.
- **The intake→loop `check_command`/`check_argv` seam — IN SCOPE AS A
  NAMED PREREQUISITE for the milestone leg only** (see §3). This is the
  one fence change vs the sealed fix plan, which had it as a candidate
  follow-on. Concretely: a read-path connection so that the command the
  loop later *freezes and executes* (`verify.FrozenAcceptance.check_argv`,
  `verify.py:42-57`; consumed `orchestrator.py:231`) is provably derived
  from the milestone the user agreed to in intake — not a separately
  hand-authored frozen-spec JSON (`cli.py:47-55` reads
  `args.frozen` today; intake output never reaches it). The interactive
  and self-refine legs do NOT require this and may land without it.
- The intake test surface that proves the refine/milestone behaviour
  (`framework/hands-off-lifecycle/tests/` — the existing
  `test_AC_HL_B1_B4_intake_structure.py` + `test_AC_HL_PBF_*` family,
  extended; new regression tests for the refinement construct). Both
  `framework/tools/` and `framework/hands-off-lifecycle/` are
  seal-admitted prefixes on this branch tip (verified against
  `framework/workspace-bootstrap/tests/test_no_sealed_amendments.py`
  `allowed_prefixes`, lines 268-308).
- IF AND ONLY IF the SKILL bundle prose
  (`plugins/loam-skills/skills/handsoff-loop/SKILL.md`) describes the
  intake step inaccurately after the change (it currently says intake
  ends at "an independent faithfulness check guarding the
  checkable-but-wrong failure" — silent on refinement): one
  behavioural-doc correction. Doc-truth touch, not a code site. Named
  so a builder neither expands nor forgets it.

**Out of scope (explicit, so effort is not wasted):**

- **The core decompose→dispatch→judge loop.** `orchestrator.py` /
  `goal_drive.py` internals are established (AC.FOUND.0). The ONLY
  orchestrator-adjacent change permitted is the seam read-path
  connection named above, and only because the milestone leg's honesty
  depends on it; the loop's decompose/dispatch/judge mechanism is NOT
  re-proved, NOT modified.
- **The verify spine** (`verify.py` freeze/hash-pin/independent-check/
  anti-overfit logic). The seam connection *feeds* `freeze_acceptance`;
  it does not change how verify decides done.
- **The §1a/§1c launch sites**, the **Telegram-poller isolation**
  (sealed `b33c0a8`, `_isolation.py`), **publish/seal-policy/
  canonical-main**, any **token/access/channel/config** change, any
  `claude` argv/model/isolation change. Plan-only artefact.
- **The elicitation leg (AC.B.2).** It is the *durable* part — across
  all 7 intents both pre- and post-fix it stayed at 3-4 bounded plain
  questions and recovered the adversarially-thin I5 (hardening §"What
  worked"; fix report AC.PBF.4). The elicitation behaviour is *reused
  by* refinement (the interactive-refine leg is the elicitation
  primitive applied a second time, scoped to the measurability gap) but
  the elicitation code is NOT modified — the durable leg must not
  regress.
- **The three sealed PBF fixes** (`ceb629b`: empty-gate, judge-sees-
  machine-check, jargon-guard). They are the *safe base* this builds
  on. The empty-gate refusal becomes the refinement *trigger*; the
  judge becomes the refinement *oracle*; neither is removed or
  loosened.
- **ProgramBench.** Revival stays downstream, gated on this evolution's
  re-harden. Not in this fence.

## §3 — Containment finding (F2 — the load-bearing question, answered from source)

**Dispatch halt-trigger #1:** *if the binding foundation is, on source
inspection, structurally infeasible on the current loop without a
re-architecture, say so plainly as a §10.5 finding; do not paper
"contained".* I read the actual source line-by-line (the reports are
medium-trust; this is the dogfood information-trust-ordering applied to
my own claim). The answer, in two parts because the foundation has two
separable legs:

### 3a — Interactive-refine + self-refine legs: CONTAINED EVOLUTION (no re-architecture). Evidence (file:line):

- The **refinement oracle already exists**: the independent
  faithfulness judge at `intake.py:336-374` is a real isolated
  `claude -p` subprocess (`_claude_json`, `intake.py:142-175`),
  post-`ceb629b` it *already sees the machine check command* and is
  *already adversarial* about proxy/plumbing checks (`intake.py:342-364`).
  "This goal is not measurable / this check is a proxy" is *the exact
  judgement it already makes*. Refinement does not need a new oracle —
  it needs the oracle's negative verdict to *route into a re-derive*
  rather than a terminal return.
- The **elicitation primitive already exists and is durable**:
  `intake.py:202-229` runs a bounded ≤4-question plain-language
  elicitation. The interactive-refine leg is *that same primitive*
  re-invoked with a measurability-gap-scoped prompt — not new
  machinery.
- The **entry point is one block, not a cross-cutting change**: the
  honest-refuse terminal is a single contiguous `return IntakeOutcome(...)`
  at `intake.py:292-311` (the `_derive_defects` path) plus the
  `faithful=False` terminal at `intake.py:368-391`. Converting a
  terminal-return into a bounded loop-back is a contained control-flow
  change *within one function* (`derive_acceptance_from_intent`), not a
  module restructure. The function is already the single unit producer
  (`__init__.py:32`, only non-test caller is
  `handsoff_loop_phase_b_runner.py:70`).
- **No new process, no new isolation, no verify-spine change** for
  these two legs. The bounded re-derive reuses `_claude_json` exactly
  as derive already does (`intake.py:247`).

**Conclusion for 3a: contained evolution, confirmed from source.** A
bounded refinement loop *inside* `derive_acceptance_from_intent`,
reusing the existing elicitation primitive and the existing independent
judge as the measurability oracle. Halt-trigger #1 does NOT fire for
these two legs.

### 3b — Milestone-on-the-path leg: contained in intake, but STRUCTURALLY GATED on the named seam. Evidence (file:line):

The milestone leg's contract is: derive a *measurable milestone on the
path*, get the user to agree to **that milestone**, the loop achieves
**that milestone**, then check in. The honesty of "the user agreed to a
measurable milestone the loop then achieved" requires that the command
the loop **actually freezes and runs** is the one tied to the agreed
milestone. Source shows that link **does not exist**:

- Intake produces `IntakeOutcome.machine_checkable` — a dict with a
  `check_command` *string* (`intake.py:256-259`, `intake.py:380-391`).
- The loop verifies via `verify.FrozenAcceptance.check_argv` — a *list*
  (`verify.py:42-57`), executed at `orchestrator.py:231` (`verify(...)`).
- The bridge between them: **there is none in the read path.**
  `cli.py:_cmd_run` (`cli.py:42-70`) reads a *separately hand-authored
  frozen-spec JSON file* (`args.frozen`, `cli.py:47`), calls
  `freeze_acceptance` from *that file's* `check_argv` (`cli.py:48-54`),
  and **never calls `derive_acceptance_from_intent`**. `IntakeOutcome`
  is exported (`__init__.py:32`) but consumed by nothing in the run
  path — only by the Phase-B *test* runner
  (`handsoff_loop_phase_b_runner.py`). Intake and the orchestrator are
  **two disconnected halves**; the user-approved milestone command and
  the executed command are, structurally, unrelated artefacts.

**This is the exact seam the sealed fix plan named "out of fence,
candidate follow-on" (`phase-b-fix-plan-2026-05-16.md` §3 honest
residual, §6.3, §8). Source confirms it is real and unbridged.** For
interactive/self-refine (3a) it stays out of scope — those legs improve
*what* `check_command` intake derives; whether that command is later
executed is the same pre-existing gap, neither worsened nor depended on.
But the **milestone leg's core promise ("you agreed to this measurable
milestone; I achieved exactly it") is unverifiable while the executed
command can be an unrelated hand-authored one.** Therefore:

**Finding (F2, stated plainly, not papered): the milestone-on-the-path
leg is a contained evolution of intake's *derivation* but requires the
named intake→loop seam closed as an in-scope prerequisite. It is NOT a
loop re-architecture — closing the seam is a read-path connection
(`IntakeOutcome.machine_checkable` → the `freeze_acceptance` input
`cli.py`/orchestrator already consumes), not a redesign of decompose/
dispatch/judge. But it is NOT zero — it is named here as a prerequisite,
not silently folded and not silently ignored (dispatch halt-trigger
#2).** Sequencing consequence: legs 3a land independent of the seam; the
milestone leg lands only with the seam connection in the same fence.

## §4 — Acceptance ladder (outcome-shape, satisfiability-tested)

Every AC states an *observable outcome*, not a method; each carries its
satisfiability note (**"can this be satisfied by a method other than
the one I have in mind?"** — yes ⇒ tight scope; no ⇒ method-in-AC, a
Lens-3 violation). The honest-negative is a **first-class valid
polarity** on the lead acceptance (AC.GR.5) by construction.

### AC.GR.1 — The honest-refuse terminal becomes a refinement entry

When the intake reaches the state it currently honest-refuses (empty/
broken/unparsed derive — `intake.py:292-311`) OR the independent judge
returns `faithful=False` (`intake.py:368-374`), the outcome is NO
LONGER an immediate terminal `approved=False`. Instead the intake
enters a bounded refinement attempt whose observable result is one of:
(a) a refined goal that *does* pass the existing
machine-checkable + independent-faithful checks, surfaced to the one
approval gate; (b) a measurable milestone-on-the-path surfaced to the
approval gate (AC.GR.3); or (c) — only after the bounded attempt is
exhausted — a definite honest-negative that names *why* this goal class
resisted refinement. A bare immediate refusal with no refinement
attempt does NOT satisfy this AC.

- *Ladders to:* both tests (the non-tech user's intent is carried
  forward by refinement instead of refused — primary-persona; the
  toolkit advances the work instead of terminating — harness).
- *Satisfiability:* satisfiable by a bounded re-derive loop, by a
  refinement sub-phase, by a recursive single-step decomposition with a
  judge-driven stop — multiple methods; the AC constrains *that the
  terminal becomes an entry with a bounded exhaustion*, not the loop
  construct. Tight, method is the builder's call.
- *Source it changes:* `intake.py:292-311` (`_derive_defects` terminal)
  + `intake.py:368-391` (`faithful=False` terminal).

### AC.GR.2 — Interactive-refine before self-refine, both bounded, elicitation not regressed

The refinement first attempts an *interactive* clarification with the
user (the existing bounded elicitation primitive, re-scoped to the
measurability gap — plain questions, hard-capped, no spec interview)
and only self-refines (model derives measurable goal(s) without further
user input) when interactive input is unavailable or does not resolve
measurability within the bound. The total user-facing question count
across original elicitation + interactive-refine stays bounded (the
durable AC.B.2 property — the user is never turned into a spec author);
the original elicitation leg's behaviour on a healthy intent is
unchanged.

- *Ladders to:* primary-persona test (interactive-first keeps the
  human in the loop on what *they* want; the bound keeps it from
  becoming the spec interview the binding foundation explicitly
  forbids) + harness test (a non-regressed durable leg).
- *Satisfiability:* satisfiable by reusing the elicitation fn with a
  refinement-scoped prompt + a global question budget, by a separate
  bounded clarify sub-routine, by a single re-elicit with a
  measurability-gap focus — multiple methods; the AC constrains
  *interactive-first + bounded + elicitation-not-regressed*, not the
  question-routing mechanism. Tight.
- *Source it leans on:* `intake.py:202-229` (elicitation, reused not
  modified) + the durable AC.B.2 invariant proven by
  `test_AC_HL_PBF_4_*` and `test_AC_HL_B1_B4_intake_structure.py`.

### AC.GR.3 — Milestone-on-the-path with explicit agreement + a re-engaged check-in

When refinement determines the real goal is not directly measurable
even after clarification, the intake derives a *measurable goal on the
path* to the user's stated aim, surfaces **that milestone** (not the
fuzzy aim) through the single plain-language approval gate framed as a
milestone the loop will aim at first, and — on agreement — produces an
outcome that (i) carries the measurable milestone as the approved unit,
AND (ii) records that this is a *milestone toward* a still-open fuzzy
aim such that a check-in is structurally re-engaged after the milestone
is achieved (the outcome is not a terminal "done" — it is "milestone
done, fuzzy aim still open, check-in due"). A milestone that silently
replaces the user's aim with no recorded check-in obligation does NOT
satisfy this AC.

- *Ladders to:* primary-persona test (the owner's explicit pattern:
  agreed measurable progress toward a fuzzy aim beats refusing the
  fuzzy aim) + harness test (the toolkit emits a unit the loop can
  actually verify *and* a recorded re-engagement obligation).
- *Satisfiability:* satisfiable by a milestone field + a
  check-in-pending flag on `IntakeOutcome`, by a chained-unit
  representation, by a recursive decomposition where the milestone is
  the first tighter-acceptance sub-objective and the check-in is the
  judge-driven re-plan — multiple methods; the AC constrains *agreed
  measurable milestone + structurally-recorded check-in obligation*,
  not the data structure. Tight.
- *Prerequisite (named, §3b):* the intake→loop seam — the milestone
  surfaced and agreed must be the command the loop freezes/executes,
  else "you agreed to this milestone, I achieved it" is unverifiable.
  AC.GR.6 is the prerequisite AC; AC.GR.3 depends on it.

### AC.GR.4 — Refinement is bounded and the honest-negative survives

The refinement construct has an explicit, finite bound (a maximum
number of refine attempts / a judge-driven stop), and on exhausting
that bound without a faithful measurable goal or an agreed milestone,
the intake produces a **definite honest-negative** that names the goal
class and why it resisted measurement — NOT an unbounded refine loop,
NOT a fabricated cheap test (the sealed `ceb629b` no-fake property is
preserved), NOT a silently weakened acceptance to force a pass. The
honest-negative is an AC-satisfying outcome exactly as a successful
refinement is.

- *Ladders to:* harness test (a refinement that could loop forever or
  fall back to a fake test is a poisoned toolkit item; the binding
  foundation's "do your best to refine" is a *bounded* best, the bar is
  honest not gamed).
- *Satisfiability:* satisfiable by an attempt counter, by a
  judge-`needs_fresh_start`-style verdict that can declare
  irreducible, by a cost/time budget — multiple methods; the AC
  constrains *bounded + honest-negative preserved + no-fake preserved*,
  not the bounding mechanism. Tight.
- *Honest-negative built in:* "this goal class cannot be made
  measurable even on-the-path, here is the evidence" satisfies this AC
  identically to a successful refinement.

### AC.GR.5 — The phase re-harden end-test (lead acceptance, §10.5 honest-negative valid)

A re-run of the **phase-b-hardening 7-intent reliability protocol**
(the same 7 verbatim, or an equivalently-varied set: 7 genuinely-vague
non-technical intents, ≥7 domains, ≥5 under-specification kinds,
including one adversarially-thin one-liner, none reusing the build's
"spending" intent), **one run per intent, no retry-to-pass**, with the
elicit/approval fns simulating a *reasonable cooperative user* (short
plain answers; agrees to a sensibly-derived measurable milestone when
the loop proposes one — the realistic shape the binding foundation
assumes), scored by an **independent faithfulness judge that is NOT the
loop's own AC.B.4b judge** (the same Tier-0 held-out methodology the
hardening + re-harden used), produces a definite per-intent verdict
table where the hard-to-verify intents are now *refined into agreed
measurable goals/milestones and reach faithful*, **reaching a bar
strictly stronger than the sealed 2/7** — **OR** returns a definite,
evidence-backed honest-negative naming, per intent class, which fuzzy
goals could not be made measurable even on-the-path.

**A definite "these classes refine, these classes are irreducible even
on-the-path — here is the evidence" is a valid, plan-success §10.5
outcome, reported straight, NOT retried to green.** If refinement
cannot make a given class measurable even on-the-path, that honest
finding stands; the bar is honest, not gamed (binding foundation's
explicit "bar is honest" + dispatch acceptance clause).

- *Ladders to:* both tests jointly — the prime-objective-level check
  that the loop now carries fuzzy non-tech intent to AI-effective
  execution by refinement.
- *Satisfiability:* the AC is "a definite, evidence-backed per-intent
  verdict on the 7-intent protocol under refinement exists, scored by a
  non-loop judge" — satisfiable by *either* polarity (refined-faithful,
  or honest-negative per-class) and by any independent
  dimension-grounded judging method that is not the loop's own judge.
  Not green-only, not method-bound.
- *Bar rationale (halt-trigger #2 surface):* the bar is "strictly
  stronger than the sealed 2/7, with each non-faithful intent carrying
  a definite refined-or-irreducible verdict" — deliberately NOT a fixed
  "≥6/7". A fixed numeric bar would (a) reward gaming on intent classes
  that are *honestly* irreducible even on-the-path (the binding
  foundation explicitly allows honest-negative per class) and (b)
  conflate "refined to a faithful full goal" with "agreed a milestone
  on the path" — different, both valid, owner-sanctioned outcomes. The
  honest bar is *per-intent definiteness + net improvement over 2/7 +
  no fabricated pass*, with the per-class irreducibility finding
  first-class. This is the §3-honest-negative-class surface for
  halt-trigger #2: the bar is set to be a fair honest test, not
  weakened to be passable and not inflated to force re-architecture.

### AC.GR.6 — The intake→loop seam closed for the milestone leg (named in-scope prerequisite)

The command the loop *freezes and executes* for an
agreed-milestone unit (`verify.FrozenAcceptance.check_argv`, executed
`orchestrator.py:231`) is provably derived from the
`IntakeOutcome.machine_checkable` the user agreed to at the approval
gate — not a separately hand-authored frozen-spec JSON unrelated to
intake. Observable: for a milestone unit, the executed check is
traceable to the approved milestone (a content/identity link the read
path enforces), such that "the user agreed to milestone M and the loop
verified exactly M" is structurally true, not coincidental.

- *Ladders to:* harness test (the toolkit's milestone promise is only
  real if the agreed thing is the verified thing) + primary-persona
  test (agreement to a milestone is meaningless if a different command
  decides done).
- *Satisfiability:* satisfiable by intake emitting the
  freeze-input directly, by `cli`/orchestrator consuming
  `IntakeOutcome` instead of a hand-authored JSON, by an identity/hash
  binding the read path checks before freeze — multiple methods; the AC
  constrains *agreed-command == executed-command provably*, not the
  wiring technique. Tight.
- *Scope note (F2):* this is the one AC that touches a read-path
  connection beyond `intake.py`. It is in-scope **only** as the
  milestone leg's prerequisite (§3b) — NOT a licence to modify
  decompose/dispatch/judge. AC.GR.1/.2/.4 do not depend on it and may
  land first; AC.GR.3 depends on it; AC.GR.5's *milestone* intents
  depend on it (AC.GR.5's interactive/self-refine intents do not).

### Ladder shape note (ODD self-check, inline)

AC.GR.1 (terminal→entry) / .2 (interactive-first bounded) / .3
(milestone+check-in) / .4 (bounded + honest-negative preserved) are
each strictly tighter than §1's objective — each pins one named
behaviour to one observable. AC.GR.6 is the milestone leg's structural
prerequisite (a tighter, separable acceptance). AC.GR.5 is the lead/
phase-end acceptance, strictly the union outcome §1 names, with the
per-class honest-negative as a first-class satisfying polarity. No AC
is "X passes" where only green satisfies. None states method (each
names ≥2 satisfying methods). Decomposition stops here — a further
split of any AC.GR.x adds only coordination overhead without tightening
the acceptance (Lens 5 stopping criterion). Dependency order:
{GR.1, GR.2, GR.4} parallelisable; GR.6 before GR.3; GR.5 depends on
all.

## §5 — Named decisions (owner calls, recommendation-led)

The binding foundation is settled product design and is NOT
re-litigated. The decisions below are *method/shape* calls the owner
explicitly invited recommendations on; none re-opens the principle and
none blocks build start (recommendation is the default; owner can
override).

### D-GR-1 — Refinement construct: bounded loop *inside intake* vs new orchestrator phase (the biggest decision)

**Recommendation: a bounded refine loop INSIDE
`derive_acceptance_from_intent`, not a new orchestrator-level phase.**
Rationale: (a) the refinement oracle (independent judge) and the
refinement primitive (bounded elicitation) *already live in intake* —
an orchestrator phase would have to call back into intake anyway; (b)
D-UNIT (the user approves one whole-objective unit) is an intake
invariant — keeping refinement in intake keeps the unit boundary
intact; (c) it keeps the durable elicitation leg and the core loop
untouched (smaller blast radius, Lens-6 reversibility signal). The
milestone leg still needs the seam (§3b) but the *refinement control
flow* is contained to one function. Owner can override toward an
orchestrator phase if a future multi-unit milestone chain is wanted;
default is in-intake.

### D-GR-2 — Interactive-refine availability when no human is present (parameter, not a block)

The binding foundation prefers interactive-refine *first*. In the
hands-off "I want Y, just go" mode the user has walked away — there is
no interactive channel mid-run. **Recommendation: interactive-refine is
attempted via the existing approval/elicit callback contract (the same
`elicit_answer_fn`/`approval_fn` seam intake already has); when that
callback indicates no live user (the hands-off case), the loop
self-refines and, if it must pick a milestone, surfaces it at the
*single existing approval gate* — which in true hands-off mode is the
user's pre-authorised "just go" standing agreement to a
sensibly-derived milestone.** This honours interactive-first when a
human is reachable and degrades to self-refine + milestone cleanly when
not, without inventing a new mid-run channel (no Telegram/channel
change — explicitly out of fence). Owner can require a hard
mid-run check-in for milestone pivots; default is the standing-agreement
degrade. Parameter, not a blocker.

### D-GR-3 — Re-harden intent set: same 7 vs equivalently-varied 7 (parameter, not a block)

**Recommendation: same 7 from the hardening report.** Same-input
before/after (3/7 → 2/7 → now) is the cleanest unambiguous evidence,
and all 7 are documented verbatim. The "equivalently-varied" clause in
AC.GR.5 exists only as the memorisation guard, named for completeness.
Owner can require a fresh varied set; default is same-7. Parameter, not
a blocker.

No other genuine owner calls surfaced. The binding foundation answers
the rest.

## §6 — What this evolution does NOT claim (F2, explicit)

1. **It does not claim refinement will make every fuzzy goal
   measurable.** AC.GR.5 is constructed so a definite per-class
   honest-negative ("these classes are irreducible even on-the-path")
   is a valid outcome. The plan claims the *behaviour transition* is a
   contained evolution + the re-harden is a fair honest test — it does
   NOT predict the verdict. The binding foundation itself anticipates
   this ("do your best", "the bar is honest").
2. **It does not claim the milestone leg lands without the seam.** §3b
   states plainly: the milestone leg's honesty is structurally gated on
   AC.GR.6. The interactive/self-refine legs (AC.GR.1/.2/.4) land
   without it; the milestone leg (AC.GR.3) does not. This is named, not
   folded, not ignored (dispatch halt-trigger #2).
3. **It does not claim a re-architecture is needed.** The containment
   finding (§3) is, from source: contained evolution of intake
   *derivation* + one named read-path seam connection for the milestone
   leg. NOT a redesign of decompose/dispatch/judge. Had source shown
   the binding foundation required reworking the loop spine, §3 would
   say so plainly and the plan would be shaped as a re-architecture — it
   does not, because the source does not support that.
4. **It does not re-open or re-prove** the core loop, the elicitation
   leg, the verify spine, the Telegram-poller isolation, or the three
   sealed PBF fixes. The sealed fixes are the *safe base* this builds
   on (their refusal becomes the trigger, their judge becomes the
   oracle); they are neither removed nor loosened.
5. **It does not claim a green re-harden auto-revives ProgramBench.**
   ProgramBench revival stays the downstream ratified step; this
   evolution's §10.5 outcome re-gates it (refined-faithful → revival
   becomes next; honest-negative-per-class → ProgramBench is bounded to
   the refinable classes or gated on a further effort). Either way the
   outcome re-gates ProgramBench; it does not fake a pass to unblock it.

## §7 — Lens self-check (ODD §9-style, inline)

- **Lens 1 (Claude-leverage):** refinement composes the *already-built*
  `claude -p` independent judge (post-`ceb629b`, machine-check-aware,
  adversarial) as the measurability oracle and the *already-built*
  bounded elicitation as the interactive-refine primitive. No new judge
  machinery, no re-implementation. Satisfied.
- **Lens 2 (harness + primary-persona):** the evolution converts the
  loop's give-up point into forward progress for a non-tech user — the
  precise translation-layer job at the precise point it currently
  fails. Both tests served; harness test served by keeping the toolkit
  item advancing instead of terminating.
- **Lens 3 (ODD authoring):** every AC is outcome-shape with a
  satisfiability note; no method-in-AC; the per-class honest-negative is
  a constructed valid polarity, not an exception.
- **Lens 4 (scope ↔ confidence):** confidence that the *behaviour
  transition shape* is right is high (it is the owner's explicit
  ruling, source-grounded as contained) → ACs tightly scoped to the
  named sites; the refinement *method* (loop construct, bound
  mechanism) is deliberately loose (D-GR-1 recommends, does not
  prescribe). The genuinely lower-confidence area (will refinement
  reach faithful per class) is left loose by construction — the
  honest-negative polarity on AC.GR.5.
- **Lens 5 (swarming):** decomposed into GR.1/.2/.3/.4 (each a tighter
  acceptance on one behaviour) + GR.6 (the milestone prerequisite) +
  GR.5 (aggregate phase end-test). Stopping criterion hit — further
  split adds only coordination overhead. The milestone-on-the-path
  *pattern itself* is a recursive single-step decomposition (milestone
  = first tighter sub-objective; check-in = judge-driven re-plan) —
  Lens 5 applied as the design, not just to the plan. Dependency order
  stated (§4 ladder-shape note).
- **Lens 6 (conflict resolution):** one latent conflict —
  scope-discipline (don't touch beyond intake) vs ruthless feedback
  (the milestone leg is dishonest without the seam). Four-step: named
  (§3b); signals — scope-confidence (high that milestone-honesty needs
  the agreed==executed link), blast radius (the seam is a read-path
  connection, not a spine redesign), reversibility (naming it in-fence
  is cheaper than discovering mid-build the milestone leg is
  unverifiable), information asymmetry (owner must know the milestone
  leg has a prerequisite the interactive legs don't); call (promote the
  seam to a named in-scope prerequisite for the milestone leg ONLY,
  keep it out for the other legs); surfaced (§3b + §6.2 + the FINAL
  message leads with it). Not silently resolved.
- **Lens 7 (ruthless feedback):** the containment question answered
  from source not report-prose (§3, file:line throughout); the seam
  disagreement with the sealed fix plan's "candidate follow-on" framing
  named with evidence (`cli.py:42-70` reads a hand-authored JSON, never
  calls intake) and an alternative (promote to in-scope prerequisite
  for the milestone leg); the bar-fairness reasoned not asserted
  (AC.GR.5 rationale). The disagreement named: *the sealed fix plan
  classed the seam "out of fence, candidate follow-on"; for the
  milestone leg specifically that classification is wrong, because the
  owner's milestone behaviour is structurally unverifiable without it;
  evidence = the disconnected halves at `cli.py:47` vs `intake.py:380`;
  alternative = in-scope prerequisite, AC.GR.6, milestone-leg-only.*
- **ODD scope:** every AC maps to §1's objective; no non-objective code
  licensed (the evolution touches `intake.py` refinement region + the
  named seam read-path connection + their tests + one conditional
  doc-truth line — nothing else). Plan-only honoured; no code here.

## §8 — §10.5-class findings (F2 — surfaced, not papered)

- **Containment (the load-bearing one): RESOLVED — contained
  evolution + one named prerequisite, from source.** Interactive/
  self-refine legs: contained, no re-architecture (§3a, file:line). The
  milestone leg: contained in intake's derivation but structurally
  gated on the intake→loop seam (§3b, file:line — the two halves are
  literally disconnected: `cli.py:47` reads a hand-authored frozen JSON
  and `derive_acceptance_from_intent` is called by no run-path code).
  Halt-trigger #1 does NOT fire (no re-architecture); the basis is
  stated explicitly so it is auditable, not asserted. Had the source
  shown the binding foundation required reworking decompose/dispatch/
  judge, this section would say re-architecture plainly.
- **The seam is now an in-scope prerequisite, not a follow-on (F2
  disagreement with the sealed fix plan, named).** The sealed
  `phase-b-fix-plan-2026-05-16.md` correctly scoped the seam out *for
  the three PBF fixes* — fix-2 did not depend on it. But the owner's
  milestone-on-the-path behaviour *does* depend on it: an agreed
  milestone is meaningless if a different hand-authored command decides
  done. Evidence: `cli.py:42-70` + `intake.py:380-391` + the absence of
  any `derive_acceptance_from_intent` run-path caller (grep-confirmed:
  only `__init__.py` export + the test runner). This is named as
  AC.GR.6, milestone-leg-only, not silently folded (dispatch
  halt-trigger #2 honoured), not silently ignored.
- **Bar fairness (halt-trigger #2): the AC.GR.5 bar is a fair honest
  test.** It is NOT a weakened-to-pass fixed number and NOT an
  inflated-to-force-re-architecture one — it is *per-intent
  definiteness + net improvement over the sealed 2/7 + no fabricated
  pass + per-class irreducibility first-class*, exactly because the
  binding foundation explicitly sanctions "honest-negative per class"
  and distinguishes "refined to full goal" from "agreed milestone on
  the path" (different valid outcomes a single number would conflate).
- **No internal inconsistency** found between the three reports'
  mechanism claims and the actual source: the honest-refuse block
  (reports: `intake.py:269-311`) confirmed at `intake.py:269-311`; the
  machine-check-aware judge (fix report AC.PBF.2) confirmed at
  `intake.py:336-374`; the seam (fix plan §3) confirmed unbridged at
  `cli.py:47` vs `intake.py:380`. Every load-bearing claim
  cross-checked against source.

---

*Plan authored 2026-05-16. Plan-only — no code in this artefact. Builds
on the sealed handsoff-loop intake + the three sealed PBF fixes
(`ceb629b`) as the safe base; does not re-prove the core loop, the
elicitation leg, the verify spine, or the Telegram-poller isolation.
Contained evolution of the intake derivation + one named in-scope
prerequisite (the intake→loop seam, milestone-leg-only). Honest-negative
per intent class is a first-class valid §10.5 outcome — the bar is
honest, not gamed.*
