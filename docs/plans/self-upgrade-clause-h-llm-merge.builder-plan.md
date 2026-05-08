# self-upgrade clause-(h) — builder-plan

**Authored:** 2026-04-26 by build-agent (BB-feat re-dispatch
post-amendment-#53 retrofit landing).
**Companion plan:** `docs/plans/self-upgrade-clause-h-llm-merge.md`.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment baseline:** 122 self-upgrade tests pass at HEAD `8ae1b82`
(post-amendment-#53 SHA-record commit). The previous BB build attempt
authored a stale builder-plan that bundled AC.H.0 retrofit work; that
work landed as amendment #53 separately. This builder-plan supersedes
the stale one and scopes strictly to clause-(h) feat code per the
re-dispatch (Resolution enum extends; ConflictEntry schema extends;
clause-(h) verifier; `--canonical` argparse + staging-resolver helper;
LLM-mediated merge resolver).

This builder-plan captures (a) **method choices** (D-build.x) within
the AC outcome bounds, (b) the **§2.5 reverse-direction trace** (one
row per code path → AC), and (c) the **build sequence** the agent
will execute.

---

## Section A — Method choices (D-build.x)

Per ODD §2.5 + plan §10 trigger 3 (no method-in-AC): the AC text says
WHAT, this section says HOW. Each row is the builder's call within
the AC's outcome bound.

### D-build.1 — canonical-pull adapter (AC.H.1)

**Choice.** Add new module `self-upgrade/src/self_upgrade/canonical.py`
exposing `resolve_canonical_to_staging(canonical_path: Path,
manifest_path: Path | None, tag: str) -> StagingResolution`. Returns
a dataclass `StagingResolution(staging_dir: Path, manifest: Manifest)`.

- `canonical_path` must resolve to a directory containing the
  unpacked tree (the local-canonical repo IS the staging shape;
  no copy needed unless clause-(h) merging requires writing
  merged-content overlays).
- Manifest path defaults to
  `<canonical_path>/self-upgrade/manifests/<tag>.yaml`; overridden
  by `manifest_path` if supplied.
- For the local-canonical case `staging_dir == canonical_path`.

Argparse mutex group on `--canonical` vs `--staging-dir` via
`add_mutually_exclusive_group(required=True)`. When `--canonical`
is supplied without `--manifest`, the manifest path is derived
from `--tag`.

**Why.** Composes onto existing `execute_upgrade(staging_dir=...)`
without rebuilding the pipeline. The `--staging-dir` codepath
remains byte-identical (the only argparse change is the mutex
group around the two flags).

### D-build.2 — Resolution enum extension (AC.H.4)

**Choice.** Extend the closed-set `Resolution` enum in
`self-upgrade/src/self_upgrade/conflict_report.py` with three
inferred values, all distinct from `skipped`:

```
INFERRED_ACCEPT_CANONICAL = "inferred-accept-canonical"
INFERRED_ACCEPT_WORKSPACE = "inferred-accept-workspace"
INFERRED_MERGED = "inferred-merged"
```

The `_reject_skipped` validator stays intact (clause-(g) structural
guarantee preserved). The `_resolution_requires` model_validator
gains a clause for `INFERRED_MERGED`: requires `resolved_content_path`
(same shape as `THREE_WAY_MERGE`). For `INFERRED_ACCEPT_*`, no
resolved_content_path required.

### D-build.3 — ConflictEntry schema extension (AC.H.4, AC.H.5, AC.H.9)

**Choice.** Extend `ConflictEntry` with optional fields capturing
the resolver verdict for inferred resolutions:

```
rationale: str | None = None
confidence: float | None = None  # 0.0-1.0
user_override: bool = False
override_rationale: str | None = None
```

- For `INFERRED_*` resolutions: `rationale` and `confidence`
  required (model_validator enforces).
- For `user_override=True`: `override_rationale` required
  (model_validator enforces).
- Existing manual-resolution flows (`accept-upstream`,
  `keep-local`, `three-way-merge`, `abort`) leave the fields
  unset; backward-compat preserved.

The existing YAML round-trip via `as_yaml()` + `load_conflict_report()`
absorbs the new fields naturally (Pydantic + safe_dump). No new file
shape: the existing `<workspace>/.pos/framework/history/<tag>-conflicts.yaml`
gains the new fields per-entry; the audit log of AC.H.5 is the same
artefact.

**Why.** The existing `ConflictReport` IS the audit. Adding fields
on `ConflictEntry` keeps the surface compositional: one schema, one
file, one read/write path. The plan's "audit.yaml" notion in §2 maps
to the existing conflicts YAML extended with `rationale` +
`confidence` + override. This avoids inventing a new state-file at
`<workspace>/.pos/upgrade/<tag>/audit.yaml` when the existing
conflicts-yaml already does the job.

### D-build.4 — sync-protected schema (AC.H.2, AC.H.3, AC.H.10)

**Choice.** Add `self-upgrade/src/self_upgrade/sync_protected.py`:

```
class FileClass(str, Enum):
    A = "A"  # workspace-state, never overwritten
    B = "B"  # operator-preference, override-resolved
    C = "C"  # framework-code, LLM-resolved on conflict

class SyncProtectedRule(BaseModel):
    pattern: str  # glob relative to workspace-root
    klass: FileClass

class SyncProtected(BaseModel):
    framework_floor: list[SyncProtectedRule]  # locked, refused-on-removal
    workspace_rules: list[SyncProtectedRule] = Field(default_factory=list)

    @model_validator(mode="after")
    def _floor_intact(self) -> "SyncProtected": ...

FRAMEWORK_FLOOR_PATTERNS: tuple[tuple[str, FileClass], ...] = (
    ("personas/**/contract.yaml", FileClass.A),
    (".pos/objective_tracker.sqlite", FileClass.A),
    (".pos/**", FileClass.A),
    (".scratch/**", FileClass.A),
    (".mcp.json", FileClass.A),
    ("memory.yaml", FileClass.B),
)

def classify(path: str, sp: SyncProtected) -> FileClass: ...
```

Default-shipping template lives at
`self-upgrade/templates/sync-protected.default.yaml` (new file
under self-upgrade/, no edits outside the fence). On first
upgrade against a workspace lacking `<workspace>/.pos/sync-protected.yaml`,
`cmd_upgrade` writes the template before invoking the resolver.

**Why.** Pydantic-validated per `odd-methodology.md` §5.3
(reach-for default). Floor refused-on-removal pattern mirrors
safety-layer's `always_ask.yaml`. `classify()` walks the
`workspace_rules` first (most-specific tunable) then
`framework_floor`; first-match wins; default is C (treat as
framework-code, route to resolver).

### D-build.5 — LLM resolver (AC.H.4, AC.H.6, AC.H.12)

**Choice.** Add `self-upgrade/src/self_upgrade/merge_resolver.py`:

```
class MergeVerdict(BaseModel):
    resolution: Literal["inferred-accept-canonical",
                        "inferred-accept-workspace",
                        "inferred-merged"]
    merged_content: str | None  # required iff resolution=inferred-merged
    rationale: str
    confidence: float  # 0.0-1.0 inclusive

    @model_validator(mode="after")
    def _merged_requires_content(self) -> "MergeVerdict": ...

class ResolverBudget(BaseModel):
    per_conflict_token_budget: int = 5_000  # BB D-1 locked
    cumulative_token_budget: int = 100_000  # BB D-1 locked

class BudgetExhausted(Exception):
    pass

class ResolverFailure(Exception):
    pass

class MergeResolver:
    def __init__(self, llm_client, budget: ResolverBudget): ...
    def resolve(self, *, path: str, canonical_text: str,
                workspace_text: str, prior_text: str | None) -> MergeVerdict:
        ...  # raises BudgetExhausted, ResolverFailure
```

`llm_client` is duck-typed against the existing structured-output
adapter surface in pos-v2. Per dispatch §"Halt-and-surface" #5: if
no suitable adapter exists in the codebase, halt. (Survey at build
time.) Failure modes (timeout, schema-reject, network error) raise
`ResolverFailure`; cumulative budget exhaustion raises
`BudgetExhausted`. Both are caught in `clause_h_check` and translate
to `ClauseResult(passed=False, ...)` per AC.H.12.

Cumulative budget tracked as a counter on the resolver instance;
each `resolve()` adds the actual cost from the LLM response and
raises `BudgetExhausted` when crossing the ceiling.

Test-time substitution: production `MergeResolver` is wired in
`cli.py`'s adapter loader. Tests instantiate `MergeResolver` with a
`StubLLMClient` returning canned `MergeVerdict`s. Optional
integration test against the real adapter is gated by
`@pytest.mark.skipif("not have_claude_credentials()")`.

### D-build.6 — clause-(h) verifier integration (AC.H.7, AC.H.12)

**Choice.** Extend `clause_checks.py` with `check_clause_h(...)`
returning `ClauseResult(clause="h", ...)`:

1. Reads `<workspace>/.pos/sync-protected.yaml` (or writes default
   from template if absent — AC.H.10 first-run path).
2. Iterates the `ConflictReport`'s entries. For each conflict
   with `change_kind=upstream_modified_and_local_modified` (or
   any other class-C-eligible conflict) AND
   `resolution=PENDING`:
   - Class A → preserve workspace; set
     `resolution=KEEP_LOCAL`; record audit fields.
   - Class B → workspace-override; set
     `resolution=KEEP_LOCAL` (operator-pref preserved when
     workspace modified) or `ACCEPT_UPSTREAM` when workspace
     unchanged; record audit fields.
   - Class C → invoke `MergeResolver.resolve(...)`; map the
     verdict to one of `INFERRED_ACCEPT_*` or `INFERRED_MERGED`;
     record `rationale` + `confidence`.
3. On any `BudgetExhausted` → `ClauseResult(passed=False,
   reason="budget_exhausted: ...", details={"resolved": K,
   "deferred": L, ...})`.
4. On any `ResolverFailure` → `ClauseResult(passed=False,
   reason="resolver_failure: ...")` per AC.H.12 fail-closed.
5. Skip entries already carrying `user_override=True` (AC.H.9).
6. Skip entries already non-PENDING (manual resolution wins;
   convergent idempotency for AC.H.8).

Add `"h"` to `run_all_clauses` so a clause-(h) failure routes to
the existing `_halt_rollback` path.

**Pre-stage positioning.** Clause-(h) operates on the
ConflictReport BEFORE the symlink swap. The natural position is
inside `cmd_upgrade` (or hoisted into `execute_upgrade` as a new
pre-pause stage), after `detect_conflicts` returns the report and
before the `report.has_pending()` blocking check. The resolver
mutates the ConflictReport in place (sets `resolution`, fills
`rationale`/`confidence`); the existing `has_pending()` path
either clears entirely (no further pending → upgrade proceeds) or
remains for entries the resolver couldn't handle (manual fallback
intact).

**Why.** Composes onto the existing clause-bundle pattern without
rebuilding `run_all_clauses` data contracts. The pre-stage
position runs before swap (where the resolver MUST decide before
manifest expected-post-shas become meaningful). Clause-(h)'s
position in `run_all_clauses` is post-restart for the auditing
verifier (validates that all conflicts were resolved with
verdicts, no `INFERRED_*` entries are missing rationale/confidence,
budget bookkeeping checks out). The pre-stage helper does the
actual resolving work; the clause-(h) verifier confirms the
outcome.

### D-build.7 — sync-protected first-run write + idempotency (AC.H.8, AC.H.10)

**Choice.** In `cli.py::cmd_upgrade`, before `detect_conflicts`:

1. If `<workspace>/.pos/sync-protected.yaml` does not exist:
   copy `self-upgrade/templates/sync-protected.default.yaml` to
   that path. Write-once; existing files are not overwritten.
2. After resolver pass: write `<workspace>/.pos/upgrade/state.yaml`
   carrying `{upgrade_tag, canonical_commit_sha, last_run_at,
   conflicts_yaml_path}`. On re-invocation, if state's
   `canonical_commit_sha` matches the new manifest's commit_sha
   AND the conflicts YAML has no PENDING entries, the resolver
   short-circuits (AC.H.8 convergent idempotency).

The existing conflicts YAML at
`<workspace>/.pos/framework/history/<tag>-conflicts.yaml` carries
the audit (per D-build.3 — extended schema). The plan's
`<workspace>/.pos/upgrade/<tag>/audit.yaml` notion is satisfied by
the existing conflicts YAML; `state.yaml` is the new convergence
sentinel only.

**Why.** Reuses the existing conflicts YAML as the audit; adds one
new sentinel file (`state.yaml`) for idempotency.

### D-build.8 — OTel spans (AC.H.11)

**Choice.** In `merge_resolver.py`, wrap each `resolve()` call in
`pos.upgrade.merge_gate.resolution` span via existing
`observability.span()` helper. Attributes: `path`, `canonical_sha`,
`workspace_sha`, `model`, `tokens`, `latency_ms`, `verdict`,
`confidence`, `override`. After all resolutions, emit one
`pos.upgrade.merge_gate.summary` span with `resolved_count`,
`deferred_count`, `total_tokens`, `halt_reason`. Tests use the
in-process span exporter pattern from existing memory-system /
observability-aggregator test conventions.

### D-build.9 — seal-test allowed-prefixes widening (AC.H.S)

**Choice.** Update `self-upgrade/tests/test_no_sealed_amendments.py`'s
`allowed_prefixes` and `allowed_files` to admit the clause-(h)
surface. New paths admitted under `self-upgrade/` (already covered
by the existing `self-upgrade/` prefix); confirm `seals/` writes
work via the existing prefix; admit
`self-upgrade/templates/sync-protected.default.yaml` (covered by
the prefix). No new top-level paths needed since all clause-(h)
files live inside `self-upgrade/`.

---

## Section B — §2.5 reverse-direction trace

Every code path / branch / dependency added by this amendment maps
to a named AC. Per ODD §2.5 + plan §5 reverse-trace assertion.

| Code path | AC |
|---|---|
| `canonical.py::resolve_canonical_to_staging` | AC.H.1 |
| `cli.py::up_arg_group` (mutex group) | AC.H.1 |
| `sync_protected.py::SyncProtected._floor_intact` | AC.H.10 |
| `sync_protected.py::FRAMEWORK_FLOOR_PATTERNS` | AC.H.10 |
| `sync_protected.py::classify` (Class A branch) | AC.H.2 |
| `sync_protected.py::classify` (Class B branch) | AC.H.3 |
| `sync_protected.py::classify` (Class C branch) | AC.H.4 |
| `templates/sync-protected.default.yaml` | AC.H.10 |
| `cli.py::write_default_sync_protected` (first-run) | AC.H.10 |
| `conflict_report.py::Resolution.INFERRED_*` (3 values) | AC.H.4 |
| `conflict_report.py::ConflictEntry.rationale` field | AC.H.4, AC.H.5 |
| `conflict_report.py::ConflictEntry.confidence` field | AC.H.4, AC.H.5 |
| `conflict_report.py::ConflictEntry.user_override` field | AC.H.9 |
| `conflict_report.py::ConflictEntry.override_rationale` field | AC.H.9 |
| `conflict_report.py::ConflictEntry._inferred_requires` validator | AC.H.5 |
| `conflict_report.py::ConflictReport.sorted_low_confidence_first` | AC.H.5 |
| `merge_resolver.py::MergeVerdict` | AC.H.4 |
| `merge_resolver.py::MergeResolver.resolve` | AC.H.4 |
| `merge_resolver.py::ResolverBudget` (per-conflict + cumulative) | AC.H.6 |
| `merge_resolver.py::BudgetExhausted` | AC.H.6 |
| `merge_resolver.py::ResolverFailure` | AC.H.12 |
| `clause_checks.py::check_clause_h` | AC.H.7, AC.H.12 |
| `clause_checks.py::run_all_clauses` (h entry) | AC.H.7 |
| `cli.py::cmd_upgrade` (clause-h pre-stage hook) | AC.H.7 |
| `cli.py::cmd_upgrade` (state.yaml write/read) | AC.H.8 |
| `cli.py::cmd_upgrade` (user_override skip-resolver) | AC.H.9 |
| `observability.py` (merge_gate spans via `span()`) | AC.H.11 |
| `tests/test_no_sealed_amendments.py` allowed_prefixes update | AC.H.S |

No row without an AC. Reverse trace closed.

---

## Section C — Test breakdown

| Test file | ACs covered | Approx test count |
|---|---|---|
| `test_canonical.py` | AC.H.1 | 4 (resolve, mutex, missing-canonical, backward-compat) |
| `test_sync_protected.py` | AC.H.2, AC.H.3, AC.H.10 | 6 (classify-A/B/C, floor-refuse, default-write, idempotent-no-overwrite) |
| `test_conflict_report_inferred.py` | AC.H.4, AC.H.5, AC.H.9 | 6 (enum-extends, validator-rejects-skipped-still, inferred-requires-rationale, low-confidence-first, override-shape, round-trip) |
| `test_merge_resolver.py` | AC.H.4, AC.H.6, AC.H.12 | 6 (verdict-shape, per-conflict-budget, cumulative, budget-exhausted, resolver-failure, merged-requires-content) |
| `test_clause_h_integration.py` | AC.H.7, AC.H.8, AC.H.9, AC.H.12 | 5 (pre-stage-resolves, state.yaml-idempotency, override-skip-resolver, resolver-fail-rollback, halt-on-budget) |
| `test_clause_h_observability.py` | AC.H.11 | 2 (per-resolution span, summary span) |

**Total new tests target**: ~29. Combined with existing 122 →
**~151 tests** post-amendment.

---

## Section D — Build sequence

1. **Pre-amendment narrow-scope test run** — `pytest self-upgrade/`;
   confirm 122 green at HEAD `8ae1b82`.
2. **Survey LLM-adapter surface** in pos-v2 (memory-system,
   primary-persona, claude-print-client locations). If no
   composable structured-output adapter exists, halt-trigger #5
   per plan §10.
3. **Land schema/enum extensions first** (D-build.2, D-build.3):
   - `conflict_report.py`: extend `Resolution`; extend
     `ConflictEntry` with `rationale`/`confidence`/`user_override`/
     `override_rationale`; add `_inferred_requires` model_validator
     extension; add `ConflictReport.sorted_low_confidence_first()`.
   - Tests in `test_conflict_report_inferred.py`.
4. **Land sync-protected schema + template** (D-build.4):
   `sync_protected.py`; `templates/sync-protected.default.yaml`;
   tests in `test_sync_protected.py`.
5. **Land merge resolver** (D-build.5): `merge_resolver.py`;
   `StubLLMClient` test fixture; tests in `test_merge_resolver.py`.
6. **Land canonical-pull adapter** (D-build.1): `canonical.py`;
   `cli.py` argparse mutex group; tests in `test_canonical.py`.
7. **Land clause-(h) verifier + integration** (D-build.6,
   D-build.7): `clause_checks.py::check_clause_h`; `cli.py` pre-
   stage hook + state.yaml write/read + sync-protected first-run
   write; tests in `test_clause_h_integration.py`.
8. **Land OTel spans** (D-build.8): wrap resolver calls;
   summary span emit; tests in `test_clause_h_observability.py`.
9. **Update seal-test allowed_prefixes** (D-build.9) — confirm
   no widening needed beyond existing `self-upgrade/` prefix
   (the templates/ subdir is covered).
10. **Run touched-component suite** (`pytest self-upgrade/`); all
    green; expected count ~151.
11. **Author manifest** at
    `docs/plans/self-upgrade-clause-h-llm-merge.manifest.yaml`
    with BASELINE = HEAD at amendment-commit-time (i.e. `8ae1b82`),
    next free amendment number, narrative body finalised.
12. **`pos-amend apply --dry-run`** → expect green (HALT: prefix
    on stdout if anything else).
13. **Amendment commit** (single commit; no `--amend`).
14. **Post-amendment narrow-scope test run** — `pytest
    self-upgrade/`; same green count.
15. **`pos-amend seal --plan-doc <abs-path>`** — seal commit +
    sidecar bump + plan-SHA backfill commit.
16. **Post-seal cross-component sweep** (`pos-amend apply
    --dry-run` against all sealed components for seal-diff-only).

---

## Section E — Backwards-compat verification plan

Per plan Hard Constraint #5: `pos upgrade <tag> --staging-dir <path>`
invocation produces byte-identical pre-amendment behaviour.

Verification:

1. `test_canonical.py::test_backward_compat_staging_dir_only`
   asserts `cmd_upgrade(args)` with `--staging-dir` and no
   `--canonical` calls through to `execute_upgrade` with the
   same parameter shape pre-amendment.
2. The existing `test_cli.py` + `test_upgrade_flow.py` suites
   must continue green unchanged. Any breakage there is a
   regression and a halt-and-surface signal.
3. The new `--canonical` codepath only activates when the flag
   is supplied; the absence path is the legacy behaviour.

---

## Section F — Halt-trigger watchlist

Per plan §10:

- **#1 (new top-level objective):** the clause-(h) work fits
  under the existing v1.0 self-upgrade objective + AC.PO.1/2.
  No watch needed.
- **#2 (ODD violation in surrounding code):** if `self-upgrade/src/`
  reveals untraced code paths during build, halt before extending.
- **#4 (source edits outside `self-upgrade/`):** strictly forbidden.
  All new code lands under `self-upgrade/src/` or
  `self-upgrade/tests/` or `self-upgrade/templates/`.
- **#5 (no LLM adapter):** verified at step 2 above. Halt if
  absent.
- **#6 (clause-bundle / pipeline rebuild):** the resolver pre-
  stage runs in `cmd_upgrade` (NOT inside `execute_upgrade`'s
  pipeline), so `execute_upgrade`'s contract is preserved.
  Clause-(h) joins `run_all_clauses` as a verifier returning
  `ClauseResult` — same shape as (a)–(g). No pipeline rebuild
  needed.
- **#9 (4–6h wall-time):** narrow scope after #53 split should
  fit comfortably. Halt with state-report if exceeded.

---

## Section G — Commit SHAs

(populated post-build by `pos-amend seal --plan-doc`)

---

## Section H — Halt findings

(populated if/when fired)
