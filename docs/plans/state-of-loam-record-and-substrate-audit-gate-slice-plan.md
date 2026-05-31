# Plan — STATE-OF-LOAM operative-reality record + substrate-audit gate (N2 / R-1 + R-3)

**Status:** sub-plan-doc (PLAN ONLY — no implementation code authored) · **HALT for owner review before build.**
**Working directory:** `/Users/lukeivers/loam` (branch: build-time call; a clean slice branch off the BASELINE seal — `feedback_dispatch_cd_literal_first_action` applies: the dispatch's literal first action is `cd /Users/lukeivers/loam && pwd`).
**Parent plan / roadmap:** `docs/plans/loam-roadmap.md` item **N2** (§4, line 81; §7 top-3 #2). Promoted to NEXT-UP, parallel track to N1 (§4 sequencing note, line 85).
**Design source:** `docs/reviews/loam-evolution-reasoning-acceleration.md` — **R-1** (the living current-reality record, Part 3 line 217 + Part 4 #1 line 303) and **R-3** (the substrate-assumption audit gate, line 251 + Part 4 #3 line 323). These two "compose into one mechanism" per the review's own synthesis (line 333): *R-1 holds current reality, R-3 forces every design to check it before assuming.*
**Owner directive bound:** `feedback_reconcile_checks_against_memory.md` (Telegram 13311, 2026-05-31) — *compare every ground-truth check to what memory claims; reconcile divergences; so manual re-verification shrinks.* This slice is that directive made STRUCTURAL.
**Predecessors (load-bearing prior seals + artefacts):**
- The live state to PROBE (DONE — the thing that makes N2 unblocked off FBM-LIVE): the FBM live hook (`pos3/.claude/settings.json` gated `user-prompt-submit`), seals `7e9af6b`/`81c7780`/`fb26be2`/`c82131e`/`7dcb95b` (roadmap §2).
- The git-ref-graph verification discipline this slice mechanizes: `feedback_published_state_only_from_git_refs.md` (built/sealed/merged/published verified ONLY from refs — `git merge-base --is-ancestor`, `git tag --contains`, `git branch --contains`; artefact prose is Tier-2 stale-prone).
- The release-gate framework to compose the gate ON (Lens 1, do NOT reinvent): `framework/tools/loam/src/loam_cli/release/gates.py` — the seven-gate `loam release` framework with the `GateResult`/`ALL_GATES` shape (line 638-760 is gate 7 `check_migration_declared`, the closest structural sibling).
- The per-component seal sidecars the probe reads: `framework/<component>/seals/SEAL_COMMIT.<slug>` (carry `BASELINE`/`SEAL_COMMIT` pins — the per-component "is this sealed and at what SHA" anchor).
- The STALE artefacts this mechanism exists to catch (the planted-divergence fixture's real-world referent): `loam-vnext-build-plan.md` §6 + `fbm-state-and-memory-roadmap-2026-05-29.md` Q1, both still calling FBM "dark" while refs say live (roadmap §6 R-1, line 149).
- The structural-enforcement parent that licenses gate-tier (not memory-tier) for this class: `feedback_structural_enforcement_on_recurrence.md` (recurrence-despite-corpus → hook, not another rule).
**BASELINE candidate:** `ea2f3a0` (current `main` HEAD, carrying FBM + migration-engine + roadmap). Confirm at build time against the actual branch-point seal.
**Status-file target:** `docs/STATE.md` amendment row at seal; `docs/plans/loam-roadmap.md` N2 → DONE on ship.
**Quality bar:** the ★ outcome-altitude AC drives a REAL planted divergence (a doc claiming "dark" for a live component) through the REAL gate entry-point and proves it is CAUGHT — not a unit test of an inner status function. This is today's lesson literally encoded (`feedback_test_outcome_altitude_required`): today's miss was caught by hand-reconciling against refs; this slice proves the mechanism catches it automatically, at the real entry-point.

---

## §1 Summary / TL;DR

**What ships:** the standing mechanism that would have caught today's built-≠-live drift automatically. Two composed parts, ONE mechanism:

1. **The STATE-OF-LOAM operative-reality record (R-1)** — a single, terse, always-loaded record of *what loam currently IS (concept) and currently RUNS (substrate)*: which components are built/sealed/merged, which hooks are wired-live vs dark, which backends are live vs design-aspirational. It is **DERIVED from ground truth on demand** (git ref graph + per-component seal sidecars + live runtime config), **never hand-maintained prose** — because hand-maintained prose is exactly the thing that drifted (the v-next plan + FBM roadmap both call FBM "dark" while refs say live). The derivation IS the dogfood of the owner directive: derive state from ground truth, so the record cannot lie.

2. **The substrate-audit gate (R-3)** — a check that fires on demand and at plan-author/release time, COMPARES claimed status (in docs, plan-docs, tasks, or a draft's "rides existing X / X already does Y" claims) against the derived record, and on a DIVERGENCE surfaces it (flags the specific claim + the ground-truth contradiction). It is the enforcement that makes R-1 load-bearing: R-1 supplies the truth, R-3 forces designs to consult it.

**How it SUBSUMES the memory↔reality reconciliation idea (one mechanism, two entry points):** the roadmap §6 names "memory↔reality reconciliation mechanism" as REDUNDANT-with-N2 and recommends folding (line 192). This plan folds it. The same divergence-detector serves two entry points: (a) the **build-program's built-≠-live drift** (a doc/plan claims a component is dark when refs say live — today's case), and (b) the **FBM stored-episode-vs-truth drift** (a stored memory claim contradicts current ground truth — the owner-directive's general case). Both are "a stored claim trusted over live truth"; both resolve by deriving truth from ground truth and surfacing the divergence. ONE detector, two callers.

**AC families:** `AC.SOL-RECORD.*` (the record is derived-not-prose, machine-backed, cannot silently drift), `AC.SOL-PROBE.*` (the liveness probe correctly classifies built/sealed/merged/wired/dark from ground truth), `AC.SOL-GATE.*` (the audit gate detects + surfaces a claim-vs-reality divergence), `AC.SOL-RECONCILE.*` (the subsumption: the SAME detector serves the FBM stored-vs-truth entry point), `AC.SOL-PLANTED.*` (★ outcome-altitude: a REAL planted "dark"-for-live divergence is CAUGHT at the real entry-point).

**Key decisions baked (confident, tight scope):** compose the gate ON the existing `loam release` `ALL_GATES` framework (NOT a new CI); derive the record from the git ref graph + seal sidecars + live runtime config (NOT hand-maintained prose); the record is GENERATED on demand from ground truth and cached, never authored; reuse the ref-ancestry checks already specified in `feedback_published_state_only_from_git_refs.md` (`merge-base --is-ancestor` / `tag --contains` / `branch --contains`) rather than inventing a status scheme; the ★ AC drives the real entry-point against a planted fixture.

**Forks needing an owner ruling (low confidence — see §3):** (D1) the record's REFRESH model — generated-fresh-every-read vs cached-with-staleness-probe vs seal-hook-updated; (D2) the gate's FIRE POINT — plan-author hook (PreToolUse on plan-doc writes) vs a `loam audit` verb vs the release-gate set vs all three; (D3) the divergence VERB on a catch — surface-only vs surface-and-block vs surface-flag-heal; (D4) the claim-extraction surface — structured status-fields only vs NL "rides existing X" scanning vs both.

**F2 on scope realism:** scope-realistically a SINGLE dispatch IF D1–D4 are ruled before build. The mechanism is small: a probe (a handful of ground-truth queries, most already specified in the git-refs memory), a record-renderer over the probe output, a divergence-comparator, and ONE gate function mirroring the existing seven (`gates.py` is the template). The risk is NOT size — it is the claim-extraction surface (D4): NL-scanning "rides existing X" claims is unbounded; structured-field comparison is bounded. Recommendation: rule D1–D4 at this review, scope the first slice to the bounded surface (structured fields + the planted-divergence fixture), defer NL-scanning to a fast-follow if D4 lands on "both." Decomposition into sub-slices is NOT warranted yet (no sub-task has a tighter AC than the parent — Lens 5 stopping criterion) UNLESS D4 lands on "both," in which case the NL-scan is a clean second slice with its own tighter AC.

---

## §2 Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| The liveness probe (ground-truth queries → classification) | **Framework** — new module; builder picks the component home (a `loam_cli` subcommand home is the natural fit, sibling to `release/`). | Identical for every loam instance; reads framework + repo ground truth; ships + versions with loam. |
| The STATE-OF-LOAM record (the rendered output) | **Generated artefact, not tracked prose.** A predictable path (e.g. `.loam/state-of-loam.md` or a `loam state` stdout) regenerated from the probe; NOT a hand-edited doc under `docs/`. | The whole point is it CANNOT be hand-maintained — a tracked editable doc would drift exactly like the v-next plan did. Derive-on-demand defeats drift by construction. |
| The substrate-audit gate | **Compose on `framework/tools/loam/src/loam_cli/release/gates.py`** as a new entry in `ALL_GATES` (release-time arm) AND/OR a plan-author hook (D2 rules which arms). | Lens 1 / leverage-loam-first: the seven-gate `loam release` framework IS the repo's gate surface; gate 7 (`check_migration_declared`) is the exact structural template. There is NO `.github/workflows/` to add CI to (verified in the migration-engine plan). |
| The claim-extraction (what gets compared) | **Framework** code; reads docs/plan-docs/tasks as INPUT. | The comparator is framework; the docs it audits are the input corpus. |
| The FBM stored-vs-truth entry point (the subsumption) | **The SAME comparator, a second caller** — invoked over a stored FBM claim instead of a doc claim. NOT a second mechanism. | Roadmap §6 redundancy note (line 192): build as ONE mechanism, two entry points. Avoids the two-parallel-tracks waste the roadmap explicitly flags. |

---

## §3 Halt-and-surface BEFORE build — the four forks (low confidence; owner rules)

Each carries my recommendation. **Recommendation IS the decision for confident items; these four are the genuine forks where reasonable people weigh signals differently, so they are surfaced (Lens 6 step 4 / M5).**

### D1 — The record's REFRESH model: how does STATE-OF-LOAM stay non-stale?
- **Option A — generated-fresh-on-every-read.** No stored record at all; `loam state` (or the always-loaded context hook) runs the probe live each time. Cannot drift by construction (there is nothing persisted to go stale). Cost: the probe runs every read (ref queries are cheap — sub-second).
- **Option B — cached record + a staleness probe.** Persist the rendered record; a cheap check (HEAD SHA changed? a seal sidecar mtime moved?) decides whether to regenerate. Faster reads; adds a staleness-detection surface that itself can be wrong.
- **Option C — seal-hook-updated.** Every `loam amend seal` regenerates the record. Drift-free at seal boundaries but blind to out-of-band changes (a hook wired by hand in `settings.json` without a seal).
- **★ Recommendation: A — generated-fresh-on-every-read, with the probe kept cheap.** The entire failure class this slice fixes is "a persisted record drifted from reality." A persisted record (B/C) reintroduces exactly that surface; the staleness-probe (B) and the seal-hook (C) are themselves drift-prone (C is blind to the hand-wired-hook case — which is precisely how `settings.json` hooks were wrongly assumed wired in IP-7). Generate-fresh has no stored state to lie. The probe is cheap (a few `git` calls + a `settings.json` read). **Signals:** blast-radius (a stale record is the exact failure being fixed — favor the option with no persisted state to go stale), information-asymmetry (ground truth is the only authority — read it live), cost (ref queries are sub-second — the perf argument for caching is weak). Owner rules; B is the fallback ONLY if the probe proves too slow to run per-read in practice.

### D2 — The gate's FIRE POINT: when does the audit run?
- **Option A — plan-author hook (PreToolUse on plan-doc / status-doc writes).** Catches the divergence at AUTHORING time — the earliest point, before the false claim is committed. This is where today's drift entered (a plan-doc authored "dark" while refs said live). Matches R-3's literal spec (line 256: "a plan-author checklist hook that scans the draft").
- **Option B — a `loam audit` verb** run on demand / in CI. Catches divergence when explicitly invoked; not automatic.
- **Option C — the release-gate set.** Catches divergence at PUBLISH time — the last line of defense, before a stale status ships in a release.
- **Option D — all three** (the hook + the verb + the gate share ONE comparator).
- **★ Recommendation: D — all three arms over ONE shared comparator, but build the `loam audit` verb FIRST (it is the testable real entry-point the ★ AC needs), then wire the release-gate arm, and declare the plan-author PreToolUse hook a fast-follow.** The verb is the bounded, independently-testable core; the gate arm is a thin `ALL_GATES` entry over the same comparator (cheap, the migration-engine slice just did exactly this); the plan-author hook is the highest-value arm (catches drift at authoring) but it touches the live hook chain + is owner-class to turn ON (it changes authoring behavior), so it composes cleanly LATER on the verb without rework. **Signals:** scope↔confidence (the verb + gate-arm are high-confidence + independently testable; the always-on authoring hook is a behavior change — looser, owner-gated), the structural-enforcement parent (R-3's whole point is gate-tier not memory-tier — so at least one ENFORCING arm, not verb-only), non-disruption (the authoring hook is the one that changes the persona's day-to-day — gate it). Owner rules whether the authoring hook rides this slice or fast-follows, and whether to turn the enforcing arms ON immediately or dark-launch (surface-only) first.

### D3 — The divergence VERB on a catch: what does the gate DO when it finds drift?
- **Option A — surface-only.** Flag the specific claim + the ground-truth contradiction; do not block, do not edit. The human/persona decides.
- **Option B — surface-and-block.** A divergence at the release-gate arm returns RED (publish cannot proceed until the stale claim is corrected); the plan-author arm warns/blocks the write. Mirrors the seven hard gates.
- **Option C — surface-flag-heal.** Additionally auto-CORRECT the stale doc (rewrite "dark" → "live" with a dated provenance note) — the full reconcile loop the owner directive describes ("see if we can address it").
- **★ Recommendation: per-arm — A (surface-only) for the plan-author hook at first; B (surface-and-block, hard) for the release-gate arm; C (heal) DEFERRED to a fast-follow.** Rationale: the release-gate is the ship-blocking line of defense and should be hard like its six siblings (a stale "dark" claim shipping in a release is the exact failure — block it). The authoring hook should surface-only at first (blocking every authoring write on a divergence is disruptive before the probe's precision is proven — dark-launch the precision first). Auto-HEAL (C) is the owner directive's aspiration but is the highest-risk verb (an auto-rewrite of a doc on a false-positive divergence corrupts the doc) — defer until the comparator's false-positive rate is measured. **Signals:** blast-radius (auto-heal on a false positive corrupts a canonical doc — highest risk, defer; block-on-ship is contained — the author just corrects the claim), reversibility (surface + block are trivially reversible; an auto-edit is not), the owner directive's intent (it wants reconcile-and-heal — so C is the destination, just not the first step). Owner rules; if the owner wants the full heal loop now, C rides behind a reversibility-primitive envelope (surface-don't-silently-overwrite).

### D4 — The claim-extraction surface: WHAT does the gate compare?
- **Option A — structured status-fields only.** Compare machine-readable status (a doc's front-matter `status:` field, a roadmap's evidence cells, a task's state, a manifest's `baseline:`) against the derived record. Bounded, precise, low false-positive.
- **Option B — NL "rides existing X / X already does Y" scanning.** Scan free prose for substrate-existence claims (R-3's literal spec, line 256). Catches IP-7's "rides loam's existing hook chain" class — but is unbounded + false-positive-prone (NL claim-extraction is fuzzy).
- **Option C — both** (structured first, NL as a second pass with a lower-confidence flag).
- **★ Recommendation: A for THIS slice (structured fields + the planted-divergence fixture is itself a structured-status case — a doc's "dark" claim for a live component), with B declared a clean SECOND SLICE if the owner wants the NL surface.** The planted-divergence the ★ AC requires (a doc claiming "dark" for a live component) is satisfiable on the structured surface — today's actual drift was a status claim, not buried prose. Structured-field comparison is bounded + testable + low-false-positive; NL scanning is the open-ended, false-positive-prone surface that would make the gate noisy and eroded-trust before it earns its keep. If the owner wants the NL "rides existing X" catch (it has real value — IP-7), it is a clean follow-on slice with its OWN tighter AC (Lens 5 — decompose only when the sub-task tightens scope). **Signals:** scope↔confidence (high confidence the structured surface covers today's failure + is bounded — tighten; low confidence NL-scan precision is acceptable yet — loosen/defer), false-positive cost (a noisy gate gets ignored — the worst outcome for an enforcement mechanism), the ★ AC's needs (the planted fixture is a structured-status case). Owner rules whether to commit the NL second slice now or wait for a driver.

---

## §4 Spec-objective placement

- Binds to roadmap **N2** (§4, line 81): "a single always-loaded 'what loam currently IS + currently RUNS' record … machine-backed by a cheap liveness probe, read first by every design step; plus a plan-author gate that blocks any 'rides existing X' claim until verified against it." Ladders to the roadmap's value spine (§1): every item ladders to the **prime directive — per-user-tuned translation + protection** (`docs/design/loam-doctrine.md`; `feedback_loam_prime_directive_user_tuned_translation.md`).
- The PROTECTION half of the prime directive is the direct binding: this mechanism is a guard against a named AI failure mode (reasoning against a substrate that isn't there / trusting a stale stored claim over live truth — patterns P-B + P-D in the reasoning-acceleration review). It is the substrate-liveness sibling of the failure-mode-guard matrix (FLAGSHIP pillar 2).
- Ladders to `docs/VALUE_PROPOSITION.md` AC.PO (the prime objective's two tests): a translator that reasons against a false model of its own substrate cannot reduce the user→machine translation burden reliably — the record is the precondition for trustworthy translation (the owner directive's "so manual re-checking shrinks" is the operational form).

---

## §5 Acceptance criteria

AC IDs are scope-descriptive (`feedback_scope_descriptive_ac_ids`), not version-packed. Each is outcome-shape. **Method-in-AC test passed:** every AC below can be satisfied by a method other than the one I have in mind (the builder may structure the probe queries, the record format, the comparator, and the gate wiring differently) — so they pin OUTCOME, not method.

### AC.SOL-RECORD.* — the record is derived from ground truth, never hand-maintained prose
- **AC.SOL-RECORD.1 (derived-not-authored)** — The STATE-OF-LOAM record is GENERATED from ground truth (refs + seal sidecars + live runtime config); there is no hand-editable prose source that the record is copied from. Editing the record by hand has no effect on the next generation (it regenerates from ground truth). *(Outcome: the record cannot drift from reality the way the v-next plan + FBM roadmap drifted — drift is impossible by construction.)*
- **AC.SOL-RECORD.2 (reflects a real change)** — When a component's ground truth changes (a new seal lands / a hook is wired in `settings.json` / a backend goes live), the regenerated record reflects the new state without any manual edit. *(Outcome: the record tracks reality automatically — the live-state-changed case.)*
- **AC.SOL-RECORD.3 (terse + always-loadable)** — The record is small enough to be read first by every design/plan step (a bounded summary, not a full dump). *(Outcome: it is operationally usable as the always-loaded "what loam currently is" surface R-1 specifies, not an unwieldy report.)*

### AC.SOL-PROBE.* — the liveness probe classifies state correctly from ground truth
- **AC.SOL-PROBE.1 (built/sealed/merged from refs)** — For a given component, the probe classifies its build/seal/merge status from the git ref graph (`merge-base --is-ancestor` / `tag --contains` / the seal sidecar's pinned SHA), NOT from any artefact's prose status line. *(Outcome: status is Tier-0 ground-truth-derived — `feedback_published_state_only_from_git_refs` made mechanical.)*
- **AC.SOL-PROBE.2 (wired vs dark)** — The probe classifies a hook/backend as wired-live vs dark by reading the live runtime config (e.g. `settings.json` hooks present-and-pointing-at-a-real-script vs absent), NOT from a claim that it is wired. *(Outcome: catches the IP-7 class — "hooks already wired" assumed true while `settings.json` was empty — and the IP-2 class — a backend assumed live while no instance exists.)*
- **AC.SOL-PROBE.3 (a live component reads live; a dark one reads dark)** — Run against the CURRENT repo, the probe reports FBM as live (the gated `user-prompt-submit` hook is wired, the seals are merged) — i.e. it produces the verdict that today required a hand-reconciliation. *(Outcome: the probe independently produces the roadmap §6 R-1 finding the persona had to derive by hand.)*

### AC.SOL-GATE.* — the audit gate detects + surfaces a claim-vs-reality divergence
- **AC.SOL-GATE.1 (divergence detected)** — Given a claimed status (in a doc/plan/task) that contradicts the derived record, the gate DETECTS the divergence and reports the specific claim + the ground-truth contradiction. *(Outcome: a stale claim is caught, not silently trusted — the core of the owner directive.)*
- **AC.SOL-GATE.2 (agreement passes clean)** — Given a claimed status that MATCHES the derived record, the gate passes with no false flag. *(Outcome: low false-positive — an enforcement mechanism that cries wolf gets ignored.)*
- **AC.SOL-GATE.3 (composes on the existing gate framework)** — The release-gate arm runs as part of the SAME `loam release` `ALL_GATES` pass as the existing gates, in one report, no parallel CI. *(Outcome: leverage-loam-first — one gate framework, gate 7 is the structural template.)*

### AC.SOL-RECONCILE.* — the subsumption: ONE detector, two entry points
- **AC.SOL-RECONCILE.1 (FBM stored-vs-truth entry point)** — The SAME divergence-comparator that detects a doc's stale status ALSO detects a stored FBM claim that contradicts current ground truth, invoked over a stored episode/claim instead of a doc. *(Outcome: the memory↔reality reconciliation idea is SUBSUMED — one mechanism, two callers — per roadmap §6 redundancy note, line 192, not two parallel tracks.)*
- **AC.SOL-RECONCILE.2 (reconciliation is dated + scoped, never an eternal claim)** — When a divergence is surfaced/recorded, the record of it is dated + scoped to the check, never stored as an eternal negative. *(Outcome: composes `feedback_notes_and_users_are_pointers_evidence_resolves` — the reconcile output cannot itself become the next stale claim.)*

### ★ AC.SOL-PLANTED.* — outcome-altitude: a REAL planted "dark"-for-live divergence is CAUGHT at the real entry-point
- **AC.SOL-PLANTED.1 (outcome-altitude: true)** — A doc is planted that CLAIMS a currently-live component is "dark"/"not wired"/"unbuilt" (the literal shape of today's drift — `loam-vnext-build-plan.md` §6 calling live FBM dark). The REAL audit entry-point (the `loam audit` verb / the release-gate arm — no pre-arranged internal comparator state) is invoked against it, and it CATCHES the divergence: it reports that the doc claims dark while ground truth (refs + live config) says live. **This AC may NOT be satisfied by a unit test of the inner status function** — it must drive the production entry-point against a real planted divergence. *(This is today's literal lesson: today's miss was caught by hand-reconciling against refs; this AC proves the mechanism catches the exact same shape automatically, at the real entry-point — `feedback_test_outcome_altitude_required`.)*

**AC ladder-up:** every AC → roadmap N2 outcome (the always-loaded operative-reality record + the substrate-audit gate) → the roadmap value spine / prime-directive PROTECTION half (a guard against the reason-against-a-false-substrate failure mode) → AC.PO (trustworthy translation requires a true model of the substrate it translates onto).

---

## §6 Build steps (method-level guidance only — builder's call per ODD §1.1)

Per-cycle shape; the builder owns the actual module decomposition.
1. **Manifest** at `docs/plans/state-of-loam-record-and-substrate-audit-gate-slice.manifest.yaml` — `schema_version: 1`; `amendment` block (number = next global counter, confirm at build); `baseline:` = the confirmed BASELINE seal; `components:` naming the framework home the builder selects for the probe/record/comparator + the `loam_cli/release` component for the gate arm; `universal_paths:` for `docs/plans/`; `narrative.target: docs/plans/sealed/state-of-loam-record-and-substrate-audit-gate-slice.md`.
2. **EXAMINE** (read before writing): `framework/tools/loam/src/loam_cli/release/gates.py` (`GateResult`/`ALL_GATES`/`run_all`, gate 7 as the template); the seal-sidecar format (`framework/<component>/seals/SEAL_COMMIT.<slug>` BASELINE/SEAL_COMMIT pins); the ref-check forms in `feedback_published_state_only_from_git_refs.md`; the live hook config shape (`pos3/.claude/settings.json`).
3. **DEFINE** the probe as ground-truth queries → a classification (built/sealed/merged/wired/dark); the record renderer over the probe output (terse); the divergence-comparator (claimed-status vs derived-record).
4. **BUILD** per the ruled forks: the `loam audit` verb (D2 — the testable core first); the release-gate arm as a new `ALL_GATES` entry mirroring gate 7; the second caller for the FBM stored-vs-truth entry point (AC.SOL-RECONCILE).
5. **PROVE** every AC; the ★ outcome-altitude AC plants a real "dark"-for-live divergence and drives the real entry-point.
6. **Tests** authored per-AC, ID-named (`test_AC_SOL_*`), under the chosen component's `tests/`.
7. **Apply + seal** via `loam amend apply` + `loam amend seal` (sealed-component dispatch — name `loam amend apply` explicitly, `feedback_dispatch_explicit_loam_amend_apply`); NEW corrective commits if a file is missed, never `--amend` (`feedback_no_amend_in_agent_dispatches`).
8. **INTEGRATE+RECORD**: author this slice's own declared migration file in `docs/state-migrations/` (the release-gate now hard-blocks a missing one — gate 7; this slice is likely `structural-only` or `no-op`); advance `docs/plans/loam-roadmap.md` N2 → DONE with the seal SHA in the evidence cell.
9. **Smoke:** the ★ planted-divergence real-entry-point walk IS the smoke for this slice.

---

## §7 Out of scope (deferred + when)

1. **NL "rides existing X / X already does Y" claim-scanning** (D4 option B) — a clean SECOND SLICE with its own tighter AC if the owner wants the NL surface; deferred because it is unbounded + false-positive-prone and the structured surface covers today's failure.
2. **The always-on plan-author PreToolUse hook arm** (D2 option A) — fast-follow; it changes authoring behavior (owner-class to turn ON) and composes cleanly on the verb later with no rework.
3. **Auto-HEAL of a stale doc** (D3 option C) — deferred until the comparator's false-positive rate is measured; when built, it rides a reversibility-primitive envelope (surface-don't-silently-overwrite). The owner directive's full reconcile-and-heal destination, not the first step.
4. **The scheduled concept-altitude / drift-audit review (R-2)** — a DIFFERENT mechanism (aggregate output-shape vs the doctrine spine, on a cadence). Roadmap §5a; not this slice. R-2 is the zoom-out; this slice is the substrate-truth + enforcement.
5. **The intent-evolution concept-changelog (R-4)** — a different artefact (how loam's self-understanding evolved). Roadmap §5a; not this slice.
6. **Onboarding the record into a brand-new user's `.loam/`** — the record generation is framework-general, but seeding it into a fresh instance is N3 (onboarding) territory.

---

## §8 Halt triggers (in-flight conditions that abort the build)

1. **A fork (D1–D4) is unresolved at build time** — if the dispatch arrives without a ruling, HALT rather than guessing the refresh model, the fire point, the divergence verb, or the claim surface. Guessing D3 wrong (auto-heal a false positive) corrupts a canonical doc; guessing D4 wrong (NL-scan) produces a noisy gate that erodes trust.
2. **The probe cannot classify a component's liveness from ground truth alone** — if EXAMINE finds a class of component whose live/dark state is NOT derivable from refs + sidecars + runtime config (it genuinely requires a claim), HALT and surface: the record cannot be fully derived, and the gap is itself signal (it names a substrate fact loam cannot currently verify).
3. **Adding the gate arm requires edits outside the declared fence** — if the new `ALL_GATES` entry touches `loam_cli/release` beyond the manifest fence, HALT and surface rather than silently widening (do not touch a sealed component without a manifest entry).
4. **The comparator's false-positive rate on the existing corpus is high** — if a dry-run over the real docs flags many AGREEING statuses as divergent, HALT: the structured-field extraction (D4-A) is mis-reading the corpus; tighten the extraction before wiring any blocking arm (a noisy enforcement mechanism gets disabled — the worst outcome).
5. **The ★ planted-divergence fixture would mutate a real canonical doc** — the planted "dark"-for-live doc is a FIXTURE (a temp copy), never an edit to the real `loam-vnext-build-plan.md` / FBM roadmap. If the only way to exercise the AC is to edit a real doc, HALT (use a fixture copy — the same read-only discipline the FBM cold-walk used).

---

## §9 Bookkeeping

1. **`docs/plans/loam-roadmap.md`** — N2 → DONE on ship, with the seal SHA in the evidence cell (§2 DONE table). Append a §6 reconciliation finding if the build surfaces any NEW divergence between a status and reality. Strike the §5b "memory↔reality reconciliation mechanism" row's separate tracking — note it as SUBSUMED-by-N2 (it already points to N2; confirm the fold).
2. **`docs/STATE.md`** — amendment row at seal (next global counter).
3. **`docs/state-migrations/`** — this slice's own declared migration file (gate 7 now hard-blocks a missing one; likely `structural-only` / `no-op`).
4. **`docs/plans/build-cursor.md`** — if the v-next build cursor is the active driver, note N2 complete (N2 is a parallel track to N1 per roadmap §4 line 85; it does not advance the N1→N3→N4 kernel cursor).
5. **Parent roadmap §7 dependency spine** — N2 is the parallel-track box; mark it landed.
6. **Plan register** — populated by the builder at build time with the D-decisions actually taken + SHAs backfilled at seal.

---

## §10 F2 Ruthless Feedback (honest doubts; named design risks)

1. **The "derive from ground truth" promise has a HARD edge: not every liveness fact is ref-derivable.** "Is this hook wired" is derivable (read `settings.json`). "Is this backend actually LIVE end-to-end" (IP-2's graphiti case — built, MCP-wired, async-queue present, but never actually running) may NOT be fully derivable from static config — it might need a real liveness PROBE (an `import graphiti_core` / a live call), which the review itself names (line 224: "`import graphiti_core` → live/dark"). **Evidence:** IP-2 — the graph was MCP-wired + had an async-write queue (so static config said "wired") yet `memory_consumer.py` was a Protocol shim that "never imports memory-system source" (review line 160) — static config would have mis-classified it as live. **Alternative:** the probe must distinguish "wired in config" from "live on a real invocation" for backend-class components — a cheap real-probe (import/call), not just a config read. Halt-trigger 2 names the case where this is not derivable. This is the single most important design subtlety and the dispatch must carry it.

2. **The mechanism that prevents drift can itself drift if it is built as prose.** The deepest irony: an audit gate whose own status record is a hand-maintained doc would be the next thing to go stale. **Evidence:** this is literally what happened to the v-next plan + FBM roadmap (prose status drifted from refs). **Alternative:** AC.SOL-RECORD.1 (derived-not-authored) is the load-bearing AC — D1-A (generate-fresh) is recommended precisely so there is no persisted prose to drift. If the owner picks D1-B/C (a cached/persisted record), the staleness-detection becomes the new drift surface and must itself be ground-truth-checked. The mechanism MUST dogfood its own principle.

3. **An enforcement gate with false positives gets disabled — and then the protection is gone with a false sense it's there.** A noisy gate is worse than no gate: it gets `--skip`'d or removed, and the absence is invisible. **Evidence:** the corpus already names "a robust workaround masks root-cause urgency" — a gate that's routinely overridden is that pattern. **Alternative:** D4-A (bounded structured surface) + the dark-launch recommendation (D2/D3: surface-only on the authoring arm first, hard-block only on the contained release-gate arm) + halt-trigger 4 (HALT on a high false-positive dry-run) are all aimed at earning trust before the gate blocks. Do NOT ship the unbounded NL-scan (D4-B) as a blocking arm in slice 1.

4. **Subsumption (AC.SOL-RECONCILE) is the right call but the FBM entry point is thinner than the doc entry point.** The doc-status comparison is concrete (a `status:` field vs a derived record). The FBM stored-vs-truth comparison is fuzzier (what stored claim, compared to what ground truth?). **Evidence:** the owner directive's own instance (memory said Cairn "PR #7", repo said #6) is a concrete checkable claim — but not every stored episode carries a checkable status. **Alternative:** scope AC.SOL-RECONCILE.1 to CHECKABLE stored claims (a stored claim that names a verifiable ground-truth fact — a SHA, a version, a built/dark status), not arbitrary episodes. The subsumption is "one comparator, two callers" — the SECOND caller passes a checkable stored claim; non-checkable stored claims are out of scope (surface, owner rules — `feedback_notes_and_users_are_pointers_evidence_resolves`). This keeps the fold honest without overclaiming the comparator handles all of memory.

5. **N2 is a parallel track to N1 but shares a likely component home (`loam_cli`).** If N1 (the `.loam/` layout) and N2 land in the same tree concurrently, they can race on the index/loam-amend (`feedback_serialize_amendment_builds`). **Evidence:** the roadmap §4 line 85 calls them near-parallel; the serialize-builds memory says two builds in one tree race. **Alternative:** if both are dispatched, isolate via worktree (`isolation:worktree`) OR serialize the builds; the dispatch brief must name whichever. Not a design flaw — a dispatch-sequencing constraint to honor.

---

## §11 Provenance trail (load-bearing sources)

- N2 definition + promotion-to-NEXT-UP + the subsumption note + the value spine: `docs/plans/loam-roadmap.md` lines 81, 85, 118, 192, 230 (§7 #2), §1 line 36.
- R-1 (the living current-reality record, machine-backed) + R-3 (the substrate-audit gate) + their composition into one mechanism: `docs/reviews/loam-evolution-reasoning-acceleration.md` lines 217-232 (R-1), 251-265 (R-3), 303-311 (#1), 323-336 (#3 + the synthesis line 333). The IP-2/IP-7/IP-3 failure classes this prevents: lines 46-63 (IP-2), 124-137 (IP-7), 65-78 (IP-3); patterns P-B + P-D: lines 173-197.
- The owner directive this makes structural: `feedback_reconcile_checks_against_memory.md` (Telegram 13311) — compare every check to memory; reconcile; so manual re-checking shrinks; the "memory↔reality reconciliation mechanism" candidate-feature line.
- The git-ref-graph verification discipline the probe mechanizes: `feedback_published_state_only_from_git_refs.md` (the `merge-base --is-ancestor` / `tag --contains` / `branch --contains` forms; status lines + registers are Tier-2 stale-prone).
- The release-gate framework to compose ON (Lens 1) + gate 7 as the structural template: `framework/tools/loam/src/loam_cli/release/gates.py` (`GateResult` line 44, `check_migration_declared` lines 693-760, `ALL_GATES` tuple line 753).
- The seal-sidecar format the probe reads: `framework/<component>/seals/SEAL_COMMIT.<slug>` (BASELINE/SEAL_COMMIT pins; sample `framework/self-upgrade/seals/SEAL_COMMIT.seal-bookkeeping-retrofit`).
- The structural-enforcement parent licensing gate-tier over memory-tier: `feedback_structural_enforcement_on_recurrence.md`.
- The outcome-altitude lesson (the ★ AC at the real entry-point): `feedback_test_outcome_altitude_required`.
- The reconcile-output-can't-become-the-next-stale-claim discipline: `feedback_notes_and_users_are_pointers_evidence_resolves.md`.
- Plan-doc + AC-ID + manifest conventions: `plugins/dev-sdlc/docs/conventions/plan-docs.md`; `feedback_scope_descriptive_ac_ids.md`; sibling exemplar `docs/plans/loam-migration-engine-and-release-gate-slice-plan.md`.

---

*Principles applied: RECONCILE-against-ground-truth (this mechanism IS the owner directive made structural — and the plan dogfoods it: derive state from ground truth, never drift-prone prose — D1-A + AC.SOL-RECORD.1); EXAMINE-before-designing (read R-1/R-3 + the roadmap + gates.py + the seal-sidecar format before authoring); plan-before-code (PLAN ONLY, halt for review); outcome-altitude AC at the real entry-point (AC.SOL-PLANTED.1 plants a real divergence, drives the real verb); Claude/loam-leverage-first (compose on git refs + seal sidecars + the `loam release` ALL_GATES framework — do NOT reinvent status-derivation or CI); ODD authoring (every AC outcome-shape, method-in-AC test passed); scope↔confidence (D1–D4 surfaced as forks where confidence is low; tight where confident — the bounded structured surface, the verb-first build); F2 (the not-all-liveness-is-ref-derivable hard edge, the mechanism-can-itself-drift irony, the false-positive-disables-the-gate risk, the thinner-FBM-entry-point, the N1/N2 race — each with evidence + an alternative); Lens 5 (decompose only when a sub-task tightens scope — NL-scan is the clean second slice, not a forced split now); Lens 6/M5 (the forks surfaced with named signals, not silently resolved).*
