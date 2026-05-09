# v0.4.3 — AC.V043.5 live-store retrieval probe

**Date:** 2026-05-09
**Plan-doc ref:** `docs/plans/v0-4-3-patch-memory-retrieval-bm25-fix.md` §4 AC.V043.5
**Verdict band:** **GREEN** (10/10; bar was ≥7/10)
**Live store:** `/Users/lukeivers/pos3/workspace/.loam/memory/`
**Corpus baseline:** 457 episode files in the `pos3` group (was 438 at investigation time; +19 episodes added since baseline; baseline shape preserved)
**Source-edit SHA tested:** `a254f2c0` + linear-norm correction (HEAD before commit-3)
**Length-normalization path chosen:** **path (b)-shaped (linear `score / doclen`)**, not the §14 default path (a) sqrt — see §"Length-normalization path decision" below.

---

## Verdict summary

| # | Probe | Verdict |
|---|---|---|
| 1 | "What was v0.4.2?" | OK |
| 2 | "How does the BallotPath schema work?" | OK |
| 3 | "What did Eric report broken?" | OK |
| 4 | "Stage 7.7 verification corrections" | OK |
| 5 | "F-DESIGN-1 closure" | OK |
| 6 | "How does loam handle subscription-only?" | OK |
| 7 | "What is the current BallotPath project status?" | OK |
| 8 | "What did v0.4.0 ship?" | OK |
| 9 | "What memory-rules were captured this session?" | OK |
| 10 | "What v0.4.1 and v0.4.2 closures landed?" | OK |

**Total: 10/10 relevant top-3 hits.** Pre-V043 baseline (per `memory-retrieval-quality-investigation.md`): 1/6 ≈ 17%. Post-V043: 10/10 = 100% — well above the ≥7/10 (70%) GREEN bar.

---

## Per-probe top-3 (paths only, basenames)

### 1. "What was v0.4.2?" — OK
- `session-summary-v0.4.1-and-v0.4.2-fdesign-closures.md`
- `turn:b00f9cf3...:7e1453322b59.md`
- `turn:b00f9cf3...:2e7cc266832d.md`

Top result is the curated session-summary that names v0.4.2 directly. Relevant.

### 2. "How does the BallotPath schema work?" — OK
- `turn:b00f9cf3...:047027878372.md`
- `turn:b00f9cf3...:4e2ce69a38f4.md`
- `session-summary-ballotpath-project-status.md`

Top hits are turns from the BallotPath build session; #3 is the curated summary. Relevant.

### 3. "What did Eric report broken?" — OK
- `turn:b00f9cf3...:ac6bab58621b.md`
- `turn:b00f9cf3...:e648f01d34a9.md`
- `turn:e684a074...:cd8716744b92.md`

Eric/rd-automation turns surface. Relevant.

### 4. "Stage 7.7 verification corrections" — OK
- `turn:b00f9cf3...:c9a9dd68089a.md`
- `turn:b00f9cf3...:b59bf9935303.md`
- `turn:b00f9cf3...:e064a316d995.md`

Three turns from the Stage-7.7 build arc. Relevant.

### 5. "F-DESIGN-1 closure" — OK
- `turn:b00f9cf3...:375b71b60650.md`
- `session-summary-v0.4.1-and-v0.4.2-fdesign-closures.md`
- `session-summary-v0.4.0-shipped-end-user-odd-grounded-codegen.md`

Curated session-summaries surface for the F-DESIGN-1 ask. Relevant.

### 6. "How does loam handle subscription-only?" — OK
- `turn:b00f9cf3...:e648f01d34a9.md`
- `turn:b00f9cf3...:39d808b88e1a.md`
- `turn:b00f9cf3...:73bb92c05c7f.md`

Investigation-thread turns covering the subscription-only architectural floor. Relevant.

### 7. "What is the current BallotPath project status?" — OK
- `session-summary-ballotpath-project-status.md`
- `turn:b00f9cf3...:a8c7744435f1.md`
- `turn:b00f9cf3...:37ef4f090fa4.md`

Curated session-summary on BallotPath status ranks #1 — exactly the design intent. Relevant.

### 8. "What did v0.4.0 ship?" — OK
- `turn:b00f9cf3...:ae9275a10246.md`
- `turn:b00f9cf3...:5aa744c2c25d.md`
- `turn:b00f9cf3...:7c1500c47e1b.md`

Three turns referencing v0.4.0 ship state. Relevant.

### 9. "What memory-rules were captured this session?" — OK
- `session-summary-memory-rules-captured-this-session.md`
- `turn:5f29a8ae...:482237ac9a27.md`
- `turn:b00f9cf3...:a8c7744435f1.md`

Curated session-summary on memory rules at #1. Relevant.

### 10. "What v0.4.1 and v0.4.2 closures landed?" — OK
- `session-summary-v0.4.1-and-v0.4.2-fdesign-closures.md`
- `turn:b00f9cf3...:a8c7744435f1.md`
- `turn:b00f9cf3...:b2c18f885cf0.md`

Curated session-summary at #1; relevant.

---

## Length-normalization path decision (§14 D-V043.2 backfill)

**Path chosen: linear `raw_score / doclen` (path b-shaped).**

**Rationale (empirical):** The §14 default path (a) sqrt was insufficient against the AC.V043.2 unit-test fixture. With the AC-spec fixture (100 KB compaction-shaped episode mentioning every query term ≥10 times; 2 KB focused episode mentioning rare term 2 times):

| Norm | Compaction score | Focused score | Winner |
|---|---|---|---|
| Raw count | 30 | 4 | compaction (wrong) |
| Sqrt(doclen) | 30/sqrt(100500) = 0.0946 | 4/sqrt(2000) = 0.089 | compaction (still wrong, narrow margin) |
| Linear (doclen) | 30/100500 = 0.000299 | 4/2000 = 0.002 | **focused (correct)** |

Sqrt does not down-weight aggressively enough at the length differential the AC text specifies (50× larger compaction). Linear `raw_score / doclen` matches BM25's `b=1` extreme without requiring per-corpus avgdoclen precomputation, satisfies the AC unit-test fixture, and remains stdlib-only (no `math` import; no ML deps). The plan-doc D-V043.2 explicitly leaves the choice to the builder at build time and admits switching to path (b)-shaped if the empirical AC.V043.5 verdict requires it.

**Live-store empirical confirmation:** linear normalization achieved 10/10 GREEN on the live store (this report) — well above the ≥7/10 bar. No further tuning required.

---

## Notes for follow-up (FUTURE_IDEAS_DRAFT candidates)

1. **Per-term saturation (BM25 `k1`).** Current ranker treats every additional mention linearly; BM25's `k1` parameter saturates the marginal value of each additional mention. For the live-store result this didn't matter (10/10 green), but for adversarial corpora (e.g., a single document mentioning a term 1000×) it would matter.
2. **avg-document-length precomputation (path b proper).** Would let us tune `b` dial between path (a) sqrt and path (b) linear. Captured for FUTURE_IDEAS_DRAFT.
3. **Recency boost.** Plan-doc §6 already deferred this. Not engaged in this verdict.

All deferred per plan-doc §6.
