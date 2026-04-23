# Research — memory-system GLiNER2 expansion (deferred amendment)

**Status:** DEFERRED — preserved research for a future amendment.
**Authored by:** assistant, 2026-04-22.
**Origin:** this research was the motivating content for amendment #8
(memory-system-subscription-routed-llm). During build, halt-trigger
fired on the torch/ML-stack transitive deps; the owner re-scoped
amendment #8 to an all-claude-p implementation (option 1) and deferred
the GLiNER2 path to its own amendment.

This doc preserves the findings so a future amendment can pick up
from here without re-running the research.

---

## 1. The idea

Graphiti-core 0.28.2 ships a `GLiNER2Client` (merged by Zep's CTO
Daniel Chalef in [PR #1284](https://github.com/getzep/graphiti/pull/1284)
on 2026-03-03) — a hybrid client that:

- Intercepts graphiti's entity-extraction prompts (the biggest and
  most frequent per-episode prompt — `extract_message`,
  `extract_text`, `extract_json` — anything where `response_model.__name__ == 'ExtractedEntities'`).
- Routes those through GLiNER2, a 205M–340M-param encoder model that
  runs on CPU in ~150ms per call.
- Delegates everything else (dedup, summarization, edge extraction,
  attribute extraction) to a secondary `LLMClient` the caller provides.

The pattern would pair GLiNER2 with `ClaudePrintLLMClient` for a
two-tier architecture: fast local-CPU entity extraction + subscription-
routed residual LLM work. Best-of-both quality and latency.

## 2. Quality findings

- **GLiNER2 ≈ GPT-4o on CrossNER** — F1 0.590 vs 0.599 across the
  CrossNER benchmark. At 205M params, essentially unbeaten for
  zero-shot NER quality-per-size.
  Source: [GLiNER2 paper (arxiv 2507.18546)](https://arxiv.org/html/2507.18546v1).
- **GLiNER zero-shot beats ChatGPT-3.5 and Vicuna** on most NER tasks.
  Source: [GLiNER zero-shot vs ChatGPT (Netra Neupane, Medium)](https://netraneupane.medium.com/gliner-zero-shot-ner-outperforming-chatgpt-and-traditional-ner-models-1f4aae0f9eef).
- **earezki.com 2B-model personal-knowledge-graph benchmark (Mar 2026):**
  qwen3-vl:2b-instruct-q4_K_M hit 0.87 F1 for person extraction with
  zero parse errors on 2 GB RAM. GLiNER2 base-v1 (205M) likely
  comparable or better on the same task.
  Source: [earezki.com personal KG benchmark](https://earezki.com/ai-news/2026-03-14-3-entity-extraction-with-a-2b-model-benchmarks-from-a-personal-knowledge-graph/).
- **CFM fine-tuned GLiNER case study** — baseline 87% F1 → 93.4%
  with ~few-hundred-example fine-tune. Reference Llama-3.1-70b
  unfinetuned: 95%. Small model + domain adaptation approaches
  big-model quality.
  Source: [HF blog CFM case study](https://huggingface.co/blog/cfm-case-study).
- **No published benchmark directly comparing Claude Haiku 4.5 to
  GLiNER2 on NER.** Best proxy: GLiNER2 ≈ GPT-4o, and Haiku is
  generally below GPT-4o on general benchmarks — so GLiNER2 is
  plausibly at-or-above Haiku for pure entity extraction. Not
  definitively shown.

**Counterpoint — cautionary finding:**
- **Sease Oct-2025 query-parsing study:** on 30 query-parsing
  queries, `gpt-4.1-mini` hit 100%, `gliner_medium-v2.1` got 16/30
  fully correct. Missing-entity bias (didn't hallucinate, just
  missed things), not false-positive problems. Signals: GLiNER
  models are strong but not flawless; on obscure domains
  fine-tuning matters.
  Source: [Sease: GLiNER vs gpt-4.1-mini](https://sease.io/2025/10/gliner-as-an-alternative-to-llms-for-query-parsing-evaluation.html).

**Verdict on quality:** GLiNER2 is credible for a general
personal-memory workload. Some quality loss vs Haiku on obscure
domain vocabulary is possible; fine-tuning closes the gap.

## 3. Why it was rejected for amendment #8

On 2026-04-22, the amendment #8 build agent attempted to install
`graphiti-core[gliner2]==0.28.2` in the memory-system venv and
halted per the approved flagged-inference #6 ruling.

**The halt:** `[gliner2]` extra pulls 53 packages into the venv,
including the full PyTorch ML stack:

- `torch>=2.0.0`
- `transformers>=4.51.3,<5.2.0`
- `onnxruntime`
- `sentencepiece`
- `tokenizers>=0.22.0,<=0.23.0`
- `safetensors>=0.4.3`
- `gliner-0.2.26` (pulled transitively by gliner2)
- `gliner2-1.3.0`
- ~15 more transitive deps (jinja2, sympy, networkx, mpmath, typer,
  rich, regex, huggingface_hub, hf-xet, …)

Reproduction:
```
cd memory-system && .venv/bin/pip install --dry-run 'graphiti-core[gliner2]==0.28.2'
```

**Why HTTP-API mode didn't escape the halt:** `gliner2-1.3.0`'s wheel
metadata declares `Requires-Dist: gliner`, and `gliner` is what pulls
torch. More fundamentally, `graphiti_core/llm_client/gliner2_client.py`
imports `from gliner2 import GLiNER2` at module scope — so even when
configured with `config.base_url=<remote>` for HTTP-API mode, the
local `gliner2` package (and therefore torch) must still be importable.
There is no in-venv path that uses `GLiNER2Client` as-shipped and
avoids torch.

## 4. Paths forward for a future GLiNER2 amendment

When the owner decides to expand into local-CPU extraction, four
routes exist. Ranked by engineering cost:

### Path A — Accept the ~500MB ML stack in memory-system venv

**Cost:** small code change (just enable the `[gliner2]` extra),
large install bloat (torch ~80MB wheel + 15 transitive deps).
Phase 3c dedicated-venv install time grows materially.

**Quality:** full GLiNER2 quality, fastest latency (~150ms per
extraction vs ~7s for claude -p).

**Re-opens:** owner ruling on amendment #8 flagged inference #6
("halt if torch is pulled") — this was explicitly gated against.

### Path B — Run GLiNER2 as a sidecar service in its own venv

**Cost:** large. Requires patching graphiti-core's
`gliner2_client.py` to NOT import `gliner2` at module scope — lazy-
import only when local-mode is selected. This is an upstream PR
(getzep/graphiti), or a vendored fork with the patch applied.
Plus: new launchd service for the GLiNER2 HTTP server, first-run
scaffold changes to bootstrap it, health-check integration.

**Quality:** same as Path A (full GLiNER2).

**Re-opens:** nothing new, but creates an upstream dependency.

### Path C — Different entity extractor (spaCy, regex NER, or similar)

**Cost:** medium-large. spaCy's small English model is ~40MB, no
torch needed. Build a custom `LLMClient` subclass that hooks
graphiti's `ExtractedEntities`-branch the same way `GLiNER2Client`
does but backed by spaCy. Requires reading graphiti's extraction
prompts and mapping entity types.

**Quality:** lower than GLiNER2 — spaCy small is a traditional NER
tagger, not an LLM-quality extractor. Might work OK for
well-formed text; weak on conversational / first-person / novel
entities.

**Re-opens:** nothing; orthogonal to the GLiNER2 stack entirely.

### Path D — Fine-tuned GLiNER2 on pos-v2 domain vocabulary

**Cost:** very large. Requires Path A or Path B first (the base
GLiNER2 has to actually run somewhere), then a labeled training
corpus of ~few-hundred pos-v2 episodes, then fine-tuning via
Fastino's hosted tuning service or local training.

**Quality:** highest — CFM case study showed 87% → 93.4% F1 with
fine-tune; pos-v2-specific terms (persona names, project codes,
Checkmate-era vocab) would all get domain-native extraction.

**When to do this:** only after measuring amendment #8's
`claude -p`-only quality in production and identifying a specific,
reproducible class of extraction failures that justifies the
engineering spend.

## 5. Decision trigger — when to revisit

Revisit GLiNER2 expansion if any of these hold:

1. **Quality signal:** amendment #8's production data shows a
   persistent pattern of extraction failures (missing entities,
   wrong dedup merges) that matter for downstream memory quality.
2. **Latency signal:** `claude -p`'s ~7s-per-call aggregate cost
   (across all graphiti LLM calls) becomes material on the user's
   ingest volume — memory lags observably behind session events.
3. **Rate-limit signal:** subscription quota is being hit frequently
   (amendment #8's `RateLimitError` → graphiti retry loop) and
   offloading the biggest prompt (entity extraction) would
   meaningfully reduce call count.

None of these are current. If amendment #8 ships and one of (1-3)
surfaces in real use, this expansion is the answer.

## 6. Other research preserved

The full research from the 2026-04-22 parallel agents covered:

- **Qwen3-Coder 30B (MoE):** viable as a general-purpose local LLM
  alongside GLiNER2 (18 GB VRAM Q4_K_M, 40-68 tok/s on Apple Silicon
  with MLX backend). Good for cases where GLiNER2's entity-only
  scope isn't enough.
- **DeepSeek-R1 32B:** Zep's own docs recommend this as the
  minimum-viable graphiti-with-Ollama model.
- **Gemma 4 26B MoE:** native function calling + structured JSON
  trained into weights; smaller footprint than Qwen3 32B dense.
- **Zep's published guidance:** "Avoid smaller models as they may
  not accurately extract data or output the correct JSON structures
  required by Graphiti. Use larger, more capable models and ensure
  they support structured output for reliable knowledge graph
  construction." — at least DeepSeek-R1 7B; community reports
  suggest 32B+ for clean graphs.
  Source: [Zep Graphiti LLM configuration docs](https://help.getzep.com/graphiti/configuration/llm-configuration).
- **Anthropic Haiku 4.5 pricing (for cost comparison):** $1.00/MTok
  input, $5.00/MTok output. Per-episode modeled tokens: ~11k input
  + ~2.4k output. Per-episode cost ~$0.023 at list. At 50
  episodes/day, ~$34.50/month list; with prompt caching + Batch API
  ~$3.50/month at 50% optimization. This is the "what would it cost
  if we just paid for a billed API key" answer — confirmed small,
  but blocked by owner's "zero cost for fundamental operation"
  principle.

## 7. References

Primary source: Zep's own graphiti repo.
- [Graphiti PR #1284 — GLiNER2 hybrid client](https://github.com/getzep/graphiti/pull/1284)
- [Graphiti v0.28.2 release notes](https://github.com/getzep/graphiti/releases)
- `/Users/lukeivers/ivers-corp-pos-v2/memory-system/.venv/lib/python3.13/site-packages/graphiti_core/llm_client/gliner2_client.py`
  (the installed file; read to see the module-scope import that
  prevents HTTP-API-mode from escaping the torch pull)

GLiNER research:
- [GLiNER2 paper (arxiv 2507.18546)](https://arxiv.org/html/2507.18546v1)
- [GLiNER2 on HuggingFace (fastino/gliner2-base-v1)](https://huggingface.co/fastino/gliner2-base-v1)
- [GLiNER2 Towards Data Science walkthrough](https://towardsdatascience.com/gliner2-extracting-structured-information-from-text/)
- [CFM GLiNER fine-tune case study](https://huggingface.co/blog/cfm-case-study)

Graphiti-Ollama known issues (context for Path B complexity):
- [#868 — Minimal Ollama example broken](https://github.com/getzep/graphiti/issues/868)
- [#912 — Validation error on ExtractedEntities](https://github.com/getzep/graphiti/issues/912)
- [#1116 — OpenAI Provider ignores api_base config](https://github.com/getzep/graphiti/issues/1116)
- [#1226 — Fully support Local Model Deployments in MCP Server](https://github.com/getzep/graphiti/issues/1226)

Local-LLM landscape (2026):
- [Qwen3 blog](https://qwenlm.github.io/blog/qwen3/)
- [Morphllm top-Ollama-models 2026 ranking](https://www.morphllm.com/best-ollama-models)
- [MikeVeerman tool-calling benchmark](https://github.com/MikeVeerman/tool-calling-benchmark)
