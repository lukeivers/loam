# Release Integration — v1.13.0 (Tilth operational-backplane integration — eight workstreams → one installable assembly)

**Version:** v1.13.0 (MINOR over published v1.12.0). **Class:** MINOR.
**WD:** `/Users/lukeivers/loam` (canonical single-writer this cycle).
**Status target:** SEALED-LOCAL + HARD-smoke-GREEN + `loam release v1.13.0 --dry-run` all-gates-GREEN, then STOP. **The public tag + push + GitHub Release is the owner's command to run — NOT pushed by this cycle** (`feedback_no_public_action_during_build`).
**Authority:** `docs/release-process.md` (runbook) + `docs/release-versioning-policy.md` (SemVer commitment) + this doc's §4/§13. Feature sub-plan: `workspace/.scratch/claude-output/backplane-integration-plan-DRAFT.md` (the integration plan-doc, AC.BPI.* ladder).

---

## 1. Objective

**loam assembles its eight built-but-non-coexisting operational-backplane workstreams into one installable release where — from a clean cwd — every backplane package imports, the two sealed fences (cost-governance, adversarial-review) stay intact, and the fleet page renders live over a real agent-run collection (the fleet-collector over real handsoff-loop run records + the observability-aggregator query + the per-project-pm decision queue). That end-state is the real "fleet done." Then it ships as its own single MINOR cut over v1.12.0.**

The objective sentence DESCRIBES the whole cut; it does not gate a split. Per the deterministic-cut rule (§3), a release cut is all unreleased seals at release time minus only explicitly owner-held items; "how many versions / which grouping" is never a decision to surface.

**Class — MINOR (per `docs/release-versioning-policy.md`).** New backwards-compatible capability: five NEW shipped runtime components + two additive sealed-component amendments. Zero BREAKING (`loam release preflight v1.13.0` → `class=MINOR expected=v1.13.0 published=v1.12.0, breaking-markers=no`). Named user-visible delta: a loam operator can now regenerate a live agent-fleet page over their real run records and receive weekly cost/cap artifacts — capability that did not exist before this cut.

---

## 2. What is being integrated (Tier-0 verified topology)

All eight workstreams are FOUR already-linear stacks; merging the four stack TIPS new-components-first / sealed-last = all eight, with ZERO textual conflict (disjoint `framework/<pkg>` dirs). Base = current `main` `2fb0906d` (after v1.12.0's post-publish doc backfill).

| Stack | Tip branch | Tip / seal SHA | Carries | Packages | Kind |
|---|---|---|---|---|---|
| S1 | `feat/ws-a3-fleet-page` | `45bb06d3` | B1 → A2 → A3 | file-lease-registry, fleet-collector, fleet-page | new components |
| S2 | `feat/ws-a5-weekly-cost-rollup` | `c688d49a` | A1 → A5 | weekly-cap-alert, weekly-cost-rollup | new components |
| S3 | `feat/ws-a4-cost-ceiling` | `e1ab5563` | (standalone) | cost-governance cap-% ceiling | SEALED amend |
| S4 | `feat/ws-d2-codex-critic-leg` | `5333874b` | D1 (`a4c08928`) → D2 | adversarial-review model-role registry + Codex leg | SEALED amend |

The D1→D2 seal dependency is already baked into the S4 branch history (D2's seal baseline IS D1's seal) — no independent-reseal reconciliation. The four stacks touch disjoint directories, so no single stack-seal dominates the others; the tag target is the integration content tip (§13 AC.REL.7).

These feature ACs (`AC.BPI.*`) are sealed + verified in the feature sub-plan; they are DISTINCT from this doc's `AC.REL.*` release-gate ladder (§4/§13).

---

## 3. Version decision — v1.13.0, single MINOR release (SemVer derivation)

```
current_published (highest tag on ORIGIN)  = v1.12.0
  [git ls-remote --tags origin -> refs/tags/v1.12.0 at commit 69a345ba; tag object 1ed1d20e]
HEAD local highest tag                      = v1.12.0   (== origin; no local-but-unpushed higher tag; recipe unambiguous)
breaking markers in v1.12.0..HEAD           = NONE
new backwards-compatible capability present  = YES (five new framework components + two additive sealed amends)
=> class = MINOR (not MAJOR: zero breaking; not PATCH: new capability)
=> bump_minor(v1.12.0) = v1.13.0, ONE release.
```

Tier-0 corroboration: `loam release preflight v1.13.0` reports `computed cut: class=MINOR expected=v1.13.0 (published=v1.12.0, 30 unreleased commit(s); breaking-markers=no)` and the dry-run's `deterministic-cut` gate confirms `v1.13.0 == computed v1.13.0`. This cut was BLOCKED at dry-run while origin sat at v1.11.0 (the deterministic-cut gate computed v1.12.0, taking all unreleased seals as one cut); it became reachable ONLY after the owner published v1.12.0 to origin, which is why this is its own cut and not batched with the per-session-resume work — the machinery's own contract enforced the separation, not a discretionary grouping choice.

---

## 4. Build + release steps

1. **Re-derive onto current main.** Merge current `main` `2fb0906d` (v1.12.0 post-publish doc backfill — disjoint from framework code) into `integration/backplane`; zero conflict; re-verify seal-tests + clean-cwd import of all eight. Integration content tip = `1e42e028`.
2. **Lockstep version bump.** `docs/ACTIVE_MINOR` 1.12.0 → 1.13.0; the 31 existing in-scope `pyproject.toml` version fields + the `loam_cli __version__` literal (`loam --version`) → 1.13.0; PLUS the five new backplane components (0.0.0 → 1.13.0) + adversarial-review (0.1.0 → 1.13.0) FOLDED INTO the PCVR `IN_SCOPE` allowlist (now 37). PLAIN commit `ebbfec9e` landing AFTER the content tip, OUTSIDE every fence window (each sealed component's seal-test stays GREEN post-bump; `test_AC_PCVR_pyproject_version_lockstep` GREEN).
3. **State-migration doc.** `docs/state-migrations/v1-13-0-operational-backplane-integration.migration.yaml` — declared `no-op` (additive read-only collectors + output artifacts; additive sealed amends; no user-state schema change).
4. **HARD smoke (per-minor gate).** `docs/experiments/v1-13-0-hard-smoke.md` — cold clone/cold install of the release content tip + a REAL spawn-isolated `claude -p` exercise + the outcome-altitude cross-package fleet-page render at the production entry-point + touched-component regression + the gate-7 `which loam` / `loam --help` evidence; literal `GREEN` verdict token.
5. **Backfill state.** `docs/STATE.md` SHIPPED-LOCAL change-log entry + `docs/release-roadmap.md` §2 seal-row (the dominance resolver picks the single dominating content-tip seal `1e42e028`) + §3 Active-version entry.
6. **Dogfood + dry-run.** `loam release v1.13.0 --dry-run`; confirm ALL gates GREEN, including `seal-dominance` (multi-seal `dominates` — `1e42e028` dominates the four parallel stack seals) + `deterministic-cut` (recomputes MINOR → v1.13.0). STOP before push.

## 5. Pre-publish gates (enforced by `loam release`)

The gates `run_all` runs per `gates.py`: hard-smoke, acs-verified, state-shipped, clean-tree, branch-main, seal-reachable, migration-declared, substrate-audit, boundary-respected, **seal-dominance**, **deterministic-cut**. `--dry-run` runs the full set without acting. Publish (tag/push/`gh release`) is the owner-authorized action, never this cycle's.

---

## §4 — Acceptance criteria

These `AC.REL.*` criteria are the release-integration gate ladder; the `acs-verified` gate reads their §13 §status verdicts. They are DISTINCT from the per-cycle feature ACs (`AC.BPI.*`, `AC.CAPC`, `AC.MRR`, `AC.PAGE`, `AC.RUP`, `AC.CAP`), sealed + verified in the feature sub-plan.

### AC.REL.1 — Plan-doc authored
This doc exists at a version-slug-resolvable path (`docs/plans/release-integration-v1-13-0.md`, resolved by the release-side fallback in `gates.py`) with §1 objective + §2 inventory + §3 SemVer derivation + §4 ACs + §13 §status, so the `acs-verified` + `hard-smoke` gates resolve it with NO `--plan-doc` flag.

### AC.REL.2 — Eight workstreams integrated on main
The four stack tips (`45bb06d3` / `c688d49a` / `e1ab5563` / `5333874b`, the last carrying D1 `a4c08928`) are merged onto the integration branch and fast-forwarded to `main`; every stack seal is reachable from HEAD; the four merges produced ZERO textual conflict (disjoint framework package dirs).

### AC.REL.3 — Lockstep version bump (MINOR discipline)
`docs/ACTIVE_MINOR` advances 1.12.0 → 1.13.0; the 31 existing in-scope `pyproject.toml` version fields + the meta `loam --version` literal fold to 1.13.0; the five new backplane components + adversarial-review are folded into the PCVR `IN_SCOPE` allowlist (now 37) and bumped to 1.13.0; `test_AC_PCVR_pyproject_version_lockstep` stays GREEN. The two excluded 0.0.0 measurement harnesses stay at 0.0.0.

### AC.REL.4 — HARD smoke GREEN (the per-minor gate)
`docs/experiments/v1-13-0-hard-smoke.md` authored; REAL cold clone of the release content tip + REAL editable install from `install-from-source.txt` with no Anthropic API key + spawn-isolated `claude -p` (scrubbed `ANTHROPIC_API_KEY` / bot tokens, `--strict-mcp-config`) + the outcome-altitude cross-package fleet-page render (AC.REL.S) + touched-component regression + the gate-7 `which loam` / `loam --help` evidence; the writeup carries the `GREEN` aggregate-verdict token.

### AC.REL.5 — Touched component suites GREEN (cold install)
The seven touched-component suites — file-lease-registry, fleet-collector, fleet-page, weekly-cap-alert, weekly-cost-rollup, cost-governance, adversarial-review — pass in the cold-installed release tree, evidenced in the HARD smoke writeup (218 passed / 2 skipped, run per-component).

### AC.REL.6 — STATE.md backfilled (pre-publish SHIPPED LOCAL)
`docs/STATE.md` carries a `**v1.13.0 MINOR SHIPPED LOCAL**` change-log entry naming the objective, the class, the eight workstreams + the four stack seals, the substrate edit, the lockstep bump, the migration verdict, and the HARD smoke path.

### AC.REL.7 — release-roadmap.md backfilled + dominating tag target
`docs/release-roadmap.md` §2 carries a v1.13.0 row whose right column names the four parallel stack seals + the integration content tip `1e42e028`; the dominance resolver picks `1e42e028` as the unique dominator (it has every stack seal as an ancestor; the stacks are parallel so no stack-seal dominates), reachable from HEAD (read by gate `seal-reachable`); §3 Active-version carries a SHIPPED-LOCAL entry.

### AC.REL.8 — Migration declared
`docs/state-migrations/v1-13-0-operational-backplane-integration.migration.yaml` exists and explicitly declares `version: v1.13.0` + `operation: no-op` (declared, not assumed).

### AC.REL.9 — Deterministic-cut + seal-dominance dogfood GREEN
`loam release v1.13.0 --dry-run` runs the release CLI's gates against this cut: `check_deterministic_cut` recomputes the cut as MINOR → v1.13.0 (published=v1.12.0) matching the target, and `check_seal_dominance` resolves `1e42e028` as the dominator of the multi-seal §2 row (exercising the real `dominates` path over parallel stacks, not the vacuous single-seal path). Both GREEN.

### AC.REL.S — Outcome-altitude (production entry-points, no pre-set state)
Two production entry-points are exercised with no pre-set release state: (1) the `fleet-page` production entry-point (`generate_page`) writes real HTML over a REAL cross-package path — an actual `fleet-collector` run against on-disk handsoff-loop run records + the observability-aggregator query + the per-project-pm decision queue — from a clean cwd (evidenced in the HARD smoke writeup + the feature sub-plan AC.BPI.5); and (2) `loam release v1.13.0 --dry-run` runs the real multi-gate release CLI and reports every structural gate GREEN.

---

## §13 — §status (gate verdict matrix)

The `loam release v1.13.0 --dry-run` `acs-verified` gate reads these verdicts. A RED here blocks the dry-run's `acs-verified` gate.

| AC | Verdict | Evidence |
|---|---|---|
| AC.REL.1 | GREEN | this doc at `docs/plans/release-integration-v1-13-0.md` (resolved by the release-side fallback in `gates.py`) |
| AC.REL.2 | GREEN | four stack seals HEAD-reachable (`45bb06d3` / `c688d49a` / `e1ab5563` / `5333874b`, carrying `a4c08928`); four `--no-ff` merges, zero textual conflict; fast-forwarded to `main` |
| AC.REL.3 | GREEN | lockstep bump `ebbfec9e` (ACTIVE_MINOR 1.13.0 + 31 in-scope pyprojects + `loam --version`→1.13.0 + six backplane components folded in, IN_SCOPE now 37); `test_AC_PCVR_pyproject_version_lockstep` 5 passed |
| AC.REL.4 | GREEN | `docs/experiments/v1-13-0-hard-smoke.md` carries the `GREEN` token + gate-7 evidence |
| AC.REL.5 | GREEN | seven touched-component suites GREEN per-component: 218 passed / 2 skipped (HARD smoke §regression) |
| AC.REL.6 | GREEN | `docs/STATE.md` `**v1.13.0 MINOR SHIPPED LOCAL**` change-log entry |
| AC.REL.7 | GREEN | `docs/release-roadmap.md` §2 row; `resolve_tag_target` → `1e42e028` dominates the parallel stack seals (reason `dominates`), reachable from HEAD; §3 SHIPPED-LOCAL entry |
| AC.REL.8 | GREEN | `docs/state-migrations/v1-13-0-operational-backplane-integration.migration.yaml` (`operation: no-op`) |
| AC.REL.9 | GREEN | `loam release v1.13.0 --dry-run`: `deterministic-cut` = MINOR → v1.13.0 (published=v1.12.0); `seal-dominance` resolves `1e42e028` dominating the four parallel stack seals (`dominates`) |
| AC.REL.S | GREEN | HARD smoke: real cross-package fleet-page render over real run records at the production entry-point (feature sub-plan AC.BPI.5) + `loam release v1.13.0 --dry-run` all structural gates GREEN |

## §14 — cycle SHA register (backfilled at cycle close)

Release plan-doc + migration + STATE/roadmap: this release-prep commit. Lockstep bump: `ebbfec9e`. Integration:

- Integration content tip / **release tag target — DOMINATING seal `1e42e028`** (merge of current `main` `2fb0906d` into the backplane assembly; the unique row-seal that has every stack-tip seal — `45bb06d3` / `c688d49a` / `e1ab5563` / `5333874b` — as an ancestor). Pre-main-merge assembly tip `766d67b0` (four stack merges + the two substrate commits).
- Stack S1 — a3-fleet-page (file-lease-registry + fleet-collector + fleet-page): seal `45bb06d3`.
- Stack S2 — a5-weekly-cost-rollup (weekly-cap-alert + weekly-cost-rollup): seal `c688d49a`.
- Stack S3 — a4-cost-ceiling (cost-governance cap-% ceiling): seal `e1ab5563`.
- Stack S4 — d2-codex-critic-leg (adversarial-review model-role registry + Codex leg): seal `5333874b` (contains d1 model-role-registry seal `a4c08928`).
- Substrate commits: `f17cec1e` (five new packages) + `766d67b0` (adversarial-review pre-existing-gap line) in `install-from-source.txt`.
- Per the v1.10.0 pattern, the lockstep bump `ebbfec9e` lands on `main` AFTER the tag target — the tag marks the sealed content tip; `origin/main` HEAD carries the bump.
