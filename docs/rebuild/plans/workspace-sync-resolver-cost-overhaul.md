# workspace-sync — resolver cost overhaul (Bundle α: ancestor-detection + classifier+verifier merge + bare subprocess) — plan

**Sealed-component amendment** extending the existing `workspace-sync/`
component (sealed at #56, `0607dc7`). Carries a `pos-amend` manifest
(sketch in §9; builder finalises at
`docs/rebuild/plans/workspace-sync-resolver-cost-overhaul.manifest.yaml`),
bumps `workspace-sync/tests/SEAL_COMMIT` per the seal-automation
extension, lands a deterministic seal commit. Plan-before-code per the
dev CDC. Per amendment #46 / #47 / #54 / #56 precedent; the
dev-discipline plan template was used for the §14 + §15 skeleton per
#51 (the template's "NOT a sealed-component amendment" lede is
overridden in this paragraph — the §-skeleton is the piece of the
template needed; the sealed-component build dispatch wraps this
plan-doc rather than replicating its §§).

**Status:** plan (pre-dispatch). 2026-04-26 (plan-author run; live-test synthesis dated 2026-04-27).
**Working directory:** /Users/lukeivers/ivers-corp-pos-v2/
**Companions:** - **#56 plan-doc:** `docs/rebuild/plans/workspace-sync.md`
  (1377 lines including §14 method-decision register; the
  keystone plan whose resolver subsystem this amendment
  extends).
- **#56 builder-plan:** `docs/rebuild/plans/workspace-sync.builder-plan.md`
  (731 lines; D-build.0 through D-build.13 method
  decisions captured).
- **Milestone live-test synthesis:**
  `/Users/lukeivers/pos3/.scratch/claude-output/milestone-live-test-2026-04-27.md`
  (the 46-conflict audit + 2 successful 0.88-confidence
  verdicts + halt-on-timeout — primary motivation for
  bundle α).
- **FUTURE_IDEAS Idea 20:**
  `docs/rebuild/FUTURE_IDEAS.md` lines 683-710 (the
  LLM-as-classifier+verifier meta-pattern; bundle α.2
  is the first manifestation).
- **FUTURE_IDEAS_DRAFT workspace-sync follow-on
  family:** `docs/rebuild/FUTURE_IDEAS_DRAFT.md` lines
  14-31 (the bundle α scope + bundle β captures + OO
  subsumption note).
- **Salvage source for α.3:**
  `workspace-sync/src/workspace_sync/_resolver_client.py`
  (242 lines; the `_ClaudePrintResolverClient` whose
  subprocess invocation gains the `--bare` opt-in).
- **α.1 attach point:**
  `workspace-sync/src/workspace_sync/conflict_detection.py`
  (250 lines; the existing detect_b_shape_conflicts
  function).
- **α.2 attach point:**
  `workspace-sync/src/workspace_sync/merge_helper.py`
  (339 lines; the existing resolve_inferred_conflicts
  helper's Class-C branch at lines ~185-234).
- **Spec anchors:**
  `docs/rebuild/spec/pos-v2-objectives-spec.md` line 81
  (v1.0 self-upgrade objective), line 114 (Gap-3
  + clause-g + workspace-customisation conflict
  surfacing).
- **ODD references:** `docs/odd-methodology.md` §2.5 (no
  non-objective code), §5.3 (Pydantic + model_validators
  as reach-for default), §10 (per-invariant BASELINE
  convention). `docs/odd-in-pos.md` §4 (clause-g pattern
  as canonical example).
- **Amendment precedents:** amendment #56 (workspace-sync
  seal — direct parent), amendment #54 (BB clause-(h)
  seal — original primitives donor), amendment #46/#47
  (single-sealed-component manifest + plan-doc shape with
  §14 method-decision register).

**Ancestor record:** - **#56 seal commit (parent):** `0607dc7` — workspace-sync
  sealed; all 62 tests green; 12 outcome-shaped ACs +
  seal-diff invariant. Bundle α extends the resolver
  subsystem #56 introduced.
- **Milestone live-test 2026-04-27:** `pos-sync` against
  pos3 halted at conflict 3 of 46 on 120s timeout
  (`FUTURE_IDEAS_DRAFT.md` merge generation); 2 verdicts
  produced before halt (`.claude/settings.json`,
  `.gitignore`) at 0.88 confidence each. Pos3 untouched
  (fail-closed honored). The synthesis's findings 1-4
  are the direct motivation for bundle α + bundle β.
- **FUTURE_IDEAS Idea 20 graduation 2026-04-27:** the
  LLM-as-classifier+verifier meta-pattern lifted from
  the live-test halt; bundle α.2 is the first
  manifestation in pos-v2 source.
- **#54 (BB clause-(h)) seal `1fd826a`:** original donor
  of the resolver primitives (MergeResolver, MergeVerdict,
  ResolverBudget, BudgetExhausted, ResolverFailure,
  build_prompt). Bundle α extends MergeVerdict's siblings
  (new MergeClassification + MergeVerification models)
  rather than amending the existing model.
- **Owner reframing 2026-04-26:** Architecture B
  (per-workspace embedded framework) is the locked
  workspace-pull mechanism; bundle α composes under it.
  No structural-architecture decisions surface in α.

**Research:** 

---

## 1. Summary / TLDR

Follow-on amendment to **#56** (workspace-sync, sealed at
`0607dc7`). The milestone live-test against pos3 (2026-04-27)
validated structural promises — fail-closed, audit, state,
Class-A protection — but **halted on a `claude -p` 120s
subprocess timeout at conflict 3 of 46**. The 2 verdicts
produced before the halt were sharp (0.88 confidence,
amendment-aware reasoning); the failure was cost, not
correctness.

Bundle α attacks resolver cost from three independent angles
in one amendment, each compositional with the others:

1. **α.1 — Content-vs-canonical-history ancestor detection.**
   Before invoking the resolver, walk canonical's git history
   looking for an ancestor commit whose blob for the conflicted
   path matches the workspace's content (sha256 or
   byte-identical). When found, fast-path resolve as
   `inferred-accept-canonical` — the workspace didn't diverge,
   it's just behind. For pos3's 46 conflicts, ~90%+ are
   stale-but-unedited framework drift the resolver would skip
   entirely. Reduces first-sync cost from O(diverged-files ×
   LLM) to O(diverged-files × git-rev-walk).

2. **α.2 — Deterministic-merge-with-LLM-verify-gate.**
   Replaces the current LLM-as-generator path
   (full-file output, ~5-7k output tokens, 60-120s wall time
   — the timeout that halted the milestone test on
   `FUTURE_IDEAS_DRAFT.md`) with a four-step
   classifier+deterministic+verifier shape:
   **(a) classify** — small LLM call (~50 token output)
   tags the file's structural class (append-only-list / log /
   tracker-table / free-prose / unknown);
   **(b) deterministic merge** — the matching primitive
   (concatenate-post-divergence-suffixes + dedupe-by-stem for
   markdown lists; structurally-equivalent for log + tracker
   classes) does the merge in ~0.01s, free, audit-grade
   reproducible;
   **(c) verify** — small LLM call (~200 token output)
   reads the deterministic result against both inputs and
   answers "did the merge lose meaning, drop entries, or
   materially alter intent?";
   **(d) apply or fall back** — verify passes → accept;
   verify fails → fall back to today's full-LLM-generator
   path (preserves correctness ceiling).
   Generalises to FUTURE_IDEAS Idea 20.

3. **α.3 — `claude --bare` subprocess flag** (HALT-FOUND;
   see §13). Initially scoped as a one-line change to
   skip hooks/LSP/plugin-sync/auto-memory/keychain-reads/
   CLAUDE.md-auto-discovery (5-20s cold-start savings per
   call). **Plan-author audit found the flag is auth-incompatible
   with the current resolver design**: `--bare` requires
   `ANTHROPIC_API_KEY` or `apiKeyHelper`; OAuth + keychain
   are never read. The current resolver's env-scrubber
   **explicitly drops `ANTHROPIC_API_KEY`** to force the
   Claude Max OAuth path. Owner-ruling-needed (D-3) on the
   auth-shape change required to land α.3.

**Subsumes the previous OO follow-on** (resolver-client
timeout config + 120→300s default — irrelevant if α.1
drops 90%+ of calls and α.2 drops per-call wall-time
3-8×).

This is dev-discipline scope: **one** sealed component
(`workspace-sync/`), no edits to `self-upgrade/` or
`tools/upgrade-merge-resolver/` (Hard Constraint #1).


---

## 2. Spec-objective placement (per CLAUDE.md §2.5 framing)

Composes under **v1.0 self-upgrade objective** (spec line 81)
and **Gap-3 acceptance line 114** without adding a new top-level
objective. Bundle α is a cost + reliability refinement of the
same workspace-sync mechanism #56 sealed; spec line 81's
*"upgrade its own framework components without meaningfully
disrupting the user's running configuration"* is unchanged. The
Gap-3 clause-(g) "no silent skip" + "conflict surfaced with
explicit resolution options" property continues to hold —
α.1's fast-path emits `inferred-accept-canonical` (an explicit
resolution recorded in the audit, not a skip); α.2's
classifier+verifier shape emits `inferred-merged` with verifier
attestation (an explicit resolution); α.3's subprocess flag
changes only the LLM call's runtime properties, not its
contract.

**Reverse trace per CLAUDE.md §2.5.** Every AC below traces
back to spec line 81 + line 114 + maps forward to AC.PO.1
(translation-burden) and/or AC.PO.2 (toolkit-primitive growth):

- **AC.PO.1 (translation-burden):** Reduces the cost+latency
  cost the persona has to translate around. Today the persona
  translating "pull canonical into pos3" must surface
  "expected cost ~46 × 60s = ~45min wall-time, may halt on
  timeout"; with α.1 the same translation surfaces
  "expected cost ~5 × 30s = ~2.5min wall-time, ~41 conflicts
  auto-resolved as just-behind." With α.2 the per-call
  wall-time drops from 60-120s to 10-30s. The persona
  invokes the same one verb (`pos-sync`) but the
  translation-burden of explaining the cost shrinks by an
  order of magnitude. The user never learns the
  ancestor-detection mechanism, the file-class taxonomy, or
  the verifier rubric.
- **AC.PO.2 (toolkit-primitive):** Bundle α adds three
  primitives the persona composes against:
  1. **Ancestor-detection helper** — a reusable git-rev-walk
     primitive that answers "is workspace content an ancestor
     of canonical?" for any workspace/canonical pair. Future
     tooling (workspace-state diagnostic, freshness reports,
     multi-workspace sync) composes against the same shape.
  2. **Classifier+deterministic+verifier scope** — a
     budgeted call shape that bookends a deterministic
     primitive with two small LLM calls. Future plans
     (memory-system supersession inference, plan-doc semantic
     compare, persona-contract merge, test-coverage
     generation, doc summarisation) compose against this
     shape per FUTURE_IDEAS Idea 20.
  3. **File-class taxonomy + matching primitives** — the
     enum (`append-only-list / log / tracker-table /
     free-prose / unknown`) plus its deterministic merge
     primitives. Future authoring tools (the dispatch-template
     memory-doc family, plan-doc append-only sections)
     compose against the same taxonomy.

**No new top-level objective is required.** Bundle α is a
performance + reliability refinement of an already-objective-
bound mechanism. Halt trigger 1 evaluated; does not fire.


---

## 3. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

Composes on Claude-native primitives without inventing new ones:

1. **Git as the ancestor-detection substrate (α.1).** The
   mechanism is `git rev-list <canonical-HEAD>` walked
   ancestor-by-ancestor with `git show <commit>:<path>`
   comparison; no new diff machinery, no `dulwich`, no
   in-Python Merkle walk. Composes on Hard Constraint #2
   from #56 (stdlib + Pydantic + PyYAML + git binary only).
2. **Claude SDK structured-output for both classify + verify
   (α.2).** The classifier returns a Pydantic-typed
   `MergeClassification` with a `Literal[...]` class field;
   the verifier returns a Pydantic-typed
   `MergeVerification` with a `passed: bool` + free-text
   concerns. Same structured-output surface the existing
   `MergeVerdict` uses; same `claude -p --output-format json`
   subprocess; same `_ClaudePrintResolverClient` contract.
   **Halt trigger 5 (LLM-call surface that doesn't exist) does
   not fire** — bundle α composes on the existing wired
   surface.
3. **`claude --bare` subprocess mode (α.3).** A
   Claude-native primitive that already exists in the
   installed binary (verified `claude --help` output:
   "Minimal mode: skip hooks, LSP, plugin sync,
   attribution, auto-memory, background prefetches,
   keychain reads, and CLAUDE.md auto-discovery"). pos-v2
   composes on it rather than re-implementing each
   skip individually. **Caveat surfaced in §13:** `--bare`
   is auth-incompatible with the current resolver's
   OAuth-via-keychain path; D-3 (§11) routes the
   resolution.
4. **Cost-governance budgeted scope.** All three new LLM
   calls (classify, verify, fall-back-generator) run inside
   the existing `MergeResolver.resolve()` budget tracking;
   ancestor-detection emits zero LLM calls. The
   `cumulative_used` counter integrates additively across
   classify (~50 tok) + verify (~200 tok) per Class-C
   conflict — far below the per-conflict 5k budget and
   dramatically below the cumulative 100k ceiling.
5. **Observability-aggregator OTel spans.** Three new spans
   compose under the existing `pos.sync.merge_gate.*`
   namespace: `pos.sync.merge_gate.ancestor_check`,
   `pos.sync.merge_gate.classify`,
   `pos.sync.merge_gate.verify`. Same exporter, same
   attribute schema; observability-aggregator picks them up
   for free.

### Lens 2 — Harness + primary-persona value

**Primary-persona test.** Reduces translation burden: the
persona translating "pull the latest canonical into this
workspace" no longer has to mediate a 30-45-minute wall-time
expectation with a non-trivial halt-on-timeout failure mode.
Post-α, the same translation surfaces "expected ~3-5
minutes; ancestor-detection skips ~90% of conflicts; halt
is unlikely; verifier-fail surfaces low-confidence merges
for review." The persona also gains the
`pos.sync.merge_gate.ancestor_check` audit span as a
primitive to answer "what was just-behind vs genuinely
diverged?" without re-running the sync. **Pass.**

**Harness test.** Three primitives added to the persona's
toolkit (ancestor-detection helper, classifier+verifier scope,
file-class taxonomy — listed in §2 above). Each is invocable
by the persona; the audit fields they emit live under stable
workspace-local paths the persona reads on demand. **Pass.**

Per AC trace:
- **AC.WSα.1 → AC.PO.1 + AC.PO.2.** Ancestor-detection
  fast-path absorbs the `inferred-accept-canonical` decision
  for stale-but-unedited files into a free local primitive.
  The audit field `ancestor_match_sha` is a toolkit primitive
  future callers compose against.
- **AC.WSα.2 → AC.PO.2.** Per-conflict cache means
  re-runs against the same workspace state are byte-cheap
  (no re-walk).
- **AC.WSα.3 → AC.PO.1 + AC.PO.2.** File-class
  classification is a primitive — future authoring tools
  consume the taxonomy.
- **AC.WSα.4 → AC.PO.2.** Deterministic merge primitives
  are reproducible audit-grade transformations the persona
  can replay or explain.
- **AC.WSα.5 → AC.PO.1.** Verifier-pass acceptance is the
  correctness floor — the persona never has to mediate a
  "did the merge lose meaning?" review for the auto-applied
  verdicts.
- **AC.WSα.6 → AC.PO.1.** Verifier-fail fall-back to the
  full LLM-generator path preserves the existing
  correctness ceiling — a Class-C conflict that defeats the
  deterministic merge still lands a verdict.
- **AC.WSα.7 → AC.PO.2.** OTel spans for each new step
  extend the existing observability primitive.
- **AC.WSα.8 → AC.PO.1.** `claude --bare` cold-start
  elimination shrinks the wall-time the persona has to
  mediate (subject to D-3 auth resolution).
- **AC.WSα.S → AC.PO.2.** Seal-diff invariant —
  workspace-sync's component fence stays exact, the
  surrounding seal commitments stay intact.

### Lens 3 — ODD authoring

ACs §4 are outcome-shaped: each names a state of the world the
amendment must make true, with deterministic test shape. No
method-in-AC (no "uses Pydantic", no "calls
ClaudeAdapter", no "implements Protocol X"). Method choices
(the file-class enum's exact members; the classifier's
prompt text; the verifier's rubric phrasing; whether
per-conflict cache lives in `state.yaml` or a sibling cache
file; whether the ancestor-walk uses `git log --follow`
vs unfollowed) are the builder's call inside §9.x's
bookkeeping notes; the AC tests outcome only.

Behaviour-count check applied in §5. ODD §2.5 reverse trace
is the builder's pre-seal check captured in the
builder-plan (one row per code path → AC).

Halt-and-surface triggers per §10; explicit per
`feedback_subagent_odd_violation_halt`.


---

## 4. Acceptance criteria (AC.WSα — sealed-component amendment)

Eight outcome-shaped acceptance criteria, plus the seal-diff
invariant. Each carries the deterministic test shape; method
is the builder's call.

**AC.WSα.1 — Ancestor-detection fast-path.** When a workspace
file's content matches the blob recorded for the same path at
some ancestor commit reachable from the canonical ref's
HEAD (sha256 equivalence; file content; not metadata), the
conflict resolves as `Resolution.INFERRED_ACCEPT_CANONICAL`
with `confidence: 1.0` and a rationale naming the matched
ancestor commit's short SHA. The resolver is NOT invoked
for that conflict (no LLM call, no token cost). Verified by
a fixture in which a workspace file equals canonical's
blob from `HEAD~3`; the audit records
`resolution: inferred-accept-canonical`,
`rationale: "workspace content matches canonical ancestor
abc1234"`, `confidence: 1.0`, and `ancestor_match_sha:
"abc1234..."` (full SHA in the audit field). No
`resolver.cumulative_used` increment for that path.

**AC.WSα.2 — Ancestor-walk bounded + cached.** The walk
terminates at a configurable depth cap (D-1 below; default
recommendation surfaced for owner ruling); when no ancestor
match is found within the cap, fast-path declines and the
Class-C resolver path runs as today. A per-conflict cache
records `(path, workspace_sha) → ancestor_match_sha | None`
so re-runs against the same workspace state on the same
canonical ref do NOT re-walk. Verified by a fixture: first
invocation walks to depth N; second invocation against
unchanged state hits the cache (zero `git rev-list` /
`git show` calls).

**AC.WSα.3 — Class-C classifier returns a typed
classification.** When ancestor-detection declines and the
file is Class C, the resolver invokes a structured
classify-call before any merge. The call returns a
Pydantic-validated `MergeClassification` with a
`Literal[...]` field naming the file's structural class
(the exact set is the builder's call within §9; the AC
requires AT LEAST: append-only-list, log, tracker-table,
free-prose, unknown). The classify-call output is bounded
to ≤200 tokens of output. Verified by a fixture per class
(markdown bullet list → append-only-list; ndjson →
log; pipe-table → tracker-table; prose → free-prose;
binary-but-text → unknown).

**AC.WSα.4 — Deterministic merge primitive applied per
class.** When the classifier returns a non-`unknown`
class, a deterministic primitive matching that class
produces the merged content WITHOUT an LLM call. The
primitive is pure, reproducible (running it twice on the
same inputs produces byte-identical output), and emits a
structured trace recording the inputs' SHA + the operation
applied. Verified by a fixture per class plus a property
test (random-input idempotency: applying the merge twice
is identical to applying once). When the classifier
returns `unknown`, the deterministic primitive is NOT
invoked and the resolver falls through to AC.WSα.6
fall-back.

**AC.WSα.5 — Verifier-pass acceptance.** After the
deterministic merge produces candidate merged content,
a structured verify-call runs against
`(canonical_text, workspace_text, candidate_merged_text)`
and returns a Pydantic-validated `MergeVerification`
with at least: `passed: bool`, `concerns: str | None`,
`confidence: float`. When `passed: true`, the resolver
emits a `MergeVerdict` with
`resolution: inferred-merged`,
`merged_content: <candidate>`,
`rationale: <verifier output>`,
`confidence: <verifier confidence>`. The audit records
the deterministic primitive used + the verifier
attestation. Verifier output is bounded to ≤500 tokens.
Verified by a fixture: known-good deterministic merge
passes; emitted verdict matches the candidate; audit
records both the primitive trace and the verifier
attestation.

**AC.WSα.6 — Verifier-fail fall-back.** When the
verifier returns `passed: false` (OR the classifier
returns `unknown` OR the deterministic primitive raises
an exception), the resolver falls back to the existing
LLM-as-generator path (today's `MergeResolver.resolve`
call producing a full-file `merged_content`). The
audit records `fallback_reason: <one of:
classifier-unknown / primitive-failed /
verifier-rejected>` plus the resulting verdict. This
preserves the correctness ceiling: every conflict the
generator path could resolve today still resolves
post-α. Fail-closed semantics from #56's AC.WS.12
carry over: a fall-back generator failure halts the
sync. Verified by a fixture: stub verifier returns
`passed: false`; the resolver invokes the
generator path; the verdict matches the stub
generator's output; audit records the fall-back reason.

**AC.WSα.7 — Observability spans for each new step.**
Each new resolver step emits an OTel span under the
existing `pos.sync.merge_gate.*` namespace: at least
`pos.sync.merge_gate.ancestor_check` (one per
conflict, attribute `matched: bool` +
`ancestor_sha: str | null` + `walk_depth: int`),
`pos.sync.merge_gate.classify` (one per Class-C
conflict that reaches the classify step, attribute
`class: str` + `tokens: int`),
`pos.sync.merge_gate.verify` (one per verify call,
attribute `passed: bool` + `tokens: int`). All
attributes namespaced `pos.sync.merge_gate.*`.
Verified by an in-process OTel exporter fixture.

**AC.WSα.8 — MCP-isolated subprocess (auth-OAuth-compatible).**
**REDESIGNED 2026-04-27 in response to owner clarification + empirical experiment** (was: "subprocess invocation flag composition" gated on `--bare` + ANTHROPIC_API_KEY restoration — auth-incompatible with Claude Max OAuth users; original purpose was timing-only, missed MCP-isolation purpose). The `claude -p` subprocess invocation in `_resolver_client.py` MUST run with **MCP isolation** so the subprocess does not load the parent session's MCP servers (preventing bun-process contention with the parent's telegram MCP, memory-graphiti MCP, etc.). Implementation: invoke as `claude --strict-mcp-config --mcp-config <empty-mcp-config-path> -p ...` where the empty-mcp-config file contains `{"mcpServers": {}}`. The `_ClaudePrintResolverClient.__init__` writes the empty-mcp-config to a stable path (e.g., `<workspace>/.pos/sync/empty-mcp.json` or a tempfile cached for the resolver lifetime) once, then every subsequent `claude -p` call references it via `--mcp-config <path>`. Auth-shape: the existing OAuth/Claude-Max path is preserved (no env-scrubber changes; no `ANTHROPIC_API_KEY` requirement). Verified empirically 2026-04-27: `claude --strict-mcp-config --mcp-config /tmp/empty-mcp.json -p --no-session-persistence --output-format json --model claude-haiku-4-5 "Reply with just OK"` returned valid result in 2.3s under Claude Max OAuth without `ANTHROPIC_API_KEY` set. Verified by a unit test asserting argv shape (presence of `--strict-mcp-config` + `--mcp-config <path>` flags + the path file contains `mcpServers: {}`) + an integration test that runs one end-to-end resolve call and asserts no MCP-related processes are spawned by the subprocess.

**AC.WSα.S — Seal-diff invariant.** Diff between
BASELINE and SEAL_COMMIT is confined to
`workspace-sync/` plus amendment-universal admissions
(`docs/rebuild/plans/`, `CLAUDE.md` if needed,
`docs/rebuild/FUTURE_IDEAS.md` if needed,
`docs/odd-*.md` if needed). Verified by
`workspace-sync/tests/test_no_sealed_amendments.py`
and the cross-component sweep at seal-time.
Specifically: zero edits to `self-upgrade/`,
`tools/upgrade-merge-resolver/`, or any other sealed
component (Hard Constraint #1).


---

## 5. Behaviour-count check (ODD §3.3 forward; applied as dev-discipline check)

Eight declared behaviours; eight outcome-shaped ACs; one
seal-invariant. Match.

| # | Declared behaviour | AC |
|---|--------------------|-----|
| 1 | Workspace content matching canonical ancestor → fast-path inferred-accept-canonical | AC.WSα.1 |
| 2 | Ancestor walk bounded + per-conflict cache | AC.WSα.2 |
| 3 | Classifier returns typed file-class | AC.WSα.3 |
| 4 | Deterministic merge primitive per class | AC.WSα.4 |
| 5 | Verifier-pass acceptance | AC.WSα.5 |
| 6 | Verifier-fail / classifier-unknown / primitive-fail fall-back to full LLM-generator | AC.WSα.6 |
| 7 | OTel spans for ancestor-check + classify + verify | AC.WSα.7 |
| 8 | Subprocess --bare flag composition (auth-compatible) | AC.WSα.8 |
| S | Seal-diff invariant: only `workspace-sync/` + universal paths | AC.WSα.S |

Forward direction (every behaviour → AC) verified above.
Reverse direction (every code path / branch / dependency →
AC) is the builder's pre-seal check captured in the
builder-plan §5 (per amendment #46/#47/#56 precedent).


---

## 6. Hard constraints

1. **Sealed-component fence: `workspace-sync/` only** (plus
   universal-paths admissions). **No edits to `self-upgrade/`**
   (Hard Constraint #1 from dispatch — binding). **No edits
   to `tools/upgrade-merge-resolver/`** (dispatch carve-out).
   The salvage source for α.3 (`_resolver_client.py`)
   is owned by workspace-sync — edits to that file are
   in-fence. Any source-edit OUTSIDE `workspace-sync/`
   triggers halt-and-surface (§10 trigger 4).
2. **No new third-party runtime dependency.** The
   ancestor-detection mechanism uses the `git` binary
   (already a runtime dep of #56's
   `conflict_detection.py`). The classifier + verifier use
   the existing `claude -p` subprocess via
   `_ClaudePrintResolverClient`. No `dulwich`, no
   `gitpython`, no `pydulwich`. Existing deps unchanged:
   pydantic + PyYAML + opentelemetry.
3. **No `--amend`.** Corrective new commits only per
   `feedback_no_amend_in_agent_dispatches`.
4. **Plan-before-code.** This plan exists; the builder
   authors a builder-plan at
   `docs/rebuild/plans/workspace-sync-resolver-cost-overhaul.builder-plan.md`
   before editing any source.
5. **Backward-compat preserved unconditionally.** A
   `pos-sync --canonical <path>` invocation on a workspace
   where ancestor-detection finds no match and the
   verifier rejects every classified merge produces a
   RESULT byte-identical to #56's pre-amendment behaviour
   (full LLM-generator path runs; verdicts land per
   AC.WS.4). Bundle α additions are pure refinements:
   they add fast-paths and verify-gates; they never
   remove a path the existing resolver could reach.
6. **Workspace data loss remains structurally impossible.**
   Class-A protection from #56 (Pydantic-validated
   `sync-protected.yaml` framework-floor) carries over
   unchanged. Bundle α touches only the Class-C resolver
   path; Class-A and Class-B resolution are untouched.
   The new classifier's `Literal[...]` enum does NOT
   contain any value that authorises overwrite of a
   Class-A path (Class-A paths are pre-resolved at
   detection time per #56's `conflict_detection.py`,
   never reaching the resolver).
7. **Fail-closed preserved.** When any α.2 step (classify,
   deterministic merge, verify) raises, the resolver
   falls back to the LLM-generator path; if the
   generator path raises, the helper raises
   `ResolverFailure` per #56's AC.WS.12. The framework
   MUST NOT silently treat α.2 step failures as
   accept-canonical or accept-workspace.
8. **Verifier rubber-stamp prevention (binding).** The
   verifier prompt MUST structurally exclude the
   pathological case where (a) the classifier mis-tags
   a file as `free-prose` (or any other class), (b) the
   deterministic primitive applies the matching merge
   incorrectly because the file's true structure differs,
   and (c) the verifier rubber-stamps the result. The
   mitigation: the verifier inputs include the
   classifier's class as a NAMED INPUT (so the verifier
   reads "the candidate was produced by the
   append-only-list primitive" alongside the inputs
   and the candidate); the verifier rubric explicitly
   asks "is this file actually structurally a
   {class}?" as the FIRST verification step; a
   `class_mismatch` concern in the verifier output
   forces `passed: false`. Builder authors the prompt
   in §9; halt-trigger 6 fires if the structural
   exclusion cannot be authored (the verifier's
   correctness becomes load-bearing on the
   classifier's correctness). See §10 trigger 6 for
   halt details.
9. **CDC adherence.** scope-only-dispatch CDC (the
   dispatch carries objective + scope + halt + ODD-check;
   the builder authors method in the builder-plan).
   Standard pos-amend manifest discipline. `pos-amend
   seal --plan-doc <abs-path>` backfills §14.
10. **No top-level objective added.** Composition under
    v1.0 self-upgrade objective + Gap-3 acceptance per §2.
    If the build surfaces a hard need for a new top-level
    objective, halt-and-surface (§10 trigger 1) — do NOT
    silently promote.
11. **Subsumes OO** (resolver-client timeout config +
    120→300s default). OO is REMOVED from the follow-on
    backlog by this amendment. The resolver subprocess
    timeout remains 120s in #56's source (no change here);
    α.1 + α.2 reduce per-call wall-time below the
    timeout, eliminating the OO motivation. **D-4 (§11)
    surfaces the question "should OO be retained as a
    fallback config knob?" for owner ruling.**


---

## 7. Out of scope (explicit)

Per ODD §2.5 and the dispatch's locked scope:

- **Edits to `self-upgrade/`.** Hard Constraint #1; binding.
  Self-upgrade's clause-(h) is canonical-only A-mode and
  its resolver path is independent of workspace-sync.
- **Edits to `tools/upgrade-merge-resolver/`.** Hard
  Constraint #1 carve-out. Salvage to workspace-sync's
  `_resolver_client.py` is the only path; the upstream
  package stays frozen.
- **Multi-conflict batched LLM call.** Each conflict still
  gets its own resolver invocation (per #56 D-AA-5). A
  future amendment may batch low-confidence-only into one
  call. Out of scope here.
- **Resolver model selection / cost-tier tuning.** The
  resolver continues to use `claude-haiku-4-5` (the
  default in `_resolver_client.py`). Per-conflict model
  choice based on file size or class is a future tuning
  amendment. Per-call configuration via the existing
  `~/.pos/sync-config.yaml` is unchanged.
- **`pos-sync --dry-run` UX bug fix.** Captured in
  FUTURE_IDEAS_DRAFT (workspace-sync follow-on family);
  not in α.
- **β bundle (ergonomics — KK/LL/MM/PP).** Separate amendment
  family; α is cost-only.
- **`--auto-accept` confidence-floor calibration.** Captured
  as PP in β bundle. Out of scope here.
- **Background-scope mode.** Foreground `pos-sync` per
  #56; future composition.
- **Telegram-channel surfacing of audit summaries.**
  Persona's call, not this amendment.
- **Storage of ancestor-detection cache across machines.**
  Cache is workspace-local (per-workspace
  `<workspace>/.pos/sync/<ref>/ancestor-cache.yaml`
  or equivalent — exact location is the builder's call
  in §9 within D-1's caching-strategy decision).


---

## 8. Implementation order (suggested — builder's call to refine)

Suggested order — builder's call to refine in the builder-plan:

1. **Read session-start corpus + this plan + #56's plan-doc**
   (`docs/rebuild/plans/workspace-sync.md`, especially §14
   method-decision register) + the milestone live-test
   synthesis at
   `/Users/lukeivers/pos3/.scratch/claude-output/milestone-live-test-2026-04-27.md`
   + FUTURE_IDEAS Idea 20.
2. **Author builder-plan** at
   `docs/rebuild/plans/workspace-sync-resolver-cost-overhaul.builder-plan.md`
   before any source edit. Builder-plan captures D-build.x
   method choices and the §2.5 reverse-direction trace,
   including:
     - The exact `MergeClassification.class_` enum members
       (the AC requires AT LEAST 5; builder authors the
       final set).
     - The classifier prompt text (D-2 below sets owner
       outcome-shape constraints; method-shape is builder's).
     - The verifier prompt text + rubber-stamp prevention
       structure (Hard Constraint #8 binding).
     - The deterministic primitive implementations per class
       (per-class merge shape; idempotency property test
       shape).
     - The ancestor-walk depth cap, caching strategy, and
       comparison-shape choice from D-1.
     - The subprocess `--bare` opt-in default + auth path
       from D-3.
3. **Land α.3 first IF D-3 ruling permits a clean shape.**
   Smallest surface; verifies the auth path before α.1+α.2
   compose on it. If D-3 surfaces a non-trivial auth-shape
   change, defer α.3 to the END of the build to isolate
   risk.
4. **Land α.1 (ancestor-detection) second.** Pure additive
   fast-path; runs before any LLM call; no behavioural
   dependency on α.2 or α.3. Tests: fixture with workspace
   equal to canonical's `HEAD~3` blob (must fast-path);
   fixture with workspace genuinely diverged (must
   decline); cache fixture (re-run under same state hits
   cache, zero git calls); depth-cap fixture (workspace
   deeper than cap declines).
5. **Land α.2 (classifier+deterministic+verifier) third.**
   Largest surface. Order within α.2:
     (a) classifier + `MergeClassification` schema; tests
         for each class.
     (b) per-class deterministic primitive implementations;
         idempotency property tests.
     (c) verifier + `MergeVerification` schema; tests
         against stub verifier returning `passed: true`
         and `passed: false` separately.
     (d) integration into the existing
         `resolve_inferred_conflicts` helper at the
         Class-C branch in `merge_helper.py` —
         ancestor-detection runs first (α.1); on decline,
         classifier+primitive+verifier runs (α.2);
         on fall-back, the existing LLM-generator path
         runs (preserves AC.WS.4 / AC.WS.12).
6. **Land OTel spans + audit-field extensions.** New
   attribute fields on existing audit-entry shape:
   `ancestor_match_sha`, `classifier_class`,
   `deterministic_primitive`, `fallback_reason` (all
   optional / `None`-permitted to preserve back-compat
   for entries that bypass each step). Tests for span
   emission per AC.WSα.7.
7. **Run touched-component suite** (`workspace-sync/tests/`),
   including the existing 62 tests at `0607dc7` baseline
   (must remain green). Then `pos-amend apply
   --dry-run`; if clean, run amendment commit; then
   `pos-amend seal --plan-doc <abs-path>`.
8. **Verify backward-compat** with a fixture forcing
   ancestor-decline + classifier-`unknown` + verifier-
   fail-on-everything; assert the resulting verdict
   matches #56's pre-amendment LLM-generator output for
   the same inputs.
9. **Re-run milestone live-test against pos3** (post-seal,
   out-of-scope of this plan but the natural follow-on
   dispatch validation).


---

## 9. Bookkeeping surface

Sealed-component amendment under workspace-sync. `pos-amend`
manifest sketch (builder finalises in
`<slug>.manifest.yaml`):

```yaml
schema_version: 1
amendment:
  number: <N>  # next free amendment number at dispatch time
  slug: workspace-sync-resolver-cost-overhaul
  title: "workspace-sync — resolver cost overhaul (Bundle α: ancestor-detection + classifier+verifier merge + bare subprocess)"

# BASELINE pinned to HEAD~1 of the amendment commit (per
# amendment #29 / #34 / ... / #56 BASELINE-as-HEAD~1 pattern).
# Builder fills SHA at apply time. The post-#56 tip is
# 0607dc7 (workspace-sync seal); subsequent commits may have
# advanced; builder reads HEAD~1 at apply time.
baseline: <HEAD~1 SHA>

plan: docs/rebuild/plans/workspace-sync-resolver-cost-overhaul.md

components:
  - name: workspace-sync
    seal_test: workspace-sync/tests/test_no_sealed_amendments.py
    sidecar: workspace-sync/tests/SEAL_COMMIT
    frozen_baseline: false
    extra_allowed_prefixes: []

universal_paths:
  prefixes:
    - docs/rebuild/plans/
  files:
    - CLAUDE.md
    - docs/odd-in-pos.md
    - docs/odd-methodology.md
    - docs/rebuild/FUTURE_IDEAS.md
    - docs/rebuild/FUTURE_IDEAS_DRAFT.md  # entries graduate / retire post-seal

narrative:
  target: workspace-sync/seals/SEAL_COMMIT.resolver-cost-overhaul
  body: |
    # Amendment #<N> — workspace-sync resolver cost overhaul
    #                  (Bundle α)

    <builder finalises body — see narrative shape in
    amendment-46 + amendment-47 + amendment-56 manifests
    for precedent>
```

**Salvage map.** Bundle α is authored fresh — there is no
existing prior-amendment salvage. The mechanism extends
three #56-resident files:

| File | Touch shape | Reason |
|---|---|---|
| `workspace-sync/src/workspace_sync/conflict_detection.py` | EXTEND | α.1 ancestor-detection helper attaches before the Class-C resolver call. |
| `workspace-sync/src/workspace_sync/merge_helper.py` | EXTEND | α.2 classifier+primitive+verifier integration at the Class-C branch (lines ~185-234 of post-#56 source). |
| `workspace-sync/src/workspace_sync/_resolver_client.py` | EXTEND | α.3 subprocess `--bare` flag opt-in (subject to D-3 auth resolution). |
| `workspace-sync/src/workspace_sync/merge_resolver.py` | EXTEND | New `MergeClassification` + `MergeVerification` Pydantic models; new `classify()` + `verify()` methods on `MergeResolver`. |
| `workspace-sync/src/workspace_sync/conflict_report.py` | EXTEND | New optional audit-entry fields (`ancestor_match_sha`, `classifier_class`, `deterministic_primitive`, `fallback_reason`). All optional → existing entries deserialise unchanged. |
| `workspace-sync/src/workspace_sync/observability.py` | UNCHANGED | Existing `span()` helper composes with the new span names. |
| `workspace-sync/src/workspace_sync/<NEW>` | NEW | Per-class deterministic merge primitives (filename builder's call — recommended `merge_primitives.py` or `merge_primitives/<class>.py`). |
| `workspace-sync/tests/test_merge_resolver.py` | EXTEND | Tests for `classify()` + `verify()`. |
| `workspace-sync/tests/test_merge_helper.py` | EXTEND | Integration tests for ancestor-fast-path + α.2 chain + fall-back. |
| `workspace-sync/tests/<NEW>` | NEW | Per-class deterministic-primitive tests + ancestor-detection tests. |
| `workspace-sync/tests/conftest.py` | EXTEND IF NEEDED | Stub clients for classifier + verifier alongside existing stub resolver. |

**Test counts (estimate; builder finalises).** ~25-35 new
tests. Existing 62 #56 tests must remain green at the
amendment commit and seal.

**Dependents cleared at seal:** the milestone live-test
re-run becomes feasible (cost-budget realistic). The
β bundle (ergonomics) becomes structurally independent;
no α dependency.

**Frozen-baseline:** `false`. workspace-sync is not the
hands-off-lifecycle frozen-BASELINE component (per
ODD §10).


---

## 10. Halt triggers (builder halts + signals owner)

Builder halts and signals owner if any of the following
fire. Each carries a specific surface check; the builder
does NOT silently extend a violation per
`feedback_subagent_odd_violation_halt`.

1. **A required new top-level spec objective surfaces.** §2
   argued composition under v1.0 self-upgrade objective +
   Gap-3 line 114; if during build the work cannot fit
   under the existing objective + AC.PO.1/2 ladder, halt.
2. **ODD violation observed in surrounding code/docs.** Per
   `feedback_subagent_odd_violation_halt`, halt and surface;
   do NOT extend a violating surface. Specifically: if
   workspace-sync's existing modules contain §2.5
   violations (code paths without backing AC) at the
   Class-C resolver-call site or its observability spans,
   halt before extending. (Pre-authoring sweep in §13:
   none observed at #56's seal commit.)
3. **An AC cannot be authored outcome-shaped.** If a
   behaviour the build needs to satisfy can only be tested
   by asserting a method choice (a specific class name, a
   specific module's import, a specific prompt-text
   substring), halt — owner rewrites as outcome.
4. **Required source-edit outside `workspace-sync/`.**
   Halt and surface. Specifically: any edit to
   `self-upgrade/` (Hard Constraint #1) or
   `tools/upgrade-merge-resolver/` (dispatch carve-out)
   fires this trigger. Universal-paths admissions
   (`docs/rebuild/plans/`, top-level docs) are exempt.
5. **LLM-merge mechanism requires a Claude SDK surface
   pos-v2 doesn't have wired.** Bundle α composes on
   existing structured-output via `_ClaudePrintResolverClient`;
   if the classifier or verifier needs e.g. streaming /
   tool-use / response-prefilling that the wired surface
   doesn't expose, halt.
6. **Verifier rubber-stamp risk cannot be structurally
   excluded.** Hard Constraint #8 binds the build to
   structurally exclude the case where (a) classifier
   mis-tags a file's class, (b) the deterministic
   primitive corrupts the merge, and (c) the verifier
   rubber-stamps. The mitigation requires the verifier
   prompt to take the classifier's class as a NAMED
   INPUT and ask "is the file actually structurally
   this class?" as the first check. If during prompt
   authoring the structural exclusion cannot be cleanly
   written (e.g. the class taxonomy bleeds into prose
   such that "is this an append-only-list?" has no
   clean answer), halt — owner rules whether to drop
   the offending class, narrow the taxonomy, or accept
   the rubber-stamp risk.
7. **`claude --bare` auth path cannot be cleanly resolved
   against the workspace's configured Claude credential.**
   The plan-author audit (§13) found `--bare` strictly
   requires `ANTHROPIC_API_KEY` or `apiKeyHelper`; OAuth
   and keychain are never read; the existing resolver's
   env-scrubber drops `ANTHROPIC_API_KEY` to force OAuth.
   D-3 (§11) surfaces the auth-shape change for owner
   ruling. If the chosen auth path requires NEW user
   configuration (e.g. demanding the user export
   `ANTHROPIC_API_KEY` when their machine uses Claude Max
   OAuth), halt — owner rules whether to (a) accept the
   config burden, (b) ship α.3 as opt-in disabled by
   default, (c) drop α.3 from the bundle.
8. **Workspace data loss reproducible under any legitimate
   input.** AC.WSα.6 fall-back must preserve #56's
   fail-closed semantics; if a fixture produces a state
   where Class-A is overwritten or a fall-back path
   applies a partial/wrong merge silently, halt.
9. **Wall-time exceeds projected 4–6 hours of build.**
   Halt with current-state report; owner triages whether
   to continue, drop α.3 to reduce surface, or split into
   sub-amendments (α.1 ships first; α.2+α.3 follow).
10. **Amendment scope expansion crosses sealed-component
    fences beyond test-fixture admissions.** Halt.


---

## 11. Decisions remaining for the owner to rule on

**All four decisions LOCKED 2026-04-27 by primary persona under confidence-delegation** (Luke 2026-04-27 broad-autonomy directive: "I authorize you to make any reasonable decisions on my behalf"). Recorded inline below per the existing convention; full reasoning preserved for audit trail.

- **D-1 LOCKED:** Plan-author recommendation accepted. Depth cap 200 (empirical max ancestor-match was 13 commits in pos3 audit; 200 is generous). Sibling cache file `<workspace>/.pos/sync/<ref>/ancestor-cache.yaml`. SHA256 of byte-content (matches what audit already records). Decline-on-shallow with fallback to existing resolver path.

- **D-2 LOCKED:** Plan-author recommendation accepted (classify on truncated 50-first+10-last lines per side; verifier reads full canonical+workspace+candidate+named-class+primitive-trace with `class_mismatch` flag forcing `passed: false`). Method-shape design; builder may refine within AC bounds.

- **D-3 RE-LOCKED 2026-04-27: NEW PATH — `--strict-mcp-config --mcp-config <empty>` instead of `--bare`.** Initial lock was path (c) — drop α.3 — based on incomplete model that treated --bare as timing-only. Owner clarified the actual purpose: **prevent bun-process contention from claude -p subprocesses spawning conflicting MCP loaders** (which had been observed disrupting the parent session's telegram MCP). Empirical test 2026-04-27 confirmed `claude --strict-mcp-config --mcp-config <empty-mcp.json> -p ...` works under Claude Max OAuth (no `ANTHROPIC_API_KEY` needed), 2.3s wall-time on a trivial prompt. **Final α.3 design:** the resolver subprocess uses `--strict-mcp-config --mcp-config <path-to-empty-mcp-config>` where the empty config contains `{"mcpServers": {}}`. Achieves MCP isolation (the goal); preserves OAuth/Claude-Max auth (avoids the --bare auth problem); no user-facing config knob needed (always-on); ships as part of the bundle (no opt-in). AC.WSα.8 redesigned (see §4) and AC seal-diff invariant unchanged. Calibration miss captured: the dispatch brief framed α.3 as "5-20s saved" purely a timing optimization; missed the MCP-isolation purpose. Owner-watching-the-terminal corrected this; the empirical-experiment reversed within a few seconds via verified-with-actual-claude-call.

- **D-4 LOCKED:** Plan-author recommendation accepted (defer; do not retain OO). The α-bundle's mechanism reduces fall-back frequency by ~95-99%; hardcoded 120s timeout that fires on rare fall-back is a tolerable failure mode (audit + halt-and-resume per #56 AC.WS.12). If post-α data shows recurring fall-back-with-timeout for a class of files, capture as follow-on then. Don't pre-engineer.

**Decisions detail follow below for audit trail purposes.**

### D-1. α.1 ancestor-walk parameters (LOCKED 2026-04-27)

Bundle α surfaces four genuine decisions for owner ruling.
All are outcome-shape (not method-shape); each carries a
recommendation grounded in the data available at
plan-author time.

### D-1. α.1 ancestor-walk parameters

**Question.** Four sub-questions bundled (each cheap to
decide together):

- **Depth cap.** How many ancestors deep does the walk go
  before declining?
- **Caching strategy.** Cache the ancestor-match result
  where? (in `state.yaml`, in a sibling
  `ancestor-cache.yaml`, in `.pos/sync/<ref>/cache/`,
  or no persistent cache — recompute every run)
- **Content comparison shape.** sha256 over UTF-8 text or
  byte-identical comparison?
- **Fallback when canonical's git history is incomplete.**
  Shallow clone, CI-pruned, or remote-only — what does
  the helper do?

**Why genuinely uncertain.** Depth cap is a knob between
cost (deep walks burn git-rev-list time) and coverage
(long-stale workspaces have ancestors many commits back).
Caching has real correctness implications — invalidating
the cache on canonical-ref change is critical to avoid
stale-fast-path verdicts. Comparison shape is a
determinism/portability tradeoff. Fallback is a
safety/coverage tradeoff.

**Recommendation.**

- **Depth cap:** 200 commits. Most pos-v2 workspaces are
  on the order of months behind canonical (≤100 commits);
  200 doubles the headroom. Walk cost is ~10ms per commit
  on warm cache; 200 commits ≈ 2s. Workspace-tunable in
  `~/.pos/sync-config.yaml`.
- **Caching strategy:** sibling
  `<workspace>/.pos/sync/<ref>/ancestor-cache.yaml`
  keyed by `(path, workspace_sha)`. Cache key includes
  the canonical ref's resolved SHA (so a canonical-ref
  advance invalidates the cache). Per-conflict cache
  entries; the cache file is rewritten at end-of-run.
  Same cache file is the artefact future tooling
  composes against (Lens 2 toolkit-primitive).
- **Comparison shape:** sha256 over file bytes (not
  text). Matches `conflict_detection.py`'s existing
  `_sha256_bytes` shape; identical hash = identical
  bytes; no encoding-dependent surprises. The helper
  skips binary-fail paths (mirrors existing
  `_git_show_bytes` skip).
- **Fallback when canonical's git history is incomplete:**
  if `git rev-list` returns < depth_cap commits AND no
  match found, the helper declines (Class-C fall-through
  to resolver). Rationale: a CI-pruned shallow clone
  is a legitimate user state; declining here means the
  resolver runs as today. The audit records
  `ancestor_walk_short: true` so observability picks up
  on incomplete-history cases. NOT a halt.

### D-2. α.2 classify-call + verify-call prompt design (LOCKED 2026-04-27)

**Question.** Two prompts to author. Owner-shape
questions:

- Classify-call: should the prompt include the file
  contents (for accurate classification) or only the
  file's METADATA (path + first-N-lines + mime hint)
  to keep the input cheap?
- Verify-call: should the verifier see ALL THREE inputs
  (canonical, workspace, candidate-merged) or only the
  candidate plus a structural summary?

**Why genuinely uncertain.** The whole point of α.2 is
cost reduction; if the classifier reads the full file,
the input cost is the same as the generator's input cost
(only the OUTPUT shrinks). The wall-time savings come
from input+output token reduction; classifier-with-full-
input + verifier-with-full-input is still a net win
vs generator-with-full-input-AND-full-output, but a
classifier-with-just-metadata + verifier-with-full-input
is the maximum-leverage shape.

Conversely: a classifier without the file contents may
mis-classify (a markdown file with bullet lists could be
free-prose; only reading reveals the structure). And
Hard Constraint #8 requires the verifier to confirm
"is this actually structurally a {class}?" — which
needs the verifier to read enough of the file to
judge.

**Recommendation.**

- **Classify-call:** include the FIRST 50 LINES + the
  LAST 10 LINES of each side (canonical + workspace).
  Bounded input (~1000-2000 tokens for typical files);
  sufficient structure-evidence for the 5-class
  taxonomy; binary-detection trivial. If the file is
  ≤60 lines, send the full file (no truncation).
  Output: `MergeClassification` Pydantic shape with
  `class_: Literal[...]` + `confidence: float`. ~50
  output tokens.
- **Verify-call:** include FULL canonical + FULL
  workspace + FULL candidate-merged + the
  classifier's named class + the deterministic
  primitive's trace. The verifier reads everything
  and answers structurally per Hard Constraint #8's
  rubric: "(1) Is the file actually structurally a
  {class}? (2) Did the {primitive} produce a
  candidate that preserves both sides' intent?
  (3) Did any line-level information from either
  side go missing?" Output: `MergeVerification` with
  `passed: bool`, `class_mismatch: bool`,
  `concerns: str | None`, `confidence: float`. ~200
  output tokens.

Per Hard Constraint #8 the `class_mismatch: true` flag
forces `passed: false`. The verifier becomes a structural
check on the classifier — not a rubber-stamp.

### D-3. α.3 subprocess MCP-isolation (RE-LOCKED 2026-04-27 = `--strict-mcp-config --mcp-config <empty>` design; auth-OAuth-compatible)

**Question.** `claude --bare` strictly requires
`ANTHROPIC_API_KEY` or `apiKeyHelper` (verified
`claude --help` 2.1.119 output:
*"Anthropic auth is strictly ANTHROPIC_API_KEY or
apiKeyHelper via --settings (OAuth and keychain are
never read)."*). The current resolver
(`_resolver_client.py`) **explicitly drops
`ANTHROPIC_API_KEY`** from the child env (per
`_ENV_ALLOWED_VARS = ("PATH", "HOME", "USER")`) so the
child cannot fall through to a billed API path on a
Claude Max OAuth machine. This is incompatible: a
`--bare` invocation with the existing env-scrubber
fails auth.

Three resolution paths:

- **(a) Restore `ANTHROPIC_API_KEY` to the child env
  when `--bare` is active.** Trivial code change. But
  a Claude Max user without `ANTHROPIC_API_KEY` set
  in their environment loses the optimization;
  silently shipping `--bare` would BREAK Claude Max
  users on first sync. Mitigation: gate `--bare` on
  `ANTHROPIC_API_KEY` being present in the parent
  env; default `--bare` OFF when the variable is
  absent. Adds a fallback path the user doesn't see.
- **(b) Use `--settings <path-with-apiKeyHelper>`.**
  Requires authoring (or having the user author) a
  `.pos/claude-bare.settings.json` with an
  `apiKeyHelper` script that echoes the user's key.
  More setup burden; works for both API-key and
  Max-with-bring-your-own-key users. Doesn't help
  Max-only users.
- **(c) Drop α.3 from the bundle; keep cost reduction
  via α.1 + α.2 only.** Cleanest plan-shape; loses the
  5-20s cold-start savings per call. With α.1+α.2
  eliminating ~95% of LLM calls (90% via ancestor +
  half the remaining via verify-pass), the absolute
  wall-time saving from α.3 may be small (~2 calls × 15s
  per pos3 first-sync = ~30s saved). Possibly not
  worth the auth complication.

**Recommendation.** **Path (a) with a gate.**
Implementation:
- Add an opt-in `bare: bool` parameter to
  `_ClaudePrintResolverClient.__init__` (default `False`
  to preserve back-compat).
- When `bare=True`, append `--bare` to argv AND restore
  `ANTHROPIC_API_KEY` to the child env if present in
  the parent env.
- The resolver factory `build_merge_resolver()` reads
  `~/.pos/sync-config.yaml`'s `bare_subprocess: bool`
  field (default `False` — opt-in); if true AND
  `ANTHROPIC_API_KEY` is present, builds the client
  with `bare=True`. Otherwise warns and falls back to
  `bare=False`.
- The audit records the subprocess mode used per call
  (`subprocess_mode: bare | full`) so observability
  picks up on the realised savings.

Owner ruling needed because:
- This is a USER-FACING surface change (the
  `bare_subprocess` config knob is new).
- The recommended default (`False`) means most users
  don't realise the savings without configuring;
  contradicts dispatch's "one-line change" framing.
- If owner prefers path (c) — drop α.3 — the bundle
  is α.1+α.2 only, the AC.WSα.8 ships as
  out-of-scope, and the seal narrative reflects the
  drop.

### D-4. Should OO (resolver-client timeout config) be retained as a fallback? (LOCKED 2026-04-27 = no, defer)

**Question.** The dispatch states α subsumes OO ("resolver-
client timeout config + 120→300s default"). The current
resolver hard-codes `timeout_s: float = 120.0` in
`_ClaudePrintResolverClient.__init__`. Should the
amendment ALSO surface this as a config-knob (for the
fall-back generator path which still emits 5-7k output
tokens when the verifier rejects), or accept the dispatch's
"irrelevant if cost is lower per call" framing?

**Why genuinely uncertain.** The fall-back generator path
(AC.WSα.6) preserves the existing slow-output behaviour;
if the verifier rejects on a 100-line file, the resolver
still hits the 120s timeout for THAT file. But the
ancestor-detection + classifier-passes-fast-path will
drop the absolute count of fall-backs to near-zero in
practice; whether 120s is still tight for the rare
fall-back is a calibration question we won't know
empirically until post-α live-test.

**Recommendation.** **Defer; do not retain OO.** The α
bundle's mechanism reduces fall-back frequency by an
estimated 95-99% (90% via ancestor + half the remaining
via verify-pass). A hardcoded 120s timeout that fires on
rare fall-back is a tolerable failure mode; the audit
records it cleanly per #56's AC.WS.12 (fail-closed with
halt-and-resume). If post-α live-test against pos3
shows the rare fall-back-with-timeout pattern recurring
for a class of files the deterministic primitives can't
reach, capture as a follow-on amendment then. Don't
pre-engineer.

Alternative: **bump the timeout default to 300s on the
fall-back generator path only** (low-risk one-line change
as a belt-and-suspenders). Owner can rule this in if
preferred.

### Decisions LOCKED by dispatch + #56 plan + companion documents
(NOT for owner ruling here — captured for builder reference):

- **Bundle scope (LOCKED):** α.1 + α.2 + α.3, three internal
  ACs. Subsumes OO.
- **Component fence (LOCKED):** workspace-sync only; no
  edits to self-upgrade/ or tools/upgrade-merge-resolver/.
- **Confidence-floor calibration (LOCKED OUT — β-bundle PP):**
  not in α scope.
- **β-bundle ergonomics (LOCKED OUT):** separate amendment
  family.
- **Per-conflict + cumulative budget defaults (LOCKED):**
  inherit #56's 5k / 100k.
- **Fail-closed semantics (LOCKED):** #56 AC.WS.12 carries
  over.
- **Class-A protection (LOCKED):** unchanged from #56.
- **AC numbering (LOCKED):** AC.WSα.1 through AC.WSα.8 +
  AC.WSα.S.


---

## 12. Summary of named decisions (owner-readable)

| Decision | Recommendation | Why it matters |
|---|---|---|
| D-1. α.1 ancestor-walk parameters (depth cap / caching / comparison / fallback) | **Depth 200; sibling cache file `<workspace>/.pos/sync/<ref>/ancestor-cache.yaml`; sha256-byte comparison; decline-on-shallow-clone** (workspace-tunable depth) | Bounds walk cost at ~2s on warm cache; cache invalidates on canonical-ref change; matches existing `_sha256_bytes` shape; declining on incomplete history is the safe floor |
| D-2. α.2 prompt design (classify-call + verify-call inputs) | **Classify: 50-first + 10-last lines per side (full file ≤60 lines); ~50 output tokens. Verify: full canonical + full workspace + full candidate + named-class + primitive-trace; ~200 output tokens; class_mismatch flag → passed=false (Hard Constraint #8 structural)** | Maximum-leverage cost reduction without losing classifier accuracy; verifier reads enough to structurally check the classifier per Hard Constraint #8 |
| D-3. α.3 `claude --bare` auth-shape (HALT-FOUND) | **Path (a): opt-in `bare_subprocess: bool` config knob (default False); restore `ANTHROPIC_API_KEY` to child env when bare=True; gate on parent env presence; warn-and-fallback otherwise.** Owner may prefer path (c) — drop α.3 — if the user-facing config knob is unwanted | Material outcome-shape change to the user-facing surface; the dispatch's "one-line change" framing was based on incomplete information; D-3 routes the resolution |
| D-4. Should OO (resolver-client timeout config) be retained as a fallback? | **Defer; do not retain.** Bundle α reduces fall-back frequency by 95-99%; rare fall-back-with-timeout is tolerable; capture as follow-on if post-α live-test shows pattern recurring | Pre-engineering against rare fall-backs adds complexity α's main mechanism makes irrelevant in 99% of paths |

All four decisions are reversible at the cost of a follow-on
amendment; none is foundational. D-3 is the most consequential
(changes user-facing config surface); D-1 is purely
performance-tuning; D-2 is prompt-engineering with rubric
bounded by Hard Constraint #8; D-4 is a single-line config
default the builder can ship one way and amend later.


---

## 13. Halt-and-surface findings encountered during plan authoring

Per `feedback_subagent_odd_violation_halt`: halt and surface
any ODD violation observed in surrounding code/docs.

Plan-authoring scope (read-only audit of `workspace-sync/src/`,
the milestone live-test synthesis, FUTURE_IDEAS Idea 20,
FUTURE_IDEAS_DRAFT entries, #56's plan-doc + builder-plan +
manifest, the relevant spec lines):

### HALT-FOUND #1 (α.3) — `claude --bare` is auth-incompatible with current resolver

The dispatch framed α.3 as "one-line change" adding `--bare`
to the `claude -p` argv. **Verified `claude --help` 2.1.119
output:** *"Anthropic auth is strictly ANTHROPIC_API_KEY or
apiKeyHelper via --settings (OAuth and keychain are never
read)."*

**The current resolver design is structurally
incompatible:** `_resolver_client.py` defines
`_ENV_ALLOWED_VARS = ("PATH", "HOME", "USER")` — explicitly
dropping `ANTHROPIC_API_KEY` to force OAuth/keychain auth
on Claude Max machines. A `--bare` invocation under that env
fails auth.

**This is NOT a build-blocker** — three resolution paths are
available (path a / b / c per D-3 above). It IS a
scope-shape change: α.3 cannot ship as a one-line change;
it requires either a user-facing config knob (path a or b)
or being dropped from the bundle (path c). **Surfaced as
D-3 in §11 for owner ruling.** Plan-author recommendation:
path (a).

This is the "halt-and-surface (do not silently extend)" the
dispatch's halt-trigger explicitly named: "An AC turns out
to be method-coupled (text mentions a specific call site /
file layout / symbol). Tighten the AC text first; halt if
non-trivial." α.3's AC.WSα.8 has been authored
outcome-shaped (subprocess flag composition with auth-shape
preserved) — but the AC carries the burden D-3 routes.

### Other findings (not halts; verify-then-proceed)

- **No ODD violations in workspace-sync/src/.** The
  `Resolution` enum's structural exclusion of `skipped`
  (carried over from clause-(g)) remains intact at #56's
  seal commit. The `MergeVerdict.model_validator` is
  structural-refusal-by-default. The
  `resolve_inferred_conflicts` helper's Class-A→KEEP_LOCAL
  branch + Class-B→ACCEPT_UPSTREAM/KEEP_LOCAL branch +
  Class-C→resolver branch are AC-backed (AC.WS.2 / AC.WS.3
  / AC.WS.4). Bundle α extends the Class-C branch only;
  the extension lands new ACs (AC.WSα.1 through
  AC.WSα.8) so reverse-trace from each new branch is
  clean.
- **No ODD violations in spec line 81 + line 114.** Both
  remain outcome-shaped; bundle α is a method refinement
  of the Gap-3 acceptance line 114's "no silent skip"
  clause and the v1.0 self-upgrade objective's
  "without meaningfully disrupting the user's running
  configuration" property.
- **No ODD violations in FUTURE_IDEAS Idea 20.** The
  meta-pattern is outcome-shape — "small-output LLM
  calls are cheap; large-output ones are not"; the
  classifier+verifier shape is its mechanism. Bundle
  α.2 IS the first manifestation. The ladder from
  Idea 20 → AC.WSα.3-6 is reverse-trace-clean.
- **Live-test synthesis findings 1-4 mapped:** Finding 1
  (0.90 floor too high) → β.4 PP, OUT OF SCOPE. Finding
  2 (120s timeout) → SUBSUMED by α.1+α.2 cost
  reduction; D-4 surfaces the residual question. Finding
  3 (46 conflicts) → α.1 PRIMARY MECHANISM. Finding 4
  (resolver IS sophisticated) → preserved; α.2's
  fall-back path keeps the LLM-generator ceiling.
- **`workspace-sync.md` §14 method-decision register
  intact** at #56's seal commit; the existing
  D-build.0 through D-build.13 entries are unchanged
  by this amendment. Bundle α adds new D-build.x
  entries inside the new amendment's plan-doc §14
  (post-build).
- **Hard Constraint #11 from #56 (`salvage-by-COPY-not-
  import`) carries over and is honoured by the bundle —
  no new cross-component imports introduced.**


---

## 14. Method-decision record (builder, post-build)

The plan §11 left D-build.x method choices to the builder within the
ACs' outcome bounds. This section is populated post-build.

### D-build.x — (placeholder for the build agent's method choices)

### Test breakdown

(placeholder)

### Backwards-compat verification

(placeholder)

### Commit SHAs

(placeholder; auto-filled by `pos-amend seal --plan-doc <ABSOLUTE PATH>` per the seal-automation extension. Pass an ABSOLUTE path to avoid the `Path.relative_to` crash documented at commit `75c4d73`. The amendment commit + seal commit + plan-SHA backfill commit each appear here on completion.)

### Commit SHAs

(populated by `pos-amend seal --plan-doc <this-file> ...` after build, or appended manually for dev-discipline plans)

### Dependents cleared to dispatch

(placeholder)

---

## 15. References

- CLAUDE.md (project + global)
- `docs/odd-methodology.md`, `docs/odd-in-pos.md`
- `docs/rebuild/VALUE_PROPOSITION.md`, `docs/rebuild/STATE.md`,
  `docs/rebuild/FUTURE_IDEAS.md`, `docs/rebuild/FUTURE_IDEAS_DRAFT.md`
- `docs/rebuild/spec/pos-v2-objectives-spec.md` (v1.0 +
  v1.1 — self-upgrade objective at line 81; clause-g +
  workspace-customisation conflict surfacing at line 114)
- `docs/rebuild/plans/workspace-sync.md` (#56 plan-doc, 1377
  lines; the parent plan)
- `docs/rebuild/plans/workspace-sync.builder-plan.md`
  (#56 builder-plan, 731 lines; D-build.0-13)
- `docs/rebuild/plans/workspace-sync.manifest.yaml`
  (#56 manifest)
- `/Users/lukeivers/pos3/.scratch/claude-output/milestone-live-test-2026-04-27.md`
  (live-test synthesis — primary motivation document)
- `docs/rebuild/FUTURE_IDEAS.md` Idea 20 (lines 683-710)
- `docs/rebuild/FUTURE_IDEAS_DRAFT.md` Workspace-sync
  follow-on family (lines 14-31)
- `workspace-sync/src/workspace_sync/_resolver_client.py`
  (α.3 attach point; current `claude -p` subprocess wrap)
- `workspace-sync/src/workspace_sync/conflict_detection.py`
  (α.1 attach point)
- `workspace-sync/src/workspace_sync/merge_helper.py`
  (α.2 attach point — Class-C branch)
- `workspace-sync/src/workspace_sync/merge_resolver.py`
  (donor of MergeVerdict / MergeResolver / ResolverBudget;
  α.2 extends with MergeClassification + MergeVerification)
- `workspace-sync/src/workspace_sync/conflict_report.py`
  (audit-entry shape; α extends with optional fields)
- `workspace-sync/src/workspace_sync/observability.py`
  (existing OTel `span()` helper)
- `workspace-sync/tests/SEAL_COMMIT` = `efbb7d2...` at
  #56 amendment commit; current seal at `0607dc7`

