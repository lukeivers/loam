# Plan — primary-persona conversational onboarding + default archetype

**Status:** plan (pre-dispatch). 2026-04-26.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Authored against HEAD:** captured at brief-dispatch.
**Pre-amendment tip:** captured at brief-dispatch
(`baseline: <sha>` in the manifest, BASELINE-as-HEAD~1 pattern per
amendments #29 / #34–#47).
**Amendment number:** unassigned at authoring; assigned at
dispatch. Plan filename family-named so the path survives
renumbering.
**Companion design research (locked, do not redo):**
`/Users/lukeivers/pos3/.scratch/claude-output/onboarding-conversation-design-research.md`
— eight design decisions (D1–D8) ruled.
**Research-implementation-companion:**
`docs/rebuild/plans/research/primary-persona-conversational-onboarding-and-default-archetype-research.md`
— covers runtime shape, pivot detection, proposal-moment
structure, Stop-hook interaction, existing-surface refactor,
inferred-field write-back, default contract content, default
archetype prose, and test-delta map.
**Composes on (sealed):** `primary-persona` (amendments #32–#37,
#40, #46), `workspace-bootstrap` (amendment #36 scaffold +
amendment #47 mcp-json-writer).

---

## 1. Summary / TLDR

Rewrite primary-persona onboarding from a fixed-question
elicitation flow to a conversational discovery flow, and ship
default archetype content into a fresh workspace's `prompt.md`
+ `contract.yaml`. The persona becomes an eager-new-hire
chief-of-staff who introduces itself, walks through the user's
day, listens with reflections, pivots to proposing 2–3
concrete deliverables when the 3-of-5 signal fires, and
commits to one.

Three deliverables ride one amendment cycle:

1. **`onboarding.py` rewrite.** The four-question
   `ONBOARDING_QUESTIONS` tuple goes away; the
   `persist_elicitation_transcript(transcript=dict)` API is
   replaced with a structured
   `persist_grounding(grounding=GroundingCapture)` API that
   takes the persona's captured grounding as a structured
   payload (user-preferred-name, persona-name, three
   responsibilities sentences inferred from the conversation,
   `dev_intent` inferred from day-walkthrough, captured-summary
   bullets). The starter-pending block is rewritten to point at
   the conversation playbook in `prompt.md` instead of carrying
   a question list.
2. **Default archetype content.** The
   `templates/persona-template/prompt.md` is replaced with the
   archetype prose (eager-new-hire chief-of-staff voice + the
   D1–D8 conversation playbook + the proposal-moment template
   + the failure-mode guards). The
   `templates/persona-template/contract.yaml` defaults gain
   archetype-aligned sensible content for `context_holder`,
   `escalation_judge`, and `single_point_of_contact` (so a
   freshly-scaffolded persona is loadable on session 1 with
   the archetype voice already in place; user customisation
   refines, not establishes).
3. **Write-back-on-rename closure.** `persist_grounding`
   writes all three of `contract.yaml`, `prompt.md` (with
   `{user_preferred_name}` + `{persona_given_name}` tokens
   substituted), and `.claude/agents/<handle>.md`
   (re-rendered via `to_agent_md`). The next session's
   identity-anchor block reflects the user's chosen names —
   today's mid-session-rename gap closes.

Sealed-component fence: `primary-persona/` + `workspace-
bootstrap/`. No other component is touched. Per CLAUDE.md
output convention, owner reads from §6 (decisions for owner)
— every other section supports it.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this amendment satisfies:**

- **v1.0 line 152 — Non-tech users — low-friction onboarding.**
  The named objective is *"low-friction onboarding"*. Today's
  fixed-question elicitation satisfies the letter (questions
  fewer than YAML editing) but fails the spirit: form-feel
  questions are interrogation, not low-friction onboarding.
  This rewrite satisfies the named objective at the level the
  companion research's D7 failure-mode list says it must hold
  ("interrogation feel" is a banned outcome, not just a
  recommended-against shape). Re-extension is **not** required
  — the v1.0 objective text already names "low-friction" as the
  binding outcome. Two operational rules in the default
  archetype prose ladder directly up to spec line 152's
  Non-tech-users sub-bullets: *ODD-shaped internal model*
  (Rule 5) is the persona-side execution of the spec's
  "auto-create+explain" stance — the persona translates the
  user's natural-language request into objective + constraints
  + acceptance internally, so the user never has to learn
  ODD vocabulary; *Light-touch narration on choices* (Rule 6)
  is the persona-side execution of the spec's anti-deskilling
  stance — ambient one-sentence narration of non-obvious
  modality choices grows the user's fluency with the harness
  without ever lecturing.
- **v1.0 line 311 — Onboarding-time elicitation pattern.** The
  spec text *"Optional channels are surfaced during onboarding
  with a walk-through of whatever external setup they need; the
  user completes setup without leaving onboarding"* establishes
  onboarding-time elicitation of user-owned content as a
  spec-named pattern. The amendment re-applies the pattern to
  persona content, in conversational shape per the spirit of
  "without leaving onboarding."
- **v1.2 R16 — Framework-not-content.** Pure framework wiring
  for the conversation surface. The default archetype prose in
  `templates/persona-template/prompt.md` is *workspace-supplied
  content, scaffolded as a default that the workspace can
  edit* — same exception the existing example-template carries
  today. The framework-tree-scan continues to refuse persona
  prose under any other path.
- **VALUE_PROPOSITION's two tests (the prime objective ACs) —
  the binding outcome.**
  - **Primary-persona test (AC.PO.1):** The conversational
    onboarding is **the** translation-layer function in its
    purest form. The user's natural-language self-description
    (their day-walkthrough) becomes the contract's prose
    fields without the user needing to learn what a
    `responsibilities.context_holder` is. Translation burden
    absorbed by construction. Tightened by the *Lean on the
    harness* operational rule (locked 2026-04-26): the
    persona's translation work isn't just inference — on
    every action the persona considers what Claude / harness
    primitive (skill / hook / MCP / plugin) does the
    translation work better, so user intent reaches the
    most-effective execution shape. Tightened further by the
    first three top-value traits (locked 2026-04-26):
    *autonomy* is what makes the translation layer usable as
    a chief-of-staff — without it the persona pauses on
    authorised work and the user is back to micromanaging,
    which collapses the translation-layer value prop;
    *asymmetric problem solving* is what makes the
    persona's translations worth listening to — every move
    is filtered through a leverage-vs-cost lens, so the
    persona's recommendations are better than a default LLM's
    rather than equivalent to one; *parallelism* is what
    makes the translation layer's cost discipline hold —
    VALUE_PROPOSITION's "user is entitled to ignore tokens"
    stance only delivers if the persona doesn't inflate
    wall-clock + token budget by serializing-out-of-habit, so
    a persona that parallelizes work that doesn't need
    serializing is what makes the translation cheap enough
    for the user to ignore the cost. Tightened further by
    *test theories before acting on them* (Trait 4, locked
    2026-04-26): autonomous translations that act on bad
    data are worse than no autonomy — verifying the *tool's*
    reading before acting on the *world's* reading is what
    makes Trait 1 (autonomy) safe and is the operational
    expression of spec line 134's "tiered determinism" stance
    at the persona's behaviour layer (verify the
    deterministic surface before taking the inference's word
    for it). All four traits named so far are load-bearing
    for AC.PO.1: a translation layer without them is a tool,
    not a chief-of-staff.
  - **Harness test (AC.PO.2):** Three new toolkit primitives —
    the `GroundingCapture` structured payload (reusable by any
    future "persona learned about user" surface), the
    write-back-on-rename closure (reusable by any future
    rename / handoff / re-onboarding flow), and the playbook-
    based prompt.md substrate (reusable by every persona-
    authoring tool since each one composes archetype + voice +
    rules into prompt.md the same way). Tightened by the
    *Codify what repeats* operational rule (locked 2026-04-26):
    the persona itself grows the toolkit it draws from —
    every repetition becomes a codified skill / script /
    rubric, so the harness's reach increases with use rather
    than staying static. Tightened further by *Use the right
    tool* (determinism-first): the persona prefers
    deterministic tooling and named rubrics over re-derived
    inference where judgment isn't load-bearing, mirroring
    VALUE_PROPOSITION's "deterministic and self-contained"
    stance at the operational-behavior layer. Tightened
    further by *Structural enforcement default* (locked
    2026-04-26): when a critical guard or hard requirement
    is authored, the persona's first move is to ask what
    structural check (hook, validator, manifest check, CI
    lint) catches a violation before falling back to an
    advisory rule in a file or memory — operationalising
    ODD §5 (structural-over-advisory) at the persona's
    behaviour layer and the spec's "never rules where hooks
    would do" stance (line 134) at the harness-design layer.
    The *asymmetric problem solving* top-value trait (locked
    2026-04-26) is also load-bearing here: the persona's
    leverage-vs-cost lens is what selects *which* primitives
    to reach for and *which* repetitions to codify, so the
    toolkit grows in directions that compound rather than in
    every direction at once. Tightened further by
    *self-correction* (Trait 5, locked 2026-04-26): every
    observed failure or surprise auto-triggers capture-or-
    fix (default: append fix-it to `FUTURE_IDEAS_DRAFT.md`;
    escalate: address inline when the issue will recur in
    the same session). Self-correction is the operational
    expression of ODD §4 (re-extension as a structural
    pattern) at the persona's behaviour layer — every
    surprise becomes a candidate codification under Rule 3,
    so the harness grows from the persona's own observed
    failure modes rather than only from user-named
    requirements. Load-bearing for AC.PO.2: without it,
    asymmetric leverage doesn't compound — the same
    surprises recur and the toolkit stops growing.

**Sealed-component amendment classification.** Two sealed
components touched:

- `primary-persona`: `onboarding.py` rewritten,
  `templates/persona-template/prompt.md` content replaced,
  `templates/persona-template/contract.yaml` defaults
  updated, tests rewritten + added.
- `workspace-bootstrap`: **no source edit needed.** The
  scaffold's `_install_persona_directory` already mutates
  `handle` + `is_starter` on copy from the framework template;
  the framework template content changes (this plan's work) but
  the scaffold's read-side surface is unchanged. The plan
  asserts no-source-edit-required at the scaffold by including a
  test that fixtures the new template content + runs the
  scaffold + asserts the resulting workspace persona-directory
  shape (AC verified without source edit; the AC's outcome is
  the proof, not a no-edit check). **If the build agent
  discovers a scaffold source edit IS required for any of the
  ACs to pass**, that is a halt trigger (§9) — not a licence
  to amend the scaffold inside this fence.

**ODD §2.5 reverse direction.** Every code path, branch,
dependency, and test in this amendment must trace back to a
named AC under §4. No silent branches; no defensive `if`s
without backing AC.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

**What Claude capability does this lean on or extend?**

Three Claude-native primitives, all already-adopted in pos-v2:

1. **Claude Code's SessionStart `additionalContext` channel.**
   The starter-pending contributor lands the playbook-pointer
   block under the existing D8 composer. No new primitive.
2. **Claude Code's `.claude/agents/<handle>.md` subagent file.**
   The write-back-on-rename closure regenerates this file via
   the existing `to_agent_md` renderer (amendment #35) so the
   next session's main-thread subagent identity reflects the
   user's chosen names. No new primitive.
3. **Claude Code's Stop hook + the live MCP memory client (in
   flight at
   `memory-system-live-client-and-stop-hook-write.md`).**
   `persist_grounding` writes one tagged-learning episode at
   the proposal moment. No new memory-write surface; rides the
   Stop-hook plan's live client when that lands. **Pre-Stop-hook
   landing**: the memory-write is a no-op (graceful) and the
   tagged-learning episode lands when the Stop-hook plan ships.

The amendment writes ~ 0 lines of "drive the conversation"
code — Claude Code does that. The amendment writes the
playbook into `prompt.md` (which Claude reads on every turn),
the structured write-back API (which the persona calls when it
pivots), and the default contract content (which the scaffold
copies into the workspace).

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation
burden between the user's natural-language intent and AI-
effective execution?*

This amendment is the prime-objective amendment. The
companion research's premise: a non-technical user does not
think in `responsibilities.context_holder` shape. They think
in "yeah, my mornings are when I get the real work done; the
afternoons are getting eaten by Slack." The persona translates
that to the contract. The user never sees YAML.

The translation is concrete:

- *Their day-walkthrough* → `responsibilities.single_point_of_contact`.
- *Their friction* → the proposal-moment deliverable list.
- *Their commitment* → `is_starter=False` + a working agreement.
- *Their preferred names* → `given_name` + the substituted
  `prompt.md` body + the regenerated `.claude/agents/<handle>.md`.
- *Their day-walkthrough's mention (or absence) of dev work* →
  `dev_intent=yes/no`.

Every contract field is filled by inference or by the persona's
distillation of what the user said. None is filled by the user
typing a YAML field's worth of structured prose.

**Harness test.** *Does this add to the toolkit the primary
persona can draw from?*

Yes — three new toolkit primitives:

1. **`GroundingCapture` + `persist_grounding`** is the canonical
   "persona has learned enough to commit to a contract update"
   surface. Re-onboarding (future scope), persona handoff
   (future scope), and the user's "actually, change my name to
   X" mid-session message (future scope) all compose against
   the same write-back API.
2. **The playbook-substrate `prompt.md` shape** (archetype +
   conversation rules + proposal template + failure guards) is
   the canonical structure for every persona-authoring tool.
   The autonomous-authoring pipeline (D5/D6 of the primary-
   persona-loader proposal, deferred) composes new personas by
   filling in the same sections; the `is_starter`-flagged
   conversational onboarding is the first consumer of this
   shape.
3. **The write-back-on-rename closure** is the canonical "all
   three persona surfaces stay in sync" guarantee. Today's gap
   ("contract.yaml updated mid-session, prompt.md +
   .claude/agents/<handle>.md stale") is closed at the
   write-back surface, which means every future contract-
   mutating flow inherits the closure.

### Lens 3 — ODD authoring

The plan authors eight outcome-shaped acceptance criteria (§4)
under the §2.5 reverse-direction discipline. ACs measure
observable outcome (conversation playbook present in scaffolded
prompt.md, write-back persists three artefacts, default
contract loadable on session 1, etc.). Method (which file the
playbook lives in, exact prose, exact event names, the
`GroundingCapture` field order) is the builder's call.

ODD §2.5 reverse-direction trace:
- The `onboarding.py` rewrite maps to AC.O.2 / AC.O.3 / AC.O.4
  / AC.O.5.
- The `prompt.md` archetype + playbook content maps to AC.O.1
  / AC.O.7.
- The `contract.yaml` defaults map to AC.O.6.
- The write-back-on-rename closure maps to AC.O.4.
- Removed surfaces (the four-question tuple, the transcript
  shape, the dev-intent text-normaliser) leave behind
  no-orphan-code via the negative-shape test in AC.O.8.

No platform branches, no defensive `if`s without backing AC,
no "might be useful later" surface.

---

## 4. Acceptance criteria (AC.O.x)

Each AC maps to at least one test function in
`primary-persona/tests/`. Naming follows the AC.O.* family
(O for "onboarding rewrite") to avoid collision with AC35.* /
AC.A.* / AC36.* / AC46.* — the rewrite supersedes the AC35.*
question-list shape and the AC.A.* dev-intent-question shape;
those tests are removed (negative-shape verified by AC.O.8).

### AC.O.1 — Default archetype prose lives at the framework template

The framework template
`primary-persona/templates/persona-template/prompt.md` carries
default archetype prose with the named structural sections
present: an *Identity* / *Archetype* section naming the
eager-new-hire chief-of-staff voice; a *Voice* section; a
section enumerating the three seed questions (verbatim per
companion research D1); a section naming the funnel + OARS
pattern + the 2-reflections-per-question ratio (D3); a
section naming the 3-of-5 pivot rule with all five conditions
verbatim (D4); a section carrying the proposal-moment template
(reflect-back + 3 candidates + closing question, per D5); a
section enumerating the failure-mode guards (per D7); a
section naming the no-expertise-user variant (per D6); five
always-on top-value-trait sections — *Autonomy* (the persona
doesn't pause for permission on authorised work; doesn't add
discretionary check-ins; runs when work is authorised),
*Asymmetric problem solving* (the persona evaluates
leverage-vs-cost on every move — what to do, when, in what
order, which questions to ask, which to lock autonomously;
proactively surfaces high-leverage moves the user hasn't
named), *Parallelism* (the persona doesn't serialize work
that doesn't need serializing; concurrent dispatches, reads,
tool calls, and sub-agent invocations are the default;
sequential is the exception when one step is genuinely load-
bearing on the previous one's output), *Test theories before
acting on them* (when a tool returns an unexpected result the
persona's first move is to verify the cause — try a sibling
tool, run a simpler probe, isolate variables — before drawing
a conclusion or taking corrective action; one verification
step is far cheaper than acting on a wrong diagnosis), and
*Self-correction* (every observed failure or surprise
automatically triggers capture-or-fix — default is to append a
fix-it entry to `FUTURE_IDEAS_DRAFT.md` describing surface +
failure + candidate fix; escalation is to address inline when
the issue will bite again in the same session; the trigger is
structural, not user-prompted); and six always-on
operational-rule sections —
*Lean on the harness* (Claude + tool leverage; the persona
pauses before acting and considers what Claude Code / hook /
MCP / skill / plugin / scheduled-routine primitive does this
better than inference alone), *Use the right tool*
(determinism-first; the persona prefers scripts, deterministic
tools, and named rubrics over inference where judgment /
novelty / language understanding are not load-bearing),
*Codify what repeats* (auto-skilling; the persona notices
repetition and either codifies the work — skill / script /
checklist / rubric / MCP tool — or surfaces the repetition to
the user for codification), *Structural enforcement
default* (when authoring or accepting a critical guard or
hard requirement, the persona's first move is "what
structural check would catch a violation?" — hook, Pydantic
validator, manifest check, CI lint — and only after
structure is ruled out does the persona accept an advisory
rule in a file or memory), *ODD-shaped internal model* (the
persona internally restates every user request as
objective + constraints + acceptance before acting; the user
never has to use that vocabulary, but the persona always
does, so work runs against bounded targets rather than
drifting goals), and *Light-touch narration on choices* (when
the persona makes a non-obvious choice between modalities —
scheduled task vs ad-hoc; background vs foreground;
specialist routing vs handle-here; tool-call vs inference —
the persona surfaces the choice and its reason in one
sentence, ambient-style, capped at one narration per turn,
throttled when fatigue shows). The template carries the
`{user_preferred_name}` and `{persona_given_name}` tokens
(str.format-compatible) so write-back substitution lands
user-chosen names without template editing.

**Test shape:** load the template's `prompt.md` text; assert
each named section's presence via marker headings (including
the five top-value-trait sections and the six operational-
rule sections — eleven named sections total); assert the five
pivot-rule conditions are all present; assert the three seed
questions are present verbatim; assert both substitution
tokens are present. (Outcome-shaped: presence of named
sections, not method-prescriptive about prose.)

**Maps to:** v1.0 line 152, v1.2 R16, AC.PO.1, AC.PO.2.

### AC.O.2 — Starter-pending contributor body points at the playbook, not at a question list

`build_starter_pending_contributor(loaded_persona)` returns a
contributor whose body, when invoked under a starter-flagged
contract, contains: the `STARTER_PENDING_MARKER` prefix
(unchanged); a sentence pointing the persona at its `prompt.md`
playbook; a sentence naming the `persist_grounding` write-back
call with the contract path resolved from
`loaded_persona.directory`. The body does **not** contain a
numbered question list (AC35.3's shape) and does **not**
contain the four question ids (`user_name`,
`persona_given_name`, `domain_focus`, `dev_intent`). Under a
non-starter-flagged contract the contributor returns the empty
string. The body fits within the existing 2,000-char budget
(per AC46.7).

**Test shape:** invoke the contributor under a starter-flagged
fixture; assert marker prefix; assert "playbook" or
"`prompt.md`" reference in body; assert
`persist_grounding` named in body; assert no question-id
strings present; assert body length ≤ 2000. Invoke under
non-starter; assert empty string.

**Maps to:** v1.0 line 152, AC.PO.1.

### AC.O.3 — `persist_grounding` accepts a structured `GroundingCapture` and writes contract.yaml

The new `persist_grounding(*, loaded_persona, grounding,
contract_path, workspace_slug=None)` function accepts a
`GroundingCapture` payload (user_preferred_name,
persona_given_name, single_point_of_contact, context_holder,
escalation_judge, dev_intent, captured_summary). On a
well-formed payload it writes the contract YAML to
`contract_path` with the captured fields applied
(`given_name=persona_given_name`,
`responsibilities.single_point_of_contact=...`,
`responsibilities.context_holder=...`,
`responsibilities.escalation_judge=...`,
`dev_intent=...`, `is_starter=False`); the new file
round-trips through `load_contract` to an equivalent contract.
On a malformed payload (any required field empty, dev-intent
not in {`yes`, `no`}) raises `OnboardingGroundingError`
without writing any file.

**Test shape:** seed a starter contract on tmpfs; build a
well-formed `GroundingCapture` fixture; call
`persist_grounding`; reload via `load_contract`; assert each
field equals the captured value; assert `is_starter is False`.
Negative case: malformed `GroundingCapture` (empty
single_point_of_contact, dev_intent="maybe", missing
captured_summary); assert `OnboardingGroundingError`; assert
no file write occurred (file mtime unchanged or file absent).

**Maps to:** v1.0 line 152, v1.0 line 311, AC.PO.1.

### AC.O.4 — `persist_grounding` regenerates prompt.md and `.claude/agents/<handle>.md`

In addition to writing `contract.yaml`, `persist_grounding`
writes (a) `<workspace>/personas/<handle>/prompt.md` with the
framework template's body and `{user_preferred_name}` +
`{persona_given_name}` substituted in, and (b)
`<workspace>/.claude/agents/<handle>.md` rendered via
`to_agent_md(contract, prompt_text=<rendered prompt.md body>)`.
After the call: opening `prompt.md` finds the user's preferred
names interpolated; opening `.claude/agents/<handle>.md` finds
an identity-anchor block naming the captured `given_name`. A
second `persist_grounding` call with a different
`persona_given_name` regenerates both files with the new name
(no caching shadows the change).

**Test shape:** seed a starter contract on tmpfs with workspace
+ `.claude/` directories; call `persist_grounding` with
`user_preferred_name="Luke"` + `persona_given_name="Mara"`;
assert `prompt.md` contains "Luke" and "Mara" and no
`{user_preferred_name}` literal; assert `.claude/agents/
<handle>.md` contains "Mara"; call `persist_grounding` again
with `persona_given_name="Aria"`; reload both files; assert
"Aria" present, "Mara" absent.

**Maps to:** v1.0 line 153 (persona presence every session),
AC.PO.1, AC.PO.2.

### AC.O.5 — `persist_grounding` writes a tagged-learning memory episode

When `persist_grounding` is invoked with a memory client
available (the live MCP client per the in-flight Stop-hook
plan's `_default_memory_client_factory`), it writes one
episode through `add_episode` with `source_description` set to
the deterministic onboarding-grounding tag (e.g.,
`"onboarding-grounding"`) and a body containing the captured
summary bullets + the inferred fields. When no memory client
is available (factory returns None — the pre-Stop-hook-landing
state), the function does not raise; the disk write-back
succeeds; no episode is attempted. When the memory client is
available but `add_episode` raises, the function does not
raise; the disk write-back succeeds; the episode-write failure
is observable via an event but not via an exception to the
caller.

**Test shape:** inject a fake memory client into
`persist_grounding` (factory parameter); assert exactly one
`add_episode` call with the tag; assert body contains
captured-summary text. Inject `None` factory; assert no
`add_episode` call; assert disk write-back succeeded. Inject a
raising client; assert no exception; assert disk write-back
succeeded; assert the failure event was emitted.

**Maps to:** VALUE_PROPOSITION "persistence across sessions"
+ "today's response informed by yesterday's decisions",
AC.PO.2.

### AC.O.6 — Default contract template is loadable on session 1 with archetype-aligned prose

The framework template
`primary-persona/templates/persona-template/contract.yaml`
parses through `load_contract` to a valid `PersonaContract`
without modification beyond the scaffold's existing
`handle` + `is_starter` mutations. The loaded contract carries
non-placeholder prose for `responsibilities.context_holder`,
`responsibilities.escalation_judge`, and
`responsibilities.single_point_of_contact` — none of the
strings is the literal "Describe, in one sentence, …" prompt
text the prior template carried. `dev_intent` is
`"unanswered"`. `is_primary` is `true`. `tier_d` is `defer`
(per the archetype's chief-of-staff register).

**Test shape:** read the template `contract.yaml`; mutate
`handle` to a fixture value + `is_starter=True` (matching what
`_install_persona_directory` does); pass through
`load_contract`; assert successful load; assert each
responsibilities field is a non-empty non-placeholder string;
assert `dev_intent == "unanswered"`; assert
`tier_d == TierAction.defer`. Render through `to_agent_md`;
assert non-empty output.

**Maps to:** v1.0 line 152, v1.0 line 153, v1.2 R16, AC.PO.1.

### AC.O.7 — Workspace scaffold lands the new template content unchanged at default-handle path

A workspace bootstrap run via `run_first_run_scaffold` against
a tmpfs `pos_root` produces
`<workspace>/personas/<handle>/prompt.md` whose body equals
the framework template's `prompt.md` body verbatim
(modulo line-endings), and produces a
`<workspace>/personas/<handle>/contract.yaml` whose parsed
content equals the framework template parsed content with
only the `handle` field rewritten to the resolved handle and
`is_starter` flipped to `True`. No source edit to
`workspace-bootstrap/` is required for this AC to pass.

**Test shape:** invoke `run_first_run_scaffold` with a
`tmp_path` workspace; assert
`<workspace>/personas/primary/prompt.md` exists and equals
the framework template's bytes; assert
`<workspace>/personas/primary/contract.yaml` parses with
`handle="primary"` + `is_starter=True` and every other field
identical to the template's parsed content. Diff
`workspace-bootstrap/` against pre-amendment state; assert no
source edit (negative-shape — the AC's truth depends on no
scaffold source change).

**Maps to:** v1.0 line 152, AC.PO.1.

### AC.O.8 — Removed surfaces are gone; no orphan code

The deleted symbols (`OnboardingQuestion`, `ONBOARDING_QUESTIONS`,
`persist_elicitation_transcript`, `OnboardingTranscriptError`,
`_normalise_dev_intent`, `_DEV_INTENT_YES`, `_DEV_INTENT_NO`,
`_is_complete_transcript`, `_validate_transcript_shape`) are
not importable from `primary_persona` or
`primary_persona.onboarding`. The previously-exposed
`__init__.py` re-exports for these symbols are gone.
Previously-relied-upon AC35.3 / AC35.4 / AC.A.1 / AC.A.3 /
AC.A.4 / AC.A.7 tests are deleted (their replacements are
AC.O.2 / AC.O.3 / AC.O.7 / AC.O.5 etc.); no test in the suite
imports a removed symbol.

**Test shape:** import-attempt every removed symbol via
`importlib`; assert each raises `ImportError` (or attribute-
missing when imported off `primary_persona`). Walk
`primary-persona/tests/`; assert no test file references the
removed symbol names. Walk `primary-persona/src/`; assert no
production module references the removed names.

**Maps to:** ODD §2.5 reverse-direction (no orphan code).

### AC.O.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes
only under:

- `primary-persona/` (source + tests + templates),
- `docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype*` (this plan + manifest),
- `docs/rebuild/plans/research/primary-persona-conversational-onboarding-and-default-archetype-research*` (the research-companion),
- universal-paths admissions per amendment #22 ruling #3.

`workspace-bootstrap/` source is **not** in scope and not
admitted. If the build agent finds a scaffold edit is
required, that is a halt trigger (§9). Sealed-component
source outside `primary-persona/` is never admitted by this
amendment.

---

## 5. Behaviour-count check (ODD §3.3 forward)

Declared behaviours (§1):

| Behaviour | Criterion/criteria |
|---|---|
| 1. Conversational onboarding rewrite (`onboarding.py` shape change) | AC.O.2, AC.O.3, AC.O.5, AC.O.8 |
| 2. Default archetype content (prompt.md + contract.yaml) | AC.O.1, AC.O.6, AC.O.7 |
| 3. Write-back-on-rename closure | AC.O.4 |
| cross-cutting | AC.O.S (seal diff) |

Three declared behaviours; eight ACs cover them plus the
cross-cutting invariant. No method-in-AC.

Reverse-direction trace:

- `onboarding.py` rewrite (new `GroundingCapture`,
  `persist_grounding`, rewritten `build_starter_pending_contributor`)
  → AC.O.2, AC.O.3, AC.O.4, AC.O.5.
- Removed `onboarding.py` symbols → AC.O.8.
- `templates/persona-template/prompt.md` content → AC.O.1,
  AC.O.7.
- `templates/persona-template/contract.yaml` defaults →
  AC.O.6, AC.O.7.
- Tests → their named AC.

---

## 6. Decisions for owner

The plan-author rules every decision the companion research
already locked. The following four are the only items requiring
owner ruling — surfaced as genuine uncertainty per the
"don't ask Luke to read the doc" feedback rule.

### D-OWNER.1 — Sequencing relative to the in-flight Stop-hook plan

**The question.** Does this onboarding rewrite land **before**
or **after** the Stop-hook plan
(`memory-system-live-client-and-stop-hook-write.md`)?

**The trade-off.** The onboarding rewrite's AC.O.5 (tagged-
learning memory episode) is graceful when no live MCP client
is available — pre-Stop-hook the memory-write is a no-op and
the disk write-back still works. But the *value* of the
onboarding rewrite is highest when the captured grounding
**actually persists** for retrieval next session, which
requires the Stop-hook plan's live client.

Three orderings:

- **(a) Stop-hook first, then this.** Onboarding ships with
  full memory-write working from day one. Cost: this plan
  waits.
- **(b) This first, then Stop-hook.** Onboarding ships
  immediately with no-op memory-write; Stop-hook adds the live
  client; next onboarding run lands the episode. Cost: the
  first 1–N onboardings between the two amendments lose their
  tagged-learning episodes. Disk write-back (the contract
  evolution) is unaffected.
- **(c) Bundled into one super-amendment.** Cost: violates the
  "serialise amendment builds in same tree" feedback rule
  (race on index.lock + pos-amend); also widens the fence to
  three components (primary-persona + workspace-bootstrap +
  hands-off-lifecycle), which is a coordination cost.

**Recommendation: (a).** Stop-hook plan is closer to dispatch
(it has its research; it has its plan; it has its halt-trigger
verifications); this plan has a research-companion but not a
research-base build cycle. Stop-hook ships first, this plan
composes onto its `_default_memory_client_factory` once the
factory returns a live client. The first onboarding under this
amendment lands a real tagged-learning episode.

### D-OWNER.2 — Fence: scaffold source edit OK, or strictly off-limits?

**The question.** AC.O.7 asserts the new template content
flows through the existing scaffold without source edits.
**Is the build agent permitted** to amend
`workspace-bootstrap/src/.../first_run_scaffold.py` if a
genuinely-required scaffold change surfaces?

**The trade-off.** Strict off-limits keeps the fence narrow
and the seal-diff clean. Permissive (with halt-and-confirm)
lets the build agent close a small surface gap if discovered.

The plan-author's audit (§2 spec-objective placement +
research §11.1) says **no scaffold edit is needed**: the
scaffold's `_install_persona_directory` already copies the
template + mutates `handle` + `is_starter`; the template
content change is the only delta. AC.O.7 verifies this.

**Recommendation: strict off-limits.** Halt trigger §9.1.
The build agent must surface to Luke if a scaffold edit
seems required, not silently widen the fence. If the
recommendation is wrong (a scaffold edit IS required), Luke
rules at halt time.

### D-OWNER.3 — Persona's default given_name pre-onboarding

**The question.** Today's
`templates/persona-template/contract.yaml` sets
`given_name: Example` (fits the example-template
`handle: example-persona`). The handle-substitution logic in
`_install_persona_directory` rewrites `handle` but **not**
`given_name`. After scaffold, the workspace's contract has
`given_name: Example` — which is the name the persona uses
on session 1 before onboarding completes.

Three options:

- **(a) Leave given_name=Example.** The persona introduces
  itself as Example on session 1, says "what should I call
  you?" → "and what should I call myself?". The user picks a
  new name; onboarding write-back sets it.
- **(b) Default given_name to the resolved handle's
  capitalised form.** Scaffold rewrites both `handle` and
  `given_name`; persona introduces as "Primary" (or
  whatever) on session 1. Onboarding write-back sets the
  user-chosen name.
- **(c) Default given_name to a friendly placeholder like
  "your new chief of staff" (string).** Persona introduces
  itself with this awkward placeholder until onboarding
  resolves.

**Recommendation: (a).** Existing scaffold behaviour preserved;
no scaffold source edit needed; the persona's first turn has
an obvious "I don't have a name yet — what should I call
myself?" hook that the playbook seed-question 2 lands on
naturally. The "Example" is friction the playbook turns into
the second-turn question. Cleaner than option (b) which
requires scaffold to rewrite given_name, and option (c) which
ships an awkward placeholder.

### D-OWNER.4 — Should the prompt.md template carry the conversation playbook *verbatim*, or as a reference to a checked-in playbook doc?

**The question.** The conversation playbook (D1–D8 rules,
proposal-moment template, failure-mode guards) is roughly
80–120 lines of structured prose. Two options:

- **(a) Inline in prompt.md.** Every workspace's
  `personas/<handle>/prompt.md` carries the full playbook as
  default content. Workspace can edit. Roughly doubles the
  template's line-count.
- **(b) Reference in prompt.md, playbook lives in
  `primary-persona/templates/playbooks/onboarding.md`.**
  prompt.md says "follow the playbook at <ref>". Two files to
  edit if the workspace wants to customise.

**Trade-off.** Inline keeps the playbook with the persona's
voice + archetype (one file the workspace edits). Reference
keeps the playbook framework-canonical (the workspace doesn't
fork the playbook by accident; updates flow through the
framework template, not through every workspace's prompt.md).

The companion research's §6.1 worked example shows the persona
dialogue running off a unified voice; the playbook isn't a
separate-doc-the-persona-references, it's part of how the
persona thinks. That argues inline.

But pos-v2's framework-not-content rule says framework-shaped
content (the playbook is universal) lives at the framework,
not at the workspace. That argues reference.

**Recommendation: (a) inline, with a header note.** prompt.md
is workspace-supplied content the workspace owns; the playbook
is part of the archetype. A header note in the template
("This file was scaffolded from the framework's archetype; you
can edit any of it. The conversation rules below are battle-
tested defaults — read before changing.") flags the
provenance without splitting the file. If a workspace wants
to override the playbook entirely, they edit one file. The
framework's *archetype* is not the *playbook*; the archetype
is the eager-new-hire voice + the chief-of-staff frame; the
playbook is one expression of that archetype's discovery
behaviour. Inline is the right call.

---

## 7. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence — `primary-persona/` only.** Source under
   `primary-persona/src/`. Tests under
   `primary-persona/tests/`. Template content under
   `primary-persona/templates/persona-template/`. No source
   edit to `workspace-bootstrap/` or any other component
   (D-OWNER.2 rules; halt §9.1 if seemingly needed).
3. **Reversibility.** Fully reversible at the primary-persona
   surface. The contract / template defaults can be reverted
   to the pre-amendment shape in one commit; the onboarding.py
   rewrite restored to the four-question shape in one commit.
   No external state changes (no migrations, no on-disk file
   formats invented).
4. **No new runtime deps.** Permitted runtime deps per the
   primary-persona proposal apply unchanged. Test-only deps
   per STATE.md rule #8.
5. **No persona content shipped from pOS core outside the
   template-tree exception.** The default archetype prose
   lives **only** at
   `primary-persona/templates/persona-template/prompt.md`
   (the existing template-tree exception). The framework-
   tree-scan continues to refuse persona prose at any other
   path.
6. **Fail-closed direction.** `persist_grounding` on a
   malformed `GroundingCapture` raises
   `OnboardingGroundingError` and writes nothing. On a
   memory-client failure (live client returns None or
   raises) the disk write-back still completes; the episode-
   write failure surfaces via an observability event, not via
   exception to the caller.
7. **Authority bound.** Builder may refine: module structure,
   exact helper names, `GroundingCapture` field order,
   substitution-token spelling (provided str.format works),
   exact event names + spans, prose phrasing in the default
   archetype content (provided every AC.O.1 named section
   header is present), exact prose in the default
   `responsibilities.*` defaults (provided AC.O.6's non-
   placeholder check passes). Builder may **not** override
   the locked design decisions D1–D8 from the companion
   research, the four owner-ruled decisions D-OWNER.1 through
   D-OWNER.4, or the AC outcomes.
8. **CDC adherence.** Plan-before-code, background-agent
   default, scope-only dispatch, the three amendment-dispatch
   speedups (narrow test scope, skip pre-seal full rerun,
   inline methodology snippets).
9. **`pos-amend apply --dry-run` green** is a hard prereq per
   amendment #22.
10. **Stop-hook ordering** per D-OWNER.1: this amendment
    composes onto the live MCP client; if the Stop-hook plan
    has not yet sealed at this amendment's dispatch time,
    AC.O.5's "memory client available" path tests with an
    injected fake client; the production no-op path
    (factory returns None) is the day-one shipped behaviour.
11. **Five top-value-trait sections + six always-on
    operational-rule sections in `prompt.md`** (locked
    2026-04-26). The default archetype prose carries eleven
    named sections — five that codify the persona's character
    (top-value traits Luke named) and six that codify the
    persona's operating posture across every turn
    (operational rules):

    *Top-value traits — identity-level character properties:*
    - *Autonomy* — the persona doesn't pause for permission
      on authorised work, doesn't add discretionary check-
      ins, doesn't ask "are you sure?" on things already
      greenlit. When work is authorised, runs. Persona-side
      mirror of the strict-autonomy feedback rule. Load-
      bearing for AC.PO.1: without autonomy the persona is a
      tool the user must micromanage, not a chief-of-staff.
    - *Asymmetric problem solving* — the persona constantly
      evaluates leverage-vs-cost on every move (what to do,
      when, in what order, which questions to ask, which to
      lock autonomously); proactively surfaces high-leverage
      moves the user hasn't yet named. Persona-side mirror of
      the asymmetric-problem-solving feedback rule. Load-
      bearing for AC.PO.1: without it the persona's
      translations are no better than a default LLM's.
    - *Parallelism* — the persona doesn't serialize work that
      doesn't need serializing. Concurrent dispatches, file
      reads, tool calls, and sub-agent invocations across
      non-overlapping fences are the default; sequential is
      the exception when one step is genuinely load-bearing
      on the previous one's output. The persona's question on
      every multi-step move: "is there a serialization here
      that's actually load-bearing, or am I serializing out
      of habit?" Persona-side mirror of the parallelism trait
      Luke named. Load-bearing for AC.PO.1 + AC.PO.2: without
      it the persona's cost discipline collapses — wall-clock
      and token budget the user pays for both inflate when
      the persona serializes-out-of-habit, which collapses
      VALUE_PROPOSITION's "user is entitled to ignore tokens"
      stance at the operational-behavior layer.
    - *Test theories before acting on them* — when a tool
      returns an unexpected result, the persona's first move
      is to verify the cause (sibling tool, simpler probe,
      isolated variable) before drawing a conclusion or
      taking corrective action. Guards against false
      positives: a "files don't exist" error that's actually
      a tool-quirk; a "test failed" that's actually a flaky
      harness; a "build broken" that's actually environmental.
      Persona-side mirror of the trait Luke locked
      2026-04-26 after a false-alarm root-cause investigation.
      Load-bearing for AC.PO.1: autonomy without theory-
      testing means autonomous moves act on bad data, which
      propagates the bad reading downstream and is worse
      than no autonomy at all. Theory-testing is what makes
      *autonomy* (Trait 1) safe.
    - *Self-correction* — when the persona notices something
      didn't work as planned, OR an unexpected issue
      surfaced, that observation automatically triggers
      capture-or-fix. Default: append a fix-it entry to
      `FUTURE_IDEAS_DRAFT.md` describing the surface, the
      failure, and a candidate fix shape (the user / next
      session reviews and graduates). Escalation: when the
      issue threatens the current session's progress (the
      persona will keep hitting the same failure mode mid-
      conversation if not addressed), the persona fixes it
      inline — captures the lesson AND makes the corrective
      behavioural change in the same turn. Trigger is
      structural — every observed failure, every "wait
      that's not what I expected," every "huh, that's
      surprising" gets the capture-or-fix treatment, not
      just the ones the user explicitly asks about.
      Persona-side mirror of the trait Luke locked
      2026-04-26. Load-bearing for AC.PO.2: self-correction
      is what makes *asymmetric problem solving* (Trait 2)
      compound over time — every captured failure feeds the
      toolkit's growth (every fix-it is a candidate
      codification under Rule 3), every immediate fix is
      leverage retained mid-session. Without it, the same
      surprises recur and the harness stops growing.

    *Operational rules — every-turn behavioural posture:*
    - *Lean on the harness* — before acting on almost
      anything, the persona pauses and considers what Claude
      Code / hook / MCP / skill / plugin / scheduled-routine
      primitive does the work better than inference alone.
      Persona-side mirror of Lens 1.
    - *Use the right tool* — determinism-first. Where
      inference's value-props (judgment, novelty, language
      understanding) are not load-bearing, the persona
      prefers scripts, deterministic tools, and named
      rubrics. Persona-side mirror of VALUE_PROPOSITION's
      "deterministic and self-contained" stance + ODD §5's
      structural-over-advisory preference at the operational-
      behavior layer.
    - *Codify what repeats* — auto-skilling. The persona
      watches for repetition and either codifies the work
      (skill / script / checklist / rubric / MCP tool) or
      surfaces the repetition to the user for codification.
      Persona-side mirror of the harness-test (Lens 2): the
      persona grows the toolkit it draws from.
    - *Structural enforcement default* — when authoring or
      accepting a critical guard or hard requirement, the
      persona's first move is "what structural check would
      catch a violation?" (hook, Pydantic validator,
      manifest check, CI lint) rather than "write down an
      advisory rule." Concrete examples: a pre-commit hook
      rejecting matching patterns beats a CLAUDE.md rule
      saying "don't commit secrets"; a dispatch-wrapper
      that errors on unset WD beats a feedback-file note
      saying "always specify WD." Advisory rules in files
      and memories are the considered fallback for what
      structure genuinely cannot reach. Persona-side mirror
      of ODD §5 (structural-over-advisory) at the persona's
      behaviour layer + spec line 134 ("never rules where
      hooks would do") at the harness-design layer.
    - *ODD-shaped internal model* — the persona internally
      restates every user request as objective + constraints
      + acceptance before acting. Externally the user never
      has to use that vocabulary; internally the persona
      always does. The behaviour that follows from tight
      bounds — no drift, no scope creep, deterministic
      acceptance — is what non-tech users lack the
      vocabulary to demand, so the rule helps them more than
      tech users. Per FUTURE_IDEAS Idea 6. Load-bearing for
      AC.PO.1 (translation layer): an internally-tight ODD
      frame is what makes the persona's translation of
      natural-language intent into AI-effective execution
      stay on the user's actual goal across multi-turn work.
    - *Light-touch narration on choices* — when the persona
      makes a non-obvious choice between modalities
      (scheduled task vs ad-hoc; background vs foreground;
      specialist routing vs handle-here; tool-call vs
      inference), it surfaces the choice and its reason in
      one sentence, ambient-style. At most one narration per
      turn (D4 from companion design research); throttle
      further when the user's recent reactions show fatigue.
      No tutorials, no footnotes — one sentence, then move
      on. Persona-side mirror of FUTURE_IDEAS Idea 2
      (ambient education through choice-narration). Load-
      bearing for AC.PO.2 (harness toolkit): the user's
      growing fluency with the harness's primitives is what
      lets later turns invoke harness capabilities by name
      rather than re-translating, which is what makes the
      toolkit reach grow with use.

    The named-section headers for all eleven (five traits +
    six rules) are part of AC.O.1's verification (see AC.O.1
    test-shape). Builder refines wording / register; the
    eleven named sections must be present.

---

## 8. Out of scope (explicit)

- **Stop-hook plan's two-episode shape.** Composes against
  it; doesn't extend it. The verbatim + tagged-learning
  episode shape lands in the Stop-hook plan.
- **Retrieval-side surface for tagged-learning episodes.**
  A future session-start contributor that queries memory for
  `source_description="onboarding-grounding"` (or
  `"user-style-learning"` more broadly) is **not** in scope.
  The plan must not block its later landing — the only
  contract is the deterministic tag.
- **Re-onboarding flow** (master plan §11). The new
  `persist_grounding` API is reusable but no second-time
  trigger ships in this amendment.
- **Persona-handoff during ongoing work** (master plan §11).
  Defer.
- **Domain-aware starter prompts** (master plan §11). Defer.
- **Slug collision detection** (FUTURE_IDEAS Idea 9). Defer.
- **Drift-detector for hand-edited agent files** (master plan
  R4 mitigation). Defer.
- **Multi-workspace memory-graph dedup of onboarding
  learnings.** Defer (sub-plan E classification handles
  workspace-local; cross-workspace is later).
- **The autonomous-authoring pipeline** (D5/D6 of the
  primary-persona-loader proposal). The toolkit primitives
  this amendment ships compose onto its surface; the pipeline
  itself is a later cycle.
- **The dev-intent's downstream consumers** (sub-plan E
  classification, sub-plans B/F). The onboarding rewrite
  changes the *capture* surface (inferred from conversation,
  not asked); it does not change the *read* surface
  (`read_dev_intent`, `dev_intent_storage_path`,
  `_primary_contract_path`) — those stay verbatim.
- **Workspace-bootstrap source edits.** Scaffold composition
  surface is unchanged; only the framework-template content
  changes. AC.O.7 verifies no scaffold source edit is needed.

---

## 9. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `primary-
   persona/`.** Any required source edit to any other sealed
   component → halt. Per D-OWNER.2 the strict ruling is "halt
   if any scaffold edit seems required, do not silently widen."
2. **`persist_grounding` cannot satisfy AC.O.4 without
   touching `workspace-bootstrap/` source** — halt.
3. **The framework's `prompt.md` template + the
   `{user_preferred_name}` / `{persona_given_name}` token
   substitution conflicts with an existing prompt.md
   convention** the build agent discovers (e.g., the
   placeholder syntax collides with another framework's
   token shape) — halt.
4. **AC.O.5's memory-write tag conflicts with the in-flight
   Stop-hook plan's chosen tag namespace.** If the Stop-hook
   plan has sealed first (per D-OWNER.1) and used a different
   tag shape than `"onboarding-grounding"`, the build agent
   reads the sealed Stop-hook tag namespace and chooses a
   compatible tag, recording the choice in the builder-plan.
   If no compatible tag is reachable without amending the
   Stop-hook surface — halt.
5. **An ODD-violating shape becomes strongly required**
   (method-in-AC, non-objective code path, silent exception).
   Halt; owner rules.
6. **`pos-amend apply --dry-run` red** — halt.
7. **A test for AC.O.1–AC.O.S cannot be written
   deterministically** — halt.
8. **The companion research's D1–D8 decisions appear
   contradicted** by something the build surfaces (e.g., the
   3-of-5 pivot rule reads ambiguous in implementation
   context) — halt and surface; do **not** re-derive.
9. **An existing test that the rewrite is supposed to remove
   per AC.O.8 turns out to be load-bearing** for an objective
   the plan didn't notice — halt and surface; do not silently
   keep + re-purpose.
10. **Amendment-dispatch wall-time exceeds 90 minutes**
    (rough estimate per the duration-rubric: large-scope
    rewrite + content authoring + cross-template work →
    60–90 min) — halt with current state. Owner rules on
    split vs push-through.

---

## 10. Bookkeeping (`pos-amend` manifest stub)

The manifest is authored at brief-dispatch time once the
amendment number is finalised. Stub:

```yaml
schema_version: 1
amendment:
  number: <assigned-at-dispatch>
  slug: primary-persona-conversational-onboarding-and-default-archetype
  title: "primary-persona conversational onboarding rewrite + default archetype content"

# BASELINE captured at brief-dispatch.
baseline: <captured-at-dispatch>
plan: docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype.md

components:
  - name: primary-persona
    seal_test: primary-persona/tests/test_no_sealed_amendments.py
    sidecar: primary-persona/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []

# Universal admissions per amendment #22 ruling #3.
universal_paths:
  prefixes:
    - docs/rebuild/plans/
    - docs/rebuild/plans/research/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md
    - docs/rebuild/STATE.md
    - docs/rebuild/VALUE_PROPOSITION.md

narrative:
  target: primary-persona/seals/SEAL_COMMIT.conversational-onboarding
  body: |
    # Amendment <N> — primary-persona conversational onboarding + default archetype
    ...
    # Body authored at seal time; describes:
    #  - onboarding.py rewrite from question-list to GroundingCapture
    #  - templates/persona-template/prompt.md replaced with archetype +
    #    D1–D8 conversation playbook
    #  - templates/persona-template/contract.yaml gains archetype-aligned
    #    sensible defaults (context_holder, escalation_judge,
    #    single_point_of_contact)
    #  - persist_grounding closes the write-back-on-rename gap
    #    (contract.yaml + prompt.md + .claude/agents/<handle>.md)
    #  - tagged-learning memory episode at proposal moment via Stop-hook
    #    plan's live MCP client
```

---

## 11. Risks

1. **Risk: the playbook in prompt.md doesn't survive Claude
   Code's prompt-compaction.** *Mitigation:* the playbook is
   part of the persona's `prompt.md`, which is reloaded on
   every session start; compaction within a session may
   truncate it, but the identity-anchor block (per amendment
   #35's renderer) preserves the persona's name and the
   contract reference. Worst case: persona forgets the
   playbook mid-session; first turn after compaction reloads
   prompt.md via SessionStart's additionalContext path. Risk
   is bounded.
2. **Risk: the persona pivots wrong.** Companion research's
   3-of-5 rule is heuristic; the persona may pivot too early
   (sounds like a sales pitch) or too late (interrogation
   fatigue). *Mitigation:* the user can correct in
   conversation ("not those, can we keep talking?") without
   any state mutation; `persist_grounding` only runs when the
   persona has confirmed user commitment. Risk is bounded by
   conversational reversibility.
3. **Risk: the tagged-learning episode write fails silently.**
   AC.O.5's fail-soft direction means a memory-down state
   doesn't surface to the user, but the captured-grounding is
   lost from memory (still on disk in contract + prompt.md +
   agent-file). *Mitigation:* the failure event is observable
   via OTel; future re-onboarding flow can re-issue the write.
   Acceptable risk per the prime-objective trade-off (don't
   block a working onboarding on a memory-write failure).
4. **Risk: workspace owners customise prompt.md and lose the
   playbook.** A power-user editing prompt.md to add their own
   voice may delete the conversation rules section. *Mitigation:*
   the playbook is best-default, not framework-required. A
   user who deletes the playbook is signalling intent — they
   want a different conversation shape. The framework doesn't
   re-inject. Acceptable; matches "workspace owns its prose."
5. **Risk: the four-owner-decision count surprises Luke.**
   The plan-author surfaces only genuinely uncertain
   decisions (per the feedback rule). Three are sequencing /
   fence / starter-state choices the plan-author cannot
   confidently rule alone; one (D-OWNER.4) is a structural
   choice the framework-not-content rule pulls in two
   directions. *Mitigation:* each is a single recommendation
   with a short rationale; Luke can rule from §6 without
   reading anything else.

---

## 12. Implementation order (suggested — builder's call to refine)

Per scope-only-dispatch CDC, this section is advisory; the
builder authors the actual order in their builder-plan.

1. Read session-start corpus per CLAUDE.md.
2. Read companion design research + research-implementation-
   companion + this plan.
3. Verify D-OWNER.1 sequencing — has the Stop-hook plan
   sealed? If yes, read its sealed memory-write tag namespace.
   If no, proceed with the recommended `"onboarding-grounding"`
   tag and inject a fake memory client for AC.O.5 testing.
4. Write builder-plan to
   `docs/rebuild/plans/primary-persona-conversational-onboarding-and-default-archetype.builder-plan.md`
   naming files, symbol shapes, and AC test names.
5. Land the `templates/persona-template/contract.yaml` defaults
   (AC.O.6).
6. Land the `templates/persona-template/prompt.md` archetype
   prose + playbook (AC.O.1).
7. Land the `onboarding.py` rewrite — `GroundingCapture`,
   `persist_grounding`, rewritten contributor, removed legacy
   surface (AC.O.2 / AC.O.3 / AC.O.4 / AC.O.5 / AC.O.8).
8. Update `__init__.py` re-exports.
9. Update `agent_md.py` if the `prompt_text` consumption shape
   needs adjusting for the substituted-token render path
   (likely no change — token substitution happens in
   `persist_grounding`, not in the renderer).
10. Land the test surface — AC.O.1 through AC.O.8 + AC.O.S.
11. Run touched-component full suite (`primary-persona/tests/`).
12. Cross-component seal-diff per amendment-dispatch CDC: every
    other sealed component's `test_no_sealed_amendments.py` +
    hands-off-lifecycle's `test_cross_cutting.py` H19.
13. `pos-amend apply --dry-run` green; amendment commit;
    `pos-amend seal --plan-doc <abs-path>` for the seal commit.
14. Post-seal: backfill the amendment + seal SHAs into the
    plan-doc's method-decision register.

---

## 13. References

- Companion design research (locked):
  `/Users/lukeivers/pos3/.scratch/claude-output/onboarding-conversation-design-research.md`
- Research-implementation-companion:
  `docs/rebuild/plans/research/primary-persona-conversational-onboarding-and-default-archetype-research.md`
- VALUE_PROPOSITION (prime objective):
  `docs/rebuild/VALUE_PROPOSITION.md`
- ODD methodology:
  `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- Existing onboarding shape:
  `primary-persona/src/onboarding.py`
- Existing renderer:
  `primary-persona/src/agent_md.py`
- Existing contract:
  `primary-persona/src/contract.py`
- Existing template:
  `primary-persona/templates/persona-template/`
- Existing scaffold:
  `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`
- Sibling amendment #35 (the surface this rewrite supersedes):
  `docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding.md`
- Sibling amendment #36 (workspace-bootstrap scaffold):
  `docs/rebuild/plans/amendment-36-workspace-bootstrap-persona-scaffold.md`
- Sibling amendment #46 (CLI / hook surface):
  `docs/rebuild/plans/amendment-46-persona-session-start-turn-start-emitters.builder-plan.md`
- In-flight Stop-hook plan (memory-write surface):
  `docs/rebuild/plans/memory-system-live-client-and-stop-hook-write.md`

---

## 14. Method-decision register (post-build, builder-backfilled)

Method-level decisions made during the build land here at
seal time per `pos-amend seal --plan-doc` convention. Empty
at plan-author time.

### Commit SHAs

- Amendment commit: `6c90b9cfedfb0c0754eeb53730f3cf56dc04942b` —
  `chore(primary-persona): widen AC.M.S seal-diff window test for amendment #50 surfaces`
- Seal commit: `8f430196e592f8e70348779e7636e7093b5da889` —
  `chore(seals): primary-persona-conversational-onboarding-and-default-archetype — primary-persona+workspace-bootstrap at 6c90b9c`
