# Plan — First-run primary-persona content + Claude Code default-agent wiring

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`
**Authored:** 2026-04-25
**Author:** research+plan agent (background dispatch from main session)
**Status:** plan (pre-dispatch). No code, no manifest, no commits.
**Classification:** **Sealed-component amendment** — touches three sealed surfaces (`primary-persona`, `workspace-bootstrap`, `hands-off-lifecycle`). Requires owner approval per multi-component amendment rule (see §10 halt triggers).
**Spec objectives backing this work:**
- v1.0 line 153: *"every interactive session (terminal or desktop) starts with the primary persona present by default — asserted by a session-start test."* This work makes that acceptance pass on a fresh clone, which it currently does not.
- v1.0 line 152: *"Non-tech users — four behaviours (low-friction onboarding, persona in every session, auto-create+explain, anti-deskilling principle)."* "Persona in every session" is the load-bearing one here.
- v1.2 addendum (proposal §1.0 mapping): *"workspace without persona cannot start session"* — the loader's fail-closed today produces a hard failure on a fresh clone instead of a guided onboarding to the persona-present state.
- v1.0 line 311: *"Optional channels are surfaced during onboarding with a walk-through of whatever external setup they need; the user completes setup without leaving onboarding."* Establishes that onboarding-time elicitation of user-owned content is a spec-named pattern, which this work re-applies to persona content.

---

## 1. Owner's report (verbatim, for context)

> "i had originally thought, and feel like i had asked, that part of the bootstrapping or onboarding process be configuring and setting up a primary persona for the system. but i don't know that i'm actually talking to that primary persona, at least in part because the default agent for the claude code session never loaded. i don't want you to actually use any of the content from ivers-corp directory, but i want you to go look at how that directory has its agents set up and how it specified the default agent for claude code. we need to do at least that much, along with setting up a default primary persona (i know we built the idea for primary persona in to pos v2)"

Two distinguishable things: (a) the Claude Code default-agent surface is unwired in pos-v2; (b) the workspace's persona content is never authored at first-run.

---

## 2. Summary (read-this-first)

A fresh-clone pos-v2 session today lands as **generic Claude**, not as the workspace primary persona, for two compounding reasons:

1. **No Claude Code default-agent wiring.** Pos-v2's `.claude/settings.json` has only a `SessionStart` hook (the first-run shim). It has no `"agent"` field naming a default subagent and no `.claude/agents/<handle>.md` registration. ivers-corp solves this with `"agent": "eve"` at the top level of `settings.json` plus a directory of `.claude/agents/<handle>.md` files (frontmatter `name`/`description`/`model`, body is the system prompt + identity-anchor). That's the structural mechanism Claude Code provides. Pos-v2 currently provides none of it.
2. **No persona content at first-run.** `PersonaLoader.load()` reads `<workspace>/personas/<handle>/contract.yaml` + `prompt.md` and fails closed (`PersonaDirectoryNotFoundError`) when the directory is absent. The first-run scaffold writes nine `~/.pos/*.yaml` files but does NOT create `<workspace>/personas/`. A `templates/persona-template/` exists in the framework tree but is never copied. Net: every fresh clone sits in a state where the loader cannot succeed and `STATE.md` rule 4 ("workspace supplies the content") is satisfied only in the sense that the workspace has supplied nothing.

The fix has three parts that ship together:

- (A) **First-run scaffolds a *starter* `personas/<handle>/` directory** by copying `templates/persona-template/` content into `<workspace>/personas/eve/` (or the user's chosen handle, defaulted), with placeholders that are valid-by-construction so the loader passes. The starter is explicitly "yours to edit," not "your persona." (No persona content shipped from pos-v2; the template is framework content, identical to what the existing `enforce_no_personas_in_core` check already permits.)
- (B) **First-run also writes `.claude/agents/<handle>.md` and sets `"agent": "<handle>"` in `.claude/settings.json`** so Claude Code's session lands as the workspace persona. The agent file's body composes from the loaded `PersonaContract` + a compaction-resilience identity anchor (the same structural shape ivers-corp uses, content authored from the workspace's own contract).
- (C) **First-session conversational elicitation, not a blocking form.** The starter contract's prose fields (`responsibilities.*`, `voice_markers`, `prompt.md` body) are pre-filled with valid-but-generic placeholders that the persona itself flags on first interaction: "I'm running on a starter contract; I'd like to learn who you are and what you want me to be — five questions, two minutes, you can skip any." That's an ODD-shaped onboarding scope-of-work, not a setup wizard. The persona is present from session one; refinement is conversational, persisted via the existing `PersonaContract.to_yaml()` write-back surface.

This shape satisfies all three lenses (§5), avoids shipping persona content from pOS core (STATE.md rule 4), and produces a working "talk to your persona" experience on a fresh clone within the first session — without forcing the user to author files before they can use the system.

---

## 3. Recommended decisions (D1–D6, owner rules from this list)

The following are surfaced for owner ruling. Each carries the agent's recommendation + one-line rationale. **The owner does not need to read §6–§10 to rule on these.**

### D1 — Claude Code default-agent mechanism

**Question:** Which Claude Code surface makes a fresh session land as the workspace persona?

Options reviewed:
- (a) `"agent": "<handle>"` in `.claude/settings.json` + `.claude/agents/<handle>.md` subagent file. (ivers-corp's pattern.)
- (b) Inject persona prompt as `additionalContext` from a SessionStart hook (the existing context-load gate's mechanism, extended).
- (c) Compose persona prompt into project-level `CLAUDE.md`.
- (d) Custom skill that the user invokes per-session.

**Recommendation: (a) — subagent registration with `"agent"` field.**
**One-line rationale:** Claude Code natively persists agent identity across the session and through compaction (the agent file's body is reloaded on context refresh); no other option gives Claude Code that structural anchor, and (b)/(c)/(d) all degrade to "the model has read about the persona" rather than "the session is running as the persona."

(b) is still used as the *companion* surface — the existing D8 SessionStart context-load gate continues to inject runtime state (corpus, scopes, awareness block); the persona file is the identity anchor, the gate carries the live context. The two compose; this is not an "or."

### D2 — Persona-content elicitation pattern at first-run

**Question:** How does first-run obtain persona content from the user?

Options reviewed:
- (a) **Starter-template-edit-flow.** First-run copies the template into `<workspace>/personas/<handle>/`; the user opens it later and edits prose. Persona is "valid-but-generic" until edited.
- (b) **Guided conversational elicitation.** The persona itself, on first interaction, asks 3–5 questions ("what do you want me to call you?", "what should I call myself?", "what kinds of work do you most want me to handle for you?", etc.) and writes the answers back to the contract via `to_yaml()`. The starter is in place from second one; refinement is conversational.
- (c) **Step-by-step instructions.** First-run prints a numbered list of edits the user must make to `personas/<handle>/contract.yaml` before continuing. Pure CDC step-by-step-when-system-cannot-act.
- (d) **Combination: (a) + (b).** Starter template lands silently; the persona itself flags it on first interaction and offers the conversational pass. User can skip ("just use the defaults") or run it.

**Recommendation: (d) combination.**
**One-line rationale:** (a) alone leaves the user with a generic persona until they manually edit YAML — fails the primary-persona test (translation burden on the user). (b) alone delays "persona present" by however long elicitation takes — fails v1.0 line 153's session-start acceptance unless we treat the partially-elicited state as "present." (c) is the worst — the user has to read step-by-step instructions before they can talk to the system at all. (d) gets the persona present on session one (loader passes against the starter), runs elicitation as a conversational scope (the persona is the one talking, not a wizard), and the user can defer or skip without leaving the experience. This is exactly what the VALUE_PROPOSITION primary-persona-as-translation-layer framing prescribes: the persona translates the user's natural-language self-description into the contract fields the loader needs.

### D3 — Default handle for the starter persona

**Question:** What handle does the starter persona ship with?

Options reviewed:
- (a) `eve` (matches ivers-corp's branding — explicitly forbidden).
- (b) `primary` (descriptive, generic).
- (c) `assistant` (very generic).
- (d) Pick at first-run from a small choice list ("call me Eve / Iris / a name you choose").
- (e) The user picks at first-run with a free-text default.

**Recommendation: (e) free-text with default `primary` and a one-question prompt.**
**One-line rationale:** (a) is forbidden. (b)/(c) are fine but feel impersonal — the persona is meant to feel like a relationship, not a service. (d) is over-prescriptive and uses up an elicitation slot for a value-low choice. (e) lets the user pick a name they like (the "given_name" field in the contract) without forcing it; the handle defaults to a sluggified version. Total cost: one question added to the elicitation flow in D2(d). The slug → handle is mechanical (lowercase, dashes, ASCII). If the user types nothing, `primary` is the slug, no question asked.

### D4 — Where the `.claude/agents/<handle>.md` body comes from

**Question:** What's in the `.claude/agents/<handle>.md` file the SessionStart sets?

Options reviewed:
- (a) Static template that references the persona spec at workspace path.
- (b) Generated at first-run by composing the loaded `PersonaContract` + a compaction-resilience identity-anchor block.
- (c) Symlink to `personas/<handle>/prompt.md`.

**Recommendation: (b) generated-at-first-run from the contract.**
**One-line rationale:** (a) means the agent file and the loader contract can drift — ivers-corp's pattern shows this is real (their agent file says "the full persona spec lives at `personas/chief-of-staff.md`" and includes a compaction-proof anchor specifically because the spec file isn't always re-read). (b) collapses the drift surface — the agent file is rendered from the contract, regenerated whenever the contract changes (the existing `to_yaml()` write-back path gets a sibling `to_agent_md()` renderer; a contract-change event re-renders the agent file). (c) is appealingly simple but the agent file needs frontmatter (`name`, `description`, `model`) plus the identity-anchor block — `prompt.md` is just the prompt body, not the full structural shape Claude Code needs. The renderer is a small primitive (~30 lines) co-owned by primary-persona.

The renderer's output is not persona content shipped from pOS core (STATE.md rule 4 holds): the contract is authored by/with the user, the renderer is a deterministic projection from contract→agent-file. Same shape as the YAML→Pydantic→YAML round-trip the loader already supports.

### D5 — Where the conversational elicitation runs

**Question:** What component owns the elicitation flow itself?

Options reviewed:
- (a) New module inside `primary-persona/` (e.g. `onboarding.py`) that the SessionStart context-load gate triggers when the contract is starter-flagged.
- (b) New module inside `workspace-bootstrap/` first-run scaffold.
- (c) Inline in `hands-off-lifecycle/hooks/first_run_*.py`.
- (d) A Claude Code skill the persona invokes.

**Recommendation: (a) module inside `primary-persona/`, triggered by the context-load gate.**
**One-line rationale:** Elicitation IS the persona's first conversational scope-of-work — it's not setup, it's the persona translating the user's self-description into the contract. Putting it inside `primary-persona/` keeps the surface coherent (the persona owns its own contract; the framework owns the loader/validator/gate). `workspace-bootstrap`'s adapters trigger it (during first-run, the `primary_persona` adapter sees a starter-flagged contract and registers a "starter elicitation pending" state) but the conversation itself runs in the persona layer. (d) is interesting but a Claude Code skill is the wrong granularity — skills are user-invoked, this is automatic-on-starter-detection. The starter-flag is a new field on the contract (`is_starter: true`), unset after elicitation completes.

### D6 — Three-component amendment vs. dev-discipline

**Question:** Is this scoped as a sealed-component amendment (multi-component, per §10 halt) or as dev-discipline?

**Recommendation: sealed-component amendment, multi-component (3 sealed surfaces).**
**One-line rationale:** The work satisfies named v1.0 spec objectives (line 152, 153, 311) and v1.2 addendum (workspace-without-persona-cannot-start-session). Per CLAUDE.md operational caution §2.5, that names a spec objective the code satisfies → it's amendment work, not dev-discipline. Three components are touched: `primary-persona` (renderer + onboarding module + starter-flag field on contract), `workspace-bootstrap` (first-run scaffold writes `personas/<handle>/`, the `primary_persona` adapter detects starter-flag), `hands-off-lifecycle` (settings.json template gains `"agent"` field + agent-file write at first-run). This needs explicit owner approval per multi-component amendment rule. Recommendation: split into three coordinated amendments or one super-amendment with a unified plan; owner rules.

---

## 4. Lens 1 — Claude-leverage analysis (concrete, not handwave)

**Required research question (CLAUDE.md §"Lens 1"):** *What Claude capability does this lean on or extend?*

Three Claude Code primitives are load-bearing here:

**4.1 The subagent registration surface (`.claude/agents/<handle>.md`).**
Claude Code looks for `.claude/agents/*.md` and treats each as a subagent the session can run as. The frontmatter (`name`, `description`, optional `model`, optional `tools`) names the subagent and constrains its tool-use; the body is the system prompt. The `"agent": "<handle>"` field at the top of `.claude/settings.json` selects the default subagent for the session's main thread. This is the structural mechanism that makes "the session lands as the persona" work — Claude Code re-loads the agent body on context refresh, which is why ivers-corp's eve.md has compaction-resilient identity anchoring at the top.

**Pos-v2 leverage:** the existing `primary-persona/src/contract.py` PersonaContract is already a strict superset of what an agent file's frontmatter needs (`handle` → frontmatter `name`; one-line summary derived from `responsibilities.single_point_of_contact` → frontmatter `description`). A renderer maps contract → agent file deterministically. We do not invent new persona structure; we project the existing one onto Claude Code's surface.

**4.2 The `SessionStart` hook (already wired) + the D8 context-load gate.**
The existing `.claude/settings.json` has a `SessionStart` hook that runs `first-run.sh`. After amendment #32, the persona-layer's session-start gate composes additionalContext for every session. That existing surface remains the runtime-context anchor; the agent file is the identity anchor. Two distinct roles, both Claude-native.

**Pos-v2 leverage:** D8 already discovers the corpus, probes services, etc. We extend its `additionalContext` payload (or add a sibling contributor) to include a "starter elicitation pending" flag when the contract is starter-flagged, so the persona's first response can open the elicitation flow naturally rather than waiting for the user to ask "what are you?"

**4.3 Skills (composition opportunity, not core path).**
Claude Code's skill ecosystem provides patterns we can compose with — e.g. an "init-persona" skill the user *could* invoke later to re-run elicitation, or per-domain skills (the future Dev/SDLC plugin) that compose with the active persona's `delegates_to` field. Out of scope for this amendment but worth noting as future composition.

**Capabilities NOT used (intentionally):**
- We don't make the persona a custom Claude Code agent invoked per-session — the default-agent field is the right grain. Per-session subagent invocation would force the user to remember to invoke it.
- We don't compose the persona prompt into project-level `CLAUDE.md` (which is global to all Claude Code sessions in the project) — `CLAUDE.md` is for codebase instructions, not persona identity. Mixing them dilutes both.

---

## 5. Lens 2 — Harness + primary-persona value (concrete)

**Two required research questions (CLAUDE.md §"Lens 2"):**

**5.1 Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

**Yes — substantially.**
Today the user sits in front of a fresh-clone pos-v2 and (a) the loader fails closed, (b) the session is generic Claude. To get to "talking to my persona" they must: read primary-persona docs, find the template, copy it into `personas/<handle>/`, edit the YAML (eight required fields, four tier-action enums, three responsibilities prose, an authority boundary they don't yet have a vocabulary for), write `prompt.md`, restart the session, debug whatever validation error surfaces. That is the *exact* translation burden VALUE_PROPOSITION says the persona is supposed to absorb. The user cannot cross it because the persona that would translate it into AI-effective steps is the thing they're trying to set up.

After this work: fresh-clone session lands as a generic-but-valid persona on session one; the persona itself elicits the user's preferences in conversation; refinement is incremental, persisted automatically. The user never edits YAML. They never know YAML is there. Zero translation burden.

**5.2 Harness test.** *Does this add to the toolkit the primary persona can draw from?*

**Yes — three new toolkit primitives.**
- The contract→agent-file renderer becomes a primitive the persona layer (and any future persona-managing tool) can invoke. When a persona is autonomously authored (D5/D6 of the existing primary-persona spec), the renderer also writes the `.claude/agents/<new-handle>.md` so the new persona is immediately invocable as a Claude Code subagent — closing a current gap where authored personas are loadable but not Claude-Code-invocable.
- The starter-flag on the contract + the elicitation flow becomes the canonical "persona is being onboarded" state. Any future flow (re-onboarding, persona handoff, persona retirement) can re-use it.
- The first-run hook into the agent-file write surface lets future first-run-time contributions add to settings.json deterministically (current first_run_settings.py merges only the SessionStart stanza; this work generalises that pattern to also-merge the `"agent"` field).

---

## 6. Lens 3 — ODD authoring (acceptance criteria + constraints)

**6.1 Objective (one sentence per declared behaviour, ODD §1.2).**

A fresh clone of pos-v2 reaches "user is talking to *their* primary persona, not generic Claude" within the first interactive session, without the user editing files or running commands, through the composition of (a) Claude Code default-agent registration generated from the workspace's persona contract, (b) a starter persona scaffolded at first-run that satisfies loader validation, and (c) a conversational elicitation flow the persona itself initiates to refine the starter into the user's persona.

**6.2 Constraints.**

1. **Dependency fence.** Touches `primary-persona/` (renderer, onboarding module, starter-flag field), `workspace-bootstrap/` (scaffold extension, adapter starter-detection), `hands-off-lifecycle/` (settings.json template, agent-file write). Multi-component — owner approval gate per §10.
2. **No persona content shipped from pOS core.** The starter contract uses only valid-but-generic prose ("I'm here to help you with [domain]" with `[domain]` deliberately not filled — the elicitation fills it). The agent-file renderer composes from the contract, not from a shipped string. STATE.md rule 4 holds. The framework-tree-scan check (`PersonaInCoreError`) continues to enforce.
3. **Reversibility.** Fully reversible. The starter directory can be deleted; first-run is idempotent (already supports `partial_recovery`); agent-file writes are tracked.
4. **Budget.** First-run cold-start budget is unchanged (work is pure file-write, no LLM calls during scaffold). Elicitation is conversational and runs only when the user engages — no background cost.
5. **Authority bound.** Generated agent file's `tools:` frontmatter is omitted (default = inherit all), matching ivers-corp's pattern. Tier-action enums in the starter contract are conservative defaults (`tier_a: defer`, `tier_b: defer`, `tier_c: execute`, `tier_d: execute` — same as the existing template).
6. **Fail-closed direction.** If elicitation fails mid-conversation (user closes session, hard error), the starter contract remains in place — the next session loads it and re-prompts the elicitation. No half-state.
7. **No `--amend`.** Corrective commits only (per CDC).
8. **§2.5 audit both directions.** Every code path back to a named AC; every AC has a test.
9. **Graceful-degradation governs.** If `.claude/agents/<handle>.md` write fails (permissions, etc.), session still proceeds — generic Claude with the existing context-load gate's additionalContext is the degraded mode. Loud diagnostic, not hard halt.
10. **Step-by-step CDC where unavoidable.** If the user has explicitly turned off auto-elicitation (a future preference), the persona surfaces the elicitation as a numbered five-step list ("Open `personas/<handle>/contract.yaml`. Edit `responsibilities.single_point_of_contact:` to one sentence describing what you want me to handle for you. …"). Each step includes time-estimate ("~30 seconds"). This is the gradient-tier-2 fallback.

**6.3 Acceptance criteria (one per declared behaviour; outcome-shaped; deterministic).**

- **AC1 — fresh-clone first-run produces a valid persona directory.** After first-run completes on a clone with no `personas/` directory, `<workspace>/personas/<handle>/contract.yaml` and `<workspace>/personas/<handle>/prompt.md` exist; `PersonaLoader(workspace_root).load()` returns a single `LoadedPersona` whose `contract.is_starter is True`. Touches: `workspace-bootstrap`, `primary-persona`.
- **AC2 — fresh-clone first-run wires Claude Code default-agent.** After first-run, `<workspace>/.claude/settings.json` contains `"agent": "<handle>"` at top level (preserving prior keys per the existing settings-merge logic), and `<workspace>/.claude/agents/<handle>.md` exists with frontmatter matching the loaded contract (`name == handle`, `description` derived from `responsibilities.single_point_of_contact`, `model: inherit`). Touches: `hands-off-lifecycle`, `primary-persona`.
- **AC3 — fresh-clone Session 1 lands as the persona.** A test that simulates a fresh-clone first-run + a SessionStart hook invocation produces an `additionalContext` payload that names the loaded persona (handle, given_name) and signals starter-elicitation-pending; the test asserts the persona's identity-anchor block is present in `.claude/agents/<handle>.md`'s body. Touches: `primary-persona`.
- **AC4 — starter contract is valid-by-construction.** A persona contract loaded from `<workspace>/personas/<handle>/` after first-run passes `PersonaContract.model_validate()` without modification (no required field missing; no validator raising). Touches: `primary-persona`.
- **AC5 — elicitation persists user input back to the contract.** Given a starter-flagged contract and a synthetic elicitation transcript with answers to each elicitation question, the onboarding module writes the answers back via `to_yaml()`; reloading produces a contract with `is_starter is False` and the user's responses in the prose fields. Touches: `primary-persona`.
- **AC6 — re-running first-run on a workspace with a non-starter persona is a no-op.** First-run on a workspace whose `personas/<handle>/contract.yaml` has `is_starter: false` does NOT overwrite, does NOT regenerate the agent-file, and does NOT re-trigger elicitation. Touches: `workspace-bootstrap`, `hands-off-lifecycle`.
- **AC7 — agent-file regenerates when the contract changes.** Editing the contract (e.g. given_name change) and triggering the persona-layer's reload writes a fresh `.claude/agents/<handle>.md` whose frontmatter `description` reflects the new contract content. Touches: `primary-persona`.
- **AC8 — graceful failure on agent-file write.** If `.claude/agents/<handle>.md` cannot be written (permissions, disk full, settings.json malformed beyond merge), first-run completes with the persona scaffold in place, surfaces a structured diagnostic via the existing observability surface, and the SessionStart hook proceeds. The loader still loads the persona; the session degrades to generic-Claude-with-context-load-gate, not a hard halt. Touches: `hands-off-lifecycle`, `primary-persona`.
- **AC9 — pOS core ships zero persona content.** The framework-tree scan continues to raise `PersonaInCoreError` if any persona directory other than `templates/persona-template/` (with reserved handle `example-persona`) appears in pOS-core paths. The renderer composes agent-file content from the loaded contract at first-run time, not from a string shipped in the framework. Touches: `primary-persona`.
- **AC10 — observability for the elicitation lifecycle.** Each elicitation question asked, each answer received, each contract write-back, and each starter-flag transition emits a span/event under `pos.persona.onboarding.*`. Touches: `primary-persona`.

Behaviour count: 10. Criterion count: 10. Counts match (ODD §3.3 forward).

**6.4 No method-in-acceptance.** Each AC names what must be true; method (file paths inside `primary-persona/src/`, function signatures, validator wiring) belongs in the builder's plan when this work is dispatched.

---

## 7. Risks (with named mitigations)

- **R1 — Persona content authored under time pressure is weak.** Elicitation runs in a fresh, low-context first session; the user may rush through. Mitigation: starter is valid by construction, so a rushed elicitation produces a working persona; refinement is supported as a re-runnable scope (future amendment can add a `re-elicit` slash command, see §11). The first run is "good enough"; not "definitive."
- **R2 — Persona elicitation blocks first-run completion.** Mitigation: elicitation is post-first-run, conversational, *skippable*. First-run completes when the scaffold is in place; the persona is present (via starter) before any elicitation runs. The user can exit the elicitation at any time and the starter remains.
- **R3 — Claude Code's default-agent surface changes in a future release.** Anthropic could rename `"agent"`, change the `agents/` directory location, alter frontmatter shape. Mitigation: the renderer is a single primitive — adapt it once. The agent-file write is detected as the surface that changed, not the persona contract; the contract remains stable. Idea 1 step 4 (CLAUDE_CAPABILITIES.md refresh) is the upstream watch.
- **R4 — Contract drifts from agent-file over time.** Mitigation: D4 (renderer is the single source of truth, regenerates on contract change). Agent-file is never hand-edited; if it is, the next contract change overwrites it. Add an AC8-like halt if an in-the-wild agent-file is detected to differ from the renderer's output (drift detector — defer to follow-up).
- **R5 — User refuses to engage with elicitation and never edits the starter.** Mitigation: that's an acceptable terminal state — they're using a generic-but-functional persona. The persona surfaces this gently in subsequent sessions ("I'm still on starter contract; want to refine?") with bounded frequency (≤ 1 reminder per N sessions, configurable).
- **R6 — Multi-component amendment introduces coordination complexity.** Mitigation: split per §10 halt-trigger guidance; owner rules. If split, `primary-persona` ships first (renderer + onboarding + starter-flag), `workspace-bootstrap` second (scaffold extension), `hands-off-lifecycle` third (settings.json + agent-file write). Each can be sealed independently.
- **R7 — Conflict with autonomous-authoring (D5/D6) in v1.2 addendum.** A persona authored by the autonomous-authoring pipeline is not a starter; it should bypass elicitation. Mitigation: starter-flag is set by first-run scaffold only; authored personas are persisted with `is_starter: false` (and their existing introduction protocol governs).

---

## 8. Halt triggers (for the eventual builder)

- **H1.** If, during build, the `.claude/agents/<handle>.md` shape Claude Code currently accepts has changed from what's documented at https://docs.claude.com/en/docs/claude-code/sub-agents (frontmatter fields, body parsing), halt and signal — the renderer's projection contract changes.
- **H2.** If the loader's existing fail-closed semantics (PersonaDirectoryNotFoundError) cannot be preserved (e.g. starter detection requires changing the load contract), halt — that's a downstream-visible change requiring re-coordination with telegram-interface and other consumers.
- **H3.** If first-run partial-recovery (existing) and starter-scaffold (new) interact in a way that overwrites a user-edited persona, halt — AC6 must hold even on partial recovery.
- **H4.** If multi-component scope expands beyond the three named (e.g. memory-system needs to be touched to record onboarding episodes), halt and re-coordinate scope.
- **H5.** If the conversational elicitation requires an LLM call inside the persona-layer's first-run path (rather than running as a normal user-turn after first-run completes), halt — that's a cost-governance concern that wasn't budgeted.

---

## 9. ODD §2.5 reverse audit checklist (for the builder, before seal)

For each diff hunk:
1. Point at the AC it satisfies.
2. If a hunk handles a case no AC names (a platform branch, a settings field, a defensive `if`), either re-extend up with an AC or delete the code.
3. Tests that exercise non-AC paths are also §2.5 violations (per `odd-in-pos.md` §9.7) — delete or re-extend.
4. Confirm `templates/persona-template/` remains the only persona-shaped directory in pOS-core paths; the framework-tree scan must continue to pass.

---

## 10. Multi-component amendment halt (per CLAUDE.md operational caution §2.5)

This work touches three sealed components: `primary-persona`, `workspace-bootstrap`, `hands-off-lifecycle`. Per CLAUDE.md ("multi-component amendments need explicit owner approval"), the owner must rule on:

- **Approve as a single super-amendment** — one plan, one dispatch, one seal across all three components. Amendment manifest names all three packages in `allowed_prefixes`. Highest cohesion, largest blast radius.
- **Approve as three coordinated amendments** — primary-persona first (renderer, onboarding, starter-flag), workspace-bootstrap second (scaffold writes personas + flags), hands-off-lifecycle third (settings.json + agent-file). Each seals independently. Lowest blast radius, more bookkeeping.
- **Decline** — defer until prerequisite work (e.g. CLAUDE_CAPABILITIES.md from Idea 1 Step 1) lands.

Recommendation: **three coordinated amendments**, in the order listed. Lower risk; primary-persona's standalone seal validates the renderer + onboarding before the other two depend on it. Owner rules.

---

## 11. Out of scope (future work, not this plan)

- **Re-elicitation slash command.** A `/persona refine` or similar that re-opens elicitation on demand. Defer.
- **Persona-handoff during ongoing work.** If the user wants to swap personas mid-session. The autonomous-authoring + introduction protocol covers the new-persona case; explicit-swap is future.
- **Domain-aware starter prompts.** A starter that detects "this workspace looks like a finance/cooking/legal workspace" and pre-fills domain hints. Defer; needs the workspace-context surface that doesn't yet exist.
- **Slug collision detection** (FUTURE_IDEAS.md Idea 9) interacts with `<handle>` collisions across workspaces. Currently out of scope — handles are per-workspace, not host-global.
- **Translating ivers-corp's hooks/rules/skills shape into pos-v2.** The `.claude/hooks/` and `.claude/rules/` patterns ivers-corp uses are interesting structural references for future amendments but are NOT part of this scope. This work covers the default-agent surface only.

---

## 12. Where this plan sits

- **Plan path:** `docs/plans/first-run-primary-persona-default-agent-wiring.md` (this file).
- **Spec backing:** v1.0 lines 152, 153, 311; v1.2 addendum (proposal §1.0 mapping rows).
- **Component proposals consulted:** `docs/archive/component-research/primary-persona-loader/proposal.md`, the v1.2 addendum in the objectives spec, the existing first-run scaffold in `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`.
- **Reference (read-only, structural shape only, no content lift):** `~/ivers-corp/.claude/settings.json` for the `"agent"` field placement; `~/ivers-corp/.claude/agents/<file>.md` frontmatter shape (the *shape*, not any persona content). No persona prose, voice, or domain content from ivers-corp informs this plan.

---

## 13. Owner-action summary (the rule list)

The owner does not need to read sections 4–11 to act. Rule on:

- **D1** — Default-agent mechanism. Recommendation: subagent + `"agent"` field. Yes/no/discuss.
- **D2** — Elicitation pattern. Recommendation: starter + conversational. Yes/no/discuss.
- **D3** — Default handle. Recommendation: free-text with `primary` default. Yes/no/discuss.
- **D4** — Agent-file source. Recommendation: rendered from contract. Yes/no/discuss.
- **D5** — Elicitation owner. Recommendation: `primary-persona/onboarding.py` triggered by D8 gate. Yes/no/discuss.
- **D6** — Amendment classification. Recommendation: three coordinated amendments. Yes/no/discuss / split differently.

After rulings: research-before-plan CDC says non-trivial new work needs a research artefact. This plan doc is the *plan*, drawing on the existing research surface (primary-persona research.md, the existing first-run amendments, ivers-corp's structural reference). A separate short research artefact at `docs/plans/research/first-run-primary-persona-default-agent-research.md` may be required before dispatch — owner ruling on the multi-component split tells us how many builder dispatches are needed and whether each needs its own research doc or shares this one.
