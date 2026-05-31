# FBM episode SALIENCE gate slice plan (B3 — the recall-quality safety-pair)

**Status:** slice plan-doc (plan-before-code per the v-next build workflow)
**Working dir:** `/Users/lukeivers/loam` (canonical loam)
**Branch:** `slice/p1.2-loam-layout` (current build branch; carries
rank-normalize `7e9af6b` + rule-weighting `81c7780`)
**Date:** 2026-05-31
**Workflow:** `docs/plans/loam-vnext-build-workflow.md` (per-slice loop)
**Predecessor slices:**
- FBM rank-normalize (`fbm-rank-normalize-slice-plan.md`) — made rules +
  episodes compete fairly on RELEVANCE.
- FBM rule-weighting + hard-floor (B1, `fbm-rule-weighting-slice-plan.md`,
  `81c7780`) — added the per-hit WEIGHT knob to `_merge_by_score`
  (`boosted = norm * (weight / BASELINE_WEIGHT)`). **B3 is the episode-side
  consumer of that same knob.**

---

## Objective
Junk turns — agent task-notification turns, empty/near-empty channel-header
events, and bare acks — currently get logged as episodes and rank HIGH on
shared boilerplate tokens (`task-id`, `tool-use-id`, `status`, `completed`,
`channel`, `message_id`), polluting recall with confident noise. B3 adds an
**episode SALIENCE gate**: at ingest, each turn is tagged a salience score;
at recall, below-threshold-salience episodes do not surface. Salience is the
episode's side of the SAME weight knob B1 added to the merge — a near-zero
salience cannot compete; a meaningful episode keeps its normalized relevance.

**HARD INVARIANT (load-bearing): NEVER not-store, NEVER delete.** Every turn
is still STORED on disk verbatim. Salience gates SURFACING only, and the
threshold is RE-TUNABLE — a mis-judged junk turn stays on disk and is
re-admittable by lowering the threshold. No not-store path, no delete path.

## EXAMINE — verified against the LIVE store (empirical, read-only)

**Live episode store:** `/Users/lukeivers/pos3/workspace/.loam/memory/episodes`
(1288 episodes). Classified read-only via `/tmp/classify_episodes.py` (never
wrote the live store). Episode body shape (from `memory_write_worker.
_build_episode_args`): `[user]\n<msg>\n\n[assistant]\n<reply>\n`.

**The structural junk classes (exact signatures, with live counts):**

| Class | Structural signature (on the `[user]` half of the body) | Live count |
|---|---|---|
| **task-notification** | user-half (lstripped) starts with `<task-notification>` | **494** |
| **channel-empty** | user-half is a `<channel …>` wrapper whose inner text (tags stripped) is `< 8` chars | **38** |
| **empty-user** | user-half is empty / `< 8` chars and NOT a channel/task wrapper | **17** |
| **bare-ack** | user-half inner text (channel-tag-stripped) is a pure ack token (`ok`, `yes`, `no`, `thanks`, `got it`, …) | **12** |

**NOT junk — must be PROTECTED (the load-bearing EXAMINE finding):**

| Class | Why it is NOT junk | Live count |
|---|---|---|
| **channel-with-real-text** | a real Luke Telegram message wrapped in a `<channel>` tag — substantive content inside the wrapper | **687** |
| **other** | non-channel, non-task substantive user text | **52** |

The trap this avoids: a real Luke message is wrapped in a `<channel …>` header
exactly like an empty channel event. The signature must therefore look at the
RESIDUAL inner text after stripping the wrapper — NOT the mere presence of a
`<channel>` or `<task-notification>` tag. A `<channel>`-wrapped message with
real text inside is fully salient.

**Where episodes are WRITTEN (the ingest path):**
Stop-hook `memory_write_queue.enqueue` → queue JSON → `memory_write_worker.
_build_episode_args` (composes the `[user]/[assistant]` body) → `client.
add_episode` → `FileMemoryStore.write_episode` (renders frontmatter + body to
`<memory_dir>/episodes/<group_id>/<date>/<turn_id>.md`). **`write_episode` is
the single ingest choke-point where every episode's frontmatter is authored —
salience is computed and stored there.**

**Schema / migration verdict — a REAL (non-no-op) but NON-DESTRUCTIVE
migration.** Unlike B1 (optional corpus frontmatter, no-op), B3 adds a
`salience: <float>` line to the frontmatter of EVERY newly-written episode.
That is a real user-state schema addition to the episode store. BUT:
- `_split_frontmatter` already parses arbitrary flat `key: value` lines, so it
  reads `salience:` with no parser change (forward-compatible).
- Pre-existing episodes (1288 of them) lack the field. They must default to
  **full salience** (`SALIENCE_FULL = 1.0`) — fail toward SURFACING, never
  toward dropping. **No rewrite of existing episodes is performed** (the
  HARD-INVARIANT never-touch-stored-state rule + protection floor). The
  migration is forward-additive: the field appears on new episodes; old
  episodes ride at full salience until naturally aged out. This is declared in
  the migration file as a real schema-add, non-destructive, non-rewriting.

**How the merge consumes episode scores today (post-B1):** `_episode_hits`
builds hit dicts `{pointer, score, _episode: True}`. `_merge_by_score` then
applies `boosted = _minmax_norm(score) * (_weight_of(hit) / BASELINE_WEIGHT)`.
**Salience plugs in cleanly as a multiplicative factor on the episode hit's
boosted score** — the episode-side analogue of B1's rule weight. A near-zero
salience drives `boosted → 0`, so the junk episode loses to any real hit. The
gate then DROPS any merged hit whose salience is below `SALIENCE_THRESHOLD`
(the force-DROP, the episode mirror of B1's pinned force-INCLUDE) so a junk
episode cannot surface even on a query with no competition.

EXAMINE disposition: **extend** (two sealed framework functions —
`FileMemoryStore.write_episode`/`search` on the file-memory side, and
`_episode_hits`/`_merge_by_score` on the retrieval side).

## The salience scoring (method — chosen + justified)

A cheap, deterministic, stdlib-only STRUCTURAL scorer
(`compute_salience(user_text, assistant_text) -> float`) on the hot ingest
path. Proportionality: structural junk is the bulk (561 of 1288 ≈ 44% are
junk-class) and is mechanically recognizable; an LLM micro-judge for
borderline trivial-but-real turns is a FUTURE layer, explicitly NOT built now.

`SALIENCE_FULL = 1.0`, `SALIENCE_JUNK = 0.0`. The scorer returns
`SALIENCE_JUNK` for a turn whose USER half matches a junk signature, else
`SALIENCE_FULL`:

1. **task-notification** — user-half lstripped starts with `<task-notification>`.
2. **channel/scaffolding-empty** — strip `<channel …>` / `<system-reminder>`
   wrapper tags from the user-half; if the residual inner text is `< 8` chars
   → junk.
3. **empty-user** — user-half (whole) is `< 8` chars and not otherwise real.
4. **bare-ack** — residual inner text, lowercased and punctuation-stripped, is
   in a small `_ACK_TOKENS` frozenset (`ok`, `okay`, `k`, `yes`, `no`, `yep`,
   `yeah`, `thanks`, `thank you`, `ty`, `got it`, `nice`, `cool`, `great`,
   `perfect`, `sounds good`, `done`).

The scorer keys on the USER half only — the assistant half being substantive
does NOT rescue a turn whose user-half is pure plumbing (a task-notification
turn's tokens that pollute recall are the boilerplate `task-id`/`status`/
`tool-use-id` tokens, which live in the user half). **Fail-safe (the hot
path): `compute_salience` is wrapped so any exception returns `SALIENCE_FULL`
— a scorer error fails toward storing-at-full-salience + surfacing, never
toward dropping** (the never-drop floor).

### Threshold (named, tunable constant)
`SALIENCE_THRESHOLD = 0.5` (a NAMED module constant in `retrieval.py`). A hit
whose salience is `< SALIENCE_THRESHOLD` is force-DROPPED from the merged set.
`SALIENCE_FULL (1.0) >= 0.5` surfaces; `SALIENCE_JUNK (0.0) < 0.5` is gated.
RE-TUNABLE: lowering the threshold (e.g. to `0.0`) re-admits every previously
gated junk episode — proving the gate is reversible, nothing lost.

### Storage of salience on the episode
`write_episode` gains a `salience: <float>` frontmatter line (rendered after
`group_id`, before the `context:` block). `_fts_search` / `_grep_search`
read it back via `_split_frontmatter` (already flat-key-capable) and thread it
onto each episode dict as `"_salience": <float>` (default `SALIENCE_FULL` when
the key is absent — the old-episode fail-toward-surface default). `_episode_
hits` copies `_salience` onto the retrieval hit; `_merge_by_score` applies it
as the multiplicative factor + the below-threshold force-drop.

## DEFINE — outcome-altitude acceptance criteria

- **AC-FBM-SAL-1 — JUNK-FILTERED (load-bearing, outcome-altitude).** A
  scaffolding episode (a `<task-notification>` turn) is tagged near-zero
  salience at ingest and does NOT surface in `retrieve()` even when it shares
  tokens with the query (the live-store pollution complaint reproduced +
  killed). Proven through the production write→search→merge path.
- **AC-FBM-SAL-2 — NO-REGRESSION (outcome-altitude).** A substantive episode
  (full salience) still surfaces normally in `retrieve()`; the rank-normalize
  + rule-weighting + FBMU suites stay green; the empty-episode early-return in
  `_merge_by_score` stays byte-identical.
- **AC-FBM-SAL-3 — NEVER-DELETE (load-bearing, outcome-altitude).** After
  ingest, the junk episode is still STORED on disk and retrievable by DIRECT
  lookup (read the file / `recent_episodes`), proving salience gates SURFACING
  only, not storage. The episode file exists with its full body verbatim.
- **AC-FBM-SAL-4 — RE-TUNABLE (load-bearing, outcome-altitude).** Lowering
  `SALIENCE_THRESHOLD` (passed through the merge) re-admits the previously
  filtered junk episode into the `retrieve()` surface — proving the gate is
  reversible and nothing was lost.
- **AC-FBM-SAL-5 — LIVE-STORE COLD-WALK (outcome-altitude, the bar).** Against
  a COPY of the REAL episode store shape (real `<task-notification>` +
  `<channel>`-wrapped-real-text episodes copied into a TEMP root; never the
  live `workspace/.loam` store), through the production `retrieve()`
  entry-point with no pre-arranged state: the task-notification junk is
  suppressed AND a real channel-wrapped Luke message on the same query DOES
  surface (the protect-real-messages property proven, not just junk-drop).

## Edit list (surgical)
1. `framework/primary-persona/src/loam/primary_persona/file_memory.py`
   — (a) add `compute_salience(user_text, assistant_text) -> float` +
   `SALIENCE_FULL`/`SALIENCE_JUNK`/`_ACK_TOKENS`/`_SALIENCE_MIN_CHARS` +
   the wrapper-strip helper (fail-safe envelope → `SALIENCE_FULL`);
   (b) `write_episode` computes salience from the `[user]`/`[assistant]`
   body halves and renders a `salience: <float>` frontmatter line;
   (c) `_fts_search` / `_grep_search` read `salience` from the parsed
   frontmatter and put `"_salience"` on each episode dict (default
   `SALIENCE_FULL`). The body-split for the scorer reuses the same `[user]`/
   `[assistant]` markers the worker writes.
2. `framework/primary-persona/src/loam/primary_persona/keep_pace/retrieval.py`
   — (a) add `SALIENCE_THRESHOLD = 0.5` + `_salience_of(hit)` (fail-soft to
   `SALIENCE_FULL`); (b) `_episode_hits` copies `_salience` onto the hit;
   (c) `_merge_by_score` (and `retrieve`, threading an optional
   `salience_threshold` param defaulting to the constant) multiplies each
   hit's boosted score by its salience AND force-DROPS any hit whose salience
   `< salience_threshold`, BEFORE the top-N cut. The empty-episode early-return
   stays byte-identical (no salience logic runs on that path — corpus hits
   ride at `SALIENCE_FULL` and are never gated, since only episodes carry a
   sub-full salience).
3. `framework/primary-persona/tests/test_AC_FBM_SAL_*` — the five ACs above.
   The cold-walk + never-delete + re-tunable tests write to a TEMP root.
4. `docs/state-migrations/fbm-episode-salience-slice.migration.yaml` — the
   declared migration. **REAL schema-add (a new `salience` field on
   newly-written episodes), NON-DESTRUCTIVE / NON-REWRITING** (existing
   episodes keep no field and default to full salience; nothing on disk is
   rewritten, removed, or compressed). `reversible: true` (git; old episodes
   never gained the field, new ones drop it harmlessly on revert via the
   absent-key default).
5. `docs/plans/build-cursor.md` — advance the cursor.
6. `framework/primary-persona/tests/test_no_sealed_amendments.py` BASELINE
   (→ `81c7780…`, the rule-weighting tip = current sealed HEAD~ pattern) +
   `tests/SEAL_COMMIT` — advanced per the amend/seal discipline at INTEGRATE.

## Fail-safe (every-turn live hook — ingest AND recall both run every turn)
- **Ingest (`write_episode`):** `compute_salience` is wrapped — any exception
  → `SALIENCE_FULL`. A scorer crash never blocks the write and never drops an
  episode's salience below the surface threshold. The write itself is
  unchanged (atomic tmp+rename); the only addition is one frontmatter line.
- **Recall (`_merge_by_score`):** salience read is fail-soft (`_salience_of`
  → `SALIENCE_FULL` on any malformed value); the empty-episode early-return is
  byte-identical; the multiply + drop are pure arithmetic on already-fetched
  hits (no new I/O). A corpus-only turn never reaches salience logic.
- **The never-drop floor:** every default and every error path resolves to
  `SALIENCE_FULL` (surface), so the gate can only SUPPRESS a turn it
  affirmatively recognized as structural junk — never a turn it failed to
  score.

## ODD §2.5 — every line maps to a named AC (no non-objective code)
- `compute_salience` + the four junk signatures + `salience:` frontmatter
  render → AC-FBM-SAL-1 (junk tagged near-zero) and AC-FBM-SAL-2 (real turn →
  full salience, no-regression).
- `_salience` read-back in `_fts_search`/`_grep_search` + `_episode_hits` copy
  → carries salience to the merge (AC-FBM-SAL-1 / -4 / -5).
- salience multiply + below-threshold force-drop in `_merge_by_score` →
  AC-FBM-SAL-1 (junk does not surface) + AC-FBM-SAL-4 (threshold lowers →
  re-admits).
- the file-still-on-disk assertion path uses the UNCHANGED write/read surface
  → AC-FBM-SAL-3 (never-delete: storage untouched).
- fail-soft defaults to `SALIENCE_FULL` → the named never-drop floor (part of
  AC-FBM-SAL-2's no-regression + the HARD INVARIANT), not defensive code for
  an unnamed case.
- live cold-walk harness (temp copy of the real store shape) → AC-FBM-SAL-5.

## Halt triggers honoured
- Sealed-component edit (two functions across file_memory + retrieval) →
  amend/seal discipline (advance BASELINE + `SEAL_COMMIT`, run touched + FBMU +
  rank-normalize + rule-weighting + seal-fence tests). No content-filter, no
  Cairn, no `~/.claude/settings.json`, no touch of the live episode store
  (cold-walk copies the real store SHAPE into a temp root).
- No `claude -p` spawn needed (in-process production entry points). Had one
  been needed it would use `--strict-mcp-config` + empty mcpServers.
- Schema fork: the salience field IS a real schema-add — declared NON-
  DESTRUCTIVE / NON-REWRITING in the migration; no existing episode rewritten,
  so the never-delete invariant + protection floor hold. Not a halt (the
  design decided storage = frontmatter on the episode; this is the natural
  home and it is additive).
- HALT-and-surface if: the never-delete or re-tunable invariant cannot be
  proven, or a real Luke message is found to be mis-gated as junk by the
  structural signatures (the protect-real-messages property is load-bearing).

---

## Follow-up fix — spread-path × salience-gate leak (AC-FBM-SAL-6)

**Bug (confirmed Tier-0, line-level; caught by the live-store activation
smoke, missed by the 813-test suite).** The one-hop co-citation SPREAD step
in `file_memory._compose_score_and_spread` materialises spread-in neighbor
episodes as `n_row` dicts carrying `_spread_from: True` + `_bm25_raw` but
**no `_salience` key**. The B3 salience gate tags `_salience` on the FTS5 +
grep candidate pools (`_salience_from_body(body)` at the two pool-build
sites) but NOT on these spread-activated neighbors. A junk episode (e.g. a
`<task-notification>` turn) reachable ONLY via co-citation spread therefore
arrived at the gate with no `_salience`, `_salience_of` returned the
full-salience default, and it BYPASSED the gate — leaking ~1 junk pointer
per query into the rendered recall block.

**Fix (minimal, surgical, mirrors existing code).** Tag
`"_salience": _salience_from_body(body)` on the spread-neighbor `n_row`
dict, reusing the SAME `_salience_from_body` helper B3 already uses for the
FTS/grep candidate rows (no second scorer). The gate now sees spread
neighbors on identical footing to direct BM25 hits.

**New test — the missing coverage (SAL family × COCG family intersection).**
`tests/test_AC_FBM_SAL_6_spread_neighbor_junk_gated.py`: a junk
`<task-notification>` episode reachable ONLY via co-citation spread (NOT a
direct BM25 match) must be salience-gated out of the production `retrieve()`
block (outcome-altitude — real access-log-driven spread, real `retrieve()`
entry-point, no pre-arranged retrieval state). A precondition guard proves
the neighbor IS spread-reachable (so the gate test isn't a no-op) and that
the spread row now carries `_salience == 0.0`. The test FAILS on old code
(spread row's `_salience` is `None`) / PASSES on fixed code.

**Verification.** New test 2/2 PASS on fixed code, precondition guard FAILS
on old code (proving the gap). Full primary-persona suite: 815 passed / 1
skipped (813 prior + 2 new). Seal-fence + SAL/COCG families green.
Code-only (no stored-field change — `_salience` is an in-memory result-row
slot, not new frontmatter); the slice migration is a forward no-op.
