# Plan — foundation-polish cluster (the 1.0 install/upgrade/skill gate)

**Status:** sub-plan-doc (PLAN ONLY — no implementation code authored) · **HALT for owner ruling on the two public-action / wide-blast forks before build (F-FLATTEN, F-PUBLISH).** The autonomous sub-items dispatch off this plan without a further ask.
**Working directory:** `/Users/lukeivers/loam` (branch `main`; the builder branches per-sub-item before code).
**Parent plan:** `docs/plans/loam-roadmap.md` (the live build roadmap — §3 IN-FLIGHT "loam upgrade mechanism", §5b "structure flatten + PyPI / conventional install", §5b "skill triage"). This cluster is the **foundation-polish step the 1.0 acceptance-smoke is sequenced AFTER** (`docs/plans/loam-1.0-acceptance-smoke.md` §1 status-note + §7 sequencing).
**Predecessors (load-bearing prior seals + artefacts):**
- **Migration ENGINE + `loam migrate` verb — SEALED** (`framework/state-migration-engine/`; seal `58bead7`; engine commits `c08cbcb`/`6587e94`). The `migrate` subcommand entry-point is declared (`framework/state-migration-engine/pyproject.toml:23-24` → `build_migrate_subcommand`, present at `cli.py:53`) and resolves through the unified loam CLI's `loam.cli.subcommands` discovery loop (`framework/tools/loam/src/loam_cli/cli.py:40-64`). **This is the engine the auto-detect trigger wires onto — it is NOT re-built here.**
- **Migration-engine slice plan** (`docs/plans/loam-migration-engine-and-release-gate-slice-plan.md`) — its **D4 ruled "build only the `loam migrate` verb; auto-detect hook is a fast-follow."** SUB-ITEM 3 of THIS cluster IS that named fast-follow.
- **Release-gate framework — SEALED** (`framework/tools/loam/src/loam_cli/release/gates.py`, `ALL_GATES`; gate 7 `check_migration_declared`, gate 8 `check_substrate_audit`, gate 9 `boundary-respected`). The PyPI-publish path composes on this gate chain (NOT a new CI).
- **`reversibility-primitive` — SEALED** — the backup/verify/rollback envelope the auto-upgrade composes ON (the migration engine already wraps it; the trigger inherits it).
- **Install-from-source substrate** — `install-from-source.txt` (the ordered `-e ./<path>` editable-install file, FBE.4) + `README.md` install section (lines 48-87) + `docs/install-from-source.md`. The README ALREADY declares the v0.x source-only path intentional and names the future PyPI shift verbatim (lines 84-87): *"A future minor will ship the CLI from PyPI directly, eliminating the install clone."* SUB-ITEM 1 IS that future minor.
- **Platform-portability blueprint — task #47, IN-FLIGHT, NOT yet on disk** (the Windows + Claude-desktop-app sprint-ready blueprint). SUB-ITEM 1 names it as a **named consumer + compose-target**, does NOT duplicate it (F2 §10.4).
- **Skill-triage — task #35, greenlit / in_progress.** Installed skills live at `plugins/loam-skills/skills/` (23 skills present). SUB-ITEM 4 folds in REMAINING scope only.
- **Current published version: `0.14.0`** (`docs/ACTIVE_MINOR`). 1.0 is the target this cluster gates toward.

**BASELINE candidate:** HEAD of `main` `cc512b1f` at plan-authoring time; each sub-item's manifest confirms its own baseline against the predecessor sub-item's seal-advance commit at build time. **The global amendment counter is at 160 (highest manifest); each sub-item advances it — the builder confirms the exact number at apply time** (`feedback_version_numbers_at_release_time` — never pre-bake).
**Status-file target:** `docs/STATE.md` amendment-row backfill per sealed sub-item; `docs/plans/loam-roadmap.md` §3/§5b row-moves (DONE) per sub-item.
**Quality bar:** outcome-altitude AC per the load-bearing sub-items — a REAL install into a genuinely clean environment producing a working `loam init` (AC.INST.S), and a REAL stale-state instance auto-upgraded at session-start (AC.UPGR.S). STUB-class tests do NOT satisfy these (`feedback_test_outcome_altitude_required`).

---

## §1 Summary / TL;DR

**What ships:** the four foundation-polish pieces that must land before loam earns the 1.0 label and before the 1.0 acceptance-smoke can run against a stable install — sequenced so the high-confidence pieces dispatch autonomously and the two genuine owner-calls (the flatten, the public publish) are surfaced with recommendations.

**The four sub-items (build order shown in §6):**
1. **SUB-ITEM 1 — Conventional install / PyPI publish** *(the load-bearing 1.0 requirement; the smoke gates against THIS).* A non-technical user — and a Windows user via the Claude desktop app — installs loam through a documented, normal path (`pip install` / `pipx` / Claude-plugin route), not a dev-tree checkout. **Composed in two phases:** (1a) **packaging readiness** — autonomously buildable, no public action (assemble the single installable surface, lock the dependency graph, dry-run-build the wheels, prove a clean-env install from a LOCAL artefact index); (1b) **the public PyPI flip** — OWNER-GATED (publishing a public package is a public action + creates an irreversible name claim).
2. **SUB-ITEM 2 — Structure flatten** *(framework layout).* **VERDICT: SEPARABLE, NOT a prerequisite for SUB-ITEM 1 — and the specific `framework/framework` doubling the roadmap names DOES NOT EXIST.** This is an OWNER-RULING fork (do / defer / partial) because of blast radius + redo cost. **Recommendation: DEFER** — see F-FLATTEN. It is NOT bundled into the install path.
3. **SUB-ITEM 3 — Migration auto-detect / auto-upgrade trigger** *(non-tech-automatic upgrade UX).* Wire the already-sealed engine + `loam migrate` verb to a session-start auto-detect: notice a stale user-state cursor → run the wrapped replay → surface what it did in plain language. **Autonomously buildable as a verb-composed module; the always-on session-start ARM is owner-class to flip live** (runtime behaviour) — mirrors the migration plan's D4 ruling exactly.
4. **SUB-ITEM 4 — Skill triage (REMAINING scope only).** Greenlit/in-progress; fold in only what's left: confirm installed skills have working triggers, retire dead ones. **Autonomously buildable; kernel-independent ride-along.**

**AC families:** `AC.INST.*` (clean-env install from the unified surface), `AC.PYPKG.*` (single installable package surface + locked dep graph + buildable wheels), `AC.UPGR.*` (auto-detect stale cursor → wrapped replay → plain-language surface), `AC.SKTRI.*` (installed skills trigger; dead skills retired), plus the two outcome-altitude ACs `AC.INST.S` + `AC.UPGR.S`.

**Key decisions baked (confident, tight scope per Lens 4):** SUB-ITEM 1 packaging composes on `pip`/`pipx` + the existing `install-from-source.txt` dependency graph + the existing release-gate chain (no new CI); SUB-ITEM 3 composes on the SEALED migration engine + `loam migrate` verb + the `reversibility-primitive` envelope (zero re-implementation — D4 fast-follow); SUB-ITEM 4 composes on the existing `plugins/loam-skills/` surface.

**Forks needing an owner ruling (the two genuine owner-calls — see §3):** **F-FLATTEN** (flatten do/defer/partial — wide-blast, owner ruling; recommend DEFER) and **F-PUBLISH** (the public PyPI flip — public action, owner-gated; recommend AUTHORIZE after 1a packaging proves a clean-env install). A third, lower-stakes fork **F-INSTALL-MECH** (which install mechanism) carries a confident recommendation and is dispatcher-rulable.

**F2 on scope realism:** this cluster is **NOT a single dispatch** — it is 3–4 separate amendments (1a, 3, 4 autonomous + 1b owner-gated + 2 deferred-pending-ruling), correctly decomposed because each sub-item has a strictly tighter, independently-testable AC than the cluster (Lens 5 stopping criterion: further splitting 1a/3/4 adds only coordination overhead). They are **near-parallel but NOT fully parallel in one tree** — serialize the amendment builds (`feedback_serialize_amendment_builds`): 1a, 3, 4 each seal before the next applies, OR run in worktree-isolation. The owner-gated 1b + the deferred 2 do not block 3 + 4.

---

## §2 Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| Single installable package surface (1a) | **Framework, tracked** — a root-level or `loam-init`-anchored meta-package surface the builder selects; composes the existing per-component `loam-*` pyproject graph. | There is NO root `pyproject.toml` today (verified — no single installable package); the install surface is the multi-package `install-from-source.txt`. The builder picks the meta-package home (root meta-package vs `loam` umbrella vs the `pip install loam-cli loam-init …` published-set the README already names, line 85). |
| Dependency-graph lock + buildable wheels (1a) | **Framework** — the per-component `pyproject.toml` `dependencies` blocks (already carry inter-component bounds per `install-from-source.txt` header) + a verified build of each wheel. | The version discipline already lives in the pyproject `dependencies` blocks (install-from-source header §2–3); 1a hardens + proves it, does NOT re-invent it. |
| The public PyPI flip (1b) | **OWNER-GATED public action** — the `twine upload` / registry publish step + the name claim. Composes on the release-gate chain as the pre-flight. | Publishing a public package is a public action (`feedback_published_state_only_from_git_refs` discipline + Luke's "be careful with external/public actions"). Irreversible name claim. |
| Structure flatten (2) | **DEFERRED pending owner ruling** — touches every import path across `framework/<component>/`. | High blast radius + high redo cost + SEPARABLE from install (§F-FLATTEN). Not placed until ruled. |
| Migration auto-detect trigger (3) | **Framework** — a session-start contributor that INVOKES the sealed `loam migrate` verb; composes on the live session-start hook chain (shared with KP7/FBM activation). Effect mutates user-state under `<workspace>/.loam/` via the engine's envelope. | The trigger is a thin consumer of the verb (the verb is the engine entry-point); the always-on arm rides the existing session-start hook, NOT a new hook (mirror KP7's fail-soft contributor pattern). |
| Skill triage (4) | **`plugins/loam-skills/skills/`** (the installed-skill surface) + the skill frontmatter triggers. | The skills already live there (23 present); triage is trigger-verification + dead-skill retirement on the existing surface. |

---

## §3 Halt-and-surface BEFORE build — the forks (the two genuine owner-calls + one dispatcher-rulable)

Each carries my recommendation. **Recommendation IS the decision for the confident sub-items (1a, 3, 4 dispatch off this plan). Two forks are surfaced because reasonable people weigh signals differently OR a public action is involved (Lens 6 step 4 + Lens 7).**

### F-FLATTEN — structure flatten: do / defer / partial? *(OWNER RULING NEEDED — wide blast)*

**First, the framing the dispatch demanded, said loudly:**
> **The flatten is SEPARABLE from conventional install — it is NOT a prerequisite. Conventional install / packaging is achievable WITHOUT a disruptive repo-wide flatten.** Packaging composes the EXISTING per-component pyproject graph into one installable surface (or publishes the README's already-named `pip install loam-cli loam-init …` set); none of that requires moving a single import path. **Bundling the flatten into the install path would be a scope error** — it would couple a zero-blast, high-confidence, 1.0-load-bearing piece to a repo-wide, high-redo-cost refactor.

> **F2 / Ruthless Feedback on the roadmap's own framing:** the roadmap §5b describes the flatten as *"the cosmetic `framework/framework` doubling."* **That doubling DOES NOT EXIST.** Evidence: `ls framework/` shows components ONE level deep (`framework/loam-init/`, `framework/orchestrator/`, … — no `framework/framework/` directory; `ls framework/framework` returns nothing). The stale-claim class is exactly the built-≠-doc drift N2 exists to catch. **Alternative:** the roadmap §5b flatten row should be re-marked "the named `framework/framework` doubling is not present on disk as of `cc512b1f`; if a flatten is wanted, its actual target must be re-identified" — do NOT silently carry the stale target into a build brief.

- **Option A — DO the flatten now (before/with install).** REJECTED as a bundle: high blast radius (every import path), high redo cost, and the named target is absent. Only defensible if a concrete clean-install blocker is found that flattening uniquely fixes — none is (1a proves install works on the current layout).
- **Option B — DEFER (recommended).** Ship conventional install on the CURRENT layout; treat any flatten as a separate, independently-scoped hygiene cycle (§5b "ride any convenient cycle") AFTER 1.0, with its real target re-identified and the `pos-sync --ff-only` invariant named as the load-bearing constraint (roadmap §5b: "risk = keep `pos-sync --ff-only` working").
- **Option C — PARTIAL.** A narrow, low-blast cosmetic tidy (if a real small doubling is found at build time) decoupled from the import graph. Acceptable only if 1a EXAMINE surfaces a concrete small target; otherwise collapses to B.

**★ Recommendation: B (DEFER), and OWNER RULES.** **Signals:** scope↔confidence (LOW confidence the flatten is needed for install + the named target is absent → loosen + surface, do not bundle); blast-radius (repo-wide import rewrite — the highest-blast item in the cluster); reversibility (a flatten is high-redo-cost to undo); information-asymmetry (the owner may know a flatten reason — clean-install ergonomics, OSS first-impression — that the code does not show, so I recommend but do not decide). **This is owner-ruling because the owner may weigh OSS-first-impression / future-maintenance signals the code can't show; my evidence says SEPARABLE + DEFER, but the call is the owner's.**

### F-PUBLISH — the public PyPI flip: authorize now / after packaging-proof / hold? *(OWNER-GATED — public action)*

- The PUBLISH step (1b) claims a public package name on PyPI and pushes an installable artefact to the world. This is a **public action** (Luke's standing rule: be careful with anything public; ask first) + an **irreversible name claim**.
- **Option A — authorize the flip now (unconditional).** Premature — packaging readiness (1a) isn't proven yet.
- **Option B — authorize the flip CONDITIONAL on 1a proving a clean-env install from a local artefact index (recommended).** 1a builds + proves the install offline/locally (no public action); the owner then rules the public flip with a working artefact in hand. The name + index are the owner's to pick (`loam` vs `loam-cli` umbrella vs the README's published-set).
- **Option C — hold the public publish past 1.0.** Possible (1.0 could ship with the documented source-install + a private/local index), but it WEAKENS the 1.0 "non-technical user installs through a normal path" promise — the smoke's premise (§1) is a finished onboarding pipeline reached without dev-tree literacy.

**★ Recommendation: B — build + prove 1a autonomously now; surface the proven artefact + the name/index choice to the owner for the public flip.** **Signals:** public-action (the flip is the one genuinely public, owner-gated step — non-negotiable surface); reversibility (a PyPI name claim is irreversible — surface before claiming); value (the public install is the 1.0-load-bearing promise — so build everything UP TO the flip autonomously, gate only the flip). **OWNER RULES the flip + the name/index; everything up to it is autonomous.**

### F-INSTALL-MECH — which install mechanism for the non-tech + Windows + Claude-desktop-app user? *(dispatcher-rulable — confident recommendation)*

- **Option A — public PyPI package(s) + `pip install`.** The README's already-named target (line 85). Standard, but bare `pip` assumes a Python/venv-literate user — friction for non-tech.
- **Option B — `pipx install loam` (recommended primary).** `pipx` installs a CLI into an isolated managed venv with a single command + puts `loam` on PATH — the closest thing to a "normal documented path" for a non-technical user on a CLI tool, and it composes on the SAME published wheels as A. Cross-platform (incl. Windows).
- **Option C — Claude plugin-marketplace / `/plugin install` route** for the Claude-desktop-app + Cowork surface. This is the RIGHT surface for the **Windows + Claude-desktop-app consumer** (dispatch Lens 1) — but the desktop-app install methodology is **task #47's** (the platform-portability blueprint), NOT this cluster's to author. COMPOSE: this cluster ships the published wheels (A/B) that #47's plugin/desktop path then consumes.
- **Option D — private index.** A pre-publish staging surface only; not a user-facing 1.0 answer.

**★ Recommendation: ship A's published wheels as the substrate; document `pipx` (B) as the primary non-tech CLI path; and EXPOSE the wheels for #47's Claude-desktop / `/plugin install` route (C) WITHOUT authoring that route here (it's #47's fence).** The Windows + desktop-app surface is a **named consumer** that composes on this cluster's output, per the dispatch. **Dispatcher can rule this** (no public action in the recommendation itself — the public flip is F-PUBLISH); it shapes 1a's deliverable (build wheels installable by all three paths).

---

## §4 Spec-objective placement

- Binds to the **1.0 acceptance-smoke** (`docs/plans/loam-1.0-acceptance-smoke.md` §1 status + §7 sequencing): this cluster IS the "foundation polish (install/PyPI #21, migration auto-detect, skill triage #35)" the smoke is sequenced AFTER. The smoke's AC.SMOKE.1 (outcome-altitude: a real fresh `loam init`) DEPENDS on a stable install — which SUB-ITEM 1 hardens.
- Binds to the roadmap (`docs/plans/loam-roadmap.md`): SUB-ITEM 3 closes the §3 IN-FLIGHT "loam upgrade mechanism — auto-detect-on-upgrade hook"; SUB-ITEM 1 closes the §5b "PyPI publish / conventional install"; SUB-ITEM 4 closes the §5b "skill triage"; SUB-ITEM 2 resolves the §5b "structure flatten" (DEFER, with the stale-target finding recorded).
- **Ladders up to the prime objective** (`docs/VALUE_PROPOSITION.md` AC.PO.1/AC.PO.2 + the prime directive `feedback_loam_prime_directive_user_tuned_translation`): a non-technical user reaching a working, learning loam **without dev-tree literacy** is the prime directive's precondition — they bring WHAT (their work), loam owns HOW (install/upgrade/skills are pure HOW the user must never translate). Conventional install + auto-upgrade + working skills are the translation-burden removal that lets the per-user-tuned loop even START.

---

## §5 Acceptance criteria

AC IDs are scope-descriptive (`feedback_scope_descriptive_ac_ids`), not version-packed. Each is outcome-shape; **method-in-AC test passed:** every AC below can be satisfied by a method other than the one I have in mind (the builder may pick the meta-package shape, the trigger-module decomposition, the wheel-build tooling, the trigger's surfacing copy) — so they pin OUTCOME, not method.

### AC.PYPKG.* — a single installable package surface + a locked, buildable dependency graph (SUB-ITEM 1a — autonomous, no public action)
- **AC.PYPKG.1** — There is ONE documented install surface (a meta-package OR a named published-set) such that a single documented command resolves + installs the whole loam CLI dependency graph; the builder's chosen surface is named in one place, not re-derived per component. *(Outcome: one normal install entry-point, not a 20-line editable-install walk.)*
- **AC.PYPKG.2 (dep graph locks + builds)** — Every `loam-*` component's wheel BUILDS from its `pyproject.toml`, and the inter-component dependency bounds resolve into a consistent install set with no unresolved/conflicting constraint. *(Outcome: the dependency graph the install-from-source header documents is provably buildable + resolvable, not just editable-installable.)*
- **AC.PYPKG.3 (no public action)** — The full 1a deliverable is achievable + verified against a LOCAL artefact index (e.g. a local wheelhouse / `--find-links` dir), with ZERO publish to any public registry. *(Outcome: packaging readiness is proven before — and decoupled from — the owner-gated public flip.)*

### AC.INST.* — a clean environment reaches a working loam without dev-tree literacy (SUB-ITEM 1a)
- **AC.INST.1** — Installing from the unified surface into a Python environment that has NEVER seen the loam source tree puts the `loam` CLI on PATH and `loam --help` lists the real subcommands (`init`, `amend`, `migrate`, `release`, …) discovered through the entry-point group. *(Outcome: install ≠ checkout — a stranger with no clone gets a working CLI.)*
- **AC.INST.2 (non-tech-documented path)** — The documented install path is a normal, single-command-class flow (`pip`/`pipx`), and the README's source-only-is-intentional caveat (lines 84-87) is superseded by the conventional path for the published surface. *(Outcome: the documented path matches what a non-technical user can actually follow.)*
- **★ AC.INST.S (outcome-altitude: true)** — Running the install in a genuinely CLEAN environment (a throwaway venv / fresh container with no pre-arranged loam state, no source clone on PATH) from the unified surface, then `loam init <tmpdir>`, produces a WORKING freshly-initialized workspace (the real `loam init` entry-point runs to a scaffolded `.loam/` + a primary-persona greeting), with NO step requiring the user to clone or edit the framework tree. **This AC may NOT be satisfied by a unit test of the packaging metadata** — it must drive a real clean-env install + the real `loam init`. *(This is the 1.0-load-bearing proof the acceptance-smoke depends on; `feedback_test_outcome_altitude_required`.)*

### AC.UPGR.* — stale user-state is auto-detected + upgraded non-technically (SUB-ITEM 3)
- **AC.UPGR.1 (auto-detect)** — When a workspace's applied-migration cursor is behind the migrations shipped with the installed loam version, the session-start path DETECTS the gap (reads the cursor, enumerates pending declared migrations) without the user running anything. *(Outcome: stale state is noticed automatically, not on a manual `loam migrate`.)*
- **AC.UPGR.2 (composes the sealed engine + envelope)** — The auto-upgrade applies pending migrations by INVOKING the sealed `loam migrate` verb / engine wrapped in the existing `reversibility-primitive` backup-verify-rollback envelope — NOT a re-implemented apply path. *(Outcome: the trigger is a thin consumer of the sealed engine; zero re-implementation; the safety envelope is inherited.)*
- **AC.UPGR.3 (plain-language surface, non-tech-safe)** — After an auto-upgrade the user is told in plain language what was migrated (no SHAs / cursor internals / AC-IDs); on a migration FAILURE the rollback fires and the user is told the state was restored, not left half-migrated. *(Outcome: non-tech-safe UX — the four-step-loop surfacing + the protection-floor recoverability.)*
- **★ AC.UPGR.S (outcome-altitude: true)** — A genuinely SEPARATE instance (a temp `.loam/` workspace seeded at a real prior cursor version with real seeded user-state) reaches the session-start path with NO pre-arranged trigger state; the auto-detect fires, the wrapped replay runs through the intermediate migrations, the cursor reads the target version, the seeded user-state survives intact, and the plain-language surface reports it. **May NOT be satisfied by a unit test of the trigger function** — it must drive the real session-start entry-point against a real stale instance. *(`feedback_test_outcome_altitude_required`.)*

### AC.SKTRI.* — installed skills trigger; dead skills are retired (SUB-ITEM 4 — REMAINING scope)
- **AC.SKTRI.1 (triggers work)** — Each skill retained in `plugins/loam-skills/skills/` has a frontmatter trigger that fires on its intended natural-language shape (verified by a trigger-match check against representative phrasings), OR is explicitly removed. *(Outcome: a retained skill is reachable; a skill that can't be triggered is not silently retained.)*
- **AC.SKTRI.2 (dead skills retired)** — Skills with no working trigger / superseded / non-functional are REMOVED from the installed surface, with the removal recorded. *(Outcome: the installed surface is the live set, not an accreting graveyard.)*

**AC ladder-up:** every AC → its sub-item's roadmap row → the 1.0 acceptance-smoke's stable-install premise (AC.SMOKE.1's real `loam init`) → AC.PO.1/AC.PO.2 (a non-technical user reaches a working, learning, state-preserving loam without translation burden — the prime directive's precondition).

---

## §6 Build steps (method-level guidance only — builder's call per ODD §1.1) + the gating SEQUENCE

**The gating sequence (the dispatch asked which sub-items gate which — answered):**

```
SUB-ITEM 1a (packaging readiness, AUTONOMOUS) ──► [F-PUBLISH owner ruling] ──► SUB-ITEM 1b (public flip)
        │                                                                              │
        │ (a stable install)                                                           ▼
        └──────────────────────────────────────────────────────────► 1.0 ACCEPTANCE SMOKE
SUB-ITEM 3 (auto-upgrade trigger, AUTONOMOUS) ──────────────────────► (parallel; the smoke may exercise upgrade)
SUB-ITEM 4 (skill triage, AUTONOMOUS) ──────────────────────────────► (parallel; kernel-independent)
SUB-ITEM 2 (flatten) ── DEFERRED pending F-FLATTEN ruling ── does NOT gate anything in this cluster
```

- **1a GATES 1b GATES the smoke.** The smoke needs a stable install (its §7 sequencing); 1b's public flip needs 1a's proven artefact; 1a is the autonomous head.
- **2 (flatten) gates NOTHING here** — it is SEPARABLE (F-FLATTEN); the install path explicitly does not wait on it.
- **3 + 4 are parallel tracks** off the current tree (no dependency on 1 or each other), but **serialize the actual amendment builds in the same tree** (`feedback_serialize_amendment_builds`) — 1a, 3, 4 each apply+seal before the next applies, OR run in worktree-isolation.

**Per-sub-item build shape (the builder owns module decomposition):**

1. **SUB-ITEM 1a** — Manifest `docs/plans/foundation-polish-cluster-install.manifest.yaml`. EXAMINE the per-component `pyproject.toml` graph + `install-from-source.txt` header constraints + the `loam.cli.subcommands` entry-point discovery; DEFINE the single install surface (meta-package or published-set); BUILD wheels for each component + the unified entry-point; PROVE AC.INST.S in a clean throwaway env from a LOCAL wheelhouse (no public push); author the conventional-install README replacement (supersede lines 84-87 for the published surface). Apply + seal via `loam amend apply` / `loam amend seal` (`feedback_dispatch_explicit_loam_amend_apply`); NEW corrective commits on a miss, never `--amend`.
2. **SUB-ITEM 1b** — OWNER-GATED. Only after F-PUBLISH ruled: the public registry flip + name claim, run AFTER the full release-gate chain passes green. Record the publish in git refs (`feedback_published_state_only_from_git_refs`), not just prose.
3. **SUB-ITEM 3** — Manifest `docs/plans/foundation-polish-cluster-auto-upgrade.manifest.yaml`. EXAMINE the sealed `loam migrate` verb (`framework/state-migration-engine/src/loam/state_migration_engine/cli.py:build_migrate_subcommand`) + the live session-start hook chain (the KP7 fail-soft contributor pattern on `pos_session_start.py`) to confirm the compose points; BUILD a fail-soft session-start contributor that reads the cursor, and on a gap INVOKES the verb inside the reversibility envelope, then surfaces in plain language; the always-on session-start ARM stays owner-class to flip live (build the module + prove it; the live wiring is the owner-gated runtime step — mirror D4 + KP7's draft-gate). PROVE AC.UPGR.S against a temp stale instance (READ-ONLY-copy the live store into a temp root; never write the live pos3 store — the FBM cold-walk discipline). Apply + seal as above.
4. **SUB-ITEM 4** — Manifest `docs/plans/foundation-polish-cluster-skill-triage.manifest.yaml`. EXAMINE the 23 installed skills' frontmatter triggers; for each, verify the trigger fires on its intended shape OR retire it; record retirements. PROVE AC.SKTRI.1/2. Apply + seal as above. (Smaller; may ride a single amendment.)

---

## §7 Out of scope (deferred + when)

1. **The structure flatten (SUB-ITEM 2)** — DEFERRED pending F-FLATTEN owner ruling; SEPARABLE from install; its real target must be re-identified (the named `framework/framework` doubling is absent). Post-1.0 hygiene cycle if ruled DO.
2. **The Windows + Claude-desktop-app / `/plugin install` install methodology** — task #47's fence (the platform-portability blueprint). This cluster ships the wheels #47 consumes; it does NOT author the desktop-app path (F2 §10.4 — do not duplicate the blueprint).
3. **The full acceptance-smoke harness** (`docs/plans/loam-1.0-acceptance-smoke.md`) — sequenced AFTER this cluster; not built here. This cluster is its precondition, not its content.
4. **The migration ENGINE itself + the `loam migrate` verb** — already SEALED (`58bead7`). SUB-ITEM 3 wires the trigger ONTO it; it does NOT touch the engine.
5. **The full adaptive user-model / Phase-2 kernel mechanisms** — separate roadmap lanes (§5a); this cluster is foundation polish, not kernel.
6. **The carry-forward / selective-migration manifest** (roadmap Phase 3, gate G6) — a different, destructive-by-omission concern with its own owner gate; not this cluster.

---

## §8 Halt triggers (in-flight conditions that abort the build)

1. **A sub-item's build would require the flatten** — if 1a EXAMINE finds conventional install GENUINELY cannot work on the current layout without a flatten, HALT and surface (this would overturn F-FLATTEN's SEPARABLE verdict — the owner must re-rule). Evidence-first: state the specific blocker, generate ≥3 non-flatten alternatives, test each, halt only if all fail (`feedback_agent_empirical_recheck_before_halt`).
2. **1b's public flip is reached without an explicit owner ruling** — HALT; the public PyPI publish is a public action and NEVER fires autonomously (`feedback_published_state_only_from_git_refs` + Luke's public-action rule).
3. **SUB-ITEM 3 would re-implement any apply/replay/backup path** instead of composing the sealed engine + envelope — HALT (this is the migration-plan's #1 boundary-leak risk; the trigger is a THIN consumer of `loam migrate`, never a parallel engine).
4. **The auto-upgrade always-on session-start ARM would flip live without owner sign-off** — build the module + prove it; the LIVE runtime wiring is owner-class (mirror D4 + the KP7 activation pattern). Surface, don't flip.
5. **A sub-item's fence would touch a sealed component without a manifest entry** — HALT rather than silently widen the fence.
6. **Any step would remove/compress/overwrite live user-state** — G★ standing gate; surface-before-cut, reversible, dependency-checked. AC.UPGR.S READ-ONLY-copies the live store into a temp root; never writes it.

---

## §9 Bookkeeping

1. **`docs/plans/loam-roadmap.md`** — per sealed sub-item, move the row: §5b "PyPI publish / conventional install" → DONE (1a) / IN-FLIGHT-owner-gated (1b); §3 "loam upgrade mechanism — auto-detect hook" → DONE (3); §5b "skill triage" → DONE (4); §5b "structure flatten" → record the F-FLATTEN ruling + the stale-`framework/framework`-target finding (do NOT silently leave the stale target).
2. **`docs/STATE.md`** — amendment-row backfill per sealed sub-item (number confirmed at apply time; counter currently at 160).
3. **`docs/state-migrations/`** — SUB-ITEM 3 authors its own declared migration file IF it changes the cursor's shape (likely `structural-only` or `no-op`); the release-gate (gate 7) enforces this.
4. **`README.md` + `docs/install-from-source.md`** — SUB-ITEM 1a supersedes the source-only-intentional caveat (lines 84-87) for the published surface; `install-from-source.txt` stays as the contributor/dev path.
5. **`docs/plans/loam-1.0-acceptance-smoke.md`** — once 1a + 3 seal, the smoke's §1 "do NOT build until foundation polish seals" gate clears for those pieces; note it (the smoke's own build is a separate dispatch).
6. **Plan §14 register (per sub-item manifest's plan)** — each sub-item's builder narrates its D-decisions + backfills SHAs at seal.

---

## §10 F2 Ruthless Feedback (honest doubts; named design risks)

1. **The roadmap's flatten target is STALE — and bundling flatten into install would be the scope error this plan exists to prevent.** **Disagreement:** the roadmap §5b calls the flatten "the cosmetic `framework/framework` doubling" and pairs it with PyPI in one row. **Evidence:** `ls framework/` shows components one level deep — there is NO `framework/framework/` directory (`ls framework/framework` → nothing); and there is NO root `pyproject.toml`, so install is genuinely a packaging problem, not a layout problem. **Alternative:** keep them SEPARATE (this plan does — F-FLATTEN deferred, install ships on the current layout); re-mark the roadmap row's target as absent-and-to-be-re-identified rather than carrying the stale `framework/framework` string into a build brief. This is the built-≠-doc class N2 catches; caught here by reconciling against the tree.

2. **SUB-ITEM 3 is genuinely small + low-risk BECAUSE the engine is sealed — but the always-on session-start ARM is the one real owner-gated subtlety.** **Evidence:** the `loam migrate` verb is fully wired (`build_migrate_subcommand` present + entry-point declared + discovery loop resolves it); the migration plan's D4 already RULED "verb now, auto-detect fast-follow." **Risk:** the trigger that runs migrations automatically at session-start changes RUNTIME behaviour on every session of every workspace — that flip is owner-class (the same class as every prior live-activation flip: FBM, KP7). **Alternative:** build + prove the trigger module autonomously; gate ONLY the live session-start wiring (mirror the KP7 draft-gate + the FBM activation pattern). Do not flip it live in the build.

3. **"Single installable surface" hides a real builder fork the plan deliberately leaves open (correctly).** **Evidence:** three viable shapes — a root meta-package (`loam`), the README's already-named published-set (`pip install loam-cli loam-init …`, line 85), or a `loam`-umbrella that depends on the rest. **This is NOT a fork I surface to the owner** — it is method, inferable from the AC constraints (one documented command resolves the graph), and it's the builder's call per ODD §1.1. Naming it here so it is not mistaken for an un-surfaced owner decision: it is intentionally the builder's.

4. **The Windows + Claude-desktop-app surface is a CONSUMER, not this cluster's content — and conflating them would duplicate task #47.** **Evidence:** task #47 (platform-portability blueprint) is in_progress and owns the Windows / Cowork / `/plugin install` methodology; it is NOT yet on disk. **Risk:** F-INSTALL-MECH option C (the plugin route) is tempting to build here. **Alternative:** this cluster ships the published wheels #47's plugin/desktop path consumes (Lens 1 compose), and explicitly fences the desktop-app install methodology OUT (§7.2). The dispatch named this exact composition; I honour it.

5. **Skill-triage scope-drift risk.** **Evidence:** task #35 is greenlit/in_progress; the roadmap §5b frames it as "the manual first pass the [capability-adoption] loop later automates." **Risk:** a builder could re-plan the whole skill ecosystem. **Alternative:** SUB-ITEM 4's AC fence is REMAINING scope only — verify-triggers + retire-dead on the existing 23-skill surface; the automated adoption loop is explicitly OUT (a separate roadmap lane).

---

## §11 Provenance trail (load-bearing sources)

- **Migration engine + `loam migrate` verb SEALED + wired:** `framework/state-migration-engine/pyproject.toml:20-24` (the `migrate` entry-point), `…/src/loam/state_migration_engine/cli.py:53` (`build_migrate_subcommand`), `framework/tools/loam/src/loam_cli/cli.py:40-64` (the `loam.cli.subcommands` discovery loop); seal `58bead7`; engine `c08cbcb`/`6587e94`. The D4 "verb-now / auto-detect-fast-follow" ruling: `docs/plans/loam-migration-engine-and-release-gate-slice-plan.md` §3 D4 + §7 item 2.
- **Install substrate + the future-PyPI promise verbatim:** `install-from-source.txt` (header §1–3 — the multi-package editable-install graph + the version-discipline lives in pyproject `dependencies`); `README.md` lines 48-87 (the source-only install + the "future minor ships from PyPI" caveat); `docs/install-from-source.md`.
- **No root package / no `framework/framework`:** verified — no `pyproject.toml` / `setup.py` at repo root; `framework/` holds components one level deep (no `framework/framework/`). This is the F-FLATTEN + §10.1 evidence.
- **Release-gate chain to compose ON (Lens 1, no new CI):** `framework/tools/loam/src/loam_cli/release/gates.py` (`ALL_GATES`; gates 7/8/9). The flatten's load-bearing invariant (`pos-sync --ff-only`): roadmap §5b.
- **Reversibility envelope the auto-upgrade inherits:** `framework/reversibility-primitive/` (the migration engine already wraps it).
- **The smoke this cluster gates:** `docs/plans/loam-1.0-acceptance-smoke.md` §1 (foundation-polish-first status) + §7 (sequencing: foundation polish → smoke → 1.0 label).
- **The roadmap rows this cluster closes:** `docs/plans/loam-roadmap.md` §3 (upgrade mechanism IN-FLIGHT), §5b (flatten + PyPI; skill triage).
- **Platform-portability blueprint (named consumer, NOT duplicated):** task #47 (in_progress; not yet on disk) — the Windows + Claude-desktop-app surface.
- **AC-ID + plan-doc shape conventions:** `plugins/dev-sdlc/docs/conventions/plan-docs.md`. Shape exemplar: `docs/plans/loam-migration-engine-and-release-gate-slice-plan.md`.
- **Discipline sources:** `feedback_test_outcome_altitude_required` (the two outcome-altitude ACs), `feedback_published_state_only_from_git_refs` + Luke's public-action rule (F-PUBLISH gating), `feedback_serialize_amendment_builds` (the build serialization), `feedback_scope_descriptive_ac_ids` (AC IDs), `feedback_dispatch_explicit_loam_amend_apply` (apply/seal naming), `feedback_version_numbers_at_release_time` (no pre-baked amendment number).

---

## §14 Method-decision register (populated by the builder at build time per sub-item)

Placeholder — each sub-item's builder narrates its D-decisions (D-INST.\*, D-UPGR.\*, D-SKTRI.\*) + backfills commit SHAs at seal. The owner rulings (F-FLATTEN, F-PUBLISH, F-INSTALL-MECH) are recorded here once issued, before the gated sub-items dispatch (`feedback_record_owner_ratification_before_dispatch`).

### SUB-ITEM 1a — rulings + D-decisions (2026-06-01)

**R-INST.A — Option-A fence-widen (dispatcher ruling, 2026-06-01).** SUB-ITEM 1a's
fence is WIDENED from two components (loam-init + loam-cli) to **three** (adds
`workspace-bootstrap`). Rationale: the prior EXAMINE pass proved that conventional
install is NOT pure packaging for the outcome-altitude AC.INST.S — a clean-env
`loam init` fails with `persona-template-not-found` because the first-run scaffold's
framework-data resolver (`first_run_scaffold.py:_resolve_persona_template_dir`)
walks `Path(__file__).parents` for the persona template, which from a wheel install
sits under `site-packages/` and never finds the template even though `loam init`
clones it into `<ws>/framework/`. The fix resolves framework data against the cloned
workspace; it lives in `workspace-bootstrap`. The 1a amendment ships the packaging
surface + this resolver fix + the install-from-source.txt completion as ONE
multi-component sealed amendment. AC.INST.S stays the LOAD-BEARING outcome-altitude
AC (NOT downgraded). Recorded into the manifest's `components` block + title before
any source edit (plan-before-code + record-ratification-before-dispatch).

**Correction to §2 / §10.3 'pure packaging' assumption.** The plan asserted
conventional install is "pure packaging — none of that requires moving a single
import path / touching source." That holds for AC.PYPKG.\* + AC.INST.1 (the CLI
surface) but is FALSE for AC.INST.S (the working `loam init`): that AC requires the
workspace-bootstrap resolver source fix. The assumption is corrected here; the fix
is folded into 1a under the Option-A widen. (This does NOT reopen F-FLATTEN — no
flatten is involved; the fix is a 30-line resolver change inside one component.)

**D-INST.1 — install surface = dependencies-only `loam` meta-distribution + the
README published-set.** `loam` is a PEP 420 implicit-namespace package (no top-level
`loam/__init__.py` exists; every component ships `loam.<sub>` only). A meta-package
literally named `loam` must therefore ship ZERO `loam/` package code — it is a
dependencies-only distribution whose `dependencies` pull the CLI closure. `pipx
install loam` (the F-INSTALL-MECH-recommended primary) then resolves the whole graph
in one command. The README's explicit published-set (`pip install loam-cli loam-init
…`) is documented as the equivalent form. Meta-package home: inside the loam-init
fence (`framework/loam-init/meta/`) so no new root-level file is needed (a root
`pyproject.toml` would also trip every seal-test's fence — it is in no allowed set).

**D-INST.2 — resolver fix composes on `_resolve_plugins_root`.** The persona-template
resolver gains a `workspace_root` parameter and checks the cloned-framework
locations first (the doubled `<ws>/framework/framework/...`, the single-level
`<ws>/framework/...`, and `<ws>/...` for canonical pos-v2), then falls back to the
existing `__file__` parents-walk for the editable dev tree. This mirrors the
two-case workspace-relative pattern `_resolve_plugins_root` already uses (Lens 1 —
no reinvention).

**D-INST.3 — install-from-source.txt completion.** `loam-state-migration-engine`
(a transitive runtime dep: self-correction → state-migration-engine; self-correction
is pulled by workspace-bootstrap) was MISSING from `install-from-source.txt`. Added
as a Tier-F partner line. The component itself is NOT bumped/edited (it sits at
0.13.0 while the rest are 0.14.0; the unpinned inter-component deps absorb the skew —
the prior pass proved the full closure resolves with it at 0.13.0). No fourth
component is touched.

### SUB-ITEM 1a — build SHAs + the seal HALT (2026-06-01)

Branch `plan/foundation-polish-install` (worktree `/Users/lukeivers/loam-wt-pkg`):
- **apply** `da8f7c88` — `loam amend apply` auto-commit (new meta-package + AC tests +
  seal-test widenings + sidecar bumps; BASELINE confirmed `cc512b1f`).
- **corrective** `95996e23` — folds the apply-missed modified-tracked source (the
  workspace-bootstrap resolver fix, the install-from-source.txt completion, the
  loam-init pytest markers, the manifest 3-component fence + this register). The apply
  step only auto-stages the NEW files handed to it pre-staged + its own tool-managed
  edits; modified tracked files not pre-staged were left in the working tree, so a NEW
  corrective commit folds them in (never `--amend`).
- **corrective** `84906b51` — makes AC.INST.S hermetic: builds wheels from tmp copies
  so `python -m build` leaves no `build/` artefact in the source tree (which had
  tripped workspace-bootstrap's d2 inline-path scanner on `build/lib/...`).

**AC verification (all GREEN locally):** AC.PYPKG.1/2 (7 tests), the resolver-unit
half of AC.INST.S (7 tests), and ★ the outcome-altitude AC.INST.S end-to-end (real
wheel build → clean throwaway venv → `pip install loam` from a local wheelhouse →
`loam --help` lists `init/amend/release` → real `loam init` → persona template
resolves from the cloned framework → runtime data present). The full workspace-
bootstrap suite is 556 passed / 15 skipped EXCEPT the LIVI family (below).

**SEAL HALT (surfaced, not silently worked around).** `loam amend seal` runs the
touched components' FULL suites; workspace-bootstrap's `AC.LIVI.*` integration tests
bootstrap a workspace from canonical-`main` (`git clone <LOAM_ROOT>` then
`checkout origin/main`). The worktree's local `main` is pinned at `5999fb95` (checked
out at the sibling `/Users/lukeivers/loam` worktree; not movable here), so the LIVI
clone gets the OLD `install-from-source.txt` WITHOUT the state-migration-engine line →
`_provision_framework_venv`'s `pip install -r install-from-source.txt` fails on the
unresolvable bare-name dep → 10 errors + 1 fail. This is **pre-existing** (verified
identical on pristine `5999fb95` with all 1a changes stashed — the four-test
no-false-fault passes: NOT this amendment's regression) and is exactly the
install-graph hole this amendment REPAIRS — it clears the moment `main` carries the
fix. Proven transitively: AC.INST.S green (the same `bootstrap_new_workspace` path,
driven from a FIXED canonical) ⟹ LIVI green from fixed `main`. The seal cannot
observe green in this worktree because making it so requires advancing local `main` =
a merge-to-main action the dispatch reserves to the dispatcher (merge-on-seal).
Recommended sequencing: dispatcher merges `da8f7c88..84906b51` to `main`, THEN runs
`loam amend seal` (LIVI then clones fixed main and passes); or seals with the LIVI
family acknowledged as pre-existing-cleared-by-this-fix.

### SUB-ITEM 4 — skill triage rulings + D-decisions (2026-06-01)

Branch `plan/foundation-polish-skill-triage` (worktree
`/Users/lukeivers/loam-wt-skilltri`); single-component fence on
`plugins/loam-skills/`; BASELINE `19a14b91` (the SUB-ITEM 1a seal —
this branch's HEAD; `git rebase main` was a no-op). Amendment #162
(highest manifest counter on disk was 161 = 1a; confirmed at apply
time). Apply + seal SHAs backfilled at cycle close.

**Scope held: REMAINING scope only.** Verify-triggers + retire-dead on
the EXISTING 22-skill surface. The skill-ecosystem re-architecture and
the automated capability-adoption loop are a SEPARATE roadmap lane and
were NOT touched (§10 item 5 fence honoured; no drift halt fired).

**D-SKTRI.MATCH — deterministic trigger-match, NOT a live LLM probe.**
Claude's skill-load decision reads the `description` frontmatter; the
ODD-deterministic proxy for "the trigger fires on the intended shape"
is discriminating-token overlap between a curated representative-
phrasing table (the intended NL shapes) and each skill's trigger
surface (description + body). Composes on the in-plugin AC.SKILLCAP.
{2,3,4} substring-trigger-match technique (Lens 1 — no new matcher).
A live `claude -p` probe would be non-deterministic + trip the
no-API-key / determinism discipline; rejected. Tolerance: one
non-matching content token per phrasing (a user's phrasing need not be
a verbatim substring); two+ absent = a non-firing trigger.

**D-SKTRI.TABLE — the phrasing table is asserted to EXACTLY mirror the
installed surface.** A phantom table entry would mask a real
retirement; a missing entry would leave a skill unverified. Drift
between table and disk is itself a test failure
(`test_table_matches_installed_surface`).

**D-SKTRI.CONSUMER — "live consumer" = any tracked file outside the
skill's own directory + the plugin tests that names the skill (git
grep).** This IS the §15 no-live-consumer retirement gate. A retained
skill at zero consumers fails AC.SKTRI.2 (graveyard surface) → the
retire-or-wire-a-consumer signal.

**D-SKTRI.RETIRE-NONE — ZERO retirements.** TRIAGE OUTCOME: all 22
installed skills meet all three retention criteria — (1) firing
trigger on intended shape (AC.SKTRI.1 green), (2) not superseded
(substantive bodies; each owns a distinct intended-shape band — the
four scheduling primitives cron-create / launchd-plist /
schedule-wakeup / loop-command partition the cadence axis and name
each other COMPOSES-WITH, not supersedes), (3) ≥3 live consumers each
(lowest: cron-create, monitor-tool, run-in-background-bash,
schedule-wakeup at 3). No skill meets a retirement criterion; the
RETIRED map is empty. **F2 on the roadmap framing:** the §5b row's
"retire dead ones" assumed a graveyard the evidence does not show —
the installed surface is already the live set. Recorded, not silently
carried.

**HALT TRIGGERS (cluster §8 / §10 item 5 — none fired):** no scope
drift into ecosystem re-architecture / adoption loop; no retirement
that would break a live consumer (zero retirements; the live-consumer
scan is the gate); no ODD violation / method-in-AC (both AC.SKTRI.*
satisfiable by outcome-shape tests, method left to the builder); no
rebase conflict (`git rebase main` no-op); no sealed-component fence
touched without a manifest entry (single-component loam-skills fence;
only `plugins/loam-skills/` + `docs/` bookkeeping touched).

**AC → test map:**
- AC.SKTRI.1 → `plugins/loam-skills/tests/test_AC_SKTRI_1_triggers_
  fire_on_intended_shape.py` (table-mirror assertion + per-skill
  trigger-fire on intended shape).
- AC.SKTRI.2 → `plugins/loam-skills/tests/test_AC_SKTRI_2_dead_skills_
  retired.py` (retired-dir-absent + retirement-recorded + per-skill
  live-set invariant / no-live-consumer gate).

## §15 Backwards-compat verification (per sub-item)

- SUB-ITEM 1a: the existing `install-from-source.txt` editable path STILL WORKS (contributors/dev); the published surface is ADDITIVE, not a replacement of the dev path.
- SUB-ITEM 3: the existing live session-start hook chain (FBM/KP7 contributors) is PRESERVED + fail-open — a broken auto-upgrade contributor never breaks session-start (the KP7 fail-soft invariant).
- SUB-ITEM 4: retiring a skill does not break a workflow that referenced it — verify no live consumer before removal.

## §16 Halt-and-surface findings (raised + ruled at plan-authoring)

- **Stale flatten target** (§10.1) — the roadmap's `framework/framework` doubling is absent on disk; surfaced, recorded as the F-FLATTEN evidence, roadmap row to be corrected at bookkeeping.
- **Flatten SEPARABLE from install** (F-FLATTEN) — surfaced as the dispatch demanded; recommend DEFER; OWNER RULES.
- **Public PyPI flip is a public action** (F-PUBLISH) — surfaced; everything up to the flip is autonomous; OWNER RULES the flip + name/index.
- **AC.INST.S needs a workspace-bootstrap source fix, not just packaging** (raised at 1a EXAMINE, RULED Option-A 2026-06-01) — the clean-env `loam init` fails with `persona-template-not-found` because the first-run scaffold resolves the persona template `__file__`-relative (misses under a wheel install). This overturned the §2/§10.3 'pure packaging' assumption for AC.INST.S only. Dispatcher RULED Option-A (widen the 1a fence to add workspace-bootstrap); recorded in §14 R-INST.A + the manifest. NOT a flatten and NOT a fourth component — the fix is contained in workspace-bootstrap.
