# Personas — Methodology Reference

**Status:** methodology — names what makes a persona valuable, when to add
one, and when not to. Authored 2026-05-08 against the existing 6-persona
shape (1 primary + 5 dev-sdlc subagents) shipped in v0.1.7.

This doc is the framework loam authors against when proposing or rejecting
new personas — at any plugin or framework layer. It does not propose
specific new personas; specific proposals come after, walking the rubric
in §5.

Authority chain: [`CLAUDE.md`](../CLAUDE.md) Lenses 1, 2, 4;
[`VALUE_PROPOSITION.md`](rebuild/VALUE_PROPOSITION.md); the canonical
shape at [`personas/primary/`](../personas/primary/) and the five
subagents at [`plugins/dev-sdlc/agents/`](../plugins/dev-sdlc/agents/);
[`STATE.md`](rebuild/STATE.md) v0.1.7 row;
[`FUTURE_IDEAS.md`](rebuild/FUTURE_IDEAS.md) Idea 3.

---

## §1 What is a persona in loam (AC.PM.1)

A persona in loam is the pairing of two artefacts loaded into Claude
Code's subagent context at dispatch time:

1. **A persona contract** — machine-readable YAML at
   `personas/<name>/contract.yaml` (or `plugins/<plugin>/agents/<name>.md`
   for plugin-shipped subagents, where the front-matter block carries
   the contract data). Names handle, model selection, tool surface where
   restricted, addressable status, dev-intent flag, primary flag.
2. **A persona prompt** — free-prose markdown at `personas/<name>/prompt.md`
   (or the body of the same plugin-shipped `agents/<name>.md` file).
   Names role, voice, when-to-invoke triggers, harness-composition
   surfaces, method-shape (builder's call per ODD §1.1), halt-and-surface
   rules, out-of-scope.

Both pieces are loaded together at the start of a dispatched subagent's
context window. The pairing is what makes a persona a persona — the
contract alone is metadata, the prompt alone is unenforced prose.

**Persona vs SKILL.** A SKILL (Claude Code's `~/.claude/skills/<name>/`
mechanism) is *body-loaded-on-trigger*: the SKILL's `SKILL.md` ships
with a description, the harness loads the body only when an active
description match fires. A persona is *full-context-set-at-dispatch*:
the entire persona prompt is in context before the first turn runs, and
stays there for the lifetime of the subagent. Personas are heavier and
shape the agent's whole trajectory; skills are lighter and shape one
local decision. The right shape for repeated, broad-trajectory work is
a persona; the right shape for a narrow procedural rule the agent
should follow is a SKILL.

**Persona vs plain dispatch prompt.** A plain dispatch prompt is
authored fresh per dispatch with no shared shape. A persona is
reusable across dispatches with the same role-shape. Break-even is
roughly three dispatches; below that, a plain prompt is fine.

---

## §2 Why personas are valuable — the constraint-narrowing framing (AC.PM.2)

A prompt is a probability mass over agent trajectories (Lens 4). A
generic primary-persona dispatch covers a wide trajectory space —
every domain, every task shape, every method. Mass is diffuse;
tail-shaped trajectories (the one-in-twenty "agent went off and did
the wrong thing") consume real probability.

A persona narrows that mass. The contract names role and tool surface;
the prompt names voice, halt-and-surface rules, method-shape, and
out-of-scope. The sampled trajectory space is deliberately smaller;
off-pattern tails are correspondingly shorter. A `loam-builder`
dispatch cannot wander into research-only
territory without first violating its named scope; a `loam-researcher`
dispatch cannot edit source because the tool surface forbids it. The
constraint is structural where it can be (tool restriction), prosaic
where structural is unreachable (halt-and-surface rules in the prompt).

This composes tightly with Lens 4. The primary persona is broad-scope
(it has to be — it's the address for any work that is not yet clearly
someone else's). Sub-personas are narrow-scope by design — each is a
constrained-scope pre-built template the primary draws from when the
work-shape matches. The choice of which persona to dispatch IS the
scope-tightness decision Lens 4 names; personas pre-package the
common scope-tightness configurations so the primary doesn't author
them per dispatch.

---

## §3 When to add a persona (AC.PM.3)

Four signals that a new persona is worth authoring. Each is necessary
but none alone is sufficient — the case strengthens when multiple fire.

**Signal 1 — domain has consistent shape with repeatable work patterns.**
The work has a recognisable role-name. "Builder of sealed-component
amendments" is a role; "person who occasionally edits files" is not.
Worked example: the dev-sdlc cycle has a stable shape (plan → manifest
→ edits → tests → apply → seal → backfill); that supports `loam-builder`.

**Signal 2 — primary persona over-generalises and produces drift.**
When the primary handles this domain, outputs vary across dispatches.
Worked example: plan-doc authoring before v0.1.7 drifted on §-ordering,
named-decision surfacing, and method-in-AC violations;
`loam-plan-author` exists because the consistency cost was real.

**Signal 3 — tighter constraints would meaningfully change the
trajectory distribution.** The persona's constraints have to cover
ground a prose constraint in a fresh dispatch prompt cannot reach.
Worked example: `loam-researcher` ships with read-only tool surface
(no Edit / Write / Bash). That structural constraint cannot be
replicated by a prose rule; the persona is the only place it lives.

**Signal 4 — work is dispatched-to often enough to amortise authoring
cost.** Authoring a persona costs hours; the cost has to amortise.
Break-even is roughly three dispatches per month (estimate; calibrate
from observed rate). Worked example: amendment cycles dispatch
`loam-builder` multiple times per week — pays for itself within a week.

---

## §4 When NOT to add a persona (AC.PM.4)

Four anti-signals. Any one is enough to reject the persona proposal.

**Anti-signal 1 — work is too varied or one-shot to amortise.** If
the role's first three dispatches each have a different scope-shape,
the role isn't a role yet — it's three ad-hoc tasks the primary
should handle directly. Add the persona only after the shape stabilises.

**Anti-signal 2 — primary persona already handles it well.** If the
primary's outputs in this domain are consistent and on-shape across
dispatches, adding a sub-persona burns coordination overhead with no
trajectory tightening. The right move is "no persona, primary handles."
Worked example: short user-facing replies need the primary's voice,
context, and trust relationship; a "reply-writer" sub-persona would
fragment that and gain nothing.

**Anti-signal 3 — proposed persona would surface directly to the user.**
Sub-personas exist to give the primary a tool to dispatch to, not to
appear directly at the user's surface (Lens 2). A persona that the user
talks to directly violates the single-coherent-voice property that
makes the primary the address-of-record. The right move is to extend
the primary's vocabulary, not split its voice. The primary may invoke
a sub-persona for the work, then translate the result back to the user
in its own voice.

**Anti-signal 4 — proposed persona duplicates an existing one's role.**
If two personas would dispatch on overlapping triggers, the boundary
between them is unclear and the dispatching primary will mis-route.
Worked example: a hypothetical `loam-architect` covering both research
and plan-authoring would overlap with `loam-researcher` and
`loam-plan-author`; the right move is sharper boundaries between the
two existing personas, not a third one that blurs them further.

---

## §5 Decision rubric (AC.PM.5)

Six questions a future authoring agent walks before proposing a new
persona. The rubric output is a recommendation: **add this persona /
extend an existing one / primary handles it; reject.**

1. **Role-shape stability.** Does the work have a stable role-name
   the next ten dispatches would all match? *Yes / Partial / No.* No
   → reject (anti-signal 1).
2. **Primary drift evidence.** Has the primary, dispatched on this
   work, produced inconsistent outputs we can name? *Yes with
   examples / Suspect / No.* No → primary handles it (anti-signal 2).
3. **Structural constraints reachable.** Is there a tool-surface,
   model-tier, or pre-loaded-context constraint a fresh dispatch
   prompt cannot replicate? *Yes / No.* No → consider a SKILL or a
   prompt template instead.
4. **Dispatch frequency.** Does the work dispatch ≥3 times per
   month, sustained? *Yes / Borderline / No.* No → ad-hoc dispatch
   amortises better.
5. **Lens 2 audience check.** Does this persona serve the primary
   (sub-persona) or attempt to surface to the user? *Sub-persona /
   User-surface.* User-surface → reject (anti-signal 3).
6. **Boundary cleanliness vs existing personas.** Can a clear,
   one-sentence boundary be drawn against every existing persona
   the proposal might overlap with? *Yes with the sentence / Fuzzy.*
   Fuzzy → extend the existing persona instead (anti-signal 4).

**Rubric output.** Six "yes" answers (Q1, Q3, Q4 yes; Q5 sub-persona;
Q6 yes-with-sentence; Q2 yes or suspect-with-evidence) → **add this
persona.** Five-of-six with one borderline → **extend an existing
persona** (the borderline question names where the extension goes).
Four or fewer → **primary handles it; reject.**

---

## §6 Per-language personas worked example (AC.PM.6)

Luke's 2026-05-08 example: should there be per-programming-language
personas inside dev-sdlc — `loam-builder-python`,
`loam-builder-typescript`, `loam-builder-ruby`?

Walking the rubric:

1. **Role-shape stability.** Yes — building inside a language has a
   stable shape per language (idiomatic patterns, test framework,
   lint rules, dependency model). The Python builder's work-shape is
   recognisably different from the TypeScript builder's.
2. **Primary drift evidence.** Suspect — the current `loam-builder`
   sometimes ships TypeScript code with Python-flavoured test
   structure or vice-versa when the codebase is polyglot. Evidence
   isn't formally collected; the suspicion is real.
3. **Structural constraints reachable.** Yes — each language persona
   could ship with language-specific lint commands, idiomatic patterns
   pre-loaded, test framework conventions named. A fresh dispatch
   prompt could *say* "use pytest" but couldn't carry the full
   language-idiom context as efficiently.
4. **Dispatch frequency.** Per language, depends on the codebase mix.
   For pos-v2 (predominantly Python with some Bash), a Python
   sub-builder dispatches roughly as often as the current `loam-builder`;
   a TypeScript sub-builder rarely. Borderline for non-primary languages.
5. **Lens 2 audience check.** Sub-persona — these would be dispatched
   by `loam-builder` (or directly by the primary), never user-facing.
6. **Boundary cleanliness.** Yes — language is the boundary.
   `loam-builder-python` handles Python work; `loam-builder-typescript`
   handles TypeScript work. Polyglot files force a routing call but
   the boundary itself is clean.

**Rubric output.** Five-of-six yes (Q4 borderline for non-primary
languages). Recommendation: **extend an existing persona** — keep
`loam-builder` as the dispatched role, but author a **language-adapter
SKILL bundle** the builder loads on trigger when it detects the file's
language. The SKILL bundle gives the same trajectory-tightening as a
sub-persona without paying the dispatch-overhead and authoring-cost of
N language sub-personas, most of which would dispatch rarely.

This is the right move because Q4 is the load-bearing question — the
constraint-narrowing per-language is real (Q3 yes), but the dispatch
volume per language doesn't amortise N sub-personas. SKILLs amortise
better at low-frequency.

---

## §7 Existing-persona-shape audit against the rubric (AC.PM.7)

Each of the six shipped personas walked against the rubric.

**`primary` — chief-of-staff translator.** Value-prop: single
coherent voice the user develops trust with; translates intent into
AI-effective execution. Why-it-passes: Q5 carves out the user-facing
role explicitly; the primary IS the user-facing exception sub-personas
defer to.

**`loam-builder` — sealed-component-cycle builder.** Value-prop: ODD
§2.5 fluent; source edits + tests + apply + seal end-to-end within a
named fence. Why-it-passes: Q1 yes (cycle has stable shape); Q2 yes
(primary mis-orders the apply/seal ritual without it); Q3 yes
(halt-and-surface fluency baked in); Q4 yes (multiple per week); Q5
sub-persona; Q6 yes ("apply + seal", not plan, review, or document).

**`loam-plan-author` — plan-doc author.** Value-prop: outcome-shape
ACs; named decisions with recommendations; F2 RF baked into §10.
Why-it-passes: Q1 yes (plan-doc shape stable per convention); Q2 yes
(pre-v0.1.7 plans drifted on §-ordering and method-in-AC); Q3 yes
(ODD + F4 fluency pre-loaded); Q4 yes (every cycle needs one); Q5
sub-persona; Q6 yes ("plan, not build, review, or research").

**`loam-researcher` — read-only research.** Value-prop: tool-surface
restriction makes the read-only contract structural; Lens 1–3 fluency
baked into the artefact shape. Why-it-passes: Q1 yes; Q2 yes (without
it, "research" dispatches sometimes edit mid-research); Q3 **strongly
yes** — tool restriction is the canonical structural constraint a
fresh prompt cannot replicate; Q4 yes; Q5 sub-persona; Q6 yes.

**`loam-reviewer` — gate-review of sealed amendments.** Value-prop:
ODD §2.5 walk + fence-diff cleanliness + AC-test mapping verdict.
Read-only-with-git tool surface. Why-it-passes: Q1 yes; Q2 yes
(primary-as-reviewer drifts on which checks to run); Q3 yes (tool
restriction + verdict template); Q4 yes; Q5 sub-persona; Q6 yes.

**`loam-documenter` — public-facing docs.** Value-prop: non-jargon
voice; loam idioms translated to general engineering language. Lens
2 fluent. Why-it-passes: Q1 yes; Q2 yes (primary uses internal jargon
by reflex); Q3 yes (anti-pattern checklist + voice constraints
pre-loaded); Q4 borderline — release-cadence-bound; Q5 sub-persona; Q6 yes.

**Audit verdict.** All six survive. `loam-documenter`'s Q4 is the
borderline case; if release cadence drops below ~3 doc-touching
releases per quarter, revisit whether the primary handles it directly
with a doc-authoring SKILL bundle instead.

---

## §8 F2 Ruthless Feedback — honest tensions (AC.PM.10)

Three tensions worth naming explicitly.

**Tension 1 — more personas vs more dispatch overhead.** Each new
persona narrows one trajectory space at the cost of one more
dispatch-routing decision the primary makes. At the limit, a persona
per task-shape replaces "primary thinks about the task" with "primary
thinks about which persona handles the task" — coordination-shaped
work that doesn't ladder up to user value. The rubric's Q4 (dispatch
frequency) is the brake; if dispatch volume doesn't amortise, the
overhead exceeds the trajectory tightening.

*Resolution.* Run the rubric every time. Q4 is the load-bearing
question for this tension; reject low-frequency persona proposals
even if Q1–Q3 all fire.

**Tension 2 — primary as single coherent voice vs delegation cost.**
Lens 2 says the primary is the single voice the user trusts. But the
primary's coherence is paid for by every sub-persona delegation — the
result has to come back through the primary's voice, which is a
translation cost. At the limit, if every dispatch goes to a sub-persona,
the primary becomes a router with no voice, and the user's trust
relationship hollows out.

*Resolution.* Sub-personas exist for work the user doesn't see directly
or for work the primary cannot do well even with full attention.
Anti-signal 3 (user-facing → reject) names this; the primary owns the
user surface even when the work is sub-persona-shaped underneath.

**Tension 3 — Lens 4 confidence vs constraint-narrowing.** Lens 4 says
loosen scope when confidence in the outcome is low; constraint-narrowing
says tighten scope to bias trajectories. These can pull opposite
directions when the work-shape is ambiguous (e.g., a research question
that might also be a plan-authoring question). A too-tight persona
choice locks the agent out of the actually-correct alternative; a
too-loose choice burns tokens on options the dispatcher already knew
were wrong.

*Resolution.* Apply the multi-signal conflict-resolution discipline
(name the conflict, name the active signals, make the call, surface
if non-obvious). For ambiguous work-shapes, dispatch the broader
persona (researcher over plan-author when the question is "is this
buildable?"; primary over researcher when the question is "what does
the user want?") and let halt-and-surface narrow the next dispatch.

---

## §9 Composition with the lenses

**Lens 1 (Claude-leverage).** Personas in loam ride Claude Code's
subagent mechanism — `Task` dispatch with model selection, tool
restriction, and front-matter contract. Seam: file at
`plugins/<plugin>/agents/<name>.md` or the pair at
`personas/<name>/{contract.yaml,prompt.md}`. No custom runtime.

**Lens 2 (primary-persona translation).** Sub-personas are the toolkit
the primary draws from. Anti-signal 3 + rubric Q5 enforce the
user-side boundary structurally on every new proposal.

**Lens 4 (prompt scope ↔ confidence).** Personas are pre-built
constrained-scope templates; choosing which to dispatch IS the
scope-tightness call. Tension 3 above names where the two principles
pull against each other and how the multi-signal discipline resolves.

---

*Document maintained alongside [`odd-semver-pinning.md`](odd-semver-pinning.md)
and [`release-versioning-policy.md`](release-versioning-policy.md) as
methodology-tier reference for loam.*
