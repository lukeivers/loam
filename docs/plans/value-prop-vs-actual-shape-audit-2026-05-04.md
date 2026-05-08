# Value-prop vs actual-shape audit — persona-as-translator vs persona-as-orchestrator

**Date authored:** 2026-05-04. **Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`. **Trigger:** owner directive (Luke, 2026-05-04) — *"I feel like we are starting to drift some from where I thought we would be going with loam … the goal of the primary persona as we defined it is to figure out how to make the harness and LLM work for me, but I've turned you into more of an orchestrator."* **Doc class:** planning + analysis (pre-build; doc-only). **Length target band:** 3000–5000 words. **Anchors:** `docs/VALUE_PROPOSITION.md`; `framework/CLAUDE.md` lenses 1–5; `framework/primary-persona/templates/persona-template/prompt.md`; `docs/design/primary-persona-shape.md`; `docs/plans/v0-1-x-roadmap.md`; the in-flight M-FBM operational-health amendment (#125, sealed `dc408f7`/`c8de8e3`).

---

## §1 — VALUE_PROPOSITION re-grounding

The locked design document at `docs/VALUE_PROPOSITION.md` defines two prime-objective tests. Reproduced verbatim:

**Primary-persona test.** *"Does this reduce the translation burden between the user's natural-language intent and AI-effective execution?"* (`VALUE_PROPOSITION.md:60`).

**Harness test.** *"Does this add to the toolkit the primary persona can draw from?"* (`VALUE_PROPOSITION.md:66`).

The doc names a derived rule as well — *"a feature that fails the primary-persona test may still be right occasionally … a feature that fails the harness test is almost always wrong"* (`VALUE_PROPOSITION.md:72,74`). Both tests, in the locked text, treat the persona as the *translator*, not as the *executor of any particular workflow*. The locked text also calls out an explicit failure mode: *"features that push translation work onto the user turn the primary persona into a dispatcher rather than a translator, and the user pays the usability cost"* (`VALUE_PROPOSITION.md:62`).

That last sentence is the hinge. The locked design names "dispatcher" — Luke's "orchestrator" framing in his 2026-05-04 directive is the same failure mode under a different word. The locked text already anticipates the drift; the question this doc answers is whether the drift has actually happened, where, and what to do about it.

The doc unpacks six translation responsibilities the persona owns (`VALUE_PROPOSITION.md:82–87`): modality translation, specialist routing, cross-domain integration, authority translation, proactive surfacing, outcome ownership. And eight harness contributions the persona draws from (`VALUE_PROPOSITION.md:95–102`): persistence, autonomous continuity, structural governance, real-tool integration, role specialisation, audit trail, process structure, composition. The audit in §2–§3 maps observed behaviour against these specifically named items.

**No halt on §1.** `VALUE_PROPOSITION.md` is fully present, well-formed, and unambiguous about the persona-as-translator framing. The locked text is the right anchor. The drift Luke is naming is operational, not document-level — the audit has solid ground to stand on.

---

## §2 — How the persona is currently behaving

### 2.1 — Audit window and sources

Audit window: roughly the last seven days of canonical pos-v2 work (2026-04-27 through 2026-05-04). Sources:

- `git log --oneline -50` from canonical (50 commits, all visible).
- The recently-sealed primary-persona prompt (`framework/primary-persona/templates/persona-template/prompt.md`, 356 lines).
- The in-flight M-FBM operational-health diagnosis at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/m-fbm-operational-failure-diagnosis-2026-05-04.md` (the trigger this turn shares a timeline with).
- `docs/plans/v0-1-x-roadmap.md` (current in-flight roadmap).
- Recent FIDRAFT entries (81 entries; full content available at `docs/FUTURE_IDEAS_DRAFT.md`).

### 2.2 — Observed behaviour patterns

The patterns below are descriptive of the recent persona, not aspirational. Each carries a citation.

**Pattern A — heavy plan-doc + manifest authoring before any code.** Every recent amendment ships a sub-plan-doc (e.g. `docs/plans/v0-1-3-skill-packages.md`, `docs/plans/v0-1-2-V11-A-orchestrator-fix.md`, the in-flight m-fbm-operational-health sub-plan) plus a manifest (`*.manifest.yaml`) plus a §8 SHA-record commit on the parent roadmap. Citation: commits `f50647f`, `c7c429c`, `93a2a3a`, `2c95507`, `6749f44`, `d63ba9c`, etc. — every amendment cycle adds three or more doc-only commits before and after any sealed-component build. This is consistent with `feedback_plan_before_code` (hard rule) but the *volume* of plan-doc material is large enough that the persona's tokens-per-turn skew toward plan authorship rather than translation.

**Pattern B — dispatch shapes are scope-only, but the persona still authors most of the dispatch text itself.** Every dispatch reproduces a multi-section scaffold (principles-to-apply, source directive, objective with seven to eight named sections, constraints, acceptance, halt triggers, model rationale). Citation: this turn's own dispatch prompt; the previously-sealed dispatches captured in `framework/primary-persona/templates/persona-template/prompt.md` reference the dispatch-with-gates SKILL package (`plugins/loam-skills/skills/dispatch-with-gates/SKILL.md`) but the persona still composes the prompt rather than invoking the skill as a primitive. The skill describes the shape; the persona still does the composition each time.

**Pattern C — coordination work consumes a large share of the persona's user-facing output.** Recent Telegram-channel arcs (described in `~/.claude/CLAUDE.md` channel rules and verifiable from FIDRAFT entries about footer-discipline) report dispatch-status, agent-completion-summaries, SHA-recording, and gate-recommendation. The persona's outbound surface looks like a status-stream of "agent A landed at SHA X; agent B in flight; here's the next gate" rather than translation-of-intent. Citation: the principle-application footer rule (`feedback_principle_application_footer_in_telegram` in `~/.claude/CLAUDE.md`) was authored *because* the persona's user-visible messages had become long-enough to warrant a structured footer — i.e. the medium-to-long status report is the dominant message shape.

**Pattern D — sealed-component amendments dominate the work mix.** v0.1.0 ship → 96+ amendments (per STATE.md row "Amendment cycle 2026-04-21 → present"). v0.1.1, v0.1.2, v0.1.3 ship arc has been almost entirely sealed-component amendments + plan-docs + design notes. New translation-layer surfaces (skills, scheduled scopes, integrations) for end-users land in narrow windows: v0.1.3 ships five SKILL.md packages (commit `bb9bcb1`), v0.1.4 will add subagent personas. Most weeks the persona's productive output is *amendments to the harness* rather than *translations of user intent into harness invocation*.

**Pattern E — the persona itself does very little user-intent translation in canonical pos-v2 sessions, because the canonical workspace's "user intent" is overwhelmingly meta-work on loam itself.** The dev-mode partition (`framework/CLAUDE.md` introduction) acknowledges this: dev-mode workspaces auto-load methodology fluency that normal-use workspaces never see. The persona running in canonical pos-v2 *is the loam-builder persona*, not the production-use chief-of-staff persona. So Luke's "you've become an orchestrator" framing is partly grounded in observing the persona at a workspace where translation surface is genuinely thin and orchestration surface is thick — by the workspace's own design.

**Pattern F — the persona reaches for structural primitives correctly.** The leverage rule + capability index in the persona prompt (`framework/primary-persona/templates/persona-template/prompt.md:160–190`) specifically forces a "what Claude Code primitive does this lean on?" pause before action. Recent activity confirms this fires: V11.A reached for `launchctl bootstrap` rather than re-implementing service supervision; V11.E used the existing plist-existence probe rather than authoring new health-checking code; the M-FBM operational-health amendment added heartbeat NDJSON to existing log surfaces rather than a new observability sidecar. So the harness-leverage *test* is being applied; the question is whether the *outputs of the work* aggregate into translation-burden reduction at the user surface, which Pattern E suggests they don't yet (because there is barely any translation surface in canonical pos-v2 to test against).

### 2.3 — What the user-facing surface looks like

If a stranger read the last week of Telegram-channel output (the user-visible surface per `~/.claude/CLAUDE.md` channel rules) without context, they would see: amendment briefs, gate-review prompts, SHA notifications, dispatch dispatches, agent-completion summaries, footer-of-principles-applied. They would *not* see: a chief-of-staff translating "I want this done every 12 hours" into a scheduled scope, surfacing tomorrow's calendar friction, recovering forgotten context across sessions for a non-engineering decision, or routing a non-development question to the right specialist behind the scenes.

This is the empirical core of Luke's framing. The persona *is* doing translation, but the translation it's doing is "loam-build-instruction → sealed-component-amendment-cycle." That's a narrow and dev-mode-specific translation, not the broad chief-of-staff translation `VALUE_PROPOSITION.md` describes.

---

## §3 — Drift assessment against the two prime-objective tests

### 3.1 — Primary-persona test (translation-burden reduction)

**Verdict: pass on the dev-mode subset, fail on the broader VALUE_PROPOSITION-described subset, with the caveat that the broader subset is largely untested in canonical pos-v2.**

Pass evidence: the persona consistently translates Luke's natural-language directives ("dispatch an agent to research X", "ship V11.A as a hotfix", "defer V11.C to v0.1.4+") into harness operations (sub-plan-doc → manifest → sealed-component fence → amendment cycle → SHA-record). The user does not pick which sealed-component to touch, does not pick the manifest fields, does not pick the test fixture names. That *is* translation, in the locked-design sense.

Fail evidence: the *kind* of intent the persona translates is narrow. Luke's directive in this turn — "explain how we are meeting the value prop" — is itself a dev-mode-of-loam directive. The persona handles it. But broader intents the locked design names — "do this every 12 hours", cross-domain integration, proactive non-engineering surfacing, life-management chief-of-staff work — never come up in canonical pos-v2 because the workspace is set up to build loam, not to use loam-as-product. The pattern-E observation matters here: *the canonical workspace cannot test the broader translation*, only the dev-mode subset.

The honest reading: the persona passes the primary-persona test for the workload it sees. The drift Luke is sensing is that the workload it sees is unrepresentative of what the locked design optimises for — and the persona's output volume is dominated by coordination ceremony for a build cycle rather than translation of broad user intent.

### 3.2 — Harness test (toolkit expansion)

**Verdict: pass.**

Every recent amendment lands toolkit growth: V11.A unblocks the orchestrator (toolkit primitive), the v0.1.3 SKILL packages add five discoverable composable patterns (`memory-recall`, `scope-decompose`, `dispatch-with-gates`, `onboarding-conversation`, `session-handoff`), V11.E and the M-FBM operational-health amendment harden harness primitives, the ack-first persona contract amendment encodes a turn-shape rule into the harness rather than keeping it in advisory feedback files. Each is a toolkit addition, and each is invokable by the primary persona — i.e. not the harness-test-fail shape (capabilities the user has to orchestrate themselves).

The five SKILL packages in particular are the most user-facing harness expansion in months and explicitly target the persona-leverage surface. They pass `harness test` cleanly.

### 3.3 — Drift name

The drift, named precisely, is **not** persona-as-orchestrator at the contract level. The persona prompt + design note still describe the persona as a translator, and the user-facing channel rules + ack-first rule keep the persona's contract translator-shaped.

The drift is **persona-as-build-coordinator-in-canonical-workspace**. The canonical workspace's workload is meta-work-on-loam, the persona is doing translation of meta-work-on-loam intent into amendment-cycle ceremony, and the *output volume* of that ceremony is large enough that the channel surface looks orchestration-shaped even when the contract isn't.

This matters because the fix is different. If the drift were contract-level (persona-as-orchestrator), the fix would be reshape-the-persona. Because it's workload-level (persona-doing-too-much-build-coordination-itself-vs-delegating-it), the fix is to push the build-coordination ceremony *off* the persona — into structural primitives the persona invokes — so the persona's user-facing surface returns to translation shape even when the workload happens to be loam-on-loam.

### 3.4 — F2 ruthless feedback to the owner framing

Luke's framing is "you've become an orchestrator." The audit partially confirms (output-volume pattern) and partially contradicts (contract-level persona shape is intact, harness test passes cleanly). The reconciliation is: the persona's *contract* is translator-shaped; the persona's *workload-mix* in canonical pos-v2 has skewed toward coordination because the workload is loam-on-loam. The owner-visible symptom — the chat surface reads as status-stream — is real, but the root cause is "build-coordination is happening *inside* the persona's context window" rather than "the persona is conceptually orchestration-shaped."

Naming alternatives to the owner: the framing "I've turned you into an orchestrator" treats the persona-shape as the lever. The audit suggests the lever is one level down — the *placement* of coordination work, not the persona's identity. F2 RF requires surfacing this even if it complicates the directive: structural placement of build-coordination is the reshape candidate, not the persona contract itself.

---

## §4 — The reconciliation tension Luke named

Luke's tension verbatim: *"You should be relying on an orchestration skill or service or whatever for handling all of this stuff … but also I do need some way to get what I'm asking for processed and communicated back to me. So I'm not sure how to reconcile those things."* Decomposed into named sub-tensions:

### T1 — persona-as-translator vs persona-as-orchestrator (which is the persona's job)

Multi-signal call: scope-confidence in the locked design's translator framing is **high** (`VALUE_PROPOSITION.md:17–32` is unambiguous; the design note at `docs/design/primary-persona-shape.md:40–47` is explicit about specialists existing behind the persona, dispatched by the persona). Reversibility of changing the persona contract is **low** (the contract is referenced from hooks, the workspace-bootstrap, the ack-first amendment, and the principle-application footer rule). Information asymmetry between Luke's framing and the audit is **non-trivial** — Luke is observing chat-surface-as-orchestrator and inferring contract-as-orchestrator; the audit suggests these are two different layers.

**Resolution.** Persona-as-translator is the right contract. The audit confirms the locked design without revision. Luke's directive should be interpreted as "shift coordination work *off the persona's user-visible surface*, not change what the persona is." The principle-conflict-resolution discipline (`feedback_principle_conflict_resolution_multi_signal`, M5) supports surfacing this back to the owner because reasonable people would weigh the signals differently — silent application of "persona stays a translator" without naming the conflict would propagate as silent precedent.

### T2 — orchestration-as-skill vs orchestration-as-service vs orchestration-as-runtime (where does orchestration live)

Three architectural placements for the build-coordination machinery currently happening inside the persona's context:

- **Skill placement.** Codify the dispatch-cycle (sub-plan → manifest → fence-one-no-edit → seal → §8 SHA record) as a SKILL package. The persona invokes it at need; Claude Code's skill loader handles the steps. Lens 1 high (uses skill primitive); Lens 2 high (fewer dispatch tokens means more user-translation surface); Lens 3 forces the codified shape into objective-form. Cost: ~2–4h to author + verify. Reversibility: high (skill is a folder; remove it cleanly).

- **Service placement.** A long-lived process — possibly extending the existing orchestrator at `framework/orchestrator/` — owns the amendment-cycle state machine. The persona submits an "amendment intent" through IPC and receives status callbacks. Lens 1 medium (uses launchd + IPC primitives but doesn't directly map to a Claude Code primitive). Lens 2 high (dispatches the entire ceremony out of the persona's context window). Lens 3 needs careful AC authoring at the service boundary. Cost: ~8–16h to extend orchestrator + design IPC contract + thread persona invocation. Reversibility: medium-low (service-shaped components are harder to retire than skills).

- **Runtime placement.** A swarm-runtime (the deferred V2.C item in `v0-1-x-roadmap.md` §3) handles enumerate→execute→judge cycles natively, with the persona submitting a high-level objective and receiving the verdict. Lens 1 high if it composes with `claude` background-agent invocations. Lens 2 highest of the three (the persona barely touches the cycle internals). Lens 3 maps cleanly. Cost: ~12–24h (per the v0.1.x roadmap §3 entry — large, sequenced for v0.2.x). Reversibility: low.

These are not exclusive — the durable shape is likely "skill at v0.1.x for fast feedback, runtime at v0.2.x once the skill's coordination pattern is exercised across enough usage data to design the runtime against."

### T3 — communication-via-persona vs communication-via-orchestrator-status (what surfaces back to user)

The locked design names the persona as *the owner of the user-facing voice* (`docs/design/primary-persona-shape.md:38–45`). Status-stream output from a separate orchestrator that the user reads directly is the multi-agent failure mode the design note explicitly rules out (`docs/design/primary-persona-shape.md:54–60`).

But this conflicts with Luke's directive that the persona should "rely on an orchestration skill or service for handling all of this stuff." Reconciliation: orchestration *executes* the work; the persona *narrates* the work's outcomes. The orchestrator does not address the user. The persona *integrates* orchestration outputs into its own voice — possibly with light-touch narration per the persona prompt's *"Light-touch narration on choices"* rule (`framework/primary-persona/templates/persona-template/prompt.md:332–342`).

Multi-signal call: blast radius of changing this is high (the user's mental model is one voice). The reversibility of integrating orchestration outputs into the persona's voice is high (it's a presentation-layer choice). Audience: end-users get one voice; Luke as builder may reasonably want richer status output during dev-mode work — which is where the dev-mode partition is the right tool, not a contract change.

**Resolution.** Communication stays via the persona unconditionally for normal-use workspaces. Dev-mode workspaces may surface a richer build-status panel through a separate channel (e.g. an in-terminal `loam status` invocation) without altering the persona's user-facing voice. This is consistent with the dev-mode auto-load partition pattern already established in `framework/CLAUDE.md`.

### T4 — persona-token-spend on coordination vs translation (a derived tension)

The audit surfaced this implicitly. Each turn's persona-context budget is finite; tokens spent narrating dispatches are tokens not spent on user-intent translation. The harness's `cost-governance` component has a per-scope budget but no per-turn discipline that distinguishes coordination tokens from translation tokens. This is upstream of the structural placement question — even with orchestration moved to a skill, if every turn still narrates the skill invocation in the persona's voice, the chat surface still looks coordination-heavy.

Composes with T2 and T3: the placement and communication choices together determine the observable token-spend ratio. Recommended capture: a FIDRAFT entry "per-turn persona-token-spend taxonomy: translation vs coordination vs ceremony" so the question becomes durable for v0.2.x cost-governance work.

### T5 — Luke's role: user-of-loam vs builder-of-loam (a context tension)

Not strictly a sub-tension of Luke's verbatim framing, but the audit surfaces it. Luke is currently both end-user and builder. When the canonical workspace's workload is "build loam," the persona behaves as a build-coordinator-as-translator; when it's "use loam to manage Luke's life," the persona behaves closer to the chief-of-staff shape `VALUE_PROPOSITION.md` describes. The drift Luke is naming may correlate with a workload-mix shift over the past arc rather than a persona-shape change.

**Resolution.** Beyond audit scope to resolve, but worth surfacing: if Luke wants to validate the chief-of-staff shape against the locked design, the test is to run an explicit non-loam-of-loam workload through the canonical workspace and observe the persona's output shape. The audit cannot do that test from existing artefacts.

---

## §5 — Re-shape options

Five options. Each is a candidate for the reshape Luke asked about. Costs are AI-time bands per the duration estimation rubric.

### Option 1 — Do nothing structurally; document the dev-mode-vs-normal-use distinction

**Shape.** Persona contract stays as-is. A new design note (`docs/design/dev-mode-persona-workload-shape.md`) names the audit's finding: in canonical pos-v2 the persona's workload is build-coordination-as-translation, which is correct for the workspace and consistent with `VALUE_PROPOSITION.md`. No code changes.

**Cost.** 30–60 min AI-time. **Pros:** primary-persona test pass (current behavior is correct, just needed articulation); risk-light; full reversibility. **Cons:** does not address the output-volume drift — if Luke's complaint is "the chat surface looks like status-stream," documenting that this is correct does not change what Luke sees. **Risk:** low; the underlying observation likely re-raises later.

### Option 2 — Codify the amendment-cycle as a SKILL package; persona invokes the skill

**Shape.** New SKILL package (`plugins/loam-skills/skills/amendment-cycle/SKILL.md`) captures the full sub-plan → manifest → fence-one-no-edit → seal → §8 SHA-record sequence. Persona detects amendment-shaped work in the user's intent and invokes the skill rather than authoring each step in its own context.

**Cost.** 2–4h AI-time. **Pros:** primary-persona test pass with strong evidence — coordination tokens shift to a single skill invocation, freeing context for translation. Harness test pass. Composes with v0.1.3's already-validated SKILL pattern. **Cons:** the SKILL itself becomes a place where method may get prescribed; if it enumerates files / symbols / ACs it falls into the `feedback_agent_prompts_scope_only` failure mode. **Risk:** medium; reversibility is high (folder delete). Skill may ossify the current cycle shape before it's fully stable.

### Option 3 — Extend the orchestrator service to own amendment-cycle state

**Shape.** The existing orchestrator (`framework/orchestrator/`) gains an `AmendmentCycleManager` subsystem. Persona submits an `AmendmentIntent` over IPC; the manager owns the state machine; persona receives status callbacks and integrates them into its voice. Build-time tokens leave the persona's context entirely.

**Cost.** 8–16h AI-time + IPC-schema gate-review touchpoints. **Pros:** highest primary-persona-test pass — persona narrates state transitions only. Aligns with existing orchestrator's scope-runtime + objective-tracker + background-work-monitor pattern. **Cons:** large; service-shaped components are harder to retire than skills; amendment-cycle pattern is still being refined and freezing it into a service is premature. **Risk:** medium-high. Composes with the v0.1.x roadmap's deferral of V2.C swarm-runtime to v0.2.x for the same reason.

### Option 4 — Move build-coordination to subagent personas (V11.B + v0.1.4 path)

**Shape.** Build-coordination work happens in dispatched subagent personas (`loam-builder`, `loam-plan-author`, `loam-reviewer` per v0.1.4 §2) rather than in the primary persona's context. The primary persona delegates the entire amendment-cycle to a `loam-builder` subagent; subagent personas carry the methodology fluency that currently lives in dispatch-prompt scaffolding. The primary persona handles user-intent translation and result integration only.

**Cost.** 4–6h AI-time additional to v0.1.4's existing scope. **Pros:** primary-persona test pass with high confidence — persona's role becomes "dispatch + integrate," the locked-design shape. Harness test pass — subagent personas are toolkit additions. Lens 5 (swarming) composes (each subagent carries a tighter AC than the primary). Aligns with v0.1.4 without adding components. **Cons:** subagent persona authoring carries the `feedback_agent_prompts_scope_only` risk pattern at one remove (priming-prose that prescribes method becomes the same failure). **Risk:** low-medium; reversibility high (subagent files are `.claude/agents/<name>.md`).

### Option 5 — Hybrid: Option 1 (document) + Option 4 (subagent personas) + Option 2 (skill) at v0.1.4 cadence

**Shape.** Three shipping artefacts across v0.1.4:

1. The dev-mode-vs-normal-use design note from Option 1 (small).
2. Subagent personas with amendment-cycle ownership from Option 4 (medium; already on roadmap, just sharpened).
3. An `amendment-cycle` SKILL package from Option 2 (small-to-medium; lives in `plugins/loam-skills/`) that the primary persona and subagent personas both invoke. The skill encodes the cycle shape; subagent personas carry the methodology fluency to invoke it correctly.

**What changes.** v0.1.4 §2 gains one item (skill) and sharpens one item (subagent personas → subagent personas-with-amendment-cycle-ownership). v0.1.4 AI-time band shifts from 3–5h to 5–8h. Owner gate-review unchanged in count, slightly heavier per touchpoint.

**Cost.** ~5–8h AI-time on top of v0.1.4's existing scope. Some of v0.1.4's scope absorbs the work (V2.B subagent personas anyway), so the marginal cost is the skill package + the integration narrative.

**Pros.** Primary-persona test: highest pass of any option — the persona's context becomes pure user-intent translation; build-coordination lives in subagent personas + skill. Harness test: pass — adds two toolkit primitives (skill, three subagent persona archetypes with cycle ownership). Lens 5 composes (subagent personas are tighter-AC subtasks). Lens 1 composes (subagent personas use Claude Code's `.claude/agents/` primitive). Lens 2 composes (skill + subagent personas are persona-invokable). Lens 3 composes (each artefact is ODD-authorable). Lens 4 composes (scope-confidence on the subagent persona contracts is high).

**Cons.** Three artefacts means three failure modes. Authoring discipline must hold across all three. The amendment-cycle skill must not prescribe method.

**Risk.** Low-medium. Composes with existing roadmap; reversibility per-artefact is high.

---

## §6 — How current in-flight work ladders up

Each in-flight or recently-shipped item, mapped against the two tests.

**v0.1.3 R.4 — five SKILL packages** (sealed `bb9bcb1`; commit `f04e925`). Both tests pass — five toolkit primitives directly reducing translation burden for raw-Claude-Code users. Ladders up cleanly.

**v0.1.3 R.5 design note 1 — primary-persona-shape** (sealed `7ae346d`). Doc-only; anchors future feature work against the locked design. Ladders up.

**v0.1.3 V11.C — DEFERRED to v0.1.4+.** Luke ruling 2026-05-04 + M-FBM operational-failure diagnosis confirm V11.C as a workaround for broken M-FBM, not a translation-burden reducer. Deferral is correct.

**v0.1.4 — five subagent personas + V11.B + 2 design notes.** Both tests pass *if* §5 Option 5 lands (subagent personas-with-cycle-ownership); pass *weakly* if subagent personas land as priming-only. V11.B's tracker-context contributor is a session-start improvement either way.

**v0.1.5 — memory pluggable (D-3 Protocol widen + D-1 progressive disclosure + D-2 Anthropic-tool adapter).** Both tests strong-pass. D-1 progressive disclosure directly reduces translation burden by lowering retrieval token-spend (more context for translation). Three new MemoryProvider surface affordances.

**M-FBM operational-health amendment #125** (in flight as agent B; sealed `dc408f7`/`c8de8e3`). Indirect persona-test pass (fixes the substrate the persona depends on for cross-session translation); strong harness-test pass (new AC.MFBM-OPS.\* family). Exactly the structural work `feedback_specific_claims_verified_or_marked_guess` + the 2026-05-04 diagnosis flagged.

**Smoke-test-discipline canonical doc** (sealed `4fb9e3c`). Doc; composes with the harness test by codifying the 6-dimension coverage spec the M-FBM amendment satisfied.

**Aggregate verdict.** All in-flight work ladders up to one or both prime-objective tests. The drift Luke is naming is *not* visible in the work-mix's ladder-up — every shipping item satisfies the tests. The drift is in the *output volume* of the persona's user-visible coordination of that work, which §5 Option 5 directly addresses.

---

## §7 — Recommendation

**Recommended option: §5 Option 5 (hybrid).**

**Defense against the two prime-objective tests.**

- *Primary-persona test.* Option 5 moves build-coordination off the persona's user-visible surface (subagent personas own amendment-cycle ownership; skill encodes the cycle shape; design note articulates the dev-mode workload distinction). The persona's chat surface returns to translation-of-intent shape. Pass with strongest evidence of any option.
- *Harness test.* Option 5 adds two toolkit primitives (skill + three sharpened subagent personas) plus one design-anchor doc. Pass.

**Defense against the named tensions.**

- *T1 (translator vs orchestrator).* Resolves toward translator at the contract level; surfaces the structural-placement reframe to Luke explicitly.
- *T2 (skill vs service vs runtime).* Picks skill for now, defers runtime to v0.2.x per existing roadmap. Honest about the staging.
- *T3 (communication via persona vs orchestrator-status).* Communication stays via persona; subagent personas + skill are invisible at user surface; possible dev-mode-only `loam status` panel is a future option, not in this reshape.
- *T4 (token-spend ratio).* Skill + subagent persona placement directly addresses this by moving coordination tokens out of the persona's context.
- *T5 (user-vs-builder workload).* Surfaced to Luke as an open question (§8); reshape does not require resolving it.

**Decisions Luke needs to rule on (named, with recommendations).**

1. **Is §5 Option 5 the right reshape, vs Options 1–4?** Recommendation: yes, Option 5. Composes with existing v0.1.4 roadmap and addresses the named drift at the right layer.
2. **Should the amendment-cycle skill ship at v0.1.3.1 hotfix cadence, or wait for v0.1.4 alongside subagent personas?** Recommendation: wait for v0.1.4. The skill's value lands when subagent personas can invoke it; shipping it stand-alone earlier doesn't reduce translation burden.
3. **Should subagent personas be authored as priming-only (current v0.1.4 §2 scope), or as priming-plus-amendment-cycle-ownership (Option 5 sharpening)?** Recommendation: priming-plus-ownership. Otherwise the reshape is mostly cosmetic.
4. **Should the dev-mode-vs-normal-use design note ship in v0.1.4 alongside the other design notes, or land as a v0.1.5 item?** Recommendation: v0.1.4. It contextualises the subagent persona work and pairs naturally with the file-based-memory-rationale + odd-for-delegation notes already in v0.1.4 §2.
5. **Should principle-application-footer rule be revisited as part of this reshape?** The footer rule was authored to make principle-application visible; if subagent personas absorb coordination work, the footer-discipline applies primarily to subagents rather than the primary persona. Recommendation: keep the footer rule as-is for now; revisit at v0.1.5 once subagent persona behavior in the field is observable.

**AI-time band.** ~5–8h for the marginal Option-5 work on top of v0.1.4's existing 3–5h scope. Total v0.1.4: ~8–13h AI-time, ~30–45 min owner gate-review across 3–4 touchpoints (sharpened from the existing v0.1.4 estimate of 3–5h / 25–35 min owner; the reshape adds ~3h AI-time and ~10 min owner-time).

**Sequencing.**

- v0.1.3 ships now as already scoped (R.4 SKILL packages sealed; R.5 part 1 sealed; V11.C deferred).
- v0.1.4 ships per the reshape: subagent personas-with-cycle-ownership + amendment-cycle skill + dev-mode-vs-normal-use design note + V11.B (#38/#39/#40) + 2 R.5 design notes already on roadmap.
- v0.1.5 unchanged (memory pluggable).
- v0.2.x retains V2.C swarm-runtime as the durable replacement for the skill placement once the cycle pattern is validated.

**Risk + mitigation.** The largest risk is amendment-cycle skill ossifying the current cycle shape before it's stable. Mitigation: author the skill at outcome-shape granularity (no file enumeration, no symbol naming, no AC text) per `feedback_agent_prompts_scope_only`. The skill describes the *shape* of an amendment-cycle dispatch; the subagent persona carries the methodology fluency to invoke it correctly. Builder dispatch authoring stays scope-only.

The second risk is subagent persona authoring failing to absorb amendment-cycle ownership cleanly — a subagent persona that reads a method recipe is the same failure mode at one remove. Mitigation: each subagent persona's prompt is itself ODD-shaped; halt-and-surface fluency is mandatory; method stays the builder's call within the subagent's context.

---

## §8 — Open questions

Discrete decisions Luke can rule on.

1. **Is the audit's drift-naming correct?** Audit calls the drift *persona-as-build-coordinator-in-canonical-workspace* (workload-level), not *persona-as-orchestrator* (contract-level). Yes / no / partial.
2. **§5 Option 5 (hybrid) vs another option?** Pick from §5 (Option 1, 2, 3, 4, 5).
3. **Should T5 (user-vs-builder workload mix) be a separate planning artefact?** Yes / no. If yes, its scope.
4. **Is the chief-of-staff workload validation worth running explicitly?** I.e. should Luke (as user, not builder) intentionally route a non-loam-of-loam intent through the canonical workspace and observe whether the persona's output shape matches `VALUE_PROPOSITION.md`? Yes / no / later.
5. **Should `framework/CLAUDE.md` Lens 2 carry an explicit reference to this audit doc as a worked example?** Yes / no.
6. **Should the `feedback_principle_application_footer_in_telegram` rule be re-evaluated as part of the reshape, given that Option 5 reduces persona-side coordination?** Yes / no / defer to v0.1.5 verification.
7. **Should the audit recommend a periodic re-run cadence?** Audit is a snapshot; persona-shape drift is a recurring failure mode. Recommendation if yes: quarterly drift audit, ~1–2h AI-time per snapshot, anchored to the same VALUE_PROPOSITION tests. Yes / no / yes-but-different-cadence.

---

## §9 — Halt-and-surface findings

None at the locked-design level. `VALUE_PROPOSITION.md` is fully present, well-formed, and unambiguous. The persona-as-translator framing is intact in the contract surface (`framework/primary-persona/templates/persona-template/prompt.md` + `docs/design/primary-persona-shape.md`). The drift Luke is naming is real but operates one layer below the contract — at the workload-mix and output-volume layer — and is reshapable without touching `VALUE_PROPOSITION.md`.

One caveat worth surfacing: the audit relied on canonical pos-v2's recent commit history + plan-doc corpus. It did not run a chief-of-staff-mode probe (per §8 question 4) to validate the persona's behavior on non-loam-of-loam intent. That probe would tighten the audit's confidence on whether the persona's contract holds in the workload it was actually designed for. The audit's Pattern E (canonical workspace doesn't have the broader translation surface to test against) is the limit of what archival evidence can establish.

---

*End of audit. Companion artefacts: `VALUE_PROPOSITION.md` (anchor); `framework/primary-persona/templates/persona-template/prompt.md` (contract surface); `docs/design/primary-persona-shape.md` (shape rationale); `docs/plans/v0-1-x-roadmap.md` (sequencing). Reshape lands at v0.1.4 if Luke rules in favor of §5 Option 5.*
