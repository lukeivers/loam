# Proposal — memory-system-subscription-routed-llm amendment (#8)

**Status:** APPROVED (option 1 re-scope) — owner signoff 2026-04-22.
**Authored by:** assistant (this session).
**Target components (multi-component amendment):**
`memory-system` + `hands-off-lifecycle` (BASELINE bump + first-run
assertions for the ANTHROPIC_API_KEY no-longer-required path).
**Precedent:** orchestrator-bootstrap-unification amendment
(multi-component seal at `9aeabd4`); namespaced-labels-and-bootout
amendment (multi-component seal at `a5dbf8f`).

---

## 0. Revision note (2026-04-22)

This proposal was originally drafted with a hybrid architecture:
graphiti's `GLiNER2Client` (local-CPU 205M-param encoder) for entity
extraction + a new `ClaudePrintLLMClient` for residual LLM work
(dedup/summary/edges/attributes).

On first build attempt, halt-trigger §5 #6 fired:
`graphiti-core[gliner2]==0.28.2` pulls **53 packages** including
`torch`, `transformers`, `onnxruntime`, `sentencepiece`, `tokenizers`,
`safetensors` — the full PyTorch ML stack (~500MB+ install bloat).
Even `GLiNER2Client`'s HTTP-API mode requires the `gliner2` package
locally, because `graphiti_core/llm_client/gliner2_client.py` imports
`from gliner2 import GLiNER2` at module scope. There is no in-venv
path that uses `GLiNER2Client` and avoids torch.

Owner ruling 2026-04-22: **option 1 — drop GLiNER2 entirely from this
amendment.** All graphiti LLM calls route through `ClaudePrintLLMClient`.
The headline goal (subscription-routed, zero dollar cost) is unaffected.
Local-CPU fast-path for entity extraction is deferred to a future
amendment; research preserved at
`docs/rebuild/components/memory-system-gliner2-expansion/research.md`.

---

## 1. Objective

The memory-graphiti sidecar runs without any billed API key. All
graphiti LLM calls — entity extraction, deduplication, summarization,
edge extraction, attribute extraction — route through `claude -p`
subprocess invocations that consume the user's Claude Max subscription,
not an Anthropic Console account. Fresh first-run completes end-to-end
with zero ongoing dollar cost.

Two behaviours in one objective — §4 below counts criteria.

## 2. Constraints

- **Budget.** Behavioural refactor + one new module
  (`ClaudePrintLLMClient`). No new graphiti-core version. No new
  heavyweight Python dependencies (no torch, no ML stack). The only
  new dep is the `claude` CLI binary, which the user already has
  installed as part of their Claude Code environment.
- **Reversibility.** Fully reversible. Old `make_anthropic_client`
  function and its call sites can be restored from git if the
  subscription-routed path proves untenable. Graphiti's sealed
  ingestion semantics are unchanged — only the LLM backend swaps.
- **Dependency fence.** Amends `memory-system/` and
  `hands-off-lifecycle/` only. Every other sealed component is
  off-limits — orchestrator, safety-layer, reversibility-primitive,
  cost-governance, self-correction, graceful-degradation,
  scope-of-work, objective-tracker, primary-persona,
  observability-aggregator, self-upgrade, workspace-bootstrap,
  telegram-interface.
- **Authority bound.** Owner approves acceptance criteria (this doc)
  + the seal-plan SHA bump + the flagged inferences in §5. Owner has
  already ruled on inferences #1–#4 (2026-04-22); #5 + #6 dropped with
  the option-1 re-scope. Builder chooses the `ClaudePrintLLMClient`
  module layout, diagnostic wording, and rate-limit/backoff specifics.
- **Fail-closed direction.** `claude` binary missing from PATH or
  not authenticated (OAuth keychain empty) halts factory construction
  with a typed error *before* any episode is ingested. No silent
  degradation to billed API. If the subscription-routed path is
  unavailable, the service refuses to start — graceful-degradation
  framework's `memory_sidecar` degraded mode handles this at the
  orchestrator layer per the existing hands-off-lifecycle sidecar
  design.
- **Error codes.** Memory-system's historical claim inside the
  hands-off-lifecycle block is `-32095` (staging-overflow) and
  `-32096` (drain-poison); those stay with their original owners —
  no overloading. This amendment claims a fresh
  **memory-system runtime block at `-32110..-32119`** (the first
  available ten-code block after telegram-interface's
  `-32100..-32109`). New codes: `-32110` claude-binary-missing,
  `-32111` claude-unauthenticated, `-32112`
  claude-print-response-malformed. `hands-off-lifecycle/README.md`
  is updated to cross-reference the new block.
- **`--bare` is NOT used.** `claude -p --bare` explicitly skips
  OAuth/keychain reads and requires `ANTHROPIC_API_KEY` — the exact
  thing we're avoiding. The client invokes `claude -p` without
  `--bare` so OAuth authentication resolves from the user's keychain.
- **Latency budget.** `claude -p` subprocess overhead is ~7s per call.
  With all graphiti LLM calls now routing through it (4–5 calls per
  episode after the option-1 re-scope), budget is ~30s/episode p95.
  At 50 episodes/day ≈ 25 min/day of wall-clock CPU-light subprocess
  work. Graphiti's async model parallelises across concurrent
  ingests. Memory ingest is a sidecar, not user-facing — this is fine.
- **Out of scope (other tasks / future amendments).** GLiNER2 local-
  CPU extraction (preserved research at
  `docs/rebuild/components/memory-system-gliner2-expansion/research.md`;
  future amendment if quality pressure warrants the engineering cost).
  Ollama fallback for rate-limit scenarios. Telegram-interface adapter
  (separate amendment).

## 3. Acceptance criteria

Each criterion maps 1:1 to a test function in the build.

### AC1 — Factory requires no ANTHROPIC_API_KEY

`make_graphiti()` called with `ANTHROPIC_API_KEY` absent from the
environment, `claude` binary on PATH, and authenticated Claude Code
OAuth state succeeds and returns a usable `Graphiti` instance. Test:
unset `ANTHROPIC_API_KEY` in a monkeypatched env; mock the subprocess
layer to simulate authenticated `claude`; assert factory returns
without raising.

### AC2 — ClaudePrintLLMClient invokes subprocess with expected argv + scrubbed env

Given a `Message` list and a `response_model`, the client spawns
`claude -p --no-session-persistence --output-format json --model <model>`
as a subprocess. `--bare` is explicitly NOT passed. The subprocess's
environment is explicitly constructed (PATH, HOME, and other benign
vars) so that `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` cannot leak
from the parent into the child — prevents accidental billing via the
wrapper. Test: patch `asyncio.create_subprocess_exec`; assert argv
matches + the `env` kwarg excludes all API-key vars even when set in
the parent process.

### AC3 — ClaudePrintLLMClient parses JSON response into graphiti's expected dict

Given a synthetic `claude -p --output-format json` stdout payload
(shape verified in-session: `{"type":"result","result":"<text>","total_cost_usd":<float>,...}`),
the client extracts `.result`, parses it as JSON against the
`response_model` Pydantic schema, and returns the expected
`dict[str, Any]`. Malformed JSON → typed parse error. Test: feed
fixture JSON blobs; assert output matches schema.

### AC4 — claude binary missing fails closed at factory construction

Monkeypatch `shutil.which("claude")` to return None. Call
`make_graphiti()`. Assert it raises a typed error (new subclass of a
memory-system-owned base; code in `-32095..-32096` range) with
remediation text naming "install Claude Code". Structural refusal
before any orchestrator import or subprocess spawn.

### AC5 — Unauthenticated claude fails closed at factory construction

Mock the initial `claude -p` probe subprocess to emit the exact
"Not logged in · Please run /login" string the CLI produces in bare
mode or when OAuth is absent. Assert `make_graphiti()` raises a typed
error distinguishable from AC4's (different `kind:` label in the
exception payload). Remediation text names `claude /login`.

### AC6 — Subprocess rate-limit response raises graphiti RateLimitError

Simulate a `claude -p` response indicating subscription rate limit
(exact string detection is builder's call — likely inspects
`is_error: true` + result text for "rate"/"429"/similar signal).
`ClaudePrintLLMClient._generate_response` translates that into
`graphiti_core.llm_client.errors.RateLimitError` so graphiti's
existing retry-with-backoff machinery kicks in. Confirms integration
with graphiti-core's error model.

### AC7 — Error-code-block discipline (re-extension, 2026-04-22)

All `ClaudePrintClientError` subclasses defined by this amendment
carry a `.code` attribute within the `-32110..-32119` memory-system
runtime block. **No** subclass code collides with any existing code
in the hands-off-lifecycle-owned `-32090..-32099` block (staging-
overflow, drain-poison, pip-install-failed, etc.). Test: introspect
the error-class hierarchy (`ClaudePrintClientError` and every subclass
defined in `claude_print_client.py`); assert each `.code` satisfies
`-32119 <= code <= -32110`.

This criterion is the ODD re-extension of the gap discovered during
the first build attempt: the original proposal said "reuse -32095..-32096"
but those values were already claimed by `staging.py` and `drain.py`.
The builder initially tried to overload via `kind:` labels (rejected
at owner review) before the correct structural fix — claim a fresh
memory-system runtime block at `-32110..-32119` — landed. This AC
pins the structural outcome so future errors added to the client stay
inside the new block.

### AC8 — Reranker does not invoke the billed OpenAI path at ingest (re-extension, 2026-04-22)

Memory-system's `add_episode` (ingest) path must not issue any
outbound OpenAI API request as a side effect of the graphiti-core
reranker. A test calls the memory-system's default ingest surface
with a monkey-patched `OpenAI` client (or equivalent intercept at the
`openai` package boundary); asserts zero API calls were made during
ingest.

Rationale: the original memory-system proposal (§1 line 24) names
"reranking: Claude via Anthropic Max subscription" as the intent.
Graphiti-core 0.28.2 auto-instantiates an `OpenAIRerankerClient` in
`Graphiti()` that would route reranker calls to OpenAI with whatever
`OPENAI_API_KEY` the environment provides. Test-time uses
`OPENAI_API_KEY=ollama` (an Ollama-compat placeholder) to let the
reranker client construct without exploding, but any actual API call
issued at ingest would bill OpenAI. This AC pins the invariant
*"ingest stays billed-API-call-free"* without blocking on the full
reranker-subscription-routing work.

Full subscription-routing of the reranker (replace the OpenAI client
with a claude-`-p`-backed reranker) is scoped to a **follow-up
amendment**; this amendment captures the gap via the BACKLOG entry
added under the same commit.

### AC9 — Seal diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` after the amendment
shows only paths under `memory-system/`, `hands-off-lifecycle/`,
`docs/rebuild/components/memory-system-subscription-routed-llm/`,
`docs/rebuild/components/memory-system-gliner2-expansion/`
(the preserved-research doc), `docs/rebuild/plans/` (plan-before-
code CDC paper trail — the CDC was codified at commit `fd8c833`
after this proposal was first drafted; amendment #10's
`linux-removal-amendment.md` set the precedent for including plan
files in the amendment's code commit), and `data/`. Any path
outside this set is a halt condition for the seal commit.

## 4. Behaviour-count check

| Behaviour | Criteria |
|-----------|----------|
| Factory runs without billed API key | AC1 (construct succeeds no-key), AC4 (binary missing halts), AC5 (unauthed halts) |
| Subscription routing is the actual execution path | AC2 (argv + clean env), AC3 (response parse), AC6 (rate-limit integration) |
| Error-code hygiene | AC7 (re-extension) |
| Reranker does not silently re-introduce a billed-API path | AC8 (re-extension) |
| Seal discipline | AC9 |

Five distinct behaviours → nine criteria → every behaviour covered.

## 5. Flagged inferences (owner rulings, 2026-04-22)

1. **`ClaudePrintLLMClient` location.** RULING: **`memory-system/src/claude_print_client.py`**
   (new file, workspace-local). Upstreaming to graphiti-core is a
   separate follow-on task.

2. **Latency tolerance.** RULING: **accept ~7s/call.** All-through-
   `claude -p` routing yields ~30s/episode wall-clock. At 50
   episodes/day ≈ 25 min/day of background subprocess work. Memory
   ingest is sidecar, not user-facing. No pool, no batch, no
   complex optimization in this amendment.

3. **Rate-limit behaviour.** RULING: **translate to graphiti's
   existing `RateLimitError`**; rely on graphiti-core's 4-attempt
   exponential-backoff retry. No Ollama fallback, no graceful-
   degradation integration in this amendment. Revisit if real-world
   data shows insufficient recovery.

4. **Observability.** RULING: **surface the `total_cost_usd` field**
   from `claude -p`'s JSON output as an "equivalent cost" signal via
   graphiti's `TokenUsageTracker` or a custom span attribute. Useful
   as a Max-subscription-usage proxy even though no actual billing
   occurs.

   **LANDED (amendment #11 audit-closure §F3):** custom span
   attribute. `ClaudePrintLLMClient.cost_tracker` accumulates
   `total_cost_usd` across calls; `MemoryAPI.ingest` snapshots the
   tracker before and after each `graphiti.add_episode` and emits
   the delta as the `claude.equivalent_cost_usd` attribute on the
   `memory.ingest` span. Graphiti's `TokenUsageTracker` would have
   required a vendor-side seam for cost (it tracks tokens, not
   dollars); the span-attribute path keeps the observability surface
   owned by memory-system without modifying graphiti-core.

5–6. **GLiNER2 weights + `[gliner2]` extra.** DROPPED per option-1
re-scope. See §0 revision note. Preserved research at
`docs/rebuild/components/memory-system-gliner2-expansion/research.md`.

## 6. Seal plan

1. Create a new `memory-system/tests/test_no_sealed_amendments.py`
   (memory-system currently ships a `SEAL_COMMIT` sidecar but no
   seal-diff test — same situation orchestrator was in before
   amendment #7). Mirrors
   `orchestrator/tests/test_no_sealed_amendments.py` structure.
   `BASELINE` starts at `9aeabd4` (the amendment-#7 seal commit —
   current tip pre-amendment).
2. Advance `BASELINE` in
   `hands-off-lifecycle/tests/test_cross_cutting.py` from `a5dbf8f`
   → `9aeabd4`.
3. Amendment commit: `fix(memory-system, hands-off-lifecycle):
   memory-system-subscription-routed-llm amendment (#8)`.
4. Tests committed together with the fix.
5. Seal commit (separate): `chore(seals):
   memory-system-subscription-routed-llm seal — memory-system +
   hands-off-lifecycle at <sha>`. Advances
   `memory-system/tests/SEAL_COMMIT` from `0df02d5` → amendment
   code-commit SHA; advances `hands-off-lifecycle/tests/SEAL_COMMIT`
   from `445a6b4` → amendment code-commit SHA; appends amendment-
   cycle note to `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`.
6. Allowed-prefix additions for the seal tests:
   - `memory-system/` test (new):
     `("memory-system/", "hands-off-lifecycle/", "docs/rebuild/components/memory-system-subscription-routed-llm/", "docs/rebuild/components/memory-system-gliner2-expansion/", "docs/rebuild/plans/", "data/")`.
     `docs/rebuild/plans/` is the CDC paper-trail slot added after
     the proposal's first draft; fd8c833 codified plan-before-code.
   - `hands-off-lifecycle/` test gains the two new docs prefixes to
     its top-level `docs` permission (currently segment-matching;
     already permissive enough).

## 7. Halt triggers

- `claude -p` OAuth keychain lookup fails on Luke's clean macOS
  keychain with active Max subscription (suggests Claude Code CLI
  bug, not this amendment's concern).
- Rate-limit detection requires inspecting undocumented `claude -p`
  internals not exposed via `--output-format json` — signals the
  error-signal seam needs a different design.
- Any AC test cannot be written deterministically without actually
  invoking a network-bound `claude` subprocess — signals the
  subprocess seam needs a cleaner injection point.
- Memory-system test suite has a regression outside the amendment's
  touched files — halt before seal.
- `make_anthropic_client()` has callers outside `make_graphiti()`
  (smoke tests, eval scripts) that would break if deleted — builder
  leaves it in place, uses it only when called explicitly, removes
  the env-var requirement at the default path only.

Any of the above: halt, signal to owner, re-scope.
