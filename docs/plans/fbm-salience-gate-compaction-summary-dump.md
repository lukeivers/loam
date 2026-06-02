# FBM salience-gate — drop compaction-summary context-dump episodes

**Amendment slug:** `fbm-salience-gate-compaction-summary-dump`
**Component:** `framework/primary-persona/` (existing sealed component; follow-on)
**Class:** small, single-component amendment. Method is the builder's call;
this plan pins objective + ODD ACs only.

---

## §1 — Problem (Tier-0, diagnosed)

The keep-pace / file-memory episode-retrieval path is dominated every turn by
compaction-summary context dumps — turns whose user half begins
`This session is being continued from a previous conversation that ran out of
context`. Diagnosis source-of-scope:
`/Users/lukeivers/pos3/workspace/.scratch/claude-output/loam-fbm-relevance-assessment-and-garry-tan.md`
(§1.3 smoking gun: 19 such episodes on the live store; each passes
`compute_salience` at full salience because it matches none of the four
existing junk signatures, contains every objective keyword, and is long +
recent → BM25-dominates almost every work-anchored query → surfaces as the
top "On-file context relevant to what you're working on" hit).

Tier-0 confirmation against the live code: `compute_salience` in
`framework/primary-persona/src/loam/primary_persona/file_memory.py` (lines
~164-216) recognizes exactly four junk shapes (task-notification,
channel/scaffolding-empty, empty-user, bare-ack). A compaction-summary dump is
none of them → returns `SALIENCE_FULL` → surfaces.

## §2 — Objective (ODD)

> Extend the episode salience gate so a compaction-summary context-dump turn
> is recognized as structural plumbing and tagged junk salience at ingest +
> search time, so it stops surfacing as a top retrieval hit — while a genuine
> Luke turn that merely mentions a continuation is NOT mis-classified.

The fix is a 5th junk signature inside the existing, tested
`compute_salience` gate — the same mechanism, same `SALIENCE_JUNK` return,
same never-drop floor (the episode stays on disk; only its retrieval salience
drops). No new classifier, no LLM, stdlib-only (honours
`feedback_no_anthropic_api_key`). If the signature turns out to need anything
heavier than a deterministic prefix/marker match, HALT and surface (Ruthless
Feedback) rather than forcing a classifier into a "small" cycle.

## §3 — Acceptance criteria (every line of code maps to one of these)

- **AC-FBM-SAL-7 — compaction-summary dump tagged junk.** `compute_salience`
  returns `SALIENCE_JUNK` for a user half that is (begins with / is dominated
  by) the compaction-summary continuation marker
  (`This session is being continued from a previous conversation`). The marker
  match is the load-bearing signature; the existing four signatures are
  untouched.
- **AC-FBM-SAL-8 — no false positive on a real continuation mention.** A
  genuine substantive Luke turn that merely *mentions* a previous conversation
  / continuation in prose (without BEING the auto-generated summary dump)
  stays `SALIENCE_FULL`. The signature keys on the dump's structural opening,
  not on incidental token overlap — the protect-real-messages property
  (sibling of AC-FBM-SAL-5).
- **★ AC-FBM-SAL-9 — outcome-altitude (`outcome-altitude: true`).** A real
  `retrieve()` call through the production write→search→merge path, no
  pre-arranged retrieval state: ingest a real compaction-summary dump episode
  that shares the work-anchor query tokens via the production
  `FileMemoryStore.write_episode` path, plus a genuinely-relevant real
  episode; assert the dump does NOT appear in the top retrieval hits and the
  relevant episode does. Mirrors the AC-FBM-SAL-1 outcome-altitude pattern
  (`test_AC_FBM_SAL_1_junk_episode_filtered.py`).

## §4 — Non-regression (already-green tests stay green)

AC-FBM-SAL-1..6 must stay green: the four existing signatures unchanged, a
substantive turn still surfaces (AC-FBM-SAL-2), the never-delete floor holds
(AC-FBM-SAL-3 — the dump is still on disk), the threshold stays re-tunable
(AC-FBM-SAL-4), the live cold-walk (AC-FBM-SAL-5) and spread-neighbor gating
(AC-FBM-SAL-6) hold.

## §5 — Cycle mechanics

Single-component amendment on the EXISTING `framework/primary-persona/`
component. `loam amend apply <manifest>` → touched tests green →
`loam amend seal`. LOCAL seal only — no push. New corrective commit; never
`--amend`. Manifest declares the one component + universal `docs/plans/`
admission. Sidecar `framework/primary-persona/tests/SEAL_COMMIT` advances.

## §6 — Halt-surface check

No ODD violation found in surrounding code. The fix composes on the existing
gate's never-drop invariant + fail-safe-to-FULL exception path; it adds one
deterministic signature, no defensive code for unnamed cases.
