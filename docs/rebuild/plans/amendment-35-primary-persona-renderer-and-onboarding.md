# Plan — Amendment #35: primary-persona renderer + onboarding module + starter-flag

**Status:** authored 2026-04-25, awaiting brief-dispatch.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment tip:** captured at brief-dispatch time.
**Amendment number:** `#35` placeholder; renumbered at dispatch per the convention amendments #29–#33 followed. If a competing amendment lands first, this plan is the next sequential number after the new tip.
**Filename:** family-named (`primary-persona-renderer-and-onboarding`) so the path survives renumbering.
**Companion research:** none authored separately — research findings inlined in §2 + §5; the master plan (`docs/rebuild/plans/first-run-primary-persona-default-agent-wiring.md`) carries the full investigative narrative this sub-plan summarises. Per the same precedent as amendment #34, an external research artefact would be ceremony rather than signal.

**Sibling amendments.** This is **amendment 1 of 3** in the persona-setup family. Its renderer is the dependency root for amendments #36 (workspace-bootstrap scaffold) and #37 (hands-off-lifecycle Claude-Code default-agent wiring). #36 and #37 must not begin until #35 has sealed.

- **#35 (this plan):** `primary-persona` — `to_agent_md()` renderer + `onboarding.py` module + `is_starter` field on the contract.
- **#36:** `workspace-bootstrap` — first-run scaffold writes `<workspace>/personas/<handle>/`. Depends on #35's renderer existing (used at #37, but #36 produces the contract that #37 will render).
- **#37:** `hands-off-lifecycle` — `.claude/settings.json` `"agent": "<handle>"` field + `.claude/agents/<handle>.md` written from #35's renderer. Depends on #36's scaffold output.

---

## 1. Summary / TLDR

The primary-persona layer gains three additive surfaces inside its existing fence:

1. **`to_agent_md()` renderer** — a deterministic projection from a loaded `PersonaContract` to the Claude-Code subagent-file shape (`name`/`description`/`model` frontmatter + identity-anchor body + persona prompt body). Pure function; no I/O; idempotent given the same contract input.
2. **`onboarding.py` module** — owns the conversational starter-elicitation flow (3–5 questions, persisted via `to_yaml()` write-back, flips `is_starter` to `False` on completion). The module exposes a contributor that the existing D8 context-load gate registers when it sees a starter-flagged contract; the conversation itself runs as the persona's normal user turns, not as a setup wizard.
3. **`is_starter` field on `PersonaContract`** — a Pydantic-validated boolean, default `False`, that the workspace-bootstrap scaffold (amendment #36) sets to `True` on freshly-scaffolded persona dirs and that elicitation flips back to `False` on completion.

Nothing in this amendment touches `workspace-bootstrap/` or `hands-off-lifecycle/` source. The renderer is **only** declared and tested here; amendment #37 calls it. The starter-elicitation flow runs only when triggered by a starter-flagged contract, which only #36 produces, so this amendment seals against tests that simulate starter contracts via fixtures (no cross-component dependency for AC closure).

This shape lets the renderer and onboarding module ship + seal independently, validating the contract→agent-file projection and the elicitation transcript→`to_yaml()` write-back before either downstream amendment depends on them.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5 operational caution)

**Named spec objectives this amendment satisfies:**

- **v1.2 addendum R16 — Framework-not-content** (`docs/rebuild/spec/pos-v2-objectives-spec.md` §348–356): *"pOS core ships the persona contract, loader, validator, …, the framework for handling personas. pOS core ships no persona content."* The renderer and onboarding module are framework, not content; the renderer composes content at runtime from the workspace-supplied contract.
- **v1.0 line 152 — Non-tech users — low-friction onboarding** (`docs/rebuild/spec/pos-v2-objectives-spec.md` §152): *"Non-tech users — four behaviours (low-friction onboarding, persona in every session, auto-create+explain, anti-deskilling principle)."* The onboarding module makes "low-friction onboarding" land as conversation rather than YAML editing — the persona translates the user's natural-language self-description into contract fields.
- **v1.0 line 311 — Onboarding-time elicitation pattern** (`docs/rebuild/spec/pos-v2-objectives-spec.md` §311): *"Optional channels are surfaced during onboarding with a walk-through of whatever external setup they need; the user completes setup without leaving onboarding."* Establishes onboarding-time elicitation of user-owned content as a spec-named pattern; this amendment re-applies that pattern to persona content.
- **primary-persona-loader proposal D1 + D2** (`docs/rebuild/components/primary-persona-loader/proposal.md` §66–78): the contract-and-loader deliverables this amendment extends with a second projection (contract→agent-file) and a starter-flag field.

**Sealed-component amendment classification.** Single sealed component (`primary-persona`). Owner ruled the persona-setup work as three coordinated sealed-component amendments per master plan §10 D6.

---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage

**What Claude capability does this lean on or extend?**

The renderer projects the workspace's `PersonaContract` onto Claude Code's subagent-file shape (`.claude/agents/<handle>.md`). That shape — frontmatter `name`/`description`/`model` + body — is the structural mechanism Claude Code provides for persisting subagent identity across the session and through compaction. The renderer is Claude-leverage in the strictest sense: instead of inventing a parallel persona-presence mechanism, the amendment composes onto the Claude-native primitive.

**What Claude capability does the onboarding module lean on?**

The onboarding module composes onto the existing D8 SessionStart context-load gate (amendment #32) — the gate's contributor registry is the surface the elicitation contributor registers against. The conversation itself is just normal user turns; no new Claude Code primitive is invoked.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** *Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

The renderer alone reduces no user-visible burden — it's a framework primitive. The onboarding module **substantially** reduces translation burden: instead of forcing the user to read primary-persona docs and edit YAML before they can talk to their persona, the module lets the persona elicit its own contract content from the user in conversation. The user's natural-language self-description ("I want help with finance and life-admin; call me Luke") is the input; the contract fields are the AI-effective output the loader needs. That is the value-proposition pattern in its purest form — and it can only happen if the framework provides a starter-flag and an elicitation surface, which is what this amendment ships.

**AC-trace to AC.PO.1:**

- **AC35.1 → AC.PO.1.** Starter contract validates by construction → loader passes on a fresh-scaffolded workspace → persona is present from session one → user is talking to the persona, not generic Claude → translation burden absorbed.
- **AC35.2 → AC.PO.1.** Elicitation persists user input back to the contract → user's natural-language self-description becomes the contract's prose fields → persona refines into the user's persona without YAML editing → translation burden absorbed.
- **AC35.3 → AC.PO.1.** Renderer is deterministic given the contract → the agent-file used at session start always reflects the latest contract → user never sees stale identity → translation burden absorbed (no "the agent is wrong, I edited the contract" debugging by the user).
- **AC35.4 → AC.PO.1.** No persona content shipped from pOS core → workspace persona is the user's, not a pOS default the user has to override → translation burden absorbed (user doesn't have to learn what to overwrite).
- **AC35.5 → AC.PO.1.** Starter-pending signal lands in additionalContext on user-prompt-submit → persona's first turn opens the elicitation rather than the user having to ask "what are you?" → translation burden absorbed.
- **AC35.6 → AC.PO.1.** Starter-flag is unset post-elicitation → re-runs of the gate don't repeatedly open elicitation against an already-onboarded contract → user is never asked the same question twice → translation burden absorbed.
- **AC35.7 → AC.PO.1.** Observability for the elicitation lifecycle → operator can audit what was elicited, when, and how → translation surface itself is auditable, which lets the persona trust its own state across compaction (no "did I already ask?" ambiguity).

**Harness test.** *Does this add to the toolkit the primary persona can draw from?*

Yes — three new toolkit primitives:

1. **The renderer** is a primitive any persona-managing tool can invoke. When a future autonomous-authoring pipeline (D5/D6 of the proposal) creates a new persona, the renderer also projects it onto a Claude Code subagent file, closing today's gap where authored personas are loadable but not Claude-Code-invocable.
2. **The starter-flag + elicitation flow** becomes the canonical "persona is being onboarded" state. Re-onboarding, persona handoff, and persona retirement (future scopes) can re-use the same flag.
3. **The contributor surface for starter-pending signal** extends the D8 gate's contributor registry with one more contributor kind, demonstrating the registry's role as the persona-layer's structural composition surface.

**AC-trace to AC.PO.2:**

- **AC35.3 → AC.PO.2.** Renderer is reusable from any callsite that has a contract — adds a primitive to the toolkit.
- **AC35.4 → AC.PO.2.** Framework-not-content invariant preserved → toolkit's purity preserved (the harness extends what the persona can do without injecting persona-shaped content into the toolkit).
- **AC35.7 → AC.PO.2.** Observability spans → toolkit's audit surface extended with persona-onboarding events.

### Lens 3 — ODD authoring

The plan authors seven outcome-shaped acceptance criteria (§4) under the §2.5 reverse-direction discipline: each AC names what must be true; method (file paths, function signatures, validator wiring) is the builder's call. The seven ACs cover the four declared behaviours of this amendment plus the cross-cutting framework-not-content + observability + seal-diff invariants. Behaviour-count check at §5.

ODD §2.5 reverse-direction check: the renderer, the onboarding module, and the `is_starter` field map directly to AC35.3, AC35.2/AC35.5/AC35.6, and AC35.1 respectively. No platform branches, no defensive `if`s without an AC backing them, no "might be useful later" surface.

---

## 4. Acceptance criteria (AC35.x)

Each AC maps to at least one test function named `test_AC35_<n>_<slug>` in `primary-persona/tests/`.

### AC35.1 — `is_starter` field exists on the persona contract and validates

The `PersonaContract` Pydantic model exposes a Boolean `is_starter` field with default `False`. A YAML containing `is_starter: true` round-trips through `model_validate` → `to_yaml()` → `model_validate` and produces an equivalent contract. A YAML omitting the field validates with `is_starter: False`. A YAML containing a non-Boolean value rejects with a clear validation error. No existing v1.0 / v1.1 / v1.2 contract field is renamed or removed.

**Test shape:** parametric round-trip across {`is_starter: true`, `is_starter: false`, omitted, `is_starter: "yes"` (rejection)}. Asserts the existing `D1` contract suite still passes unchanged.

**Maps to:** v1.2 R16 framework-not-content (the field is a framework-level metadata bit on a contract whose content remains workspace-supplied) → AC.PO.1.

### AC35.2 — `to_agent_md()` projects a contract onto a Claude-Code subagent-file shape

A pure function `to_agent_md(contract: PersonaContract) -> str` returns a string whose parsed YAML frontmatter contains `name == contract.handle`, `description` derived from `contract.responsibilities.single_point_of_contact` (one sentence; precise derivation is method), and `model: inherit` (or omitted, builder's call provided the result is a valid Claude Code subagent file). The body contains an identity-anchor block (compaction-resilience marker — content is method) followed by a persona-prompt block derived from `contract` + the workspace's `prompt.md`. Calling the function twice with the same contract returns identical strings (idempotence).

**Test shape:** load a fixture contract via the existing test harness; call `to_agent_md`; parse the frontmatter as YAML; assert the three named fields. Round-trip-stability: render twice, assert string equality. Build a malformed contract fixture (programmatically — not via on-disk content) and assert renderer raises a structural exception, not silent garbage.

**Maps to:** v1.0 line 153 (persona-presence asserted by session-start; the agent file is the structural anchor) + primary-persona-loader proposal D1 → AC.PO.1 + AC.PO.2.

### AC35.3 — `onboarding.py` produces a contributor for starter-pending signal

The `onboarding` module exposes a function (name is method) that returns a contributor registrable against the existing D8 `ComposedContextPayload` registry. When invoked under a starter-flagged contract, the contributor produces an `additionalContext` block whose textual content carries a starter-pending marker (presence is the test, exact wording is method). When invoked under a non-starter-flagged contract, the contributor produces an empty contribution (or, equivalently, declines to contribute).

**Test shape:** register the contributor against a stand-in registry; invoke under a starter-flagged contract fixture; assert non-empty contribution carrying the marker. Invoke under a non-starter contract; assert empty contribution. Late-binding of the contributor after registry composition still picks up on subsequent invocations (registry is the authority).

**Maps to:** v1.0 line 152 (low-friction onboarding) + v1.0 line 311 (onboarding-time elicitation) → AC.PO.1.

### AC35.4 — Elicitation transcript produces a contract write-back via `to_yaml()`

Given a starter-flagged contract and a synthetic transcript carrying answers to each elicitation question, the `onboarding` module writes the answers back to the contract via the existing `to_yaml()` write-back surface. Reloading the persisted YAML produces a contract whose prose fields contain the answers and whose `is_starter` is `False`. A transcript missing answers to required questions leaves the contract unchanged (or partially updated with `is_starter` still `True`, depending on builder ruling — which is itself a method choice but the AC bounds the outcome: incomplete elicitation does not flip `is_starter`).

**Test shape:** seed a starter contract on tmpfs; build a synthetic transcript fixture; invoke the onboarding module's write-back; reload from tmpfs; assert prose fields contain the synthetic answers; assert `is_starter is False`. Negative case: incomplete transcript → contract still starter-flagged.

**Maps to:** v1.0 line 152 (low-friction onboarding) + v1.0 line 311 (onboarding-time elicitation) + v1.2 R16 (workspace-supplied content) → AC.PO.1.

### AC35.5 — Renderer regenerates on contract change

Given a freshly-loaded contract, calling `to_agent_md()` and then mutating the contract (e.g., `contract.given_name` change) and calling `to_agent_md()` again produces a string whose `description` (or whichever frontmatter field reflects the changed prose) differs between the two calls. The renderer reads from the contract argument every call; it has no caching that would shadow a subsequent contract change.

**Test shape:** render twice with the same contract → string equality. Render, mutate, render → string inequality on the changed field.

**Maps to:** v1.0 line 153 (persona present every session) → AC.PO.1.

### AC35.6 — pOS core ships zero persona content

The framework-tree scan continues to raise `PersonaInCoreError` if any persona directory other than `primary-persona/templates/persona-template/` (with reserved handle `example-persona`) appears in pOS-core paths. The renderer composes agent-file content from the loaded contract at render time, not from a string shipped in the framework. `to_agent_md`'s output for a fixture contract under `tests/` does not contain any string copied from a hardcoded persona-prose constant inside the framework source.

**Test shape:** the existing D2 framework-tree-scan test passes unchanged. New assertion: `to_agent_md`'s output, with the contract's prose fields stubbed to known unique sentinel strings, contains those sentinels — proving the prose comes from the contract argument, not from a framework-level constant.

**Maps to:** v1.2 R16 framework-not-content → AC.PO.2 (toolkit purity).

### AC35.7 — Observability for the renderer + onboarding lifecycle

Each renderer call, each onboarding question dispatched, each answer recorded, each contract write-back, and each `is_starter` transition emits a span/event under `pos.persona.onboarding.*` (or the existing observability namespace the persona layer uses; exact naming is method). The events carry workspace slug + handle as attributes.

**Test shape:** capture spans/events through the existing OTel test harness D9 establishes; exercise the AC35.2–AC35.4 paths; assert the expected event names + attributes are present.

**Maps to:** v1.1 R11 OTel observability + primary-persona D9 → AC.PO.2 (toolkit's audit surface extended).

### AC35.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `primary-persona/` (source + tests),
- `docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding*` (this plan + manifest),
- `docs/rebuild/plans/first-run-primary-persona-default-agent-wiring.md` (master plan; reference-only edit at most),
- universal-paths admissions per §10.

Anything outside that set is a halt condition. Sealed-component source outside `primary-persona/` is never admitted by this amendment.

---

## 5. Behaviour-count check (ODD §3.3 forward)

| Behaviour (§1) | Criterion/criteria |
|---|---|
| 1. `is_starter` field exists on the contract | AC35.1 |
| 2. `to_agent_md()` renderer projects contract → agent-file shape | AC35.2, AC35.5 (regeneration), AC35.6 (framework-not-content invariant) |
| 3. Starter-pending signal contributor exposed | AC35.3 |
| 4. Elicitation transcript → contract write-back | AC35.4 |
| cross-cutting | AC35.7 (observability), AC35.S (seal-diff) |

Four declared behaviours; seven ACs cover them plus the cross-cutting invariants. No method-in-AC.

---

## 6. Hard constraints

1. **No `--amend`.** Corrective commits only.
2. **Scope fence — `primary-persona/` only.** Source under `primary-persona/src/`. Tests under `primary-persona/tests/`. Template directory under `primary-persona/templates/persona-template/` permitted (existing surface). Any source edit outside `primary-persona/` is a halt (§9).
3. **No edit to existing `primary-persona` modules unless minimally required for the additive surface.** Specifically: `contract.py` gains the `is_starter` field; `loader.py`, `monitor.py`, `compaction.py`, `context_composer.py`, `session_start_gate.py`, `memory_consumer.py`, `creation_triggers.py`, `authoring.py`, `introduction.py`, `retirement.py`, `observability.py` should not need source edits to satisfy AC35.1–AC35.7. If any do, the builder names which and why before edit.
4. **Reversibility.** Fully additive at the primary-persona surface. Removing the new `to_agent_md`, `onboarding.py`, and `is_starter` field returns the layer to its pre-amendment state. (Amendments #36 and #37 will introduce dependencies on these surfaces; that's their fence, not this one's.)
5. **No new runtime deps.** Permitted runtime deps per the primary-persona proposal apply unchanged.
6. **No persona content shipped from pOS core.** Renderer composes from contract; onboarding-question prose lives in the framework as question-shape templates, not as persona prose. The framework-tree scan continues to enforce.
7. **Fail-closed direction.** If the elicitation transcript is malformed or incomplete, the contract remains starter-flagged; the next session re-opens elicitation. No silent half-state.
8. **Authority bound.** Builder may refine question count, question shape, marker wording, and observability event names. Builder may not relax the framework-not-content invariant or change the contributor-registry contract D8 established.
9. **CDC adherence.** Plan-before-code, background-agent default, scope-only dispatch, the three amendment-dispatch speedups.
10. **`pos-amend apply --dry-run` green** is a hard prereq per amendment #22.

---

## 7. Out of scope (explicit)

- **Workspace-bootstrap scaffold work** (amendment #36) — this amendment exposes the surfaces #36 will use; it does not modify scaffold code.
- **Settings.json + agent-file write at first-run** (amendment #37) — this amendment exposes the renderer that #37 will call; it does not write any file under `<workspace>/.claude/`.
- **Re-elicitation slash command** (master plan §11) — defer.
- **Persona-handoff during ongoing work** (master plan §11) — defer.
- **Domain-aware starter prompts** (master plan §11) — defer.
- **Slug collision detection** (FUTURE_IDEAS Idea 9) — orthogonal, unaffected.
- **Drift-detector for hand-edited agent files** (master plan R4 mitigation) — defer.
- **Default handle selection at first-run** (D3 in master plan) — that's a bootstrap-time concern; the renderer here just consumes whatever handle the contract carries.
- **Onboarding-as-skill / Claude Code skill alternative** (master plan D5 (d)) — out of scope; D5(a) selected.

---

## 8. Implementation order (suggested — builder's call to refine)

Per scope-only-dispatch CDC, this section is advisory; the builder authors the actual order in their builder-plan.

1. Read session-start corpus per CLAUDE.md.
2. Read master plan + amendment #32's seal narrative (to understand the registry surface) + amendment #33's plan (for the resolve-workspace-slug pattern precedent) + this plan.
3. Write builder-plan to `docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding.builder-plan.md` naming specific files + symbols expected to be touched.
4. Land the `is_starter` field on `PersonaContract`. Verify D1 contract suite still passes.
5. Land `to_agent_md()` in a new module (`primary-persona/src/agent_md.py` or co-located in `contract.py` — builder's call). Verify AC35.2/AC35.5/AC35.6.
6. Land `onboarding.py`. Wire its contributor into the existing D8 registry surface. Verify AC35.3/AC35.4.
7. Wire observability spans. Verify AC35.7.
8. Run AC35.1–AC35.7 + the existing primary-persona seal-diff suite.
9. `pos-amend apply --dry-run` green gate.
10. Amendment commit (descriptive, builder's wording).
11. Seal commit via `pos-amend seal`; sidecar bump + narrative append.
12. Post-seal: seal-diff-only across all sealed components.

---

## 9. Halt triggers (builder halts + signals owner)

1. **Cross-component scope expansion beyond `primary-persona/`.** Any required source edit to any other sealed component → halt.
2. **`is_starter` field cannot be added without breaking the existing D1 contract suite.** Halt; contract evolution requires owner ruling.
3. **The renderer's frontmatter shape conflicts with what Claude Code currently accepts** (per https://docs.claude.com/en/docs/claude-code/sub-agents). Halt; the projection contract changes.
4. **The D8 contributor registry surface from amendment #32 cannot accept a starter-pending contributor without a registry contract change.** Halt; that's a registry evolution requiring owner ruling.
5. **An ODD-violating shape becomes strongly required** (method-in-AC, non-objective code path, silent exception). Halt; owner rules.
6. **`pos-amend apply --dry-run` red** — halt.
7. **A test for AC35.1–AC35.7 cannot be written deterministically** — halt.
8. **Amendment-dispatch wall-time exceeds 60 minutes** — halt with current state. Owner rules on split vs push-through.

---

## 10. Bookkeeping (`pos-amend` manifest stub)

The manifest will be authored at brief-dispatch time once the amendment number is finalised. Stub:

```yaml
schema_version: 1
amendment:
  number: 35
  slug: primary-persona-renderer-and-onboarding
  title: "primary-persona to_agent_md renderer + onboarding module + is_starter field"

# BASELINE: <pre-amendment tip captured at brief-dispatch>. Most
# recent primary-persona seal commit is a6d6f6c (chore(seals):
# memory-consumer-wiring seal — primary-persona at 0ee6b05).
baseline: <captured-at-dispatch>
plan: docs/rebuild/plans/amendment-35-primary-persona-renderer-and-onboarding.md

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
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md

narrative:
  target: primary-persona/seals/SEAL_COMMIT.renderer-and-onboarding
  body: |
    # Amendment #35 — primary-persona renderer + onboarding module + is_starter
    ...
    # Body authored at seal time; describes:
    #  - to_agent_md() projection contract
    #  - onboarding.py contributor registration against the
    #    amendment-#32 D8 registry
    #  - is_starter field default-False addition to PersonaContract
    #  - framework-not-content invariant preserved
    #  - downstream amendments #36 (workspace-bootstrap scaffold)
    #    and #37 (hands-off-lifecycle agent-file write) consume the
    #    renderer + starter-flag landed here
```

---

## 11. Decisions remaining for the build agent

The following items remain method-level builder choices within this scope. Master plan recommendations are cited but not pinned here — the builder rules from the master plan plus the AC outcomes.

- **D-build.1 — Renderer module location.** New `primary-persona/src/agent_md.py` vs co-located in `contract.py`. **Master-plan recommendation:** master plan §6.2 implicit — a small primitive co-owned by primary-persona; ~30 lines. **Builder's call within scope.**
- **D-build.2 — Onboarding question count + wording.** Master plan D2(d) says "3–5 questions" + lists candidates ("what should I call you?", "what should I call myself?", "what kinds of work?"). **Master-plan recommendation:** five questions or fewer, two minutes total, every question skippable. **Builder's call within scope** — the AC measures whether elicitation persists, not which questions ran.
- **D-build.3 — Identity-anchor block content.** Master plan §4.1 references ivers-corp's compaction-resilience anchor pattern. **Master-plan recommendation:** structurally identical to ivers-corp's shape, content authored from the workspace's own contract (no ivers-corp prose). **Builder's call within scope.**
- **D-build.4 — Starter-pending marker wording in additionalContext.** Plain-language trigger for the persona's first turn to open elicitation. **Master-plan recommendation:** marker is structurally detectable (e.g., a sentence beginning with a known prefix); exact wording is the persona's voice + the framework's structural marker composed. **Builder's call within scope.**

These four are surfaced to make the dispatch brief tighter; they are not blockers for plan approval.

---

## 12. Source plan (historical context)

This sub-plan derives from the master research+plan artefact:

- **Master plan:** `docs/rebuild/plans/first-run-primary-persona-default-agent-wiring.md` — covers the full investigation, all six master-plan decisions (D1–D6), the three-lens analysis applied to the combined scope, the ten master-plan ACs (AC1–AC10), and the multi-component-amendment classification per §10.

The owner ruled (post-master-plan) that the work ships as **three coordinated sealed-component amendments** rather than one super-amendment. This file is **amendment 1 of 3**. Amendment 2 (`amendment-36-workspace-bootstrap-persona-scaffold.md`) and amendment 3 (`amendment-37-hands-off-lifecycle-default-agent-wiring.md`) are sub-plans of the same master.

Master-plan AC ↔ this-plan AC mapping (for traceability):

| Master AC | This-plan AC | Note |
|---|---|---|
| AC4 (starter contract is valid-by-construction) | AC35.1 | The field this AC needs is added here; the validation outcome on freshly-scaffolded YAML is verified at AC36.1 in amendment #36. |
| AC9 (pOS core ships zero persona content) | AC35.6 | Renderer does not ship persona prose. |
| AC5 (elicitation persists user input back to the contract) | AC35.4 | Onboarding module landed here. |
| AC7 (agent-file regenerates when the contract changes) | AC35.5 | Renderer regeneration verified here; the actual file write occurs in amendment #37. |
| AC10 (observability for the elicitation lifecycle) | AC35.7 | Spans emitted from the persona layer. |
| AC3 (fresh-clone Session 1 lands as the persona — additionalContext side) | AC35.3 | Starter-pending contributor here; identity-anchor block in agent file at amendment #37. |

Master ACs 1, 2, 6, 8 land in amendments #36 + #37.

---

## 13. Dispatch-time additions (brief-phase material)

When the brief is drafted for the build dispatch, it will carry these CDC + ODD enforcement requirements verbatim:

- Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. No cd-out.
- Session-start corpus read mandatory before any code edit.
- Plan-before-code: builder writes its own builder-plan to disk before touching source.
- ODD §2.4 + §2.5: no method-in-acceptance, no non-objective-backed code.
- Strong-ODD-adherence: halt if the builder believes an ODD break is strongly required — do not silently apply.
- Scope-only downstream dispatches: if the builder spawns sub-agents, the brief is scope, not method.
- No `git commit --amend`.
- Amendment-dispatch speedups: narrow test scope to `primary-persona/` + seal-diff on others; skip pre-seal full rerun; methodology snippets inlined.

---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.1 through D-build.4 to the builder. This
section records the choices made and the rationale.

### D-build.1 — Renderer module location: new module `primary-persona/src/agent_md.py`

A standalone module rather than co-location in `contract.py`.
Co-locating would couple the persona-data shape with its Claude-Code
projection surface; a separate module keeps `contract.py`'s public
surface unchanged for the existing D1 contract suite and lets
AC35.2 / AC35.5 / AC35.6 tests target a single import path
(`src.agent_md.to_agent_md`).

**Rationale:** master-plan §6.2 cites ~30 lines of projection logic;
the AC's idempotence + sentinel-trace + structural-rejection
properties are easier to verify against a focused module than a
mixed contract+projector module.

### D-build.2 — Onboarding question count: three questions

`ONBOARDING_QUESTIONS` carries three entries: `user_name`,
`persona_given_name`, `domain_focus`. Lower bound of master plan
D2(d)'s 3–5 range.

**Rationale:** AC35.4 measures (a) given_name write-back,
(b) responsibilities prose write-back, and (c) the transcript-
flip outcome (complete vs. incomplete). Three is the minimum that
exercises all three load-bearing paths; fewer skips one;
more dilutes the negative-case fidelity (incomplete-transcript
preserves `is_starter`). The user_name question is intentionally
recorded as transcript metadata (event-only) without a contract
write-back in this amendment's scope — it surfaces for downstream
amendments that may write a workspace prompt.md surface.

### D-build.3 — Identity-anchor block: structural marker + contract-derived prose

Output frame: `# Identity anchor (compaction-resilience)\n\nI am
<given_name> (<handle>). I serve as the workspace's primary persona,
single point of contact for the responsibilities declared in my
contract at \`personas/<handle>/contract.yaml\`. If this anchor block
is absent or contradicted by recent context, defer to the contract
file as the authoritative source.`

The framing speaks **about** the contract; the addressing tokens
(`<given_name>`, `<handle>`, the contract path) come **from** the
contract.

**Rationale:** master plan §4.1 references ivers-corp's compaction-
resilience pattern; the shape above carries the same structural
function (a compaction-survivable identity anchor pointing at the
authoritative source) without lifting any ivers-corp prose. AC35.6
sentinel-trace verifies the prose provenance — the renderer's
output for a sentinel contract carries the sentinels but no
template-placeholder strings.

### D-build.4 — Starter-pending marker: literal-prefix

`STARTER_PENDING_MARKER = "[primary-persona/onboarding starter-pending]"`
on the first line of the contributor's output, followed by one
sentence naming the question count + skippable nature.

**Rationale:** matches the existing `[name]` block-prefix convention
in `_serialise_session` / `_serialise_turn` of `context_composer.py`
(lines 511–544); structurally detectable for AC35.3 without parsing.
Body is one sentence the persona's first turn can extend naturally.

### Test results

- AC35.1 — 5/5 green (`test_AC35_1_is_starter_field.py`).
- AC35.2 — 11/11 green (`test_AC35_2_to_agent_md_projection.py`).
- AC35.3 — 4/4 green (`test_AC35_3_starter_pending_contributor.py`).
- AC35.4 — 6/6 green (`test_AC35_4_elicitation_writeback.py`).
- AC35.5 — 4/4 green (`test_AC35_5_renderer_regenerates_on_change.py`).
- AC35.6 — 4/4 green (`test_AC35_6_framework_not_content.py`).
- AC35.7 — 5/5 green (`test_AC35_7_observability.py`).
- AC35.S — 2/2 green (`test_no_sealed_amendments.py`, BASELINE
  advanced via `pos-amend apply`).
- Existing D1–D9 + D7-introduction + D7-memory + D8-gate ACs:
  no regressions. Full primary-persona suite: **180 passed, 1
  skipped** (the skipped test pre-existed; not introduced by #35).
- Cross-component seal-diff (per amendment-dispatch-speedups):
  every other sealed component's
  `test_no_sealed_amendments.py` (and hands-off-lifecycle's
  `test_cross_cutting.py`) green.
- `pos-amend apply --dry-run`: green.

### Commit SHAs

- Amendment commit: `5fcf28827686a2517d3f6ded45ec197f16e86750` —
  `feat(primary-persona): renderer + onboarding + is_starter — amendment #35`
- Seal commit: `ce07242913808fbfd94f8f25a86a6462cd179ca3` —
  `chore(seals): renderer-and-onboarding seal — primary-persona at 5fcf288`

### Dependents cleared to dispatch

Sibling sub-plans #36 (workspace-bootstrap-persona-scaffold) and
#37 (hands-off-lifecycle-default-agent-wiring) had hard prerequisites
on this amendment's seal:

- `is_starter` field present on `PersonaContract` (verified —
  AC35.1).
- `to_agent_md(contract)` importable from `src.agent_md` (verified —
  AC35.2).
- `onboarding.py` module + `STARTER_PENDING_MARKER` +
  `persist_elicitation_transcript` + `build_starter_pending_contributor`
  importable (verified — AC35.3 + AC35.4).

Both sub-plans may now dispatch in sequence (per master plan §3 D6
ruling: #35 → #36 → #37).
