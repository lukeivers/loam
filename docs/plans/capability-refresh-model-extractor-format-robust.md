# capability-refresh-model-extractor-format-robust — plan

**Slug:** `capability-refresh-model-extractor-format-robust`
**Component (sealed fence):** `framework/tools/capability-refresh/`
**Predecessor / BASELINE:** `a1166b8d` (canonical `main` at plan authoring —
memory-redesign S4 STATE change-log backfill tip).
**Working directory:** `/Users/lukeivers/loam-fix-modelextract` (isolated
worktree off `main`; NOT canonical `main`, NOT pos3).

---

## 1. Problem (Tier-0 verified)

The model-lineup tracker's ID extractor under-detects live models when the
upstream models-overview page changes its Markdown *formatting*.

`src/capability_refresh/models.py::extract_model_ids()` matches model IDs
ONLY when wrapped in backticks:

```python
_MODEL_ID_PATTERN = re.compile(r"`(claude-[a-zA-Z0-9][a-zA-Z0-9.-]*)`")
```

Anthropic reformatted the "Latest models comparison" table so the
**Claude API ID** row now renders most IDs as PLAIN text (matching the
other columns). Verified against the committed snapshot
`docs/capability-corpus/.refresh/snapshots/anthropic-models-overview.txt`
line 26:

```
| **Claude API ID** | claude-fable-5 | claude-opus-4-8 | `claude-sonnet-5` | claude-haiku-4-5-20251001 |
```

Only `claude-sonnet-5` is still backticked; `claude-fable-5`,
`claude-opus-4-8`, `claude-haiku-4-5-20251001` are plain. The extractor
therefore misses them. The committed lineup artifact
`docs/capability-corpus/.refresh/model-lineup/anthropic-models-overview.json`
confirms the miss — its `ids` list has **6** entries and does NOT contain
`claude-opus-4-8` or `claude-haiku-4-5-20251001` (both current, live
models — Opus 4.8 is the flagship). A purely cosmetic upstream edit
(backtick → plain) fakes a "removed" delta for any model that flips, and
permanently hides any model that was never backticked.

Root cause: extraction keys on a *presentation* detail (backticks) rather
than on *structure* (the model comparison table's ID row).

## 2. Objective

Make Claude model-ID detection robust to upstream docs FORMATTING changes:
a model whose ID is present in the models comparison table's Claude-API-ID
row is detected whether or not that ID happens to be backticked, so a
cosmetic edit cannot fake an add/remove delta — WITHOUT relaxing matching
so broadly that IDs from incidental prose/examples/version strings pollute
the lineup.

## 3. Halt-and-surface (pre-build)

- WD is the worktree, not canonical `main` — confirmed.
- No out-of-fence edits: all source + tests under
  `framework/tools/capability-refresh/`; plan + manifest under `docs/plans/`.
- The dispatch named a `pending-deltas/2026-07-08-anthropic-models-overview.md`
  evidence file that does NOT exist in canonical `main`. Substituted the
  committed snapshot + lineup artifact (both in-tree, Tier-0) as the real
  before/now evidence — the snapshot IS the fetched page text. Surfaced.
- The committed lineup JSON is already wrong (missing opus-4-8 + haiku-4-5).
  I am NOT hand-editing that machine-state artifact — see §7 decision D2.

## 4. Method (builder's call)

Replace the backtick-only regex with a UNION of two precise signals:

1. **Structural table-row parse (primary, authoritative).** Scan Markdown
   table rows; for any row whose first cell normalizes to `claude api id`
   (strip `*` bold markers, backticks, whitespace; lowercase), take each
   remaining cell, strip surrounding backticks + whitespace, and accept it
   iff the whole cell matches `^claude-[a-zA-Z0-9][a-zA-Z0-9.-]*$`. This
   is backtick-agnostic and handles both the wide real-page table (one
   row, many ID columns) and the narrow fixture table (one ID per row).
   Row-label gating + whole-cell anchoring keep it from capturing Bedrock
   / Google-Cloud ID rows (`anthropic.claude-*`, `claude-*@date`),
   description prose, or header cells.

2. **Backtick-quoted prose IDs (secondary, preserved from the original).**
   Keep the original `` `(claude-…)` `` regex over the whole text. This is
   NOT a loosening — it is the conservative original signal — and it is
   REQUIRED to avoid a phantom removal: models that appear only as a
   backticked ID in prose (e.g. `claude-mythos-5`, `claude-mythos-preview`
   in the snapshot's §"Claude Fable 5 and Claude Mythos 5" paragraph) have
   no table row. Dropping this half would delete them from the lineup and
   fire a false "removed".

`extract_model_ids` returns `sorted(set(table_ids) | set(backtick_ids))`.
`compute_model_delta`, `load/save_model_lineup`, and `run_refresh` are
UNCHANGED — the fix is localized to the one extraction function (+ a small
private table-row helper).

Why this avoids BOTH failure modes:
- **Under-detection (this bug):** the table parse catches plain-text IDs in
  the ID row regardless of backticks.
- **Over-capture:** neither half is a page-wide plain-text `claude-*` grep.
  The table half is gated to the ID-labeled row and anchored whole-cell;
  the prose half still requires backticks. An unrelated `claude-…` token in
  incidental prose (not backticked, not in an ID row) is captured by
  neither.

## 5. Acceptance criteria (outcome-shape; family `AC.CLP-MDLR`)

- **AC.CLP-MDLR.1 ★ (outcome-altitude).** Running the production extraction
  (`extract_model_ids`) on the REAL committed snapshot content of
  `anthropic-models-overview.txt` detects the full current-generation
  comparison-table lineup regardless of backtick formatting — the returned
  set INCLUDES `claude-fable-5`, `claude-opus-4-8`, `claude-sonnet-5`, and
  `claude-haiku-4-5-20251001`. Proven by reading the real file and calling
  the production function (not by inspecting the regex).
- **AC.CLP-MDLR.2 (no phantom delta across a pure formatting change).** A
  two-run refresh through the production `run_refresh`, built from the real
  before/after snippet (the comparison table identical except
  `claude-sonnet-5` backticked in run 1, plain in run 2), yields
  `model_delta.removed == []` and `model_delta.added == []` for the
  reformatted model.
- **AC.CLP-MDLR.3 (true removal still fires).** A model genuinely absent
  from the comparison table on the second run (present run 1, deleted run
  2) is still named in `model_delta.removed`.
- **AC.CLP-MDLR.4 (no over-capture).** `claude-…` tokens appearing only in
  incidental prose/examples (not backticked, not in a Claude-API-ID row),
  Bedrock-style `anthropic.claude-*` IDs, and `claude-*@date` Google-Cloud
  IDs are NOT added to the lineup.
- **AC.CLP-MDLR.5 (prose-only backticked model preserved).** A model
  present only as a backticked ID in prose with no table row (e.g.
  `claude-mythos-5`) is still detected — the structural change does not
  drop it, so no false removal.

Existing `AC.CLP-MDL.1-4` tests stay green (regression floor): the union is
a strict superset of the old backtick behavior on the existing fixtures.

Every changed line maps to a named AC above (ODD §2.5). No non-objective
code.

## 6. Build steps

1. Commit this plan + manifest (docs). [plan-before-code gate]
2. Edit `src/capability_refresh/models.py`: replace `extract_model_ids`
   with the union method + add the private `_extract_table_id_row` helper;
   update the module + function docstrings to name the new ACs.
3. Author `tests/test_AC_CLP_MDLR_1_5_format_robust.py` covering
   AC.CLP-MDLR.1–5, including the outcome-altitude read of the real
   committed snapshot.
4. Run the component suite locally; fix to green (never loosen a test).
5. Commit source + tests (`fix(capability-refresh): …`).
6. `loam amend validate` → `loam amend apply` → `loam amend seal`.
7. §14 SHA backfill in this plan-doc.

## 7. Named decisions

- **D1 — union, not table-only.** A table-only parse would drop prose-only
  models (mythos-5, mythos-preview) and fire a phantom removal. The union
  keeps every model the original caught PLUS the mis-formatted table IDs.
  Guarded by AC.CLP-MDLR.5.
- **D2 — do NOT hand-edit the committed lineup JSON.** It is runtime
  machine state carrying a `run_ts` provenance stamp. The next real refresh
  run recomputes it with the fixed extractor. That run will emit a
  ONE-TIME `added` delta for the genuinely-present-but-previously-hidden
  models (opus-4-8, haiku-4-5, and the legacy-table IDs) — a TRUE signal,
  not a phantom (the dangerous direction is phantom *removal*, which the
  fix eliminates). Fabricating the artifact by hand would forge its
  provenance. Surfaced to the dispatcher so the one-time delta is expected.

## 8. In-flight halt triggers

- Any required edit outside the component fence + `docs/plans/`.
- The union changing an existing `AC.CLP-MDL.1-4` assertion (would signal a
  behavior regression — halt, do not loosen the old test).
- Seal-test / guard-sweep failure unrelated to this change.

## 14. Method-decision register (SHA backfill)

| Step | Commit | SHA |
| --- | --- | --- |
| plan + manifest | docs(plans) | `7cecd58a` |
| source + tests | fix(capability-refresh) | `975588c4` |
| apply | loam amend apply | `ff5f9ba1` |
| seal | loam amend seal | `4bec445a` |

Sealed LOCALLY on branch `fix/capability-refresh-model-extractor-robust`
(worktree `/Users/lukeivers/loam-fix-modelextract`). NOT pushed — owner holds
the push. Seal-test fence green at SEAL_COMMIT `ff5f9ba1`.
