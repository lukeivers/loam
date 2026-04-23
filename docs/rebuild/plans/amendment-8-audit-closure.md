# Amendment #11 — Amendment-#8 audit-closure plan

**Status:** plan (written before any source edit, per plan-before-code CDC).
**Branch:** `pos-v2` at HEAD `77389ce` (seal commit of amendment #8).
**Motivation:** close every actionable finding from the 2026-04-22
Blocker-3 audit of the memory-system-subscription-routed-llm amendment
(amendment #8). Findings fall into three buckets: one RED (an AC's
test does not exercise the AC's named surface), one structural
collision (error-code sentinel overlaps a sibling component's claim),
and a cluster of §2.5 orphan surfaces (code present without AC
backing).

Amendment number is **#11** (not #9 — #9 is a drafted-not-built
telegram proposal, #10 is the linux-removal amendment). All findings
close in this single amendment cycle.

**Primary surface:** `memory-system/`. **Secondary surface:**
`hands-off-lifecycle/README.md` only if the error-code-collision fix
requires a README cross-reference update (it will — we relocate the
base-class sentinel into the memory-system runtime block, which
removes the collision the README currently names).

---

## 1. Objective

Remove the audit-named defects without rewriting amendment #8's
shipped contract. Every finding listed below closes in this amendment;
no amendment-#8 AC is weakened. The existing proposal document
(`docs/rebuild/components/memory-system-subscription-routed-llm/proposal.md`)
gets a revision note documenting the flagged-inference #4 resolution
path chosen here; the ACs themselves stand.

---

## 2. Findings in scope (audit numbering preserved)

The in-scope findings and their structural resolution:

### F10 (RED) — AC8 test does not exercise the ingest surface

**Current state:** the test stops at factory construction and asserts
zero OpenAI calls during `make_graphiti(...)`. AC8's text names
*"ingest path"* and *"memory-system's default ingest surface"*. The
test currently misses the ingest call entirely.

**Resolution:** rewrite `test_AC8_ingest_path_issues_no_openai_api_call`
to (a) construct a graphiti with fully-mocked subprocess + embedder +
graph driver, (b) invoke the ingest surface (`graphiti.add_episode`
or `MemoryAPI.ingest`), (c) assert zero OpenAI calls across the whole
ingest. The subprocess layer stays patched so `ClaudePrintLLMClient`
takes every LLM call; the embedder is mocked to avoid network; the
KuzuDriver runs in-memory against `:memory:` so the ingest completes.

**Halt trigger:** if graphiti-core's ingest path cannot be exercised
behind clean mocks without recreating internals (would violate
halt-trigger §scope of the audit-closure task), halt and re-scope F10
to "delete AC8 + BACKLOG the reranker-subscription-routing work".

### F13 — `ClaudePrintClientError.code = -32099` collides with `hands_off_lifecycle_internal`

**Current state:** `hands-off-lifecycle/README.md` claims `-32099` for
its own catch-all ("`hands_off_lifecycle_internal` — inventory-parse
failures, self-retire verification failures, venv-creation failures,
etc."). `ClaudePrintClientError` base class sets `code = -32099` as a
"sentinel that is explicitly NOT the runtime code" (per the test
docstring at `test_AC7`). Structural collision.

**Resolution:** move the base-class sentinel to **`-32119`** — the
last slot of memory-system's own claimed runtime block. Keep it
never-instantiated-in-production by convention (the three concrete
subclasses own `-32110..-32112`; the sentinel on `-32119` is a
"memory-system-catchall-reserved" marker). Update AC7's test to
recognise the new sentinel explicitly: base-class code must be in the
`-32110..-32119` block, must not equal any concrete subclass's code,
and must not equal `-32095` / `-32096` / `-32099` (which are owned by
staging, drain, and hands-off-lifecycle-internal respectively).

**Halt trigger:** if moving the sentinel cascades into more than the
base class plus its test, halt and re-scope to "delete the sentinel
and make `ClaudePrintClientError` abstract with no default `.code`".

### F1 — `make_anthropic_client()` + unused `AnthropicClient` import

**Evidence:** `grep -rn "make_anthropic_client\|AnthropicClient"` across
the entire working tree shows zero callers outside the definition
site itself. The claim in the docstring ("kept for eval scripts") is
not backed by any caller.

**Resolution:** delete `make_anthropic_client` from
`memory-system/src/factory.py`. Delete the
`from graphiti_core.llm_client.anthropic_client import AnthropicClient`
import. Delete the docstring fragment naming "billed AnthropicClient
available on request". Delete the `AnthropicClient` mention in
`claude_print_client.py`'s `_extract_json_object` comment (cosmetic).

### F2 — `_run_sync()` running-loop threadpool fallback has no AC / no test

**Current state:** `_run_sync` has two branches: (a) `asyncio.run`
when no loop is running, (b) run in a worker thread with a fresh loop
when a loop IS running. The (b) branch is only reachable when the
client's `__init__` is called from an already-running event loop.
AC1 does reach (b) in the current wiring, because
`make_graphiti` is async and constructed via `asyncio.run(make_graphiti(...))`
which creates a loop before constructing the client. No AC names the
running-loop pathway.

**Resolution:** refactor the probe invocation so the running-loop
path is eliminated structurally, not by adding a test:

1. Make `make_claude_print_client` in `factory.py` **async**. It
   constructs `ClaudePrintLLMClient(config=..., skip_auth_probe=True)`
   (sync, `__init__` only runs the binary-missing check), then
   `await client.probe_authenticated()` explicitly. This is the
   correct place for async work — the factory is already in async
   context.
2. `make_graphiti` awaits `make_claude_print_client` (instead of
   calling it sync).
3. `ClaudePrintLLMClient.probe_authenticated(self)` is a public async
   method that wraps `_probe_claude_authenticated(binary_path, env)`.
   AC5 (currently `ClaudePrintLLMClient()` sync, expects the probe
   to raise) stays working because the sync path goes through
   `__init__` where `skip_auth_probe=False` still runs the probe
   via `asyncio.run` — no running loop in the AC5 test context.
4. Delete the thread-pool fallback branch in `_run_sync` entirely;
   if a caller tries to run the probe sync from inside a running
   loop, raise `RuntimeError("probe must be awaited in async context;
   call ClaudePrintLLMClient.probe_authenticated() directly")`.

### F3 — `SubscriptionCostTracker` accumulates without a consumer

**Current state:** `SubscriptionCostTracker` records `total_usd`,
`call_count`, `per_call_usd`. AC3 assertions read `total_usd` and
`call_count` in one test. Nothing consumes `per_call_usd`. Flagged-
inference #4 on the proposal ruled "surface via TokenUsageTracker or
custom span attribute"; the ruling is live and unimplemented.

**Resolution:** **wire the tracker to the observability span path.**
Each `_generate_response` call emits a span attribute
`claude.equivalent_cost_usd` on the span already being built for
`memory.ingest` (via `observability.default_emitter`). Since the
span is built by `MemoryAPI.ingest` (the caller) and not by the
LLM client, the cleanest seam is: the client accumulates
`total_usd` and exposes it as a read-only attribute; `MemoryAPI`
reads the delta after each ingest and calls
`span.set_attr("claude.equivalent_cost_usd", delta)`.

This mirrors the existing per-prompt token-delta emission in
`MemoryAPI._record_delta_tokens`. The new attribute is additive and
does not change any AC-backed behaviour.

**Orphan fields:** drop `per_call_usd` (never read anywhere after the
wiring above; we only need the running total + delta). Keep
`total_usd` and `call_count` since both have live readers.

Update proposal §5 #4 ruling text to name the span-attribute seam as
the landed implementation.

**Halt trigger (task-named):** if graphiti-core surfaces don't cleanly
support a span-attribute emission from the caller's scope (they
should — we own `MemoryAPI.ingest`'s span builder), halt and re-scope
F3 to "delete the tracker entirely + update the proposal to drop
ruling #4".

### F4 — unused `logger` + `import logging` in `claude_print_client.py`

**Resolution:** delete both lines.

### F5 — `_ENV_ALLOWED_VARS` 11 entries beyond PATH/HOME with no AC backing

**Current state:** tuple has 13 entries (PATH, HOME, USER, LOGNAME,
SHELL, LANG, LC_ALL, LC_CTYPE, TERM, TMPDIR, XDG_CONFIG_HOME,
XDG_DATA_HOME, XDG_CACHE_HOME). AC2's test asserts PATH is preserved
and the API keys are excluded — nothing more.

**Resolution:** trim to `("PATH", "HOME")`. If `claude -p` later
requires another var (empirical finding, not speculation), add it
with a concrete AC extension naming the runtime failure observed.

### F6 — `DEFAULT_SMALL_MODEL` duplicates `DEFAULT_MODEL` verbatim

**Resolution:** delete `DEFAULT_SMALL_MODEL`. Replace its two use
sites (`config.small_model = DEFAULT_SMALL_MODEL`, default in
`LLMConfig(...)` constructor) with `DEFAULT_MODEL`. No AC names
small-model variance; introducing a distinct constant suggests a
seam that doesn't exist.

### F8 — `_RATE_LIMIT_MARKERS` has 6 markers; AC6 tests exercise 1

**Current state:** 6 markers (`"rate limit"`, `"rate-limit"`,
`"rate_limit"`, `"429"`, `"too many requests"`, `"usage limit"`).
AC6's test uses "Claude usage limit reached — rate limit exceeded"
which matches both `"rate limit"` and `"usage limit"`. The other
markers are speculative.

**Resolution:** trim to `("rate limit", "usage limit")` — the two
substrings actually present in AC6's test fixture. If a real `claude -p`
response surfaces a different phrasing, the empirical signal adds an
AC extension + a new marker together.

### F11 — `_probe_claude_authenticated` has `except json.JSONDecodeError: pass`

**Current state:** the probe defensively re-parses stdout as JSON
looking for an envelope-wrapped "Not logged in" marker. If stdout is
not JSON, the parse raises `JSONDecodeError` and the bare `except ...: pass`
swallows it. No AC names non-JSON probe output as a handled case;
§8 rule 8 forbids silent exception branches.

**Resolution:** remove the secondary JSON-parse-and-re-check block
entirely. The primary check at the top of the function (substring
match on `stdout`/`stderr` for `_UNAUTH_MARKERS`) already handles
both raw-text and envelope-wrapped "Not logged in" responses
(substring match works in both). AC5's two tests both pass via the
primary check (one with raw stdout, one with envelope-wrapped
`{"result":"Not logged in..."}`, still a substring match on the
unparsed JSON). Deleting the secondary block removes the silent
except without losing coverage.

---

## 3. Out of scope

- **F7** (probe sends real LLM call) — AC5 delegates probe strategy
  to the builder; cheaper probe is scope expansion, not defect closure.
- **F12** (AC2 argv exactness) — argv is a subprocess contract
  surface; AC-text discretion. Cosmetic only.
- **F9** (AC7/AC8 tests were missing at original build time) — the
  Step 4 landing work already closed this; only AC8's test SHAPE
  remains wrong (that is F10, in scope).
- **F15** (plan-before-code CDC landed after the original build) —
  compliance-gap-at-time-of-build, not retroactively fixable.
- Amendment #9 (telegram-interface-framework-integration) — separate
  untouched amendment.

---

## 4. Acceptance criteria (this amendment)

- **AC11.1** — AC8's test (`test_AC8_ingest_path_issues_no_openai_api_call`)
  exercises `graphiti.add_episode` (or `MemoryAPI.ingest`) under fully-
  mocked subprocess + embedder + in-memory Kuzu, and asserts zero
  outbound OpenAI calls *across the ingest call*, not just across
  factory construction. The subprocess mock returns valid
  response-model JSON at every call so the ingest path runs to
  completion.
- **AC11.2** — `ClaudePrintClientError.code` sits inside the
  `-32110..-32119` memory-system runtime block. No
  `ClaudePrintClientError`-hierarchy code equals `-32099`. The AC7
  introspection test enforces this on the base class as well as
  subclasses.
- **AC11.3** — `make_anthropic_client` is absent from
  `memory-system/src/factory.py`. The `AnthropicClient` import is
  absent. `grep -n "AnthropicClient\|make_anthropic_client"
  memory-system/src/factory.py` returns nothing.
- **AC11.4** — `_run_sync` has a single branch (`asyncio.run`); the
  running-loop ThreadPoolExecutor branch is absent.
  `make_claude_print_client` is `async` and awaits
  `client.probe_authenticated()`. `make_graphiti` awaits
  `make_claude_print_client`. AC1's test still passes without
  modification to its *assertions* (the `asyncio.run(factory.make_graphiti(...))`
  invocation already awaits correctly).
- **AC11.5** — `SubscriptionCostTracker` has no `per_call_usd` field.
  `MemoryAPI.ingest` writes a `claude.equivalent_cost_usd` span
  attribute whose value is the delta in `cost_tracker.total_usd`
  across the ingest. A new unit test asserts the attribute is
  present on the emitted span when a mocked ingest reports a non-
  zero cost.
- **AC11.6** — `claude_print_client.py` has no `import logging` and
  no module-level `logger = logging.getLogger(__name__)`.
- **AC11.7** — `_ENV_ALLOWED_VARS == ("PATH", "HOME")`. AC2's test
  continues to pass (PATH preserved, API keys excluded).
- **AC11.8** — `DEFAULT_SMALL_MODEL` is absent. All prior use sites
  reference `DEFAULT_MODEL`. `config.small_model` default is
  `DEFAULT_MODEL` at call sites that previously defaulted to
  `DEFAULT_SMALL_MODEL`.
- **AC11.9** — `_RATE_LIMIT_MARKERS == ("rate limit", "usage limit")`.
  AC6's two tests continue to pass.
- **AC11.10** — `_probe_claude_authenticated` has no
  `except json.JSONDecodeError: pass` block. Both AC5 tests still
  pass via the primary substring-match check.
- **AC11.11** — Seal-diff test passes (`test_B20_only_..._surfaces_changed`
  and `test_H19_diff_scope_covers_only_approved_surfaces`); the
  amendment's diff stays under `memory-system/`,
  `hands-off-lifecycle/`,
  `docs/rebuild/components/memory-system-subscription-routed-llm/`,
  `docs/rebuild/plans/`, and (if touched) `data/`.
- **AC11.12** — memory-system suite: 61 existing passes + new tests
  for AC11.1 (rewritten) and AC11.5 (new). Hands-off-lifecycle
  suite: 67 passes unchanged.

---

## 5. Seal plan

1. **BASELINE advance.** Both seal tests' BASELINE constants advance
   from `4ec9ae9` to `77389ce` (the amendment-#8 seal commit — the
   pre-amendment-#11 tip).
2. **Amendment commit:** `fix(memory-system, hands-off-lifecycle):
   amendment-#8 audit closure (amendment #11)`.
3. **Seal commit (separate):** `chore(seals): amendment-#8-audit-closure
   seal — memory-system + hands-off-lifecycle at <sha>`. Advances
   `memory-system/tests/SEAL_COMMIT` and
   `hands-off-lifecycle/tests/SEAL_COMMIT` from `7111602` →
   amendment-#11 code-commit SHA.
4. **Allowed-prefix set** (unchanged from amendment #8): the existing
   prefix tuples already cover `docs/rebuild/plans/` +
   `docs/rebuild/components/memory-system-subscription-routed-llm/`
   + the two component source directories. No new prefixes needed.

---

## 6. Halt triggers

- Scope creep beyond the ten enumerated findings (F1, F2, F3, F4, F5,
  F6, F8, F10, F11, F13).
- F10 requires recreating graphiti-core internals to make
  `add_episode` run under mocks → halt, re-scope to "delete AC8,
  BACKLOG reranker-subscription-routing".
- F3 span-attribute seam is not reachable from `MemoryAPI.ingest`
  without violating a sealed graphiti surface → halt, re-scope to
  "delete tracker + remove proposal ruling #4".
- F13 collision fix cascades beyond base class + its one test → halt,
  re-scope.
- Any unrelated test regression surfaces during the build → halt,
  diagnose before sealing.

---

## 7. Build order

1. Write this plan (done — this file).
2. Edit `memory-system/src/claude_print_client.py` (F1 ref, F2, F3,
   F4, F5, F6, F8, F11, F13).
3. Edit `memory-system/src/factory.py` (F1 body, F2 async
   `make_claude_print_client`).
4. Edit `memory-system/src/memory.py` (F3 span-attribute wiring from
   `MemoryAPI.ingest`).
5. Edit `memory-system/tests/test_claude_print_client.py` (F10
   rewrite of AC8; AC7 updated for base-class sentinel in runtime
   block; AC11.5 new test for span-attribute; remove any test that
   presumed removed constants).
6. Edit `hands-off-lifecycle/README.md` (F13 cross-reference —
   confirm base-class sentinel location).
7. Edit proposal §5 #4 ruling text (F3 — name the landed span
   attribute).
8. Advance BASELINE in both seal tests.
9. Run both test suites; confirm all pass.
10. Amendment commit.
11. Write SEAL_COMMIT sidecars (both) to the new SHA.
12. Seal commit.

---

## 8. ODD compliance check (run at close)

- Every AC listed above is outcome-shaped (asserts a visible invariant,
  not a method).
- Every finding is closed or explicitly accepted with named rationale
  (§2 above covers all ten in-scope findings).
- No new silent except branches introduced.
- No new non-objective code introduced (the span-attribute wiring
  backs a flagged-inference ruling that was already approved).
- Test suites pass across memory-system + hands-off-lifecycle.
