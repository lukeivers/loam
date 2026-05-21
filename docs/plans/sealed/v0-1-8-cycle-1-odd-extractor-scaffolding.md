# v0.1.8 Cycle 1 — odd-extractor scaffolding (NEW component)

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, build dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** master plan `docs/plans/v0-1-8-master-plan.md` sealed at `1c2c478`.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/plans/v0-1-8-master-plan.md` §3 + §4 Cycle 1.

**Status file:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-8-cycle-1-status-2026-05-04.md`.

**Quality bar (load-bearing):** "WOW Eric. No partial features. No excuses." — Luke 2026-05-04. The scaffold ships COMPLETE; if any AC ships partial we halt and surface.

---

## §1 — Outcome shape (the "why")

v0.1.8 ships an extractor that reads codebases and emits confidence-banded ODD contract drafts. Cycle 1 lands the **shape without content** — a four-stage workflow (init → analyze → generate → verify), a language-adapter registry that ships zero adapters, a dry-run mode powered by the v0.1.6 cost-governance primitive, and a foreign-codebase budget envelope. Cycles 2–4 fill in bands + Ruby + Python; Cycle 5 ships SKILLs.

Cycle 1's release-note promise: `loam odd-extract <repo>` runs end-to-end against any directory, walks the four stages in dry-run mode, produces an empty-but-well-shaped contract draft + per-stage artefacts, surfaces a budget estimate before any LLM calls, and refuses to run live on a repo above the configurable budget ceiling without `--budget-override`.

The shape is the deliverable. The content (Ruby/Python adapters) is explicitly not in this cycle's fence.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

The extractor composes on top of Claude-native primitives rather than re-implementing them:
- **Cost-governance dry-run primitive (v0.1.6).** `dry_run_estimate(scope_id=, recent_actuals=)` returns an `EstimateResult`; the extractor wraps this in its budget surface. No re-implementation.
- **`BudgetEnvelope` Pydantic model (v0.1.6).** The extractor's `--budget-override` flag toggles the envelope's `overrun_action`; the runtime is borrowed.
- **Plan-doc + manifest discipline.** Every extracted contract is plan-doc-shaped — it produces a markdown artefact at `<workspace>/.loam/extractions/<repo-id>/contract-draft.md`, parallel to the existing `docs/plans/` shape. Cycle 2 adds confidence bands; Cycle 3+4 populate.

The required research question — **"What Claude capability does this lean on or extend?"** — answer: cost-governance dry-run + budget envelope (composed) + persona walk-through (Cycle 2's ratification flow extends; this cycle ships only the produce-an-empty-draft seam).

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden drops because the persona no longer has to hand-roll "walk this codebase + produce ACs"; the extractor produces the scaffold + the persona just helps the user ratify (Cycle 2). Cycle 1's seam is "the extractor exists and runs"; the primary-persona work is in Cycles 2+5.
- **Harness test:** every persona that does code-archaeology can call the extractor's Python API instead of re-implementing repository walking. Cycle 1 ships the API surface; Cycle 5's `dispatch-brief-authoring` SKILL composes against it.

Both pass.

### Lens 3 — ODD authoring

Outcome above + named ACs (§4) + halt triggers (§5) + acceptance smoke (§6). Method (file structure / API shapes / state shape / which subprocess for repo walk) stays the builder's call.

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH** for shape: master plan §3 names the four-stage workflow, the registry contract (`supports(repo)` + `extract(repo, plan)`), the dry-run-default rule (Decision D), the budget envelope (v0.1.6). Tight scope: extend the dev-sdlc plugin tree with a new sub-package; halt-and-surface if the master plan's named contract turns out unimplementable. Method (where each stage lives in code, single-module vs four-module split, how the registry walks subdirectories) stays the builder's call.

Outcome confidence is **MEDIUM** for the language-adapter contract: master plan names `supports(repo)` + `extract(repo, plan)` but the input/output Pydantic shapes are the builder's call. The registry tests the *contract*, not specific shapes — adapters in Cycle 3+4 will need richer input/output, and the contract should not constrain that prematurely. The shape ships LOOSE in Cycle 1 (Pydantic models with `extra='forbid'` per cost-governance precedent, but minimal required fields); Cycle 3 will tighten as the Ruby adapter lands.

### Lens 5 — Swarming

Single-component fence under the dev-sdlc plugin tree. Within the cycle, decomposition options:
- (a) one-file per stage (init.py, analyze.py, generate.py, verify.py) — natural decomposition, each with its own AC test. Tighter per-stage acceptance criteria; meets stopping criterion.
- (b) one-file per concern (workflow.py, registry.py, budget.py, cli.py) — also tighter per-concern; also meets stopping criterion.

The builder picks (a) — per-stage decomposition matches the master plan's §3 four-stage naming and gives the tightest AC-per-file mapping. `max_planner_depth: 1` (no sub-planners; per-stage files are the right granularity already). No further decomposition adds value.

---

## §3 — Single-component fence

**Scope:** `plugins/dev-sdlc/` (the existing dev-sdlc plugin's sealed fence; the odd-extractor lands as a NEW sub-package under it).

**New paths (this cycle):**

- `plugins/dev-sdlc/odd-extractor/` (NEW directory)
  - `pyproject.toml` — separate distribution, mirrors `plugins/dev-sdlc/tools/loam-amend/pyproject.toml` precedent.
  - `README.md` — what-this-component-is + cycle-status pointers.
  - `src/loam_odd_extractor/__init__.py` — public API re-exports.
  - `src/loam_odd_extractor/spec.py` — Pydantic models (`ExtractionConfig`, `AnalysisPlan`, `RawACs`, `ContractDraft`, `LanguageAdapterContract`).
  - `src/loam_odd_extractor/init.py` — Stage 1: configure repo + budget envelope.
  - `src/loam_odd_extractor/analyze.py` — Stage 2: walk repo, plan extractions per language adapter.
  - `src/loam_odd_extractor/generate.py` — Stage 3: dispatch per-language extractions (zero adapters in Cycle 1 → empty result).
  - `src/loam_odd_extractor/verify.py` — Stage 4: post-process + ODD §2.5 coverage check.
  - `src/loam_odd_extractor/registry.py` — language-adapter registry with `register_adapter`, `discover_adapters`, `LanguageAdapter` Protocol.
  - `src/loam_odd_extractor/budget.py` — dry-run estimate wrapper + foreign-codebase envelope check.
  - `src/loam_odd_extractor/state.py` — extraction state (workspace-scoped at `<workspace>/.loam/extractions/<repo-id>/`).
  - `src/loam_odd_extractor/observability.py` — audit-log entry writer (one entry per stage, one entry per extraction-run).
  - `src/loam_odd_extractor/cli.py` — `build_odd_extract_subcommand` builder for `loam odd-extract` registration via `loam.cli.subcommands` entry-point group.
  - `src/loam_odd_extractor/errors.py` — typed exceptions (`OddExtractorError`, `BudgetExceededError`, `RegistryError`, `StageError`).
- `plugins/dev-sdlc/odd-extractor/tests/` — per-AC test files (one file per AC.OREK.{1..7}).
- `plugins/dev-sdlc/odd-extractor/seals/` — empty at Cycle 1; populated at seal time.

**Edits to existing dev-sdlc paths (universal-admitted within fence):**

- `plugins/dev-sdlc/pyproject.toml` — no edit required; the odd-extractor pyproject is independent (loam-cli discovers the subcommand via the new pyproject's entry-point).
- `plugins/dev-sdlc/README.md` — append a "Sub-packages" section pointing at `odd-extractor/`.

**Composition (read-only, no edit):**

- `framework/cost-governance/` — import `dry_run_estimate`, `EstimateResult`, `BudgetEnvelope`, `OverrunAction`. No edits to cost-governance.
- `framework/tools/loam/` — depends on the unified loam CLI's `loam.cli.subcommands` entry-point group; no edit required (the dev-sdlc plugin's installation-time entry-point declaration is enough).

**Universal-admitted prefixes/files (off-fence, allowed under standard amendment policy):**

- `docs/plans/` — this plan-doc + manifest.
- `CLAUDE.md`, `docs/odd-in-loam.md`, `docs/odd-methodology.md`, `docs/STATE.md` — universal admission per `dev-pattern-simplifications-2.manifest.yaml` precedent.

**Out-of-fence (would halt-and-surface):**

- Any framework/ component edit other than read-only imports of cost-governance.
- Any other plugin (loam-skills/) edit.
- Any actual language-adapter implementation (Cycles 3+4).

---

## §4 — AC family — `AC.OREK.*` (locked)

Each AC has at least one explicit pytest under `plugins/dev-sdlc/odd-extractor/tests/test_AC_OREK_<n>_<slug>.py`. ODD §2.5 — every line of code, every branch, every test maps to a named AC.

- **AC.OREK.1 — Component scaffold present.**
  - `plugins/dev-sdlc/odd-extractor/` exists with `pyproject.toml`, `README.md`, `src/loam_odd_extractor/`, `tests/`, `seals/` directories.
  - `pyproject.toml` declares `name = "loam-odd-extractor"`, `version = "0.1.0"`, `requires-python = ">=3.13"`, dependency on `loam-cost-governance` + `loam-cli`.
  - `pyproject.toml` registers `[project.entry-points."loam.cli.subcommands"] odd-extract = "loam_odd_extractor.cli:build_odd_extract_subcommand"`.
  - Test: structural — files exist; pyproject parses; entry-point declaration present.

- **AC.OREK.2 — `loam odd-extract <repo-path>` CLI invocable.**
  - `loam odd-extract --help` lists the subcommand.
  - `loam odd-extract <path>` runs in dry-run mode by default (no `--live` flag) per Decision D.
  - `--live` flag opt-in; `--live` without `--budget-override` triggers AC.OREK.6 envelope check.
  - `--budget-cents <int>` sets the hard-cap money ceiling; `--budget-override` opts-out of the foreign-codebase ceiling check.
  - `--workspace-root <path>` overrides default cwd.
  - Test: dispatches the CLI builder; verifies argparse surface; runs subcommand against a tmp fixture; asserts dry-run produces an estimate without invoking any LLM.

- **AC.OREK.3 — Four-stage workflow with structured per-stage artefacts.**
  - Each stage is a pure function (input → output, no global state).
  - Stage 1 (`init`): input `(repo_path, budget, workspace_root)` → output `ExtractionConfig` written to `<workspace>/.loam/extractions/<repo-id>/config.yaml`.
  - Stage 2 (`analyze`): input `ExtractionConfig` → output `AnalysisPlan` written to `<workspace>/.loam/extractions/<repo-id>/plan.yaml`. Walks the repo via `pathlib`, classifies each path by language hint, builds per-adapter slice-list (zero adapters in Cycle 1 → all paths in `unhandled_paths`).
  - Stage 3 (`generate`): input `AnalysisPlan` → output `RawACs` written to `<workspace>/.loam/extractions/<repo-id>/raw-acs.yaml`. With zero adapters, output is empty `acs: []` + `unhandled_paths: [<all-from-plan>]`.
  - Stage 4 (`verify`): input `RawACs` → output `ContractDraft` markdown + sidecar YAML at `<workspace>/.loam/extractions/<repo-id>/contract-draft.md` + `contract-draft.yaml`. With empty raw-ACs, draft contains only an "Unhandled paths" section listing files not yet covered by any adapter.
  - Each stage is invocable independently (e.g., `loam odd-extract --stage analyze`) for testing + future scriptability.
  - Test: each stage's input → output contract, exercised against a tmp fixture (small synthetic repo with a couple of files).

- **AC.OREK.4 — Language-adapter registry.**
  - `LanguageAdapter` Protocol exposes `name: str`, `supports(repo: Path) -> bool`, `extract(repo: Path, plan: AnalysisPlan) -> RawACs`.
  - Registry exposes `register_adapter(adapter)` + `discover_adapters() -> list[LanguageAdapter]`.
  - Discovery via entry-point group `loam.odd_extractor.language_adapters` (lazy resolution; mirrors `loam.cli.subcommands` precedent).
  - At Cycle 1, zero adapters ship; `discover_adapters()` returns `[]`.
  - Registry handles registration failure (entry-point load error / non-callable / Protocol-violation) with a logged warning and skips the offending entry-point per `loam.cli.subcommands` precedent.
  - Test: registry initialises empty; manual `register_adapter(stub)` works; entry-point discovery returns []; Protocol-violator raises `RegistryError`.

- **AC.OREK.5 — Dry-run cost estimate via cost-governance primitive.**
  - `budget.estimate_for_extraction(scope_id, recent_actuals)` wraps `loam.cost_governance.dry_run_estimate` and returns the `EstimateResult` unchanged.
  - Every CLI invocation calls `estimate_for_extraction` BEFORE any actual extraction work.
  - Estimate surfaces in the CLI's stdout output as a structured block (`estimated_money_cents`, `estimated_tokens`, `estimated_time_seconds`, `confidence_band`, `reason`).
  - In dry-run mode (default), the estimate is the only output; no extraction work runs.
  - In `--live` mode, estimate runs first; extraction work runs after the budget envelope check passes.
  - Test: CLI invocation returns the estimate fields; cold-start (no recent actuals) returns LOW band + non-empty reason.

- **AC.OREK.6 — Foreign-codebase budget envelope.**
  - `BudgetEnvelope` Pydantic model from cost-governance attaches to each extraction run's `ExtractionConfig`.
  - Default ceiling: `hard_cap_money_cents = 1000` (= $10), `soft_cap_money_cents = 500` (= $5), `overrun_action = halt`. Configurable via `--budget-cents <int>` flag (sets both caps to this value).
  - Live extraction (`--live`) without `--budget-override` enforces the ceiling: if the dry-run estimate's `estimated_money_cents > hard_cap_money_cents`, refuse to run live and exit with a non-zero status + structured `BudgetExceededError` message naming the ceiling + estimate.
  - `--budget-override` opts out: live runs proceed regardless of estimate vs ceiling. Audit-log entry records the override.
  - Test: `--live` without override + estimate > ceiling raises BudgetExceededError; `--live --budget-override` proceeds; dry-run mode never enforces (the ceiling check is `--live`-only).

- **AC.OREK.7 — Component-level test surface.**
  - Per-AC test files: `test_AC_OREK_1_component_scaffold.py` ... `test_AC_OREK_7_component_test_surface.py` (one file per AC).
  - Plus integration tests:
    - `test_full_workflow_dry_run.py` — end-to-end `init → analyze → generate → verify` against a tmp fixture in dry-run mode; asserts all four artefacts land at the expected paths; asserts the contract draft is well-formed (parses as markdown; sidecar parses as YAML).
    - `test_audit_log_entries.py` — D6 telemetry-floor: each stage writes one audit-log entry; each extraction run writes a start + end entry.
    - `test_cross_session_state.py` — D5: state.yaml at `<workspace>/.loam/extractions/<repo-id>/state.yaml` survives a fresh process invocation; resume reads prior state; `--resume` flag picks up where a paused run left off.
    - `test_steady_state_idempotent.py` — D2 (within scope): 5 init→analyze→generate→verify cycles against the same fixture produce byte-identical artefacts (no spurious diffs from non-determinism). Uses fixed timestamps via clock injection where needed.
    - `test_no_sealed_amendments.py` — seal-fence test (mirrors `plugins/dev-sdlc/tests/test_no_sealed_amendments.py`, scoped to the odd-extractor sub-tree).
  - All tests must pass before seal.

---

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

### Surface #1 — sub-package vs top-level plugin (no halt — recorded)

**Decision (autonomous):** odd-extractor lands at `plugins/dev-sdlc/odd-extractor/` (a sub-package of the dev-sdlc plugin's tree, with its own pyproject.toml). Master plan §2 explicitly names this path. Precedent: `plugins/dev-sdlc/tools/loam-amend/` is also a separately-pyproject'd package living inside dev-sdlc's sealed fence. The dev-sdlc plugin's seal-test (`plugins/dev-sdlc/tests/test_no_sealed_amendments.py`) gates the entire `plugins/dev-sdlc/` sub-tree, so the odd-extractor's diff lands inside that fence.

Rationale: avoids creating a new top-level `plugins/<name>/` component (which would require its own contribution registration + seal-test scaffolding), reuses the existing dev-sdlc plugin's sealed-component infrastructure, matches the master plan's named placement.

### Surface #2 — language-adapter Protocol shape (no halt — recorded)

**Decision (autonomous):** `LanguageAdapter` is a `typing.Protocol` (not an ABC). Methods: `name: str`, `supports(repo: Path) -> bool`, `extract(repo: Path, plan: AnalysisPlan) -> RawACs`.

Rationale: Protocol is the v0.1.6 / v0.1.7 convention (`MemoryProvider` Protocol pattern; cost-governance pure-functional + Protocol shapes). Allows duck-typing for tests + future adapters without inheritance overhead. Forward-compat: Cycle 3 (Ruby) + Cycle 4 (Python) can extend the Protocol with optional methods (e.g., `supports_test_first(repo)`) without breaking Cycle 1's contract.

The Protocol is intentionally LOOSE per Lens 4 medium-confidence: input is `(Path, AnalysisPlan)` and output is `RawACs`; the AnalysisPlan + RawACs Pydantic shapes carry minimal required fields (`paths: list[Path]`, `acs: list[dict]`) so adapters can extend per-language.

### Surface #3 — entry-point group name for adapters (no halt — recorded)

**Decision (autonomous):** `loam.odd_extractor.language_adapters` (underscored, namespace-prefixed). Mirrors `loam.cli.subcommands` (loam-cli) and `loam.bootstrap.contributions` (workspace-bootstrap) precedents. Underscored to match Python entry-point convention.

Rationale: explicit namespace prevents collision with future loam features. Discovery via `importlib.metadata.entry_points(group=...)` is the canonical pattern.

### Surface #4 — workspace state location (no halt — recorded)

**Decision (autonomous):** `<workspace>/.loam/extractions/<repo-id>/` for all per-extraction state. `<repo-id>` is a slug derived from the repo's absolute path (last directory segment + 8-char hash of the absolute path, separated by `-`). This handles the case where multiple workspaces extract the same repo (different absolute paths → different repo-ids).

Rationale: matches ODD-RE research §3.4 recommendation. Cycle 2's ratification and Cycles 3+4's slice outputs share the same root. Composes with the existing `<workspace>/.loam/` namespace (M-FBM uses `<workspace>/.loam/memory/`; PM uses `<workspace>/.loam/pms/<pm-name>/`; extractions get their own sibling).

### Surface #5 — repo-id determinism (no halt — recorded)

**Decision (autonomous):** repo-id format: `<basename>-<8-char-sha256-hex-of-abs-path>`. Sha256 is overkill but consistent with cost-governance store IDs. 8 hex chars = 32 bits collision space, ample for a per-workspace identifier.

Rationale: deterministic (same abs path always → same id); collision-resistant within reasonable workspace sizes; human-readable prefix (the basename) for ergonomics.

### Surface #6 — dry-run as default (Decision D from master plan)

**Decision (locked by master plan):** `loam odd-extract <repo>` runs in dry-run mode by default; `--live` is opt-in. No autonomous decision needed; the dispatch enforces this.

### Surface #7 — budget defaults (no halt — recorded)

**Decision (autonomous):** default `hard_cap_money_cents = 1000` ($10), `soft_cap_money_cents = 500` ($5), `overrun_action = halt`. These are bound to be revisited when actual extraction runs land in Cycles 3+4 — the values reflect "small foreign codebase" expectations and may be tuned.

Rationale: ten dollars is enough for a realistic dry-run-for-budget-estimate-only scenario; halt-on-overrun is the safe default per the BudgetEnvelope semantics. `--budget-cents <int>` overrides both caps to the same value.

### Surface #8 — audit-log entry shape (no halt — recorded)

**Decision (autonomous):** mirror per-project-pm's `audit-log/<YYYY-MM-DD>-<NNNN>.yaml` shape. NNNN counter is per-extraction-run (not per-day) since extractions are bounded. Schema:

```yaml
schema_version: 1
event_kind: extraction_start | stage_complete | extraction_end | budget_override
timestamp: <iso8601-tz>
extraction_id: <repo-id>
stage: init | analyze | generate | verify | <null for non-stage events>
artefact_path: <relative path under .loam/extractions/<repo-id>/ | null>
estimate: <EstimateResult dict | null>
notes: <free-form string>
```

The audit-log lives at `<workspace>/.loam/extractions/<repo-id>/audit-log/`. D6 telemetry-floor: each stage writes one `stage_complete` entry; each run writes `extraction_start` + `extraction_end` (or `extraction_failed`) bookend entries.

Rationale: precedent reuse (per-project-pm); SOC-2 audit-trail floor (Decision P); diagnosable by reading YAML files (no proprietary log format).

### Surface #9 — Pydantic model shape (no halt — recorded)

**Decision (autonomous):** all spec models use `pydantic.BaseModel` with `ConfigDict(extra='forbid')`. Mirrors cost-governance + per-project-pm conventions. Fields default to required; optional fields use `... | None = None`.

Models:
- `ExtractionConfig` — `repo_path: Path`, `repo_id: str`, `workspace_root: Path`, `budget: BudgetEnvelope`, `dry_run: bool`, `created_at: str` (ISO8601).
- `AnalysisPlan` — `extraction_id: str`, `slices: list[Slice]`, `unhandled_paths: list[Path]`, `created_at: str`.
- `Slice` — `slice_id: str`, `adapter_name: str`, `paths: list[Path]`.
- `RawACs` — `extraction_id: str`, `acs: list[dict]`, `unhandled_paths: list[Path]`, `per_slice_costs: dict[str, dict]`.
- `ContractDraft` — `extraction_id: str`, `markdown_path: Path`, `sidecar_path: Path`, `ac_count: int`, `unhandled_count: int`.

### Surface #10 — D2/D3/D4 smoke applicability (no halt — recorded)

**Decision (autonomous):** the extractor is invoked-on-demand (not a long-running daemon). Per smoke-test-discipline §6 quick-reference card, "one-shot CLI / library? Dimensions 1, 5, 6 only." Dimensions D2 (steady-state durability over sustained load), D3 (restart resilience under signal), and D4 (full reboot) do not apply structurally.

But — the master plan dispatch wording asks all 6 dimensions exercised at cycle level. The interpretation: D1, D5, D6 are exercised against the extractor's named ACs; D2, D3, D4 are exercised at the level "the extractor remains a clean Python library invocable within any process — no leaked state, no zombie processes, no per-process global state." The latter is *structurally true by design* (pure functions per stage, no global state, no daemon loop).

Resolution per master plan dispatch text "D2 / D3 / D4: n/a per cycle scope (extractor is invoked-on-demand, not a long-running daemon); document n/a in plan-doc": D2/D3/D4 marked `n/a` here in §6 with one-sentence rationale per dimension. Cycle 5+ (long-running process candidates like a continuous codebase-watch) would re-engage these dimensions.

Plus: D2 *within applicability* — running the same extraction five times produces byte-identical artefacts. This is a *steady-state-of-the-extraction-itself* test, distinct from the daemon-style D2. Captured as `test_steady_state_idempotent.py` per AC.OREK.7. This satisfies the master plan's "D2 steady-state: 5+ init/analyze runs idempotent" wording from the dispatch brief.

### Surface #11 — release-note promise mapping (no halt — recorded)

**Decision (autonomous):** the master plan's quality bar requires every release-note promise correspond to tested + reliable behavior. Release-note promises this cycle:

| Promise | Backing AC | Test |
|---|---|---|
| "extractor scaffolds and runs end-to-end" | AC.OREK.1 + AC.OREK.2 + AC.OREK.3 | `test_full_workflow_dry_run.py` |
| "dry-run produces a budget estimate" | AC.OREK.5 | `test_AC_OREK_5_*.py` |
| "language-adapter registry exists; adapters land in cycles 3+4" | AC.OREK.4 | `test_AC_OREK_4_*.py` |
| "foreign-codebase budget envelope refuses runaway live runs" | AC.OREK.6 | `test_AC_OREK_6_*.py` |
| "extraction state survives /clear" | D5 smoke + AC.OREK.7 (cross-session test) | `test_cross_session_state.py` |
| "audit-log entry per stage" | D6 smoke + AC.OREK.7 (audit-log test) | `test_audit_log_entries.py` |

If any test in the right column FAILs at build time, the corresponding promise gets de-shipped (not partially-shipped) — halt-and-surface to dispatcher.

---

## §6 — Smoke (REALISTIC CONDITION — applicable dimensions per smoke-test-discipline §6)

Cycle-level smoke. Release-level HARD gate at v0.1.8 close (master plan §5 + Decision R), not this cycle.

### D1 — cold-state (fresh canonical workspace)

**Pattern.** Tmp directory as workspace root; tmp directory as fixture repo (containing a couple of synthetic .py / .rb / README files). Run `loam odd-extract <fixture>` in dry-run mode. Assert: (a) all four stage artefacts land at expected paths under `<tmp-workspace>/.loam/extractions/<repo-id>/`; (b) `contract-draft.md` exists, parses as markdown, has an "Unhandled paths" section listing every fixture path; (c) stdout carries the `EstimateResult` block; (d) exit status 0.

**Test:** `test_full_workflow_dry_run.py`.

### D2 — steady-state durability (n/a structurally; idempotency variant covered)

**Structural rationale.** The extractor is a one-shot CLI / library, not a long-running daemon. There is no queue, no producer/consumer pair, no log volume to bound. Smoke-test-discipline §6 quick-reference: one-shot CLI doesn't engage D2.

**Idempotency variant exercised.** AC.OREK.7's `test_steady_state_idempotent.py` runs the extraction five times against the same fixture and asserts byte-identical artefacts (modulo timestamp fields injected through clock injection). This satisfies the master plan dispatch's "D2 steady-state: 5+ init/analyze runs idempotent" wording.

### D3 — restart resilience (n/a)

**Structural rationale.** No long-running process to kill. The extractor invocation is a single Python process; if it crashes mid-run, the next invocation reads `state.yaml` and resumes (Cycle-2-and-later behaviour). Restart resilience for the Python process itself is the OS's concern; loam doesn't supervise extractor invocations.

### D4 — reboot resilience (n/a)

**Structural rationale.** Same as D3 — no daemon to recover after host reboot. Cross-session continuity (D5) is the relevant analog.

### D5 — cross-session continuity

**Pattern.** Test setup invokes the full workflow against a fixture in process A (inside the test's pytest worker). Then constructs a fresh `ExtractionConfig` in process B (a subprocess invocation of the CLI) pointing at the same workspace root + repo path. Asserts: (a) state.yaml at `<workspace>/.loam/extractions/<repo-id>/state.yaml` exists from A's run; (b) B's `loam odd-extract --resume <repo>` reads A's state and reports "extraction already complete" (no duplicate extraction); (c) `loam odd-extract --status <repo>` from B reads A's artefacts and prints the stage statuses.

**Test:** `test_cross_session_state.py`.

The `/clear` analog is "fresh process boundary"; the test validates that boundary directly (subprocess vs in-process).

### D6 — telemetry floor

**Pattern.** Run a full extraction; assert: (a) `<workspace>/.loam/extractions/<repo-id>/audit-log/` directory exists; (b) one `extraction_start` entry; (c) four `stage_complete` entries (one per stage); (d) one `extraction_end` entry; (e) every entry carries `schema_version: 1`, `timestamp` (ISO8601 with TZ), `extraction_id`, `event_kind`. Filenames follow `<NNNN>.yaml` with monotonic sequence.

**Test:** `test_audit_log_entries.py`.

---

## §7 — Out of scope

Explicit deferrals (master plan §3 Cycle 1 + per-cycle dispatch):

- **Confidence bands.** VERIFIED / PLAUSIBLE / HYPOTHESISED schema → Cycle 2.
- **Ratification workflow.** `loam odd-extract ratify <draft>` → Cycle 2.
- **PM integration.** Composing with `framework/per-project-pm/` for the ratification queue → Cycle 2.
- **Ruby/Rails adapter.** First-class extractor for ActiveRecord, callbacks, concerns, polymorphic associations, ActiveJob/Sidekiq → Cycle 3.
- **Python adapter.** Mirror Ruby coverage for Python → Cycle 4.
- **Smoke fixtures.** Python-Flask-payment + Ruby-Rails-payment full fixtures → Cycle 4.
- **6 dev-sdlc SKILLs.** `loam-amend-cycle`, `dispatch-brief-authoring`, etc. → Cycle 5.
- **Continuous codebase-watch.** Long-running daemon mode → v0.2.0+.
- **Aggregator + slice-and-swarm.** ODD-RE research §3 patterns → Cycle 3 (Cartographer-style for SaaS scale).
- **Persona walk-through flow.** Conversational ratification → Cycle 2 + persona-side wiring at v0.2.0+.

---

## §8 — Halt triggers (in-flight)

Per dispatch + master plan:

- **WD drifts.** If `git rev-parse --show-toplevel` is not `/Users/lukeivers/ivers-corp-pos-v2/`, halt + surface.
- **Plan-doc not authored before code.** This document IS that plan-doc. If code lands before this is committed, halt.
- **Any AC ships partial.** If `test_AC_OREK_<n>_*.py` is XFAIL, skipped, or asserts a degraded behaviour, halt + reframe before sealing.
- **D5 cross-session smoke fails.** This is the ship-test for cross-session continuity per master plan §3 Cycle 1 dispatch; halt unconditionally on red.
- **Cycle exceeds 5 hours wall-clock.** Halt with partial findings; consider further decomposition (e.g., split CLI from registry into separate sealable units).
- **ODD violations discovered in surrounding code.** Halt + surface; do not silently extend (per `feedback_subagent_odd_violation_halt`).
- **More than 3 in-build decisions need Luke escalation.** Master plan recommends 5; this dispatch tightens to 3 since the cycle is foundational.
- **Master plan's Cycle 1 scope reveals a structural unknown.** If a named AC turns out to require Cycle-2-or-later infrastructure, halt + surface.

---

## §9 — Bookkeeping

- **Manifest:** `docs/plans/v0-1-8-cycle-1-odd-extractor-scaffolding.manifest.yaml` — schema_version: 3 with `plan_doc_ref:`. amendment.number omitted per AC.DPS1.10. ac_count: 7. smoke_outcome: "D1 + D5 + D6 exercised; D2 idempotency variant exercised; D3/D4 n/a per smoke-test-discipline §6".
- **Apply:** `loam amend apply` — single merged manifest+apply commit per AC.DPS1.6 (v3 schema).
- **Seal:** `loam amend seal --plan-doc docs/plans/v0-1-8-cycle-1-odd-extractor-scaffolding.md` — synthesizes 5–15 line narrative body per AC.DPS2.{1,4} into `plugins/dev-sdlc/seals/SEAL_COMMIT.v0-1-8-cycle-1-odd-extractor-scaffolding`.
- **§14 backfill:** master plan `docs/plans/v0-1-8-master-plan.md` §9 method-decision register row for v0.1.8 Cycle 1 — doc-only commit after seal.
- **No tag push.** v0.1.8 tag waits on Cycles 2–5 + release-level HARD gate (Decision R).

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **The `loam.odd_extractor.language_adapters` entry-point group has zero adapters in this cycle.** Worth flagging: the registry can return `[]` cleanly, but the *integration* with adapters is untested until Cycle 3 lands the first adapter. Cycle 1's registry test uses a stub adapter (registered manually in-test) to exercise the registration path; entry-point-driven discovery only tests the empty case. This is a known coverage gap that closes when Cycle 3's Ruby adapter ships.

2. **Budget defaults (`$10` hard cap, `$5` soft cap) are guess-shaped.** No empirical basis — they're chosen as "reasonable starter ceilings for a foreign codebase dry run". They will be revisited in Cycle 3 (first real extraction with real costs) and Cycle 4 (Python adapter calibration). Flagged in `FUTURE_IDEAS_DRAFT.md` (or surfaced to dispatcher) as a tunable.

3. **The `ContractDraft` markdown shape ships skeletal in Cycle 1.** It contains only an "Unhandled paths" section — no AC structure, no confidence bands. Cycle 2 fills this in. The Cycle 1 shape MUST be forward-compatible: the markdown structure leaves named anchors (e.g., `<!-- ACS_TABLE_HERE -->` HTML comments) where Cycle 2 will inject. If those anchors are missing or wrong-named, Cycle 2's plan-author dispatch needs to authoring around them or re-architect. Builder verifies anchor placement against the Cycle 2 master plan AC.BANDS.* family.

4. **Cycle 1's `verify` stage performs a no-op coverage check** (since RawACs is empty, every fixture path lands in `unhandled_paths`). The "ODD §2.5 coverage check" promised in the AC seed is shape-only — Cycle 2's bands and Cycle 3+4's adapters are what make the check meaningful. Honest framing.

5. **`--resume` flag semantics are stub-shaped in Cycle 1.** Since extractions are zero-AC + nearly free in dry-run, "resume" is mostly a no-op (reads state, reports "complete"). The full mid-extraction-pause-and-resume mechanism (per ODD-RE research §3.4 / §3.5) lands when actual adapter work + token-budget instrumentation engage in Cycles 3+4.

6. **Loose vs tight scope check.** Per Lens 4: outcome confidence HIGH for shape; MEDIUM for adapter contract. The Pydantic models for `AnalysisPlan` / `RawACs` ship with minimal-required fields and `extra='forbid'`. If Cycle 3 needs additional fields (e.g., per-slice token budgets), it will tighten via additive Pydantic model migration — schema versions if necessary. Builder flags any field that *might* tighten in Cycle 3 with a code-comment marker.

7. **Manifest schema v3 first-real-build-use after DPS2 introduction.** DPS2 was the first amendment to use v3; this is the second. Watch for any v3-specific tooling defects that DPS2 didn't catch (e.g., synthesizer edge cases when ac_count > 10, sidecar SHA pin behaviour). Builder verifies the seal commit shape post-apply matches DPS2's expectations.

---

## §11 — Provenance trail

- v0.1.6 production-safety + cost-governance — sealed at `3f1d237` + `88674cb`. Provides `dry_run_estimate` + `BudgetEnvelope` + `OverrunAction`.
- v0.1.7 per-project-pm + layered-skill discovery + one-question-at-a-time — sealed at `3aa20dd` + `73505f0` + `bcf699a` + `122a7c8`. Provides composition substrate for Cycle 2 (ratification workflow) but not directly used in Cycle 1.
- Dev-pattern-simplifications #1 + #2 (manifest schema v3 + seal-narrative compression) — sealed at `019cfca` + `df3f50f`. This cycle uses v3 schema.
- v0.1.8 master plan — sealed at `1c2c478`. This cycle is its first build.
- ODD-RE research at `<pos3>/.scratch/claude-output/odd-reverse-engineering-skill-research.md` (907 lines) — D-Q.RE.{1..8} sub-decisions. Method-level guidance for adapter contract + budget instrumentation + state shape.
- Smoke-test-discipline at `plugins/dev-sdlc/docs/smoke-test-discipline.md` — six dimensions; D2/D3/D4 marked n/a per quick-reference card §6.
- ODD-methodology at `plugins/dev-sdlc/docs/odd-methodology.md` — every line maps to a named AC.

---

## §12 — Acceptance gate

This plan-doc is gate-ready when:

1. All 7 AC.OREK.* families named with explicit pytest paths (§4) ✓
2. Single-component fence named (§3) ✓
3. All 6 smoke dimensions addressed — applicable exercised, n/a documented (§6) ✓
4. Halt triggers named (§8) ✓
5. Bookkeeping path named (§9) ✓
6. F2 gaps named (§10) ✓

Build proceeds.
