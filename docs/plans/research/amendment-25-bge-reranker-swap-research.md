# Research — Amendment #25: memory-system BGE reranker swap

**Author:** amendment builder, 2026-04-22 (working dir
`/Users/lukeivers/ivers-corp-pos-v2/`, pre-amendment tip `390c0c1`).
**Status:** research artefact backing the amendment plan at
`docs/plans/amendment-25-bge-reranker-swap.md`.
**Scope:** characterise the graphiti-core cross-encoder default
(`OpenAIRerankerClient`), the proposed replacement
(`BGERerankerClient`), the `sentence-transformers` dependency
footprint, and the factory lifecycle implications for the memory-
system MCP service introduced by amendment #24.

---

## 1. Why the default is wrong for this codebase

`graphiti_core.Graphiti.__init__` (0.28.2, lines 221–224 of
`graphiti.py`) defaults an unset `cross_encoder` parameter to
`OpenAIRerankerClient()`. That client's `__init__`
(`graphiti_core/cross_encoder/openai_reranker_client.py`) constructs
an `AsyncOpenAI` client from the process environment when `client` is
`None`. `AsyncOpenAI()` reads `OPENAI_API_KEY` at request time — the
constructor tolerates a missing key, but the first `rank()` call
fails with an `openai.AuthenticationError` deep inside
`_run_boolean_classifier_prompt`.

The memory-system amendment #8 (subscription-routed LLM) explicitly
*removed* `ANTHROPIC_API_KEY` coupling from the LLM path by swapping
in `ClaudePrintLLMClient`. The embedder path is Ollama (amendment #8,
`make_ollama_embedder`). **The reranker path is the only surface
where a missing-API-key failure can still land**, and it does so
silently: `make_graphiti()` returns a fully-constructed Graphiti
object, then a downstream `graphiti.search()` with `SearchConfig`
reranking turned on raises. No AC covers this today because no test
flexes reranking. The brief's "queryable through the MCP interface"
clause (D1) is therefore latent-broken on a fresh-first-run machine
that has never set `OPENAI_API_KEY`.

`OpenAIRerankerClient` also defaults to `gpt-4.1-nano` and uses
log-probabilities to do a boolean classifier per passage. Even if
the key were configured, this is a billed API path that contradicts
amendment #8's subscription-routed direction.

**Scope conclusion:** the default must be replaced with a local
reranker; BGE is the only offline cross-encoder option graphiti-core
ships.

## 2. What `BGERerankerClient` is

Source: `graphiti_core/cross_encoder/bge_reranker_client.py`.

```python
class BGERerankerClient(CrossEncoderClient):
    def __init__(self):
        self.model = CrossEncoder('BAAI/bge-reranker-v2-m3')

    async def rank(self, query: str, passages: list[str]) -> list[tuple[str, float]]:
        # runs self.model.predict on (query, passage) pairs via
        # loop.run_in_executor; returns (passage, score) sorted desc.
```

- Model: `BAAI/bge-reranker-v2-m3`. Multilingual cross-encoder
  released July 2024. Parameter count ~568M; on-disk HF weights
  roughly 2.3 GB (f32) / 1.1 GB (f16) — downloaded via
  `sentence-transformers` → `huggingface_hub` on first `CrossEncoder()`
  instantiation.
- Runs locally on CPU or MPS/CUDA via `torch`; no network after
  initial download.
- Same `CrossEncoderClient` interface as `OpenAIRerankerClient`, so
  it drops into `Graphiti(cross_encoder=…)` without any search-path
  changes.
- Import-time behaviour: the module's top-level `try: from
  sentence_transformers import CrossEncoder` raises `ImportError`
  with a hint if `sentence-transformers` is missing. Importing the
  module does not touch the network or load the model.

## 3. Lifecycle: when does the model load?

**Critical finding: `CrossEncoder('BAAI/bge-reranker-v2-m3')` runs
inside `BGERerankerClient.__init__`.** Instantiation is
synchronous and:

1. On a machine with no HF cache, triggers a ~1 GB download (f16
   weights) from `huggingface.co`.
2. On a machine with a warm cache, still loads the weights into
   RAM via `torch` — measurable seconds of overhead.

If `make_graphiti()` instantiated `BGERerankerClient()` directly and
unconditionally, every pytest run that imports the factory would pay
that cost (or fail offline / in CI). The halt trigger "BGE requires
model download at factory-construction time and that would slow every
test dramatically" fires.

**Resolution: a lazy wrapper.** A thin subclass in
`memory-system/src/factory.py` defers the `CrossEncoder(...)` load
until the first `rank()` call:

```python
class LazyBGERerankerClient(BGERerankerClient):
    """Defer the BGE model load until first rank() — not __init__.

    Parent's __init__ does `CrossEncoder('BAAI/bge-reranker-v2-m3')`
    synchronously, which costs ~1 GB download on first run and
    seconds of load time even when warm. Factory-construction-time
    cost is unacceptable for the test suite (mocks aside) and for
    MCP service startup. The rerank path is only flexed when
    `graphiti.search()` is called with a reranker-enabled
    SearchConfig, so deferring to first use lines up with actual
    cost-to-value.
    """

    def __init__(self) -> None:  # no super().__init__ — that's the point
        self.model = None  # sentinel; loaded lazily

    async def rank(self, query, passages):
        if self.model is None:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder('BAAI/bge-reranker-v2-m3')
        return await super().rank(query, passages)
```

The wrapper:

- Preserves `BGERerankerClient` typing and public surface.
- Does not call parent's `__init__` (which loads eagerly).
- Passes `isinstance(x, BGERerankerClient)` — the required AC
  assertion in the new test.
- Makes test mocking trivial: patch the `CrossEncoder` import at
  first-rank or patch the whole `LazyBGERerankerClient` class.

## 4. `sentence-transformers` footprint

PyPI versions available as of 2026-04: up to `5.4.1`.
`graphiti-core==0.28.2` declares `sentence-transformers>=3.2.1` as
the `sentence-transformers` optional-extra. Pin convention in this
codebase is `>=`-floor, matching every other line of
`memory-system/requirements.txt` except the explicit
`graphiti-core==0.28.2` lock (which itself carries a load-bearing
factory patch — see §11).

Transitive deps (5.4.1 at the time of writing):

- `torch` (PyTorch, already potentially present from other
  installs; if absent, a several-hundred-MB wheel).
- `transformers` (~15 MB wheel + `tokenizers`, `safetensors`,
  `huggingface-hub`, `regex`, `pyyaml` — pyyaml already pinned for
  amendment #13's hands-off-lifecycle reachability work).
- `numpy` (already pinned).
- `scikit-learn`, `scipy`, `pillow`, `tqdm` — small/medium wheels.
- `filelock`, `packaging`, `typing-extensions`, `requests`, `certifi`,
  `urllib3`, `idna`, `charset-normalizer` — universally small.

**Conflict scan:** the current `memory-system/requirements.txt` pins
`pyyaml>=6.0`, `numpy>=1.26`, `pydantic>=2.0`, `anthropic>=0.39.0`.
None of `sentence-transformers`'s transitives conflict:

- `anthropic>=0.39.0` pulls no deps in conflict with `transformers`.
- `numpy>=1.26` is compatible with recent `transformers`/`torch`.
- `pydantic>=2.0` is compatible with `transformers` which uses
  `pydantic` only as an optional import.
- `pyyaml>=6.0` is compatible with `transformers`.

Halt trigger "sentence-transformers dep conflicts with an existing
dep pin" is **cleared**.

Net footprint growth: noticeable (torch + transformers + model
weights on first run), but this is the cost of moving a billed API
path to a local model. The embedder already runs locally (Ollama);
the reranker matching that direction is consistent.

## 5. Amendment #24 MCP startup interaction

Amendment #24 replaced the FastAPI service with a FastMCP server
whose `lifespan` calls `make_graphiti()` at startup. With the lazy
wrapper in place:

- Service startup pays **zero** reranker cost. Only the embedder
  (Ollama HTTP probe), the Claude-print client (OAuth probe), and
  Kuzu index build happen at startup.
- First `search` tool invocation with reranking enabled triggers the
  one-time BGE model load inside the `rank()` executor
  (`loop.run_in_executor`). It is awaited, so the first-query
  latency includes the load. Subsequent calls hit the warm model.
- `graphiti.add_episode()` does not touch the reranker; ingest is
  unaffected.

This matches amendment #24's dispatch goal of "Graphiti lifecycle
preserved, startup footprint not worsened." Had eager instantiation
stayed, MCP service startup would have paid the model-load cost —
acceptable for a long-lived daemon but still bad for the first-run
UX and test suite.

## 6. Test shape

`test_AC25_make_graphiti_uses_bge_reranker_by_default` (new, in
`test_service.py` or a dedicated `test_factory.py` — builder's call
on placement; existing `test_service.py` already covers the MCP
surface, so a new file is cleaner):

- Monkeypatch `make_claude_print_client`, `make_ollama_embedder`,
  `make_kuzu_driver` to return stubs (factory already isolates each
  piece; the `test_service.py` `FakeGraphiti` fixture pattern from
  amendment #24 is the precedent).
- Call `make_graphiti()`; assert
  `isinstance(graphiti.cross_encoder, BGERerankerClient)`.
- Do NOT instantiate the real `CrossEncoder`. Because the amendment
  introduces a `LazyBGERerankerClient` whose `__init__` skips the
  parent load, no mock of `CrossEncoder` is required for this
  assertion; `isinstance` check holds via subclassing.

Coverage: amendment #24's `test_service.py::test_AC24_1_…` already
mocks `make_graphiti` entirely. The new test exercises the factory
path directly — the layer amendment #24 skipped.

## 7. Proposal-doc placement

`docs/archive/component-research/memory-system/proposal.md` carries the
component's design narrative. Amendment #8 edited §Direction's LLM
paragraph when it swapped AnthropicClient → ClaudePrintLLMClient;
the parallel move for this amendment is §Direction's
reranker/embedder sentence (or §Adaptation, whichever is the active
version). Builder's exact placement call per the dispatch; a one-
paragraph note at the bottom of the most recent §Adaptation entry is
sufficient.

## 8. Seal-diff scope

Manifest touches only `memory-system`:

- `memory-system/src/factory.py` — wrapper + import + call site.
- `memory-system/requirements.txt` — new dep pin.
- `memory-system/tests/test_factory.py` (new) — or
  `memory-system/tests/test_service.py` (extension).
- `docs/archive/component-research/memory-system/` — proposal doc note.

`hands-off-lifecycle` is **not** coupled. Per the frozen-H19 pattern
established by amendment #23, its BASELINE is pinned at project-
start; no amendment-driven bump needed. H19's seal-diff allowed-
prefix tuple already admits `memory-system/` and
`docs/archive/component-research/memory-system/`.

`memory-system/tests/test_no_sealed_amendments.py` — BASELINE
advances from `494a5ef` → `390c0c1` (pre-amendment tip), sidecar
sealed to the amendment SHA post-code. The allowed-prefix tuple is
already wide enough; no extra-prefix admission needed.

## 9. Halt triggers — status

| Trigger | Status |
|---|---|
| BGE model download at factory-construction time | **Cleared** via `LazyBGERerankerClient` (defer to first `rank()`). |
| `sentence-transformers` dep conflicts with existing pin | **Cleared** — no transitive overlaps with the existing `memory-system/requirements.txt`. |
| Test requires live-network or real model | **Cleared** — `isinstance` check passes without model load. |
| Scope cascades beyond memory-system | **Cleared** — no sibling component source touched. |

## 10. Prior-art cross-reference

- Amendment #8: removed billed LLM API path (AnthropicClient →
  ClaudePrintLLMClient). Same spirit. Proposal-doc edit precedent
  set there.
- Amendment #11 §F1: deleted orphan `make_anthropic_client` factory
  after the swap. No such orphan exists here — the OpenAI reranker
  was never used explicitly, it was the implicit default.
- Amendment #24: MCP migration. Lifespan calls `make_graphiti` at
  startup — the target surface for this amendment's lazy-load
  correctness.
- Frozen-H19 (amendment #23): no hands-off-lifecycle BASELINE bump
  for amendments that don't source-edit H19.

## 11. Versioning caveat (carried over)

`graphiti-core==0.28.2` stays pinned. The two KuzuDriver patches in
`factory.py::make_kuzu_driver` remain load-bearing. Upgrading
graphiti-core is out of scope for amendment #25; if the upstream
cross-encoder registry changes shape (e.g. adds a "none" option), a
future amendment can revisit.
