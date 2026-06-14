# seal-guard-floor-draft-baseline-skip — the floor's manifest-conformance sweep must not couple an unrelated seal to in-flight draft plans' placeholder baselines

## §1 — Objective

The GUARD-SWEEP FLOOR's class-5 member — the manifest-conformance
sweep `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_DPS1_*.py`
(`AC.DPS1.13`, "all manifests validate clean") — validates EVERY
`docs/plans/*.manifest.yaml` via `load_manifest` at every seal. Two
sibling DRAFT plans carry legitimate PLACEHOLDER baselines that fail
`load_manifest`'s 7-40-char lowercase-hex `baseline` check:

- `docs/plans/claude-leverage-program-s4b-wire.manifest.yaml`
  (`baseline: PENDING-S4A-SEAL`) — baselines on S4a's seal; resolves
  at S4b's own apply.
- `docs/plans/principle-foundation-structural-enforcement.manifest.yaml`
  (`baseline: PLAN_DOC_COMMIT`) — resolves at its first slice's apply.

These are not-yet-applied drafts whose baselines resolve at THEIR OWN
apply/seal time; they are not errors. The floor wrongly couples every
unrelated seal to every in-flight draft manifest's validity. Tier-0
confirmed (2026-06-14): `load_manifest` raises `InvalidField` on both
placeholders; the real-baseline Slice-3 manifest validates clean.

This is locked-design-not-license on the guard floor (sealed
`f7c1cc29`, 2026-06-12): the outcome is bad (blocks unrelated seals),
so the design is revisitable.

**Objective:** the manifest-conformance sweep validates manifests
whose baseline is a real (resolvable) commit-ish in full, and SKIPS
manifests whose baseline is a placeholder/draft marker — so an
unrelated cycle's seal is never blocked by an in-flight draft plan's
not-yet-resolved baseline, while a genuinely malformed real-baseline
manifest STILL blocks.

## §2 — Scope / fence

ONE sealed fence: `plugins/dev-sdlc/` (the `dev-sdlc` plugin).
`loam-amend` is a tool under that plugin; its tests + src seal via
`plugins/dev-sdlc/tests/test_no_sealed_amendments.py` / sidecar
`plugins/dev-sdlc/tests/SEAL_COMMIT`.

- IN fence: the manifest-conformance sweep test
  (`test_AC_DPS1_dev_pattern_simplifications_1.py`) and, if used, a
  small reusable skip-predicate helper in `loam_amend` src.
- Universal admissions: `docs/plans/` (plan pair).
- OUT of fence: any other component; the placeholder manifests
  themselves (read-only inputs — NOT edited); `manifest.py`'s
  `_SHA_RE` / `load_manifest` baseline validation (UNCHANGED — the
  hex check at real apply/seal time is correct and stays).

### §2bis — Primitive check (REQUIRED, Slice-2 convention)

- **Claude primitive leaned on:** none new. The fix is a Python
  predicate inside an existing pytest floor member; no hook, SKILL,
  MCP, or scheduling primitive is the right shape — the sweep already
  runs inside the seal subprocess via the established guard-floor
  registry mechanism (class 5). Adding a primitive here would be
  over-engineering a one-predicate correction.
- **Verdict:** no primitive adoption; the existing pytest-floor
  primitive is the correct and sufficient surface.

## §3 — Named decisions

**D-GFLOOR2.1 (RULED — dispatcher law, recorded here, not re-litigated):**
the manifest-conformance sweep SKIPS any manifest whose `baseline`
is NOT a valid resolvable commit-ish — i.e. a placeholder/draft
marker (non-hex, OR hex-shaped but not resolvable to a commit in the
repo). Manifests with REAL resolvable baselines stay FULLY validated.

- Rationale: a placeholder baseline marks a not-yet-applied DRAFT;
  its manifest is validated at its OWN apply/seal, never at an
  unrelated cycle's seal. A real-baseline plan is applied/sealed —
  its manifest must always parse, so a malformed one still blocks
  (that protection is the floor's point; do NOT over-loosen).
- Predicate detail: a baseline is "real" iff it matches
  `^[0-9a-f]{7,40}$` (the canonical `_SHA_RE` shape — single source
  of truth, imported from `loam_amend.manifest`) AND
  `git rev-parse --verify --quiet <baseline>^{commit}` resolves in
  the repo under test. Non-hex placeholders (`PENDING-*`,
  `PLAN_DOC_COMMIT`) skip on the shape check alone (no git call).
  A hex-shaped-but-unresolvable baseline (a draft using a
  `<backfill>`-style hex sentinel, or a stale SHA) skips on the
  resolve check — it too marks "not yet anchored to this repo's
  history". This is the "not-resolvable-to-a-commit" clause of the
  ruling, made concrete.

## §4 — Acceptance criteria (scope-descriptive, outcome-shape)

- **AC.GFLOOR2.1** — the manifest-conformance sweep validates (calls
  `load_manifest` on) every manifest whose baseline resolves to a
  real commit-ish, and reports any such manifest that fails to parse
  as a sweep failure. (The class-5 protection is preserved for
  applied/sealed plans.)

- **AC.GFLOOR2.2** — the manifest-conformance sweep does NOT fail on
  a manifest whose baseline is a non-resolvable placeholder/draft
  marker (`PENDING-*`, `PLAN_DOC_COMMIT`, any non-hex value); such a
  manifest is skipped, not validated.

- **AC.GFLOOR2.3 (★ outcome-altitude)** — invoking the PRODUCTION
  seal entry-point (`loam_amend.commands.seal.run` in finalize mode,
  no pre-arranged in-memory state) against a real repo that contains
  BOTH a draft manifest with a placeholder baseline AND an unrelated
  in-fence cycle does NOT halt on the placeholder draft via the
  guard-floor manifest-conformance sweep; AND a real-baseline manifest
  that is genuinely malformed STILL causes the sweep to fail. One test
  asserts both legs through the floor's sweep member running as the
  seal runs it (the production code path, not a re-implementation).

## §5 — Build steps (method = builder's call)

1. Add the skip predicate to the manifest-conformance sweep
   (`test_AC_DPS1_13_existing_manifests_validate_clean`): for each
   `*.manifest.yaml`, read its `baseline` field; if not a resolvable
   commit-ish per D-GFLOOR2.1, skip; else `load_manifest` + collect
   failures as today. Reuse `_SHA_RE` from `loam_amend.manifest` for
   the shape test (single source of truth).
2. Author AC tests: `test_AC_GFLOOR2_1_*`, `test_AC_GFLOOR2_2_*`,
   `test_AC_GFLOOR2_3_*` (the ★ runs the production sweep against a
   synthetic repo fixture carrying placeholder + malformed real-
   baseline manifests).
3. Run the dev-sdlc fence test + the loam-amend touched suite +
   the GFLOOR2 ACs locally; all green.
4. Commit source+tests as `fix(dev-sdlc): ...` BEFORE apply.
5. `loam amend validate` → `loam amend apply` → `loam amend seal`.
   Self-consistency: `loam_amend` is installed EDITABLE (the `loam`
   binary resolves `seal.py` straight from this working tree —
   Tier-0 verified 2026-06-14: `loam_amend.commands.seal.__file__`
   == the repo path), so the working-tree fix is exercised at seal
   with no reinstall. Prove it at seal: the seal that previously
   halted on the two placeholders now passes the manifest-conformance
   sweep.

## §6 — Halt triggers

- Tree dirtier than the one expected untracked Slice-3 narrative file
  at start.
- The fix would require loosening real-baseline validation (it must
  NOT — a malformed real-baseline manifest still blocks).
- The editable-install assumption proves false (working-tree fix not
  exercised at seal) — surface the install mechanics.
- A THIRD distinct pre-existing breach blocks the seal — HALT
  (three-strikes), do not fix-loop.

## §14 — Method-decision register

- plan-doc commit: `b14e279d`
- source commit (AC.GFLOOR2.*): `716b7b97`
- apply commit: `5ded29a0`
- seal commit: `82c93c5b`
- AC.GFLOOR2.1–3 (incl. ★ outcome-altitude AC.GFLOOR2.3): GREEN at seal
  (the GUARD-SWEEP FLOOR's manifest-conformance sweep skips draft
  placeholder baselines; real-baseline manifests still fully validated).
