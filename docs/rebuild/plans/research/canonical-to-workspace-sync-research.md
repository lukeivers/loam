# Canonical-to-workspace sync — research

**Date:** 2026-04-26.
**Author:** dispatched research agent (Opus 4.7, 1M context).
**Working tree audited:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Lens:** Lens 1 (Claude-leverage), Lens 2 (harness + primary-persona value), Lens 3 (ODD).
**Owner directive (locked 2026-04-26):** inference-driven conflict resolution, no workspace data loss, idempotent, auditable, default-shipping for non-tech users.

---

## TL;DR — one-page summary

**Does a sync/pull mechanism exist today?** **No.** No component, slash command, or CLI in pos-v2 currently pulls canonical-pos-v2 changes into a downstream workspace clone (e.g. `pos3`) while preserving workspace-local data. The closest adjacent surface is the **self-upgrade framework**, but it is structurally a different operation: it upgrades the framework files of one pos-v2 install in-place at `~/.pos/framework/current/`, on a single machine, with YAML-edit-by-user conflict resolution (no LLM in the loop) and no concept of multiple separate workspace clones.

**The shape needed.** A new mechanism — working name `pos sync` — that pulls canonical changes into a downstream clone at the git-merge level, then runs an LLM-mediated reconciliation pass over conflicts where workspace-supplied content (persona `prompt.md`, `personas/<handle>/contract.yaml`, `<workspace>/.pos/*` state, `<workspace>/.mcp.json`, `FUTURE_IDEAS_DRAFT.md` workspace-side additions, settings overrides) collides with upstream framework changes. Inference reads both sides, understands intent, and proposes a resolution; the user reviews and overrides via a structured artefact at `<workspace>/.pos/sync/<timestamp>/`.

**Recommended shape.** A single sealed component **`workspace-sync`** that ships:
1. A CLI subcommand (`pos sync` — composes on the existing `pos` CLI surface used by `pos upgrade`).
2. An LLM-mediated `ConflictResolver` that runs as a deterministic-budgeted scope (Lens 1: composes on Claude SDK; Lens 2: persona-invokable as `/sync` slash-command).
3. A structurally-enforced audit log mirroring self-upgrade's `<tag>-conflicts.yaml` shape, extended with `inferred_resolution` + `inference_rationale` + `user_override`.
4. Idempotency via per-resolution sentinels in `<workspace>/.pos/sync/`.

**Implementation form.** **One sealed component + one amendment-shape**. The component is small (research suggests ~12 ACs spread across detection, inference, audit, and idempotency); the amendment is "introduce `workspace-sync` as a new sealed component composing on self-upgrade's conflict-detection primitives." A single research+plan dispatch can graduate this directly to a sealed-component cycle once owner rules on the seven decisions surfaced in §6.

**Halt note.** None of the four halt-and-surface conditions named in the dispatch (new top-level objective; sealed-component edits; new LLM-call surface; mechanism already exists) fire — but **D-1 (does this constitute a new top-level spec objective?)** is on the edge and is named for owner ruling.

**Bottom-line recommendation.** Author one research-doc-anchored sealed component (`workspace-sync`); single-amendment graduation if owner rules D-1 against new-objective; otherwise it lifts into a new spec objective and decomposes into 2–3 sub-amendments. Active programme stays unblocked either way.

---

## Decisions for owner ruling (named, with recommendations)

Per `feedback_summarize_and_surface_decisions`. Each decision has a recommendation; owner rules from this summary.

### D-1. Spec-objective placement — new top-level objective, or composition?

**Question.** The two-modes-and-multi-workspace umbrella (Idea 13) treats pos-v2 as "single GitHub-distributed repository." Multi-workspace concurrency was deferred. The objective tree never named "downstream workspace pulls canonical updates" because the mental model has been "one canonical install, possibly per machine." Does `pos sync` constitute (a) a new top-level objective in spec v1.x; (b) composition on existing v1.0 self-upgrade objective extended to "downstream-workspace-from-canonical" semantics; or (c) a dev-discipline tool only (workspace-instances-of-canonical isn't part of the shipped contract)?

**Recommendation.** **(b)** — extend the self-upgrade clause to cover the "downstream pull" case as a sibling shape. The seven-clause acceptance contract (a–g) already names a "no silent skip" + "reversible" + "in-flight tasks preserved" + "personas load unchanged" semantic; reframe these as "across pull" rather than "across upgrade." Single new clause needed: **(h) inference-mediated conflict resolution with audit and override** — that's the only thing self-upgrade's contract doesn't already imply. (a) is heavy (new top-level objective, new acceptance criteria across the spec); (c) breaks Luke's locked requirement that the mechanism "ships as a default everyone inherits" — dev-discipline tools live under `tools/` and don't ship in NORMAL USE. Halt-trigger for (a) named but recommendation lands at (b).

### D-2. Mechanism shape — CLI, slash-command, or both?

**Question.** Where does the user invoke `pos sync`?

**Options.** (a) CLI only (`pos sync` in the workspace's venv); (b) slash-command only (`/sync` invocable from any Claude Code session); (c) both (CLI is canonical, slash-command is persona-invokable wrapper).

**Recommendation.** **(c)**. Per Lens 1 (Claude-leverage): the slash-command IS the persona-invokable form, composes on the slash-command primitive Claude Code already exposes. Per Lens 2 (primary-persona test): the persona must be able to translate "pull updates from canonical" into the right execution path without the user knowing the shape — `/sync` is that hook. The CLI underneath is what the slash-command invokes. Two surfaces, one mechanism.

### D-3. Conflict-resolution timing — at sync time, or per-file?

**Question.** When does the LLM-mediated resolver run?

**Options.** (a) **At sync time, batched.** Detect all conflicts; run one resolver pass; write a single audit artefact; user reviews top-down. (b) **Per-file, on-demand.** Detect conflicts; surface each to the user one at a time; the resolver runs interactively. (c) **Background, with summary surfacing.** Detect conflicts; run resolver in a background scope; persona surfaces "N conflicts resolved, ready for review" when complete.

**Recommendation.** **(c) for default, (a) as fallback for non-Claude-mediated runs.** Lens 1: composes on the background-scope primitive (cost-governance budgeted scope) the harness already has. Lens 2: aligns with `feedback_background_agents.md` — long resolution runs go to background so the main session stays interactive. The persona invokes `/sync`, the resolver runs in a background scope with a declared token budget, completion notification flows through the harness's existing `BackgroundWorkMonitor` surface. (a) is the form for "user invokes from a terminal, no Claude session active."

### D-4. Workspace-data envelope — what's preserved?

**Question.** What counts as "workspace data" the sync must preserve?

**Recommendation (locked categories).** Three classes mirroring D-MASTER.2's `~/.claude/`-style global-vs-workspace partition, with a third class added:
- **Class A — Workspace state (always preserved, never overwritten by sync):** `<workspace>/.pos/` (tracker DB, orchestrator/scope-of-work SQLite, first-run.state, in-flight scopes), `<workspace>/personas/` (persona contracts), `<workspace>/.mcp.json`, `<workspace>/.scratch/`, `<workspace>/CLAUDE.md` if user-modified, `FUTURE_IDEAS_DRAFT.md` workspace-side additions.
- **Class B — Operator preferences (preserved with override-resolution, defaults from canonical pulled if not overridden):** `<workspace>/memory.yaml`, `<workspace>/safety/`, `<workspace>/cost/`, etc. — anything mirroring D-MASTER.2's "preference files."
- **Class C — Framework code (canonical wins on no-conflict; LLM resolves on conflict):** Python source under sealed components, docs/, tools/, etc.

The class-A/B distinction is exactly what self-upgrade already structurally enforces; the new bit for sync is "what's a Class-A path in a downstream clone." Recommendation: workspace-supplied paths are declared in a `<workspace>/.pos/sync-protected.yaml` shipped in the scaffold's defaults (mirrors safety-layer's `always_ask.yaml` Pydantic-validated load pattern).

### D-5. Inference budget — how much does the resolver cost?

**Question.** What's the token-budget ceiling for a single sync's LLM-mediated resolution?

**Options.** (a) Hard ceiling (e.g. 50k tokens per sync); (b) per-conflict budget (e.g. 5k per conflict, scaled by file size); (c) user-declared at invocation.

**Recommendation.** **(b) with workspace-tunable ceiling.** Composes on cost-governance's existing per-scope budget primitive (Lens 1 + the Phase-3 cost component already shipped). The per-conflict budget is a declared scope; the cost-governance gate fires structurally; a sync with too many conflicts hits ceiling and halts, surfacing "X conflicts resolved, Y deferred — bump budget or resolve manually" rather than running indefinitely. Workspace-tunable per `~/.pos/sync-config.yaml` global default.

### D-6. Failure mode — partial sync allowed?

**Question.** If the resolver succeeds on N of M conflicts and fails on the rest, what happens?

**Options.** (a) **Whole-or-nothing** (mirror self-upgrade's atomic rollback). (b) **Partial commit + audit.** Resolved conflicts land; unresolved ones halt the sync but already-resolved files stay. (c) **Stage all changes, single accept-or-reject gate.**

**Recommendation.** **(c)** — stage to `<workspace>/.pos/sync/staging/`, present audit, single accept-or-reject by user (or automatic if all conflicts auto-resolved with high confidence). (a) is too brittle — one stuck conflict dooms a 500-file sync. (b) leaves the workspace in a half-state that violates idempotency. (c) is what `git merge` does conceptually; staging gives the user atomic acceptance.

### D-7. Re-runnability and convergence semantics

**Question.** What does "idempotent / re-runnable" mean concretely when canonical has moved between two sync invocations?

**Options.** (a) **Strict idempotency** — if user re-runs sync against the same canonical commit, no-op (no resolver invocations, no audit writes). (b) **Convergent idempotency** — re-runs against the same canonical state always reach the same workspace state regardless of intermediate state.

**Recommendation.** **(b)** is the locked contract. Operationally: every sync writes a `<workspace>/.pos/sync/state.yaml` recording canonical commit pulled-from + last-sync-timestamp + last-resolution-fingerprints. A re-run reads that state, fast-paths past unchanged conflicts, only invokes the resolver on what's actually new. (a) would force "you already pulled this" UX even when the workspace was perturbed mid-sync.

---

## What exists today (mechanism survey)

### Self-upgrade framework — `self-upgrade/src/self_upgrade/`

**What it does.** Upgrades pos-v2's *own framework files* on a single machine. Reads a release-tag manifest (`pos-release.yml`), pre-snapshots all sealed-component substrates, pauses orchestrator activation, drains, swaps the symlink at `~/.pos/framework/current/`, kicks the orchestrator on the new tree, runs clause-(a)–(g) verification, accepts or rolls back atomically. Documented at `self-upgrade/docs/architecture.md` + `self-upgrade/docs/cli-reference.md`. Sealed 2026-04-19, 14:12.

**Conflict-resolution surface (`conflict_detection.py` + `conflict_report.py`).** When the manifest's expected-pre-SHA mismatches the live file, the upgrade emits `<tag>-conflicts.yaml` (Pydantic-validated, schema in `conflict_report.py`). The `Resolution` enum has six values: `pending`, `auto-accept-local-matches-upstream`, `accept-upstream`, `keep-local`, `three-way-merge` (user supplies merged content), `abort`. **No LLM in the loop** — the user edits the YAML, sets each `resolution` field, and re-runs `pos upgrade`. Clause (g) "no silent skip" is structurally enforced by the absence of `skipped` from the enum.

**Why it doesn't satisfy Luke's requirement.** Three structural mismatches:
1. **Single-machine framework substitution, not cross-clone pull.** The framework's mental model is "one install, swap files at the live path." It has no notion of "canonical lives over there in `/Users/lukeivers/ivers-corp-pos-v2/` and a downstream clone wants to pull from it." The release-tag-and-manifest shape assumes a published release artefact, not a sibling working tree.
2. **No LLM-mediated resolution.** The owner's locked 2026-04-26 requirement is inference-driven conflict resolution. Self-upgrade's resolution is human-edits-YAML; the closest semantic option is `three-way-merge` where the user supplies the merged file. That's not the same as "the persona reads both sides and resolves."
3. **In-flight orchestrator dependence.** Self-upgrade pauses the orchestrator, drains it, SIGTERMs it, then restarts. A downstream-clone pull doesn't necessarily have a running orchestrator — pos3 is a workspace, not a running install — and even when it does, the workspace's data (persona contracts, MCP config, scope state) is conceptually orthogonal to whether the orchestrator is up.

The **shape of the conflict-detection primitive** (`conflict_detection.py`'s SHA-comparison structure, the Pydantic-enforced Resolution enum, the YAML round-trip) is reusable for `pos sync`. The **upgrade-execution sequence** is not.

### Workspace-bootstrap — `workspace-bootstrap/src/workspace_bootstrap/`

**What it does.** Composes the ten sealed foundational components into a running orchestrator + gate chain at boot time. Reads `bootstrap.yaml` listing contributions; resolves discovery via Python entry-points + path-and-callable dict; topologically sorts contributions per phase; constructs `BootstrapHost`; runs each contribution's `contribute(host)`; coordinates shutdown. Sealed 2026-04-20.

**Workspace-scaffolding surface (`adapters/first_run_scaffold.py`).** On first-run in a fresh clone, this writes the workspace's seed files: `personas/` directory (per amendment #36), `<workspace>/.pos/first-run.state` (per amendment #28), tracker DB seed (per amendment #39), scaffolds the venv, populates `<workspace>/.mcp.json` (per amendment #47). The scaffold is **idempotent per file** — missing → write, present → leave alone — and the entire surface is one-shot first-run-only, not a sync surface.

**Why it doesn't satisfy Luke's requirement.** The scaffold is "lay down initial files" not "merge new canonical content into an existing workspace." It deliberately does NOT overwrite workspace-supplied content (the idempotent-per-file rule); on a re-run it leaves all files alone. That's the right behaviour for first-run but the wrong behaviour for sync — sync needs to *update* canonical-tracked files while *preserving* workspace-tracked files.

The **idempotency-via-sentinel** pattern + **per-file dispatcher** shape are reusable for `pos sync`. The **pure-write-no-overwrite** semantic is not.

### Pos-amend (`tools/pos-amend/`)

**What it does.** Mechanises the bookkeeping side of the sealed-component amendment cycle: BASELINE bumps, seal-diff `allowed_prefixes` widening, `tests/SEAL_COMMIT` sidecar bumps, narrative-sidecar appends. This is dev-time tooling — it runs in-canonical to land amendments — and never runs in a downstream clone. Confirmed by inspecting `tools/pos-amend/README.md` and the `pos-amend apply` flow, which writes back to the sealed components' source under `<canonical>/...`.

**Relationship to sync.** Amendments produced by pos-amend are framework-level changes. A downstream clone like pos3 would receive these via `pos sync` — sync is the consumer of pos-amend's output, not a peer. They compose: pos-amend ships amendments into canonical; `pos sync` pulls them into downstream clones.

### Other surfaces searched, found-not-applicable

- `hands-off-lifecycle/hooks/` — first-run hooks; lifecycle bootstrapping; no pull semantics.
- `docs/rebuild/components/` — searched all 23 component proposal directories. None mention "pull from canonical" or "downstream sync."
- `docs/rebuild/FUTURE_IDEAS.md` (689 lines) and `FUTURE_IDEAS_DRAFT.md` (108 lines) — no entry captures the canonical-to-workspace-sync concept. Closest related ideas are #13 (two-modes umbrella) and #18 (reusable integration-test harness for fresh-clone fixtures), neither of which crosses the sync boundary.
- `docs/rebuild/spec/pos-v2-objectives-spec.md` — searched the v1.0 + v1.1 + v1.2 contract. Self-upgrade U1(a)–(g) is the only "framework changes propagate without losing user data" surface. No clause names "downstream workspace pulls."
- `docs/rebuild/plans/two-modes-and-multi-workspace/MASTER.md` — the active four-sub-plan programme (A → E → B → F) addresses single-clone two-mode partitioning. The DEFERRED sub-plans (C / D / G) are about multi-workspace concurrency on one host — orthogonal to canonical-to-downstream-pull.

**Verdict.** Nothing in the codebase or the design corpus covers the workspace-side pull semantic. New work needed.

---

## Recommended shape — `workspace-sync` component

### One-line synthesis

A new sealed component `workspace-sync/` that ships a `pos sync` CLI subcommand, a `/sync` slash-command, and an LLM-mediated `ConflictResolver`; composes on self-upgrade's conflict-detection schema, cost-governance's per-scope budget, and primary-persona's slash-command surface; structurally enforces "no workspace data loss" via a Pydantic-validated `sync-protected.yaml` and "audit trail" via a Pydantic-validated `<workspace>/.pos/sync/<timestamp>/audit.yaml`.

### Three-lens analysis

**Lens 1 — Claude-leverage.** Composes on:
1. **The slash-command primitive.** `/sync` is a persona-invokable surface; users say "pull updates from canonical" → persona translates → `/sync` runs.
2. **The Claude SDK's structured-output capability.** The conflict resolver invokes Claude with an explicit Pydantic-typed response shape; structured output is a Claude-native primitive, not pos-v2-built.
3. **The cost-governance scope.** Resolver runs as a budgeted scope through the existing four-gate chain.
4. **The background-work-monitor.** Long-running resolutions emit progress to the persona's `BackgroundWorkMonitor` surface — surfaces complete naturally.

No part of `workspace-sync` requires changes to Claude Code itself or invents a new primitive. **Halt-trigger 4 (mechanism requires a new LLM-call surface that doesn't exist) does not fire.**

**Lens 2 — Harness + primary-persona value.**

*Primary-persona test.* Reduces translation burden: today, an operator with a downstream clone of pos-v2 has no path other than "git pull and hope." A user who clones pos-v2 from GitHub, configures their workspace, then later wants the latest pos-v2 features — that user is forced to pick between (a) starting over (loses data) or (b) doing a manual git merge (requires git fluency the persona is supposed to absorb). `/sync` translates "I want latest pos-v2" into the right execution path. Pass.

*Harness test.* Adds to the persona's toolkit: `pos sync` is a primitive the persona invokes when the user expresses pull-intent. Composes with the existing harness — surfaces in `BackgroundWorkMonitor`, fires through `cost-governance`, audit lands in `observability-aggregator`. Pass.

**Lens 3 — ODD authoring.** Outcome-shaped acceptance criteria, structural enforcement of audit + protection envelope, halt-and-surface on inference failures. ODD §2.5 forward + reverse audit at plan time. Detail in §AC sketch below.

### Mechanism flow (suggested method — builder's call to refine)

1. **Detect.** `pos sync --canonical <path-or-url>` reads canonical's HEAD. If canonical is a local working tree (e.g. `/Users/lukeivers/ivers-corp-pos-v2/`), read `git rev-parse HEAD`. If a remote, fetch into a temporary worktree.
2. **Diff.** Compute three-way diff: workspace's current HEAD vs canonical's HEAD vs their common ancestor. Categorise files into Class A (workspace-protected, never overwrite), Class B (operator preferences with override resolution), Class C (framework code, normal merge). Class membership read from `<workspace>/.pos/sync-protected.yaml` (Pydantic-validated; missing entries default to Class C with explicit warning).
3. **Conflict-detect.** Class C files: if both sides changed, mark as conflict pending resolution. Class B: if workspace overrode, keep workspace; if not, take canonical. Class A: never touch.
4. **Stage.** Write canonical-clean files to `<workspace>/.pos/sync/staging/<timestamp>/`. For each conflicting file, write three artefacts: `<path>.workspace`, `<path>.canonical`, `<path>.ancestor`.
5. **Resolve.** For each conflict, dispatch a budgeted scope to the resolver: a Claude call with structured output `{resolution: "accept-canonical" | "accept-workspace" | "merged-content", merged_content: str | None, rationale: str, confidence: float}`. The prompt loads all three sides plus context (path, file purpose inferred from path, last-modification messages). Audit written to `<workspace>/.pos/sync/<timestamp>/audit.yaml`.
6. **Present.** Once all conflicts resolved (or budget exhausted), surface the audit to the user: `N files updated cleanly, M conflicts resolved by inference, K halted (budget/low-confidence), Q deferred.` Persona surfaces via the channel the workspace declares.
7. **Accept or reject.** User says "accept" → atomic commit (or working-tree apply if not a git workspace). User says "reject" → staging dropped, no workspace state changes. User says "review file X" → presents that file's audit + content, persona explains; user can override resolution; resolver re-runs only that file.
8. **Bookkeep.** On accept, write `<workspace>/.pos/sync/state.yaml` with canonical commit synced-from + timestamp + per-file resolution fingerprints. Re-runs of `pos sync` consult this state for §D-7's convergent idempotency.

### Acceptance-criteria sketch (12 candidate ACs — final shape lands in plan-doc)

- **AC.S.1.** A `pos sync --canonical <path>` invocation against a workspace at canonical-commit-N pulls all Class-C clean updates from canonical-commit-M (M > N), overwriting nothing in Class A and respecting Class B overrides.
- **AC.S.2.** Conflicts in Class C trigger the LLM-mediated resolver; each conflict produces an audit entry in `<workspace>/.pos/sync/<timestamp>/audit.yaml` containing the file path, both source SHAs, the inferred resolution, the resolver's rationale, the confidence score.
- **AC.S.3.** Workspace-protected paths in `sync-protected.yaml` are NEVER touched by sync — verified by a controlled test fixture with a Class-A file modified on both sides.
- **AC.S.4.** `<workspace>/.pos/sync-protected.yaml` is Pydantic-validated at sync-load time; missing categories raise structural error; an override of the framework-floor protected paths is rejected (mirrors safety-layer's `always_ask.yaml` floor pattern).
- **AC.S.5.** Re-running `pos sync` against the same canonical commit + same workspace state is a no-op (no resolver invocations, no audit writes) — convergent idempotency.
- **AC.S.6.** A sync hitting the per-conflict budget ceiling halts with a structured report listing resolved / deferred conflicts; user can resume from the deferred list with `pos sync --resume`.
- **AC.S.7.** Atomic accept: on user-accept, the staging directory's content lands in the workspace as one operation; on user-reject, staging is discarded and the workspace is byte-identical to pre-sync.
- **AC.S.8.** The audit artefact is human-readable, sorted by confidence (low-confidence resolutions first for review), and writes to a deterministic path per sync run.
- **AC.S.9.** Resolver invocations run inside a budgeted scope that flows through the four-gate chain (cost, safety, reversibility, observability); cost overruns halt the sync per cost-governance's existing semantics.
- **AC.S.10.** Slash-command `/sync` invokes the same code path as `pos sync` CLI; the persona surfaces background progress through `BackgroundWorkMonitor`.
- **AC.S.11.** A user override on any inferred resolution writes to the audit (`user_override: true`, `override_rationale: <user-supplied>`); the next re-sync reads the override and skips re-inference for that file.
- **AC.S.12.** The whole sync run emits a `pos.sync.*` OTel span with attributes for canonical-commit, workspace-commit, file-count, conflict-count, resolution-mix, total-cost — observability-aggregator ingests automatically per v1.1 R11.

### Composition with self-upgrade

The two surfaces compose: **self-upgrade ships pos-v2 framework releases**; **`workspace-sync` pulls those releases into downstream clones**. They share:
- The Pydantic-validated conflict-report schema shape (`workspace-sync` extends with `inferred_resolution`, `inference_rationale`, `confidence`, `user_override`).
- The "no silent skip" structural rule (the resolver enum has no `skipped` value; the Resolution enum extends self-upgrade's six with `inferred-accept-canonical`, `inferred-accept-workspace`, `inferred-merged`).
- The history directory pattern (`<workspace>/.pos/sync/<timestamp>/` mirrors `~/.pos/framework/history/<tag>/`).

They differ:
- `self-upgrade` operates on `~/.pos/framework/current/` (single live tree); `workspace-sync` operates on `<workspace>/` (the user's clone).
- `self-upgrade` requires a running orchestrator (pause/drain/SIGTERM); `workspace-sync` is orchestrator-agnostic (pull is conceptually a file-system operation).
- `self-upgrade`'s conflict resolution is YAML-edit-by-user; `workspace-sync`'s is LLM-mediated by default (with manual-edit fallback for offline runs).

The composition justifies framing `workspace-sync` as **clause-(h) extension** of the existing self-upgrade contract per D-1's recommendation: same family of guarantees, distinct execution path.

---

## Sequencing and amendment scope

### If owner rules D-1 = (b) — composition on self-upgrade clause

**One sealed component, one amendment cycle.** `workspace-sync/` lands as a new top-level package mirroring `self-upgrade/`'s shape; one research-plan + research-doc + proposal + brief + dispatch chain (the existing five-gate cycle); ~12 ACs above; net-new test surface; consumes `self-upgrade.conflict_report` and `cost-governance` primitives. Single dispatch.

### If owner rules D-1 = (a) — new top-level objective

**Programme of 2–3 amendments + spec amendment.** First, a spec-side addendum naming the new objective ("downstream-workspace pulls canonical updates with semantic conflict resolution"). Then `workspace-sync` lands across two or three sub-amendments: (i) detection + staging; (ii) inference resolver; (iii) accept/reject + audit. Each sub-amendment has its own pos-amend cycle. Programme master plan parallels the two-modes-and-multi-workspace MASTER.md shape.

### If owner rules D-1 = (c) — dev-discipline only

**One dev-discipline plan.** Lives at `tools/workspace-sync/`, never auto-loads in NORMAL USE, only operational for canonical maintainers. **This contradicts the locked Luke requirement** that the mechanism ships as a default everyone inherits — recommendation is to NOT pick (c).

---

## Halt-and-surface check

Per dispatch-brief halt triggers:

1. **A required new top-level objective surfaces** — D-1 names this as a possibility. Recommendation is composition (no new objective), but the boundary is judgment-call. **Surfaced for owner ruling — does not auto-halt.**
2. **Mechanism requires source edits to multiple sealed components** — proposed shape is a NEW component, not edits to existing sealed surfaces. `self-upgrade` is consumed (its public Pydantic schemas + conflict-report module imported), not edited. **No halt.**
3. **Inference-driven conflict-resolution requires LLM-call surface that doesn't exist** — Claude SDK's structured-output capability is the existing primitive; it's already used in pos-v2 (memory-system's Graphiti-mediated extraction; primary-persona's authoring pipeline). **No halt.**
4. **Self-upgrade already provides this** — answered "no" in §"What exists today." Composition is possible but the framework doesn't ship the pull semantic. **No halt.**

**Halt-and-surface conclusion: no auto-halt. Owner ruling on D-1 + D-3 + D-4 (sync-protected envelope) before plan-doc dispatch.**

---

## Asymmetric observations (per `feedback_asymmetric_problem_solving`)

### Asymmetric wins surfaced

1. **Class-A protection envelope is the same shape as self-upgrade's Pydantic-validated `always_ask.yaml`.** The framework-floor pattern is already proven (safety-layer ships it; immune to monkey-patch by design). Re-using the pattern for `sync-protected.yaml` is one Pydantic validator + one YAML schema + one test. **Effort:** very low. **Leverage:** very high — locks "workspace-data-loss-impossible" structurally rather than as advisory. Closes Luke's "no workspace data loss" requirement at the schema level.

2. **The slash-command + CLI dual surface is one substrate.** Slash-commands compose on Claude Code's slash-command primitive; the slash-command body is "invoke the CLI." One implementation, two invocation surfaces. The persona learns one verb (`/sync`) and the operator learns one CLI (`pos sync`). **Effort:** low (a slash-command stub is ~20 lines). **Leverage:** medium-high — closes Lens 1 and Lens 2 in the same primitive.

3. **Convergent-idempotency state file mirrors `first-run.state` shape.** Amendment #28's `<workspace>/.pos/first-run.state` already has the per-workspace state-file pattern. `<workspace>/.pos/sync/state.yaml` is a sibling. Test patterns transfer. **Effort:** very low. **Leverage:** medium.

### Inverse-asymmetric proposals dropped

1. **A full git-merge-driver replacement.** Tempting because git already does three-way merges. But pos-v2's mental model has Class A/B/C envelopes that git's textual merge doesn't understand; building a smart git-merge-driver is more cost than `pos sync` because it has to plug into git's plumbing. Inverse-asymmetric — drop.
2. **An always-on background sync watcher.** Tempting because the persona could "always know" when canonical has updates. But the harness already has `BackgroundWorkMonitor`; surfacing "canonical has new commits" is one cron-style scope, not a new component. Re-use existing surfaces; no separate watcher.
3. **A semantic-aware diff that pre-computes resolution-class for every file.** Would be lovely; cost is medium-high (heuristics over file-shapes are known-brittle). The Class-A/B/C envelope from `sync-protected.yaml` does most of the work; the resolver handles the rest. Drop the semantic-pre-classifier; ship the simpler envelope.
4. **A "trust score" that auto-accepts high-confidence resolutions without user review.** Tempting for non-tech UX. But Luke's locked requirement is "every conflict resolution surfaces what was decided + why, so the user can review and override." High-confidence-auto-accept violates the audit-with-override property. Drop.

---

## Recommended next action

**One follow-on dispatch.** A plan-author dispatch that:
1. Authors the proposal-doc at `docs/rebuild/components/workspace-sync/proposal.md` (mirroring sealed-component proposal shape).
2. Authors the research-plan + research-doc pair if owner rules D-1 = (a) (new objective).
3. Lifts the AC sketch in §"Recommended shape" into a finalised AC list (target: 12–15 ACs).
4. Drafts the manifest YAML for the eventual amendment cycle.

Estimated wall-clock for the plan-author dispatch: 30–60 minutes (per `feedback_duration_estimation_rubric`, this is "single-component plan with research already done"). Goes to background per `feedback_background_default_for_authoring`.

**Pre-condition: owner rules on D-1, D-3, D-4 above.** D-2, D-5, D-6, D-7 can be deferred to plan-doc time (their recommendations are clear enough that the plan-author can proceed unless owner objects).

---

## Summary of the find

| Question | Answer |
|---|---|
| Does pos-v2 have a canonical-to-workspace sync mechanism today? | **No.** |
| Closest existing surface? | `self-upgrade` framework. Different problem (in-place framework upgrade on one machine vs cross-clone pull); reusable primitives (Pydantic conflict schema, Resolution enum pattern, audit shape). |
| Does self-upgrade satisfy the locked requirements? | No — no LLM-mediated resolution, no cross-clone semantics, requires running orchestrator. |
| Recommendation? | Build new `workspace-sync` sealed component composing on self-upgrade's primitives; ships as Class-A-protected sync with LLM-mediated resolver, audit trail, convergent idempotency, slash-command + CLI dual surface. |
| Single amendment or programme? | **Single sealed-component amendment** if owner rules D-1 = composition (recommended). 2–3 sub-amendment programme if owner rules D-1 = new top-level objective. |
| Halt triggers fired? | None auto-fire. D-1 surfaced for owner ruling. |
| Decisions for owner ruling | Seven (D-1 through D-7), each with recommendation in §Decisions above. |

End of research doc. Plan-doc authoring deferred to follow-on dispatch per Luke's "research-and-plan are separate dispatches" preference (`feedback_summarize_and_surface_decisions`).
