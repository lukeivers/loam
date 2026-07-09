# Brittle exact-value guards -> intent assertions — apply ladder

Cycle 3 of 3 (FINAL) of the fix program off the 2026-07-08 release-seal
near-miss audit (`workspace/.scratch/claude-output/release-seal-near-miss-audit-2026-07-08.md`,
pos3). Cycle 1 (`release-cli-tag-target-and-cut-hardening`, Classes D/A/B)
sealed at c074dc18; cycle 2 (`shared-doc-guard-floor-coverage`, Class C)
sealed at a8a34b47. This cycle lands **Class E only** — brittle exact-value
guards / seal-baseline-drift.

Root (audit §2 Class E, VERIFIED): two guard genera pin exact values that
legitimately change every cycle, so they fire on legitimate change and train
the "rebaseline it to match reality" reflex — which silently defeats the
guard if reality carries a real regression.

This amendment (dev-sdlc + hands-off-lifecycle fences, TEST assertions only,
NO public action):
  1. (BVG.1) `test_AC_KDOC_1` drops its `assert n <= 380` magic ceiling and
     asserts the leanness property it exists to protect — no return of the
     dropped 8-lens design-lens sprawl (the seven Lens 1-7 names do not
     reappear as sections) + the existing required-element presence. Its
     sibling `test_AC_MSLB_1` (the same genus, worse: an `n <= 380` meta-pin
     on the KDOC source + a two-sided `360 < n <= 380` on the spec) is
     converted IN PLACE to assert its true intent — the §7.6 cap-bias
     checklist is admitted into the spec — with every line-count assertion
     removed. MSLB keeps its filename + `test_AC_MSLB_1_*.py` floor pattern
     and still reads the doc, so cycle-2's AST shared-doc-coverage meta-check
     keeps detecting it as a floored shared-doc content-guard (zero
     `guard-floor.yaml` churn). RVL_8 independently covers the §7/§8
     checklist cap-bias lines.
  2. (BVG.2) `test_d1_byte_content_match.py` drops its whole-file SHA-256
     pins on 15 module bodies (the sole 64-hex whole-tracked-file pins in
     the tree; STATE.md logs 6+ manual-rebaseline recurrences with
     "root-cause fix OWED") and asserts a structural signature instead —
     `ast.parse` validity + expected stable public top-level surface —
     following the proven STATE.md L143 "stable module-body replacements"
     pattern. All 15 samples convert (not only the churny `cli.py` +
     `session_start_emitter.py`); the ≥15-sample floor (AC.D.1.5) is kept.

Outcome-altitude (AC.BVG.S, exercised with no pre-set state): the converted
leanness check PASSES a legitimately-grown spec fixture (real doc + a new
required feature checklist) and REDs a sprawl-injected fixture (real doc +
a returned 8-lens exposition); the converted signature check PASSES a
legit-edited module fixture (license header / added kwarg) and REDs a
truncated / wrong-surface module fixture.

Named decisions (plan §2, surfaced): MSLB converted in place, not retired
(D-EG.MSLB); all 15 d1 samples converted, not only the churny two
(D-EG.ALL15); the leanness invariant deliberately narrows from "generic
length" to "the named 8-lens sprawl does not return" so the doc may grow
freely otherwise (D-EG.ANTISPRAWL); the module-surface signature catches
truncation/emptying/wrong-file/public-surface deletion but not surgical
mid-body edits — the same residual as the STATE.md L143 fix, with behavioral
regressions caught by each module's own tests (D-EG.SIGLIMIT).

Enumeration (plan §3): the two named genera are the full recurring
exact-value-guard surface; other numeric caps
(WS_LIVE/ANL/AC40/alpha_1/O_2/WMS7/PERSONAS/PRGATE/SKILLCAP/DPS) are
resource caps with a named resource (legitimate bounded budgets, no
rebaseline recurrence) and are named-and-left per F2.

STOP at sealed-local. Does NOT run `loam release`, does NOT tag, does NOT
push — the eventual single published cut of all three cycles is the
dispatcher's action AFTER this seal.

BASELINE a8a34b47 — HEAD of main at plan-authoring (cycle-2 seal); confirm
at apply time. Counter 197 next free; confirm at apply time.
