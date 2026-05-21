# v0.1.8 Cycle 4b — canonical Ruby-Rails fixture + Ruby e2e ratification + DRY refactor

**Status:** plan-author phase — sub-plan authored 2026-05-04, predecessor: Cycle 4a sealed at `67dd302`.

This is the **residue cycle** spawned when Cycle 4a's plan-author phase split per master plan §7.9 + the in-flight halt-trigger. Cycle 4a shipped the JS/TS/Playwright adapter + the `jsts-playwright-app` fixture + JsTs e2e smoke + the JsTs portion of AC.FIXTURES.3. Cycle 4b ships the residue: **canonical `ruby-rails-payment` fixture (AC.FIXTURES.2) + Ruby e2e ratification (AC.FIXTURES.4 ruby-portion) + LICENSE (AC.FIXTURES.5 ruby-portion) + DRY refactor of repo_sha/slugify/heuristic-inference patterns into `lang/_common/` (RF surfaced in 4a §10 #6).**

The cycle is fixture-heavy (no new adapter code, no new recognizers); the only `src/` edits are the move-only DRY refactor. Refactor must be byte-behaviour-preserving — verified by all 304 odd-extractor tests (Cycle 1+2+3+4a) remaining green post-refactor.

---

## §0 — Scope decision (autonomous, F2 surface)

**Decision (no halt — authorized by Cycle 4a §0 + master plan §7.9):** Cycle 4b's scope is the **fixture-heavy residue from Cycle 4a + the DRY refactor surfaced in 4a §10 RF #6**. No new adapter code; no new recognizers; no schema churn. The refactor relocates duplicated symbols (`repo_sha.resolve_repo_sha`, `_ast_utils.slugify`, `_ast_utils.file_slug`, possibly `slicer.SliceDriftError`) from `lang/ruby/` and `lang/jsts/` into `lang/_common/`, with both adapters importing from the new common subpackage.

**Rationale:** Cycle 4a shipped 99 new tests across 304 total; Cycle 4b's surface is ~1.5× simpler (canonical Ruby fixture + e2e mirror + ≤200-line move-only refactor + ≤25 new tests). Cycle 4a's wall-clock came in well under the 10h halt-trigger; Cycle 4b's predicted band is **4–8 hours**.

**Independent fence:** single-component fence on `plugins/dev-sdlc/odd-extractor/` (same as Cycle 3 + Cycle 4a). No edits to `framework/`. No edits to other plugins.

---

## §1 — Outcome shape (the "why")

**Pin:** Eric's release-level smoke (path 2 — Rails-payment) lands against a canonical fixture that exercises the Ruby adapter at SaaS-app scale (5–10 routes, ActiveRecord with callbacks/concerns/polymorphic, Sidekiq, ≥10 RSpec tests, README, LICENSE) — distinct from Cycle 3's intentionally-thin synthetic Rails fixture (which is enough for adapter unit-shape testing but not for release-gate smoke).

**Pin:** The Ruby end-to-end ratification path (`extractor → ratification batch → audit log`) is exercised end-to-end on the canonical fixture in the same shape as Cycle 4a's JsTs e2e ratification + AC.FIXTURES.3 — symmetry across Eric's two project paths (path 1 = JsTs / first project; path 2 = Rails / itsacheckmate.com first-party ordering / second project).

**Pin:** The cross-language DRY surface flagged in Cycle 4a RF §10 #6 is closed BEFORE Cycle 5 ships, so the language-adapter prior art (the patterns Cycle 5+ amendments will reuse) is the consolidated `_common/` shape — not the local-copy precedent. Behaviour preservation verified by 304-test green sweep.

**Pin:** Master plan §3 Cycle 4 ACs that Cycle 4a deferred — AC.FIXTURES.{2, 3-ruby, 4, 5-ruby} — all close in this cycle. After 4b seals, the v0.1.8 release-level smoke gate (§5 in master plan) is unblocked: Cycle 5 (6 SKILLs) is the only remaining cycle before release-level smoke runs.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

The Ruby adapter (Cycle 3) + ratification machinery (Cycle 2) + JsTs adapter (Cycle 4a) all exist; this cycle composes on top — no new Claude capability is leveraged. The fixture shape exposes the persona-mediated extractor flow (Eric's natural surface): `loam odd-extract tests/fixtures/ruby-rails-payment/` → banded contract → `loam odd-extract ratify` → audit-logged decisions. The DRY refactor uses no Claude primitive (it's pure Python module reorganization).

### Lens 2 — Harness + primary-persona value

**Primary-persona test:** the canonical fixture is the artefact Eric's persona will encounter when the v0.1.8 release-gate smoke runs against a Rails-payment-shape codebase; richer fixture = richer band distribution = more representative extraction → less translation burden when Eric is asked to ratify. **PASS.**

**Harness test:** the DRY refactor adds NOTHING new to the toolkit — it consolidates existing toolkit. Persona doesn't gain a new primitive, but Cycle 5+ amendments (and any future language adapter) inherit a cleaner reuse surface. **PASS — secondary.** The fixture itself adds a load-bearing test surface for Cycle 5 + release-level smoke. **PASS — primary.**

### Lens 3 — ODD authoring

Every line maps to a named AC in §4 below. AC.FIXTURES.{2, 3-ruby, 4-ruby, 5-ruby} + AC.DRY.{1,2,3,4} (named-locally for the refactor); test paths explicit; method-decision record §14 lists the few non-default decisions.

### Lens 4 — Prompt scope ↔ confidence

**Confidence in outcome shape:** HIGH for the fixture (Cycle 3's synthetic-rails has the structure; the canonical fixture is "same shape, fuller content + LICENSE + ≥10 RSpec tests"); HIGH for the e2e mirror test (Cycle 3's `test_AC_RAILS_5_eric_ratification_pin.py` is the structural reference); HIGH for the DRY refactor (the duplicated symbols are byte-identical or near-byte-identical; relocation pattern is mechanical).

**Scope tightness:** TIGHT. Each AC names a specific test path; the refactor surface is enumerated symbol-by-symbol; the fixture file count is bounded (12–25 files, mirroring synthetic-rails' shape). Method-level decisions (RSpec test names, model field choices, auth pattern, polymorphic association choice) remain the builder's call.

**Failure-mode guard:** the over-tight risk is "the canonical fixture grows beyond the 5–10-route bound and exceeds the 8h ceiling"; the §8 halt-trigger at 3h-of-fixture-authoring catches this. The over-loose risk is "the DRY refactor scope creeps into a redesign of the slicer or a rewrite of `_ast_utils`"; AC.DRY scope explicitly enumerates the moved symbols and excludes the slicer's `aggregate_slice_results` (kept inside `lang/ruby/slicer.py` since it's already cross-language-shared via import).

### Lens 5 — Swarming

**Decomposition assessment:** the cycle has TWO loosely-coupled work streams:

1. **Fixture authoring** (canonical ruby-rails-payment) — sequential within itself; no decomposition gain (the parts are interdependent — README references files; Gemfile references gems; specs reference models).
2. **DRY refactor** — sequential within itself; small enough scope (~150-line move) that decomposition adds only coordination overhead.

**Stopping criterion met.** Single-agent serial execution is correct shape; further decomposition introduces only coordination overhead without tightening any subtask's AC. (Cycle 4a's plan-doc made the same call for the same reasons — fixture + adapter cycles are inherently intertwined when the fixture is the verification target for the adapter changes.)

**`max_planner_depth` not invoked.** No sub-planning required.

---

## §3 — Single-component fence

**Component fence (manifest names this exactly):**

- `plugins/dev-sdlc/odd-extractor/` — single component; canonical `ruby-rails-payment` fixture lands here under `tests/fixtures/`; the DRY refactor moves symbols inside `src/loam_odd_extractor/lang/`.

**Universal admissions:**

- `docs/plans/` — the plan-doc paper trail.
- `plugins/dev-sdlc/docs/odd-methodology.md` — §13 already extant from Cycle 4a (per-language conventions JS/TS); Cycle 4b adds a small note mentioning `lang/_common/` as the canonical shared-symbol home for future adapters.

**Cross-component edits:** NONE. No edits to `framework/`, `personas/`, other plugins, or root-level paths.

**Plan-doc + manifest live at:**

- Plan-doc: `docs/plans/v0-1-8-cycle-4b-ruby-fixture-and-dry-refactor.md` (this file).
- Manifest: `docs/plans/v0-1-8-cycle-4b-ruby-fixture-and-dry-refactor.manifest.yaml` (schema v3 — `plan_doc_ref` + `ac_count` + `smoke_outcome`).

---

## §4 — AC family — `AC.FIXTURES.*` (Ruby portion) + `AC.DRY.*` (locked for 4b)

Each AC has at least one explicit pytest under `plugins/dev-sdlc/odd-extractor/tests/lang/ruby/` (fixture + e2e ACs) or `plugins/dev-sdlc/odd-extractor/tests/lang/_common/` (DRY ACs). ODD §2.5 — every line of code, every branch, every test maps to a named AC.

### AC.FIXTURES.2 — canonical `ruby-rails-payment` realistic fixture

- `plugins/dev-sdlc/odd-extractor/tests/fixtures/ruby-rails-payment/` is committed real files matching the master plan AC.FIXTURES.2 shape:
  - **Routes:** `config/routes.rb` declares 5–10 RESTful routes (e.g., `resources :payments`, `resources :customers`, `resources :webhooks`, `resources :sessions`); namespaced under `:api` for realism.
  - **ActiveRecord models:** `app/models/payment.rb`, `app/models/customer.rb`, `app/models/webhook_event.rb` — at minimum:
    - **Callbacks:** `before_save`, `after_create`, `before_validation` on at least one model (different lifecycles).
    - **Concerns:** `app/models/concerns/auditable.rb` AND `app/models/concerns/timestampable.rb` (or similar pair); each concern `extend ActiveSupport::Concern` and `included do ... end`.
    - **Polymorphic association:** at least one `belongs_to :owner, polymorphic: true` declaration (e.g., webhook_event polymorphic on payment/customer/refund).
    - **Validations:** `validates :foo, presence: true`, `validates :bar, uniqueness: true` (≥3 validations across models — drives heuristic-inference HYPOTHESISED ACs).
  - **Sidekiq jobs:** at least 2 jobs under `app/jobs/`:
    - `app/jobs/process_payment_job.rb` — `include Sidekiq::Job`; performs payment processing.
    - `app/jobs/payment_webhook_dispatcher_job.rb` — Sidekiq fan-out pattern.
  - **Controllers:** `app/controllers/payments_controller.rb`, `app/controllers/customers_controller.rb`, `app/controllers/webhooks_controller.rb` — each controller has 3–5 RESTful actions with strong-params + before-actions.
  - **Migrations:** `db/migrate/<ts>_create_payments.rb`, `db/migrate/<ts>_create_customers.rb`, `db/migrate/<ts>_create_webhook_events.rb` — declare schema with fk + index hints.
  - **RSpec tests:** ≥10 RSpec specs under `spec/` covering models + controllers + jobs:
    - `spec/models/payment_spec.rb` — ≥3 `it` blocks (validations, callbacks, polymorphic).
    - `spec/models/customer_spec.rb` — ≥2 `it` blocks.
    - `spec/models/webhook_event_spec.rb` — ≥2 `it` blocks (polymorphic association).
    - `spec/jobs/process_payment_job_spec.rb` — ≥2 `it` blocks.
    - `spec/controllers/payments_controller_spec.rb` — ≥1 `it` block.
    - Total: **≥10 RSpec `it` blocks** across the fixture (the AC.FIXTURES.2 floor).
  - **`Gemfile`** — declares `rails`, `rspec-rails`, `sidekiq`, `pg`, `bcrypt`, `devise` (or similar real-world Rails-payment gem set).
  - **`README.md`** — explains the fixture; **clearly labelled SYNTHETIC** (banner: "This is a SYNTHETIC fixture for testing the loam odd-extractor's Ruby/Rails adapter against a Rails-payment-shape codebase. Not a real payment processor."); brief description of each model + each job + each route domain.
  - **`LICENSE`** — permissive (MIT or Apache-2.0; choose MIT to match loam-odd-extractor's parent license shape — verify at build time).
- The fixture is committed as **real files** (not a fixture-builder script) so byte-identical extractions across runs are testable. Distinct from `synthetic-rails` (Cycle 3's intentionally-thin one-controller fixture); both fixtures continue to coexist.
- **Test:** `tests/lang/ruby/test_AC_FIXTURES_2_ruby_rails_payment_fixture_shape.py` — fixture file count ≥ 18; named files exist (controllers, models, jobs, specs, migrations, README, LICENSE, Gemfile, routes.rb); `Gemfile` is parseable text (declares rails, rspec, sidekiq); README contains the SYNTHETIC banner; LICENSE is non-empty + recognisable header (MIT/Apache-2.0); `spec/` directory contains ≥ 10 `it ` occurrences across files.

### AC.FIXTURES.3 (ruby-only portion) — End-to-end smoke band distribution against canonical fixture

- `loam odd-extract tests/fixtures/ruby-rails-payment` produces a confidence-banded contract draft.
- Band distribution sanity-checks: ≥3 VERIFIED, ≥5 PLAUSIBLE, ≥2 HYPOTHESISED for the canonical Ruby fixture (mirror of Cycle 4a's same AC against the JsTs fixture).
- The contract draft parses as markdown with the banded-AC table populated (Cycle 2's `<!-- ACS_TABLE_HERE -->` injection).
- `RawACs.acs` round-trips through `BandedAC.model_validate()` for every entry.
- Exit status 0.
- **Test:** `tests/lang/ruby/test_AC_FIXTURES_3_ruby_e2e_band_distribution.py` — runs the four-stage workflow end-to-end against the canonical fixture in live mode (with budget override since the fixture is small); asserts band counts at the AC.FIXTURES.3 floors; asserts contract draft markdown shape.

### AC.FIXTURES.4 (ruby-only portion) — Eric-ratification end-to-end pin against canonical Ruby fixture

- `extract_rails_acs(repo=ruby_rails_payment_repo)` produces `RawACs` whose `acs` round-trip through `BandedAC.model_validate()`.
- The resulting `BandedAC` list is consumable by Cycle 2's `enqueue_ratification_batch(extraction_id, banded_acs, workspace_root, pm_runtime, pm_handle, draft_path)` at the structural-shape level (the contract pin — same shape as Cycle 3's `test_AC_RAILS_5_eric_ratification_pin.py`).
- Test name + file path + repo SHA captured as evidence on every VERIFIED AC.
- **Test:** `tests/lang/ruby/test_AC_FIXTURES_4_ruby_ratification_pin.py` — three test functions matching Cycle 3's `test_AC_RAILS_5_eric_ratification_pin.py` shape, run against the canonical fixture instead of the synthetic:
  - `test_canonical_adapter_output_round_trips_through_banded_ac` — every dict round-trips.
  - `test_canonical_adapter_output_meets_master_plan_band_distribution` — same band-distribution asserts as AC.FIXTURES.3 (overlap is intentional; the existing Cycle 3 test is fixture-bound to synthetic-rails).
  - `test_canonical_adapter_output_consumable_by_ratification_batch` — same `inspect.signature(...)`-based contract-shape assertion as Cycle 3's test.

### AC.FIXTURES.5 (ruby-only portion) — Both fixtures committed real repos with permissive LICENSE

- `tests/fixtures/ruby-rails-payment/LICENSE` exists; non-empty; recognisable as MIT or Apache-2.0 (header pattern match).
- `tests/fixtures/jsts-playwright-app/LICENSE` exists (Cycle 4a satisfied this if a LICENSE file shipped; if not, this AC pulls in the JsTs LICENSE addition as a follow-on).
- Both fixtures are real committed file trees (NOT git submodules; not generated-by-script).
- **Test:** `tests/test_AC_FIXTURES_5_both_fixtures_have_license.py` — both fixtures have a `LICENSE` file at their root; both are non-empty; both contain a recognisable license header (MIT-pattern: "Permission is hereby granted, free of charge..."; Apache-pattern: "Apache License" + "Version 2.0").
- **Note:** Cycle 4a may not have shipped `jsts-playwright-app/LICENSE`. If the file is missing on the 4a HEAD, the build agent ADDS it (MIT) under the same fence — this is universal-admissions-friendly since both fixtures live under the single-component fence's prefix.

### AC.DRY.1 — `_common/` subpackage exists with shared `repo_sha`

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/_common/__init__.py` exists; module is importable as `loam_odd_extractor.lang._common`.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/_common/repo_sha.py` exposes `resolve_repo_sha(repo_path: Path) -> str | None` with the SAME function body as `lang/ruby/repo_sha.resolve_repo_sha` (which is byte-equivalent to `lang/jsts/repo_sha.resolve_repo_sha` modulo docstring).
- `lang/ruby/adapter.py` and `lang/jsts/adapter.py` import `resolve_repo_sha` from `..\\_common.repo_sha` (relative import).
- The OLD per-adapter `lang/ruby/repo_sha.py` and `lang/jsts/repo_sha.py` files are **DELETED** (not re-exports — outright removed; the import path is the single source of truth via `lang._common`).
- **Test:** `tests/lang/_common/test_AC_DRY_1_repo_sha_common.py` — `from loam_odd_extractor.lang._common.repo_sha import resolve_repo_sha` works; the function returns the expected SHA for a tmp git repo (mirror of Cycle 3's existing `repo_sha`-related test); `lang/ruby/repo_sha.py` and `lang/jsts/repo_sha.py` files do NOT exist (verify via `Path(__file__).parent.parent.parent.parent / "src" / "loam_odd_extractor" / "lang" / "ruby" / "repo_sha.py"` is `not exists()`).

### AC.DRY.2 — `_common/` exposes shared `slugify` + `file_slug` helpers

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/_common/slugs.py` exposes:
  - `slugify(text: str) -> str` — same body as `lang/ruby/_ast_utils.slugify` (byte-identical to `lang/jsts/_ast_utils.slugify` modulo docstring).
  - `file_slug(file_path: Path, repo_root: Path) -> str` — same body as the existing `_ast_utils.file_slug`.
- `lang/ruby/_ast_utils.py` and `lang/jsts/_ast_utils.py` no longer DEFINE `slugify` or `file_slug`; they re-export them: `from .._common.slugs import slugify, file_slug`. (The re-export form is necessary because dozens of recognizer modules currently import via `from .._ast_utils import slugify, file_slug`; re-exporting at `_ast_utils` preserves all those import sites without churn — call this DRY-with-compat-shim. AC.DRY.4 below decides whether to ALSO migrate the recognizer import sites in this cycle or leave them on the compat shim. Cycle 4b plan-author decision: **migrate** — see AC.DRY.4.)
- **Test:** `tests/lang/_common/test_AC_DRY_2_slugs_common.py` — `from loam_odd_extractor.lang._common.slugs import slugify, file_slug` works; both functions produce identical output to a frozen list of pre-refactor inputs (regression-pin against the local copies); `lang/ruby/_ast_utils.slugify is lang/_common.slugs.slugify` (re-export identity check) AND `lang/jsts/_ast_utils.slugify is lang/_common.slugs.slugify`.

### AC.DRY.3 — Heuristic-inference rationale-string pattern uses shared helper

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/_common/heuristic_helpers.py` exposes `make_inferred_banded_ac(ac_id, text, source_ac, heuristic_name, backing_files=None) -> BandedAC` — the canonical constructor for HYPOTHESISED-band ACs derived from a source PLAUSIBLE AC. Body:
  - Constructs `BandedAC(ac_id=ac_id, text=text, confidence=ConfidenceBand.HYPOTHESISED, evidence=Evidence(kind="inference", citations=list(source_ac.evidence.citations) if source_ac.evidence and source_ac.evidence.citations else [], rationale=f"<heuristic_name>: derived from {source_ac.ac_id}"), backing_files=backing_files or list(source_ac.backing_files))`.
  - The exact rationale string format ships in the helper; per-language `heuristic_inferences.py` modules call it instead of hand-constructing `Evidence(kind="inference", ...)`.
- `lang/ruby/heuristic_inferences.py` and `lang/jsts/heuristic_inferences.py` are refactored to call `make_inferred_banded_ac(...)` for every HYPOTHESISED AC they emit. The structural pattern (`BandedAC(...)` with hand-rolled `Evidence(kind="inference", ...)`) is GONE from both files.
- The PER-LANGUAGE files retain their language-specific regex tables + heuristic logic — only the boilerplate constructor pattern moves to `_common/`.
- **Test:** `tests/lang/_common/test_AC_DRY_3_heuristic_helpers_common.py` — `make_inferred_banded_ac()` constructs a valid HYPOTHESISED `BandedAC`; the rationale string contains the heuristic name + source ac_id; running `infer_domain_rules()` on a Ruby + a JsTs PLAUSIBLE AC list both produce HYPOTHESISED ACs with the helper's rationale-string format.

### AC.DRY.4 — Recognizer import sites migrated to `_common/`

- All recognizer modules under `lang/ruby/recognizers/` and `lang/jsts/recognizers/` that currently import `slugify` or `file_slug` from `.._ast_utils` are migrated to import from `.._common.slugs` directly (the compat shim at `_ast_utils` continues to re-export, but new code is on the canonical path).
- The shim in `_ast_utils.py` is retained to avoid breaking external code (none exists yet, but the re-export costs nothing); a comment marks it as a compat shim.
- **Test:** `tests/lang/_common/test_AC_DRY_4_import_sites_migrated.py` — grep-style verification: every `lang/ruby/recognizers/*.py` and `lang/jsts/recognizers/*.py` file that imports `slugify` does so from `.._common.slugs` (not from `.._ast_utils`); the count matches the pre-refactor count (no recognizer dropped its import); no `lang/{ruby,jsts}/recognizers/` file imports `slugify` from `.._ast_utils` anymore.

**Out of scope for AC.DRY:**

- `SliceDriftError` + `aggregate_slice_results` are NOT relocated. The current Cycle 4a state already cross-imports them from `lang/ruby/slicer.py` (the JsTs `slicer.py` re-exports rather than duplicates). Moving them to `_common/` would be a separate refactor; the dispatch's "possibly relocate to `_common/` for symmetry" is **declined** for Cycle 4b — the current shape (one canonical home + one re-exporter) is already DRY. Surfaced in §10 RF.
- The slicer's `aggregate_slice_results` parameterisation (per Cycle 4a §10 RF #6 last sentence) is NOT pursued — that would be a structural refactor, not a behaviour-preserving move.
- Test-runner detection helpers (Cycle 4a) are language-specific and NOT consolidated.
- Per-language heuristic regex tables remain per-language.

---

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

### Surface #1 — `_common/` subpackage path choice (no halt — recorded)

**Choice:** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/_common/` (leading underscore to mark as private/internal-to-the-lang-subtree).

**Alternatives considered:** `lang/shared/` (less idiomatic — `_common/` is the Python convention for shared internals), `lang_common/` (a sibling of `lang/`, breaks the locality), inlining into `loam_odd_extractor/_lang_common.py` (top-level — too distant from the per-language code that uses it). **`_common/` chosen.**

### Surface #2 — Compat shim retention at `_ast_utils.slugify` re-export (no halt — recorded)

**Choice:** retain the re-export at `lang/{ruby,jsts}/_ast_utils.py` (just `from .._common.slugs import slugify, file_slug` at module top). The re-export costs ~2 lines per adapter and prevents external code (any future tool/test importing from `_ast_utils`) from breaking.

**Alternative:** delete the re-export and force everyone to import from `_common`. **Rejected** — symmetry with the dispatch's "behaviour-preserving" rule; external symbol surface (even within tests) is preserved.

### Surface #3 — Recognizer import-site migration vs leave-on-shim (no halt — recorded)

**Choice:** **migrate** all recognizer import sites to `_common/` directly (AC.DRY.4). Avoids confusion about whether `_ast_utils` or `_common` is the canonical home; the shim is only there for forward-compat with hypothetical external imports.

**Alternative:** leave recognizers on the shim. **Rejected** — establishes a "use the canonical path going forward" precedent for Cycle 5+ amendments.

### Surface #4 — Heuristic-helper boundary (no halt — recorded)

**Choice:** ONLY the `make_inferred_banded_ac()` constructor moves to `_common/`. Per-language regex tables, the `infer_domain_rules()` orchestration, and the heuristic-firing logic all stay in `lang/{ruby,jsts}/heuristic_inferences.py`. Avoids over-abstraction (the heuristic regexes are deeply language-specific).

**Alternative:** factor out a generic `apply_heuristics(ac_list, heuristic_table)` orchestrator. **Rejected** — would obscure per-language readability for a small line-count win.

### Surface #5 — `SliceDriftError` + `aggregate_slice_results` location (no halt — recorded)

**Choice:** **leave them where they are.** Current state: defined in `lang/ruby/slicer.py`, re-exported via `from .ruby.slicer import SliceDriftError, aggregate_slice_results` in `lang/jsts/slicer.py`. This is already DRY — one canonical home + one re-exporter. Moving them to `_common/` would require updating both adapters AND ensures cross-language semantic alignment that the existing pattern already provides.

**Alternative:** move both to `_common/slicer.py`. **Rejected** — the dispatch's "possibly relocate for symmetry" is qualifier-language; the current shape is sufficient. Surfaced in §10 RF as a follow-up.

### Surface #6 — Canonical Ruby fixture authoring strategy (no halt — recorded)

**Choice:** **author from scratch** (real Rails idioms, real-shaped models + concerns + jobs + specs); not generated from a script. Mirrors Cycle 4a's `jsts-playwright-app` shape (real committed files). The synthetic-rails fixture (Cycle 3) is retained alongside — the canonical fixture has DIFFERENT content (richer surface) but co-exists.

**Alternative:** copy synthetic-rails + extend. **Rejected** — synthetic-rails is intentionally minimal; the canonical fixture's structure is different (5–10 routes vs 1 controller, 3+ models vs 1, ≥10 RSpec tests vs ~5). Authoring from scratch is cleaner.

### Surface #7 — RSpec test count floor — exactly ≥10 vs richer (no halt — recorded)

**Choice:** ≥10 `it` blocks **floor** (the master plan AC.FIXTURES.2 floor). Aim for 10–15 (richer than synthetic-rails' 4–5 spec blocks but bounded so the cycle doesn't sprawl into "build a real app"). Distribution: ~5 model specs + ~3 controller specs + ~2 job specs.

**Alternative:** 20+ specs for richer band distribution. **Rejected** — diminishing returns vs cycle wall-clock; AC.FIXTURES.3 (band distribution ≥3 VERIFIED) requires a small floor only.

### Surface #8 — Polymorphic association choice (no halt — recorded)

**Choice:** `webhook_event` polymorphic on `payment` / `customer` / `refund` (a plausible payment-domain shape — webhooks emitted for events on multiple resource types). Mirrors a common Rails-payment pattern.

**Alternative:** notification polymorphic on user/order/etc. **Rejected** — webhook polymorphism is more Rails-payment-specific.

### Surface #9 — Sidekiq concurrency / sidekiq-pro features (no halt — recorded)

**Choice:** plain Sidekiq with `include Sidekiq::Job` (the modern API; Sidekiq 7+); no Sidekiq Pro features (paid). The `Gemfile` declares the OSS `sidekiq` gem.

**Alternative:** ActiveJob abstraction. **Rejected** — Sidekiq is the master plan AC.FIXTURES.2 explicit shape ("Sidekiq job").

### Surface #10 — Devise vs hand-rolled auth (no halt — recorded)

**Choice:** `bcrypt` + `has_secure_password` (Rails built-in) — no Devise. Smaller fixture surface; Devise adds significant complexity (controllers + views) that doesn't drive band-distribution outcome.

**Alternative:** Devise. **Rejected** — out of proportion for a smoke fixture.

### Surface #11 — LICENSE choice (MIT vs Apache-2.0) (no halt — recorded)

**Choice:** **Apache-2.0** for both fixtures' LICENSE (canonical Ruby AND JsTs). Verified at plan-author 2026-05-04 — `/Users/lukeivers/ivers-corp-pos-v2/LICENSE` is Apache 2.0; both fixture LICENSEs match parent.

**Alternative:** MIT. **Rejected** — match parent's permissive choice for consistency.

### Surface #12 — JsTs LICENSE remediation (no halt — recorded; pre-author verified)

**Status (verified 2026-05-04):** `tests/fixtures/jsts-playwright-app/LICENSE` does NOT exist on Cycle 4a HEAD `67dd302`. Cycle 4b adds it (Apache-2.0) under the same fence as the Ruby fixture LICENSE — universal-admissions-friendly (same component prefix). AC.FIXTURES.5 closes BOTH portions in 4b (not just Ruby).

**Alternative:** defer to a follow-on amendment. **Rejected** — AC.FIXTURES.5 names BOTH fixtures explicitly; Cycle 4b is the close-out.

### Surface #13 — Cycle 4b plan-doc references jsts-playwright-app fixture verification (no halt — recorded)

**Choice:** Cycle 4b's plan-doc does NOT alter Cycle 4a's tests against the JsTs fixture; the only JsTs-touching work in 4b is (a) the optional LICENSE addition (AC.FIXTURES.5) and (b) the recognizer import-site migration (AC.DRY.4). Both are additive/non-behavioural.

**Alternative:** also enrich the JsTs fixture's RSpec-equivalent surface. **Out of scope** — Cycle 4a closed AC.FIXTURES.1 + AC.FIXTURES.3 (jsts-only) at seal.

---

## §6 — Smoke (REALISTIC CONDITION — all 6 dimensions per smoke-test-discipline.md §6 + dispatch's explicit naming)

### D1 — cold-state (fresh canonical workspace + canonical Ruby fixture)

- **Scope:** fresh tmp workspace; canonical `ruby-rails-payment` fixture; full `loam odd-extract` four-stage workflow runs end-to-end against the fixture; produces banded contract draft with band-tagged AC table (Cycle 2's `<!-- ACS_TABLE_HERE -->` injection); ≥3 VERIFIED + ≥5 PLAUSIBLE + ≥2 HYPOTHESISED (the AC.FIXTURES.3 ruby-portion floor).
- **Test:** `tests/lang/ruby/test_smoke_d1_cold_state_canonical.py` (NEW; mirrors Cycle 4a's `tests/lang/jsts/test_smoke_d1_cold_state.py` structure but bound to the canonical fixture, not synthetic-rails). One test function asserts non-empty banded contract; another asserts band-distribution floor.

### D2 — steady-state durability — IDEMPOTENCY VARIANT (n/a structurally for one-shot CLI; idempotency variant covered)

- **Scope:** 5 extractions byte-identical (modulo timestamps). Pre-refactor + post-refactor both byte-identical.
- **Test:** `tests/lang/ruby/test_smoke_d2_idempotency_canonical.py` (NEW; mirrors `synthetic-rails`-bound idempotency test against the canonical fixture). 5 runs; collected `ac_id`s match across runs; lexicographic ordering preserved; aggregate slice results (where applicable) deterministic.

### D3 — restart resilience (n/a)

- **Scope:** `loam odd-extract` is a one-shot CLI; no long-running process; no supervisor. Per smoke-test-discipline §6 — n/a; document only.

### D4 — reboot resilience (n/a)

- **Scope:** same as D3 — one-shot CLI. No persistent state daemon. n/a; document only.

### D5 — cross-session continuity

- **Scope:** partial extraction state survives subprocess boundary; resume completes remaining stages. Same shape as Cycle 4a's D5 against the JsTs fixture.
- **Test:** `tests/lang/ruby/test_smoke_d5_cross_session_canonical.py` (NEW; mirror of Cycle 4a's d5 test, bound to canonical Ruby fixture). Stage 1 (init) runs; subprocess exits; subprocess re-invokes; stages 2–4 complete; final contract draft is identical to a single-process extraction.

### D6 — telemetry floor

- **Scope:** full extraction writes `extraction_start` + 4× `stage_complete` + ≥1× `slice_complete` + ≥6× `recognizer_finding` + `extraction_end` audit-log entries against the canonical fixture; schema v1 preserved; filenames monotonic NNNN.yaml.
- **Test:** `tests/lang/ruby/test_smoke_d6_telemetry_floor_canonical.py` (NEW; mirror of Cycle 4a's d6 test, bound to canonical Ruby fixture).

### Plus: full-suite green sweep (the load-bearing DRY-refactor verification)

**The DRY refactor is supposed to be behaviour-preserving — every test that passed pre-refactor must still pass post-refactor.**

- Pre-refactor baseline (verified by plan-author 2026-05-04): **304 tests pass** in `plugins/dev-sdlc/odd-extractor/tests/`; **71 tests pass** in `plugins/dev-sdlc/tests/` (parent plugin smoke); total **375 tests** at canonical pos-v2 HEAD `67dd302` (Cycle 4a seal). With Cycle 4b's added tests (~25 new tests across AC.FIXTURES.2/3/4/5 + AC.DRY.{1..4}): post-refactor target ≥ **400 tests pass** (304 prior cycles + 71 parent + ~25 new).
- **Halt trigger:** if any prior-cycle test (Cycle 1+2+3+4a) regresses post-refactor → halt, surface, do NOT proceed; the refactor is invalid.
- **Verification step:** runs in build-time TWICE — once after each major batch (fixture authoring, then DRY refactor) and once at end-of-cycle.

---

## §7 — Out of scope (Cycle 4b)

- **No new adapter code** — Ruby + JsTs adapters land in Cycles 3 + 4a respectively. Cycle 4b only refactors imports.
- **No new recognizers** — recognizer surface is locked at the Cycle 3+4a shape.
- **No schema churn** — `BandedAC`, `Evidence`, `ConfidenceBand` are fixed at Cycle 2's shape.
- **No new heuristic regexes** — Cycle 4b refactors the helper, not the heuristics. (RF #1 — extending the heuristic list is Cycle 4c/5+ scope.)
- **No `SliceDriftError` / `aggregate_slice_results` move to `_common/`** — Surface #5; current shape is already DRY enough.
- **No Python adapter** — deferred to v0.2.2+.
- **No real OSS Rails-payment fixture** — release-gate (v0.2.1) scope.
- **No JS/TS/Playwright fixture changes** beyond the optional LICENSE addition.
- **No `framework/` edits.**
- **No release-tag push** — DO NOT push tags.
- **No Cycle 5 work** — independent at plan-author per master plan §3.
- **No `--run-tests` flag** — RF #2 mirror; deferred.

---

## §8 — Halt triggers (in-flight)

1. **WD drift.** Build agent's CWD must be `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). Halt + surface if drifted (e.g., into `/Users/lukeivers/pos3`).
2. **Prior-cycle test regression post-refactor.** Any of the 304 odd-extractor tests OR 71 dev-sdlc parent tests that passed at HEAD `67dd302` regress post-refactor → halt + surface; do NOT proceed; the refactor is invalid.
3. **Plan-doc not authored before code.** This plan-doc must exist on disk before any source-code edit. (Satisfied by this file's commit landing first.)
4. **AC.FIXTURES.2 fixture authoring exceeds 3 hours wall-clock.** Halt + surface; recommend simplifying fixture (drop one model, drop polymorphic, etc.).
5. **AC ships partial.** If any AC ships partial (e.g., DRY refactor migrates ruby but not jsts) → halt + reframe.
6. **DRY refactor causes import cycle / startup-time regression.** `import loam_odd_extractor` time post-refactor exceeds pre-refactor by >30% → halt + surface; lazy-import the new shared module if necessary.
7. **More than 5 in-build decisions need Luke escalation.** Halt + describe.
8. **Wall-clock exceeds 8 hours total.** Halt with partial findings.
9. **Band distribution fails sanity check.** Canonical fixture's extraction produces <3 VERIFIED, <5 PLAUSIBLE, OR <2 HYPOTHESISED → halt + RF the fixture content (extend heuristic-driving content) OR the schema.
10. **Existing Cycle 3 fixture (`synthetic-rails`) is mistakenly modified.** synthetic-rails is intentionally thin and Cycle 3-bound; Cycle 4b does NOT touch it. Halt + surface if any edit lands.
11. **ODD violations discovered in surrounding code** → halt + surface; do not silently extend.
12. **Manifest schema v3 not used / `--amend` flag used.** Halt; bookkeeping discipline is non-negotiable.

---

## §9 — Bookkeeping

Per `feedback_dispatch_explicit_pos_amend_apply` + `feedback_no_amend_in_agent_dispatches`:

- Source-edit feat commit lands FIRST (the canonical `ruby-rails-payment` fixture + DRY refactor + new tests).
- `loam amend apply --plan-doc <abs path>` lands the manifest+apply commit (single semantic commit per schema v3 AC.DPS1.6).
- `loam amend seal --plan-doc <abs path>` lands the deterministic short-form seal commit per AC.DPS2.{1,4,6}.
- `git commit --amend` is **forbidden** — if a file is missed, create a NEW corrective commit.
- Single-component manifest:
  - `name: dev-sdlc`
  - `seal_test: plugins/dev-sdlc/tests/test_no_sealed_amendments.py`
  - `sidecar: plugins/dev-sdlc/tests/SEAL_COMMIT`
  - `frozen_baseline: false`
  - `extra_allowed_prefixes: []`
- Universal admissions: `docs/plans/` + `plugins/dev-sdlc/docs/odd-methodology.md` (mirrors Cycle 4a).
- Backfill master plan §9 method-decision register Cycle 4b row with apply + seal SHAs (separate post-seal commit per Cycle 1–4a precedent).
- DO NOT push tags.

**Status file:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-cycle-4b-status-2026-05-04.md` — build agent writes per-AC status + smoke outcome + halt-and-surface findings here.

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **Canonical Ruby fixture is still synthetic** — clearly labelled, but it's an authored fixture, not a real public OSS Rails-payment app. Master plan §6 item 1 names a real OSS fixture as v0.2.1 release-gate scope; Cycle 4b's canonical fixture is the v0.1.8 release-level smoke surface (AC.FIXTURES.3) but NOT the v0.2.1 fresh-user smoke surface. Distinction recorded; release-gate dispatch still surfaces real-OSS-fixture selection.

2. **The DRY refactor's `make_inferred_banded_ac` helper assumes a uniform inference shape across languages.** Today: Ruby + JsTs heuristics both fit this shape (one PLAUSIBLE source AC → one HYPOTHESISED inferred AC). Future heuristics may want multi-source inference (combine 2+ PLAUSIBLE ACs into one HYPOTHESISED) or no-source inference (LLM with no anchoring AC). The helper's `(source_ac, ...)` signature constrains future shape. Mitigation: helper signature is `kwargs`-friendly (`source_ac=None` allowed for no-anchor case); multi-source case is a follow-on extension (helper grows a `source_acs: list[BandedAC]` variant).

3. **`SliceDriftError` cross-import (Cycle 4a's pattern) is semi-DRY but asymmetric** — JsTs imports from Ruby; if Cycle 5+ adds a Python adapter, Python would also import from Ruby's slicer (creating an "every adapter imports from Ruby" pattern that's brittle). Surface #5 declined to fix this in 4b, but the symmetry argument has weight; Cycle 5+ should reconsider (move to `_common/slicer_aggregator.py`).

4. **Compat shim re-exports at `_ast_utils.slugify` may rot.** If a future cycle ADDs new functions to `_ast_utils.py` that should live in `_common/`, the shim pattern needs to grow. RF: the shim only handles `slugify` + `file_slug`; new shared symbols default to `_common/` directly + no shim.

5. **Heuristic helpers `make_inferred_banded_ac` does NOT validate that `source_ac.confidence == PLAUSIBLE`.** It accepts any source. Both adapters' callers gate this externally (in `infer_domain_rules()`). RF: should the helper itself enforce? Cycle 4b plan-doc decision: **no** — let the per-language orchestration enforce; the helper stays generic. (Future inference shapes may want VERIFIED → HYPOTHESISED inference too.)

6. **Cycle 4b's fixture validates the shape but not the runtime semantics.** RSpec specs aren't actually executed (Ruby runtime + bundler not in scope; mirror of Cycle 4a's same RF). Persona must verify test pass-state at ratification time. Surfaced in `odd-methodology.md` §12 Cycle 3 already; no doc edit needed in 4b.

7. **No real Rails app verification.** The canonical fixture matches the master plan AC.FIXTURES.2 shape but isn't a real production app. There may be Rails idioms it doesn't exercise (e.g., `acts_as_paranoid` for soft-delete, `paper_trail` for audit, ActionText for rich content, ActiveStorage for file uploads). Real OSS fixtures (v0.2.1) cover this gap.

8. **Test count target (~25 new tests) is a guess, not a derivation.** Plan-doc estimates ~25 new tests across AC.FIXTURES.{2,3,4,5} (~5 each) + AC.DRY.{1..4} (~3 each); actual count may land in 18–30. Marked as estimate per `feedback_specific_claims_verified_or_marked_guess`.

9. **`_common/` may grow into a god-module across cycles.** Today it's `repo_sha.py` + `slugs.py` + `heuristic_helpers.py` (3 files). Cycle 5+ may add slicer aggregator, more shared helpers. RF: revisit `_common/`'s shape if it exceeds ~10 files; sub-package by concern (`_common/git/`, `_common/slugs/`, `_common/inference/`) at that point.

10. **Plan-doc length.** This plan-doc is ~520 lines. The output-to-disk convention is satisfied; the dispatcher reads the summary section + decisions, not the full doc.

11. **JsTs LICENSE confirmed missing at plan-author** — verified 2026-05-04 via `ls`; closed RF inline (Surface #12 updated). AC.FIXTURES.5 lands BOTH portions in 4b (not just Ruby).

---

## §11 — Provenance trail

- v0.1.6 production-safety + cost-governance — sealed at `3f1d237` + `88674cb`.
- v0.1.7 per-project-pm + layered-skill discovery — sealed at `3aa20dd` + `73505f0` + `bcf699a` + `122a7c8`.
- Dev-pattern-simplifications #1 + #2 — sealed at `019cfca` + `df3f50f`.
- v0.1.8 master plan — sealed at `1c2c478`; rerouted at `17f32a9` (Cycle 4 Python → JS/TS/Playwright).
- v0.1.8 Cycle 1 — sealed at `c1abda1`. Provides scaffold + adapter Protocol + audit-log primitive.
- v0.1.8 Cycle 2 — sealed at `4865028`. Provides `BandedAC` + `Evidence` + `ConfidenceBand` + ratification.
- v0.1.8 Cycle 3 — sealed at `6711dd7`. Provides Ruby/Rails first-class adapter + per-file routing + slicer/aggregator pattern + `synthetic-rails` fixture.
- v0.1.8 Cycle 4a — sealed at `67dd302`. Provides JS/TS/Playwright adapter + `jsts-playwright-app` synthetic fixture + multi-grammar tree-sitter dispatch + 8 idiom recognizers + `_common/`-precursor RF (this cycle's primary derivation).
- Cycle 4a §10 RF #6 — explicit DRY surface flag; this plan-doc closes it.
- Cycle 4a §12 — Cycle 4b residue surface; this plan-doc operationalises it.
- Master plan §3 Cycle 4 ACs — `AC.FIXTURES.{2, 3-ruby, 4, 5}` named here; Cycle 4b closes them.
- Master plan §7.9 — explicit halt-trigger authorization for the 4a/4b split (now operationalised in Cycle 4a §0 + this Cycle 4b plan-doc).
- Smoke-test-discipline at `plugins/dev-sdlc/docs/smoke-test-discipline.md` — six dimensions.
- ODD-methodology at `plugins/dev-sdlc/docs/odd-methodology.md` — Cycle 2 added §11; Cycle 3 added §12; Cycle 4a added §13. Cycle 4b's edit (if any) is a small note in §12 referencing `lang/_common/` as the canonical shared-symbol home (universal admission).
- Pre-refactor baseline: 304 odd-extractor tests + 71 dev-sdlc parent tests passing at HEAD `67dd302` (verified 2026-05-04 via `pytest -q` after installing tree-sitter language deps).

---

## §12 — Acceptance gate

This plan-doc is gate-ready when:

1. All 8 ACs (AC.FIXTURES.{2, 3-ruby, 4-ruby, 5-ruby} + AC.DRY.{1..4}) named with explicit pytest paths (§4) — done.
2. Single-component fence named (§3) — done.
3. All 6 smoke dimensions addressed — applicable exercised, n/a documented (§6) — done.
4. Halt triggers named (§8) — done.
5. Bookkeeping path named (§9) — done.
6. F2 gaps named (§10) — done.
7. Method-decision record named per AC.D-sa.7 (§14) — done below.
8. Pre-refactor baseline verified (§6 + §11) — done (304 + 71 = 375 tests).
9. Cycle 4a/4b split clean surface (§0 + §11) — done.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Per AC.D-sa.7, every plan-doc that selects non-default methods records the decision + rationale. This cycle's method-level decisions:

| Decision | Choice | Rationale |
|---|---|---|
| Subpackage path | `lang/_common/` (Python convention; underscore-prefix marks internal) | Local to the `lang/` subtree where it's used; avoids top-level pollution; underscore-prefix matches `_ast_utils.py` precedent. |
| Compat shim retention | Re-export `slugify` + `file_slug` at `lang/{ruby,jsts}/_ast_utils.py` (`from .._common.slugs import slugify, file_slug`) | Zero-cost backward-compat; future external consumers (tests, dev-mode probes) don't break. |
| Recognizer import-site migration | All recognizer files migrate to import from `.._common.slugs` directly (not via the shim) | Establishes canonical-path precedent for Cycle 5+ amendments; recognizer count matches pre-refactor (no migration drops). |
| Heuristic helper boundary | ONLY `make_inferred_banded_ac()` constructor moves to `_common/`; per-language regex tables + orchestration stay per-language | Avoids over-abstraction; per-language readability preserved; constructor boilerplate is the only true duplication. |
| `SliceDriftError` / `aggregate_slice_results` location | Stay in `lang/ruby/slicer.py`; `lang/jsts/slicer.py` re-exports as today | Already DRY (one canonical home + one re-exporter); moving to `_common/` is symmetric but cosmetic. RF #3 surfaced for Cycle 5+ reconsideration. |
| Canonical Ruby fixture authoring | Real committed files; mirror Cycle 4a's `jsts-playwright-app` shape | Byte-identical extractions across runs (D2 idempotency); not generated-by-script; clearly labelled SYNTHETIC. |
| RSpec test count floor | ≥10 `it` blocks; aim 10–15 (5 model + 3 controller + 2 job) | Master plan AC.FIXTURES.2 floor; bounded growth to keep cycle within wall-clock band. |
| Polymorphic association | `webhook_event` polymorphic on `payment` / `customer` / `refund` | Plausible Rails-payment domain shape; drives one HYPOTHESISED AC via Cycle 3's `belongs_to :owner, polymorphic: true` heuristic. |
| Sidekiq API | Modern `include Sidekiq::Job`; OSS gem only | Sidekiq 7+ standard; no paid features; matches AC.FIXTURES.2 explicit naming. |
| Auth pattern | `bcrypt` + `has_secure_password` (Rails built-in); no Devise | Smaller surface; Devise complexity doesn't drive band-distribution outcome. |
| LICENSE choice | Apache-2.0 for BOTH fixtures (verified parent at plan-author: `/Users/lukeivers/ivers-corp-pos-v2/LICENSE` is Apache 2.0) | Match parent's permissive license; consistency across the canonical pos-v2 OSS surface. |
| AC ladder structure | `AC.FIXTURES.{2, 3-ruby, 4-ruby, 5-ruby}` + `AC.DRY.{1..4}` (8 total) | AC.FIXTURES.* mirrors master plan's Cycle 4 ladder (ruby portions); AC.DRY.* is local-to-cycle (no master plan AC mapping; prefix established for in-cycle consistency). |
| Test path discipline | Ruby fixture + e2e tests at `tests/lang/ruby/`; DRY refactor tests at `tests/lang/_common/` | Mirror of existing per-language test layout (Cycle 3 + 4a precedent); `_common/` test directory is NEW (lazy-create with `__init__.py`). |
| Smoke test naming | `*_canonical.py` suffix on Ruby smoke tests to distinguish from existing `synthetic-rails`-bound tests | Both fixtures coexist; tests must distinguish; the synthetic-rails tests are NOT modified (Cycle 3 territory). |
| Pre-refactor baseline pinning | 304 odd-extractor + 71 dev-sdlc-parent tests verified passing at HEAD `67dd302` BEFORE plan-doc author | Refactor halt-trigger needs a verified baseline; numbers are empirically verified, not guessed. |

---

### Commit SHAs

- Plan-doc commit: `3f8a8d1` —
  `docs(plans): v0.1.8 Cycle 4b — canonical Ruby-Rails fixture + DRY refactor sub-plan`
- Source-edit feat (BASELINE) commit: `c3c5afc` —
  `feat(dev-sdlc): canonical Ruby-Rails fixture + Ruby e2e + DRY refactor (v0.1.8 Cycle 4b)`
- Amendment (manifest+apply) commit: `042c3e19134052ad47981dbd90635f67ce73b81a` —
  `chore(amend): v0-1-8-cycle-4b-ruby-fixture-and-dry-refactor manifest+apply — dev-sdlc BASELINE+sidecar bump to c3c5afc`
- Seal commit: `c648cf99d63774cd9a1ccfe0bc1c117d97f5f018` —
  `chore(seals): v0-1-8-cycle-4b-ruby-fixture-and-dry-refactor — dev-sdlc at 042c3e1`
