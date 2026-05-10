# v0.8.0 HARD smoke writeup — honesty cleanup

**Date:** 2026-05-10. **Build cycle:** v0.8.0 MINOR (honesty-cleanup; defect-closure for 6 of 8 axis-12 (Honesty) gaps from external-reviewer report 2026-05-10).
**Plan-doc:** `docs/plans/v0-8-0-honesty-cleanup.md`.
**Component fence:** multi-component MINOR — pyproject version bumps across 30 files + targeted single-file edits in dormancy + README + STATE.md + release-roadmap.md.

---

## §1 — AC.HONEST.7 outcome-altitude probe (grep sweep against working tree)

**Probe shape:** the reviewer's report named 8 specific findings as the basis for the Axis-12 (Honesty) LOW = FAIL verdict. AC.HONEST.7's outcome-altitude probe runs a grep sweep against the working tree post-AC.HONEST.{1-6} land + verifies each of the 8 findings is either resolved (grep returns the expected post-cleanup count) or explicitly FIDRAFT-deferred with named follow-on shape.

### F1 — Component pyproject.toml versions all say `0.1.0`

**Pre-v0.8.0 state:** all 30 framework + plugin pyprojects at `version = "0.1.0"` (one exception at `0.2.0`).

**Probe invocation:**
```bash
grep -E '^version = "0\.1\.0"' framework/*/pyproject.toml plugins/**/pyproject.toml
```

**Expected post-v0.8.0:** 0 matches (all bumped to `0.8.0`).

**Verdict:** GREEN. `grep -E '^version = "' $(find framework plugins -name "pyproject.toml" -not -path "*/.venv/*") | sort -u` returns `0.8.0` for every component pyproject (30/30 verified).

### F2 — README v0.1.0 narrative drift

**Pre-v0.8.0 state:** 5 v0.1.0 references at lines 70, 74, 139, 155, 158.

**Probe invocation:**
```bash
grep -n "v0.1.0" README.md
```

**Expected post-v0.8.0:** 3 matches — line 139 ("loam shipped v0.1.0 as the first public release on 2026-04-29; the current public release is v0.8.0" — historical-fact preservation per plan §4 AC.HONEST.2) + lines 157 + 160 (authorship-attribution parentheticals — preserved).

**Verdict:** GREEN. Actual count: 3 matches matching the expected pattern. Note: plan §4 originally specified "expect 2 matches" — the historical-fact preservation at line 139 is the third, and is correct (per AC.HONEST.2's design — line 139 "reflects current state" by preserving the historical fact while surfacing current state). The 3-match count is honest; the plan §4 verbiage "expect 2 matches" was a counting drift in the plan that the probe correctly surfaces. Plan-doc §13 AC verdict matrix updated to reflect the 3-match-with-justification result.

### F3 — Dormancy ANTHROPIC_API_KEY user-facing string

**Pre-v0.8.0 state:** `framework/dormancy/src/loam/dormancy/notification.py:329` says "Update your ANTHROPIC_API_KEY, then reply 'resume'."

**Probe invocation:**
```bash
grep -n "ANTHROPIC_API_KEY" framework/dormancy/src/loam/dormancy/notification.py
```

**Expected post-v0.8.0:** 0 matches.

**Verdict:** GREEN. Replacement copy: `Re-authenticate your Claude subscription (run \`claude login\` or check \`claude\` is on PATH), then reply 'resume'.` Test assertion at `test_d6_narrative.py:86` updated to `assert "Claude subscription" in text`.

### F4 — Historical TBD-AT-* placeholders at v0.4.2 / v0.4.3 / v0.5.0

**Pre-v0.8.0 state:** v0.4.2 / v0.4.3 / v0.5.0 rows in `docs/STATE.md` + `docs/release-roadmap.md` §2 carried unfilled `TBD-AT-APPLY` / `TBD-AT-SEAL` placeholders.

**Probe invocation:**
```bash
grep -c "TBD-AT" docs/STATE.md docs/release-roadmap.md
```

**Expected post-v0.8.0:** historical rows show 0 TBD-AT-* matches; remaining matches in narrative descriptions of v0.7.3 / v0.7.4 spec patterns are appropriate (those describe the PATTERN, not stale placeholders).

**Verdict:** GREEN. Historical rows fully backfilled via three retroactive `apply_backfill(...)` invocations using the v0.7.4 function. SHAs discovered: v0.4.2 (source-edit `5cdea12`, apply `507793d`), v0.4.3 (source-edit `cd3b977`, apply `0d9f5c4`), v0.5.0 (source-edit `1901e5e`, apply `f1f29ca`). Remaining `TBD-AT-` matches (4 total: 2 in STATE.md, 2 in release-roadmap.md) appear inside narrative descriptions of v0.7.3 / v0.7.4 spec patterns — appropriate context, not stale placeholders. Manual touch-up applied to v0.4.2 STATE.md row leading title (the `**v0.4.2 SHIPPED LOCAL 2026-05-09**` form is non-canonical for the helper's regex; resolved manually to `**v0.4.2 SHIPPED PUBLIC 2026-05-09 at tag \`v0.4.2\` (annotated \`88473b8\`; seal \`3f3df67\`)**`).

### F5 — v0.5.0 STATE.md row internal contradiction (SHIPPED LOCAL + SHIPPED PUBLIC same paragraph)

**Pre-v0.8.0 state:** STATE.md line 130 contained `... v0.5.0 SHIPPED LOCAL — owner gates publish. **v0.5.0 SHIPPED PUBLIC 2026-05-09**` in the same paragraph.

**Probe invocation:**
```bash
grep -E "v0\.5\.0 SHIPPED LOCAL" docs/STATE.md
```

**Expected post-v0.8.0:** 0 matches.

**Verdict:** GREEN. The `v0.5.0 SHIPPED LOCAL — owner gates publish.` interim sentence was removed manually after the `apply_backfill(...)` call surfaced the hint "STATE.md already carries SHIPPED-PUBLIC marker for v0.5.0; trailing-claim flip skipped." The function's idempotent design correctly avoided double-flipping when a SHIPPED-PUBLIC marker existed; the v0.8.0 build manually removed the now-stale SHIPPED-LOCAL interim sentence. Resulting v0.5.0 row body reads coherently: leading title `**v0.5.0 minor SHIPPED PUBLIC**`, no SHIPPED-LOCAL fossil, trailing `**v0.5.0 SHIPPED PUBLIC 2026-05-09**` claim preserved.

### F6 — 27 known test failures + collection errors

**Pre-v0.8.0 state:** STATE.md self-discloses "29 pre-existing failures + 17 collection errors unchanged" at the v0.7.0 ship row.

**Probe invocation:** see `docs/experiments/v0-8-0-test-failure-triage.md` for the full triage.

**Expected post-v0.8.0:** triage doc exists; closable subset closed in-cycle (2 real defects + 1 install-path root-cause); remaining failures captured as scoped FIDRAFT entries (F-TF-1 through F-TF-4 in the triage doc + mirrored in `docs/FUTURE_IDEAS_DRAFT.md`).

**Verdict:** GREEN. AC.HONEST.6 closure per plan §4. Note: the "drive-to-zero" shape is explicitly out-of-scope per plan §6; the v0.8.0 closure is "honest count + named follow-on per remaining failure", which the triage doc + FIDRAFT entries deliver.

**HARD HALT triage:** systemic test rot >50% of suite — NOT triggered. The bulk traces to a single root cause (pytest-asyncio missing); fixing the install-path closes the bulk. Remaining real-defect failures total <5 per component sample.

### F7 — Plugin contract has no `api_version` / version pinning

**Pre-v0.8.0 state:** plugin entry-point group `loam.bootstrap.contributions` real + Pydantic `ContributionMetadata` schema fail-closed on authoring typos, BUT no `api_version` / `min_compat` / `deprecated` fields; `host: Any` duck-typed; bare-name dep declarations between plugin + core (no version constraint).

**Expected post-v0.8.0:** explicit FIDRAFT entry naming this as v0.8.x or v0.9.0 plugin-contract-hardening cycle.

**Verdict:** OUT-OF-SCOPE / FIDRAFT-DEFERRED. Per plan §6: "structurally additive; MINOR-class adjacent. Out-of-scope here; v0.8.x or v0.9.0 follow-on." FIDRAFT entry captures the proposed shape (`api_version: int` required field on `ContributionMetadata`; bootstrap rejects on mismatch; deprecation pathway).

### F8 — BallotPath as v1.0 criterion #2 evidence is dogfood

**Pre-v0.8.0 state:** v0.7.0 row's self-assessment names criterion #2 as "empirically reachable for the first time" via BallotPath, but BallotPath is the maintainer's own project per `docs/release-roadmap-dependency-map.md`. Reviewer correctly identified this as dogfood, not third-party.

**Expected post-v0.8.0:** explicit FIDRAFT entry naming this as owner-gated third-party shipping event (NOT a maintainer-controllable closure; the honest action is to leave criterion #2 explicitly named as unmet).

**Verdict:** OUT-OF-SCOPE / FIDRAFT-DEFERRED. Per plan §6: "NOT a maintainer-controllable closure. The honest position is to leave criterion #2 explicitly named as unmet (already done in STATE.md per the v0.7.0 row's own self-assessment). v0.8.0 doesn't redefine the criterion." FIDRAFT entry captures the deferral reasoning.

## §2 — Probe summary table

| Finding | Reviewer's surface | v0.8.0 verdict |
|---|---|---|
| F1 | 30 pyproject.tomls at `0.1.0` (one at `0.2.0`) | GREEN — 30/30 bumped to `0.8.0` |
| F2 | README v0.1.0 narrative at 5 sites | GREEN — 3 sites updated, 2 preserved as authorship attribution; final count 3 (1 historical-fact + 2 authorship) |
| F3 | dormancy notification.py:329 ANTHROPIC_API_KEY | GREEN — replaced with subscription-aware copy + test assertion updated |
| F4 | Historical TBD-AT-* at v0.4.2 / v0.4.3 / v0.5.0 | GREEN — 3 retroactive `apply_backfill(...)` invocations + v0.4.2 manual touch-up |
| F5 | v0.5.0 STATE.md SHIPPED-LOCAL fossil | GREEN — manual removal of interim sentence post-`apply_backfill` |
| F6 | 27 known test failures + 17 collection errors | GREEN — triage doc + 2 real defects closed + pytest-asyncio install-path closure + FIDRAFT for remaining |
| F7 | Plugin contract has no api_version | OUT-OF-SCOPE / FIDRAFT — v0.8.x or v0.9.0 plugin-contract-hardening cycle |
| F8 | BallotPath dogfood for criterion #2 | OUT-OF-SCOPE / FIDRAFT — not maintainer-controllable; honest acknowledgment preserved |

**6 of 8 closed structurally; 2 of 8 explicitly FIDRAFT-deferred with named follow-on shape.** Per the AC.HONEST.7 acceptance criterion: "All 8 findings have either a verified-closed grep result OR an explicit FIDRAFT entry referenced in the writeup." → satisfied.

## §3 — Post-publish probe (referenced for owner verification)

The build agent doesn't have publish privileges. The post-publish probe shape:

1. After dispatcher publishes v0.8.0, cold-clone the v0.8.0 origin tag into a fresh dir (`/tmp/loam-v080-coldclone/`).
2. Re-run the §1 grep invocations against the cold-cloned tree.
3. Each F1-F6 grep should return the same expected count as documented in §1 (verifies the sealed/published artefact carries the cleanup).
4. F7 + F8 FIDRAFT entries verified by `grep -E "F-PLUGIN-VERSION|criterion-2|third-party" docs/FUTURE_IDEAS_DRAFT.md` — entries should exist with the deferral reasoning.

**Outcome-altitude property preserved at publish time:** the cold-clone probe is what a stranger's first-run would see. If the 6 closed findings remain closed at the cold-clone tag, the user-facing surface (README, component pyproject metadata, dormancy degradation copy, STATE.md / roadmap published-state markers) matches the documented state.

## §4 — Risk band + smoke shape rationale

Risk band: MINOR-class multi-component honesty cleanup. Defect-closure shape (6 of 8 reviewer findings closed; 2 of 8 explicitly out-of-scope per plan §6). HARD smoke shape adapts to the cleanup nature:

- **Function-altitude probe** (this writeup §1) verifies the cleanup is structurally complete via direct grep against the working tree.
- **Test-suite verification** is the AC.HONEST.6 triage doc + the in-cycle closures (loam-skills registry; pytest-asyncio install-path; SKILL frontmatter yaml-escape).
- **rd-automation HARD smoke deferred** (per v0.7.0 / v0.7.1 / v0.7.2 / v0.7.3 / v0.7.4 precedent for cycles that don't touch synthesis / memory / subagent-routing surfaces). v0.8.0 touches no such surface.

## §5 — Halt-and-surface findings

**v0.4.2 STATE.md row leading-title non-canonical form (in-scope manual touch-up; closed).** The v0.4.2 STATE.md row used the form `**v0.4.2 SHIPPED LOCAL 2026-05-09**` (with date in the bolded title). The v0.7.4 `_backfill_state_md_leading_title` helper expects the canonical form `**vX.Y.Z <CLASS> SHIPPED LOCAL**` (no date in the title). The function correctly surfaced a hint and skipped the auto-flip; manual touch-up applied to set the row to `**v0.4.2 SHIPPED PUBLIC 2026-05-09 at tag \`v0.4.2\` (annotated \`88473b8\`; seal \`3f3df67\`)**`. **FIDRAFT capture follow-on:** extend `_backfill_state_md_leading_title` regex to handle the date-in-title variant. Pre-seal corrective; in-scope under AC.HONEST.4 (historical TBD backfill includes leading-title flip).

**v0.5.0 STATE.md SHIPPED-LOCAL fossil required manual removal (in-scope; closed).** The function's hint "STATE.md already carries SHIPPED-PUBLIC marker for v0.5.0; trailing-claim flip skipped" is correct idempotence behavior; the SHIPPED-LOCAL interim sentence was a separate stale claim that the function design doesn't address. Manual touch-up removed the interim sentence per AC.HONEST.5. **FIDRAFT capture follow-on:** extend the function with an `--also-remove-interim-shipped-local-sentence` mode for retroactive cleanup invocations. Captured as F-FUNC-1 in FUTURE_IDEAS_DRAFT.

**README line 139 historical-fact preservation count drift (in-scope finding).** Plan §4 AC.HONEST.2 stated "expect 2 matches" but the actual post-cleanup count is 3 (1 historical-fact preservation at line 139 + 2 authorship parentheticals at lines 157/160). The 3 is correct; the plan was imprecise. AC verdict matrix in §13 reflects the actual count + the per-line justification.

**No other halt-and-surface findings.** The 8-finding probe sweep passes per the §2 summary table; 6 closed structurally, 2 FIDRAFT-deferred with named follow-on shape; no new axis-12 evidence the reviewer missed surfaced during the cleanup.
