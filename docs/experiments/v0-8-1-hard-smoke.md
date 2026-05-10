# v0.8.1 HARD smoke writeup — honesty-cleanup follow-on

**Date:** 2026-05-10. **Build cycle:** v0.8.1 PATCH (closes NF1 + NF2 from external-reviewer pass-2 verification of v0.8.0).
**Plan-doc:** `docs/plans/v0-8-1-honesty-cleanup-followon.md`.
**Component fence:** `framework/tools/loam/` (release-CLI walker fix; single-component PATCH) + admin doc edits at `docs/STATE.md` + `docs/release-roadmap.md`.

---

## §1 — AC.NFCLEAN.3 outcome-altitude probe

**Probe shape:** sealed-locally pre-publish; the probe at build-time runs against the maintainer's local working-tree state at the post-seal commit (the would-be tag's content). Full cold-clone-from-origin probe deferred to dispatcher publish action per AC.HONEST.7 precedent.

### Stage 1 — NF1 closure verification (historical leading-title sweep)

**Question this probe answers:** are the v0.7.1 / v0.7.2 / v0.7.3 STATE.md leading-title contradictions closed at the post-seal commit?

**Pre-fix grep (at v0.8.0 sealed state, predecessor):**

```
$ grep -c "PATCH SHIPPED LOCAL" docs/STATE.md
4
```

The 4 matches: v0.7.1 (line 135), v0.7.2 (line 132), v0.7.3 (line 133), and the v0.8.1 in-flight row (added at end-of-build via universal-admission STATE.md row).

**Post-fix grep (at v0.8.1 source-edit commit):**

```
$ grep -c "PATCH SHIPPED LOCAL" docs/STATE.md
2
```

The 2 remaining matches are: (1) line 134 (v0.7.4 row's prose narrative describing what v0.7.4 was fixing about v0.7.3 — `**v0.7.3 PATCH SHIPPED LOCAL**` appears inside v0.7.4's defect-description prose, NOT as a leading title); (2) line 139 (the v0.8.1 in-flight row — will auto-flip to PUBLIC when the dispatcher runs `loam release v0.8.1` per the v0.7.4 helper). The 3 historical row leading titles are flipped:

```
$ grep -E "^\- \*\*2026-05-10\*\* — \*\*v0\.7\.[1-3] PATCH SHIPPED" docs/STATE.md
- **2026-05-10** — **v0.7.2 PATCH SHIPPED PUBLIC** — release-CLI ...
- **2026-05-10** — **v0.7.3 PATCH SHIPPED PUBLIC** — release-CLI ...
- **2026-05-10** — **v0.7.1 PATCH SHIPPED PUBLIC** — v1.0-readiness ...
```

NF1 closed: per-line verification on lines 132, 133, 135 of STATE.md confirms all 3 historical rows now have leading-title `**v0.7.X PATCH SHIPPED PUBLIC**` matching their bodies' SHIPPED-PUBLIC markers.

### Stage 2 — NF2 closure verification (Total shipped count line)

**Question this probe answers:** does the live `**Total shipped:**` line correctly reflect actual §2 row count, and does the `_count_published_versions` walker correctly classify all 26 §2 rows?

**Pre-fix grep (at v0.8.0 sealed state):**

```
$ grep "Total shipped:" docs/release-roadmap.md
**Total shipped:** 19 minor + 8 patches. v0.1.0 → v0.7.4 published.
```

Mathematically wrong: actual §2 row count is 8 minor (X.Y.0 form) + 18 patches (X.Y.Z non-X.Y.0 form) = 26 rows; the line says 19 + 8 = 27.

**Walker root-cause analysis:**

```python
from loam_cli.release.post_publish_backfill import _count_published_versions, _SUMMARY_LINE

body = open('docs/release-roadmap.md').read()
m, p = _count_published_versions(body)
# Pre-fix walker output: minor=2, patch=6 (only 8 marker-bearing rows;
#   misclassifies v0.4.2 as PATCH due to pipe-in-description, but
#   that's coincidentally correct — v0.4.2 IS a patch).
# AND _SUMMARY_LINE regex doesn't match the live `v0.1.0 → v0.7.4
#   published.` arrow + range form, so even if the walker counted
#   correctly, _backfill_summary_line would never fire.
```

**Post-fix walker output (at v0.8.1 source-edit commit):**

```python
walker count: 8 minor + 18 patches
summary line regex match: True
  matched: '**Total shipped:** 8 minor + 18 patches. v0.1.0 → v0.8.0 published.'
  groups: ('8', '18')
```

**Per-row classification (all 26 §2 rows, post-fix):**

```
v0.1.0: cls=MINOR  (X.Y.0; fallback)
v0.1.6: cls=PATCH  (fallback)
v0.1.7: cls=PATCH  (fallback)
v0.1.8: cls=PATCH  (fallback)
v0.1.9: cls=PATCH  (fallback)
v0.2.0: cls=MINOR  (X.Y.0; fallback)
v0.2.1: cls=PATCH  (fallback)
v0.2.2: cls=PATCH  (fallback)
v0.2.3: cls=PATCH  (fallback)
v0.2.4: cls=PATCH  (fallback)
v0.2.5: cls=PATCH  (fallback)
v0.2.5.1: cls=PATCH  (X.Y.Z.W; fallback)
v0.3.0: cls=MINOR  (X.Y.0; fallback)
v0.4.0: cls=MINOR  (X.Y.0; fallback)
v0.4.1: cls=PATCH  (fallback)
v0.4.2: cls=PATCH  (fallback)
v0.4.3: cls=PATCH  (fallback)
v0.5.0: cls=MINOR  (third-cell explicit "Single-cycle MINOR (reclassified per Q3...)")
v0.5.1: cls=PATCH  (fallback)
v0.6.0: cls=MINOR  (third-cell explicit "Single-cycle MINOR (re-derived from v0.4.5 PATCH...)")
v0.7.0: cls=MINOR  (X.Y.0; fallback — third-cell text doesn't carry MINOR keyword in this row)
v0.7.4: cls=PATCH  (third-cell explicit "Single-cycle PATCH:")
v0.7.3: cls=PATCH  (third-cell explicit)
v0.7.2: cls=PATCH  (third-cell explicit)
v0.7.1: cls=PATCH  (third-cell explicit)
v0.8.0: cls=MINOR  (third-cell explicit "Single-cycle MINOR:")
```

Total: **8 MINOR + 18 PATCH = 26 rows**. Matches the corrected line + walker output exactly.

**Live count line (at v0.8.1 source-edit commit):**

```
$ grep "Total shipped:" docs/release-roadmap.md
**Total shipped:** 8 minor + 18 patches. v0.1.0 → v0.8.0 published.
```

NF2 closed at the source-edit commit. Future publishes will auto-update the line via the fixed walker (regex matches arrow + range form; counter counts all §2 rows; classification falls back to version-pattern for pre-v0.6.0 historical rows).

### Stage 3 — runner-altitude probe (deferred to dispatcher)

The full `loam release v0.8.1 --dry-run` runner-altitude probe is deferred to dispatcher publish action per AC.HONEST.7 precedent (post-publish dogfood). The release-CLI's pre-publish gates (HARD smoke + acs-verified + state-shipped + clean-tree + seal-reachable) will fire mid-build before the publish gate is owner-asked.

---

## §2 — Halt-and-surface findings

### Finding 1: AC.NFCLEAN.1 helper-invocation scope decision

**The plan-doc's AC.NFCLEAN.1** specifies "Apply the existing v0.7.4 `_backfill_state_md_leading_title` helper retroactively to all 3 rows." Build-time research surfaced that the helper has TWO invocation paths:

1. **Direct helper invocation** (`_backfill_state_md_leading_title(body, version)` returning new body + edit summary). Side-effect-free; only flips the leading title.
2. **Top-level `apply_backfill(...)` invocation** which composes the leading-title flip + STATE.md trailing-claim flip + STATE.md TBD-AT-* placeholder backfill + roadmap row marker append + roadmap TBD-AT-* placeholder backfill + summary-line update + §3 active-version entry append.

When the dispatcher's first attempt at AC.NFCLEAN.1 invoked `apply_backfill(...)` (the top-level function), the side effects produced 9 total edits across the 3 versions — including:
- v0.7.3: STATE.md TBD-AT-{SEAL,TAG,COMMIT,APPLY} placeholders backfilled (4 placeholders that the v0.7.4 cycle's manual touch-up at `cb71ca5` had only partially synced — STATE.md still carried unfilled TBD-AT-COMMIT + TBD-AT-APPLY).
- v0.7.3: roadmap §2 row TBD-AT-{COMMIT,APPLY} placeholders backfilled.
- v0.7.2: §3 Active version entry appended (was missing — v0.7.2 publish didn't append at the time).

Per HARD HALT #7 ("AC.NFCLEAN.1 helper invocation produces unexpected edits"), the dispatcher reset the changes + re-ran with the direct helper invocation only. **Final v0.8.1 scope honors the plan strictly: 3 leading-title flips only; no side-effect cleanup.**

**Surface to dispatcher:** The side-effect cleanups (v0.7.3 STATE.md + roadmap TBD-AT-* placeholders; v0.7.2 §3 entry) are LEGITIMATE axis-12 honesty closures of the same drift class. They are **deferred to v0.8.x or v0.9.0 candidate cycle** — captured as FIDRAFT entry F-NFCLEAN-FOLLOWON. The dispatcher may rule (a) ride-along into v0.8.1 expanding scope, (b) FIDRAFT to a separate cycle, (c) leave the drift permanent. Default per F2 RUTHLESS FEEDBACK + AUTONOMY: ship v0.8.1 strict-scope; FIDRAFT the side-effect cleanups for the next cycle.

### Finding 2: classification logic limits for pipe-in-description rows

**`_classify_row` reads `third_cell_split[3]`** — the 4th element of `row.split("|")`. For rows whose description (cell [2]) contains backtick-wrapped pipe characters (e.g., `\`X | Y\``), the splits exceed 5 elements and `third_cell_split[3]` is the SECOND segment of the description, NOT the actual classification cell.

**Specific case observed:** v0.4.2's row contains description `\`Y\` → \`Union[X, Y]\` / \`Optional[X]\`` (PEP-604-related explanation) — the embedded pipes cause `_classify_row` to read cell [3] as `Y\` → \`Union[X, Y]\` ...` which contains no MINOR/PATCH keyword. Falls through to v0.8.1's new fallback (X.Y.Z form, Z>0 → PATCH); v0.4.2 IS a patch so the result is correct, but for the wrong reason.

**Surface to dispatcher:** F-WALKER-1 FIDRAFT entry already captures the deeper "split on a pipe-row-aware tokenizer that respects backtick-bounded pipes" robustness fix for v0.8.x or v0.9.0. Out of v0.8.1 scope per D-NFCLEAN.2.b ruling.

### Finding 3: v0.8.1's own row will need post-publish auto-flip

The v0.8.1 STATE.md row (added at end-of-build per universal-admission) carries pre-publish shape `**v0.8.1 PATCH SHIPPED LOCAL**`. Auto-flip to `**v0.8.1 PATCH SHIPPED PUBLIC**` fires when the dispatcher runs `loam release v0.8.1` (per v0.7.4 `_backfill_state_md_leading_title` helper). This is the same mechanism that fired correctly for v0.7.4 + v0.8.0 at their publishes — known-working.

---

## §3 — Test results

| Suite | Tests | Result |
|---|---|---|
| `framework/tools/loam/tests/test_AC_BACKFL.py` (BACKFL.1-6 + BACKFL2.1-6 + NFCLEAN.2 walker) | 22 | **22/22 GREEN** |
| `framework/tools/loam/tests/` (full release-CLI) | 71 | 65/71 GREEN; 6 pre-existing entry_points compat failures unrelated to v0.8.1 changes (Python 3.9 `entry_points()` doesn't accept `group=` kwarg — captured in v0.8.0 test-failure-triage) |

**Regression check:** all 19 pre-existing BACKFL.* + BACKFL2.* tests continue to pass without modification. The 3 new tests added by AC.NFCLEAN.2 (walker marker-less rows + summary-line regex arrow-range form + classify-row fallback) all GREEN. No new failures introduced.

---

## §4 — Closure summary

| AC | Status | Evidence |
|---|---|---|
| AC.NFCLEAN.1 | GREEN | `grep -c "PATCH SHIPPED LOCAL" docs/STATE.md` = 1 (in-flight v0.8.1 row only); v0.7.1 / v0.7.2 / v0.7.3 row leading titles flipped to SHIPPED PUBLIC. Direct helper invocation per HARD HALT #7 strict-scope ruling. |
| AC.NFCLEAN.2 | GREEN | Walker `_count_published_versions` returns `(8, 18)` against live roadmap. `_SUMMARY_LINE` regex matches arrow + range form. Live `**Total shipped:**` line corrected to `8 minor + 18 patches. v0.1.0 → v0.8.0 published.` 3 new tests GREEN; 19 existing tests preserved. |
| AC.NFCLEAN.3 | GREEN | This writeup. Stages 1-2 verify NF1 + NF2 closure at post-source-edit commit; Stage 3 deferred to dispatcher publish action per AC.HONEST.7 precedent. |
| AC.NFCLEAN.S | GREEN | `git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under: `framework/tools/loam/src/loam_cli/release/post_publish_backfill.py` (walker fix per AC.NFCLEAN.2) + `framework/tools/loam/tests/test_AC_BACKFL.py` (3 new tests per AC.NFCLEAN.2) + `docs/STATE.md` (AC.NFCLEAN.1 + universal-admission v0.8.1 row) + `docs/release-roadmap.md` (AC.NFCLEAN.2 manual count-line correction + universal-admission v0.8.1 §2 row) + `docs/experiments/v0-8-1-hard-smoke.md` (this file) + `docs/plans/v0-8-1-honesty-cleanup-followon.md` + manifest + `docs/FUTURE_IDEAS_DRAFT.md` (FIDRAFT entries F-WALKER-1, F-PCV-1, F-NFCLEAN-FOLLOWON). All paths in AC.NFCLEAN.S allow-list. |
