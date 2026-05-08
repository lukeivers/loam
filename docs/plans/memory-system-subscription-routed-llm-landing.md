# memory-system-subscription-routed-llm amendment landing — plan

**Status:** plan (written before any edit lands, per plan-before-code CDC).
**Branch:** `pos-v2` at HEAD `4ec9ae9`.
**Proposal:** `docs/archive/component-research/memory-system-subscription-routed-llm/proposal.md`.
**Deferred-path research (in scope for this amendment per proposal AC9):**
`docs/archive/component-research/memory-system-gliner2-expansion/research.md`.

---

## 1. Objective

Land the in-flight memory-system-subscription-routed-llm amendment (#8)
that an earlier background agent built but never committed. The build
output is sitting on disk as a mix of modified tracked files and
untracked files; the ACs in the proposal are all met or minor test gaps
are fillable. Close the amendment cycle with the standard two-commit
shape: amendment code commit, then seal commit.

## 2. Pre-commit adjustments required

The on-disk BASELINE/seal math is stale. Between when Blocker-3 was
authored (against tip `9aeabd4`) and now (tip `4ec9ae9`), the following
landed: `fd8c833`, `63e900b`, `7d462e3`, `9373444`, `ddf0d7c`,
`c4df239`, `4ec9ae9`. The amendment's seal-enforcement needs the
current-tip-as-pre-amendment-tip, not the stale `9aeabd4`.

Two concrete fixes:

1. `memory-system/tests/test_no_sealed_amendments.py` — BASELINE must
   advance from `9aeabd4` → `4ec9ae9`. Comment history updated in
   lockstep.
2. `hands-off-lifecycle/tests/test_cross_cutting.py` — BASELINE must
   advance from `7d462e3` → `4ec9ae9`. The proposal's seal-plan §6
   step 2 names this advance; amendment #10 reverted the earlier
   Blocker-3 draft of this hunk during hunk-staging, so it needs
   re-authoring here.
3. `memory-system/tests/SEAL_COMMIT` sidecar currently holds the
   stale `9aeabd4`. Set to `4ec9ae9` during the code commit (matching
   BASELINE so the diff is trivially empty and the seal-diff test
   passes); the seal commit bumps it to the amendment code-commit SHA.

## 3. Missing tests (ODD 1:1 AC-to-test gap)

The build-time test file exercises AC1-AC6 but is missing explicit
tests for AC7 and AC8 named in the proposal §3 + §4 behaviour table.
Both need adding before the code commit so the proposal's behaviour-
count invariant holds.

- **AC7 — error-code-block discipline.** Introspect
  `ClaudePrintClientError` and every subclass defined in
  `claude_print_client.py`; assert `.code` satisfies
  `-32119 <= code <= -32110` for every non-base class. The base class's
  `-32099` sentinel is accepted as "unused base" via a typed-exclude.
  No subclass `.code` collides with any existing staging/drain code
  (`-32095`, `-32096`).
- **AC8 — reranker does not invoke billed OpenAI path at ingest.**
  Instantiate the default `Graphiti` via `factory.make_graphiti()`
  with all subprocess paths mocked; patch the `openai` module's
  primary request seam at module boundary; assert zero calls issued
  during a minimal ingest. Uses `OPENAI_API_KEY=ollama` placeholder
  per the proposal AC8 phrasing so the OpenAIRerankerClient
  constructs. Follow-up amendment handles full subscription-routing
  of the reranker.

## 4. Seal plan (proposal §6 as-authored)

1. Code commit message:
   `fix(memory-system, hands-off-lifecycle): memory-system-subscription-routed-llm amendment (#8)`
   — includes factory edits, new `claude_print_client.py`, new
   `test_claude_print_client.py`, new memory-system
   `test_no_sealed_amendments.py` (with BASELINE=`4ec9ae9`),
   hands-off-lifecycle README cross-reference + test_cross_cutting
   BASELINE advance, `process_of_arrival.py` docstring refresh,
   the proposal and preserved-research docs.
2. Seal commit (separate):
   `chore(seals): memory-system-subscription-routed-llm seal — memory-system + hands-off-lifecycle at <CODE_SHA>`.
   Advances:
   - `memory-system/tests/SEAL_COMMIT`: `4ec9ae9` → `<CODE_SHA>`.
   - `hands-off-lifecycle/tests/SEAL_COMMIT`: `9373444` → `<CODE_SHA>`.
   - Appends amendment-cycle note (this amendment's summary) to
     `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`.

## 5. Out of scope

- `docs/archive/component-research/telegram-interface-framework-integration/`
  — that is Blocker-4 material (amendment #9). Its untracked tree is
  left entirely alone.
- `data/observability/spans.jsonl` — runtime churn; never belongs in
  an amendment commit.
- Full subscription-routing of the reranker (AC8 only pins the
  invariant; replacement client is a separate follow-up amendment).
- GLiNER2 local-CPU entity extraction — preserved as research under
  `docs/archive/component-research/memory-system-gliner2-expansion/research.md`
  for a future amendment if quality pressure warrants it.

## 6. Halt triggers

- Memory-system test suite (`memory-system/.venv/bin/pytest`) regresses
  post-code-commit on any component outside this amendment's touched
  files.
- Seal-diff tests for any touched sealed component fail post-seal-commit.
- A conflict surfaces between Blocker-3's `hands-off-lifecycle/README.md`
  error-block addition and amendment #10's README scrub in a different
  region. (Expected to compose; verify before commit.)
- Untracked telegram-interface-framework-integration files appear in
  either the code commit's `git status` staging set or the seal commit's.

## 7. ODD compliance check (runs before final report)

- Proposal's AC count (9) matches test count 1:1 post-gap-fill.
- No method-in-acceptance: every AC names an outcome (test assertion),
  not an implementation step.
- No silent exception branches beyond what the proposal declares — the
  `_probe_claude_authenticated` JSONDecodeError pass-through is the
  only tolerant path and is proposal-declared.
- No non-objective code: no Linux branches in the new client, no stray
  dependencies beyond the `claude` CLI binary (already required by the
  user's Claude Code environment).
