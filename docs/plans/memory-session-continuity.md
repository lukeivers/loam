# Memory session-continuity — a session restart is behaviourally transparent

**Status:** PLAN-AUTHOR-ONLY cycle. Plan-doc + manifest authored to disk + committed (doc-only commits). NO source edits, NO apply, NO seal, NO version bump, NO publish. Build cycle DEFERRED to a future session pending owner ratification of the named decisions in §13.

**Slug:** `memory-session-continuity` (scope-descriptive per `feedback_scope_descriptive_ac_ids`; no version pre-baked — version derives at release time).

**Class (preliminary):** MINOR — additive ranking signal + a new session-start contributor + a corpus-membership extension. No existing retrieval contract is broken; the file-based store schema gains one indexed column. Could be argued PATCH if the recency signal is purely additive and the corpus extension is config-driven, but the new session-start contributor is a behaviour change at the session boundary → MINOR is the safe call. D-MSC.1 ratifies.

**Working directory (for the proposed build):** `/Users/lukeivers/loam/` (canonical loam — core memory-system improvement, not a pos3 experiment).

**Predecessor:** v0.10.8 SHIPPED PUBLIC (`58b1452` post-publish backfill; seal `688e85b`). Plan-author HEAD `96fc5a4`. Load-bearing sealed amendments this composes against: `SEAL_COMMIT.session-start-context-load-gate` (#32 D8 composer), `SEAL_COMMIT.memory-consumer-wiring` (#33 D7), `SEAL_COMMIT.m-fbm-operational-health` (M-FBM file-based pivot), `SEAL_COMMIT.v0-4-3-patch-memory-retrieval-bm25-fix` (BM25 phrase-quoting fix — already sealed), `SEAL_COMMIT.true-first-run` (#45 multi-contributor SessionStart registry), amendment #46 session-start/turn-start emitters (`session_start_emitter.py` runtime caller).

**Owner authorization:** PENDING. Surfaced via Telegram 11260 (2026-05-15). Owner's verbatim objective in §1.

**Status-file target:** `docs/STATE.md` (shipped-state record) + `docs/release-roadmap.md` (forward-looking) — bookkeeping itemized in §9.

**Quality bar:** structural over advisory (ODD). The test applied to every mechanism in this plan: *"can a future change re-introduce session-amnesia without active discipline?"* If yes, the mechanism is rule-shaped and a stronger one is sought; if no stronger one exists, it is marked advisory-fallback explicitly as a residual risk in §10.

---

## §1 — Outcome shape (the "why")

**Owner's verbatim intent (Telegram 11260, 2026-05-15):**

> "One of the primary goals of file-based memory is making it so that sessions don't matter at all. You should be able to know exactly where we were, but it shouldn't require any special session-end hooks or anything to get there. Just storing memories and then reading them for context should make it so that there is essentially no difference talking to you before and after a session restart."

**The outcome:** a session restart is *behaviourally transparent*. A fresh session reconstructs "where we were" — the active working thread plus the live decisions / pending rulings — from durably-stored memory read at session-start, **without any bespoke session-end capture hook**. The mechanism is continuous passive capture (which already exists and is healthy — see §4) plus a session-start read smart enough to surface the *most-recent active thread*, not stale episodes.

**The failure that triggered this (evidence-grounded):** a fresh session on 2026-05-15 did not know about the active "v0.11.0 / ODD-paper-corrective / ProgramBench-v2" thread that was the live topic immediately before restart. The most-relevant durable record of "where we were" — FIDRAFT entry `F-INVERTED-FRAME` at `docs/FUTURE_IDEAS_DRAFT.md:274` (verified present in canonical loam; names v0.11.0 + the paper-corrective + ProgramBench-v2 + "owner ruling pending pos3 task #75") — exists on disk but never surfaced at session-start.

**Prime-objective ladder (per `feedback_value_proposition_as_prime_objective` + plan-docs §4):**

- **AC.PO.1** (translation-burden test, `docs/VALUE_PROPOSITION.md:60`): session-amnesia forces the user to re-establish context after every restart — the maximal translation burden, paid every session boundary. Eliminating it is the single highest-leverage translation-burden reduction in the harness. Every AC below ladders up to AC.PO.1.
- **AC.PO.2** (harness-toolkit test, `docs/VALUE_PROPOSITION.md:66`): a recency-aware session-start memory read becomes a primitive the primary persona draws from on every session — it is toolkit, not a one-off. The session-start active-thread contributor is a registered, reusable composer contributor (the #32/#45/#46 substrate), not bespoke wiring.

`docs/STATE.md:3` already names this as the ship-gate: *"cross-session continuity IS the ship-test, not within-session retrieval."* This plan operationalises that recognised gate.

---

## §2 — Class + current-state-with-evidence

### Current architecture (verified, file + content cited)

1. **Continuous passive capture exists and is healthy.** `framework/primary-persona/src/loam/primary_persona/memory_write_worker.py` is the long-running launchd-mediated drain of the disk-backed queue; `FileMemoryStore.write_episode` (`file_memory.py:241`) writes one markdown episode per turn at `<workspace>/workspace/.loam/memory/episodes/<slug>/<YYYY-MM-DD>/<turn-id>.md`. Empirically verified on pos3: **614 episode files on disk**, most-recent dated 2026-05-15, worker writing turns through 11:26 UTC the same day (`workspace/.pos/memory-writes.log` tail shows `worker-ok` entries 2026-05-15T11:26). **Capture is not the failure.** The owner's "no special session-end hooks" constraint is *already satisfied* — capture is continuous/passive, not session-end-gated.

2. **The kuzu/graphiti store deletion is BY DESIGN, not data loss.** `file_memory.py:38` D-Q.MFBM.6: *"kuzu_db state migration: discard."* The `D workspace/data/memory-system/kuzu_db` git status the dispatch cited is the *intended* M-FBM file-based pivot (`SEAL_COMMIT.m-fbm-operational-health`), not a regression. `framework/tools/loam-memory-inspect/` is the one-shot inspection script the discard left behind. See §10 F2 — the dispatch's "Gap A — store wipe" framing is partially mis-stated and is corrected here.

3. **The BM25 phrase-quoting defect is already fixed and sealed.** The 2026-05-09 investigation (`<pos3>/workspace/.scratch/claude-output/memory-retrieval-quality-investigation.md`) identified `safe_query = '"' + query + '"'` phrase-wrapping as a zero-hit defect. Current `file_memory.py:508` uses `_tokenize_for_fts` (OR-of-tokens, AC.V043.1) and `SEAL_COMMIT.v0-4-3-patch-memory-retrieval-bm25-fix` is sealed. **That investigation predates the fix; it is not an open gap.** This plan does not touch token sanitisation.

4. **Memory is NOT consulted at session-start at all.** `context_composer.py:363` `on_session_start` iterates contributors and **skips every contributor whose `trigger_kind != TriggerKind.session`**. Both memory contributors register at `TriggerKind.turn` (`file_memory.py:834` `register_file_memory_retrieval` → `TriggerKind.turn`; `memory_consumer.register_memory_retrieval` → `TriggerKind.turn`). The session-start payload (`session_start_gate.compose_session_fields`, `session_start_gate.py:334`) carries baseline-corpus presence + in-flight amendment filenames + service state + cost headroom — **it never queries the episode store.** A fresh session sees nothing from memory until the first user prompt, and even then the query is the *user's prompt text*, not "what was the most recent active thread."

5. **`_fts_search` ranks by pure BM25 relevance, zero recency weighting.** `file_memory.py:489` `_fts_search` SQL ends `ORDER BY score LIMIT ?` where `score = bm25(episodes)`. The FTS5 schema (`file_memory.py:459`) declares `reference_time UNINDEXED` — the timestamp is *stored but never used for ranking*. The grep fallback (`_grep_search`, `file_memory.py:547`) sorts by length-normalised term count, also recency-blind. A 2026-05-02 episode that lexically matches the query out-ranks a 2026-05-15 episode that is the actual active thread.

### The two gaps — confirmed, one reframed

- **Gap A — durable-surface-not-in-session-start-corpus (REFRAMED from "store wipe").** The dispatch framed Gap A as a store-wipe / durability problem. **Evidence corrects this:** capture is healthy, the store is intact (the kuzu deletion is by-design M-FBM), and the active-thread episodes ARE on disk. The real Gap A is twofold: (a) the named-thread *digest* surfaces (FIDRAFT-class entries like `F-INVERTED-FRAME` that explicitly say "where we were + owner ruling pending") are not in the session-start auto-load corpus (`session_start_gate.discover_baseline_corpus` reads only the CLAUDE.md "Session-start discipline" backtick-path list); and (b) episode memory is never read at session-start at all (current-state finding #4). Both are structural, not data-loss.

- **Gap B — retrieval recency-ranking absent (CONFIRMED exactly as dispatched).** `_fts_search` ORDER BY is pure BM25; `reference_time` is `UNINDEXED`. Recency-of-active-thread is the missing ranking signal. Confirmed at `file_memory.py:489–528` + `:459`.

---

## §3 — Scope fence (in-scope vs out-of-scope)

### In-scope (PRIMARY)

1. **Recency-aware ranking in the file-based retrieval path** (closes Gap B). `reference_time` becomes a ranking input alongside BM25 relevance, so the most-recent-active-thread episodes are reachable in the top-N for a recency-shaped query. Method is the builder's call (recency-decay blend, recency-tiebreak, time-bucketed re-rank — any mechanism that satisfies the AC).
2. **A session-start active-thread contributor** (closes Gap A part (b)). A `TriggerKind.session` contributor that, at every session-start, surfaces a bounded digest of the most-recent active working thread reconstructed from the episode store + the named-thread durable surfaces — without any session-end hook. Composes on the existing #32/#45/#46 composer + contributor-registry substrate (Lens 1 — no new hook machinery).
3. **Named-thread durable surfaces enter the session-start corpus** (closes Gap A part (a)). The session-start corpus auto-load set explicitly includes the FIDRAFT-class durable surface(s) that record "where we were + open owner rulings" (`docs/FUTURE_IDEAS_DRAFT.md` and any peer named-thread surface D-MSC.3 identifies), so a fresh session sees the live-thread digest even when episode retrieval ranks imperfectly (defence-in-depth — two independent paths to the same outcome).

### In-scope (SECONDARY)

4. The `search-index.sqlite` FTS5 schema gains `reference_time` as a rankable column (today `UNINDEXED`), and the index-rebuild path stays backward-compatible (a pre-existing index missing the column rebuilds rather than erroring — the existing grep fallback already covers index-absence).
5. A cross-session-continuity smoke probe: cold session-start in a workspace whose most-recent episodes are a known active thread → assert the active-thread digest is surfaced (the §10 HARD smoke).

### Out-of-scope (explicit)

- Rewriting graphiti / kuzu wholesale (the M-FBM pivot already removed graphiti from the runtime path; this plan does not reintroduce it).
- The ODD-paper corrective itself + ProgramBench v2 (those are the *content* of the active thread, not the continuity mechanism — separate work tracked under `F-INVERTED-FRAME`).
- Embedding-based / vector retrieval (D-Q.MFBM.2 defers embeddings; no Anthropic API key per `feedback_no_anthropic_api_key` — any future ranking stays stdlib + `claude -p` only).
- Token sanitisation / BM25 query construction (already fixed + sealed at `SEAL_COMMIT.v0-4-3-patch-memory-retrieval-bm25-fix`).
- Episode *content* schema (the evidence-vs-interpretation split is a separate plan-only artefact at `<pos3>/.../memory-schema-evidence-vs-interpretation-plan-2026-05-14.md`; see §11 reconciliation).

### Out-of-scope (deferred — captured for follow-on)

- A `loam memory thread` interactive verb to inspect/pin the active thread (FIDRAFT-track at build time if the digest proves useful as an on-demand surface).
- Per-workspace recency-decay tuning knob (ship a sane default; tuning is a follow-on if the default mis-weights on long-running workspaces).

---

## §4 — Acceptance criteria (`AC.MSC.*`)

All ACs are outcome-shape and deterministic. Method-in-AC test applied to each: *can this AC be satisfied by a method other than the one the author has in mind?* — answered per AC.

### AC.MSC.1 — Recency reaches the top-N (Gap B closed)

**Outcome:** given an episode store containing (a) an older episode with a strong lexical match to a recency-shaped query and (b) a newer episode that is the active thread with a weaker-but-present lexical match, a recency-shaped retrieval surfaces the newer active-thread episode within the returned top-N results. The older lexically-stronger episode does not crowd the active thread out of the result set.

**Verification:** a fixture store with a dated older-strong / newer-active pair; assert the newer-active episode is present in the top-N for the recency-shaped query.

**Method-in-AC test:** PASS — satisfiable by recency-decay blend, recency tiebreak, time-bucket re-rank, or a separate recency channel. Method is the builder's call.

### AC.MSC.2 — Session-start surfaces the active thread without a session-end hook (Gap A part (b) closed)

**Outcome:** a fresh session (no prior in-session state, no session-end hook having run) receives, in its session-start `additionalContext`, a bounded digest of the most-recent active working thread reconstructed from the durably-stored episodes. The digest names the live topic and any pending owner ruling associated with it. No session-end / Stop-hook capture is required for this to be present — capture is the already-existing continuous passive worker only.

**Verification:** seed a workspace's episode store with a known active-thread sequence; run the session-start CLI cold; assert the emitted `additionalContext` contains the active-thread topic marker. Separately assert no Stop / session-end hook is invoked or required by the path (the contributor reads only the episode store + named-thread surfaces).

**Method-in-AC test:** PASS — satisfiable by an episode-recency scan, a last-N-turns roll-up, an LLM-`claude -p` digest of recent episodes, or a named-thread-surface read. Method is the builder's call. (Constraint, not method: any LLM step is `claude -p` subprocess per `feedback_no_anthropic_api_key`.)

### AC.MSC.3 — Named-thread durable surfaces are in the session-start corpus (Gap A part (a) closed)

**Outcome:** the session-start baseline-corpus presence set includes the named-thread durable surface(s) that record "where we were + open owner rulings" (FIDRAFT-class). When that surface exists on disk, a fresh session's session-start payload reflects its presence and its live-thread content is reachable at session-start; when absent, the existing graceful-missing sentinel path applies unchanged.

**Verification:** with the named-thread surface present, assert it appears in the session-start corpus-presence set / contributor output; with it absent, assert the session-start payload still composes (graceful-missing, no raise) per the existing `corpus_gate_state` contract.

**Method-in-AC test:** PASS — satisfiable by extending the CLAUDE.md session-start-discipline path list, a dedicated corpus-membership config, or a contributor that reads the surface directly. Method (and exactly which surfaces, per D-MSC.3) is the builder's call.

### AC.MSC.4 — Behavioural-transparency probe (the prime outcome, end-to-end)

**Outcome:** in a workspace whose most-recent durably-stored memory is a known active thread with a pending owner ruling, a cold session-start (simulating a session restart) produces session context from which the active thread + its pending ruling are recoverable, with no in-session state and no session-end hook having run. The before-restart and after-restart context are not behaviourally identical byte-for-byte, but the *active-thread + pending-ruling* facts are present in both.

**Verification:** the §10 HARD smoke — cold session-start against a seeded active-thread store; assert the active-thread topic + pending-ruling marker are present in the emitted session context. This is the outcome-altitude AC; AC.MSC.1–3 are the mechanism ACs that ladder into it.

**Method-in-AC test:** PASS — this is pure outcome (active-thread recoverable post-restart); every method that achieves it satisfies it.

### AC.MSC.5 — Backward-compatibility + fail-soft preserved

**Outcome:** every existing memory-retrieval and session-start test stays green; a pre-existing FTS5 index without the new rankable column does not error (rebuild-or-fallback, never raise); the session-start contributor is fail-soft (any error inside it yields an empty block, the session proceeds) consistent with the existing AC46.4 / AC.MFBM.2 fail-closed contracts.

**Verification:** existing `primary-persona/` + `hands-off-lifecycle/` suites green; an index-missing-column fixture exercises the rebuild/fallback path; a contributor-raises fixture asserts empty-block + session-proceeds.

**Method-in-AC test:** PASS — outcome is "nothing regresses, nothing raises"; method (index migration vs rebuild-on-mismatch) is the builder's call.

### AC.MSC.S — Seal-diff discipline

**Outcome:** the seal diff is confined to `framework/primary-persona/`, `docs/plans/`, and (only if D-MSC.3 selects the CLAUDE.md-path-list mechanism) the workspace-corpus surface that supplies the session-start path list. No unrelated sealed component is touched without a manifest entry.

**Verification:** the component's existing `test_no_sealed_amendments` + H19 cross-cutting seal-diff test.

---

## §5 — Build-time decisions (preliminary rulings; build-time empirical recheck may shift)

### D-MSC.1 — Class: MINOR vs PATCH

**Preliminary:** MINOR. **Rationale:** AC.MSC.2 introduces a new behaviour at the session boundary (a session-start contributor that did not exist), which is a feature addition, not a defect fix. **Recheck at build:** if the active-thread digest is implemented purely as a recency-reordering of an already-emitted block and the corpus extension is config-only, PATCH is arguable — but the safe call is MINOR; downgrade only on explicit build-time evidence that no new behaviour crosses the session boundary.

### D-MSC.2 — Recency-vs-relevance blend shape (Gap B mechanism)

**Preliminary:** recency-decay blended with BM25, NOT recency-only (recency-only would surface the latest episode regardless of relevance, drowning a genuinely-relevant older answer). Decay half-life default preliminary ~3–7 days (active-thread horizon). **Recheck at build:** the §10 smoke fixture is the arbiter — tune the blend until both "active thread surfaces" AND "a directly-relevant older answer still surfaces for a non-recency query" hold. Builder's call on the exact function (linear decay / exponential / time-bucket); the AC pins the outcome, not the curve.

### D-MSC.3 — Which durable surfaces enter the session-start corpus

**Preliminary:** `docs/FUTURE_IDEAS_DRAFT.md` is the primary named-thread surface (it carries the F-INVERTED-FRAME-class "where we were + pending ruling" entries by the existing surface-to-chat-then-append convention). **Recheck at build:** evaluate whether `docs/STATE.md` (shipped-state) and the active in-flight plan-doc set are also load-bearing for "where we were"; the risk of over-inclusion is session-start payload bloat against the 10k `ADDITIONAL_CONTEXT_CAP`. Preliminary: FIDRAFT in, STATE.md already effectively in via in-flight-amendment enumeration, active plan-docs surfaced as references not inlined. Builder ratifies the exact set against the cap budget.

### D-MSC.4 — Session-start digest construction: scan vs `claude -p`

**Preliminary:** start with a deterministic recency-scan roll-up of the most-recent episode date-dir (stdlib only, zero LLM cost, fast — fits the 5s session-start hook timeout). A `claude -p` summarisation pass is a follow-on enrichment ONLY if the deterministic roll-up proves too noisy. **Hard constraint (not a decision):** any LLM step is `claude -p` subprocess per `feedback_no_anthropic_api_key` — never an SDK/API key. **Recheck at build:** the 5s `build_persona_session_start_inner_hook` timeout (`session_start_emitter.py:346`) bounds this; a `claude -p` call may not fit — the deterministic path is the safe default.

### D-MSC.5 — FTS5 schema migration vs rebuild-on-mismatch

**Preliminary:** rebuild-on-mismatch (a pre-existing index whose schema lacks the rankable column is dropped + rebuilt lazily on next write/search), reusing the existing grep fallback as the during-rebuild path. No explicit ALTER migration — the index is a derived cache, the episodes are the source of truth (`file_memory.py:224` "stateless apart from the filesystem"). **Recheck at build:** confirm rebuild latency on a 600+-episode store is within the search-time bound; if not, an in-place migration is the builder's call.

---

## §6 — Source items (FIDRAFT entries / surfaces this closes or composes with)

- `docs/FUTURE_IDEAS_DRAFT.md:274` — `F-INVERTED-FRAME` (the active thread that failed to surface; this plan makes its session-start surfacing structural). Not closed by this plan — its *content* (ODD-paper corrective) is separate work — but its *surfacing* is the AC.MSC.3 fixture.
- `docs/STATE.md:3` — names cross-session continuity as the ship-test; this plan operationalises that line.
- `<pos3>/workspace/.scratch/claude-output/memory-retrieval-quality-investigation.md` — 2026-05-09 BM25 investigation; **already resolved** by `SEAL_COMMIT.v0-4-3-patch-memory-retrieval-bm25-fix`; cited here so the build does not re-open a sealed fix.

---

## §7 — Composes with / supersedes (reconciliation with in-flight + prior work)

**Reconciliation verdict:** NO in-flight amendment overlaps the PRIMARY scope. All five named amendments are SEALED predecessors this composes ON, not parallel work. Detail:

| Amendment | Seal status | Relationship to this plan |
|---|---|---|
| #24 memory-system-mcp-migration | Superseded by M-FBM file-based pivot (`SEAL_COMMIT.m-fbm-operational-health`) — no live MCP runtime path. | This plan operates on the file-based substrate (`file_memory.py`), the post-#24 reality. No overlap. |
| #33 memory-consumer-wiring | SEALED (`SEAL_COMMIT.memory-consumer-wiring`). | Provides the `_render_retrieval` shape this plan's session-start contributor reuses. Composes on. |
| #34 memory-system-eager-lifespan-d1-conformance | Manifest present; graphiti-lifespan scoped — graphiti is out of the M-FBM runtime path. | Not load-bearing for file-based continuity. No overlap. |
| #45 merge-session-start-multi-contributor | SEALED (`SEAL_COMMIT.true-first-run`). | Provides the multi-contributor SessionStart registry the AC.MSC.2 contributor registers into. **This is the Lens-1 leverage point — no new hook machinery.** Composes on. |
| #46 persona-session-start-turn-start-emitters | SEALED (runtime caller `session_start_emitter.py`). | Provides `build_session_composer` + the session-start CLI the AC.MSC.2 contributor is registered through. Composes on. |

**Prior investigation artefacts reconciled:**

- `memory-retrieval-quality-investigation.md` (2026-05-09) — RESOLVED + sealed; this plan explicitly does NOT re-open token sanitisation (§3 out-of-scope).
- `file-based-memory-systems-survey.md`, `memory-curated-backfill-report.md`, `phase-b-memory-capture-loop-2026-05-11.md` — capture-loop research; confirm continuous-capture is the sanctioned shape (consistent with the empirical finding that capture is healthy). This plan builds on the capture loop, does not replace it.
- `memory-schema-evidence-vs-interpretation-plan-2026-05-14.md` (pos3, plan-only) — a SEPARATE plan-only artefact about episode *content* schema (evidence vs interpretive claims). **Orthogonal:** that plan changes what is stored per episode; this plan changes how stored episodes are *ranked + surfaced at session-start*. They compose cleanly (a richer episode schema makes a better digest) but neither depends on the other. Surfaced here per F2 so the owner can sequence them; no scope collision.
- `memory-write-worker.{err,out}.log` + `memory-writes.log` (pos3) — empirical proof the worker runs; cited as current-state evidence (§2 finding #1).

**No halt-and-surface fired during reconciliation:** no in-flight amendment delivers any part of this objective; no scope to halt.

---

## §8 — Estimated AI-time + cost (per `feedback_duration_estimation_rubric`)

AI-time only (10–50× human-developer; `wall_clock_min ≈ tool_calls × 0.1–0.15`). Owner gate-review time is separate and not included.

| Phase | Band | Midpoint |
|---|---|---|
| Recency-blend ranking edit + tests (Gap B) | 12–22 min | ~17 min |
| Session-start active-thread contributor + registration + tests (Gap A part b) | 18–35 min | ~26 min |
| Corpus-membership extension + tests (Gap A part a) | 8–15 min | ~11 min |
| FTS5 schema rebuild-on-mismatch + backward-compat suite | 8–15 min | ~11 min |
| `loam amend validate` + baseline backfill + apply + seal + §13 §status backfill + roadmap-row seal-SHA backfill | 15–30 min | ~22 min |
| HARD smoke (cold-session cross-session-continuity probe) writeup + run | 12–25 min | ~18 min |
| **Total build cycle (serialized, single working tree)** | **73–142 min** | **~105 min** |

**Cost:** $0 incremental if D-MSC.4 stays deterministic (stdlib-only, zero `claude -p` calls). If a `claude -p` digest enrichment is selected at build, add ~$0.50–1.50 for the smoke-run digest calls (Sonnet default; band per `claude_print_client` characteristics). No Anthropic API key — subscription-only via `claude -p` (`feedback_no_anthropic_api_key`).

**Build-cycle serialization:** serializes against any concurrent amendment build in the same working tree per `feedback_serialize_amendment_builds`; verify at build dispatch via `loam amend status`. Plan-author cycle file-touch fence is strictly `docs/plans/memory-session-continuity.md` + `.manifest.yaml` (parallel-safe with other plan-author / research agents).

---

## §9 — Bookkeeping (backfill items at build-cycle seal time)

1. `docs/STATE.md` — append a shipped-state line under the v0.10.x record once sealed (cross-session-continuity mechanism shipped; the §3 ship-gate line at `STATE.md:3` updated from "awaiting cross-session memory probe" to the sealed mechanism).
2. `docs/release-roadmap.md` — add the row + backfill the seal SHA at seal time.
3. The plan-doc §13 §status matrix flips PENDING → GREEN/YELLOW/RED at build-cycle time.
4. The §14 method-decision register (this plan's D-MSC.{1–5}) is backfilled post-build: which preliminary rulings stuck, which shifted, the empirical evidence that drove any shift, the SHA register for plan-doc + source-edit + apply + seal commits.
5. `F-INVERTED-FRAME` FIDRAFT entry: add a note that its *surfacing* is now structural (its content remains OPEN — separate work).

---

## §10 — F2 Ruthless Feedback (honest doubts + design risks named)

1. **The dispatch's "Gap A — store wipe / capture-durability" framing is partially wrong — named, with evidence, with the alternative.** *Disagreement:* the dispatch attributes Gap A to a deleted kuzu store + a non-running memory service. *Evidence:* `file_memory.py:38` D-Q.MFBM.6 makes the kuzu discard intentional (M-FBM pivot, `SEAL_COMMIT.m-fbm-operational-health`); the file-based store is the *current sanctioned runtime*; `workspace/.pos/memory-writes.log` shows the capture worker wrote 614 episodes including 2026-05-15T11:26 — capture is healthy, nothing was lost. The `service_state: memory: not_expected` session-start signal is the *correct* M-FBM signal (`session_start_gate.py:228`), not a fault. *Alternative:* Gap A is correctly framed as (a) named-thread durable surfaces not in the session-start corpus + (b) episode memory never read at session-start at all. The plan is built on the corrected framing. **If the build is dispatched on the original framing it will chase a store-durability fix that does not exist and miss the real structural gaps.**

2. **The "no session-end hooks" constraint is already satisfied — and that is load-bearing for the design.** Continuous passive capture (the worker) is not session-end-gated. The plan does NOT introduce any session-end hook and does not need to: the entire fix is read-side (session-start) + ranking-side. If a future builder reaches for a Stop-hook to "capture where we were," that violates the owner constraint AND is unnecessary — capture already happens continuously. This is named as a build-time halt trigger in §12.

3. **Residual risk — the deterministic recency roll-up may not equal "knowing exactly where we were."** A recency scan surfaces *recent episodes*; it does not *understand* the thread. The owner's bar is "no difference talking to you before and after a session restart" — a strong bar. The deterministic digest (D-MSC.4 preliminary) is a structural floor that guarantees the active-thread *episodes* and the *named-thread surface* are present; it does not guarantee the persona *synthesises* them into "here's exactly where we were" without reading them. **This is marked an explicit residual risk, not silently accepted:** the structural mechanism eliminates the *amnesia* failure class (the facts are present and reachable); whether the persona then *uses* them well is a persona-discipline axis the structural floor enables but does not itself enforce. A `claude -p` digest (D-MSC.4 follow-on) tightens this but risks the 5s session-start timeout. The honest statement: this plan makes session-amnesia *structurally impossible to reproduce without active discipline* (the facts are always surfaced), which is the dispatched bar; it does not make the persona's *use* of those facts structural — that is the correct scope boundary and the residual is named here rather than over-claimed.

4. **Defence-in-depth is deliberate, not redundant.** AC.MSC.2 (episode-recency digest) and AC.MSC.3 (named-thread surface in corpus) are two independent paths to the same outcome. If recency ranking mis-weights on an edge-case store, the corpus-membership path still surfaces the named-thread digest. Two mechanisms for one outcome is justified here because the failure being prevented (session-amnesia) is the maximal-translation-burden failure (AC.PO.1) and a single point of failure on the prime objective is unacceptable. This is an asymmetric-leverage call, named explicitly.

---

## §11 — Authority chain

Plan-author authors the plan + named decisions WITH recommendations (§13). Owner ratifies the named decisions before any build-cycle dispatch. This plan-author cycle is doc-only + fully reversible (plan-doc + manifest only; no source edits, no apply, no seal). Fail-closed: §10 risk 3 is the named advisory-residual — the structural mechanism eliminates the amnesia failure class; persona *use* of surfaced facts is the named boundary, not silently absorbed.

---

## §12 — Halt triggers (the builder obeys these in-flight)

1. **Session-end-hook reach.** If the build finds itself adding any Stop / SessionEnd capture hook to make continuity work, HALT — the owner constraint forbids it and capture is already continuous (§10 risk 2). Surface the conflict + the read-side alternative; do not silently design in a session-end hook.
2. **Sealed-component widening.** If closing Gap A part (a) requires touching a sealed component not in the manifest (beyond `primary-persona/` + the D-MSC.3-selected corpus surface), HALT and surface rather than widen.
3. **Cap overflow.** If the session-start active-thread digest + corpus extension pushes the session-start payload past `ADDITIONAL_CONTEXT_CAP` (10k, `context_composer.py`), HALT — the digest must be bounded; surface the bound-vs-completeness trade for owner ruling rather than silently truncating load-bearing thread context.
4. **Recency drowns relevance.** If the §10 smoke shows the recency blend surfaces the latest episode at the cost of a directly-relevant older answer for a non-recency query (AC.MSC.1 regression), HALT and re-tune D-MSC.2 rather than shipping a blend that trades retrieval quality for recency.
5. **ODD violation in surrounding code.** If the build discovers an ODD §2.5 violation (unnamed code path) in the surrounding memory-system code, surface it — do not silently extend it (`feedback_subagent_odd_violation_halt`).

---

## §13 — §status

**Build cycle:** PLAN-AUTHOR-ONLY cycle. Plan-doc + manifest authored to disk + committed (doc-only commits). NO source edits, NO apply, NO seal, NO version bump, NO publish. Build cycle DEFERRED to a future session pending owner ratification of §13 named decisions.

**Plan-doc commits:** plan-doc + manifest TBD-AT-COMMIT (single doc-only commit pair authored by this cycle).

### AC verdict matrix (PENDING — flipped to GREEN / YELLOW / RED / DEFERRED at build-cycle time)

| AC | Verdict | Evidence |
|---|---|---|
| AC.MSC.1 — recency reaches top-N (Gap B) | PENDING | flipped at build-cycle time |
| AC.MSC.2 — session-start surfaces active thread, no session-end hook (Gap A b) | PENDING | flipped at build-cycle time |
| AC.MSC.3 — named-thread surfaces in session-start corpus (Gap A a) | PENDING | flipped at build-cycle time |
| AC.MSC.4 — behavioural-transparency probe (prime outcome) | PENDING | flipped at build-cycle time |
| AC.MSC.5 — backward-compat + fail-soft preserved | PENDING | flipped at build-cycle time |
| AC.MSC.S — seal-diff discipline | PENDING | flipped at build-cycle time |

### Named decisions the owner must rule on (recommendation-first)

1. **Ratify the corrected Gap A framing.** *Recommendation: ratify.* Gap A is NOT a store-wipe/durability problem (the kuzu deletion is by-design M-FBM, capture is healthy — 614 episodes, worker writing 2026-05-15). Gap A is: (a) named-thread surfaces not in session-start corpus + (b) episode memory never read at session-start. Building on the original framing chases a non-existent durability fix. *Owner rules only because this reframes the dispatched diagnosis (F2).*

2. **D-MSC.3 — which durable surfaces enter the session-start corpus.** *Recommendation: `docs/FUTURE_IDEAS_DRAFT.md` as the primary named-thread surface; STATE.md already effectively covered via in-flight-amendment enumeration; active plan-docs surfaced as references not inlined.* Risk is session-start cap bloat; builder ratifies the exact set against the 10k cap at build time. *In-scope autonomous if owner defers; surfaced because over/under-inclusion is a judgement call.*

3. **D-MSC.4 — session-start digest: deterministic scan vs `claude -p`.** *Recommendation: deterministic recency-scan roll-up first (stdlib, $0, fits the 5s hook timeout); `claude -p` enrichment as a follow-on only if the deterministic digest proves too noisy.* No Anthropic API key — `claude -p` only if used at all (`feedback_no_anthropic_api_key`).

4. **Class: MINOR.** *Recommendation: MINOR* (new session-boundary behaviour). Downgrade to PATCH only on explicit build-time evidence no new behaviour crosses the session boundary. *Autonomous-class decision; surfaced for visibility only.*

5. **Sequencing vs the evidence-vs-interpretation schema plan.** *Recommendation: ship this plan independently; the two are orthogonal* (this = ranking/surfacing; that = episode content schema). They compose but neither blocks the other. *Owner sequences; no scope collision.*

The single owner action required to unblock the build cycle: **ratify decision 1 (the corrected Gap A framing)**. Decisions 2–5 carry recommendations the builder can act on autonomously if the owner defers; only decision 1 reframes the dispatched diagnosis and is the gating ruling.

---

## §14 — Method decisions (post-build backfill)

Populated at build-cycle time. §5 names the build-time decisions (D-MSC.{1,2,3,4,5}); each is a preliminary ruling at plan-time. Post-build §14 backfill captures: which preliminary rulings stuck; which shifted; the empirical evidence that drove any shift; the SHA register for plan-doc + source-edit + apply + seal commits.

| Item | SHA |
|---|---|
| Plan-doc + manifest (this cycle) | TBD-AT-COMMIT |
| Source edits (build cycle) | TBD-AT-BUILD |
| Manifest baseline backfill | TBD-AT-BUILD |
| Apply + seal | TBD-AT-BUILD |
| §13 §status backfill + roadmap-row seal-SHA backfill | TBD-AT-BUILD |
