# OSS v0.1.0 publish — loam first public release — master plan

Multi-amendment **publish programme** that takes pos-v2's canonical
tree from "internal harness with pos-v2 brand and dev-discipline
machinery on the surface" to a clean, stranger-bootable v0.1.0 of
**loam** at `https://github.com/lukeivers/loam`. This doc is the
umbrella plan; per-amendment / per-milestone sub-plan files (linked
in §5) carry the build-shape detail. Plan-before-code per the dev
CDC.

**Status:** plan (pre-dispatch). 2026-04-29.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical
pos-v2 / future loam).
**Public target:** `https://github.com/lukeivers/loam` (created at M9;
no commits before then).

**Companion artefacts (read first; this plan does not duplicate
their content):**

- **OSS-readiness audit (milestone framework + 12 strategic answers):**
  `.scratch/claude-output/oss-readiness-audit.md`
  — milestone shape M0–M10, partition recommendations, license + governance scaffold.
  *Note:* the audit's wall-clock estimates are **human-developer-time**;
  this plan re-prices them in AI-builder-time per the calibrated rubric
  (see §6).
- **Feature-usage audit (wired vs dormant matrix):**
  `.scratch/claude-output/feature-usage-audit.md`
  — three dormant surfaces flagged: `dispatch_with_scope` (D-1),
  `graceful-degradation` constructor (D-2), per-component CLIs (D-3).
  Owner authorised wiring of all three.
- **Master decisions dossier (synthesis of three audits with TL;DR):**
  `.scratch/claude-output/oss-publish-master-dossier.md`
  — single-page rule-set; **note:** carries human-time estimates that
  are corrected here.
- **loam-rename decisions (Idea 10 authority):**
  `docs/rebuild/plans/loam-rename-decisions.md` — Tier-1 + Tier-2
  rename catalogue, monolithic `loam.*` namespace ruling, history-
  preservation ruling. Authority for every rename AC in this plan.
- **loam-rename research (mechanics):**
  `.scratch/claude-output/loam-rename-migration-plan.md` — phased
  inventory and dependency ordering. Source for the rename amendment's
  scope.
- **OSS-launch research (positioning, repo hygiene, launch sequencing):**
  `docs/rebuild/plans/research/loam-open-source-launch-research.md`.
- **FUTURE_IDEAS authority:**
  - Idea 10 (rename to loam): `docs/rebuild/FUTURE_IDEAS.md:430` —
    UN-TABLED 2026-04-29.
  - Idea 12 (OSS launch): `docs/rebuild/FUTURE_IDEAS.md:510` —
    ACTIVE 2026-04-29; three open rulings closed.
  - Idea 3 (Dev/SDLC plugin): `docs/rebuild/FUTURE_IDEAS.md:278` —
    must-ship at v1 per Idea 12.
- **STATE.md:** governing rules + component table; row added 2026-04-29
  for OSS publish.
- **Spec:** `docs/rebuild/spec/pos-v2-objectives-spec.md` — the
  contract being built against. AC.PO.1 + AC.PO.2 in
  `docs/rebuild/VALUE_PROPOSITION.md` are the prime objective ACs;
  every milestone ladders up.
- **Synthesis tool (the publish mechanism):**
  `framework/tools/pos-publish-framework-only/src/pos_publish_framework_only/synth.py`
  — composes a parent-chained `framework-only` branch by promoting
  `framework/<entry>` to root and overlaying chosen top-level docs.
  Sealed amendment #67. Extended at M2 to consume a publish-mode
  partition.

**Ancestor record:**

- **Owner ruling 2026-04-29 (locked, three Idea-12 open rulings):**
  - **R1** Dormancy rename (graceful-degradation → dormancy): **pre-launch,
    inside the v0.1.0 sequence.** Idea-10 Tier-2 lands as part of the
    rename amendment, not as a v0.2 follow-on.
  - **R2** v1 plugin count: **Dev/SDLC only.** Idea 3's Dev/SDLC plugin
    is must-ship at v0.1.0; no other plugins ship in the first release.
  - **R3** Public repo ownership: **`lukeivers/loam`** (personal account).
    Honest about bus-factor-1; can migrate to an org later without
    disruption.
- **Owner ruling 2026-04-29 (wire-or-strip):** wire all three dormant
  surfaces. `dispatch_with_scope` becomes the persona's actual Agent-
  dispatch path (D-1.a). `graceful-degradation` gets a real
  constructor adapter wired to orchestrator pause/resume hooks (D-2.a).
  Per-component CLIs land as `[project.scripts]` entry-points (D-3.a).
- **Pre-flight verified clean:** no `.env` ever committed; no
  hardcoded credentials in tracked source; `.env` exists working-tree-
  only at `framework/memory-system/.env` (untracked). **No git-history
  rewrite required** (audit §1.1).
- **Synthesis pipeline already present:** `pos-publish-framework-only`
  (sealed #67) is the publish mechanism; the public artefact is the
  synthetic `framework-only` branch promoted to a fresh repo with a
  squashed initial commit.

---

## 1. Objective

**v0.1.0 of loam is published at `https://github.com/lukeivers/loam`
as a clean, stranger-bootable open-source release** — Apache-2.0
licensed, with positioning + getting-started + architecture docs, a
Dev/SDLC plugin demonstrating the harness pattern, and the three
runtime gaps surfaced by the feature-usage audit closed (so the
harness ships fully wired). The public artefact carries the loam
brand from commit 1; the canonical `pos-v2` private working tree
keeps its full history and dev-discipline machinery, and synthesises
to public on demand.

**Scope of this programme.** Six amendment cycles (one rename, one
publish-mode partition, three wire-or-strip closures, one Dev/SDLC
plugin) plus one parallel-safe documentary lane (positioning,
license, governance, public docs, condensed ODD), gated by three
owner-review checkpoints (M5 license/governance, M8 synthesis dry-
run, M9 publish-and-tag), absorbed by one bus-factor-1 mitigation
lane (M7 review-circle recruitment) running in parallel with M1–M5.

**Out-of-band items** (decoupled, not part of this plan): M10
HN/blog announce; community-channel setup; second-plugin scoping
beyond Dev/SDLC.

---

## 2. Three Idea-12 rulings as governing constraints

Recorded inline so any builder reading this plan does not have to
chase FUTURE_IDEAS to find them. **All three are LOCKED** as of
2026-04-29.

**R1 — Dormancy rename pre-launch.** Tier-2 of Idea 10's loam-
rename catalogue (graceful-degradation → dormancy) executes inside
the v0.1.0 publish sequence. The Tier-2 rename folds into the
rename amendment (M1) alongside Tier-1, **not** deferred to v0.2.
Cascade: directory `framework/graceful-degradation/` →
`framework/dormancy/`, package, event namespace, config-file paths
(`degradation.sqlite`, `degradation-config.yaml`), AC-prefix `P`
stays (P = Policy). Migration mechanics in
`.scratch/claude-output/loam-rename-migration-plan.md` §4.1.

**R2 — Dev/SDLC plugin only at v1.** The first plugin to ship is
the Dev/SDLC plugin (Idea 3). It is must-ship at v0.1.0 per the
Idea 12 research recommendation: it makes the harness pattern
visible to the developer audience and demonstrates plugin-extension
to the workspace-bootstrap surface. No other plugins ship at v1.

**R3 — Public repo at `lukeivers/loam`.** Personal account. Reasons:
(a) honest about bus-factor-1; (b) low-ceremony setup; (c) easy to
migrate to an org (transfer GitHub repo) later if traction warrants;
the reverse path (org → personal) is friction-laden. CODEOWNERS
authored if the M7 review circle yields a co-reviewer.

---

## 3. Acceptance criteria (programme-level invariants)

Outcome-shape only. Method-shape decisions (which exact files,
which test names, which exact synth-time substitution table) are
the per-amendment builder's call inside the AC outcome bound, per
the established `docs/rebuild/plans/` convention.

### AC.OSS.1 — A stranger clones loam from GitHub and bootstraps without manual intervention.

A user with no prior loam exposure runs:

```
git clone https://github.com/lukeivers/loam <new-ws>/framework/
cd <new-ws>
pos init .                # via the loam CLI's init verb (post-rename)
claude                    # Claude Code launches; first-run bootstraps
```

…and reaches the first useful primary-persona session (memory-
sidecar online, primary-persona-onboarding question fired or
skipped per ruling, getting-started doc surfaced) **without
needing to read source, edit settings, or know any pos-v2-internal
vocabulary.** The harness composes against Claude's native
capabilities (skills, hooks, MCP, plugins) where they cover the
ground; loam-specific configuration is request-driven, not
mandatory.

**Verification.** End-to-end test on a clean macOS user account
or fresh container exercises the clone → init → first-session
path against the staging repo at M8 and the published repo at
M9. Failure modes recorded in M8's owner-review artefact;
retried after fix.

### AC.OSS.2 — Every sealed component in the public set is wired and exercised by primary persona's normal operation.

The feature-usage audit's three dormant surfaces (D-1
`dispatch_with_scope`, D-2 graceful-degradation constructor, D-3
per-component CLIs) are wired before publish. Every component the
public artefact ships carries at least one production caller; no
component is shipped only with test-callers. Exception:
operator-driven CLIs (e.g. `loam-amend`-equivalent) are dev-only
and do not ship with v0.1.0 (hidden via M2 partition).

**Verification.** A repeat of the feature-usage audit's test-only-
caller detection sweep passes against the synthetic v0.1.0 tree at
M8: zero components have only test-callers in the shipping set.

### AC.OSS.3 — No dev-discipline machinery visible in the public synthesis output.

The public artefact contains no:

- `pos-amend` / `loam-amend` CLI surface
- A1–A4 PreToolUse gates, TDD-guard, objective-binding gate,
  blast-radius gate, agent-context guard
- `loam-mode` / dev-mode auto-load partition (DEV_MODE-only)
- ODD seal-test sidecars (`tests/test_no_sealed_amendments.py`,
  `tests/seals/`)
- `docs/rebuild/` tree (plans, components, capability-corpus
  authoring shape, FUTURE_IDEAS, BACKLOG, STATE, dev-mode
  manifest, decay-retention analysis, spec/)
- `plugins/dev-sdlc/tools/loam-mode/`, `framework/tools/heavy-b-migrate/`,
  `framework/tools/upgrade-merge-resolver/`,
  `framework/tools/orphan-plist-cleanup/`,
  `framework/tools/pos-publish-framework-only/`
- `CLAUDE.dev.md` fragment
- `plugins/dev-sdlc/docs/odd-methodology.md` (long form),
  `plugins/dev-sdlc/docs/odd-in-loam.md` (long form),
  `plugins/dev-sdlc/docs/duration-estimation-rubric.md`

The condensed `docs/design/odd.md` (~200 lines) is shipped as the
public methodology surface; the long forms remain DEV-MODE-only.

**Verification.** Synth the canonical HEAD via the M2-extended
synthesis pipeline; grep the synthetic tree for every excluded
artefact by literal path. Count of expected exclusions == count
of actual exclusions.

### AC.OSS.4 — License + governance scaffold present.

`LICENSE` (Apache-2.0; copyright "Copyright 2026 Luke Ivers and
contributors"), `CONTRIBUTING.md` (workflow, AC requirement, ODD
principle reference, sign-off model), `CODE_OF_CONDUCT.md`
(Contributor Covenant 2.1), `SECURITY.md` (vulnerability-reporting
address, disclosure timeline, scope) all live at workspace root in
the public artefact. Apache-license headers added to every runtime-
shipping `.py` file in `framework/`; not added to dev-only tools.

**Verification.** All four files present at synthetic-tree root;
content checked against an authored template per M5's builder-
plan. License-header spot check passes for ≥3 components × ≥3
files each.

### AC.OSS.5 — Documentary rebrand complete in public artefacts.

Every user-facing string in the public artefact reads "loam" not
"pos-v2" / "pOS v2" / "POS_V2_*". Includes top-level `README.md`,
`CLAUDE.md`, `docs/positioning.md`, `docs/getting-started.md`,
`docs/architecture.md`, `docs/components/<name>.md`,
`docs/design/odd.md`, license headers, error messages emitted by
runtime code, `--help` output of every shipped CLI. Tier-1 and
Tier-2 renames per `loam-rename-decisions.md` are complete.

**Verification.** Synth the v0.1.0 tree; grep for `pos-v2`,
`pOS v2`, `POS_V2_`, `pos.v2`, `~/.pos/`, `pos-amend`,
`com.pos-v2.`, `lukeivers/pos-v2`. Allowed residuals:
historical commit prose **inside the canonical `pos-v2` working
tree** (NOT in synthetic), and dev-only artefacts that are
excluded by M2 partition. Public-tree count of disallowed
matches: zero.

### AC.OSS.6 — Dev/SDLC plugin ships and demonstrates the plugin pattern.

Per R2: the Dev/SDLC plugin (Idea 3) ships in v0.1.0 as the first
plugin. It composes against workspace-bootstrap's extension
protocol; defaults new projects to ODD-shaped research/spec/plan/
build/review/verify; provides an opt-out for users who prefer
TDD/BDD/ad-hoc.

**Verification.** Plugin's own AC suite passes; plugin-loading is
exercised by a smoke test in `framework/workspace-bootstrap/tests/`
or in the plugin's own tests. Visible in `pos --help` (or `loam
--help` post-rename) under a plugin-discoverability surface.

### AC.OSS.7 — Bus-factor-1 mitigation in place before public-flip.

A 3–5-person review circle is recruited before the public-flip
gate (M9.4). Each member has read positioning + architecture +
design/odd; each has confirmed willingness to triage early
issues. Names recorded privately (not publicised) in
`docs/rebuild/plans/oss-launch-decisions.md`.

**Verification.** List committed; M9 gate-review checks the list
exists and is non-empty before the public-flip step proceeds.

### AC.OSS.S — Programme-level seal.

After M9, every milestone's commit SHA is recorded in §14 below.
The synthetic `framework-only` branch advances normally for
v0.1.x patches; v0.2 begins a new master-plan cycle.

---

## 4. Scope boundaries

### In v0.1.0 (this plan delivers)

- Tier-1 + Tier-2 rename to loam (Idea 10 Phases 1 + 3).
- Publish-mode partition mechanism + extended synthesis pipeline.
- Three wired-dormant closures (dispatch_with_scope, dormancy
  constructor, per-component CLIs).
- Dev/SDLC plugin v1 (Idea 3, must-ship per R2).
- Public docs scaffold (positioning, getting-started,
  architecture, per-component reference, condensed ODD).
- Apache-2.0 + Contributor Covenant 2.1 + SECURITY.md +
  CONTRIBUTING.md.
- Personal-info scrub (path substitution + fixture-name
  refactors).
- Bus-factor-1 review circle (3–5 people).
- Public repo creation at `lukeivers/loam`; v0.1.0 tag;
  release notes.

### Deferred to v0.2 or later (out of this plan)

- Additional plugins beyond Dev/SDLC (Idea 3's other candidates).
- Idea 10 Phase 4–5 (additional CLI alias work, `plot` user-
  facing alias for scope-of-work).
- HN / blog post / community-channel announcement (M10 — owner-
  driven; decoupled).
- Multi-workspace umbrella (Idea 13's deferred sub-plans C/D/G).
- Recollapse/reseal (Idea 11 — deferred until trigger).
- GLiNER2 expansion (Idea 7 — independent component).
- Workspace-tooling adoption (uv workspaces / hatch
  workspaces) — out of scope per d-migration §7.
- Org-level repo migration (R3's "if traction warrants" path).
- Long-form `plugins/dev-sdlc/docs/odd-methodology.md` shipping as a public
  differentiator (audit D5; deferred — short form ships).

---

## 5. Work decomposition

Six amendment cycles + one parallel-safe documentary lane + one
parallel-safe owner-driven lane. Naming follows
`docs/rebuild/plans/oss-v0-1-0-publish-<slug>.md` for sub-plans
that need their own file; trivial milestones inline here. **Per-
amendment sub-plans are authored by each amendment's builder**
before any source edit (plan-before-code CDC).

Each row: ID + one-line description + AC reference + AI-time
range + midpoint. Per the duration-estimation rubric (categories
+ formula), all estimates are AI-builder wall-clock; gate-review
time is owner-time and NOT included.

| ID | Sub-plan | Description | ACs | AI-time | Midpoint |
|----|----------|-------------|-----|---------|----------|
| **M0** | (this plan) | Owner approves v0.1.0 plan + sub-plan ladder. Authority captured in `docs/rebuild/plans/oss-launch-decisions.md`. | — | (owner time only) | — |
| **M1.rename (series)** | `oss-v0-1-0-publish-rename.md` | **Multi-amendment series** per owner ruling D-RNM.1 (2026-04-29). Tier-1 + Tier-2 rename per `loam-rename-decisions.md` split into seven independently-sealed sub-amendments M1a..M1g. The empirical surface (~91 import sites + ~597 OTel emit sites + ~1310 `pos-amend` doc/code refs across sixteen sealed components) was 5–10× the original rubric estimate; the split eliminates the wall-clock-blow-out failure class per ODD §5.1.1. Each row below is its own AC family (`AC.RNM-1a.*` .. `AC.RNM-1g.*`). | AC.OSS.5 (rebrand); AC.OSS.3 (dev-only artefact rename consistency) | (sum below) | (sum below) |
| **M1a** | `oss-v0-1-0-publish-rename-1a.md` | **Docs/prose-only brand rebrand.** Live docs / READMEs / CLAUDE.md (root) / VALUE_PROPOSITION / odd-methodology / odd-in-pos / duration-rubric / CLAUDE_CAPABILITIES — `pos-v2` / `pOS v2` brand strings rewritten to `loam` in user-facing prose. ZERO code, env-vars, paths, CLI, OTel, launchd. **Sealed `143d465` 2026-04-29.** | AC.RNM-1a.1..6 + AC.RNM-1a.S | 30–45 min (actual ~60 min — surrounding-debt tax) | 35 min |
| **M1b** | `oss-v0-1-0-publish-rename-1b.md` | **Per-host config dir + env-vars.** `~/.pos/` → `~/.loam/` (path constants in code + docs); `POS_V2_*` → `LOAM_*` (seven post-dedup names; `POS_V2_ROOT` + `POS_V2_REPO` collapse to `LOAM_REPO`; `POS_V2_POS_ROOT` de-doubles to `LOAM_DATA_DIR`). Hard cutover (no fallback module per D-RNM.3). One-shot per-host migration helper. Includes the precursor doc-only commit that creates this M1a..M1g table. | AC.RNM-1b.1..6 + AC.RNM-1b.S | 60–120 min | 90 min |
| **M1c** | `oss-v0-1-0-publish-rename-1c.md` | **launchd labels.** `com.pos-v2.<slug>.*` → `com.loam.<slug>.*`. plist filenames cascade. hands-off-lifecycle's bootout-before-bootstrap flow issues bootouts for old labels once on first run after upgrade, then installs new labels. First sub-amendment that may cross HC#4. | AC.RNM-1c.1..S | 30–60 min | 45 min |
| **M1d** | `oss-v0-1-0-publish-rename-1d.md` | **OTel `pos.*` → `loam.*` roots.** All 23 root namespaces (per migration plan §3.5; `pos.degradation` rebases to `loam.dormancy` deferred to M1f). Names below the second segment unchanged. Aggregator subscription registration updates. **No dual-prefix read window** (D-RNM.3 hard-cutover). Largest single-grep amendment of the series. | AC.RNM-1d.1..S | 45–90 min | 60 min |
| **M1e** | `oss-v0-1-0-publish-rename-1e.md` | **Monolithic `loam.*` namespace pivot.** Per-component `framework/<comp>/src/loam/<comp>/` restructure (D-RNM.2 ruling). Every `from pos_<comp> import` callsite rewrites to `from loam.<comp> import`. pyproject.toml `name` fields update. Editable-install reconfig. Hard cutover. **HC#4 retire-and-rebaseline definitely lands here.** Owner-review gate recommended pre-dispatch given fence width. | AC.RNM-1e.1..S | 90–180 min | 135 min |
| **M1f** | `oss-v0-1-0-publish-rename-1f.md` | **Tier-2: graceful-degradation → dormancy.** Directory + package + OTel `pos.degradation.*` → `loam.dormancy.*` + config files (`degradation.sqlite` → `dormancy.sqlite`, `degradation-config.yaml` → `dormancy-config.yaml`) + docs subdir + workspace-bootstrap adapter. AC prefix `P` stays. Per-host migration script for SQLite + YAML rename. Depends on M1e (the `loam.*` namespace must exist). | AC.RNM-1f.1..S | 30–60 min | 45 min |
| **M1g** | `oss-v0-1-0-publish-rename-1g.md` | **`pos-amend` CLI → `loam amend` subcommand.** `framework/tools/pos-amend/` → `framework/tools/loam/`. Console-script entry-point `pos-amend` → `loam` with `amend` as a subcommand. All ~1310 doc/code refs to `pos-amend` rewrite. **No shim binary** per D-RNM.3. Last amendment built under the `pos-amend` CLI name; subsequent amendments use `loam amend`. | AC.RNM-1g.1..S | 30–60 min | 45 min |
| **M2.partition** | `oss-v0-1-0-publish-partition.md` | **Single-component sealed amendment** (workspace-bootstrap or new tooling host). Author `publish-mode-manifest.yaml` + extend `pos-publish-framework-only` (post-rename: `loam-publish-framework-only`) to consume it; partition every workspace path into `public_only` / `dev_and_public` / `dev_only` / `excluded_from_publish`; default partition assigns the dev-discipline artefacts named in AC.OSS.3 to `dev_only`. | AC.OSS.3 | 25–45 min | 35 min |
| **M3.wire-clis** | inline (trivial; bundle with M2 or its own) | **Multi-component sealed amendment** (5 components: safety-layer, cost-governance, self-correction, reversibility-primitive). Add `[project.scripts]` entries: `loam-kill`, `loam-cost`, `loam-correction`, `loam-reversibility`, `loam-rollback` (post-rename names). | AC.OSS.2 (D-3) | 10–20 min | 15 min |
| **M4.wire-dispatch** | `oss-v0-1-0-publish-dispatch-with-scope.md` | **Multi-component sealed amendment** (primary-persona + hands-off-lifecycle). Wire `dispatch_with_scope` as the persona's actual Agent-dispatch path. PreToolUse hook on `Task` intercepts native Agent dispatches and routes through the four-gate wrapper. | AC.OSS.2 (D-1) | 25–45 min | 35 min |
| **M5.wire-dormancy** | `oss-v0-1-0-publish-dormancy-constructor.md` | **Multi-component sealed amendment** (workspace-bootstrap + dormancy [post-rename] + orchestrator). Promote bootstrap adapter from declaration-only to real constructor; bind `policy_dispatch` into orchestrator pause/resume hooks; `MemorySupervisor` outage events feed `DegradationComponent`. | AC.OSS.2 (D-2) | 25–45 min | 35 min |
| **M-FBM** | `oss-v0-1-0-publish-memory-pivot.md` | **Multi-component sealed amendment** (primary-persona + workspace-bootstrap + M2 partition manifest). File-based memory replaces graphiti as v0.1.0 default; Stop+UPS hook contributor; partition reclassifies `framework/memory-system/**` as `dev_only`; first-run-inventory drops graphiti-service; `MemoryProvider` Protocol stub authored for M-GMP to implement against. Memory-system source UNTOUCHED (only partition class changes). | AC.MFBM.1..7 + AC.MFBM.S | 90–180 min | 135 min |
| **M6.dev-sdlc-plugin** | `oss-v0-1-0-publish-dev-sdlc-plugin.md` | **Full new-component cycle** (5-gate: research plan → research → proposal → brief → build → seal). The Dev/SDLC plugin per Idea 3. ODD-by-default for new projects; opt-out preserves internal ODD representation; objective-extraction skill for existing repos lands in v0.1 or v0.1.1 (builder's call). | AC.OSS.6 | 90–180 min | 135 min |
| **M7.docs-lane** (parallel) | `oss-v0-1-0-publish-public-docs.md` | **Documentary lane** (parallel-safe with M1–M6 builds). Author `docs/positioning.md`, `docs/getting-started.md`, `docs/architecture.md`, `docs/components/<name>.md` (×15 per partition manifest), `docs/components/index.md` summary, `docs/plugins/dev-sdlc.md`, `docs/design/odd.md` (~200-line condensation), `README.md`. **Per-doc fan-out coordinator-serialised** per sub-plan §11 D-Q.M7.4; verify-first on existing high-quality docs (positioning.md / odd.md / README.md), rewrite-only-on-fail per sub-plan §7. Re-priced from 30–60 min after per-component fan-out concretised; sub-plan §13 rationale. | AC.OSS.5 | 90–180 min | 120 min |
| **M8.license-governance** | inline | **Trivial-shape amendment.** Author `LICENSE` + `CONTRIBUTING.md` + `CODE_OF_CONDUCT.md` + `SECURITY.md`. Apache-license headers script-added to runtime `.py` files. Lands as a single docs commit (no sealed-component fence required — top-level scaffold files only). | AC.OSS.4 | 10–20 min | 15 min |
| **M9.scrub** | `oss-v0-1-0-publish-scrub.md` | **Single-component sealed amendment** (publish synthesis tool) + **in-place fixture refactor** (graceful-degradation [post-rename: dormancy] + memory-system tests/scripts). Synth-time path substitution `/Users/lukeivers/ivers-corp-pos-v2/` → `<workspace>/loam/`; fixture names "Luke Ivers" → "Alice Anderson"; `lukeivers/pos-v2` URL refs → `lukeivers/loam`. | AC.OSS.5 (residuals) | 20–40 min | 30 min |
| **M10.bus-factor** (parallel, owner-time) | inline | **Owner-driven lane.** Recruit 3–5-person review circle. Each member reads positioning + architecture + odd. Names recorded privately in oss-launch-decisions.md. | AC.OSS.7 | (owner-driven; days–weeks calendar) | — |
| **M11.dry-run** | `oss-v0-1-0-publish-dry-run.md` | **Synthesis dry-run + private-staging review.** Synth canonical HEAD via the M2-extended pipeline → push to private `lukeivers/loam-staging` → review-circle members + owner spend ≥30 min each browsing → halt-and-surface findings → fold back into prior milestones if needed. **Owner gate at end (M8 in audit numbering).** | AC.OSS.1, AC.OSS.2 (sweep), AC.OSS.3 (sweep), AC.OSS.5 (sweep) | 30–60 min AI + owner gate | 45 min + gate |
| **M12.publish** | `oss-v0-1-0-publish-publish.md` | **Trivial-shape execution + tag.** Create `lukeivers/loam` repo (private); push squashed initial commit (drop parent-chain to pos-v2); tag v0.1.0; author release notes from positioning + architecture; flip public; capture URL in oss-launch-decisions.md. **Owner gate at end (M9 in audit numbering).** | AC.OSS.S | 15–30 min AI + owner gate | 20 min + gate |
| **M-GMP** (v0.1.x lane; post-M12) | `oss-v0-1-0-publish-memory-pivot.md` | **Multi-component sealed amendment** (memory-system relocation + workspace-bootstrap adapter rewire + M2 partition manifest). Relocates `framework/memory-system/` → `plugins/graphiti-memory/` mirroring Dev/SDLC plugin shape; bootstrap adapter rewires from canonical-path to plugin-path; partition reclassifies. Composes against M-FBM's file-based baseline as enrichment. v0.1.x; not counted toward v0.1.0 critical path. | AC.MGMP.1..4 + AC.MGMP.S | 60–120 min | 90 min |

**Total AI-time (sequential builds + parallel docs):**

- **M1.rename series sum (M1a..M1g, sequential):** roughly **5.5–10 h AI wall-clock** (M1a 35 min + M1b 90 min + M1c 45 min + M1d 60 min + M1e 135 min + M1f 45 min + M1g 45 min = 7.5 h midpoint). The post-split sum is higher than the pre-split monolithic estimate (45 min) because the original estimate was empirically 5–10× too low (per series-master §1); the split makes the actual cost visible as named slices rather than failing once at the monolithic seal step.
- **Critical path (sequential builds M1.rename-series → M2 → M3 → M4 → M5 → M-FBM → M6 → M9 → M11 → M12):** ~11–17 h AI wall-clock midpoint ~13 h (memory-pivot M-FBM 90–180 min midpoint 135 min added between M5 and M6 per `oss-v0-1-0-publish-memory-pivot.md` §6). Was 9–14 h pre-pivot. M-GMP (60–120 min) sits in the v0.1.x lane post-M12; not counted toward v0.1.0 critical path.
- **Parallel lanes:** M7 (docs, ~30–60 min) overlaps with M1–M6 builds; M8 (license/governance, ~10–20 min) overlaps with any build; M10 (bus-factor) is owner-time only, runs alongside everything.
- **Owner gate-review time:** distinct, additive. Three gates: M8/license-governance review (5–15 min), M11/synthesis-dry-run review (~30 min/reviewer × 3–5 reviewers + owner ~30 min), M12/publish-and-tag review (5–15 min). Bus-factor-1 review circle (M10) is days–weeks calendar, not AI-time.
- **Programme total:** **roughly 9–14 h AI wall-clock + multi-day owner gate-review + days-to-weeks M10 calendar lane**, multi-session.

---

## 6. Sequencing — parallel-safe lanes vs serial-amendment lane

Per `feedback_serialize_amendment_builds`: amendment builds in the
canonical tree race on `pos-amend`, `index.lock`, and tests; they
**must be serial** unless worktree-isolated (which is not yet
production-verified). Documentary authoring agents and research
agents are parallel-safe. Owner-driven recruitment is calendar-
parallel.

```
                                                                  GATES
TIME →
                                                                  
Lane A — sealed-component build chain (SERIAL):
  M1.rename-series (M1a → M1b → M1c → M1d → M1e → M1f → M1g) →
  M2.partition → M3.wire-clis → M4.wire-dispatch →
  M5.wire-dormancy → M-FBM.memory-pivot → M6.dev-sdlc-plugin → M9.scrub → M11.dry-run → M12.publish
  (v0.1.x post-M12: M-GMP.graphiti-plugin)
                                                              [M8.lic]   [M11.gate] [M12.gate]
                                                              owner       owner      owner

Lane B — documentary (PARALLEL with Lane A; multi-artefact background agents):
  M7.docs-lane (positioning, README, architecture, getting-started,
                components/, design/odd.md)
                                                              [M8.lic gate co-occurs]

Lane C — license/governance (TRIVIAL; PARALLEL):
  M8.license-governance (single docs commit; no fence)
                                                              [M8 gate]

Lane D — bus-factor-1 (OWNER-TIME calendar; PARALLEL):
  M10.bus-factor (recruit 3–5 reviewers; each reads positioning+architecture+odd)
                                                              ┴ must close before M12 public-flip
```

**Concrete sequencing rules:**

1. **M1 must build first** — every downstream amendment references
   the post-rename surface (paths, env vars, OTel roots, CLI names,
   `loam.*` namespace). Building M2–M6 against pre-rename surface
   doubles work.
2. **M2 (partition) gates M9 (scrub) and M11 (dry-run)** — the
   partition manifest is the contract the synthesis tool and the
   sweep tests read.
3. **M3, M4, M5 are independent** in scope but **serial in the
   shared tree.** Order is builder's call inside the amendment-
   sequence; M3 (wire-clis) is the cheapest and is recommended
   first to land easy progress.
4. **M6 (Dev/SDLC plugin) is the largest single cycle** (~90–180
   min) and is parallel-safe with the M7 docs lane but serial with
   other amendment builds. Recommend running M6 alongside M7's
   background docs agents.
5. **M7 (docs) parallel with builds** — multiple background agents
   compose the docs corpus; each writes a disjoint file set; agents
   are dispatched as `oss-v0-1-0-publish-public-docs.md` sub-plans
   with explicit objectives and ODD-check halt clauses.
6. **M8 (license/governance) lands any time before M11**; trivial-
   shape; can land alongside M7's docs commits.
7. **M9 (scrub) runs after M1 (rename), M2 (partition), and ideally
   after all wire-and-plugin amendments** — so the scrub captures
   the final public surface, not a moving target.
8. **M11 (dry-run) is the integration gate** — owner + review
   circle exercise the synthetic tree; halt-and-surface fold-back
   to prior amendments if findings warrant.
9. **M12 (publish) is gated on M10 (bus-factor) closing** — the
   review circle must be in place before the public-flip per
   AC.OSS.7.

---

## 7. Owner gate-review checkpoints

Three named owner-review gates (distinct from per-amendment seal
checkpoints, which are builder-side). Each gate has an artefact
the owner sees and a decision the owner makes.

### Gate G1 — License + governance review (after M8)

**What owner sees:**
- `LICENSE` (Apache-2.0 with copyright header)
- `CONTRIBUTING.md` (workflow + AC + ODD + sign-off)
- `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1)
- `SECURITY.md` (vulnerability-reporting address + disclosure
  timeline)

**What owner decides:**
- Approve license text (especially the copyright line —
  "Copyright 2026 Luke Ivers and contributors").
- Approve the SECURITY.md vulnerability-reporting address (owner
  email vs `loam-security@…` placeholder).
- Approve the Apache-license header script (which files get
  headers; runtime-only by recommendation).

**Time estimate:** 5–15 min owner time. Owner reads four short
files and rules.

### Gate G2 — Synthesis dry-run review (after M11)

**What owner sees:**
- A private GitHub repo at `lukeivers/loam-staging` (or analogous
  staging path) with the synthetic v0.1.0 tree.
- The 3–5-person review circle's notes (collected privately).
- An automated sweep report (the AC.OSS.3 grep, the AC.OSS.5
  literal-match check, the feature-usage-audit re-run from
  AC.OSS.2).

**What owner decides:**
- Approve the public surface as v0.1.0-shippable, or
- Halt-and-surface: name the findings that need fold-back into
  prior milestones; specify the corrective amendment scope.

**Time estimate:** ~30 min owner browsing time + circle's
parallel ~30 min × 3–5 reviewers (calendar-parallel; max-of, not
sum-of). Fold-back, if needed, adds 1–2 amendment cycles
(20–60 min AI-time).

### Gate G3 — Publish-and-tag review (during M12)

**What owner sees:**
- The synthetic `framework-only` HEAD ready for push as
  `lukeivers/loam:main` initial commit (squashed; parent-chain
  dropped at v0.1.0).
- Authored release notes (from positioning + architecture).
- The bus-factor-1 review-circle list (AC.OSS.7 closed).

**What owner decides:**
- Approve squashed initial commit message + authorship + co-
  author trailer policy (recommend keep `Co-Authored-By:
  Claude` trailers — honest about build process).
- Approve release-notes text.
- Approve the public-flip (private → public) — final go/no-go.

**Time estimate:** 5–15 min owner time. Owner reads release
notes, confirms list, rules.

**Note on M10/bus-factor:** not a single-point gate — it's a
calendar-parallel obligation that must close before G3's public-
flip. Owner-driven; days-to-weeks calendar. AI cannot
compress this.

---

## 8. Halt-and-surface conditions

Per `feedback_subagent_odd_violation_halt`: each amendment's
builder halts and signals owner if any of the following fire. The
builder does NOT silently extend a violation. **Builders must
also halt if they find an ODD violation in surrounding code/docs**
(per the global rule).

1. **An audit recommendation contradicts a sealed-component
   invariant.** If wiring `dispatch_with_scope` requires breaking
   a primary-persona seal contract, or if the dormancy-rename
   touches a non-sealed surface that turns out to be load-bearing
   in the seal-test sidecar, halt — the amendment fence is wrong.
2. **The path to v0.1.0 implies a methodology breach.** E.g. an
   AC cannot be authored outcome-shape; or the publish-mode
   partition mechanism requires LLM-mediated synthesis (loses
   determinism); halt.
3. **An ODD violation surfaces in surrounding code/docs.** Per
   `feedback_subagent_odd_violation_halt`. Halt + surface; do NOT
   extend.
4. **Wiring D-1 / D-2 / D-3 cannot land without touching sealed
   components outside the named amendment fence.** Halt; owner
   rules whether to extend the fence or split into a sub-amendment.
5. **The Dev/SDLC plugin (M6) requires a new top-level objective
   not covered by AC.PO.1 + AC.PO.2.** Halt; owner rules whether
   to author a v1.3 spec addendum or recompose the plugin under
   existing ACs.
6. **The synthesis dry-run (M11) reveals "still looks like a
   rebuild" or "too obscure to follow" findings.** Fold-back to
   prior milestones; document fold-back amendments in §14;
   re-run dry-run.
7. **HC#3 binding analogue — no new third-party deps.** Same
   constraint as d-migration HC#3; new deps require explicit
   amendment of the per-component permitted list and owner
   ruling.
8. **Wall-time exceeds projected per-amendment estimate by >50%.**
   Halt with current-state report; owner triages whether to
   continue, split, or pause.
9. **Pre-existing test fails post-rename or post-partition.**
   During M1 or M2, if a pre-existing component test fails after
   the rename or after the partition manifest lands (other than
   mechanical-fixture-update fails for the surface shift itself),
   halt — that's a bug.
10. **Bus-factor-1 mitigation (M10) cannot close before G3.** If
    the 3–5-person review circle is not in place at G3, **delay
    public-flip 2 weeks** per Idea 12's research recommendation;
    do NOT flip with bus-factor unmitigated.
11. **Personal-info scrub residual matches.** If the M11 sweep
    finds `pos-v2` / `lukeivers` / `ivers-corp` matches in
    user-facing prose of the synthetic tree (matches in dev-only
    artefacts are out of scope), halt — M9 scrub is incomplete.
12. **Synthesis-time substitution (M9) introduces nondeterminism.**
    If the rewrite is not purely textual `s/X/Y/` with a fixed
    table, halt — determinism + idempotence are
    `pos-publish-framework-only` invariants per audit §6.3.

---

## 9. Out of scope (explicit)

Per ODD §2.5 and the locked plan:

- **Multi-plugin v1.** R2 caps v1 at the Dev/SDLC plugin only.
  Other plugins (project/task overlay, communications, knowledge
  management, finance, creative, health, trading, legal) are
  v0.2 and beyond.
- **Idea 10 Phase 4–5 work.** Plugin pre-naming and `plot` user-
  facing CLI alias for scope-of-work — deferred to v0.2.
- **Long-form ODD methodology + odd-in-loam as public docs.**
  Audit D5: condensed `docs/design/odd.md` ships; long forms
  remain DEV-MODE-only.
- **History rewrite of canonical pos-v2.** Audit §1.1: no secret-
  leak forcing function; squash at synth time only. Canonical
  keeps full history.
- **Org-level repo migration.** R3: personal account v0.1.0; org
  migration is a future option, not v0.1.0 scope.
- **HN / blog post / community-channel announcement (M10 in
  audit numbering, NOT this plan's M10).** Owner-driven;
  decoupled; not part of the v0.1.0 plan-doc.
- **`upgrade-merge-resolver` retirement.** Verify-usage flagged
  as audit observation but not v0.1.0 scope; lands as its own
  cleanup amendment if dead-code confirmed post-publish.
- **Workspace-tooling adoption.** Same as d-migration §7 —
  monorepo (uv / hatch) tooling stays out unless per-component
  editable-install pain emerges.
- **Multi-framework workspaces.** A workspace pulling from two
  canonical sources is a future direction, not v0.1.0.
- **Recollapse/reseal (Idea 11).** Deferred until trigger.
- **Channel rules structural amendment** (per `oss-publish-master-
  dossier.md` Decision Set A3). Captured to FUTURE_IDEAS_DRAFT
  (canonical post-#75); sequenced after Idea-25 graduation
  lands the workspace `primary_channel` contract field. Not
  part of v0.1.0.

---

## 10. Cross-references

- **Idea 10 — rename to loam:** `docs/rebuild/FUTURE_IDEAS.md:430`.
  Authority: `docs/rebuild/plans/loam-rename-decisions.md`.
  Mechanics: `.scratch/claude-output/loam-rename-migration-plan.md`.
- **Idea 12 — open-source launch of loam:**
  `docs/rebuild/FUTURE_IDEAS.md:510`. Authority: this plan +
  `docs/rebuild/plans/oss-launch-decisions.md` (M0 output).
  Research: `docs/rebuild/plans/research/loam-open-source-launch-research.md`.
- **Idea 3 — initial plugin suite (Dev/SDLC plugin scope):**
  `docs/rebuild/FUTURE_IDEAS.md:278`. Source for M6.
- **Audit framework (M0–M10 milestone shape):**
  `.scratch/claude-output/oss-readiness-audit.md`.
- **Wired-vs-dormant matrix (D-1 / D-2 / D-3 source):**
  `.scratch/claude-output/feature-usage-audit.md`.
- **Master decisions dossier (synthesis):**
  `.scratch/claude-output/oss-publish-master-dossier.md`.
- **Synthesis tool (publish mechanism):**
  `framework/tools/pos-publish-framework-only/`.
- **VALUE_PROPOSITION (prime objective):**
  `docs/rebuild/VALUE_PROPOSITION.md` — primary-persona test +
  harness test.
- **STATE.md** — governing rules + component table (OSS-publish row).
- **D-migration master plan (shape reference):**
  `docs/rebuild/plans/d-migration.md`.
- **Two-modes master plan (shape reference):**
  `docs/rebuild/plans/two-modes-and-multi-workspace/MASTER.md`.
- **Duration estimation rubric (AI-time categories):**
  `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_duration_estimation_rubric.md`.
- **Serialize-amendment-builds rule:**
  `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_serialize_amendment_builds.md`.
- **Background-default for multi-artefact authoring:**
  `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_background_default_for_authoring.md`.

---

## 11. Spec-objective placement (per CLAUDE.md §2.5 framing)

This programme binds to **AC.PO.1 (translation-burden absorption)
+ AC.PO.2 (toolkit-primitive growth)** in
`docs/rebuild/VALUE_PROPOSITION.md` as the prime spec hooks. Per
`feedback_value_proposition_as_prime_objective` (CLAUDE.md §2.5),
AC.PO.1 / AC.PO.2 are the prime objective's ACs and every
component/feature/amendment ladders up.

**Reverse trace per AC:**

- **AC.PO.1 (translation-burden):**
  - **AC.OSS.1 (stranger-bootable):** the entire point — a
    stranger experiences the harness as "Claude greets me with
    what needs attention; I never had to learn `pos-amend`, ODD,
    or amendment-numbering to get my workspace useful."
  - **AC.OSS.5 (rebrand):** loam is a single-syllable identity;
    pos-v2 carries internal-build-team flavor.
  - **AC.OSS.6 (Dev/SDLC plugin):** ODD-by-default for new
    projects authored inside loam reduces translation burden
    for the developer audience — the methodology pos-v2
    practices natively becomes the methodology applied to new
    work without the user explicitly opting in.
- **AC.PO.2 (toolkit-primitive):**
  - **AC.OSS.2 (wired components):** the harness ships fully
    wired; future workspace tooling composes on a complete
    surface, not a half-asleep one.
  - **AC.OSS.3 (no dev machinery in public):** the public
    artefact's toolkit IS the harness; partition mechanism is
    queryable at synth time.
  - **AC.OSS.6 (Dev/SDLC plugin):** the first plugin
    demonstrates the workspace-bootstrap extension protocol —
    the toolkit grows by one fully-formed verb (`/dev` or
    similar plugin-shape) for the persona to invoke.

**No new top-level spec objective is required.** This is method-
shape realignment of the existing prime objective ACs, not a new
outcome axis. Halt trigger 5 fires if any builder finds an
amendment's work cannot fit under existing ACs.

---

## 12. Three-lens analysis (per CLAUDE.md design lenses)

### Lens 1 — Claude leverage

- The publish-mode partition (M2) extends `loam-mode`'s existing
  Claude-Code-shaped manifest pattern. No new MCP server, no new
  hook event — incremental composition on the existing
  partition primitive.
- M4 (wire dispatch_with_scope) leverages Claude Code's native
  PreToolUse hook event on `Task` to intercept Agent dispatches.
  The four-gate chain becomes a Claude-native interception
  point; no bespoke dispatch protocol required.
- The synthesis tool itself (M2 extension) is pure git plumbing —
  determinism preserved, no LLM in the loop. Per audit §7
  observation, this is correct.
- M6 (Dev/SDLC plugin) composes against the workspace-bootstrap
  extension protocol; plugins are a Claude-Code-shaped artefact
  per Idea 3's framing.
- The condensed `docs/design/odd.md` (M7) lets external users
  invoke ODD as a methodology against Claude's native
  capabilities (skills, hooks, plugins) without the heavy
  authoring corpus.

**Pass.**

### Lens 2 — Harness + primary-persona value

- **Primary-persona test** (translation burden):
  - Stranger-clone path (AC.OSS.1): persona greets, surfaces
    next action, asks the persona-onboarding question.
    Stranger does not learn pos-v2 vocabulary.
  - Wired components (AC.OSS.2): persona dispatches Agents and
    they automatically pass through the four-gate chain — no
    manual gate-invocation by the user.
  - Rename (AC.OSS.5): one identity, one CLI verb (`loam`).
- **Harness test** (toolkit primitive):
  - Publish-mode partition (M2) adds a queryable surface
    ("what ships? what doesn't?") downstream features can read.
  - Per-component CLIs (M3) add five operator-callable verbs.
  - Dev/SDLC plugin (M6) is itself a new toolkit verb the
    primary persona invokes for "set up a new project under
    ODD" intent.

**Pass on both tests.**

### Lens 3 — ODD authoring

Each AC is outcome-shape, observable, deterministic. Method-
shape choices (exact files, exact tests, exact substitution
tables) are the per-amendment builder's call inside each AC's
outcome bound — captured in each amendment's builder-plan + §14
method-decision register.

Behaviour-count check: forward direction passes per §3 above;
reverse direction (every code path / branch / dependency / test
in each amendment's diff → backing AC) is each builder's pre-
seal check.

**Pass.**

---

## 13. Decisions remaining for owner ruling

**Three Idea-12 rulings already LOCKED 2026-04-29** (R1–R3 in §2).
The three wire-or-strip decisions also LOCKED (D-1 / D-2 / D-3 in
the ancestor record). The plan-author surfaces the residual
**outcome-shape** decisions below; method-shape (which exact files,
which exact substitution tables) is the per-amendment builder's
call.

### D-Q.OSS.1 — License copyright line wording

**Question.** Audit recommends `Copyright 2026 Luke Ivers and
contributors`. Alternative: `Copyright 2026 Luke Ivers` (cleaner
until contributors land). **Recommendation:** `Copyright 2026
Luke Ivers and contributors` — signals openness to contribution
even at v0.1.0 with no contributors yet, matches Apache-2.0
contribution-friendly tone.

### D-Q.OSS.2 — SECURITY.md vulnerability-reporting address

**Question.** Owner's email (`lukeivers@gmail.com`) directly,
or a placeholder address (`security@…` / GitHub Security
Advisories) before public-flip? **Recommendation:** GitHub
Security Advisories (private vulnerability reporting feature)
+ a fallback note pointing to a project-specific email. Keeps
the owner's personal email out of the public surface.

### D-Q.OSS.3 — Squashed-initial-commit author identity

**Question.** Audit §4.8: keep `Co-Authored-By: Claude Opus 4.7
(1M context) <noreply@anthropic.com>` trailer in the squashed
initial commit, or strip? **Recommendation:** keep — honest about
the build process; the public surface should not present a false
narrative of who authored what.

### D-Q.OSS.4 — `loam-staging` repo lifecycle

**Question.** After M11 dry-run, does the staging repo persist
(useful for future v0.x dry-runs) or get deleted? **Recommendation:**
persist as a private repo; reuse for every minor-version dry-run.
Cost: GitHub private repo (free for personal account).

### D-Q.OSS.5 — Dev/SDLC plugin surface placement

**Question.** Plugin lives at `framework/dev-sdlc/` (in-tree, post-
rename naming) or `plugins/dev-sdlc/` (separate plugin tree
recognised by workspace-bootstrap's extension protocol)?
**Recommendation:** `plugins/dev-sdlc/` — establishes the plugin-
tree pattern at v0.1.0 for future plugins to follow. Defer if
M6's builder finds the in-tree shape simpler — builder's call.

### D-Q.OSS.6 — Personal-info-scrub default-substitution table

**Question.** Current state: M9's substitution table is "Luke
Ivers" → "Alice Anderson", "Acme Corp", `<workspace>/loam/`.
Acceptable, or refine? **Recommendation:** accept; refine in
builder-plan if M9's builder finds friction — fixture names
are arbitrary anyway.

---

## 14. Method-decision record (post-build per amendment)

To be filled by each amendment's builder post-build, per the
`d-migration` precedent (§14 SHA list + per-amendment method
records).

### M1.rename — OSS-build.M1.x

Now a multi-amendment series (M1a..M1g per series-master `oss-v0-1-0-publish-rename.md`). Each sub-amendment carries its own method-decision register inside its own sub-plan-doc:

- M1a — `oss-v0-1-0-publish-rename-1a.md` §12 (sealed `143d465`).
- M1b — `oss-v0-1-0-publish-rename-1b.md` §12 (in flight).
- M1c–M1g — sub-plan-docs authored at each sub-amendment's dispatch time.

### M2.partition — OSS-build.M2.x

(post-build)

### M3.wire-clis — OSS-build.M3.x

(post-build)

### M4.wire-dispatch — OSS-build.M4.x

(post-build)

### M5.wire-dormancy — OSS-build.M5.x

(post-build)

### M6.dev-sdlc-plugin — OSS-build.M6.x

(post-build)

### M7.docs-lane — OSS-build.M7.x

(post-build per parallel agent)

### M8.license-governance — OSS-build.M8.x

(post-build)

### M9.scrub — OSS-build.M9.x

Sealed `2161cb1` 2026-04-29 (amendment #91). Builder:
sub-plan-doc + manifest + feature + apply + corrective +
seal commit ladder per M9 sub-plan §14. Substitution pass
landed in `loam.publish_framework_only.synth` consuming the
M9-locked 4-entry SUBSTITUTION_TABLE per master plan §13
D-Q.OSS.6 ruling. 12-file in-place fixture refactor across 7
components. AI-time actual ~30 min (within calibrated 10–25 min
band; +5 min over upper bound due to env-test flake on
test_D5_1_memory_graphiti during scoped sweep [resolved by
isolation rerun] + corrective commit for HSF#1 stale workspace-
sync test text). Method-decision register narratives in the
sub-plan §14 (D-build.M9.1..M9.6).

Halt-and-surface findings folded into the next-amendment
register: HSF#1 (gate-test partition-completeness gap; resolved
in-band as a doc-only test fix at corrective commit aa647c4 +
captured for follow-on plugin-hooks-test extraction amendment) +
HSF#2 (plist source paths; verified workspace-bootstrap renderer
contract at plan-time) + HSF#5 (pOS fixture rename; in-scope at
AC.OSS-M9.5).

### M10.bus-factor — OSS-build.M10.x

(post-recruit; names recorded in `oss-launch-decisions.md`,
NOT here)

### M11.dry-run — OSS-build.M11.x

(post-dry-run; findings + fold-back amendments listed)

### M12.publish — OSS-build.M12.x

(post-publish; public repo URL + tag SHA + release-notes URL)

### Commit SHAs

(post-build per amendment)

- M1a feature commit: `2b2899b` (sealed)
- M1a apply commit: `5dc1122` (sealed)
- M1a corrective commit: `92098e1` (AC39_6 sentinel)
- M1a sub-plan §11 update: `f3041a5`
- M1a seal commit: `143d465`
- M1a manifest correction: `aa9aa5a`
- M1a §14 SHA-register backfill: `481c697`
- M1b feature commit: `<TBD>`
- M1b apply commit: `<TBD>`
- M1b seal commit: `<TBD>`
- M1c..M1g commits: `<TBD>` (sealed at each sub-amendment's dispatch)
- M2.partition amendment commit: `<TBD>`
- M2.partition seal commit: `<TBD>`
- M3.wire-clis amendment commit: `<TBD>`
- M3.wire-clis seal commit: `<TBD>`
- M4.wire-dispatch amendment commit: `<TBD>`
- M4.wire-dispatch seal commit: `<TBD>`
- M5.wire-dormancy amendment commit: `<TBD>`
- M5.wire-dormancy seal commit: `<TBD>`
- M6.dev-sdlc-plugin amendment commit: `<TBD>`
- M6.dev-sdlc-plugin seal commit: `<TBD>`
- M7.docs-lane commits (multiple, per docs file): `<TBD>`
- M8.license-governance commit: `<TBD>`
- M9.scrub sub-plan commit: `0364ec9`
- M9.scrub feature commit: `3ae817c`
- M9.scrub manifest commit: `d43cc28`
- M9.scrub apply commit: `3e6ac88`
- M9.scrub corrective commit: `aa647c4` (workspace-sync test_AC_D_5_5_1
  tightened post-M1g + M6b.0 + M6b.1)
- M9.scrub seal commit: `2161cb1`
- M11.dry-run synthesis commit + staging push: `<TBD>`
- M12.publish — squashed initial commit on `lukeivers/loam:main`:
  `<TBD>`
- M12.publish — `v0.1.0` tag SHA: `<TBD>`

---

## 15. Backwards-compat verification (per amendment, post-build)

To be filled by builders post-build. Each amendment's record
documents:

- All pre-existing tests pass post-amendment.
- Any test fixtures requiring mechanical updates documented with
  intent preservation.
- HC analogue (per-amendment fence) verified via seal-diff test.
- HC analogue (no regression) verified via touched-component
  pytest pass (full repo-wide pytest skipped pre-seal per
  `feedback_amendment_dispatch_speedups`).
- HC analogue (no new third-party deps) verified via `uv.lock`
  diff.

---

## 16. Halt-and-surface findings encountered during plan authoring

Per the dispatch's halt-and-surface clause: surface any audit-
recommendation conflict with sealed-component invariants,
methodology breaches, or surrounding-code/-doc ODD violations.

**Findings:**

1. **(No audit/invariant conflict found.)** The OSS-readiness
   audit's recommendations and the feature-usage audit's wire-or-
   strip recommendations compose cleanly with sealed-component
   invariants. No sealed component's seal-diff window is broken
   by the amendments planned here. (Builders will verify per-
   amendment.)
2. **(No methodology breach found.)** Every milestone has
   outcome-shape ACs. The Dev/SDLC plugin (M6) requires a full
   five-gate cycle, which is the standard for new components;
   no shortcut.
3. **(One observation, not a halt.)** The audit flagged that
   `loam-staging` repo's lifecycle is undefined. Surfaced as
   D-Q.OSS.4 above for owner ruling; not a halt because it
   doesn't block any AC.
4. **(One ODD §2.5 observation, not a halt.)**
   `framework/workspace-sync/src/workspace_sync/canonical_cache.py`
   docstring examples carry `github.com/lukeivers/pos-v2` URLs.
   The path-parsing logic is generic; only docstring examples
   are personal. Out-of-scope-ish, but the M9 scrub amendment
   touches the same file (per audit §4.7) so the cleanup
   compounds naturally. Not a halt.
5. **(Dossier human-time correction applied.)** The companion
   `oss-publish-master-dossier.md` carries "18–35 days" for the
   programme; that's human-developer-time. AI-builder-time is
   ~4–8 h wall + multi-day owner gate-review + days-to-weeks
   M10 calendar lane (see §5–§6 above). Not a halt; corrected
   here. The dossier's recommendation set is preserved; only
   the time framing is re-priced.
6. **(One sequencing observation, surfaced.)** R2 (Dev/SDLC
   plugin must-ship at v1) makes M6 the largest single cycle
   and a critical-path item. If M6 unexpectedly blows out
   (~180 min upper bound + halt-and-surface risk on plugin-
   surface decisions), v0.1.0 timeline shifts. Mitigation: M6
   is parallel-safe with M7 (docs lane), so the docs lane
   absorbs no slip; only the publish gate (G3) shifts.

**Halt summary.** None of the above triggers a halt. All
findings are surfaced for owner awareness; the plan is
authorised to proceed pending M0 owner sign-off.

---

*End of plan.*
