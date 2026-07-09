# Brittle exact-value guards → intent assertions (release-seal near-miss audit, Class E — cycle 3 of 3)

Audit: `workspace/.scratch/claude-output/release-seal-near-miss-audit-2026-07-08.md`
(pos3), **Class E** (§2 "Brittle exact-value guards / seal-baseline-drift").
Cycles 1 (`c074dc18`, Classes D/A/B) and 2 (`a8a34b47`, Class C) sealed on
main. This cycle lands **Class E only** and is the FINAL cycle of the program.

## §1 — Objective

Two guard genera pin exact values that legitimately change across cycles, so
they fire on legitimate change and train the "just rebaseline it to match
reality" reflex — which, if reality carries a real regression, silently defeats
the guard. Convert both to **intent assertions** that check the property the
guard exists to protect.

1. **Line-count pin → leanness/structure invariant.** `test_AC_KDOC_1`'s
   `assert n <= 380` (raised 360→380 in v1.11.0) pins a magic ceiling on
   `plugins/dev-sdlc/docs/odd-methodology.md`. Its stated intent (Tier-0,
   three sources: the doc §10.2, `dev-sdlc-kdoc-methodology-line-budget-raise.md`,
   `docs/experiments/v1-11-0-hard-smoke.md`) is *leanness / no return of the
   dropped 8-lens sprawl* — NOT an absolute line number. Its sibling
   `test_AC_MSLB_1` is the same genus and worse: it pins `n <= 380` as a
   meta-string on the KDOC source AND a two-sided `360 < n <= 380` on the spec.
2. **Whole-file byte-hash pin → structural invariant.** `test_d1_byte_content_match.py`
   pins SHA-256 of 15 module-body files (the pyproject sub-instance was already
   root-caused 2026-06-11 by removing pyprojects). The remaining actively-edited
   module bodies (`cli.py`, `session_start_emitter.py`, `__init__.py`, …) get
   manually rebaselined nearly every cycle (STATE.md: 2nd/3rd/4th/6th recurrence,
   "root-cause fix OWED"). Follow the proven pattern (STATE.md L143 "stable
   module-body replacements"): assert the structural invariant / module surface
   the pin protects, not the whole-file hash.

## §2 — Named decisions (surfaced; recommendation IS the decision on in-scope build work)

- **D-EG.MSLB — convert MSLB_1 in place (not retire).** MSLB_1's entire subject
  (the 380 budget) disappears when the line-count is converted; its three tests
  all reference the pin and would RED. Convert it in place to assert its TRUE
  underlying intent — the §7.6 cap-bias checklist is admitted into the spec —
  dropping every line-count assertion. Keep the filename + `test_AC_MSLB_1_*.py`
  floor pattern so it stays a floored shared-doc content-guard (it still reads
  the doc via `.read_text`, so the cycle-2 AST meta-check keeps detecting it as
  floored). Retiring instead would force a `guard-floor.yaml` pattern removal +
  meta-check reconciliation — cross-cycle blast this tighter conversion avoids.
  RVL_8 independently covers the §7/§8 checklist cap-bias lines.
- **D-EG.ALL15 — convert all 15 d1 samples, not only the churny two.** All 15
  are the same whole-file-hash genus; converting only `cli.py` +
  `session_start_emitter.py` leaves the other 13 as latent landmines that
  re-break on the next legit edit. Evaluate-the-rule-not-just-patch → remove the
  whole recurrence class.
- **D-EG.ANTISPRAWL — narrow "generic length" to "the named 8-lens sprawl."**
  The replacement asserts the dropped design-lens exposition has not returned
  (the seven Lens 1–7 names as section headers, or ≥4 present in the body),
  which is MORE faithful to the stated intent than a length ceiling — but is
  deliberately narrower: the doc may now grow freely as long as the lenses do
  not return. Surfaced so a reviewer is not surprised the length ceiling is gone.
- **D-EG.SIGLIMIT — the module-surface signature's honest limit.** It catches
  truncation / emptying / wrong-file / public-surface deletion (via `ast.parse`
  validity + expected top-level surface). It does NOT catch a surgical edit
  inside a function body — the SAME residual as the "stable module-body" fix
  already blessed at STATE.md L143; behavioral regressions are caught by each
  module's own tests. Outcome-AC wording is scoped to what the signature detects.

## §3 — Enumeration (Tier-0; the full exact-value-guard surface at plan-authoring)

- **Line-count ceilings on odd-methodology.md (the recurring seal-baseline-drift
  offenders — CONVERT):** `test_AC_KDOC_1_methodology_rewrite.py:46` (`n <= 380`);
  `test_AC_MSLB_1_line_budget_admits_cap_bias_checklist.py` (`n <= 380` meta +
  `360 < n <= 380` ×2).
- **Whole-file byte-hash pins (the recurring genus — CONVERT):** only
  `framework/hands-off-lifecycle/tests/test_d1_byte_content_match.py` carries
  hardcoded 64-hex whole-tracked-file SHA literals (verified: it is the sole
  match of `"[0-9a-f]{64}"` across non-smoke `test_*.py`).
- **Other numeric caps — EVALUATED and LEFT (F2, with the exact-match reason):**
  `test_AC_WS_LIVE_1` (block ≤600), `test_AC_ANL_SURFACE_1_2_3_4` (≤700),
  `test_AC40_4_cap_guard` (≤2200), `test_AC_alpha_1` (index ≤1500),
  `test_AC_O_2` (body ≤2000), `test_AC_WMS7_LIVE_1` (≤700),
  `test_AC_PERSONAS` (desc ≤1536), `test_AC_PRGATE_5` (≤60000),
  `test_AC_SKILLCAP_1` (name ≤64), `test_AC_DPS1/DPS2` (5≤lines≤15). These are
  byte/line **resource caps with a named resource** (a legitimate bounded-output
  budget — the §7.6 "cap WITH a named resource" shape, NOT cap-bias), not the
  odd-methodology.md leanness treadmill; none show STATE.md rebaseline
  recurrence. They pin a value for a genuinely-must-be-bounded reason → they stay.

## §4 — Acceptance criteria (outcome-shape; method is the builder's call)

### BVG.1 — line-count → leanness intent (dev-sdlc)
- **AC.BVG.1** — the odd-methodology.md leanness guards assert the protected
  properties — no return of the dropped 8-lens design-lens sprawl (KDOC) + the
  §7.6 cap-bias checklist is admitted (MSLB) + required structural elements
  present — with NO absolute line-count ceiling anywhere in the two guard files.

### BVG.2 — byte-hash → module-surface intent (hands-off-lifecycle)
- **AC.BVG.2** — the d1 guard asserts each sampled file survived the D.1 move as
  a valid, correctly-surfaced module (`ast.parse` valid + its expected stable
  public top-level surface present) with NO whole-file byte-hash pin, preserving
  the ≥15-sample floor (≥5 per component × 3 components, AC.D.1.5).

### BVG.S — outcome-altitude (both genera) — `outcome-altitude: true`
- **AC.BVG.S** — exercised on real-shaped inputs with no pre-set state:
  (a) **leanness** — the converted leanness check PASSES a legitimately-grown
  spec fixture (real doc + a new required feature checklist, the exact shape that
  tripped 360→380) and REDs a sprawl-injected fixture (real doc + a returned
  8-lens design-lens exposition);
  (b) **signature** — the converted signature check PASSES a legitimately-edited
  module fixture (real source + an inserted license header / added kwarg — the
  exact edits that forced past rebaselines) and REDs a truncated / wrong-surface
  module fixture.

Uplink: AC.BVG.* → "seal-baseline-drift guards protect their intent, not a magic
value" → release-seal near-miss audit Class E → the amendment cycle's
change-management integrity (odd-methodology §10 / KEEL).

## §5 — Fence (multi-component)

- **dev-sdlc** — `seal_test: plugins/dev-sdlc/tests/test_no_sealed_amendments.py`;
  `sidecar: plugins/dev-sdlc/tests/SEAL_COMMIT`; `frozen_baseline: false`.
  Files: `tests/test_AC_KDOC_1_methodology_rewrite.py`,
  `tests/test_AC_MSLB_1_line_budget_admits_cap_bias_checklist.py`.
- **hands-off-lifecycle** — `seal_test:
  framework/hands-off-lifecycle/tests/test_cross_cutting.py`; `sidecar:
  framework/hands-off-lifecycle/tests/SEAL_COMMIT`; `frozen_baseline: true`.
  File: `tests/test_d1_byte_content_match.py`.
- Universal-admitted: `docs/plans/` (plan + manifest + sealed narrative),
  `docs/STATE.md`, `docs/plans/loam-roadmap.md`. **No `guard-floor.yaml` edit**
  (D-EG.MSLB keeps floor patterns stable). No source/runtime change to any
  component — TEST assertions only.

## §6 — Build steps

1. Convert `test_AC_KDOC_1`: drop `test_spec_at_most_380_lines`; add a module-
   level `_design_lens_sprawl_present(flat)` helper + a real-doc leanness test +
   the BVG.S sprawl-injection fixture test; keep REQUIRED_ELEMENTS; fix docstring.
2. Convert `test_AC_MSLB_1`: drop all line-count assertions; assert the §7.6
   cap-bias anchor is present; fix docstring (still reads the doc → stays floored).
3. Convert `test_d1_byte_content_match.py`: replace the SHA map with an
   expected-surface map + `_module_surface(src)` helper; parametrized real-file
   survival test + the BVG.S corruption fixture test; keep the ≥15-count test;
   fix docstring.
4. Run touched tests; then dev-sdlc + hands-off-lifecycle full suites (guard-floor
   sweep will re-run KDOC/MSLB via cycle-2's machinery — a dogfood).
5. Commit source (feat/fix) BEFORE apply; confirm clean `git status`.
6. `loam amend validate` → `apply` (grep HEAD after apply to confirm the intended
   edits landed) → `seal`. Backfill STATE.md + roadmap.

## §7 — Halt triggers (return to dispatcher; do NOT silently extend)

- A byte-hash→invariant conversion would weaken a genuine security/reproducibility
  exact-match need → KEEP the pin + surface. (Pre-answered NO: ordinary Python
  modules, D.1 migration long done, the pin is already toothless — freely
  rebaselined every cycle to bless current bytes.)
- Brittleness beyond the two named genera → surface the scope question, don't
  silently expand. (Enumerated §3: none beyond the two.)
- Any ODD violation in the work or surrounding code; any audit/brief conflict.
- The cycle-2 shared-doc-coverage meta-check REDs from a conversion → reconcile
  or surface, never bypass.

## §8 — Status

- Baseline: `a8a34b47b84b50568ee52bcdefe839414eabc2c0` (cycle-2 seal; confirm at
  apply). Amendment #197 (confirm at apply — highest on disk is 196).
- STOP at sealed-local. NO `loam release`, tag, or push — the single published
  cut of all three cycles is the dispatcher's action after this seal.
