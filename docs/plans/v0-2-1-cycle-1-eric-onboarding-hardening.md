# v0.2.1 Cycle 1 — Eric onboarding ritual hardening

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, plan-author dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** v0.2.1 master plan committed at `2ff444e` / patched at `2ba7fcd` / swept at `9355ef2` / FIDRAFT entry at `df447bc`. v0.2.0 SHIPPED rollup at `bbc93a7`.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/plans/v0-2-1-master-plan.md` §3 Cycle 1 + §4 Cycle 1 dispatch brief.

**Status file (to be authored by build agent):** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-1-cycle-1-status-2026-05-04.md`.

**Quality bar (Luke directive 2026-05-04, load-bearing):**

> "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."

v0.2.1 Cycle 1 IS the make-or-break first 5–10 minutes of Eric's install. Every named AC ships complete. One-question-at-a-time enforced via PM (no question-bombing). Auto-detection works on the canonical Ruby + JS/TS adapter fixtures from v0.1.8. Production-stake default highlighted on Rails. Install docs at feel-intentional level. Fresh-user fixture exercises full path. **No partial features.**

---

## §1 — Outcome shape (the "why")

v0.2.1 Cycle 1 ships the **install-time onboarding ritual** that polishes the first 5–10 minutes when a fresh user runs `loam init`. The ritual auto-detects project language, sequences six install-time questions one-at-a-time through the existing PM batch API (composing on v0.1.7 Cycle 4 `122a7c8`), bootstraps the production-stake profile / language adapter / channel based on responses, and emits a SOC-2-floor-honoring audit-log per Decision P. Cycle 1 also wires in a survey-as-default-source mechanism (AC.ONBOARD.15): if Eric (or any pre-installed user) has run the async onboarding survey (artefact at `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-onboarding-prompt-2026-05-05.md` per master plan §6.3) and dropped the resulting markdown file at the conventional path, the install-time flow becomes a confirm-or-adjust pass over pre-filled defaults rather than a fresh re-ask.

**Fence reality.** `framework/loam-init/` already exists (FBE.1; `loam init <path> --from <canonical>` clones canonical + scaffolds). Cycle 1 does NOT touch loam-init's argparse surface — it adds a post-bootstrap onboarding-ritual hook that the loam-init `_cmd_init` invokes after a successful `bootstrap_new_workspace`. The ritual itself lives under `framework/workspace-bootstrap/` per master plan §3 Cycle 1 fence. `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py` already carries `safety_profile` (v0.1.6) + `enable_auto_skill_capture` (v0.2.0 Cycle 2) — the precedent for adding new boolean / enum fields is verified-working.

**Cycle 1's release-note promise:** `loam init <path>` followed by entering the new workspace and re-invoking `loam onboard` (or auto-trigger on first session) walks Eric through six questions one-at-a-time (language confirmation / channel preference / safety profile / extractor opt-in / continuous-watch opt-in / auto-skill-capture opt-in), writes the resulting config to `bootstrap.yaml`, fires the chosen activations (channel setup via `framework/telegram-interface/`'s existing `SetupWalkthrough`, extractor via v0.1.8 adapters, watch via v0.2.0 Cycle 1, auto-skill-capture via v0.2.0 Cycle 2), emits an audit-log per question + activation, and ends with a single-next-action summary. Under the survey-file path, the ritual reads `~/loam-onboarding-survey.md` (or `$LOAM_ONBOARDING_SURVEY` override), parses the H2-headed Q+A pairs, pre-fills defaults, and the user confirms-or-adjusts each — still one-at-a-time per Decision Q.

**Discipline-shaped gating per `LOAM_ONBOARDING_SKIP=1`.** CI / smoke fixtures pass `LOAM_ONBOARDING_SKIP=1` to bypass the ritual entirely (ritual returns immediately with no audit-log entries; defaults left at workspace-bootstrap defaults). This is the same fail-closed flag pattern used by the existing `LOAM_*_SKIP` envs.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

The ritual composes on existing primitives:

- **`framework/loam-init/`'s `_cmd_init`.** Cycle 1 adds a post-bootstrap callout (after `bootstrap_new_workspace` returns success); no argparse-surface edit.
- **`framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py`'s `Manifest` dataclass + `load_manifest` validation pattern.** v0.1.6 `safety_profile` + v0.2.0 `enable_auto_skill_capture` are the verified precedents for new manifest fields. New onboarding-config fields (channel preference, language, extractor/watch/skill-capture opt-ins) follow the same shape.
- **`framework/per-project-pm/`'s `PMRuntime.enqueue_decision` + `surface_next_questions_batch(n=1)` + `record_response`.** The six install-time questions enqueue through this exact API one-at-a-time per Decision Q. Zero PM-side edits.
- **`framework/telegram-interface/`'s `SetupWalkthrough` + `should_offer`.** When the user picks Telegram in Q2, the ritual delegates to the existing setup-walkthrough flow.
- **`plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/`'s `ruby` + `jsts` adapter modules.** Auto-detection uses these adapters' presence / file-detection signals (Gemfile, package.json, tsconfig.json) for language identification.
- **`plugins/dev-sdlc/odd-extractor/`'s extraction entry-points.** When the user opts-in on Q4, the ritual fires the existing extraction CLI (no re-implementation).
- **v0.2.0 Cycle 1 `loam odd-extract <repo> --incremental` + Cycle 2 auto-skill-capture.** Q5 + Q6 toggle these opt-ins; the existing capabilities provide the activation surface.
- **Anthropic's filesystem-discovery for skill auto-load + the `Read` tool for survey parsing.** The survey-file parser reads markdown via standard file IO; H2-section split is plain-text parsing (no Claude API call).

The required research question — **"What Claude capability does this lean on or extend?"** — answer: every load-bearing primitive composes on top of an existing v0.1.6 → v0.2.0 surface. The ritual is the orchestration layer that wires these together for the first-5-minutes use case.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden drops dramatically. Eric's natural-language intent ("install loam, get sensible defaults, don't make me read 200 pages of docs") translates to AI-effective execution ("six questions, one-at-a-time, auto-detect what we can, surface only what needs decisions"). The persona doesn't have to ask Eric how Rails-vs-JS-vs-mixed should be detected, what audit-log location to use, or whether to enable continuous-watch — those are pinned by the ritual. Pass.
- **Harness test:** every loam-driven workspace (Eric's Node/TS/Playwright app, Luke's loam-of-loam, future writers / lawyers / researchers) gets the same onboarding shape from `loam init`. The ritual is a reusable harness primitive that any persona inherits. Pass.

Both pass.

### Lens 3 — ODD authoring

Outcome above + named ACs (§3) + halt triggers (§5) + acceptance smoke (§4 smoke dimensions). Method (Q-text exact wording / detection-file precedence / survey-file path canonical choice / parse-tolerance heuristic / fixture layout) stays the builder's call within constraints (six questions; one-at-a-time; PM batch API; survey-file optional with env-var override; production-stake default-highlight on Rails; SOC-2 audit-log per Decision P).

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH** for shape: master plan §3 Cycle 1 names all 14 ACs; v0.1.6 `safety_profile` + v0.2.0 manifest-flag patterns are the verified shape for new fields; PM batch API is verified-working. Tight scope: extension to `framework/workspace-bootstrap/`, additive manifest fields, post-bootstrap hook on `framework/loam-init/`, AC-shaped tests.

Outcome confidence is **MEDIUM** for the language-detection heuristic. Master plan §3 Cycle 1 names "depth-bounded tree walk + Gemfile / package.json / config detection." This plan-doc commits to: (1) **primary signals** = `Gemfile` (→ Rails/Ruby), `package.json` + `tsconfig.json` (→ JS/TS), `package.json` without tsconfig (→ JS); (2) **Rails specialisation** = if `Gemfile` present AND `config/application.rb` exists → Rails; (3) **mixed detection** = if both Gemfile and package.json present at root → present "mixed (primary?)" with Q1 asking for primary pick; (4) **unknown fallback** = neither file present → ask language free-form. Polyglot beyond simple primary-pick deferred to v0.2.x (master plan §7.2).

Outcome confidence is **MEDIUM-LOW** for the survey-file parse heuristic. AC.ONBOARD.15 introduces a tolerant parser. This plan-doc commits to: (1) **strict-parse path** = H2 headings keyed by question-number (`## 1. Stack versions` etc.) → body text → match against expected-question slug; on success, pre-fill default. (2) **fuzzy-match path** = if heading text doesn't include question-number, match by keyword overlap (e.g., "Communication channel" → channel question). (3) **fallback** = if any question is ambiguous (no heading match, body too short, multiple-choice answer doesn't match expected options), fall back to ask the question fresh (don't block, don't error). The "never block on parse failure" rule is structural — survey-as-default is best-effort.

Outcome confidence is **HIGH** for the PM batch API one-at-a-time enforcement. v0.1.7 Cycle 4 + Decision Q + AC.QSURF.1 verified.

### Lens 5 — Swarming

Single-component fence under `framework/workspace-bootstrap/` (PRIMARY) + tertiary additive hook on `framework/loam-init/`. Within the cycle, decomposition options:

- (a) one module per concern (`onboarding.py` for orchestrator + `language_detection.py` for detector + `survey_parser.py` for AC.ONBOARD.15 + `audit_log.py` for SOC-2 floor + `activations.py` for opt-in dispatch). Each with its own AC test.
- (b) collapse into a single `onboarding.py` orchestrator that imports inline helpers — denser but loses the named-feature surfaces.

The builder picks **(a)** — per-concern decomposition matches the master plan's named-mechanism naming (auto-detect / question-sequencing / survey-as-default-source / audit-log / activation-dispatch) and gives the tightest AC-per-file mapping. `max_planner_depth: 1` (no sub-planners; per-concern files are the right granularity). No further decomposition adds value.

---

## §3 — AC enumeration — `AC.ONBOARD.*` (locked, 15 ACs)

Each AC has at least one explicit pytest. ODD §2.5 — every line of code, every branch, every test maps to a named AC. AC.ONBOARD.1 → AC.ONBOARD.14 inherited verbatim from master plan §3 Cycle 1; AC.ONBOARD.15 is new per Luke 2026-05-05 ruling.

- **AC.ONBOARD.1 — `loam onboard` triggers ritual on fresh workspace; `LOAM_ONBOARDING_SKIP=1` env-var disables for CI.**
  - Surface: `loam onboard` subcommand (registered via `loam.cli.subcommands` entry-point group, mirroring loam-init's M6a contract). Optional invocation; idempotent (re-run on already-onboarded workspace re-uses prior config + offers per-question re-ask).
  - Auto-trigger: `loam init` post-bootstrap callout invokes onboarding when interactive (TTY detected) AND `LOAM_ONBOARDING_SKIP` unset.
  - `LOAM_ONBOARDING_SKIP=1` short-circuits the ritual; defaults remain at workspace-bootstrap defaults; no audit-log entries written.
  - Fence component: `framework/workspace-bootstrap/`.
  - Test: `test_AC_ONBOARD_1_trigger_and_skip.py` — argparse-surface registration; SKIP=1 returns immediately; default invocation enters question loop.

- **AC.ONBOARD.2 — Project-language auto-detection.**
  - `detect_language(workspace_root: Path) -> LanguageDetection` walks `workspace_root` depth-bounded (max depth 3) and inspects: `Gemfile`, `Gemfile.lock`, `config/application.rb`, `package.json`, `tsconfig.json`, `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`.
  - Returns `LanguageDetection(primary: Literal["rails", "ruby", "ts", "js", "mixed", "unknown"], signals: list[str])`.
  - **Q1 shape:** on `rails` / `ruby` / `ts` / `js` → "I detected this is <X>. Continue? Y/N." On `mixed` → "I detected both Ruby and JS/TS. Which is primary? (1) Ruby (2) JS/TS (3) other." On `unknown` → "I couldn't auto-detect. What language is this? (free-form)".
  - Fence component: `framework/workspace-bootstrap/`.
  - Test: `test_AC_ONBOARD_2_language_detection.py` — fixtures covering Rails / Ruby-no-rails / JS / TS / mixed / unknown trees; assert correct primary + signals; assert depth-bound respected.

- **AC.ONBOARD.3 — Question sequencing via PM batch API in single-question form per Decision Q.**
  - Onboarding runtime calls `PMRuntime.enqueue_decision(question_text, provenance=f"onboarding:Q{n}:{slug}")` once per question; calls `surface_next_questions_batch(n=1)` to render exactly one question; awaits response via `record_response`.
  - PM blocks on user response before the next `enqueue_decision` fires. No bundled-question shape.
  - Fence component: `framework/workspace-bootstrap/` (consumer of `framework/per-project-pm/` — read-only).
  - Test: `test_AC_ONBOARD_3_pm_sequencing.py` — synthetic PM mock; assert `surface_next_questions_batch` called with `n=1`; assert one enqueue per question; assert N questions = N record_response calls.

- **AC.ONBOARD.4 — Q2: channel preference (Telegram / CLI / Skip-for-now).**
  - Question text: "Where do you want async pings when work completes? (1) Telegram (2) CLI-only (3) Skip for now."
  - On (1) → invoke `framework/telegram-interface/`'s `SetupWalkthrough.offer()` flow inline; on completion (or decline / defer), record outcome.
  - On (2) → set `channel_preference: cli` in bootstrap.yaml; no further setup.
  - On (3) → set `channel_preference: deferred`; record audit-log; ritual proceeds.
  - ONE channel question — NOT a Telegram + Slack + email tree (master plan §3 Cycle 1).
  - Fence component: `framework/workspace-bootstrap/` (consumer of `framework/telegram-interface/` — read-only on its public surface).
  - Test: `test_AC_ONBOARD_4_channel_preference.py` — three branches; assert manifest field set correctly; assert SetupWalkthrough invoked on (1); assert no walkthrough on (2)/(3).

- **AC.ONBOARD.5 — Q3: safety profile (production-stake / dev / research).**
  - Question text: "Safety profile? (1) production-stake (2) dev (3) research."
  - **Default-highlight production-stake when language=rails** (per master plan §9 method-decision register). Question text becomes: "Safety profile? (1) production-stake [recommended for Rails apps] (2) dev (3) research."
  - On answer → set `safety_profile` field on bootstrap.yaml using existing v0.1.6 mechanism (no manifest schema change; `safety_profile` already validated).
  - **Production-stake default-flip semantics (per master plan §3 Cycle 1):** when production-stake selected, downstream defaults flip per AC.ONBOARD.10 (extractor dry-run-default; PR-gate halt-on-push; auto-skill-capture default-false; ratification-required-for-PLAUSIBLE→VERIFIED). Cycle 1 records the profile selection; the actual default-flip behavior already exists in v0.1.6 / v0.1.9 / v0.2.0 honour-flows — Cycle 1 verifies they fire.
  - Fence component: `framework/workspace-bootstrap/`.
  - Test: `test_AC_ONBOARD_5_safety_profile.py` — three branches; rails-language → production-stake highlighted; ruby/ts/js without rails → no highlight; manifest `safety_profile` written correctly.

- **AC.ONBOARD.6 — Q4: extractor opt-in (Y now / Defer / Never).**
  - Question text: "Run the ODD extractor against this codebase now? (1) Yes — fire now (2) Defer — I'll run `loam odd-extract` later (3) Never — disable extractor for this workspace."
  - On (1) → fires `loam odd-extract <workspace_root>` scoped to the detected adapter (Ruby or JS/TS per AC.ONBOARD.2).
  - On (2) → no-op; sets `extractor_opt_in: deferred`.
  - On (3) → sets `extractor_opt_in: never`; persisted as workspace-bootstrap manifest field.
  - Fence component: `framework/workspace-bootstrap/` (consumer of `plugins/dev-sdlc/odd-extractor/` CLI — read-only invocation).
  - Test: `test_AC_ONBOARD_6_extractor_opt_in.py` — three branches; on (1) assert subprocess invocation with correct args; assert manifest field writes.

- **AC.ONBOARD.7 — Q5: continuous-watch opt-in (Y / Defer-default / N).**
  - Question text: "Enable continuous codebase-watch (auto re-extract when commits land)? (1) Yes (2) Defer (3) No."
  - **Defer is the default for fresh-user low-context** per master plan §7.1 mitigation.
  - On (1) → set `watch_opt_in: yes`; emit a one-line note pointing at the v0.2.0 Cycle 1 README scheduling section.
  - On (2)/(3) → set `watch_opt_in: deferred` / `watch_opt_in: no`.
  - Fence component: `framework/workspace-bootstrap/`.
  - Test: `test_AC_ONBOARD_7_watch_opt_in.py` — three branches; default-highlight (2); manifest field writes.

- **AC.ONBOARD.8 — Q6: auto-skill-capture opt-in (Y / N-default).**
  - Question text: "Enable auto-skill-capture (persona drafts SKILL.md when patterns repeat; you ratify each)? (1) Yes (2) No (default)."
  - **N is the default** per layered-skills §3.6 Decision E (universal-tier; opt-in).
  - On answer → set `enable_auto_skill_capture` on bootstrap.yaml (field already exists per v0.2.0 Cycle 2; Cycle 1 just writes it).
  - Fence component: `framework/workspace-bootstrap/`.
  - Test: `test_AC_ONBOARD_8_auto_skill_capture_opt_in.py` — two branches; default-highlight N; manifest field writes.

- **AC.ONBOARD.9 — Ritual completion summary.**
  - On final question response, render summary: capabilities-active list (channel + safety profile + extractor + watch + auto-skill-capture, each with their Q-derived state), single-next-action ("Run `loam odd-extract <repo>`" / "Open a Telegram chat with @<bot>" / etc. — one specific actionable sentence per the channel/profile state), audit-log location (`<workspace>/.loam/audit-log/onboarding-<date>.yaml`).
  - Output is plain-text to stdout (TTY-friendly); also written to `<workspace>/.loam/onboarding-summary.md`.
  - Fence component: `framework/workspace-bootstrap/`.
  - Test: `test_AC_ONBOARD_9_completion_summary.py` — assert summary contains all 5 capability states + 1 next-action + audit-log path; summary file written.

- **AC.ONBOARD.10 — Production-stake defaults flip on AC.ONBOARD.5 selection.**
  - When `safety_profile=production-stake` selected during ritual, downstream defaults verified active:
    - Extractor dry-run default per v0.1.6 honour-flow.
    - PR-gate halt-on-push per v0.1.9 Cycle 1 honour-flow.
    - Auto-skill-capture forced to `false` regardless of Q6 (production-stake gates auto-write per `feedback_no_amend_in_agent_dispatches`-style discipline).
    - Ratification-required-for-PLAUSIBLE→VERIFIED per Decision I (already in v0.1.8 ratify-flow).
  - Composes with v0.1.6 + Decision P SOC-2 floor; Cycle 1 verifies the composition end-to-end.
  - Fence component: `framework/workspace-bootstrap/` (verification surface only; the honour-flows live in their respective components).
  - Test: `test_AC_ONBOARD_10_production_stake_default_flip.py` — invoke ritual with synthetic Rails fixture + Q3=production-stake + Q6=Y; assert final manifest has `enable_auto_skill_capture: false` (forced) + production-stake; assert audit-log records the flip.

- **AC.ONBOARD.11 — Audit-trail floor honored per Decision P.**
  - Every Q + A + activated capability emits one entry in `<workspace>/.loam/audit-log/onboarding-<YYYY-MM-DD>.yaml`.
  - Schema (mirrors odd-extractor's audit-log shape from v0.2.0 Cycle 1):
    ```yaml
    schema_version: 1
    event_kind: <onboarding_question_asked | onboarding_response_recorded |
                  onboarding_capability_activated | onboarding_default_flip |
                  onboarding_skipped | onboarding_completed>
    timestamp: <iso8601-tz>
    notes: " key1=val1 key2=val2"
    artefact_path: <str | null>
    ```
  - Event kinds at minimum: `onboarding_question_asked` (one per question), `onboarding_response_recorded` (one per response), `onboarding_capability_activated` (one per Y-opt-in that fires), `onboarding_default_flip` (when production-stake forces auto-skill-capture off), `onboarding_completed` (terminal entry with completion summary).
  - Fence component: `framework/workspace-bootstrap/`.
  - Test: `test_AC_ONBOARD_11_audit_log.py` — full-ritual run; assert all event_kinds present; YAML parses; schema_version + timestamp + notes populated.

- **AC.ONBOARD.12 — Fresh-user smoke fixture.**
  - Fixture at `framework/workspace-bootstrap/tests/fixtures/fresh-user-onboarding/` containing:
    - `synthetic-rails/` — minimal Rails-shaped tree (Gemfile + config/application.rb + app/controllers/).
    - `synthetic-jsts/` — minimal Node/TS-shaped tree (package.json + tsconfig.json + src/).
    - `synthetic-mixed/` — both root-level Gemfile + package.json.
    - `synthetic-unknown/` — empty repo with only `.git/`.
  - Test exercises full ritual end-to-end against each fixture with a synthetic PM-mock that auto-answers each question deterministically.
  - Fence component: `framework/workspace-bootstrap/`.
  - Test: `test_AC_ONBOARD_12_fresh_user_smoke.py` — four sub-tests (one per fixture); assert ritual completes; assert audit-log + summary files present; assert manifest has expected fields.

- **AC.ONBOARD.13 — Install docs updated at quality-bar feel-intentional level.**
  - Update `docs/getting-started.md` with: install-from-source pointer (already exists at `docs/install-from-source.md`); first-run walkthrough section showing the six-question ritual; channel selection walkthrough; production-stake explanation; SOC-2 audit-trail location; troubleshooting section.
  - **NEW file:** `docs/dev-mode-getting-started.md` — currently does NOT exist (pre-flight-confirmed; see §6 Halt #1). Cycle 1 authors this file at quality-bar-feel-intentional level: dev-mode prerequisites; how to enable dev-mode; what additional CLAUDE.md fragment auto-loads; v0.1.0+ dev-mode walkthrough.
  - Fence component: `docs/` (universal-paths admission per `docs/plans/` precedent).
  - Test: `test_AC_ONBOARD_13_install_docs.py` — both files exist; required headings present (substring match); minimum length thresholds (≥150 lines getting-started; ≥80 lines dev-mode); broken-link check (markdown links to existing files).

- **AC.ONBOARD.14 — Component-level tests + integration test.**
  - One test file per AC (AC.ONBOARD.1 → .15) under `framework/workspace-bootstrap/tests/`.
  - Plus integration test: `test_onboarding_integration.py` — full ritual end-to-end on synthetic-rails fixture; asserts every AC's exit-state simultaneously (manifest fields + audit-log + summary file + activation side-effects).
  - All tests must pass before seal.
  - Fence component: `framework/workspace-bootstrap/`.
  - Test: meta-test that validates the test-file roster (15 per-AC files + 1 integration file).

- **AC.ONBOARD.15 — Survey-as-default-source (NEW per Luke 2026-05-05 ruling).**
  - **Survey-file conventional path:** `~/loam-onboarding-survey.md` (default). Override via `$LOAM_ONBOARDING_SURVEY` environment variable (absolute path).
  - **Format:** the markdown shape produced by `/Users/lukeivers/pos3/workspace/.scratch/claude-output/eric-onboarding-prompt-2026-05-05.md` — H2 headings as questions; body text as answers; question-numbering optional.
  - **Parse semantics:**
    - On ritual start, check if survey-file exists at conventional path OR env-var path. If absent → falls back to default-by-language heuristic per AC.ONBOARD.5 + .6 + .10 logic; ritual proceeds with no defaults pre-filled.
    - If present → parse H2 sections; for each known question slug (channel / safety-profile / extractor / watch / auto-skill-capture / language), match by question-number prefix OR keyword overlap on heading text.
    - For matched questions: pre-fill the default; question text changes to confirm-or-adjust shape ("From your survey: <pre-filled>. Confirm? (1) Yes (2) Adjust to: <free-form>").
    - For unmatched / ambiguous questions: fall back to ask the question fresh.
    - **Never block on parse failure.** Best-effort. Any unparseable section → fall back to fresh-ask for that question.
  - **Question count stays at 6 install-time.** Survey may pre-fill all 6; user still confirms each one-at-a-time per Decision Q. Survey-as-default reduces friction (typing) but preserves explicit confirmation.
  - **Lightweight code budget:** parse + prefill logic ≤ 30 lines of new code per the brief constraint.
  - Fence component: `framework/workspace-bootstrap/` (new `survey_parser.py` module).
  - Test: `test_AC_ONBOARD_15_survey_as_default_source.py` — fixtures: well-formed-survey (all 6 prefilled); partial-survey (only 3 questions matched); malformed-survey (heading shapes broken); env-var-override (custom path honored); no-survey (existing default path empty → falls through). Assert pre-fill behavior per fixture; assert no exceptions raised on malformed input.

---

## §4 — Component & file layout

**PRIMARY scope:** `framework/workspace-bootstrap/` (the existing component's sealed fence; new modules + tests + manifest-field extensions land under it).

**TERTIARY admission:** `docs/` (universal-paths admission for `docs/getting-started.md` extension + `docs/dev-mode-getting-started.md` new authoring) + `framework/loam-init/` (additive post-bootstrap callout — minimal).

### Existing paths (extend in-place; sealed-content unchanged)

- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py` — extend `Manifest` dataclass with new fields (`channel_preference`, `extractor_opt_in`, `watch_opt_in`, `language_primary`, `onboarding_completed_at`); extend `load_manifest` validation (additive — fail-closed on invalid types). Existing `safety_profile` + `enable_auto_skill_capture` unchanged.
- `framework/workspace-bootstrap/src/loam/workspace_bootstrap/__init__.py` — additive exports of new module entry-points.
- `framework/loam-init/src/loam/loam_init/cli.py` — additive: post-`bootstrap_new_workspace` success branch invokes onboarding ritual when interactive (TTY) AND `LOAM_ONBOARDING_SKIP` unset. Lazy-import to honor the existing import-isolation pattern.

### New paths (this cycle)

Source modules (under `framework/workspace-bootstrap/src/loam/workspace_bootstrap/`):

- `onboarding.py` — orchestrator entry-point; `run_onboarding(workspace_root, *, pm_runtime, language_detection, survey_path) -> OnboardingResult`. Hosts the question-loop.
- `language_detection.py` — `detect_language(workspace_root) -> LanguageDetection` per AC.ONBOARD.2.
- `survey_parser.py` — `parse_survey_file(path) -> SurveyDefaults | None` per AC.ONBOARD.15.
- `onboarding_audit.py` — `emit_audit_entry(workspace_root, *, event_kind, notes, artefact_path)` per AC.ONBOARD.11. Mirrors odd-extractor's `observability.py` shape; component-local `<workspace>/.loam/audit-log/onboarding-<date>.yaml`.
- `onboarding_activations.py` — `activate_extractor(workspace_root, language)`, `activate_channel_telegram(workspace_root, pm_runtime)` (delegates to `framework/telegram-interface/`), `activate_watch_pointer(workspace_root)` (writes a one-line note; no daemon spawn at MVP).
- `onboarding_cli.py` — `loam onboard` subcommand builder (mirrors loam-init's M6a contract).

Tests (under `framework/workspace-bootstrap/tests/`):

- `test_AC_ONBOARD_1_trigger_and_skip.py`
- `test_AC_ONBOARD_2_language_detection.py`
- `test_AC_ONBOARD_3_pm_sequencing.py`
- `test_AC_ONBOARD_4_channel_preference.py`
- `test_AC_ONBOARD_5_safety_profile.py`
- `test_AC_ONBOARD_6_extractor_opt_in.py`
- `test_AC_ONBOARD_7_watch_opt_in.py`
- `test_AC_ONBOARD_8_auto_skill_capture_opt_in.py`
- `test_AC_ONBOARD_9_completion_summary.py`
- `test_AC_ONBOARD_10_production_stake_default_flip.py`
- `test_AC_ONBOARD_11_audit_log.py`
- `test_AC_ONBOARD_12_fresh_user_smoke.py`
- `test_AC_ONBOARD_13_install_docs.py`
- `test_AC_ONBOARD_14_test_surface.py` (meta-test on roster)
- `test_AC_ONBOARD_15_survey_as_default_source.py`
- `test_onboarding_integration.py`

Fixtures (under `framework/workspace-bootstrap/tests/fixtures/fresh-user-onboarding/`):

- `synthetic-rails/` — Gemfile + config/application.rb + app/controllers/users_controller.rb (3 files minimum).
- `synthetic-jsts/` — package.json + tsconfig.json + src/index.ts (3 files minimum).
- `synthetic-mixed/` — both Gemfile + package.json at root.
- `synthetic-unknown/` — empty `.git/` only.
- `survey-files/well-formed.md` — all 6 questions prefilled.
- `survey-files/partial.md` — 3 of 6 questions present.
- `survey-files/malformed.md` — broken H2 shapes.

Documentation:

- `docs/getting-started.md` — extend with onboarding-walkthrough section (additive; ~50–80 line addition).
- `docs/dev-mode-getting-started.md` — NEW file; minimum 80 lines; covers dev-mode enable + dev-CLAUDE.md fragment + walkthrough.

### Smoke dimensions (per master plan §3 Cycle 1)

- **D1 (cold-state)** ✓ — ritual fires on fresh workspace; 6 questions sequenced; manifest + audit-log + summary present post-ritual. Verified by `test_onboarding_integration.py` + per-AC tests.
- **D2 (steady-state)** ✓ — re-run ritual on already-onboarded workspace is idempotent (re-reads existing manifest fields; offers per-question re-ask; no double-write on no-change). Verified by integration test re-invocation.
- **D3 (restart)** ✓ — mid-onboarding `kill -TERM` → restart re-uses partial state from audit-log (the `onboarding_question_asked` entries serve as resume points); user sees "resuming at Q<N>" prompt. Verified by `test_AC_ONBOARD_11_audit_log.py` + a dedicated subprocess-killed test variant.
- **D5 (cross-session)** ✓ — post-state (manifest + audit-log + summary) survives `/clear`. Files persist; next session reads manifest. Verified by manifest-roundtrip test.
- **D6 (telemetry-floor)** ✓ — per AC.ONBOARD.11. Verified by `test_AC_ONBOARD_11_audit_log.py`.
- **D4 (reboot)** inherited from filesystem persistence; n/a structurally for ritual itself (one-shot CLI).

---

## §5 — Build dispatch brief (READY FOR DISPATCH after this plan-doc seals)

```
# v0.2.1 Cycle 1 BUILD dispatch — Eric onboarding ritual hardening

Working directory: `/Users/lukeivers/ivers-corp-pos-v2/`. NOT pos3.

Authority: build the 15 AC.ONBOARD.* family per sub-plan-doc §3. Single-component fence on framework/workspace-bootstrap/. Tertiary admissions: docs/ + framework/loam-init/cli.py (additive callout).

Principles to apply at turn-start:
  AUTONOMY / F2 RUTHLESS FEEDBACK / LOCKED-DESIGN-NOT-LICENSE / PROMISES > IN-MOMENT JUDGMENT / ODD §2.5 / OUTPUT-TO-DISK / WD-IN-DISPATCHES / NO --amend / NO push / NO FALSE FAULT / PRINCIPLE-APPLICATION DISCIPLINE.

Quality bar (Luke directive 2026-05-04): every AC ships complete + tested. One-at-a-time questions via PM verified end-to-end (no question-bombing). Auto-detection works on Rails + JS/TS canonical fixtures. Production-stake default highlighted on Rails. Install docs feel-intentional. Fresh-user fixture exercises full path. THE Eric ship — no partial features.

Source pointers (READ FIRST):
  - sub-plan-doc (THIS file's predecessor) at docs/plans/v0-2-1-cycle-1-eric-onboarding-hardening.md
  - master plan §3 Cycle 1 + §4 Cycle 1 dispatch brief at docs/plans/v0-2-1-master-plan.md
  - Decisions Q + P at parent docs/plans/eric-final-delivery-plan-2026-05-04.md §3
  - v0.1.7 Cycle 4 PM batch API at 122a7c8 (framework/per-project-pm/)
  - v0.1.6 production-safety at 3f1d237 / 88674cb
  - v0.1.8 adapters at 6711dd7 (Ruby) / 67dd302 (JS/TS) / c648cf9
  - v0.2.0 Cycle 1 6fef2f1 / Cycle 2 549fe88
  - framework/loam-init/src/loam/loam_init/cli.py (existing CLI; lazy-import idiom at lines 69-86)
  - framework/telegram-interface/.../setup_walkthrough.py (SetupWalkthrough class)
  - smoke discipline at plugins/dev-sdlc/docs/smoke-test-discipline.md

Fence + ACs + smoke + AI-time + out-of-scope: per sub-plan-doc §3 + §4.

Halt triggers — enumerated at sub-plan-doc §6 + below; halt-and-surface, do NOT silently work around:
  - WD drifts to pos3.
  - PM-side edits needed (any framework/per-project-pm/ surface change).
  - telegram-interface SetupWalkthrough API insufficient for inline Q2-channel-selection.
  - Language-detection misclassifies canonical Ruby+JS/TS adapter fixtures.
  - Production-stake default-flip ambiguous on what files / settings flip.
  - docs/dev-mode-getting-started.md authoring stubs out OR scope-creeps past 150 lines.
  - Survey-file parser crashes on a malformed-input case (graceful degrade is the contract).
  - Cycle wall-clock >8 h with no progress.
  - ODD §2.5 violations in surrounding code OR master plan itself.
  - >3 escalations needed.

Bookkeeping:
  - pos-amend apply (NOT --amend); manifest schema v3.
  - Single semantic commit on apply: feat(workspace-bootstrap): v0.2.1 Cycle 1 — Eric onboarding ritual hardening.
  - Short-form seal commit per AC.DPS2 schema-v3.
  - §14 backfill separate post-seal commit per AC.D-sa.7.
  - Master plan §9 per-cycle SHA backfill row updates with apply + seal SHAs.

Model rationale: (none — Sonnet default).
```

---

## §6 — Honest doubts (F2 RF on this Cycle 1 decomposition)

The places this plan-doc is least confident.

### Halt #1 surfaced pre-build — `docs/dev-mode-getting-started.md` does not exist

**Pre-flight check:** `ls /Users/lukeivers/ivers-corp-pos-v2/docs/dev-mode-getting-started.md` returns "No such file or directory." `docs/getting-started.md` exists at 211 lines. Master plan §3 Cycle 1 AC.ONBOARD.13 names BOTH files as install-docs to be updated at quality-bar feel-intentional level. AC.ONBOARD.13 thus implicitly REQUIRES authoring `docs/dev-mode-getting-started.md` from scratch (not just "updating" it).

**Resolution (recorded autonomously here; build agent honors):** Cycle 1 authors the new file. Minimum 80 lines (plan-doc §3 AC.ONBOARD.13 commits). Content scope: dev-mode prerequisites; how to enable dev-mode (`bootstrap.yaml: dev_mode: true` if such a flag exists; else mechanism per build-agent discovery); what additional CLAUDE.md fragment auto-loads in dev workspaces; v0.1.0+ dev-mode walkthrough. Build agent halts + surfaces if dev-mode-enable mechanism is itself unimplemented (plausible — the dev-mode fragment auto-load mechanism is referenced in the project CLAUDE.md but its enable-trigger is not enumerated in pos-v2 components I scanned).

### 6.2 — `loam onboard` subcommand may need argparse-discovery wiring

`loam onboard` registration via `loam.cli.subcommands` entry-point group is well-precedented by loam-init's M6a contract. *Mitigation:* build agent verifies workspace-bootstrap's pyproject.toml admits a `[project.entry-points."loam.cli.subcommands"]` block additively pre-add; halt + surface if not.

### 6.3 — Production-stake force-flip on Q6=Y surfaces user-facing override

When Q3=production-stake AND Q6=Y, AC.ONBOARD.10 forces `enable_auto_skill_capture: false`. *Mitigation:* build agent surfaces "Production-stake mode disables auto-skill-capture (SOC-2 floor); your Y on Q6 is overridden" in the completion summary. Method-level. Audit-log records the flip.

### 6.4 — Survey-file parser tolerance band is genuinely fuzzy

AC.ONBOARD.15's "never-block; fall back to fresh-ask" is the safe default. *Mitigation:* `survey-files/malformed.md` fixture exercises edge cases; build agent extends as needed; halt only on parser crash (graceful degrade is the contract).

### 6.5 — Telegram-interface `SetupWalkthrough` may not compose cleanly inline

Pre-flight grep showed `SetupWalkthrough` has `offer()` / `decline()` / `defer()` methods; full signature + side-effect surface unverified. *Mitigation:* build agent verifies inline invocation (sync or async wrapper) from `onboarding_activations.py`; halt + surface on non-trivial extension need (master plan halt-trigger).

### 6.6 — Question-resume on D3 restart is method-level

The plan-doc commits "audit-log serves as resume points" but resume-flow specifics (re-confirm vs skip vs partial-mid-Q) are builder's call. *Mitigation:* `test_AC_ONBOARD_11_audit_log.py` kill-mid-Q3 variant pins the chosen behavior.

### 6.7 — Cycle wall-clock band 5–9 h may be optimistic

15 ACs + integration test + 7 fixtures + 2 docs + manifest extension + audit-log + 5 new modules + entry-point wiring is substantive. *Mitigation:* halt-trigger at 8h with no progress; AI-time rubric calibration logged on completion.

---

## §7 — Method-decision register (Cycle-1-specific)

| Decision | Choice | Rationale |
|---|---|---|
| Onboarding entry-point | `loam onboard` subcommand + auto-trigger from `loam init` post-bootstrap | Composes on existing `loam init` precedent; idempotent re-invocation supports re-onboarding. |
| Question count | 6 install-time Qs (language / channel / safety-profile / extractor / watch / auto-skill-capture) | Per master plan §3 Cycle 1 + §9; survey is separate 12-Q surface (master plan §6.3). |
| Question sequencing API | `framework/per-project-pm/`'s `enqueue_decision` + `surface_next_questions_batch(n=1)` | v0.1.7 Cycle 4 verified; zero PM-side edits. |
| One-question-at-a-time enforcement | `n=1` parameter to `surface_next_questions_batch` | Decision Q + AC.QSURF.1 from v0.1.7 Cycle 4. |
| Language detection signals | Gemfile + config/application.rb + package.json + tsconfig.json (depth-bounded walk to depth 3) | Mirrors v0.1.8 adapter discovery shape; polyglot deferred to v0.2.x. |
| Production-stake default-highlight | Only when language=rails | Master plan §9 method-decision register; non-Rails users don't get the highlight (no false signal). |
| Survey-file conventional path | `~/loam-onboarding-survey.md` | Matches Eric survey output filename pattern from §6.3. |
| Survey-file env-var override | `$LOAM_ONBOARDING_SURVEY` (absolute path) | Mirrors `LOAM_ONBOARDING_SKIP` naming. |
| Survey-file parse tolerance | Best-effort; never-block; fall back to fresh-ask on ambiguity | Per AC.ONBOARD.15 + brief constraint. |
| Audit-log path | `<workspace>/.loam/audit-log/onboarding-<YYYY-MM-DD>.yaml` | Component-local; mirrors per-project-pm + odd-extractor audit-log shapes. |
| Audit-log schema | schema_version + event_kind + timestamp + notes + artefact_path | Per Decision P SOC-2 floor + odd-extractor v0.2.0 Cycle 1 shape. |
| Test-file granularity | One per AC (15 files) + 1 integration + 1 meta-test on roster | Mirrors v0.2.0 Cycle 1 + Cycle 2 convention. |
| Fresh-user fixture coverage | 4 synthetic-tree shapes (rails / jsts / mixed / unknown) + 3 survey-file shapes (well-formed / partial / malformed) | Covers all AC.ONBOARD.2 + .15 paths. |
| Production-stake force-flip on auto-skill-capture | Force `false` when production-stake; surface message in completion summary; audit-log records flip | Per AC.ONBOARD.10 + Decision P. |
| Channel-Telegram delegation | Inline `SetupWalkthrough.offer()` invocation; halt + surface on API mismatch | Per master plan halt-trigger. |
| Extractor-fire on Q4=Y | Subprocess invocation of `loam odd-extract <workspace_root>` (no Python-internal call) | Mirrors how loam-init invokes bootstrap_new_workspace; subprocess isolation |
| Watch-pointer on Q5=Y | Write a one-line note pointing at v0.2.0 Cycle 1 README scheduling section; no daemon spawn | Cycle 1 ships pointer; v0.2.x can extend to actual cron registration. |
| dev-mode-getting-started.md authoring | NEW file; minimum 80 lines; covers dev-mode enable + walkthrough | Halt #1 resolution; quality-bar binding. |
| Post-bootstrap callout in loam-init | Additive; lazy-import; TTY + LOAM_ONBOARDING_SKIP gates | Mirrors existing import-isolation idiom. |
| Idempotent re-invocation | Read existing manifest fields; offer per-question re-ask; no double-write on no-change | D2 smoke dimension. |

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Cycle-1 method decisions at §7. Master-plan method decisions at master plan §9 (`docs/plans/v0-2-1-master-plan.md`).

### Commit SHAs

- Amendment commit: `f6b5047ec2afce68a09e0d8305d10bf5d0434ccd` —
  `chore(amend): v0-2-1-cycle-1-eric-onboarding-hardening manifest+apply — workspace-bootstrap BASELINE+sidecar bump to 0bf33f1`
- Seal commit: `55640b1dadc0256c6090615eae18de1dfe91c846` —
  `chore(seals): v0-2-1-cycle-1-eric-onboarding-hardening — workspace-bootstrap at f6b5047`
