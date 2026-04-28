# Corpus-inlining SessionStart hook (failure-class elimination per ODD §5.1.1)

**Status:** authored 2026-04-28 (plan-doc only; no code, no commits, no manifest yet).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**FIDRAFT origin:** `docs/rebuild/FUTURE_IDEAS_DRAFT.md` entry "SessionStart corpus_gate should inline corpus content into additionalContext, not just verify presence" (captured 2026-04-28; relocated from pos3/framework dirty FIDRAFT during post-#68 sync recovery).
**Research artefact:** `docs/rebuild/plans/research/corpus-inlining-session-start-hook-research.md` (locked 2026-04-28; governs the inline-strategy + token-budget findings).
**Composes on:** A1 substrate (`hands-off-lifecycle/hooks/corpus_load_sentinel.py` + `corpus_load_session_start.py`); #45 `extra_inner_hooks` registry; #46 persona session-start emitter; #67 `_resolve_corpus_path` reader fall-through.

---

## 1. Summary / TLDR

The hook reads the always-load corpus from the workspace (mode-aware via A1's `workspace_mode` + `compute_corpus_paths_required`), emits the file contents into Claude Code's SessionStart `additionalContext` channel, and updates A1's sentinel `corpus_paths_loaded` to record what entered context. The persona observes the corpus *already loaded* on every DEV MODE session-start. NORMAL USE workspaces no-op (mode-bit gates the work).

After this hook lands, "always read corpus at session-start" stops being an advisory rule in MEMORY.md prose and becomes a substrate property — the model has the bytes in context the moment the session opens. Per ODD §5.1.1 this is *elimination* of the failure class (the failed state — corpus-not-in-context — becomes unrepresentable on a successful hook fire), not relocation.

The recurring miss this targets: persona observes A1's `[present]` dossier markers, sees `corpus_gate_state: loaded`, and acts on the user's prompt without firing Read against the corpus files. Luke flagged the miss explicitly today ("you literally never do it"). The substrate guarantees the *paths* are present today; this hook makes the *contents* present.

Fence is **one sealed component**: `hands-off-lifecycle/{hooks,tests,seals}/`. The hook composes on existing primitives only; the substrate change is small (a single new hook + minimal A1 surface extension to accept a `corpus_paths_loaded` argument on `write_corpus_load_sentinel`, additive-only).

---

## 2. Spec-objective placement (per CLAUDE.md §2.5)

**Named spec objectives this plan satisfies:**

- **`docs/rebuild/spec/pos-v2-objectives-spec.md` line 134–135 — Deterministic (tiered).** Additional acceptance line 135-(a): *"for any decision currently implemented as a rule/prompt where a deterministic hook/script could produce the same outcome, an audit surfaces it."* The corpus-load discipline is rule #10 in the structural-enforcement audit (`docs/rebuild/plans/research/structural-enforcement-of-critical-requirements-research.md` §2 row 10) — flagged PROMOTE under A1 substrate. A1 shipped the sentinel (paths-required + state machine); this hook ships the content inlining that completes the structural promotion.

- **VALUE_PROPOSITION.md prime objective.** Per `feedback_value_proposition_as_prime_objective`: every component/feature ladders up to the two VALUE_PROPOSITION tests. This hook reduces the persona's translation burden directly (the persona stops needing to remember-then-execute the corpus-read) AND adds to the harness toolkit (every dispatch the persona makes inherits the corpus context without per-dispatch re-reads). Both Lens 2 tests satisfied.

**Sealed-component fence:**

- `hands-off-lifecycle` — new SessionStart inner hook (`hooks/corpus_inline_session_start.py` or similar) + minimal extension to `corpus_load_sentinel.py` (additive `corpus_paths_loaded` argument on `write_corpus_load_sentinel`; no breaking change).

The fence is **one sealed component** in normal shape. Path-resolver helper duplicates the 3-line `_resolve_corpus_path` logic per the precedent A1 set with `WORKSPACE_STATE_SUBDIR` (D-CI.4 in research; see §6 D-build.2). Workspace-mode bit reuses A1's `workspace_mode` consumer-only. Manifest read reuses A1's `compute_corpus_paths_required` consumer-only. **No edits anticipated outside hands-off-lifecycle's fence.**

**ODD §2.5 reverse direction.** Every code path, branch, dependency, and test in the diff traces back to a named AC under §4. No silent branches; no defensive `if`s without backing AC.

---

## 3. Three-lens analysis

### Lens 1 — Claude-leverage

*Required research question: what Claude capability does this lean on or extend?*

The hook leans on three Claude Code primitives end-to-end:

- **SessionStart inner-hook surface** + **`additionalContext` channel** — the canonical place to seed model context at session-start. Same surface A1, #45 (loam-mode), #46 (persona) already use. The new hook is the **fourth** concrete consumer of the registry.
- **`extra_inner_hooks` registry (#45)** — registration is a one-line addition to `hands-off-lifecycle/hooks/first_run_helper.py` (or wherever the SessionStart stanza is composed for first-run / supervisor registration). The marker substring joins `_POS_V2_COMMAND_MARKERS` so re-merge recognises it as pos-v2-owned.
- **A1's `workspace_mode` bit** + **A1's sentinel** — workspace-mode partition + the proof-of-read record. The hook composes on the substrate, does not re-invent it.

This is a recursive instance of the structural-enforcement programme research's asymmetric finding: *Claude Code's hook surface IS the structural-enforcement surface.* Corpus-load discipline becomes structural by being expressed as a SessionStart contributor — exactly the pattern A1/A2/A3/A4 already use. No new substrate; one more consumer of an existing one.

### Lens 2 — Harness + primary-persona value

*Primary-persona test: does this reduce the translation burden between the user's natural-language intent and AI-effective execution?*

**Yes — directly.** Today the persona must remember the rule "always read the corpus before any non-trivial pos-v2 turn" (lives in MEMORY.md prose; relocated-not-eliminated per ODD §5.1.1). The hook makes the corpus *already loaded* — no rule to remember, no Read-tool dispatch at session-start, no failure mode if the rule is forgotten. The translation burden drops to zero for the corpus-load step.

*Harness test: does this add to the toolkit the primary persona can draw from?*

**Yes — `corpus is in context` becomes a session-level harness primitive.** Every dispatch the persona makes inherits the always-load corpus without a per-dispatch Read call. The dispatch overhead drops; the per-dispatch corpus-read cost is paid once at session-start, not N times across the session.

### Lens 3 — ODD authoring

The hook is structurally shaped, not advisory. The ACs below are outcome-shaped: the SessionStart contributor's stdout content satisfies a deterministic shape contract; A1's sentinel shows `corpus_paths_loaded` populated; mode-partition refusal is deterministic. Method (file paths, exact module names, exact stdout format, ceiling literal values) is the builder's call and lives in the builder plan.

---

## 4. Acceptance criteria

The outcome is the substrate's observable state: corpus content reaches `additionalContext` on every DEV MODE session-start; A1's sentinel records what was loaded; NORMAL USE workspaces no-op; cumulative behaviour is bounded by the SessionStart inner-hook envelope. Eight ACs cover the behaviours plus the seal-diff invariant.

- **AC.CI.1 — Always-load corpus content reaches `additionalContext` (DEV MODE).** On a SessionStart fan-out in a workspace where the mode bit (A1's `workspace_mode`) returns `dev-mode`, the new hook emits to stdout an `additionalContext`-shaped payload that contains the literal byte content of every always-load corpus file (per the partition decision recorded in §6 D-build.1). The contents are emitted with per-file delimiters (path label + content + boundary marker — exact shape is the builder's call); the model can disambiguate one file from another. Files absent from disk are emitted with a structured `[missing]` marker carrying the workspace-relative path; their content is omitted.

- **AC.CI.2 — On-demand-tier path-pointer block emitted (DEV MODE).** On a DEV MODE session-start, the hook ALSO emits a structured pointer block listing the workspace-relative paths of every on-demand-tier corpus file (per §6 D-build.1) — the persona reads on-demand via the Read tool. The pointer block carries one entry per on-demand file; entries are workspace-relative paths only (per §6 D-build.5; section-anchor extraction is a follow-on). Missing on-demand files are omitted from the pointer block (no `[missing]` marker — that is the always-load tier's contract).

- **AC.CI.3 — Mode-partition refusal (NORMAL USE → no-op).** On a SessionStart fan-out in a workspace where `workspace_mode` returns `normal-use`, the hook fires, observes the mode bit, and exits 0 with empty stdout. No `additionalContext` emission; no error; no sentinel update. The persona's existing #46 dossier remains the NORMAL USE shape unchanged.

- **AC.CI.4 — A1 sentinel `corpus_paths_loaded` populated (DEV MODE).** After the new hook runs in DEV MODE, A1's sentinel file at `<workspace>/workspace/.pos/session-state/<session_id>.json` has `corpus_paths_loaded` populated with the workspace-relative paths the hook actually inlined — the always-load files that existed and were emitted. The sentinel `state` field reflects the loaded subset (`loaded` if every required path was inlined; `partial` if some required paths were absent; `missing` if none could be loaded). Path-existence semantics match A1's `_classify_corpus_state`. The sentinel update is atomic per A1's existing write contract (`.tmp` + `os.replace`).

- **AC.CI.5 — Path-resolver fall-through (`<workspace>/<rel>` then `<workspace>/framework/<rel>`).** The hook's corpus-content reads probe the workspace-root path first; on absence, probe `<workspace>/framework/<rel>`. Fall-through behaviour matches #67's `_resolve_corpus_path` contract bit-for-bit: workspace-root copy wins; framework-only-clone shape (canonical-clone scaffolded by `pos-new-workspace`) is supported transparently. Behaviour is verified against both shapes (workspace-root copy present; framework-only branch shape).

- **AC.CI.6 — Per-file size ceiling and truncation marker.** A per-file ceiling (literal value picked in §6 D-build.3; recommendation 50 k chars) caps the inlined content per file. Files exceeding the ceiling have their content truncated at the ceiling boundary and a structured `[truncated at N chars; full file at <path>]` marker emitted. The hook does not refuse to emit other files when one truncates. The ceiling is observable from the hook's emitted text (the marker is byte-grep-able in tests).

- **AC.CI.7 — SessionStart envelope and fail-soft.** The hook completes within the 5 s SessionStart inner-hook budget (matches A1 / loam-mode / persona precedent) and exits 0 on every path. Environmental failures (file unreadable, sentinel write failure, manifest absence) degrade gracefully: the always-load file's content slot becomes `[missing]` or is omitted; A1's sentinel `state` reflects the degradation; the hook never raises into Claude Code's SessionStart fan-out.

- **AC.CI.S — Seal-diff confined to fence.** The seal-diff window contains only edits under `hands-off-lifecycle/{hooks,tests,seals}/` plus the universal-paths admissions (`docs/rebuild/plans/`, `CLAUDE.md` if a README pointer is added, `docs/odd-methodology.md` is read-only, `docs/rebuild/FUTURE_IDEAS.md` for the FIDRAFT graduation). `hands-off-lifecycle` is H19-frozen-baseline-aware per amendment #23 — `frozen_baseline: true`. No edits outside the fence.

### Behaviour-count check (forward)

| # | Declared behaviour in §1 / §4 | AC |
|---|---|---|
| 1 | Always-load corpus content emitted to `additionalContext` (DEV MODE) | AC.CI.1 |
| 2 | On-demand pointer block emitted (DEV MODE) | AC.CI.2 |
| 3 | NORMAL USE no-op (mode-partition refusal) | AC.CI.3 |
| 4 | A1 sentinel `corpus_paths_loaded` populated post-fire | AC.CI.4 |
| 5 | Path-resolver fall-through (#67 contract reuse) | AC.CI.5 |
| 6 | Per-file size ceiling + truncation marker | AC.CI.6 |
| 7 | SessionStart envelope + fail-soft on every error path | AC.CI.7 |
| 8 | Seal-diff confinement | AC.CI.S |

**Behaviours = 8, ACs = 8.** Match.

### Behaviour-count check (reverse)

The reverse direction (every code path / branch / dep / test in the diff traces back to AC.CI.x) is exercised in the builder plan's §2.5 reverse-direction audit at build time. This plan asserts the audit will run; the builder records its outcome.

---

## 5. Hard constraints

1. **Dependency fence.** Source-edit scope: `hands-off-lifecycle/{hooks,tests,seals}/`. Any edit to other sealed components is a halt trigger. A1's `corpus_load_sentinel.py` extension is in-fence (same component). Path-resolver duplication is in-fence (no cross-component edit).
2. **Reversibility.** Fully reversible. The hook is additive: a new SessionStart inner-hook entry registered through the existing `extra_inner_hooks` registry (revertible by removing the entry); a new module under `hands-off-lifecycle/hooks/` (revertible by deleting the file); A1 sentinel extension is additive (default-empty argument; old call sites still work). No retraction of any existing surface.
3. **Budget.** SessionStart inner hook 5 s timeout (matches A1 / #45 / #46 precedent). Disk reads of the always-load corpus tier on local SSD: <20 ms expected (research §3, §8.4). The 5 s envelope is generous by ~250×.
4. **Token budget.** Per-session inline cost bounded by the always-load partition decision (§6 D-build.1). Recommendation: lean tier ~6.8 k tokens per session-start. Hard upper bound on per-session emission: configurable per-file ceiling × always-load file count (§6 D-build.3). Token-cost creep across future amendments is mitigated by the partition-source being the existing manifest — every always-load addition gates through a new manifest amendment.
5. **Fail-closed direction.** Hook failures are fail-soft per the SessionStart contract — exit 0, emit what can be emitted, mark missing/degraded files in the sentinel. The hook NEVER raises into Claude Code's SessionStart fan-out. This matches A1's pattern (`return 0` on every error path in `corpus_load_session_start.py::main`).
6. **No `--amend`.** Corrective commits only (per `feedback_no_amend_in_agent_dispatches`).
7. **ODD §2.5.** Every code path, branch, dependency, and test in the diff traces back to AC.CI.1–AC.CI.S. The builder runs the §2.5 reverse-direction audit before seal.
8. **No method prescription.** This plan-doc names outcomes; the builder plan picks file paths, module names, exact stdout format (delimiter strings, label shapes), per-file ceiling literal value, sentinel update mechanism (extend `write_corpus_load_sentinel` signature vs. add a sibling `update_corpus_paths_loaded` function — both shapes satisfy AC.CI.4).
9. **A1 substrate compatibility.** A1's `write_corpus_load_sentinel` accepts an optional `corpus_paths_loaded` argument (or an equivalent additive surface) post-amendment. If A1's surface cannot extend additively (halt-trigger 2), an A1.1 corrective lands first. The contract direction is fixed: A1 owns the sentinel; this hook updates fields A1 owns.
10. **Mode-partition compliance.** The hook's DEV-MODE-only behaviour matches A1 D4 (ODD-discipline gates DEV-MODE-only). NORMAL USE workspaces fire the hook, observe mode, exit 0 with empty stdout — no exceptions to this contract.
11. **Sealed-component dispatch must explicitly name `pos-amend apply`** as the bookkeeping mechanism for the seal-diff window per `feedback_dispatch_explicit_pos_amend_apply`.
12. **Backwards-compat.** Workspaces lacking the new hook continue to function exactly as today (A1 substrate persists; persona dossier persists). Workspaces with the hook installed but lacking the `dev-mode-manifest.yaml` (manifest absent) degrade per A1's manifest-absent path: empty `corpus_paths_required` → no inlines emitted → sentinel `state == "missing"`. No crash.

---

## 6. D-decisions for this plan (record + rationale)

The research-doc named four D-CI decisions (D-CI.1, D-CI.2, D-CI.3, D-CI.4) and four open questions (D-CI.5, D-CI.6, D-CI.7, D-CI.8). All are surfaced for owner ruling in §9. The decisions below are the build-author choices the builder picks during the build (D-build.x) — they shape mechanical form, not whether the feature exists.

### D-build.1 — Always-load partition source

**Lock:** consume A1's `compute_corpus_paths_required(workspace_root, mode)` directly. Always-load tier = the manifest's `always_loaded` set MINUS files unsuited to inline (per §9 D-CI.1 ruling). Builder applies the owner's D-CI.1 decision as a static set in the hook's source (not a manifest-tightening edit).

If owner rules **D-CI.1.(a) lean** → always-load tier = {`CLAUDE.md`, `docs/rebuild/VALUE_PROPOSITION.md`, `docs/rebuild/STATE.md`}.
If owner rules **D-CI.1.(b) widened** → always-load tier = lean ∪ {`docs/odd-methodology.md`, `docs/odd-in-pos.md`}.
On-demand tier = the manifest's `always_loaded` ∪ `dev_only` set MINUS the always-load tier MINUS non-document globs (component source globs in the manifest are not corpus; the hook filters them per file-extension `.md|.yaml|.txt|.toml`).

### D-build.2 — Path-resolver helper

**Lock:** duplicate the 3-line `_resolve_corpus_path` logic inside `hands-off-lifecycle/hooks/` (per D-CI.4 recommendation). No cross-component edit; no shared util. Match A1's precedent with `WORKSPACE_STATE_SUBDIR`. Tests verify fall-through behaviour against the same test fixtures #67 used.

### D-build.3 — Per-file size ceiling

**Lock:** 50 k chars per file (research §8.2 + §11 D-CI.7 recommendation). Largest current always-load file is 11 k; 50 k buys 4.5× headroom and surfaces the truncate path if a corpus file ever grows that large. Truncate marker: `[truncated at <N> chars; full file at <workspace-relative-path>]` (exact format is builder's call).

### D-build.4 — Hook ordering in SessionStart fan-out

**Lock:** A1 → corpus-inline → persona (per D-CI.6 option (a)). The persona's dossier reads A1's sentinel; corpus-inline updates the sentinel BEFORE persona reads it; persona dossier reflects the up-to-date `corpus_paths_loaded`. Future micro-amendment can grow a `corpus_inlined: true|partial` marker in the persona dossier without re-ordering.

### D-build.5 — On-demand tier shape

**Lock:** path-pointer block ONLY (workspace-relative paths). Section-anchor extraction (research §5.4 hybrid + §11 D-CI.2) is a follow-on amendment, not this hook's scope. Owner-rule via D-CI.2 may revisit; default is bare paths, matching the existing #46 dossier shape.

### D-build.6 — A1 sentinel surface extension shape

**Lock:** the builder confirms whether A1's `write_corpus_load_sentinel` extends with an optional `corpus_paths_loaded` parameter, OR a new sibling `update_corpus_paths_loaded(workspace_root, *, session_id, paths)` function lands alongside. Both satisfy AC.CI.4. The builder picks whichever is the smaller diff against A1's existing module surface. **If A1's contract cannot extend additively without a breaking change to existing call sites, halt-trigger 2 fires and an A1.1 corrective lands first.**

### D-build.7 — Caching across sessions

**Lock:** none — re-emit every session per D-CI.3 recommendation. No cache substrate, no hash skip. The disk-I/O cost is sub-millisecond; per-session token cost is paid intentionally.

---

## 7. Out of scope (explicit per ODD §2.5)

Nothing below lands in this hook.

- **Section-anchor extraction for on-demand tier.** Research §5.4 hybrid (extract markdown headings + line ranges, emit alongside paths). A future micro-amendment can add it; this hook ships path-pointers only per D-build.5.
- **Compaction-resilient corpus load.** When the model's context compacts mid-session, the inlined corpus is discarded along with the rest of the session's pre-compact state. Re-loading after compaction is a PreCompact-hook or compaction-recovery problem, not this hook's. Out-of-scope; tracked elsewhere.
- **Caching across sessions.** Per D-CI.3 / D-build.7, the hook re-emits every session. A future amendment may add a content-hash cache if the disk-I/O cost or token-cost emerges as a real concern; today it's premature.
- **Persona dossier `corpus_inlined` marker.** The persona's #46 emitter could grow a one-line marker reflecting the new sentinel `corpus_paths_loaded`. Follow-on micro-amendment; out-of-scope here.
- **NORMAL USE corpus inlining (CLAUDE.md only).** A future amendment may widen the hook's universe to inline a CLAUDE.md-only payload in NORMAL USE workspaces (mirroring the persona's NORMAL USE dossier). Today NORMAL USE is no-op.
- **Manifest tightening.** The current `dev-mode-manifest.yaml` `always_loaded` set includes whole component-source globs (cost-governance/**, etc.) which are not corpus-shaped. The hook filters by file-extension; the manifest is not edited. A future amendment may introduce a dedicated "session-start essentials" manifest field if the always-load partition needs first-class manifest representation.
- **Audit-on-corpus-loaded.** Future ODD-discipline gates (A2 binding, A3 TDD-guard) may consult A1's sentinel to assert "the model has the corpus in context." This hook makes the assertion structurally honest by populating `corpus_paths_loaded`. The audit is a downstream gate's design surface, not this hook's.

---

## 8. Halt triggers

Halt and surface (do not silently extend) when any of the following fires:

1. **Pre-flight surfaces this hook already shipped.** Verification at build start: `git log --grep="corpus-inlining\|corpus.load.inline\|corpus.gate.inline"` returns only the FIDRAFT-capture commit (`76cec04` at plan-author time). If a later commit shipped the hook, halt and signal — the build is stale.
2. **A1's `write_corpus_load_sentinel` cannot extend additively.** If A1's existing signature requires a breaking change to accept the new field, halt and signal — A1.1 corrective lands first; this hook depends on the substrate it composes on.
3. **A1's `compute_corpus_paths_required` cannot be consumed without a contract change.** Same shape as halt-trigger 2 against the manifest-read surface.
4. **#67's `_resolve_corpus_path` semantics drift between primary-persona and the duplicated copy.** Build-time check: the test fixtures verifying fall-through must produce identical results against both implementations. If they diverge (e.g. primary-persona's helper grew a third probe path post-#67), halt — either lift to a shared util (D-CI.4 option (a) revisit) or align the duplicated copy.
5. **An ODD §2.5 violation surfaces in surrounding code during the build.** The substrate's adjacent code (hands-off-lifecycle hooks) may contain pre-existing §2.5 violations the build's verification pass uncovers. Halt-and-surface per the dispatch's explicit ODD-violation clause; do not silently extend.
6. **A SessionStart-budget breach is observable in test runs.** If the cumulative inner-hook chain (loam-mode + A1 + corpus-inline + persona) exceeds 2 s in a representative test, halt and surface — the 5 s envelope is at risk and a refinement is owed (e.g. async file reads, or partition tightening). Today's measured budget is well under, so this is a defensive halt.
7. **An AC the builder cannot author outcome-shaped surfaces.** If during the builder plan's authoring some behaviour resists outcome-shaping (a method prescription is the only natural form), halt and signal back — the AC's wording may need owner ruling before build proceeds.
8. **Token-budget breach under measured emission.** If the always-load tier's measured emission exceeds the partition decision's expected ceiling by more than ~50% (e.g. owner ruled lean tier ≈7 k tokens, build measures 11 k+), halt and surface — the partition is wrong-sized.

---

## 9. Decisions for owner (only genuinely uncertain)

The research artefact resolved most decisions; four (D-CI.1 through D-CI.4) plus four open questions (D-CI.5 through D-CI.8) need owner ruling before build. Recommendations attached; rule from this list.

### D-CI.1 — Always-load partition (token-cost / recall trade-off)

**Options:**
- **(a) Lean** — {CLAUDE.md, VALUE_PROPOSITION.md, STATE.md}. ~6.8 k tokens per session.
- **(b) Widened** — lean ∪ {odd-methodology.md, odd-in-pos.md}. ~28 k tokens per session.

**Recommendation: (a) lean.** Methodology docs are referenced often but not every turn; on-demand via Read with section-anchor pointers preserves recall fidelity at much lower per-session cost.

### D-CI.2 — On-demand tier shape

**Options:**
- **(a) Path-pointer only** — workspace-relative paths in a structured block. Persona reads on-demand via Read.
- **(b) Hybrid** — path + extracted top-level section anchors per file. Persona has exact line ranges to read.

**Recommendation: (a) path-pointer only**, via §6 D-build.5. (b) is a follow-on amendment if the persona's on-demand reads turn out to need anchor hints.

### D-CI.3 — Caching across sessions

**Options:**
- **(a) Re-emit every session** — no cache.
- **(b) Hash-skip** — content-hash cache; skip re-emit if unchanged.

**Recommendation: (a) re-emit every session.** Sessions are isolated context windows; cross-session cache saves zero model-context tokens. Disk I/O is sub-millisecond; not worth caching. Premature.

### D-CI.4 — Path-resolver helper

**Options:**
- **(a) Lift `_resolve_corpus_path` to a shared util.**
- **(b) Duplicate the 3-line helper inside `hands-off-lifecycle/hooks/`.**

**Recommendation: (b) duplicate.** Matches A1's `WORKSPACE_STATE_SUBDIR` precedent; keeps the seal-diff window clean (no cross-component edit); the helper is small enough that duplication is not maintenance debt.

### D-CI.5 — Sentinel update target (open question)

**Options:**
- **(a) Update A1's sentinel** — this hook updates `corpus_paths_loaded` in A1's existing sentinel file.
- **(b) Write a separate sentinel** — sibling file; future amendment unifies.

**Recommendation: (a) update A1's sentinel.** Field reserved for it; single source of truth.

### D-CI.6 — Hook ordering vs. persona emitter (open question)

**Options:**
- **(a) A1 → corpus-inline → persona** — persona dossier reflects inlined state.
- **(b) A1 → persona → corpus-inline** — persona dossier as today; corpus content emitted last.

**Recommendation: (a)** — preserves the option to grow a persona-dossier `corpus_inlined: true` marker in a later micro-amendment.

### D-CI.7 — Per-file size ceiling (open question)

**Recommendation: 50 k chars per file** (per §6 D-build.3). Builder applies; not load-bearing.

### D-CI.8 — Mode-partition refinement (open question)

**Recommendation: DEV MODE only; NORMAL USE no-op.** Surfaced for the record. A future amendment may widen if NORMAL USE workspaces evolve to have shared corpus.

**Decisions surfaced for owner ruling: 4 (D-CI.1 through D-CI.4); 4 open questions with strong recommendations (D-CI.5 through D-CI.8) the builder applies absent owner override.**

---

## 10. Risks

- **R1 — Token-cost creep.** Always-load tier expansion across future amendments balloons session-start cost. Mitigation: every always-load addition gates through a new amendment (no implicit-add); the lean default makes the cost visible; AC.CI.6's ceiling is a defensive backstop.
- **R2 — Corpus drift outpaces inlining.** A new corpus file added without a manifest update; hook silently misses it; persona doesn't notice. Mitigation: existing AC.F1/F3 manifest-coverage tests already enforce manifest consistency for always-load; the hook reads the manifest, not a hardcoded list, so manifest expansion is the only update needed.
- **R3 — Inlined content masks dossier missingness signal.** The persona dossier today says `[MISSING]` for absent files; if the hook also emits content from present files, a future contributor might assume content presence implies file presence. Mitigation: AC.CI.1 mandates an explicit `[missing]` marker for absent always-load files; AC.CI.4 mandates A1's sentinel `state` reflect the loaded subset; downstream consumers read the sentinel, not the inlined text shape.
- **R4 — A1 surface gap.** If A1's `write_corpus_load_sentinel` cannot extend additively, the hook either (i) lands an A1.1 corrective first (halt-trigger 2) or (ii) writes a separate sentinel (D-CI.5 option (b) fallback). Mitigation: builder plan resolves before code lands.
- **R5 — Persona session-start emitter coupling.** The persona dossier reads the sentinel; if hook ordering changes, the dossier could be outdated relative to content state. Mitigation: D-build.4 locks the order (A1 → corpus-inline → persona); regression tests verify the persona dossier reflects the post-corpus-inline sentinel state.
- **R6 — File-extension filter false negatives.** D-build.1 names a file-extension filter on the manifest's globs; a corpus file with an unusual extension (e.g. `.markdown`, `.rst`) would be silently dropped. Mitigation: the always-load tier is small and explicit; new corpus files land through a manifest amendment that the builder can extend the filter for at the same time.
- **R7 — Ceiling-truncation hides relevant content.** A 50 k-char ceiling on a corpus file truncates the tail; if methodology grows past 50 k and the truncated section is load-bearing, the persona misses it. Mitigation: AC.CI.6's truncation marker is byte-grep-able; the persona observes the marker and reads the full file via the path pointer. The marker itself is the structural signal.

---

## 11. Bookkeeping

- **Plan-doc:** this file at `docs/rebuild/plans/corpus-inlining-session-start-hook.md`.
- **Research artefact:** `docs/rebuild/plans/research/corpus-inlining-session-start-hook-research.md` (locked 2026-04-28; governs).
- **Builder plan:** to be authored by the build agent post-owner-approval at `docs/rebuild/plans/corpus-inlining-session-start-hook.builder-plan.md`. Contains files-touched, symbol-level details, AC-to-test mapping, D-build choices applied to owner D-CI rulings, §2.5 reverse-direction audit, halt-trigger checks, pos-amend bookkeeping flow.
- **Manifest:** to be authored alongside the builder plan at `docs/rebuild/plans/corpus-inlining-session-start-hook.manifest.yaml`. Single-component manifest (`hands-off-lifecycle`), `frozen_baseline: true` (H19 frozen per amendment #23). Universal-paths block as standard (`docs/rebuild/plans/`, `CLAUDE.md`, `docs/odd-methodology.md`, `docs/odd-in-pos.md`, `docs/rebuild/FUTURE_IDEAS.md`).
- **Pos-amend bookkeeping flow** (per `feedback_dispatch_explicit_pos_amend_apply`):
  1. Author manifest at `docs/rebuild/plans/corpus-inlining-session-start-hook.manifest.yaml` with the correct BASELINE (HEAD~1 of the upcoming amendment commit per the established amendment pattern).
  2. Author all source edits + tests; commit as the amendment commit on branch `pos-v2`.
  3. `pos-amend apply --dry-run <manifest>` — must exit 0.
  4. `pos-amend apply <manifest>` — advances BASELINE literals + widens seal-diff bindings + writes SEAL_COMMIT sidecars.
  5. `pos-amend seal --plan-doc /Users/lukeivers/ivers-corp-pos-v2/docs/rebuild/plans/corpus-inlining-session-start-hook.builder-plan.md <manifest>` — runs the scoped test sweep, creates the seal commit, advances SEAL_COMMIT to the seal commit, appends builder-plan §SHA backfill follow-up commit.
  6. Verify: `pos-amend apply --dry-run <manifest>` exits 0 against post-seal HEAD.
- **Seal-diff window:** BASELINE = HEAD~1 of amendment commit (set in builder plan after dispatch). Allowed paths under the window: `hands-off-lifecycle/{hooks,tests,seals}/`, plus universal admissions.
- **FIDRAFT graduation:** the FIDRAFT entry "SessionStart corpus_gate should inline corpus content" graduates to a sealed amendment via this work. The graduation entry update lands in `docs/rebuild/FUTURE_IDEAS.md` (graduated-from-DRAFT entry) at seal time.
- **Composes-on dependencies (read-only consumers):**
  - `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py` — A1's sentinel module (extended additively per D-build.6).
  - `framework/hands-off-lifecycle/hooks/first_run_settings.py` — `merge_session_start` + `_POS_V2_COMMAND_MARKERS` (new marker added).
  - `framework/hands-off-lifecycle/hooks/first_run_helper.py` — extra_inner_hooks composition site (one new entry).
  - `tools/loam-mode/` — A1's `compute_corpus_paths_required` consumes `loam_mode.manifest.load_manifest` + `loam_mode.selector.select_corpus`. Read-only consumer; no edits.
  - `framework/primary-persona/src/session_start_gate.py::_resolve_corpus_path` — duplicated, not imported. Read-only reference.

---

## 14.

### Method-decision register (post-build, builder-backfilled)

Method-level decisions made during the build land here at seal time per `pos-amend seal --plan-doc` convention. Empty at plan-author time.

### Commit SHAs

- Amendment commit: `<post-build>`
- Apply commit: `<post-build>`
- Seal commit: `<post-build>`

---

*End of plan-doc. Builder plan + manifest authored after owner approval.*
