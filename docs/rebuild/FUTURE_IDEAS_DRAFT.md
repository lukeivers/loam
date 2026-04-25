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

- **`personas/primary/` at canonical root cleanup.** Apr 18 mtime, untracked, predates the persona-setup amendments. Decide: gitignore `personas/` at repo root, commit a working-state sentinel, or delete the stale directory. Currently noise in `git status`. **Cause identified by #42 build agent (2026-04-25):** some test in workspace-bootstrap's full-suite invokes `run_first_run_scaffold` without `workspace_root` set; the `_resolve_workspace_root` walk-up heuristic falls through to the canonical repo root, materialising `personas/primary/` there. Fix is workspace-bootstrap-test-side: tests should always pass an explicit `workspace_root` (tmp dir).

- **#20 empirical finding: parallel doc-edit + dev-discipline-build is safe.** `feedback_serialize_amendment_builds` may be over-broad — the rule applies specifically to sealed-component-amendment-build pairs racing on `pos-amend`, not generic git activity. Tighten the memory to clarify scope.

- **Stale `error_code` + `remediation` fields in completed `first-run.state`.** Cosmetic from the gen-2 timeout → gen-3 success transition; `_advance_state` doesn't clear them on completion. Flagged in #3 audit. Cosmetic only.

- **Phase-5 confirmation sentence "twelve components".** Actual install is 13 components (telegram-interface auto-discovered). Hardcoded string in `_confirmation_sentence()`. Cosmetic.

- **`/effort` confirmation message bug.** `/effort auto` says "Effort level set to max" but actual state is `xhigh` (which is correct behaviour). UI-only mismatch in the confirmation prose. File via `/feedback`.

- **Dynamic `/effort auto` (feature request).** Luke's intuition that "auto" should scale per task, not statically reset to model default. Not a Claude Code feature today; file as upstream feature request.

- **AC text precision sweep.** Opportunistic batch of post-seal AC tightenings (similar to AC37.5, AC40.1) — when an AC pins specific vocabulary that turns out to be method-not-objective, tighten the AC. Could batch across multiple sealed amendments in one doc-only sweep.

- **`TRACKER_DB_FILENAME` repeated across three consumers.** Graduated to FUTURE_IDEAS.md Idea 15 on 2026-04-25.

- **Pos-amend pokes tracker SQLite directly for `update_source_commits`.** Graduated to FUTURE_IDEAS.md Idea 16 on 2026-04-25.

- **Dispatch-template + Heavy-B-phase-migration could compose.** Graduated to FUTURE_IDEAS.md Idea 17 on 2026-04-25.

- **Asymmetric finding from integration test approach itself.** Graduated to FUTURE_IDEAS.md Idea 18 on 2026-04-25 (reusable integration-test harness extraction).

- **Scaffold-runner observability gap.** Graduated to FUTURE_IDEAS.md Idea 19 on 2026-04-25.

- **Integration-test methodology gap on SQLite file inspection.** Bare `stat()` on the main `.sqlite` file mid-WAL can mislead — the size doesn't reflect committed data until WAL checkpoints. Future integration-test fixtures should sample sibling `-wal`/`-shm` files AND open-then-close a `sqlite3` connection before size-checking. The 0-byte Finding 2 was caused by this methodology gap, not a real bug.

- **Pos-amend `--bare` mode use case.** `claude --bare --settings .claude/settings.json` could be useful for clean experiments / scripted scenarios where the full pos-v2 harness shouldn't load. Document the recipe somewhere if it becomes a recurring need.

- **Template engine: one-pass substitution authoring discipline.** The dispatch-template engine's `{{var}}` substitution doesn't recursively expand defaults — a default containing `{{OTHER_VAR}}` renders the literal placeholder. Caught early in #25 build (the dispatch template's `PRIME_OBJECTIVE_FRAMING` default contained `{{AC_PREFIX}}`). Worth documenting in the dispatch-template authoring guide alongside the future skills wrapping.

- **Template engine: package-data declaration for wheel form.** Templates root resolves via `__file__` parents — works for editable installs (the only mode pos-amend ships in today). If pos-amend ever lands in PyPI / wheel form, templates need `package-data` declaration in `pyproject.toml`. Not blocking; noted for the eventual packaging story.

- **`pos-amend new-plan <slug>` orchestration.** Plan-doc skeleton has 13 required vars — that's a lot to author by hand for every plan. A `pos-amend new-plan <slug>` orchestration that scaffolds the vars-file with empty defaults (or pre-fills `TITLE` / `AC_PREFIX` from CLI args) would be a high-leverage follow-up — bigger leverage than the D-3c skills wrapping. Surfaced by #25 build.

- **Template `description` frontmatter doubles as `list` one-liner.** The introspection-surface frontmatter the engine requires gives `pos-amend template list` its descriptions for free; useful pattern when memory-doc / commit-message families land.

- **System-design concern: shipped runtime vs dev-time machinery — TWO MODES.** Graduated to FUTURE_IDEAS.md Idea 13 on 2026-04-25 (umbrella for the broader two-modes-and-multi-workspace programme; the active part is in flight as A/B/E/F sub-plans, the deferred parts C/D/G sit under the idea's umbrella).

- **Path-mismatch (#39 ↔ #40) fix direction.** Graduated to FUTURE_IDEAS.md Idea 14 on 2026-04-25 (active fix folded into sub-plan E; comprehensive resolver-pattern direction stays deferred under Idea 13's multi-workspace umbrella).

- **G-activation-first dissolves D.** If sub-plan G (shared host-level memory-graphiti instance + workspace-keying via group_id) activates first at multi-workspace reactivation time, sub-plan D (per-workspace memory-graphiti port auto-allocation) becomes moot — one shared instance means no port-collision problem. Worth flagging at reactivation-time triage so we don't redundantly build D before G. Surfaced by doc-update agent 2026-04-25 (captured as G's D-G.4).

- **Lazy-projection trigger ↔ amendment #32 session-start gate composition.** When sub-plan #17 (heavy-b-phase-α/β/γ-migration) reactivates as the lazy-projection job triggered by dev_intent=yes, the cheapest available attach point is amendment #32's session-start gate — same lifecycle event, contract is already loaded at that point, one read + one dispatch decision. Method-level note for #17's future builder. Surfaced by doc-update agent 2026-04-25 (captured as #17 D-build.6).

- **C may activate as "audit + cleanup" rather than "migrate" when multi-workspace lands.** D-MASTER.2's owner-revised mirror of `~/.claude/` (global + workspace-override) collapsed C's migration burden; if any of the resolver pattern is partially in place by reactivation time, C's scope shifts from "migrate state files" to "audit existing layout for compliance + close gaps." Worth the triage at reactivation. Surfaced by doc-update agent 2026-04-25.

- **`pos-amend seal --plan-doc` crashes on relative path argument.** `Path.relative_to` raises ValueError when invoked from repo root with a relative `--plan-doc` arg. Worked around in #41 build by hand-authoring the SHA subsection. Fix: normalise to absolute path inside the subcommand before resolution, or document the absolute-path requirement clearly. Surfaced by #41 build agent.

- **Amendment-cycle workflow refinements** (3 sub-items, surfaced by #41 build):
  - **`pos-amend apply` should run BEFORE the amendment commit**, so BASELINE bump + sidecar advance + narrative append are bundled INTO the feature commit. The #41 build ran apply AFTER the amendment commit, causing a corrective "manifest-apply" commit + a doubled seal commit. Workflow doc should clarify the order; future plan-doc dispatch template should bake it into the build-step ordering.
  - **Pre-author plan §14 method-decision register heading** in plan docs before running `pos-amend seal --plan-doc`. The seal automation backfills the SHAs subsection inside an existing §14, but doesn't create the heading from scratch. Plan-doc skeleton template should include the §14 heading as a pre-authored section.
  - **One-file-per-AC test convention is the precedent** (matches AC35.x / AC40.x / AC.A.x), even when a plan §12 register suggests fewer test files. Plan-doc skeleton template should standardise this expectation.

- **`.scratch/` should be in root `.gitignore`.** `pos-amend`'s dirty-tree halt rejected `.scratch/` despite per-dir gitignore (the dir itself isn't in root `.gitignore`); the #42 build agent had to move it aside temporarily mid-build. Tiny one-line fix; removes friction for future amendments. Surfaced by #42 build agent. **ACTIONED 2026-04-25** in commit `f7cb781` (root `.gitignore` updated).

- **Cross-mode reference debt: `memory-system/launchd/README.md` references dev-only path.** F's AC.F3 reference scanner found `memory-system/launchd/README.md` (an always-loaded artefact) references `docs/rebuild/components/true-first-run/research.md` (a dev-only artefact). Editing the README would breach F's sealed-component fence (memory-system is sealed; F is dev-discipline). F captured as `KNOWN_CROSS_MODE_DEBT` allowlist so AC.F3 passes; allowlist must shrink to empty when fixed. **Two resolution paths:** (a) future memory-system amendment scrubs the cross-ref (preferred — minimal partition surface); (b) partition relaxes locked ruling 4 to carve out `memory-system/launchd/` from sealed-component coverage (worse — undermines partition's structural simplicity). Surfaced by #44 (sub-plan F build).

---

*New entries appended to bottom; review-and-graduate happens post-initial-phase.*
