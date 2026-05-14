# Release-backfill helpers completeness batch — HARD smoke writeup

**Cycle:** v0.10.3 PATCH (`release-backfill-helpers-completeness-batch`).
**Slug-named per `F-CYCLE-ARTEFACT-SLUG-NAMING`** (FIDRAFT 2026-05-14) — file path is `<slug>-hard-smoke.md`, NOT `v<version>-hard-smoke.md`. The `hard-smoke` release gate constructs the expected path from the plan-doc stem; slug-naming is structural compliance.
**Date:** 2026-05-14.
**Probe altitude:** function-altitude (per D-RBHCB.6) — direct invocation of the extended helpers via `.venv/bin/python` against synthetic fixtures hitting each historical corruption pattern. Three probes total, one per sub-scope.

---

## §1 — Probe 1 (F-FUNC-2 closure): interim SHIPPED-LOCAL sentence removal

**Sub-scope:** AC.RBHCB.1 — `_backfill_state_md` extended so when a SHIPPED-PUBLIC marker already exists for the version AND a stale `<version> SHIPPED LOCAL — owner gates publish.` interim sentence still lingers, the stale sentence is removed.

**Historical pattern this fixes:** v0.5.0's row at v0.8.0 AC.HONEST.5 — public-marker landed manually before v0.7.3's auto-backfill existed; the v0.7.4 helper's idempotence-by-skip path correctly avoided double-flipping but didn't clean up the stale interim sentence. v0.8.0 manually removed it.

**Synthetic fixture (input STATE.md body):**

```
# State

- **2026-05-09** — **v0.5.0 minor SHIPPED PUBLIC** — work. Plan-doc `aaaaaaa`. v0.5.0 SHIPPED LOCAL — owner gates publish. **v0.5.0 SHIPPED PUBLIC 2026-05-09 at tag `v0.5.0` (annotated `bbbbbbb`)**.
```

**Invocation:**

```python
_backfill_state_md(body, "v0.5.0", _dt.date(2026,5,14), "v0.5.0", "abc1234567890def")
```

**Verbatim post-call body excerpt:**

```
# State

- **2026-05-09** — **v0.5.0 minor SHIPPED PUBLIC** — work. Plan-doc `aaaaaaa`. **v0.5.0 SHIPPED PUBLIC 2026-05-09 at tag `v0.5.0` (annotated `bbbbbbb`)**.
```

**Verbatim edit_summary:**

```
STATE.md: removed stale interim sentence 'v0.5.0 SHIPPED LOCAL — owner gates publish.' (SHIPPED-PUBLIC marker already present)
```

**Verdict:** GREEN. Stale interim sentence (`v0.5.0 SHIPPED LOCAL — owner gates publish.`) removed; SHIPPED-PUBLIC marker preserved verbatim; leading-title PUBLIC marker preserved; preceding whitespace cleanly trimmed (no double-space artefact between `Plan-doc \`aaaaaaa\`.` and the SHIPPED-PUBLIC marker).

---

## §2 — Probe 2 (F-WALKER-1 closure): backtick-aware pipe tokenizer

**Sub-scope:** AC.RBHCB.2 — new `_split_pipe_row_backtick_aware(row)` helper respects backtick parity; `_classify_row` and `_extract_objective_sentence` use it instead of naive `row.split("|")`.

**Historical pattern this fixes:** v0.4.2's row description contains backtick-wrapped pipes (`` `Y` → `Union[X, Y]` / `Optional[X]` ``); naive split over-segments and `cell[3]` becomes the SECOND segment of the description rather than the actual class cell. The v0.8.1 version-pattern fallback incidentally produced the right answer for v0.4.2 (it IS a patch), but the explicit-class detection path was silently wrong.

**Synthetic fixture (contradiction-shape input row):**

The row's version (v0.4.0) would fallback-classify as MINOR (X.Y.0 form); the explicit-class keyword in the third cell is PATCH. Pre-fix would over-segment, miss PATCH in the actual third cell, and fall back to MINOR — wrong answer. Post-fix tokenizer reaches the third cell correctly so PATCH wins.

```
| v0.4.0 | desc with `a` `|` `b` pipe-wrapped pattern. | Single-cycle PATCH: seal `xxx` |
```

**Invocations + verbatim outputs:**

```
naive split count:                6
backtick-aware split count:       5
classify_row(row):                'PATCH'   (would be 'MINOR' via fallback alone)
extract_objective_sentence(row):  'desc with `a` `|` `b` pipe-wrapped pattern.'
```

**Verdict:** GREEN. Backtick-aware tokenizer correctly skips the backtick-wrapped pipe in cell [2]; reduces cell count from naive 6 to correct 5; reaches the actual third cell so the explicit-class PATCH keyword detection fires (NOT the version-pattern fallback). `_extract_objective_sentence` returns the full description string including the backtick-wrapped pipe (no mid-stream truncation). The contradiction-shape fixture (v0.4.0 + explicit PATCH) confirms the explicit-class path engages, not the fallback.

---

## §3 — Probe 3 (F-FUNC-3 closure): TBD-AT-* placeholder narrative-safety

**Sub-scope:** AC.RBHCB.3 — `_backfill_tbd_placeholders` regex-anchored via positive lookbehind to canonical surrounding tokens (`seal ` / `tag ` / `source-edit ` / `apply `); prose-narrative occurrences inside backtick-wrapped descriptions are preserved.

**Historical pattern this fixes:** the v0.7.3 STATE.md row at `docs/STATE.md:133` whose body description literally contains `` backfills `TBD-AT-SEAL` / `TBD-AT-TAG` placeholders from known SHAs `` as prose describing what the v0.7.3 helper does. Pre-fix `str.replace` would corrupt this prose narrative — the v0.10.1 Path-A halt finding.

**Synthetic fixture (input row carrying BOTH a canonical-context TBD AND prose-narrative TBDs):**

```
| v0.7.3 | helper backfills `TBD-AT-SEAL` / `TBD-AT-TAG` placeholders. | seal TBD-AT-SEAL |
```

**Invocation:**

```python
_backfill_tbd_placeholders(row, tag="v0.7.3", tag_sha="ffffffffffffffff", seal_sha="ddddddd1234567890")
```

**Verbatim post-call row:**

```
| v0.7.3 | helper backfills `TBD-AT-SEAL` / `TBD-AT-TAG` placeholders. | seal `ddddddd` |
```

**Verbatim backfilled list:** `['TBD-AT-SEAL']`

**Verdict:** GREEN. The canonical-context occurrence (`seal TBD-AT-SEAL`) was replaced with `seal \`ddddddd\``; the two prose-narrative occurrences inside backticks (`` `TBD-AT-SEAL` `` and `` `TBD-AT-TAG` `` in the description cell) were preserved verbatim. The lookbehind anchors do exactly what they should: canonical context preserved; prose narrative untouched.

---

## §4 — Combined regression check

**Test count:** 25 → 34 (25 existing BACKFL tests preserved unmodified + 9 new RBHCB tests across the three sub-scopes).

**Full release-CLI test suite:** 89 → 98 GREEN.

**Invocation:** `pytest framework/tools/loam/tests/` from the loam venv.

**Result:** all 98 tests pass (89 baseline + 9 new). No existing test was modified to accommodate the helper extensions.

---

## §5 — Slug-naming compliance check

This file lives at `docs/experiments/release-backfill-helpers-completeness-batch-hard-smoke.md` (slug-named per `F-CYCLE-ARTEFACT-SLUG-NAMING` FIDRAFT capture from 2026-05-14). The plan-doc stem is `release-backfill-helpers-completeness-batch`; the `hard-smoke` release gate's path-construction (`docs/experiments/<plan-doc-stem>-hard-smoke.md`) resolves to this file. NOT `v0-10-3-hard-smoke.md` (which would re-trigger the prior-cycle slip the FIDRAFT was captured to prevent).

---

## §6 — Closure log

| FIDRAFT | Status before | Status after | Sub-scope AC | Probe |
|---|---|---|---|---|
| F-FUNC-2 | capture-only (2026-05-10) | RESOLVED 2026-05-14 | AC.RBHCB.1 | §1 |
| F-WALKER-1 | capture-only (2026-05-10) | RESOLVED 2026-05-14 | AC.RBHCB.2 | §2 |
| F-FUNC-3 | capture-only (2026-05-13) | RESOLVED 2026-05-14 | AC.RBHCB.3 | §3 |

All three captured-only entries closed in this single PATCH cycle. Helper-internal extensions only; no public API changes; no `_backfill_state_md_leading_title` modification (HARD HALT respected).
