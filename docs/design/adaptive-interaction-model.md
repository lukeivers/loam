# loam — The Adaptive Interaction Model (the persona's user-model spine)

**Date:** 2026-05-31
**Status:** READ-ONLY design (nothing built; every schema/hook/file change below is an owner-gated follow-on build)
**Owner:** Luke Ivers
**Author:** dispatched design agent (Opus)
**Scope-tightness (Lens 4):** the *structure* is high-confidence and tightly scoped (the schema, the openness-biased default, the deterministic-lookup consumption path); the *content* — which signals move which cell, the exact thresholds — is low-confidence and explicitly left to calibrate-on-real-data. Deterministic in structure, adaptive in content.

**Reads this composes on (Tier-0 verified on disk 2026-05-31, do NOT re-derive):**
- The keep-pace spine — `keep-pace-with-user.md` (the live UserPromptSubmit + PreToolUse hook chain; KP1 retrieval, KP5 OBJECTIVES.md, KP7 SessionStart surface, KP9 draft-gate). **This model is the generalization of that design's Layer-4 "per-topic depth-preference model," which is currently in the NOT-BUILT backlog** (`fbm-state-and-memory-roadmap-2026-05-29.md` Q1 table: KP-backlog "NOT BUILT"). This design IS that L4, widened from one axis (depth) to four and from "topic" to a component×axis matrix.
- The abstraction-voice research — `keep-pace-research-abstraction-voice.md` §4.4 (PONTE-style coarse, auditable, behaviorally-learned per-topic preference; the four-axis register judge; the "self-correction fails for register → independent gate" finding).
- The three voice principles this **parameterizes** — `feedback_abstraction_first_default.md`, `feedback_translate_outbound_too.md`, `feedback_coworker_relationship_framing.md`.
- A consumer — `feedback_user_distress_is_priority_diagnostic_signal.md` (the non-tech-user self-recovery entry point).
- The re-eval loop pattern to reuse — `claude-capability-adoption-loop-design.md` (cadence/triggers/judge-verdict/auto-apply-vs-owner-gate).
- The store — `fbm-state-and-memory-roadmap-2026-05-29.md` (FBM/S2 corpus; OBJECTIVES.md file-shape precedent at `~/.claude/OBJECTIVES.md`, verified live).
- The product frame — `VALUE_PROPOSITION.md` (the persona IS the translation layer; this model is what makes the translation per-user instead of one-size).

**Tier-0 machine facts that shaped this design (verified 2026-05-31):**
- `~/.claude/settings.json` `hooks` = `{UserPromptSubmit, PreToolUse}` — **the keep-pace chain is LIVE.** (The 2026-05-29 roadmap found it un-flipped; it has since been activated.) This model parameterizes a *running* read-path, not a hypothetical one. This is the single most leverage-changing fact: the consumption interface (§4) plugs into hooks that already fire every turn.
- No `depth-preferences.md` / `interaction-model.md` / `user-model.md` / `user-profile.md` exists anywhere in the tree or `~/.claude`. **This model is net-new state** (`find` over both trees, empty).
- `~/.claude/OBJECTIVES.md` is live (1689 bytes, two seeded objectives) — its header pattern (`status` OWNER-GATED + soft-auto `last-touched`/`cadence` + `detail-path`) is the exact file-shape precedent this design reuses for the profile.

---

## 0. The one-paragraph version

loam must respond to the *specific* user — how much technical detail it exposes, how it talks, how much it decides versus surfaces, and how it teaches — and that response must adapt per-component, continuously, from evidence. The mechanism is a **deterministic matrix** (`~/.claude/INTERACTION-MODEL.md`) of `component × axis → {value, confidence, evidence-pointers}`, where the structure is fixed and auditable and only the cell *contents* move. The matrix **defaults openness-biased** — every cell starts at "assume an engaged learner who wants to grow," dialing *down* exposure only on accumulated evidence, never up-front. The persona **reads the matrix at turn time via the already-live keep-pace hooks** (deterministic lookup, not vibes) to set exposure, tone, autonomy, and education for the active component; **evidence updates cells with hysteresis** (a confidence band, debounced against single data points) on the same re-eval cadence as the capability-adoption loop; the user can **inspect and correct their own profile in plain language**, and the persona shows its reasoning ("I'm showing you this because X — tell me to dial it back"). It is the **spine**: the three voice principles become parameterized lookups against it instead of fixed rules, the abstraction-voice gate scores against the cell instead of a global setting, and the non-tech-recovery design and capability auto-adoption both read it.

**The single F2 headline (the owner's vision, engaged critically):** the owner's "default to assume they want to engage whether or not it's true" is *correct as a prior but dangerous as a destination*. The danger is the **mislabel-and-condescend** failure in reverse: defaulting everyone to "engaged learner" risks **firehosing a genuinely-overwhelmed user with education they didn't want at the exact moment they're already lost** — which is the precise condition `feedback_user_distress_is_priority_diagnostic_signal.md` flags as the #1 fire alarm. The design guards this with an **asymmetric update rule** (§2.4): *distress / overwhelm dials exposure down fast and on a single signal; the climb back up to "more technical" is slow and needs repeated evidence.* Openness is the default, but the floor drops out the instant the user signals overload. This is the load-bearing safety property and it is built in, not bolted on.

---

## 1. The model schema

### 1a. The matrix shape

One file, `~/.claude/INTERACTION-MODEL.md`, index-and-detail shaped exactly like `OBJECTIVES.md` (so it inherits the FBM budget discipline and lands in M2's audited-surface set). It is a **2-D matrix**: rows = components/areas, columns = axes; each cell carries a value + a confidence + dated evidence pointers.

```
component-slug:
  technical-exposure:  { value: open,        confidence: prior, evidence: [] }
  autonomy:            { value: surface,     confidence: prior, evidence: [] }
  tone:                { value: peer-warm,   confidence: prior, evidence: [] }
  learning-appetite:   { value: invite,      confidence: prior, evidence: [] }
  last-evaluated: 2026-05-31
```

`confidence: prior` means "this is the openness-biased default, no evidence yet." It rises to `low → medium → high` as evidence accumulates (§2). Evidence pointers are dated turn-references (journal/episode IDs), never raw quotes inline — auditable but budget-bounded.

### 1b. The component/area taxonomy — what "parts" can a user be technical/non-technical about?

**F2 — the obvious choice is wrong.** `docs/components/index.md` lists 18 runtime components (`orchestrator`, `cost-governance`, `reversibility-primitive`…). Keying the matrix on *those* is a **Lens-2 violation**: those are dev-internal mechanisms the user should never have to hold (the exact thing `abstraction-first` forbids). A user is never "technical about the reversibility-primitive"; they're technical about *the kind of work they bring*. The taxonomy must be **interaction-surface-shaped, not implementation-shaped** — the areas a user actually has a stable stance toward. Proposed taxonomy (open list; the matrix grows rows as new areas of work appear — see §2.5):

| Area slug | What the user has a stance about | Example evidence of "wants technical here" |
|---|---|---|
| `harness-mechanics` | how loam itself works (hooks, memory, scheduling, the persona's own machinery) | "show me the hook", "why did it use a background agent" |
| `code-and-builds` | code the persona writes / debugs / ships for them | "show me the diff", reads the code, "use a generator not a list" |
| `their-domain-work` | the user's own subject-matter output (e.g. the LitRPG pipeline, a revenue model) | engages with craft/strategy depth; pushes back on substance |
| `ops-and-money` | tokens, cost, scheduling, external actions, anything with a real-world consequence | "how much did that cost", "what's it going to do at 9am" |
| `decisions-and-tradeoffs` | how much the persona explains *why* vs just acts | "walk me through the options", vs "just pick one" |
| `default` | the catch-all every new/unseen area inherits from until it earns its own row | — |

**Why this set:** it maps to the *kinds of translation* `VALUE_PROPOSITION.md` §"Unpacking the translation" already enumerates (modality, specialist-routing, authority, proactive-surfacing, outcome-ownership) collapsed to the surfaces a user forms a *preference* about, not every internal. The owner's vision is explicit that a user "may want technical in some areas, non-technical in others" — `harness-mechanics` vs `their-domain-work` is exactly that split (Luke himself: high exposure on loam-infra, wants craft-depth on fiction). The list is deliberately **coarse (~6 areas, not 18 components)** — `keep-pace-research-abstraction-voice.md` §4.4 makes the coarse/auditable choice load-bearing: "a non-tech user must be able to see and correct 'you've decided I want technical detail about X' in plain language, which a latent vector can't offer."

### 1c. The axes per cell, value ranges, and defaults

Four axes (the owner's stated set: `{technical-exposure, decide-vs-surface autonomy, tone/voice, learning-appetite}`). Each is a small ordered enum (auditable, not a learned float):

| Axis | Range (ordered) | Openness-biased default | What it controls |
|---|---|---|---|
| **technical-exposure** | `minimal → plain-plus-offer → open → deep` | `open` *(but see floor below)* | how much mechanism/detail the persona surfaces unprompted in this area |
| **autonomy** | `surface → recommend → decide-and-tell → decide-silently` | `surface` for ops-and-money/decisions; `recommend` elsewhere | decide-vs-surface — how much the persona acts vs asks |
| **tone** | `formal → peer-warm → casual → terse-execution` | `peer-warm` | register/voice (parameterizes the coworker-relationship principle) |
| **learning-appetite** | `none → answer-if-asked → invite → teach-alongside` | `invite` | whether the persona offers the explanation *alongside* the technical thing |

**The openness-biased prior, stated precisely:** a brand-new user, or any unseen area, starts at `technical-exposure: open` + `learning-appetite: invite` — i.e. *present the technical thing WITH the explanation, and invite engagement* — because the owner's thesis is that hiding-by-default harms the non-technical-but-wants-to-grow user. This is the **deliberate evolution of `abstraction_first_default.md`**, which currently defaults to `minimal` (full-hide). See §6.1 for why this is a *correct* revision and not a contradiction.

**The floor exception (the safety property, §0 headline):** `autonomy` defaults to the **cautious** end (`surface`/`recommend`), NOT the open end, for `ops-and-money` and anything with real-world consequence — because exposure is reversible (you can dial detail down next turn) but a wrong autonomous *action* may not be. Openness-bias applies to *talking*, not to *acting*. This mirrors the capability-adoption-loop's "move fast on knowledge, slow on behavior" rule (`claude-capability-adoption-loop-design.md` §3b) and the existing safety-layer/ASK-FIRST-on-public gates, which this model never overrides.

---

## 2. The evidence → update mechanism

### 2a. The signals (what observable thing moves which cell)

Signals are read from the **same turn stream the keep-pace hooks already see** — the prompt, the reply, the user's next reaction. No new instrumentation; these are behavioral proxies (PONTE's "learn from behavior, not config" — `keep-pace-research-abstraction-voice.md` §4.4):

| Observable signal | Cell it moves | Direction |
|---|---|---|
| User asks "how does that work / show me the code / why" | active area · technical-exposure | ↑ |
| User engages with a technical answer (follow-up in kind, doesn't bounce) | technical-exposure, learning-appetite | ↑ |
| User says "just tell me if it worked / I don't need the details / skip it" | technical-exposure | ↓ |
| User corrects the persona on substance in an area | technical-exposure (they have expertise here) | ↑ |
| **User expresses confusion / overwhelm / "I'm lost" / repeated "are you there"** | technical-exposure ↓↓ + learning-appetite ↓ | **↓ fast (single signal — §2.4)** |
| User says "just do it / stop asking me / you decide" | autonomy | ↑ (toward decide) |
| User overrides a persona decision / "ask me first next time" | autonomy | ↓ (toward surface) |
| User mirrors terse execution-mode (short, imperative) | tone → terse-execution | ↑ (per-turn, soft) |
| User explicitly asks to learn / "teach me / I want to understand this" | learning-appetite → teach-alongside | ↑ |
| User explicitly states a preference ("always show me X" / "stop explaining Y") | the named cell | **hard-set + high-confidence + locked-until-re-stated** (§5) |

### 2b. The update rule (hysteresis + confidence, so one data point can't thrash)

A cell does **not** move on a single ordinary signal. Each cell holds a small signed **evidence counter** within its confidence band; an ordinary signal increments/decrements the counter, and the cell's *value* only steps when the counter crosses a threshold (the debounce / hysteresis). This is the owner's "demonstrably + **consistently**" requirement (`keep-pace-research-abstraction-voice.md` §4.4) made mechanical: consistent repeated signal moves the value; a one-off does not.

- **Confidence rises with corroboration:** `prior → low` on first corroborating signal, `low → medium → high` as the counter accumulates in one direction. Contradicting signal *first* decays confidence before it flips the value (so a settled "high-confidence open" survives one off-day, but sustained contradiction still moves it).
- **An explicit user statement bypasses the counter** — it hard-sets the value at `high` confidence immediately (§5). Behavior should never out-vote a stated preference.
- **Thresholds are calibrate-on-data, NOT imported** (Lens 4 / the keep-pace "do not import a tuning number" discipline). Ship the band structure; tune the step-count on real traffic.

### 2c. The openness-biased prior in the math

The prior isn't just the starting value — it's a **soft pull**. With zero evidence the cell sits at `open`; the climb from `open → deep` needs only modest positive evidence (the user is *welcome* to go deeper), but the drop from `open → minimal` for the *technical-exposure* axis needs sustained negative evidence — **except** the overwhelm signal, which is exempt (§2.4). The asymmetry encodes "assume they want to engage, but never make a lost user fight to be heard."

### 2d. The asymmetric safety rule (the load-bearing guard — F2 §0)

**This is the single most important rule in the design.** Updates are deliberately asymmetric to guard the owner's openness-default against its worst failure mode:

- **Down (toward less exposure / less teaching) on overwhelm/distress = FAST, single-signal, no debounce.** The instant the user signals confusion or overload, `technical-exposure` and `learning-appetite` drop immediately. Rationale: `feedback_user_distress_is_priority_diagnostic_signal.md` makes repeated user confusion the #1 fire alarm — the model must *react to it*, not average it away under hysteresis. Firehosing education at an already-lost user is the condescension-in-reverse failure (§7).
- **Up (toward more exposure) = SLOW, debounced, needs repeated corroboration.** Climbing someone toward "deep technical" is never urgent and is the higher-blast-radius direction (over-firehose), so it pays the full hysteresis cost.

The default is open; the floor is one distress signal away. That is the resolution of the determinism-vs-openness-vs-safety tension.

### 2e. New rows appear by demand (the matrix grows with the work)

When the user works in an area with no row, the area inherits `default` and a row is lazily created on first sustained signal — the same demand-paging shape FBM uses for cold memories (`keep-pace-with-user.md` §2 Dimension B). The matrix is never pre-enumerated to exhaustion; it grows to fit how *this* user actually works.

---

## 3. The re-evaluation loop (cadence, triggers, what it measures)

Reuses the **capability-adoption-loop pattern wholesale** (`claude-capability-adoption-loop-design.md`) — time-based floor + event triggers + a fresh-evaluator judge + auto-apply-vs-owner-gate. It does **not** invent a new loop.

### 3a. Two update paths — fast (per-turn) and slow (periodic)

- **Per-turn (fast path):** the evidence counters in §2 increment **live, every turn**, inside the already-firing keep-pace hooks. No separate schedule — the read-path that consumes the model (§4) also writes the counter for the turn it just saw. This is turn-granular and free (it rides KP1's existing UserPromptSubmit pass). *Cell value* changes here only when a counter crosses threshold (or on an explicit statement).
- **Periodic (slow path / the re-eval loop proper):** a low-frequency consolidation pass (recommend **weekly floor**, same as the adoption loop) that (a) re-reads the accumulated counters + recent journal, (b) re-derives confidence, (c) checks for **drift** (an area whose evidence stopped matching its value — e.g. a value still says `deep` but the last month shows the user bouncing off detail), and (d) **surfaces** any proposed value change to the user before committing the non-trivial ones (§3c). Mechanism: a `claude -p` consolidation step (Sonnet, via the real `claude_print_synthesis_client.py` wrapper — `feedback_no_anthropic_api_key`) on the existing Stop/periodic fold, exactly the FBM-T3.1 consolidation seam (`fbm-state-and-memory-roadmap-2026-05-29.md` C1).

### 3b. Event triggers (responsiveness)

- **Overwhelm/distress signal** → immediate out-of-cycle down-update (§2.4) — does not wait for the weekly pass.
- **Explicit preference statement** → immediate hard-set (§5).
- **Sustained counter cross** → immediate per-turn value step (the fast path).
- The weekly floor is the backstop that catches *slow* drift the per-turn path is too local to see.

### 3c. What it measures + writes back

Per the owner's "continuous re-evaluation of engagement level, voice, and tone": the loop measures, per area, **engagement** (does the user follow up in kind or bounce), **voice/tone** (terse-execution vs discursive — read from message shape), and **depth-pull** (asks-for-more vs asks-for-less). It writes the re-derived `{value, confidence, evidence}` back to `INTERACTION-MODEL.md` via the FBM write path. The judge step (Lens 5 CycleVerdict, reused from the adoption loop) is a fresh evaluator confirming the proposed cell changes are evidence-supported and didn't drift into over-personalization (§7) before any non-trivial change is surfaced.

---

## 4. The consumption interface (deterministic lookup, not vibes)

The persona must **read the matrix to make each exposure/tone/autonomy/education decision at turn time** — and it must be a lookup, not a judgment call, or the determinism property is lost.

### 4a. The read path (rides the live keep-pace hooks — Tier-0: they're already wired)

1. **UserPromptSubmit (read).** The keep-pace UserPromptSubmit hook already computes the **work-anchor** (active objective + subgoal + last topic — `keep-pace-with-user.md` §1 fix #1). This design adds one step: **map the work-anchor to an area slug** (a small deterministic classifier — keyword/objective-tag map, e.g. litrpg-objective → `their-domain-work`, a loam-dev topic → `harness-mechanics`), then **look up that area's four cells** and inject them as a terse, plain, system-reminder-framed directive: *"This area's settings — exposure: open; autonomy: recommend; tone: peer-warm; teaching: invite."* This is the Layer-3 re-injection of `keep-pace-research-abstraction-voice.md` §4.3, now keyed to the matrix cell instead of a global rule. The injection is **clean (no disclaimer wrapper)** per that research's finding.
2. **Draft (apply).** The persona drafts with the injected cell settings as the register/autonomy target for this turn.
3. **PreToolUse / draft-gate (enforce).** The live KP9 draft-gate (`draft_gate.py`) already lints jargon + checks constraints. This design **parameterizes its threshold by the cell**: in an area whose `technical-exposure` is `deep`, the jargon/register gate runs *loose* (the user wants the detail); in a `minimal` area it runs *strict*. The gate's register-judge (the §4.4-research four-axis rubric) scores the draft against **the cell's value**, not a global setting. This is the exact seam where the model stops being advisory and becomes structural enforcement.

### 4b. Why deterministic-lookup and not "the model decides each time"

The owner requires it ("deterministic + structured... a matrix of how its behaviors should steer"), and the abstraction-voice research proves *why it must be structural*: instruction influence decays within ~8 rounds (`keep-pace-research-abstraction-voice.md` §1.1), and **self-correction fails for register** (§1.3) — so "the model decides how technical to be each turn" is the failure mode, not the design. The matrix is the *external* state the hook injects and the gate enforces; the model never has to *remember* the user's preference because the hook re-states it from the file every turn. Determinism lives in the lookup-and-inject mechanism; adaptivity lives in the file contents.

### 4c. Graceful degradation

If the file is missing/unreadable, every lookup returns the openness-biased prior (the `default` row) and the system behaves exactly as the un-personalized keep-pace chain does today — fail-open, no regression. The model is a *refinement* of a working read-path, never a dependency that can break it.

---

## 5. User transparency + override (the safety valve against condescension)

The owner's locked principle 2: the model is transparent + user-overridable; this is the guard against the core risk (mislabeling someone non-technical and quietly condescending).

- **Inspect in plain language.** The user can ask "how are you treating me / what have you decided about how I like things / why are you explaining this" and the persona renders the matrix **in prose, never as the raw file** (the abstraction-voice rule applies to the model describing *itself* — `keep-pace-research-abstraction-voice.md` §4 fix 2: "the system explaining itself is the highest-risk leak surface"). Example: *"On the loam-mechanics side I've been going fairly technical with you because you keep asking how things work; on the writing side I keep it about the craft, not the machinery. Want me to change either?"*
- **Correct it.** Any explicit statement ("stop explaining the mechanics", "I do want the code on builds") is a **hard-set** (§2.a/§5): it sets the cell to the stated value at `high` confidence and **locks** it — behavioral evidence cannot silently override a stated preference; it can only *prompt a re-ask* ("you said skip the details here, but you've asked how-does-that-work three times — want me to open it back up?"). The user always out-votes the model.
- **Visible reasoning at point of exposure.** When the persona surfaces something technical it could have hidden, it pairs it with the *why* and the *off-switch*: "showing you this because you've wanted the detail here before — tell me to dial it back." This is the owner's locked principle 2 verbatim and the single best mitigation for the mislabel risk (§7).
- **The model never narrates its own mechanism.** It never says "I've raised your technical-exposure cell to deep" — that's a mechanism-leak (the cure becoming the disease, `keep-pace-research-abstraction-voice.md` §6.5). It says "I'll keep going technical here."

---

## 6. Composition map (this is the SPINE — get this right)

| Existing thing | How this model parameterizes / feeds it (one line each) |
|---|---|
| **FBM / S2 corpus (the store)** | The matrix lives at `~/.claude/INTERACTION-MODEL.md`, OBJECTIVES.md-shaped, in M2's audited-surface set; counters/evidence write via the FBM write path; no new store. |
| **The re-eval loop** | Reuses the capability-adoption-loop pattern (weekly floor + event triggers + fresh-evaluator judge + auto-apply-vs-owner-gate) — `claude-capability-adoption-loop-design.md` — not a new loop. |
| **Non-tech recovery (#31 / distress signal)** | A **consumer**: the distress signal (`feedback_user_distress_is_priority_diagnostic_signal.md`) is the §2.4 fast-down trigger; the recovery design reads the matrix to pitch its plain-language recovery at the user's current exposure level. |
| **Capability auto-adoption** | A **consumer**: competence-adaptive auto-adoption reads `harness-mechanics` exposure + autonomy to decide whether to auto-apply a primitive silently or surface it as a teachable moment. |
| **`abstraction_first_default.md`** | Becomes a **lookup**: instead of a fixed `minimal` default, the rule's exposure level is `technical-exposure` for the active area (default now `open`, dialable down on evidence). §6.1. |
| **`translate_outbound_too.md`** | Becomes a **lookup**: the outbound register/voice register is `tone` for the active area; the "no SHAs/IDs/jargon" floor stays unconditional (syntactic leak is never wanted), but the *depth* of what's translated tracks the cell. |
| **`coworker_relationship_framing.md`** | Becomes a **lookup**: the CEO/CTO peer-warmth, push-back-harder, want-expression register is the `tone` axis default (`peer-warm`); a user who mirrors terse-execution shifts `tone` toward `terse-execution` per-area without losing the mutual-F2 contract. |

### 6.1 — Why this is a correct evolution of `abstraction_first_default.md`, not a contradiction (F2)

`abstraction_first_default.md` defaults to **full-hide** (`minimal`); this model defaults to **open-with-education** (`open`). That looks like a reversal of a Luke-tuned rule — so it needs justifying, not hand-waving. The justification (and it's the owner's own stated intent):

1. **The old rule was over-tight at the wrong default.** `abstraction_first_default.md` itself notes it "was Luke-tuned" and the brief states it's "too aggressive even for Luke, who wants high exposure in loam-infra." A fixed `minimal` default *cannot represent* "abstract on writing, technical on infra" — it's a global flag where the owner's vision is explicitly per-area (the §1b taxonomy). The old rule isn't wrong; it's **a single cell value frozen as a global default.**
2. **The model preserves what the old rule got right and makes it adaptive.** The old rule's real content — "the user shouldn't have to *hold* file names / mechanism / IDs" — survives **unconditionally as the syntactic-leak floor** (§6 row 2: SHAs/paths/IDs never reach prose regardless of cell). What becomes adaptive is the *semantic depth*: whether to explain the *outcome* or the *mechanism*. The old rule conflated "don't leak internals" (always right) with "don't go deep" (area-dependent); this model separates them.
3. **The evidence the old rule was tuned on is preserved as a cell, not discarded.** If Luke's behavior shows he wants `minimal` on some area, that area's cell *becomes* `minimal` — the old default is reachable, just no longer mandatory everywhere. This honors `feedback_locked_design_not_license_for_bad_outcomes.md`: the locked rule is revisitable because its fixed-global shape produced a bad outcome (jargon-firehose *and* over-hiding, depending on area), and the fix names the bad outcome and offers the per-area alternative.

**The owner should ratify this specific evolution** (§8) — it edits the meaning of a memory rule, and per `feedback_record_owner_ratification_before_dispatch.md` that edit is recorded before any build.

---

## 7. F2 risk section (the owner's vision, engaged critically)

| Risk | The failure, concretely | Mitigation (built-in, not advisory) |
|---|---|---|
| **Mislabeling (the core risk)** | The model decides someone is non-technical and quietly condescends — or decides they're an "engaged learner" and firehoses education at someone who's drowning. | (a) **Openness-biased prior** means the default failure is "too much" not "too little" — and the §2.4 **fast-down on distress** makes "too much" instantly correctable on one signal. (b) **Visible reasoning + off-switch** (§5) surfaces every exposure choice with its why. (c) **User statement hard-overrides** behavior (§5). The mislabel can't be *silent* — that's the property that defangs it. |
| **The owner's "assume engaged whether or not it's true"** | A genuinely-overwhelmed user gets treated as a learner who wants depth, at the worst moment. This is condescension-in-reverse and it directly collides with the #1 distress fire-alarm. | **§2.4 asymmetric rule** — distress dials exposure *down fast, single-signal, no debounce*; the climb up is slow. Openness is the prior; the floor is one overwhelm signal away. This is *the* guard and it's structural. |
| **Privacy / consent** | The system builds a behavioral profile of the user without their awareness. | The profile is (a) **local-only** (`~/.claude/`, single-user, same trust boundary as MEMORY.md/OBJECTIVES.md), (b) **fully inspectable in plain language on demand** (§5), (c) **stores dated pointers, not transcripts** (§1a — no quote hoarding), (d) coarse 6-area × 4-axis enums, not a fine-grained psychological model. Consent is the inspect-and-correct surface; nothing is hidden from the user about themselves. |
| **Condescension** | Even correctly-labeled, "let me explain that for you" can patronize a peer. | `tone` defaults to `peer-warm` (the coworker-relationship register), never `formal`/teacherly; `learning-appetite: invite` *offers* the explanation, doesn't *impose* it; the off-switch is always one phrase away. |
| **Over-personalization / filter-bubble** | The model narrows the user into a profile and stops offering things outside it — the user never grows because the system stopped challenging them. | (a) The openness-bias is *anti*-bubble by construction — it keeps offering depth rather than narrowing. (b) The §3c **drift check + fresh-evaluator judge** explicitly looks for over-narrowing. (c) **Confidence decay** (§2b): a cell that hasn't seen corroborating evidence in a long time *loses* confidence and drifts back toward the open prior — the model forgets a stale narrow label rather than calcifying it. |
| **Determinism vs adaptivity** | A "deterministic matrix" that changes every turn isn't deterministic; an immutable one isn't adaptive. | The owner's own resolution, made mechanical: **structure is deterministic + auditable** (fixed schema, fixed lookup, fixed enums), **content is adaptive** (cell values move from evidence). The persona's *behavior given a cell* is deterministic; *which cell* updates on the §2 cadence. Hysteresis (§2b) keeps it from thrashing turn-to-turn. |
| **The classifier mis-routes the area** | The §4a work-anchor→area map sends a turn to the wrong row, applying the wrong cell. | Fail-open to `default` (openness prior) on low-confidence classification; the area map is coarse (6 buckets) so mis-routes are rare and low-harm; a mis-route surfaces as a normal exposure-mismatch the user can correct in-line (§5), feeding evidence that re-tunes. |
| **Simpler equivalent exists?** | Could a single global "technical level" slider do this? | **No** — `keep-pace-research-abstraction-voice.md` §5 already rejected the global flag: it "can't represent 'abstract about the writing pipeline, technical about loam-dev.'" The per-area matrix is the minimum shape that satisfies the owner's explicit "technical in some areas, non-technical in others." But the *axes* could plausibly start at **two** (exposure + autonomy) and add tone/learning-appetite later — see §8 MVP. |

**One thing flagged, not assumed (Lens 7):** the owner frames this as "possibly loam's core differentiator." It might be — but the evidence-driven cells are only as good as the signal-classification, and **signal-classification accuracy is unverified** (does "just tell me if it worked" reliably parse as a down-signal vs a neutral status request?). The whole adaptive layer rests on that classifier the way the keep-pace architecture rests on the objective-model (`keep-pace-with-user.md` §2 "the architecture's own fragility"). **Mitigation, same shape as keep-pace's `w_s`-capped-low:** ship with the matrix **mostly reading the openness prior** and the cells moving *slowly* (high hysteresis) until the signal-classifier is calibrated on real traffic and trusted; let the *explicit-statement* path (§5, high-confidence, no classifier needed) carry most of the early personalization. Adapt aggressively only once the behavioral classifier is proven.

---

## 8. Phased build plan (owner-gated — nothing below is built here)

Every item names the Claude primitive (Lens 1) and rides already-live seams. **The whole comprehensive system is deliberately NOT the first slice** — per Lens 4 the high-confidence part is the structure + the explicit-statement path; the low-confidence part is the behavioral classifier, which ships last and calibrated.

### MVP — the smallest slice that delivers per-area adaptivity (ships the outcome)

| # | Item | Primitive | Why first | Owner-gate |
|---|---|---|---|---|
| **AIM-0** | Create `~/.claude/INTERACTION-MODEL.md` seeded with the §1b taxonomy, all cells at the openness prior. | file (OBJECTIVES.md-shaped) | The state every later piece reads; 15–30 min; zero behavior change until read. | Ratify the **taxonomy + the openness-default revision of `abstraction_first_default.md`** (§6.1) before seeding. |
| **AIM-1** | **Read path:** add the work-anchor→area classifier + cell-lookup-and-inject step to the **live** keep-pace UserPromptSubmit hook. | UserPromptSubmit (live) | This is what makes behavior per-area; rides the already-wired hook (Tier-0). The two-axis subset (exposure + autonomy) is enough for v1. | Hook edit = behavior change → owner-gated per the adoption-loop §3b rule. |
| **AIM-2** | **Enforce path:** parameterize the live KP9 draft-gate threshold by the area's `technical-exposure` cell. | PreToolUse / `draft_gate.py` (live) | Turns the model from advisory to structural at the one seam that already gates outbound. | Hook edit → owner-gated. |
| **AIM-3** | **Explicit-statement path:** "always show me X / stop explaining Y" → hard-set + lock the named cell; plain-language inspect ("how are you treating me"). | persona behavior + file write | High-confidence, no classifier needed (§7 flag) — carries early personalization while the behavioral path is uncalibrated. | None beyond AIM-0 (it's the user's own statement). |

**MVP delivers:** per-area exposure + autonomy that the user can directly set and inspect, enforced structurally at the live draft-gate, defaulting open. It does **not** yet auto-learn from behavior — that's deliberately deferred until the classifier is calibrated.

### Backlog — ships on observed need / after calibration

| # | Item | Gate to start |
|---|---|---|
| **AIM-4** | Behavioral signal counters + hysteresis update (§2) — the auto-learn path; dark-launch (log signals, don't move cells) for a week, then calibrate thresholds. | AIM-1 live + a week of logged signals (same dark-launch discipline as keep-pace KP2). |
| **AIM-5** | The §2.4 fast-down-on-distress trigger wired to the distress-signal detector (the #31 consumer seam). | The distress-signal detector exists / AIM-4 signal-classification trusted. |
| **AIM-6** | Add the `tone` + `learning-appetite` axes (MVP runs on exposure + autonomy). | AIM-1–4 observed working on two axes. |
| **AIM-7** | The weekly re-eval consolidation pass + fresh-evaluator drift judge (§3) — reuses the adoption-loop + FBM-T3.1 consolidation seam. | FBM consolidation (C1) landed; AIM-4 counters accruing. |
| **AIM-8** | Capability-auto-adoption + non-tech-recovery wired as consumers (§6). | The consumers themselves built; the model live. |

**Dependency on FBM (#20):** AIM-0/1/2/3 (the MVP) depend only on the **already-live** keep-pace hooks + a markdown file in `~/.claude/` — **not** on the unbuilt FBM consolidation tier. AIM-7 (the weekly consolidation pass) is the one piece that genuinely needs FBM-T3.1's `claude -p` consolidation seam (`fbm-state-and-memory-roadmap-2026-05-29.md` C1) — so the auto-learn-and-consolidate top of the system is FBM-gated, but the per-area-adaptive *outcome* is not. This is the Lens-4 cut: ship the high-confidence structure now (no FBM dependency), defer the low-confidence learning top until both the classifier is calibrated and FBM consolidation lands.

### The single first thing to build

**AIM-0 + AIM-1 + AIM-3 as one MVP slice** — the file, the read-path on the live hook (exposure + autonomy only), and the explicit-statement override. That delivers user-controllable per-area adaptivity defaulting-open, enforced at the live gate, with zero dependence on the unbuilt learning machinery or FBM consolidation. AIM-1 is load-bearing (it's where per-area behavior actually happens); AIM-3 carries personalization safely while the behavioral classifier (AIM-4) is still dark-launched.

---

## 9. Lens coverage

- **Lens 1:** every mechanism rides a live Claude-native primitive — the wired UserPromptSubmit + PreToolUse hooks, `claude -p` (consolidation/judge) via `claude_print_synthesis_client.py`, FBM markdown store, the OBJECTIVES.md file pattern. No new engine; the read-path is an *addition* to an already-firing hook.
- **Lens 2:** the model is the mechanism that makes the translation layer *per-user* — it directly reduces translation burden (the persona pitches every area at the user's demonstrated level) and adds to the toolkit (a deterministic preference-lookup the persona invokes every turn). It is the personalization of `VALUE_PROPOSITION.md`'s core function.
- **Lens 3:** the schema + read-path state observable outcomes (a cell value injected; a gate threshold set; a cell moved on a counter-cross); method (the classifier impl, the exact thresholds) is the builder's call, calibrated at build time.
- **Lens 4:** structure tight (high-confidence — schema, lookup, openness-default, asymmetric-safety rule); content loose (low-confidence — signal-classification, thresholds → dark-launch + calibrate, never imported). The MVP cut puts the high-confidence structure first and defers the low-confidence learning top.
- **Lens 5:** decomposed into AIM-0..8, MVP/backlog partitioned, each with a tighter AC than "adaptive interaction model"; the §3c fresh-evaluator judge IS the CycleVerdict applied to cell changes; the drift check is the `needs_fresh_start` signal applied to over-narrowed profiles.
- **Lens 6:** the determinism-vs-adaptivity conflict and the openness-vs-distress-safety conflict are named with signals (reversibility — exposure cheap to undo vs an action not; blast radius — firehose at a lost user) and resolved by the asymmetric rule (§2.4) + structure/content split, with the `abstraction_first` evolution explicitly surfaced for owner ratification (§6.1, §8) rather than silently applied.
- **Lens 7:** the owner's "assume engaged whether true or not" is engaged critically (§0 headline, §7) with its concrete failure named + the asymmetric guard; the `abstraction_first` default-reversal is justified, not hand-waved (§6.1); the unverified signal-classifier is flagged with the keep-pace `w_s`-capped-low mitigation (§7 final); the wrong-but-obvious component taxonomy (the 18 runtime components) is named and rejected (§1b).
```
