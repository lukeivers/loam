# FBM rule-weighting + hard-floor slice plan (B1 — the rank-normalize safety-pair)

**Status:** slice plan-doc (plan-before-code per the v-next build workflow)
**Working dir:** `/Users/lukeivers/loam` (canonical loam)
**Branch:** `slice/p1.2-loam-layout` (current build branch; carries the
rank-normalize merge at `7e9af6b`)
**Date:** 2026-05-31
**Workflow:** `docs/plans/loam-vnext-build-workflow.md` (per-slice loop)
**Predecessor slice:** FBM rank-normalize (`fbm-rank-normalize-slice-plan.md`,
seal sidecar advanced at `62081d8`) — made rules + episodes compete fairly on
relevance. **This slice is its SAFETY-PAIR.**

---

## Objective
Close the hole rank-normalize opened: now that a relevant episode can compete
on equal relevance footing with a rule, a hyper-relevant episode can out-rank
a **critical** rule. B1 adds a per-rule WEIGHT with two layers so importance —
not just relevance — shapes what surfaces:

1. **Scalar weight (gradient).** A rule (corpus doc) carries an optional weight
   on a 1–100 scale; it BOOSTS that doc's normalized `[0,1]` relevance so a
   more-important rule is selected more critically. Absent weight → a baseline
   default that preserves today's behaviour byte-for-byte. Episodes ride at
   baseline (no weight).
2. **Hard floor (the load-bearing safety layer).** A rule can be marked an
   absolute floor: it is ALWAYS included in the retrieved set regardless of
   relevance — a hard force-include, NOT a big multiplier. Required because a
   pure multiplier cannot guarantee never-drop: `weight × ~0-relevance ≈ 0`, so
   a hyper-relevant episode would still beat a high-weight-but-currently-
   irrelevant critical rule. The floor force-includes ahead of the relevance cut.

## EXAMINE — verified corpus-doc structure + where the weight is read

Empirical, against the LIVE corpus (`~/.claude/projects/-Users-lukeivers-pos3/memory`):

- **132 markdown docs; 30 carry YAML frontmatter** (a leading `---` … `---`
  block, e.g. `feedback_ruthless_feedback.md`, `feedback_agent_prompts_scope_only.md`),
  **102 have no frontmatter** (start straight at a `# Title`, e.g.
  `feedback_abstraction_first_default.md`). Verified by counting.
- **NO doc currently declares `weight`, `pinned`, or `priority`** (grep
  confirmed). So the field is purely additive — adding it to the parser changes
  nothing about today's corpus (every doc resolves to the baseline default).
- **`read_corpus_docs` (corpus_index.py) does NOT parse frontmatter today** —
  it reads the whole file body (frontmatter block included) into the FTS `body`
  column. The weight must be parsed there and threaded through.

**Data flow the weight must travel** (verified by reading the source):
`read_corpus_docs` → `CorpusDoc` → FTS row (`CREATE VIRTUAL TABLE corpus`) →
`CorpusIndex.search` returns `{path, title, pointer, score}` → `_merge_by_score`.
For weight/floor to reach the merge they must be (a) parsed in `read_corpus_docs`,
(b) stored on the FTS row (new UNINDEXED columns), (c) returned by `search`,
(d) consumed in `_merge_by_score`.

**EXAMINE disposition: extend** (two sealed framework functions —
`read_corpus_docs`/`CorpusDoc`/`CorpusIndex` schema+search on the corpus-index
side, `_merge_by_score` on the retrieval side). No new storage system; the
weight lives as optional frontmatter on the existing corpus markdown.

**Storage fork check (HALT trigger): frontmatter is the right home.** The
recommended storage (frontmatter on the corpus doc) is viable and additive —
30 docs already use frontmatter, none declares a weight, the parser already
needs touching to read it. No schema fork → no halt.

## The weight encoding (method — chosen + justified)

- **`weight: <int 1–100>`** optional frontmatter key on a corpus doc.
  - Baseline default `BASELINE_WEIGHT = 50` (mid-scale). A doc with no `weight`
    key resolves to 50; the gradient boost at weight 50 is a NO-OP multiplier
    (see math) so today's corpus (every doc → 50) is byte-identical.
  - Out-of-range / non-int → clamped into `[1,100]` then used (fail-soft; never
    raises — the every-turn hot path).
- **`pinned: true`** optional frontmatter key → the **hard floor**. Chosen as a
  **separate boolean**, NOT a `weight=100` sentinel, because: (a) it is a
  different SEMANTIC (always-include vs boost-a-lot) and conflating them hides
  intent — a doc can be `weight: 100` (boost hard) WITHOUT being an always-
  include floor, and a doc can be a floor at any weight; (b) a sentinel would
  make `weight: 100` un-expressible as "very important but still relevance-
  gated"; (c) the boolean is self-documenting in the frontmatter. Episodes are
  never pinned (no frontmatter surface).
- Both fields are parsed only from a leading YAML frontmatter block; a doc with
  no frontmatter resolves to `weight=50, pinned=False` (the 102-doc majority).

### Gradient math (the boost)
The merge already min-max-normalizes each source onto `[0,1]` (`_minmax_norm`).
The weight applies a multiplicative boost to a corpus hit's normalized score:

```
boosted_norm = norm * (weight / BASELINE_WEIGHT)
```

- At `weight = BASELINE_WEIGHT (50)` the factor is `1.0` → **no-op** (today's
  behaviour preserved exactly — the no-regression guarantee).
- `weight > 50` boosts (up to `100/50 = 2.0×`); `weight < 50` damps.
- Episodes carry no weight → factor `1.0` (ride at baseline), so a weighted rule
  out-ranks an equally-relevant episode by exactly its boost factor.
- The boost is applied to the normalized `[0,1]` value (not raw BM25), so it
  composes cleanly with rank-normalize and stays scale-free.

### Hard-floor force-include (the safety layer)
Pinned corpus hits are **force-included ahead of the relevance cut**:

1. Partition the combined hits into `pinned` and `rest`.
2. `pinned` are placed at the FRONT of the result (ordered among themselves by
   boosted-norm desc, stable arrival tie-break), then `rest` by boosted-norm desc.
3. Truncate to `top_n` — but pinned occupancy is guaranteed: if `len(pinned) >=
   top_n` the result is the top `top_n` pinned (a pinned rule is never displaced
   by a non-pinned hit). A pinned rule at ~0 relevance therefore SURVIVES against
   a hyper-relevant episode — the property a multiplier alone cannot deliver.

This is a force-include, not a multiplier: it does not depend on the pinned
rule's relevance score at all.

## DEFINE — outcome-altitude acceptance criteria

- **AC-FBM-W-1 — GRADIENT (outcome-altitude).** At comparable relevance, a
  higher-weighted rule out-ranks a lower-weighted rule. Verified by a `retrieve()`/
  `_merge_by_score` call where two corpus hits with equal raw relevance but
  different declared weights surface in weight order.
- **AC-FBM-W-2 — FLOOR / SAFETY (load-bearing, outcome-altitude).** A
  `pinned: true` rule co-surfaces in the retrieved set even at ~0 relevance,
  against a hyper-relevant episode — it does NOT drop. The test ALSO proves the
  property a multiplier alone could not deliver: a multiplier-only variant (same
  weight, no pin) of the same scenario DOES drop the rule out of `top_n`; the
  floor includes it. Both shown in the same test.
- **AC-FBM-W-3 — NO-REGRESSION.** Corpus docs with NO weight/pinned frontmatter
  behave exactly as today (weight 50 → factor 1.0 no-op; never pinned). The
  rank-normalize tests + the sealed `test_AC_FBMU_*` set stay green; the
  no-episode early-return (`if not episode_hits: return corpus_hits`) stays
  byte-identical (no normalization, no boost, no partition runs on that path).
- **AC-FBM-W-4 — LIVE-CORPUS COLD-WALK (outcome-altitude, the bar).** In a fresh
  process, against the REAL `feedback_*.md` corpus copied into a TEMP repo root
  (never the live store), a `pinned: true` rule survives in the top-N against a
  hyper-relevant freshly-written episode — proven through the production
  `retrieve()` entry-point with no pre-arranged retrieval state, and proven that
  the un-pinned variant of the same rule drops.

## Edit list (surgical)
1. `framework/primary-persona/src/loam/primary_persona/keep_pace/corpus_index.py`
   — (a) add a `_parse_frontmatter` helper (leading `---`…`---` YAML block →
   dict; absent → empty); (b) `CorpusDoc` gains `weight: int` + `pinned: bool`;
   (c) `read_corpus_docs` reads `weight`/`pinned` from frontmatter (clamp/coerce
   fail-soft, defaults 50/False); (d) the FTS schema gains `weight UNINDEXED,
   pinned UNINDEXED` columns; `sync` writes them; `search` returns them on each
   hit. **Schema bump → the index is a derived `.scratch/` cache, rebuilt on
   schema mismatch (already the documented contract), so no user-state migration
   of the index.** Body indexing strips the frontmatter block so frontmatter
   keys aren't FTS-searchable noise (a behaviour refinement; see no-regression
   note below).
2. `framework/primary-persona/src/loam/primary_persona/keep_pace/retrieval.py`
   — `_merge_by_score` gains the weight boost + pinned force-include. Episode
   hits default `weight=BASELINE_WEIGHT, pinned=False`. The empty-episode
   early-return stays byte-identical. Add a `BASELINE_WEIGHT` constant + a small
   `_weight_of`/`_pinned_of` accessor (fail-soft defaults).
3. `framework/primary-persona/tests/test_AC_FBM_W_*` — the four ACs above
   (gradient, floor+multiplier-can't-do-it, no-regression, and the live-corpus
   cold-walk). Cold-walk writes to a TEMP repo root.
4. `docs/state-migrations/fbm-rule-weighting-slice.migration.yaml` — declared
   migration. NO-OP for user-state: the corpus markdown is user-authored; adding
   an OPTIONAL frontmatter key is backward-compatible (absent key → baseline);
   the FTS index is a derived `.scratch/` cache rebuilt on schema change, not
   migrated. No `.loam/` episode store touched.
5. `docs/plans/build-cursor.md` — advance the cursor.
6. `framework/primary-persona/tests/test_no_sealed_amendments.py` BASELINE +
   `tests/SEAL_COMMIT` — advanced per the amend/seal discipline (HEAD~1 pattern)
   at INTEGRATE.

### Frontmatter-strip no-regression note (FBMU.2 / AC-FBM-W-3)
Stripping the frontmatter block from the FTS `body` changes what is indexed for
the 30 frontmatter docs. This is checked: the frontmatter block is metadata
(`name:`, `description:`, `type:`, `derivation:` keys) — NOT topical corpus
prose — so dropping it cannot remove a genuine topical match; it only removes
metadata-key tokens that could spuriously match. The body's `# Title` and prose
(the real topical signal) are untouched. The no-regression ACs assert the
existing FBMU + rank-normalize tests stay green AND a no-frontmatter doc indexes
byte-identically. If any rank-normalize/FBMU live-corpus expectation regressed on
the strip, the slice would HALT — it does not (those tests use synthetic hit
dicts / temp corpora, not frontmatter-key matches).

## Fail-safe (every-turn live hook)
`retrieval.py` + `corpus_index.py` are on the live keep-pace UPS hook (every
turn). The change is fail-safe by construction: (a) the no-episode early-return
is byte-identical (FBMU.2); (b) the boost + partition are pure arithmetic / set
ops on already-fetched hit lists — no new I/O on the merge path; (c) frontmatter
parse is wrapped fail-soft (any parse error → `weight=50, pinned=False`, the
no-op baseline) so a malformed frontmatter block never breaks retrieval; (d) the
FTS schema bump is absorbed by the derived-cache rebuild already in `sync`.

## ODD §2.5 — every line maps to a named AC (no non-objective code)
- frontmatter parse + `weight`/`pinned` on `CorpusDoc` + schema cols + search
  return → AC-FBM-W-1/2 (carry the weight/pin to the merge) and AC-FBM-W-3
  (default = no-op).
- gradient boost math → AC-FBM-W-1.
- pinned force-include → AC-FBM-W-2 (+ the multiplier-can't-do-it demonstration).
- clamp/coerce/fail-soft defaults → AC-FBM-W-3 (baseline preserved) — these are
  the named no-regression behaviour, not defensive code for an unnamed case.
- live cold-walk harness → AC-FBM-W-4.

## Halt triggers honoured
- Sealed-component edit (two functions across corpus_index + retrieval) →
  followed via the amend/seal discipline (advance BASELINE + `SEAL_COMMIT`, run
  touched + FBMU + rank-normalize + seal-fence tests). No content-filter, no
  Cairn, no `~/.claude/settings.json`, no touch of the live episode store
  (cold-walk uses a temp repo root copy of the corpus).
- No `claude -p` spawn needed (in-process production entry points). Had one been
  needed it would use `--strict-mcp-config` + empty mcpServers.
- Storage-schema fork: NONE (frontmatter is the confirmed home) → no halt.
