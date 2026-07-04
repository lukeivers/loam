# Release Integration — v1.10.0 (on-demand adversarial review)

**Status:** PREP — persona-side prep up to but excluding the public
tag/push. The public tag + push + GitHub Release remains the owner's
command to run.
**Author:** loam-builder (release worktree `/Users/lukeivers/loam-release-v1.10.0`), 2026-07-03.
**Type:** MINOR over v1.9.1. Single release.
**Class:** END-USER — the named user-visible delta is an on-demand
adversarial review of any artifact, invokable in plain language via the
`adversarial-review` SKILL (§1).
**Ground-truth basis:** git refs (tags + `origin/main` + seal SHAs), not
STATE/roadmap prose (per `feedback_published_state_only_from_git_refs`).

This plan is a **lift**, not a fresh derivation: the capability was
already built, tested, and calibration-proven pos3-local under its own
builder-brief + determinations (`workspace/strategy/research/adversarial-review-capability-2026-07-03/`
in pos3 — `build-plan.md`, `builder-brief.md`, `determinations.md`). The
build-plan's own J1 names *this* migration: "Migration to canonical loam
+ sealing is the ACTIVATION step (separate owner decision). Package
layout mirrors a canonical framework tool so migration is a move, not a
rewrite." This release executes that step.

---

## 1. Objective

Publish loam's standing adversarial-review capability as a MINOR,
v1.10.0, promoting the pos3-local package into canonical loam as a new
sealed component + a discoverable SKILL, landing the on-demand review as
a user-visible outcome.

**Objective sentence (the version's identity):** *"A loam user can get a
genuinely harsh, evidence-bound adversarial review of any artifact, on
demand — point loam at one artifact plus what it is supposed to
accomplish and get back a validated, plain-language review whose harshness
is guaranteed by how the review is constructed, not by asking a model to
be brutal."*

**END-USER class — the named user-visible delta (policy §"END-USER vs
META-FRAMEWORK" gate):** before v1.10.0 a loam user could not ask for an
adversarial review and get one; the `document-trust-review` SKILL covers
the lighter document-domain pass and `loam-reviewer` covers sealed-cycle
conformance, but neither delivers an on-demand, evidence-bound,
survivability review of an arbitrary artifact. After v1.10.0 the user
says "do an adversarial review of X" (or "tear this apart", "red-team
this", "poke holes in this") in plain language and the `adversarial-review`
SKILL drives the standing capability and returns findings in plain
English. That is the specific translation-burden delta: the user brings
WHAT to stress-test; loam owns the HOW (the isolation, the two-phase
falsification, the validation, the verdict).

## 2. What is being promoted (verified from git)

- **Last public release:** v1.9.1 (tag `v1.9.1`, annotated `8666c12`;
  content tip / seal `8f6e49cd`). Highest tag on `origin` AND locally
  (verified equal — no local/unpushed-tag disambiguation halt).
- **`origin/main` == local `main` == `d6d65c2b`** (`git rev-list
  --left-right --count origin/main...main` = `0 0`). The 3 commits in
  `v1.9.1..main` (`d6d65c2b`, `f199fd0f`, `5573e0a0`) are all v1.9.1
  post-publish / sealed-narrative / HARD-smoke bookkeeping — docs-only,
  already public on the branch, release-safe; they ride into this MINOR's
  window.
- **The capability source** lives in the pos3 repo
  (`/Users/lukeivers/pos3`) on branch `feat/adversarial-review-capability`,
  tree end-state at commit `e398789` (6 source commits `7f20b07..e398789`;
  promoted as the tree END-STATE, not cherry-picked — all 6 commits'
  effect including `bc4861a`).

**MINOR (1.9.1 → 1.10.0):** a new backward-compatible capability — a NEW
opt-in out-of-graph component (`framework/adversarial-review/`) + a new
SKILL. Zero BREAKING changes; no existing surface altered. Per the
number-derivation recipe (`docs/release-versioning-policy.md`):
`current_version = v1.9.1` (highest on origin), `candidate_class = MINOR`
⇒ `bump_minor(1.9.1) = 1.10.0`.

## 3. Scope — what lands, what does NOT

**Lands under v1.10.0:**

1. The adversarial-review capability → NEW component
   `framework/adversarial-review/` (0.1.0, OUT of install-graph +
   lockstep this cut, per the D-LOCK precedent — see §5 D-AR-LOCK).
2. The `adversarial-review` SKILL → `plugins/loam-skills/skills/adversarial-review/`
   (discoverable via `_symlink_plugin_skills` at scaffold time — the
   established discoverable-skill home).
3. The 3 already-canonical docs commits in `v1.9.1..main` (v1.9.1
   bookkeeping tail).

**Explicitly EXCLUDED (surfaced + owner-ruled DROP):** the two pos3
channel-hook changes that rode the same feature branch —
notifications-default→Discord (`channel_notify.py` + `owner-channel.json`)
and the `channel_rule_check` leak-kill. Ground truth: canonical loam has
**no `.claude/hooks/` directory**, no `channel_notify.py`, no
`channel_rule_check.py`; its notification path runs through
`primary_persona.cli stop`. These are pos3 RUNTIME operational config with
no canonical PRODUCT home (three-roles kernel: RUNTIME ≠ PRODUCT).
Forcing them in would be a rewrite of primary-persona's notify code, not a
move, and is outside this MINOR's named outcome. They stay live in pos3
where they already are. (Dispatcher ruling, 2026-07-03.)

## 4. The fence (two-component cycle)

A two-component seal, per the established multi-component pattern
(precedent: loam-skills' own seal-test admitted `framework/workspace-bootstrap/`
as a secondary fence at v0.2.0 Cycle 2):

- **`framework/adversarial-review/` — NEW component, first-seal.** Its
  own `tests/test_no_sealed_amendments.py` fences the component dir +
  the SKILL partner path + the universal doc admissions.
- **`plugins/loam-skills/` — EXTEND (sealed).** Adds the
  `skills/adversarial-review/` skill dir. Its seal-test gains
  `framework/adversarial-review/` as an admitted partner prefix (a
  normal partner admission, the pattern that seal-test already documents
  for prior cycles).

No other sealed component's fence moves. `framework/tools/loam-spawn-isolation/`
is READ/NAMED only (the capability composes on the sealed
`spawn_isolated_claude` — it is imported, never edited; the promotion
converts the pos3 out-of-tree absolute reach into an in-tree relative
reach, a change to the NEW component's own `spawn.py`, inside the fence).

**dev-mode-manifest registration: intentionally SKIPPED.** Ground-truth
deviation from the dispatch's "register the component" step, evidence:
the most-recent new components (`local-deploy-tier` v1.9.0,
`deploy-safety-floor` v1.8.0, and 7+ others) are absent from
`plugins/dev-sdlc/dev-mode-manifest.yaml`; no audit test requires a
framework component to be registered (`test_AC_PMR_3` checks a specific
historical realignment, not exhaustive coverage). Registering would touch
`plugins/dev-sdlc/` and widen the fence for zero seal-gate benefit.
Dev-mode source auto-load of the new component is a documented follow-up
candidate, mirroring how `local-deploy-tier` shipped.

## 5. Named decisions

- **D-AR-HOME** — canonical home is `framework/adversarial-review/` (new
  sealed component, not a plugin). *Rec + ruling:* CONFIRM. The package
  was built to mirror a framework component (build-plan J1); framework/
  is where shipped runtime capabilities live.
- **D-AR-LOCK** — the new component ships at `0.1.0`, OUT of
  install-graph + out of the `IN_SCOPE_PYPROJECTS` lockstep set this cut.
  *Rec + ruling:* CONFIRM, per the D-LOCK precedent (every new component
  at v1.7.0/v1.8.0/v1.9.0 rode at 0.1.0 out-of-lockstep at its first
  cut). The 31 existing in-scope pyprojects bump to 1.10.0; the lockstep
  test stays green.
- **D-AR-SKILL** — the SKILL lives in `plugins/loam-skills/skills/`
  (discoverable), making loam-skills a second fence component. *Rec +
  ruling:* CONFIRM. `.claude/skills/` symlinks are scaffold-generated
  (not git-tracked) and only wire `plugins/loam-skills/`; a skill
  anywhere else is undiscoverable in fresh workspaces — which would break
  the named outcome.
- **D-AR-DROP-HOOKS** — the two channel-hook changes are dropped from the
  product release (§3). *Rec + ruling:* CONFIRM.
- **D-AR-TREE-END-STATE** — promote the tree END-STATE (all 6 commits'
  effect incl. `bc4861a`), not a cherry-pick. *Rec + ruling:* CONFIRM.

## 6. AC ladder (family AC.AR.*, scope-descriptive; ODD §2.5)

Lifted verbatim-in-intent from the build-plan §4 (the ladder the shipped
tests already satisfy; test files `tests/test_AC_AR_*.py`). Outcome-altitude
ACs: **AC.AR.1** and **AC.AR.10** (real run).

- **AC.AR.1** (outcome-altitude) — manual entry against one artifact file
  + stated objective returns a structured harsh review (findings pinned
  location+scenario+severity + a verdict), no gate/block; exercised
  through the real entry fn against a real file, no pre-set state.
- **AC.AR.2** — critic seed = artifact + objective + methodology +
  protocol ONLY; excludes parent conversation / author self-assessment /
  provenance.
- **AC.AR.3** — derive-phase seed excludes the artifact bytes; diff-phase
  seed carries derivation + artifact; two-spawn ordering is structural.
- **AC.AR.4** — a finding blocks only after ground-truth validation;
  unvalidated findings quarantine as HYPOTHESIZED (visible,
  severity-capped, non-blocking).
- **AC.AR.5** — the gate verdict BLOCKs by default on validated
  top-severity findings; owner override is an explicit act; a PASS
  missing strongest-surviving-objection + what-couldn't-be-checked is
  malformed and rejected.
- **AC.AR.6** — zero validated substantive findings on a nontrivial
  artifact ⇒ suspicion flag on the REVIEW, not a clean pass.
- **AC.AR.7** — a finding true-of-any-artifact-of-class is flagged
  generic + excluded from the verdict calculus.
- **AC.AR.8** — every critic/judge/validator spawn routes through
  `spawn_isolated_claude`; a hand-rolled bare `claude` argv is refused.
- **AC.AR.9** — the corpus is checked before any pull; a kept doc is
  indexed with citations and reused by a later same-domain review; the
  two seed docs are present.
- **AC.AR.10** (outcome-altitude) — feeding a seeded-flaw artifact reads
  back a computed catch rate; the harness matches critic findings to
  seeded flaws (real variant: an actual isolated critic run reads back a
  nonzero catch rate).
- **AC.AR.11** — the STANDARD floor is non-skippable for a boundary
  artifact; DEEP adds parallel per-axis isolated critics (no shared
  context) + a separate merge judge preserving disagreement; a symmetric
  panel is never the mechanism.
- **AC.AR.12** — with the activation switch OFF (default), the
  gate/automation entry is a no-op; the manual entry works regardless.
- **AC.AR.13** — review output carries no stakeholder-reaction-prediction
  framing; a lint rejects "they will think / how X will receive it"
  framing.

## 7. The experimental auto-BLOCKING gate — SHIPS OFF, with an activation bar

The auto-blocking boundary gate (`adversarial_review.gate.gate_review`,
AC.AR.12) ships **present but OFF/unwired** and is **NOT the named
v1.10.0 outcome.** The released, supported outcome is the MANUAL,
on-demand review + the SKILL only.

**Written activation bar (the gate stays experimental until ALL hold):**

1. **A measured false-positive / precision test on clean artifacts.**
   Recall is proven (D9 seeded-flaw calibration, `calibration/CALIBRATION-RESULT.md`,
   catch 1.0 on the seeded proof). Precision is NOT: there is no measured
   false-positive rate for the gate blocking a genuinely-clean artifact.
   The gate may not be activated to auto-block any real boundary until a
   precision/false-positive measurement on a set of clean artifacts is
   recorded — a gate that blocks good work is worse than no gate.
2. Owner explicit activation (same discipline as frame-kernel activation:
   default-OFF, opt-in, owner-gated).
3. Live boundary-hook wiring authored as its own amendment (the seal/send
   hook is a separate build, not part of this promotion).

Until then AC.AR.12 guarantees the gate is a proven no-op: the manual
path works, the gate blocks nothing.

## 8. Build steps (this is the shape; method is the builder's call)

1. Worktree off `main` (done: `/Users/lukeivers/loam-release-v1.10.0`,
   branch `release/v1.10.0`, at `d6d65c2b`). The dirty
   `feat/memory-redesign-s1a` tree is never touched.
2. This plan-doc + the amend manifest land FIRST (plan-before-code); that
   commit is the seal-fence BASELINE (HEAD~1 of the feat commit).
3. Promote the 42 git-tracked package files → `framework/adversarial-review/`
   (git-tracked-only; runtime cruft excluded). Path-surgery: `spawn.py`
   out-of-tree absolute reach → in-tree relative; README/SKILL pos3 paths
   → canonical. Author the component's `tests/test_no_sealed_amendments.py`
   + `tests/SEAL_COMMIT` sidecar. Promote the SKILL →
   `plugins/loam-skills/skills/adversarial-review/`; admit
   `framework/adversarial-review/` in loam-skills' seal-test. Commit as
   `feat(adversarial-review): …`.
4. `loam amend validate` → `loam amend apply` → `loam amend seal`
   (NEVER `--amend`).
5. Lockstep bump: `docs/ACTIVE_MINOR` 1.9.0 → 1.10.0 + the 31 in-scope
   pyprojects + the meta `--version` literal; run
   `test_AC_PCVR_pyproject_version_lockstep` → GREEN. (Release commits,
   after the seal — outside the seal window.)
6. `docs/CHANGELOG-v1.10.0.md` (de-AI voice; the tag annotation =
   release notes verbatim). `docs/STATE.md` + `docs/release-roadmap.md`
   §2 row + a `no-op` state-migration yaml.
7. HARD cold-smoke per `docs/release-process.md` (cold-clone of the
   release HEAD + editable install + real isolated `claude -p` +
   the AR suite GREEN + ride-along regressions). Writeup with the
   literal `GREEN` token.
8. Annotated LOCAL tag `v1.10.0` (annotation = the changelog). STOP —
   no push, no GitHub Release.

## 9. Halt triggers (in-flight)

- The promotion is not a clean move (path structure won't map, a rewrite
  is required) — HALT + surface, do NOT force. *(Resolved at plan time:
  the AR package + skill map cleanly; the two channel hooks were the
  non-mapping items and are dropped — §3.)*
- The cold-smoke fails, or the pyproject-lockstep test fails and the fix
  is not obvious — HALT.
- The AR suite does not pass on the promoted tree — HALT (a broken
  promotion, not a release-ready seal).
- `v1.9.1..main` contains anything whose release-safety is unclear —
  HALT. *(Resolved: 3 docs-only bookkeeping commits — §2.)*
- Any surrounding-code ODD violation surfaces during the promotion —
  HALT + surface.

## §4 — Acceptance criteria

The in-scope AC ladder (family `AC.AR.*`, scope-descriptive; ODD §2.5),
lifted from the pos3 build-plan §4 — the same ladder the shipped tests
`framework/adversarial-review/tests/test_AC_AR_*.py` satisfy. This is the
heading form the `acs-verified` gate scans; the prose summary in §6 and the
verdicts in §status below carry the same set. Outcome-altitude ACs:
**AC.AR.1** and **AC.AR.10**. The real-calibration smoke test `AR.S`
(`test_AR_S_real_calibration_smoke`) is env-gated and is exercised in the
HARD smoke §4, not a numbered AC.

### AC.AR.1 — manual entry returns a structured harsh review (outcome-altitude)
Manual entry against one artifact file + stated objective returns a
structured harsh review (findings pinned location+scenario+severity + a
verdict), no gate/block; exercised through the real entry fn on a real file.

### AC.AR.2 — critic seed excludes the author's world
Critic seed = artifact + objective + methodology + protocol ONLY; excludes
parent conversation / author self-assessment / provenance.

### AC.AR.3 — two-spawn artifact-blind derivation before diff
Derive-phase seed excludes the artifact bytes; diff-phase seed carries
derivation + artifact; two-spawn ordering is structural.

### AC.AR.4 — validation before a finding can block
A finding blocks only after ground-truth validation; unvalidated findings
quarantine as HYPOTHESIZED (visible, severity-capped, non-blocking).

### AC.AR.5 — block-by-default verdict; malformed-PASS rejected
The gate verdict BLOCKs by default on validated top-severity findings; owner
override is an explicit act; a PASS missing strongest-surviving-objection +
what-couldn't-be-checked is malformed and rejected.

### AC.AR.6 — zero-findings suspicion
Zero validated substantive findings on a nontrivial artifact ⇒ suspicion
flag on the REVIEW, not a clean pass.

### AC.AR.7 — generic-finding lint
A finding true-of-any-artifact-of-class is flagged generic + excluded from
the verdict calculus.

### AC.AR.8 — every spawn via the sealed spawn_isolated_claude
Every critic/judge/validator spawn routes through `spawn_isolated_claude`; a
hand-rolled bare `claude` argv is refused.

### AC.AR.9 — kept + indexed methodology corpus
The corpus is checked before any pull; a kept doc is indexed with citations
and reused by a later same-domain review; the two seed docs are present.

### AC.AR.10 — seeded-flaw self-calibration reads back a catch rate (outcome-altitude)
Feeding a seeded-flaw artifact reads back a computed catch rate; the harness
matches critic findings to seeded flaws (real variant: an actual isolated
critic run reads back a nonzero catch rate).

### AC.AR.11 — STANDARD floor non-skippable; DEEP parallel-axis critics
The STANDARD floor is non-skippable for a boundary artifact; DEEP adds
parallel per-axis isolated critics (no shared context) + a separate merge
judge preserving disagreement; a symmetric panel is never the mechanism.

### AC.AR.12 — the auto-blocking gate is a no-op while OFF (experimental)
With the activation switch OFF (default), the gate/automation entry is a
no-op; the manual entry works regardless. Ships EXPERIMENTAL, activation
barred on a measured false-positive/precision test (§7).

### AC.AR.13 — internal-QA-lens only; no stakeholder-reaction framing
Review output carries no stakeholder-reaction-prediction framing; a lint
rejects "they will think / how X will receive it" framing.

## §status — AC verdicts

**Aggregate: GREEN.** All AC.AR.{1–13} are satisfied by the promoted test
suite on the canonical tree (56 passed / 1 skipped; the 1 skip is the
env-gated `AR.S` real-calibration leg, exercised directly in the HARD smoke
§4). AC.AR.1 + AC.AR.10 are the outcome-altitude ACs (real manual review
entry + real catch-rate read-back). Two-component seal `99a1be9` clean;
post-seal `apply --dry-run` clean. HARD cold-smoke
`docs/experiments/v1-10-0-hard-smoke.md` = **GREEN** (cold clone + real
editable install at 1.10.0 + system binary operational + a real
subscription-mode spawn-isolated `claude -p` review leg returning output +
touched-component and ride-along regressions clean). Public steps NOT run.

| AC | Verdict | Evidence |
|---|---|---|
| AC.AR.1 | **GREEN** | `test_AC_AR_1_manual_entry_returns_review` (outcome-altitude) |
| AC.AR.2 | **GREEN** | `test_AC_AR_2_isolation_seed_excludes_author_world` |
| AC.AR.3 | **GREEN** | `test_AC_AR_3_derive_before_read_is_artifact_blind` |
| AC.AR.4 | **GREEN** | `test_AC_AR_4_validation_before_surfacing` |
| AC.AR.5 | **GREEN** | `test_AC_AR_5_verdict_blocks_and_pass_names_residual` |
| AC.AR.6 | **GREEN** | `test_AC_AR_6_zero_findings_suspicion` |
| AC.AR.7 | **GREEN** | `test_AC_AR_7_generic_finding_lint` |
| AC.AR.8 | **GREEN** | `test_AC_AR_8_spawn_isolation` |
| AC.AR.9 | **GREEN** | `test_AC_AR_9_corpus_keep_and_reuse` |
| AC.AR.10 | **GREEN** | `test_AC_AR_10_seeded_flaw_calibration` (outcome-altitude) |
| AC.AR.11 | **GREEN** | `test_AC_AR_11_depth_tiers` |
| AC.AR.12 | **GREEN** | `test_AC_AR_12_inactive_gate_default_off` |
| AC.AR.13 | **GREEN** | `test_AC_AR_13_internal_lens_only` |
