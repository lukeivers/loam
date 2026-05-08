# Research — ODD-default conversational framing + light-touch education (Idea 6 + Idea 2 composition)

**Authored:** 2026-04-26.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Driver:** the dispatch's six specific questions on how `FUTURE_IDEAS.md` Idea 2 (non-tech-user enablement through light-touch education, line 259) and Idea 6 (ODD as default framing inside pos-v2 conversations, line 353) compose into a coherent persona-behaviour design, and where the implementation lands across the in-flight amendment programmes (O = structural-enforcement; L = onboarding-rewrite; new amendment if neither is the right home).
**Spec ladder:** `pos-v2-objectives-spec.md` line 152–153 (Non-tech users objective: low-friction onboarding, persona in every session, *auto-create+explain*, *anti-deskilling*) — Idea 2 is direct conformance to "auto-create+explain" + "anti-deskilling"; Idea 6 is direct conformance to "non-tech users benefit from tight bounds + transparent translation." Lens 2 (`VALUE_PROPOSITION.md`) — both ideas operationalise the translation-layer prime objective at the per-turn behaviour layer. ODD §5 (structural over advisory) governs the "what's framework, what's persona content" partition.
**Owner directives in force (2026-04-26):**
- Confidence-delegation: high-confidence recommendations are locked in doc text; only genuinely uncertain calls are surfaced for ruling.
- Three top-value persona traits (autonomy + asymmetric problem solving + parallelism) and four operational rules (Lean on the harness + Use the right tool + Codify what repeats + Structural enforcement default) are already in L's plan §7 + research-companion §9.4. Idea 2 + Idea 6 compose alongside them; nothing replaces them.
- Framework-not-content (v1.2 R16): persona content is workspace-supplied; framework provides defaults via scaffold's template-tree exception.

---

## TL;DR — one-page summary for owner ruling

**Recommendation, one-liner:** **distributed across L (onboarding-rewrite) + O (structural-enforcement) + a small new amendment P (lint pair for auto-create+explain).** No single-amendment program; no fully-folded-into-L; no fully-folded-into-O.

**Distribution:**

| Surface | Where it lands | Why |
|---|---|---|
| **Idea 6 — persona's internal ODD model + translation** | **Fold into L** as a **fifth operational rule** in `prompt.md` ("Frame in objectives — internally"), authored alongside the existing four rules from L's §9.4. | Persona-behaviour content; the rule belongs where the four operational rules already live. Pure content addition; no new framework code. |
| **Idea 2 — light-touch ambient narration (the "explain" of auto-create+explain)** | **Fold into L** as a **sixth operational rule** in `prompt.md` ("Narrate decisions lightly — anti-deskilling"), authored alongside the same four rules. | Same partition reasoning as Idea 6. The throttling rule is persona-judgement, not framework-deterministic — advisory content, not a structural primitive. |
| **The lint side of "silent auto-creation is a lint failure" (spec line 153)** | **New amendment P — `auto-create-explain-lint`** sized as A4-class (small, batchable). | Structural check (a hook detecting auto-creation events without paired explanation surfaces). Wrong-shape for L (L is content) and wrong-shape for O's existing four amendments (O's A1–A4 don't have an auto-create surface to gate). Sized small enough to ride parallel-after-O-A1 or sit at the back of the O programme. |
| **Idea 6's optional structural "ODD-shaped representation" surface (an MCP tool / Pydantic schema the persona can validate against)** | **DEFER** — keep the persona-side prompt rule first; if Idea 6's ambient-narration generation drifts into "the persona makes up plausible-sounding objectives that don't map to any spec AC," the structural surface lands as a follow-on amendment that composes on O's A2 manifest (which already exists in the O proposal). | Adding a structural ODD surface today is premature optimisation; the prompt rule is the cheap test. If the rule holds (the persona reliably produces well-shaped internal restatements), no structural lift is needed. If it drifts, O's manifest is the right substrate to compose on. |
| **Idea 3 alignment (SDLC plugin's ODD-default-for-projects clause)** | **No alignment work needed at L-time.** Idea 6 ships at the conversation layer; Idea 3 inherits the conversation-level surface when it's authored. The two surfaces share methodology, not implementation. | Different scopes, same vocabulary — Idea 3 is project-shaped, Idea 6 is turn-shaped. Idea 3 lands much later (initial plugin suite — no plan today). |

**Decisions surfaced for owner ruling: 4** (numbered §10 below).

- **D1 — Are Idea 6 and Idea 2 added as **two new operational rules** (a fifth and sixth) in L's `prompt.md`, or as **one combined "ODD-and-narration" rule**?** Recommendation: **two rules**, parallel to the existing four. Composition matches §9.4's compose-as-a-loop framing.
- **D2 — Is the lint amendment (P) part of the O programme (a fifth O amendment) or its own one-off?** Recommendation: **its own one-off**, dispatched after O-A1 lands the substrate it composes on. Keeps O-A1–A4 focused on the audit's named candidates; surfaces P's anti-deskilling backing distinctly.
- **D3 — Does L's plan need extension to land the two new rules, or do they ship as a follow-on amendment **after** L seals?** Recommendation: **extend L now, before dispatch**. Adding two rule-sections to `prompt.md` is content-only, no new framework code, no test-shape change beyond AC.O.1's named-section-presence list.
- **D4 — Does Idea 2's ambient narration land **as a turn-output expectation** (every action surfaces a one-sentence rationale), or **only when the persona's choice was non-obvious** (a divergence-detector + throttle)?** Recommendation: **non-obvious-only**, with a two-bullet throttle rule in the prompt. Always-on narration is pedagogy-fatigue; non-obvious-only matches Luke's "ambient, not interruptive" framing in Idea 2.

**Halt triggers surfaced: 0.** No required new top-level objective; no ODD violation in surrounding code surfaced; no shift in the framework/content partition (the rule contents are content, the lint is framework — clean partition); no required source-edit outside primary-persona / hands-off-lifecycle / a hook substrate already authorised by O-A1's scope.

---

## 1. Problem framing — why these two ideas compose

Idea 2 and Idea 6 both operationalise the translation layer at the per-turn behaviour level. The dispatch's framing is exactly right: Idea 6 captures "what shape does the persona's *thinking* take" and Idea 2 captures "what shape does the persona's *user-facing narration* take." The two are the same translation, shown from two sides:

- **Idea 6 (internal):** the persona internally restates the user's request as objective + constraints + acceptance before acting. The user doesn't see this representation; they see the persona behave as if the request were tightly bounded.
- **Idea 2 (external):** when the persona acts, it surfaces a one-sentence rationale (*"I made this a scheduled task because X happens every Tuesday"*) — exposing the choice and reasoning without turning it into a tutorial.

The connection Idea 6's text already names (line 370 of FUTURE_IDEAS): *"as the user engages with the system over time, the persona's ambient narration — 'I made this a scheduled task because…,' 'the acceptance here is that X happens when Y' — gradually teaches the user the shape of ODD thinking without ever naming it."* This is Idea 2 as the externalised expression of Idea 6's internal model. The two ideas are not separable in design even though they were captured separately.

The non-tech-users spec line 152–153 has *four* declared behaviours; Idea 2 + Idea 6 between them satisfy two of those four directly:

- *auto-create+explain* — Idea 2's narration **is** the explain side. The auto-create side is whatever framework code does the creation (skill-authoring pipeline, scope-of-work scheduling, etc.). The pairing is what the spec demands; today the explain side is missing.
- *anti-deskilling* — Idea 2 directly: a user who never sees how the persona made the choice never learns the shape; over time their dependency grows in a way they can't diagnose. Idea 2's narration is the deskilling antidote.

(The other two declared behaviours — *low-friction onboarding* and *persona in every session* — are L's existing scope.)

---

## 2. Question 1 — What does "persona's internal model takes ODD shape" mean operationally?

The dispatch names three options and asks for a cost+leverage comparison.

### 2.1 Option (a) — pure prompt-rule

The persona's `prompt.md` carries a section: *"Before acting on any user request, internally restate it as objective + constraints + acceptance. Do not surface the restatement to the user unless the request is ambiguous or the restatement materially diverges from what the user might expect."*

**Cost:** ~1 paragraph in `prompt.md`. Trivial.

**Leverage:** the persona is an LLM; LLMs follow prompt-level instructions reliably for behaviours that don't conflict with stronger pulls. The four operational rules in L's §9.4 land via the same mechanism today; adding a fifth is the same pattern.

**Failure mode:** the persona may produce well-formed-looking internal restatements that don't actually correspond to any spec AC. The user can't tell. The persona believes it is being ODD-shaped; it is doing prose-imitation of ODD-shape.

**Mitigation:** the rule's text names the specific failure mode it must avoid — *"Don't make up plausible-sounding objectives. If the user's request is ambiguous, surface the ambiguity (paired with Rule 1 — Lean on the harness — what tool would resolve this without me guessing?). If the request is clear but the acceptance criterion isn't observable, name that explicitly: 'I can do this, but I can't verify it landed correctly without X.'"* This makes the failure mode a halt-trigger rather than a silent drift.

### 2.2 Option (b) — structural primitive (the persona produces an ODD-shaped representation, validated against a Pydantic schema)

A new harness primitive: `RequestRestatement(objective: str, constraints: list[str], acceptance: list[str])` Pydantic model. The persona's first move on every user request is to construct an instance of this model (via tool call or via structured generation); the model's `@model_validator` enforces minimum field shape (objective is non-empty, at least one acceptance criterion present, no method verbs in acceptance — this last via a regex check on a known list of method-prescriptive verbs).

**Cost:** one new component or one new module under `primary-persona/`. Pydantic schema, the validator, the tool-call surface, tests. 🟡 (1-3d build.) Plus prompt-rule changes to make the persona use it.

**Leverage:** the validator catches drift the prompt-rule alone can't catch. The objective is observable + queryable (every restatement can be logged + reviewed; cumulative restatements form a corpus the user can audit).

**Failure mode 1 — gate-bypass:** an LLM-driven persona doesn't strictly need to produce structured output unless gated. If the validator fires only on explicit tool-call use, the persona can simply not call the tool. The validator becomes advisory.

**Failure mode 2 — over-mechanisation:** every user request becomes a tool-call ceremony. The user never sees this, but the persona's first turn becomes "produce a RequestRestatement object" before any actual translation — adding latency + tokens to what should be the fastest part of the conversation. Friendly user-facing flow becomes a robot-shaped form-filler.

**Mitigation:** the structural surface is opt-in (the persona reaches for it when uncertain); the prompt-rule alone is the default. This is a hybrid (option c) — but if hybrid is the answer, the right framing is "the prompt-rule alone, with the structural surface as an *escape hatch* the persona reaches for when it can't satisfy the rule confidently." That re-frames the structural surface as **complementary follow-on work**, not the primary mechanism.

### 2.3 Option (c) — hybrid (rule first, structural surface as escape hatch)

The persona always produces an internal restatement (the prompt-rule). When the persona is uncertain whether the restatement is well-formed (ambiguous request, multi-objective request, request whose acceptance is hard to articulate), it reaches for the `RequestRestatement` validator as a deterministic check.

This is the right shape long-term. But it has a cheaper precursor: ship the prompt-rule first, observe the failure rate, then build the structural surface only if the prompt-rule's failure rate exceeds a threshold.

### 2.4 Recommendation

**Ship option (a) — pure prompt-rule — first. Defer option (b)/(c) until the prompt-rule's failure mode (made-up well-formed-looking restatements) is observed in practice.**

Rationale:

1. **Cheapest test of the hypothesis.** Idea 6's premise is that an LLM-driven persona can hold ODD framing as its default mental model. The prompt-rule is the cheapest test. If the rule holds (the persona's restatements are usefully objective-shaped and don't drift into plausible-but-wrong), the structural lift was unnecessary.
2. **Aligns with the four-rule operational structure.** The four operational rules in L's §9.4 are all prompt-rules. A fifth rule for ODD-internal-model lands as the same shape; this is a content-clean addition rather than a framework-substrate addition.
3. **Composition with O's manifest provides the structural fallback for free.** O-A2's objective-binding gate already requires every code edit to declare an AC binding. The persona's restatements, if persisted (e.g., into the same active-scope sentinel O-A2 introduces), become first-party data the gate consumes. The structural surface for Idea 6 doesn't need to be authored in advance; it composes onto O-A2's manifest if and when needed.
4. **Token efficiency.** Always producing a structured restatement object for every user prompt would add ~200–500 tokens per turn (objective text + constraints + acceptance text + validator round-trip). Across thousands of turns/year, this is real. The prompt-rule is free.

**Cost vs leverage table:**

| Option | Cost | Leverage | Verdict |
|---|---|---|---|
| (a) Pure prompt-rule | ~1 paragraph in prompt.md | Catches the everyday case; persona consistently frames in objectives | **PROMOTE** — fold into L now |
| (b) Pure structural | 🟡 1-3d build + token cost per turn | Catches drift but at high overhead | **REJECT** — wrong starting point |
| (c) Hybrid (rule-then-validator-when-uncertain) | (a) + 🟡 follow-on if needed | Best long-term; deferred until needed | **DEFER** — compose on O-A2 if drift observed |

---

## 3. Question 2 — What does "light-touch education" look like in production?

The dispatch's questions: *concrete sentence shapes; when does it surface (every action / ambiguous-only / divergence-only); what's the throttling rule?*

### 3.1 Sentence shapes

Idea 2's text gives one canonical example: *"I made this a scheduled task because X happens every Tuesday."* Generalising:

```
[I did/chose/picked/set up] [the action] because [the user-observable reason].
```

The structural template:

- **Subject (implicit "I"):** the persona.
- **Verb (action):** the choice the persona made — *made it a scheduled task / dispatched a background agent / used the calendar MCP / proposed three deliverables / asked you instead of guessing*.
- **Reason:** something the user can verify against their own knowledge of their life — *because X happens every Tuesday / because this needs to run while we're not chatting / because your day-walkthrough mentioned afternoons get eaten by Slack / because I wasn't sure whether you meant draft or send*.

**The reason side is load-bearing.** A reason that references implementation detail (*"because the scope-of-work primitive supports cron-shaped events"*) fails Idea 2 — it's pedagogy on the wrong axis. A reason that references the user's life (*"because X happens every Tuesday"*) succeeds — it teaches what the chosen mechanism is **for**, not what the mechanism **is**. After three or four exposures the user has a working model of "scheduled tasks are for the every-Tuesday shape of work" without having read documentation.

### 3.2 When does it surface — three options

Three candidate surfacing rules:

- **(a) On every action.** Every choice the persona makes carries a one-sentence rationale.
- **(b) Only on ambiguous actions.** When the persona had to pick between modalities (scheduled task vs background agent vs synchronous response), it narrates; when the action is obvious, it doesn't.
- **(c) Only when divergent from user expectation.** When the persona's choice diverges from what the user might have expected (e.g., the user said "remind me" and the persona picked `/schedule` cron rather than a Telegram one-off ping), it narrates.

**(a) is too much.** Every action on every turn carries narration → pedagogy fatigue → the user starts skimming → narration becomes noise. Idea 2's text explicitly says "ambient, not interruptive."

**(c) is too little.** The persona doesn't know what the user expected; divergence-detection requires modelling user expectations, which the persona doesn't have a structural surface for. Approximating "what would a non-tech user have expected here?" is itself a hard inference. Failure mode: the persona never narrates because every choice feels obvious to the persona.

**(b) is the right shape, with concrete trigger.** The trigger isn't "is this action ambiguous to me" — that's also unstable. The trigger is structural: **"did I pick between two-or-more modalities the user could plausibly have expected?"** When the persona picked `/schedule` over a Telegram ping, both modalities were plausible — narrate. When the persona answered a factual question synchronously, no other modality was plausible — don't narrate. This is a heuristic the persona applies per-turn, but the criterion ("did I have a real choice between modalities the user might have expected?") is concrete enough that the persona can apply it consistently.

### 3.3 Throttling rule — preventing pedagogy fatigue

Even with (b), narration on every multi-modality choice can fatigue the user. Two throttling shapes:

- **Cap per turn.** At most one rationale-sentence per turn, even if the persona made multiple choices. If multiple choices exist, the persona surfaces the highest-leverage one — typically the one that introduced a primitive the user hasn't seen before.
- **Cap per session.** The first time a primitive is chosen in a session, narrate. The second time the same primitive is chosen, don't (the user's already seen it). The third time it appears in the next session, the persona narrates again only if the user's response in earlier sessions suggested they didn't fully grok it (a deferred mechanism — the persona doesn't have this signal at the prompt-rule layer; treat as future work).

**Recommendation: per-turn cap (one rationale-sentence max), with a per-session "first-use" rule overriding the cap when a not-yet-seen primitive is picked.** The first-use rule needs the persona to track "what primitives has the user already seen this session?" — which is naturally part of the conversation context (the persona reads the transcript). Across sessions, the memory-system's interaction memory carries the signal naturally.

The throttling rule's text in `prompt.md`:

> When you've made a real choice between modalities the user might have expected — for example, scheduled task vs Telegram ping, background agent vs synchronous answer, MCP tool call vs inline reasoning — surface a one-sentence rationale that ties the choice to something in the user's life or request. *"I made this a scheduled task because X happens every Tuesday"* is the shape. Don't narrate when the action is obviously the only modality; don't narrate the same primitive twice in one session unless the user's reaction suggests they didn't grok it the first time. One rationale-sentence per turn is the cap; the highest-leverage choice wins ties.

### 3.4 The relationship to Idea 6

When the persona makes the choice and surfaces the rationale, the *form* of the rationale is implicitly ODD-shaped: *"I made this [action — the method] because [user-life condition — the constraint that bounded the method]."* The user is hearing objective-driven thinking exposed at the level of a single sentence. Over time, the user's questions to the persona begin to take the same shape: *"can we make X happen every Tuesday?"* — that's an objective + constraint, framed in user-life vocabulary, no methodology word required.

This is the connection Idea 6's text §9 names. The persona's externalised narration **is** the user's gradual exposure to ODD-shaped thinking, with no pedagogy.

---

## 4. Question 3 — Composition with O (structural-enforcement)

The dispatch asks: *"if O lands a PreToolUse hook requiring 'objective the code is tied to,' does Idea 6's ODD-internal-model become the upstream surface that satisfies the hook?"* — and asks to cross-reference O's research.

### 4.1 What O actually requires

O-A2 (`objective-binding-gate`, per the O research §6.2) is a `PreToolUse` hook that fires on `Edit`/`Write` tool calls into sealed-component source paths. It requires one of three bindings to be in place:

1. The most-recent commit message has a `Component-AC: <component>/<AC-id>` trailer matching the manifest.
2. An active `pos-amend` manifest declares the component+AC pair.
3. A `.scope-of-work` sentinel in `.scratch/active-scopes/<scope-id>.yaml` declares the AC-binding.

The third path is the run-loop binding. A primary-persona dispatch that authors a plan at `docs/plans/<name>.md` writes the sentinel via plan frontmatter; the gate consults the sentinel on subsequent edits.

### 4.2 Where Idea 6 plugs in

Idea 6's internal-model is **not** the same surface as O-A2's binding. O-A2 binds **code edits** to **named ACs in a spec/proposal/plan**. Idea 6's internal-model binds **user requests** to **objective+constraints+acceptance the persona generated**. The two operate at different scopes:

- O-A2 surface: dev-mode, source edits, strict enforcement.
- Idea 6 surface: every user request (dev-mode or normal-use), conversational, persona-internal.

But they **compose meaningfully** when a user request leads to a code edit:

1. User: *"add a feature that does X."*
2. Persona's Idea 6 internal-model: objective = *X exists*, constraints = *Y, Z*, acceptance = *W is observable*.
3. Persona authors a plan at `docs/plans/<slug>.md`. The plan's frontmatter declares the AC binding.
4. The active-scope sentinel writer (O-A1 substrate) reads the plan's frontmatter, writes the sentinel.
5. Persona dispatches the build.
6. Build agent's first Edit fires; O-A2 gate consults the sentinel; allow.

The persona's Idea 6 internal-model **becomes the named AC** in the plan when the request leads to code. **Idea 6 is the upstream surface for O-A2 in the request→code flow**, but Idea 6 also covers the much larger set of user requests that don't lead to code (most non-tech-user requests don't). Idea 6's surface is broader than O-A2's; O-A2's surface is a strict subset of Idea 6's, applied at the source-edit moment.

### 4.3 Implication for sequencing

L's plan ships first (it's near-dispatch — see L's D-OWNER.1 ordering). Idea 6's prompt-rule lands inside L. L seals.

O's programme starts (O-A1, O-A2, O-A3, O-A4 sequenced).

When O-A1 lands the active-scope sentinel substrate, the primary persona's plan-authoring surface (which today writes a plan at `docs/plans/<name>.md`) gains a structural binding into the sentinel. The persona's existing Idea 6 prompt-rule continues to drive the **mental model**; O-A1's sentinel writer captures the **structured artefact** at plan-authoring time.

**No L-time work to align with O.** L ships Idea 6's prompt-rule; O ships the substrate independently; the composition is natural because O's plan-frontmatter input shape is exactly what Idea 6 produces.

### 4.4 Implication for the structural ODD surface (option (b)/(c) from §2)

If at some future point Idea 6's prompt-rule fails (the persona drifts into making up well-formed-looking restatements), the structural fallback is **a Pydantic validator on the active-scope sentinel's frontmatter** — refusing to write the sentinel if the objective field is empty, if there's no acceptance criterion, if any acceptance criterion contains a method-verb. This is a **single-day amendment** that lives inside O's substrate (O-A1 owns the sentinel writer). It does not require a separate primary-persona-side validator.

**This is the recommendation:** if Idea 6 drifts, fix it inside O's sentinel writer, not inside primary-persona. The sentinel is the natural integrity point.

---

## 5. Question 4 — Composition with L (onboarding-rewrite)

The dispatch asks: *"L already authors the persona's prompt.md content with three traits + four rules. Does L's plan need extension (a fifth rule for ODD-internal-model + a sixth for ambient-narration-on-decisions), or do these belong in a separate amendment?"*

### 5.1 The case for extending L

- **L is the plan that authors the operational-rule sections.** L's research §9.4 already enumerates four rules with a clear compose-as-a-loop framing. Adding two more rules to that loop is content-only; no new framework code, no new test file, no new test shape (just two extra named-section names in AC.O.1's presence-check).
- **The two new rules naturally compose with the existing four.**
  - Rule 5 (ODD-internal-model) composes with Rule 4 (Structural enforcement default): both are about thinking in shapes that hold across time. Rule 5 is the persona-side; Rule 4 is the harness-side.
  - Rule 6 (light-touch narration) composes with Rule 3 (Codify what repeats): both are about the persona's relationship to the user's growing understanding. Rule 3 grows the harness; Rule 6 grows the user.
- **The two rules are content the framework-not-content rule (v1.2 R16) places in workspace-supplied prose.** L's plan already lands archetype prose under the template-tree exception — the two new rules ride exactly that exception. No partition shift.
- **Owner attention budget.** Surfacing this work as a separate amendment costs an extra dispatch, an extra plan-doc, an extra seal, an extra round of the amendment-cycle ceremony. Folding into L is one extra paragraph in the plan-doc and two extra sections in the prompt.md template.

### 5.2 The case against extending L (and why it's weak)

- **L's plan has been authored; extending it adds churn just before dispatch.** Counter: the dispatch happens after Stop-hook plan seals (L's D-OWNER.1 ruling), so there's a real window. Adding two rule sections is bounded work.
- **Two new rules might not compose cleanly with the four already authored.** Counter: the §5.1 compose argument shows they do.
- **Risk that the new rules dilute the four already-locked rules' clarity.** Counter: the four-rule loop is preserved exactly; the new rules sit alongside, not inside the loop. This is a §9.4-style "X named sections must be present" amendment, not a re-architecture.

**Recommendation: extend L now, before dispatch.** L's plan §7 hard-constraint #11 already lists "Three top-value-trait sections + four always-on operational-rule sections." Extending to "Three traits + six rules" is one bullet update. AC.O.1's named-section presence test gains two new section-name strings in its list. No other AC changes.

### 5.3 What "extending L" looks like concretely

Updates to L's plan and research-companion:

1. **Plan §7 hard-constraint #11** — change "four always-on operational-rule sections" to "six always-on operational-rule sections," add the names *Frame in objectives* and *Narrate decisions lightly*.
2. **Plan §1** — bullet 2 ("Default archetype content") gains an updated description listing six rules instead of four.
3. **Plan AC.O.1** — the named-section list in the test-shape description gains the two new section-header names.
4. **Research-companion §9.4** — gains two new subsections (Rule 5, Rule 6) parallel to the existing four; the "How the rules compose" subsection at §9.4 end is updated to describe the six-rule shape.
5. **Plan D-OWNER table** — gains a new D-OWNER.5 if owner wants to rule on the recommendation; otherwise the recommendation locks per the confidence-delegation directive.

The prompt.md text for the two new rules (drafted; build agent refines wording per L's authority bound):

#### Rule 5 — Frame in objectives (internally)

> Before I act on what you've asked me to do, I form a quick mental shape of the request: what state of your world has to be true when this is done (the objective), what bounds the way I get there (the constraints — your time, your money, your reversibility tolerance, what tools you have), and how we'll both know it landed (the acceptance — what changes in your world).
>
> You don't have to talk in those terms. Most people don't. The objective is whatever you said you wanted; the constraints are usually obvious from context (you didn't ask me to spend $500 to do a $5 task); the acceptance is "you can see it worked."
>
> What this gets us: I don't drift. I don't over-build. I stop when the thing you asked for is true, not when I've used up some attention budget. If your request is genuinely ambiguous — two equally-reasonable readings — I tell you, instead of guessing.
>
> I keep this framing internal. I don't make you sit through me restating what you said in a different vocabulary. The shape is mine to hold; your conversation is yours.

#### Rule 6 — Narrate decisions lightly (anti-deskilling)

> When I make a real choice between options you might have expected — like setting up a scheduled task vs. sending you a Telegram ping, or dispatching a background agent vs. answering you here — I'll surface a one-sentence reason that ties to something in your life or request.
>
> The shape: *"I made this a scheduled task because X happens every Tuesday."* That sentence is for you, not for me. It tells you the **why** without making you learn the **how**. Over time, you'll start to see the shapes — scheduled tasks are for the every-Tuesday kind of thing, background agents are for the long-running kind of thing — without me ever lecturing you.
>
> Three rules on this so it doesn't become noise:
>
> 1. Only when there was a real choice between modalities. If the action was the only sensible thing to do, no narration.
> 2. At most one rationale per turn. If I made several choices, the highest-leverage one wins.
> 3. Within a session, don't narrate the same primitive twice — you've already seen it. If your response suggests you didn't grok it, then yes.
>
> Why I do this: not narrating at all turns me into a black box, and using me long enough turns into dependency you can't diagnose. A one-sentence rationale exposes my reasoning without turning every interaction into a lesson. You stay in the driver's seat.

---

## 6. Question 5 — Composition with Idea 3 (SDLC plugin)

The dispatch asks: *"Idea 3 says ODD is the default framing for projects authored inside pOS v2. Idea 6 says ODD is the default framing for conversations. Does Idea 6 need to align its surface with whatever Idea 3 produces, or does Idea 6 ship first and Idea 3 inherits the conversation-level surface?"*

### 6.1 Different scopes, same vocabulary

Idea 3 (line 285): *"ODD is the default for new projects authored inside pOS v2. When the user starts a new project using pOS v2, the SDLC plugin defaults its research/spec/plan/build/review/verify stages to ODD's objective-centric shape unless the user explicitly opts out."*

Idea 6 (line 357): *"the primary persona should think in objectives by default. ODD is not only the methodology pos-v2 uses to author its own components — it is also the shape the primary persona's internal model of every user request takes, inside every pos-v2 conversation."*

Idea 3 is **project-shaped**: the SDLC plugin owns the project-level lifecycle; ODD-shaped means the project's stages are objective+constraints+acceptance shaped. The user is doing software-development-shaped work, and the plugin shapes the SDLC artefacts.

Idea 6 is **turn-shaped**: every conversational turn carries an internal ODD framing of the request, regardless of whether the work is project-shaped, household-shaped, ad-hoc-shaped, or anything else.

The two surfaces share methodology (ODD), share vocabulary (objective / constraints / acceptance), and share design principles (structural over advisory, behaviour-count, re-extension over silent handling). They do not share implementation.

### 6.2 Which ships first, and what the later one inherits

Idea 6 ships first because L is near-dispatch. Idea 3 lands much later — Idea 3 is part of "Initial plugin suite" (line 278), which has no plan today and depends on the plugin extension protocol being battle-tested in workspace-bootstrap (line 280).

When Idea 3 lands, it inherits:

- The vocabulary (objective / constraints / acceptance) from `docs/odd-methodology.md` and `docs/odd-in-pos.md` — the same vocabulary the primary persona uses internally per Idea 6.
- The persona's behaviour at the conversation layer — when the user says *"start a new project,"* the persona's Idea-6 internal model frames the request, and the persona's response composes naturally with whatever Idea-3-plugin surfaces it dispatches to.

### 6.3 Required cross-surface alignment work — none

Idea 6 ships at L's prompt.md layer and produces no artefacts that constrain Idea 3's design. Idea 3 ships as a plugin that registers via workspace-bootstrap's extension protocol; the plugin can produce its own ODD-shaped artefact templates (ODD-shaped research-plan template, proposal template, etc.) without coordinating with Idea 6 at all.

The **minor alignment** to do at Idea-3 plan-time (much later): the plugin's stage-template authoring should match the methodology vocabulary the persona uses in conversation, so the user's experience is continuous (the same words mean the same things in conversation as in their project artefacts). This is content-coherence, not framework-integration.

**Implication for sequencing:** Idea 6 ships in L, no Idea-3 dependency. Idea 3 ships much later as a plugin — when it does, it composes on whatever the persona's conversation-level ODD framing has settled into.

---

## 7. Question 6 — Anti-deskilling enforcement (the lint)

The dispatch asks: *"the Non-tech-users spec objective requires 'auto-create+explain; silent auto-creation is a lint failure.' Idea 2's ambient narration IS the explain side. Should this amendment also land the lint? Or does the lint belong in O?"*

### 7.1 What the lint actually checks

The spec objective (line 153, behaviour-level acceptance audit): *"every auto-created skill/workflow produces an accompanying explanation artifact; silent auto-creation is a lint failure."*

What "silent" means concretely: when the framework auto-creates a skill, slash command, scheduled routine, MCP server registration, or any persistent harness artefact on the user's behalf, an explanation surface must be produced and presented to the user — either in-conversation (the rationale-sentence Idea 2 prescribes) or in a discoverable artefact (a section in the persona's session-end summary, a memory-graph episode the user can search, a file in `.pos/auto-creations/<ts>.md`, etc.).

The lint's deterministic check: for every event of class `auto_creation` (whatever the harness's event taxonomy names this), within the same session there must exist either:

- A persona response sent to the user containing a rationale-sentence that references the auto-created artefact's name or category, or
- An explanation artefact written to the appropriate sidecar location.

If neither: lint failure.

### 7.2 Which surface emits `auto_creation` events today

**None of the sealed components do.** Auto-creation as a class doesn't exist as a typed event today. Sealed components emit OTel spans and pyee events for their own activity (cost ledger writes, kill-switch fires, etc.) but not auto-creation events. The auto-creation surface is part of the future capability set — skill-authoring pipeline (R14), proactive-suggestions (Idea 5), persona-authoring autonomous pipeline (D5/D6 of primary-persona-loader).

This means the lint is **mostly forward-looking** — it gates behaviour that doesn't exist yet. There's one near-term auto-creation surface that *does* exist today: the primary-persona's `is_starter` → `is_starter=False` transition during L's onboarding. This is auto-creation in spirit (a contract was filled in by the persona's inference) and L's plan already pairs it with explanation (the persona's reflect-back in the proposal moment + the captured summary).

### 7.3 Does the lint ride O, L, or its own amendment?

**Not L.** L is content + onboarding-rewrite. The lint is a structural check (a hook on auto-creation events, refusing the event if no paired explanation surface is present). Wrong-shape for L.

**Not O directly.** O's audit (research §2) lists 27 advisory rules. Auto-create+explain is **not** one of them — it's a *spec acceptance criterion* (line 153), not an advisory rule. O's amendment programme A1–A4 doesn't include this gate; it would be a fifth amendment grafted into the programme.

But the lint **fits naturally on O's substrate.** O-A1 lands the hook-registration substrate, the workspace-mode partition (DEV MODE / NORMAL USE), and the active-scope sentinel surface. O-A2 lands an audit-log writer. The lint composes on those exactly: a `PreToolUse` or `PostToolUse` hook (depending on which surface emits auto-creation events) consults the same workspace-mode bit, writes the same audit log, fires through the same hook substrate.

**Recommendation: a small new amendment P (`auto-create-explain-lint`), dispatched after O-A1 seals.** Sized the same as O-A4 (1-2d). Owns:

- The `auto_creation` event taxonomy (which existing or future events count) — likely a small enum + a registration surface.
- The pairing-check hook.
- The audit-log entries for paired vs unpaired auto-creation events.
- The fail-shape (lint failure means the auto-creation is reverted, queued for owner review, or marked-pending-explain — D-OWNER.6 below).

P's dependency on O-A1 (substrate) is structural; it can ship in parallel with O-A2/A3 if needed (different surface, different gate). Per `feedback_serialize_amendment_builds` parallel build is forbidden in canonical tree — but P's design is small enough that it's a low-risk single-shot.

### 7.4 Why P is its own amendment and not folded into O

- **Different audit pedigree.** O's research is structural-promotion-of-advisory-rules. P's is spec-acceptance-criterion-realisation. Folding P into O dilutes O's narrative ("the audit") with content the audit doesn't cover.
- **Different timing.** O-A1–A4 is a known programme; P is a follow-on. Bundling delays P or bloats O.
- **Different test surface.** O's tests assert hook-substrate behaviour and gate-decision correctness. P's tests assert event-pair correctness — different test families.

**Sequence:** O-A1 → O-A2 → O-A3 → O-A4 → P (or O-A1 → P in parallel with O-A2 if owner rules parallel-safe; recommendation: serial).

### 7.5 Cross-reference to O's research

P is **not** in O's recommended programme (research §6) and is **not** in O's audit table (research §2). Adding P to O's programme in retrospect requires O's research to be amended; this research artefact is the addendum. When O's plan-author authors O-A1's proposal, they should reference this artefact's §7 to surface that P is queued behind A1 with substrate dependency.

---

## 8. Three-lens analysis — the combined recommendation

### 8.1 Lens 1 — Claude-leverage-first

The combined recommendation (extend L with two new rules + new P amendment):

- **L extension:** uses no new Claude primitive — the rules are content in `prompt.md`, which Claude reads on every turn. The persona's behaviour (Idea 6's internal model + Idea 2's narration) is LLM-driven; no harness wiring required beyond the already-existing prompt.md substrate.
- **P amendment:** uses Claude Code's `PreToolUse`/`PostToolUse` hook surface, the same mechanism O-A1–A4 uses. No new primitive; composition with O-A1's substrate.
- **Future structural fallback (option (c)):** would compose on O-A2's manifest surface. No new primitive.

End-to-end: every component of the recommendation leans on Claude primitives + pos-v2 substrate that's either sealed or in-flight. No new framework primitives are required.

### 8.2 Lens 2 — Harness + primary-persona value

**Primary-persona test.** The recommendation is **directly load-bearing** for the translation-layer prime objective:

- Idea 6 makes the persona's internal model tight without surfacing technical vocabulary to the user — this **is** the translation layer's central act, applied to every conversational turn rather than only at code-build time.
- Idea 2's narration externalises the translation **selectively** — the user gets exposure to the shape of ODD thinking in user-life vocabulary, building intuition without burden.

Both ideas reduce translation burden: Idea 6 by tightening the persona's bounds (so its outputs are higher-leverage); Idea 2 by teaching the user enough that over time, requests become easier for the persona to translate (the user's vocabulary moves up the sophistication curve). This is a **compounding** translation-layer improvement — the more sessions, the better the user's framing of requests, the lower the per-request translation cost.

**Harness test.** The recommendation adds:

- Two operational rules that future persona-authoring tools (D5/D6 of primary-persona-loader) compose on, the same way the existing four rules do.
- The auto-create+explain pairing surface (P), which becomes a reusable pattern for every future auto-creation primitive (skill-authoring, proactive-suggestions, persona-authoring).

The harness test passes; both ideas ladder up cleanly.

### 8.3 Lens 3 — ODD authoring

**The recommendation itself is ODD-shaped.** L's extension lands six AC.O.1 named-section names (deterministic test-shape: presence of section headers). P's ACs are deterministic event-pair checks. No method-in-AC, no judgement-shaped acceptance, no orphan code.

**Idea 6's failure mode (made-up restatements) is itself ODD-shaped to detect.** If the prompt-rule fails, the failure is observable (the persona's behaviour drifts), nameable (per-request restatement quality), and re-extendable (the structural fallback in §4.4 is a Pydantic validator on the sentinel — clause-(g) pattern applied to the sentinel writer).

**Idea 2's narration is bounded by the throttling rule.** The throttling rule is itself a deterministic check (per-turn cap = 1; first-use rule = primitive-name string-match against the session transcript). The rule isn't structural-enforced (no hook checks "did the persona narrate"), but the rule's failure modes are detectable in observability — narration-rate-per-turn is queryable.

---

## 9. Implementation summary — concrete actions

Per the dispatch's "name slugs + sequence; don't author plan-docs" framing where the recommendation distributes:

### 9.1 L extension (immediate, in-flight L plan-doc)

Edit `docs/plans/primary-persona-conversational-onboarding-and-default-archetype.md`:

1. §1 bullet 2 — change "four always-on operational-rule sections" to "six."
2. §7 hard-constraint #11 — same change; add the two new rule names to the enumerated list.
3. AC.O.1 — extend the named-section list in test-shape description with two new section-header strings.

Edit `docs/plans/research/primary-persona-conversational-onboarding-and-default-archetype-research.md`:

4. §9.4 — add Rule 5 (Frame in objectives) and Rule 6 (Narrate decisions lightly), parallel to existing Rules 1–4.
5. §9.4 "How the rules compose" — extend the loop description to cover six rules.

Both edits land before L dispatches. Owner ruling required if D1, D3, or D4 below resolves differently.

### 9.2 P amendment (follow-on after O-A1)

**Slug:** `auto-create-explain-lint`.

**Sequence:** dispatched after O-A1 seals (substrate dependency). Optionally parallel with O-A2/A3 if owner rules parallel-safe — recommendation is serial.

**Don't author plan-doc here** (per dispatch instruction). Plan author at dispatch time uses this artefact §7 + spec line 153 + O-A1's actual sealed substrate as inputs.

### 9.3 Idea 3 alignment (deferred — no current action)

When Idea 3's plugin plan is authored (much later, after the workspace-bootstrap extension protocol matures and a plugin-suite-design cycle runs), the plan-author references this artefact's §6 to ensure Idea 3's stage-template vocabulary aligns with the persona's conversational ODD framing already in production.

### 9.4 Structural fallback for Idea 6 (deferred — drift-triggered)

If Idea 6's prompt-rule shows drift in production (the persona produces well-formed-looking restatements that don't correspond to spec ACs), a single-amendment follow-on adds a Pydantic validator to O-A1's sentinel writer. Slug: `odd-restatement-validator`. Author when drift signal triggers; not before.

---

## 10. Decisions surfaced for owner ruling

Four decisions surfaced. Each carries a recommendation per the confidence-delegation directive.

### D1 — Two rules or one combined rule in `prompt.md`?

**Question.** Should Idea 6 (internal ODD framing) and Idea 2 (light-touch narration) land as **two separate rules** alongside L's existing four, or as **one combined rule** ("ODD-shaped thinking with light narration")?

**Options:**

- **(a) Two rules.** Rule 5 = "Frame in objectives (internally)" + Rule 6 = "Narrate decisions lightly (anti-deskilling)." Parallel to existing rule shape.
- **(b) One combined rule.** "Frame in objectives, narrate decisions lightly" as a single Rule 5.

**Recommendation: (a) — two rules.** Rationale: the four existing rules each address a distinct behavioural posture; combining Idea 6 and Idea 2 into one rule conflates the *internal* model with the *external* surface, making both harder to apply individually. The two rules' compose-with-existing-rules story is also distinct (Rule 5 ↔ Rule 4, Rule 6 ↔ Rule 3 — see §5.1) and would be lost if combined. Cost difference is one paragraph of `prompt.md`; clarity benefit is significant.

### D2 — Is amendment P part of O's programme (a fifth O amendment) or its own one-off?

**Question.** Does the auto-create+explain lint (§7) ship as O-A5 (extending O's programme), or as a standalone amendment (P) sequenced after O-A1?

**Options:**

- **(a) Fold into O as O-A5.** O's programme grows to five amendments.
- **(b) Standalone amendment P.** Separately authored, dependency on O-A1.

**Recommendation: (b) — standalone P.** Rationale: O's audit pedigree is structural-promotion-of-advisory-rules (research §1). P's pedigree is spec-acceptance-criterion-realisation (a different surface — line 153 of the spec). Conflating dilutes O's narrative. P composes on O-A1's substrate without needing to be inside O's authoring window. Risk of (a): O's research has to be amended retroactively, and O-A2–A4 may seal before P is fully designed; (b) keeps each amendment's scope intact.

### D3 — Extend L now (before dispatch) or ship the two rules as a follow-on amendment after L seals?

**Question.** L is near-dispatch. Adding two new rules to its prompt.md template + research-companion §9.4 + plan AC.O.1's named-section list is bounded work but does extend the in-flight plan.

**Options:**

- **(a) Extend L now.** Two new rule sections + two new named-section names in AC.O.1 + research-companion update. L dispatches with six rules instead of four.
- **(b) Follow-on amendment after L seals.** L ships with four rules; new amendment Q adds Rules 5 and 6 to the template after L seals.

**Recommendation: (a) — extend L now.** Rationale: the work is content-only (no new framework code, no new test file), the rules naturally compose with the existing four, the test shape is unchanged (AC.O.1 is a presence-check on a section list — adding two names to the list is one bullet edit), and bundling avoids an entire follow-on amendment cycle for what is effectively a content addendum. Risk of (a): L's plan grows by ~30 lines and the dispatch is delayed by the owner ruling cycle; mitigated by surfacing only the four owner-rulings (D1–D4 here). Risk of (b): two separate amendments for what is one design-coherent unit; longer time-to-production for the prime-objective-load-bearing rules.

### D4 — When does Idea 2's ambient narration surface — every action / ambiguous-only / divergent-only?

**Question.** Per §3.2, the surfacing rule has three candidate shapes. The recommendation locks (b) ambiguous-only-with-modality-trigger but the owner may prefer differently.

**Options:**

- **(a) Every action.** Pedagogy-fatigue risk; explicit advisory in Idea 2's text against this.
- **(b) When the persona had a real choice between modalities the user could plausibly have expected** — with per-turn cap and within-session-first-use override. The recommendation.
- **(c) When the persona's choice diverged from user expectation.** Requires modelling user expectations; unstable trigger.

**Recommendation: (b) — modality-choice trigger with per-turn cap and per-session first-use rule.** Rationale: matches Idea 2's "ambient, not interruptive" framing exactly; trigger is concrete enough for the persona to apply consistently; throttling prevents fatigue. Risk: false negatives where the persona didn't recognise it had a real choice. Mitigated by the persona's existing operational Rule 1 (Lean on the harness) — which already pauses to consider Claude/harness primitives, surfacing the modality-choice naturally.

---

## 11. Halt-and-surface findings

- **No required new top-level objective.** The recommendation satisfies existing spec line 152–153 (Non-tech users, behaviour-level acceptance audit) directly and the prime-objective AC.PO.1/AC.PO.2 from L's plan.
- **No ODD violation in surrounding code.** The two new rules are content. The lint amendment P composes on O's hook substrate (a substrate authorised by O's research). No surrounding-code violations to surface.
- **No shift in the framework/content partition.** The two new rules ride exactly the L template-tree exception (R16) the existing four rules ride. P's hook is framework, exactly the partition O is establishing.
- **No required source-edit outside primary-persona / hands-off-lifecycle / a hook substrate already authorised by O.** L's edits are in `primary-persona/`. P's hook lands in `hands-off-lifecycle/hooks/structural/` (per O-A1's substrate placement, research §9, "Q1 — sub-component within hands-off-lifecycle"). No source-edit elsewhere.

No halt required.

---

## 12. Cross-references

- `docs/FUTURE_IDEAS.md` Idea 2 (line 259, light-touch education), Idea 3 (line 285–286, SDLC plugin's ODD-default clause), Idea 6 (line 353, ODD as default conversational framing).
- `docs/odd-methodology.md` (the methodology these ideas operationalise).
- `docs/odd-in-pos.md` (the in-pos illustrative companion).
- `docs/VALUE_PROPOSITION.md` (the translation-layer prime objective Lens 2 derives from).
- `docs/spec/pos-v2-objectives-spec.md` line 152–153 (Non-tech users objective + behaviour-level acceptance audit).
- `docs/plans/primary-persona-conversational-onboarding-and-default-archetype.md` (in-flight L plan, §7 hard-constraint #11 + AC.O.1 are extended per §9.1 above).
- `docs/plans/research/primary-persona-conversational-onboarding-and-default-archetype-research.md` §9.4 (the four operational rules; §9.1.1 the three top-value traits — extended per §9.1 above).
- `docs/plans/research/structural-enforcement-of-critical-requirements-research.md` (O programme; §6 the four-amendment chain; §9 the substrate placement; §10 the open decisions; this artefact §4 and §7 cross-reference).
- `docs/plans/research/persona-capability-knowledge-grounding-research.md` (M extension; §9.4-shape rules; the prompt-as-spine pattern this recommendation rides).

---

*End of research artefact.*
