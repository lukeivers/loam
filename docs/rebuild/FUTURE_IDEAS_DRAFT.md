# FUTURE_IDEAS_DRAFT.md — no-overhead idea capture

This is a draft surface for *every* improvement idea about pos-v2 — Luke's or the assistant's — captured at point-of-occurrence with no overhead. Sibling to `FUTURE_IDEAS.md` but distinct in lifecycle:

- `FUTURE_IDEAS.md` is **curated**: each idea has a designated number, a rationale section, and a relationship to other ideas.
- `FUTURE_IDEAS_DRAFT.md` is **no-overhead capture**: append a brief bullet with rationale (~3–5 lines) the moment an idea surfaces. No numbering, no curation, no ordering.

**Lifecycle.** During the initial phase of pos-v2 development, entries accumulate. After the initial phase concludes, a daily rigor reviews the draft:

- Incidentally-actioned items get removed (the work happened, the idea served its purpose).
- No-longer-relevant items get pruned.
- Graduate-worthy items get promoted to `FUTURE_IDEAS.md` with full curation.
- Others get dropped or restated.

**Convention.** Agents (background or main-session) **surface to chat** — they do not write to this file directly. The parent (or owner) appends. This avoids file-write races when multiple agents run in parallel, and keeps the parent in the loop on every captured idea.

**Why this exists.** Asymmetric findings, deferred decisions, anti-pattern observations, and feature ideas are valuable signals. Without a destination, they drift away in chat or get lost in memory churn. `FUTURE_IDEAS.md` is too weighty for impromptu capture; this file is the lower-friction destination.

---

## Entries

- **Dispatch-prompt template family.** Every agent dispatch is currently 150–300 lines, with ~70–80% boilerplate (WD, halt triggers, ODD-check, output conventions, etc.). A markdown template with `{{placeholders}}` for the variable parts would collapse per-dispatch authoring cost ~3×. In flight as research+plan task #23.

- **Plan-doc skeleton template.** Broader applicability of the dispatch-template idea: every amendment plan has the same ~13-section shape (objective, AC list, scope/non-scope, manifest fields, §14 register, etc.). Currently propagated by precedent — each new plan starts by reading the previous one and copying structure. A skeleton template would mechanise the shape and let the plan author focus on content.

- **Memory-doc skeleton template.** Broader applicability of the same template family: every memory has frontmatter (name/description/type) + Why + How-to-apply structure. Skeleton would standardise memory authoring and ensure no fields drift over time.

- **Commit-message templates per category.** Patterns like `feat(<comp>): ... — amendment #N`, `chore(seals): ... — <comp> at <sha>`, `docs(plans): record amendment #N commit SHAs`, etc. are hand-crafted each time. A small template library + a `pos-amend commit-msg <category> <vars>` helper would mechanise the prose and reduce drift.

- **`pos-amend log-decisions <plan> <key>=<value>...`** (stretch). Mechanise §14 method-decision register's mostly-deterministic subsections — test counts, dependents-cleared list, file-touched manifests — while leaving D-build.x prose to the builder. Marginal value vs. cost; flag only.

- **Master plan §6.3 AC3 tightening.** `first-run-primary-persona-default-agent-wiring.md`'s parent AC has loose "additionalContext payload that names the loaded persona" wording; symmetric to the AC37.5 tightening done post-#33 but in the master plan. Marginal value vs. cost; opportunistic batch candidate.

- **`personas/primary/` at canonical root cleanup.** Apr 18 mtime, untracked, predates the persona-setup amendments. Decide: gitignore `personas/` at repo root, commit a working-state sentinel, or delete the stale directory. Currently noise in `git status`.

- **#20 empirical finding: parallel doc-edit + dev-discipline-build is safe.** `feedback_serialize_amendment_builds` may be over-broad — the rule applies specifically to sealed-component-amendment-build pairs racing on `pos-amend`, not generic git activity. Tighten the memory to clarify scope.

- **Stale `error_code` + `remediation` fields in completed `first-run.state`.** Cosmetic from the gen-2 timeout → gen-3 success transition; `_advance_state` doesn't clear them on completion. Flagged in #3 audit. Cosmetic only.

- **Phase-5 confirmation sentence "twelve components".** Actual install is 13 components (telegram-interface auto-discovered). Hardcoded string in `_confirmation_sentence()`. Cosmetic.

- **`/effort` confirmation message bug.** `/effort auto` says "Effort level set to max" but actual state is `xhigh` (which is correct behaviour). UI-only mismatch in the confirmation prose. File via `/feedback`.

- **Dynamic `/effort auto` (feature request).** Luke's intuition that "auto" should scale per task, not statically reset to model default. Not a Claude Code feature today; file as upstream feature request.

- **AC text precision sweep.** Opportunistic batch of post-seal AC tightenings (similar to AC37.5, AC40.1) — when an AC pins specific vocabulary that turns out to be method-not-objective, tighten the AC. Could batch across multiple sealed amendments in one doc-only sweep.

- **`TRACKER_DB_FILENAME` repeated across three consumers.** The constant `"objective_tracker.sqlite"` lives in `workspace_bootstrap.adapters.tracker_seed`, `primary_persona.tracker_context`, and now `pos_amend.tracker_registration` (post-#16). A fourth consumer would warrant extraction into a shared `pos_paths` (or similar) helper module so the convention is single-sourced. Surfaced by #16 build agent.

- **Pos-amend pokes tracker SQLite directly for `update_source_commits`.** Works against amendment #38's stable schema, but a future tracker amendment changing the `lifted_from` JSON shape would silently break `pos_amend.tracker_registration.update_source_commits` without an obvious test signal in pos-amend. Future safeguard: add a tracker public API like `tracker.rewrite_lifted_from_source_commit(objective_id, sha)` so pos-amend stops touching the SQLite directly. Worth raising when (a) a fourth tracker consumer arrives, OR (b) the next tracker amendment touches `lifted_from`'s shape. Surfaced by #16 build agent.

- **Dispatch-template + Heavy-B-phase-migration could compose** so the dispatch-template engine itself uses the persona-tracker context (per #40) to know which sub-agent shape applies. Stretch — surfaced as broader-applicability of the dispatch-template work; only valuable once both land. Surface for review post-initial-phase.

- **Asymmetric finding from integration test approach itself:** the "fresh-clone first-run with sandbox isolation + Monitors" pattern could become a reusable harness for any future integration test (post-amendment regression, cross-clone sanity, etc.). Currently a one-shot agent; could be extracted to a `tools/integration-test/` script. Worth considering after the current integration test concludes and we know the pattern actually worked.

- **Scaffold-runner observability gap.** `first_run_scaffold_runner.py` discards the `ScaffoldResult` returned by `run_first_run_scaffold` — the `tracker_seeded` / `tracker_seed_reason` / `tracker_classification` fields never reach the worker log. A `skipped_no_value_prop` outcome would be silent (exactly the silent-failure shape that misled the integration-test agent's Finding 2 hypothesis). One-line diagnostic emit on success path would prevent future investigations from having to re-derive seed outcome.

- **Integration-test methodology gap on SQLite file inspection.** Bare `stat()` on the main `.sqlite` file mid-WAL can mislead — the size doesn't reflect committed data until WAL checkpoints. Future integration-test fixtures should sample sibling `-wal`/`-shm` files AND open-then-close a `sqlite3` connection before size-checking. The 0-byte Finding 2 was caused by this methodology gap, not a real bug.

- **Pos-amend `--bare` mode use case.** `claude --bare --settings .claude/settings.json` could be useful for clean experiments / scripted scenarios where the full pos-v2 harness shouldn't load. Document the recipe somewhere if it becomes a recurring need.

- **Template engine: one-pass substitution authoring discipline.** The dispatch-template engine's `{{var}}` substitution doesn't recursively expand defaults — a default containing `{{OTHER_VAR}}` renders the literal placeholder. Caught early in #25 build (the dispatch template's `PRIME_OBJECTIVE_FRAMING` default contained `{{AC_PREFIX}}`). Worth documenting in the dispatch-template authoring guide alongside the future skills wrapping.

- **Template engine: package-data declaration for wheel form.** Templates root resolves via `__file__` parents — works for editable installs (the only mode pos-amend ships in today). If pos-amend ever lands in PyPI / wheel form, templates need `package-data` declaration in `pyproject.toml`. Not blocking; noted for the eventual packaging story.

- **`pos-amend new-plan <slug>` orchestration.** Plan-doc skeleton has 13 required vars — that's a lot to author by hand for every plan. A `pos-amend new-plan <slug>` orchestration that scaffolds the vars-file with empty defaults (or pre-fills `TITLE` / `AC_PREFIX` from CLI args) would be a high-leverage follow-up — bigger leverage than the D-3c skills wrapping. Surfaced by #25 build.

- **Template `description` frontmatter doubles as `list` one-liner.** The introspection-surface frontmatter the engine requires gives `pos-amend template list` its descriptions for free; useful pattern when memory-doc / commit-message families land.

- **System-design concern: shipped runtime vs dev-time machinery (LOAD-BEARING — see chat).** Owner ruled 2026-04-25 that pos-v2 is downloaded from GitHub by end users; their clone IS pos-v2 for them; no separate "canonical" exists for end users. Implications for the system, surfaced in chat: (1) `classify_workspace` in #39 uses `docs/rebuild/VALUE_PROPOSITION.md` presence as the "dev" marker — every GitHub-cloned end user has it, so end users get classified as "dev" wrongly; (2) host-global `~/.pos/` SQLite files (`orchestrator.sqlite`, `scope_of_work.sqlite`, post-#39 `objective_tracker.sqlite`) cross-workspace contaminate; (3) what ships in the GitHub-distributed form vs what's dev-time machinery (`pos-amend`, plan docs, manifest YAMLs, BASELINE conventions, SEAL_COMMITs, sealed-component conventions, dispatch-template, spec docs, component proposals + seal narratives) — all dev-only, probably shouldn't ship for end users. Awaits owner ruling on whether to scope a broader "shipped-vs-dev-time surface review" before further fixes.

- **Path-mismatch (#39 ↔ #40) fix direction.** Tracker DB write path (`tracker_seed.tracker_db_path_for(pos_root)`) vs read path (`primary_persona.tracker_context.tracker_db_path_for(workspace_root)`). Owner has leaned **B (#39 writes to workspace_root)** consistent with #28's workspace-locality and end-user-shipped principle. Fix held pending the broader shipped-vs-dev-time scoping ruling. Real latent bug — bites the moment #40's contributor is wired to live persona registration.

---

*New entries appended to bottom; review-and-graduate happens post-initial-phase.*
