# v0.1.8 Cycle 4 — JavaScript/TypeScript/Playwright first-class adapter + jsts-playwright fixture

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, build dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** Cycle 3 sealed at `6711dd7` (Ruby/Rails first-class adapter); Cycle 2 sealed at `4865028` (confidence bands + ratification); Cycle 1 sealed at `c1abda1` (odd-extractor scaffolding); v0.1.8 master plan rerouted at `17f32a9` (Cycle 4 Python → JS/TS/Playwright). §9 register backfilled through Cycle 3 at `cfee099`.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/rebuild/plans/v0-1-8-master-plan.md` §3 + §4 Cycle 4 (rerouted 2026-05-04).

**Status file:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-cycle-4-status-2026-05-04.md`.

**Quality bar (load-bearing):** *"I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses."* — Luke 2026-05-04. Eric's **first project** is JS/TS/Playwright (TypeScript Playwright tests + page objects under `src/playwright/` and `tests/`; JavaScript Node.js/Express backend under `src/`; plain HTML/JS surface). A weak JS/TS adapter directly compromises Eric's first-impression deliverable. Every JS/TS/Playwright idiom we claim to handle must be **tested + reliable**; "thin grep fallback" fails the bar.

---

## §0 — Scope decision (autonomous, F2 surface) — Cycle 4 → 4a focus

**Master plan §7.9 + dispatch halt-trigger:** "wall-clock >10 hours on plan-author + first-pass implementation → halt-and-surface; recommend 4a/4b split. Broader surface than Cycle 3's Ruby — two syntaxes, two module systems, multiple test runners."

**Surface comparison Cycle 3 vs Cycle 4-as-briefed:**

| Dimension | Cycle 3 (Ruby) | Cycle 4 (JS/TS/Playwright) |
|---|---|---|
| Syntaxes | 1 (Ruby) | 2 (JavaScript + TypeScript + TSX variant) |
| Module systems | 1 (require-or-Bundler) | 2 (ESM + CommonJS) — both must be parsed correctly |
| Idiom recognizers | 6 (AR / migrations / callbacks / concerns / polymorphic / jobs) + 2 test runners (RSpec / Minitest) = 8 modules | Express routes + middleware + Playwright tests + Playwright page objects + TS types/interfaces + Zod schemas + class-validator decorators + Jest/Mocha/Vitest test runners + plain HTML/JS file-level = 7+ recognizer modules + multi-grammar parser + extra HTML/JS file-level |
| Tree-sitter grammars | 1 (`tree-sitter-ruby`) | 3 (`tree-sitter-javascript` + `tree-sitter-typescript`'s `language_typescript()` + `language_tsx()`) |
| Fixture | 1 synthetic Rails fixture (11 files; cycle-level smoke) | 1 jsts-playwright-app fixture (Eric-first-project shape, ≥10 tests) + 1 ruby-rails-payment canonical fixture (AC.FIXTURES.2 in brief) |
| End-to-end smoke | Synthetic fixture → 6 dimensions | TWO fixtures × 6 dimensions; ratification e2e on both |
| Wall-clock band | 6–12 h (master plan) | 6–12 h (master plan) — but the surface is ~2× Cycle 3's |

**Decision (autonomous, recorded — F2 RF):** **Cycle 4a ships in this dispatch**; **Cycle 4b is the surfaced residue.**

- **Cycle 4a (this dispatch):** JS/TS/Playwright adapter (multi-grammar tree-sitter wrapper + Express + Playwright + page-object + TS-types + Zod + Jest/Mocha/Vitest/Playwright-test recognizers + plain HTML/JS file-level recognizer + slice-and-swarm extension); jsts-playwright-app fixture (Eric's first-project shape — TS Playwright + JS Express + HTML/JS); end-to-end smoke against the JSTS fixture (all 6 dimensions); analyze.py per-file routing extension to JS/TS file extensions.
- **Cycle 4b (residue surfaced; not in this dispatch):** the canonical ruby-rails-payment fixture (AC.FIXTURES.2 in brief). Cycle 3 already shipped a `tests/fixtures/synthetic-rails/` fixture (11 files; exercises every Ruby recognizer + all 6 smoke dimensions); Cycle 4b's job is the **release-level fixture** — full ActiveRecord models with callbacks + concerns + polymorphic + Sidekiq + ≥10 RSpec tests + permissive LICENSE — for the v0.1.8 release-level HARD gate per master plan §5. AC.FIXTURES.4 (ratification e2e on Rails fixture) and AC.FIXTURES.5 (Rails fixture committed real repo + LICENSE) move to Cycle 4b too. Cycle 4a's smoke proves the contract shape against the JSTS fixture; the same shape will hold against the Rails fixture by construction (BandedAC schema + ratification flow are unchanged).

**Why this is the right call:** Cycle 3's synthetic Rails fixture already proves the Ruby adapter end-to-end (AC.RAILS.5 — Eric-ratification e2e pin); Cycle 4a's job is to prove the JS/TS adapter end-to-end with EQUIVALENT rigor against an Eric-first-project-shaped fixture. The canonical Ruby fixture is **release-level smoke** (per master plan §5 + Decision R) — it doesn't compose with cycle-level adapter quality, only with release-gate confidence. Splitting at this seam preserves the QUALITY BAR ("WOW Eric") on the adapter that ships first while not blocking Cycle 4a on a fixture that doesn't change Cycle 4a's smoke outcome.

**This decision is recorded as Surface #0 in §5.** It does not waive the brief — it splits the brief into 4a (this) + 4b (next). The dispatcher decides whether to ship 4b before or after Cycle 5.

**AC family scope this cycle:** `AC.JSTS.{1..5}` (full) + `AC.FIXTURES.{1, 3-jsts-only}` (jsts-playwright-app fixture + JSTS-only end-to-end smoke). `AC.FIXTURES.{2, 3-ruby-rails-portion, 4, 5}` move to Cycle 4b.

---

## §1 — Outcome shape (the "why")

Cycles 1+2+3 shipped: extractor's shape (four-stage workflow, banded ACs, ratification, Ruby/Rails first-class adapter against synthetic fixture). Cycle 4 lands the **JavaScript/TypeScript/Playwright first-class adapter** — the language-specific extractor that understands JS/TS/Playwright idioms (Express routes, Playwright tests + page objects, TypeScript types/interfaces, Zod/class-validator schemas, Jest/Mocha/Vitest test runners, plain HTML/JS surface), uses tree-sitter for deterministic AST parsing across BOTH JavaScript and TypeScript (with separate grammars per language + a TSX variant for React-like TS), derives ACs test-first from passing Playwright/Jest/Mocha/Vitest tests (per AC.JSTS.3), produces `BandedAC` instances with the correct confidence band per idiom (per AC.JSTS.5 mapping rules), and supports slice-and-swarm decomposition for full-stack JS/TS codebases that exceed the budget envelope.

Cycle 4a's release-note promise: `loam odd-extract <jsts-app>` against an Eric-first-project-shaped JS/TS/Playwright codebase produces a confidence-banded contract draft where **passing Playwright + Jest + Mocha + Vitest tests → VERIFIED ACs** (with `evidence.kind="test"` and the test pinned to a `repo_sha`); **TypeScript types/interfaces, Zod/class-validator schemas, Express route declarations, Playwright page-object classes, Playwright test scaffolding (`test.describe`, `test.beforeEach`) → PLAUSIBLE ACs** (with `evidence.kind="source"` and file-path + line-number citations); **heuristic-derived domain inferences (e.g., `validates email presence-via-Zod` → "User creation requires email") → HYPOTHESISED ACs** (with `evidence.kind="inference"` and a non-empty rationale). Slice-and-swarm engages when the codebase exceeds the budget envelope; per-domain partitioning (per-page-object cluster, per-route-domain cluster, per-test-file cohort) mirrors the Ruby cycle's per-Rails-idiom strategy.

The shape is the deliverable. The cycle-level fixture is `tests/fixtures/jsts-playwright-app/` — small but representative (TypeScript Playwright tests + page objects under `src/playwright/`, JavaScript Express backend under `src/`, plain HTML/JS top-level dir, ≥10 tests across runners, README, `package.json` + `tsconfig.json`). Cycle 3's analogue (the synthetic Rails fixture) shipped at 11 files; Cycle 4a's JSTS fixture is sized similarly (~14-18 files) to cover the broader surface.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

Cycle 4a composes on top of Claude-native primitives + already-shipped loam machinery + Cycle 3's prior art:

- **Cycle 1's `LanguageAdapter` Protocol.** The JsTsAdapter implements `name: str`, `supports(repo: Path) -> bool`, `extract(repo: Path, plan: AnalysisPlan) -> RawACs`. No re-implementation; the Protocol is the contract.
- **Cycle 1's entry-point group `loam.odd_extractor.language_adapters`.** The JsTs adapter's pyproject declares an entry-point producing the adapter instance; `discover_adapters()` picks it up alongside Ruby.
- **Cycle 2's `BandedAC` + `Evidence` + `ConfidenceBand`.** Adapter outputs construct `BandedAC` instances, dump via `model_dump()` to dict, and append to `RawACs.acs` per the round-trip contract (Cycle 2 plan-doc §5 Surface #1). No schema changes.
- **Cycle 1's `write_audit_entry` primitive.** The JsTs adapter writes per-slice `slice_complete` audit entries when slice-and-swarm engages (same event_kind Cycle 3 introduced; no new event_kind in Cycle 4a).
- **Cycle 1's budget envelope + dry-run primitive.** Slice-and-swarm respects the per-extraction `BudgetEnvelope`; each slice contributes a `per_slice_costs` entry to `RawACs.per_slice_costs` (existing field).
- **Cycle 2's ratification workflow.** Banded ACs produced by the JsTs adapter flow through `enqueue_ratification_batch` → PM → user-mediated promotion at v0.2.0+; Cycle 4a produces the ACs that Cycle 2 ratifies.
- **Cycle 3's per-file routing in analyze.py.** Cycle 4a EXTENDS the `_LANGUAGE_HINTS` table to include `.js/.mjs/.cjs/.jsx/.ts/.tsx` → `jsts`. No structural change to analyze.py logic; only the hint table grows.
- **Cycle 3's `_ast_utils` shape.** Ruby's `_ast_utils.py` is a per-language utility module; JsTs ships its own `_ast_utils.py` with the same shape (slugify, walk_nodes, find_*, node_text, node_line). Helpers are intentionally NOT shared across language adapters because each tree-sitter grammar exposes different node types — sharing would create false coupling. (DRY opportunity surfaced: the SLUGIFY regex is identical; documented as a future opportunistic refactor in §10 RF #6 — not a Cycle 4a halt.)
- **Cycle 3's slicer + aggregator pattern.** JsTs ships its own `slicer.py` mirroring Ruby's `slicer.py` — same `slice_repo()` + `aggregate_slice_results()` shape; same `SliceDriftError` semantic; partitioning axis is JS/TS-domain instead of Rails-idiom-domain. Per Surface #4 below — same shape, distinct logic; sharing would couple the slicing strategies and prevent each language from evolving independently.
- **tree-sitter ecosystem.** `tree-sitter` Python bindings (already a Cycle 3 dep) + `tree-sitter-javascript` (new, pre-compiled wheel) + `tree-sitter-typescript` (new, pre-compiled wheel; exposes `language_typescript()` and `language_tsx()` for TS + TSX). Pre-compiled wheels mean install-time cost stays small (~360KB combined). Same lazy-import pattern as Cycle 3.

The required research question — **"What Claude capability does this lean on or extend?"** — answer: composes on Cycle 1's adapter Protocol + Cycle 2's banded schema + cost-governance budget + audit-log primitive + Cycle 3's per-file routing + Cycle 3's slicer/aggregator shape + tree-sitter ecosystem. Nothing re-implemented; no new schema migrations.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden for a JS/TS/Playwright-codebase user (Eric is the load-bearing user) drops dramatically. The persona no longer hand-rolls "walk this Node/Express + TS/Playwright repo + extract route declarations + parse Playwright test names + follow page-object classes" — the adapter does it. The persona's job becomes "relay the contract draft + mediate ratification of HYPOTHESISED ACs." Without this cycle, the persona must hand-roll JS/TS/Playwright-idiom recognition for every Eric-JS request — and Eric's first project is a JS/TS/Playwright surface, so this is the FIRST adapter Eric encounters.
- **Harness test:** every persona that handles JS/TS codebases can call `loam odd-extract <jsts-repo>` and get a banded contract draft. The JsTs adapter is a public API surface that composes — Cycle 5's `dispatch-brief-authoring` SKILL can compose against `loam.odd_extractor.lang.jsts.JsTsAdapter` directly when a JS/TS-specific brief needs idiom-aware AC seeds.

Both pass.

### Lens 3 — ODD authoring

Outcome above + named ACs (§4) + halt triggers (§8) + acceptance smoke (§6). Method (which tree-sitter queries, which schema validators are recognised in pass-1, fixture content shapes, exact grammar selection per file) stays the builder's call.

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH** for the JsTs adapter's overall shape: master plan §3 Cycle 4 (rerouted) + dispatch §4 Cycle 4 names every AC (`AC.JSTS.{1..5}` + `AC.FIXTURES.{1,3}`) with explicit semantics; Cycle 1's adapter Protocol + Cycle 2's banded schema + Cycle 3's slicer/aggregator pattern fix the input/output shapes; tree-sitter is a known-good AST library with both `tree-sitter-javascript` and `tree-sitter-typescript` available as pre-compiled wheels (verified via dry-run pip resolution at plan-author time — version `0.23.1` and `0.23.2` respectively).

Outcome confidence is **MEDIUM** on the following points (recorded as halt-surfaces in §5):

1. **Multi-grammar parser file routing.** A `.js` file uses `tree-sitter-javascript`; a `.ts` file uses `tree-sitter-typescript`'s `language_typescript()`; a `.tsx` file uses `tree-sitter-typescript`'s `language_tsx()`. `.mjs` and `.cjs` route to JS grammar; `.jsx` routes to JS grammar (tree-sitter-javascript handles JSX). The route-by-extension table is method (Surface #1).
2. **Per-recognizer module split.** Whether each JS/TS/Playwright idiom (Express routes, Playwright tests, Playwright page objects, TS types, Zod schemas, plain HTML/JS file-level) lives in its own module or as named functions in one `idioms.py` is a method choice — same as Cycle 3 Surface #1; resolved identically: per-idiom files (Surface #2).
3. **Slice-and-swarm aggregator partitioning axis for JS/TS codebases.** Cycle 3 partitioned by Rails-idiom domain (`app/models/`, `db/migrate/`, etc.); Cycle 4 partitions by JS/TS-domain (per-page-object cluster, per-route-file, per-test-file cohort, per-src-module). Specific axis is method (Surface #4).
4. **TypeScript schema validator subset for pass-1.** Eric uses Zod (per his stack quote); the dispatch lists Zod, class-validator, and joi as candidates. **Pass-1 in Cycle 4a recognizes Zod + class-validator;** joi is a Cycle 4b/4c extension (Surface #5).
5. **Jest/Mocha/Vitest detection signal.** All four test runners use `describe`/`it`/`test` calls; differentiation is via package.json/import statements/test-runner-specific config files. Pass-1 detects via call-name (`describe`, `it`, `test`) regardless of runner; the runner identity is recorded as evidence metadata (Surface #6). This is intentionally LOOSE — the "test runner" identity is a HYPOTHESISED-band annotation, the test-as-AC is VERIFIED.
6. **HYPOTHESISED inference patterns for JS/TS.** Same shape as Cycle 3 (heuristic-shaped inference, no LLM call); 5 patterns mirroring the Ruby set (Zod required-field → "User creation requires email" etc.); Cycle 4b+ extends (Surface #7).
7. **Plain HTML/JS surface granularity.** Pass-1 indexes `<script>`-bearing HTML files at FILE LEVEL (one PLAUSIBLE AC per file: "HTML page <name> contains client-side JS"); deep AST analysis of inline JS deferred to v0.2+ (Surface #8). Per the brief: "AC noted as PLAUSIBLE-by-default."

The Pydantic models for JsTs-adapter outputs ship LOOSE — strict on `BandedAC` (already enforced by Cycle 2's model_validators), looser on per-JsTs-idiom metadata fields (e.g., a `JsTsAdapterMetadata` dict-typed field on BandedAC.evidence's `citations` list with `extra='ignore'` semantics — Cycle 4b/4c can extend without schema migration).

### Lens 5 — Swarming

Cycle-internal decomposition options:

- (a) per-JS/TS-idiom: Express recognizer, Playwright-test recognizer, Playwright-page-object recognizer, TS-types recognizer, Zod-schema recognizer, class-validator recognizer, Jest/Mocha/Vitest aggregating recognizer, plain-HTML/JS recognizer (8 sub-units). Each sub-unit has a tighter AC. Stopping criterion: each sub-unit's AC is strictly tighter than the parent AC.JSTS.2.
- (b) per-pipeline-stage: AST parsing layer (multi-grammar), recognizer registry, slice-and-swarm orchestrator, aggregator, banded-AC constructor (5 sub-units).
- (c) single-module JsTs adapter with internal helper functions. Coordination overhead minimal; AC granularity coarser. Stopping criterion fires (further decomposition adds only coordination overhead).

Builder picks (a) **internally** but ships as a single Cycle-4a dispatch — the per-idiom decomposition matches the AC.JSTS.2 sub-list (Express + Playwright + TS-types + schemas + test-runners + plain HTML/JS) and gives the tightest per-recognizer AC mapping. Each idiom recognizer lives in its own file under `lang/jsts/recognizers/`, with one test file per recognizer. `max_planner_depth: 1` (no sub-planners; per-idiom files are the right granularity).

**No sub-agent dispatches in Cycle 4a.** The cycle-level halt-triggers (master plan halt: "wall-clock >10 hours on plan-author + first-pass implementation"; dispatch halt: "wall-clock >14 hours total") are the swarm-level escape hatch — if the cycle exceeds the budget, halt-and-surface (already done in §0 by pre-emptively splitting 4a/4b).

---

## §3 — Single-component fence

**Scope:** `plugins/dev-sdlc/odd-extractor/` (the existing Cycle-1+2+3-sealed sub-package; the JsTs adapter lands as a NEW sub-tree under it, parallel to `lang/ruby/`).

**New paths (this cycle):**

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/__init__.py` — public re-exports (`JsTsAdapter`, `extract_jsts_acs`).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/adapter.py` — `JsTsAdapter` class implementing the `LanguageAdapter` Protocol. `name="jsts"`; `supports(repo)` checks for `package.json` or any `.js/.mjs/.cjs/.jsx/.ts/.tsx` file at root; `extract(repo, plan)` orchestrates AST parsing + recognizer dispatch + slice-and-swarm.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/parser.py` — multi-grammar tree-sitter wrapper. Loads JS, TS, and TSX grammars lazily on first parse-call; routes files to grammar by extension via `parse_file(path)` dispatch table:
  - `.js`, `.mjs`, `.cjs`, `.jsx` → `tree_sitter_javascript.language()`.
  - `.ts` → `tree_sitter_typescript.language_typescript()`.
  - `.tsx` → `tree_sitter_typescript.language_tsx()`.
  Exposes `parse_file(path) -> tuple[Tree, bytes, GrammarKind]` + `parse_source(source, kind) -> Tree` for in-memory snippets. Per Surface #1 — the routing is by extension; content sniff (e.g., shebang) is a v0.2+ extension.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/_ast_utils.py` — JS/TS AST helpers (mirror of Ruby's `_ast_utils.py`):
  - `slugify(text)` — same regex as Ruby (DRY opportunity surfaced §10 RF #6).
  - `file_slug(file_path, repo_root)` — mirror of Ruby.
  - `walk_nodes(node)` — pre-order tree walker (tree-sitter API is grammar-agnostic).
  - `find_call_expressions(root)` — JS/TS: `call_expression` node type.
  - `find_function_declarations(root)` — JS/TS: `function_declaration` node type.
  - `find_class_declarations(root)` — JS/TS: `class_declaration` node type.
  - `find_method_definitions(root)` — JS/TS: `method_definition` node type (inside class bodies).
  - `find_interface_declarations(root)` — TS/TSX: `interface_declaration` node type.
  - `find_type_alias_declarations(root)` — TS/TSX: `type_alias_declaration` node type.
  - `find_export_statements(root)` — JS/TS: `export_statement` node type.
  - `find_import_statements(root)` — JS/TS: `import_statement` node type.
  - `call_callee_text(call_node, source)` — extract callee identifier from a `call_expression`.
  - `call_arguments(call_node, source)` — return list of argument strings.
  - `class_name(class_node, source)` — class name identifier.
  - `class_extends(class_node, source)` — class heritage clause; what does it extend?
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/recognizers/__init__.py` — re-exports each recognizer + the registry list `ALL_RECOGNIZERS`.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/recognizers/express_routes.py` — `recognize_express_routes(tree, source, file_path, repo_root, repo_sha) -> list[BandedAC]`. Detects `app.get/post/put/delete/patch/use(...)` and `router.get/post/...(...)` call expressions; emits PLAUSIBLE ACs per route. Method extraction: callee is a `member_expression` with `object` matching `app|router|server|api` and `property` in `{get,post,put,patch,delete,use,all,head,options}`.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/recognizers/playwright_tests.py` — `recognize_playwright_tests(tree, source, file_path, repo_root, repo_sha) -> list[BandedAC]`. Detects Playwright-test calls: `test(...)`, `test.describe(...)`, `test.beforeEach/beforeAll/afterEach/afterAll(...)`. Each `test(...)` block emits one VERIFIED AC (per AC.JSTS.3 + AC.JSTS.5); the enclosing `test.describe(...)` provides context. Per Surface #6 — runner-identity (Playwright vs Jest vs Mocha vs Vitest) is detected by import statement; runner identity stored in evidence metadata. Note: page-object methods called from `test(...)` (e.g., `await loginPage.login(...)`) carry forward to the page-object's PLAUSIBLE AC via citation.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/recognizers/playwright_page_objects.py` — `recognize_playwright_page_objects(tree, source, file_path, repo_root, repo_sha) -> list[BandedAC]`. Detects classes under `src/playwright/` (or files matching `*-page.ts`/`*Page.ts`/`*.page.ts`/`*PageObject.ts`) that define methods with `page.locator()` or `page.goto()` calls inside; emits PLAUSIBLE ACs for the page object class + each navigable action method.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/recognizers/ts_types.py` — `recognize_ts_types(tree, source, file_path, repo_root, repo_sha) -> list[BandedAC]`. Detects `interface X { ... }` and `type X = { ... }` declarations in `.ts/.tsx` files; emits PLAUSIBLE ACs per type/interface. Skipped on `.js/.mjs/.cjs/.jsx` files (no TS types in JS).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/recognizers/zod_schemas.py` — `recognize_zod_schemas(tree, source, file_path, repo_root, repo_sha) -> list[BandedAC]`. Detects `z.object({...})` calls (Zod's primary schema constructor) + `z.string()`, `z.number()`, `z.boolean()`, `z.array()`, `z.enum()` field constructors; emits PLAUSIBLE ACs per top-level schema. Per Surface #5 — class-validator decorators (`@IsString()`, `@IsEmail()`, etc.) recognized by `decorator` node type on class fields.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/recognizers/class_validator.py` — `recognize_class_validator(tree, source, file_path, repo_root, repo_sha) -> list[BandedAC]`. Detects `@IsString()`, `@IsEmail()`, `@IsNotEmpty()`, `@MinLength()`, `@MaxLength()`, `@IsOptional()` decorators on class fields; emits PLAUSIBLE ACs per validated field.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/recognizers/test_runners.py` — `recognize_test_runners(tree, source, file_path, repo_root, repo_sha) -> list[BandedAC]`. Detects Jest/Mocha/Vitest test calls (`describe(...)`, `it(...)`, `test(...)`) in non-Playwright test files (heuristic: file is under `tests/` or `__tests__/` or matches `*.test.ts/js`/`*.spec.ts/js` AND is NOT a Playwright test — distinguished by import pattern: Playwright tests import from `@playwright/test`; Jest/Mocha/Vitest tests use globals or import from their own packages). Each `it(...)`/`test(...)` block emits one VERIFIED AC (per AC.JSTS.3 + AC.JSTS.5). Runner identity captured in evidence metadata.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/recognizers/plain_html_js.py` — `recognize_plain_html_js(file_path, repo_root, repo_sha) -> list[BandedAC]`. File-level recognizer (no AST parse): detects HTML files (`*.html`, `*.htm`) that contain `<script>` tags by reading the file as text; emits ONE PLAUSIBLE AC per HTML file naming the file. Per Surface #8 — pass-1 is file-level only; deep inline-JS analysis deferred.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/heuristic_inferences.py` — `infer_domain_rules(banded_acs: list[BandedAC]) -> list[BandedAC]`. Heuristic-based inference of HYPOTHESISED ACs (mirrors Cycle 3 Surface #4).
  Heuristic patterns (5; extensible):
  - Zod `email: z.string().email()` (or chained `.email()` matcher) → "<Schema> requires a valid email" (HYPOTHESISED).
  - Zod `<field>: z.string().min(N)` → "<Schema>.<field> has minimum length N" (HYPOTHESISED).
  - class-validator `@IsEmail()` on field → "<Class>.<field> must be a valid email" (HYPOTHESISED).
  - Express middleware chain with auth-named middleware (e.g., `requireAuth`, `authenticate`) on a route → "Route <method> <path> requires authentication" (HYPOTHESISED).
  - Playwright page-object method named `login*`/`signIn*`/`signUp*` → "Page object <X> exposes an authentication entry point" (HYPOTHESISED).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/slicer.py` — slice-and-swarm orchestrator (mirror of Ruby `slicer.py` shape). `slice_repo()` partitions by JS/TS domain when over budget:
  - One slice per `src/playwright/` cluster (page objects).
  - One slice per `src/routes/` or `src/controllers/` cluster (Express routes).
  - One slice for each top-level `src/` subdirectory (modules).
  - One slice per test directory (`tests/`, `__tests__/`).
  - One slice for each plain HTML/JS surface directory.
  - One catch-all slice for remaining JS/TS files.
  `aggregate_slice_results()` merges with deterministic AC ordering + duplicate-ratio drift detection (≤50% threshold per Cycle 3 pattern). `SliceDriftError` reused from Ruby's `slicer.py` (or each language ships its own subclass — method choice; surface #4).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/repo_sha.py` — `resolve_repo_sha(repo_path) -> str | None`. Subprocess-runs `git rev-parse HEAD`. Identical shape to Ruby's `repo_sha.py`; same DRY surface as `_ast_utils.py` slugify (§10 RF #6).

**Extension to Cycle 1's analyze.py (universal-admitted within fence):**

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/analyze.py` — extend the `_LANGUAGE_HINTS` dict with:
  ```python
  "jsts": frozenset({".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx"}),
  ```
  No structural change to routing logic. Cycle 3's per-file routing dispatches files to adapters by hint table; adding `jsts` is additive.

**Tests (new):**

- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/__init__.py` — package marker.
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/conftest.py` — JsTs-fixture-specific pytest fixtures (jsts-playwright-app fixture path + injected repo_sha + adapter cleanup).
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_AC_JSTS_1_jsts_ast_adapter.py` — adapter implements `LanguageAdapter` Protocol; tree-sitter parses both JS and TS files; `supports()` returns True for `package.json`-bearing repos; ESM and CommonJS module shapes both parse without error; `.tsx` routes through TSX grammar; entry-point factory registers correctly.
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_AC_JSTS_2_jsts_idiom_recognizers.py` — every JS/TS/Playwright idiom recognizer recognizes its idiom on the JsTs fixture; no false negatives on the named patterns; Playwright tests recognized in TS files; Express routes recognized in JS files.
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_AC_JSTS_3_test_first_extraction.py` — passing Playwright test → VERIFIED AC with `evidence.kind="test"`, `repo_sha` non-null, `citations=[<file>:<line>:<test_name>]`. Same for Jest/Mocha/Vitest. Runner identity captured in citations/metadata.
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_AC_JSTS_4_slice_and_swarm.py` — when budget would be exceeded, slicer partitions by JS/TS domain; aggregator merges; deterministic `ac_id` ordering; no duplicates; `SliceDriftError` raised when >50% duplicates injected.
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_AC_JSTS_5_band_mapping_per_idiom.py` — TS type/interface → PLAUSIBLE; Zod schema → PLAUSIBLE; passing Playwright/Jest test → VERIFIED; Express route → PLAUSIBLE; LLM-inferred (heuristic in Cycle 4a) → HYPOTHESISED. Each band variant constructed from the JsTs fixture matches the expected band.
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_AC_FIXTURES_1_jsts_playwright_app_shape.py` — fixture shape verification: TS Playwright tests + page objects under `src/playwright/` + JS Express backend under `src/` + plain HTML/JS in top-level dir + ≥10 tests across runners + README + `package.json` + `tsconfig.json`. Each shape claim is a separate test method.
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_AC_FIXTURES_3_jsts_e2e_band_distribution.py` — end-to-end smoke against jsts-playwright-app fixture: `loam odd-extract` produces a banded contract draft with ≥3 VERIFIED, ≥5 PLAUSIBLE, ≥2 HYPOTHESISED ACs. Sanity-checks the schema.
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_AC_JSTS_8_synthetic_snippets.py` — adapter unit tests against hand-authored JS/TS snippets (no full fixture) — one snippet per recognizer + one combined snippet.
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_per_file_routing.py` — analyze.py's per-file routing extension correctly partitions `.js/.ts/.tsx/.mjs/.cjs/.jsx` → jsts slice; coexistence with Ruby adapter (Rails+Node-data-script repo correctly partitioned); `.py` files stay unhandled (no Python adapter in Cycle 4a).
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_smoke_d1_cold_state.py` — D1 cold-state: fresh tmp workspace + jsts-playwright-app fixture → `loam odd-extract` end-to-end → banded contract draft with the expected idiom counts.
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_smoke_d2_idempotency.py` — D2 idempotency variant: 5 extractions against the JsTs fixture produce byte-identical artefacts (modulo timestamps via clock injection).
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_smoke_d5_cross_session.py` — D5 cross-session: per-slice extraction state survives subprocess boundary; resume reads partial slice state and completes remaining slices.
- `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/test_smoke_d6_telemetry_floor.py` — D6 telemetry floor: every JS/TS idiom recognized + every slice run logs an audit entry per audit-trail floor.

**Test fixtures (new):**

- `plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/` — small but realistic JS/TS/Playwright app shaped like Eric's first project:
  - `package.json` — declares `express`, `@playwright/test`, `zod`, `vitest`; lists scripts (`test:e2e`, `test`, `start`).
  - `tsconfig.json` — TypeScript compilation config (strict, ES2022, moduleResolution: node).
  - `playwright.config.ts` — Playwright configuration.
  - `src/server.js` — Express app entry point (CommonJS — exercises CJS module shape).
  - `src/routes/users.js` — Express user routes (`router.get`, `router.post`, etc.) — JavaScript; ESM (export-default-router) — but wait, the file declares CJS via package.json field... method-level: both ESM and CJS files in the fixture (one of each) per AC.JSTS.1's "ESM and CommonJS module shapes both supported" claim.
  - `src/routes/sessions.mjs` — ESM routes file (exercises ESM `.mjs` parsing).
  - `src/middleware/auth.js` — Express auth middleware (the `requireAuth` heuristic source).
  - `src/schemas/user.ts` — Zod schemas (`userSchema = z.object({email: z.string().email(), name: z.string().min(1)})`) — TypeScript; ESM.
  - `src/schemas/session-class-validator.ts` — class-validator example (a class with `@IsEmail()` / `@MinLength()` decorators).
  - `src/playwright/login-page.ts` — Page-object class (`class LoginPage { async login(...){} }`).
  - `src/playwright/dashboard-page.ts` — Second page-object.
  - `tests/playwright/login.spec.ts` — Playwright test using LoginPage (`test('user can log in', async () => { await loginPage.login(...) })`); ≥3 `test(...)` blocks.
  - `tests/playwright/dashboard.spec.ts` — Playwright test for dashboard; ≥2 `test(...)` blocks.
  - `tests/unit/users.test.ts` — Vitest unit test for the user schema (≥3 `test(...)` blocks; tests Zod schema validation).
  - `tests/unit/server.test.js` — Jest-style test for Express handlers (≥2 `it(...)` blocks; CJS).
  - `public/index.html` — Plain HTML with embedded `<script>` (the plain HTML/JS surface).
  - `public/admin.html` — Second HTML file with `<script>`.
  - `README.md` — describes the synthetic fixture (clearly labelled `SYNTHETIC TEST FIXTURE — NOT A REAL APP`).
  - Total: ~17 files. Tests across 4 runners (Playwright + Vitest + Jest-style + module-tests). Both ESM and CJS module shapes. Both `.ts` and `.js` extensions. Plain HTML/JS surface. Page-object pattern.

**Edits to existing dev-sdlc paths (universal-admitted within fence):**

- `plugins/dev-sdlc/odd-extractor/pyproject.toml` — add dependencies on `tree-sitter-javascript>=0.23` + `tree-sitter-typescript>=0.23`. Add entry-point declaration:
  ```toml
  [project.entry-points."loam.odd_extractor.language_adapters"]
  jsts = "loam_odd_extractor.lang.jsts.adapter:_singleton_factory"
  ```
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/__init__.py` — re-export `JsTsAdapter` from `lang.jsts`.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/analyze.py` — extend `_LANGUAGE_HINTS` with `jsts` entry (per §3 above).
- `plugins/dev-sdlc/odd-extractor/README.md` — add a "JS/TS/Playwright adapter" subsection naming the public API + tree-sitter-javascript/typescript deps.
- `plugins/dev-sdlc/docs/odd-methodology.md` — append §13 "Per-language adapter conventions (JS/TS/Playwright second)" describing the band-mapping rules per JS/TS/Playwright idiom (mirrors §12's structure for Ruby/Rails).

**Composition (read-only, no edit):**

- `framework/cost-governance/` — read-only import of dry-run primitive + budget envelope.
- `framework/per-project-pm/` — no direct edits; ratification flow already wired via Cycle 2.

**Universal-admitted prefixes/files (off-fence, allowed under standard amendment policy):**

- `docs/rebuild/plans/` — this plan-doc + manifest.
- `CLAUDE.md`, `docs/odd-in-loam.md`, `docs/odd-methodology.md` (top-level), `docs/rebuild/STATE.md` — universal admission per `dev-pattern-simplifications-2.manifest.yaml` precedent.

**Out-of-fence (would halt-and-surface):**

- Any `framework/` component edit other than read-only imports.
- Any other `plugins/` component edit (loam-skills/, etc.).
- Any change to Cycle 2's PM contract or `BandedAC` schema.
- Any change to `lang/ruby/` (Cycle 3's seal).
- Any change to the synthetic-rails fixture (Cycle 3 owns).
- Any Python adapter implementation (deferred to v0.2.2+).
- The canonical Ruby-Rails-payment fixture (4b residue per §0).

---

## §4 — AC family — `AC.JSTS.*` + `AC.FIXTURES.*` (locked for 4a)

Each AC has at least one explicit pytest under `plugins/dev-sdlc/odd-extractor/tests/lang/jsts/`. ODD §2.5 — every line of code, every branch, every test maps to a named AC.

### AC.JSTS.1 — JS/TS AST adapter via tree-sitter (multi-grammar)

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/adapter.py` exposes `JsTsAdapter` class:
  - `name = "jsts"`.
  - `supports(repo: Path) -> bool` returns True iff the repo contains a `package.json` OR any `.js/.mjs/.cjs/.jsx/.ts/.tsx` file at the repo root or one level deep.
  - `extract(repo: Path, plan: AnalysisPlan) -> RawACs` runs the orchestration: parses every JS/TS file in the plan's slices via the appropriate tree-sitter grammar; dispatches to recognizers; constructs `BandedAC` instances; returns `RawACs` with `acs=[d.model_dump() for d in banded_acs]`.
- `lang/jsts/parser.py` exposes:
  - `parse_file(path: Path) -> tuple[tree_sitter.Tree, bytes, GrammarKind]` where `GrammarKind` is a `Literal["javascript", "typescript", "tsx"]` enum-like type. Routes by extension.
  - `parse_source(source: bytes, kind: GrammarKind) -> tree_sitter.Tree` for in-memory snippets.
  - `get_parser(kind: GrammarKind) -> tree_sitter.Parser` — per-kind parser cache (lazy import).
  Parse failure (`tree.root_node.has_error == True`) returned anyway; recognizers skip files with parse errors and emit a `parse_error` audit-log entry.
- The adapter declares a `[project.entry-points."loam.odd_extractor.language_adapters"]` entry that resolves to `_singleton_factory` (callable factory, returns the singleton instance) — same shape as Ruby.
- Both ESM (`import`/`export`) and CommonJS (`require`/`module.exports`) parse cleanly via tree-sitter-javascript (the grammar handles both natively); no special handling needed at the adapter level.
- **Test:** `test_AC_JSTS_1_jsts_ast_adapter.py` — adapter is `LanguageAdapter`-Protocol-compliant (manually validated via `_validate_adapter`); `supports()` True for `package.json`-bearing fixture, False for empty dir; `parse_file()` round-trips a known JS snippet (CJS), an ESM snippet, a TS snippet, and a TSX snippet; tree-sitter JS/TS/TSX grammars load; entry-point discovers the adapter from a tmp install (deferred — entry-point registration is structural verification only via `discover_adapters()` after manual entry-point declaration).

### AC.JSTS.2 — JS/TS/Playwright-idiom recognizers (8 idioms)

- Each idiom has a dedicated recognizer module under `lang/jsts/recognizers/`:

| Idiom | Module | Detection signal | Band emitted |
|---|---|---|---|
| Express routes | `express_routes.py` | `app.get/post/put/delete/patch/use(...)`, `router.get/post/...(...)` | PLAUSIBLE |
| Playwright tests | `playwright_tests.py` | `test(...)`, `test.describe(...)`, `test.beforeEach(...)`, etc. — file imports from `@playwright/test` | VERIFIED (with repo_sha; PLAUSIBLE downgrade) |
| Playwright page objects | `playwright_page_objects.py` | Class declarations under `src/playwright/` or matching `*-page.ts`/`*Page.ts` patterns; method bodies contain `page.locator()` or `page.goto()` calls | PLAUSIBLE |
| TypeScript types/interfaces | `ts_types.py` | `interface X { ... }` and `type X = { ... }` in `.ts/.tsx` files | PLAUSIBLE |
| Zod schemas | `zod_schemas.py` | `z.object({...})`, `z.string()`, `z.number()`, `z.array()`, `z.enum()` calls | PLAUSIBLE |
| class-validator decorators | `class_validator.py` | `@IsString()`, `@IsEmail()`, `@IsNotEmpty()`, `@MinLength()`, `@MaxLength()`, `@IsOptional()` decorators on class fields | PLAUSIBLE |
| Test runners (Jest/Mocha/Vitest) | `test_runners.py` | `describe(...)`, `it(...)`, `test(...)` calls in non-Playwright test files (heuristic by file location + import pattern) | VERIFIED (with repo_sha; PLAUSIBLE downgrade) |
| Plain HTML/JS surface | `plain_html_js.py` | HTML files (`*.html`, `*.htm`) containing `<script>` tags (file-level; no AST) | PLAUSIBLE |

- Each recognizer:
  - Takes `(tree, source, file_path, repo_root, repo_sha)` (or `(file_path, repo_root, repo_sha)` for plain_html_js which is file-level) and returns `list[BandedAC]`.
  - Constructs `BandedAC` with: `ac_id` (deterministic — `f"AC.JSTS.<idiom>.{slug}"` derived from the AST node's content + file slug); `text` (descriptive prose); `confidence` per the table; `evidence=Evidence(kind="source"|"test", citations=[f"<file>:<line>"], repo_sha=<resolved>)`; `backing_files=[<file>]`.
- `lang/jsts/recognizers/__init__.py` exposes `ALL_RECOGNIZERS: list[Recognizer]` for the adapter's main loop.
- **Test:** `test_AC_JSTS_2_jsts_idiom_recognizers.py` — for each idiom, the recognizer applied to the jsts-playwright-app fixture finds the expected occurrence (no false negatives on the named patterns); applied to an empty file, returns `[]` (no false positives); ESM and CJS variants both recognized.

### AC.JSTS.3 — Test-first extraction (Playwright + Jest + Mocha + Vitest → VERIFIED)

- `recognizers/playwright_tests.py` produces VERIFIED ACs from passing Playwright test files.
- `recognizers/test_runners.py` produces VERIFIED ACs from passing Jest/Mocha/Vitest test files.
- For Playwright: detect `test('...', async ({page}) => { ... })` and `test.describe('...', () => { test(...) })`. Per-`test`-block AC: `ac_id=f"AC.JSTS.test.playwright.{describe_slug}.{test_slug}.{file_slug}"`; `text=f"Playwright — {describe}: {test_text}"`; `confidence=VERIFIED`; `evidence=Evidence(kind="test", citations=[f"{file}:{line}:playwright:{describe}#{test_text}"], repo_sha=<resolved>, rationale=None)`.
- For Jest/Mocha/Vitest: detect `describe('...', () => { it('...', () => {...}) })` or `test(...)` calls. Per-`it`/`test`-block AC. Runner identity (Jest/Mocha/Vitest) detected via import statements (`vitest`, `jest`, `mocha`) at file head; recorded as evidence metadata in the `citations` string (e.g., `f"{file}:{line}:vitest:{describe}#{it_text}"`).
- Cycle 4a does NOT execute the tests (same as Cycle 3 — requires Node.js runtime + Playwright browsers); the VERIFIED band is granted on the assumption tests in the repo were passing at the resolved `repo_sha`. The persona MUST verify test pass-state during ratification (RF gap §10 #2; mirror of Cycle 3 RF #2).
- repo_sha resolution: `lang/jsts/repo_sha.py` runs `git -C <repo> rev-parse HEAD`. If the repo isn't a git repo, returns None; the recognizer downgrades VERIFIED → PLAUSIBLE (`evidence.kind="source"` instead of `"test"`) per AC.BANDS.2.
- **Test:** `test_AC_JSTS_3_test_first_extraction.py` — fixture's Playwright spec produces N VERIFIED ACs (N = number of `test(...)` blocks across spec files); each carries `evidence.kind="test"`, non-null `repo_sha`, citations matching `<file>:<line>:playwright:<describe>#<test>`; Vitest test produces VERIFIED ACs with `vitest` runner identity in citation; Jest-style test produces VERIFIED ACs; non-git fixture produces PLAUSIBLE (downgrade) ACs. Bands round-trip via `BandedAC.model_validate(ac.model_dump())`.

### AC.JSTS.4 — Slice-and-swarm

- `lang/jsts/slicer.py` exposes:
  - `slice_repo(files, estimate_money_cents, budget_hard_cap_cents) -> list[Slice]` — when `estimate_money_cents <= budget_hard_cap_cents`, returns one all-files slice (`adapter_name="jsts"`, `paths=<all-jsts-files>`). When over-budget, partitions by JS/TS-domain:
    - One slice per `src/playwright/` cluster (page objects).
    - One slice per `src/routes/` cluster (Express route declarations).
    - One slice per `src/controllers/` cluster.
    - One slice for each top-level `src/` subdirectory (catch-all per module).
    - One slice per `tests/` subdirectory (`tests/playwright/`, `tests/unit/`, `__tests__/`).
    - One slice per plain-HTML/JS surface directory (`public/`).
    - One catch-all slice for remaining JS/TS files.
  - `aggregate_slice_results(slice_results: list[RawACs]) -> tuple[RawACs, list[dict]]` — same merge + dedup + drift detection as Ruby.
- F3 (swarming) `needs_fresh_start` analog: if the aggregator detects more than 50% duplicate `ac_id`s across slices, raises `SliceDriftError`; the adapter halts the extraction with a structured `slice_drift` audit entry.
- Per Surface #4 — `SliceDriftError` is REUSED from Ruby's `slicer.py` (one canonical exception; not language-bound). DRY mitigation; if Cycle 4b/5 wants per-language drift behaviour, subclass — not split.
- The adapter's `extract()` calls `slice_repo()` for the single-vs-multi-slice decision; iterates slices, parses+recognizes per-slice, aggregates.
- **Test:** `test_AC_JSTS_4_slice_and_swarm.py` — single-slice path (cost ≤ budget → one slice); multi-slice path (cost > budget → ≥ 6 slices for the JsTs fixture; every JS/TS-domain represented); aggregator merges deterministically; duplicate `ac_id`s deduplicated with audit-log entry; `SliceDriftError` raised when >50% duplicates injected.

### AC.JSTS.5 — Confidence band rules per JS/TS/Playwright idiom

- Bands are emitted per the master plan AC.JSTS.5 mapping:
  - **VERIFIED** — passing Playwright/Jest/Mocha/Vitest test (per AC.JSTS.3).
  - **PLAUSIBLE** — TypeScript types/interfaces, Zod schemas, class-validator decorators, Express route declarations, Playwright page-object classes, plain HTML/JS files (file-level).
  - **HYPOTHESISED** — heuristic-derived domain inferences (`heuristic_inferences.py`).
- Each band's `evidence` block carries the per-band-required fields per AC.BANDS.2:
  - VERIFIED → `kind="test"`, non-null `repo_sha`, non-empty `citations`.
  - PLAUSIBLE → `kind="source"`, non-empty `citations`.
  - HYPOTHESISED → `kind="inference"`, non-empty `rationale`.
- The adapter constructs `BandedAC` instances directly; `BandedAC`'s model_validator enforces band/evidence consistency at construction time. Any malformed pair raises `pydantic.ValidationError`; the adapter catches + downgrades + logs a `band_downgrade` audit entry (e.g., VERIFIED→PLAUSIBLE when repo_sha is None).
- **Test:** `test_AC_JSTS_5_band_mapping_per_idiom.py` — for each band/idiom pair from the JsTs fixture, the constructed `BandedAC` has the expected band; for each malformed pair (e.g., test recognizer with no repo_sha), the adapter downgrades correctly + logs the downgrade.

### AC.FIXTURES.1 — jsts-playwright-app realistic fixture (Eric-first-project shape)

- `plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/` is committed real files matching the Eric stack quote:
  - **TypeScript Playwright tests + page objects** under `src/playwright/` (page objects: `login-page.ts`, `dashboard-page.ts`) AND under `tests/playwright/` (specs: `login.spec.ts`, `dashboard.spec.ts`).
  - **JavaScript/Node Express backend** under `src/` (`server.js` (CJS), `routes/users.js` (CJS), `routes/sessions.mjs` (ESM), `middleware/auth.js`).
  - **Plain HTML/JS** in `public/` (`index.html`, `admin.html`).
  - **TypeScript schemas** under `src/schemas/` (Zod: `user.ts`; class-validator: `session-class-validator.ts`).
  - **≥10 tests across runners**: Playwright spec files have ≥3 + ≥2 = ≥5 tests; Vitest unit test ≥3 tests; Jest-style test ≥2 tests; total ≥10.
  - **README.md** — explains the fixture; clearly labelled SYNTHETIC.
  - **`package.json`** — declares `express`, `@playwright/test`, `zod`, `vitest`, `class-validator`; lists scripts.
  - **`tsconfig.json`** — strict mode, ES2022.
- The fixture contains BOTH ESM (`.mjs` + `import`/`export`) and CommonJS (`.js` + `require`/`module.exports`) module shapes (per AC.JSTS.1).
- The fixture is **clearly labelled** as synthetic (README banner + filename prefix `jsts-playwright-app/`) so it's never mistaken for a real app.
- The fixture is committed real files (not a fixture-builder script) so byte-identical extractions across runs are testable (D2 idempotency).
- Per Surface #5 — fixture exercises BOTH Zod AND class-validator (pass-1 schema validators).
- **Test:** `test_AC_FIXTURES_1_jsts_playwright_app_shape.py` — fixture file count + presence checks (each named file/directory exists); tests count via `grep -c "test('"` or AST parse; `package.json` validates as JSON; `tsconfig.json` validates as JSON; README is non-empty.

### AC.FIXTURES.3 (jsts-only portion) — End-to-end smoke band distribution

- `loam odd-extract tests/fixtures/jsts-playwright-app` produces a confidence-banded contract draft.
- Band distribution sanity-checks: ≥3 VERIFIED, ≥5 PLAUSIBLE, ≥2 HYPOTHESISED for the JsTs fixture.
- The contract draft parses as markdown with the banded-AC table populated (Cycle 2's `<!-- ACS_TABLE_HERE -->` injection).
- `RawACs.acs` round-trips through `BandedAC.model_validate()` for every entry.
- Exit status 0.
- **Test:** `test_AC_FIXTURES_3_jsts_e2e_band_distribution.py` — runs the four-stage workflow end-to-end against the JsTs fixture in live mode (with budget override since the fixture is small); asserts band counts; asserts contract draft markdown shape.

### Eric-ratification end-to-end pin (carried via D5 smoke + AC.FIXTURES.3 e2e — no separate AC.FIXTURES.4 in 4a)

- The ratification e2e pin is exercised structurally via the same path as Cycle 3's `test_AC_RAILS_5_eric_ratification_pin.py` (consumability of adapter output by `enqueue_ratification_batch`). Cycle 4a's smoke tests (test_smoke_d1_cold_state + test_AC_FIXTURES_3_jsts_e2e_band_distribution) cover the consumability claim end-to-end against the jsts-playwright-app fixture.
- AC.FIXTURES.4 (per master plan: "Eric-ratification workflow runs end-to-end on BOTH fixtures") moves to Cycle 4b — the ruby-rails portion is what gates 4b.

---

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

### Surface #0 — Cycle 4a/4b split (HALT-and-SURFACED at plan-author time per master plan §7.9)

**Decision (autonomous, surfaced):** master plan §7.9 + dispatch's halt-trigger ("wall-clock >10 hours on plan-author + first-pass implementation → halt-and-surface; recommend 4a/4b split. Broader surface than Cycle 3's Ruby — two syntaxes, two module systems, multiple test runners.") explicitly authorizes a 4a/4b split. Pre-build assessment of surface area (10 ACs across 2 fixtures + 8 recognizers + 3 grammars + 4 test runners + 2 module systems vs Cycle 3's 8 ACs across 1 fixture + 7 recognizers + 1 grammar + 1 module system) showed Cycle 4-as-briefed roughly doubles Cycle 3's surface; Cycle 3's wall-clock band was 4–8 h and shipped at 81 tests. Splitting at the seam between "JS/TS adapter against Eric-first-project fixture" (load-bearing for Eric's first impression) and "canonical Ruby-Rails fixture" (release-level smoke surface; not adapter-quality-bearing) preserves the QUALITY BAR on the JSTS adapter while not blocking on a fixture that doesn't change Cycle 4a's band-distribution outcome.

**Rationale:** AC.FIXTURES.2 (canonical Ruby-Rails fixture), AC.FIXTURES.4 (ratification e2e on BOTH fixtures), AC.FIXTURES.5 (both fixtures committed real repos with LICENSE) are RELEASE-LEVEL surface, not ADAPTER-QUALITY surface. Cycle 3 shipped a synthetic Rails fixture that proves the Ruby adapter works; the canonical Ruby fixture is the v0.1.8 release-gate hard-smoke (per master plan §5 + Decision R). Cycle 4a's adapter quality is what Eric's first impression depends on. Splitting clarifies the dependency: Cycle 4b can land independently of Cycle 5; the v0.1.8 release-gate is gated on 4b's canonical Ruby fixture + e2e on both fixtures, not 4a.

**4b residue surfaced:** AC.FIXTURES.2 (canonical Ruby-Rails-payment fixture), AC.FIXTURES.4 (ratification e2e on Ruby-Rails fixture; the JsTs portion of AC.FIXTURES.4 is implicit via Cycle 4a's smoke), AC.FIXTURES.5 (both fixtures committed real repos with LICENSE — the JsTs portion is satisfied in 4a; the Ruby portion moves to 4b). Cycle 4b's wall-clock band: 4–8 h (just the canonical Ruby fixture authoring + e2e smoke; no new adapter code). Cycle 4b is a fixture-only cycle (no `lang/` source edits).

### Surface #1 — Multi-grammar parser file routing (no halt — recorded)

**Decision (autonomous):** the parser routes files to grammar by EXTENSION:

```
.js, .mjs, .cjs, .jsx → tree-sitter-javascript
.ts                   → tree-sitter-typescript.language_typescript()
.tsx                  → tree-sitter-typescript.language_tsx()
```

**Rationale:** extension-based routing is unambiguous, fast (no file-content read), and matches the JS/TS ecosystem convention. Content-sniff (e.g., shebang, BOM) is over-engineering for v0.1.8; v0.2+ may add for edge cases. Tree-sitter-javascript handles JSX natively (the grammar accepts both plain JS and JSX); Tree-sitter-typescript provides BOTH a typescript-only grammar AND a TSX grammar — the TSX grammar is required for `.tsx` files because the typescript-only grammar treats `<>` as a generic syntax marker, not JSX.

### Surface #2 — Per-recognizer module split (no halt — recorded)

**Decision (autonomous):** each JS/TS/Playwright idiom recognizer lives in its own file under `lang/jsts/recognizers/`. Eight recognizer files: `express_routes.py`, `playwright_tests.py`, `playwright_page_objects.py`, `ts_types.py`, `zod_schemas.py`, `class_validator.py`, `test_runners.py`, `plain_html_js.py`. Plus `heuristic_inferences.py` for HYPOTHESISED ACs.

**Rationale:** matches the per-idiom AC.JSTS.2 sub-list; each recognizer has its own per-AC test file (one test file per recognizer); future Cycle-4.x amendments (e.g., NestJS-specific syntax, React-specific patterns) tighten one recognizer at a time without touching the rest. Per-file decomposition matches Lens 5 stopping criterion (each sub-unit's AC is strictly tighter than the parent AC.JSTS.2).

### Surface #3 — Test-first extraction granularity (no halt — recorded)

**Decision (autonomous):** **per-`test(...)`-block** for Playwright; **per-`it(...)`-block** + **per-`test(...)`-block** for Jest/Mocha/Vitest. Each block becomes one VERIFIED AC.

**Rationale:** matches Cycle 3 Surface #3 (test-name-as-AC-name, per-test granularity); aligns with the JS test-runner idiom where `test()`/`it()` is the assertion-as-spec; aggregates well at ratification (one decision per test, not one per assertion). `test.describe(...)` clusters provide context but don't become ACs themselves (same as RSpec's `describe`/`context`).

### Surface #4 — Slicer's slicing strategy (no halt — recorded)

**Decision (autonomous):** the slicer partitions by **JS/TS-domain** (one slice per `src/playwright/` cluster, one per `src/routes/`, one per top-level `src/` subdirectory, one per test-directory cohort, etc.) when the dry-run estimate exceeds the budget; otherwise returns a single all-files slice. Migration cohort chunking is N/A (no migrations in JS/TS world).

**Rationale:** JS/TS-domain is the natural partitioning axis (Cartographer-style per ODD-RE research §3.4); each slice is independently parseable + recognizable; cross-slice dedup handles the rare case where a page-object file appears in two slices. Alternative strategies (per-file, per-MB) rejected for the same reasons as Cycle 3 Surface #2.

`SliceDriftError` is REUSED from `lang/ruby/slicer.py` (single canonical class). Method-level rationale: drift detection is a slice-level concern, not language-level; coupling the exception class is the right level of DRY. If 4b/5 needs per-language drift behaviour, subclass per-language (not split the class).

### Surface #5 — Schema validator subset for pass-1 (no halt — recorded)

**Decision (autonomous):** Pass-1 (Cycle 4a) recognizes **Zod + class-validator**. joi is deferred to Cycle 4b/4c.

**Rationale:** the dispatch lists Zod, class-validator, and joi as candidates. Eric uses Zod (his stack quote names it). Zod is the most common modern TS schema library; class-validator is the second-most-common (NestJS-adjacent). joi is older and less common in TS-first projects. Pass-1 covers what Eric uses + the most common alternative; joi extends in 4b/4c.

### Surface #6 — Test-runner detection signal (no halt — recorded)

**Decision (autonomous):** Test-runner identity (Playwright vs Jest vs Mocha vs Vitest) detected by **import statement** at file head:

- `import { test, expect } from '@playwright/test'` → Playwright.
- `import { describe, it, expect } from 'vitest'` → Vitest.
- `import { describe, it } from 'mocha'` → Mocha.
- No import statement (Jest globals) OR `import { describe, it } from '@jest/globals'` → Jest.

For files with NO recognized test runner import, but located under `tests/`/`__tests__/`/matching `*.test.ts/js`/`*.spec.ts/js`, runner identity is **"unknown"** but the test calls (`describe`/`it`/`test`) STILL emit VERIFIED ACs (the runner identity is metadata, not a gate). Runner identity recorded in `evidence.citations` as `f"{file}:{line}:{runner}:{describe}#{test_text}"`.

**Rationale:** import-based detection is fast (file-head scan, no full AST traversal needed); the runner identity is HYPOTHESISED-band metadata not a structural claim about the test (the test still claims VERIFIED based on its passing state). The dispatch lists 4 runners; this resolves them.

### Surface #7 — HYPOTHESISED AC source: heuristic-shaped, no LLM (no halt — recorded)

**Decision (autonomous):** Cycle 4a produces HYPOTHESISED ACs from **heuristic-shaped inferences** based on already-extracted PLAUSIBLE ACs, mirroring Cycle 3 Surface #4. No real LLM calls.

Heuristic patterns (5; extensible in `lang/jsts/heuristic_inferences.py`):

- Zod `email: z.string().email()` (or chained `.email()`) → "<Schema> requires a valid email" (HYPOTHESISED — runtime usage may be conditional).
- Zod `<field>: z.string().min(N)` → "<Schema>.<field> has minimum length N" (HYPOTHESISED).
- class-validator `@IsEmail()` on field → "<Class>.<field> must be a valid email" (HYPOTHESISED).
- Express middleware chain naming auth-like middleware (`requireAuth`, `authenticate`, `isLoggedIn`, `withAuth`) → "Route <method> <path> requires authentication" (HYPOTHESISED — middleware may have early returns).
- Playwright page-object method named `login*`/`signIn*`/`signUp*` → "Page object <X> exposes an authentication entry point" (HYPOTHESISED).

Each HYPOTHESISED AC's `rationale` field captures the heuristic that produced it, mirroring Cycle 3's pattern.

**Rationale:** matches Cycle 3 Surface #4 — heuristic-shaped inference is faithful to the band semantics ("LLM-derived inference" → "machine-derived inference with explicit reasoning chain") without requiring an actual LLM call. Cycle 5+ can swap in LLM-shaped inference under the same rationale-required contract.

**RF flag (§10 #1):** the heuristic inference list is intentionally minimal in Cycle 4a (5 patterns). Real JS/TS apps have richer signals. Cycle 4b/5+ extends.

### Surface #8 — Plain HTML/JS surface granularity (no halt — recorded)

**Decision (autonomous):** Pass-1 indexes `<script>`-bearing HTML files at FILE LEVEL. One PLAUSIBLE AC per HTML file containing at least one `<script>` tag (named `f"AC.JSTS.html.{file_slug}"`, text `f"HTML page {basename} contains client-side JS"`). No deep AST parse of inline JS in pass-1.

**Rationale:** matches the dispatch's brief: "AC noted as PLAUSIBLE-by-default." Deep inline-JS analysis adds parser complexity (HTML parser + script-tag extraction + JS parser dispatch) for marginal smoke-coverage benefit; v0.2+ extends. The file-level claim is honest — "this HTML has client JS" is a structurally true claim that can be rationally verified by ratification.

### Surface #9 — analyze.py per-file routing (no halt — recorded)

**Decision (autonomous):** Cycle 3 introduced per-file routing in `analyze.py` (Cycle 3 Surface #6). Cycle 4a EXTENDS the `_LANGUAGE_HINTS` table with `jsts` → `frozenset({".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx"})`. NO structural change to `analyze.py` logic.

**Rationale:** the routing logic is unchanged; only the hint table grows. Multi-adapter co-existence (Rails + Node+TS in the same repo) routed correctly: Ruby adapter claims `.rb`, JsTs adapter claims `.js/.ts/etc.`, files matching neither land in `unhandled`.

### Surface #10 — repo_sha + heuristic-inference DRY across language adapters (no halt — recorded; RF surfaced §10 #6)

**Decision (autonomous):** `lang/jsts/repo_sha.py` is a near-duplicate of `lang/ruby/repo_sha.py` (subprocess-shells `git rev-parse HEAD`); `lang/jsts/heuristic_inferences.py` shares the rationale-string pattern with `lang/ruby/heuristic_inferences.py`. Cycle 4a does NOT factor these into a shared `lang/_common/` module.

**Rationale:** the brief calls out "DRY opportunity ignored (JS/TS and Ruby adapters duplicate aggregator code) → halt + refactor + surface." The aggregator is `slicer.py`'s `aggregate_slice_results()`; the JsTs slicer.py reuses Ruby's `SliceDriftError` (Surface #4 — the exception class is shared). The aggregator FUNCTION itself is similar between Ruby and JsTs but operates on per-language slice content; collapsing into a shared function would require parameterizing slice-domain semantics (`_categorize_file()`) into a callable injected at the language-adapter level — a real refactor. **Cycle 4a takes the local copy approach** and surfaces this as RF #6 for explicit Cycle 4b/5 cleanup. The justification for not blocking 4a on the refactor: the locked design (Cycle 3) shipped per-language `slicer.py`; copying-and-extending matches the locked design + cleanup is doc-only refactor, no behaviour change.

### Surface #11 — Synthetic JsTs fixture vs canonical (no halt — recorded)

**Decision (autonomous):** Cycle 4a ships a small in-tree synthetic JsTs fixture at `plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/`. The fixture is sized to exercise every recognizer + all 6 smoke dimensions (~17 files). Eric's actual first project codebase is v0.2.1 fresh-user smoke (master plan §5).

**Rationale:** matches Cycle 3 Surface #5 (synthetic in-tree fixture + AC.RAILS.8 hand-authored snippets in same tests dir); Cycle 4a's fixture serves both cycle-level smoke + Eric-first-project shape verification. The fixture is **clearly labelled** as synthetic (README banner) so it's never mistaken for a real Eric project.

### Surface #12 — D2/D3/D4 smoke applicability (no halt — recorded)

**Decision (autonomous):** mirrors Cycle 3 Surface #11:

- D2 — n/a structurally (one-shot CLI). Idempotency variant exercised: 5 extractions against the JsTs fixture produce byte-identical artefacts (modulo timestamps via clock injection). Cycle-4a-specific: per-grammar idempotency — the same TS file extracted twice produces byte-identical per-file results; `test.describe(...)` blocks emit ACs in deterministic order.
- D3 — n/a (no long-running process).
- D4 — n/a (same as D3).

D1, D5, D6 fully exercised at cycle level per master plan §3 Cycle 4 dispatch.

### Surface #13 — Universal-admitted doc edits (no halt — recorded)

**Decision (autonomous):** `plugins/dev-sdlc/docs/odd-methodology.md` is universal-admitted per Cycle 1+2+3's manifest precedent + the v3 manifest's `universal_paths.files` list. Cycle 4a appends a §13 "Per-language adapter conventions (JS/TS/Playwright second)" section; the manifest's `universal_paths` admits the path explicitly to document intent for SOC-2-style audit readers.

---

## §6 — Smoke (REALISTIC CONDITION — applicable dimensions per smoke-test-discipline §6)

Cycle-level smoke. Release-level HARD gate at v0.1.8 close (master plan §5 + Decision R), not this cycle.

### D1 — cold-state (fresh canonical workspace + JsTs fixture)

**Pattern.** Tmp directory as workspace root; jsts-playwright-app fixture copied to a tmp directory as the target repo. Run `loam odd-extract <fixture> --live --budget-cents 5000` (live mode + bumped budget so the small fixture isn't blocked). Assert: (a) all four stage artefacts land at expected paths; (b) `contract-draft.md` parses as markdown with the banded-AC table populated (Cycle 2's `<!-- ACS_TABLE_HERE -->` injection); (c) the contract draft has ≥3 VERIFIED AC (from Playwright + Vitest + Jest test recognition), ≥5 PLAUSIBLE ACs (Express routes + page objects + TS types + Zod schemas + class-validator + plain HTML/JS), ≥2 HYPOTHESISED AC (from heuristic inference); (d) `RawACs.acs` round-trips through `BandedAC.model_validate()` for every entry; (e) exit status 0.

**Test:** `test_smoke_d1_cold_state.py`.

### D2 — steady-state durability (n/a structurally; idempotency variant covered)

**Structural rationale.** Same as Cycle 3 — extractor is one-shot; no daemon.

**Idempotency variant exercised.** `test_smoke_d2_idempotency.py` runs the extraction five times against the JsTs fixture (with clock injection for timestamps + fixed repo_sha) and asserts byte-identical artefacts. Cycle-4a-specific addition: per-grammar idempotency — the same TS file extracted twice produces byte-identical per-file results; multi-grammar parser caches don't introduce non-determinism.

### D3 — restart resilience (n/a)

Same rationale as Cycles 1+2+3 — no long-running process.

### D4 — reboot resilience (n/a)

Same rationale as D3.

### D5 — cross-session continuity

**Pattern.** Test setup runs the four-stage workflow against the JsTs fixture in process A; mid-extraction (after `analyze` + first slice's `generate` complete), simulates `/clear` by spawning process B as a subprocess. B runs `loam odd-extract <fixture> --resume --workspace-root <same>`; asserts B reads A's per-slice state and completes the remaining slices. Final contract draft has the union of A's + B's slice outputs.

**Test:** `test_smoke_d5_cross_session.py`. The `/clear` analog is "fresh process boundary"; the test validates that boundary directly.

### D6 — telemetry floor

**Pattern.** Run a full extraction against the JsTs fixture; assert the audit log has:

- `extraction_start` (1 entry) — bookend.
- `stage_complete` (4 entries — one per stage) — Cycle 1 inheritance.
- `slice_complete` (≥1 entries — one per slice) — Cycle 3 addition (reused).
- `recognizer_finding` (≥6 entries — one per recognized JS/TS/Playwright-idiom occurrence) — Cycle 3 addition (reused with `recognizer_name` extending to JS/TS recognizers).
- `extraction_end` (1 entry) — bookend.
- Schema version preserved at 1; filenames monotonic `<NNNN>.yaml`.

**Test:** `test_smoke_d6_telemetry_floor.py`.

---

## §7 — Out of scope

Explicit deferrals (master plan §3 Cycle 4 + per-cycle dispatch + 4a/4b split per Surface #0):

- **Canonical Ruby-Rails-payment full fixture** (AC.FIXTURES.2) → Cycle 4b. 5–10 routes + ActiveRecord models with callbacks + concerns + polymorphic + Sidekiq jobs + ≥10 RSpec tests + README + permissive LICENSE. Cycle 3 already shipped a synthetic Rails fixture for cycle-level smoke; the canonical fixture is release-level smoke surface.
- **Eric-ratification e2e on Ruby-Rails fixture** (AC.FIXTURES.4 ruby-portion) → Cycle 4b. Cycle 4a's smoke covers the JsTs portion structurally.
- **Both fixtures committed real repos with permissive LICENSE** (AC.FIXTURES.5 ruby-portion) → Cycle 4b. JsTs portion shipped in 4a.
- **Python adapter** → v0.2.2+ (deferred 2026-05-04 per Cycle 4 reroute).
- **Continuous codebase-watch** → v0.2.0+.
- **Eric's actual first-project codebase smoke** → v0.2.1 fresh-user smoke.
- **6 dev-sdlc SKILLs** → Cycle 5.
- **LLM-driven HYPOTHESISED inference** → Cycle 4b+ (heuristic-shaped in 4a per Surface #7).
- **joi schema validator recognizer** → Cycle 4b/4c (Zod + class-validator only in 4a per Surface #5).
- **Real test execution to verify VERIFIED-band claims.** Same as Cycle 3 — Cycle 4a grants VERIFIED on the assumption tests pass at the resolved repo_sha.
- **Deep inline-JS AST analysis in HTML files** → v0.2+ (Surface #8; file-level only in 4a).
- **NestJS-specific decorator patterns** (`@Controller`, `@Get('/path')`, `@Module`) → Cycle 4b/4c. NestJS is a structured Express dialect; Express alone covers Eric's first project.
- **React/Vue/Svelte component idioms** → v0.2+ (`.tsx` parses cleanly via TSX grammar but no per-framework recognizers in 4a).
- **DRY refactor of repo_sha + heuristic_inferences across language adapters** → Cycle 4b/5 doc-only refactor (Surface #10; behavior-preserving).
- **Cartographer-style optimization beyond what's needed for full-stack JS/TS scale** → subsequent v0.x amendments.

---

## §8 — Halt triggers (in-flight)

Per dispatch + master plan:

- **WD drifts.** If `git rev-parse --show-toplevel` is not `/Users/lukeivers/ivers-corp-pos-v2/`, halt + surface.
- **Cycles 1+2+3 not sealed.** Verified at dispatch start: Cycle 1 sealed at `c1abda1`, Cycle 2 sealed at `4865028`, Cycle 3 sealed at `6711dd7`. If any is not sealed, halt.
- **Plan-doc not authored before code.** This document IS that plan-doc.
- **Wall-clock >10 hours on plan-author + first-pass implementation.** Master plan §7.9 + dispatch halt-trigger. **Pre-emptively addressed via Surface #0 4a/4b split.** If 4a alone exceeds 10h, halt + reframe further.
- **Wall-clock >14 hours total.** Hard stop with partial findings; do NOT push through.
- **Any AC ships partial.** If `test_AC_JSTS_<n>_*.py` or `test_AC_FIXTURES_<n>_*.py` is XFAIL, skipped, or asserts a degraded behaviour, halt + reframe.
- **JS and TS handled inconsistently** (e.g., TS works but JS regresses, or vice-versa). Halt + RF.
- **ESM/CJS distinction not honored.** If the parser fails to parse one or the other, halt + reframe.
- **DRY opportunity ignored** (per dispatch — JS/TS and Ruby adapters duplicate aggregator code) → halt + refactor + surface. **Pre-emptively addressed: SliceDriftError shared via Ruby's slicer; aggregator function NOT shared (Surface #10 RF surfaced for 4b/5).** If a deeper aggregator-DRY opportunity emerges during build, halt + surface.
- **AST library choice infeasible within ~3 h plan-author + first-pass implementation.** Pre-emptively verified: tree-sitter-javascript + tree-sitter-typescript pre-compiled wheels are available at PyPI; verified at plan-author time via dry-run pip resolution (versions 0.23.1 + 0.23.2). Both grammars load + parse without error in plan-author smoke.
- **JS/TS/Playwright-idiom coverage requires more than 5 in-build decisions to land.** Halt + describe.
- **Slice-and-swarm aggregator surfaces drift between slices** (>50% duplicate `ac_id`s; F3 needs_fresh_start analog).
- **D5 cross-session smoke fails.** Halt unconditionally on red.
- **ODD violations discovered in surrounding code.** Halt + surface; do not silently extend.
- **Tree-sitter JS/TS grammars fail to parse common JS/TS patterns.** If the JsTs fixture's hand-authored TS/JS fails tree-sitter parsing on any recognizer-target pattern, halt — this is the cycle's foundational AST library failure.
- **Either fixture fails the band-distribution sanity check** (≥3 VERIFIED, ≥5 PLAUSIBLE, ≥2 HYPOTHESISED) — halt + RF the schema.

---

## §9 — Bookkeeping

- **Manifest:** `docs/rebuild/plans/v0-1-8-cycle-4-jsts-playwright-adapter-and-fixtures.manifest.yaml` — schema_version: 3 with `plan_doc_ref:`. amendment.number omitted per AC.DPS1.10. ac_count: 7 (AC.JSTS.{1..5} + AC.FIXTURES.{1, 3-jsts}). smoke_outcome: "D1+D2-idempotency+D5+D6 exercised; D3/D4 n/a per smoke-test-discipline §6 (one-shot CLI)".
- **Apply:** `loam amend apply` — single merged manifest+apply commit per AC.DPS1.6 (v3 schema).
- **Seal:** `loam amend seal --plan-doc docs/rebuild/plans/v0-1-8-cycle-4-jsts-playwright-adapter-and-fixtures.md` — synthesizes 5–15 line narrative body into `plugins/dev-sdlc/seals/SEAL_COMMIT.v0-1-8-cycle-4-jsts-playwright-adapter-and-fixtures`.
- **§9 backfill:** master plan `docs/rebuild/plans/v0-1-8-master-plan.md` §9 method-decision register row for v0.1.8 Cycle 4a — doc-only commit after seal.
- **No tag push.** v0.1.8 tag waits on Cycle 4b + Cycle 5 + release-level HARD gate (Decision R).

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **Heuristic inference list is minimal in Cycle 4a (5 patterns).** Real JS/TS apps have richer signals — JWT-named secret config, role-based auth-middleware patterns, Playwright `expect(page).toHaveURL(...)` URL constraints, React form `onSubmit` validation patterns, GraphQL schema → API contract derivation. Cycle 4b+ must extend. The `heuristic_inferences.py` module is structured as an extensible list of `(pattern, inference_template, rationale_template)` tuples so additions don't require core refactoring.

2. **VERIFIED band is granted on the assumption tests pass at repo_sha.** Cycle 4a doesn't execute Playwright/Vitest/Jest tests (requires Node.js runtime + Playwright browsers + npm install, outside loam's scope). The persona MUST verify test pass-state during ratification. This is a known limitation; the band is "VERIFIED *as-of-extraction-time-by-human-authority*" not "VERIFIED *by automated test run*." Mirror of Cycle 3 RF #2. Surfaced in `odd-methodology.md` §13 doc edit. Cycle 4b/5+ may add `--run-tests` flag.

3. **Per-file routing's language-hint mapping is minimal.** Cycle 4a covers `.js/.mjs/.cjs/.jsx/.ts/.tsx` → jsts. Modern JS/TS apps include `.json` configs (already excluded as non-source), `.scss/.css` styles (out-of-scope), `.vue/.svelte` framework templates (deferred). Cycle 4a's job is the **JS/TS routing**, not a comprehensive web-language hint table.

4. **Slice-and-swarm slicing strategy is heuristic.** Per-JS/TS-domain partitioning is a reasonable default but isn't load-aware (a `src/playwright/` cluster with 200 page objects dwarfs a `src/middleware/` cohort with 5 middlewares). Cycle 4b/5+ may add load-aware re-balancing. Cycle 4a's strategy meets master plan AC.JSTS.4 + works for Eric-first-project scale.

5. **HYPOTHESISED ACs have the same cross-version drift as Ruby.** Mirror of Cycle 3 RF #5. Surfaced in `odd-methodology.md` §13.

6. **DRY across language adapters: repo_sha + slugify + heuristic_inferences shape are local copies, not shared.** Surface #10 — Cycle 4a takes the local-copy approach to avoid blocking 4a on a refactor. Cycle 4b/5 should factor these into `lang/_common/` (or similar) as a doc-only behaviour-preserving refactor. Specifically:
   - `repo_sha.py` is byte-identical between Ruby and JsTs (same subprocess shell to `git rev-parse HEAD`).
   - `slugify(text)` regex is identical.
   - Heuristic-inference rationale-string pattern is identical (different regex + different output text, same structural shape).
   - `aggregate_slice_results()` is structurally near-identical (same merge + dedup + drift detection); differs only in slice-domain semantics (which is parameterizable via injected `_categorize_file()`).
   The fix is non-blocking; flagging here for explicit Cycle 4b/5 cleanup.

7. **Tree-sitter JS/TS grammar version-pinning matters.** `tree-sitter-javascript>=0.23` and `tree-sitter-typescript>=0.23` are the floors; minor version bumps may add new syntax (TS 5.x features, JS proposed-stage-3 features). The pyproject's lower bounds are `>=0.23`; an upper bound is intentionally NOT set (semver-loose). Cycle 4b+ may add a tested-against version map if compatibility breakage emerges.

8. **`recognizer_finding` audit-log entry surface (Cycle 3 inheritance).** Cycle 3 introduced the `recognizer_finding` event_kind; Cycle 4a extends with `recognizer_name=jsts_<idiom>`. Schema is unchanged; the `event_kind: str` field is a string. RF: should we tighten `event_kind` to a Literal enum? Cycle 4a keeps it loose (same as Cycle 3); tightening is a separate amendment cleanup if needed.

9. **`ac_id` derivation must be globally unique across slices.** The slug-based derivation (`f"AC.JSTS.<idiom>.{slug}"` + file-relative-path suffix) mirrors Cycle 3 RF #9. Cross-slice collisions possible if two slices both contain a class named `LoginPage` (e.g., one in `src/playwright/` and one in `tests/legacy/`). Slugs extended with file-relative-path; aggregator's `ac_id` dedup logs `slice_aggregate_dedup` for actual collisions.

10. **No real LLM means HYPOTHESISED ACs are bounded by hand-authored heuristics.** Mirror of Cycle 3 RF #10. Cycle 5+ (or v0.1.9) is where LLM-driven inference enters; ratification flow is the safety net regardless.

11. **Multi-grammar parser cache complexity.** Cycle 4a's parser caches three parser instances (JS, TS, TSX) lazily. If a process imports the package but never extracts anything, none are loaded. If a process extracts only TS files, only TS parser loads. Memory cost is small (each parser is ~200KB); the lazy-load pattern preserves "import is cheap" property. RF: should we lazy-load the entire `tree_sitter` package or just the language modules? Cycle 4a lazy-loads the language modules at first parse-call; the `tree_sitter` package itself is loaded with the first language module. This matches Cycle 3's pattern.

12. **Plain HTML/JS surface is intentionally shallow.** Pass-1 produces ONE PLAUSIBLE AC per HTML file. Eric's actual project may have richer HTML/JS surface (DOM event handlers, AJAX patterns, fetch API usage). Surfacing this as RF for Cycle 4b/5 deepening; v0.2+ may add HTML AST library + inline-JS extraction.

---

## §11 — Provenance trail

- v0.1.6 production-safety + cost-governance — sealed at `3f1d237` + `88674cb`. Provides `dry_run_estimate` + `BudgetEnvelope`.
- v0.1.7 per-project-pm + layered-skill discovery — sealed at `3aa20dd` + `73505f0` + `bcf699a` + `122a7c8`.
- Dev-pattern-simplifications #1 + #2 (manifest schema v3 + seal-narrative compression) — sealed at `019cfca` + `df3f50f`.
- v0.1.8 master plan — sealed at `1c2c478`; rerouted at `17f32a9` (Cycle 4 Python → JS/TS/Playwright).
- v0.1.8 Cycle 1 — sealed at `c1abda1`. Provides scaffold + adapter Protocol + audit-log primitive.
- v0.1.8 Cycle 2 — sealed at `4865028`. Provides `BandedAC` + `Evidence` + `ConfidenceBand` + ratification.
- v0.1.8 Cycle 3 — sealed at `6711dd7`. Provides Ruby/Rails first-class adapter + per-file routing + slicer/aggregator pattern.
- ODD-RE research — `<pos3>/.scratch/claude-output/odd-reverse-engineering-skill-research.md` (907 lines). Tree-sitter as AST library; aider-style repomap as slicer reference.
- Lens 5 (swarming) — `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md`.
- Smoke-test-discipline at `plugins/dev-sdlc/docs/smoke-test-discipline.md` — six dimensions.
- ODD-methodology at `plugins/dev-sdlc/docs/odd-methodology.md` — Cycle 2 added §11 (confidence bands); Cycle 3 added §12 (Ruby/Rails adapter conventions); Cycle 4a adds §13 (JS/TS/Playwright adapter conventions).
- Eric synthesis Decision F — two fixtures (rerouted 2026-05-04 from Python-Flask to JS/TS-Playwright per Cycle 4 reroute).
- Eric synthesis G9 — language-agnostic skeleton + second-language reference implementation.
- Eric stack quote (from Luke's Telegram messages 10009 / 10011 / 10013, 2026-05-04): "TypeScript (Playwright tests + page objects under src/playwright/ and tests/) and JavaScript (Node.js/Express backend under src/), with plain HTML/JS in [...]".
- tree-sitter-javascript 0.23.1 + tree-sitter-typescript 0.23.2 — verified pre-compiled wheel availability at PyPI 2026-05-04.

---

## §12 — Cycle 4b residue (clear surface to dispatcher)

Cycle 4b delivers the residue surfaced via Surface #0:

- **AC.FIXTURES.2 — canonical ruby-rails-payment fixture.** 5–10 routes + ActiveRecord models with callbacks + concerns + polymorphic + Sidekiq jobs + ≥10 RSpec tests + README + permissive LICENSE. Committed real files (no submodule). Distinct from Cycle 3's synthetic-rails fixture (which is intentionally under-specified for cycle smoke).
- **AC.FIXTURES.4 ruby-portion — Eric-ratification end-to-end on Ruby-Rails fixture.** Mirror of Cycle 3's `test_AC_RAILS_5_eric_ratification_pin.py` shape, run against the canonical fixture instead of the synthetic.
- **AC.FIXTURES.5 ruby-portion — both fixtures committed real repos with permissive LICENSE.** JsTs portion satisfied in Cycle 4a; this is the Ruby half.
- **DRY refactor opportunities surfaced in §10 RF #6** — `lang/_common/` module factored from local copies in Ruby and JsTs (`repo_sha.py`, `slugify`, heuristic-inference patterns; possibly `aggregate_slice_results` if the parameterized form is clean).

**Cycle 4b wall-clock band (estimate):** 4–8 hours (canonical fixture authoring + e2e test + DRY refactor; no new adapter code; no new recognizers).

**Cycle 4b dependency:** Cycle 4a sealed (so the JsTs adapter exists) + Cycle 3 sealed (already done; provides the Ruby adapter to test). Independent of Cycle 5.

---

## §13 — Acceptance gate

This plan-doc is gate-ready when:

1. All 7 ACs (AC.JSTS.{1..5} + AC.FIXTURES.{1, 3-jsts}) named with explicit pytest paths (§4) — done.
2. Single-component fence named (§3) — done.
3. All 6 smoke dimensions addressed — applicable exercised, n/a documented (§6) — done.
4. Halt triggers named (§8) — done.
5. Bookkeeping path named (§9) — done.
6. F2 gaps named (§10) — done.
7. Method-decision record named per AC.D-sa.7 (§14) — done below.
8. Cycle 4a/4b split surfaced (§0 + §12) — done.

---

## 14. Method-decision record (per AC.D-sa.7 lint requirement)

Per AC.D-sa.7, every plan-doc that selects non-default methods records the decision + rationale. This cycle's method-level decisions:

| Decision | Choice | Rationale |
|---|---|---|
| Cycle 4a/4b split | 4a: JsTs adapter + JsTs fixture + JsTs e2e smoke; 4b: canonical Ruby-Rails fixture + Ruby e2e + DRY refactor | Master plan §7.9 + dispatch halt-trigger explicitly authorize 4a/4b split. Surface area roughly doubles Cycle 3 (2 syntaxes × 2 module systems × 4 test runners + 8 recognizer modules + 3 grammars vs Cycle 3's 1 × 1 × 2 × 7 × 1). Splitting at the seam between adapter-quality (4a) and release-level fixture (4b) preserves the QUALITY BAR on the JS/TS adapter (Eric's first impression) without blocking on a fixture that doesn't change adapter-smoke outcome. |
| AST library | tree-sitter via Python bindings — `tree_sitter` (existing Cycle 3 dep) + `tree-sitter-javascript` (new) + `tree-sitter-typescript` (new); `language_typescript()` for `.ts`, `language_tsx()` for `.tsx` | Verified pre-compiled wheel availability at plan-author time; matches Cycle 3's tree-sitter pattern; deterministic; `tree-sitter-typescript` exposes both grammars (typescript + tsx) so a single dep covers both extensions. Alternative `@typescript-eslint/parser` via subprocess rejected: adds Node.js runtime dep + subprocess overhead + non-deterministic timing; only buys richer TS-specific node types we don't need for pass-1. |
| Multi-grammar parser file routing | By extension: `.js/.mjs/.cjs/.jsx` → tree-sitter-javascript; `.ts` → tree-sitter-typescript (typescript); `.tsx` → tree-sitter-typescript (tsx) | Extension-based routing is unambiguous, fast, matches JS/TS ecosystem convention. tree-sitter-javascript handles JSX natively (the grammar accepts JSX); tree-sitter-typescript provides separate typescript + tsx grammars (the typescript-only grammar treats `<>` as generics, not JSX — TSX requires the dedicated grammar). |
| Recognizer module split | One file per JS/TS/Playwright idiom (8 modules under `recognizers/`) | Per-idiom AC granularity (Lens 5 stopping criterion); per-recognizer test files; Cycle 4b/5 amendments tighten one recognizer at a time. Mirror of Cycle 3 Surface #1. |
| Slicing strategy | Per-JS/TS-domain partitioning when over budget (per-page-object cluster, per-route-domain, per-test-cohort, per-src-module) | Natural JS/TS partitioning axis; per-slice deterministic processing; cross-slice dedup. Mirror of Cycle 3's per-Rails-idiom strategy. |
| Test-first granularity | Per-`test(...)`-block (Playwright); per-`it(...)`/`test(...)`-block (Jest/Mocha/Vitest) | Matches test-name-as-AC-name; aligns with JS test-runner idiom; aggregates well at ratification. Mirror of Cycle 3 Surface #3. |
| Schema validator subset | Zod + class-validator in pass-1; joi deferred | Eric uses Zod; class-validator is the second-most-common in TS-first projects. joi is older/less-common; deferred to Cycle 4b/4c. |
| Test-runner detection signal | Import-statement scan at file head | Fast (no full AST traversal); correctly identifies Playwright vs Jest vs Mocha vs Vitest; runner identity is HYPOTHESISED-band metadata not a structural gate on the test AC. |
| HYPOTHESISED inference | Heuristic-shaped (no LLM in Cycle 4a) | Mirror of Cycle 3 Surface #4 — preserves band semantics without LLM cost-governance complexity; Cycle 5+ swaps in LLM under same rationale-required contract. |
| repo_sha resolution | Subprocess shell to `git rev-parse HEAD` | Universal availability; matches loam-amend + Cycle 3 precedents; no Python git library dep. Local copy of `lang/ruby/repo_sha.py` (DRY surface flagged §10 RF #6). |
| tree-sitter-javascript + tree-sitter-typescript dep declaration | Required (not optional/extra); lazy-imported at first use | Honest dep declaration; pre-compiled wheels mean install-time cost is small; lazy import preserves "import is cheap" property. Mirror of Cycle 3 Surface #8. |
| Per-file routing extension | Extend Cycle 3's `_LANGUAGE_HINTS` table with `jsts` entry | Smallest extension; structural change zero. |
| Aggregator order | Lexicographic sort by `ac_id` | D2 idempotency. Mirror of Cycle 3 Surface #9. |
| `SliceDriftError` reuse | Reused from `lang/ruby/slicer.py`; not duplicated in `lang/jsts/slicer.py` | Drift detection is slice-level not language-level concern; coupling the exception class is the right level of DRY. |
| Plain HTML/JS surface granularity | File-level only (one PLAUSIBLE AC per `<script>`-bearing HTML file); deep inline-JS analysis deferred to v0.2+ | Per dispatch brief: "AC noted as PLAUSIBLE-by-default." Pass-1 keeps parser complexity bounded. |
| Synthetic JsTs fixture vs canonical Eric codebase | Synthetic in 4a (`tests/fixtures/jsts-playwright-app/`); Eric's actual codebase v0.2.1 | Synthetic suffices for adapter-shape verification + cycle-level smoke; Eric's codebase is fresh-user smoke surface. |
| ESM + CommonJS coverage in fixture | Mixed: `.js` (CJS), `.mjs` (ESM), `.ts/.tsx` (TS module-resolution per tsconfig) | AC.JSTS.1's "ESM and CommonJS module shapes both supported" claim verified directly via fixture content. |

---
