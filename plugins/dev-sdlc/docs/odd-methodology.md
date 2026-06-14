# Objective-Driven Design (ODD) — Operational Specification

**Audience:** AI assistants authoring, reviewing, or executing work inside a
loam workspace — the canonical reference for what "doing ODD properly"
requires at the mechanical level. This is the **methodology tier (FR.2)** of the foundation-revision split, declared as a named primitive (id `FR.2`) in the machine-read [`docs/design/principle-manifest.yaml`](../../../docs/design/principle-manifest.yaml); its principles tier is [`framework/docs/principles/odd-principles.md`](../../../framework/docs/principles/odd-principles.md). **Status:** normative — when this document
and a persona's instincts disagree, this document wins. Rewritten 2026-06-10
per the ratified methodology-synthesis verdict (KEEL adoption program,
Phase 1); full pre-rewrite text (1,264 lines) at
`docs/archive/odd-methodology-2026-06-10-pre-keel.md`; section map at §11.

**Ancestry (honest).** ODD is not a novel discipline; an earlier version of
this corpus claimed it was "genuinely new", and that claim is retracted
(`docs/archive/odd-llm-grounding-derivation.md`). ODD descends from named
ancestors: goal-oriented requirements engineering (KAOS — van Lamsweerde et
al.), Outcome-Driven Innovation (Ulwick), Specification by Example (Adzic),
and Design by Contract (Meyer). What ODD actually is: ATDD +
goal-reverse-engineering + a strict reverse-coverage rule (§2.5) + evidence
banding (§6), tuned for LLM delegation, backed since the KEEL merge by
structural contract enforcement — a composite claim stronger true than the
novelty claim was false.

**Scope split (one sentence, load-bearing):** *ODD is how criteria are
written; KEEL is how they are enforced* — and the amendment cycle
(`plugins/dev-sdlc/docs/conventions/amendment-cycle.md`) is loam's
change-management, not part of the authoring methodology.

## 0. The spine — the system that produces the record

loam's works-as-expected outcome record is produced by six elements working
together. They were practice before doctrine; this section documents the
de-facto system AS the system. None may be removed or weakened except by
owner-ratified amendment.

1. **Pre-build owner-ratified plan** — the plan-doc lands and is ratified
   BEFORE code (plan-before-code is a hard rule).
2. **Precise, checkable acceptance criteria at a declared altitude** —
   precision + pre-agreement, more than altitude purity, makes delivery
   match expectation (§3.6).
3. **§2.5 forward/reverse coverage — the leading rule** (every declared
   behaviour has a criterion; every code path in the diff maps back to one).
4. **One production-entry-point `.S` smoke** — every AC family carries ≥1
   outcome-altitude criterion verified with no pre-arranged state.
5. **Seal-time executed suites + the seal-diff blast-radius fence** — tests
   RUN at seal, never assumed; diffs that escape the declared surface are
   refused.
6. **Recorded live probes + regression floor** — probes are recorded
   evidence; prior green is a floor the next change may not sink below.

**The KEEL frame.** These six are loam's instance of one objective-contract
primitive — a **contract** = { verbatim intent (Charter entries,
`docs/charter.md`) + derived binary criteria, each with a check-kind +
ratification record + content hash }, enforced by { a deterministic Gate
that is the only path to "done" + a stateless judge for judged criteria +
user-only amendment }. One lifecycle everywhere: **Capture → Translate →
Ratify → Bind → Build → Verify → Deliver, with Amend as the only change
path** — Amend user-only: the AI proposes, never enacts. ODD is the
authoring grammar of the Translate step. The unification table (verdict §3):

| Consumer | Charter (verbatim intent) | Criteria | Gate | Judge | Dial |
|---|---|---|---|---|---|
| Dev work | `docs/charter.md` (entry #0 = founding intent; owner rulings append) | plan-doc AC tables (ODD grammar) | `loam amend seal` + seal-diff fence | seal-time stateless leg for judged criteria; pytest for mechanical | M / L |
| Build-from-intent | confirmed intent from intake | frozen gate text, hash-pinned | `verify.py` | independent tool-executing judge + held-out check | S / M |
| Delivery promises | the gate text's promises, in the user's words | each promise a checked criterion | same `verify.py` gate | same judge — letter AND spirit | rides BFI |
| Owner conversations | decisions ledger = capture staging; ratified entries append | derived per ask | size-S: one verification before "here you go" | proportional | S default |

## 1. What ODD is

Every unit of work is defined by its **observable outcome**, not a sequence
of steps: an *objective* (a state of the world that must be true when the
work is done) + *constraints* (bounds on method) + *acceptance criteria*
(deterministic checks that the objective is met). **§1.1 The four terms:**

| Term | Definition | Authored by |
|------|------------|-------------|
| **Objective** | A state of the world the work must make true. Outcome, not procedure. | The delegator |
| **Constraint** | A bound the method must respect (budget, dependency fence, reversibility class, authority bound, fail-closed direction). | The delegator |
| **Acceptance criterion** | A deterministic, test-shaped check confirming the objective is met. One per declared behaviour. **Binary**: true / not-yet-true (§6). | The delegator; builder challenge permitted |
| **Method** | How the objective is satisfied — files, algorithm, library, sequencing. | The builder |

An instruction stating *steps to take* rather than *what must be true at the
end* is a procedure, not an objective; procedures in a brief are advisory,
only objectives bind.

**§1.2 The one-sentence test.** *An objective is a state of the world you
want true; an acceptance criterion is a deterministic check that the
objective is met.* If a work description does not fit that shape, rewrite
it until it does.

## 2. Authoring an objective

**§2.1 Required: scope.** Small enough that one criterion tests it, or large
enough to decompose cleanly. A scope needing seven criteria is probably
three objectives.
**§2.2 Required: constraints.** Budget · reversibility class · dependency
fence · authority bound · fail-closed direction. Constraints bound method
without prescribing it: "no LLM calls inside the gate" is a constraint;
"use a Pydantic validator" is method.
**§2.3 Required: acceptance criterion.** A deterministic check someone else
can run and get pass/fail without consulting the author's intent. The
criteria-audit rule: **every declared behaviour carries its own testable
criterion** — count "and"s, count criteria, they match.
**§2.4 Forbidden: method in acceptance.** The most common authoring-time
violation: "the test will use pytest", "the component implements a visitor
pattern", "the refusal is a Pydantic model_validator". Rewrite as what must
be true ("a component receiving malformed input refuses it with a
structured error"). Where a mechanism genuinely IS the contract, declare it
per §3.6 instead of smuggling it.

**§2.5 Forbidden: code for cases the objectives do not name.** The
positive-space corollary of §2.4 and the leading review rule: **build only
what the objectives require.** Every line of code, branch, test, and
dependency maps to a named criterion backing a named objective; code for
cases the objectives do not declare is a violation regardless of quality.

Anti-patterns: a platform branch no objective names; a config field no
criterion exercises; a defensive `if/except` for a case the contract says
cannot arise; a "might want it later" dependency; a test exercising a path
no criterion declares. The test: point at the criterion each code block
satisfies. If you cannot: **(1) re-extend up the objective chain** (§4) —
promote the case to a named criterion with its own test — or **(2) delete
the code.** "Might be useful later" is never a backing; later cases get
later amendments.

The check runs in both directions — **forward (authoring):** every declared
behaviour has a criterion; **reverse (review):** every code path, test,
branch, and dependency in the diff maps back to one. Forward + reverse
passing = scope-clean. Enforcement is convention + review + the seal-diff
fence (§0.5); there is no write-time machine gate (§10.3).

## 3. Acceptance criteria in detail

**§3.1 Deterministic.** Same verdict for the same state, every run, without
model inference or human judgment; a criterion you cannot execute is a wish.
**§3.2 Test-shaped.** A well-formed criterion writes its own test: every
clause maps to one assertion (state transition, side-effects, timing).
**§3.3 One criterion per declared behaviour.** "Accepts X, rejects Y, logs
Z" = three behaviours = three criteria (or one criterion with three
independently testable clauses). Prevents declaring four behaviours, testing
the easiest, shipping three unverified.
**§3.4 Timing and budget belong in the criterion.** Latency, cost, and
concurrency bounds are part of the criterion — a kill that works in 60s is
not the objective.
**§3.5 Negative criteria are criteria.** "X does not happen" is valid and
testable when the objective prevents something: construct the forbidden
state, fire, assert refusal.
**§3.6 Per-criterion altitude declaration (canonized 2026-06-10).** Every
criterion declares its altitude: **outcome** (observable from outside;
survives implementation rewrite) or **mechanism** (pins a specific surface
or behaviour of the implementation). Mechanism-pinning is **legitimate when
the mechanism is the deliverable** — a gate, hook, or fence IS the thing
being built — provided the criterion (a) declares its altitude and
(b) traces to an outcome-altitude parent in its chain. Every AC family
carries ≥1 criterion marked `outcome-altitude: true`, verified by a
production-entry-point test with no pre-arranged state (the `.S` smoke).
The old doctrine's dishonesty was denying this; disciplined
mechanism-pinned criteria are half of why delivery matches expectation.
Altitude quality tools: §9.

## 4. Defects, gaps, and re-extension

**A failure mode discovered during work is re-extended up the objective
chain as a new positive criterion — never buried as an exception branch.**
**§4.1 The pattern:** on discovering a scenario the objectives don't cover,
a collision between objectives, or a letter-passes/spirit-fails case,
promote it to a named criterion (the A20 pattern), author a test, name the
rationale in the commit.

**§4.2–4.4 Why, and the boundary.** A buried branch is invisible to the
criteria audit, untestable independently, and accumulates silently; a
re-extended criterion appears in the audit list with its own test.
Re-extension is never a scope violation; **silent handling is.** When the
gap exceeds the scope's remit, the sanctioned action is
**halt-and-surface**: stop, name the condition, return to the delegator for
ruling. "Almost done" is never a reason to push through — and the halt rule
now has a structural backstop: a builder who blows past a halt condition
also fails the Gate, which never saw their reasoning.
**§4.5 Repeating hotfixes = architecture-level gap.** 2+ hotfix amendments
against the same code area in close succession put the gap below the AC
level: pause hotfix iteration, commission a first-principles review, ruling
before more hotfixes.
**§4.6 First-principles triggers.** (1) N≥2 hotfixes on one sealed component
within ~14 days; (2) the same root cause in 2+ distinct code paths in one
fix cycle; (3) tests pass but the bug ships — review the test contract, not
just the bug; (4) operator-confusion events; (5) estimate inflation that
feels wrong for the scope. Trigger-based, not periodic: every-decision
reflection is paralysis, never-reflect is decay.

## 5. Enforcement in code — structural over advisory

**§5.1 The distinction.** An **advisory rule** lives in prose and depends on
the reader. A **structural check** lives in the type system, schema, or
constructor — the forbidden state is unrepresentable. Structural wherever
possible; advisory only where structure cannot reach (voice, clarity,
abstraction choice).
**§5.1.1 Relocate-vs-eliminate.** Among structural options, prefer the one
that *eliminates* the failure class over the one that *relocates* it
("forgot the rule" → "forgot to update the mechanism"). The test: *can a
future code change re-introduce the same failure class without active
discipline?* If yes, the option is rule-shaped despite its mechanism; seek
stronger.

**§5.3 Reach-for default.** Pydantic schemas with `model_validator` — fail
at construction, structured errors, test-shaped, composable. (The worked
clause-(g) example lives in the archived spec §5.2.)
**§5.4 What structure cannot reach.** An LLM verdict is not a deterministic
structural mechanism — same prompt, same model, different verdicts across
runs. When an LLM verdict gates, pair it with a deterministic floor or
N-of-M agreement, and say plainly the check is not structurally guaranteed;
judged verdicts are evidence-graded accordingly (§6).

## 6. Check-kinds and evidence grades (banding, restated honestly)

Criteria are **binary** — true / not-yet-true. What was formerly a
"confidence band on the AC" decomposes into two orthogonal facts about the
*check*:

**Check-kind** (how the criterion is verified): **mechanical** — executable
check (pytest, grep-class sweep, hash comparison), stateless by
construction; **judged** — verified by a stateless, conversation-blind judge
receiving only (Charter, criteria, deliverable), which must quote evidence
(verdict without evidence = FAIL); **attested** — a human attests, recorded
with source + timestamp.

**Evidence grade** (what the verification evidence is worth):

- **VERIFIED** — *the check ran green at a known SHA.* Nothing else earns
  this word. Evidence: run record + SHA.
- **ASSERTED** — assumed-green: a test exists and is believed to pass, or a
  source citation supports the claim, but no recorded run at a known SHA
  backs it. (The honest name for what parts of the old corpus called
  VERIFIED.)
- **HYPOTHESISED** — inference; evidence is a rationale chain; must be
  independently confirmed before treated as binding.

**Extractor mapping note (until the code rename lands):** the
odd-extractor's band enum
(`plugins/dev-sdlc/odd-extractor/.../bands.py`) still spells its top band
`VERIFIED` and grants it on a *test-pass assumption* without executing the
foreign suite. Under this doctrine, **the extractor's `VERIFIED` band = the
ASSERTED evidence grade** until the enum rename ships in a later
extractor-touching amendment; PLAUSIBLE likewise maps to ASSERTED
(source-citation form); HYPOTHESISED is unchanged. Extractor mechanics
(evidence-field rules, ratification workflow, promotion asymmetry, adapter
band tables): `plugins/dev-sdlc/odd-extractor/docs/adapter-conventions.md`.

## 7. Authoring checklist (for delegating personas)

**§7.1 Order of composition.** 1. Objective first ("X must be true").
2. Constraints second. 3. Acceptance third — count behaviours = count
criteria; declare altitude per criterion; mark the `.S` outcome-altitude
criterion. 4. Method last, only as suggestion, never inside acceptance. If
step 4 feels necessary before step 3, the objective is underspecified.

**§7.2 The how-vs-what smell test.** For every line: end-state or
path-to-it? Path lines in objective or acceptance sections are defects —
move to a suggested-approach section or delete.
**§7.3 The behaviour-count check.** Re-read each objective; count declared
behaviours; count criteria; add until they match.
**§7.4 Flagged inferences.** List the author's ungrounded judgments
(thresholds, naming, category lists) explicitly as "flagged for the builder
to challenge" — visible inheritance, not silent.
**§7.5 Halt triggers are part of the brief.** Every brief names its
halt-and-surface conditions; their absence lets a builder treat "almost
done" as license to exceed scope.

## 8. Catching violations (for reviewers)

**§8.1 Authoring-time.** (1) method in acceptance; (2) behaviour-count
mismatch; (3) objective with no criterion — a wish, reject; (4)
judgment-reliant acceptance ("should be readable") — replace with a
deterministic check, route to a judged-kind criterion (§6), or name it a
soft goal outside the contract; (5) procedure in the objective;
(6) unbounded scope (no budget / reversibility / authority); (7) missing
halt trigger; (8) undeclared altitude (§3.6).
**§8.2 Review-time.** (9) silent exception branches; (10) code for cases no
objective names (§2.5 reverse — no criterion, no code); (11) acceptance
tests asserting implementation detail instead of outcome; (12) criteria
without tests; (13) advisory rules where structural checks would work;
(14) verdict-shape-only verification on state-mutating diffs — ≥1 test must
read the post-mutation artefact from disk and compare content; output
strings and audit rows describe intent, not effect.
**§8.3 The two quick rules.** "The test will use pytest" is a violation;
"the component refuses malformed input" is an objective. Most violations
look like the first; most well-formed objectives look like the second.

## 9. Altitude tests, drift modes, self-checks (Translate-step quality tools)

Promoted from the archived derivation doc (§6–§8 there); the lean prime
(`docs/odd-llm-grounding.lean.md`) carries the same tools in load-first
form. **§9.1 The four altitudes:**

| Altitude | Definition | Test |
|---|---|---|
| **Objective** | Outcome the system delivers; observable from outside | Rewrite the implementation in another language — does the statement still describe the system? |
| **Constraint** | Bound on the solution space, not itself an outcome | Restricts HOW without being an outcome? |
| **Capability** | Feature serving objectives; one of many possible HOWs | Could a different system deliver the same objectives without it? |
| **Implementation** | Specific symbol/file/line/library | Names one? Then implementation. |

**§9.2 The seven drift modes** (look ODD-shaped but aren't):
(1) **symbol-as-AC** — "route X exists at file:line"; state the outcome the
route serves; (2) **function-name-as-AC** — "foo() exists"; same correction;
(3) **feature-as-objective** — "app has CSV upload" is a capability; the
objective is the outcome upload serves; (4) **test-name-as-implementation**
— tests asserting calls/DOM are implementation-shaped; tests asserting
outcomes are AC-shaped; (5) **gap-as-objective** — missing coverage is a
finding, not an objective; (6) **constraint-as-objective** — "must be SOC-2
compliant" is a bound; the outcome behind it is the objective;
(7) **implementation-detail-as-constraint** — "uses RSA-OAEP" lifts to
"tokens confidential under transport".
**§9.3 The five self-checks** (before declaring any AC/objective):
(1) **outcome-or-fact?** — a fact about how it's built is not an objective;
(2) **implementation-swap** — survives a rewrite? objective-altitude;
(3) **builder-method** — could a different builder meet it differently? if
not, it prescribes method — loosen, or declare per §3.6;
(4) **observable-from-outside** — verifiable without reading the code?
(5) **user-purpose** — names value-to-someone? Any check fails → wrong
altitude → restate.

## 10. Where this fits

**§10.1 The document set.** This spec governs the mechanics. Contributor
short form: `docs/design/odd.md`; worked loam examples: `odd-in-loam.md`;
load-first prime: `docs/odd-llm-grounding.lean.md`. The Charter
(`docs/charter.md`) is the root contract every criterion ladders to;
`docs/VALUE_PROPOSITION.md` carries `AC.PO.1` / `AC.PO.2`, the first
derived criteria. Change-management (amendment cycle, seal, fence) lives in
`plugins/dev-sdlc/docs/conventions/` — how loam ships changes, not how
criteria are authored.
**§10.2 The plan-doc standard (recent-era shape, promoted 2026-06-10).** A
loam plan is **lean**: objective + constraints/fence + AC table with
per-criterion outcome-shape annotation (§3.6) + chain uplinks (AC family →
parent objective → program objective → Charter) + one
production-entry-point `.S` smoke + named decisions + halt triggers.
Mandatory per-plan 8-lens sections are dropped — the design lenses stay at
feature-proposal altitude (CLAUDE.md), where they were aimed.
**§10.3 Write-time gates: archived, not dormant.** There is **no active
write-time structural enforcement** of §2.5 (no per-edit objective-binding
or TDD gate). Two built-but-never-registered hooks were archived by
decision on 2026-06-10 — see
`docs/archive/dormant-write-time-gates-2026-06-10.md` for the gates, the
three reasons, and the one salvaged component (dispatch contract-carriage,
KEEL Cycle A). §2.5's enforcement is convention + review + the seal-diff
fence; the doctrine saying otherwise was the falsehood the archive note
ends.

## 11. Section map (pre-KEEL 1,264-line spec → this spec)

Sealed plans citing "ODD §N" cite the meaning at their seal SHA; this map
keeps those citations resolvable against the current spec.

| Old | Content | Now |
|---|---|---|
| §1–§5 | definitions, authoring, ACs, re-extension, structural enforcement | §1–§5 (numbering + meaning preserved; §2.5/§3.3/§3.4/§4.x/§5.1.1/§5.3 intact; §3.6 added) |
| §6 | ODD vs TDD vs BDD | cut (triplicated); short form survives in `docs/design/odd.md` |
| §7–§8 | authoring checklist, violation catalogue | §7–§8 (compressed; §7.4/§8.2 meanings preserved; §8.1 gains item 8) |
| §9 | quick-reference card | cut — this spec is now short enough to be the card |
| §10 | where this fits | §10 (extended) |
| §11 | confidence bands for derived ACs | restated as §6 evidence grades; extractor mechanics → `odd-extractor/docs/adapter-conventions.md` |
| §12–§13 | per-language adapter conventions (Ruby, JS/TS) | `plugins/dev-sdlc/odd-extractor/docs/adapter-conventions.md` |
| §14 | v0.2.3 multi-source banding rule | `plugins/dev-sdlc/docs/odd-methodology-CHANGELOG.md` |
