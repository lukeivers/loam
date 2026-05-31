# keep-pace — The Abstraction Voice as a Structural Discipline

**Date:** 2026-05-28
**Status:** research (external + foundation read; design recommendations for the keep-pace work-stream)
**Owner:** Luke Ivers
**Dimension:** ABSTRACTION / TRANSLATION-LAYER VOICE — how to make the persona default to plain-language abstraction over technical internals, and go deep only on request or demonstrated per-topic preference, as a STRUCTURAL discipline rather than an advisory reminder that keeps getting ignored.
**Composes with:** `memory-architecture.md` (surfacing/load-boundary), Lens 2 (`VALUE_PROPOSITION.md` — the persona IS a translation layer), the existing structural-enforcement hook cluster.

---

## 0. The spine in five sentences

The abstraction voice is **load-bearing for loam's entire pitch** — the product promise is "an abstraction over hard concepts for a non-technical user," and a persona that leaks file names, mechanism names, SHAs, and implementation detail has *broken the core value proposition*, not committed a style nit (`VALUE_PROPOSITION.md`: "If the user is thinking about tokens, the translation layer has failed" — the same logic extends to every internal the user shouldn't have to hold). The reason "talk in abstractions" keeps getting ignored despite living in CLAUDE.md is **not** persona laziness or a missing reminder — it is a *measured, mechanistic* failure: instruction influence decays over a conversation (transformer attention decay + lost-in-the-middle), and the model's base training distribution (dense, technical, internet-shaped prose) reasserts itself as the system-prompt's relative weight drops (Li et al. COLM 2024 measured significant drift within **8 dialog rounds**; the CEFR-tutoring study measured **20–30% register drift by turn 10–15** even with the instruction explicitly present). Because the failure is architectural, the fix must be architectural: a **two-layer enforcement gate between draft and send** — a cheap deterministic lint for the syntactic jargon classes (already proven in loam's `translation_jargon_check.py`) plus an LLM-as-judge **register gate** for the semantic leak the regex can't catch (mechanism-leak, over-technical framing, unrequested depth) — fed by a **per-topic depth-preference file** that records where the user has demonstrably wanted depth, and refreshed by a **UserPromptSubmit re-injection** that pulls the attention weights back to center every turn. The single highest-leverage insight: **self-correction does not work for register** (the CEFR study found models "lack reliable self-assessment for linguistic register"), so the gate must be an *independent* check on the drafted output, never "remember to talk simply" added to the persona's own prompt.

---

## 1. Why advisory reminders fail — the mechanism, from primary sources

This is the load-bearing finding for the whole dimension. The failure is **not** a willpower or attention problem the persona can fix by trying harder; it is a measured property of how transformer dialog systems behave. Three independent sources converge:

### 1.1 Instruction influence decays measurably over a conversation

**Li, Liu, Bashkansky, Bau, Viégas, Pfister, Wattenberg — "Measuring and Controlling Instruction (In)Stability in Language Model Dialogs," COLM 2024 ([arxiv 2402.10962](https://arxiv.org/abs/2402.10962)).** The paper builds a self-chat benchmark and measures how fast a system-prompt instruction (persona, style, constraint) decays. The headline result: **significant instruction drift within eight rounds** of conversation on LLaMA2-chat-70B and GPT-3.5. The proposed mechanism is **attention decay over long exchanges** — formalized with a geometric "cone"-based theory of why early-context instructions lose relative weight as the dialog grows. Their fix, **split-softmax**, is a *model-internal* intervention (it re-weights the attention distribution) — **not available to a harness sitting on top of a closed model.** This is the key boundary: the research-grade fix is at a layer loam cannot touch, so loam must approximate it at the harness layer (re-injection, §4.3).

### 1.2 The drift direction is toward MORE complexity (the abstraction-voice failure exactly)

**"Alignment Drift in CEFR-prompted LLMs for Interactive Spanish Tutoring" ([arxiv 2505.08351](https://arxiv.org/pdf/2505.08351)).** This is the closest analog to loam's exact problem: a model instructed to hold a *simple* language register (CEFR A1 for a beginner) for an audience that needs simplicity. Findings:
- The model **progressively drifts toward higher complexity** over turns despite the instruction staying present — **20–30% drift from the target proficiency level by turn 10–15.**
- The named mechanism is **competing optimization objectives**: the model was trained on dense, complex internet prose, and "the model's base training patterns gradually reassert themselves as the system prompt's influence weakens relative to in-context patterns." The simple-register instruction is a thin layer over a distribution that defaults to complexity.
- **Direction matters:** the drift is *always toward the technical/complex pole*, never toward over-simplification. For loam this means the failure is structurally one-sided — the persona drifts into jargon, it does not drift into baby-talk — so the gate only has to defend one direction.

### 1.3 What the two papers found about FIXES (this is the design input)

The CEFR study tested the obvious interventions and is blunt about what works:

| Intervention | Result (CEFR study) | Implication for loam |
|---|---|---|
| **System-prompt re-injection** (periodically re-state the instruction mid-conversation) | **Partially effective** — modest improvement, did not eliminate drift | Worth doing (cheap), but NOT sufficient alone. → loam's UserPromptSubmit re-inject (§4.3) |
| **Output filtering** (post-generation check for compliance) | Caught **egregious violations** but **degraded response quality** when it forced rewrites bluntly | A filter is the right shape but must be *surgical* (flag + targeted rewrite), not a blunt regenerate. → loam's two-layer gate (§4.1–4.2) |
| **Self-correction prompting** ("verify your output is at level") | **Minimal impact** — "models lack reliable self-assessment for linguistic register" | **The most important negative result.** The check must be INDEPENDENT of the generating context, never self-review. → the gate is a separate pass / separate agent (§4.2) |

**The synthesis:** advisory reminders fail because they are the weakest of the three (a static instruction subject to decay); re-injection helps a little; the thing that actually catches the leak is an *independent post-generation gate* — but it must be surgical, not blunt, or it trades jargon-leak for quality-loss. This is precisely the shape loam already proved with `translation_jargon_check.py`.

### 1.4 Anthropic's own confirmation: memory rules are context, not enforcement

From the L5 foundation research (`l5-context-memory-deep-3.md`) and Anthropic's docs ([code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)): *"Claude treats them as context, not enforced configuration. To block an action regardless of what Claude decides, use a PreToolUse hook instead."* And: *"Files over 200 lines consume more context and may reduce adherence."* loam's CLAUDE.md corpus is far over 200 lines, so the abstraction-voice rule is buried in a diluted, decaying instruction surface — *exactly* the condition §1.1–1.2 predicts will drift. **An abstraction-voice rule in CLAUDE.md is the architecturally weakest possible enforcement.** This is why tonight's failure happened and why a better-worded reminder won't fix it.

---

## 2. Why this matters for a non-tech user (Lens 2)

`VALUE_PROPOSITION.md` makes the abstraction voice a **prime-objective AC**, not a polish item:
- The persona's *basic function* is to translate between the user's natural-language intent and AI-effective execution. A reply carrying `translation_jargon_check.py`, `AC.NTU.1`, `feedback_*.md`, a 7-char SHA, or "the UserPromptSubmit re-injector" has **handed the translation burden back to the user** — the exact failure the document defines.
- "Just because the assistant can remember [the file name / mechanism] doesn't mean the user can." Token-management is named in VALUE_PROPOSITION as something the user is *entitled to ignore*; mechanism-detail is the same class. The user should never have to **push** for abstraction — full abstraction is the default operating mode, and going technical is the *opt-in*, not the default.
- Trust (the P2 property in `memory-architecture.md`) compounds in one consistent voice. A voice that randomly drops into engineer-mode breaks the "one entity the user knows and trusts" property — it feels like a different, less competent assistant each time it leaks.

So the abstraction voice is not a tone preference; it is the surface where the product either delivers or fails its core promise on every single turn.

---

## 3. The two halves of the problem: SYNTACTIC leak vs SEMANTIC leak

The dimension splits cleanly, and the split dictates the mechanism for each half.

**Syntactic leak — deterministically detectable.** File names (`*.py`, `*.md`), SHAs, AC-IDs, §-pointers, Greek-letter labels, agent-IDs, raw path strings, un-introduced ALLCAPS abbreviations. These have a *regular form* — a regex catches them with near-zero false-negatives. loam already enforces a subset (`translation_jargon_check.py`: Greek letters, SHAs, AC-IDs, §-pointers). This half is **solved-pattern, extend-coverage**.

**Semantic leak — NOT deterministically detectable.** "Talking too technically" with no banned token present: explaining the *mechanism* when the user asked for the *outcome*; unrequested implementation depth; framing a decision in engineering terms; assuming the user holds prior technical context. There is no regex for "this paragraph is pitched at an engineer." This half needs a **judge** — an LLM-as-judge register gate (§4.2). This is the genuinely hard, genuinely novel part of the dimension; the syntactic half is a known quantity.

The L6 verification research already establishes LLM-as-judge as a loam-validated pattern, and the literature backs the accuracy: rubric-guided LLM judges reach **80–90% agreement with human evaluators** on style/tone dimensions ([LLM-as-a-Judge practical guides](https://towardsdatascience.com/llm-as-a-judge-a-practical-guide/); [LLM-Rubric, arxiv 2501.00274](https://arxiv.org/html/2501.00274v1)) — comparable to inter-human agreement. A register-appropriateness judge is squarely inside the validated envelope.

---

## 4. The recommended structural design (buildable on a Claude Code harness)

Four composable mechanisms. Each names the Claude primitive it leans on (Lens 1) and degrades gracefully if a later layer isn't built. **All are file-based + Claude-native; none requires the Anthropic API** (`feedback_no_anthropic_api_key` — the judge runs via `claude -p`, default Sonnet).

### 4.1 Layer 1 — extend the deterministic jargon lint (syntactic half) — HIGH, cheap, proven

The existing `translation_jargon_check.py` PreToolUse hook on `mcp__plugin_telegram_telegram__reply` is the exact pattern. **Extend its pattern set** to cover the rest of the syntactic class:
- File-name leak: `\b[\w\-]+\.(py|md|json|yaml|toml|sh|ts|js)\b` in user-facing prose.
- Raw absolute-path leak: `/Users/...`, `~/.claude/...`, `framework/...`.
- Agent-ID / task-ID leak; un-introduced ALLCAPS internal abbreviations (allow a whitelist the user has been taught).

**Primitive:** PreToolUse hook (client-enforced, blocks regardless of what the model decides — the Anthropic-documented hard-enforcement layer). **Why it sticks:** it is *structural* — fires between draft and send every time, immune to the attention-decay that kills the CLAUDE.md rule. **Cost:** trivial — it is a pattern-set addition to an existing tested hook. **Limit:** catches only the regular-form classes; the semantic leak passes straight through, which is why Layer 2 exists.

### 4.2 Layer 2 — an LLM-as-judge REGISTER GATE (semantic half) — HIGH leverage, the novel piece

A second PreToolUse stage (or an inline pre-send check) that sends the drafted reply to an **independent `claude -p` judge** with a tight register rubric, and flags (does not silently rewrite) when the draft pitches above the user's depth setting for the active topic.

**Why independent and not self-review:** §1.3 — the CEFR study's clearest negative result is that self-correction fails for register; the model can't reliably self-assess its own linguistic level. The judge MUST see only the draft + the topic's depth setting, NOT the generating conversation (the same fresh-eyes property `memory-architecture.md` §3.1 demands for the independent judge — and the same reason it gets no persistent memory).

**The rubric (named-axis, per Lens 5 `EVAL_DIMENSIONS`):** score the draft on orthogonal axes rather than one yes/no —
1. *Mechanism-leak:* does it name an internal mechanism/file/tool the user didn't ask about?
2. *Unrequested depth:* does it explain HOW when the user asked WHAT/WHETHER?
3. *Assumed-context:* does it lean on prior technical detail the user would have to hold in their head?
4. *Register:* is the vocabulary/syntax pitched at an engineer vs. the user's demonstrated level?

A draft failing any axis (above the topic's allowed depth) is returned to the persona with the specific axis + offending span, for a **surgical rewrite of that span** — not a blunt full regenerate (§1.3: blunt rewrites degrade quality). The judge's PASS/FLAG verdict + per-axis reasoning makes it interpretable and tunable.

**Primitive:** `claude -p` subprocess via the existing `claude_print_client.py` wrapper (default Sonnet — token-efficient; the gate is short). Fail-OPEN on judge error/timeout (a broken judge must not block the user's reply — availability beats perfection here; the syntactic Layer-1 still fires). **Cost:** one extra short `claude -p` call per outbound reply — measurable token cost, so make it *conditional* (§4.4): skip the judge entirely on topics the user has set to "technical," run it on default/abstraction topics.

**F2 / open fork:** a judge on *every* outbound reply adds latency + token cost to the most latency-sensitive surface (the live Telegram reply). Reasonable people could prefer: (a) judge every reply (max protection, max cost), (b) judge only replies above N words / containing borderline-technical signals (cheaper, small miss-rate), or (c) judge async-after-send and *learn* (log the leak, tune the depth-model, don't block) — which trades same-turn enforcement for zero added latency. **Recommendation: start with (b)** — gate only replies a cheap pre-filter flags as plausibly-technical (e.g. contains domain nouns, exceeds a length threshold, or follows a technical-topic turn), fail-open, log every catch to tune the threshold. This is the latency/protection balance; surfacing because it's a genuine cost-vs-coverage call the owner should weigh.

### 4.3 Layer 3 — UserPromptSubmit re-injection (the attention-pull) — MEDIUM, the decay countermeasure

The harness-layer approximation of split-softmax (§1.1, which loam can't do model-internally). A **UserPromptSubmit hook** re-injects a *terse, clean, no-disclaimer* abstraction-voice directive every turn, so the instruction's relative attention weight is pulled back to center instead of decaying over the conversation.

**Why UserPromptSubmit and not SessionStart:** re-injection has to happen *every turn* to counter per-turn decay (§1.1 — drift within 8 rounds means a once-per-session injection is gone by mid-conversation). loam already injects reliably at UserPromptSubmit (`queue_status_inject.py`, `principle_reminder.py`) — this is the same proven channel. The injected text must be **clean system-reminder framing, no "may or may not be relevant" disclaimer** (the dev.to source in `l5-context-memory-deep-3.md` names the disclaimer-wrapper as itself a cause of ignored instructions).

**Primitive:** UserPromptSubmit hook (loam-proven channel). **Why it's only MEDIUM not HIGH:** the CEFR study rates re-injection "partially effective" — it reduces drift, doesn't eliminate it. It is the *cheap continuous nudge* that lowers how often Layers 1–2 have to fire, not a standalone fix. Compose, don't substitute.

### 4.4 Layer 4 — the per-topic DEPTH-PREFERENCE model (the "go deep only where demonstrated" half) — MEDIUM, the personalization piece

A file-based preference model (PONTE-style, §ref) recording, per topic/domain, the user's demonstrated depth preference: **abstraction-default | technical-on-request | technical-default**. This is what lets the persona "selectively go deep only on user-request or demonstrated per-topic preference" without the user having to re-ask every time.

**Shape (file-based, Claude-native, ties into `memory-architecture.md`):**
- A `depth-preferences.md` (or a section in the S2 FBM corpus / a structured store) — one line per topic: `topic-slug → depth-setting → evidence (the turns where the user asked for / welcomed depth)`.
- **Learned from behavioral signal, not explicit config** (PONTE's key move, [arxiv 2603.06485](https://arxiv.org/pdf/2603.06485)): when the user asks "how does that work?" / "show me the code" / engages with a technical answer rather than bouncing off it → that topic's depth setting rises. When the user says "just tell me if it worked" / "I don't need the details" → it falls (or stays at abstraction-default). The persona proposes the update; it lands durably in the file (the standard loam capture pattern).
- The depth setting **feeds both Layer 2 and Layer 3**: it is the threshold the register-judge scores against, and the value the re-injection states ("topic X: technical OK; default: abstraction").

**This is the direct answer to Luke's vision item 8** ("go technical ONLY when asked or on topics where the user has demonstrably + consistently wanted depth") — the "demonstrably + consistently" is exactly a behavioral preference model, and "consistently" means the setting changes only on *repeated* signal, not a single turn (debounce against one-off technical questions flipping a topic permanently technical).

**PONTE architecture loam adapts (3 components):** (1) a **low-dimensional preference model** (here: the per-topic depth setting — coarse-grained, 3 levels, not a learned vector; loam doesn't need the continuous latent space, the discrete setting is enough and stays human-auditable, which P2-trust requires); (2) a **preference-conditioned generator** (the persona, conditioned via the Layer-3 re-injection); (3) a **closed-loop validate-and-adapt** (Layer 2 is the validate; the preference-file update is the adapt). loam's adaptation is the *coarse, auditable* version — deliberately, because a non-tech user must be able to see and correct "you've decided I want technical detail about X" in plain language, which a latent vector can't offer.

**Primitive:** markdown file in the FBM corpus + the existing capture discipline (no new engine). **Why MEDIUM:** it's the longest-horizon piece and only pays off once it has accumulated signal; Layers 1–3 deliver value on day one without it. But it is the piece that makes the discipline *adaptive* rather than uniformly-flat, and it is what keeps the voice tied to the user's *current* scope of work (Luke's vision item 7, keep-pace) — a topic the user has moved on from drifts back to abstraction-default.

### 4.5 How the four layers compose (the keep-pace abstraction-voice loop)

```
user prompt
  → UserPromptSubmit hook re-injects abstraction-voice directive
      keyed to the active topic's depth setting        (Layer 3 + Layer 4 read)
  → persona drafts reply
  → PreToolUse Layer 1: deterministic jargon lint        (syntactic — block on hit)
  → PreToolUse Layer 2: register judge (conditional)      (semantic — flag + surgical rewrite)
  → reply sent
  → behavioral signal observed (did user ask for depth? bounce off it?)
      → depth-preference file update proposed + captured  (Layer 4 adapt)
```

Layers 1 + 3 are cheap and always-on. Layer 2 is conditional (cost-gated by Layer 4's setting). Layer 4 is the slow learner that tunes the whole loop to the user's current scope. Remove any one layer and the rest still function — graceful degradation by design.

---

## 5. Why each rejected approach is wrong (F2 — name the alternative AND why not)

- **"Just write a stronger CLAUDE.md rule."** Rejected: §1.1–1.4 — instruction influence decays measurably (drift within 8 rounds), CLAUDE.md is the weakest enforcement surface (context-not-config, >200-line dilution), and this is precisely what failed tonight. A better-worded reminder is the same architecture that's already failing.
- **"Have the persona self-check before sending."** Rejected: §1.3 — the CEFR study's clearest negative result is that self-correction fails for register; models can't reliably self-assess linguistic level. The check must be *independent* of the generating context.
- **"Blanket post-filter that rewrites every reply to be simpler."** Rejected: §1.3 — output filtering "degraded response quality" when applied bluntly. The gate must be surgical (flag specific span + targeted rewrite), and conditional on the topic's depth setting, or it flattens replies the user *wanted* technical.
- **"Fine-tune / model-internal fix (split-softmax)."** Rejected: §1.1 — that's a model-layer intervention; loam sits on a closed model via subscription `claude -p` and cannot touch attention weights. Re-injection (Layer 3) is the harness-layer approximation.
- **"One global depth setting for the user."** Rejected: Luke's vision item 8 is explicitly *per-topic* ("topics where the user has demonstrably wanted depth"). A global flag can't represent "abstract about the writing pipeline, technical about loam-dev." The preference must be per-topic (Layer 4).

---

## 6. Risks

1. **Layer-2 latency/cost on the live reply surface.** A judge call per outbound reply adds latency + tokens to the most latency-sensitive surface. Mitigation: conditional gating (§4.2 fork, recommendation (b)), fail-open, cheap pre-filter. Residual: a small miss-rate on borderline replies that the pre-filter doesn't flag. Acceptable vs. the alternative (jargon-leak on every turn).
2. **False-positive over-blocking flattens legitimately-technical replies.** If Layer 1's pattern set is too broad or Layer 2's threshold too low, replies the user *wanted* technical get blocked/flattened — the opposite failure, and arguably worse for trust (the persona feels lobotomized). Mitigation: Layer 4's per-topic setting raises the threshold where the user has demonstrated preference; the syntactic lint stays narrow (file-names/SHAs are *never* wanted in prose; the semantic judge respects the depth setting).
3. **Depth-preference model mis-learns from a one-off question.** A single "how does that work?" should not flip a topic permanently to technical-default. Mitigation: debounce — require *consistent repeated* signal (Luke's vision item 8 says "demonstrably + consistently") before raising a topic's setting; single technical questions get a technical *answer* without changing the standing setting.
4. **Judge anchoring / drift if given memory.** If the register-judge accumulates state it could anchor on prior verdicts and lose calibration. Mitigation: the judge is stateless per call (the fresh-eyes property), reads only draft + depth-setting, exactly as `memory-architecture.md` §3.1 mandates for the independent judge.
5. **The gate itself becomes an internal the user sees.** If a block/flag message ever surfaces to the user ("your reply was blocked by the register judge"), that is itself a mechanism-leak — the cure becomes the disease. Mitigation: gate feedback is model-facing only (stderr/hook-reason → persona), never user-facing; the user only ever sees the clean rewritten reply.

---

## 7. Lens coverage

- **Lens 1 (Claude-leverage):** every layer is a Claude-native primitive — PreToolUse hooks (Layers 1–2), `claude -p` judge (Layer 2), UserPromptSubmit injection (Layer 3), FBM markdown corpus (Layer 4). No new engine; extends the proven `translation_jargon_check.py` pattern.
- **Lens 2 (translation-layer value):** the abstraction voice IS the prime-objective AC (`VALUE_PROPOSITION.md`) — this dimension is the surface where loam delivers or fails its core promise every turn. Every layer reduces the user's burden of holding internals.
- **Lens 3 (ODD):** recommendations state observable outcomes (no syntactic jargon reaches the user; register judged against the topic depth-setting; instruction re-injected per turn; depth-setting learned from behavioral signal) without prescribing implementation method.
- **Lens 4 (scope↔confidence):** Layer 1 tight (very-high confidence, proven pattern). Layer 2/4 looser (the conditional-gating fork + learned-vs-config carry real design choice → surfaced, not pre-decided). Layer 3 medium (re-injection only "partially effective" per the source — explicitly a nudge, not a fix).
- **Lens 5 (swarming + named-axis judging):** Layer 2's rubric uses `EVAL_DIMENSIONS` (four orthogonal register axes) rather than one yes/no. Any judge dispatch selecting non-default model carries a `model-rationale` line (default is Sonnet here → none needed).
- **Lens 6 (conflict resolution):** the cost-vs-coverage fork (§4.2) and over-block-vs-leak risk (§6.2) are surfaced with signals named (latency, token-cost, trust, miss-rate), not silently resolved.
- **Lens 7 (ruthless feedback):** §5 names each rejected alternative *with its disqualifying evidence*; §6 names risks with mitigations and residuals; the strongest finding (self-correction fails for register) is stated even though it constrains the most obvious "just have it check itself" design.

---

## Sources

- [Li, Liu, Bashkansky, Bau, Viégas, Pfister, Wattenberg — "Measuring and Controlling Instruction (In)Stability in Language Model Dialogs," COLM 2024 (arxiv 2402.10962)](https://arxiv.org/abs/2402.10962) — instruction drift within 8 rounds; attention-decay mechanism + cone theory; split-softmax (model-internal, not harness-available).
- ["Alignment Drift in CEFR-prompted LLMs for Interactive Spanish Tutoring" (arxiv 2505.08351)](https://arxiv.org/pdf/2505.08351) — closest analog; 20–30% register drift by turn 10–15; re-injection partially effective, output filtering degrades quality, self-correction fails; competing-objectives mechanism.
- [Anthropic — memory docs (code.claude.com/docs/en/memory)](https://code.claude.com/docs/en/memory) — "context, not enforced configuration"; >200-line adherence erosion; "use a PreToolUse hook" for hard rules.
- [PONTE: Personalized Orchestration for Natural Language Trustworthy Explanations (arxiv 2603.06485)](https://arxiv.org/pdf/2603.06485) — low-dimensional preference model + preference-conditioned generator + closed-loop validate-and-adapt; preferences learned from behavioral signal, not explicit config; per-topic depth.
- [LLM-Rubric: A Multidimensional, Calibrated Approach to Automated Evaluation (arxiv 2501.00274)](https://arxiv.org/html/2501.00274v1) — multidimensional rubric-guided LLM judging (basis for the named-axis register rubric).
- [LLM-as-a-Judge: A Practical Guide (Towards Data Science)](https://towardsdatascience.com/llm-as-a-judge-a-practical-guide/) — rubric-guided judges reach 80–90% human agreement on style/tone (validates the register gate).
- [Self-Refine: Iterative Refinement with Self-Feedback (arxiv 2303.17651)](https://arxiv.org/pdf/2303.17651) — two-pass generate-then-refine; ~20% absolute improvement; basis for surgical-rewrite-over-blunt-regenerate.
- [dev.to — "Your CLAUDE.md Instructions Are Being Ignored" (via l5-context-memory-deep-3.md)](https://dev.to/albert_nahas_cdc8469a6ae8/your-claudemd-instructions-are-being-ignored-heres-why-and-how-to-fix-it-23p6) — disclaimer-wrapper as itself a cause of ignored instructions; clean re-injection technique.
- Foundation files read: `/Users/lukeivers/loam/docs/design/memory-architecture.md`; `/Users/lukeivers/loam/docs/VALUE_PROPOSITION.md`; `/Users/lukeivers/pos3/workspace/strategy/loam-harness/l5-context-memory-deep-3.md`; loam's live hook `/Users/lukeivers/pos3/.claude/hooks/translation_jargon_check.py` (the proven structural pattern this design extends).
