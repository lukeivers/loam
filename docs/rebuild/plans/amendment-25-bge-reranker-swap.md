# Plan — Amendment #25: memory-system BGE reranker swap

**Status:** authored 2026-04-22. Pre-amendment tip `390c0c1`. Research:
`docs/rebuild/plans/research/amendment-25-bge-reranker-swap-research.md`.
Manifest: `docs/rebuild/plans/amendment-25-bge-reranker-swap.manifest.yaml`.

Small scoped amendment. Swaps graphiti-core's silent default reranker
(`OpenAIRerankerClient` — needs `OPENAI_API_KEY` we don't configure)
for the local `BGERerankerClient` (`BAAI/bge-reranker-v2-m3`). Eliminates
a latent missing-API-key failure in the search path with reranking
enabled.

---

## 1. Objective

`make_graphiti()` passes an explicit `cross_encoder=...` argument to
the `Graphiti(...)` constructor so the library does not silently
default to `OpenAIRerankerClient`. The explicit argument is a
`BGERerankerClient` instance (via a lazy wrapper introduced in this
amendment — model load deferred to first `rank()` call). No
behaviour change when reranking is not exercised; the failure mode
flips from "silent AuthenticationError on first rerank" to "local
model loads on first rerank, then ranks locally".

## 2. Hard constraints

1. No `--amend`. Corrective commits only if something misses.
2. Scope: `memory-system/` source + tests + proposal note. **One
   sealed component only.** If a second needs touching → halt.
3. `graphiti-core==0.28.2` stays pinned (factory Kuzu patches remain
   load-bearing).
4. No real BGE model load in tests. Tests assert shape/type; no
   `CrossEncoder(...)` is invoked at test time.
5. pos-amend manifest is the bookkeeping interface; no hand-edits to
   BASELINE literals or sidecars.
6. `frozen_baseline: true` does NOT apply here — memory-system has a
   live floating BASELINE (not frozen like hands-off-lifecycle).

## 3. Acceptance criteria (AC25.x)

Each AC maps to one or more test functions named
`test_AC25_<n>_<slug>` in `memory-system/tests/test_factory.py`
(new file — the existing `test_service.py` covers transport; factory
tests are a distinct module).

### AC25.1 — `make_graphiti` passes explicit `BGERerankerClient`

`make_graphiti()` invoked without an explicit `cross_encoder`
override produces a Graphiti instance whose `cross_encoder`
attribute is an instance of
`graphiti_core.cross_encoder.bge_reranker_client.BGERerankerClient`
(subclass match via `LazyBGERerankerClient` counts). Test
monkeypatches `make_claude_print_client`, `make_ollama_embedder`,
and `make_kuzu_driver` to return stubs so the real LLM/embedder/DB
are not exercised; assertion is `isinstance(graphiti.cross_encoder,
BGERerankerClient)`.

### AC25.2 — factory does not load the BGE model at construction time

Constructing the factory's reranker wrapper does not invoke
`sentence_transformers.CrossEncoder` at `__init__` time. Test
imports the wrapper class, instantiates it, and asserts that the
model sentinel is `None` (or equivalent — the load is deferred to
first `rank()`). No network or model-weight read occurs during this
test.

### AC25.3 — `requirements.txt` pins `sentence-transformers`

`memory-system/requirements.txt` gains a `sentence-transformers>=3.2.1`
line (matching graphiti-core's declared extra floor). Test parses
the file and asserts the pin is present.

## 4. Test shape

New file: `memory-system/tests/test_factory.py`.

- `test_AC25_1_make_graphiti_uses_bge_reranker_by_default` — monkeypatches
  the three sub-factories (`make_claude_print_client`,
  `make_ollama_embedder`, `make_kuzu_driver`), awaits
  `make_graphiti()`, asserts `isinstance(g.cross_encoder,
  BGERerankerClient)`.
- `test_AC25_2_lazy_wrapper_defers_model_load` — instantiates
  `LazyBGERerankerClient()` directly, asserts `.model is None`. No
  mock needed because the wrapper's `__init__` skips the parent's
  eager load.
- `test_AC25_3_requirements_pins_sentence_transformers` — reads
  `memory-system/requirements.txt`, asserts `sentence-transformers`
  line exists with a `>=` specifier.

Stubs: monkeypatched factory returns minimal fake objects. The
`Graphiti(...)` constructor needs a `graph_driver`, an `llm_client`,
and an `embedder` — the stubs are the same plain-object shapes
amendment #24's `FakeGraphiti` precedent used (but simpler; this
test runs `Graphiti.__init__` itself rather than mocking the whole
constructor).

If `Graphiti.__init__` proves hostile to stubs (e.g. touches
`llm_client.set_tracer` in a way the stub can't satisfy), fall back
to monkeypatching `graphiti_core.Graphiti` itself to a recording
double; assert the recorder saw a `BGERerankerClient` in the
`cross_encoder` kwarg. Builder's call at implementation time; both
shapes satisfy AC25.1.

## 5. Source edits

### 5.1 `memory-system/src/factory.py`

Add the lazy wrapper class and route `make_graphiti` through it:

```python
from graphiti_core.cross_encoder.bge_reranker_client import BGERerankerClient


class LazyBGERerankerClient(BGERerankerClient):
    """Defer the BGE model load until first rank() call.

    Amendment #25. Parent's __init__ does a synchronous
    `CrossEncoder('BAAI/bge-reranker-v2-m3')`, which triggers a
    ~1 GB HF download on first run and several seconds of weight
    load even when warm. Factory-construction-time cost is
    unacceptable for the test suite and for MCP service startup
    (amendment #24's lifespan calls make_graphiti on every launchd
    start). Reranking is only exercised when graphiti.search() runs
    with a reranker-enabled SearchConfig, so deferring the load to
    first use lines cost up with value.
    """

    def __init__(self) -> None:
        # Intentionally skip super().__init__; parent's constructor
        # loads the model eagerly. Sentinel = None; load happens on
        # first rank().
        self.model = None  # type: ignore[assignment]

    async def rank(self, query, passages):
        if self.model is None:
            from sentence_transformers import CrossEncoder
            self.model = CrossEncoder("BAAI/bge-reranker-v2-m3")
        return await super().rank(query, passages)
```

In `make_graphiti`:

```python
graphiti = Graphiti(
    llm_client=llm_client,
    embedder=embedder,
    graph_driver=driver,
    cross_encoder=LazyBGERerankerClient(),  # amendment #25
)
```

Docstring addendum: cite amendment #25, note that without the
explicit argument graphiti-core defaults to `OpenAIRerankerClient`
which requires `OPENAI_API_KEY` — a billed-API coupling we rejected
in amendment #8 for the LLM path.

### 5.2 `memory-system/requirements.txt`

Add `sentence-transformers>=3.2.1` in the runtime-dep block, above
the `# dev / test` section. Inline comment cites amendment #25 and
explains it backs `BGERerankerClient`.

### 5.3 `memory-system/tests/test_factory.py`

New file. Three `test_AC25_*` functions per §4.

### 5.4 Proposal doc

`docs/rebuild/components/memory-system/proposal.md` — add a note in
the most recent §Adaptation (or §Direction if that's where the LLM
swap was recorded in amendment #8) recording the explicit local-
reranker choice. Builder's call on exact placement; one paragraph,
no scope expansion.

## 6. Manifest

`docs/rebuild/plans/amendment-25-bge-reranker-swap.manifest.yaml`:

- `baseline: 390c0c1`
- One component entry: `memory-system` (floating BASELINE).
- No `hands-off-lifecycle` entry — frozen-H19 precedent (per
  amendment #23) means H19 doesn't get bumped for amendments that
  don't source-edit it, and this amendment doesn't. If during
  implementation a second sealed component proves necessary →
  HALT per §2 constraint 2.
- `universal_paths` unchanged (default admissions).
- No extra allowed prefixes needed — `memory-system/` and
  `docs/rebuild/components/memory-system/` are both already in the
  seal-diff allowed tuple.

## 7. Commit plan (two commits, no `--amend`)

1. `fix(memory-system): switch reranker default from OpenAI to BGE
   local cross-encoder (amendment #25)` — code + tests +
   requirements + proposal note + `pos-amend apply` manifest output
   (BASELINE bump + sidecar placeholder).
2. `chore(seals): bge-reranker-swap seal — memory-system at
   <amendment-sha>` — `pos-amend seal` output (sidecar advances to
   amendment SHA, narrative appended).

## 8. Test scope (amendment-dispatch-speedup CDC)

Pre-amendment:

- `cd memory-system && .venv/bin/pytest -q` — full memory-system
  suite (expect 80 passed, 1 skipped at baseline).
- Seal-diff-only on the other 9 components
  (`test_no_sealed_amendments.py` / `test_cross_cutting.py`).

Post-seal:

- Seal-diff-only across all 10 components.

Rationale: the code change is narrowly confined to
`memory-system/src/factory.py`. No downstream component reads that
surface. The speedup CDC admits seal-diff-only for unaffected
components.

## 9. Halt triggers (carried from research)

1. `BGERerankerClient()` instantiated without the lazy wrapper
   triggers model download at factory-construction time → **halt**,
   redesign. (Resolved at plan time by introducing
   `LazyBGERerankerClient`.)
2. `sentence-transformers>=3.2.1` refuses to pip-install because of
   a transitive conflict with an existing pin → **halt**. (Cleared
   in research §4; verify again at implementation.)
3. `Graphiti.__init__` stubs require mocks too invasive to assert
   the `cross_encoder` shape cleanly → **halt**, use the fallback
   recorder pattern from §4.
4. Scope would need to touch a second sealed component → **halt**,
   rescope.

## 10. Done when

- Two commits landed matching §7 messages.
- `memory-system/src/factory.py::make_graphiti` passes explicit
  `BGERerankerClient` via `LazyBGERerankerClient`.
- `memory-system/requirements.txt` has `sentence-transformers`
  pinned with a `>=` floor.
- `memory-system/tests/test_factory.py` new, three `test_AC25_*`
  tests, all pass.
- Proposal doc carries the explicit-local-reranker note.
- Seal-diff tests for all 10 components pass post-seal.
- No non-memory-system source paths touched (modulo proposal doc
  and plans/research paper trail).
