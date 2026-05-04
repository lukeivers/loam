# plugins/dev-sdlc/odd-extractor

ODD reverse-engineering scaffold for loam — reads a foreign codebase,
emits a confidence-banded ODD contract draft, surfaces ambiguity for
ratification rather than fabricating ACs.

**Status:** v0.1.8 Cycle 1 (sealed-component discipline applies; the
dev-sdlc plugin's seal-test gates the entire `plugins/dev-sdlc/`
sub-tree, including this package). Cycle 1 ships the four-stage
workflow shape + language-adapter registry skeleton; Cycles 2-4 ship
confidence bands, ratification workflow, Ruby/Rails first-class
adapter, Python first-class adapter.

**Plan-docs:**

- v0.1.8 master plan: `docs/rebuild/plans/v0-1-8-master-plan.md`.
- Cycle 1 (this scaffolding): `docs/rebuild/plans/v0-1-8-cycle-1-odd-extractor-scaffolding.md`.

## What this package is

A Python library + `loam odd-extract` CLI subcommand that:

1. **Walks a target repository** (any language).
2. **Plans extractions per language adapter** (zero adapters in
   Cycle 1; Ruby in Cycle 3; Python in Cycle 4).
3. **Generates raw ACs** by dispatching adapters per slice.
4. **Verifies + post-processes** into a contract draft + sidecar
   YAML at `<workspace>/.loam/extractions/<repo-id>/`.

Every invocation runs in **dry-run mode by default** (Decision D —
Eric synthesis). Live extraction requires `--live`. Live extraction
respects a **foreign-codebase budget envelope** (Decision E) that
refuses runaway runs above a configurable money ceiling.

## Public API surface

```python
from loam_odd_extractor import (
    # Stage functions (pure — input → output, no global state).
    init_extraction,
    analyze_repo,
    generate_raw_acs,
    verify_contract,
    # Pydantic models.
    ExtractionConfig,
    AnalysisPlan,
    Slice,
    RawACs,
    ContractDraft,
    # Registry.
    LanguageAdapter,
    register_adapter,
    discover_adapters,
    # Budget.
    estimate_for_extraction,
    enforce_budget,
    # Errors.
    OddExtractorError,
    BudgetExceededError,
    RegistryError,
    StageError,
)
```

## CLI surface

```
loam odd-extract <repo-path> [--live] [--budget-cents N]
                             [--budget-override] [--workspace-root P]
                             [--stage init|analyze|generate|verify]
                             [--resume] [--status] [--repo-id X]
```

Default behaviour: dry-run; produces an `EstimateResult` block on
stdout; writes per-stage artefacts to
`<workspace>/.loam/extractions/<repo-id>/`.

## Workspace layout

```
<workspace>/.loam/extractions/<repo-id>/
    config.yaml          # Stage 1 output (ExtractionConfig)
    plan.yaml            # Stage 2 output (AnalysisPlan)
    raw-acs.yaml         # Stage 3 output (RawACs)
    contract-draft.md    # Stage 4 output (markdown)
    contract-draft.yaml  # Stage 4 output (sidecar)
    state.yaml           # cross-run state (D5 cross-session)
    audit-log/           # per-stage + per-run audit entries
        0001.yaml        # extraction_start
        0002.yaml        # stage_complete (init)
        ...
```

`<repo-id>` is derived deterministically from the repo's absolute
path: `<basename>-<8-char-sha256-hex>`.

## Language-adapter contract (for cycles 3+4)

```python
from typing import Protocol
from pathlib import Path
from loam_odd_extractor import AnalysisPlan, RawACs

class LanguageAdapter(Protocol):
    name: str
    def supports(self, repo: Path) -> bool: ...
    def extract(self, repo: Path, plan: AnalysisPlan) -> RawACs: ...
```

Adapters register via the `loam.odd_extractor.language_adapters`
entry-point group on their own pyproject.

## Confidence bands + ratification workflow (Cycle 2)

Cycle 2 of v0.1.8 adds the band schema + ratification workflow. Every
derived AC carries a `confidence:` field with one of three values
(`VERIFIED | PLAUSIBLE | HYPOTHESISED`) and an `evidence:` block
whose shape depends on the band. See `bands.py` for the typed model
and `plugins/dev-sdlc/docs/odd-methodology.md` §11 for the
methodology.

Ratification mediates band changes through the per-project PM's
one-question-at-a-time decision queue:

```
loam odd-extract <contract-draft.md> --ratify --pm-name <handle>
```

Per Eric synthesis Decision I, `PLAUSIBLE → VERIFIED` requires
explicit user confirmation (default-no on silent promotion); other
band changes are default-allow. Every action writes one audit-log
entry per the SOC-2 audit-trail floor (Decision P).

## Public API (Cycle 2 additions)

```python
from loam_odd_extractor import (
    # Confidence bands.
    ConfidenceBand,    # Enum: VERIFIED | PLAUSIBLE | HYPOTHESISED
    Evidence,          # Pydantic model — kind/citations/repo_sha/rationale
    BandedAC,          # Pydantic model — ac_id/text/confidence/evidence
    # Ratification.
    RatificationAction,
    promote, demote, edit, reject,         # factory functions
    apply_ratification_action,
    enqueue_ratification_batch,
    # Ratification state.
    RatificationState, CompletedAction,
    load_ratification_state, save_ratification_state,
    initialise_ratification_state,
    # Errors.
    RatificationRefusedError,
)
```

## Ruby/Rails first-class adapter (Cycle 3)

v0.1.8 Cycle 3 ships the Ruby/Rails adapter as the first registered
language adapter. Public API:

```python
from loam_odd_extractor import RubyAdapter
from loam_odd_extractor.lang.ruby.adapter import extract_rails_acs

# Convenience function — runs the adapter against ``repo`` directly.
raw = extract_rails_acs(repo=Path("/path/to/rails/app"))
# raw.acs is a list of dict-shaped BandedAC entries
```

The adapter implements the `LanguageAdapter` Protocol and is wired
via the `loam.odd_extractor.language_adapters` entry-point group
(Cycle 1's discovery mechanism).

### Recognized Rails idioms

- ActiveRecord models — `class X < ApplicationRecord` (PLAUSIBLE).
- ActiveRecord migrations — `db/migrate/*.rb` with `create_table`,
  `add_column`, `add_index`, `add_foreign_key`, `add_reference :X,
  polymorphic: true` (PLAUSIBLE).
- Callbacks — `before_save`, `after_create`, etc. (PLAUSIBLE).
- Concerns — `module X; extend ActiveSupport::Concern; ...; end`
  (PLAUSIBLE definition + PLAUSIBLE `include X` usage).
- Polymorphic associations — `belongs_to :owner, polymorphic: true`
  (PLAUSIBLE).
- ActiveJob — `class X < ApplicationJob` + `queue_as :name`
  (PLAUSIBLE).
- Sidekiq — `include Sidekiq::Worker / Sidekiq::Job` +
  `sidekiq_options queue: :name` (PLAUSIBLE).
- Routes — `config/routes.rb` with `resources`, `get/post/...`,
  `namespace`, `scope`, `root` (PLAUSIBLE).
- RSpec tests — `RSpec.describe ... it '...' do ... end` (VERIFIED
  with non-null `repo_sha`; downgrades to PLAUSIBLE without).
- Minitest tests — `test '...' do ... end` + `def test_<name>`
  (VERIFIED, same downgrade rule).
- Heuristic inferences — validates-presence → required-on-create;
  before_save :normalize_X → normalised-before-save; etc.
  (HYPOTHESISED with `rationale` capturing heuristic provenance).

### Tree-sitter dependency

The Ruby adapter uses the `tree-sitter` Python bindings + the
`tree-sitter-ruby` grammar (both pre-compiled wheels — no native
compile step). The imports are lazy at first parse-call so
``import loam_odd_extractor`` doesn't pull tree-sitter into
memory unnecessarily.

### Slice-and-swarm

When the dry-run estimate exceeds the budget envelope, the slicer
partitions the repo by Rails-idiom domain. The aggregator merges
per-slice results lexicographically by `ac_id`; >50% duplicate-
ratio across slices raises `SliceDriftError` (the F3-swarming
`needs_fresh_start` analog).

See `docs/odd-methodology.md` §12 for the full per-language
adapter conventions.

## JS/TS/Playwright first-class adapter (Cycle 4a)

v0.1.8 Cycle 4a ships the JavaScript / TypeScript / Playwright
adapter as the second registered language adapter — load-bearing
for Eric's first-project shape (TypeScript Playwright tests + page
objects under `src/playwright/` and `tests/`; JavaScript Node.js/
Express backend under `src/`; plain HTML/JS surface). Public API:

```python
from loam_odd_extractor import JsTsAdapter
from loam_odd_extractor.lang.jsts import extract_jsts_acs

# Convenience function — runs the adapter against ``repo`` directly.
raw = extract_jsts_acs(repo=Path("/path/to/jsts/app"))
# raw.acs is a list of dict-shaped BandedAC entries
```

The adapter handles BOTH JavaScript (.js / .mjs / .cjs / .jsx) and
TypeScript (.ts / .tsx) via three tree-sitter grammars
(`tree-sitter-javascript` for JS + JSX; `tree-sitter-typescript`'s
`language_typescript()` for `.ts`; `language_tsx()` for `.tsx`).
Both ESM (`import` / `export`) and CommonJS (`require` /
`module.exports`) module shapes are parsed.

### Recognized JS/TS/Playwright idioms

- Express routes — `app.get/post/put/delete/patch/use(...)`,
  `router.<verb>(...)` (PLAUSIBLE; middleware names captured in AC
  text).
- Playwright tests — `test(...)`, `test.describe(...)`,
  `test.beforeEach/afterEach/...` in files importing from
  `@playwright/test` (VERIFIED with non-null `repo_sha`; PLAUSIBLE
  downgrade without).
- Playwright page objects — classes under `src/playwright/` (or
  matching `*-page.ts`/`*Page.ts`) whose method bodies contain
  `page.locator()`/`page.goto()` calls (PLAUSIBLE).
- TypeScript types/interfaces — `interface X { ... }` and `type X
  = { ... }` (PLAUSIBLE).
- Zod schemas — `z.object({...})` and chained field constructors
  `z.string().email()`, `z.string().min(N)`, etc. (PLAUSIBLE).
- class-validator decorators — `@IsEmail()`, `@IsNotEmpty()`,
  `@MinLength(N)`, etc. on class fields (PLAUSIBLE).
- Test runners — Jest / Mocha / Vitest `describe(...)` /
  `it(...)` / `test(...)` calls; runner identity detected via
  import statements (VERIFIED with `repo_sha`; PLAUSIBLE downgrade).
- Plain HTML/JS — file-level: HTML files containing `<script>`
  tags emit one PLAUSIBLE AC each.
- Heuristic inferences — Zod `.email()` → "<Schema> requires a
  valid email"; class-validator `@IsEmail()` → email-required;
  Express auth-middleware → "route requires authentication";
  Playwright page-object `login*` method → auth entry point
  (HYPOTHESISED with `rationale`).

### tree-sitter-javascript / tree-sitter-typescript dependencies

Both grammars are pre-compiled wheels (no native compile step) and
are required dependencies of the package; lazy-imported at first
parse-call so `import loam_odd_extractor` is still cheap.

### Slice-and-swarm

The JsTs adapter ships its own `slicer.py` with a JS/TS-domain
partitioning strategy (per-page-object cluster, per-route-domain,
per-test-file cohort, per-src-module). Aggregator + `SliceDriftError`
are reused from the Ruby adapter (single canonical drift-detection
contract).

### Synthetic fixture

`tests/fixtures/jsts-playwright-app/` is a small but realistic
Eric-first-project-shaped fixture (~17 files; TS Playwright + JS
Express + HTML/JS + Zod + class-validator + ≥10 tests across
runners + ESM/CJS module-shape mix). Cycle-level smoke runs against
this fixture; release-level smoke against a real OSS JS/TS-Playwright
fixture is at v0.2.1.

See `docs/odd-methodology.md` §13 for the full per-language adapter
conventions (JS/TS/Playwright second).

## Out of scope (Cycles 1+2+3+4a)

- Python adapter → v0.2.2+ (deferred from Cycle 4 reroute).
- Canonical full Ruby-Rails-payment fixture + e2e smoke → Cycle 4b
  (residue surfaced from Cycle 4 via 4a/4b split per master plan
  §7.9).
- 6 dev-sdlc SKILLs → Cycle 5.
- Continuous codebase-watch → v0.2.0+.
- Persona-side natural-language → RatificationAction parser → v0.2.0+.
- LLM-driven HYPOTHESISED inference → v0.2+ (heuristic-shaped in
  Cycles 3 + 4a).
- Real test execution to verify VERIFIED claims → v0.1.9+ (both
  adapters grant VERIFIED on ratification-mediated assumption).
- DRY refactor of `repo_sha` + `slugify` + heuristic-inference
  patterns across Ruby/JsTs adapters → Cycle 4b/5 (local copies in
  Cycle 4a per RF §10 #6).
- joi schema validator recognizer → Cycle 4b/4c (Zod +
  class-validator only in 4a).
- NestJS-specific decorator patterns (`@Controller`, `@Get`, etc.)
  → v0.2+.

See the master plan for full scope and sequencing.
