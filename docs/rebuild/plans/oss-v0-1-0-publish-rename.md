# OSS v0.1.0 publish — M1.rename — multi-amendment series master plan

**Status:** series master plan. 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Programme position:** M1 in `oss-v0-1-0-publish.md` — the most-upstream amendment milestone in the OSS-publish programme. Now structured as a **multi-amendment series** (M1a → M1b → … → M1n) per owner ruling D-RNM.1 (2026-04-29).
**Authority documents:**
- `docs/rebuild/plans/loam-rename-decisions.md` (locked Tier-1 + Tier-2 + Kept-Technical catalogue).
- `.scratch/claude-output/loam-rename-migration-plan.md` (research; mechanics + dependency ordering).
- `docs/rebuild/plans/oss-v0-1-0-publish.md` §5 (M1 row needs re-pricing post-split — flagged for the dispatcher in §13).

---

## 1. Owner rulings (locked 2026-04-29)

The prior monolithic-amendment plan-doc surfaced three method-level decisions to the owner. All three are now ruled:

- **D-RNM.1 — Land Tier-1 + Tier-2 together vs split.** **SPLIT.** Idea 10 already specifies "multi-amendment migration." The empirical surface (5–10× the rubric estimate; sixteen sealed components in one fence; ~91 import sites + ~597 OTel emit sites + ~1310 `pos-amend` doc/code refs) makes a single sealed amendment unsafe. M1 is now a **multi-amendment series** of independently-sealed sub-amendments.
- **D-RNM.2 — `loam.*` package layout shape.** **Per-component namespace-package shape.** Each component lives at `framework/<comp>/src/loam/<comp>/`; `loam` is a PEP-420 implicit namespace package. Preserves workspace-bootstrap's editable-install discipline; M2 partition manifest flattens at synth time. (Resolved at sub-amendment scope in M1d-class — see ladder below.)
- **D-RNM.3 — Compat window.** **None.** Pre-public release with zero existing users. Hard cutover at each sub-amendment's seal; no `POS_V2_*` env-var fallback module, no `pos-amend` shim binary, no aggregator dual-prefix read window. Methodology-aligned per the no-extras invariant in ODD §5.1.1.

**Methodology heads-up (locked at owner-ruling time):**

- **H19 byte-content-match invariant retires under ODD §4** for the paths this rename touches. This is the same retirement class flagged in the FIDRAFT entry from amendment #74 (`framework/<comp>/src/__init__.py` byte-content invariant blocks legitimate public-API additions). The retirement happens **in-band** as part of whichever sub-amendment's scope first touches an H19-pinned path; new pins land at the post-rename baseline. Sub-plans whose scope crosses an H19 path are responsible for naming the retire-and-rebaseline step in their own §4 ACs and §10 halt-trigger conditions.

---

## 2. Sub-amendment ladder

Each row is an independently-sealed amendment authored against its own plan-doc. **Each carries its own AC family** (`AC.RNM-1a.*`, `AC.RNM-1b.*`, …) so AC-prefix collisions across sub-amendments are structurally impossible. Sub-plans live alongside this master at `docs/rebuild/plans/oss-v0-1-0-publish-rename-1<letter>.md`.

| ID | Sub-plan | Description | AC-prefix | Components in fence (preliminary) | Sealed | Notes |
|----|----------|-------------|-----------|-----------------------------------|--------|-------|
| **M1a** | `oss-v0-1-0-publish-rename-1a.md` | **Docs/prose-only brand rebrand.** Live docs / READMEs / CLAUDE.md (root) / VALUE_PROPOSITION / odd-methodology / odd-in-pos / duration-rubric / CLAUDE_CAPABILITIES — `pos-v2` / `pOS v2` brand strings rewritten to `loam` in user-facing prose. ZERO code, env-vars, paths, CLI, OTel, launchd. Per-component READMEs are touched (small fence). | `RNM-1a` | 5 (READMEs only): objective-tracker, workspace-bootstrap, hands-off-lifecycle, scope-of-work, workspace-sync | yes | Cheapest, safest first landing. Establishes the pattern, exercises pos-amend at the new naming, surfaces cross-mode debt early. |
| **M1b** | `oss-v0-1-0-publish-rename-1b.md` | **Per-host config dir + env-vars.** `~/.pos/` → `~/.loam/` (path constants in code + docs); `POS_V2_*` → `LOAM_*` (eight env vars; dedupe per migration plan §2.5). Hard cutover (no fallback module per D-RNM.3). One-shot per-host migration script lives in workspace-bootstrap or a one-shot under `framework/tools/`. | `RNM-1b` | likely 3–5: workspace-bootstrap, hands-off-lifecycle, memory-system, primary-persona (depending on env-var/path callsite distribution) | yes | First code-touching sub-amendment. Cross-mode debt: dispatch templates referencing `~/.pos/` update concurrently. |
| **M1c** | `oss-v0-1-0-publish-rename-1c.md` | **launchd labels.** `com.pos-v2.<slug>.*` → `com.loam.<slug>.*`. plist filenames cascade. hands-off-lifecycle's bootout-before-bootstrap flow issues bootouts for old labels once on first run after upgrade, then installs new labels. | `RNM-1c` | 2: hands-off-lifecycle, workspace-bootstrap | yes | First sub-amendment that may cross H19. **H19 retire-and-rebaseline lands here if the diff exceeds H19's frozen baseline window.** Verify pre-build whether HOL's H19 byte-content sample includes any plist file. |
| **M1d** | `oss-v0-1-0-publish-rename-1d.md` | **OTel `pos.*` → `loam.*` roots.** All 23 root namespaces (per migration plan §3.5; `pos.degradation` rebases to `loam.dormancy` deferred to M1f's dormancy rename). Names below the second segment unchanged. Aggregator subscription registration updates. **No dual-prefix read window** (D-RNM.3 hard-cutover; existing retention-DB rows under `pos.*` stay queryable as data; no compat read in code). | `RNM-1d` | likely 8–12 (every emitter component) | yes | Largest single-grep amendment of the series; pure mechanical substitution. |
| **M1e** | `oss-v0-1-0-publish-rename-1e.md` | **Monolithic `loam.*` namespace pivot.** Per-component `framework/<comp>/src/loam/<comp>/` restructure (D-RNM.2 ruling). Every `from pos_<comp> import` callsite rewrites to `from loam.<comp> import`. pyproject.toml `name` fields update. Editable-install reconfig in workspace-bootstrap / first-run / dev setup. Hard cutover (no `from pos_<comp>` compat). | `RNM-1e` | 14–16 (all sealed components except dormancy, which lands in M1f) | yes | The largest structural-surface amendment. **H19 retire-and-rebaseline definitely lands here** (the byte-content sample's paths move under the rename). Owner-review gate recommended pre-dispatch given fence width. |
| **M1f** | `oss-v0-1-0-publish-rename-1f.md` | **Tier-2: graceful-degradation → dormancy.** Directory `framework/graceful-degradation/` → `framework/dormancy/`; package `graceful_degradation` → `dormancy` (under the `loam.dormancy` namespace from M1e); OTel `pos.degradation.*` → `loam.dormancy.*`; config files `degradation.sqlite` → `dormancy.sqlite`, `degradation-config.yaml` → `dormancy-config.yaml`; docs subdir `docs/rebuild/components/graceful-degradation/` → `docs/rebuild/components/dormancy/`; workspace-bootstrap adapter `workspace_bootstrap.adapters.graceful_degradation` → `workspace_bootstrap.adapters.dormancy`. AC prefix `P` stays. Per-host migration script for SQLite + YAML rename. | `RNM-1f` | 2: dormancy (renamed), workspace-bootstrap | yes | Depends on M1e (the `loam.*` namespace must exist). Tier-2 cascades naturally once Tier-1 lands. |
| **M1g** | `oss-v0-1-0-publish-rename-1g.md` | **`pos-amend` CLI → `loam amend` subcommand.** `framework/tools/pos-amend/` → `framework/tools/loam/`. Package `pos_amend` → `loam_cli` (or `loam_amend` under a `loam_cli` umbrella — builder's call). Console-script entry-point `pos-amend` → `loam` with `amend` as a subcommand (`loam amend apply`, `loam amend seal`, etc.). All ~1310 doc/code refs to `pos-amend` rewrite to `loam amend`. **No shim binary** per D-RNM.3 hard cutover. Existing per-component manifests apply unchanged via `loam amend apply <manifest>`. Dispatch-template path refs update. | `RNM-1g` | 1: workspace-bootstrap (`[project.scripts]` entry-points) + universal admissions for `framework/tools/` | yes | **Last amendment built under the `pos-amend` CLI name** — the rename amendment itself uses `pos-amend` for its own bookkeeping; subsequent amendments use `loam amend`. |

**Ladder dependency notes:**

1. **M1a is independent of all later sub-amendments** — docs-only.
2. **M1b is independent of M1a** — env-vars and `~/.pos/` are code/path concerns; can run in either order. Conventionally lands second since prose-rebrand is cheapest.
3. **M1c, M1d, M1e are pairwise-independent in scope** but **serial in the shared tree** (per `feedback_serialize_amendment_builds`). Order is dispatcher's call.
4. **M1f depends on M1e** (the `loam.*` namespace must exist before dormancy moves under it).
5. **M1g is the dependency-final sub-amendment** — the `pos-amend → loam amend` self-rename only lands once the rest of the rename has stabilised. Authoring `loam amend` while still building amendments under `pos-amend` is the smoothest sequencing.

**Re-pricing flag for the master programme plan.** The M1 row in `oss-v0-1-0-publish.md` §5 currently prices "30–60 min midpoint 45 min" against the monolithic shape. Post-split, the sum across M1a..M1g is roughly **4–8 h AI wall-clock spread across multiple sessions**. **Action item for the next dispatch:** edit `oss-v0-1-0-publish.md` §5 to replace the single M1 row with the M1a..M1g ladder above and re-price the programme total. **This dispatch does NOT edit the master programme plan** — that's the next dispatcher's call after this series master commits.

---

## 3. Spec-objective placement (per CLAUDE.md §2.5)

Each sub-amendment carries its own §2.5 statement in its own plan-doc. The series-level objectives this multi-amendment series satisfies are:

- **AC.OSS.5** (`oss-v0-1-0-publish.md` §3) — *"Documentary rebrand complete in public artefacts"* — Tier-1 + Tier-2 rename per `loam-rename-decisions.md`. The M1 series is the principal contributor; M9 scrub closes residuals.
- **AC.OSS.3** — *"No dev-discipline machinery visible in public synthesis output"* — the M1 series ensures the dev-only artefact paths the M2 partition manifest will reference are stable post-rename.
- **AC.PO.1** (VALUE_PROPOSITION primary-persona test) — single-syllable identity (`loam`) reduces the user's translation-burden vocabulary.
- **AC.PO.2** (VALUE_PROPOSITION harness test) — monolithic `loam.*` namespace becomes the import-path the persona's toolkit composes against.

**ODD §2.5 reverse-direction commitment.** Every line of code/test/doc-prose changed in any sub-amendment's diff traces back to an AC named in that sub-amendment's plan-doc. Series-level cross-cutting concerns (AC-prefix uniqueness, fence non-overlap when consecutive, H19 retirement bookkeeping) are surfaced here.

---

## 4. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

The series preserves every existing Claude-native composition (PreToolUse hooks, MCP servers, skills, plugins) by rebasing the namespace they emit on (`loam.*` instead of `pos.*`). Future Claude-Code-shaped extensions (M6's Dev/SDLC plugin) read uniform paths post-series. **Pass.**

### Lens 2 — Harness + primary-persona value

**Primary-persona test:** single-syllable single-CLI identity post-M1g. The persona's user-prose vocabulary loses `pos-v2`/`pOS v2`/`pos-amend` and gains the one word `loam`. **Pass.**

**Harness test:** the monolithic `loam.*` namespace IS a new harness primitive — every future component's persistent import path. The dormancy rename is a behavioural-vocabulary lift. **Pass.**

### Lens 3 — ODD authoring

The series is mechanical-substitution work. Each sub-amendment's ACs are outcome-shaped (post-rename grep counts, post-import-resolution checks, post-launchctl-list checks, etc.). Method-shape (which exact regex, which exact rename order within a sub-amendment) is the builder's call inside the AC outcome bound. The split itself is an ODD §5.1.1 elimination of the wall-clock-blow-out failure class.

---

## 5. Hard constraints (series-wide)

- **No public-API surface changes** beyond the rename itself.
- **No SQL schema migration** beyond column-content (e.g. `loam.*` instead of `pos.*` in trace span-name columns; existing rows untouched).
- **No new external deps** in any sub-amendment.
- **Historical commit messages + seal narratives unchanged** (locked owner ruling `loam-rename-decisions.md` Q2).
- **AC letter prefixes unchanged.** `H1` stays `H1`; `B25` stays `B25`; etc.
- **No git-history rewrite** in this series. Repo-rename to `lukeivers/loam` is M9-deferred.
- **No `git commit --amend`** — corrective commits are NEW commits per `feedback_no_amend_in_agent_dispatches`.
- **`pos-amend apply` runs BEFORE the seal commit** in every sub-amendment per FIDRAFT note from amendment #41.
- **AC-prefix uniqueness across sub-amendments.** Each sub-amendment uses `AC.RNM-1<letter>.*`; collisions are structurally impossible.
- **H19 retirement happens in-band** at whichever sub-amendment first crosses an H19-pinned path; new pins land at the post-rename baseline.

---

## 6. Out of scope (series-wide; named explicitly per ODD §2.5)

- **Repo directory rename** `ivers-corp-pos-v2` → `loam` + GitHub repo creation at `lukeivers/loam`. M12 publish-time only. Dispatch instructions (`feedback_always_specify_wd_in_dispatches`) update post-rename.
- **`plot` user-facing CLI alias for scope-of-work.** Idea 10 Phase 5 — deferred to v0.2 per `oss-v0-1-0-publish.md` §4.
- **Plugin pre-naming** (trellis, arbor, etc.). Phase 4, deferred per `loam-rename-decisions.md`.
- **Long-form `docs/odd-methodology.md` filename change.** ODD is methodology, not brand-bound. Internal prose updates "pos-v2" references; filename stays.
- **`docs/odd-in-pos.md` filename change.** Filename change folds into M1e (the namespace pivot has the file-tree restructure energy already in scope). M1a updates content prose only; the filename change is M1e's.
- **`docs/rebuild/spec/pos-v2-objectives-spec.md` / `pos-v2-rebuild-proposal.md` filename changes.** Filename changes fold into M1e for the same reason. M1a updates content prose only; filenames stay until M1e.
- **Audit-log line-level prose.** Logs are read by humans; "dispatcher logged X" stays prose-shaped. Out of scope; M9 scrub may catch stragglers.
- **`docs/rebuild/` tree rename to `docs/foundation/` or `docs/history/`.** "rebuild" remains historically meaningful; not theme-driven.
- **Renaming `personas/` or persona file conventions.** Workspace-content surface; not this series.
- **Rewriting the `pos3` derived workspace's vocabulary.** Workspace-side migration, not framework-side rename.
- **AC-prefix family reshape** (e.g. `H` → `D` for hands-off-lifecycle). Locked Kept-Technical (loam-rename-decisions §6).

---

## 7. Series-level halt triggers

A sub-amendment builder MUST halt and surface to the dispatcher when:

1. **A rename target disagrees with `loam-rename-decisions.md`.** Owner ruling needed; do not improvise.
2. **A sealed-component invariant cannot be satisfied without retiring it.** Surface for owner ruling on whether to retire the invariant per ODD §4. Series-level expectation: H19 retirement happens in-band at the first sub-amendment that crosses an H19-pinned path. If that sub-amendment's builder finds H19 byte-content match would prevent the rename, the retire-and-rebaseline IS the methodology-aligned path; record in §14 of that sub-plan and proceed.
3. **An ODD §2.5 violation surfaces** in the surface being edited (per `feedback_subagent_odd_violation_halt`). Halt; do NOT silently extend.
4. **A docs-only rename produces a code-side breakage.** Means the "docs-only" classification was wrong for the surface — re-scope to a later sub-amendment that includes the code surface.
5. **Cross-mode debt cascade beyond the sub-amendment's stated scope.** A DEV-MODE artefact references a pre-rename identifier and the rename can't be done in this sub-amendment's fence. Surface for owner ruling on whether to widen fence or defer to a later sub-amendment.
6. **`pos-amend` automation hits a gap.** Regex narrowness, abs-path requirement, stash-pop conflict, SHA-backfill heuristic mis-target. Record in `FUTURE_IDEAS_DRAFT.md` and surface; do not push through.
7. **Wall-clock exceeds 2× the sub-plan's projected estimate.** Halt with current-state report; dispatcher triages continue/split-further/pause.
8. **Pre-existing test fails post-rename.** Halt; the rename has hit a non-mechanical change. Surface failing test + diagnosis.
9. **A sub-amendment's mid-build finds the dependency ordering was wrong** (e.g. M1f tries to land before M1e and discovers `loam.*` namespace doesn't exist). Halt; do NOT improvise dependency ordering.
10. **The rename uncovers a `loam` identifier already in use** in the existing tree. Halt; rename the conflicting use first.

---

## 8. Series-level risks

1. **Sub-amendment fence creep.** A sub-amendment intended to touch only its named surface accidentally pulls in an adjacent surface (e.g. an env-var rename touches a launchd label as a side-effect). Mitigation: per-sub-amendment AC.<prefix>.S seal-diff fence is exhaustively named; halt-trigger §7.4 fires on any cross-surface reach.
2. **Dependency-order race.** Two builders accidentally dispatched in parallel against the shared tree race on `index.lock` / `pos-amend` state / per-component editable installs. Mitigation: `feedback_serialize_amendment_builds` — sub-amendment builds are SERIAL.
3. **H19 retirement bookkeeping.** Whichever sub-amendment first crosses H19 owns the retire-and-rebaseline. Mitigation: each sub-plan's §10 explicitly checks H19 cross-state pre-build; series master tracks which sub-amendment claimed the retirement in §14.
4. **Cross-mode debt slippage.** A DEV-MODE artefact references a pre-rename identifier and isn't caught until the M2 partition synthesis runs. Mitigation: each sub-amendment includes a "cross-mode debt closure" AC for its own surface; M2's dry-run captures any straggler.
5. **AC-prefix collision.** A sub-amendment's builder accidentally reuses an AC.RNM-1<letter>.* prefix already used by an earlier sealed sub-amendment. Mitigation: strict per-sub-amendment AC-prefix discipline named in this master plan §2.

---

## 9. Sub-amendment output convention

Each sub-amendment's plan-doc carries the same shape:

1. Summary / TLDR + sub-amendment ID + dependencies on prior sub-amendments.
2. Spec-objective placement (CLAUDE.md §2.5).
3. Three-lens analysis (CLAUDE.md design lenses) — abbreviated; series-master §4 covers the cross-cutting case.
4. Acceptance criteria (`AC.RNM-1<letter>.*`).
5. Hard constraints (sub-amendment-specific; series constraints inherit).
6. Out of scope (sub-amendment-specific).
7. Implementation order.
8. Halt triggers (sub-amendment-specific; series triggers inherit).
9. Risks (sub-amendment-specific).
10. Decisions remaining for owner ruling (preferably none — by sub-amendment time, all method-decisions are owner-ruled).
11. Halt-and-surface findings encountered during plan authoring.
12. Method-decision record (post-build, per `pos-amend seal --plan-doc <abs-path>` convention).
13. Test breakdown.
14. Commit SHAs (populated by `pos-amend seal` SHA-backfill).
15. References.

---

## 10. Series progress tracker

| ID | Status | Plan-doc commit | Feature commit | Apply commit | Seal commit | H19 retire? | Notes |
|----|--------|-----------------|----------------|--------------|-------------|-------------|-------|
| M1a | (in flight — see this dispatch) | TBD | TBD | TBD | TBD | no | docs-only |
| M1b | not started | — | — | — | — | TBD | env-vars + `~/.pos/` |
| M1c | not started | — | — | — | — | possibly | launchd labels |
| M1d | not started | — | — | — | — | TBD | OTel roots |
| M1e | not started | — | — | — | — | **likely yes** | namespace pivot |
| M1f | not started | — | — | — | — | possibly | dormancy |
| M1g | not started | — | — | — | — | possibly | CLI rename |

Each row is updated by the dispatcher as the series progresses. The "H19 retire?" column declares whether THIS sub-amendment retired the invariant (and rebaselined); only one row should read **yes** when the series completes.

---

## 11. Out-of-band: M1 row in the master programme plan

The current M1 row in `oss-v0-1-0-publish.md` §5 reads:

> | **M1.rename** | `oss-v0-1-0-publish-rename.md` | **Multi-component sealed amendment.** Tier-1 + Tier-2 rename per `loam-rename-decisions.md`. … | AC.OSS.5; AC.OSS.3 | 30–60 min | 45 min |

Post-split, this row needs replacement with the M1a..M1g ladder. **The next dispatcher (post-M1a-seal) is responsible for editing `oss-v0-1-0-publish.md` to reflect the split.** The recommended replacement shape: one row per sub-amendment (M1a..M1g) with each sub-amendment's wall-clock estimate; the series total replaces the current M1 wall-clock total. **This master plan-doc commits before any code; the M1 row update is a separate doc-only commit at a future dispatch.**

---

## 12. References

- **Authority documents:**
  - `docs/rebuild/plans/loam-rename-decisions.md` (locked Tier-1 + Tier-2 + Kept-Technical catalogue).
  - `.scratch/claude-output/loam-rename-migration-plan.md` (research; mechanics + dependency ordering).
  - `docs/rebuild/plans/oss-v0-1-0-publish.md` §5 (M1 row needs re-pricing post-split).
- **STATE.md** — governing rules.
- **ODD methodology + ODD-in-pos:** `docs/odd-methodology.md`, `docs/odd-in-pos.md`.
- **VALUE_PROPOSITION:** `docs/rebuild/VALUE_PROPOSITION.md`.
- **CLAUDE.md** + `~/.claude/CLAUDE.md` + `~/.claude/projects/-Users-lukeivers-pos3/memory/MEMORY.md`.
- **Memory bullets carried forward (cited by name per the dispatch corpus):**
  - `feedback_no_amend_in_agent_dispatches`.
  - `feedback_dispatch_explicit_pos_amend_apply`.
  - `feedback_subagent_odd_violation_halt`.
  - `feedback_amendment_dispatch_speedups`.
  - `feedback_summarize_and_surface_decisions`.
  - `feedback_serialize_amendment_builds`.
  - `feedback_always_specify_wd_in_dispatches`.
  - `feedback_verify_post_amendment_state`.
  - `feedback_duration_estimation_rubric`.
  - `feedback_loose_AC_text_fix_AC_not_implementation`.
- **Precedent multi-component sealed-amendment manifests:**
  - `docs/rebuild/plans/single-framework-restructure.manifest.yaml` (three-component fence; universal-paths pattern).
  - `docs/rebuild/plans/a1-substrate-timestamp-format-normalization.manifest.yaml` (three-component fence with H19-frozen on hands-off-lifecycle).
- **Synthesis tool (publish mechanism downstream):** `framework/tools/pos-publish-framework-only/` (renames in M1g).
- **`pos-amend` tool:** `framework/tools/pos-amend/` (renames in M1g).

---

## 13. Revision history

- **2026-04-29 (this doc, initial):** Authored as series-master after owner rulings on D-RNM.1 (split), D-RNM.2 (per-component namespace-package), D-RNM.3 (no compat window). Replaces the prior monolithic-amendment plan that surfaced these decisions for ruling.
