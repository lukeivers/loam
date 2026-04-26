# Plan — Claude-Code-corpus prompt-spine + seed docs (amendment α)

**Status:** plan (pre-dispatch). 2026-04-26.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored against HEAD:** captured at brief-dispatch
(`baseline: <sha>` in the manifest, BASELINE-as-HEAD~1 pattern per
amendments #29 / #34–#47).
**Amendment number:** unassigned at authoring; assigned at
dispatch. Plan filename family-named (`claude-code-corpus-…`) so
the path survives renumbering.
**Locked design research (governs):**
`docs/rebuild/plans/research/persona-capability-knowledge-grounding-research.md`
— hybrid-with-prompt-as-spine; four-amendment program α/β/δ/γ;
two-class corpus partition (Class A + Class B); §2.6 + §7bis.
α only.
**Sibling in-flight plan:**
`docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype.md`
— rewrites `templates/persona-template/prompt.md` (the L plan).
α composes additively onto L's prompt.md by adding **one new
named section (Capability leverage spine)** and **one new
operational rule (Lean on the corpus)**; α does not edit any of
the eleven sections L authors. Section-level composition surface
documented in §2.6 below.
**Composes on (sealed):** `primary-persona` (prompt.md
template surface from amendments #35 + L), `workspace-bootstrap`
(scaffold's persona-directory installer copies the framework
template's prompt.md verbatim — already verified by L's
AC.O.7).

---

## 1. Summary / TLDR

α ships the **prompt-spine + seed corpus** layer of the
four-amendment Claude-Code-knowledge program. After α lands:

1. The persona's `prompt.md` template carries a **Capability
   leverage spine** — a leverage rule (one paragraph) plus a
   tight capability index (≤ 1.5 k chars, one-line entries
   pointing at corpus-doc paths). The persona, on every plan
   that takes action, runs the leverage check before the first
   tool call.
2. A **two-class corpus authoring guide** lives under
   `docs/rebuild/capability-corpus/AUTHORING.md`. It defines
   the section schema for Class A (Anthropic-canonical, paired
   with each entry's `[user-intent phrasings]` overlay) and
   Class B (best-practice synthesis, paired with each entry's
   trust-marker block — `sources_count`, `validation_count`,
   `supersession_chain`, `owner_acked`).
3. **≥ 5 seed Class A docs** ship under
   `docs/rebuild/capability-corpus/claude-code/` — covering
   the highest-leverage Claude Code primitives the persona
   reaches for daily. ≥ 3 seed docs ship under
   `docs/rebuild/capability-corpus/best-practice/` covering
   patterns Luke has already articulated and that ladder
   directly to Class B entries.
4. The **prompt.md spine names the corpus paths** so the
   persona uses the Read tool to fetch detail when the user's
   prompt invokes a capability the spine names. No MCP server
   yet; β replaces the Read-by-path convention with
   `mcp__knowledge__resources/read` once the server lands.

α is **content + a prompt-section addition**; no Python source,
no Python tests beyond a static-content presence check on the
template, no behavioural change to existing sealed components.
The spine and the corpus authoring guide are workspace-template
content (the persona-template exception per L's AC.O.1 / v1.2
R16 framework-not-content rule). The corpus docs themselves
are framework-level reference material — they live under
`docs/rebuild/capability-corpus/` (not under
`primary-persona/templates/`) because they are pos-v2
artefacts that future amendments (β/δ) consume programmatically;
the workspace doesn't fork them, the framework manages them.

Sealed-component fence: `primary-persona/` (template content
only) + `docs/rebuild/capability-corpus/` (new docs tree —
outside any sealed-component fence; admitted via
universal-paths). No source edit to `workspace-bootstrap/` or
any other sealed component.

Per CLAUDE.md output convention, owner reads from §6
(decisions for owner) — every other section supports it.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this amendment satisfies:**

- **v1.0 line 152 — Non-tech users — low-friction onboarding /
  effective persona on session 1.** The spec text requires
  every interactive session to start with the primary persona
  *present and effective*. Effectiveness collapses if the
  persona doesn't know what's in its toolkit — the persona
  recommends raw-LLM workarounds when a Claude-native primitive
  exists, or fails to translate a user request because the
  primitive's name is outside its training-cut. α satisfies the
  named objective at the level the locked research's §1
  framing makes binding ("the persona's leverage discipline is
  the prime expression of the translation-layer value prop"):
  the leverage rule + capability index in prompt.md is
  always-on, every-turn behavioural posture against a current
  toolkit.
- **v1.0 Knowledge-accrual + R3 (process-of-arrival capture)
  + R5 (4-dimensional temporal model) + R6 (supersession
  refined).** The two-class corpus partition (§2.6 of the
  research) is the structural realisation: Class B's
  trust-marker rubric (`sources_count`, `validation_count`,
  `supersession_chain`) is process-of-arrival capture; both
  classes' `source_fetch_ts` / `validation_count` is the
  temporal-validity surface; Class B's `supersession_chain` is
  the supersession-refined realisation. α ships the
  authoring-guide schema for these markers; β/δ ship the
  retrieval and accrual surfaces. The schema is the binding
  shape — every seed doc α authors carries the markers, so
  later amendments inherit a clean substrate.
- **v1.0 Tiered-determinism.** Class A is layer-1 deterministic
  projection (α ships seed Class A docs in the deterministic-
  projection target shape so δ's projection refresh has a
  clean substrate). Class B is layer-2 rubric (trust-marker
  metadata is deterministic; the synthesis judgement is
  layer-3). α ships the layer boundaries as authoring-guide
  rules.
- **v1.2 R16 — Framework-not-content.** The leverage spine
  + the persona-side "Lean on the corpus" operational rule
  are workspace-supplied content scaffolded as defaults
  the workspace can edit (same exception L's amendment uses).
  The capability-corpus tree itself is framework-level
  reference (consumed by β + δ programmatically); admitted
  outside the no-personas-in-core rule because it is not
  persona prose — it is documentation of pOS-v2's external
  Claude-leverage surface.
- **VALUE_PROPOSITION's two tests (the prime objective ACs)
  — the binding outcome.**
  - **Primary-persona test (AC.PO.1):** the leverage rule
    is the prime-objective amendment. The persona's
    translation of natural-language intent into AI-effective
    execution depends on the persona knowing what execution
    paths exist *as of today*, not as of training-cut. α
    closes that gap at the always-on prompt layer (the rule
    fires every turn) and at the on-demand corpus layer
    (detail fetched when the user's prompt invokes a named
    capability). Without α the persona's Lens-1 reads are
    best-effort against stale training-cut knowledge; with
    α they are checked against the corpus.
  - **Harness test (AC.PO.2):** α adds three new toolkit
    primitives — the **Capability leverage spine** (the
    section every future persona-template authoring tool
    composes against), the **two-class corpus authoring
    guide** (the schema every future capability-doc author
    follows, including δ's deterministic projection
    transform), and the **seed corpus tree** (the substrate
    β's MCP knowledge-server reads from on startup). All
    three primitives are reusable by every later amendment
    in the program (β / δ / γ) and by future workspace
    authors who want to extend the corpus.

**Sealed-component amendment classification.** One sealed
component touched at the **template-tree exception surface**:

- `primary-persona`: `templates/persona-template/prompt.md`
  gains one new named section (the Capability leverage
  spine) plus one new operational-rule entry (the "Lean on
  the corpus" rule, sibling to L's six rules). No source
  edit to `primary-persona/src/`. Tests added under
  `primary-persona/tests/` for the static-content presence
  check.
- `workspace-bootstrap`: **no source edit.** The scaffold
  copies the framework template's prompt.md verbatim
  (verified by L's AC.O.7). The template content change is
  the only delta. AC.α.7 re-verifies this composition.

**Ordering vs the L plan — composition surface (per dispatch
note).** L authors eleven sections (five top-value-trait
sections + six operational-rule sections) per its AC.O.1. α
extends that surface additively:

- α adds one new top-level named section: **Capability leverage
  spine** — slotted between L's identity / archetype block and
  L's traits block, before any operational rule.
- α adds one new operational-rule entry: **Lean on the corpus**
  — slotted as a seventh entry under L's "Operational rules"
  section, sibling to L's six rules.

L's AC.O.1 verifies its eleven sections by marker headings;
α's verification pattern is identical (marker headings for
the new section + the new rule). The two amendments are
structurally compatible: both add named sections to the same
template; neither rewrites the other's content. **If L has
not sealed at α-dispatch time**, α's build agent reads L's
in-flight builder-plan to confirm the section-marker shape,
then authors α's content against the agreed shape (this is
not method-prescription — α composes onto L's heading
convention; the convention is L's contract).

**ODD §2.5 reverse direction.** Every code path, branch,
content artefact, and test in this amendment must trace back
to a named AC under §4. The amendment is content-heavy and
code-light — most reverse traces are
content-section → AC-content-presence-check.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

**What Claude capability does this lean on or extend?**

Three Claude-native primitives, all already-adopted in pos-v2:

1. **Claude Code's persona-prompt + agent-md projector**
   (amendment #35). The leverage spine is one new section in
   prompt.md; the same projector renders it into the agent.md
   on each rebuild. No new primitive.
2. **Claude Code's Read tool.** Pre-β, the persona fetches
   capability detail by reading the corpus-doc path via the
   Read tool. This is the cheapest possible "spine names →
   persona fetches" flow — zero infrastructure beyond what
   Claude already has. β replaces Read-by-path with
   `mcp__knowledge__resources/read`; α's spine names paths,
   not URIs, so β's substitution is one-line per spine entry.
3. **Claude Code's SessionStart `additionalContext` channel**
   (D8 of primary-persona; reinforced by L). The leverage
   rule + spine sit inside prompt.md (always-on per turn);
   they do not consume additionalContext budget at session-
   start. The capability-content stays out of additionalContext
   per L's AC46.7 (2,000-char budget).

α writes ~ 0 lines of "drive capability lookup" code — Claude
Code does that. α writes the spine into prompt.md (which Claude
reads on every turn), the authoring guide (which humans + δ's
projection transform follow), and the seed docs (which the
persona reads on demand).

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation
burden between the user's natural-language intent and AI-
effective execution?*

α is the prime-objective amendment for capability-awareness.
The locked research's §1 framing is the binding read: when
the persona plans how to take action on almost anything, it
should actively stop and think about how to best leverage
both Claude Code and the harness. Today the persona's
training-cut knowledge does not reliably know what's in the
toolkit — `/loop` and `/schedule` ship faster than
training-cut updates, pos-v2 primitives ship weekly, and
operational patterns evolve continuously. α gives the
persona an always-on rule that runs the leverage check on
every plan and a current corpus the persona can consult
when the rule fires.

The translation is concrete:

- *User says:* "set me up to get a daily briefing."
- *Spine fires:* the persona checks the leverage rule;
  consults the capability index; sees `/schedule`,
  `/loop`, background-agent-pairing entries; reads
  `docs/rebuild/capability-corpus/claude-code/schedule.md`
  via the Read tool; selects `/schedule` with the
  background-agent dispatch as the target; explains the
  choice in one sentence (per L's "Light-touch narration on
  choices" rule); does the work.

The user never picks the modality; the persona picks. The
persona's pick is checked against a current corpus, not
against training-cut memory. Translation burden absorbed by
construction.

**Harness test.** *Does this add to the toolkit the primary
persona can draw from?*

Yes — three new toolkit primitives (named in §2 above; not
re-listed). Each is consumed by every later amendment in
the program: β builds its MCP server's resources from the
corpus tree; δ's deterministic projection transform writes
to the same tree following the authoring guide; γ's dynamic
contributor reads the corpus to surface today's relevant
subset; future workspace authors extend the corpus via the
authoring guide.

### Lens 3 — ODD authoring

The plan authors eight outcome-shaped acceptance criteria
(§4) under the §2.5 reverse-direction discipline. ACs
measure observable outcome (named section present in
template, named guide present at canonical path, ≥ N seed
docs at canonical paths with named structural sections,
etc.). Method (exact prose, exact wording of the leverage
rule paragraph, exact selection of which 5–10 capabilities
to seed first, exact `[user-intent phrasings]` lists, exact
trust-marker numeric values for the seed Class B entries) is
the builder's call.

ODD §2.5 reverse-direction trace:

- The Capability leverage spine in prompt.md → AC.α.1.
- The "Lean on the corpus" operational rule in prompt.md →
  AC.α.1 (sibling to spine; tested by the same shape).
- The two-class corpus authoring guide → AC.α.2.
- Each seed Class A doc → AC.α.3.
- Each seed Class B doc → AC.α.4.
- The `[user-intent phrasings]` discipline + trust-marker
  block schemas → AC.α.5 (cross-cutting check that every
  seed doc satisfies its class's schema).
- The composition with L's prompt.md surface → AC.α.6
  (verifies L's eleven sections still present; α adds, does
  not subtract).
- The scaffold-passthrough verification → AC.α.7.
- Negative-shape (no capability content under any path
  outside `docs/rebuild/capability-corpus/` and the
  template-tree exception) → AC.α.8.

No platform branches, no defensive `if`s without backing AC,
no "might be useful later" surface.

---

## 4. Acceptance criteria (AC.α.x)

Each AC maps to at least one test or content-presence check.
Naming follows the AC.α.* family (α for "alpha — capability
spine + seed corpus") to avoid collision with AC.O.* (L plan)
and prior AC.A.* / AC35.* / AC36.* / AC46.* / AC47.* families.

### AC.α.1 — Capability leverage spine + "Lean on the corpus" rule present in prompt.md template

The framework template
`primary-persona/templates/persona-template/prompt.md` carries
a new top-level named section **Capability leverage spine**
containing two sub-blocks: a *Leverage rule* paragraph (the
declarative rule the persona runs on every plan that takes
action — one paragraph, ≤ 250 words, naming both the
Claude-Code-leverage and harness-leverage halves of the rule
per CLAUDE.md Lens 1) and a *Capability index* (one-line
entries pointing at corpus-doc paths under
`docs/rebuild/capability-corpus/`; ≥ 8 entries; ≤ 1500 chars
total for the index block).

The template's existing operational-rules section (six rules
authored by L) carries one additional sibling rule: **Lean on
the corpus** — a one-paragraph rule (≤ 150 words) that names
the on-demand fetch convention (the persona reads
corpus-doc paths via the Read tool when the spine names a
capability the user's prompt invokes; once β lands the MCP
server, the rule's text gets a one-line edit substituting
`mcp__knowledge__resources/read` for the Read tool).

**Test shape:** load the template's `prompt.md` text; assert
**Capability leverage spine** marker heading present; assert
*Leverage rule* sub-marker present; assert *Capability index*
sub-marker present; assert ≥ 8 path entries in the index
matching the regex `docs/rebuild/capability-corpus/.+\.md`;
assert *Lean on the corpus* operational-rule marker present
in the operational-rules section. (Outcome-shaped: presence
of named markers + count of index entries; not method-
prescriptive about exact prose.)

**Maps to:** v1.0 line 152, v1.2 R16, AC.PO.1, AC.PO.2.

### AC.α.2 — Two-class corpus authoring guide present at canonical path

The file `docs/rebuild/capability-corpus/AUTHORING.md`
exists and carries:

- A *Class A — Anthropic-canonical reference* section naming
  the deterministic-projection contract (each Class A doc is
  projected from a canonical upstream source; LLM judgement
  enters only at the curated `[user-intent phrasings]`
  overlay); naming the required sections per Class A doc
  (a *Surface* description, an *Inputs/outputs* contract, a
  *Composition notes* block, a `[user-intent phrasings]`
  list, a *Source* metadata block carrying `source_url` +
  `source_fetch_ts`).
- A *Class A-prime — pos-v2 harness primitives* section
  naming the same shape applied to pos-v2 component docs
  (sourced from `docs/rebuild/components/<name>/` rather
  than Anthropic).
- A *Class B — best-practices wisdom* section naming the
  synthesis-and-curation contract; naming the required
  sections per Class B doc (a *Pattern* description, a
  *Conditions* block — when this pattern applies, a
  *Failure modes* block — what this pattern guards against,
  one or more `[primitive: <name>]` cross-references to
  paired Class A entries, a *Trust marker* block carrying
  `sources_count`, `validation_count`, `supersession_chain`,
  `owner_acked`).
- A *Cross-class* section naming the paired-fetch
  convention (when a Class A primitive has Class B entries
  attached via `[primitive: <name>]` cross-reference, the
  persona fetches both before planning).
- A *No-cross-class-write* invariant — Class A's
  deterministic refresh (δ) never writes to Class B; Class
  B's accrual channels never write to Class A. Documented
  here so β's plan-author has the structural rule when
  authoring the resource-path partition.

**Test shape:** read the file; assert each named top-level
marker present (`Class A`, `Class A-prime`, `Class B`,
`Cross-class`, `No-cross-class-write`); assert each named
sub-marker for the per-class schemas (`[user-intent
phrasings]`, `Trust marker`, `[primitive: <name>]` etc.)
appears in the relevant section.

**Maps to:** v1.0 Knowledge-accrual, v1.0 R3, v1.0 R5,
v1.0 R6, v1.0 Tiered-determinism, AC.PO.2.

### AC.α.3 — ≥ 5 seed Class A docs covering highest-leverage primitives

At least five files exist under
`docs/rebuild/capability-corpus/claude-code/` (and/or under
`docs/rebuild/capability-corpus/harness/` for Class A-prime
seeds), each satisfying the Class A schema from AC.α.2.

**Bounded list-of-candidates flagged for builder selection
(not method-prescription — these are the primitives the
locked research §2.1 + §2.4 names as highest-leverage; the
builder picks ≥ 5 of them or substitutes a primitive of
equal or greater leverage with rationale recorded in the
builder-plan):**

- `/schedule` (cron-shaped scheduler skill)
- `/loop` (self-pacing recurring scope)
- background-agent dispatch (Task tool, run_in_background,
  Monitor)
- hook events (SessionStart, UserPromptSubmit,
  PreToolUse, Stop, SubagentStop)
- MCP server registration + tool-call surface
- subagent / Agent tool dispatch shape
- skills marketplace + custom skill authoring
- settings.json hooks/permissions/env
- Telegram-interface inbound/outbound (Class A-prime —
  pos-v2 primitive)
- memory-system MCP tools (Class A-prime — pos-v2
  primitive)

**Test shape:** glob
`docs/rebuild/capability-corpus/claude-code/*.md` +
`docs/rebuild/capability-corpus/harness/*.md`; assert
combined count ≥ 5; for each file, assert each Class A
section marker present per the schema in AC.α.2; assert
non-empty `[user-intent phrasings]` list (≥ 3 phrasings);
assert `source_url` + `source_fetch_ts` populated (non-
empty, non-placeholder).

**Maps to:** v1.0 line 152, v1.0 Tiered-determinism,
AC.PO.1, AC.PO.2.

### AC.α.4 — ≥ 3 seed Class B docs covering owner-articulated patterns

At least three files exist under
`docs/rebuild/capability-corpus/best-practice/`, each
satisfying the Class B schema from AC.α.2.

**Bounded list-of-candidates flagged for builder selection
(not method-prescription — these are patterns Luke has
already articulated in `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`
that ladder cleanly to seed Class B entries; the builder
picks ≥ 3 of them or substitutes patterns of equal or
greater articulation with rationale recorded in the builder-
plan):**

- "background agents by default for multi-artefact
  authoring or ~30 s+ generation"
- "fire-and-forget for cost — don't pause on cost ceilings
  the user has already authorised"
- "no parallel-memory chaos — `source_description` is the
  partition, not separate substrates"
- "anti-deskilling pairing on auto-create — owner ack
  before merge for novel additions"
- "scope-only dispatch — no method prescription in agent
  briefs"
- "always specify WD in dispatches"
- "verify the dispatch is the right action before sending
  it"

**Test shape:** glob
`docs/rebuild/capability-corpus/best-practice/*.md`;
assert count ≥ 3; for each file, assert each Class B
section marker present per the schema in AC.α.2; assert
≥ 1 `[primitive: <name>]` cross-reference present; assert
trust-marker block carries `sources_count` (integer ≥ 1),
`validation_count` (integer ≥ 0), `supersession_chain`
(string, possibly empty), `owner_acked` (boolean).

**Maps to:** v1.0 line 152, v1.0 Knowledge-accrual,
v1.0 R3, AC.PO.1, AC.PO.2.

### AC.α.5 — Schema discipline: every seed doc satisfies its class's schema

This is the cross-cutting structural check verifying that
AC.α.3 + AC.α.4 are not satisfied by minimum-viable token
content. For every file under
`docs/rebuild/capability-corpus/claude-code/` +
`harness/` + `best-practice/`: every required marker from
AC.α.2's schema is present; every required field is non-
empty; no schema field carries the literal prompt text from
the authoring guide (the "Describe, in one sentence, …"
anti-pattern from L's AC.O.6).

**Test shape:** for each file in the corpus tree (excluding
`AUTHORING.md`), determine its class from its parent
directory; load the class schema; assert every required
marker present; assert every required field non-empty
(non-whitespace); assert no field equals the placeholder
prose from `AUTHORING.md`.

**Maps to:** v1.0 Knowledge-accrual, v1.0 Tiered-
determinism, ODD §2.5 reverse-direction (no orphan
schema-incomplete content).

### AC.α.6 — L's eleven sections in prompt.md remain unchanged in shape

If L has sealed at α-dispatch time, the post-α prompt.md
template still carries every one of L's eleven named
sections (five top-value-trait headings + six operational-
rule headings) as defined by L's AC.O.1. α's additions
(the Capability leverage spine + the seventh operational-
rule entry "Lean on the corpus") slot in additively without
removing or renaming any L section.

If L has **not** sealed at α-dispatch time, this AC reduces
to a structural composition statement in α's builder-plan
(the builder reads L's in-flight surface and authors
against the agreed section-heading convention). The AC's
test is then deferred to L+α-merge time.

**Test shape:** load the template's `prompt.md` text;
assert every L-named section heading present (the five
trait headings + the six rule headings + L's identity /
archetype / voice / proposal-moment / failure-guards
sections per L's AC.O.1). Combined with AC.α.1, this
verifies α-additions sit alongside L-content rather than
displacing it.

**Maps to:** v1.0 line 152, v1.2 R16, AC.PO.1.

### AC.α.7 — Workspace scaffold lands the new template content unchanged at default-handle path

A workspace bootstrap run via `run_first_run_scaffold`
against a tmpfs `pos_root` produces
`<workspace>/personas/<handle>/prompt.md` whose body equals
the framework template's `prompt.md` body verbatim
(modulo line-endings). No source edit to
`workspace-bootstrap/` is required for this AC to pass.
Mirrors L's AC.O.7; α's verification is the same shape
applied to the post-α template content.

**Test shape:** invoke `run_first_run_scaffold` with a
`tmp_path` workspace; assert
`<workspace>/personas/<handle>/prompt.md` exists and
equals the framework template's bytes; diff
`workspace-bootstrap/` against pre-amendment state; assert
no source edit (negative-shape — the AC's truth depends on
no scaffold source change).

**Maps to:** v1.0 line 152, AC.PO.1.

### AC.α.8 — No capability content outside the corpus tree + template-tree exception

Every file matching the capability-content shape (Class A
or Class B schema markers, the leverage spine markers, the
authoring-guide markers) lives under one of:

- `primary-persona/templates/persona-template/prompt.md`
  (the template-tree exception per v1.2 R16, hosting the
  spine + the operational rule),
- `docs/rebuild/capability-corpus/AUTHORING.md` (the
  authoring guide),
- `docs/rebuild/capability-corpus/<class-dir>/*.md` (the
  seed docs).

No other file in the repo carries capability-content
schema markers.

**Test shape:** grep the repo (excluding the three admitted
locations) for the schema marker strings (`Capability
leverage spine`, `[user-intent phrasings]`, `Trust marker`,
etc.); assert zero matches outside the admitted paths.
Negative-shape — verifies α did not leak content to
unintended locations and that no pre-existing content
collides with the new schema names.

**Maps to:** v1.2 R16 (framework-not-content), ODD §2.5
reverse-direction (no orphan content paths).

### AC.α.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes
only under:

- `primary-persona/templates/persona-template/prompt.md`
  (the spine + new operational rule),
- `primary-persona/tests/` (new test files for AC.α.1,
  AC.α.6, AC.α.7),
- `docs/rebuild/capability-corpus/` (new tree — authoring
  guide + seed docs),
- `docs/rebuild/plans/claude-code-corpus-prompt-spine-and-seed-docs*`
  (this plan + manifest + builder-plan),
- universal-paths admissions per amendment #22 ruling #3.

`primary-persona/src/` source is **not** in scope and not
admitted (α is template-content + tests only). Sealed-
component source outside `primary-persona/` is never
admitted by this amendment.

If the build agent finds a `primary-persona/src/` edit is
required (e.g., a renderer change to handle a new
substitution token), that is a halt trigger (§9). The
plan-author's audit says no `src/` edit is needed: the
spine is plain markdown sections; the agent_md.py renderer
already handles arbitrary prompt.md content per amendment
#35.

---

## 5. Behaviour-count check (ODD §3.3 forward)

Declared behaviours (§1):

| Behaviour | Criterion/criteria |
|---|---|
| 1. Capability leverage spine + "Lean on the corpus" rule in prompt.md | AC.α.1, AC.α.6 |
| 2. Two-class corpus authoring guide at canonical path | AC.α.2 |
| 3. ≥ 5 seed Class A + ≥ 3 seed Class B docs satisfying class schemas | AC.α.3, AC.α.4, AC.α.5 |
| 4. Scaffold passthrough preserved (no source edit) | AC.α.7 |
| cross-cutting | AC.α.8 (no leak), AC.α.S (seal diff) |

Four declared behaviours; eight ACs cover them plus two
cross-cutting invariants. No method-in-AC.

Reverse-direction trace:

- New section *Capability leverage spine* in
  `primary-persona/templates/persona-template/prompt.md` →
  AC.α.1, AC.α.6.
- New operational rule *Lean on the corpus* in
  `primary-persona/templates/persona-template/prompt.md` →
  AC.α.1, AC.α.6.
- `docs/rebuild/capability-corpus/AUTHORING.md` content →
  AC.α.2.
- `docs/rebuild/capability-corpus/claude-code/*.md` +
  `docs/rebuild/capability-corpus/harness/*.md` content →
  AC.α.3, AC.α.5.
- `docs/rebuild/capability-corpus/best-practice/*.md`
  content → AC.α.4, AC.α.5.
- `primary-persona/tests/test_*` for the static-content
  presence checks → their named AC.α.x.
- Negative-shape (no capability content outside admitted
  locations) → AC.α.8.

No code paths, no platform branches, no defensive `if`s.
α is content + a single static-content presence test
suite.

---

## 6. Decisions for owner

The plan-author rules every decision the locked research
already locked. The following four are the only items
requiring owner ruling — surfaced as genuine uncertainty
per the "don't ask Luke to read the doc" feedback rule.

### D-OWNER.1 — Sequencing relative to the L plan (onboarding-rewrite)

**The question.** Does α land **before**, **after**, or
**concurrent with** the L plan
(`primary-persona-conversational-onboarding-and-default-archetype.md`)?

**The trade-off.** L is the onboarding-rewrite + default-
archetype amendment; its scope rewrites the same prompt.md
template α extends. Three orderings:

- **(a) L first, then α.** L lands its eleven sections; α
  adds two additional named markers (the spine section + the
  "Lean on the corpus" rule). α's build agent reads L's
  sealed prompt.md and slots its content in additively.
  Cleanest composition; no race on the same template file.
  Cost: α waits for L to seal.
- **(b) α first, then L.** α lands the spine + rule against
  the *current* prompt.md (the example-template prose, not
  L's archetype). L then rewrites the template whole-cloth
  and must re-author α's content into its new shape.
  Doubles α's content authoring (lands twice). Cost: α
  authoring waste.
- **(c) Concurrent — both run in parallel.** Per the
  serialize-amendment-builds feedback rule (race on
  `index.lock`, `pos-amend`, tests), concurrent builds in
  the same working tree are disallowed without worktree
  isolation. Even with worktrees, both amendments edit the
  same template file. Merge conflict is structurally
  guaranteed.

**Recommendation: (a) L first, then α.** L is closer to
dispatch (its plan is complete; this α plan is being
authored alongside but β/δ depend on α's corpus tree, not
on its prompt.md spine, so L's prompt.md surface is the
binding ordering constraint). α's build agent reads L's
sealed template at α-dispatch, slots the spine in
additively, runs the AC.α.6 verification against L's
eleven sections.

### D-OWNER.2 — Fence: persona-template prompt.md edit OK, or strictly off-limits?

**The question.** AC.α.1 places the leverage spine + the
new operational rule inside
`primary-persona/templates/persona-template/prompt.md`.
This is the same template L is rewriting. **Is the build
agent permitted** to touch
`primary-persona/src/` (the renderer / loader / projector
code) if a genuinely-required source change surfaces (e.g.,
the spine's `Capability index` block needs a new
substitution-token shape that the existing
`agent_md.to_agent_md` renderer doesn't support)?

**The trade-off.** Strict off-limits keeps the fence narrow
(template-content-only) and the seal-diff clean. Permissive
(with halt-and-confirm) lets the build agent close a small
surface gap if discovered.

The plan-author's audit (§3 Lens 1 + §4 AC.α.S) says **no
src edit is needed**: the spine is plain markdown sections;
the index entries are plain markdown bullet-list lines
pointing at corpus paths; the renderer (per amendment #35)
already passes arbitrary prompt.md content through verbatim.

**Recommendation: strict off-limits.** Halt trigger §9.1.
The build agent must surface to Luke if a `src/` edit
seems required, not silently widen the fence. If the
recommendation is wrong, Luke rules at halt time.

### D-OWNER.3 — Should seed Class A docs ship with **populated** `source_fetch_ts` or with placeholder timestamps that δ replaces on first projection?

**The question.** AC.α.3 requires each seed Class A doc to
carry a non-empty non-placeholder `source_url` +
`source_fetch_ts`. Two options:

- **(a) Populated at α-author-time.** The build agent
  fetches each canonical source once at authoring-time,
  records the fetch timestamp, projects the content
  manually following the authoring guide. δ's later
  scheduled refresh re-projects from the same source and
  updates the timestamp. **Cost:** the build agent does
  one round-trip per seed doc to fetch the canonical
  source (web fetch); ~5 fetches at ~10 s each = ~1 min.
- **(b) Placeholder timestamps.** Seed docs ship with
  `source_fetch_ts: "<deferred-to-δ-projection>"` literal;
  AC.α.3's "non-empty non-placeholder" check is relaxed
  to "non-empty" only. δ's first projection populates the
  timestamps. **Cost:** AC.α.3 is structurally weaker;
  the corpus ships with content claiming to be a
  projection of an upstream source it has not actually
  read.

**Recommendation: (a).** The seed corpus is supposed to
demonstrate the projection pattern; shipping with
unverified content undermines the demonstration. The web-
fetch round-trip is small (≤ 1 min total). The seed docs
become the calibration set δ's projection transform is
tested against — if α's manual projections diverge from
δ's automated projections, that surfaces δ's transform-
fidelity problem at δ-build-time rather than later. (a)
also matches Luke's "test theories before acting on them"
trait: the seed doc *claims* to be projected from a source;
verifying the source on first read is the operational
expression of that trait.

### D-OWNER.4 — Should the corpus-tree directory layout match the β knowledge-server's eventual resource-URI partition exactly, or is it allowed to diverge?

**The question.** AC.α.3 / AC.α.4 / AC.α.5 reference three
sub-directories under `docs/rebuild/capability-corpus/`:
`claude-code/` (Class A), `harness/` (Class A-prime),
`best-practice/` (Class B). The locked research §7.2
proposes β's MCP server's resource URIs as
`capability:claude-code:<name>`, `capability:harness:<name>`,
`capability:best-practice:<topic>`. Two options:

- **(a) Directory layout mirrors the URI partition
  exactly.** Each seed doc's path is
  `docs/rebuild/capability-corpus/<class-dir>/<name>.md`
  and the URI under β becomes
  `capability:<class-dir>:<name>` mechanically. β's
  server reads from the same disk layout it serves;
  one-to-one path↔URI mapping; no translation. **Cost:**
  the directory naming is locked to β's partition; if β
  later refines the partition (e.g., splits Class A into
  `anthropic/` and `claude-code/`), α's directory layout
  needs migration.
- **(b) Directory layout is α-internal; β translates at
  load time.** α uses the layout that's most natural for
  human authoring (which may or may not match β's URI
  shape); β adapts at startup. **Cost:** β's plan-author
  has more decision surface; the path↔URI mapping
  becomes a method-level concern at β-build-time rather
  than a structural invariant.

**Recommendation: (a) match exactly.** Locked-research
§7.2 already names the partition; matching α's directories
to it locks the structural invariant at α-time and reduces
β's decision surface. If β later refines, that's a
migration amendment (small, content-move-only, no
behaviour change). The cleaner immediate-term layout is
worth the locked partition. Builder records this as a
structural invariant in the authoring guide so future
contributors know not to invent a fourth class without
co-amending β's partition.

---

## 7. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence — `primary-persona/` template-content +
   `docs/rebuild/capability-corpus/` only.** Source under
   `primary-persona/src/` is **off-limits** (D-OWNER.2
   rules; halt §9.1 if seemingly needed). Tests under
   `primary-persona/tests/` for the static-content
   presence checks. Template content under
   `primary-persona/templates/persona-template/prompt.md`
   only (not `contract.yaml` — α does not touch contract).
   New tree under `docs/rebuild/capability-corpus/`. No
   source edit to `workspace-bootstrap/` or any other
   sealed component.
3. **Reversibility.** Fully reversible at the corpus +
   template surface. The capability-corpus tree can be
   removed wholesale in one commit; the prompt.md spine
   + the new operational rule can be removed in one
   commit. No external state changes (no migrations,
   no on-disk file formats invented beyond markdown).
4. **No new runtime deps.** Permitted runtime deps per
   the primary-persona proposal apply unchanged. Test-
   only deps per STATE.md rule #8.
5. **No persona content shipped from pOS core outside
   the template-tree exception.** The leverage spine +
   the new operational rule live **only** at
   `primary-persona/templates/persona-template/prompt.md`
   (the existing template-tree exception). The
   capability-corpus tree under `docs/rebuild/` is
   **framework-level reference**, not persona prose;
   admitted because it is documentation of pOS-v2's
   external Claude-leverage surface, consumed by β + δ
   programmatically.
6. **No new top-level objective.** Per the locked
   research §7bis.4 + §9.4, the work realises existing
   v1.0 objectives (Knowledge-accrual + Tiered-
   determinism + Non-tech-users) without introducing
   new top-level objectives. Halt §9.5 fires if the
   build surfaces a need for a new top-level objective.
7. **Two-class partition is structural, not advisory.**
   The authoring guide names the No-cross-class-write
   invariant (Class A's δ-projection refresh never
   writes to Class B; Class B's accrual channels never
   write to Class A); seed docs respect the boundary.
   This sets up β's resource-path partition as a
   structural invariant rather than a documentation rule.
8. **Authority bound.** Builder may refine: exact prose
   wording in the leverage rule paragraph (provided the
   AC.α.1 marker headings are present + the rule names
   both Claude-Code-leverage and harness-leverage halves);
   exact selection of which 5–10 capabilities to seed
   first (provided AC.α.3 + AC.α.4 minimums hit and the
   selection rationale lands in the builder-plan); exact
   `[user-intent phrasings]` lists per Class A doc; exact
   trust-marker numeric values for seed Class B entries
   (provided the schema fields are populated non-
   placeholder); exact directory layout under
   `docs/rebuild/capability-corpus/` (provided D-OWNER.4's
   ruling is followed). Builder may **not** override the
   locked design decisions from the research, the four
   owner-ruled decisions D-OWNER.1 through D-OWNER.4, or
   the AC outcomes.
9. **CDC adherence.** Plan-before-code, background-agent
   default, scope-only dispatch, the three amendment-
   dispatch speedups (narrow test scope, skip pre-seal
   full rerun, inline methodology snippets).
10. **`pos-amend apply --dry-run` green** is a hard prereq
    per amendment #22.
11. **L ordering** per D-OWNER.1: this amendment composes
    onto L's prompt.md template content; if L has not yet
    sealed at α-dispatch time, the build agent reads L's
    in-flight builder-plan to confirm the section-marker
    convention before authoring α's additions. If L
    cannot be reached for the convention, halt §9.4.
12. **No β / δ / γ scope creep.** β (MCP knowledge-
    server), δ (currency mechanism — Class A
    deterministic projection refresh + Class B
    community-survey channel), γ (dynamic session-start
    contributor) are out of scope (§8). Halt §9.6 if
    the build surfaces a temptation to land any of them
    inside α.

---

## 8. Out of scope (explicit)

The following are **out of scope for α** by locked design.
Named explicitly so the build agent does not drift into
them. Each is named-amendment in the four-amendment
program; α leaves the room for them to land later cleanly.

- **β — MCP knowledge-server (two-class-aware).** New
  top-level package `knowledge-server/` exposing
  `resources/list` + `resources/read` + `search(query)`
  with Class A / A-prime / B partition. **Out of scope
  for α.** α's seed corpus tree is the substrate β reads
  from; α does not author β's server, its sqlite-FTS5
  index, its embedding store, or the `BestPracticeMirrorContributor`
  Stop-hook subscriber. Tracked separately.
- **δ — Currency mechanism (Class A deterministic
  projection refresh + Class B community-survey
  channel + internal-Stop-hook accrual + user-driven
  capture).** **Out of scope for α.** α ships seed docs
  authored manually following the authoring guide; α
  does not ship the `/schedule`-bound projection
  transform, the per-source manifest schema in
  `personas/<handle>/capability-sources.yaml`, the
  community-survey prompt, or any Stop-hook subscriber.
  Tracked separately.
- **γ — Dynamic session-start contributor.** A new
  contributor in `primary-persona/src/` registered
  against D8's session-level surface emitting "given
  recent scope-of-work activity, the capabilities most
  likely relevant today are…". **Out of scope for α.**
  α's spine is always-on prompt.md content; γ is the
  contextual-relevance overlay added once the corpus is
  stable. Tracked separately.
- **Authoring the full corpus.** α ships ≥ 5 seed Class
  A + ≥ 3 seed Class B; the full inventory (~50–70
  docs per the locked research §2.5) lands incrementally
  through δ's accrual channels and ongoing manual
  authoring. The seed count is a demonstration of the
  pattern, not full coverage.
- **MCP tool calls in α's spine.** Pre-β, the spine
  names corpus paths (`docs/rebuild/capability-corpus/<class>/<name>.md`)
  consumed via the Read tool. **The spine does not yet
  reference `mcp__knowledge__resources/read`** — that's
  a one-line edit at β-time.
- **Activity-type → capability mapping.** Used by γ;
  workspace-authored. **Out of scope for α.**
- **Lens-1-enforcement at research-plan-author time.**
  Idea 1 / Step 3's structural-enforcement gate that
  refuses research plans without Lens-1 sections.
  Separate, complementary workstream. **Out of scope
  for α.**
- **Spec amendment naming capability-awareness
  explicitly.** Recommended by the locked research §9.4
  as a docs-only addendum; viable to land inside α as
  an additional content artefact, but the plan-author
  judges this as separable workstream and **does not
  include it in α's scope.** If owner prefers it bundled,
  surface at D-OWNER (not currently named).
- **MCP `.mcp.json` registration of a knowledge-server.**
  Lands at β; α does not amend the `mcp_json_writer.py`
  surface from amendment #47.
- **Workspace-bootstrap source edits.** Scaffold
  composition surface is unchanged; only the framework-
  template content + the new corpus tree changes.
  AC.α.7 verifies no scaffold source edit is needed.

---

## 9. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond
   `primary-persona/` template-content +
   `docs/rebuild/capability-corpus/`.** Any required
   source edit to `primary-persona/src/`,
   `workspace-bootstrap/`, or any other sealed component
   → halt. Per D-OWNER.2 the strict ruling is "halt if
   any src edit seems required, do not silently widen."
2. **L plan composition collision.** If L has sealed
   and L's eleven sections cannot be additively extended
   by the spine + the seventh operational rule (e.g., L's
   chosen heading convention turns out to forbid same-
   level additions, or the marker syntax collides) →
   halt. The locked research §7.1 + this plan §2.6
   declare α/L composable; if the build surfaces a
   structural conflict, halt-and-surface, do not silently
   re-author L's content.
3. **L plan not sealed at α-dispatch time AND L's
   in-flight builder-plan is not reachable.** Per
   D-OWNER.1 + hard constraint #11, α composes onto L's
   convention; without the convention reachable, halt.
4. **The corpus-tree paths conflict with an existing
   tree.** Per AC.α.8, the corpus tree is
   `docs/rebuild/capability-corpus/`; if a pre-existing
   tree under that path exists with conflicting
   schema-marker content → halt.
5. **An ODD-violating shape becomes strongly required**
   (method-in-AC, non-objective code path, silent
   exception). Halt; owner rules.
6. **The build surfaces a need for β / δ / γ scope to
   land inside α** (e.g., AC.α.3 cannot be tested
   without β's `search` tool). Per hard constraint #12,
   halt; owner rules on splitting α / re-scoping or
   pulling β surface forward.
7. **`pos-amend apply --dry-run` red** — halt.
8. **A test for AC.α.1–AC.α.S cannot be written
   deterministically** — halt.
9. **The locked research's design decisions appear
   contradicted** by something the build surfaces (e.g.,
   the two-class partition reads ambiguous for a seed
   doc the builder is authoring) — halt and surface;
   do **not** re-derive.
10. **D-OWNER.3's web-fetch for `source_fetch_ts`
    population fails** for ≥ 1 of the seed Class A
    sources (network unreachable, source moved, etc.).
    Halt; owner rules between (a) wait + retry, (b)
    fallback to placeholder timestamp for that one
    doc, (c) substitute a different seed primitive.
11. **A required new top-level objective surfaces.**
    Per hard constraint #6 + locked research §7bis.4 +
    §9.4 the work realises existing v1.0 objectives. If
    the build surfaces a gap that genuinely requires a
    new top-level objective → halt; owner rules.
12. **Amendment-dispatch wall-time exceeds 60 minutes**
    (rough estimate per the duration-rubric: small-
    scope content authoring + ≤ 8 seed docs + a single
    template additive section + a small test suite →
    30–60 min) — halt with current state. Owner rules
    on split vs push-through.

---

## 10. Bookkeeping (`pos-amend` manifest stub)

The manifest is authored at brief-dispatch time once the
amendment number is finalised. Stub:

```yaml
schema_version: 1
amendment:
  number: <assigned-at-dispatch>
  slug: claude-code-corpus-prompt-spine-and-seed-docs
  title: "Claude-Code-corpus prompt-spine + ≥ 5 seed docs (amendment α of the four-amendment knowledge program)"

# BASELINE captured at brief-dispatch.
baseline: <captured-at-dispatch>
plan: docs/rebuild/plans/claude-code-corpus-prompt-spine-and-seed-docs.md

components:
  - name: primary-persona
    seal_test: primary-persona/tests/test_no_sealed_amendments.py
    sidecar: primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes:
      - docs/rebuild/capability-corpus/

# Universal admissions per amendment #22 ruling #3.
universal_paths:
  prefixes:
    - docs/rebuild/plans/
    - docs/rebuild/plans/research/
    - docs/rebuild/capability-corpus/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md
    - docs/rebuild/STATE.md
    - docs/rebuild/VALUE_PROPOSITION.md

narrative:
  target: primary-persona/seals/SEAL_COMMIT.capability-spine-and-seed-corpus
  body: |
    # Amendment <N> — Claude-Code-corpus prompt-spine + seed docs (α)
    ...
    # Body authored at seal time; describes:
    #  - prompt.md spine (Capability leverage spine section
    #    + Lean-on-the-corpus operational rule) added
    #    additively to L's eleven sections
    #  - two-class corpus authoring guide at
    #    docs/rebuild/capability-corpus/AUTHORING.md
    #  - ≥ 5 seed Class A docs under
    #    docs/rebuild/capability-corpus/claude-code/ +
    #    /harness/
    #  - ≥ 3 seed Class B docs under
    #    docs/rebuild/capability-corpus/best-practice/
    #  - α of the four-amendment program (β/δ/γ named
    #    out-of-scope; the corpus tree is the substrate
    #    β consumes)
```

---

## 11. Risks

1. **Risk: the spine in prompt.md doesn't survive Claude
   Code's prompt-compaction.** *Mitigation:* per L's risk
   #1 the same applies — prompt.md is reloaded on every
   session start; compaction within a session may
   truncate it, but the identity-anchor block (per
   amendment #35's renderer) preserves the persona's
   name and the contract reference. Worst case: persona
   forgets the spine mid-session; first turn after
   compaction reloads prompt.md via SessionStart.
   Bounded.
2. **Risk: seed docs go stale before β + δ ship.** α's
   seeds are projected manually from canonical sources at
   α-author-time (per D-OWNER.3 recommendation (a));
   between α and δ, those seeds may go stale (Anthropic
   ships features faster than training-cut). *Mitigation:*
   the seed count is small (≥ 5 + ≥ 3); δ's first
   projection refreshes them; pre-δ staleness is bounded
   by δ's wall-clock timeline (~1–2 weeks per the locked
   research §7.3). Acceptable risk per the prime-
   objective trade-off (better a fresh-now corpus going
   stale than no corpus at all).
3. **Risk: the L plan's eleven sections shift before α's
   build.** L is in-flight at α-authoring time. If L's
   final section-headings differ from what α composes
   against, AC.α.1 + AC.α.6 fire. *Mitigation:* per
   D-OWNER.1 + hard constraint #11, α's build agent
   reads L's sealed (or in-flight) heading convention
   before authoring; halt §9.2 / §9.3 if the convention
   is unreachable or changes structurally.
4. **Risk: the corpus tree directory layout collides
   with β's eventual partition.** Per D-OWNER.4
   recommendation (a), α's directories match β's URI
   partition exactly; if β's plan-author later refines
   the partition (e.g., adds a fourth class), a
   migration amendment moves the seed docs. *Mitigation:*
   the migration is content-only (file moves); no
   behaviour change.
5. **Risk: corpus authoring becomes a long tail.** The
   locked research §2.5 names ~50–70 docs at full
   coverage; α ships ≥ 5 + ≥ 3. If full coverage is
   never reached, the persona's leverage check may miss
   primitives the corpus doesn't cover. *Mitigation:*
   δ's accrual channels (community-survey + internal
   Stop-hook + user-driven) are designed to grow the
   corpus over time. α's seed count is a demonstration
   of the pattern, not full coverage; full coverage is
   the program's emergent outcome, not α's deliverable.
   Acceptable per the four-amendment program's design.
6. **Risk: the four-decision count surprises Luke.** The
   plan-author surfaces only genuinely uncertain
   decisions (per the feedback rule). All four are real
   (sequencing, fence narrowness, source-fetch policy,
   directory layout). *Mitigation:* each is a single
   recommendation with a short rationale; Luke can rule
   from §6 without reading anything else.
7. **Risk: workspace owners customise prompt.md and
   delete the spine.** A power-user editing prompt.md
   may delete the Capability leverage spine section
   (treating it as boilerplate). *Mitigation:* same as
   L's risk #4 — the spine is best-default, not
   framework-required. A user who deletes it is
   signalling intent — they want a different leverage
   shape. The framework doesn't re-inject. Acceptable;
   matches "workspace owns its prose."

---

## 12. Implementation order (suggested — builder's call to refine)

Per scope-only-dispatch CDC, this section is advisory; the
builder authors the actual order in their builder-plan.

1. Read session-start corpus per CLAUDE.md.
2. Read locked research + L plan + this plan.
3. Verify D-OWNER.1 sequencing — has L sealed? If yes,
   read its sealed prompt.md. If no, read its in-flight
   builder-plan; confirm section-heading convention.
4. Write builder-plan to
   `docs/rebuild/plans/claude-code-corpus-prompt-spine-and-seed-docs.builder-plan.md`
   naming files, exact spine prose, exact selection of
   ≥ 5 seed Class A primitives + ≥ 3 seed Class B
   patterns + selection rationale, exact AC test names.
5. Land the corpus authoring guide at
   `docs/rebuild/capability-corpus/AUTHORING.md`
   (AC.α.2).
6. For each selected seed Class A primitive: web-fetch
   the canonical source (per D-OWNER.3 (a)); project
   into the Class A schema; record `source_url` +
   `source_fetch_ts`; land the file at
   `docs/rebuild/capability-corpus/<class-dir>/<name>.md`
   (AC.α.3, AC.α.5).
7. For each selected seed Class B pattern: synthesise
   from MEMORY.md / locked-research material; populate
   trust-marker block; land the file at
   `docs/rebuild/capability-corpus/best-practice/<topic>.md`
   (AC.α.4, AC.α.5).
8. Land the prompt.md spine + the seventh operational-
   rule entry in the framework template
   `primary-persona/templates/persona-template/prompt.md`
   (AC.α.1, AC.α.6).
9. Land the test surface — AC.α.1 through AC.α.8 +
   AC.α.S.
10. Run touched-component test scope
    (`primary-persona/tests/`).
11. Cross-component seal-diff per amendment-dispatch
    CDC: every other sealed component's
    `test_no_sealed_amendments.py` + hands-off-
    lifecycle's `test_cross_cutting.py` H19.
12. `pos-amend apply --dry-run` green; amendment commit;
    `pos-amend seal --plan-doc <abs-path>` for the seal
    commit.
13. Post-seal: backfill the amendment + seal SHAs into
    the plan-doc's method-decision register.

---

## 13. References

- Locked research:
  `docs/rebuild/plans/research/persona-capability-knowledge-grounding-research.md`
- Sibling in-flight plan (L):
  `docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype.md`
- VALUE_PROPOSITION (prime objective):
  `docs/rebuild/VALUE_PROPOSITION.md`
- ODD methodology:
  `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- Existing template:
  `primary-persona/templates/persona-template/prompt.md`
- Existing renderer:
  `primary-persona/src/agent_md.py` (amendment #35)
- Existing scaffold:
  `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`
- Sibling amendment #35 (renderer + template surface):
  `docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding.md`
- Sibling amendment #36 (workspace-bootstrap scaffold):
  `docs/rebuild/plans/amendment-36-workspace-bootstrap-persona-scaffold.md`
- Sibling amendment #47 (`.mcp.json` writer — surface β
  later extends):
  `docs/rebuild/plans/amendment-47-workspace-local-mcp-json-writer.md`
- FUTURE_IDEAS Idea 1 (the four-step three-lens
  enforcement programme; Step 1 = the capability map
  α + β + δ + γ realises):
  `docs/rebuild/FUTURE_IDEAS.md`
- pos-v2 spec ladder:
  `docs/rebuild/spec/pos-v2-objectives-spec.md`

---

## 14. Method-decision register (post-build, builder-backfilled)

Method-level decisions made during the build land here at
seal time per `pos-amend seal --plan-doc` convention. Empty
at plan-author time.

### Selected seed primitives (Class A)

(builder records the ≥ 5 selected primitives + selection
rationale here at seal time)

### Selected seed patterns (Class B)

(builder records the ≥ 3 selected patterns + selection
rationale here at seal time)

### Commit SHAs

```
Amendment commits:
  <SHA>  feat(primary-persona,docs): Claude-Code-corpus
         prompt-spine + ≥ 5 seed docs (amendment α,
         AC.α.1–AC.α.S)

Seal commit:
  <SHA>  chore(seals): capability-spine-and-seed-corpus
         seal — primary-persona at <SHA>
```
