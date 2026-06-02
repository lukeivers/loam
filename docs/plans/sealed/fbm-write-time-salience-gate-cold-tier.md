# FBM write-time salience gate — junk diverted to a cold tier at ingest (Slice A)

**Author:** build agent · **Date:** 2026-06-02 · **Owner:** Luke (greenlit 13512)
**Parent plan:** `workspace/.scratch/claude-output/loam-fbm-quality-and-accuracy-unified-plan.md` (Slice A, P2).
**Mode:** plan-before-code; single-component amendment on the EXISTING `framework/primary-persona/` component.

---

## Objective

A turn whose user half matches a structural junk signature does **NOT** enter the hot
episode index at write time — it is diverted to a **cold tier** (written there, never
indexed, never deleted). A substantive turn is written to the hot index at full
salience exactly as today.

This moves the already-sealed `compute_salience` gate onto the WRITE path. Today the
gate has zero write-path callers: junk is written to the hot `episodes/` dir AND
FTS-indexed, then suppressed only at read via the `salience` frontmatter field. That is
the structural waste the owner is owed a fix for after two reactive read-side patches —
44.1% of the live store (600 of 1361 episodes) is gated-junk that the system writes,
indexes, and re-filters forever.

## The structural bug (Tier-0, verified this session)

- `compute_salience` / `_salience_from_body` have ZERO write-path callers.
  `grep -rn "compute_salience\|_salience_from_body" framework/` resolves only to:
  tests, and `file_memory.py` itself where the value is computed-then-stored-as-frontmatter
  (lines 552, 960, 1077, 1626) for the READ-side gate. The write path
  (`FileMemoryStore.write_episode`, line 466) computes salience at line 552 but writes
  the episode to `EPISODES_SUBDIR` and FTS-indexes it **unconditionally**.
- The ingest funnel is single and clean:
  queue entry → `memory_write_worker.drain_once` → `_process_one_entry`
  → `FileBackedMemoryClient.add_episode` → `FileMemoryStore.write_episode`.
  `write_episode` is the one place every production episode is written.

## Cold-tier mechanism (the never-drop invariant)

The hot retrieval paths — `search` (FTS5 + grep) and `recent_episodes` — both scan
`self.memory_dir / EPISODES_SUBDIR` exclusively (verified: lines 618, 674).
A new sibling subdir `COLD_SUBDIR = "cold"` (mirroring the existing
`ARCHIVED_SUBDIR = "archived"` pattern at line 100) is therefore invisible to BOTH
hot paths automatically — no search-path or recency-path edit is required to exclude it.

At ingest, `write_episode` computes salience (as today). When the salience is
`SALIENCE_JUNK`, the episode markdown file is written under
`<memory_dir>/cold/<group_id>/<YYYY-MM-DD>/<stem>.md` (identical layout to the hot
tier) and is **NOT** FTS-indexed. The file body, frontmatter, and `salience` field are
identical to what the hot tier would have stored — nothing is dropped, compressed, or
deleted. A substantive turn (`SALIENCE_FULL`) writes to `EPISODES_SUBDIR` and FTS-indexes
exactly as today (byte-identical behaviour for non-junk).

The return shape (`{"path", "name", "group_id"}`) is preserved; `path` points at the
cold-tier file for a gated turn, so the worker's diagnostic log and the
`FileBackedMemoryClient` access-log replay still see a real on-disk path
(never-drop is observable downstream).

Fail-open is preserved end-to-end: `compute_salience` / `_salience_from_body` already
return `SALIENCE_FULL` on ANY exception (lines 245, 272), so a classifier error routes
the turn to the HOT tier (stored + surfaced) — the gate can only divert a turn it
affirmatively recognized as junk. No new error path is introduced.

## Constraints (hard)

- REUSE `compute_salience` / `_salience_from_body` verbatim as the classifier. Do NOT
  author a sixth signature. The five proven signatures (task-notification,
  channel/scaffolding-empty, empty-user, bare-ack, compaction-summary dump) are the
  exact ones the read gate runs today; their live precision is verified (the 600 they
  drop are boilerplate; no new false positives).
- stdlib-only; no API key; no LLM (`feedback_no_anthropic_api_key`).
- Never-drop HARD INVARIANT: a gated turn is WRITTEN to the cold tier, never deleted.
- Fail-open: any classifier error → hot tier at full salience (the existing fail-safe).
- ODD §2.5: every line maps to a named AC below; no non-objective code, no defensive
  `if` without an AC anchor.

## ACs

- **AC-FBM-WGATE-1** — a `<task-notification>`-opening turn written through the
  production `write_episode` path is NOT written under `EPISODES_SUBDIR` and is NOT in
  the FTS index; a search for its boilerplate tokens returns it with zero hot-store
  weight (it is absent from the surfaced set entirely). It IS written under
  `COLD_SUBDIR`.
- **AC-FBM-WGATE-2** — a substantive Luke turn (real instruction, >8 chars, no junk
  signature) IS written under `EPISODES_SUBDIR` AND FTS-indexed at full salience —
  byte-identical to pre-amendment behaviour; the cold tier stays empty for it. Write-gate
  precision matches read-gate precision (no new false positives vs. the sealed gate).
- **AC-FBM-WGATE-3** — a gated turn is recoverable from the cold tier: the file exists
  on disk under `COLD_SUBDIR/<group_id>/<date>/<stem>.md` with its full body verbatim
  and its `salience: 0.0` frontmatter; the never-drop invariant holds.
- **AC-FBM-WGATE-4 (outcome-altitude)** — drive the REAL production ingest path
  (`memory_write_worker.drain_once` against a disk-backed queue with no pre-arranged
  store state) with one boilerplate queue entry + one substantive queue entry. Assert
  post-drain that the hot tier (`EPISODES_SUBDIR` + FTS `search`) contains exactly the
  substantive turn and the cold tier (`COLD_SUBDIR`) contains exactly the boilerplate
  turn. Exercised through `drain_once → add_episode → write_episode`, no internal
  call shortcut.

## Non-regression

- AC-FBM-SAL-1..9 stay green. The five read-side signatures, the surfaced-set salience
  multiply/drop, the spread-neighbor gating, the re-tunable threshold, and the
  never-delete floor are unchanged. (The read-side gate stays in place as defence in
  depth for pre-amendment episodes already in the hot tier and for any future
  classification drift; the write gate stops new junk from entering.)
- `recent_episodes` and `search` are NOT edited — the cold subdir is excluded by
  construction (they scan `EPISODES_SUBDIR` only).
- `archive_before` is NOT edited — it operates on `EPISODES_SUBDIR` and is orthogonal.

## Out of scope (named)

- Purging the existing 600 hot-tier junk episodes to the cold tier — owner-gated,
  deferred to after Slice B (the unified load-time filter) per the parent plan §7.
- The load-time systematic filter (Slice B), dedup, the absolute BM25 floor.
- Any change to the read-side salience gate's signatures or threshold.

## Method-decision register

- **D-WGATE.1** — cold tier is a new top-level sibling subdir `cold/` (NOT a reuse of
  `archived/`). Rationale: `archived/` has age-based semantics (`archive_before`) and is
  consumed by `/memory:archive`; the salience cold tier is junk-classification-based and
  must not be conflated with operator age-archival. Distinct subdir keeps both
  invariants clean.
- **D-WGATE.2** — the read-side gate is RETAINED (not removed). Rationale: defence in
  depth for the ~600 pre-amendment junk episodes still in the hot tier until the
  owner-gated purge; removing it would un-gate them at read. The write gate is additive.
