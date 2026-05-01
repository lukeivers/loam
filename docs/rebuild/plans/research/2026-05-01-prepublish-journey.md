# 2026-05-01 — pre-publish journey: M9 scrub completion → memory infrastructure full repair → ready-for-cross-session-test

**Created:** 2026-05-01 (corpus-refresh hedge before owner runs cross-session memory continuity test).
**Purpose:** durable record of the session arc that drove canonical pos-v2 from "M-numbered amendments queued + memory partially broken" to "all pre-publish blockers closed + memory verified end-to-end + awaiting cross-session probe gate."

---

## Plan-style preamble (this doc + sibling refreshes authored together)

This file is the journey-doc the corpus-refresh dispatch named. Sibling artefacts authored in the same commit:

- **`docs/rebuild/STATE.md`** — header bumped to 2026-05-01; amendment-cycle row updated #75 → #96 with the seven 2026-05-01 amendments named; OSS-publish row tightened to "all pre-publish blockers CLOSED; awaiting cross-session memory probe before M11 dry-run"; change-log entry for 2026-05-01.
- **`docs/rebuild/FUTURE_IDEAS_DRAFT.md`** — three session-significant findings appended that the existing corpus did NOT carry: (a) bootstrap idempotency gap (first-run-only merge logic; workspaces miss any hook added post-first-run), (b) read-side success logging gap (`memory-reads.log` only carries exceptions; no success records), (c) plist-template divergence between `first_run_scaffold` and pos3's existing layout. The other six findings flagged by the dispatch (telegram channel rule, opus 4.7, graceful-fallthrough-with-detection CDC, stale-editable-installs, cross-source group_id convention, silent-swallow patterns) verified present at FIDRAFT lines 117-131.
- **`docs/rebuild/FUTURE_IDEAS.md`** — Ideas 22-26 confirmed stable. NO new graduations this pass; the post-amendment cleanup baseline is too recent to telegraph another round.
- **`.scratch/claude-output/oss-publish-master-dossier.md`** — refreshed: pre-publish blockers all CLOSED (memory infrastructure end-to-end verified empirically; all DECISION-SET items from the original 2026-04-29 dossier resolved); recommended sequence collapsed to "owner runs cross-session probe → M11 dry-run → M12 publish."

The dispatch's halt-and-surface triggers were: (1) STATE-vs-reality contradiction (none — git log matches what the dispatch named, plus a small reconciliation note: HEAD is `984e84e`, not `25ae41b` as the dispatch context wrote, because two follow-on `docs(plans)` commits landed for amendment #96 between dispatch authoring and execution); (2) FIDRAFT duplication (none discovered; the three additions slot cleanly under existing parent CDCs); (3) dossier-decision-no-longer-holds (none; the dossier's recommendations were ratified by execution); (4) ODD §2.5 violations in surrounding text (none in scope of doc-only edits); (5) wall-clock 60min ceiling (not approached).

---

## Session arc (chronological)

The session opened with the M9 substitution-pass amendment authored (the synthesis tool needed to rewrite canonical-path literals to public-form at synth time, NOT in-place in canonical, so dev-mode gate-detection assertions stay canonical). M9 sealed cleanly. Then the dispatch programme pivoted to memory infrastructure repair — the user-visible failure mode "memory not surfacing relevant content" was traced to multiple compounding root causes that needed sequenced sealed amendments.

### Phase 1 — M9 synth-time substitution pass (sealed `2161cb1`)

Closed AC.OSS.5 (residuals) by introducing `framework/tools/pos-publish-framework-only/src/.../synth/substitution.py` — applies a 4-entry locked SUBSTITUTION_TABLE to every shipping blob AFTER partition filter, BEFORE _LeafEntry construction. Binary-safe (UTF-8 decode try/except preserves bytes), idempotent (no replacement IS itself a substitution source), well-tested (4 new test files: substitution_after_partition / substitution_idempotent / substitution_binary_safe / substitution_smoke). 12 in-place fixture refactors landed alongside (Luke Ivers → Alice Anderson, /Users/lukeivers/ivers-corp-pos-v2 → \<workspace\>/loam, lukeivers/pos-v2 → lukeivers/loam) for shipping-surface files where the canonical-path literal was NOT load-bearing for dev-mode gate detection. Three load-bearing test files explicitly preserved canonical literals (test_AC_AG_1_wrong_wd_dispatch.py + test_AC_BAG_5_wrong_tree_write.py + test_d4_scope_binding.py) — substitution pass rewrites them at synth time. The M9 gate per master plan §6 sequencing rule #7 BEFORE M11 dry-run.

### Phase 2 — Memory-sidecar-recovery (sealed `8ee241b`)

Diagnostic agent traced the "memory not surfacing" failure to TWO independent root causes: (1) lifespan-leak in `framework/memory-system/src/service.py:115` where the FastAPI `lifespan` context manager never entered on certain initialisation paths — `graphiti not initialised (lifespan not entered)` had been silently failing on every UPS hook → memory_consumer → MCP call; (2) an idempotent reference_time schema migration that was needed to bring the Kuzu DB schema up to current expectations. Both fixed in this single amendment per the dispatch HSF rule. The memory-system silent-swallow patterns surfaced by the build agent (factory.py:201-206, observability.py:312/318, scope.py:91-94) were captured to FIDRAFT — out of scope for this amendment but added concrete evidence to the parent graceful-fallthrough-with-detection CDC's structural-enforcement candidate (e).

### Phase 3 — M1c-corrective (sealed `603e953`)

The M1.rename programme (M1a–M1g) had landed weeks earlier but trailing-edge stragglers slipped: `com.pos.orchestrator` launchd label remained instead of `com.loam.orchestrator`, and `dev-mode-manifest.yaml` lines 137-138 still referenced pre-M1 stale paths `tools/pos-amend/**` + `tools/orphan-plist-cleanup/**`. Closed in this amendment with a "rename-only" fence. Surfaced to FIDRAFT: (a) the broader manifest staleness problem (15 component dirs in `roots:` block still reference pre-M6b.0 top-level paths — dev-mode-manifest-realignment is a separate partition-design amendment, not mechanical), (b) orchestrator runtime-provisioning gap (`pos_orchestrator` not installed editable in canonical pos-v2 venv — process throttle-retry-locks; was running stably from a different venv pre-amendment), (c) 4+ orchestrator silent-swallow patterns at supervisor.py:539,556,563,570 + 295 + 555.

### Phase 4 — Post-M6 partition realignment (sealed `e2828ba`)

Three coherent items in one bundle: (a) gate-test files reclassified `dev_only` to match the gate-source files that moved to `plugins/dev-sdlc/hooks/` post-M6b.0; (b) corpus_gate path-list update to point at the moved ODD docs (`plugins/dev-sdlc/docs/odd-{methodology,in-loam}.md`); (c) `dev-mode-manifest.yaml` `roots:` + `always_loaded:` glob refresh to `framework/<comp>/`. The realignment uncovered 5 pre-existing cross-mode prose refs in 3 sealed-component artefacts (memory-system/launchd/README.md, primary-persona/templates/persona-template/prompt.md, workspace-sync/README.md) that were masked by the stale globs matching ZERO files; resolved in-amendment via `KNOWN_CROSS_MODE_DEBT` allowlist extension per F-pattern; queued 3 separate component-scoped scrub amendments post-v0.1.0.

### Phase 5 — Memory-pipeline-fix (sealed `67968b7`)

5 fix shapes in one amendment:

1. **Stop-hook re-seater** in `framework/primary-persona/src/.../pos_session_start.py` — workspaces that completed their bootstrap before the Stop hook stanza was added would never auto-write. Re-seater patches `.claude/settings.json` at session-start when the Stop entry is missing. (Closes the bootstrap idempotency gap for THIS specific hook; the broader gap stays open per FIDRAFT.)
2. **Visible empty-state retrieval render** in primary_persona — `_render_retrieval` now emits a structured "no relevant memory" message instead of silently rendering nothing. Persona always knows whether retrieval ran-and-found-empty vs ran-and-broke.
3. **`memory-reads.log` exceptions** — the read path now logs exceptions to NDJSON (was previously silently swallowed). NOTE: this is exception logging, not success logging — see FIDRAFT addition.
4. **Empty-contributor handling** in `serialise_turn` — when a contributor returns empty, persona skips it cleanly rather than producing degenerate output.
5. **Group-ID convention regression-pin test** — locks the convention so future amendments don't drift the workspace_slug vs default_scope_id behavior again.

### Phase 6 — FastMCP search-tool surface (sealed `25ae41b`)

The investigation agent rewrote the dispatch's framing: the filter was NOT broken. Root cause: the search MCP tool wrapped `graphiti.search()` which returns ONLY edges. Sparse-episode invisibility (newly-extracted episodes have edges still being built; visible content lives at the episode level for ~30s after extraction) made the search appear empty. Fix is a one-call substitution + return-shape grow: switched to `graphiti.search_(COMBINED_HYBRID_SEARCH_RRF)` which returns the edges+nodes+episodes superset, plus the persona consumer falls through to episodes when edges are empty (commits `8e33ee1` + `646e2c7`). This is the **FINAL pre-publish blocker** per the dispatcher.

### Phase 7 — pos3 operational alignment (NOT an amendment)

Outside the canonical pos-v2 amendment cycle, the pos3 workspace needed catch-up after canonical advanced 25 commits since pos3's last sync (6f272ce → 984e84e). Operations performed:

- `pos-sync` ff'd pos3/framework branch.
- 4 components' venv editable installs refreshed (pos-amend / loam-amend / loam-mode / others touched by M6b moves).
- Stop hook stanza added to pos3's `.claude/settings.json` by the M-pipeline reseater on first session-start post-sync.
- 10 legacy `com.pos-v2.*` launchd plists evicted; `com.loam.orchestrator` + `com.loam.pos3.memory-graphiti` loaded; health-200 verified.
- End-to-end memory verification via raw HTTP curl with `kestrel-9341` marker: write→search round-trip succeeds under `group_id=pos3`. Empirical proof memory infrastructure works at the protocol level.

This work doesn't ladder to a sealed-component amendment because it's pos3-side state, not framework code. It IS the prerequisite for the cross-session probe.

---

## First-principles reframe (owner-locked 2026-05-01)

Mid-session the owner reframed memory's ship-test:

> The actual ship-test for memory is **cross-session continuity** — user comes back later, persona has context. Within-session real-time retrieval is a side-effect; LLM extraction is async + slow (~30s/episode); within-session you race the extractor.

The pre-publish gate becomes: `/clear → fresh session → probe message → memory surfaces relevant content from prior session`. If yes, publish. If no, diagnose + fix + retry.

This reframe matters because all the within-session retrieval debugging earlier in the cycle was working against the wrong definition of success. Within-session retrieval working is desirable but NOT the gate; cross-session continuity IS.

---

## Owner's post-memory-verifies sequence

1. **/clear and run cross-session probe** — the actual ship-test. If memory surfaces prior content, gate cleared.
2. **M11 dry-run** — synthesis pipeline produces public-form output; owner gates the synthesised tree visually before publish.
3. **M12 publish** — push to `lukeivers/loam`.

The corpus-refresh dispatch this doc was authored under is the hedge: capture everything to disk BEFORE /clear so nothing depends on within-session memory continuity to recover.

---

## Cumulative status post-session

- **Amendment cycle:** #75 → #96 (21 amendments since the prior STATE refresh, of which 7 are 2026-05-01-dated). Numbering tracked in plan-doc §14 method-decision register backfills.
- **Pre-publish blockers:** all CLOSED. Last blocker was fastmcp-group-ids-filter-fix (#96, sealed `25ae41b`); memory infrastructure now produces edges+nodes+episodes superset on search.
- **Memory verification:** end-to-end empirically verified (raw HTTP curl with kestrel-9341 marker, group_id=pos3). Within-session retrieval working; cross-session test pending.
- **Awaiting:** the /clear → fresh session → probe → "did memory surface?" gate.
- **Post-gate:** M11 dry-run; M12 publish.

---

## Files touched in the corpus-refresh commit (this commit)

- `docs/rebuild/STATE.md` — header refresh, amendment-cycle row, OSS-publish row, change-log entry.
- `docs/rebuild/FUTURE_IDEAS_DRAFT.md` — three new entries appended.
- `.scratch/claude-output/oss-publish-master-dossier.md` — full refresh of the 2026-04-29 dossier.
- `docs/rebuild/plans/research/2026-05-01-prepublish-journey.md` — this file.

---

*Authored 2026-05-01 by main-session corpus-refresh dispatch. Hedge against /clear before cross-session memory probe. Single commit on `pos-v2` per the dispatch's acceptance shape.*
