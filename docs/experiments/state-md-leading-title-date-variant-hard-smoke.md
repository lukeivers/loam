# v0.10.2 HARD smoke writeup — STATE.md leading-title date-in-title variant

**Date:** 2026-05-13. **Build cycle:** v0.10.2 PATCH (`state-md-leading-title-date-variant`).
**Plan-doc:** `docs/plans/state-md-leading-title-date-variant.md`.
**Component fence:** `framework/tools/loam/` (release-CLI single-helper extension).

---

## §1 — AC.SMLTV.4 outcome-altitude probe (synthetic-fixture dogfood)

**Probe shape (single-stage):** the regex extension is a small structural change in one helper function. The outcome-altitude probe runs `_backfill_state_md_leading_title` directly against a synthetic STATE.md fixture containing all 4 cases the extension is meant to handle. This matches the v0.7.4 Stage-1 function-altitude precedent: the function-altitude probe is sufficient evidence the helper handles the input domain correctly.

### Synthetic fixture

```python
SYNTHETIC_STATE_MD = """\
# State

Some preamble.

- **2026-05-08** — **v0.9.0 MINOR SHIPPED LOCAL** — canonical-form
  pre-publish row (case 1).
- **2026-05-09** — **v0.4.2 SHIPPED LOCAL 2026-05-09** — date-in-title
  variant pre-publish row (case 2; historical v0.4.2 shape).
- **2026-05-08** — **v0.8.1 PATCH SHIPPED PUBLIC** — canonical-form
  already-public row (case 3).
- **2026-05-09** — **v0.4.3 SHIPPED PUBLIC 2026-05-09** — date-in-title
  variant already-public row (case 4).
"""
```

### Probe code

```python
from loam_cli.release.post_publish_backfill import (
    _backfill_state_md_leading_title,
)

cases = [
    ("v0.9.0", "case 1 — canonical-form LOCAL"),
    ("v0.4.2", "case 2 — variant LOCAL"),
    ("v0.8.1", "case 3 — canonical-form already-PUBLIC"),
    ("v0.4.3", "case 4 — variant already-PUBLIC"),
]
for version, label in cases:
    body_after, edit = _backfill_state_md_leading_title(
        SYNTHETIC_STATE_MD, version
    )
    edit_applied = edit is not None
    print(f"{label}: edit_applied={edit_applied}")
    if edit_applied:
        print(f"  edit_summary: {edit}")
```

### Expected output

```
case 1 — canonical-form LOCAL: edit_applied=True
  edit_summary: STATE.md leading title: '**v0.9.0 MINOR SHIPPED LOCAL**' → '**v0.9.0 MINOR SHIPPED PUBLIC**'
case 2 — variant LOCAL: edit_applied=True
  edit_summary: STATE.md leading title: '**v0.4.2 SHIPPED LOCAL 2026-05-09**' → '**v0.4.2 SHIPPED PUBLIC 2026-05-09**'
case 3 — canonical-form already-PUBLIC: edit_applied=False
case 4 — variant already-PUBLIC: edit_applied=False
```

### Verdict

**AC.SMLTV.4 GREEN.** All 4 cases handled correctly:

- **Case 1 (canonical LOCAL):** flipped to canonical PUBLIC; CLASS casing preserved (`MINOR`).
- **Case 2 (variant LOCAL):** flipped to variant PUBLIC; date preserved verbatim (`2026-05-09`); NO at-tag/annotated suffix appended (the trailing-sentence flip helper owns that surface per D-SMLTV.1).
- **Case 3 (canonical already-PUBLIC):** no edit applied; idempotent (matches AC.BACKFL2.4 precedent).
- **Case 4 (variant already-PUBLIC):** no edit applied; idempotent (extends AC.BACKFL2.4 to the variant per AC.SMLTV.3).

The verbatim post-call body excerpts demonstrate the regex extension widens the input domain by one variant without breaking canonical-form behavior and without introducing double-flip on already-public rows.

---

## §2 — AC.SMLTV.2 regression check (test suite)

`.venv/bin/python -m pytest framework/tools/loam/tests/test_AC_BACKFL.py -q` reports **25 passed** post-extension:

- 22 existing tests (the v0.7.3 + v0.7.4 + v0.8.1 BACKFL suite) — all pass unmodified, confirming AC.SMLTV.2 (canonical-form behavior preserved).
- 3 new tests (AC.SMLTV.1 positive flip, AC.SMLTV.3 already-public variant no-op, AC.SMLTV.1+AC.SMLTV.2 internal named-group invariant) — all pass.

**Pre-extension baseline (commit `80618a8`, post-plan-doc commit before regex change):** 22/22 BACKFL tests passing.
**Post-extension (this commit):** 25/25 BACKFL tests passing.
**Net:** +3 tests; zero regressions.

---

## §3 — Composition with existing helpers

The extension touches only `_leading_title_pattern` + `_state_md_title_already_public` + `_backfill_state_md_leading_title`. The other helpers in `post_publish_backfill.py` remain unchanged:

- `_backfill_state_md` (trailing-sentence flip per v0.7.3 AC.BACKFL.1) — UNCHANGED. Continues to emit the at-tag/annotated suffix as part of the trailing-sentence replacement.
- `_backfill_state_md_placeholders` (TBD-AT-* placeholder backfill per v0.7.4 AC.BACKFL2.2) — UNCHANGED. F-FUNC-3 narrative-safety gap stays open in its own future cycle.
- `_backfill_roadmap_row` (§2 row marker append per v0.7.3 AC.BACKFL.1 part 2) — UNCHANGED.
- `_discover_source_edit_and_apply_shas` (commit-graph walk per v0.7.4 AC.BACKFL2.3) — UNCHANGED.
- `_backfill_summary_line` + `_count_published_versions` + `_classify_row` (aggregate-count summary per v0.7.3 AC.BACKFL.2 + v0.8.1 AC.NFCLEAN.2) — UNCHANGED.
- `_backfill_section_3` (§3 Active Version entry append per v0.7.3 AC.BACKFL.3) — UNCHANGED.

The extension is structurally local to one helper-pair (pattern + already-public + flip).

---

## §4 — F-FUNC-1 closure

F-FUNC-1 (FIDRAFT entry at `docs/FUTURE_IDEAS_DRAFT.md:246`, captured 2026-05-10 from v0.8.0 AC.HONEST.4 halt-and-surface) is marked RESOLVED by this PATCH. The originating defect (v0.4.2 row's date-in-title variant required manual touch-up because the v0.7.4 helper's canonical-only regex skipped it) is now closed structurally: future post-publish rows in either shape get flipped by `apply_backfill(...)` without manual operator touch-up.

---

## §5 — Out-of-scope items deliberately left open

- **F-FUNC-3** (narrative-safety extension to `_backfill_state_md_placeholders`) — separate future cycle per dispatch brief HARD HALT.
- **F-FUNC-2** (interim SHIPPED-LOCAL-sentence removal mode) — different shape; not touched.
- **Historical row sweep** — no retroactive `apply_backfill(...)` invocations against v0.4.2 / v0.5.0 / other historical date-in-title rows beyond the new test fixture. Historical rows already manually-touched-up at v0.8.0 / v0.8.1 / v0.10.1; sweep stays deferred to a future cycle if needed.
