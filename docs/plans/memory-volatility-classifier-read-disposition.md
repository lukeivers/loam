# memory-volatility-classifier-read-disposition (MINOR) — plan

**Slug:** `memory-volatility-classifier-read-disposition`
**Component fence (single):** `primary-persona`
**Baseline (HEAD~1 pattern, confirmed at apply):** `a7c9f1b2` (branch tip
at dispatch; my source commit sits directly on it).
**Working directory:** `/Users/lukeivers/loam` (CANONICAL).
**Derived from:** `pos3/workspace/strategy/research/memory-system-issues-2026-06-28/memory-system-research.md`
(read fully; §4 recommendation, owner-ratified "go with your recommendations").

---

## §1 Objective

Give loam's file-backed memory a **volatility dimension** so a recent,
stale *operational-status* claim ("the shim is broken", "service is
down", "HEAD is at <sha>", "3 PRs pending") is NOT served back as
current in a later session, while the **durable decision** behind it
survives recall. This guards a named Lens-0 AI-betrayal: *no real
memory / confidently-wrong recall*. It does NOT promise the model never
states a stale fact — it removes the recall path that *promotes* one.

Two halves, composed on the **already-sealed bitemporal interval
machinery** (`_supersession_interval` / `_filter_by_interval` /
`_interval_contains` in `file_memory.py`, AC.SUP.*) — NOT a parallel
freshness store:

1. **Write-side classifier** — deterministic, stdlib-only; classifies a
   captured fact `durable` / `volatile-hard` / `volatile-soft` on the
   named tells. `volatile-hard` is born with a **closed interval**
   (`volatile_until = reference_time + window`); `durable` + `soft` are
   born **open**.
2. **Read-side disposition** — `volatile-hard` is **hard-excluded** from
   the default current view by the existing interval filter (the durable
   decision behind it is a *separate* record and survives; live status is
   re-derived by the session, not recalled). `volatile-soft` survives but
   its surfaced pointer is **annotated** `VOLATILE — re-verify before
   serving`.

## §2 Scope-tightness (F4)

High confidence in the outcome shape (the research VERIFIED the
current-state map from code; the interval machinery is sealed + present).
Scope is **tight**: objective + constraints + ACs pin the outcome;
method (regex tells, frontmatter keys, insertion points) stays the
builder's call. One named decision was the owner's tuning fork
(hard-exclude vs annotate) — ratified, recorded §4.

## §3 Halt-and-surface triggers (pre/in-flight)

- WD ≠ `/Users/lukeivers/loam` → halt.
- Interval machinery can't be reused cleanly for the volatility close → halt.
- Hard-exclude would remove the durable decision (not a separate record) → halt.
- **A read-side change would be INERT in canonical** (live-vs-dormant split) → halt+surface. **FIRED — see §F2.**
- Fence touches a sealed component with no manifest entry → halt.
- An AC can only ship partial → halt.

## §F2 Ruthless-Feedback finding — research §4 item #4 is INERT in canonical (DROPPED, not built)

**Disagreement.** The research's 4th recommendation — "volatile-classified
episodes must be exempted from the 5-day recency blend
(`RECENCY_BLEND_WEIGHT`)" — cannot be built as a *live* change in
canonical. It targets a code path that is **dead in canonical**.

**Evidence (verified live, this build).**
- The research measured the **pos3 OLD tree**, whose live ranking applies
  the recency blend (`file_memory.py:417,434`, research §1).
- In **canonical** the live episode-search scoring path is
  `_compose_score` (`file_memory.py:1688`), called by `_fts_search`
  (1028) and `_grep_search` (1135). It composes **BM25 × activation(off)
  × supersession penalty** — there is **no recency term**.
- `_blend_recency` (1593) and `_recency_weight` (1392) — the only carriers
  of `RECENCY_BLEND_WEIGHT` — have **zero callers** and **zero tests** in
  canonical (`grep -rn '_blend_recency(\|_recency_weight('` returns only
  the in-`_blend_recency` self-reference). They are leftover from before
  the June-7 eval **floor arm** (AC.EVX.1) replaced the blended ranker
  (the floor arm beat the blended ranker ~2× on recall@10/MRR).

**Why building it anyway is wrong, two ways.** (a) Editing
`_blend_recency` is dead-code theater — inert on the live path
(information-trust: no false work). (b) *Re-introducing* a live recency
blend so the exemption would bite would **regress a sealed eval verdict**
(AC.EVX.1 deliberately removed it) and is far out of fence.

**Alternative (what actually delivers the research's intent).** In
canonical the recency adversity **does not exist on the live path**, so
the protection the research wanted from item #4 is already structurally
true: `volatile-hard` is *filtered out* (can't be promoted at all);
`volatile-soft` is ranked by `_compose_score` with no recency boost. The
remaining live effect is delivered by **Step 0 (canonical→pos3 sync,
owner-gated, NOT this build)** — once pos3 runs `_compose_score`, the
recency-promotion path is gone there too.

**Disposition.** Item #4 is **DROPPED from the AC ladder** (no
`AC.VOL.recency`). The other three research items are LIVE in canonical
and are built. The hard-exclude read-side change (the *primary* read
edit) was CONFIRMED live: `keep_pace/retrieval.py:_episode_hits` →
`FileMemoryStore.search(as_of=None)` → `_compose_score` →
`_filter_by_interval`. Not inert.

## §4 Named decisions (ratified)

- **D1 — hard-exclude vs annotate boundary (owner fork).** Ruling:
  hard-exclude the unambiguous operational classes (is-broken / up-down /
  current-version / latest-SHA / pending-count / who's-allowed), annotate
  the borderline (`right now` / `as of today` / `at the moment` without a
  hard tell). Source: research §3 fork + owner "go with your
  recommendations". Mechanism: hard → closed interval (filtered); soft →
  open + annotation.
- **D2 — durable-bias on ambiguity (safe failure direction).** When a
  hard tell fires BUT a durable-decision signal is also present
  (`decided` / `ruling` / `we will` / `going forward` / `the rule is` …),
  classify `volatile-soft`, never `volatile-hard`. A false-negative
  (volatile kept visible) is status-quo-today; a false-positive (durable
  decision hard-excluded) is the dangerous outcome — D2 structurally
  prevents it. Also: hard-exclude removes the *volatile-status* episode,
  never the durable-decision record (a distinct episode / ledger entry),
  so the durable decision is never lost.
- **D3 — compose, don't fork.** The volatility close reuses the interval
  reader: `_supersession_interval` is extended to also read a
  `volatile_until` frontmatter close (in addition to `superseded-date`),
  taking the earliest non-None close. No parallel freshness store; no
  change to `_interval_current` / `_filter_by_interval` semantics (closed
  is closed; as_of-in-window still reaches it — filtering ≠ deletion).
- **D4 — single classifier source.** `classify_volatility(text)` lives in
  `file_memory.py` (stdlib `re`); the read-side annotation path imports it
  (no duplicate logic). Computed fresh from the body on read, so episodes
  written before this build classify correctly with no rewrite.

## §5 Acceptance criteria (outcome-shape; method inferable, not stated)

- **AC.VOL.1 — write-side classifier.** `classify_volatility(text)` is
  deterministic + stdlib-only and returns `durable` / `volatile-hard` /
  `volatile-soft`: each named hard tell (is-broken, up-down,
  current-version, latest-SHA, pending-count, who's-allowed) → `hard`
  absent a durable signal; a borderline soft tell → `soft`; a durable
  ruling → `durable`; an ambiguous hard-tell-with-durable-signal → `soft`
  (D2). Same input → same output across calls.
- **AC.VOL.2 — write-side interval birth.** A `volatile-hard` episode
  written via `write_episode` carries a `volatile_until` close
  (= `reference_time` + window) and a `volatility` class field in
  frontmatter; a `durable` episode carries no close (born open). Verified
  by reading the written file's interval through `_supersession_interval`
  (hard → closed; durable → open).
- **AC.VOL.3 — read-side hard-exclude, history preserved.** Reusing
  `_filter_by_interval`: under the default current view (`as_of=None`) a
  `volatile-hard` record is absent from results; under an `as_of` query
  with `as_of` inside `[valid_from, volatile_until)` the same record is
  returned (filtering ≠ deletion; AC.SUP.2 property holds for the
  volatility close too).
- **AC.VOL.4 — read-side soft annotation.** A `volatile-soft` episode
  surfaced through the keep_pace pointer path carries the prefix
  `[VOLATILE — re-verify before serving]`; a `durable` episode's pointer
  does not.
- **AC.VOL.5 — OUTCOME-ALTITUDE, end-to-end, no pre-arranged state.**
  Through the REAL write + retrieval entry-points (`write_episode` then
  `FileMemoryStore.search`): a volatile operational fact written "this
  session" is NOT in a later default-view recall, while the durable
  decision behind it IS — with a query that matches both bodies (so
  exclusion is the interval filter, not BM25). Invokes production
  entry-points; builds its own store; arranges no internal interval state
  by hand.

## §6 Build steps (order)

1. `file_memory.py`: add `classify_volatility` + volatility constants
   (AC.VOL.1); emit `volatility` + `volatile_until` frontmatter in
   `write_episode` for hard class (AC.VOL.2); extend
   `_supersession_interval` to read `volatile_until` (AC.VOL.3, D3).
2. `keep_pace/retrieval.py`: in `_episode_pointer`, prefix the soft
   annotation (AC.VOL.4), importing `classify_volatility`.
3. Tests under `framework/primary-persona/tests/`: one file per AC,
   `test_AC_VOL_*`; parametrized over tells.
4. Run touched tests; fix to green (never loosen).
5. Commit source (feat). Confirm clean `git status`.
6. `loam amend validate` → `loam amend apply` → `loam amend seal`.
7. Backfill §14 + STATE/roadmap.

## §7 Fence

Allowed surfaces (per `framework/primary-persona/tests/test_no_sealed_amendments.py`):
`framework/primary-persona/` + `docs/plans/`. All edits land there. No
sealed test loosened. No `_interval_current` / `_filter_by_interval`
semantic change (additive close source only). No re-introduction of a
recency blend.

## §8 Live-activation remaining (for dispatcher, owner-gated)

This build SEALS in canonical only. To take effect in the **live pos3
session**, the dispatcher must run the **canonical→pos3 sync** (the
research's Step 0) — that single sync brings BOTH the already-sealed
interval filter AND this volatility build to the tree pos3 imports
(`pos3/framework/framework/primary-persona/...`), and simultaneously
removes the live recency adversity (pos3 starts running `_compose_score`,
which has no recency blend). Until that sync, this is dormant in pos3.

## §14 Method-decision register (SHAs backfilled at close)

| Item | SHA |
|---|---|
| plan-doc | `25610cbf` |
| source (feat + AC.VOL.* tests) | `779d306f` |
| manifest | `f6bfb490` |
| apply | `f9fb305c` |
| seal | `fe7e2de2` |
| §14 backfill | (this commit) |

Baseline (seal-diff window open): `a7c9f1b2`. Seal-diff window
`a7c9f1b2..f9fb305c` (SEAL_COMMIT sidecar = the apply commit, house
pattern). Local seal only — NOT pushed, NOT published, NOT synced to
pos3 (live activation is the dispatcher's owner-gated call — see §8).
