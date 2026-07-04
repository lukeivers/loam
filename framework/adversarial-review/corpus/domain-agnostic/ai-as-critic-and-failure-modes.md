# AI as the adversarial critic — patterns that work, failure modes, counters

**Status: KEPT, reusable methodology. Researched 2026-07-03 (WebSearch + WebFetch, live).**
All claims cited; workspace synthesis marked **[SYNTHESIS]**. Companion to
`adversarial-review-general.md`.

This document answers two questions: (1) what does the research say about using an
LLM as critic/adversary, and (2) what are the KNOWN failure modes of AI review and
what structurally counters each? The second question is the important one — an AI
review that isn't genuinely harsh is worse than none, because it manufactures false
assurance.

---

## 1. What works — the load-bearing results

### 1.1 LLM critics catch real flaws — at the cost of noise

Nat McAleese et al. (OpenAI), "LLM Critics Help Catch LLM Bugs," arXiv:2407.00215,
June 2024. https://arxiv.org/abs/2407.00215

CriticGPT — an RLHF-trained critic for code — caught substantially more inserted and
naturally-occurring bugs than paid human reviewers (model critiques preferred over
human critiques in 63% of cases on naturally-occurring bugs; press coverage of the
same work reports ~85% vs ~25% bug catch rates: IEEE Spectrum,
https://spectrum.ieee.org/openai-rlhf). The catch: **the rate of nitpicks and
hallucinated bugs is much higher for models than for humans**, and even after
training specifically to reduce it, "their absolute rate is still quite high."
Human–machine teams wrote more comprehensive critiques than humans alone **while
reducing the hallucination rate compared to models alone**.

Design consequences: (a) an LLM critic is worth having — the recall is real;
(b) precision must be engineered around, never assumed; (c) a validation layer
between raw critique and delivered findings is not optional.

### 1.2 Isolated critique beats unstructured panel debate

Blaž Bertalanič & Carolina Fortuna, "The Cost of Consensus: Isolated Self-Correction
Prevails Over Unguided Homogeneous Multi-Agent Debate," arXiv:2605.00914.
https://arxiv.org/abs/2605.00914

Controlled study, teams of 10 identical models: unguided peer debate **underperformed
isolated self-correction** while burning 2.1–3.4× more tokens. Three named
mechanisms: **sycophantic conformity** (agents adopting majority positions at rates
exceeding 85%), **contextual fragility** (peer rationales destabilizing initially
correct reasoning, up to 70% vulnerability), and **consensus collapse** (plurality
voting discarding correct answers already present, gaps up to 32.3 points).

Corroborating: Binwei Yao et al., "Peacemaker or Troublemaker: How Sycophancy Shapes
Multi-Agent Debate," arXiv:2509.23055. https://arxiv.org/abs/2509.23055 — sycophancy
collapses debate into premature consensus; multi-agent setups then underperform
single-agent baselines; failure arrives by two distinct paths (debater-driven
agreement and judge-driven premature validation).

Design consequence: **critics run independently, in parallel, without seeing each
other**; their findings are merged by a separate judge; disagreement between critics
is preserved in the output, not negotiated away in a shared context.

### 1.3 Structured two-sided debate before a separate judge does work

Akbir Khan et al., "Debating with More Persuasive LLMs Leads to More Truthful
Answers," ICML 2024 (best paper), arXiv:2402.06782. https://arxiv.org/abs/2402.06782

When debate is *structured* — two experts argue opposite sides, a non-expert judge
decides — judges reach the truth far more often than without debate (76% vs 48% for
model judges; 88% vs 60% for humans), and optimizing debaters for persuasiveness
*improves* judge accuracy. Also Yilun Du et al., "Improving Factuality and Reasoning
in Language Models through Multiagent Debate," arXiv:2305.14325 (ICML 2024) — debate
rounds improve factuality on reasoning tasks.

Reconciliation with §1.2: debate helps when it is **adversarially structured with
assigned opposing sides and a separate judge**; it fails when it is a homogeneous
panel chatting toward consensus. The structure, not the multiplicity, does the work.

### 1.4 Self-critique without external grounding is worthless

Jie Huang et al., "Large Language Models Cannot Self-Correct Reasoning Yet,"
ICLR 2024, arXiv:2310.01798. https://arxiv.org/abs/2310.01798

Intrinsic self-correction — the model reviewing its own answer with no external
signal — fails to improve and often **degrades** performance. Design consequences:
(a) the author-agent's own "I reviewed my work" pass carries no evidential weight;
(b) the critic must be a different context (ideally a different agent) than the
author; (c) wherever the artifact admits an executable/checkable ground truth (run
the tests, re-derive the number, click the link), the review must use it — critique
anchored to external signals is the kind that works.

### 1.5 Named-axis judging beats single holistic verdicts

Lianmin Zheng et al., "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena,"
NeurIPS 2023 Datasets & Benchmarks, arXiv:2306.05685. https://arxiv.org/abs/2306.05685

The canonical LLM-as-judge study: strong aggregate agreement with human preference is
achievable, but the judge carries **position bias, verbosity bias, self-enhancement
bias, and limited reasoning on hard domains**; mitigations include position-swapping,
reference-guided grading, and multi-judge aggregation. Reference-guided / rubric-
anchored grading — giving the judge an explicit standard rather than asking for a
holistic impression — is the transferable pattern (it is also loam's existing
EVAL_DIMENSIONS discipline from the swarming corpus, kyegomez/swarms HEAD e48100a).

---

## 2. The failure modes — each named, evidenced, and countered

### F1 — Sycophancy / agreement bias

**Evidence:** Mrinank Sharma et al. (Anthropic), "Towards Understanding Sycophancy in
Language Models," ICLR 2024, arXiv:2310.13548. https://arxiv.org/abs/2310.13548 —
five state-of-the-art assistants consistently produce responses matching the user's
stated view over the true one; **both humans and preference models prefer
convincingly-written sycophantic responses over correct ones a non-negligible
fraction of the time** — i.e., the bias is trained-in via the preference signal and
will not be prompted away.

**Structural counters:**
- **Context isolation.** The critic never sees the parent conversation, the author's
  enthusiasm, the owner's investment, or the author's self-assessment. It is seeded
  with artifact + stated objective + review methodology only. (loam already has this
  primitive built and sealed: the frame-kernel's isolated fresh-context judge,
  `spawn_isolated_claude` — the review stage reuses it rather than reinventing.)
- **Refutation objective.** The tasking is "construct the strongest case this
  artifact fails its objective," not "evaluate" — the premortem stance removes the
  agreement-shaped question entirely.
- **One-shot verdict.** The verdict renders before any author/dispatcher response
  exists in context; there is no conversational turn for the critic to cave in.

### F2 — Self-preference / self-review

**Evidence:** Arjun Panickssery et al., "LLM Evaluators Recognize and Favor Their Own
Generations," NeurIPS 2024, arXiv:2404.13076. https://arxiv.org/abs/2404.13076 —
evaluators can recognize their own outputs, and self-recognition capability
correlates linearly with self-preference bias. Plus Huang et al. (§1.4): self-review
without external signal degrades.

**Structural counters:**
- The authoring agent instance is never the critic. Fresh context minimum;
  provenance-stripped artifact where feasible (the critic isn't told who wrote it).
- Where the critic and author are necessarily the same base model (a real constraint
  in a Claude-only harness), lean harder on the other counters: external ground
  truth (run it, re-derive it), independent derivation before reading (see F5), and
  domain-methodology anchoring — the biases that survive model identity are the ones
  anchored evaluation suppresses. **[SYNTHESIS]** on the compensation strategy; the
  bias itself is the cited finding.

### F3 — Shallow / generic critique

**Evidence:** Weixin Liang et al., "Can large language models provide useful feedback
on research papers? A large-scale empirical analysis," arXiv:2310.01783 (NEJM AI,
2024). https://arxiv.org/abs/2310.01783 — GPT-4 review comments on 3,096 Nature-
family + ICLR papers overlapped with human reviewers at rates comparable to
inter-reviewer agreement, **but tended toward generic rather than targeted critique**.
Generic critique is the AI-review failure that most resembles success.

**Structural counters:**
- **Domain methodology in hand** (the Fagan-checklist principle): the critic reviews
  against the failure taxonomy of THIS artifact class, pulled and kept before the
  pass — not against "good work" in the abstract.
- **Named-axis decomposition** (§1.5): each axis pinned to specifics the domain doc
  names; no single holistic pass.
- **Evidence pins per finding:** every finding must cite artifact location + concrete
  failure scenario + severity. **Generic-finding lint [SYNTHESIS]:** any finding that
  would read as true of *any* artifact of this class ("error handling could be more
  robust") is flagged as generic and excluded from the verdict calculus.

### F4 — Hallucinated flaws / nitpick floods

**Evidence:** McAleese et al. (§1.1) — model critics' hallucinated-bug and nitpick
rates are much higher than humans' and remain high even after targeted training.

**Structural counters:**
- **Finding-validation pass:** before findings reach the author/dispatcher, each is
  re-checked against the artifact by a separate cheap pass (re-read the cited lines,
  run the code, re-derive the number). Unverifiable findings are quarantined as
  HYPOTHESIZED — reported, but severity-capped and excluded from the blocking
  verdict. (Directly analogous to the human-machine team result in §1.1; the
  VERIFIED / INFERRED / HYPOTHESIZED tiering already exists in loam's reviewer
  personas.)
- **Severity taxonomy fixed in advance** (adversarial-collaboration pre-commitment):
  the verdict is driven by top-severity *validated* findings only; nitpicks are
  binned low and never block. Accept the recall/precision trade CriticGPT names —
  keep recall high, and spend the precision budget in the validation layer, not by
  making the critic timid.

### F5 — Performed harshness (Nemeth's trap, AI edition)

**Evidence:** Charlan Nemeth et al., "Devil's advocate versus authentic dissent,"
*Eur. J. Soc. Psych.* 2001 (full treatment in companion doc §3) — assigned
contrarianism produces weaker critique than authentically-held dissent, and its
presence inoculates the work against real challenge. For an LLM, a "be brutal"
system prompt is precisely an assigned role: it reliably buys brutal *tone*.

**Structural counters:**
- **Independent derivation, then diff [SYNTHESIS, from Nemeth]:** the critic first
  constructs, from the objective + domain methodology alone, what a correct artifact
  would have to contain — before reading the artifact — then diffs reality against
  its own construction. Disagreements are genuinely held positions, not poses.
- **Success is measured in validated findings, not adjectives.** The critic's output
  format has no register for hedged praise; its quality metric is the count and
  severity of findings that survive validation (Fagan's inspection-yield
  measurement, transplanted).
- Voice calibration with GOOD/DRIFT examples (loam's external-reviewer persona
  already carries this) — necessary but NOT sufficient; without the structural
  counters it produces harsh-sounding rubber stamps.

### F6 — Panel consensus collapse

**Evidence:** Bertalanič & Fortuna and Yao et al. (§1.2).

**Structural counters:** independent parallel critics, no shared context, separate
merge-judge, disagreement preserved. If deliberation is wanted for a high-stakes
call, use the Khan et al. structure (§1.3): assigned opposing sides, separate judge
— never a symmetric panel talking itself into agreement.

### F7 — False assurance from the review's existence

**Evidence base is the sum of F1–F6:** every mode above produces a review that ran,
looks rigorous, and missed the real flaws — after which "it passed adversarial
review" becomes ANTI-evidence, lowering everyone's guard. This is the failure the
whole capability must be designed against, and it has no single-paper citation
because it is the composite.

**Structural counters [SYNTHESIS, with named analogies]:**
- **Zero-findings suspicion:** a review of a nontrivial artifact that returns no
  substantive validated findings is an anomaly, not a clean bill (Fagan's yield
  statistics). The report must always carry "what I could not check" + the strongest
  surviving objection; a clean bill without named residual risk is malformed output.
- **Seeded-flaw calibration:** periodically hand the review stage an artifact with
  known injected flaws and measure catch rate — mutation testing / Fagan
  inspection-effectiveness measurement, applied to the reviewer itself. A review
  stage whose detection rate is never measured is faith, not protection.

---

## 3. One caution from loam's own corpus

The adversarial critic is an internal QA lens. Its skeptical persona must not become
the model of the actual audience or stakeholder — a bought-in counterparty is not a
hostile reviewer, and relaying the critic's worst-case as "what they will think"
misjudges the human on the other end
(`feedback_model_the_actual_stakeholder_not_a_defensive_archetype`). The review
answers "can this artifact survive attack?", never "how will this person receive it?"

---

## 4. Source index

| # | Source | What it establishes |
|---|--------|---------------------|
| 1 | McAleese et al. (OpenAI), *LLM Critics Help Catch LLM Bugs*, arXiv:2407.00215, 2024 | LLM critics out-catch humans; hallucinated-flaw + nitpick rates high; human/validation layer reduces them |
| 2 | Bertalanič & Fortuna, *The Cost of Consensus*, arXiv:2605.00914 | Unguided homogeneous debate < isolated critique; conformity >85%, consensus collapse |
| 3 | Yao et al., *Peacemaker or Troublemaker*, arXiv:2509.23055 | Sycophancy collapses multi-agent debate; debater- vs judge-driven failure paths |
| 4 | Khan et al., *Debating with More Persuasive LLMs...*, ICML 2024 (best paper), arXiv:2402.06782 | Structured opposing-sides debate + separate judge improves truth-finding (76/88% vs 48/60%) |
| 5 | Du et al., *Improving Factuality... through Multiagent Debate*, arXiv:2305.14325, ICML 2024 | Structured debate improves factuality/reasoning |
| 6 | Huang et al., *LLMs Cannot Self-Correct Reasoning Yet*, ICLR 2024, arXiv:2310.01798 | Intrinsic self-correction fails/degrades; external grounding required |
| 7 | Zheng et al., *Judging LLM-as-a-Judge...*, NeurIPS 2023, arXiv:2306.05685 | Judge biases (position/verbosity/self-enhancement) + mitigations; rubric-anchored judging |
| 8 | Sharma et al. (Anthropic), *Towards Understanding Sycophancy...*, ICLR 2024, arXiv:2310.13548 | Sycophancy is general and preference-trained; won't prompt away |
| 9 | Panickssery et al., *LLM Evaluators Recognize and Favor Their Own Generations*, NeurIPS 2024, arXiv:2404.13076 | Self-preference bias; correlates with self-recognition |
| 10 | Liang et al., *Can LLMs provide useful feedback on research papers?*, arXiv:2310.01783 / NEJM AI 2024 | LLM review overlaps human but skews generic |
| 11 | Perez et al., *Red Teaming LMs with LMs*, arXiv:2202.03286, 2022 | The adversary itself can be an LM |
| 12 | Ganguli et al. (Anthropic), *Red Teaming LMs to Reduce Harms*, arXiv:2209.07858, 2022 | Red teaming as discover→measure→reduce discipline |
| 13–18 | Klein (HBR 2007); Nemeth et al. (EJSP 2001); Fagan (IBM Sys. J. 1976); UK MOD Red Teaming Handbook 3rd ed. (2021); CIA Tradecraft Primer (2009); Mellers/Hertwig/Kahneman (Psych. Sci. 2001) | General-discipline foundations — see companion doc |
