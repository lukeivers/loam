# FBM-LIVE slice plan (loam v-next Phase-1, slice P1.1)

**Status:** slice plan-doc (plan-before-code per the v-next build workflow)
**Working dir:** `/Users/lukeivers/loam` (canonical loam)
**Date:** 2026-05-31
**Workflow:** `docs/plans/loam-vnext-build-workflow.md` (per-slice loop)
**Master plan / ACs:** `docs/plans/loam-vnext-build-plan.md` §6 (AC-FBM-LIVE-1..4)
**Roadmap:** `docs/design/fbm-state-and-memory-roadmap-2026-05-29.md`
**Predecessor seal:** amendment #154 (FBM Cycle 1 — write-path fix + unify),
seal `4b258218`, amendment commit `505b32eb`, BASELINE `14e972e`.

---

## Objective
Make loam's already-built FBM episode store actually run behind the
framework↔user-state boundary, unified with the keep-pace corpus
retrieval into ONE retrieval surface, so a fact stated in one session is
retrieved in a cold fresh session — and PROVE it with a real two-session
cold-walk. This is COMPOSE-ON-EXISTING (sealed FBM Tiers 0-2 + keep-pace
+ the sealed #154 write-path-fix + unify), NOT build-from-scratch.

## Acceptance bar (restated from master plan §6 — outcome-altitude)
- **AC-FBM-LIVE-1** — cross-session continuity: a fact written in real
  session A is retrieved+surfaced in a cold session B whose prompt is
  relevant. The production hooks do the write and the read; no pre-seeded
  index.
- **AC-FBM-LIVE-2** — unified retrieval surface: one retrieval call at
  turn time sees BOTH the FBM episode store AND the keep-pace corpus index
  (rules + OBJECTIVES.md).
- **AC-FBM-LIVE-3** — fail-open, no regression: with the store dir
  absent/unreadable a real session runs end-to-end with zero error,
  behaviour identical to baseline.
- **AC-FBM-LIVE-4** — boundary respected: episodes reside on the
  user-state side (`<workspace>/.loam/memory/...`); no framework-code path
  writes user-state elsewhere.

## EXAMINED disposition: **LEAVE** (already live — verified empirically)

Step-1 EXAMINE established, from git refs + live runtime + a probe (NOT
stale docs), that the slice's three deliverables already shipped and the
owner-gated activation was already executed:

1. **D1 write-path fix — DONE in the live runtime.** The live pos3 runtime
   imports `primary_persona` from
   `/Users/lukeivers/pos3/framework/framework/primary-persona/`; that
   tree's `_resolve_workspace` is the FIXED version (honours
   `LOAM_WORKSPACE_ROOT`, else strips a trailing `workspace` segment).
   Empirical probe (cwd `pos3/workspace`, no env): resolves repo root
   `/Users/lukeivers/pos3`, `queue_dir` →
   `/Users/lukeivers/pos3/workspace/.pos/memory-write-queue` (single
   `workspace`), `memory_dir` → `/Users/lukeivers/pos3/workspace/.loam/memory`.
   The doubled-nesting dead shadow `pos3/workspace/workspace/.pos/...` is
   **gone** (migrated + removed). NB: §13 of the #154 plan PREDICTED the
   pos3 tree still held the OLD buggy resolver; the live runtime now has
   the fix — i.e. the propagate step §13(a) was executed since the seal.

2. **D2 unify — LIVE.** The sealed merge-at-retrieval (`retrieval.py`
   `episode_memory_dir` + `_episode_hits` + `_merge_by_score`) is present
   in canonical loam, which is exactly what the global `~/.claude/`
   keep-pace UPS hook imports (`/Users/lukeivers/loam/.venv/bin/python
   .../keep_pace/user_prompt_submit.py`). The contributor resolves the
   live episode dir when it exists.

3. **D3 activation — DONE (owner already flipped).** Live evidence:
   1281 episodes in the store; `search-index.sqlite` (7MB) + `.access-log.jsonl`
   updated **today**; **67 episodes written since 2026-05-30**, newest
   11:03 today; a `.scratch/fbm-activation-backup-2026-05-29-fbm-activation/`
   snapshot exists (the backup-first activation per §13). The writer hooks
   (`cli stop` / `session-start` / `user-prompt-submit`) are wired live in
   `pos3/.claude/settings.json` on `pos3/.venv` and ARE firing.

Disposition is therefore **LEAVE** (workflow Step-1 outcome `leave`):
the slice already does its job. The workflow REQUIRES this be PROVEN by an
empirical cold-walk before recording done — "it's wired" is not proof.

## Edit list
This is a `leave` disposition → **no production-code edits.** Work is:
1. PROVE via a real two-session cold-walk (AC-FBM-LIVE-1 + AC-FBM-LIVE-2),
   plus a fail-open probe (AC-FBM-LIVE-3) and a boundary check (AC-FBM-LIVE-4).
2. Author the version's user-state migration file under `.loam/migrations/`
   (no-op is a valid declared migration — this slice changes no user-state
   schema; the episode store + queue already exist on disk).
3. Establish + update the position cursor at `.loam/build-cursor.md`.
4. Commit the slice plan + migration + cursor in canonical loam.

## Boundary respected
Episodes persist to the user-state home `<workspace>/.loam/memory/...`
(empirically confirmed); framework code stays in the framework tree. No
framework-code path writes user-state elsewhere. This slice writes only
docs + `.loam/` bookkeeping in canonical loam, nothing in `framework/`.

## Owner-gated
The single owner-gated action (G3, the `~/.claude/settings.json`/runtime
activation flip) was ALREADY executed by the owner on 2026-05-29 (backup
snapshot + live episode flow are the evidence). This slice does NOT touch
`~/.claude/settings.json` activation. If the cold-walk had shown the flip
was still pending, the slice would HALT-and-surface it; it does not.

## Halt triggers honoured
- Sealed-component edits: none made (disposition is `leave`).
- Cairn repo: not touched.
- The cold-walk used direct in-process production entry points
  (`enqueue`/`drain_once`/`retrieve`) against an ephemeral `/tmp` repo
  root — no `claude -p` spawn was needed, so no bot-slot-steal risk arose;
  had one been needed it would have used `--strict-mcp-config` + empty
  mcpServers.

## PROVE result (Step-4, 2026-05-31) — 3/4 PASS, AC-2 gap HALTED
Evidence file: `.scratch/claude-output/fbm-cold-walk/COLD-WALK-RESULTS.md`
(gitignored user-state-side; scripts alongside it).

| AC | Result | Note |
|---|---|---|
| AC-FBM-LIVE-1 cross-session continuity | **PASS** | fact written in process A surfaced in a fresh process B via production `retrieve()` (codeword ZEPHYR-NIGHTINGALE-7741, matching no corpus doc). |
| AC-FBM-LIVE-2 unified surface | **PARTIAL — gap surfaced + HALTED** | seam wired + sealed test GREEN, but against the LIVE corpus a single call does NOT co-surface an episode: `_merge_by_score` ranks by raw score and the two indexes are on incompatible scales (corpus BM25 30–285 vs episode bm25 ~0–1 at `file_memory.py:779`), so episodes truncate out of top_n. Reproduced 3×. A sealed-component scoring change to the every-turn live hook at low fix-shape confidence → Lens-6 HALT, owner/next-cycle decision (reserve-slot / rank-normalize / per-source quota). |
| AC-FBM-LIVE-3 fail-open / no-regression | **PASS** | absent + None episode store → zero error, corpus-side byte-identical. |
| AC-FBM-LIVE-4 boundary respected | **PASS** | episodes only under `<root>/workspace/.loam/memory/episodes/`; zero `framework/` writes during the cold-walk. |

**Disposition confirmed `leave` for the live wiring** (continuity, fail-open,
boundary all proven against the production path). The AC-2 unify-effectiveness
gap is the one open item — surfaced, not silently edited; recommended scope is
FBM Cycle-2 (the roadmap's R2 "guaranteed-surface" already lands there).
