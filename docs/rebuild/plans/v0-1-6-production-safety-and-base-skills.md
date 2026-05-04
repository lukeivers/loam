# v0.1.6 sub-plan — production-safety mode + base-skills additions + 2 bug fixes

**Status:** sub-plan-doc, plan-before-code. Authored 2026-05-04.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Parent plan:** `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` (§2 v0.1.6 row).
**Predecessors:**
- `f04e925` — v0.1.3 SKILL.md packages bundle (5 base SKILLs sealed).
- `5438860` — eric-final-delivery synthesis plan (parent).
- `972293b` — current canonical pos-v2 HEAD (BASELINE candidate).

**BASELINE (pre-build tip):** `972293b`.
**Status-file target:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-6-status-2026-05-04.md`.
**Quality bar:** WOW Eric. No partial features. All 6 smoke dimensions exercised.

---

## §1. Summary / TL;DR

v0.1.6 ships **two amendment cycles** (serialized per `feedback_serialize_amendment_builds`):

**Cycle 1 — production-safety + bug fixes** (multi-component fence):
- `framework/workspace-bootstrap/`: adds `safety_profile` field to `bootstrap.yaml`; pre-creates `<workspace>/.claude/skills/.gitkeep`; enrolls `plugins/loam-skills/` in default `contributions:` so the 5 base SKILLs are no longer dormant in fresh canonical workspaces.
- `framework/cost-governance/`: adds dry-run mode primitive + foreign-codebase budget envelope schema; minor recalibration of advisory ceilings (Eric-shape: production-stake mode tightens defaults).
- `plugins/dev-sdlc/`: dev-mode safety defaults (no production-stake escalation in dev).

**Cycle 2 — base-skills additions** (single-component fence):
- `plugins/loam-skills/`: 3 new SKILL.md packages — `translation-discipline`, `audit-block-on-telegram`, `owner-decision-summary`.

**The 8 SKILLs after Cycle 2** (5 existing + 3 new):
1. `memory-recall` (existing)
2. `scope-decompose` (existing)
3. `dispatch-with-gates` (existing)
4. `onboarding-conversation` (existing)
5. `session-handoff` (existing)
6. **`translation-discipline`** (NEW) — anti-pattern checklist (no commit SHAs / AC IDs / abbreviations / doc-section refs without summary) + before-send pass.
7. **`audit-block-on-telegram`** (NEW) — surface-when-meaningful audit-block on Telegram replies; thinking-block always walks the list.
8. **`owner-decision-summary`** (NEW) — recommendation-with-rationale shape; prevents doc-section-pointer regression.

**Decision P resolved (SOC-2 audit-trail floor):** RESOLVED YES per dispatcher autonomous resolution. `production-stake` profile non-tunably enables audit-trail-on; the other safety_profile values (`dev`, `research`) tune separately.

---

## §2. Placement decisions (per partition rule)

| Item | Placement | Rationale |
|---|---|---|
| `safety_profile` field on `bootstrap.yaml` | `framework/workspace-bootstrap/` | Workspace-bootstrap owns the manifest schema; safety_profile is workspace-level, not component-level. |
| `production-stake` profile defaults | `framework/workspace-bootstrap/` (the routing) + `framework/cost-governance/` (the cost-side defaults) | Profile is a meta-config that flips named defaults across components; the routing lives in workspace-bootstrap, the per-component defaults live where each component reads them. |
| Dev-mode safety defaults | `plugins/dev-sdlc/` | Dev-specific behavior per partition rule. |
| Cost-governance dry-run primitive | `framework/cost-governance/` | General primitive; harness-wide surface (all components can opt in). |
| Foreign-codebase budget envelope | `framework/cost-governance/` | Schema lives where the budget logic lives; usage by dev-sdlc extractor (v0.1.8) is consumer-side. |
| Bug fix: `plugins/loam-skills/` enrollment in default `bootstrap.yaml` | `framework/workspace-bootstrap/` | The bug is in `_BOOTSTRAP_YAML` template (loam-skills missing). |
| Bug fix: pre-create `<workspace>/.claude/skills/.gitkeep` | `framework/workspace-bootstrap/` | First-run scaffold owns the workspace-tree pre-creation. |
| 3 new SKILL.md packages | `plugins/loam-skills/skills/<name>/` | All three are harness-general (translation-discipline applies to all loam users; audit-block applies wherever Telegram is used; owner-decision-summary applies to any owner-relay). Per layered-skills research §1.2 — these are the harness-general candidates from the FIDRAFT 6, not the dev-specific ones. |

---

## §3. Halt-and-surface BEFORE build

### Surface #1 (no halt — recorded; safety_profile shape)

**Decision (autonomous):** `safety_profile` is a single string field on `bootstrap.yaml` at the top level (not nested), with three legal values: `production-stake`, `dev`, `research`. Default value when absent: `dev` (matches today's behavior — dev workspaces don't pay the production-stake tax). The field is read by workspace-bootstrap at manifest-load time and surfaced to other components via the existing host context surface.

### Surface #2 (no halt — recorded; production-stake non-tunable defaults)

**Decision (autonomous, per Decision P resolved YES):** `production-stake` profile, when active, sets the following non-tunable floors:

- `audit_trail: on` (every persona action logged with provenance traceable to a named decision; SOC-2 floor non-negotiable for Eric).
- `cost_governance.warning_fraction: 0.6` (tighter than the default 0.8 — more headroom for Eric's compliance posture).
- `safety_layer.always_ask` extends the framework floor with: `production-data-mutation`, `customer-record-edit` (additive — does not remove the existing floor).

These are **floors**, not absolute values: workspaces in production-stake mode CAN add to `always_ask` further; they CANNOT remove the named floor entries. The other profile values (`dev`, `research`) carry no floors beyond what's already in `safety/always_ask.yaml` framework defaults.

### Surface #3 (no halt — recorded; dry-run primitive shape)

**Decision (autonomous):** dry-run mode is a method on the cost-governance Controller surface — `dry_run_estimate(scope_id) -> EstimateResult`. The result carries: `estimated_money_cents`, `estimated_tokens`, `estimated_time_seconds`, `confidence_band` (HIGH / MEDIUM / LOW). The estimator is a thin extrapolator that consumes the rolling window's recent-actuals and projects forward; not a model-call. Live execution remains uninstrumented unless explicitly wired by the consumer. Foreign-codebase budget envelope is a separate `BudgetEnvelope` Pydantic model attached to the scope; carries hard-cap + soft-cap + overrun-action enum (warn / halt / continue).

### Surface #4 (no halt — recorded; new SKILLs are reference-content style)

**Decision (autonomous):** all 3 new SKILLs are reference-content (knowledge applied alongside conversation), matching the existing 5. None set `disable-model-invocation`. None declare `allowed-tools`. Frontmatter carries only `description` (matches the v0.1.3 minimal-surface convention).

### Surface #5 (no halt — recorded; .gitkeep pre-create only on fresh scaffold)

**Decision (autonomous):** the `.gitkeep` is pre-created during fresh-scaffold and partial-recovery paths only. It is NEVER overwritten if it exists. The directory `<workspace>/.claude/skills/` is created (mkdir -p) and a zero-byte `.gitkeep` is written. Anthropic's live-change-detection picks up new SKILL files in this directory immediately because the directory itself was created at scaffold time (no session restart required for subsequent additions, per the layered-skills research §1.4 finding).

### Surface #6 (no halt — recorded; loam-skills enrollment placement)

**Decision (autonomous):** `loam-skills` is a markdown-only plugin with NO `loam.bootstrap.contributions` entry-point (per its `pyproject.toml`), so it cannot be enrolled as a contribution in the same shape as the 13 framework adapters. Instead, the bug fix is two-fold:
1. The default `_BOOTSTRAP_YAML` template gets a `# Discoverable plugins (filesystem-walk; no contribution entry):` comment block listing `plugins/loam-skills/` and `plugins/dev-sdlc/`.
2. The first-run scaffold ensures `<workspace>/.claude/plugins/` (or equivalent Claude Code discovery root) is symlinked / referenced so plugin SKILLs are visible.

The simpler fix: `<workspace>/.claude/skills/.gitkeep` ensures the workspace-local discovery root exists, AND we document the plugin-discovery seam. Per Anthropic's published precedence (plugin > project), the 5 base SKILLs from `plugins/loam-skills/skills/` ARE discovered automatically when the plugin is on the Python path (which it is, post-`pip install -e .`). The "enrollment" issue from the research §1.3 is therefore primarily about the fresh `.claude/skills/` directory existing — not about adding loam-skills to `contributions:`. **Refined autonomous resolution:** the bug-fix items are (1) the `.gitkeep` pre-create, (2) a comment in the scaffolded `bootstrap.yaml` that explicitly names `plugins/loam-skills/` as a discoverable plugin (not as a contribution).

### Surface #7 (no halt — recorded; serialization between cycles)

**Decision (autonomous):** Cycle 1 (multi-component) seals before Cycle 2 (single-component) starts, per `feedback_serialize_amendment_builds`. Each cycle gets its own manifest, its own `loam amend apply`, its own seal commit. Total: 2 apply commits + 2 seal commits.

### Surface #8 (no halt — recorded; no out-of-fence dev-mode-manifest edit at v0.1.6)

**Decision (autonomous):** dev-mode-manifest changes (e.g., admitting `plugins/loam-skills/` to `dev_only`) is **explicitly deferred to v0.1.7** per parent-plan §2 v0.1.7 row. v0.1.6 does NOT touch `plugins/dev-sdlc/dev-mode-manifest.yaml`.

---

## §4. Spec-objective placement

**Binds to:**

- **AC.PO.1 + AC.PO.2** (prime objective per VALUE_PROPOSITION.md) — production-safety is a translation-burden reducer (the persona's job during Eric-pointed dispatches becomes much easier when production-stake floor is ambient); base-skills additions add to the harness toolkit.
- **Eric-final-delivery §2 v0.1.6** — defensive shield ships first; SOC-2 audit-trail floor (Decision P RESOLVED YES) baked in.
- **Layered-skills research §1.2** — the 3 new SKILLs are the harness-general candidates from the FIDRAFT 6 (translation-discipline, audit-block-on-telegram, owner-decision-summary; the other 3 — front-load-principle-walk, dispatch-brief-authoring, sealed-component-amendment-ship — are dev-specific and ship under `plugins/dev-sdlc/skills/` later, per Eric synthesis §2 v0.1.8).
- **Decision P resolved YES** — SOC-2 audit-trail floor non-tunable for production-stake.

**Ladders to:** AC.PSAFE.* + AC.SKILLS-BASE.* + AC.SKILLS-BUG.* → v0.1.6 → v0.1.7+ (every later release composes against these defenses + skill toolkit) → AC.PO.

---

## §5. Acceptance criteria

### AC.PSAFE.* family — production-safety mode

- **AC.PSAFE.1 — `safety_profile` field accepted at workspace-bootstrap.** Tests load a `bootstrap.yaml` carrying `safety_profile: production-stake` (or `dev` / `research`) and assert the manifest loader exposes the value on the parsed `Manifest`. Invalid values (anything other than the 3 legal strings) raise `MissingConfigError` (fail-closed per existing pattern).
- **AC.PSAFE.2 — default value when absent.** Tests load a `bootstrap.yaml` WITHOUT `safety_profile` and assert the parsed manifest carries `safety_profile = "dev"` (the default).
- **AC.PSAFE.3 — `production-stake` profile non-tunable floors.** Tests construct a workspace context with `safety_profile: production-stake` and assert: (a) `audit_trail: on` is observable; (b) `cost_governance.warning_fraction = 0.6` overrides any user-configured value > 0.6 (floor); (c) `always_ask` includes `production-data-mutation` and `customer-record-edit` regardless of user config (floor).
- **AC.PSAFE.4 — cost-governance dry-run primitive returns EstimateResult.** Tests call `Controller.dry_run_estimate(scope_id)` and assert the return carries the four named fields (`estimated_money_cents`, `estimated_tokens`, `estimated_time_seconds`, `confidence_band`) with the correct types.
- **AC.PSAFE.5 — foreign-codebase budget envelope schema present.** Tests construct a `BudgetEnvelope` Pydantic model with `hard_cap_money_cents`, `soft_cap_money_cents`, `overrun_action` (enum: `warn` | `halt` | `continue`); pydantic validation rejects malformed envelopes.
- **AC.PSAFE.6 — `production-stake` profile observable in canonical pos-v2 session.** Smoke: write a `bootstrap.yaml` with `safety_profile: production-stake` to canonical pos-v2's `~/.loam/bootstrap.yaml`; bootstrap; observe the floor values in the loaded host context. (Smoke-test, not unit; status-file-recorded.)

### AC.SKILLS-BASE.* family — 3 new SKILLs

- **AC.SKILLS-BASE.1 — `translation-discipline` SKILL.md authored, frontmatter valid, body covers anti-pattern checklist.** File at `plugins/loam-skills/skills/translation-discipline/SKILL.md` exists; YAML frontmatter parses; description ≤1536 chars; body has the standard 6-section shape (`## What this skill captures`, `## When to use`, `## How the persona applies it`, `## Graceful degradation`, `## Composition`, `## Out of scope`); body explicitly enumerates the anti-patterns (no commit SHAs / AC IDs / abbreviations / doc-section refs without summary) and names a before-send pass.
- **AC.SKILLS-BASE.2 — `audit-block-on-telegram` SKILL.md authored, surface-when-meaningful logic specified.** File at `plugins/loam-skills/skills/audit-block-on-telegram/SKILL.md` exists; same frontmatter/body shape; body specifies the surface-when-meaningful refinement: surface only when ✗ / decision / commit / explicitly asked; thinking-block always walks the list.
- **AC.SKILLS-BASE.3 — `owner-decision-summary` SKILL.md authored, body covers summary + named-decisions-with-recommendations format.** File at `plugins/loam-skills/skills/owner-decision-summary/SKILL.md` exists; same frontmatter/body shape; body specifies the recommendation-with-rationale format (summary first; named decisions with explicit recommendation each; never doc-section-pointers without summary).
- **AC.SKILLS-BASE.4 — All 3 new + 5 existing skills well-formed per AC.LSK.{1,2,3} test family.** The existing tests in `plugins/loam-skills/tests/test_AC_LSK_{1,2,3}_*.py` are extended (or `EXPECTED_SKILLS` constants updated) so all 8 packages are checked, not just the original 5. All AC.LSK assertions pass for all 8.
- **AC.SKILLS-BASE.5 — All 8 SKILLs auto-discoverable in canonical pos-v2.** Smoke: live `claude` session in canonical lists all 8 in `/` menu / SKILL discovery surface. (Status-file-recorded; tested via static walk over `plugins/loam-skills/skills/*/SKILL.md` returning 8 files at the AC test level; live `claude` smoke at the smoke layer.)

### AC.SKILLS-BUG.* family — 2 bug fixes

- **AC.SKILLS-BUG.1 — `plugins/loam-skills/` named in default `bootstrap.yaml` template.** Tests load the rendered `_BOOTSTRAP_YAML` constant and assert the file references `plugins/loam-skills/` in a discoverable-plugins comment block (matches Surface #6 refined resolution).
- **AC.SKILLS-BUG.2 — workspace-bootstrap pre-creates `<workspace>/.claude/skills/.gitkeep` at first-run.** Tests run `run_first_run_scaffold` against a tmpfs workspace; assert `<workspace>/.claude/skills/.gitkeep` exists and is zero bytes; idempotent (second run does not overwrite if already present).
- **AC.SKILLS-BUG.3 — Smoke: fresh canonical workspace → all 8 SKILLs visible without restart.** Status-file-recorded smoke (live `claude` session in a fresh workspace clone).

### AC.PSAFE.S — fence (single-cycle, multi-component for Cycle 1)

- Cycle 1 fence: `framework/workspace-bootstrap/`, `framework/cost-governance/`, `plugins/dev-sdlc/`, plus `docs/rebuild/plans/` (universal admission for sub-plan + manifest), plus `CLAUDE.md` if updated for the production-stake reference.
- Cycle 2 fence: `plugins/loam-skills/` only, plus `docs/rebuild/plans/` for cycle-2 manifest.

---

## §6. Build steps

### Cycle 1 (production-safety + bug fixes) — multi-component

1. **Plan-doc** lands (this file).
2. **Manifest** authored: `docs/rebuild/plans/v0-1-6-production-safety-and-base-skills.manifest.yaml` — multi-component fence on the 3 components named above.
3. **Source edits** (in order):
   - `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py` — add `safety_profile` field to `Manifest` dataclass; parse from YAML; default `"dev"`; validate against {`production-stake`, `dev`, `research`}.
   - `framework/workspace-bootstrap/src/loam/workspace_bootstrap/adapters/first_run_scaffold.py` — add `<workspace>/.claude/skills/.gitkeep` pre-create; update `_BOOTSTRAP_YAML` template with the discoverable-plugins comment block + a default `safety_profile: dev` line.
   - `framework/cost-governance/src/loam/cost_governance/controller.py` (or new `dry_run.py`) — add `dry_run_estimate(scope_id) -> EstimateResult` method.
   - `framework/cost-governance/src/loam/cost_governance/spec.py` (or new) — add `BudgetEnvelope` Pydantic model.
   - `framework/cost-governance/src/loam/cost_governance/config.py` — add production-stake floor logic (warning_fraction floor at 0.6 when profile=production-stake).
   - `plugins/dev-sdlc/` — add a docs entry naming dev-mode safety defaults (no production-stake escalation in dev mode); minimal touch.
4. **Tests** authored:
   - `framework/workspace-bootstrap/tests/test_AC_PSAFE_1_safety_profile_field.py`
   - `framework/workspace-bootstrap/tests/test_AC_PSAFE_2_default_dev.py`
   - `framework/workspace-bootstrap/tests/test_AC_PSAFE_3_production_stake_floors.py`
   - `framework/workspace-bootstrap/tests/test_AC_SKILLS_BUG_1_loam_skills_in_default_bootstrap.py`
   - `framework/workspace-bootstrap/tests/test_AC_SKILLS_BUG_2_skills_gitkeep_pre_created.py`
   - `framework/cost-governance/tests/test_AC_PSAFE_4_dry_run_estimate.py`
   - `framework/cost-governance/tests/test_AC_PSAFE_5_budget_envelope.py`
5. **Touched-tests run** (only the new tests + their existing-component tests under `framework/workspace-bootstrap/tests/` and `framework/cost-governance/tests/`).
6. **`loam amend apply`** — auto-commit lands.
7. **`loam amend seal`** — deterministic seal commit.
8. **Smoke (D1 cold-state):** fresh workspace → safety_profile defaults to `dev`; production-stake activation observable.

### Cycle 2 (3 new SKILLs) — single-component fence

1. **Manifest** authored: `docs/rebuild/plans/v0-1-6-production-safety-and-base-skills-cycle2.manifest.yaml` — single-component fence on `plugins/loam-skills/`.
2. **Source edits**:
   - `plugins/loam-skills/skills/translation-discipline/SKILL.md` (NEW)
   - `plugins/loam-skills/skills/audit-block-on-telegram/SKILL.md` (NEW)
   - `plugins/loam-skills/skills/owner-decision-summary/SKILL.md` (NEW)
3. **Test extension**: update `EXPECTED_SKILLS` lists in the 3 existing AC.LSK tests to include the 3 new packages (8 total). The tests are parametrized; adding to the constant gates the new files.
4. **Tests run** (all of `plugins/loam-skills/tests/`).
5. **`loam amend apply`** — auto-commit lands.
6. **`loam amend seal`** — deterministic seal commit.

### Smoke (REALISTIC CONDITION — all 6 dimensions per `plugins/dev-sdlc/docs/smoke-test-discipline.md`)

After both cycles seal:

- **D1 cold-state:** fresh workspace → production-safety profile + 8 SKILLs functional.
- **D2 steady-state:** profile remains active across 5 dispatches; no skill description-budget regression.
- **D3 restart:** profile preserved across pos-v2 process restart; SKILLs remain discoverable.
- **D4 reboot:** profile + SKILLs survive macOS reboot (or simulated equivalent — `launchctl bootout` + `bootstrap` cycle).
- **D5 cross-session:** profile + SKILLs visible after `/clear` (THE ship-test per STATE.md).
- **D6 telemetry-floor:** cost-governance per-dispatch budget log entries observable.

All 6 outcomes status-file-recorded.

---

## §7. Out of scope (deferred)

- **dev-mode-manifest edits** — defer to v0.1.7.
- **Auto-creation mechanism** — defer to v0.2.0.
- **PM-shape work** — defer to v0.1.7.
- **Heavy reverse-engineering / Rails extractor** — defer to v0.1.8.
- **12 dev-sdlc skill-ifications** — defer to v0.1.8 + v0.1.9.
- **Promotion rubric** — defer to v0.2.1.
- **Migration of existing flat-shape skills** (`framework/primary-persona/skills/memory-{search,archive}.md`, `plugins/dev-sdlc/skills/start-project.md`) to directory-per-skill — out of fence; v0.2+.
- **Complete re-entry of every persona-action through the audit-trail** — production-stake floor sets the policy; per-component instrumentation is consumer-side and not exhaustively wired here.
- **Ruby/Rails-aware extractor** — v0.1.8.
- **Subagent personas (5 named)** — v0.1.7.

---

## §8. Halt triggers (in-flight)

- WD drifts → halt + surface.
- More than 5 in-build decisions need Luke escalation → halt + describe.
- Any AC ships partial → halt + reframe.
- 6-dimension smoke fails on D5 cross-session → halt (THE ship-test).
- Any SKILL fails frontmatter validation → halt.
- Production-safety profile breaks an existing `AC.*` test in canonical → halt + RF the conflict.
- Cycle 1 seal fails → halt; do NOT start Cycle 2.

---

## §9. Bookkeeping

- `loam amend apply` on each cycle (NOT `git commit --amend`; create NEW corrective commits if a file is missed).
- Single semantic commit message per cycle.
- Backfill `docs/rebuild/plans/v0-1-x-roadmap.md` §8 method-decision register row for v0.1.6.
- Backfill `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2 v0.1.6 table with apply + seal SHAs.
- Update `docs/rebuild/STATE.md` v0.1.6 row.
- DO NOT push tags until Luke gates the release.
