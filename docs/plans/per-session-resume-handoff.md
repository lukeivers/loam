# Per-session resume handoff — episodic resume scoped by session, semantic memory stays workspace-global

**Status:** BUILD-READY — plan + manifest REBASED in place onto canonical HEAD
`30a3aaef` (was authored against `75adf102`; two commits shipped the read-side
reshape while this plan was blocked — see §2A). Core design D1–D5 re-verified
against the reshaped code and HOLDS unchanged; only the concrete read-surface
mechanics moved. Owner ask: multiple concurrent channel-sessions
(master-control / loam-dev / tilth-dev) must each resume THEIR OWN thread, not a
shared `pos3`-global mash. Single-owner build per §3 (collision gate).
**Component (sealed):** `framework/primary-persona` — advances the existing sidecar
(`new_component: false`; SEAL_COMMIT now `c17fb90c`, was `aefb3eb6`). Single-component amendment.
**Predecessors:** the SessionStart multi-contributor substrate (#45 registry + #46
emitter); the FBM file-memory substrate (M-FBM, `_default_memory_client_factory`
returns `None` → file store is the live path); the disk-backed memory-write queue
(amendment J) + worker (#48/J) + encoding-context capture (AC.FBMT1.ENCC.1); the
active-thread session-start contributor (AC.MSC.2); the consolidated keep-pace
turn contributor (AC-FBM-CON-1); **the recall volume-limits reshape (AC.RVL.1–9,
`ec9dd982`) + the write-side facts-discipline additions (AC.WFD.1–9, `6d0e20a5`)**
— both landed on the read/write surfaces this plan targets and are re-verified in
§2A. All live in the canonical tree at `30a3aaef`.
**Design source:** `workspace/.scratch/claude-output/per-session-resume-handoff-design.md`
(named decisions D1–D5, fence, draft AC ladder AC.PSR.1–7). This rebase adds
**AC.PSR.8** (byte-cap starvation, forced by the RVL volume caps).
**Build tree:** canonical `/Users/lukeivers/loam/`; seal in canonical, then sync to
`pos3/framework` (byte-identical mirror). **This build must be single-owner** (§3).

---

## §1 — Objective

Make episodic resume — "where were we" — private to the channel-session that
produced it, wherever it surfaces (session-start active-thread AND per-turn
keep-pace episodic snippets), while decision-ledger / ruling records stay
workspace-global shared knowledge; so a session in persona P resumes P's own
thread and none of the other concurrent personas', and a single-session workspace
resumes exactly as today.

---

## §2 — Findings pinned at plan-authoring (Tier-0, re-verified from the live code at `30a3aaef`)

Every claim read from the canonical tree. These ground the fence and correct one
file pointer in the design (finding 5, surfaced in §11 F2-1). Constants + line
numbers below are POST-reshape (see §2A for the rebase deltas).

1. **Session-start read leaks by workspace.** `active_thread.py:198` calls
   `store.recent_episodes(group_ids=[workspace_slug], limit=ACTIVE_THREAD_EPISODE_SCAN)`
   where `ACTIVE_THREAD_EPISODE_SCAN = 8` (`active_thread.py:82`); `workspace_slug`
   resolves to `pos3` for every concurrent session. Only caller of
   `recent_episodes` in the src tree (exhaustive grep). `recent_episodes`
   (`file_memory.py:1088`) walks group dirs, collects candidates PATH-ONLY, and
   caps the walk at `len(candidates) >= limit * 4` (`file_memory.py:1151` → 32
   files across ALL personas) BEFORE it reads any frontmatter (`file_memory.py:1156-1168`)
   — the recency-walk's own upstream volume cut (see §2A finding B, the starvation
   hazard on resume-after-idle).
2. **Per-turn read leaks by workspace on the LIVE path.** The live production
   per-turn episodic read is `keep_pace/retrieval.py::_episode_hits`
   (`retrieval.py:546`), scoped by `config.episode_group_ids`, which
   `_resolve_composer_config` sets to `(workspace_slug,)` (`retrieval.py:1734`),
   wired by `register_keep_pace_turn_contributor` (`retrieval.py:1754`). This —
   not `memory_consumer.py` — is the live surface (see F2-1). POST-RVL the branch
   fetches a NAMED generous window `EPISODE_CANDIDATE_WINDOW = 200` (`retrieval.py:124,838`),
   which `file_memory._fts_search` widens to `num_results * RECENCY_CANDIDATE_FACTOR`
   (floored `RECENCY_CANDIDATE_FLOOR`) = `max(200*8, 40) = 1600` BM25 candidates
   (`file_memory.py:791,792,1361`), then `_compose_score` cuts to 200, the merge
   runs, and the render applies the `INJECTION_CHAR_CAP = 5000` byte budget
   (`retrieval.py:181` — `= round(0.5 * ADDITIONAL_CONTEXT_CAP)`). THREE successive
   volume cuts, all downstream of `_fts_search`'s group filter (see §2A finding A).
3. **The write path already threads per-turn in-hook values into worker
   frontmatter.** `memory_write_queue.enqueue()` captures `session_id` + four
   encoding-context fields (`triggering_msg_id`, `active_task_id`, `cwd`,
   `active_files`) into the on-disk record AT ENQUEUE (`memory_write_queue.py:142`).
   The Stop-hook enqueue call site is `stop_emitter.py::_spawn_memory_write`
   (`stop_emitter.py:375`) — in-process with the Stop hook's env (where
   `CLAUDE_PERSONA` is live). The detached worker's `_build_episode_args`
   materializes the frontmatter `context:` block PURELY from `record.get(...)`
   (`memory_write_worker.py:159`) and reads NOTHING from its own env
   (grep-confirmed: no `os.environ` / `getenv` / `CLAUDE_PERSONA` in the worker).
   `FileMemoryStore.write_episode` emits the `context:` block (`file_memory.py:709`).
   So `session_key` rides the SAME enqueue→record→worker→frontmatter path
   `session_id` already rides.
4. **`group_id` stays `workspace_slug` everywhere.** Writes stamp
   `group_id=workspace_slug` (`memory_write_worker.py:171`); the FTS `episodes`
   table indexes `group_id` (`file_memory.py:1020`). The design deliberately does
   NOT fragment `group_id` into `pos3:<persona>` (many surfaces key on it — lower
   blast radius to add a `session_key` dimension inside the existing `context`
   frontmatter than to re-key the group).
5. **`CLAUDE_PERSONA` is read nowhere in the persona layer today** (grep-confirmed);
   the `handoffs/` surface does not exist yet — D4 is greenfield.
6. **Episodic and semantic are NOT entangled in one code path.** The per-turn merge
   composes three SEPARATE branches — episodes (`_episode_hits`), corpus rules
   (`corpus_index.search`), decisions (`open_decisions`). Session-scoping the
   episode branch alone leaves corpus + decisions workspace-global with zero shared
   code. The decision-ledger catch-up sweep (`decision_ledger.py`, registered
   `session_start_emitter.py:347`) reads episode FILES to detect rulings but emits
   workspace-global ruling records (D2 semantic) — it is the AC.PSR.4 positive
   guarantee, correctly out-of-fence. **The fence is cleanly drawable; the §3
   entanglement halt does not fire.**

**Net:** the write path needs one new field (`session_key`) captured at the Stop
hook and threaded through the existing enqueue→worker→frontmatter chain; the
live read surfaces (now THREE — see §2A) need a session-key filter applied DURING
candidate selection, upstream of every volume cut (not a post-filter over the
top-N / byte-cap — see F2-2); semantic surfaces are untouched.

---

## §2A — Rebase re-verification (`75adf102` → `30a3aaef`) — Tier-0, read from code

This plan was authored against `75adf102`. While it was blocked on the §3
single-owner collision gate, two commits shipped onto the READ + WRITE surfaces
it targets. Every claim below re-read from the live tree at `30a3aaef`.

**CONFIRMED UNCHANGED (byte-identical since `75adf102`; `git diff --stat` empty):**
`memory_write_queue.py`, `memory_write_worker.py`, `stop_emitter.py`,
`session_start_emitter.py`, `active_thread.py`, `memory_consumer.py`. So Finding
§2.3 (D3 — `session_key` captured at enqueue, materialized from the RECORD, worker
reads NOTHING from its own env), §2.1's contributor wiring, and the dormant-twin
scoping all hold verbatim. `session_key` / `CLAUDE_PERSONA` are read NOWHERE in
`file_memory.py` / worker / queue / stop_emitter (grep-confirmed) — the surface is
still greenfield.

**CHANGED (the rebase deltas):** only `keep_pace/retrieval.py` (+203/-41, the RVL
reshape `ec9dd982`) and `file_memory.py` (+248, the facts-discipline additions
`6d0e20a5`). The write-side facts-discipline commit added `volatility` +
`epistemic` frontmatter blocks to `write_episode` (`file_memory.py:952-985`) —
additive scalar fields alongside `salience`; `session_key` materializes as one
more such additive field (the D3 write target is intact, `_render_context_block`
now at `file_memory.py:1723`, `write_episode` at `:846`).

The reshape did NOT break the approach. It sharpened one interaction into THREE
concrete findings the builder must respect:

- **Finding A — per-turn FTS path: filter must beat the RVL candidate window AND
  the byte cap.** `_fts_search` builds its 1600-row BM25 pool from the FTS INDEX
  (`file_memory.py:1386-1414`), NOT from disk frontmatter — so `session_key`
  (a frontmatter field) is not on the pool rows unless it is ALSO carried in the
  index. The clean in-scan mechanism is to make `session_key` an FTS column
  (mirroring `group_id`/`reference_time`) and filter in the SQL `WHERE`
  (`file_memory.py:1365-1381`), so the filter engages before candidate_limit=1600
  → num_results=200 → INJECTION_CHAR_CAP=5000. The alternative (post-scan
  frontmatter filter) would need up to 1600 hot-path disk reads OR would filter
  after the 200-cut (starvation). This is a Fork B recommendation, NOT a mandate
  (§10) — a lazy frontmatter read in BM25 order until P's ~5000-char budget fills
  also bounds the reads. Either satisfies the AC as long as it engages upstream of
  all three cuts.
- **Finding B — session-start recency-walk: the `limit*4=32` collection cut
  starves resume-after-idle.** `recent_episodes` collects PATH-ONLY candidates and
  breaks at `len(candidates) >= limit * 4` (`file_memory.py:1151` → 32 files across
  ALL personas) BEFORE reading the frontmatter where `session_key` lives
  (`:1156-1168`). A frontmatter filter dropped into the read loop engages AFTER the
  32-file collection — so persona P starves exactly when P has been idle while other
  personas were chatty (P's tagged episodes fall outside the 32 newest all-persona
  files). This is the identical starvation class as the byte cap, on the PRIMARY
  resume scenario. The early-break CANNOT simply be deleted (a 600+-episode store
  would blow the 5s session-start envelope the `RECENCY_CANDIDATE_FLOOR` comment at
  `file_memory.py:780` protects). Method guidance (§6): a persona-aware bounded walk
  — keep reading frontmatter until `limit` P-episodes are found, up to a hard
  file-read ceiling.
- **Finding C — `_grep_search` is a THIRD live read surface during the FTS-rebuild
  window.** If `session_key` becomes an FTS column, the D-MSC.5 rebuild-on-mismatch
  (`file_memory.py:1272-1283`) DROPS + lazily rebuilds the index; until the next
  write the FTS table is empty and `search` falls to `_grep_search`
  (`file_memory.py:1072`). So during the entire post-deploy window the LIVE per-turn
  path is grep — and if grep does not filter `session_key` the leak persists exactly
  when it matters. Grep already reads every candidate's frontmatter
  (`file_memory.py:1503`), so this is the TRIVIAL in-scan surface: fence its
  `group_id` loop (`file_memory.py:1454`) to also match `session_key`. It is
  in-fence and must be named (below).

**Difficulty ranking (do not invert it):** `_grep_search` = easy (reads frontmatter
anyway) · `recent_episodes` = medium (the `limit*4` bounded-walk fix) · `_fts_search`
= hard (FTS-column-add-or-lazy-reads). All three are in-fence.

**Halt-trigger 4 evaluated → does NOT fire (recorded per Lens 6, not resolved
silently).** Adding `session_key` as an FTS column is NOT "a schema migration of the
on-disk episode store." Reasoning, checkable: (1) the on-disk store is the episode
MARKDOWN files, which receive a frontmatter field — the exact thing Halt-trigger 4
explicitly PERMITS ("rather than a frontmatter field + in-scan filter"); (2) the FTS
index is a DERIVED CACHE with an EXISTING drop-and-rebuild-on-schema-mismatch path
(D-MSC.5) that the `reference_time` column already rides; a column-add is that same
class of change, not an ALTER-migration of source data; (3) the trigger's PURPOSE —
preserve the D5 age-out / no-data-migration story — survives: absent-key-inclusive
matching means pre-amendment untagged episodes still surface through the rebuild.
Reasonable people could weigh this differently (it is a genuine Lens-6 call), so it
is recorded here as evaluated-and-cleared rather than assumed. If the builder finds a
mechanism that genuinely rewrites episode SOURCE files to add the key, THAT trips
Halt-trigger 4.

**AC ladder re-verified:** AC.PSR.1–7 map to real post-reshape surfaces; line/constant
refs updated throughout. AC.PSR.6 (write, outcome-altitude) target intact (write path
byte-unchanged). AC.PSR.7 (per-turn live path) target intact, refs re-pointed
(`retrieval.py:1734,1754`). **NEW: AC.PSR.8** added — the byte-cap starvation
falsifier the RVL volume caps introduced (distinct from AC.PSR.7's candidate-window
starvation).

---

## §3 — Halt-and-surface recorded at plan-authoring

- **Single-owner build gate (F2, from the design §"coordination").** Luke routed
  the "multiple concurrent sessions" ask to the loam-dev channel too. Two builders
  racing the canonical tree is the `feedback_serialize_amendment_builds` hazard
  (index.lock, half-applied `loam amend`). **Recorded as §8 Halt-trigger 1:**
  master-control owns this build per Luke's direct ask; loam-dev stays scoped to
  its own manual handoff. This is the one gate before dispatch.
- **The design's per-turn file pointer is the dormant twin, not the live surface
  (F2-1, §11).** Constraint 2 / the design fence names `memory_consumer.py`; the
  live per-turn episodic read is `keep_pace/retrieval.py`. Refinement, not a
  contradiction — the design's D3 already delegated live-vs-dormant tagging to the
  builder. Surfaced, plan re-pointed to the live surface, dormant twin scoped
  consistently.
- **Post-filter-after-top-N starves persona P (F2-2, §11).** Filtering by
  session_key AFTER taking the global top-N (by recency in `recent_episodes`, by
  BM25 in `_episode_hits`) silently under-returns P's window whenever
  other-persona episodes fill the N slots ahead of P's. AC.PSR.1 and AC.PSR.7
  fixtures are shaped to FAIL that method (interleaved stores where P's records are
  not all in the global top-N). The filter must engage DURING the scan/query.
- **Rebase resolution (RVL × session-scoping) — NO halt fired.** Re-verified the
  core against the reshaped code (§2A): D1–D5 hold, write path byte-unchanged, and
  the reshape does not fundamentally break the approach (the F2 halt condition on
  the dispatch). Three concrete findings recorded (§2A A/B/C): the filter must beat
  THREE volume cuts (FTS candidate window 1600, recency-walk `limit*4=32`, byte cap
  5000), and `_grep_search` is a third live surface during the FTS-rebuild window.
  Halt-trigger 4 (FTS-column-add) evaluated and cleared (§2A) — a Lens-6 call,
  recorded not silent. AC.PSR.8 added for the byte-cap falsifier.
- **Path correction (dispatch pointer stale).** The dispatch named
  `docs/rebuild/plans/`; that directory does not exist. Canonical is `docs/plans/`
  (the convention doc + every exemplar). This plan is at `docs/plans/`.

---

## §4 — Acceptance criteria

Outcome-shape; method inferable from the constraints, never stated. AC IDs
scope-descriptive (`PSR` = Per-Session Resume), not version-packed (per
`feedback_scope_descriptive_ac_ids`). One-test-per-criterion. AC.PSR.6 is the
outcome-altitude criterion (production write entry-point, no pre-arranged state).
The "Source" column traces each AC to its design decision (D1–D5).

| AC | Outcome | Verification | Source |
|---|---|---|---|
| **AC.PSR.1** — session-start resumes P's thread only | At session-start in persona P, with episodes from P AND from other personas in the store, the active-thread digest reconstructs P's thread and includes NONE of the other personas' episodes. | Drive the real `active-thread` contributor against a store whose episodes INTERLEAVE P and other personas so **P's tagged episodes fall OUTSIDE the 32 newest all-persona files** (`recent_episodes` collects `limit*4` path-only before reading frontmatter — §2A finding B); this fixture fails both a post-filter-after-`limit` method AND a naive frontmatter filter inside the read loop that runs after the `limit*4` collection cut. Assert every surfaced episode is P's and P's full window is present. `test_AC_PSR_1_*`. | D1, D2 |
| **AC.PSR.2** — handoff-file fallback resume | A persona P with no episodes yet but a `workspace/.loam/handoffs/P.md` present resumes from that named file at session-start. | Empty episode store + a `handoffs/P.md` fixture → the session-start payload surfaces P.md's content; a `handoffs/Q.md` for another persona is NOT surfaced in P's session. `test_AC_PSR_2_*`. | D4 |
| **AC.PSR.3** — single-session no-op + old untagged episodes age out | A workspace with no `CLAUDE_PERSONA` (single-session / non-channel) resumes exactly as today; pre-migration episodes that carry no `session_key` still surface (they are not hidden by the new filter). | With no persona resolvable, the fixture includes pre-migration UNTAGGED episodes and asserts they surface as before (workspace-global); output is byte-identical to the pre-amendment active-thread digest on that fixture. `test_AC_PSR_3_*`. | D1, D5 |
| **AC.PSR.4** — semantic retrieval stays workspace-global | A session in persona P still sees another workstream's decision/ruling record (decision-ledger + per-turn decision branch are not session-scoped). | In P's session, a ruling recorded under a different workstream surfaces in both the session-start decision-ledger catch-up AND the per-turn decision branch. `test_AC_PSR_4_*`. | D2 |
| **AC.PSR.5** — fail-soft on the reader's OWN identity-resolution error | If the reader cannot resolve ITS OWN session_key (env missing/garbled at read time), it degrades to today's workspace-global behavior — never an empty/blank resume. (Distinct from AC.PSR.3: that is an old episode with no key; this is the reader failing to resolve its own key.) | Force a session-key resolution failure at the read surface → the digest falls back to workspace-global (non-empty when episodes exist), no exception escapes the contributor sandbox. `test_AC_PSR_5_*`. | D1, D2 |
| **AC.PSR.6** (outcome-altitude) — real turn-close write stamps `session_key` from the RECORD, not the worker's env | A real turn-close write in persona P through the enqueue→worker path (not an injected store) yields an episode whose frontmatter carries `session_key=P` — even when the worker's OWN `CLAUDE_PERSONA` is unset or set to a DIFFERENT value. | Enqueue a record carrying `session_key=P`; drain the worker with its own `CLAUDE_PERSONA` unset (or set to `WRONG`); assert the written `.md` frontmatter carries `session_key=P`. This is the AC that catches a worker reading its own env instead of the record. `test_AC_PSR_6_OA_*`. | D3 |
| **AC.PSR.7** — per-turn keep-pace shows P's episodes only, rulings stay cross-workstream | The per-turn keep-pace block in persona P surfaces P's episodic snippets only, while still surfacing cross-workstream rulings (the D2 split, on the LIVE per-turn path `retrieval.py`). | Drive the live `register_keep_pace_turn_contributor` path against an INTERLEAVED store (P's episodes NOT all in the BM25 candidate window ahead of other-persona episodes — fails post-filter, F2-2): assert episodic snippets are all P's, and a cross-workstream ruling still surfaces in the same block. `test_AC_PSR_7_*`. | D2, D3 |
| **AC.PSR.8** — session filter engages upstream of the byte-budget cap (RVL interaction) | In persona P's per-turn keep-pace block, when the store holds other-persona episodes that BOTH out-rank P's by BM25 AND collectively exceed the `INJECTION_CHAR_CAP` byte budget, the rendered block still contains P's episodes (not a budget filled by other-persona episodes) — i.e. the filter engaged during candidate selection, ahead of the byte cap, not after render. | Drive the live per-turn path against a store where other-persona episodes are higher-BM25 than P's AND total > the fact-block byte budget; assert P's episodic snippets render and NO other-persona episode appears. A post-render (or any post-byte-cap) filter fails this: the budget fills with other-persona episodes and P's block returns empty. This is the falsifier the RVL volume caps introduced — distinct from AC.PSR.7's candidate-window starvation. `test_AC_PSR_8_*`. | D2, D3 |

**No-regression envelope:** the MSC / FBMU / FBM-FILTER / SRF / KP / DLG / J / M
suites stay green — AND the reshape's own suites **RVL (AC.RVL.1–9, volume caps /
candidate window / byte budget) + WFD (AC.WFD.1–9, write-side facts-discipline) +
RDP / RTEL / EVX** stay green, since this cycle threads a filter dimension through
exactly the `_fts_search` / `_compose_score` / byte-cap surfaces those suites pin.
Any suite whose fixture legitimately encodes the old workspace-only episode scoping
is updated in-cycle and named in §14; a suite that fails for any OTHER reason is a
real regression → §8 Halt-trigger 2.

**Ladder-up:** AC.PSR.* → the design outcome (each concurrent session resumes its
own thread; semantic knowledge stays shared) → AC.PO.1 / AC.PO.2
(`docs/VALUE_PROPOSITION.md`): per-user translation (a session resumes the RIGHT
person's context, not a mash) + protection-from-betrayal (the "no real memory /
lost context" failure mode — a session no longer resumes a stranger's thread).

---

## §5 — The fence

**In-fence, edited (episodic — write side, the capture→materialize chain):**
- `stop_emitter.py` — `_spawn_memory_write` (and its caller `handle_stop_envelope`):
  capture `session_key` from the Stop-hook env (the session-key resolver, §Primitive
  check) AT ENQUEUE (`CLAUDE_PERSONA` is live in-hook) and pass it to `enqueue`.
- `memory_write_queue.py` — `enqueue`: add an optional `session_key` param, store it
  on the on-disk record (mirrors `session_id` exactly).
- `memory_write_worker.py` — `_build_episode_args`: read `session_key` from the
  RECORD (never env) and thread it into the writer args (into `context` or a
  frontmatter field, builder's call), keeping `group_id=workspace_slug` untouched.
- `file_memory.py` — `write_episode` (`:846`) / `_render_context_block` (`:1723`):
  materialize `session_key` into episode frontmatter as an additive field (alongside
  `salience` / `volatility` / `epistemic`). ALL THREE read surfaces get an optional
  `session_key` filter applied DURING candidate selection, upstream of every volume
  cut (NOT a post-filter — F2-2), absent-key-inclusive (D5 age-out):
  - `recent_episodes` (`:1088`, session-start) — the filter must engage inside the
    candidate walk in a way that does NOT starve at the `limit*4=32` early-break
    (`:1151`); a persona-aware bounded walk, not a filter after the collection cut
    (§2A finding B). The `limit*4` line is the named hazard.
  - `_fts_search` (`:1328`, per-turn FTS) — the filter must engage ahead of the
    `candidate_limit` (1600) BM25 cut and the num_results (200) `_compose_score` cut;
    the pool rows come from the INDEX not disk (`:1386`), so an FTS `session_key`
    column filtered in the SQL `WHERE` (`:1365-1381`) is the recommended mechanism
    (Fork B). Its schema-bump rides the EXISTING D-MSC.5 rebuild-on-mismatch
    (`:1272-1283`) — extend `_index_schema_is_current` (`:1288`) + `_index_episode`
    (`:1306`) to carry `session_key`; a pre-amendment index drops+rebuilds lazily.
  - `_grep_search` (`:1430`, the FTS-rebuild-window fallback) — fence its `group_id`
    loop (`:1454`) to ALSO match `session_key`; it reads frontmatter already
    (`:1503`), so this is trivial. Load-bearing during the post-deploy rebuild window
    (§2A finding C) — MUST be filtered or the leak persists exactly when it matters.

**In-fence, edited (episodic — read side, session-scoping):**
- `active_thread.py` — `build_active_thread_contributor`: resolve THIS session's
  session_key and pass it to the `recent_episodes` filter; fall back to
  workspace-global on resolution failure (AC.PSR.5); also read the
  `handoffs/<persona>.md` fallback surface (D4 / AC.PSR.2).
- `keep_pace/retrieval.py` — `_episode_hits` (`:546`) + `_resolve_composer_config`
  (`:1671`, sets `episode_group_ids` at `:1734`) + `register_keep_pace_turn_contributor`
  (`:1754`): thread the session_key into the episode branch's `store.search` call
  (the episode branch ONLY; corpus + decision branches stay workspace-global —
  AC.PSR.4, AC.PSR.7). The episode fetch is `num_results=EPISODE_CANDIDATE_WINDOW`
  (`:838`); the render byte cap is `INJECTION_CHAR_CAP` (`:181`) — the filter must be
  upstream of both (AC.PSR.8).
- `session_start_emitter.py` — `build_session_composer`: resolve the session_key
  once and thread it into BOTH contributor builders (active-thread + keep-pace turn).
- `memory_consumer.py` — the DORMANT MCP twin (`register_memory_retrieval` read +
  `PerTurnEpisodeWriter.add_episode` write): scope it session-consistently too, so
  re-enabling the MCP client path later cannot reintroduce the leak. Not the live
  verification surface (AC.PSR.7 targets `retrieval.py`); tagged for consistency.

**New in-fence module:**
- `handoffs.py` (name builder's call) — the `workspace/.loam/handoffs/<persona>.md`
  surface: write at turn-close (SECONDARY, human-readable), read at session-start
  filtered to THIS persona. Plus a shared **session-key resolver**
  (`CLAUDE_PERSONA` → `DISCORD_STATE_DIR` basename → `workspace_slug`), placement
  builder's call.
- `framework/primary-persona/tests/test_AC_PSR_*` — the AC suite.

**Explicitly OUT of fence (semantic — stays workspace-global):**
- `decision_ledger.py` + the session-start decision-ledger catch-up sweep (reads
  episode files, emits workspace-global rulings — AC.PSR.4).
- `keep_pace/corpus_index.py` (corpus feedback-rules — timeless, shared).
- the decision branch of the per-turn merge (`open_decisions` in `retrieval.py`).
- any `group_id` schema change (group_id stays `workspace_slug` — finding §2.4).
- any session-END hook (the design adds NONE — turn-close write only; a SessionEnd
  hook would violate the owner constraint AND be unnecessary, per the active-thread
  module's own §12 halt trigger 1).

**Blast radius:** the two read surfaces are on the live per-session-start and
per-turn paths; the change narrows what a session surfaces (adds a filter dimension)
under the existing fail-open contracts. The write change adds one field to an
existing record + frontmatter block — no new I/O, no new hook, no group_id re-key.

**Reversibility:** episodes written pre-amendment carry no `session_key` and age
out of the recency window (D5); git-revert the seal is the whole-cycle rollback; no
data migration (no content-parsing backfill — D5).

---

## §6 — Build steps (method-level; builder's call per ODD §1.1)

1. Author `test_AC_PSR_*` first (plan-before-code; TDD-guard). Shape AC.PSR.1 to
   place P's tagged episodes OUTSIDE the 32 newest all-persona files (beats the
   `limit*4` collection cut — §2A finding B); AC.PSR.7 to interleave personas so P's
   episodes are not all in the BM25 candidate window (F2-2); AC.PSR.8 to make
   other-persona episodes both higher-BM25 AND collectively exceed the byte budget
   (beats a post-byte-cap filter); AC.PSR.6 to run the worker with a wrong/absent
   own-env.
2. Add the shared session-key resolver (`CLAUDE_PERSONA` → `DISCORD_STATE_DIR`
   basename → `workspace_slug`).
3. Write side: `session_key` param on `enqueue`; capture at `_spawn_memory_write`;
   materialize from the RECORD in `_build_episode_args` → `write_episode` frontmatter.
4. Read side: optional `session_key` filter on ALL THREE surfaces —
   `recent_episodes` (persona-aware bounded walk, no `limit*4` starvation),
   `_fts_search` (in-scan ahead of the 1600/200 cuts; recommended FTS column via the
   D-MSC.5 rebuild), and `_grep_search` (fence its group loop) — all absent-key-
   inclusive. Thread the resolved session_key through `active_thread.py`,
   `keep_pace/retrieval.py` (episode branch only), and `session_start_emitter.py`;
   scope the dormant `memory_consumer.py` twin consistently. Confirm the filter is
   upstream of `INJECTION_CHAR_CAP` (AC.PSR.8).
5. Add the `handoffs/<persona>.md` write (turn-close) + read (session-start,
   persona-filtered) surface.
6. Run the AC suite + no-regression suites; update only fixtures that legitimately
   encoded workspace-only episode scoping (name them in §14).
7. `loam amend apply` then `loam amend seal` against the manifest (never
   `git commit --amend`; new corrective commits if a file is missed). Sync canonical
   → `pos3/framework` after seal.

---

## §7 — Out of scope (deferred)

- **Content-parsing backfill of old untagged episodes** — explicitly rejected (D5,
  brittle); old episodes age out of the recency window.
- **`group_id` fragmentation into `pos3:<persona>`** — rejected (finding §2.4);
  `session_key` inside `context` frontmatter is the lower-blast-radius dimension.
- **A SessionEnd/Stop-driven handoff-correctness path** — the handoff file is
  SECONDARY (D4); episodes are the crash-robust primary. No new end-hook.
- **Re-enabling the MCP memory client** — stays dormant; the twin is scoped only so
  a future re-enable does not reintroduce the leak.
- **Cross-persona thread MERGE / hand-off between sessions** — each session resumes
  its own thread; deliberate cross-session sharing is a later ask, not this cycle.

---

## §8 — Halt triggers (abort the in-flight build)

1. **A second builder (loam-dev or other) is building this in the canonical tree** →
   halt (single-owner gate; serialize-amendment-builds hazard).
2. A no-regression suite fails for a reason that is NOT the deliberate workspace-only
   → session-scoped fixture update → halt + surface (real regression).
3. **Episodic and semantic turn out to share a code path** such that session-scoping
   episodes also scopes rulings (contradicts finding §2.6) → halt + surface (the D2
   split would be un-drawable; the plan assumed the branches are separable).
4. Implementing the read filter requires a schema migration of the on-disk episode
   SOURCE store — i.e. rewriting existing episode markdown files to add the key
   (rather than a frontmatter field on new writes + the derived-cache rebuild) →
   halt + surface (the design assumed no data migration; a source migration changes
   the blast radius + D5 age-out story). NOTE (§2A): adding `session_key` as an fts5
   INDEX column does NOT trip this — the FTS index is a derived cache rebuilt by the
   existing D-MSC.5 mechanism, and only NEW writes gain the frontmatter field; this
   was evaluated and cleared at plan-authoring (Lens 6).
5. The session-key resolver cannot produce a restart-stable key on a real channel
   session (e.g. `CLAUDE_PERSONA` absent where it was assumed present) → halt +
   surface (D1's anchor assumption is the load-bearing premise).
6. Any surrounding ODD violation surfaces (unnamed code, method-in-AC drift) → halt
   + surface per `feedback_subagent_odd_violation_halt`.

---

## §9 — Bookkeeping (backfilled at seal)

- `docs/STATE.md` — note per-session resume shipped (episodic session-scoped;
  semantic workspace-global).
- `docs/plans/v0-1-x-roadmap.md` §8 — if a memory/session ledger line applies, add
  this cycle.
- Parent design dir — no edit (research artefact is immutable); this plan cites it.
- §14 below — method-decision register + SHA backfill by `loam amend seal --plan-doc`.

---

## §10 — Named decisions (design D1–D5, each ratified with a recommendation) + build forks

Design decisions D1–D5 are carried from the ratified design; each already carries
the design's recommendation, restated here so the builder acts without re-reading.

- **D1 — session key = `CLAUDE_PERSONA`** (fallback `DISCORD_STATE_DIR` basename →
  `workspace_slug`). **Recommendation: adopt.** Restart-stable, explicit, already in
  every hook env; `CLAUDE_CODE_SESSION_ID` is unusable (fresh per process — breaks
  the very resume being fixed).
- **D2 — episodic scopes by session; semantic stays workspace-global.**
  **Recommendation: adopt (load-bearing).** Filter episodes (active-thread + per-turn
  episode branch); leave decision-ledger + corpus + decision branch global. AC.PSR.4
  is the guarantee.
- **D3 — capture `session_key` at ENQUEUE, materialize from the RECORD.**
  **Recommendation: adopt.** Rides the existing `session_id` path; the worker must
  never read its own env (AC.PSR.6 catches it).
- **D4 — named `handoffs/<persona>.md` surface, SECONDARY.** **Recommendation:
  adopt as convenience, not correctness.** Turn-close write can go stale on a
  refusal/crash (the 2026-06-10 no-Stop-hook failure mode); crash-robust filtered
  episodes are PRIMARY (AC.PSR.1/.7 vs AC.PSR.2).
- **D5 — back-compat by age-out, no backfill.** **Recommendation: adopt.** Old
  untagged episodes surface until the 8-episode window rolls; a brief cross-session
  tail on the first post-deploy session-start is acceptable + self-correcting
  (AC.PSR.3).

**Build forks (builder's call, recommendation given):**

- **Fork A — where `session_key` lives in frontmatter.** Inside the existing 4-field
  `context:` block vs a new top-level frontmatter key. **Recommendation: builder's
  call** — either satisfies AC.PSR.6 as long as the read-side filter reads the same
  place. Prefer the lowest-churn option consistent with the `context`-block schema
  discipline (TG 11805 was "schema-minimal"; a 5th context field or a sibling key
  are both defensible).
- **Fork B — read-side filter mechanism (per surface, post-RVL).** **Recommendation:
  builder's call, ONE hard constraint** — the filter engages DURING candidate
  selection, upstream of EVERY volume cut, so persona P's full window is returned; a
  post-filter over the global top-N / candidate window / byte cap is FORBIDDEN
  (starves P — F2-2; AC.PSR.1/.7/.8 fail it). The reshape splits the recommendation
  by surface (§2A): (a) `recent_episodes` — a persona-aware bounded walk (read
  frontmatter until `limit` P-episodes found, hard read ceiling), NOT a filter after
  the `limit*4` collection; (b) `_fts_search` — an fts5 `session_key` column filtered
  in the SQL `WHERE`, recommended over a lazy-frontmatter-read-over-the-1600-pool
  because the pool rows come from the index not disk (both remain valid — the AC is
  outcome-shape, satisfiable by either); (c) `_grep_search` — a frontmatter fence on
  the group loop (trivial; it reads frontmatter already). The FTS column-add rides
  the EXISTING D-MSC.5 derived-cache rebuild and does NOT trip §8 Halt-trigger 4
  (evaluated in §2A — a Lens-6 call recorded, not silent); only a mechanism that
  rewrites episode SOURCE files to add the key would.

---

## §11 — F2 Ruthless Feedback (honest doubts / risks — named, not smoothed)

1. **The design's per-turn file pointer is imprecise — named, not followed blindly.**
   Constraint 2 / the design fence name `memory_consumer.py` as the per-turn episodic
   surface. Evidence: `memory_consumer.py`'s `register_memory_retrieval` is the MCP
   read path, dormant in production (`_default_memory_client_factory` returns `None`,
   `session_start_emitter.py:168`); the LIVE per-turn episodic read is
   `keep_pace/retrieval.py::_episode_hits` scoped by `episode_group_ids` at
   `retrieval.py:1734`. Alternative rejected: "scope memory_consumer.py and call it
   done" — it would no-op on the live path while an injected-MCP test still passed.
   This does NOT contradict the 5 design constraints — constraint 2's SUBSTANCE
   (per-turn episodic must be session-scoped) holds, and D3 already delegated
   live-vs-dormant tagging to the builder. Plan re-points to `retrieval.py` as the
   live surface + verification target; `memory_consumer.py` scoped consistently as
   the dormant twin.
2. **The obvious filter method is subtly wrong (starvation).** Take the global top-N
   THEN filter by session_key and persona P's window is silently starved whenever
   other-persona episodes occupy the N slots ahead of P's — P under-returns even with
   plenty of its own episodes, invisibly. Evidence: `recent_episodes` returns
   recency-ordered top-N; `_episode_hits` returns BM25 top-N; both cut before any
   session filter would run if applied naively. Alternative (adopted): filter DURING
   the scan/query; AC.PSR.1 + AC.PSR.7 fixtures interleave personas so a post-filter
   method fails the test. This is the plan's core enforcement value-add over the
   draft AC ladder.
3. **The handoff file's staleness window is real.** D4's turn-close write goes stale
   on a refusal/crash (documented 2026-06-10). Mitigated by making episodes primary
   (AC.PSR.1/.7) and the handoff file a same-persona convenience fallback only
   (AC.PSR.2) — but a user who trusts a stale `handoffs/P.md` over the live episodes
   would be misled. Worth stating so the surface is never promoted to primary.
4. **D1's anchor is only as stable as `CLAUDE_PERSONA`'s presence.** If a real
   channel session ever launches without `CLAUDE_PERSONA` exported, it silently falls
   to `workspace_slug` and re-shares the pos3 mash for that session — the exact bug,
   re-appearing. Not a defect in this plan (the fallback is correct fail-soft), but
   §8 Halt-trigger 5 makes the builder confirm the anchor is actually present on a
   live channel session before sealing, rather than assuming it.
5. **The recency-walk starvation is the subtlest of the three cuts — and it hits the
   PRIMARY scenario.** `recent_episodes` caps its candidate collection at
   `limit*4=32` all-persona files (`file_memory.py:1151`) BEFORE reading the
   frontmatter that carries `session_key`. Evidence: the walk appends path-only
   tuples (`:1146-1147`), breaks at `:1151`, and only reads `_split_frontmatter` in a
   SECOND loop (`:1156-1168`). A frontmatter filter naively dropped into that second
   loop under-returns persona P exactly on resume-after-idle (P quiet while others
   were chatty → P's tagged episodes are not among the 32 newest). This is more
   dangerous than the byte cap because it is INVISIBLE (P just resumes thin, no
   error) and it is the MAIN use case. Alternative (adopted, §6 step 4): a
   persona-aware bounded walk with a hard read ceiling; AC.PSR.1's fixture places P's
   episodes outside the 32-window so a naive filter fails the test. This doubt was
   surfaced by the advisor pass after the first-cut plan waved `recent_episodes`
   through as "clean" — recorded so the builder does not rediscover it against the
   fixture.
6. **The byte-cap interaction (AC.PSR.8) is the RVL-specific falsifier.** Post-RVL,
   `INJECTION_CHAR_CAP=5000` is a HARD best-first drop-whole ceiling
   (`retrieval.py:181,1059`). A handful of large, higher-BM25 other-persona episodes
   can exhaust it before any P episode renders if the filter runs post-cap — P's
   block silently empties even with plenty of P's own episodes indexed. This is
   distinct from the top-N/candidate-window starvation AC.PSR.7 catches; AC.PSR.8's
   fixture forces it (other-persona episodes higher-BM25 AND collectively >5000
   chars).

---

## §12 — Provenance trail

- Ratified design (root cause + D1–D5 + fence + draft ACs):
  `workspace/.scratch/claude-output/per-session-resume-handoff-design.md`.
- Live code (canonical `30a3aaef`, re-verified this rebase): `active_thread.py:82,198`
  (session-start read, `ACTIVE_THREAD_EPISODE_SCAN=8`);
  `keep_pace/retrieval.py:124,181,546,838,1671,1734,1754` (per-turn live read +
  `EPISODE_CANDIDATE_WINDOW` + `INJECTION_CHAR_CAP` + config wiring);
  `memory_consumer.py` (dormant MCP twin, byte-unchanged); `memory_write_queue.py:142`
  (enqueue capture, byte-unchanged); `stop_emitter.py:375` (Stop-hook enqueue call
  site, byte-unchanged); `memory_write_worker.py:159,171` (materialize-from-record,
  byte-unchanged); `file_memory.py:791,846,1088,1151,1272,1306,1328,1361,1430,1454,1503,1723`
  (write frontmatter + three read surfaces + FTS schema-rebuild + candidate widening);
  `session_start_emitter.py` (contributor wiring, byte-unchanged).
- Rebase-delta commits: `ec9dd982` (RVL volume-limits reshape, AC.RVL.1–9 —
  reshaped `retrieval.py`); `6d0e20a5` (write-side facts-discipline, AC.WFD.1–9 —
  +248 to `file_memory.py`). Baseline retargeted `75adf102` → `30a3aaef`.
- Substrate predecessors: SessionStart registry #45 + emitter #46; memory-write queue
  amendment J; #48/J worker; AC.MSC.2 active-thread; AC-FBM-CON-1 keep-pace turn.

---

## §Primitive check (REQUIRED — this plan introduces new mechanisms)

Per the plan-doc convention leg of the prefer-the-primitive doctrine (Lens 1).

| New mechanism | Primitive considered | Chosen |
|---|---|---|
| Session identity anchor | Claude Code hook env vars — `CLAUDE_PERSONA` is exported into every hook process (channel-session bound, restart-stable) | **Native env var (`CLAUDE_PERSONA`)** — no bespoke session-registry; the platform already carries a restart-stable per-session identity. |
| Per-session episode capture | The SEALED enqueue→worker→frontmatter path (amendment J / #48 / AC.FBMT1.ENCC.1) already threads in-hook per-turn values into worker frontmatter | **Compose on the existing write path** — add one field; no new queue, hook, or worker. |
| Session-scoped read | The SEALED #45 SessionStart contributor registry + the live keep-pace turn contributor | **Compose on existing contributors** — thread a filter dimension; no new hook machinery. |
| FTS `session_key` index column | The EXISTING D-MSC.5 rebuild-on-schema-mismatch path (`file_memory.py:1272-1283`) that `reference_time` already rides | **Compose on the existing derived-cache rebuild** — a column-add drops+lazily-rebuilds the FTS index (grep covers the window); no ALTER-migration, no bespoke migration path, no source-file rewrite. |
| Human-readable handoff surface | Bespoke `<persona>.md` file (no Claude primitive maps to a per-persona turn-close scratch surface) | **bespoke — a small file surface**, deliberately SECONDARY to the crash-robust episodes; formalizes the manual handoff loam-dev already writes by hand. |

No new hook event, scheduler, or orchestrator is introduced.

---

## §14 — Method-decision register (populated at build; SHA-backfilled at seal)

**Design decision rulings (carried from the ratified design — recommendations in §10):**
- D1 (session key = CLAUDE_PERSONA + fallbacks) — _pending build confirmation_.
- D2 (episodic session-scoped / semantic global) — _pending build confirmation_.
- D3 (capture at enqueue / materialize from record) — _pending build confirmation_.
- D4 (handoff file secondary) — _pending build confirmation_.
- D5 (age-out, no backfill) — _pending build confirmation_.

**Build forks:**
- D-ForkA (session_key frontmatter placement — additive scalar alongside
  salience/volatility/epistemic recommended) — _pending_.
- D-ForkB (read-side filter mechanism; in-scan-upstream-of-every-cut mandatory;
  per-surface recommendation in §10 — recency-walk bounded, FTS column via D-MSC.5
  rebuild, grep frontmatter fence) — _pending_.

**Rebase judgment recorded (Lens 6):** Halt-trigger 4 evaluated against the
FTS-column-add mechanism → does NOT fire (derived-cache rebuild ≠ source-store
migration; new writes gain a frontmatter field; D5 age-out purpose intact). §2A.

**Builder method decisions:** _populated at build._

**Verification:** _AC.PSR.1–8 results (AC.PSR.8 = the RVL byte-cap falsifier) +
RVL/WFD/RDP/RTEL/EVX no-regression state populated at build._

- **SOURCE SHA:** _backfill._
- **APPLY SHA:** _backfill._
- **SEAL SHA:** _backfill._
- **Branch:** _backfill (behavior-changer on read/write paths — owner-gated public
  push; seal LOCAL first, sync canonical → pos3)._

---

## §15 — Backwards-compat verification

- Single-session / non-channel workspaces (no `CLAUDE_PERSONA`) resume byte-identical
  to today (AC.PSR.3) — the primary back-compat contract.
- Pre-migration untagged episodes surface until they age out of the recency window
  (D5 / AC.PSR.3); no episode is hidden by the new filter merely for lacking a key.
- `group_id=workspace_slug` unchanged everywhere (finding §2.4) — every surface that
  keys on group_id is unaffected.
- The MSC / FBMU / FBM-FILTER / SRF / KP / DLG / J / M suites stay green except for
  fixtures that legitimately encoded workspace-only episode scoping (named in §14);
  any other failure is a real regression (§8 Halt-trigger 2).
