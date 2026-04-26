# Structural enforcement — A1: substrate (workspace-mode partition + active-scope sentinel + corpus-load sentinel + objective-manifest substrate)

**Status:** authored 2026-04-26 (plan-doc only; no code, no commits, no manifest yet).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme:** A1 of the four-amendment structural-enforcement programme established by `docs/rebuild/plans/research/structural-enforcement-of-critical-requirements-research.md` (the locked research artefact). A1 is the foundational substrate; A2 (objective-binding gate), A3 (TDD-guard test-pinned-to-objective), A4 (Bash/Agent-context guards) compose on this substrate and are **out of scope** for A1.
**Owner directive (locked 2026-04-26):** *"Structural enforcement of critical guards and user-defined hard requirements is always going to trump rules in files and memories."* Structural enforcement is therefore a default mechanism, not a rule-in-files preference.
**D-decisions (all 5 LOCKED 2026-04-26):** D1 dev-discipline carve-outs for `docs/`, `tools/`, `.scratch/`, `CLAUDE*.md`; D2 TDD-guard scoped to re-extension-with-new-AC; **D3 objective manifest extends `objective-tracker` SQLite store** (governs A1's substrate shape); D4 secret/blast-radius gates universal, ODD-discipline gates DEV-MODE-only; D5 KEEP-ADVISORY list of 10 rules to short-circuit future re-litigation.

---

## 1. Summary / TLDR

A1 lands the foundational primitives every later structural-enforcement amendment composes on. **No user-visible gate fires in A1.** A1 ships:

1. **Workspace-mode partition.** A single `mode` bit (`dev-mode | normal-use`) is queryable from any hook or substrate caller via the existing `loam-mode` selector; gates in A2/A3/A4 will short-circuit to allow when `mode = normal-use` (D4 governs which gates are universal regardless).
2. **Active-scope sentinel.** A workspace-local sentinel file (`<workspace>/.pos/active-scope.json` shape; gitignored alongside the existing `<workspace>/.pos/first-run.state` family) declares which `(component, ac_id, plan_path)` triple the current dispatch is operating against. Authored when an agent (or main session) starts a scope; consumed by future gates.
3. **Corpus-load sentinel.** A workspace-local session-scoped sentinel (`<workspace>/.pos/session-state/<session_id>.json` shape) records that the session-start required-corpus reads have happened. Written by a `SessionStart` hook entry; consumed by future gates.
4. **Objective-manifest substrate.** A new table inside the existing `objective-tracker` SQLite store records `(component, ac_id, source_path_glob)` rows. The active-scope sentinel binds against rows in this table. The manifest is queryable by future gates (A2: AC binding; A3: AC → test-existence path).

After A1 lands, the substrate is observable end-to-end (a sentinel can be written and read, the manifest table accepts and returns rows, the workspace-mode bit is reachable from a hook context) but no production-code gate refuses anything. A2 is the first amendment that turns the substrate into a deny.

A1's scope is sized so that A2/A3/A4 are pure additions of `PreToolUse` matchers + decision logic against this substrate. No A2/A3/A4 design choice may force structural changes back into A1 — if it does, A1 is wrong-sized. Halt-and-surface in §10 names the specific shape.

Per "scope-only-dispatch" CDC, the per-AC files/symbols/test names belong in the builder plan that follows owner approval of this plan-doc, not here.

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objective this plan satisfies:**

- **`docs/rebuild/spec/pos-v2-objectives-spec.md` line 134–135 — Deterministic (tiered).** The objective declares three tiers plus two negative rules (*"never rules where hooks would do"*, *"never arbitrary where rubric exists"*). Additional acceptance line 135-(a): *"for any decision currently implemented as a rule/prompt where a deterministic hook/script could produce the same outcome, an audit surfaces it."* Additional acceptance line 135-(b): *"any arbitrary decision (no rubric cited) surfaces as a lint failure pending rubric definition."*

A1 satisfies the binding two ways:

- The locked research artefact (`structural-enforcement-of-critical-requirements-research.md`) IS the audit line 135-(a) requires; A1 lays the substrate that the audit's PROMOTE rows (A2/A3/A4) will run on.
- A1's audit-log surface (the manifest's event-stream + the sentinel write/read transactions emit observability events) gives line 135-(b) a place to land — arbitrary decisions naturally fail to bind to a manifest row, and the deny+reason text is the lint output.

**Sealed-component fence (D3 governs):**

- `objective-tracker` — schema extension (new table + read/write API surface for `(component, ac_id, source_path_glob)` rows).
- `primary-persona` — no source change anticipated; A1's substrate is consumable by the persona's session-start emitter without an emitter change.
- `hands-off-lifecycle` — new `SessionStart` inner hook entry (registered through #45's `extra_inner_hooks` registry, like #46's persona session-start hook) writes the corpus-load sentinel; new sentinel writer module under `hands-off-lifecycle/hooks/`.

The fence is **two sealed components** in normal A1 shape: `objective-tracker` (manifest table) and `hands-off-lifecycle` (corpus-load sentinel writer + hook registration). The active-scope sentinel writer is a small CLI under `tools/` (dev-discipline path; non-fence) per D1 — see §6 D-A1.4 below. The workspace-mode bit reuses `loam-mode` (already exists at `tools/loam-mode/`; non-fence) — A1 is consumer-only, not amender. **Builder confirms exact fence in the builder plan; this plan names two sealed components, two non-fence consumers, and A1's fence-scope assertion is explicit per AC.SE.S below.**

**ODD §2.5 reverse direction.** Every code path, branch, dependency, and test in A1's diff traces back to a named AC under §4. No silent branches; no defensive `if`s without backing AC.

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage

*Required research question: what Claude capability does this lean on or extend?*

A1 leans on three Claude Code primitives end-to-end:

- **`SessionStart` hook surface** — the corpus-load sentinel writer is a `SessionStart` inner hook, registered through `hands-off-lifecycle`'s existing `merge_session_start` + `extra_inner_hooks` registry (the same registry amendment #45 generalised, that #46 added the persona's emitter to, that loam-mode's mode-aware fragment selector already uses). A1 is the third concrete consumer of that registry.
- **Workspace-local `.mcp.json` / `.claude/` surface** — the `<workspace>/.pos/` sentinel directory pattern is the same pattern `<workspace>/.pos/first-run.state` (`hands-off-lifecycle/hooks/first_run_state.py`) and `<workspace>/.mcp.json` (amendment #47) already use. A1 adds two new files in that namespace; no new namespace, no new surface.
- **`additionalContext` channel** — the corpus-load sentinel can OPTIONALLY be surfaced into the persona's SessionStart `additionalContext` (via #46's emitter) so the model sees `corpus_loaded: true|partial|missing` without an extra hook fire. A1 does not require this surfacing — A2's gate consults the sentinel directly — but A1's sentinel format must be compatible with consumption-by-additionalContext for future composition.

The substrate (objective-manifest table inside `objective-tracker`) extends Claude-adjacent infrastructure, not Claude itself; that's appropriate — Claude doesn't ship an objective registry, but `objective-tracker` already exists and already has the schema-evolution mechanism (D3-(a) is the natural extension). The asymmetric finding from research §7.1 — *"Claude Code's hook surface IS the structural-enforcement surface"* — applies recursively to A1: A1's substrate exists exactly because Claude's hook surface needs it; nothing is built that the Claude primitives cannot consume.

### Lens 2 — Harness + primary-persona value

*Primary-persona test: does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

**Yes — preparation-stage value.** Today the persona's translation toolkit includes "remember the 27 advisory rules audited in research §2 and apply them to every dispatch / every edit / every commit." A1 alone does not reduce that burden (no gate fires); but A1 is the prerequisite for A2/A3/A4, which collectively move the rules out of memory and into hook substrate. Without A1, the burden-reduction in A2/A3/A4 cannot land — the substrate has to exist first. The plan-level value is therefore the unblocking of subsequent amendments rather than a direct user-visible reduction.

*Harness test: does this add to the toolkit the primary persona can draw from?*

**Yes — four new primitives.**

1. **Workspace-mode bit** — the persona can interrogate "am I in DEV MODE or NORMAL USE?" structurally; future dispatches branch on this without re-asking the user.
2. **Active-scope sentinel** — the persona can answer "what AC am I working on?" by reading the sentinel; dispatches inherit the binding without re-stating it.
3. **Corpus-load sentinel** — the persona can answer "did I load the required design corpus this session?" structurally; the same data feeds future gates.
4. **Objective-manifest table** — every future tooling consumer (pos-amend, foundation-audit, plan-validators, AC-coverage reports) gets a queryable registry of `(component, ac_id, source_path_glob)` mappings.

Each primitive is harness-toolkit-shaped: composable, queryable, persistent across sessions. **→ AC.PO.2.**

### Lens 3 — ODD authoring

A1 is structurally shaped, not advisory. The substrate's surfaces are deterministic: the manifest schema accepts/refuses rows by validation; the sentinel files have deterministic write contracts; the workspace-mode bit is one-of-two values. Every AC below is outcome-shaped (no "the implementation will use X" language). Method (file paths, exact module names, validator shapes, schema column names) is the builder's call and lives in the builder plan.

---

## 4. Acceptance criteria

A1's outcome is the substrate's observable existence + correctness, not gate behaviour. Eight ACs cover the substrate's behaviours plus the seal-diff invariant.

- **AC.SE.1 — Workspace-mode bit is queryable.** A pure-Python helper exposed by `loam-mode` (consumer surface; no edit to `loam-mode` source if the existing surface is sufficient — builder confirms) returns `"dev-mode" | "normal-use"` deterministically given the workspace's primary-persona contract `dev_intent` field. The helper is callable from inside a Claude Code hook process (no async-runtime dependency, no Claude SDK dependency, sub-100ms p95). When `dev_intent` is unset or unreadable, the helper returns `"normal-use"` (fail-closed-to-permissive — DEV-MODE machinery is opt-in).

- **AC.SE.2 — Active-scope sentinel write contract.** A documented sentinel-writer surface (CLI subcommand or library function — builder's call) creates `<workspace>/.pos/active-scope.json` with deterministic JSON shape carrying at minimum: `scope_id` (string), `plan_path` (workspace-relative), `bindings: [{component: str, ac_id: str}]`, `created_at` (ISO-8601 UTC), `session_id` (string when known, else null). Re-invocation with the same `scope_id` is idempotent (byte-equal write skipped); re-invocation with a different `scope_id` overwrites atomically (`.tmp` + `os.rename`).

- **AC.SE.3 — Active-scope sentinel read contract.** A documented sentinel-reader surface returns the parsed JSON object as a typed structure (or `None` when the file is absent / malformed / unreadable). Reader never raises on environmental failure; malformed JSON is surfaced as a structured `MalformedSentinel` outcome the caller can route. Concurrent read while writer is mid-rename returns either pre-rename content or post-rename content (atomic — never a partial JSON read).

- **AC.SE.4 — Corpus-load sentinel write contract.** A `SessionStart` inner hook entry registered via `merge_session_start` writes `<workspace>/.pos/session-state/<session_id>.json` carrying at minimum: `session_id`, `corpus_paths_required` (list of workspace-relative paths drawn from the dev-mode-manifest's always-loaded set), `corpus_paths_loaded` (list — empty at session-start; future hooks may append), `state` ∈ `{loaded, partial, missing}` (computed from path-existence checks at session-start time), `created_at`. Hook completes within the 5s SessionStart inner-hook budget (matches loam-mode's #45 budget envelope) and exits 0 on every path (fail-soft per the SessionStart contract).

- **AC.SE.5 — Workspace-mode partition is honoured by the corpus-load hook.** When the workspace-mode bit is `normal-use`, the corpus-load sentinel hook still writes a sentinel (so future gates can read it), BUT its `corpus_paths_required` reflects the NORMAL-USE always-loaded set (smaller — DEV-MODE-only paths excluded). When `dev-mode`, the required set is the full DEV-MODE always-loaded set. This ensures A2/A3/A4 gates that consult the sentinel produce mode-correct decisions without each gate re-computing the partition.

- **AC.SE.6 — Objective-manifest table accepts well-formed rows.** A new table inside the existing `objective-tracker` SQLite store accepts rows of shape `(component: str, ac_id: str, source_path_glob: str)` with appropriate uniqueness on `(component, ac_id, source_path_glob)`. A documented public API surface (read + write) on the tracker exposes: insert-row, list-rows-for-component, list-rows-for-ac, list-rows-matching-source-path. Schema is forward-compatible (adding an optional column in a later amendment must not require rewriting existing rows).

- **AC.SE.7 — Objective-manifest table refuses malformed rows structurally.** Insertion of a row with empty `component`, empty `ac_id`, or empty `source_path_glob` is refused at the API boundary with a structured error. Insertion of a row whose `source_path_glob` is not a valid fnmatch pattern is refused (validation at write time, not at query time). The refusal is observable to the caller without requiring a schema-internal exception leak.

- **AC.SE.8 — `<workspace>/.pos/` sentinel directory is gitignored.** Either via repo-level `.gitignore` (top-level entry for `.pos/`), per-workspace `.gitignore` written by first-run scaffold, or per-component `.gitignore` already in place (builder picks the lowest-friction shape per existing conventions; the existing `<workspace>/.pos/first-run.state` is created by `hands-off-lifecycle` and is currently *not* explicitly gitignored — see §10 halt-trigger 1 — so the builder may need to add the entry, which is a doc/dev-discipline edit per D1, not a sealed-component amendment).

- **AC.SE.S — Seal-diff confined to fence.** The seal-diff window for A1 contains only edits under `objective-tracker/{src,tests,seals}/`, `hands-off-lifecycle/{hooks,tests,seals}/`, and the universal-paths admissions (`docs/rebuild/plans/`, `CLAUDE.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/FUTURE_IDEAS.md`, `.gitignore` if AC.SE.8 lands a top-level entry). Non-fence consumers (`tools/loam-mode/`, `tools/<active-scope-sentinel-writer>/`) are dev-discipline paths if they need any edits at all. `objective-tracker` is the H19-frozen-baseline-aware sealed component for this amendment per the existing `frozen_baseline` manifest field set per-component.

### Behaviour-count check (forward)

| # | Declared behaviour in §1 / §4 | AC |
|---|---|---|
| 1 | Workspace-mode bit queryable from hook context | AC.SE.1 |
| 2 | Active-scope sentinel writer surface | AC.SE.2 |
| 3 | Active-scope sentinel reader surface (with malformed-handling) | AC.SE.3 |
| 4 | Corpus-load sentinel SessionStart hook writer | AC.SE.4 |
| 5 | Mode-honouring required-corpus computation | AC.SE.5 |
| 6 | Objective-manifest table positive surface (insert + queries) | AC.SE.6 |
| 7 | Objective-manifest table negative surface (refuse malformed) | AC.SE.7 |
| 8 | `<workspace>/.pos/` directory is gitignored | AC.SE.8 |
| 9 | Seal-diff confinement | AC.SE.S |

**Behaviours = 9, ACs = 9.** Match. (AC.SE.S counts as both the "no edits outside fence" and "edits inside fence are admitted" — single seal-diff invariant per existing convention.)

### Behaviour-count check (reverse)

The reverse direction (every code path / branch / dep / test in the diff traces back to AC.SE.x) is exercised in the builder plan's §2.5 reverse-direction audit at build time. This plan asserts the audit will run; the builder records its outcome.

---

## 5. Hard constraints

1. **Dependency fence.** Source-edit scope: `objective-tracker/{src,tests,seals}/`, `hands-off-lifecycle/{hooks,tests,seals}/`. Any edit to other sealed components is a halt trigger. Non-fence consumers (`tools/loam-mode/`, `tools/<active-scope-sentinel-writer>/`, `.gitignore` adjustment) are explicitly permitted as dev-discipline paths per D1.
2. **Reversibility.** Fully reversible. The substrate is additive: a new table in `objective-tracker` with no existing-row migration; a new SessionStart inner hook registered through the existing `extra_inner_hooks` registry (revertible by removing the entry); new sentinel files in `<workspace>/.pos/` that absent installations simply lack. No retraction of any existing surface.
3. **Budget.** SessionStart inner hook 5s timeout (matches #45/#46 precedent). Sentinel writer p95 < 200ms (matches the research §6.1 AC.SE.1 timing target). Manifest API call p95 < 50ms for single-row insert/query against the existing `objective-tracker` SQLite WAL.
4. **Fail-closed direction.** Sentinel writer failures are observable (returned via a structured-result dataclass like #37's `AgentFileWriteResult` and #47's `MCPJsonWriteResult`) but never raise into the SessionStart hook; the hook exits 0. Manifest API failures DO raise to the caller — refusal to insert a malformed row is a deterministic structural refusal (§AC.SE.7), not graceful degradation. This split matches the research §3.6 + §4.4 envelope.
5. **No `--amend`.** Corrective commits only (per `feedback_no_amend_in_agent_dispatches`).
6. **ODD §2.5.** Every code path, branch, dependency, and test in A1's diff traces back to AC.SE.1–AC.SE.S. The builder runs the §2.5 reverse-direction audit before seal.
7. **No new top-level objective.** The research artefact (§9) confirmed line 134–135's binding is sufficient; A1 does not require spec amendment.
8. **No method prescription.** This plan-doc names outcomes; the builder plan picks file paths, module names, schema column names, validator shapes, exact CLI surface, sentinel-file JSON keys (within the documented minimum set in §4 ACs), and the hook-vs-library shape of the workspace-mode helper.
9. **A2/A3/A4 may not force A1 redesign.** If during A2/A3/A4 design or build, a substrate change becomes necessary (e.g. the manifest schema needs an additional column, or the active-scope sentinel needs a new field), that change is a NEW amendment to A1's surface — it is NOT folded into A2/A3/A4. The substrate is a sealed contract after A1.
10. **Backwards-compat.** Workspaces lacking the substrate (e.g. workspaces last touched before A1 lands) continue to function exactly as today. The corpus-load sentinel's absence is an allowed state for any consumer that doesn't yet exist (A1 ships no consumer); the active-scope sentinel's absence is a declared state (`scope_id: null` semantics — A2 will define whether absence = deny or absence = allow, not A1).
11. **Sealed-component dispatch must explicitly name `pos-amend apply`** as the bookkeeping mechanism for the seal-diff window per `feedback_dispatch_explicit_pos_amend_apply`.

---

## 6. D-decisions for this plan (record + rationale)

The five programme-level D-decisions are LOCKED 2026-04-26 (see header). This section records the A1-level design choices that follow from those locks; **none are open for builder challenge** — they bound the builder plan's authoring surface.

### D-A1.1 — Sealed-component fence (governed by D3)

**Lock:** `objective-tracker` + `hands-off-lifecycle`. Two sealed components.

`objective-tracker` is the natural home for the manifest table per D3 (the existing SQLite store + projection + event-log surface accommodate the new table without architectural refactor). `hands-off-lifecycle` is the natural home for the corpus-load sentinel writer because it owns the SessionStart hook composition surface (`merge_session_start` + `extra_inner_hooks` registry) and the existing `first_run_state.py` sentinel-writer pattern that the new writer mirrors. A standalone `structural-enforcement/` peer component was named as a possibility in the research artefact (§Q1); D3's lock governs against it (the manifest belongs in objective-tracker; the hook belongs in hands-off-lifecycle).

### D-A1.2 — Active-scope sentinel writer location

**Lock:** non-fence consumer under `tools/` (e.g. `tools/pos-scope/` or extension to existing `tools/pos-amend/`); builder plan picks the exact home.

The writer is a developer-tool entry point invoked by agents at scope-start; it is not part of the runtime surface any user-facing harness consumes. Per D1's dev-discipline carve-out, `tools/` is excluded from objective-binding so the writer itself doesn't need a manifest entry. Builder plan documents whether to extend `pos-amend` (which already authors plan-files at scope-start) or stand up a new `pos-scope` CLI; rationale-cost trade-off recorded in builder plan §D-build.x.

### D-A1.3 — Workspace-mode bit consumer

**Lock:** existing `loam-mode` selector surface (`tools/loam-mode/src/loam_mode/session_start.compute_session_mode`). Consumer-only; no edits to `loam-mode` source unless a halt-trigger surface gap is found (§10 trigger 4).

The bit already has a canonical computation site (per `loam-mode`'s sub-plan F machinery); A1 adds a consumer, not a producer. If `loam-mode` needs a new export (e.g. a synchronous `read_workspace_mode(workspace_root) -> str` helper that hides the contract-read internals), the builder confirms it can be added without sealed-component amendment — `tools/loam-mode/` is dev-discipline per `dev-mode-manifest.yaml`.

### D-A1.4 — Sentinel directory

**Lock:** `<workspace>/.pos/` (extends the existing first-run-state namespace at `<workspace>/.pos/first-run.state`). Sub-paths: `<workspace>/.pos/active-scope.json` and `<workspace>/.pos/session-state/<session_id>.json`.

The namespace already exists (#29's per-workspace memory port carries on the same pattern); A1 is consistent. The session-state subdirectory's per-session-id JSON files will accumulate over time; A1 does NOT define rotation/garbage-collection — that is deferred to a future amendment (out of scope per §7).

### D-A1.5 — No new top-level objective

**Lock:** confirmed by research §9. Line 134–135 of `pos-v2-objectives-spec.md` is the binding objective; A1 satisfies the audit-substrate clause-(a) along with the rest of the four-amendment programme.

---

## 7. Out of scope (explicit per ODD §2.5)

The four-amendment programme decomposition (research §6) names A2/A3/A4 explicitly; A1 declares each as a future amendment. Nothing below lands in A1.

- **A2 — `objective-binding-gate`.** The PreToolUse Edit/Write hook that consults A1's manifest + sentinel and denies edits without an AC binding. A1 ships zero gate code; A2 owns the entire gate-decision surface.
- **A3 — `tdd-guard-test-first`.** The PreToolUse Edit/Write hook that requires a matching `test_<AC>_*.py` to exist before the source edit. Depends on A2's manifest binding mechanism.
- **A4 — `bash-and-agent-context-guards`.** The Bash-tool + Agent-tool guards (`git commit --amend` blocker, WD-verification, `pos-amend apply --dry-run` exit-0 commit gate, secret-file commit blocker). Depends on A1's workspace-mode bit (DEV-MODE-only gates per D4) and on A1's audit-log writer surface for shared logging.
- **Audit-log retention/rotation.** Research §11 Q2: weekly rollup of JSONL into objective-tracker events with truncation. A1 ships no audit log (no gate decisions to log); the design lands with A2.
- **Cross-amendment manifest queries.** "Show me all ACs A20 covers across components" (research §10 D3 motivation). A1 ships the table + per-component/per-AC queries; cross-amendment historical queries are a later layer.
- **DEV-MODE-only-vs-universal partition for individual gates.** D4 declares the principle (secret/blast-radius universal; ODD-discipline DEV-MODE-only) but the gate-by-gate placement is A4's design surface.
- **Sentinel garbage collection.** The `<workspace>/.pos/session-state/<session_id>.json` files accumulate; rotation is a later amendment.
- **Persona-side surfacing of corpus-load sentinel into `additionalContext`.** A1's sentinel format is consumption-ready (per Lens 1), but the actual emission via #46's persona session-start emitter is a future composition, not A1's work.
- **Audit-on-clause-(b) — arbitrary decision lint surface.** Spec line 135-(b) is satisfied as a later byproduct of the gate audit logs (research §8); A1 contributes the sentinel + manifest substrate that make the lint surface possible, but A1 does not define the lint format itself.

---

## 8. Halt triggers

Halt and surface (do not silently extend) when any of the following fires:

1. **`<workspace>/.pos/` is not safely gitignored across the workspace family.** Verification at A1 build start — if the existing `.pos/first-run.state` files are tracked anywhere, A1 needs to add a top-level `.gitignore` entry as part of AC.SE.8, which is a universal-paths admission. Halt and surface if the gitignore shape is unclear; do not silently land an edit.
2. **`objective-tracker`'s schema-evolution surface cannot accept the new table without a contract change.** Per the §10 halt-and-surface clause: if extending `objective-tracker` requires changing a public API surface that other sealed components consume, that's an A1 redesign, not an extension. Halt and signal back to owner; the alternative is a peer `structural-enforcement/` component, which contradicts D3 — owner must rule before either path advances.
3. **`hands-off-lifecycle`'s `merge_session_start` + `extra_inner_hooks` registry cannot accept the new corpus-load inner hook without a contract change.** Same shape as halt-trigger 2. The registry is the surface #45/#46 already added through; if the registry is insufficient, halt and signal.
4. **`loam-mode` does not expose the workspace-mode bit synchronously enough for a SessionStart hook to consume in <200ms.** Verification: read `tools/loam-mode/src/loam_mode/session_start.py` against the timing target. If the existing `compute_session_mode` + `read_dev_intent_safe` path is too slow (e.g. requires async runtime, requires Claude SDK invocation), halt and signal — A1 cannot land a sentinel writer that exceeds the SessionStart budget.
5. **An ODD §2.5 violation surfaces in surrounding code during A1 build.** The substrate's adjacent code (objective-tracker schema, hands-off-lifecycle hooks) may contain pre-existing §2.5 violations the build's verification pass uncovers. Halt-and-surface per the dispatch's explicit ODD-violation clause; do not silently extend.
6. **An AC the builder cannot author outcome-shaped surfaces.** If during the builder plan's authoring some A1 behaviour resists outcome-shaping (a method prescription is the only natural form), halt and signal back — the AC's wording may need owner ruling before build proceeds.
7. **A2/A3/A4 design surfaces a substrate change A1 has not anticipated.** Per constraint 9: the substrate is sealed after A1. If during A2 plan-authoring the manifest's schema needs an additional column, halt and signal back — that's a NEW amendment to A1's surface (an A1.1 corrective), not folded into A2.

---

## 9. Decisions for owner (only genuinely uncertain)

The five programme-level D-decisions are LOCKED 2026-04-26 (see header) and not surfaced here. The A1-level D-decisions in §6 are LOCKED by the research artefact + the programme-level locks and are not surfaced here.

**No A1-level decisions remain uncertain at plan-authoring time.** The research artefact resolved all five surfaced decisions; the locked D-decisions cover the substrate's shape end-to-end; the dispatch named A2/A3/A4 as out-of-scope.

Two adjacent questions surfaced during plan authoring may want owner attention but are NOT load-bearing for A1 dispatch:

- **Q-adj.1 — Sentinel directory `.gitignore` shape (AC.SE.8).** Top-level entry vs per-workspace first-run-scaffold-authored entry. Recommendation: top-level (one-line addition; covers every workspace using the namespace). Builder confirms in builder plan.
- **Q-adj.2 — Active-scope sentinel writer's home (D-A1.2).** Extend `tools/pos-amend/` (already authors plan-file machinery) vs new `tools/pos-scope/` CLI. Recommendation: extend `pos-amend` — keeps the scope-start machinery in one place, no new tool to maintain. Builder confirms.

Neither blocks A1 dispatch. Both can be answered in the builder plan without a return to the owner.

**Decisions surfaced for owner ruling: 0.**

---

## 10. Risks

- **R1 — Substrate shape lock-in.** A1's sealed-after-A1 contract (constraint 9) means a wrong choice of manifest column set or sentinel JSON shape costs an A1.1 corrective amendment, not a routine A1 amendment. Mitigation: the builder plan's §D-build choices are explicitly graded for forward-compatibility (manifest schema reserved-for-future columns; sentinel JSON additive-only post-A1).
- **R2 — Hook budget creep at SessionStart.** A1's corpus-load hook adds ~50–150ms to every session-start; #45/#46/loam-mode already contribute to the inner-hook chain. The 5s SessionStart budget envelope is generous, but observability matters. Mitigation: AC.SE.4's < 5s envelope is measured at build time; if the cumulative inner-hook chain creeps past 2s, surface the trend.
- **R3 — `objective-tracker` schema migration on existing workspaces.** A new table in the SQLite store needs to be created on first-load against existing databases. Mitigation: `CREATE TABLE IF NOT EXISTS` semantics already used by `objective-tracker`'s schema (per `store.py::_SCHEMA`); no destructive migration. The risk surfaces only if a column type needs changing post-A1, which is the constraint-9 scenario.
- **R4 — Sentinel-file proliferation.** `<workspace>/.pos/session-state/<session_id>.json` accumulates one file per Claude Code session. Long-lived workspaces may collect thousands of files. Out-of-scope-for-A1 (§7) but tracked: a future garbage-collection amendment.
- **R5 — Workspace-mode bit fail-closed-to-permissive.** AC.SE.1 names the fail-closed-to-`normal-use` direction. This is the correct shape for DEV-MODE-only gates (a derived workspace without the persona contract should NOT trip ODD-discipline gates), but it means a corrupted persona contract on a real DEV MODE workspace silently degrades to NORMAL USE — gates won't fire when they should. Mitigation: a future amendment (NOT A1) may add an explicit `mode_resolution_failed` sentinel state for observability; A1 ships only the two-value surface.
- **R6 — D3-vs-Q1 (research §11) tension.** Research §11 Q1 noted "is `structural-enforcement/` a new sealed peer component, or a sub-component within `hands-off-lifecycle/`?" D3 locks the manifest into `objective-tracker`. The corpus-load sentinel writer lands in `hands-off-lifecycle/hooks/`. There is no `structural-enforcement/` peer; the substrate is distributed across two existing sealed components. This is the correct shape per the locks but creates a discoverability question for future contributors. Mitigation: A1's seal narrative (`objective-tracker/seals/SEAL_COMMIT.<slug>` and `hands-off-lifecycle/seals/SEAL_COMMIT.<slug>`) names the cross-component substrate explicitly so a future contributor reading either seal sees the other.

---

## 11. Bookkeeping

- **Plan-doc:** this file at `docs/rebuild/plans/structural-enforcement-a1-substrate.md`.
- **Research artefact:** `docs/rebuild/plans/research/structural-enforcement-of-critical-requirements-research.md` (locked 2026-04-26; governs).
- **Builder plan:** to be authored by the build agent post-owner-approval at `docs/rebuild/plans/structural-enforcement-a1-substrate.builder-plan.md`. Contains files-touched, symbol-level details, AC-to-test mapping, D-build choices, §2.5 reverse-direction audit, halt-trigger checks, pos-amend bookkeeping flow.
- **Manifest:** to be authored alongside the builder plan at `docs/rebuild/plans/structural-enforcement-a1-substrate.manifest.yaml`. Two-component manifest (`objective-tracker`, `hands-off-lifecycle`), `frozen_baseline: false` for `objective-tracker`, `frozen_baseline: true` for `hands-off-lifecycle` (H19 is frozen per amendment #23). Universal-paths block as standard (`docs/rebuild/plans/`, `CLAUDE.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/FUTURE_IDEAS.md`, plus `.gitignore` if AC.SE.8 lands a top-level entry).
- **Pos-amend bookkeeping flow** (per `feedback_dispatch_explicit_pos_amend_apply`):
  1. Author manifest at `docs/rebuild/plans/structural-enforcement-a1-substrate.manifest.yaml` with the correct BASELINE (HEAD~1 of the upcoming amendment commit per the established #29/#34/.../#47 pattern).
  2. Author all source edits + tests; commit as the amendment commit on branch `pos-v2`.
  3. `pos-amend apply --dry-run <manifest>` — must exit 0.
  4. `pos-amend apply <manifest>` — advances BASELINE literals + widens seal-diff bindings + writes SEAL_COMMIT sidecars.
  5. `pos-amend seal --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/rebuild/plans/structural-enforcement-a1-substrate.builder-plan.md <manifest>` — runs the scoped test sweep, creates the seal commit, advances SEAL_COMMIT to the seal commit, appends builder-plan §SHA backfill follow-up commit.
  6. Verify: `pos-amend apply --dry-run <manifest>` exits 0 against post-seal HEAD.
- **Seal-diff window:** BASELINE = HEAD~1 of amendment commit (set in builder plan after dispatch). Allowed paths under the window: `objective-tracker/{src,tests,seals}/`, `hands-off-lifecycle/{hooks,tests,seals}/`, plus universal admissions.
- **Programme tracking:** A1 unblocks A2 (which depends on A1's manifest + sentinel) and A4 (which depends on A1's workspace-mode bit). A3 depends on A2. The four amendments serialise per `feedback_serialize_amendment_builds` (no parallel builds in canonical tree until pos-amend worktree-isolation is verified).

---

## 14. Method-decision register (post-build, builder-backfilled)

Method-level decisions made during the build land here at
seal time per `pos-amend seal --plan-doc` convention. Empty
at plan-author time.

### Commit SHAs

- Amendment commit: `b3218b4309bc755c91366e4203f55c38a8f8e0d6` —
  `feat(structural-enforcement-a1): substrate (workspace-mode + sentinels + objective-manifest table)`
- Apply commit: `c41da3ad8593cc888fa546f49401523256926913` —
  `chore(objective-tracker, hands-off-lifecycle): advance BASELINE + SEAL_COMMIT for structural-enforcement-a1 window`
- Corrective commit: `97f78290f6a810957dc0bd0c8a6a1d4b96524f65` —
  `chore(hands-off-lifecycle): repair stale AC37.6 sentinel-prose test (method-coupling cleanup)`
- Seal commit: `d4dcfa91764a1a270aec7a91c3c94e432bc71571` —
  `chore(seals): structural-enforcement A1 substrate (workspace-mode + sentinels + objective-manifest table) — objective-tracker+hands-off-lifecycle at 97f7829`

---

*End of plan-doc. Builder plan + manifest authored after owner approval.*
