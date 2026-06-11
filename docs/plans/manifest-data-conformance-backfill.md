# manifest-data-conformance-backfill — sub-plan-doc

Status: sub-plan-doc — BUILD-READY pending dispatcher ratification.
WD: /Users/lukeivers/loam (canonical loam; LOCAL only, NO push).
Parent context: AC.DPS1.13 manifest-sweep RED at HEAD `a73ff88e`.
Predecessors (load-bearing, all Tier-0 verified this authoring pass):
  - `df3f50f6` (2026-05-04) — dev-pattern-simplifications-2 seal; the 200-char
    `smoke_outcome` cap (manifest.py:558-575) live from here.
  - `019cfca7` — dev-pattern-simplifications-1 seal; AC.DPS1.13 sweep test
    (`test_AC_DPS1_13_existing_manifests_validate_clean`) live from here.
  - `2662245c` (2026-06-10) — v1.5.0 release prep; ADDED the three
    context-management manifest stubs at main (c1/c2/c3) in pre-v3 draft form.
  - `58c3c401` / `c0670065` / `4c47a646` (2026-06-05) — context-management
    Cycle-1 seal ladder on the UNMERGED branch `build/context-management-c1-see`;
    carries the conformant schema-v3 c1 manifest (baseline `fa422412`).
  - `5e086286` / `26fd2e5a` (2026-05-18) — session-clear-safety master
    manifest authored + ratified; its sub-amendments later sealed via their
    OWN sub-manifests (G seal `0c937746`) — the master manifest never drove
    an apply.
  - `a73ff88e` + `70302d17` (2026-06-11) — precedent docs-only backfills to
    sealed plans' docs (single-file direct docs commits).
BASELINE candidate: `a73ff88e` (main tip at plan-authoring; builder re-walks
  if HEAD has moved — do not treat as the apply-time pin).
Quality bar: data-conformance fix; the sweep test is the honest guard and is
  untouchable.

## §1 Objective / TL;DR

Outcome: the full dev-pattern-simplifications-1 test module passes 19/19 at
HEAD via the production pytest entry-point, with the sweep test (and every
other test file) byte-unchanged, because the four non-conformant manifests
under `docs/plans/` express the same facts conformantly.

Tier-0 verified state at `a73ff88e` (re-run this authoring pass, not taken
from the dispatch brief):

1. `pytest tests/test_AC_DPS1_dev_pattern_simplifications_1.py` → **1 failed,
   18 passed**; the one failure is `test_AC_DPS1_13_existing_manifests_validate_clean`,
   naming exactly four files.
2. `context-management-see-budget-eviction-{c1-see,c2-budget,c3-eviction}.manifest.yaml`
   — `schema_version: 1` with `number: null` (v1 requires an integer number;
   manifest.py:380-388).
3. `session-clear-safety-tracker-register-and-first-run-update-parity.manifest.yaml`
   — already schema v3; `smoke_outcome` is 575 chars vs the 200-char cap
   (manifest.py:570-575).
4. **The brief's diagnosis was incomplete (F2, named):** a bare
   `schema_version: 1 → 3` bump does NOT fix the three context-management
   manifests. `baseline` is required as a real 7-40-char hex SHA at EVERY
   schema version (manifest.py:399-403) and all three carry `baseline: null`.
   Empirically tested: bumping c1 to v3 alone yields
   `InvalidField: 'baseline' must be a non-empty string`. The conformant
   expression must also supply a real baseline SHA (see D-MCONF.2/.3).
5. **World-state refinement (F2, named):** c1's at-HEAD manifest is NOT the
   sealed cycle's record. The c1 cycle sealed 2026-06-05 on
   `build/context-management-c1-see` (NOT an ancestor of main;
   `framework/context-management/` absent at HEAD) with a fully conformant
   v3 manifest. Main's copy was independently ADDED by the v1.5.0 release
   prep (`2662245c`) in the older draft form — main and the sealed branch now
   carry divergent content at the same path (a latent merge conflict this
   cycle dissolves; see D-MCONF.2).

AC family: AC.MCONF.* (4 ACs, 1 outcome-altitude). Fence: docs/data only.

## §2 Placement

All four target files live under `docs/plans/` — universal-admission surface
(amendment #22 ruling #3), no component source touched. The cycle's seal
anchor is `dev-sdlc` (the sweep test is part of its `loam-amend` tool's
suite) with ZERO source edits — see D-MCONF.4 for the mechanism decision.

## §3 Scope

In scope:
- The four named manifest YAMLs under `docs/plans/`.
- This plan-doc + manifest pair, §14 backfill, and the standard
  `loam amend apply`/`seal` bookkeeping artifacts (sidecar bump, sealed
  narrative).

Out of scope (deferred):
- The sweep test and every other file under
  `plugins/dev-sdlc/tools/loam-amend/` — NO test or source edits.
- Merging `build/context-management-c1-see` into main (separate decision;
  this cycle only makes main's c1 manifest agree with the sealed record).
- Any guard preventing future release-prep stubs from being authored in
  non-conformant draft form (surfaced as an F2 item in §10; candidate
  FUTURE_IDEAS entry, dispatcher's call).
- Version assignment (derives at release time) and publishing (LOCAL only).

## §4 Acceptance criteria

| ID | Outcome | Verification |
|---|---|---|
| AC.MCONF.1 (outcome-altitude: true) | At the cycle's final commit, the full DPS1 test module run via the production pytest entry-point passes 19/19 with no pre-arranged state, and the cycle's diff over `plugins/dev-sdlc/tools/loam-amend/` (tests AND src) is empty. | Real pytest run + `git diff BASELINE..HEAD -- plugins/dev-sdlc/tools/loam-amend/` empty. |
| AC.MCONF.2 | Each of the four manifests loads clean through `load_manifest` AND every recorded fact survives re-expression: slug, title, plan pointer, component entries, narrative substance, and smoke-outcome meaning are unchanged; for c1 specifically, the at-HEAD file now expresses the sealed cycle's recorded facts (schema v3, slug-identified, baseline `fa422412`). | `load_manifest` on all four + a per-file fact-diff narrated in §14. |
| AC.MCONF.3 | The cycle's complete diff is confined to the four manifest files plus this cycle's own plan bookkeeping (this plan-doc, its manifest, §14 backfill, seal-ritual artifacts). No source code, no test files. | `git diff --stat BASELINE..HEAD` audited in §14. |
| AC.MCONF.4 | This cycle's own manifest joins the swept set and validates clean under the same sweep (the fix does not itself add a fifth non-conformity). | Covered by the AC.MCONF.1 run (the sweep globs all `docs/plans/*.manifest.yaml`). |

Method-in-AC check passed per AC: each pins WHAT (sweep green, facts
preserved, diff confined) and is satisfiable by any file-edit method.
Ladder-up: AC.MCONF.* → AC.DPS1.13's standing guarantee (every committed
manifest validates against the production loader) → AC.PO.2 (protection: the
amend machinery's data integrity is what keeps sealed-state claims honest).

## §5 Sealed-component fence

- Component anchor: `dev-sdlc` (seal_test
  `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`, sidecar
  `plugins/dev-sdlc/tests/SEAL_COMMIT`, currently `bd95f081…`) — zero source
  edits; anchor exists so the ritual has a seal surface and the RED→GREEN
  gets an auditable seal.
- Universal admissions: `docs/plans/` prefix (the four targets + this plan's
  bookkeeping all live here).
- No other component is touched. Touching any sealed component's source is a
  fence breach → halt.

## §6 Halt triggers (build-time)

1. Tier-0 RED re-check at the build's HEAD diverges from the four-file
   diagnosis (different files, different count, or sweep already green).
2. Any edit would change a recorded FACT rather than its expression — e.g.
   the sealed-branch c1 content no longer matches what main's history
   implies, or compressing the session-clear `smoke_outcome` cannot preserve
   all four named outcome facts within 200 chars. (This is the dispatcher's
   semantic-alteration halt, carried verbatim.)
3. The sweep is still red after the four edits (a fifth non-conformity
   surfaced) — halt; the fence may need widening and that is owner-gated.
4. Any change to the sweep test itself would be required — hard halt; the
   test is the honest guard and is explicitly not to be loosened.
5. `loam amend apply`/`seal` structurally rejects a docs-only,
   zero-source-edit cycle → fall back to direct docs commits per the
   `a73ff88e`/`70302d17` precedent (autonomous, low-blast-radius,
   reversible), record the fallback in §14, and surface it in the build
   report.

## §7 Build steps (method-level guidance; mechanics are the builder's call)

1. `cd /Users/lukeivers/loam && pwd && git log -1 --oneline` — verify WD +
   re-walk BASELINE if HEAD moved past `a73ff88e`.
2. Tier-0 RED re-check: run the DPS1 module (Python ≥3.11 with pytest,
   pyyaml, pydantic, pyee on path — e.g. `uv run --with ...`; the repo has
   no committed venv) — expect 1 failed / 18 passed on the four files.
3. Apply the four re-expressions per D-MCONF.2/.3/.5.
4. Re-run the module — 19/19 green (AC.MCONF.1/.4).
5. Narrate the per-file fact-diff into §14 (AC.MCONF.2).
6. `loam amend apply` + `loam amend seal` against this plan's manifest
   (D-MCONF.4); on structural rejection, halt-trigger 5's fallback.
7. §14 SHA-register backfill. LOCAL only — no push.

## §10 Named decisions (recommendations are the decision; dispatcher rules only if overriding)

- **D-MCONF.1 — Is conformance-normalizing a sealed cycle's manifest data a
  legitimate docs/data amendment?** Position: YES, with no special handling
  beyond (a) the facts-unchanged AC (AC.MCONF.2), (b) explicit
  conformance-backfill commit framing, (c) the untouchable-sweep rule.
  Grounds: sealed state is anchored in the git ref graph — commits, sidecars,
  seal tests — never in mutable working-tree YAML
  (`feedback_published_state_only_from_git_refs`); a re-expression cannot
  alter what `git show <seal>` returns. Precedent: `a73ff88e` + `70302d17`
  (today's docs-only backfills to sealed plans' docs). The Tier-0 findings
  further dissolve the concern's force here: c1's at-HEAD file is a
  release-prep stub, not the sealed record (which lives untouched on
  `build/context-management-c1-see`), and the session-clear master manifest
  is a ratified planning artifact that never drove an apply (its
  sub-amendments sealed via their own sub-manifests, e.g. G at `0c937746`).
- **D-MCONF.2 — c1 fix shape.** RECOMMENDED: restore main's copy
  byte-identical to the sealed branch's content
  (`git show 58c3c401:docs/plans/context-management-see-budget-eviction-c1-see.manifest.yaml`).
  Verified this pass: that content validates clean under HEAD's validator
  (smoke_outcome 191 chars) and is stable across the branch's amend+seal
  commits. It is the truest expression of the sealed cycle's facts AND
  pre-dissolves the latent same-path merge conflict. Alternative (hand-bump
  the stub in place) rejected: it would invent a second divergent expression
  of a cycle that already has a sealed one.
- **D-MCONF.3 — c2/c3 conformant expression.** RECOMMENDED: bump to
  `schema_version: 3`; drop the `number:` key entirely (v3 is slug-identified;
  keep the no-pre-bake comment); set `baseline:` to `2662245c` — the commit
  that authored the stubs, their true provenance pin — with a comment that
  the baseline is provisional and gets re-walked at apply time per the
  established pattern (the `ace6f87` session-clear precedent pins a real
  predecessor SHA the same way). `narrative.body` is present in both, so the
  v3 plan_doc_ref-or-body contract is already satisfied. Alternative
  (pin the fix-cycle's HEAD) rejected: weaker provenance, same conformance.
- **D-MCONF.4 — cycle mechanism.** RECOMMENDED: standard `loam amend apply`
  + `seal` anchored on `dev-sdlc` with zero source edits (everything rides
  the `docs/plans/` universal admission). This keeps a real RED→GREEN test
  transition inside the audit machinery and lets the new manifest dogfood
  the sweep (AC.MCONF.4). The plain-direct-commit precedent shape remains
  the named fallback (halt trigger 5) — those precedents edited plan-doc
  prose; this cycle flips a failing production test, which merits a seal.
- **D-MCONF.5 — session-clear `smoke_outcome` compression.** Builder authors
  a single-line ≤200-char re-expression preserving the four named outcome
  facts: (1) existing never-seeded workspace backfilled through the
  production update entry-point, (2) session-start digest priority-ordered,
  (3) owner-pending state representable + surfaced as open (never as done),
  (4) registered setup steps discovered + idempotently replayed. Non-binding
  candidate (187 chars, verified): `Existing never-seeded workspace via the
  production update path: tracker backfilled; digest priority-ordered;
  owner-pending surfaced as open, never done; setup steps replayed
  idempotently.` The full 575-char text stays recoverable at `5e086286`.

### F2 Ruthless Feedback / honest doubts

1. **Brief diagnosis incomplete** (named in §1.4): the v3 bump alone was the
   stated fix; baseline-null is a second, masked failure (validator raises
   first-error-only). Evidence: empirical validator run. Alternative shipped:
   D-MCONF.2/.3 supply real SHAs.
2. **Release-prep stub authoring is a recurrence surface**: `2662245c`
   authored three manifests in a draft shape the production validator
   rejects, at a path colliding with an unmerged sealed branch. One more
   such prep recreates this RED. Candidate structural fix (dispatcher's
   call, out of scope here): the release-prep flow runs the manifest sweep
   before committing stubs — cheap, the test already exists.
3. **Mild doubt on D-MCONF.4**: a zero-source-edit amend cycle bumps the
   dev-sdlc sidecar without touching dev-sdlc — defensible (the ritual's own
   bookkeeping; narrows future fence windows) but unusual. Halt trigger 5
   bounds the risk.

## §14 Method-decision register (populated at build + seal time)

- **D-MCONF.1..5 outcomes (build 2026-06-11, HEAD == BASELINE `a73ff88e`):**
  all five executed as ratified, zero deviations. D-MCONF.2: restored via
  `git show 58c3c401:<path>` redirect (byte-identical by construction).
  D-MCONF.3: v3 bump + `number:` key dropped (no-pre-bake comment kept,
  reworded to the slug-identified v3 form) + `baseline: "2662245c"` with the
  provisional/re-walk comment. D-MCONF.4: standard apply+seal anchored on
  `dev-sdlc`, zero source edits. D-MCONF.5: the plan's 187-char candidate
  adopted verbatim (verified 187 chars via `load_manifest`).
- **Tier-0 RED→GREEN (AC.MCONF.1):** at `a73ff88e` the DPS1 module ran
  1 failed / 18 passed, the failure naming exactly the four files
  (diagnosis confirmed). Post-edit: **19 passed / 0 failed** via the
  production pytest entry-point (`uv run` env: pytest + pydantic + pyee +
  local `loam-cli` + local `objective-tracker` + local `loam-amend`; the
  repo has no committed venv). `git diff` over
  `plugins/dev-sdlc/tools/loam-amend/` (tests AND src): empty.
- **Per-file fact-diff (AC.MCONF.2):**
  - **c1-see:** main's `2662245c` release-prep stub (v1, `number: null`,
    `baseline: null`, draft `seal_description`) replaced byte-identical with
    the sealed-branch record (`58c3c401`): schema v3, slug-identified,
    `baseline: "fa422412"`, 191-char `smoke_outcome`, `ac_count`, narrative
    body. No fact invented — every field is the sealed cycle's own recorded
    fact; the latent same-path merge conflict with
    `build/context-management-c1-see` is dissolved. Slug + plan pointer
    unchanged between stub and record.
  - **c2-budget:** `schema_version: 1 → 3`; `number: null` key dropped
    (v3 slug-identified; no-pre-bake comment preserved); `baseline:
    null → "2662245c"` (the stub's authoring commit — provenance pin,
    commented provisional/re-walked-at-apply). Slug, title,
    plan pointer, `seal_description`, both component entries
    (context-management + loam-skills), universal paths, and the full
    narrative body byte-unchanged.
  - **c3-eviction:** identical transformation to c2 (v3 bump, `number:`
    dropped, `baseline: "2662245c"`). Slug, title, plan pointer,
    `seal_description`, loam-skills component entry, universal paths,
    narrative body byte-unchanged.
  - **session-clear-safety master:** `smoke_outcome` 575 → 187 chars,
    single line, preserving all four named outcome facts: (1) existing
    never-seeded workspace through the production update path with tracker
    backfilled, (2) digest priority-ordered, (3) owner-pending surfaced as
    open never done, (4) setup steps replayed idempotently. The AC-ID
    enumeration + failing-step-surfaces clause moved out of the field; full
    575-char original recoverable at `5e086286` (comment added in-file).
    Every other field byte-unchanged.
- **Build-artifact note:** the `uv` test runs materialized transient
  setuptools `build/` dirs in three package trees; removed before commit
  (never staged; AC.MCONF.3 diff unaffected).
- **SHA register (sealed 2026-06-11, LOCAL only — not pushed):**
  - plan pair: `475a79ed`
  - source-edit (four manifests): `4e2d055c`
  - apply: `3f218a63` (dev-sdlc sidecar + seal-test BASELINE → `a73ff88e`)
  - seal: `40fba3ef` (post-seal `apply --dry-run` clean per seal output)
- **AC.MCONF.3 diff audit (at seal):** 9 files — the four target manifests,
  this plan-doc + its manifest, the sealed narrative
  (`docs/plans/sealed/manifest-data-conformance-backfill.md`), and the two
  machinery-written seal-ritual artifacts from the apply auto-commit
  (`plugins/dev-sdlc/tests/SEAL_COMMIT` sidecar; the 1-line BASELINE
  constant in `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — the
  BASELINE-aware seal anchor, advanced by `loam amend apply` itself, NOT a
  hand edit; the untouchable DPS1 sweep test is byte-unchanged — empty diff
  over `plugins/dev-sdlc/tools/loam-amend/`). Conformant per AC.MCONF.3's
  seal-ritual-artifacts admission.
- **Seal-mechanics note:** `loam amend seal` HALTed once on the dispatcher's
  intentionally-uncommitted `docs/FUTURE_IDEAS_DRAFT.md` (dirty-tree guard);
  resolved by stash → seal → stash-pop, content verified byte-identical by
  sha256 before/after. Not halt-trigger 5 (no structural docs-only
  rejection — apply + seal both accepted the zero-source-edit cycle;
  D-MCONF.4's mild doubt resolved in favor of the standard mechanism).
- **Final verification at seal HEAD `40fba3ef`:** DPS1 module 19/19 via the
  production pytest entry-point (AC.MCONF.1 + AC.MCONF.4 — this cycle's own
  manifest swept clean among them; 18 sibling tests stayed green per §15).

## §15 Backwards-compat verification

- Full DPS1 module 19/19 (18 currently-green siblings must stay green).
- No other test surface is touched; no source is touched (AC.MCONF.3 is the
  guard).

## §16 Halt-and-surface findings at plan-authoring

1. Baseline-null masked failure — surfaced (§1.4), resolved in-plan
   (D-MCONF.2/.3); no owner ruling needed (outcome shape + fence unchanged).
2. c1 "sealed manifest" framing refinement — surfaced (§1.5); strengthens,
   not contradicts, the four-file diagnosis; no halt (the dispatcher's halt
   condition was contradiction; this is confirmation with sharper provenance).
3. Operational-objective test run on all five named decisions: the cycle's
   objective (sweep green, facts preserved, docs-only) implies clear answers
   for each; none is critical-call / public-action / financial → recommended
   autonomously, dispatcher rules only on override.

## §17 Provenance trail

- Sweep test: `plugins/dev-sdlc/tools/loam-amend/tests/test_AC_DPS1_dev_pattern_simplifications_1.py`
  (`test_AC_DPS1_13_existing_manifests_validate_clean`, asserts at :862).
- Validator: `plugins/dev-sdlc/tools/loam-amend/src/loam_amend/manifest.py`
  — number rule :379-395; baseline rule :399-403; plan_doc_ref/body contract
  :486-513; smoke cap :558-575; `SUPPORTED_SCHEMA_VERSIONS = (1, 2, 3)` :35.
- Commits: see header Predecessors block (all dated via `git show`).
- Conventions: `plugins/dev-sdlc/docs/conventions/plan-docs.md` §1/§3/§4.
