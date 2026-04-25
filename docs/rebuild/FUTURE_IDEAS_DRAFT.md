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

---

*New entries appended to bottom; review-and-graduate happens post-initial-phase.*
