# odd-extractor — adapter conventions and banded-AC mechanics

**Relocated 2026-06-10** from `plugins/dev-sdlc/docs/odd-methodology.md`
(pre-rewrite §11.2–§11.4, §12, §13) per the KEEL adoption program Phase 1
(AC.KDOC.5): adapter tables and extractor ratification mechanics are
package documentation, not methodology doctrine. Section numbers below are
preserved from the pre-rewrite spec so historical citations resolve; the
full pre-rewrite text is archived at
`docs/archive/odd-methodology-2026-06-10-pre-keel.md`.

**Evidence-grade mapping note (doctrine §6, D4 — until the enum rename
lands):** this package's band enum (`src/loam_odd_extractor/bands.py`)
still spells its top band `VERIFIED`, and (per §12.3 / §13.6 below) grants
it on a *test-pass assumption* without executing the foreign suite. Under
the rewritten doctrine, **the extractor's `VERIFIED` band = the ASSERTED
evidence grade** (VERIFIED in doctrine means "ran green at a known SHA");
PLAUSIBLE likewise maps to ASSERTED (source-citation form); HYPOTHESISED is
unchanged. The code-level rename is deferred to a later extractor-touching
amendment; this note is the binding mapping until then.

---

### 11.2 Evidence requirements per band

The `evidence:` block on every banded AC carries fields that depend
on the band. The `BandedAC` model
(`plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/bands.py`)
enforces these structurally via a Pydantic model_validator:

- **VERIFIED requires:**
  - `evidence.kind` = `"test"`.
  - `evidence.citations` = non-empty list (test name + file path).
  - `evidence.repo_sha` = the repo SHA at extraction time
    (non-null).
- **PLAUSIBLE requires:**
  - `evidence.kind` = `"source"`.
  - `evidence.citations` = non-empty list (file path + line
    numbers).
- **HYPOTHESISED requires:**
  - `evidence.kind` = `"inference"`.
  - `evidence.rationale` = non-empty, non-whitespace-only string
    explaining the inference chain.

The model_validator is structural enforcement per §5.3 — Pydantic
violations raise on construction, not at runtime in some inner
loop. ODD §5 applies: invariants that must hold "always" should be
encoded structurally, not advisory.

### 11.3 Promotion and demotion (the ratification workflow)

A banded AC's confidence can be **promoted** (e.g., HYPOTHESISED →
PLAUSIBLE → VERIFIED) when fresh evidence emerges, or **demoted**
when prior evidence proves wrong. Promotion / demotion is mediated
by the per-project PM's one-question-at-a-time decision queue
(v0.1.7 Cycle 4). The CLI verb is `loam odd-extract ratify
<contract-draft>`.

Promotion has an asymmetric rule per Eric synthesis Decision I:
**PLAUSIBLE → VERIFIED requires explicit user confirmation**
(default-no on silent promotion). Other promotions
(HYPOTHESISED → PLAUSIBLE, HYPOTHESISED → VERIFIED) are
default-allow. Demotions are always default-allow — the safer
direction is permitted without ceremony.

The four ratification action kinds:

- **promote** — raise an AC's confidence band; requires fresh
  evidence to satisfy the new band's evidence rules.
- **demote** — lower an AC's confidence band; the prior evidence
  is preserved on the demoted record.
- **edit** — modify an AC's prose without changing the band; the
  evidence stays attached.
- **reject** — drop an AC from the contract draft entirely; the
  audit-log entry preserves the rejection rationale for SOC-2
  audit trail.

Every action writes one entry to the extraction's audit log under
`<workspace>/.loam/extractions/<repo-id>/audit-log/` per the SOC-2
audit-trail floor (Eric synthesis Decision P). The PM-side
`record_response` audit entry is cross-referenced on each
ratification entry's `pm_audit_path` field so audit readers can
join the two trails.

### 11.4 When re-extension applies

Per §4.1 (re-extension pattern): when a HYPOTHESISED AC's rationale
turns out to name a defect the foreign codebase doesn't actually
exhibit, the AC isn't promoted — it's **re-extended** as a
new-named negative AC describing what the codebase actually does.
The HYPOTHESISED AC is rejected (with rationale recorded in the
audit log); a fresh AC is added at the appropriate band based on
the actual behaviour discovered.

This composes with §4.4 — re-extension is never a violation. The
audit-log entry pair (the rejected HYPOTHESISED + the new banded
AC referenced via re-extension provenance) is the durable record.

Silent acceptance of a wrong HYPOTHESISED AC, or silent promotion
of a PLAUSIBLE AC without confirming the test pin, **is** the
violation §4.4 prohibits.


---

## 12. Per-language adapter conventions (Ruby/Rails first)

Per v0.1.8 Cycle 3 (the Ruby/Rails first-class adapter), the
`loam odd-extractor` ships per-language adapters that populate the
banded-AC contract from a target codebase. Each adapter implements
the `LanguageAdapter` Protocol from Cycle 1 (`name`, `supports`,
`extract`); the per-Rails-idiom recognizers under
`plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/ruby/recognizers/`
are the canonical reference shape. Cycle 4 mirrors the same shape
for Python.

### 12.1 Confidence band rules per Rails idiom

| Idiom | Band | Evidence |
|---|---|---|
| Passing RSpec / Minitest test | `VERIFIED` | `kind="test"`, `repo_sha` non-null, `citations=[<file>:<line>:<framework>:<descriptor>]` |
| ActiveRecord model declaration | `PLAUSIBLE` | `kind="source"`, `citations=[<file>:<line>]` |
| ActiveRecord migration (`create_table`, `add_column`, `add_index`, `add_foreign_key`, `add_reference`) | `PLAUSIBLE` | same |
| Callbacks (`before_save`, `after_create`, etc.) | `PLAUSIBLE` | same |
| Concern definition (`module X; extend ActiveSupport::Concern`) | `PLAUSIBLE` | same |
| Concern usage (`include X` in a model/controller) | `PLAUSIBLE` | same |
| Polymorphic association (`belongs_to :owner, polymorphic: true`) | `PLAUSIBLE` | same |
| ActiveJob class (`class X < ApplicationJob`) | `PLAUSIBLE` | same |
| Sidekiq worker (`include Sidekiq::Worker / Sidekiq::Job`) | `PLAUSIBLE` | same |
| Routes (`resources`, `get/post/...`, `namespace`, `scope`) | `PLAUSIBLE` | same |
| Heuristic-derived domain inference (validates-presence → required-on-create; before_save :normalize_X → normalised-before-save; etc.) | `HYPOTHESISED` | `kind="inference"`, `rationale` non-empty (heuristic provenance string) |

Adapters MUST construct `BandedAC` instances directly (Cycle 2's
Pydantic + model_validator catches malformed band/evidence pairs
at construction time); adapter outputs append to `RawACs.acs` as
`model_dump()`-d dicts that round-trip through
`BandedAC.model_validate()` without schema migration.

### 12.2 Test-first granularity

Per Eric synthesis Decision G1 (test-name-as-AC-name), each test
file's `it` block (RSpec) or `test '...'` block / `def test_<name>`
method (Minitest) becomes one `VERIFIED` AC. Per-`describe` /
per-`context` clusters are too coarse; per-`expect(...)` assertions
are too fine. The `it`/`test` block IS the verification-as-spec
boundary that ratification consumes.

### 12.3 Test-pass assumption

Cycle 3 grants `VERIFIED` on the **assumption that the test passed
at the resolved repo SHA**. Loam doesn't execute tests — running
RSpec / Minitest against a foreign Rails codebase requires a Ruby
runtime + Rails environment that's outside loam's process scope.
Ratification is the human verification step: the persona surfaces
each `VERIFIED` AC for owner confirmation that the test was
genuinely passing at the time of extraction.

When the repo isn't a git repo (no SHA), the test recognizer
**downgrades** `VERIFIED` → `PLAUSIBLE` per AC.BANDS.2 — the
evidence reverts to source-citation only and the persona is
expected to upgrade to `VERIFIED` only after running the test
suite themselves.

### 12.4 HYPOTHESISED inference engine

Cycle 3 produces HYPOTHESISED ACs from **heuristic-shaped
inferences** over already-extracted PLAUSIBLE ACs (no LLM call).
Each heuristic carries a rationale string capturing its
provenance; Cycle 4+ may swap in LLM-driven inference under the
same `rationale`-required contract.

Heuristic provenance changes when the inference engine changes
(heuristic → LLM); ratification is the cross-version reconciliation
point. Owners reviewing a HYPOTHESISED AC produced by the heuristic
engine in v0.1.8 Cycle 3 should re-evaluate (not blindly accept)
the same AC if it re-emerges from an LLM-driven engine in a later
version — the `rationale` field is the visible signal.

### 12.5 Slice-and-swarm decomposition

Per AC.RAILS.4 — when the dry-run estimate exceeds the budget
envelope, the Ruby adapter slices the repo by Rails-idiom domain
(one slice per `app/models/` cluster, one per `db/migrate/`
cohort split into chunks of 25, etc.) and aggregates per-slice
results deterministically (lexicographic sort by `ac_id`;
last-write-wins on duplicates).

When the aggregator detects >50% duplicate `ac_id`s across slices
(the F3-swarming `needs_fresh_start` analog), it raises
`SliceDriftError`; the adapter halts. Per Lens 5 — completing a
diverged shard chain is never the correct response; the slicing
strategy must be re-run with adjusted shard boundaries.

### 12.6 Per-file routing

Cycle 1's analyze stage routed all files to the first adapter that
claimed the repo (all-or-nothing). Cycle 3 extends this to
**per-file routing** by language hint (file extension /
filename). This unblocks multi-adapter codebases — modern Rails
apps include JS, ERB, YAML, JSON, and (occasionally) Python data-
science scripts that the Ruby adapter shouldn't claim. Files
matching no claiming adapter's hint land in `unhandled_paths`.

## 13. Per-language adapter conventions (JS/TS/Playwright second)

v0.1.8 Cycle 4a ships the JavaScript / TypeScript / Playwright
first-class adapter at
`plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/lang/jsts/`
— the second registered adapter, parallel to `lang/ruby/`. Eric's
first project is JS/TS/Playwright (per the cycle reroute
2026-05-04), so this adapter is load-bearing for the
first-impression deliverable. The conventions below mirror §12's
Ruby/Rails treatment, adjusted for the JS/TS surface.

### 13.1 Confidence band rules per JS/TS/Playwright idiom

| Idiom | Band emitted |
|---|---|
| Express routes (`app.get/post/...`, `router.<verb>(...)`) | PLAUSIBLE |
| Playwright tests (`test(...)` in `@playwright/test`-importing files) | VERIFIED (with non-null `repo_sha`) / PLAUSIBLE (downgrade) |
| Playwright page objects (classes under `src/playwright/` with `page.locator()`/`page.goto()` calls) | PLAUSIBLE |
| TypeScript types/interfaces (`interface X {...}`, `type X = ...`) | PLAUSIBLE |
| Zod schemas (`z.object({...})`, `z.string()`, `z.array()`, etc.) | PLAUSIBLE |
| class-validator decorators (`@IsEmail()`, `@MinLength()`, etc.) | PLAUSIBLE |
| Jest/Mocha/Vitest tests (`describe`/`it`/`test`) | VERIFIED (with non-null `repo_sha`) / PLAUSIBLE (downgrade) |
| Plain HTML/JS surface (HTML files containing `<script>` tags) | PLAUSIBLE (file-level only) |
| Heuristic inferences (Zod `.email()` → required email; auth-named middleware → auth-gated route; etc.) | HYPOTHESISED |

The mapping is enforced **structurally** by Cycle 2's
`BandedAC.model_validator` — a band/evidence pair that violates
the band's required fields raises `pydantic.ValidationError`. The
adapter catches such violations + downgrades + logs a
`band_downgrade` audit entry (e.g., VERIFIED → PLAUSIBLE when
`repo_sha` is None for a Playwright/Vitest test).

### 13.2 Multi-grammar tree-sitter dispatch

Three grammars are loaded lazily on first parse-call:

- `tree-sitter-javascript` for `.js`, `.mjs`, `.cjs`, `.jsx` (the
  JS grammar accepts JSX natively).
- `tree-sitter-typescript`'s `language_typescript()` for `.ts`.
- `tree-sitter-typescript`'s `language_tsx()` for `.tsx` (the
  typescript-only grammar treats `<>` as generics, not JSX; the
  TSX grammar is required).

The per-grammar parser cache keeps three separate parser instances.
Routing is by extension; content sniff (e.g., shebang) is a v0.2+
extension.

### 13.3 ESM and CommonJS module shapes

Both `import`/`export` (ESM) and `require`/`module.exports` (CJS)
are parsed cleanly by `tree-sitter-javascript` — no special
handling at the adapter level. The synthetic fixture exercises
both shapes (`src/routes/users.js` is CJS; `src/routes/sessions.mjs`
is ESM) so the band-distribution test catches regressions.

### 13.4 Test-first extraction granularity

Per-`test(...)`-block (Playwright) + per-`it(...)`/`test(...)`-block
(Jest/Mocha/Vitest). Each block becomes one VERIFIED-band AC. The
enclosing `test.describe(...)` (or `describe(...)`) provides
context — captured in the AC text + citation, but not its own AC
(matching Cycle 3's per-`it`-block convention).

### 13.5 Test-runner identity detection

Runner identity (Playwright vs Jest vs Mocha vs Vitest) is
detected via import statements at file head:

- `import { test } from '@playwright/test'` → handled by
  `playwright_tests` recognizer.
- `import { describe, it } from 'vitest'` → vitest.
- `import { describe, it } from 'mocha'` → mocha.
- `import { describe, it } from '@jest/globals'` (or no import,
  Jest globals) → jest / unknown.

The runner identity is recorded in `evidence.citations` as
`f"{file}:{line}:{runner}:{describe}#{test}"`. Per the cycle
plan-doc Surface #6 — runner identity is METADATA, not a gate on
the VERIFIED band; the test claims VERIFIED based on its passing
state regardless of runner.

### 13.6 Test-pass assumption

Same caveat as §12.3: the JsTs adapter does NOT execute Playwright
or Jest/Mocha/Vitest tests in Cycle 4a. The VERIFIED band is
granted on the assumption that tests in the repo were passing at
the resolved `repo_sha`. The persona MUST verify test pass-state
during ratification. This is a known limitation; the band is
"VERIFIED *as-of-extraction-time-by-human-authority*" not
"VERIFIED *by automated test run*." A future `--run-tests` flag
can tighten this.

### 13.7 HYPOTHESISED inference engine

Same shape as §12.4: heuristic-based inference (no LLM call in
Cycle 4a). The 5 patterns shipped: Zod `.email()` chain → required
email; Zod `.min(N)` → minimum length; class-validator `@IsEmail()`
→ email-required; Express middleware chain with auth-named
middleware → auth-gated route; Playwright page-object `login*`/
`signIn*`/`signUp*` method → auth entry point. Each
HYPOTHESISED AC's `rationale` field captures the heuristic
provenance, making the inference chain machine-traceable.

LLM-driven HYPOTHESISED inference enters at v0.2+ under the same
rationale-required contract; the BandedAC schema is unchanged.

### 13.8 Slice-and-swarm decomposition

The JsTs adapter ships its own `slicer.py` with a JS/TS-domain
partitioning strategy (per-page-object cluster, per-route-domain,
per-test-cohort, per-src-module). The aggregator + `SliceDriftError`
class are reused from `lang/ruby/slicer.py` — drift detection is a
slice-level concern, not language-level, so a single canonical
exception class is right level of DRY (Cycle 4a Surface #4 +
RF §10 #6).

### 13.9 Plain HTML/JS file-level recognizer

HTML files containing `<script>` tags emit one PLAUSIBLE AC each
(file-level; no inline-JS AST analysis in pass-1). Per cycle
plan-doc Surface #8 — the dispatch brief explicitly named this as
"PLAUSIBLE-by-default." Deep inline-JS analysis is a v0.2+
extension.

### 13.10 Per-file routing extension

Cycle 4a extends Cycle 3's `_LANGUAGE_HINTS` table with `jsts` →
`{.js, .mjs, .cjs, .jsx, .ts, .tsx, .html, .htm}` plus `package.json`,
`tsconfig.json`, etc. The routing logic is unchanged from Cycle 3;
only the hint table grows. Multi-adapter co-existence (a Rails
project with a Node tools script) is verified by
`tests/lang/jsts/test_per_file_routing.py::test_multi_adapter_partitioning`.

### 13.11 Local-copy DRY surface (RF §10 #6) — closed in Cycle 4b

Cycle 4a took the local-copy approach for `repo_sha.py` (byte-
identical to the Ruby adapter's `repo_sha.py`), `slugify(text)`
regex (identical), and the heuristic-inference rationale-string
pattern (identical structurally). The cleanup landed in Cycle 4b
as the canonical home `loam_odd_extractor.lang._common/`:

- `_common/repo_sha.py` exposes the single canonical
  `resolve_repo_sha`; per-adapter `lang/{ruby,jsts}/repo_sha.py`
  files were deleted.
- `_common/slugs.py` exposes `slugify` + `file_slug`; per-adapter
  `_ast_utils.py` modules retain a compat-shim re-export for
  external/historical callers but recognizer modules import from
  `..._common.slugs` directly (the canonical path).
- `_common/heuristic_helpers.py` exposes
  `make_inferred_banded_ac()` — both adapters'
  `heuristic_inferences.py` modules call it instead of hand-rolling
  the `BandedAC(...)` + `Evidence(kind="inference", ...)`
  boilerplate.

`SliceDriftError` + `aggregate_slice_results` stay where they were
(defined in `lang/ruby/slicer.py`; re-exported by
`lang/jsts/slicer.py`) — already DRY (one canonical home + one
re-exporter), and moving them to `_common/` is symmetric but
cosmetic. Cycle 5+ can revisit if a Python adapter (v0.2.2+) or
other future adapter changes the calculus.

Future adapters (Python in v0.2.2+) inherit the consolidated shape:
import `resolve_repo_sha`, `slugify`, `file_slug`, and
`make_inferred_banded_ac` from `..._common`; build per-language
recognizers, AST helpers, and heuristic regex tables in
`lang/<name>/`.
