# FBM Cycle 1 — ACTIVATE + UNIFY + FIX-WRITE-PATH

**Status:** sub-plan-doc (Cycle 1 of the FBM activation lineage; Cycles 2/3 are separate later plans)
**Working dir:** `/Users/lukeivers/loam` (canonical loam)
**Parent plan / roadmap:** `docs/design/fbm-state-and-memory-roadmap-2026-05-29.md` — "RECOMMENDED next-cycle plan" §CYCLE 1 (R1)
**Predecessors (load-bearing prior seals):**
- FBM Tier 0 — episode store + BM25 (seal `1a1f830`, `M-FBM`)
- FBM Tier 1 — write-side + supersession, amendment **#134** (seal `0347760`, apply `ed8d3bf`)
- FBM Tier 2 — retrieval mechanics (activation + co-citation), amendment **#135** (seal `32608d2`, apply `b41b52b`)
- Keep-pace KP1 — work-anchored corpus retrieval, amendment **#150** (seal `aadf2b7`)
- Keep-pace KP7 — SessionStart objective + last-state surface, amendment **#152** (seal `07d3b59`)
**Research artefacts:**
- `docs/design/fbm-state-and-memory-roadmap-2026-05-29.md` (designed-vs-built, drift findings, Cycle 1/2/3 rec)
- `/Users/lukeivers/pos3/workspace/.scratch/claude-output/workspace-inventory-and-routing-map-2026-05-29.md` PART B (cross-root collisions — the stranded-write-path finding is load-bearing here)
**BASELINE candidate:** HEAD~1 of the amendment commit (mirrors #38–#40 / #150–#152 BASELINE-as-HEAD~1 pattern). Current HEAD `58b6255`.
**Amendment number:** #154 (last sealed = #153).
**Status-file target:** `docs/STATE.md` (#154 entry) + roadmap §"RECOMMENDED next-cycle plan" CYCLE 1 marked done.
**Quality bar:** ODD §2.5 (every code path traces to a named AC); no method-in-AC; ≥1 outcome-altitude AC; serialize builds in one tree; sealed-component fence honoured via `loam amend apply` / `loam amend seal`.

---

## §1 Summary / TL;DR

**What ships:** Cycle 1 turns ON the comprehensive memory that is ~80% built but sitting dark, and fixes the bug that is silently throwing memory writes away. Three coupled deliverables, in dependency order:

1. **FIX-WRITE-PATH (do first — everything else is pointless without it).** Memory episodes are being written to a DEAD doubled-nesting shadow dir (`pos3/workspace/workspace/.pos/memory-write-queue/`, 17 stranded JSONs newest 15:07 today) while the LIVE queue (`pos3/workspace/.pos/memory-write-queue/`) is empty and drained. Root cause (Tier-0): the path resolvers `queue_dir()` (`memory_write_queue.py:52-65`) and `memory_dir_for_workspace()` (`file_memory.py:105-122`) both append `WORKSPACE_STATE_SUBDIR` (`= "workspace"`, `workspace_paths.py:99`) to their `workspace_root` argument — so a caller that passes the *operator workspace* (`pos3/workspace`) instead of the *repo root* (`pos3`) produces the doubled `pos3/workspace/workspace/.pos/...` path. Writes + reads must agree on one location.

2. **UNIFY the two retrieval tracks into one surface.** Today there are two BM25/FTS5 indexes over two corpora, neither aware of the other at retrieval time: the **FBM episode index** (`file_memory.py`, `search-index.sqlite`) and the **KP1 corpus index** (`keep_pace/corpus_index.py`, over `feedback_*.md` + CLAUDE.md hierarchy + `OBJECTIVES.md`). The unify seam already exists: `keep_pace/corpus_index.py:110-146` `discover_corpus(..., memory_dir, ...)` already accepts a `memory_dir` parameter and the comment at `:58-59` notes the episode store is the deliberately-separate other half. One retrieval call must see episodes AND rules AND objectives.

3. **ACTIVATE live wiring (owner-gated).** Flip the single owner-gated `~/.claude/settings.json` activation switch (the keep-pace chain + `OBJECTIVES.md` seed are already bundled into this one step per STATE.md #152) so the per-turn read/write path actually fires. This is a BACKUP-FIRST, verify-it-fires step that changes Luke's live runtime memory — owner-class.

**AC families:** `AC.FBMW.*` (write-path), `AC.FBMU.*` (unify), `AC.FBMA.*` (activation), plus `AC.FBM1.S` (outcome-altitude end-to-end) and `AC.FBM1.SEAL` (seal-diff fence).

**Key decisions baked (full text §3):** D1 write-path fix is **caller-side** (callers pass the repo root, not the operator workspace) + **migrate the 17 stranded JSONs into the live queue** before draining; D2 unify is **extend the KP1 contributor to merge episode-index hits** (the indexes stay two physical stores, one merged retrieval surface); D3 activation is **backup-first + post-flip fires-verification**; D4 coexistence is **additive wiring — keep-pace's existing live behaviour is unchanged during cutover**.

**F2 scope-realism (§10):** this is mostly *wiring already-built parts*, which is genuinely high-confidence / tight-scope per F4 — with ONE real risk I am naming up front: the write-path bug means there is **no proof the live write path has EVER worked end-to-end**, only that writes landed *somewhere*. The outcome-altitude AC (`AC.FBM1.S`) is therefore load-bearing, not ceremonial — it is the only thing that proves write + unify + activation actually compose. If `AC.FBM1.S` can't be made to pass with caller-side-only changes, that is a halt trigger (§8 H3), because it would mean the resolver contract itself is wrong and the fix is larger than Cycle 1.

---

## §2 Placement decisions

| Item | Placement | Rationale |
|---|---|---|
| Write-path fix (resolver caller + queue migration) | `framework/primary-persona/` (sealed component) — the enqueue/worker callers + the resolvers live here | The bug is a caller-vs-resolver contract mismatch inside primary-persona; the resolvers' `<root>/workspace/...` shape is the *designed* D-Q.MFBM.3 contract and stays — the fix is making callers pass the right root (D1). Sealed-component edit → `loam amend apply` / `seal`. |
| Unify (episode-index merge into KP1 retrieval) | `framework/primary-persona/src/loam/primary_persona/keep_pace/` (same component) | KP1 + FBM episode store are BOTH in primary-persona — the roadmap implied a cross-component unify; it is in fact intra-component. `discover_corpus(..., memory_dir, ...)` + the retrieval merge already have the seam. |
| Activation wiring | Luke's LIVE `~/.claude/settings.json` (+ possibly `pos3/.claude/settings.json`) | Runtime config, NOT loam source. Owner-gated. The wiring points at `loam/.venv/bin/python` per the sweep PART B; placement of the activation entry is deliberate given the split-settings finding. |
| Stranded-JSON migration | one-time operator action against `pos3/workspace/workspace/.pos/` → `pos3/workspace/.pos/` | Operator-workspace data, not loam source. Migrate-then-fix so no episode is lost (P2 trust promise). |

---

## §3 Named decisions (with recommendations)

Every decision below is a recommendation stated AS the decision (per reporting discipline); only the activation flip itself (D3) is owner-class because it mutates Luke's live runtime.

### D1 — WRITE-PATH fix: where do writes land, and what happens to the 17 stranded JSONs?

**Decision (recommended):** Fix it **caller-side**, not resolver-side, AND **migrate the 17 stranded JSONs into the live queue** before draining the dead shadow.

- **Root cause (Tier-0):** `queue_dir()` and `memory_dir_for_workspace()` both do `<workspace_root>/workspace/.pos|.loam/...`. The resolver's `+ workspace/` is the *intended* D-Q.MFBM.3 contract (the resolver expects the **repo root**). The live write caller is passing the **operator workspace** (`pos3/workspace`), so the path doubles to `pos3/workspace/workspace/.pos/...`. The live worker reads the single-`workspace` path → writes go nowhere it reads.
- **Why caller-side not resolver-side:** the resolver contract is depended on by the worker, the prewarm path, and the (drained, healthy) live single-`workspace` queue. Changing the resolver to strip a doubled segment would be a guess-and-special-case (it can't tell a legitimately-nested workspace from the bug). Making the callers pass the documented `workspace_root` (repo root) is the narrow, contract-preserving fix. The builder identifies the offending caller(s) and corrects the root they pass.
- **Migrate not discard:** the 17 stranded JSONs are real episodes (P2 trust promise: never silently lose what the user said to keep). Recommend: move them into the live queue so the worker drains them, THEN remove the dead shadow dir. Discarding them would be a silent data loss; the roadmap's stranded-write finding treats them as live-looking-but-stranded, not garbage.
- **Fence note:** the doubled-nesting cleanup *beyond what the write-path fix needs* is OUT (§7). Cycle 1 migrates the queue JSONs + removes the dead `.pos` shadow only; the broader `workspace/workspace/` doubled-tree cleanup is a separate concern.

### D2 — UNIFY: how to make one retrieval surface see episodes + rules + objectives

**Decision (recommended):** **Extend the live KP1 UserPromptSubmit contributor to also query the FBM episode index and merge results by score** — keep the two physical indexes (they have different update cadences + different ranking machinery), unify at the *retrieval call*, not the *index*.

- **Why merge-at-retrieval not merge-the-index:** the FBM episode index carries the mature T2.1/T2.2 ranking (power-law activation × supersession × co-citation spread, `file_memory.py:1294-1313`); the KP1 corpus index is a plain BM25/FTS5 over markdown. Collapsing them into one physical index would throw away the episode-side ranking machinery that #135 shipped. The roadmap's R1 explicitly offers both options ("point KP1's indexer at the FBM episode dir too, OR have the UserPromptSubmit contributor query both and merge by score") — the merge-by-score option preserves both rankers.
- **The seam is already present:** `corpus_index.py:110` `discover_corpus(..., memory_dir, ...)` already takes `memory_dir`; `:58-59` documents the episode store as the deliberately-separate other half. The contributor calls `FileMemoryStore.search()` (the post-#96 `{query,results,nodes,episodes}` shape) and merges its `episodes` into the KP1 result set under the existing top-N≤5 + byte budget.
- **Outcome, not method:** the AC (`AC.FBMU.*`) bounds *"a single retrieval call returns both an episode hit and a corpus hit for a query that matches both corpora"* — the merge algorithm (interleave / score-normalise / dedup) is the builder's call.

### D3 — LIVE-SETTINGS ACTIVATION: backup-first, verify-it-fires (OWNER-GATED)

**Decision (recommended, owner-class — Luke flips it):** Activate via a **deliberate, backup-first, fires-verified** step against the LIVE `~/.claude/settings.json`.

- **This is the one owner-class action in Cycle 1** — it mutates Luke's live runtime memory behaviour. Per the activation-gate discipline (STATE.md #152: "ONLY the single owner-gated live `~/.claude/settings.json` activation step remains"), this is the gated switch the whole built-but-dark system sits behind.
- **Backup-first:** snapshot `~/.claude/settings.json` (and `pos3/.claude/settings.json` if touched) before edit, so the activation is reversible (reversibility is a named signal in the M5 frame).
- **Split-settings finding (sweep PART B / B1):** `~/.claude/settings.json` wires only keep-pace + spawn-guard; `pos3/.claude/settings.json` wires 13 more hook invocations. The activation entry must be placed in the correct settings.json for its scope (global memory wiring → `~/.claude/`; project-scoped → `pos3/.claude/`) and the builder must NOT assume a `~/.claude`-only edit reaches the project hooks.
- **Verify-it-fires (NOT verify-it-was-written):** a settings.json edit that parses is not proof the hook fires. The activation step ends by confirming a real turn produces a real episode at the LIVE path (this is what `AC.FBM1.S` measures) — written-but-doesn't-fire is the exact failure class the sweep's "live-looking but stranded" finding warns about.
- **Isolation constraint:** any `claude -p` invoked in verification goes through `ClaudePrintClient` and the live spawn-isolation guard (never a hand-rolled un-isolated `claude` spawn — the Telegram-bot-slot-steal fix is live).

### D4 — NO-REGRESSION coexistence with the live keep-pace track during cutover

**Decision (recommended):** **Additive-only wiring.** Keep-pace's existing live SessionStart/UserPromptSubmit/Stop behaviour (KP1/KP5/KP7/KP9, amendments #149–#152) is unchanged; Cycle 1 *adds* the episode-merge to the existing KP1 contributor and *adds* the corrected write-path — it removes nothing the live chain depends on.

- The keep-pace chain is fail-open by contract (`chain_runner.py:18`: "a broken memory hook must never break the live session"). The episode-merge extension inherits that envelope: if the episode index is absent/empty, the merge contributes zero and KP1's corpus retrieval is unchanged (a no-regression property the AC measures).
- The write-path fix changes *where* writes land, not *that* keep-pace reads its corpus — KP1's corpus roots (`feedback_*.md`, CLAUDE.md, OBJECTIVES.md) are untouched by D1.

---

## §4 Spec-objective placement

- **Binds to:** VALUE_PROPOSITION's two prime-objective tests (AC.PO.1 primary-persona translation-burden reduction; AC.PO.2 harness-toolkit growth) via the memory-architecture three user-promises (`memory-architecture.md:62-68`): **P1 transparent continuity** (episodes carry context across sessions — directly served by fixing the write-path + activating retrieval), **P2 trust** (never silently lose what the user said to keep — served by migrating the 17 stranded JSONs rather than discarding), **P3 graceful scaling** (the unified surface grows for years).
- **Ladders up to:** prime objective — the persona absorbing the "what was I working on / what did I already decide" translation burden the owner observed missing on 2026-05-29.

---

## §5 Acceptance criteria

All outcome-shape. Method-in-AC test applied to each (can it be satisfied by a method other than the one I have in mind? — yes for every AC below).

### AC.FBMW.* — write-path fix

| AC | Outcome | Verification |
|---|---|---|
| **AC.FBMW.1** | An episode written through the live enqueue path lands at the **single-`workspace` live queue/store location**, not the doubled-`workspace` shadow. | Test invokes the production enqueue with the documented `workspace_root`; asserts the written file's resolved path contains exactly one `workspace/` segment. |
| **AC.FBMW.2** | The 17 stranded shadow-dir JSONs are recoverable into the live queue with no episode lost. | Test: given N stranded entries in the shadow path, the migration yields N drainable entries in the live queue; count preserved; no overwrite of an existing live entry. |
| **AC.FBMW.3** | After migration, the dead shadow queue dir no longer accumulates new writes. | Test: a post-fix write does NOT create/append under the doubled-`workspace` path. |

### AC.FBMU.* — unify

| AC | Outcome | Verification |
|---|---|---|
| **AC.FBMU.1** | A single retrieval call (the UserPromptSubmit contributor) returns BOTH an episode-store hit AND a corpus hit for a query that matches content in both corpora. | Test seeds one episode + one `feedback_*.md` matching the same query term; asserts both appear in the merged `additionalContext` under the top-N + byte budget. |
| **AC.FBMU.2** | When the episode index is absent or empty, the unified contributor's corpus-side output is byte-identical to the pre-unify KP1 output (no regression). | Test: empty episode store → merged output equals KP1-only output; fail-open envelope preserved. |
| **AC.FBMU.3** | The merged surface respects the existing top-N≤5 + byte-budget caps (episode hits do not blow the budget). | Test: many episode + corpus hits → result is capped; truncation deterministic. |

### AC.FBMA.* — activation (verified against the built artefact; the live flip is the owner-gated step)

| AC | Outcome | Verification |
|---|---|---|
| **AC.FBMA.1** | The activation wiring, once applied, causes the per-turn read/write contributor to actually fire on a real turn (not merely parse). | Verification step (owner-gated flip + post-flip check): a real turn through the wired settings produces a retrieval block AND an episode write at the live path. |
| **AC.FBMA.2** | The activation entry is placed in the settings.json matching its scope; a `~/.claude`-only assumption does not silently drop project-scoped wiring. | Verification confirms the wiring location against the split-settings reality (sweep B1). |

### AC.FBM1.S — OUTCOME-ALTITUDE (`outcome-altitude: true`)

> **AC.FBM1.S** — A **fresh session** (no pre-arranged in-memory state) writes an episode that **lands in the live store** AND is **retrievable through the unified surface** in a subsequent retrieval call — proving write-path + activation + unify compose end-to-end.

- **Verification:** invoke the production entry-point (the live persona turn path via `ClaudePrintClient`, isolated) with no pre-seeded episodes; assert (a) the episode file appears at the single-`workspace` live path, (b) a follow-up UserPromptSubmit retrieval for that episode's content returns it through the merged contributor alongside any matching corpus doc. STUB-class tests do NOT satisfy this AC (per `feedback_test_outcome_altitude_required`).
- **Why load-bearing:** this is the ONLY AC that proves the write-path bug is actually fixed in the live flow — every other AC tests a layer in isolation. If this can't pass caller-side-only, halt (§8 H3).

### AC.FBM1.SEAL — seal-diff fence

| AC | Outcome | Verification |
|---|---|---|
| **AC.FBM1.SEAL** | Only `framework/primary-persona/` + `docs/plans/` + universal paths changed in the loam seal window; no other sealed component touched. | `primary-persona/tests/test_no_sealed_amendments.py` at BASELINE + the per-component sweep. (Live settings.json + operator-workspace migration are NOT loam-tree changes and are out of the seal diff by construction.) |

---

## §6 Build steps (method-level guidance; builder's call per ODD §1.1)

Serialize in one tree (no parallel build agents in `/Users/lukeivers/loam` — `feedback_serialize_amendment_builds`).

1. **Manifest:** `docs/plans/fbm-activate-unify-and-fix-write-path.manifest.yaml` (paired; `amendment.number: 154`, single component `primary-persona`, BASELINE = HEAD~1 of the amendment commit).
2. **FIX-WRITE-PATH first (D1).** Identify the live enqueue/store caller(s) passing the operator-workspace as `workspace_root`; correct them to pass the documented repo root (or otherwise reconcile so the resolver yields the single-`workspace` path). Author `AC.FBMW.1/2/3` tests (incl. the migration helper for the 17 stranded JSONs). The stranded-JSON migration is an operator-side one-time action driven by a tested helper — it is NOT a loam-source data edit.
3. **UNIFY (D2).** Extend the KP1 UserPromptSubmit contributor (`keep_pace/`) to query `FileMemoryStore.search()` and merge episodes into the result set under the existing caps. Author `AC.FBMU.1/2/3`. Preserve the fail-open envelope (`chain_runner.py:18`).
4. **Author the outcome-altitude test (`AC.FBM1.S`)** against the isolated production turn path. This is authored as part of the loam seal (the test exists in-tree); the live flip that makes it pass in Luke's runtime is the owner-gated activation step.
5. **Apply + seal (sealed component):** `loam amend apply` then `loam amend seal --plan-doc` against the manifest. primary-persona's SEAL_COMMIT sidecar advances per the standard window.
6. **ACTIVATION (D3 — owner-gated, runtime, NOT in the loam seal):** backup `~/.claude/settings.json` (+ `pos3/.claude/settings.json` if scoped there); apply the activation wiring in the correct settings.json; run the post-flip fires-verification (`AC.FBMA.1/2` + `AC.FBM1.S` against the live runtime). HARD-smoke per the per-minor publish discipline if this rides a release.
7. **Bookkeeping (§9).**

---

## §7 Out of scope (deferred + when)

| Out | Why / when |
|---|---|
| **Consolidation (FBM Tier 3 / C1 / C2)** — session-end + work-state projection | **Cycle 3** (separate plan). Warm-up precondition is satisfied *by* Cycle 1 flipping the switch. |
| **Claim-guard / MM1 (extend KP9 Layer-C to live claim-vs-state)** | **Cycle 2** (separate plan). |
| **Guaranteed-surface / T2.3 working set (R2)** | **Cycle 2** (separate plan). |
| **Remaining deferred tiers** (KP2 miss-gate, MM2/MM3, T3.2 scheduled consolidation) | **Cycle 4+ on observed need.** |
| **Graphiti-residue kill** (the live-looking dead-name sweep) | **task #19, separate cycle, same lineage.** graphiti is DEAD + out of scope (Luke 12955) — file-based only; this plan never proposes graphiti/external store. |
| **Doubled-nesting cleanup beyond the write-path fix** (`framework/framework/`, the broader `workspace/workspace/` shadow tree) | Cycle 1 touches ONLY the queue-JSON migration + the dead `.pos` shadow removal needed for D1; the broader doubled-tree cleanup is a separate concern. |
| **FBE→FBM naming sweep** | doc-only, Cycle 4+ (low severity per roadmap §F2.3). |
| **memory-architecture M1/M2** (MEMORY.md compression / InstructionsLoaded budget hook) | Cycle 4+; MEMORY.md verified 20,669B < 24.4KB cap, so M1 is not urgent. |

---

## §8 Halt triggers (abort the in-flight build + surface)

- **H1 — resolver contract is depended-on in a way caller-side fix can't satisfy.** If correcting the callers' `workspace_root` breaks the (drained, healthy) live single-`workspace` queue or the worker/prewarm path, halt — the fix is larger than a caller correction.
- **H2 — the unify merge would require changing the FBM episode index schema or the KP1 index schema.** Cycle 1 is merge-at-retrieval only; a schema change is out of scope and signals the unify is bigger than wiring — halt.
- **H3 — `AC.FBM1.S` cannot be made to pass with caller-side-only changes.** This means write+activation+unify don't actually compose end-to-end under the chosen fix — halt and surface (the fix is larger than Cycle 1).
- **H4 — the activation flip would touch a sealed component without a manifest entry, or the correct settings.json scope is ambiguous** (given the split-settings finding). Halt rather than silently widen the fence or guess the scope.
- **H5 — migrating the 17 stranded JSONs would overwrite or collide with existing live-queue entries.** Halt — silent overwrite violates the P2 trust promise.
- **H6 — any ODD violation discovered in surrounding code** (unnamed code path, method-in-AC in a sibling) — surface, do not silently extend (`feedback_subagent_odd_violation_halt`).

---

## §9 Bookkeeping

- `docs/STATE.md` — add #154 entry (FBM Cycle 1: write-path fix + unify + activation).
- Roadmap `docs/design/fbm-state-and-memory-roadmap-2026-05-29.md` — mark "RECOMMENDED next-cycle plan" CYCLE 1 (R1) as built; note the "~1 week re-eval" lapse (§F2.4) is superseded by this cycle's activation (which restarts the KP2 score-logging clock).
- `pos3/.claude/workstream-queue.yaml` — close/advance the FBM-activation workstream entry; record the stranded-write incident as resolved.
- §11 method-decision register — populated by the builder at build time + SHA-backfilled at seal.

---

## §10 F2 Ruthless Feedback (honest doubts + named gaps vs roadmap / sweep)

1. **Disagreement with the roadmap's framing of the unify as cross-track.** The roadmap (Q1 drift #3) describes FBM and KP1 as "two parallel memory tracks built without a unifying retrieval surface" and R1 frames the unify as joining two components. **Evidence:** both live in `framework/primary-persona/` — KP1 is `primary_persona/keep_pace/`, FBM is `primary_persona/file_memory.py`; `corpus_index.py:110` already takes a `memory_dir` param and `:58-59` already documents the episode store as the intended other half. **Alternative:** treat the unify as the *intra-component* wiring it actually is — this tightens scope (F4) and is why D2 is high-confidence.

2. **Gap the roadmap did NOT surface: the write-path bug invalidates the roadmap's "built ≠ live" confidence.** The roadmap (Q1 drift #1) says the episode store is "built but not wired live." **Evidence (sweep PART B / B2):** writes were *firing* — they were just landing in the dead doubled path. So the system is worse than "dark": it was *half-on and silently discarding*. **Alternative:** Cycle 1 must FIX-WRITE-PATH before activation, and the outcome-altitude AC must be load-bearing (not ceremonial) — this plan elevates the write-path fix to the first build step and `AC.FBM1.S` to the proof-of-compose. This is the single most important correction this plan makes over a naive reading of the roadmap's "just flip the switch."

3. **Risk I'm naming: "verify it fires" is hard to make deterministic in a test.** A loam-tree test can prove the resolver math + the merge logic; it CANNOT prove Luke's live `~/.claude/settings.json` actually invokes the hook on a real turn. **Evidence:** the sweep's whole reason-for-existing is "live-looking but stranded" — written config that doesn't fire. **Alternative:** `AC.FBMA.1` + `AC.FBM1.S` are explicitly post-flip *runtime* verification steps (owner-gated), separate from the in-tree seal tests — the plan does not pretend the seal proves liveness.

4. **Gap: I did not independently verify the count "17 stranded JSONs."** **Evidence:** it is the sweep's Tier-0 finding (`workspace-inventory-and-routing-map-2026-05-29.md` B2, newest 15:07 today), carried forward, not re-counted by me. **Alternative:** `AC.FBMW.2` is written as "N stranded entries → N drainable, count preserved" — parameterised on the actual count at build time, so it's correct whether the count is 17 or has drifted by build-time. The builder re-counts at migration time (Tier-0).

---

## §11 Provenance trail

- **Write-path root cause:** `framework/primary-persona/src/loam/primary_persona/memory_write_queue.py:52-65` (`queue_dir`), `file_memory.py:105-122` (`memory_dir_for_workspace`), `framework/workspace-bootstrap/src/loam/workspace_bootstrap/workspace_paths.py:99` (`WORKSPACE_STATE_SUBDIR = "workspace"`); stranded-JSON finding from sweep PART B / B2.
- **Unify seam:** `framework/primary-persona/src/loam/primary_persona/keep_pace/corpus_index.py:58-59, 110-146` (the `memory_dir` param + the "indexes the markdown corpus, not episode files" note); FBM ranking `file_memory.py:1294-1313`.
- **Activation gate:** STATE.md #152 ("ONLY the single owner-gated live `~/.claude/settings.json` activation step remains"); split-settings reality from sweep PART B / B1.
- **Predecessor seals:** #134 `0347760`, #135 `32608d2`, #150 `aadf2b7`, #152 `07d3b59`; FBM Tier 0 `1a1f830`.
- **Roadmap recommendation:** `docs/design/fbm-state-and-memory-roadmap-2026-05-29.md` §"RECOMMENDED next-cycle plan" CYCLE 1 (R1).
- **Owner authorization:** Luke TG 12960 / 12962 (build Cycle 1); graphiti-dead ruling TG 12955.
- **Fail-open envelope:** `framework/hands-off-lifecycle/hooks/keep_pace/chain_runner.py:18`.
- **VERIFIED facts used (not re-derived):** MEMORY.md = 20,669B < 24.4KB cap; FBM component built-but-unwired; consolidation/working-set deferred = OUT.

---

## §12 Build-time method-decision register (builder, 2026-05-29)

Source edits authored + tested; **apply/seal HALTED on H6** (see below).

| Decision | Method chosen (builder's call) | AC |
|---|---|---|
| D1 caller root | The bug is `cli._resolve_workspace(None)` returning bare `Path.cwd()`. The live Stop/UPS/SessionStart hooks fire with cwd = operator workspace `<repo>/workspace/`; the resolver then doubles its `workspace` segment. Fix is the single chokepoint `_resolve_workspace`: honour `LOAM_WORKSPACE_ROOT` (the canonical repo-root env the worker plist already sets — `first_run_scaffold.py:1440/1448`), else strip a trailing `workspace` segment off cwd, else bare cwd. Resolver contract untouched (H1 NOT triggered). | AC.FBMW.1/3 |
| D1 migration | `memory_write_queue.migrate_stranded_queue(shadow, live)` — `os.replace` each `*.json`; filename collision with a live entry → surfaced in `collisions` (NOT overwritten, H5), stranded copy left in place. Count-preserving: `migrated + collisions == stranded_total`. Operator drives it; dir teardown is out of the helper. **Tier-0 re-count: 17 stranded JSONs; 0 collisions with the (empty) live queue → clean migration.** | AC.FBMW.2 |
| D2 unify | Merge-at-retrieval in `keep_pace/retrieval.py`: `RetrievalConfig.episode_memory_dir` + `_episode_hits()` query `FileMemoryStore.search()`, `_merge_by_score()` interleaves by descending score (stable; corpus-before-episode on ties) capped at top-N, then existing `_render_injection` byte budget. Episode pointer = first sentence of episode `content` (plain-language; opaque `turn/<id>` name never leaks). Both physical indexes preserved (H2 NOT triggered). Live config resolves the episode dir via the same repo-root derivation as D1. | AC.FBMU.1/2/3 |
| D4 coexistence | Additive-only: `episode_memory_dir=None` (or empty store) → merged set IS `corpus_hits` (same objects) → byte-identical pre-unify output. Fail-soft `_episode_hits` returns `[]` on any boundary error (chain fail-open inherited). | AC.FBMU.2 |
| AC.FBM1.S | Drives the FULL production chain with no pre-seeded episodes: caller resolution → `enqueue` → `drain_once` (default file-backed client → `write_episode`) → `retrieve` with episode store wired. Episode lands at single-`workspace` live store + surfaces through the merged surface. No layer stubbed. | AC.FBM1.S |

**Test result (Tier-0):** 19/19 new AC cases pass; full primary-persona suite = **1 failed, 792 passed, 1 skipped** with my edits — identical failure set to clean HEAD `58b6255` (verified by stash-and-run). My edits introduce **zero** new failures.

**H6 HALT (pre-existing surrounding-code ODD violation, NOT mine):**
`framework/primary-persona/tests/test_AC_KP_S_1_live_session_safety_fence.py::test_AC_KP_S_1_live_wiring_is_staged_not_done` asserts `keep_pace/user_prompt_submit.py` `contributors()` returns `[]` ("staged, not done"). Commit `5fcd0c5` (keep-pace MVP activation, #150-152) wired both contributors live — `contributors()` now returns `[kp1-retrieval, kp7-reassert]`. The #150-152 cycle landed the activation but left this assertion stale. `loam amend seal` runs the touched component's FULL suite (`seal.py` step (d)), so this stale test blocks the #154 seal even though it is outside FBM Cycle 1's AC fence (it belongs to the keep-pace activation lineage). Builder halts rather than silently fix a sibling-lineage test inside this cycle's fence (F2 / serialize / no-false-fault four-test all clear: the miss is #150-152's, not #154's).

**Recommended resolution (dispatcher rules):** update the one stale assertion in `test_AC_KP_S_1_live_wiring_is_staged_not_done` to reflect the shipped #150-152 reality (the wiring IS live; assert the two contributors are registered, not `return []`). Doc/test-only, reversible, inside primary-persona's fence — admittable into #154's seal window OR a tiny separate corrective. Once the assertion matches reality, `loam amend apply` + `seal` proceed clean.

---

## §13 D3 activation — CORRECTED procedure (owner-gated; builder NOT executing — Tier-0 verified, supersedes the plan's `~/.claude/settings.json`-flip model)

The plan §3 D3 + STATE.md #152 modelled activation as flipping ONE owner-gated switch in `~/.claude/settings.json`. **Tier-0 inspection of the live runtime contradicts that model (F2):**

1. **The writer hook is ALREADY wired live — in `pos3/.claude/settings.json`, not `~/.claude/`.** `pos3/.claude/settings.json` already invokes `loam.primary_persona.cli stop` (Stop), `cli session-start` (SessionStart), and `cli user-prompt-submit` (UserPromptSubmit). `~/.claude/settings.json` wires ONLY the keep-pace `user_prompt_submit.py` UPS hook (no Stop, no SessionStart). The split-settings reality is the REVERSE of the plan's read: the write path is in the PROJECT settings and is already firing — which is why 17 JSONs accumulated (writes WERE happening, to the doubled dead path). **No settings.json edit is needed to "turn on" the writer; it is on.**

2. **The live pos3 runtime imports `primary_persona` from a DIFFERENT tree than canonical loam.** `pos3/.venv` editable-installs `primary_persona` from `/Users/lukeivers/pos3/framework/framework/primary-persona/` (a separate git working copy of the framework — note the doubled `framework/framework/`, itself the broader doubled-nesting the plan flags OUT). Verified: that tree's `_resolve_workspace` is the OLD buggy `return Path.cwd().resolve()`; from cwd `pos3/workspace` it resolves `queue_dir` → `pos3/workspace/workspace/.pos/memory-write-queue/` (the exact dead shadow). **My sealed fix lands in canonical `/Users/lukeivers/loam`; it does NOT reach Luke's live runtime via the seal alone.**

**Therefore the REAL activation step (owner-gated) is a propagate-then-migrate, not a settings flip:**

- **(a) Propagate the sealed fix into the live runtime tree.** Sync the sealed #154 `primary-persona` source from canonical `/Users/lukeivers/loam/framework/primary-persona/` into the live runtime tree `/Users/lukeivers/pos3/framework/framework/primary-persona/` (via the normal pos-sync / framework-publish path Luke uses to update the pos3 framework copy — backup-first per the `feedback_backup_pos3_before_canonical_affecting_sync` once-over + rsync-snapshot + git-tag discipline). The editable install means the corrected `_resolve_workspace` takes effect on the next hook fire with no settings.json edit. **Confidence the fix then fires:** from the live `pos3/.claude/settings.json` Stop hook (cwd `pos3/workspace`, no `--workspace`, no `LOAM_WORKSPACE_ROOT`), the cwd-strip branch yields repo root `pos3` → `queue_dir` = `pos3/workspace/.pos/memory-write-queue/` (single-`workspace` live queue) — verified-by-construction against the resolver.

- **(b) Migrate the 17 stranded JSONs.** Run the tested `migrate_stranded_queue(shadow=/Users/lukeivers/pos3/workspace/workspace/.pos/memory-write-queue, live=/Users/lukeivers/pos3/workspace/.pos/memory-write-queue)`. **Tier-0: 17 stranded JSONs; 0 filename collisions with the (empty) live queue → all 17 migrate clean, none overwritten.** Then remove the dead `pos3/workspace/workspace/.pos/` shadow dir (operator action; the broader `workspace/workspace/` + `framework/framework/` doubled-tree cleanup stays OUT per §7).

- **(c) Verify-it-FIRES (not verify-it-was-written).** After (a)+(b): run a real persona turn in pos3, then confirm a NEW episode `.md` appears under `pos3/workspace/.loam/memory/episodes/` (the single-`workspace` live store) AND that a follow-up retrieval surfaces it through the merged keep-pace contributor. Any verification `claude -p` goes through `ClaudePrintClient` + the live spawn-isolation guard (never a hand-rolled un-isolated spawn). This is AC.FBMA.1 + the runtime leg of AC.FBM1.S.

- **(d) OPTIONAL — episode-merge in the live keep-pace UPS hook.** D2's unify is in the sealed `retrieval.py` (`build_keep_pace_contributor` resolves `episode_memory_dir` automatically when the live store exists). It activates with the same propagate step (a) since the keep-pace UPS hook lazy-imports from the same `primary_persona` package. No separate settings edit. **Note:** the `~/.claude/settings.json` keep-pace UPS hook imports from canonical `/Users/lukeivers/loam` directly (not the pos3 tree) — so the unify is live in the global keep-pace hook the moment #154 seals into canonical loam; the writer fix (a) is the pos3-runtime-tree propagate.

**AC.FBMA.2 (settings scope):** confirmed — global keep-pace UPS wiring is in `~/.claude/`; the project-scoped write/session hooks are in `pos3/.claude/`. A `~/.claude`-only edit would NOT reach the writer. The corrected step (a) targets the runtime TREE, sidestepping the settings-scope trap entirely.
</content>
</invoke>
