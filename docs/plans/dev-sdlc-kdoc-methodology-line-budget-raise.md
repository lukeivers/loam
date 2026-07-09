# dev-sdlc — methodology-spec line-budget raise (KDOC ≤360 → ≤380)

**WD:** `/Users/lukeivers/loam` (canonical). **Component:** `dev-sdlc` (sealed, `plugins/dev-sdlc/`). **Cut:** rides the v1.11.0 release integration (`docs/plans/release-integration-v1-11-0.md`) as its 4th fence — REQUIRED to ship recall (the two sealed constraints below are otherwise incompatible), and "everything unreleased ships in the one cut" covers it. **Dispatcher-ruled** (not owner-gated).

## 1. Problem (Tier-0 verified)

The recall-volume-limits reshape cycle (sealed this cut, `AC.RVL.8`) adds a required cap-bias checklist to `plugins/dev-sdlc/docs/odd-methodology.md` — a new `§7.6` (numeric-limit resource check) plus reviewer checklist item 15 — verified present by `framework/primary-persona/tests/test_AC_RVL_8_cap_bias_checklist_line.py`. That legitimately-required content grows the doc from 360 to **373 lines**.

`plugins/dev-sdlc/tests/test_AC_KDOC_1_methodology_rewrite.py::test_spec_at_most_360_lines` asserts the doc is **≤ 360 lines** (a keel-adoption-program Phase-1 leanness guard; `docs/plans/keel-adoption-program.md §5`). At 373 lines it fails. The two sealed constraints collide: the checklist is required content; the ≤360 bound rejects it.

The `test_AC_KDOC_1` 360-line assertion (line 36) is the SOLE dependent on that number — the "360 lines" in the module docstring and any BANDS-3 reference are historical prose, not assertions (proven: at 373 lines exactly one test fails). The guard's INTENT is leanness / no return of the dropped 8-lens sprawl; a 13-line legitimately-required feature checklist is not that bloat.

## 2. The fix (per `feedback_loose_AC_text_fix_AC_not_implementation`)

The content matches intent; the AC's numeric bound is now too tight given legitimately-required new content, and nothing but this one test depends on the exact number. So adjust the AC (test-only), not the content: raise the `test_AC_KDOC_1` line-count bound **360 → 380** (≈7 lines of headroom above the current 373 so a trivial future edit does not re-trip a brittle +2 bound, while still catching real dozens-of-lines bloat), update its assertion + message + the module docstring's "≤360", and add a code comment crediting the `AC.RVL.8` §7.6 cap-bias checklist as the reason. No production source changes; `odd-methodology.md` itself is unchanged by this amendment (it already carries the checklist from the recall cycle).

## 3. Scope

Single-component fence on `dev-sdlc` (`plugins/dev-sdlc/`). Edits confined to:
- `plugins/dev-sdlc/tests/test_AC_KDOC_1_methodology_rewrite.py` — raise the bound + docstring + rationale comment.
- `plugins/dev-sdlc/tests/test_AC_MSLB_1_line_budget_admits_cap_bias_checklist.py` — NEW test for `AC.MSLB.1` (ODD §2.5 traceability for the raise).

`F-SEAL-PLUGINS-TESTS-SKIPPED` applies — the seal runner skips plugins/ tests; the builder runs `python3.13 -m pytest plugins/dev-sdlc/tests/ -q` manually pre-seal.

## §4 — Acceptance criteria

### AC.MSLB.1 — the methodology-spec line budget admits the cap-bias checklist
The `test_AC_KDOC_1` methodology-spec line-count guard bound is raised from 360 to 380; the raise is credited (in a code comment) to the `AC.RVL.8` §7.6 cap-bias checklist that necessitated it. The current `odd-methodology.md` (373 lines, carrying the checklist) passes the raised guard; the bound stays tight enough that real bloat (well beyond the checklist's ~13 lines) still fails. Verified by `test_AC_MSLB_1_line_budget_admits_cap_bias_checklist.py`: the guard bound is 380 (not the old 360, not an unbounded value), and the §7.6 cap-bias anchor is present in the doc (the raise is justified by real content, not a blanket loosening).

### AC.MSLB.S — dev-sdlc suite green on the raised budget
`python3.13 -m pytest plugins/dev-sdlc/tests/ -q` is green: `test_AC_KDOC_1` (both the raised ≤380 line-count assertion and all 30 required-element anchors) passes on the 373-line doc, and no other dev-sdlc test regressed. `test_AC_RVL_8` (primary-persona, the checklist's own contract) remains green.

## §13 — §status

| AC | Verdict | Evidence |
|---|---|---|
| AC.MSLB.1 | GREEN | `test_AC_MSLB_1_line_budget_admits_cap_bias_checklist.py` passes |
| AC.MSLB.S | GREEN | dev-sdlc suite green pre-seal; test_AC_RVL_8 green |

## §14 — SHA register (backfilled at cycle close)

- plan+manifest `8919a713` · test edits `4094467b` · apply `20700c2` · seal `badd2d6f` (BASELINE `dd25353a`; dev-sdlc fence window = own delta only; dev-sdlc suite 399 passed / 7 skipped).
