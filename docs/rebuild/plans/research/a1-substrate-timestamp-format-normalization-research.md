# Research — A1 substrate timestamp-format normalization

**Status:** research-doc only (no code, no commits, no manifest yet). 2026-04-28.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Sibling plan-doc:** `docs/rebuild/plans/a1-substrate-timestamp-format-normalization.md`.
**Programme position:** follow-on amendment after A1 (#51), A2 (#70), A3 (#71), A4 (#72), #52 (A8 dispatch wrapper), #73 (corpus inlining), #74 (dispatcher-side test-stub authoring). Composes; no programme amendment.
**Pre-flight verification (mandatory; per `feedback_verify_dispatch_before_sending` + brief):** dispatch verifies `git log --grep="A1.*timestamp\|timestamp.*normaliz\|created_at.*format\|sentinel.*manifest.*timestamp"` returns only the FIDRAFT-capture commit `1ca6f62` (no implementation commit), AND `ls docs/rebuild/plans/ | grep -iE "timestamp|created.at"` returns nothing matching this slug. Halt-and-surface if either does.

---

## 0. Pre-flight verification (mandatory)

Per the brief and `feedback_verify_dispatch_before_sending`. Already executed at research-author time:

- `git log --grep="A1.*timestamp\|timestamp.*normaliz\|created_at.*format\|sentinel.*manifest.*timestamp"` → returns only `1ca6f62 docs(FIDRAFT): capture amendment #74 build-findings — A1 timestamp heterogeneity, init.py byte-content brittleness, stale editable installs`. No implementation commit. Pass.
- `ls docs/rebuild/plans/ | grep -iE "timestamp|created.at"` → returns nothing. Pass.

The fix has not shipped. The dispatcher-side `_wait_until_next_iso_second` (#74, `framework/primary-persona/src/dispatch_wrapper.py:597`) is the current operational mitigation; the substrate bug is intact.

---

## 1. Problem statement

A1 (the structural-enforcement substrate, sealed at amendment #51) ships TWO timestamp emitters that produce LEXICOGRAPHICALLY INCOMPARABLE strings on same-second writes:

1. **A1 sentinel writers** — `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py:282` and `corpus_load_sentinel.py:472`:
   ```python
   return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
   ```
   Format: `2026-04-28T18:34:56Z` (second resolution, `Z` suffix).

2. **A1 manifest insert** — `framework/objective-tracker/src/store.py:329`:
   ```python
   created_at = datetime.now(tz=timezone.utc).isoformat()
   ```
   Format: `2026-04-28T18:34:56.123456+00:00` (microsecond resolution, `+00:00` suffix).

Lexicographic byte comparison of the two formats reverses on same-second writes:
- `Z` is byte 0x5A.
- `.` is byte 0x2E.
- `0x2E < 0x5A` → microsecond-suffixed string sorts BEFORE Z-suffixed string when seconds match.

Result: a manifest row inserted AFTER a sentinel write at the same wall-clock second has `manifest.created_at < sentinel.created_at` lexicographically — the temporal order is INVERTED for the comparator.

**A3's TDD-guard predicate (`framework/hands-off-lifecycle/hooks/tdd_guard.py:334`):**
```python
row_created_at > sentinel_created_at
```
This is a string compare. On the inverted order, A3's "new AC in this diff" predicate silently produces `False` for legitimate new-AC manifest rows, and A3 may DENY a legitimate edit (or, depending on hop, ALLOW a forbidden edit because the partition logic flips).

**Empirical:** 1000/1000 collisions in tight-loop test without mitigation (Q1 empirical answer recorded by amendment #74 build agent; FIDRAFT line 155).

**Current operational mitigation (#74):** the dispatcher's `_wait_until_next_iso_second` helper sleeps until the wall clock advances to the next whole ISO second before manifest insert. Worst-case wait < 1s, typical < 500ms. The mitigation works at ONE call site (the persona's `dispatch_with_scope` setup phase) and is invisible to any other code path that writes a manifest row from inside the same second as a sentinel write.

---

## 2. Inventory of emit + read sites

### 2.1 Timestamp emitters (write side)

| Site | File:line | Format | Resolution |
|---|---|---|---|
| Active-scope sentinel | `active_scope_sentinel.py:282` (`_now_iso`) | `%Y-%m-%dT%H:%M:%SZ` | second |
| Corpus-load sentinel | `corpus_load_sentinel.py:472` (`_now_iso`) | `%Y-%m-%dT%H:%M:%SZ` | second |
| Manifest row insert | `objective_tracker/src/store.py:329` | `datetime.now(tz=timezone.utc).isoformat()` | microsecond |
| Centralised gate helper | `_gate_helpers.py:278` (`now_iso_z`) | `%Y-%m-%dT%H:%M:%SZ` | second |
| A2 audit log | `objective_binding_gate.py:372` via `_helpers.now_iso_z()` | `%Y-%m-%dT%H:%M:%SZ` | second |
| A3 audit log | `tdd_guard.py:541` via `_helpers.now_iso_z()` | `%Y-%m-%dT%H:%M:%SZ` | second |
| A4 audit log | `agent_guard.py:502`, `bash_guard.py:594` via `_helpers.now_iso_z()` | `%Y-%m-%dT%H:%M:%SZ` | second |
| Persona dispatch-wrapper diagnostic | `dispatch_wrapper.py` (multiple `"ts":` records) | `datetime.now(timezone.utc).isoformat()` | microsecond |
| `objective_tracker` events | `objective_tracker/src/events.py:31` (`_utcnow_iso`) | `datetime.now(timezone.utc).isoformat()` | microsecond |

The format heterogeneity is wider than the brief's headline pair — it's "second-Z for sentinels + audit logs; microsecond-+00:00 for SQLite columns + diagnostic NDJSON `ts` keys." But (a) audit-log `ts` values are never compared against sentinel `created_at`, and (b) the only LEXICOGRAPHIC compare anywhere in the code base on these fields is A3's predicate. **The bug surface is one comparison site, not many.**

### 2.2 Read sites that lexicographically compare these fields

Exhaustive grep on the canonical tree (`framework/`, excluding tests + `.venv` + `.pyc`):

- **A3 TDD-guard (`tdd_guard.py:321`, `:334`):** `row_created_at > sentinel_created_at` — THE bug site.
- **A2 (`objective_binding_gate.py:243` ff):** reads `tracker.manifest_rows_for_ac(...)` but only checks `bool(rows)`. No `created_at` compare.
- **A4 agent_guard (`agent_guard.py:240`, `:392`):** reads `manifest_rows_for_ac(...)` but only checks `bool(rows)`. No `created_at` compare.
- **#74 dispatch wrapper (`dispatch_wrapper.py`):** WRITES sentinel + manifest; doesn't read either's `created_at` for comparison. The `_wait_until_next_iso_second` is preventative, not consumer-side.
- **A1 store SELECTs (`store.py:344`, `:358`, `:377`):** `ORDER BY created_at ASC, ...` — SQLite uses lexicographic comparison on TEXT columns. Within-table all rows use one format, so order is correct AS LONG AS no future change inserts a different format into the same column.

**The single lexicographic cross-format compare is A3's line 334.**

### 2.3 On-disk state on canonical tree

`/.pos/` and `workspace/` are gitignored (`.gitignore` lines `54` and `74`). The canonical tree carries NO sentinel JSON files and NO objective-tracker SQLite database. All A1 substrate state is per-workspace at runtime (`<workspace>/workspace/.pos/active-scope.json`, `<workspace>/.../objective_tracker.db`).

**Implication:** the brief's framing of "existing data on canonical's tree" is partially incorrect. There is no committed substrate state to migrate. There is, however, *runtime* state in any workspace where A1 is active (Luke's working trees: `pos3`, `ivers-corp-pos-v2`, etc.). Migration scope is therefore "any individual operator's runtime state," not "the canonical commit history."

### 2.4 Heterogeneity beyond timestamps (halt-trigger #2 check)

Per the brief halt trigger #2: are there OTHER A1 substrate fields with format mismatches beyond `created_at`?

Exhaustive grep + read of A1 surface:

- **`session_id`:** string-or-null on both sentinels. No format heterogeneity.
- **`scope_id`:** string. No heterogeneity.
- **`bindings`:** list-of-dict on sentinel; SQLite rows on manifest. Different containers but no compared cross-shape comparison.
- **`source_path_glob`:** string on manifest; not present on sentinel. No comparison.
- **`state` (corpus-load sentinel only):** literal `"loaded" | "partial" | "missing"`. Never compared against manifest.
- **`corpus_paths_required`, `corpus_paths_loaded`:** lists of strings on corpus-load sentinel. Not on manifest. No comparison.

**No other format mismatches.** Halt-trigger #2 does not fire. Scope is the timestamp pair only.

---

## 3. Design space — format choice

Three serialisable formats are on the table. All three are ISO-8601-conformant strings; the differences are resolution and zone-suffix shape.

### 3.1 Candidate α — second-resolution Z (current sentinel format)

```python
time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
# 2026-04-28T18:34:56Z
```

Pros:
- Already the format of all sentinels + audit logs. No change to sentinel writers.
- Centralised helper (`_gate_helpers.now_iso_z`) already exists.
- Fixed-width 20 chars; trivially comparable.

Cons:
- **Loses microsecond resolution.** Two writes inside the same second produce identical strings — A3's strict `>` predicate fails when manifest write lands in the same second as sentinel write.
- Forces continued reliance on `_wait_until_next_iso_second` for every new write site OR enforces the rule "no two related writes within one second" structurally elsewhere (advisory, fragile).

### 3.2 Candidate β — microsecond `+00:00` (current manifest format)

```python
datetime.now(tz=timezone.utc).isoformat()
# 2026-04-28T18:34:56.123456+00:00
```

Pros:
- Microsecond resolution distinguishes back-to-back writes structurally.
- Already the format of one production emitter (manifest insert).
- Stdlib-native, no manual format string.

Cons:
- **Variable suffix.** When microsecond is zero, Python's `isoformat()` OMITS the `.000000` segment, producing `2026-04-28T18:34:56+00:00`. Lexicographic compare across that boundary breaks: `2026-04-28T18:34:56+00:00` vs `2026-04-28T18:34:56.000001+00:00` — the `+` (0x2B) sorts BEFORE `.` (0x2E). Edge case but real (1-in-10^6 of writes).
- Heterogeneous string lengths complicate eyeballing audit logs.
- The `+00:00` zone suffix is verbose vs the more common `Z`.

### 3.3 Candidate γ — microsecond Z-suffixed (recommended)

```python
datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
# 2026-04-28T18:34:56.123456Z
```

Pros:
- Microsecond resolution distinguishes back-to-back writes structurally.
- Fixed-width 27 chars regardless of microsecond value (`%f` always emits 6 digits).
- `Z` zone-suffix matches existing sentinel convention; no migration of `Z` consumers.
- Lexicographic comparison is structurally correct for any pair of γ-format strings.

Cons:
- New format; not currently used by any emitter on the canonical tree.
- Loses the "drop trailing zero microseconds" cosmetic of `isoformat()` (irrelevant for compare).

### 3.4 Compare-time normalisation (no format choice)

Alternative to picking ONE format: parse-then-compare in the consumer. A3's predicate becomes:

```python
from datetime import datetime
sentinel_dt = datetime.fromisoformat(sentinel_created_at.replace("Z", "+00:00"))
row_dt = datetime.fromisoformat(row_created_at.replace("Z", "+00:00"))
if row_dt > sentinel_dt:
    ...
```

Pros:
- No emitter change. No on-disk format change. No audit-log change.
- Structurally correct for any IS0-8601 input (microsecond or not, Z-suffixed or `+00:00`-suffixed).
- Compare-layer fix is local to A3.

Cons:
- Relocates the failure to the compare layer: every FUTURE consumer that wants to compare these fields lexicographically must remember to parse first or use a shared helper. Per ODD §5.1.1, this RELOCATES rather than ELIMINATES the failure class.

### 3.5 Trade-off analysis

| | α (sec-Z) | β (microsec-+00:00) | γ (microsec-Z) | δ (compare-only) |
|---|---|---|---|---|
| Eliminates same-second collision | NO (relies on dispatcher wait) | YES | YES | YES |
| Eliminates trailing-zero edge case | N/A | NO (`isoformat()` drops zeros) | YES (`%f` always 6 digits) | YES (parse-then-compare) |
| ODD §5.1.1 (eliminate vs relocate) | RELOCATES (to "remember the wait") | ELIMINATES with edge-case caveat | ELIMINATES | RELOCATES (to "remember to parse") |
| Touches A1 surface (sealed) | no | yes (sentinel emitters change) | yes (sentinel + manifest emitters change to common format) | no |
| Touches A3 surface (sealed) | no | no | no | yes (predicate replaced) |
| Removes need for `_wait_until_next_iso_second` | no | yes | yes | yes |
| Eyeball / log-grep symmetry | yes (all uniform) | NO (mixed lengths) | yes (all 27 chars) | irrelevant |
| Audit log uniformity preserved | yes | NO (audit logs already Z; would mismatch SQLite) | yes (audit-log consumers ALSO migrate) | yes |
| Bytes per row | 20 | 26-32 | 27 | varies (storage = whatever was written) |

### 3.6 Recommended format choice

**Candidate γ — microsecond Z-suffixed.** Eliminates the failure class structurally, preserves the Z-suffix convention already used by sentinels + audit logs, fixed-width simplifies eyeballing, no edge case from `isoformat()`'s zero-microsecond stripping. Single shared helper (`_gate_helpers.now_iso_microsecond_z`) replaces both `_now_iso` instances and the manifest's inline `datetime.now(tz=timezone.utc).isoformat()`.

---

## 4. Design space — A1-emitter fix vs A3-compare fix

Per ODD §5.1.1 the question is which shape ELIMINATES the failure class.

### 4.1 Shape A — A1 emitter fix (recommended)

Change all three timestamp emitters (active-scope sentinel `_now_iso`, corpus-load sentinel `_now_iso`, manifest insert) to use the single shared helper that produces format γ. Migrate the audit-log helper `_gate_helpers.now_iso_z` along with them (so the entire substrate uses one format).

**Effect on the failure class:** ELIMINATES at the source. Any future consumer that lexicographically compares a sentinel `created_at` against a manifest `created_at` (or any other A1-substrate `created_at`) gets correct ordering structurally. The `_wait_until_next_iso_second` mitigation (#74) becomes unnecessary and can be removed.

**Future-proofing:** any new A1-substrate consumer that compares these fields cannot re-introduce the failure unless they actively author a different emitter with a non-conforming format — and the shared helper makes the conforming choice the obvious default.

**Sealed-component fence:** touches `objective-tracker/` (the manifest emitter) AND `hands-off-lifecycle/` (both sentinel emitters + the shared helper). Two sealed components.

### 4.2 Shape B — A3 compare-layer fix

Change A3's predicate to parse both timestamps as datetimes, compare structurally:

```python
def _compare_timestamps_strict_gt(later: str, earlier: str) -> bool:
    later_dt = datetime.fromisoformat(later.replace("Z", "+00:00"))
    earlier_dt = datetime.fromisoformat(earlier.replace("Z", "+00:00"))
    return later_dt > earlier_dt
```

**Effect on the failure class:** RELOCATES. A3 is fixed but every other consumer (current: none; future: any) must also parse-then-compare. The advisory rule "always use the parse helper before comparing A1 created_at fields" lives in the consumer, not the data.

**Sealed-component fence:** touches `hands-off-lifecycle/` only (A3 hook + a new helper in `_gate_helpers.py`). Smaller fence.

### 4.3 Shape C — keep dispatcher wait, document brittleness

What shipped at #74. Document the brittleness in `odd-in-pos.md` as a "structural-enforcement substrate invariant gap" so future contributors avoid the trap.

**Effect on the failure class:** RELOCATES to "remember to call `_wait_until_next_iso_second` before manifest insert from any new call site." Pure-advisory; ODD §5.1.1 says this is the weakest shape.

### 4.4 Recommendation

**Shape A.** ODD §5.1.1 strictly prefers elimination over relocation when both are structural; Shape A is the only one that eliminates the failure class. The wider sealed-component fence is justified by:

1. The fix is mechanically tiny (three function bodies + one helper).
2. The format change is BACKWARDS-COMPATIBLE on the read path (γ-format strings are valid ISO-8601; existing readers that parse via `fromisoformat` continue to work).
3. The wait-helper at the dispatcher (#74) becomes unnecessary and can be removed in the same amendment, simplifying the dispatch wrapper.
4. The shared helper consolidates the substrate's timestamp shape into a single source of truth.

---

## 5. Migration path for already-stored data

### 5.1 What "already-stored" means in this substrate

Per §2.3, NO substrate state lives on the canonical tree (gitignored). Stored state lives per-workspace at runtime. Per-workspace state classes:

1. **Active-scope sentinel** (`<workspace>/workspace/.pos/active-scope.json`): single file, one row of state, OVERWRITTEN on every `write_active_scope_sentinel(...)` call. Idempotent on byte-equal content.
2. **Corpus-load sentinel** (`<workspace>/.pos/session-state/<session_id>.json`): per-session file, written once per session.
3. **Objective-tracker SQLite** (per-workspace path; multiple manifest rows accumulated across amendments).

### 5.2 Behaviour of γ-format vs existing data

Sentinels (#1, #2): OVERWRITTEN. Within at most one session-start hook fire after the fix lands, every sentinel on every active workspace carries γ-format. No migration step needed.

Manifest (#3): rows ACCUMULATE. Existing rows carry β-format (microsecond `+00:00`). After the fix, new rows carry γ-format. The manifest column `created_at` mixes formats.

### 5.3 Migration options for the manifest

**Option (i) — accept heterogeneity in compare layer (RECOMMENDED).** Existing manifest rows stay β-format; new rows are γ-format. All read paths that compare `created_at` (only A3 does this lexicographically) use a parse-then-compare helper. The lexicographic ORDER BY in store.py SELECTs continues to work *within* a single format and produces stable order across the heterogeneity boundary because both formats sort microseconds-correctly within their own group, and the shape change happens once at the timestamp boundary.

Caveat: lexicographic `ORDER BY created_at ASC` over a row set that mixes β and γ produces a *non-temporally-correct* order at the boundary — γ's `Z` (0x5A) sorts AFTER β's `+` (0x2B). That means newly-inserted γ rows sort LAST regardless of their actual second. For A3's predicate this is harmless because A3 partitions by "is this row's `created_at` > sentinel's `created_at`?" and the sentinel side moves to γ in the same change — both sentinel and manifest flip to γ on the same release boundary. For other ORDER BY consumers (none currently exist that compare across the boundary), the order is "old rows first by their internal order; new rows after."

**Option (ii) — backfill rewrite on first read.** On first manifest read after fix, detect non-γ rows and rewrite them. Adds complexity for a substrate that never re-reads its own old data. Rejected.

**Option (iii) — UPDATE-all-rows migration on amendment apply.** A one-shot SQL `UPDATE objective_manifest SET created_at = ...` that converts existing β rows to γ. Possible because the conversion is well-defined (β → γ: replace `+00:00` with `Z`, ensure `.%f` segment is 6 digits, padding with zeros if `isoformat()` dropped them). One-shot upgrade hook on first SQL connection after the schema-version bump.

**Option (iii) is the right shape if the in-vivo amendment apply needs the column to carry one format.** Only one consumer (#74's setup phase) writes manifest rows post-amendment, and that consumer flips to γ on the same change. No other consumer compares `created_at` across rows. Option (i) — accept heterogeneity — is sufficient and simpler.

### 5.4 Backwards-compat at the read boundary

The two sentinel readers (`read_active_scope_sentinel`, `read_corpus_load_sentinel`) accept any string that passes the `isinstance(created_at, str) and created_at` check (`active_scope_sentinel.py:231`, `corpus_load_sentinel.py:386`). γ-format strings pass. β-format strings pass. α-format strings pass. No reader-side change required.

The one consumer that matters — A3's predicate — moves to parse-then-compare in the recommended shape (§6). Parse-then-compare admits all three formats.

---

## 6. Recommended implementation shape (preview)

The plan-doc carries the AC list. This research's recommendation:

1. **New shared helper.** Add `now_iso_microsecond_z()` to `_gate_helpers.py` returning `datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")`. Single source of truth.
2. **Migrate sentinel emitters.** `active_scope_sentinel.py:_now_iso` and `corpus_load_sentinel.py:_now_iso` delegate to the new helper.
3. **Migrate manifest emitter.** `objective_tracker/src/store.py:329` uses the new helper.
4. **Audit-log helpers stay second-Z** — different concern (human-readable log lines, no compare). Out of scope.
5. **A3 predicate stays lexicographic** — γ-format strings are correctly orderable by lex-compare. The change at the emitter is sufficient. No A3 source change required. (This is the load-bearing structural payoff of choosing γ over β.)
6. **Remove `_wait_until_next_iso_second`** from `dispatch_wrapper.py`. The dispatcher can write sentinel + manifest back-to-back; γ-format microsecond resolution distinguishes them. Update the docstring + the §14 method-decision register on amendment #74's plan.
7. **Migration is option (i)** — accept heterogeneity. No SQL UPDATE. No backfill hook. The only cross-format compare path is A3, and A3's compare works because both sides flip to γ on the same release.

---

## 7. ODD self-check on this research's recommendations

- **§5.1.1 elimination test:** Shape A (γ-format at all three emitters) ELIMINATES the failure class — a future contributor cannot re-introduce same-second collision without actively authoring a non-γ timestamp through a path other than the shared helper. The shared helper is the obvious default, and the canonical tree carries no other emitter pattern post-fix.
- **§2.5 reverse direction:** every recommended code change traces to a named AC in the plan-doc (sentinel emitter migration → AC.TFN.1; manifest emitter migration → AC.TFN.2; helper extraction → AC.TFN.3; wait-helper removal → AC.TFN.4; cross-format read compatibility → AC.TFN.5; format invariant test → AC.TFN.6).
- **§4 (handling defects):** this is a defect class (silent wrong-verdict on same-second writes). The fix is structural, not advisory. Method (exact format string, exact helper name, exact ordering of writes within the migration commit) is the builder's call.
- **§8.1 method-in-acceptance:** every AC below is outcome-shaped ("created_at strings sort lex-correctly across all A1 emitters"); no method prescription.

---

## 8. Open questions for owner ruling

The plan-doc's §6/§9 carries the named decisions. This research surfaces:

1. **Format choice — γ confirmed.** Recommend Shape A + γ. Owner ruling on §3.6.
2. **Migration strategy — option (i) confirmed.** Accept heterogeneity. Owner ruling on §5.3.
3. **Wait-helper removal — confirmed.** Remove `_wait_until_next_iso_second` and its callsite in the same amendment. Owner ruling on §6.6.
4. **Audit-log helpers — out of scope.** `now_iso_z` (second-resolution) stays for log lines because (a) no compare, (b) human readability. Owner may rule that audit logs ALSO migrate for uniformity; flagged as cosmetic + low-cost.

---

## 9. References

- FIDRAFT capture: `docs/rebuild/FUTURE_IDEAS_DRAFT.md` line 155.
- A1 plan-doc: `docs/rebuild/plans/structural-enforcement-a1-substrate.md`.
- A3 plan-doc: `docs/rebuild/plans/structural-enforcement-a3-tdd-guard.md`.
- #74 plan-doc: `docs/rebuild/plans/dispatcher-side-test-stub-authoring.md`.
- A1 sentinel emitters:
  - `framework/hands-off-lifecycle/hooks/active_scope_sentinel.py:282`
  - `framework/hands-off-lifecycle/hooks/corpus_load_sentinel.py:472`
- A1 manifest emitter: `framework/objective-tracker/src/store.py:329`.
- A3 compare site: `framework/hands-off-lifecycle/hooks/tdd_guard.py:321,334`.
- Dispatcher wait helper: `framework/primary-persona/src/dispatch_wrapper.py:597`.
- Centralised gate helper: `framework/hands-off-lifecycle/hooks/_gate_helpers.py:278`.
- ODD methodology: `docs/odd-methodology.md` (§3.3, §4, §5.1.1, §7.4, §8).
- VALUE_PROPOSITION: `docs/rebuild/VALUE_PROPOSITION.md` (translation-layer §; AC.PO.1, AC.PO.2).
- `.gitignore` lines `54` (`.pos/`), `74` (`workspace/`).
