# v0.1.8 Cycle 3 — Ruby/Rails first-class adapter

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, build dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** Cycle 2 sealed at `4865028` (confidence bands + ratification); Cycle 1 sealed at `c1abda1` (odd-extractor scaffolding); v0.1.8 master plan `docs/plans/v0-1-8-master-plan.md` sealed at `1c2c478`; §9 register backfilled through Cycle 2 at `236fdcd`.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/plans/v0-1-8-master-plan.md` §3 + §4 Cycle 3.

**Status file:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-cycle-3-status-2026-05-04.md`.

**Quality bar (load-bearing):** "WOW Eric. No partial features. No excuses." — Luke 2026-05-04. Eric's app is Rails. A weak Rails adapter directly compromises Eric's deliverable. Every Rails idiom we claim to handle must be handled with **tested + reliable** behavior; "thin grep fallback" fails the bar (Decision O is the locked design rejecting that path).

---

## §1 — Outcome shape (the "why")

Cycle 1 shipped the extractor's shape (four-stage workflow, language-adapter registry, dry-run, budget envelope). Cycle 2 shipped confidence bands + ratification. Both ship with **zero adapters** — adapters are the content that makes the shape mean something.

Cycle 3 lands the **Ruby/Rails first-class adapter** — the language-specific extractor that understands Rails idioms (ActiveRecord migrations, callbacks, concerns, polymorphic associations, ActiveJob/Sidekiq, routes), uses tree-sitter for deterministic Ruby AST parsing, derives ACs test-first from RSpec/Minitest test files (per Decision G1), produces `BandedAC` instances with the correct confidence band per idiom (per AC.RAILS.6 mapping rules), and supports slice-and-swarm decomposition for SaaS-app-scale codebases that exceed the budget envelope.

Cycle 3's release-note promise: `loam odd-extract <rails-repo>` produces a confidence-banded contract draft where **passing RSpec tests → VERIFIED ACs** (with `evidence.kind="test"` and the test pinned to a `repo_sha`), **ActiveRecord schema + callbacks + concerns + polymorphic associations + Sidekiq jobs → PLAUSIBLE ACs** (with `evidence.kind="source"` and file-path + line-number citations), and **LLM-inferred domain rules → HYPOTHESISED ACs** (with `evidence.kind="inference"` and a non-empty rationale). Slice-and-swarm engages when the codebase exceeds the budget envelope: per-component slices (one per `app/models/` directory level, plus one per `db/migrate/` cohort, plus one per `app/jobs/` cohort) each get a sub-extraction; a deterministic aggregator merges into a single `RawACs` payload with no duplicate `ac_id`s.

The shape is the deliverable. The full Ruby-Rails-payment fixture (with 5–10 routes + ActiveRecord models with callbacks + concerns + polymorphic associations + Sidekiq jobs + ≥10 RSpec tests + README + permissive LICENSE) lands in **Cycle 4** per master plan §3 — Cycle 3 ships a small in-tree Rails-shape **synthetic test fixture** (controller + model + migration + concern + polymorphic association + Sidekiq worker + RSpec test) sufficient to exercise all 6 smoke dimensions at cycle level + every Rails-idiom recognizer. Release-level smoke against a real OSS Rails-payment fixture is at v0.1.8 close per master plan §5.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

Cycle 3 composes on top of Claude-native primitives + already-shipped loam machinery:

- **Cycle 1's `LanguageAdapter` Protocol.** The Ruby adapter implements `name: str`, `supports(repo: Path) -> bool`, `extract(repo: Path, plan: AnalysisPlan) -> RawACs`. No re-implementation; the Protocol is the contract.
- **Cycle 1's entry-point group `loam.odd_extractor.language_adapters`.** The Ruby adapter's pyproject declares an entry-point producing the adapter instance; `discover_adapters()` picks it up.
- **Cycle 2's `BandedAC` + `Evidence` + `ConfidenceBand`.** Adapter outputs construct `BandedAC` instances, dump via `model_dump()` to dict, and append to `RawACs.acs` per the round-trip contract (Cycle 2 plan-doc §5 Surface #1).
- **Cycle 1's `write_audit_entry` primitive.** The Ruby adapter writes per-slice `stage_complete` audit entries when slice-and-swarm engages; new event_kind value `slice_complete` extends without schema migration.
- **Cycle 1's budget envelope + dry-run primitive.** Slice-and-swarm respects the per-extraction `BudgetEnvelope`; each slice contributes a `per_slice_costs` entry to `RawACs.per_slice_costs` (existing field).
- **Cycle 2's ratification workflow.** Banded ACs produced by the Ruby adapter flow through `enqueue_ratification_batch` → PM → user-mediated promotion at v0.2.0+; Cycle 3 produces the ACs that Cycle 2 ratifies.
- **tree-sitter (Claude-adjacent ecosystem primitive).** `tree-sitter` Python bindings (pre-compiled wheels) provide deterministic AST parsing; `tree-sitter-ruby` (pre-compiled wheel) is the Ruby grammar. ODD-RE research §3 explicitly identified tree-sitter as the right tool ("tree-sitter has grammars for ~40 languages; signature extraction is per-grammar but uniform once parsed").

The required research question — **"What Claude capability does this lean on or extend?"** — answer: composes on Cycle 1's adapter Protocol + Cycle 2's banded schema + cost-governance budget + audit-log primitive + tree-sitter ecosystem. Nothing re-implemented.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden for a Rails-codebase user drops dramatically. The persona no longer has to hand-roll "walk this Rails repo + extract migrations + parse RSpec test names + follow polymorphic associations" — the adapter does it. The persona's job becomes "relay the contract draft + mediate ratification of HYPOTHESISED ACs." Without this cycle, the persona must hand-roll Rails-idiom recognition for every Eric-Rails request.
- **Harness test:** every persona that handles Rails codebases can call `loam odd-extract <rails-repo>` and get a banded contract draft. The Ruby adapter is a public API surface that composes — Cycle 5's `dispatch-brief-authoring` SKILL can compose against `loam.odd_extractor.lang.ruby.RubyAdapter` directly when a Rails-specific brief needs idiom-aware AC seeds.

Both pass.

### Lens 3 — ODD authoring

Outcome above + named ACs (§4) + halt triggers (§8) + acceptance smoke (§6). Method (which tree-sitter query strings, where the migration parser lives, how the slice-and-swarm aggregator merges, exact provenance string for VERIFIED test evidence) stays the builder's call.

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH** for the Ruby adapter's overall shape: master plan §3 Cycle 3 + dispatch §4 Cycle 3 names every AC (`AC.RAILS.{1..8}`) with explicit semantics; Cycle 1's adapter Protocol + Cycle 2's banded schema fix the input/output shapes; tree-sitter is a known-good AST library with Ruby grammar.

Outcome confidence is **MEDIUM** on five points (recorded as halt-surfaces in §5):

1. **Per-idiom recognizer split.** Whether each Rails idiom (ActiveRecord, callbacks, concerns, polymorphic, Sidekiq, routes) lives in its own module or as named functions in a single `idioms.py` is a method choice. Builder picks (see Surface #1).
2. **Slice-and-swarm aggregator algorithm.** Master plan AC.RAILS.4 names "codebase exceeding budget ceiling sliced + swarmed; aggregator merges" but doesn't specify the slicing strategy or merge algorithm. Builder picks the simplest deterministic strategy that exercises the slice-and-swarm contract end-to-end (see Surface #2).
3. **Test-first VERIFIED extraction granularity.** Master plan AC.RAILS.3 names "every passing RSpec/Minitest test → candidate VERIFIED AC" but doesn't constrain whether each `describe`/`it` block, each `context` cluster, each spec file, or each `expect(...).to...` assertion becomes one AC. Builder picks per-`it`-block as the natural granularity (see Surface #3).
4. **HYPOTHESISED AC source.** Master plan AC.RAILS.6 names "LLM-inferred domain rule → HYPOTHESISED" but Cycle 3's smoke runs without invoking a real LLM (cycle scope is the adapter shape; LLM integration is a Cycle 4+ scaling concern). Builder produces HYPOTHESISED ACs from heuristic-shaped inferences (e.g., "the model has `validates :email, presence: true` → infer 'email is required to create a User'") — labelled HYPOTHESISED with `rationale` capturing the heuristic provenance (see Surface #4).
5. **Synthetic Rails fixture vs cycle-internal vs plugin-tests-shape.** Master plan §3 Cycle 3 mentions "synthetic Rails snippets" for unit tests (AC.RAILS.8); Cycle 4 lands the canonical full Rails-payment fixture. Cycle 3's mid-shape: a small Rails-shape **integration fixture** (controller + model + migration + concern + polymorphic + Sidekiq + RSpec test) at `tests/fixtures/synthetic-rails/` is sufficient to exercise every recognizer + run all 6 smoke dimensions (see Surface #5).

The Pydantic models for Ruby-adapter outputs ship LOOSE — strict on `BandedAC` (already enforced by Cycle 2's model_validators), looser on per-Rails-idiom metadata fields (e.g., a `RubyAdapterMetadata` dict-typed field on BandedAC.evidence's `citations` list with `extra='ignore'` semantics — Cycle 4's Python adapter can extend without schema migration).

### Lens 5 — Swarming

Cycle-internal decomposition options:

- (a) per-Rails-idiom: ActiveRecord recognizer, callbacks recognizer, concerns recognizer, polymorphic recognizer, Sidekiq recognizer, routes recognizer + RSpec test extractor + ActiveRecord-migration recognizer (8 sub-units). Each sub-unit has a tighter AC (per-idiom — Sidekiq AC distinct from ActiveRecord AC). Stopping criterion: each sub-unit's AC is strictly tighter than the parent AC.RAILS.2.
- (b) per-pipeline-stage: AST parsing layer, recognizer registry, slice-and-swarm orchestrator, aggregator, banded-AC constructor (5 sub-units). Each has a tighter contract; stopping criterion met.
- (c) single-module Ruby adapter with internal helper functions. Coordination overhead minimal; AC granularity coarser. Stopping criterion fires (further decomposition adds only coordination overhead).

Builder picks (a) **internally** but ships as a single Cycle-3 dispatch — the per-idiom decomposition matches the AC.RAILS.2 sub-list (six named idioms) and gives the tightest per-recognizer AC mapping. Each idiom recognizer lives in its own file under `lang/ruby/recognizers/`, with one test file per recognizer. `max_planner_depth: 1` (no sub-planners; per-idiom files are the right granularity).

**No sub-agent dispatches in Cycle 3.** The cycle-level halt-trigger (5h plan-author + first-pass) is the swarm-level escape hatch — if the cycle exceeds the budget, halt and recommend 3a/3b split rather than spawning sub-agents (which would multiply working-tree coordination per `feedback_serialize_amendment_builds`).

---

## §3 — Single-component fence

**Scope:** `plugins/dev-sdlc/odd-extractor/` (the existing Cycle-1+2-sealed sub-package; the Ruby adapter lands as a NEW sub-tree under it).

**New paths (this cycle):**

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/__init__.py` — package marker for per-language adapter sub-trees.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/__init__.py` — public re-exports (`RubyAdapter`, `extract_rails_acs`).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/adapter.py` — `RubyAdapter` class implementing the `LanguageAdapter` Protocol. `name="ruby"`; `supports(repo)` checks for `Gemfile`; `extract(repo, plan)` orchestrates AST parsing + recognizer dispatch + slice-and-swarm.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/parser.py` — tree-sitter wrapper. Loads the Ruby grammar via `tree_sitter_ruby.language()`; exposes `parse_file(path) -> tree_sitter.Tree` + `query(tree, query_string) -> list[Capture]` helper. Lazy import (so `import loam_odd_extractor` doesn't pull tree-sitter into memory).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/recognizers/__init__.py` — re-exports each recognizer + the registry list.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/recognizers/active_record.py` — `recognize_active_record_models(tree, file_path) -> list[BandedAC]`. Detects `class X < ApplicationRecord` / `class X < ActiveRecord::Base` declarations; emits PLAUSIBLE ACs for each model with citations.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/recognizers/migrations.py` — `recognize_migrations(file_path) -> list[BandedAC]`. Reads `db/migrate/*.rb` files; detects `create_table`, `add_column`, `add_index`, `add_foreign_key`, `add_reference :owner, polymorphic: true`; emits PLAUSIBLE ACs per schema operation.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/recognizers/callbacks.py` — `recognize_callbacks(tree, file_path) -> list[BandedAC]`. Detects `before_save`, `after_create`, `before_validation`, `after_commit`, etc. (full Rails callback enumeration); emits PLAUSIBLE ACs.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/recognizers/concerns.py` — `recognize_concerns(tree, file_path) -> list[BandedAC]`. Detects `module X; extend ActiveSupport::Concern; ...; end` (concerns) and `include X` (concern usage); emits PLAUSIBLE ACs for definition + usage.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/recognizers/polymorphic.py` — `recognize_polymorphic_associations(tree, file_path) -> list[BandedAC]`. Detects `belongs_to :owner, polymorphic: true` + matching `add_reference :X, :owner, polymorphic: true` migrations; emits PLAUSIBLE ACs.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/recognizers/jobs.py` — `recognize_jobs(tree, file_path) -> list[BandedAC]`. Detects `class X < ApplicationJob` (ActiveJob), `include Sidekiq::Worker` / `include Sidekiq::Job`, `queue_as :name`; emits PLAUSIBLE ACs for job definition + queue.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/recognizers/routes.py` — `recognize_routes(file_path) -> list[BandedAC]`. Reads `config/routes.rb`; detects `resources :foo`, `get '/path', to: 'controller#action'`, `namespace :api`, `scope :v1`; emits PLAUSIBLE ACs per route.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/recognizers/rspec_tests.py` — `recognize_rspec_tests(tree, file_path) -> list[BandedAC]`. Detects `RSpec.describe X`, `describe '...'`, `it '...'`, `context '...'`; emits **VERIFIED** ACs (test-first per AC.RAILS.3) per `it` block, with `evidence.kind="test"`, `evidence.repo_sha=<resolved>`, `evidence.citations=[<file>:<line>:<test_name>]`.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/recognizers/minitest_tests.py` — `recognize_minitest_tests(tree, file_path) -> list[BandedAC]`. Detects `test '...' do` + `def test_<name>`; emits VERIFIED ACs per test method.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/heuristic_inferences.py` — `infer_domain_rules(banded_acs: list[BandedAC]) -> list[BandedAC]`. Heuristic-based inference of HYPOTHESISED ACs from already-extracted PLAUSIBLE ACs (e.g., `validates :email, presence: true` → "User creation requires email"). Per Surface #4 — heuristic-only in Cycle 3 (no LLM call); rationale field captures heuristic provenance.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/slicer.py` — slice-and-swarm orchestrator. `slice_repo(repo, plan, budget) -> list[Slice]` partitions the repo by Rails-idiom domain (one slice per `app/models/` cluster, one per `db/migrate/` cohort, etc.) when the dry-run estimate exceeds the budget; otherwise returns a single all-files slice. `aggregate_slice_results(slice_results) -> RawACs` merges per-slice `RawACs` into one with deterministic ordering + duplicate `ac_id` resolution.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/repo_sha.py` — `resolve_repo_sha(repo_path) -> str | None`. Subprocess-runs `git rev-parse HEAD` from the repo path; returns the SHA (or `None` for non-git repos). Required by VERIFIED ACs per AC.BANDS.2.

**Extension to Cycle 1's analyze.py (universal-admitted within fence):**

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/analyze.py` — extend the all-or-nothing claim model (line 130-132) to **per-file routing**. Each adapter's `supports(repo)` still gates whether the adapter participates; when multiple adapters claim, files route to adapters by language hint (`.rb` → ruby; `.py` → python; `.erb` → ruby; etc.). Per Surface #6 below — a known-required Cycle-3 refinement (Cycle 1 plan-doc explicitly noted this as a Cycle-3 tightening).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/spec.py` — no schema change required; the existing `Slice` model (`adapter_name`, `paths`) accommodates per-file routing as-is.

**Tests (new):**

- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/__init__.py` — package marker.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/conftest.py` — Ruby-fixture-specific pytest fixtures (synthetic Rails repo + injected repo_sha).
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_AC_RAILS_1_ruby_ast_adapter.py` — adapter implements `LanguageAdapter` Protocol; tree-sitter parses Ruby files; `supports()` returns True for Gemfile-bearing repos.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_AC_RAILS_2_rails_idiom_recognizers.py` — every Rails idiom recognizer recognizes its idiom on the synthetic fixture; no false negatives on the named patterns.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_AC_RAILS_3_test_first_extraction.py` — passing RSpec test → VERIFIED AC with `evidence.kind="test"`, `repo_sha` non-null, `citations=[<file>:<line>:<test_name>]`. Same for Minitest.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_AC_RAILS_4_slice_and_swarm.py` — when budget would be exceeded, slicer partitions; aggregator merges; deterministic `ac_id` ordering; no duplicates.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_AC_RAILS_5_eric_ratification_pin.py` — banded contract produced by adapter is consumable by Cycle 2's `enqueue_ratification_batch` end-to-end (uses a tmp `PMRuntime`); the contract structure pins what Cycle 4 must produce against the canonical fixture.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_AC_RAILS_6_band_mapping_per_idiom.py` — ActiveRecord schema → PLAUSIBLE; passing test → VERIFIED; LLM-inferred (heuristic in Cycle 3 per Surface #4) → HYPOTHESISED. Each band variant constructed from the synthetic fixture matches the expected band.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_AC_RAILS_7_cost_governance_dry_run.py` — dry-run produces per-slice estimate; live run respects budget envelope; over-budget slices halt with `BudgetExceededError`.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_AC_RAILS_8_synthetic_snippets.py` — adapter unit tests against hand-authored Ruby snippets (no full Rails repo) — one snippet per recognizer + one combined snippet.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_per_file_routing.py` — analyze.py's per-file routing extension correctly partitions `.rb` → ruby slice and `.py` → unhandled (no Python adapter in Cycle 3). Mirror of Surface #6.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_smoke_d1_cold_state.py` — D1 cold-state: fresh tmp workspace + synthetic Rails fixture → `loam odd-extract` end-to-end → banded contract draft with the expected idiom counts.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_smoke_d2_idempotency.py` — D2 idempotency variant: 5 extractions against the same fixture produce byte-identical artefacts (modulo timestamps via clock injection).
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_smoke_d5_cross_session.py` — D5 cross-session: per-slice extraction state survives `/clear`; resume reads partial slice state and completes remaining slices.
- `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/test_smoke_d6_telemetry_floor.py` — D6 telemetry floor: every Rails idiom recognized + every slice run logs an audit entry.

**Test fixtures (new):**

- `plugins/dev-sdlc/odd-extractor/tests/fixtures/synthetic-rails/` — small Rails-shape fixture:
  - `Gemfile` — declares `rails`, `sidekiq`, `pg`.
  - `config/routes.rb` — 3 routes (`resources :payments`, `namespace :api { resources :webhooks }`, `get '/health', to: 'health#index'`).
  - `app/controllers/payments_controller.rb` — RESTful controller (`index`, `create`, `show`).
  - `app/models/payment.rb` — `class Payment < ApplicationRecord` with `belongs_to :owner, polymorphic: true`, `validates :amount_cents, presence: true`, `before_save :normalize_amount`, `after_create :enqueue_webhook_job`, includes `Auditable`.
  - `app/models/concerns/auditable.rb` — concern with `extend ActiveSupport::Concern`, `included { ... }` block.
  - `app/jobs/payment_webhook_job.rb` — `class PaymentWebhookJob < ApplicationJob; queue_as :webhooks; def perform(payment_id); ...; end; end`.
  - `app/jobs/sidekiq_metrics_worker.rb` — `class SidekiqMetricsWorker; include Sidekiq::Job; sidekiq_options queue: :metrics; def perform; ...; end; end`.
  - `db/migrate/20260101000001_create_payments.rb` — `create_table :payments` with `t.bigint :amount_cents`, `t.references :owner, polymorphic: true`, `t.timestamps`; `add_index :payments, [:owner_type, :owner_id]`.
  - `spec/models/payment_spec.rb` — RSpec tests: `describe Payment`, `it 'validates amount presence'`, `it 'normalizes amount before save'`, `it 'enqueues webhook job after create'`.
  - `spec/jobs/payment_webhook_job_spec.rb` — RSpec test: `it 'sends a webhook for the payment'`.
  - `test/integration/payment_flow_test.rb` — Minitest test: `test 'full payment flow'` (one Minitest case to exercise the Minitest recognizer).
  - `README.md` — describes the synthetic fixture (clearly labelled `SYNTHETIC TEST FIXTURE — NOT A REAL APP`).

**Edits to existing dev-sdlc paths (universal-admitted within fence):**

- `plugins/dev-sdlc/odd-extractor/pyproject.toml` — add dependencies on `tree-sitter>=0.23` + `tree-sitter-ruby>=0.23`. Add entry-point declaration:
  ```toml
  [project.entry-points."loam.odd_extractor.language_adapters"]
  ruby = "loam_odd_extractor.lang.ruby:RubyAdapter"
  ```
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/__init__.py` — re-export `RubyAdapter` from `lang.ruby`.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/observability.py` — extend `event_kind` enum doc-comment to include `slice_complete` (no schema change; the field is `str` already, just documentation).
- `plugins/dev-sdlc/odd-extractor/README.md` — add a "Ruby/Rails adapter" subsection naming the public API + tree-sitter dep.
- `plugins/dev-sdlc/docs/odd-methodology.md` — append §12 "Per-language adapter conventions (Ruby/Rails first)" describing the band-mapping rules per idiom (mirrors §11's structure for confidence bands).

**Composition (read-only, no edit):**

- `framework/cost-governance/` — read-only import of dry-run primitive + budget envelope (already in Cycle 1 import surface; no new edits).
- `framework/per-project-pm/` — no direct edits; AC.RAILS.5's Eric-ratification pin uses Cycle 2's `enqueue_ratification_batch` which is already wired.

**Universal-admitted prefixes/files (off-fence, allowed under standard amendment policy):**

- `docs/plans/` — this plan-doc + manifest.
- `CLAUDE.md`, `docs/odd-in-loam.md`, `docs/odd-methodology.md` (top-level), `docs/STATE.md` — universal admission per `dev-pattern-simplifications-2.manifest.yaml` precedent.

**Out-of-fence (would halt-and-surface):**

- Any `framework/` component edit other than read-only imports.
- Any other `plugins/` component edit (loam-skills/, etc.).
- Any Python adapter implementation (Cycle 4).
- Any change to Cycle 2's PM contract or `BandedAC` schema.
- Any change to the canonical full Rails-payment fixture (Cycle 4 owns that).

---

## §4 — AC family — `AC.RAILS.*` (locked)

Each AC has at least one explicit pytest under `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/`. ODD §2.5 — every line of code, every branch, every test maps to a named AC.

### AC.RAILS.1 — Ruby AST adapter via tree-sitter

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/adapter.py` exposes `RubyAdapter` class:
  - `name = "ruby"`.
  - `supports(repo: Path) -> bool` returns True iff the repo contains a `Gemfile` or any `.rb` file.
  - `extract(repo: Path, plan: AnalysisPlan) -> RawACs` runs the orchestration: parses every `.rb` file in the plan's slices via tree-sitter; dispatches to recognizers; constructs `BandedAC` instances; returns `RawACs` with `acs=[d.model_dump() for d in banded_acs]`.
- `lang/ruby/parser.py` exposes `parse_file(path: Path) -> tree_sitter.Tree` using `tree_sitter.Language(tree_sitter_ruby.language())`. Lazy import to avoid pulling tree-sitter at extractor-import time. Returns parse failure (`tree.root_node.has_error == True`) as a sentinel; recognizers skip files with parse errors and emit a `parse_error` audit-log entry.
- The adapter declares a `[project.entry-points."loam.odd_extractor.language_adapters"]` entry that resolves to `RubyAdapter` (callable factory, returns the singleton instance).
- **Test:** `test_AC_RAILS_1_ruby_ast_adapter.py` — adapter is `LanguageAdapter`-Protocol-compliant (manually validated via `_validate_adapter`); `supports()` True for Gemfile-bearing fixture, False for empty dir; `parse_file()` round-trips a known Ruby snippet; tree-sitter Ruby grammar loads; entry-point discovers the adapter from a tmp install (deferred — entry-point registration is structural verification only).

### AC.RAILS.2 — Rails-idiom recognizers (six idioms)

- Each idiom has a dedicated recognizer module under `lang/ruby/recognizers/`:

| Idiom | Module | Detection signal | Band emitted |
|---|---|---|---|
| ActiveRecord models | `active_record.py` | `class X < ApplicationRecord` or `< ActiveRecord::Base` | PLAUSIBLE |
| ActiveRecord migrations | `migrations.py` | `db/migrate/*.rb` with `create_table`, `add_column`, `add_index`, `add_foreign_key`, `add_reference :X, polymorphic: true` | PLAUSIBLE |
| Callbacks | `callbacks.py` | `before_save`, `after_create`, `before_validation`, `after_commit`, `after_destroy`, `before_create`, `after_save`, `before_destroy`, `after_update`, `before_update`, `around_save`, `around_create`, `around_destroy`, `around_update` | PLAUSIBLE |
| Concerns | `concerns.py` | `module X; extend ActiveSupport::Concern; ...; end` (definition) + `include X` (usage in models/controllers) | PLAUSIBLE |
| Polymorphic associations | `polymorphic.py` | `belongs_to :X, polymorphic: true` (model side) + `add_reference :Y, :X, polymorphic: true` (migration side) | PLAUSIBLE |
| ActiveJob/Sidekiq | `jobs.py` | `class X < ApplicationJob` (ActiveJob) + `include Sidekiq::Worker` / `include Sidekiq::Job` (Sidekiq) + `queue_as :name` / `sidekiq_options queue: :name` | PLAUSIBLE |
| Routes | `routes.py` | `config/routes.rb` with `resources`, `get/post/put/patch/delete '/path'`, `namespace`, `scope`, `root to:` | PLAUSIBLE |

- Each recognizer:
  - Takes `(tree: tree_sitter.Tree, file_path: Path)` (or `(file_path: Path)` for migrations + routes which are file-pattern-based) and returns `list[BandedAC]`.
  - Constructs `BandedAC` with: `ac_id` (deterministic — `f"AC.RAILS.<idiom>.{slug}"` derived from the AST node's content); `text` (descriptive prose, e.g., "Payment model has before_save callback :normalize_amount"); `confidence=PLAUSIBLE`; `evidence=Evidence(kind="source", citations=[f"<file>:<line>"], repo_sha=<resolved>)`; `backing_files=[<file>]`.
- `lang/ruby/recognizers/__init__.py` exposes `ALL_RECOGNIZERS: list[Recognizer]` for the adapter's main loop to iterate.
- **Test:** `test_AC_RAILS_2_rails_idiom_recognizers.py` — for each idiom, the recognizer applied to the synthetic fixture finds the expected occurrence (no false negatives on the synthetic patterns); applied to an empty Ruby file, returns `[]` (no false positives).

### AC.RAILS.3 — Test-first extraction (RSpec + Minitest → VERIFIED)

- `recognizers/rspec_tests.py` and `recognizers/minitest_tests.py` produce VERIFIED ACs from passing test files.
- For RSpec: detect `RSpec.describe X do ... it '<text>' do ... end ... end`. Per-`it`-block AC: `ac_id=f"AC.RAILS.test.{describe_class}.{slugify(it_text)}"`; `text=f"{describe_class}: {it_text}"`; `confidence=VERIFIED`; `evidence=Evidence(kind="test", citations=[f"{file}:{line}:{describe_class}#{it_text}"], repo_sha=<resolved>, rationale=None)`.
- For Minitest: detect `class X < ActiveSupport::TestCase / Minitest::Test` + `test '<text>' do` + `def test_<name>`.
- Cycle 3 does NOT execute the tests (that requires a Ruby interpreter + Rails environment outside loam's scope); the VERIFIED band is granted on the assumption that tests in the repo were passing at the resolved `repo_sha`. The persona MUST verify test pass-state during ratification; this is a known limitation, surfaced as RF gap §10 #2.
- repo_sha resolution: `lang/ruby/repo_sha.py` runs `git -C <repo> rev-parse HEAD`. If the repo isn't a git repo, returns None; the recognizer downgrades VERIFIED → PLAUSIBLE for that file (per AC.BANDS.2 — VERIFIED requires repo_sha non-null).
- **Test:** `test_AC_RAILS_3_test_first_extraction.py` — synthetic `payment_spec.rb` produces N VERIFIED ACs (N = number of `it` blocks in the fixture); each carries `evidence.kind="test"`, non-null `repo_sha`, citations matching `<file>:<line>:<describe>#<it>`; Minitest case produces 1 VERIFIED AC; non-git fixture produces PLAUSIBLE (downgrade) ACs. Bands round-trip via `BandedAC.model_validate(ac.model_dump())`.

### AC.RAILS.4 — Slice-and-swarm

- `lang/ruby/slicer.py` exposes:
  - `slice_repo(repo: Path, plan: AnalysisPlan, budget: BudgetEnvelope, estimate: EstimateResult) -> list[Slice]` — when `estimate.estimated_money_cents <= budget.hard_cap_money_cents`, returns one all-files slice (`adapter_name="ruby"`, `paths=<all-ruby-files>`). When over-budget, partitions by Rails-idiom domain:
    - One slice per `app/models/` cluster (group by sub-directory).
    - One slice per `db/migrate/` cohort (split into chunks of ≤25 migration files).
    - One slice per `app/jobs/` cluster.
    - One slice per `app/controllers/` cluster.
    - One slice for `config/routes.rb` (always solo).
    - One slice for `spec/`/`test/` (for VERIFIED extraction).
    - One slice for `app/models/concerns/`.
    - One catch-all slice for remaining `.rb` files.
  - `aggregate_slice_results(slice_results: list[RawACs]) -> RawACs` — merges per-slice `RawACs`:
    - Concatenates `acs` lists; deduplicates by `ac_id` (last-write-wins; logged as `slice_aggregate_dedup` audit entry per occurrence).
    - Concatenates `unhandled_paths` lists; deduplicates by path string.
    - Merges `per_slice_costs` dicts (slice IDs are unique by construction).
    - Sorts `acs` by `ac_id` for deterministic output (D2 idempotency).
- The adapter's `extract()` calls `slice_repo()` to decide single-slice vs multi-slice, then iterates slices, parses+recognizes per-slice, and aggregates.
- F3 (swarming) `needs_fresh_start` analog: if the aggregator detects more than 50% duplicate `ac_id`s across slices (signalling drift between slices), raises `SliceDriftError`; the adapter halts the extraction with a structured `slice_drift` audit entry. (The adapter doesn't auto-restart; halt-and-surface to the dispatcher, who can re-run with adjusted slicing.)
- **Test:** `test_AC_RAILS_4_slice_and_swarm.py` — single-slice path verifies cost ≤ budget → returns one slice; multi-slice path verifies cost > budget → returns ≥ 6 slices for the synthetic fixture (every Rails-idiom domain represented); aggregator merges deterministically; duplicate `ac_id`s deduplicated with audit-log entry; `SliceDriftError` raised when >50% duplicates injected.

### AC.RAILS.5 — Eric-ratification workflow end-to-end pin

- The banded contract draft produced by the Ruby adapter against the synthetic Rails fixture is consumable by Cycle 2's `enqueue_ratification_batch` end-to-end.
- The test constructs a tmp `PMRuntime` against a tmp workspace, runs the full `loam odd-extract` four-stage workflow against the synthetic fixture in **live** mode (with budget override since the synthetic fixture is small and free), then runs `loam odd-extract <draft>.md --ratify --pm-name <handle>` and asserts:
  - The CLI exits 0.
  - The PM's decision queue carries one entry per banded AC produced by the adapter.
  - The first surfaced question contains the AC's `text` field verbatim.
  - The audit log carries one `ratification_*` entry per enqueue (cross-component verification).
- This AC pins the contract for Cycle 4: when Cycle 4 produces a banded contract from the canonical Ruby-Rails-payment fixture, the same shape must be consumable by `enqueue_ratification_batch`.
- **Test:** `test_AC_RAILS_5_eric_ratification_pin.py` — end-to-end as described above; uses the synthetic fixture, not the canonical Cycle 4 fixture (which doesn't exist yet).

### AC.RAILS.6 — Confidence band rules per Rails idiom

- Bands are emitted per the master plan AC.RAILS.6 mapping:
  - **VERIFIED** — passing RSpec/Minitest test (per AC.RAILS.3).
  - **PLAUSIBLE** — ActiveRecord schema, migrations, callbacks, concerns, polymorphic associations, Sidekiq/ActiveJob jobs, routes (per AC.RAILS.2).
  - **HYPOTHESISED** — heuristic-derived domain inferences (per Surface #4).
- Each band's `evidence` block carries the per-band-required fields per AC.BANDS.2 (Cycle 2's model_validator):
  - VERIFIED → `kind="test"`, non-null `repo_sha`, non-empty `citations`.
  - PLAUSIBLE → `kind="source"`, non-empty `citations`.
  - HYPOTHESISED → `kind="inference"`, non-empty `rationale`.
- The adapter constructs `BandedAC` instances directly; `BandedAC`'s model_validator enforces band/evidence consistency at construction time. Any malformed pair raises `pydantic.ValidationError`; the adapter catches + downgrades + logs a `band_downgrade` audit entry (e.g., VERIFIED→PLAUSIBLE when repo_sha is None).
- **Test:** `test_AC_RAILS_6_band_mapping_per_idiom.py` — for each band/idiom pair from the synthetic fixture, the constructed `BandedAC` has the expected band; for each malformed pair (e.g., test recognizer with no repo_sha), the adapter downgrades correctly + logs the downgrade.

### AC.RAILS.7 — Cost-governance dry-run + budget envelope

- The Ruby adapter's `extract()` calls `estimate_for_extraction(scope_id=f"odd-extract:{repo_id}:ruby", recent_actuals=[])` per slice via the existing Cycle-1 budget primitive.
- Per-slice estimate fed into the slicer's slice-vs-single decision per AC.RAILS.4.
- Live extraction respects the `BudgetEnvelope` per slice — over-budget slices halt with `BudgetExceededError`; the rest of the extraction proceeds on already-completed slices (non-fatal).
- Audit-log entries: `slice_complete` per slice + `slice_failed` for over-budget; the existing `extraction_end` bookend captures the cumulative outcome.
- **Test:** `test_AC_RAILS_7_cost_governance_dry_run.py` — dry-run produces an estimate; live run with an inflated artificial budget succeeds; live run with budget set below the synthetic fixture's estimated cost halts with `BudgetExceededError` + audit-log entry.

### AC.RAILS.8 — Adapter unit tests against synthetic Rails snippets

- Hand-authored Ruby snippets (one per recognizer + a combined snippet) under `tests/lang/ruby/snippets/` exercise each recognizer in isolation without requiring the full synthetic fixture.
- Per-snippet test asserts the recognizer detects the named pattern (positive) AND does not detect unrelated patterns (negative, e.g., the migrations recognizer doesn't fire on a non-migration `.rb` file).
- **Test:** `test_AC_RAILS_8_synthetic_snippets.py` — one test per recognizer; positive + negative case per recognizer.

---

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

### Surface #1 — Per-recognizer module split (no halt — recorded)

**Decision (autonomous):** each Rails idiom recognizer lives in its own file under `lang/ruby/recognizers/`. Eight recognizer files: `active_record.py`, `migrations.py`, `callbacks.py`, `concerns.py`, `polymorphic.py`, `jobs.py`, `routes.py`, `rspec_tests.py`, `minitest_tests.py` (plus `heuristic_inferences.py` for HYPOTHESISED ACs).

**Rationale:** matches the per-idiom AC.RAILS.2 sub-list; each recognizer has its own per-AC test file (one test file per recognizer); future Cycle-3.x amendments (e.g., Rails 8-specific syntax) tighten one recognizer at a time without touching the rest. Per-file decomposition matches Lens 5 stopping criterion (each sub-unit's AC is strictly tighter than the parent AC.RAILS.2).

### Surface #2 — Slicer's slicing strategy (no halt — recorded)

**Decision (autonomous):** the slicer partitions by **Rails-idiom domain** (one slice per `app/models/` cluster, one per `db/migrate/` cohort, one per `app/jobs/`, etc.) when the dry-run estimate exceeds the budget; otherwise returns a single all-files slice. Migration cohorts split at ≤25 migration files per slice (heuristic — typical Rails app has 50-200 migrations; 25 is a "small but not absurd" chunk).

**Rationale:** Rails-idiom domain is the natural partitioning axis (Cartographer-style per ODD-RE research §3.4); each slice is independently parseable + recognizable; cross-slice deduplication handles the rare case where a model file appears in two slices. Alternative strategies (per-file, per-MB, per-AST-node-count) were rejected as either too-fine-grained (per-file → thousands of slices in a SaaS app, swamps the audit log) or under-explained-by-Rails-shape (per-MB → no clear interpretation when ratification surfaces "this slice").

### Surface #3 — Test-first extraction granularity (no halt — recorded)

**Decision (autonomous):** **per-`it`-block** for RSpec, **per-`test '...'`-block** + **per-`def test_<name>`** for Minitest. Each block / method becomes one VERIFIED AC.

**Rationale:** matches Eric synthesis Decision G1 (test-name-as-AC-name); aligns with RSpec idiom (`it 'verb-phrase'` is the assertion-as-spec); aggregates well at ratification time (one decision per test, not one per assertion which would be too granular). Per-`describe`/`context` cluster would be too coarse (loses individual `it`-block fidelity); per-`expect` would be too fine (a single test often has multiple `expect`s for the same behaviour).

### Surface #4 — HYPOTHESISED AC source: heuristic-shaped, no LLM in Cycle 3 (no halt — recorded)

**Decision (autonomous):** Cycle 3 produces HYPOTHESISED ACs from **heuristic-shaped inferences** based on already-extracted PLAUSIBLE ACs, not from real LLM calls.

Heuristic patterns (initial, extensible in `lang/ruby/heuristic_inferences.py`):
- `validates :foo, presence: true` → "<Model> creation requires <foo>" (HYPOTHESISED — the validation may be conditional or bypassed).
- `validates :foo, uniqueness: true` → "<foo> is unique across all <Model> instances" (HYPOTHESISED — same reason).
- `belongs_to :owner, polymorphic: true` → "<Model> can belong to multiple owner types" (HYPOTHESISED — the polymorphism may be unused).
- `before_save :normalize_X` → "<X> is normalized before persistence" (HYPOTHESISED — the callback may have early returns).
- `after_create :enqueue_X` → "<X> is enqueued asynchronously after creation" (HYPOTHESISED — the enqueue may be conditional).

Each HYPOTHESISED AC's `rationale` field captures the heuristic that produced it (e.g., `f"heuristic: validates :{attr}, presence: true → infers required-on-create"`). This makes the heuristic provenance machine-traceable + human-reviewable.

**Rationale:** Cycle 3 must ship a working HYPOTHESISED-band path to satisfy AC.RAILS.6; LLM integration adds non-trivial cost-governance complexity (rate-limiting, retries, partial-batch recovery) that's outside the cycle scope. Heuristic-shaped inference is faithful to the band semantics ("LLM-derived inference" → "machine-derived inference with explicit reasoning chain") without requiring an actual LLM call. Cycle 4+ can swap in LLM-shaped inference under the same rationale-string-required contract; the BandedAC schema is unchanged.

**RF flag (§10 #1):** the heuristic inference list is intentionally minimal in Cycle 3 (5 patterns). Real Rails apps have richer signals (e.g., `scope :active`, `self.table_name=`, controller `before_action` chains). Cycle 4+ extends.

### Surface #5 — Synthetic Rails fixture vs cycle-internal vs plugin-tests-shape (no halt — recorded)

**Decision (autonomous):** Cycle 3 ships a small in-tree synthetic Rails fixture at `plugins/dev-sdlc/odd-extractor/tests/fixtures/synthetic-rails/`. Not a full Rails app (that's Cycle 4); not pure-snippets (those exist separately in `tests/lang/ruby/snippets/` per AC.RAILS.8).

**Shape:**
- File counts: 1 Gemfile, 1 routes.rb, 1 controller, 1 model, 1 concern, 1 migration, 2 jobs (1 ActiveJob + 1 Sidekiq), 1 RSpec spec file, 1 Minitest test file, 1 README. Total: 11 files.
- Every Rails idiom recognizer is exercised against the fixture (all 6 master-plan idioms + RSpec + Minitest).
- The fixture is **clearly labelled** as synthetic (README banner + filename prefix `synthetic-rails/`) so it can never be mistaken for a usable Rails app or accidentally distributed as the canonical Cycle-4 fixture.
- The fixture is committed real files (not a fixture-builder script) so byte-identical extractions across runs are testable (D2 idempotency).

**Rationale:** the cycle scope is "the adapter shape works"; a synthetic fixture is sufficient evidence (unit + integration + smoke); a full Rails app is over-investment for cycle scope. Cycle 4's canonical fixture is the release-level smoke surface.

### Surface #6 — analyze.py per-file routing extension (no halt — recorded)

**Decision (autonomous):** Cycle 1's `analyze.py` had an "all-or-nothing" claim model (line 130-132 noted as a Cycle-3 refinement). Cycle 3 extends `analyze_repo()` to **per-file routing**:

- For each file in the repo walk, iterate adapters; the **first adapter** whose `supports(repo) returns True` AND whose language hint (file extension) matches gets the file in its slice.
- Language hint mapping (initial; extensible per Cycle 4):
  - `.rb` → ruby (also `.erb`, `.rake`, `Rakefile`, `Gemfile`, `Gemfile.lock`, `.gemspec`).
  - `.py` → python (Cycle 4).
  - All others → unhandled.
- Files with no matching adapter land in `unhandled_paths`.
- Each adapter that claims at least one file gets a `Slice(adapter_name=<name>, slice_id=f"{name}-root", paths=<claimed-files>)`.

**Rationale:** Rails repos contain JS, ERB, YAML, JSON, README files that aren't Ruby code; the all-or-nothing model means Cycle 4's Python adapter would be blocked by Cycle 3's Ruby adapter. Per-file routing is the smallest extension that supports multi-adapter codebases (common in modern Rails apps with JS frontends, Python data-science scripts, etc.).

The extension is non-breaking: with one adapter, the behaviour is identical to Cycle 1 (all matching files go to the one adapter; non-matching files go to unhandled). With zero adapters, behaviour is unchanged (all files unhandled). Cycle 1's tests continue to pass.

### Surface #7 — repo_sha resolution: subprocess-based (no halt — recorded)

**Decision (autonomous):** `lang/ruby/repo_sha.py` runs `git -C <repo> rev-parse HEAD` via `subprocess.run(...)`. Returns the SHA on success; returns None on any failure (non-git repo, missing git binary, detached HEAD with a special form). When None, VERIFIED ACs downgrade to PLAUSIBLE per AC.BANDS.2.

**Rationale:** subprocess-shelling-to-git is the universally-available approach (no Python git library dep; matches loam's existing `loam-amend` precedent which shells to git). Test isolation: tests inject a fixed SHA via a `pytest fixture` (`monkeypatch.setattr(repo_sha, 'resolve_repo_sha', lambda _p: '<fixed-test-sha>')`).

### Surface #8 — tree-sitter dependency declaration + lazy-import (no halt — recorded)

**Decision (autonomous):** `tree-sitter>=0.23` and `tree-sitter-ruby>=0.23` are declared as **required** dependencies in `pyproject.toml` (not optional/extra). The `parser.py` module **lazy-imports** tree-sitter at first parse-call (not at module import) so `import loam_odd_extractor` doesn't pull tree-sitter into memory unnecessarily.

**Rationale:** required deps are honest — the Ruby adapter cannot function without them; making them optional would create a confusing partial-functionality matrix. Pre-compiled wheels mean install-time cost is small (~200KB combined per the pip dry-run output). Lazy-import preserves Cycle 1's "import is cheap" property for non-Ruby workflows (Python adapter Cycle 4 will follow the same pattern with `ast` stdlib — no extra deps).

### Surface #9 — Slice-aggregator deterministic order (no halt — recorded)

**Decision (autonomous):** the aggregator sorts merged ACs by `ac_id` lexicographically before returning. Per-slice processing order is deterministic (slice IDs sorted by name); within-slice AC order is preserved as-emitted by the recognizer (recognizers iterate AST nodes in tree-walk order, which is deterministic for a given input file).

**Rationale:** D2 idempotency requires byte-identical artefacts across runs; lexicographic sort by `ac_id` gives that property even if slice processing order changes (e.g., parallel slice execution in v0.2.0+).

### Surface #10 — Eric-ratification pin without canonical fixture (no halt — recorded)

**Decision (autonomous):** AC.RAILS.5's "end-to-end Eric-ratification on Ruby-Rails fixture" is exercised against the **synthetic** fixture in Cycle 3. The canonical full fixture lands in Cycle 4. The pin's purpose: verify the contract shape is consumable by Cycle 2's ratification machinery. Cycle 4's fixture-shaped test (`test_FIXTURES_4_eric_ratification_workflow_runs_e2e_on_ruby_rails_fixture`) re-exercises the same contract against the canonical fixture.

**Rationale:** the master plan's wording is "this AC pins the contract for that smoke" — the pin is a structural claim, not a content claim. Synthetic fixture is sufficient for the structural pin.

### Surface #11 — D2/D3/D4 smoke applicability (no halt — recorded)

**Decision (autonomous):** mirroring Cycle 1 §10 Surface #10:
- D2 — n/a structurally (one-shot CLI). Idempotency variant exercised: 5 extractions against the synthetic fixture produce byte-identical artefacts (modulo timestamps via clock injection). Cycle 3-specific addition: per-slice idempotency — the same slice extracted twice produces byte-identical per-slice RawACs.
- D3 — n/a (no long-running process).
- D4 — n/a (same as D3).

D1, D5, D6 fully exercised at cycle level per master plan §3 Cycle 3 dispatch.

### Surface #12 — synthetic fixture as "real Rails snippets" check (no halt — recorded)

**Decision (autonomous):** the synthetic fixture's Ruby files contain **valid Ruby syntax** that tree-sitter parses without errors. Each file is hand-authored to exercise specific recognizer patterns; comments mark which recognizer each block targets (e.g., `# RECOGNIZER: callbacks — before_save normalizes amount`).

**Rationale:** Cycle 3's smoke must be against runnable-shape Rails code, not pseudocode. The fixture doesn't need to actually run as a Rails app (no Rails environment in CI); it just needs to be syntactically valid Ruby that tree-sitter accepts. This satisfies "tested + reliable behavior" without requiring a Ruby runtime in the test environment.

### Surface #13 — universal-admitted doc edits (no halt — recorded)

**Decision (autonomous):** `plugins/dev-sdlc/docs/odd-methodology.md` is universal-admitted per Cycle 1's manifest precedent + the v3 manifest's `universal_paths.files` list. Cycle 3 appends a §12 "Per-language adapter conventions (Ruby/Rails first)" section; the manifest's universal_paths admits the path explicitly to document intent for SOC-2-style audit readers (Decision P).

---

## §6 — Smoke (REALISTIC CONDITION — applicable dimensions per smoke-test-discipline §6)

Cycle-level smoke. Release-level HARD gate at v0.1.8 close (master plan §5 + Decision R), not this cycle.

### D1 — cold-state (fresh canonical workspace + synthetic fixture)

**Pattern.** Tmp directory as workspace root; synthetic Rails fixture copied to a tmp directory as the target repo. Run `loam odd-extract <fixture> --live --budget-cents 5000` (live mode + bumped budget so the small fixture isn't blocked). Assert: (a) all four stage artefacts land at expected paths; (b) `contract-draft.md` parses as markdown with the banded-AC table populated (Cycle 2's `<!-- ACS_TABLE_HERE -->` injection); (c) the contract draft has ≥1 VERIFIED AC (from RSpec test recognition), ≥3 PLAUSIBLE ACs (model + migration + job from the synthetic fixture), ≥1 HYPOTHESISED AC (from heuristic inference); (d) `RawACs.acs` round-trips through `BandedAC.model_validate()` for every entry; (e) exit status 0.

**Test:** `test_smoke_d1_cold_state.py`.

### D2 — steady-state durability (n/a structurally; idempotency variant covered)

**Structural rationale.** Same as Cycle 1 — extractor is one-shot; no daemon.

**Idempotency variant exercised.** `test_smoke_d2_idempotency.py` runs the extraction five times against the synthetic fixture (with clock injection for timestamps + fixed repo_sha) and asserts byte-identical artefacts. Cycle-3-specific addition: per-slice idempotency — the same slice extracted twice produces byte-identical per-slice RawACs (slice-aggregator's deterministic-sort property under D2 lens).

### D3 — restart resilience (n/a)

Same rationale as Cycle 1 — no long-running process.

### D4 — reboot resilience (n/a)

Same rationale as Cycle 1.

### D5 — cross-session continuity

**Pattern.** Test setup runs the four-stage workflow against the synthetic fixture in process A; mid-extraction (after `analyze` + first slice's `generate` complete), simulates `/clear` by spawning process B as a subprocess. B runs `loam odd-extract <fixture> --resume --workspace-root <same>`; asserts B reads A's per-slice state (from `state.yaml` extended with `slice_states: dict[str, str]` field) and completes the remaining slices. Final contract draft has the union of A's + B's slice outputs.

**Test:** `test_smoke_d5_cross_session.py`.

The `/clear` analog is "fresh process boundary"; the test validates that boundary directly.

### D6 — telemetry floor

**Pattern.** Run a full extraction against the synthetic fixture; assert the audit log has:
- `extraction_start` (1 entry) — bookend.
- `stage_complete` (4 entries — one per stage) — Cycle 1 inheritance.
- `slice_complete` (≥1 entries — one per slice; multi-slice when the fixture is split, single-slice when it isn't) — Cycle 3 addition.
- `recognizer_finding` (≥6 entries — one per recognized Rails-idiom occurrence) — Cycle 3 addition; documents which recognizer fired on which file.
- `extraction_end` (1 entry) — bookend.
- Schema version preserved at 1; filenames monotonic `<NNNN>.yaml`.

**Test:** `test_smoke_d6_telemetry_floor.py`.

---

## §7 — Out of scope

Explicit deferrals (master plan §3 Cycle 3 + per-cycle dispatch):

- **Python adapter.** Mirror Ruby coverage for Python → Cycle 4.
- **Canonical Ruby-Rails-payment full fixture.** 5–10 routes + ActiveRecord models with callbacks + concerns + polymorphic associations + Sidekiq jobs + ≥10 RSpec tests + README + permissive LICENSE → Cycle 4.
- **Python-Flask-payment full fixture** → Cycle 4.
- **End-to-end smoke against canonical fixtures** → Cycle 4.
- **Real OSS Rails app smoke (e.g., gitlab, redmine)** → v0.1.8 release-level smoke per master plan §5 + Decision R.
- **6 dev-sdlc SKILLs** → Cycle 5.
- **LLM-driven HYPOTHESISED inference** → Cycle 4+ (heuristic-shaped in Cycle 3 per Surface #4).
- **Continuous codebase-watch (long-running daemon)** → v0.2.0+.
- **Cartographer-style optimization beyond what's needed for SaaS-app scale** → subsequent v0.x amendments.
- **Real test execution to verify VERIFIED-band claims.** Cycle 3 grants VERIFIED on the assumption tests pass at the resolved repo_sha; ratification is the human verification step. Cycle 4+ may add `--run-tests` flag for actual test execution.

---

## §8 — Halt triggers (in-flight)

Per dispatch + master plan:

- **WD drifts.** If `git rev-parse --show-toplevel` is not `/Users/lukeivers/ivers-corp-pos-v2/`, halt + surface.
- **Cycle 1 + 2 not sealed.** Verified at dispatch start: Cycle 1 sealed at `c1abda1`, Cycle 2 sealed at `4865028`. If either is not sealed, halt.
- **Plan-doc not authored before code.** This document IS that plan-doc.
- **Wall-clock >5 hours on plan-author + first-pass implementation.** This is THE master-plan-defined halt-trigger. Halt-and-surface; recommend split into Cycle 3.a (Ruby AST + 3 idioms — ActiveRecord, callbacks, routes) + Cycle 3.b (concerns, polymorphic, Sidekiq, slice-and-swarm).
- **Wall-clock >8 hours total.** Hard stop with partial findings; do NOT push through.
- **Any AC ships partial.** If `test_AC_RAILS_<n>_*.py` is XFAIL, skipped, or asserts a degraded behaviour, halt + reframe.
- **Rails idiom coverage requires more than 5 in-build decisions to land.** Halt + describe; don't accumulate decisions silently.
- **Slice-and-swarm aggregator surfaces drift between slices** (per F3 swarming pattern: `needs_fresh_start` analog; >50% duplicate `ac_id`s across slices). Halt + restart shard set with judge feedback (or surface the structural problem to dispatcher).
- **D5 cross-session smoke fails.** Halt unconditionally on red.
- **ODD violations discovered in surrounding code.** Halt + surface; do not silently extend (per `feedback_subagent_odd_violation_halt`).
- **Tree-sitter Ruby grammar fails to parse common Rails patterns.** If the synthetic fixture's hand-authored Ruby fails tree-sitter parsing on any recognizer-target pattern, halt — this is the cycle's foundational AST library failure (master plan halt-trigger Cycle 3 + RF on AST library choice in dispatch §4).

---

## §9 — Bookkeeping

- **Manifest:** `docs/plans/v0-1-8-cycle-3-ruby-rails-adapter.manifest.yaml` — schema_version: 3 with `plan_doc_ref:`. amendment.number omitted per AC.DPS1.10. ac_count: 8. smoke_outcome: "D1+D2-idempotency+D5+D6 exercised; D3/D4 n/a per smoke-test-discipline §6 (one-shot CLI)".
- **Apply:** `loam amend apply` — single merged manifest+apply commit per AC.DPS1.6 (v3 schema).
- **Seal:** `loam amend seal --plan-doc docs/plans/v0-1-8-cycle-3-ruby-rails-adapter.md` — synthesizes 5–15 line narrative body into `plugins/dev-sdlc/seals/SEAL_COMMIT.v0-1-8-cycle-3-ruby-rails-adapter`.
- **§9 backfill:** master plan `docs/plans/v0-1-8-master-plan.md` §9 method-decision register row for v0.1.8 Cycle 3 — doc-only commit after seal.
- **No tag push.** v0.1.8 tag waits on Cycles 4+5 + release-level HARD gate (Decision R).

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **Heuristic inference list is minimal in Cycle 3 (5 patterns).** Real Rails apps have richer signals — `scope :active`, `self.table_name=`, controller `before_action` chains, `accepts_nested_attributes_for`, `delegate :foo, to: :bar`. Cycle 4+ must extend. The `heuristic_inferences.py` module is structured as an extensible list of `(pattern, inference_template, rationale_template)` tuples so additions don't require core refactoring.

2. **VERIFIED band is granted on the assumption tests pass at repo_sha.** Cycle 3 doesn't execute tests (requires Ruby runtime + Rails environment, outside loam's scope). The persona MUST verify test pass-state during ratification. This is a known limitation; the band is "VERIFIED *as-of-extraction-time-by-human-authority*" not "VERIFIED *by automated test run*." Surfaced in `odd-methodology.md` §11 + §12 doc edits. Cycle 4+ may add `--run-tests` flag.

3. **Per-file routing's language-hint mapping is minimal.** Initial mapping covers `.rb` (and friends) → ruby; `.py` → python; everything else → unhandled. Modern Rails apps include `.js`/`.ts` (Webpacker/esbuild), `.scss`/`.css`, `.haml`/`.slim` templates, `.json`/`.yml` configs. Cycle 3's job is the **routing extension shape**, not a comprehensive language hint table. Cycle 4 + later cycles extend.

4. **Slice-and-swarm slicing strategy is heuristic.** Per-Rails-idiom-domain partitioning is a reasonable default but isn't load-aware (a `app/models/` cluster with 200 model files dwarfs a `db/migrate/` cohort with 5 migrations). Cycle 4+ may add load-aware re-balancing. Cycle 3's strategy meets master plan AC.RAILS.4 ("aggregator merges") + works for SaaS-app scale up to ~10MB Ruby code.

5. **HYPOTHESISED ACs are deduplicable across slices but not de-duplicable across runs.** If the same heuristic pattern fires on the same file in two runs, the resulting `ac_id` is deterministic (slug-derived) so cross-run dedup happens via the existing `ac_id` lexicographic sort. But the **rationale** field re-derives the heuristic provenance string each run; if the heuristic changes (Cycle 4 swap to LLM), prior runs' rationale strings drift. Surfaced in `odd-methodology.md` as "rationale provenance changes when the inference engine changes; ratification is the cross-version reconciliation point."

6. **The synthetic Rails fixture is not a Rails app.** It's a structural fixture designed to exercise recognizers; running `bundle install + rspec` against it would fail (no real `application.rb`, no `database.yml`, no test helpers). The fixture's README explicitly labels this. Cycle 4's canonical fixture is the runnable-Rails surface.

7. **Tree-sitter Ruby grammar version-pinning matters.** `tree-sitter-ruby>=0.23` is the floor; minor version bumps may add new syntax (Rails 8 syntax, Ruby 3.4 features). The pyproject's lower bound is `>=0.23`; an upper bound is intentionally NOT set (tree-sitter follows semver loosely; pinning would brick on routine updates). Cycle 4+ may add a tested-against version map if compatibility breakage emerges.

8. **`recognizer_finding` audit-log entry adds D6 surface.** Cycle 3 adds a new `event_kind` (`recognizer_finding`) that doesn't exist in Cycle 1 + 2. Schema is unchanged (existing fields accommodate); the new event_kind is documented but not enforced as enum (the `event_kind: str` field is a string). RF: should we tighten event_kind to a Literal enum at construction time? Cycle 3 keeps it loose to avoid breaking Cycle 2's ratification_* extension pattern; tightening is a separate amendment cleanup if needed.

9. **`ac_id` derivation must be globally unique across slices.** The slug-based derivation (`f"AC.RAILS.<idiom>.{slug}"`) uses local context (file basename + AST node identifier). Cross-slice collisions are possible if two slices both contain a model named `Payment` (e.g., one in `app/models/` and one in `app/models/legacy/`). Slugs are extended with file-relative-path suffix to mitigate (`f"AC.RAILS.active_record.payment.app__models__legacy"`); the aggregator's `ac_id` dedup logs `slice_aggregate_dedup` for any actual collisions.

10. **No real LLM means HYPOTHESISED ACs are bounded by hand-authored heuristics.** Cycle 3's HYPOTHESISED ACs are reasonable proxies for what an LLM would emit, but the diversity of HYPOTHESISED inferences is intentionally narrow. Cycle 4+ (or v0.1.9) is where LLM-driven inference enters; ratification flow is the safety net regardless (HYPOTHESISED → user review → promote/demote/edit/reject). The contract is right; the inference engine is a swappable component.

---

## §11 — Provenance trail

- v0.1.6 production-safety + cost-governance — sealed at `3f1d237` + `88674cb`. Provides `dry_run_estimate` + `BudgetEnvelope`.
- v0.1.7 per-project-pm + layered-skill discovery — sealed at `3aa20dd` + `73505f0` + `bcf699a` + `122a7c8`. Indirectly used via Cycle 2's ratification flow.
- Dev-pattern-simplifications #1 + #2 (manifest schema v3 + seal-narrative compression) — sealed at `019cfca` + `df3f50f`.
- v0.1.8 master plan — sealed at `1c2c478`.
- v0.1.8 Cycle 1 — sealed at `c1abda1`. Provides scaffold + adapter Protocol + audit-log primitive.
- v0.1.8 Cycle 2 — sealed at `4865028`. Provides `BandedAC` + `Evidence` + `ConfidenceBand` + ratification.
- ODD-RE research — `<pos3>/.scratch/claude-output/odd-reverse-engineering-skill-research.md` (907 lines). D-Q.RE.{1..8} sub-decisions; tree-sitter as AST library; aider-style repomap as slicer reference (§3.4).
- Lens 5 (swarming) — `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md`.
- Smoke-test-discipline at `plugins/dev-sdlc/docs/smoke-test-discipline.md` — six dimensions; D2/D3/D4 marked n/a per quick-reference card §6.
- ODD-methodology at `plugins/dev-sdlc/docs/odd-methodology.md` — Cycle 2 added §11 (confidence bands); Cycle 3 adds §12 (per-language adapter conventions).
- Eric synthesis Decision O — Ruby first-class +8–16 h adder; this cycle delivers it.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Per AC.D-sa.7, every plan-doc that selects non-default methods records the decision + rationale. This cycle's method-level decisions:

| Decision | Choice | Rationale |
|---|---|---|
| AST library | tree-sitter via Python bindings (`tree_sitter` + `tree_sitter_ruby`) | ODD-RE research §3 explicitly identified tree-sitter as the right tool; pre-compiled wheels (no native compile); deterministic; multi-language (Python adapter Cycle 4 can use the same wrapper pattern). |
| Recognizer module split | One file per Rails idiom (8 modules under `recognizers/`) | Per-idiom AC granularity (Lens 5 stopping criterion); per-recognizer test files; Cycle-3.x amendments can tighten one recognizer at a time. |
| Slicing strategy | Per-Rails-idiom-domain partitioning when over budget | Natural Rails partitioning axis; per-slice deterministic processing; cross-slice dedup handles edge cases. |
| Test-first granularity | Per-`it`-block (RSpec) + per-`test '...'`-block / `def test_<name>` (Minitest) | Matches Eric Decision G1; test-name-as-AC-name; one decision per test at ratification. |
| HYPOTHESISED inference | Heuristic-shaped (no LLM in Cycle 3) | LLM integration adds non-trivial cost-governance complexity; heuristic preserves the band semantics; Cycle 4+ swaps in LLM under the same rationale-required contract. |
| repo_sha resolution | Subprocess shell to `git rev-parse HEAD` | Universal availability; matches loam-amend precedent; no Python git library dep. |
| tree-sitter dep declaration | Required (not optional/extra); lazy-imported at first use | Honest dep declaration; pre-compiled wheels mean install-time cost is small; lazy import preserves "import is cheap" property. |
| Per-file routing extension | Extend Cycle 1's `analyze.py` with language-hint mapping | Smallest extension that supports multi-adapter codebases (Rails repos contain JS, ERB, etc.); non-breaking with one adapter or zero. |
| Aggregator order | Lexicographic sort by `ac_id` | D2 idempotency requires byte-identical artefacts; lexicographic sort gives that property. |
| Synthetic fixture vs canonical | Synthetic in Cycle 3; canonical in Cycle 4 | Synthetic suffices for adapter-shape verification; canonical is release-level smoke surface. |

---

## §13 — Acceptance gate

This plan-doc is gate-ready when:

1. All 8 AC.RAILS.* families named with explicit pytest paths (§4) — done.
2. Single-component fence named (§3) — done.
3. All 6 smoke dimensions addressed — applicable exercised, n/a documented (§6) — done.
4. Halt triggers named (§8) — done.
5. Bookkeeping path named (§9) — done.
6. F2 gaps named (§10) — done.
7. Method-decision record named per AC.D-sa.7 (§14) — done.

Build proceeds.
