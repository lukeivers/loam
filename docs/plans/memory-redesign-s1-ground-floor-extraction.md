# Memory redesign — Stage 1a: Ground-floor extraction (constitutional carve-out of the ranked pool)

**Status:** BUILT (S1a). Owner-ratified rev-2 plan; owner GO on the three forks (2026-07-02).
**Component (sealed):** `framework/primary-persona` — advances the existing sidecar (`new_component: false`).
**Design source:** `workspace/strategy/research/memory-human-vs-harness-2026-07-02/synthesis-v2.md` (Stage 1 + Stage 3 threshold) + owner refinements (`owner-refinements-2026-07-02.md`, `owner-refinements-round2-2026-07-02.md`).

---

## 1. Objective

Carve the always-on constitutional FLOOR (the `CLAUDE.md` hierarchy) OUT of the relevance-ranked per-turn memory pool, so nothing that must-always-appear competes for a scored slot a genuinely-topical fact should hold. The floor still injects unconditionally via surfaces that are NOT the ranked pool. This is the first, safety-critical, reversible stage; it makes the later ranker changes (S3) safe.

Scope: **S1a only** — the safe subtraction. The physical CLAUDE.md file-split (moving the situational design lenses into a rules store) is **S1b, deferred to land with S4's situational recall** (removing them from the always-on floor before a situational-recall destination exists would open a discipline gap). No CLAUDE.md file is edited; no lens is moved in S1a.

---

## 2. Findings pinned at build (Tier-0, from canonical live code)

- **The ranked-pool cap is `DEFAULT_TOP_N = 5`** (`keep_pace/retrieval.py:72`, "AC.KP1.3 — top-N injection cap, design recipe N ≤ 5"), threaded as `num_results`/`top_n` through corpus search, episode search, and `combined[:top_n]`. `INJECTION_CHAR_CAP = 5000` bounds bytes. (The `MAX_ROWS_PER_CATEGORY=5` in `monitor.py` is a separate surface — the work-status AwarenessBlock.) **The carve is authored K-AGNOSTIC:** removing a source from the pool is correct under both today's top-K and the redesign's future relevance-threshold (S3), and is forward-compatible (the threshold then operates only over genuine facts). No AC names the number 5.
- **Only the GLOBAL `~/.claude/CLAUDE.md` is in the ranked pool** — via `discover_corpus`'s `claude_homes` loop, fed by the two live resolvers (`_resolve_live_config`, `_resolve_composer_config`). The 383-line PROJECT `CLAUDE.md` (the 8 design lenses) is always-on via the SessionStart corpus-inline floor + native load, NOT the ranker. Both files are also natively loaded by Claude Code every session.

## 3. The carve (as built)

The always-on constitutional floor is redundant in the ranked pool: it is injected unconditionally by the SessionStart corpus-inline floor (main session), the subagent microkernel bundle, and native CLAUDE.md load. Ranking it wastes a scored slot and starves topical facts.

Implementation — a NAMED, reversible lever at the LIVE-CONFIG layer (where ranked-pool policy belongs), leaving the general `discover_corpus` contract + every direct-config caller untouched:
- `keep_pace/retrieval.py`: new module constant **`RANK_CONSTITUTIONAL_FLOOR = False`** (S1a default = carve active). Both resolvers thread `claude_homes=(claude_home,) if RANK_CONSTITUTIONAL_FLOOR else ()`. `objectives_home` is unchanged (OBJECTIVES.md is the anchor source, not the floor).

Fence: `framework/primary-persona/src/loam/primary_persona/keep_pace/retrieval.py` + `framework/primary-persona/tests/test_AC_GFE_*`. NOT touched: `discover_corpus`, `RetrievalConfig`, `corpus_inline_session_start.py`, `bundle.py`, `principle_reminder.py`, any `CLAUDE.md` file, `settings.json`.

Blast radius: `retrieve()` is on the live per-turn path (main-session UserPromptSubmit + SessionStart composer + every subagent memory tier — all three share the two resolvers), but the change only removes a source, wrapped in the existing fail-open contracts.

Rollback: git-revert the seal, OR flip `RANK_CONSTITUTIONAL_FLOOR` True to re-admit the constitution into the ranked pool byte-for-byte (nothing deleted; floor content on disk untouched).

---

## 4. Acceptance criteria (outcome-shape, K-agnostic)

- **AC.GFE.1** — the live resolvers do not thread the `~/.claude` constitutional home into the ranked corpus (`claude_homes == ()`), for any prompt. Verified: `test_AC_GFE_1_*`.
- **AC.GFE.2** — the constitution still injects every session via the existing floor: the SessionStart corpus-inline always-load set still carries `CLAUDE.md` (removed from ranking, retained on the floor). Verified: `test_AC_GFE_2_*`.
- **AC.GFE.3 (outcome-altitude)** — over the production resolver + `retrieve()` with no pre-arranged state, on a query where the constitution previously ranked alongside a topical hit: the ranked block carries the topical hit and no constitutional hit (any count); flipping the lever on restores the constitutional hit (proving it was competing for the freed slot). Verified: `test_AC_GFE_3_OA_freed_slot_topical_hit.py`.
- **AC.GFE.4** — no regression: the general `discover_corpus` contract is unchanged (a direct caller passing `claude_homes` still gets `CLAUDE.md`); the KP1/FBMU/FBM-FILTER/SRF/RQ80/SUP/DLG suites stay green. Verified: `test_AC_GFE_4_*` + full-suite run.
- **AC.GFE.5** — reversible by the named `RANK_CONSTITUTIONAL_FLOOR` lever; flipping it True re-admits the constitution in both resolvers exactly as pre-carve. Verified: `test_AC_GFE_5_*`.

---

## 5. Deferred (owner-ruled)

- **S1b** — physically split the situational design lenses out of `CLAUDE.md` into the rules store, recalled on feature-design situations; drop them from the corpus-inline always-load. Gated on S4's situational recall (destination must exist first). Owner-ruled: lenses = situational; S1a-now / S1b-with-S4 staging; floor the 43-line global file near-whole.
