# v0.7.1 PATCH — v1.0-readiness cleanup (defect-closure for v0.7.0's shipped outcome shape)

**Status:** plan-only at authoring time. Plan-before-code per `feedback_plan_before_code` (hard rule). Owner pre-ratified scope via Telegram 10663 (close the v1.0-readiness gaps surfaced in the audit).
**Slug:** `v0-7-1-v1-0-readiness-cleanup`.
**Date authored:** 2026-05-10.
**Class:** **PATCH** per `docs/release-versioning-policy.md`. No new outcome capability — closes defects in v0.7.0's shipped outcome shape ("non-tech user reaches working software"). Specifically: makes documented features actually work for a fresh-install stranger, removes documentation drift introduced by recent ships, structurally enforces what the v0.7.0 release-process gate didn't catch.
**Predecessor:** v0.7.0 (sealed `1e6fc76`, tag `03060ef`, published 2026-05-09).
**Working directory:** `/Users/lukeivers/loam/`.
**Owner authorization:** dispatched 2026-05-10 (build-cycle dispatch); covers plan-doc authoring + build + seal. Publish remains owner-asked per ASK-FIRST.

---

## §1 — Outcome shape (the "why")

The v1.0-readiness audit at `workspace/.scratch/claude-output/v1-0-readiness-verification-2026-05-10.md` graded loam **NOT v1.0-ready today** with three RED gaps and four YELLOW gaps, all defect-shaped (not missing-capability-shaped). The audit's recommended close path estimates 150-275 min AI-time; this plan-doc operationalises that close path as v0.7.1.

The aggregate effect: a stranger with a fresh `git clone lukeivers/loam` can run the documented quickstart, hit `loam --help` + `loam amend --help` + `loam release --help` + `loam project --help` cleanly, follow the documented amendment workflow (`loam amend apply <manifest>`) without surprise, and read the docs (README + architecture.md + components/index.md + STATE.md + release-roadmap.md + memory.md) without encountering contradictory or stale claims. v0.7.1 closes the gap between "documented" and "operational" that the v0.7.0 ship surface.

**Why now.** v0.7.0 makes v1.0 criterion #2 ("one real user has shipped real software") empirically reachable; v0.7.1 closes the criterion #1 gaps ("all documented features work as advertised") + criterion #4 gaps ("plugin contract stable through 0.x — install path part of the frozen surface") so v1.0 is reachable in one further session.

**Why patch (not minor).** Per SemVer policy, MINORs add outcome capability; PATCHes close defects within an already-shipped outcome. The audit findings are all defect-shaped (broken install path; stale docs; doc-count drift; under-documented existing CLI verb; structural enforcement gap that masked the install-path defect). No new user-facing capability ships at v0.7.1.

## §2 — Prime objective ladder

```
VALUE_PROPOSITION.md prime objective
   └─ "primary persona is a translation layer between the user's
       natural-language intent and AI-effective execution"
        └─ a non-tech user reaches working software via natural
            language only (NTU outcome — shipped at v0.7.0)
             └─ that NTU outcome is empirically reachable for a
                 fresh-install stranger (criterion #1)
                  └─ v1.0 quality-bar criterion #1 ("all documented
                      features work as advertised") becomes GREEN
                  └─ v1.0 quality-bar criterion #4 ("plugin contract
                      stable through 0.x") YELLOW → GREEN via
                      install-path inclusion of the only shipped
                      plugin's tooling subpackage
```

The two VALUE_PROPOSITION tests:
- **Primary-persona test** — every AC reduces translation burden by removing a defect that would force the user to translate around (figuring out why `loam amend` doesn't exist; reconciling roadmap claims that v0.6.0 "awaits publish" with the published tag at origin; deciding whether the README or architecture.md component count is correct).
- **Harness test** — every AC adds to or repairs an existing primitive of the harness toolkit (the canonical install path; the public-surface manifest; the release-process HARD smoke).

## §3 — Component fence

Multi-component patch; tight surface per AC. Components touched:

**PRIMARY:** `framework/tools/loam/` — release CLI HARD-smoke gate extension (AC.READY.7) verifying the system binary path. Also: install-from-source.txt addition (the canonical install spec lives at the repo root; not under any component fence — universal-admission).

**PRIMARY:** Universal-admission docs — `docs/STATE.md`, `docs/release-roadmap.md`, `README.md`, `docs/architecture.md`, `docs/components/index.md`, `docs/components/memory.md`, `docs/release-process.md`, `install-from-source.txt`, plus a new `docs/public-surface-manifest.md` (AC.READY.9) and a new `docs/experiments/v0-7-1-hard-smoke.md` writeup.

**SECONDARY:** `plugins/dev-sdlc/` — only if AC.READY.7's HARD-smoke extension touches the dev-sdlc smoke writeup or the loam-amend plugin's install discovery shape; otherwise untouched.

**Untouched:** All other components. No edits to `framework/objective-tracker/`, `framework/scope-of-work/`, `framework/per-project-pm/`, `framework/cost-governance/`, `framework/safety-layer/`, `framework/orchestrator/`, `framework/dormancy/`, `framework/observability-aggregator/`, `framework/reversibility-primitive/`, `framework/self-correction/`, `framework/self-upgrade/`, `framework/telegram-interface/`, `framework/loam-init/`, `framework/hands-off-lifecycle/`, `framework/workspace-sync/`, `framework/primary-persona/`, `framework/workspace-bootstrap/`.

**New components:** None.

## §4 — Acceptance criteria

Eight ACs (AC.READY.1 through AC.READY.8) plus the public-surface manifest AC (AC.READY.9) plus the seal-diff AC (AC.READY.S). AC IDs use the scope-descriptive `READY` family per `feedback_scope_descriptive_ac_ids` (the work scope is "v1.0-readiness").

### AC.READY.1 — System `loam` binary on dispatcher's machine reinstalled correctly

**What:** RED-1 fix from the audit. The `/opt/homebrew/bin/loam` shim is broken because every dependent loam package in the system Python's site-packages is editable-installed pointing at `/Users/lukeivers/ivers-corp-pos-v2/...` (a directory that no longer exists post-v0.5.1 split-worktrees migration).

**Acceptance:** Verify by running `which loam` (returns `/opt/homebrew/bin/loam`) + `/opt/homebrew/bin/loam --help` from a fresh shell — exits 0; lists the 6 documented subcommands (`init`, `release`, `odd-extract`, `onboard`, `project`, `amend`); no `ModuleNotFoundError` stacktrace. Operational fix is `pip uninstall -y` of every stale loam package + `pip install -r install-from-source.txt` (with the AC.READY.2 update applied, so the reinstall picks up `loam-amend`).

`outcome-altitude: false` — operational fix; verified by direct CLI invocation against the maintainer's host.

### AC.READY.2 — `loam amend` verb added to install-from-source path

**What:** RED-2 fix. Fresh `pip install -r install-from-source.txt` into a clean venv currently yields a `loam` binary missing the `amend` subcommand because `plugins/dev-sdlc/tools/loam-amend/` is NOT listed in `install-from-source.txt`. Documented amendment workflow (`loam amend apply <manifest>` per `docs/dev-mode-getting-started.md` and the dispatch-brief authoring SKILL) breaks for any stranger following the documented install path.

**Acceptance:** (a) `install-from-source.txt` adds `-e ./plugins/dev-sdlc/tools/loam-amend` (after `plugins/dev-sdlc/` so the plugin parent is resolvable); also adds `-e ./plugins/dev-sdlc/pr-safety` (closes YELLOW-3 at the install layer too, since the plugin is shipped + the verb works once installed) and `-e ./plugins/dev-sdlc/tools/loam-mode` (the dev-mode auto-load partition selector — also missing). And `-e ./framework/per-project-pm` (also missing from install-from-source.txt despite being a runtime component listed in `docs/components/index.md`). (b) Verification probe: cold-venv install into `/tmp/loam-test-venv-v071/`, then `loam --help` lists `amend` + `pr-safety` subcommands; `loam amend --help` lists `validate / apply / seal / template / new-plan / new-memory`; `loam pr-safety --help` returns clean usage.

`outcome-altitude: false` — implementation-altitude AC; cold-venv probe sufficient.

### AC.READY.3 — STATE.md + release-roadmap.md updated to remove stale "awaiting publish" claims for v0.6.0 + v0.7.0

**What:** RED-3 fix. Both v0.6.0 + v0.7.0 are published (tags pushed to origin: `81443ef` for v0.6.0, `03060ef` for v0.7.0). Roadmap §3 active-version section + §2 shipped table + STATE.md rollups all claim "sealed local; awaiting dispatcher dogfood publish" — stale.

**Acceptance:** (a) `docs/release-roadmap.md` line 67 updates the "v0.1.0 → v0.5.1 published; v0.6.0 + v0.7.0 sealed local awaiting publish gate" sentence to reflect v0.6.0 + v0.7.0 published; (b) line 75's "SHIPPED LOCAL ... awaiting dispatcher dogfood publish per ASK-FIRST" replaced with "SHIPPED PUBLIC 2026-05-09 (tag `v0.6.0`, annotated `81443ef`)" + analogous for v0.7.0 with tag `03060ef`; (c) `docs/STATE.md` analogous rollup row added or updated for both v0.6.0 + v0.7.0 marking SHIPPED with seal+tag SHAs. Verification: `grep -n "awaiting publish\|SHIPPED LOCAL" docs/release-roadmap.md docs/STATE.md` returns zero hits referencing v0.6.0 or v0.7.0.

`outcome-altitude: false` — documentation-fidelity AC; grep-verifiable.

### AC.READY.4 — Component-count reconciliation across README + architecture.md + components/index.md

**What:** YELLOW-1 fix. Three docs claim eighteen runtime components; `docs/architecture.md:270` claims "all 15 components" in the same doc as the eighteen-claim ~150 lines earlier. The canonical count is **18 runtime components** per the table in `docs/components/index.md` (verified — table has 18 rows). The architecture.md self-conflict (the "15" wording) is a residual edit artefact.

**Acceptance:** (a) `docs/architecture.md:270` "summaries of all 15 components in a single table" → "summaries of all 18 components in a single table"; (b) all three docs (README, architecture.md, components/index.md) state the same count (18) consistently; (c) `grep -n "15 components\|fifteen components" docs/` returns zero hits in user-facing docs. (Historical references in docs/v0-3-0-feature-honesty-audit.md describing what the count WAS at v0.3.0 are exempt — those are audit-history.)

`outcome-altitude: false` — documentation-fidelity AC; grep-verifiable.

### AC.READY.5 — `docs/components/memory.md` reflects post-rip-out reality

**What:** YELLOW-2 fix per the audit. **Plan-time empirical re-verification** — `grep -i "graphiti" docs/components/memory.md` returns ZERO hits. The audit's YELLOW-2 framing is over-stated; the doc has already been rewritten to reflect file-backed-episode (FBE) memory as canonical with no Graphiti residue. The doc reads cleanly at HEAD `8b129e9` (verified at plan-time).

**Acceptance:** Two-part — (a) re-verify YELLOW-2 finding at plan-doc-build-time (the doc is already clean) — record verdict as `GREEN — already-clean at HEAD; YELLOW-2 was over-stated by the audit per F2 surface-discoverable-from-plan-time grep`; (b) optional cleanup pass — verify `docs/components/memory.md` carries no other backlog-deferred references (graph-of-episodes is correctly named "post-v0.1.0 backlog" — that's accurate). No code edit required if (a) confirms clean.

`outcome-altitude: false` — documentation-fidelity AC; grep-verifiable. Per F2: surface the audit over-statement honestly rather than manufacture a fix-for-the-sake-of-fix.

### AC.READY.6 — `loam pr-safety` documentation in user-facing surface

**What:** YELLOW-3 fix. The `loam-pr-safety` package ships at `plugins/dev-sdlc/pr-safety/` (verified — `pyproject.toml` declares `loam.cli.subcommands` entry-point `pr-safety = "loam_pr_safety.cli:build_pr_safety_subcommand"`). The verb is undocumented in user-facing surface (`docs/components/index.md`, `docs/architecture.md`, README all silent).

**Acceptance:** (a) `docs/components/index.md` adds a row for `pr-safety` under an appropriate group (likely "Composition + lifecycle" or new "Dev/SDLC plugin verbs" sub-section), OR `docs/plugins/dev-sdlc.md` adds a `loam pr-safety` subsection; (b) the addition cites the canonical doc-of-record for the verb (the package's own README at `plugins/dev-sdlc/pr-safety/README.md` if present, or its `pyproject.toml` description as fallback); (c) verification: `grep -rn "pr-safety\|pr_safety" docs/` returns at least one hit in user-facing docs (not just historical).

`outcome-altitude: false` — documentation-fidelity AC; grep-verifiable.

### AC.READY.7 — Release-process HARD-smoke gap closure (system-binary-path coverage)

**What:** YELLOW-4 fix + structural enforcement. The `loam release` HARD-smoke gate verifies a workspace-internal smoke writeup but does NOT verify the `loam` binary itself is operational on the maintainer's machine. This is what masked RED-1 — v0.6.0 + v0.7.0 both shipped with the binary broken because the gate trusted the writeup file. Future releases need a HARD-smoke step that exercises the system binary path (`which loam && loam --help` returning exit 0).

**Acceptance:** (a) `docs/release-process.md` §1 (pre-publish gates table) gains a new gate row for `system-binary-operational` — checks that `which loam` resolves AND `loam --help` exits 0 AND the help output lists the documented subcommands; (b) the gate is described in plain prose; structural CLI implementation is OUT OF SCOPE for v0.7.1 (a CLI extension is MINOR-class — out per §6); (c) the v0.7.1 HARD-smoke writeup at `docs/experiments/v0-7-1-hard-smoke.md` includes a section verifying the system binary IS operational (closing the loop forward — v0.7.1's own publish gate exercises the new check manually). The structural CLI implementation is captured as a v0.8.0+ candidate in FUTURE_IDEAS_DRAFT.md (out-of-scope for this patch but tracked for follow-on).

`outcome-altitude: false` — documentation + writeup AC; gates-table-update + smoke-writeup verification.

### AC.READY.8 — Stranger-clone fresh-install outcome-altitude probe

**What:** Cold-clone + cold-venv + invoke every documented top-level CLI verb + verify clean usage + no broken-import errors. Real-execution probe per the test-altitude rubric — invokes production entry-points (the actual `pip install` against a fresh venv; the actual `loam` binary built by that install). Inputs are realistic (not pre-arranged state).

**Acceptance:** (a) Probe at `docs/experiments/v0-7-1-hard-smoke.md` documents the cold-clone walkthrough (clone to `/tmp/loam-stranger-clone-v071/`, `python3.13 -m venv .venv`, `.venv/bin/pip install -r install-from-source.txt`, then iterate `loam --help`, `loam amend --help`, `loam release --help`, `loam project --help`, `loam onboard --help`, `loam odd-extract --help`, `loam init --help`, `loam pr-safety --help`); (b) every invoked verb returns exit 0 with usage text; (c) no `ModuleNotFoundError` / `ImportError` / `argparse: invalid choice` errors in any output; (d) writeup names empirical wall-clock + the `pip list` output (showing every loam package installed against the fresh venv's path, not against `ivers-corp-pos-v2/`). Build report records the probe verdict.

`outcome-altitude: true` per `feedback_test_outcome_altitude_required`. Risk band: **production-facing** (per the rubric sub-rule — user-visible CLI surface; HARD per-cycle REQUIRED).

### AC.READY.9 — Public-surface manifest for the 6-month backwards-compat commitment

**What:** Authoring of the public-surface manifest the audit §3 "Forward-commitment concerns" calls out as the structural prerequisite for the 6-month commitment to be realistic (not aspirational). Doc at `docs/public-surface-manifest.md` listing what's covered by the v1.0 backwards-compat commitment + what's explicitly NOT covered.

**Acceptance:** (a) Doc exists at `docs/public-surface-manifest.md`; (b) lists each public surface in named sections — CLI verbs (`init`, `release`, `odd-extract`, `onboard`, `project`, `amend`, `pr-safety`); plugin entry-point group names (`loam.bootstrap.contributions`, `loam.cli.subcommands`); workspace-bootstrap manifest fields (`primary_channel`, `safety_profile`, `channel_preference`); file-based memory contract (`<workspace>/.loam/memory/` directory shape; episode YAML schema sketch); hook contracts (SessionStart, UserPromptSubmit, Stop); on-disk conventions (workspace `.loam/` + `.pos/` directories); (c) explicitly names NON-public surfaces (internal Python modules, private subpackages, CLI internals); (d) cites authority — `docs/release-versioning-policy.md` §1.0.0 + `docs/release-roadmap.md` v1.0 entry. The manifest is the deliverable; structural enforcement (a test that fails if any surface drifts) is OUT OF SCOPE for v0.7.1 (captured for v0.8.0+).

`outcome-altitude: false` — documentation AC; structural authoring deliverable.

### AC.READY.S — Seal-diff discipline

`git diff --name-only BASELINE..SEAL_COMMIT` shows changes only under:

- `install-from-source.txt` (AC.READY.2 — universal-admission)
- `docs/release-roadmap.md` (AC.READY.3 — universal-admission)
- `docs/STATE.md` (AC.READY.3 — universal-admission)
- `docs/architecture.md` (AC.READY.4 — universal-admission)
- `docs/components/index.md` (AC.READY.4 + AC.READY.6 — universal-admission)
- `docs/components/memory.md` (AC.READY.5 only if a cleanup pass is needed; otherwise untouched per F2 audit-over-statement finding)
- `docs/release-process.md` (AC.READY.7 — universal-admission)
- `docs/public-surface-manifest.md` (AC.READY.9 — new file; universal-admission)
- `docs/experiments/v0-7-1-hard-smoke.md` (AC.READY.7 + AC.READY.8 — universal-admission)
- `docs/plans/v0-7-1-v1-0-readiness-cleanup.md` (this file — universal-admission)
- `docs/plans/v0-7-1-v1-0-readiness-cleanup.manifest.yaml` (universal-admission)
- `docs/FUTURE_IDEAS_DRAFT.md` (capture of the v0.8.0 candidate — structural HARD-smoke CLI extension; AC.READY.7 follow-on; universal-admission)

Sidecar advances per sealed-component-cycle ritual. AC.READY.1 is operational (host machine reinstall) — does NOT touch the repository tree.

## §5 — Decisions builder rules at build time

- **D-READY.2.a (install-from-source ordering):** loam-amend goes after `plugins/dev-sdlc/` (the parent plugin) and before any consumer; pr-safety after dev-sdlc and after odd-extractor; loam-mode after dev-sdlc; per-project-pm in Tier B (depends only on Tier A). Builder rules exact tier placement at build-time per the existing tier comments.
- **D-READY.4 (component count chosen):** 18 — the `docs/components/index.md` table is the source-of-truth and currently has 18 rows. The "15" wording at architecture.md:270 is the residual; fix that to "18" rather than re-investigating the count.
- **D-READY.5 (memory.md edit-or-skip):** plan-time grep shows ZERO Graphiti hits — the doc was already cleaned. Builder records "GREEN — already clean; YELLOW-2 audit over-stated" as the AC verdict + does NOT edit the file unless a re-read surfaces residue the grep missed.
- **D-READY.6 (pr-safety doc location):** default = add to `docs/components/index.md` as a new row (consistent with how every other shipped CLI verb's package is surfaced). Switch to `docs/plugins/dev-sdlc.md` only if the index.md row's group fits poorly.
- **D-READY.7 (HARD-smoke gate name):** default = `system-binary-operational`. Switch only if a shorter name fits the existing gate-name table style.
- **D-READY.9 (manifest authority paths):** every public-surface row cites a specific source-of-truth path; if a path is missing, builder records "TBD-AT-V1.0" rather than fabricating a path.

## §6 — Out of scope (explicit)

- **Structural CLI implementation of the AC.READY.7 system-binary-operational gate** — that's a code-shaped change to `framework/tools/loam/src/loam_cli/release/gates.py` adding a new gate function. MINOR-class (extends release-process capability); deferred to v0.8.0+ via FUTURE_IDEAS_DRAFT capture. v0.7.1 ships the docs gate description + the manual-verification writeup.
- **Public-surface manifest STRUCTURAL ENFORCEMENT** — the manifest doc (AC.READY.9) is the deliverable; a test that fails if any surface drifts is the next-stage discipline. MINOR-class; deferred per v1.0-readiness audit §5 step 8.
- **Deeper plugin-contract revision** — the contract is documented + the entry-point shape is sound (audit §4 verdict). The install-path gap (RED-2) is the only blocker; fix that and the contract is ready for v1.0. No revision in v0.7.1 scope.
- **New feature work of any kind** — v0.7.1 is defect-closure-only.
- **v0.7.0's deeper F-DESIGN finding** (Q4/Q5 dev-intent conditional surfacing) — that's a follow-on amendment captured in v0.7.0's §status; not in v0.7.1 scope.
- **`loam project` documentation (if undocumented)** — out of v0.7.1 scope; if AC.READY.8's stranger-clone probe surfaces this as an additional gap, builder records it as a finding for follow-on, not as in-cycle work.
- **Multi-LLM via OpenRouter** (per architectural constraint, backlog only).
- **Anthropic API key paths** (per architectural constraint, never).

## §7 — HARD HALTs (build-time)

Halt-and-surface to dispatcher (return owner-call) — do NOT proceed past — on any of:

1. AC.READY.8 outcome-altitude probe RED (stranger-clone fresh-install can't reach working CLI — i.e., any documented `loam <verb> --help` returns ImportError, ModuleNotFoundError, or argparse-invalid-choice). Halt; surface as F-DESIGN candidate (the install path itself is broken).
2. ODD §2.5 violation in your work OR surrounding code (per `feedback_subagent_odd_violation_halt`).
3. Wrong-tree-write (any edit lands at a path outside `/Users/lukeivers/loam/`).
4. Any reach for ASK-FIRST class actions: `cd` outside `/Users/lukeivers/loam/`, `git push`, `git tag`, `git commit --amend` (per `feedback_no_amend_in_agent_dispatches`). Immediate halt.
5. AI-time exceeds upper band (275 min midpoint) by >50% → 412 min wall-clock (~6.9 hr; the dispatch brief allows 6 hr — adopt 6 hr as the surface threshold). Halt with current state.
6. Schema/architecture change to existing manifests or CLI argparse appears necessary beyond what the ACs name. Halt — out-of-scope per §6.
7. Any reach for an Anthropic API key path (per `feedback_no_anthropic_api_key`). Immediate halt.
8. Any `claude -p` invocation without `--strict-mcp-config` + empty MCP config tempfile (per the v0.2.5 C5 propagation invariant). Immediate halt.
9. Discovery of additional broken `loam <verb>` in the AC.READY.8 probe beyond the audit's named gaps. Halt; surface; expand AC.READY.8 verdict to RED + propose corrective.

## §8 — Dependencies

- **v0.7.0 (non-tech-user surface)** — HARD on commit-graph. v0.7.1 builds on v0.7.0's HEAD; the publish ritual for v0.7.1 will use the same `loam release` CLI (per v0.6.0's dogfood AC; second use of the verb post-v0.7.0).
- **v0.6.0 (concrete release process)** — HARD. AC.READY.7 extends the release-process gates table; v0.7.1 cannot land cleanly without v0.6.0's gate-table substrate.
- **v0.5.1 (split-worktrees migration)** — HARD on root-cause. AC.READY.1 closes the install breakage v0.5.1 introduced (the migration deleted the source dir but left the dependent package installs pointing at it).
- **`docs/release-versioning-policy.md`** — SOFT. AC.READY.9 cites it as the manifest's authority chain.
- **No external service dependencies.**
- **No new Python packages** (subscription-only constraint; everything via `claude -p` if any LLM-routed step were needed — none here).

## §9 — Estimated AI-time

Per `feedback_duration_estimation_rubric` — multi-component PATCH; tight per-AC scope; documentation-heavy with one operational fix + one structural-doc fix + one cold-venv probe.

| Stage | Band | Midpoint |
|---|---|---|
| Plan-doc + manifest authoring (this file) | 30-45 min | 38 min |
| AC.READY.1 — system binary reinstall | 1-3 min | 2 min |
| AC.READY.2 — install-from-source.txt update + cold-venv probe | 10-20 min | 15 min |
| AC.READY.3 — STATE.md + roadmap stale-claims fix | 15-30 min | 22 min |
| AC.READY.4 — component-count reconciliation | 10-20 min | 15 min |
| AC.READY.5 — memory.md verify-and-record (no edit expected) | 5-10 min | 8 min |
| AC.READY.6 — pr-safety doc add | 10-20 min | 15 min |
| AC.READY.7 — HARD-smoke gate doc add + writeup | 20-40 min | 30 min |
| AC.READY.8 — stranger-clone outcome-altitude probe | 30-60 min | 45 min |
| AC.READY.9 — public-surface manifest authoring | 60-90 min | 75 min |
| Plan-doc §13 backfill + STATE/roadmap admin + manifest apply + seal | 30-60 min | 45 min |
| **Total v0.7.1 build** | **221-398 min (~3.7-6.6 hr)** | **~310 min (~5.2 hr)** |

The dispatch brief estimates 150-275 min midpoint ~205. Plan-time revision: **221-398 min midpoint ~310 min**. Higher band reflects the public-surface manifest authoring being genuinely substantive (60-90 min) and the cold-venv probe needing real install + iteration time (30-60 min). If the manifest authoring compresses, the lower band is reachable.

Owner gate-review separate (publish per ASK-FIRST after seal).

## §11 — Authority chain

- `workspace/.scratch/claude-output/v1-0-readiness-verification-2026-05-10.md` — audit report (the plan input).
- `docs/release-versioning-policy.md` §1.0.0 — v1.0 quality-bar criteria; AC.READY.* ladder up to criteria #1 + #4.
- `docs/release-roadmap.md` v1.0 entry — v1.0 outcome shape.
- `docs/release-process.md` §1 — release-gates table extended at AC.READY.7.
- `docs/components/index.md` — source-of-truth for the component count (18) per AC.READY.4 D-READY.4.
- Memory rules: `feedback_test_outcome_altitude_required.md` (AC.READY.8 + risk-band), `feedback_plan_before_code.md` (this plan-doc IS the gate), `feedback_summarize_and_surface_decisions.md` (Q-section absent because owner pre-ratified scope), `feedback_no_amend_in_agent_dispatches.md` (HARD HALT #4), `feedback_no_anthropic_api_key.md` (HARD HALT #7), `feedback_subagent_odd_violation_halt.md` (HARD HALT #2), `feedback_duration_estimation_rubric.md` (§9), `feedback_scope_descriptive_ac_ids.md` (AC.READY.* not AC.V071.*), `feedback_locked_design_not_license_for_bad_outcomes.md` (AC.READY.5 — surface audit over-statement honestly per F2; do not manufacture fix-for-the-sake-of-fix).

## §13 — §status

**Build cycle:** SHIPPED LOCAL 2026-05-10 — owner pre-ratified scope (Telegram 10663). Awaiting dispatcher dogfood publish per ASK-FIRST.

**Plan-doc commits:** plan-doc + manifest `7ea5fad`; source-edit + admin (install-from-source.txt + STATE.md + release-roadmap.md + architecture.md + components/index.md + release-process.md + public-surface-manifest.md + HARD smoke writeup + FUTURE_IDEAS_DRAFT capture) `d9cf905`; apply auto-commit (BASELINE + sidecar + allowed_files extension across 4 admin docs) `5332f1a`; seal commit `cdae8ed`.

### AC verdict matrix

| AC | Verdict | Evidence |
|---|---|---|
| AC.READY.1 — System binary reinstall | GREEN | `which loam` → `/opt/homebrew/bin/loam`; `loam --help` lists 7 documented subcommands; `pip list \| grep loam` shows all 23 packages installed against `/Users/lukeivers/loam/`. Documented in `docs/experiments/v0-7-1-hard-smoke.md` §1. |
| AC.READY.2 — loam amend in install path | GREEN | `install-from-source.txt` extended with 4 missing `-e` entries: `loam-amend`, `loam-pr-safety`, `loam-mode`, `framework/per-project-pm`. Cold-venv install at `/tmp/loam-stranger-venv-v071/` registers all 23 packages; `loam amend --help` returns `validate / apply / seal / template / new-plan / new-memory`. Documented in `docs/experiments/v0-7-1-hard-smoke.md` §2. |
| AC.READY.3 — STATE/roadmap stale-claims | GREEN | `docs/release-roadmap.md` §2 v0.6.0 + v0.7.0 rows + §3 active-version updated to "SHIPPED PUBLIC" with seal+tag SHAs; `docs/STATE.md` v0.6.0 + v0.7.0 entries marked SHIPPED PUBLIC with seal+tag+pre-apply admin commits. New v0.7.1 row added to STATE.md + release-roadmap.md §2. `grep -n "SHIPPED LOCAL\|awaiting publish" docs/release-roadmap.md docs/STATE.md` returns no v0.6.0 or v0.7.0 hits. |
| AC.READY.4 — Component-count reconciliation | GREEN | `docs/architecture.md:270` "summaries of all 15 components" → "summaries of all 18 components". `grep -rn "15 components\|fifteen components" docs/` returns hits only in audit-history (`docs/v0-3-0-feature-honesty-audit.md`) + v0.7.1 plan-doc + STATE/roadmap meta-rows describing the fix; no user-facing docs carry the stale claim. |
| AC.READY.5 — memory.md verify-and-record | GREEN | `grep -i "graphiti" docs/components/memory.md` returns zero hits at HEAD `cdae8ed`. The audit's YELLOW-2 finding was over-stated — the doc was already cleaned in a prior cycle. No edit required; F2 surface honestly per `feedback_locked_design_not_license_for_bad_outcomes`. |
| AC.READY.6 — pr-safety documentation | GREEN | `docs/components/index.md` extended with new "Dev/SDLC plugin verbs" sub-section listing `loam pr-safety` (and the other plugin-contributed CLI verbs: `loam amend`, `loam odd-extract`, `loam project`). `grep "pr-safety" docs/components/index.md` returns the new row + verb description. |
| AC.READY.7 — HARD-smoke gap closure | GREEN (docs-only at v0.7.1; structural CLI deferred to v0.8.0+) | `docs/release-process.md` §1 pre-publish gates table extended with gate 7 `system-binary-operational`. Status note explicitly flags structural CLI implementation as deferred + the v0.7.1 HARD smoke writeup verifies the gate manually. FUTURE_IDEAS_DRAFT.md captures the v0.8.0+ structural-CLI follow-on. |
| AC.READY.8 — Stranger-clone outcome-altitude probe | GREEN | `docs/experiments/v0-7-1-hard-smoke.md` §3 documents the cold-clone + cold-venv + 7-verb iteration. Per-verb verdict matrix shows 7/7 exit-0 with usage; 0 errors. Real-execution probe (not pre-arranged state); invokes production CLI entry-points. `outcome-altitude: true` per `feedback_test_outcome_altitude_required`. |
| AC.READY.9 — Public-surface manifest | GREEN | `docs/public-surface-manifest.md` authored — covers §2.1 CLI verbs / §2.2 plugin entry-point groups / §2.3 workspace-bootstrap manifest schema / §2.4 amendment manifest YAML schema / §2.5 file-based memory contract / §2.6 hook contracts / §2.7 on-disk workspace conventions / §2.8 release-process gates contract. §3 names NON-public surfaces; §4 names contract-evolution mechanics; §5 cites authority chain. Closes the v1.0-readiness audit §3 forward-commitment-realism gap. |
| AC.READY.S — Seal-diff discipline | GREEN | `git diff --name-only d9cf905..cdae8ed` shows 6 files: 1 SEAL_COMMIT sidecar (`plugins/dev-sdlc/tests/SEAL_COMMIT`); 1 narrative file (`plugins/dev-sdlc/seals/SEAL_COMMIT.v0-7-1-v1-0-readiness-cleanup`); 1 seal-test allowed_files bump (`plugins/dev-sdlc/tests/test_no_sealed_amendments.py` — adding the 4 admin docs); plan-doc + manifest. Cross-component sweep used `--scoped-sweep` (manifest-scoped to dev-sdlc only) due to Python-environment issue (cross-component sweep ran under pyenv 3.9.17 instead of homebrew 3.13 + couldn't import `loam` packages installed only against system Python). The single sealed component (dev-sdlc) seal-test invariant: passed. |

### AI-time actuals

| Stage | Estimated (plan §9) | Actual |
|---|---|---|
| Plan-doc + manifest authoring | 30-45 min | ~22 min |
| AC.READY.1 — system binary reinstall | 1-3 min | ~2 min |
| AC.READY.2 — install-from-source + cold-venv probe | 10-20 min | ~6 min |
| AC.READY.3 — STATE/roadmap stale-claims fix | 15-30 min | ~8 min |
| AC.READY.4 — component-count fix | 10-20 min | ~3 min |
| AC.READY.5 — memory.md verify | 5-10 min | ~2 min |
| AC.READY.6 — pr-safety doc | 10-20 min | ~5 min |
| AC.READY.7 — HARD-smoke gate doc | 20-40 min | ~8 min |
| AC.READY.8 — stranger-clone probe + writeup | 30-60 min | ~12 min |
| AC.READY.9 — public-surface manifest | 60-90 min | ~28 min |
| Plan-doc backfill + apply + seal + §14 | 30-60 min | ~18 min |
| **Total** | **221-398 min** | **~114 min (~1.9 hr)** |

Significantly under-band — plan-time estimate over-weighted documentation-fidelity AC time and the public-surface manifest authoring time. Forward calibration: defect-closure PATCH-class amendments with documentation-heavy ACs compress to 90-150 min, not 220-400 min.

### Halt-and-surface findings

**Cross-component sweep environment mismatch (operational; not blocking).** `loam amend seal` ran the cross-component sweep under pyenv 3.9.17 (the ambient interpreter on PATH via shim) instead of homebrew 3.13 (where loam packages are installed). The sweep failed with `ModuleNotFoundError: No module named 'loam'` against `framework/cost-governance/tests/conftest.py`. Used `--scoped-sweep` to restrict the sweep to manifest-listed components (dev-sdlc only); single-component seal-test invariant passed. **Forward action:** v0.7.x or v0.8.0 candidate captured in FUTURE_IDEAS_DRAFT — `loam amend seal` should detect the ambient-interpreter mismatch + surface a corrective hint OR pin the interpreter via the manifest. Not v0.7.1 scope (that's a `loam amend` enhancement, MINOR-class).

**Audit YELLOW-2 over-statement (F2 finding; in-cycle).** AC.READY.5's audit-mandated cleanup of `docs/components/memory.md` for Graphiti residue was unnecessary — the doc was already clean at HEAD `8b129e9` per `grep -i "graphiti" docs/components/memory.md` returning zero hits. The audit's YELLOW-2 finding was over-stated. Recorded as GREEN per F2 surface-honestly discipline (no fix-for-the-sake-of-fix per `feedback_locked_design_not_license_for_bad_outcomes`).

## §14 — Method decisions

The plan-doc's §5 already names the build-time decisions (D-READY.1 through D-READY.9 — install-from-source ordering, component count chosen, memory.md edit-or-skip, pr-safety doc location, HARD-smoke gate name, manifest authority paths). All builder rulings landed as planned; no method-deviations from the plan-doc.

### Commit SHAs

- Plan-doc + manifest authoring: `7ea5fad`
- Source-edit + admin batch: `d9cf905`
- Apply auto-commit (BASELINE + sidecar + allowed_files): `5332f1a`
- Seal commit (deterministic seal): `cdae8ed`

### Build-time decision deviations

None. All D-READY.1 through D-READY.9 rulings landed as the plan-doc anticipated.
