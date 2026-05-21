# v0.1.9 Cycle 1 — PR-safety gate engine + override workflow (NEW component)

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, build dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** master plan `docs/plans/v0-1-9-master-plan.md` sealed at `b01d3eb`.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/plans/v0-1-9-master-plan.md` §3 + §4 Cycle 1.

**Status file:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-1-9-cycle-1-status-2026-05-04.md`.

**Quality bar (load-bearing):** "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses." — Luke 2026-05-04. The PR-safety gate is the load-bearing protection mechanism for Eric's SOC-2 production app. The 3-band × 4-shape decision matrix ships COMPLETE; if any cell ships partial we halt and surface.

---

## §1 — Outcome shape (the "why")

v0.1.9 ships the load-bearing protection that prevents Eric (or loam itself) from merging changes that violate the verified ACs in the v0.1.8-authored banded contract for his production codebase. Cycle 1 lands the **engine without delivery wrapping** — a NEW component `plugins/dev-sdlc/pr-safety/` with a four-stage workflow shape (read-contract → classify-diff → decide → record), a per-band gating engine that runs the 3-band × 4-shape decision matrix, override-commit recognition for deliberate contract-evolution diffs, SOC-2-compliant audit logging, and production-stake-profile integration. Cycle 2 wraps this engine in pre-commit/pre-push hooks + 3 CI templates + a provenance-traceable PR description; Cycle 3 ships 6 SKILLs + cleans up the audit allowlist.

Cycle 1's release-note promise: `loam pr-safety gate <repo>` runs against any repo with a banded contract authored by `loam odd-extract`. Default invocation diffs `HEAD vs origin/main`. The gate reads the contract, classifies every touched AC against the diff, applies the 3×4 decision matrix per the workspace's `safety_profile`, and emits a structured `GateDecision` to stdout + an audit-log entry. `contract-update:`-prefixed override commits (or trailer-equipped commits) trigger the override flow with explicit owner ratification through the PM batch API. Under `safety_profile: production-stake`, no auto-merge — every gate decision marks `requires_ratification` true.

The shape (engine + gating logic + override + audit + production-stake integration) is the deliverable. Hooks, CI templates, PR description templates are explicitly Cycle 2.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

The gate composes on top of existing loam primitives rather than re-implementing them:

- **odd-extractor's banded-contract types (v0.1.8 Cycle 2).** `BandedAC`, `Evidence`, `ConfidenceBand` are imported from `loam_odd_extractor.bands`; the gate never re-defines the contract shape.
- **per-project-pm's `RatificationBatch` + `surface_next_questions_batch` API (v0.1.7 Cycle 4 + v0.1.8 Cycle 2).** PLAUSIBLE-band SURFACE-DECISION + override-ratification + novel-candidate-decision all flow through the PM's existing one-question-at-a-time batch API. No PM-side edits.
- **workspace-bootstrap's `safety_profile` field (v0.1.6 Cycle 1).** The gate reads `Manifest.safety_profile` from `loam.workspace_bootstrap.load_manifest`; production-stake-profile is the floor-flip mechanism, not a re-implemented configuration system.
- **odd-extractor's `<workspace>/.loam/extractions/<repo-id>/contract-draft.{md,yaml}` artefact path.** The gate reads the sidecar YAML directly; no re-implementation of contract storage.
- **per-project-pm audit-log shape (`audit-log/<YYYY-MM-DD>-<NNNN>.yaml`).** The gate's audit-log mirrors this shape under `<workspace>/.loam/pr-safety/audit-log/` per Decision P (SOC-2 floor).
- **loam unified CLI (`loam.cli.subcommands` entry-point group).** The gate registers `pr-safety` as a subcommand mirroring `odd-extract` + `amend` precedents.
- **cost-governance dry-run pattern.** The gate's `--dry-run` flag mirrors the odd-extractor's dry-run-by-default pattern under production-stake (Decision D + P composition).

The required research question — **"What Claude capability does this lean on or extend?"** — answer: every load-bearing primitive is composed (banded contract from odd-extractor, ratification flow from per-project-pm, profile from workspace-bootstrap, audit-log shape from per-project-pm, CLI registration from loam-cli). The gate is the orchestration layer that ties them together for the PR-safety use case.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden drops because the persona no longer has to hand-roll "did this PR violate the verified contract?" — the gate decides + the persona just relays the decision (with provenance) to the user. The natural-language intent ("merge this PR") translates to AI-effective execution ("run the gate; route to ratification if PLAUSIBLE/novel; hard-block if VERIFIED-regression"). Pass.
- **Harness test:** every loam-driven persona (PR-author, PR-reviewer, security-reviewer, architect) can call `loam pr-safety gate` instead of re-implementing diff classification + per-band gating + audit shape. Pass — the gate is a reusable harness primitive (not a one-off integration).

Both pass.

### Lens 3 — ODD authoring

Outcome above + named ACs (§4) + halt triggers (§9) + acceptance smoke (§7). Method (which diff library, which classifier heuristic, which Pydantic model layout, which audit-log YAML shape) stays the builder's call within the constraints (line-overlap + symbol-overlap + ≥90% accuracy on synthetic test set).

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH** for shape: master plan §3 Cycle 1 names the four-stage workflow, the 3-band × 4-shape decision matrix, override-commit recognition, audit-log floor, production-stake integration. Tight scope: NEW sub-package under dev-sdlc plugin tree; halt-and-surface if any named primitive turns out unimplementable.

Outcome confidence is **MEDIUM** for the diff-classifier heuristic: master plan §7.1 calls this the load-bearing risk. Method (line-overlap-only vs symbol-overlap-only vs both vs AST-aware) is the builder's call within the constraint of ≥90% accuracy on a synthetic test set; this plan-doc commits to **both** line-and-symbol overlap as Cycle 1's heuristic, with AST-awareness deferred to a halt-and-surface escape hatch.

Outcome confidence is **MEDIUM** for the override-commit recognition convention: master plan §7.3 enumerates three options (prefix `contract-update:`, trailer `Loam-Override:`, `--override` CLI flag). This plan-doc commits to **trailer + CLI flag (both required)** as the default; prefix-based recognition is supported as a third path for ergonomics but never alone (trailer or flag is always required as the structured-rationale carrier).

### Lens 5 — Swarming

Single-component fence under `plugins/dev-sdlc/`. Within the cycle, decomposition options:

- (a) one-file per stage (contract.py, diff.py, classifier.py, gate.py, override.py, audit.py, cli.py) — natural decomposition mirroring odd-extractor's per-stage layout. Each with its own AC test.
- (b) one-file per concern (workflow.py, classifier.py, decision_matrix.py, cli.py) — collapses stages.

The builder picks **(a)** — per-stage decomposition matches the master plan's "read-contract / classify-diff / decide / record" four-stage naming and gives the tightest AC-per-file mapping. `max_planner_depth: 1` (no sub-planners; per-stage files are the right granularity already). No further decomposition adds value.

---

## §3 — Single-component fence

**Scope:** `plugins/dev-sdlc/` (the existing dev-sdlc plugin's sealed fence; pr-safety lands as a NEW sub-package under it, mirroring the v0.1.8 odd-extractor placement).

**New paths (this cycle):**

- `plugins/dev-sdlc/pr-safety/` (NEW directory)
  - `pyproject.toml` — separate distribution, mirrors `plugins/dev-sdlc/odd-extractor/pyproject.toml` precedent.
  - `README.md` — what-this-component-is + cycle-status pointers.
  - `src/loam_pr_safety/__init__.py` — public API re-exports.
  - `src/loam_pr_safety/spec.py` — Pydantic models (`BandedContract`, `DiffEntry`, `Diff`, `ClassificationResult`, `GateDecision`, `OverrideRequest`, `GateAction`).
  - `src/loam_pr_safety/contract.py` — `read_contract(repo_id, workspace_root) -> BandedContract` reads odd-extractor's sidecar YAML + reconstructs `BandedAC` instances.
  - `src/loam_pr_safety/diff.py` — `parse_diff(repo_path, sha1, sha2) -> Diff` wraps `git diff --unified=0 --no-color <sha1>..<sha2>` parsing into structured `DiffEntry` records (file path, hunks of (start_line, line_count, content)).
  - `src/loam_pr_safety/classifier.py` — `classify(diff, contract) -> ClassificationResult` with line-overlap + symbol-overlap heuristics; returns `(touched_acs: list[BandedAC], untouched: bool, novel: list[CandidateAC])`.
  - `src/loam_pr_safety/gate.py` — per-band gating engine; runs the 3-band × 4-shape decision matrix; returns `GateDecision`.
  - `src/loam_pr_safety/override.py` — recognises `contract-update:` prefix + `Loam-Override:` trailer + `--override` flag; runs the override-ratification flow through PM batch API; updates contract VERIFIED set on approval.
  - `src/loam_pr_safety/audit.py` — audit-log writer; one entry per gate decision per Decision P (SOC-2 floor).
  - `src/loam_pr_safety/state.py` — workspace-state path resolution (`<workspace>/.loam/pr-safety/audit-log/`).
  - `src/loam_pr_safety/profile.py` — reads workspace `safety_profile` via `loam.workspace_bootstrap.load_manifest`; exposes `is_production_stake(workspace_root) -> bool`.
  - `src/loam_pr_safety/errors.py` — typed exceptions (`PRSafetyError`, `ContractMissingError`, `ClassifierAccuracyError`, `OverrideRejectedError`, `GateError`).
  - `src/loam_pr_safety/cli.py` — `build_pr_safety_subcommand` builder for `loam pr-safety` registration via `loam.cli.subcommands` entry-point group.
- `plugins/dev-sdlc/pr-safety/tests/` — per-AC test files (one file per AC.PRSG.{1..9}) + integration tests + synthetic-diff fixtures.
- `plugins/dev-sdlc/pr-safety/tests/fixtures/` — synthetic banded-contract + synthetic diffs (regression diff, plausible-touch diff, hypothesised-touch diff, novel-AC diff, override commit, mixed diff). Used for classifier-accuracy test set + decision-matrix coverage.

**Edits to existing dev-sdlc paths (universal-admitted within fence):**

- `plugins/dev-sdlc/pyproject.toml` — no edit required; pr-safety pyproject is independent.
- `plugins/dev-sdlc/README.md` — append a "Sub-packages" entry pointing at `pr-safety/`. (Existing entry for `odd-extractor/` already there.)

**Composition (read-only, no edit):**

- `plugins/dev-sdlc/odd-extractor/` — import `loam_odd_extractor.bands.{BandedAC, Evidence, ConfidenceBand}`. No edits to odd-extractor.
- `framework/per-project-pm/` — import `loam.per_project_pm.{PMRuntime, RatificationBatch, PendingResponseError, RecordedResponse}`. No edits to per-project-pm.
- `framework/workspace-bootstrap/` — import `loam.workspace_bootstrap.load_manifest`. No edits.
- `framework/cost-governance/` — not directly imported in Cycle 1 (the gate is invoked-on-demand and free; no cost-governance dry-run estimate is needed for the gate itself). Imported transitively via odd-extractor's spec (which carries `BudgetEnvelope`).
- `framework/tools/loam/` — depends on the unified loam CLI's `loam.cli.subcommands` entry-point group; no edit required.

**Universal-admitted prefixes/files (off-fence, allowed under standard amendment policy):**

- `docs/plans/` — this plan-doc + manifest.
- `CLAUDE.md`, `docs/odd-in-loam.md`, `docs/odd-methodology.md`, `docs/STATE.md` — universal admission per `dev-pattern-simplifications-2.manifest.yaml` precedent.

**Out-of-fence (would halt-and-surface):**

- Any `framework/` component edit (other than read-only imports).
- Any other plugin (e.g., `loam-skills/`) edit.
- Any edit to `plugins/dev-sdlc/odd-extractor/` source (Cycle 1 reads it; never writes).
- PM-side extension (e.g., a new `RatificationBatch` shape with override-specific fields). The existing `RatificationBatch.from_banded_acs` + `surface_next_questions_batch` API is sufficient; if Cycle 1 plan-author finds it isn't, halt-and-surface for two-component fence ruling.

---

## §4 — AC family — `AC.PRSG.*` (locked)

Each AC has at least one explicit pytest under `plugins/dev-sdlc/pr-safety/tests/test_AC_PRSG_<n>_<slug>.py`. ODD §2.5 — every line of code, every branch, every test maps to a named AC.

- **AC.PRSG.1 — Component scaffold present.**
  - `plugins/dev-sdlc/pr-safety/` exists with `pyproject.toml`, `README.md`, `src/loam_pr_safety/`, `tests/` directories.
  - `pyproject.toml` declares `name = "loam-pr-safety"`, `version = "0.1.0"`, `requires-python = ">=3.11"`, dependency on `loam-cli`, `loam-odd-extractor`, `loam-per-project-pm`, `loam-workspace-bootstrap`, `pydantic>=2`, `PyYAML>=6`.
  - `pyproject.toml` registers `[project.entry-points."loam.cli.subcommands"] pr-safety = "loam_pr_safety.cli:build_pr_safety_subcommand"`.
  - Manifest schema v3 with `plan_doc_ref:`. amendment.number omitted per AC.DPS1.10.
  - Test: structural — files exist; pyproject parses; entry-point declaration present. Mirrors `test_AC_OREK_1_component_scaffold.py`.

- **AC.PRSG.2 — Banded-contract reader API.**
  - `read_contract(repo_id: str, workspace_root: Path) -> BandedContract` reads `<workspace_root>/.loam/extractions/<repo_id>/contract-draft.yaml` (the odd-extractor sidecar) and reconstructs the contract surface.
  - `BandedContract` is a Pydantic model with: `extraction_id: str`, `repo_path: Path`, `repo_sha: str | None` (the SHA from the sidecar's `acs[*].evidence.repo_sha` if any), `acs: list[BandedAC]` (typed via `loam_odd_extractor.bands.BandedAC`), `unhandled_paths: list[Path]`, `created_at: str`.
  - Round-trips through `BandedAC.model_validate` so the per-band evidence rules from `loam_odd_extractor.bands` are enforced at read time (contract corruption surfaces as `pydantic.ValidationError`).
  - Raises `ContractMissingError` when the sidecar doesn't exist; `ContractMalformedError` (a subclass of `ContractMissingError` for catch hierarchy) when the YAML parses but doesn't validate.
  - Test: reader against `tests/fixtures/synthetic-banded-contract.yaml` (the odd-extractor's existing fixture); reader against a fresh extraction artefact produced by `loam odd-extract --dry-run`; raises on missing path; raises on malformed YAML.

- **AC.PRSG.3 — Diff classifier with line-overlap + symbol-overlap heuristic.**
  - `parse_diff(repo_path: Path, sha1: str | None, sha2: str | None) -> Diff` wraps `git diff --unified=0 --no-color <sha1>..<sha2>` (or working-tree-vs-HEAD if both `None`).
  - `Diff` is a Pydantic model: `from_sha: str | None`, `to_sha: str | None`, `entries: list[DiffEntry]`. `DiffEntry`: `file_path: Path`, `hunks: list[Hunk]`. `Hunk`: `old_start: int`, `old_lines: int`, `new_start: int`, `new_lines: int`, `added_lines: list[str]`, `removed_lines: list[str]`.
  - `classify(diff: Diff, contract: BandedContract) -> ClassificationResult` runs the heuristic:
    - **Line-overlap path:** for each AC in `contract.acs`, parse `evidence.citations` for entries of shape `<file_path>:<start_line>[-<end_line>]` (or `<file_path>::<test_name>` for test-style citations — these match by `file_path` only). For each diff entry, mark the AC as touched if any cited (file, line-range) intersects the diff's hunk ranges.
    - **Symbol-overlap path:** for each AC, treat `backing_files` as a softer match — if a diff entry touches any of `ac.backing_files`, mark the AC as touched (with a `touch_kind` field set to `"backing_file"` to distinguish from line-overlap which sets `"citation_line"`).
    - **Untouched signal:** every AC whose evidence cites a file the diff doesn't touch AND whose backing-files don't overlap the diff is untouched. The classification carries `untouched: bool` (True iff no AC is touched).
    - **Novel path:** any added line in the diff that doesn't fall within any AC's citation range AND lives in a file not in any AC's `backing_files` is a novel candidate. Novel candidates are aggregated per-file as `CandidateAC{file_path: Path, hunks: list[Hunk]}` — Cycle 1 doesn't extract NL semantics from the novel diff (Cycle 2+ may).
  - `ClassificationResult` is a Pydantic model: `touched_acs: list[TouchedAC]`, `untouched: bool`, `novel: list[CandidateAC]`. `TouchedAC`: `ac: BandedAC`, `touch_kind: Literal["citation_line", "backing_file"]`, `touched_hunks: list[Hunk]` (the diff hunks that triggered the match).
  - **Accuracy bar:** synthetic test set in `tests/fixtures/classifier-accuracy/` covers ≥10 synthetic diffs spanning all 4 shapes (regression-touch / plausible-touch / hypothesised-touch / novel-only / mixed). On the test set, classifier accuracy ≥90% (true-positive-rate + true-negative-rate, weighted by AC count). If <90%, halt-and-surface for AST-aware extension (per master plan §7.1 escape hatch).
  - Test: per-shape unit tests + accuracy aggregate test + classifier deterministic-for-fixed-input test + parse_diff against tmp git repo with a synthetic commit.

- **AC.PRSG.4 — Per-band gating engine (3-band × 4-shape decision matrix).**
  - `decide(classification: ClassificationResult, *, safety_profile: str) -> GateDecision` runs the matrix:

    | Touch shape | safety_profile=production-stake | safety_profile=dev | safety_profile=research |
    |---|---|---|---|
    | VERIFIED-touched (any AC) | HARD-BLOCK + requires_ratification=True | HARD-BLOCK + requires_ratification=True | HARD-BLOCK + requires_ratification=True |
    | PLAUSIBLE-touched (no VERIFIED) | SURFACE-DECISION + requires_ratification=True | SURFACE-DECISION + requires_ratification=False (proceed-with-warning default) | SURFACE-DECISION + requires_ratification=False |
    | HYPOTHESISED-touched (no VERIFIED, no PLAUSIBLE) | DOCS-ONLY + requires_ratification=False | DOCS-ONLY + requires_ratification=False | DOCS-ONLY + requires_ratification=False |
    | Novel-only (no AC touched) | SURFACE-DECISION + requires_ratification=True | SURFACE-DECISION + requires_ratification=False | SURFACE-DECISION + requires_ratification=False |
    | Untouched (no AC, no novel) | PASS + requires_ratification=False | PASS + requires_ratification=False | PASS + requires_ratification=False |

  - **Pre-emption order:** HARD-BLOCK > SURFACE-DECISION > DOCS-ONLY > PASS. A diff that touches a VERIFIED AC AND introduces a novel candidate fires HARD-BLOCK (the highest pre-empt). A diff that touches PLAUSIBLE AND introduces novel fires SURFACE-DECISION (consolidated PM batch carries both surfaces).
  - **Cycle 1 simplification (named explicitly per F2 RF):** "VERIFIED-touched" is treated as "diff-suggests-regression" by default. The engine cannot run the underlying test in-process; reviewer ratifies via `--override` flag with `Loam-Override:` trailer to let it through (override flow per AC.PRSG.5). Cycle 2 may extend this with test-execution integration; out of Cycle 1 scope.
  - `GateDecision` is a Pydantic model: `action: GateAction` (`HARD_BLOCK | SURFACE_DECISION | DOCS_ONLY | PASS`), `requires_ratification: bool`, `touched_acs: list[TouchedAC]`, `novel: list[CandidateAC]`, `safety_profile: str`, `reason: str` (structured human-readable explanation), `pm_batch_pairs: list[tuple[str, str]]` (question-text + provenance pairs to enqueue if SURFACE-DECISION; empty otherwise), `audit_payload: dict` (the structured payload written to audit-log).
  - Test: per-cell decision-matrix coverage (5 shapes × 3 profiles = 15 cells; each tested) + pre-emption test (mixed diffs verify highest-pre-empt fires) + Cycle 1 simplification test (VERIFIED-touched always HARD-BLOCK).

- **AC.PRSG.5 — Override-commit recognition + ratification flow.**
  - **Recognition:** the override commit is the most-recent commit at `to_sha` (default: `HEAD`) iff EITHER:
    1. Commit message subject matches `^contract-update:` (case-sensitive prefix), OR
    2. Commit message body contains a `Loam-Override: <rationale>` trailer (RFC-822-style; rationale must be non-empty after stripping whitespace).
    - **AND** the gate is invoked with `--override`. Commit-prefix or trailer alone is NOT sufficient — Decision I default-no demands the explicit CLI flag as the structural carrier. (The trailer/prefix carries rationale; the flag is the explicit opt-in.)
  - **Override flow:** when override is recognised AND the gate decision is HARD-BLOCK, the gate switches to OVERRIDE mode:
    - Parse `Loam-Override: <rationale>` from commit body (or read trailing prose under `contract-update:` subject if no trailer present).
    - Build `OverrideRequest{ original_acs: list[BandedAC] (the VERIFIED-touched), proposed_acs: list[BandedAC] (constructed from the diff — novel candidates promoted to PLAUSIBLE by default; reviewer adjusts), rationale: str, owner: str (from git config user.name), commit_sha: str, repo_sha: str (HEAD) }`.
    - Enqueue an override-ratification question through `RatificationBatch.from_banded_acs(extraction_id=..., banded_acs=[proposed_ac])` with `surface_next_questions_batch(n=1)` — Decision Q one-question-at-a-time. Provenance string: `f"pr-safety:override:{original_ac.ac_id}->{proposed_ac.ac_id}"`.
    - On approval (a `record_response` audit entry with affirmative response prose), update the contract's VERIFIED set: write a new sidecar YAML at `<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml` (NOT directly mutating the odd-extractor's contract sidecar — that's an odd-extractor surface and would be cross-component; instead, the override is recorded as an additive overlay that the next `read_contract` call composes on top). Audit-log entry records the (timestamp, owner, rationale, original-VERIFIED-AC, new-VERIFIED-AC) tuple.
    - On rejection (negative response), raise `OverrideRejectedError`; the gate's exit status is non-zero; audit-log entry records the rejection.
  - **Decision I default-no:** absent `--override` flag, an override-prefixed/trailered commit is NOT auto-promoted. The gate logs the candidate but proceeds with the normal HARD-BLOCK/SURFACE-DECISION decision matrix. No silent override.
  - Test: synthetic `contract-update:` commit + `--override` → ratification surfaces; approval-path applies override; rejection-path raises; absent `--override` → no auto-promotion; trailer-only recognition; prefix-only recognition; both prefix-and-trailer.

- **AC.PRSG.6 — CLI: `loam pr-safety gate <repo>`.**
  - `loam pr-safety --help` lists the subcommand.
  - `loam pr-safety gate <repo>` runs gate against the repo (default: HEAD vs origin/main).
  - `--diff <sha1>..<sha2>` overrides the default diff range.
  - `--override` opts into override-flow recognition (Decision I — explicit opt-in).
  - `--dry-run` (default under production-stake per Decision D) — runs gate, emits decision, but does NOT enqueue PM ratification + does NOT write the contract-override sidecar (audit-log entry still written so the dry-run is observable).
  - `--workspace-root <path>` overrides default cwd.
  - `--repo-id <id>` overrides automatic repo-id derivation (default: same `<basename>-<8-char-sha256>` formula as odd-extractor's `compute_repo_id`).
  - `--json` emits structured output instead of human-readable text.
  - Exit codes: 0 = PASS, 2 = HARD-BLOCK, 3 = SURFACE-DECISION (caller must run a follow-up after PM ratification), 4 = OVERRIDE-REJECTED, 5 = ContractMissing/ClassifierAccuracy, etc. (errors from `errors.py`).
  - Test: dispatches the CLI builder; verifies argparse surface; runs subcommand against a tmp repo + tmp workspace + synthetic contract; asserts each exit code path.

- **AC.PRSG.7 — SOC-2 audit-trail floor.**
  - Audit-log directory: `<workspace>/.loam/pr-safety/audit-log/`. Filename: `<YYYY-MM-DD>-<NNNN>.yaml` (mirrors per-project-pm + odd-extractor precedent).
  - Schema:
    ```yaml
    schema_version: 1
    event_kind: gate_decision | override_proposed | override_approved | override_rejected | dry_run
    timestamp: <iso8601-tz>
    repo_id: <str>
    repo_sha: <str>  # the to_sha of the diff range
    diff_range: <str>  # e.g., "abc123..def456"
    safety_profile: <str>
    decision: <action>  # PASS | HARD_BLOCK | SURFACE_DECISION | DOCS_ONLY
    requires_ratification: <bool>
    touched_acs: <list[ac_id]>
    novel_count: <int>
    reason: <str>
    owner: <str | null>  # populated when override or PM-mediated
    rationale: <str | null>  # populated when override
    ```
  - Every gate invocation (PASS / HARD-BLOCK / SURFACE-DECISION / DOCS-ONLY / dry-run) writes one entry. Override-flow invocations write three entries: `override_proposed` (request enqueued through PM), `override_approved` OR `override_rejected` (after `record_response`), and the original `gate_decision` entry that triggered the override flow.
  - Filenames are monotonic per-day; counter is `_next_audit_seq` (mirrors per-project-pm pattern).
  - Test: D6 telemetry-floor — each event-kind writes one entry; entry parses as YAML; schema_version present; timestamp ISO8601 with TZ; required fields populated.

- **AC.PRSG.8 — Production-stake profile integration.**
  - `is_production_stake(workspace_root: Path) -> bool` reads `<workspace_root>/loam.yaml` (or wherever `loam.workspace_bootstrap.load_manifest` resolves) and returns `manifest.safety_profile == "production-stake"`.
  - Under production-stake: every SURFACE-DECISION decision sets `requires_ratification=True` (no proceed-with-warning auto-pass); PASS decisions still pass cleanly; HARD-BLOCK decisions are unaffected (already block); DOCS-ONLY decisions are unaffected.
  - Under dev: PLAUSIBLE-touched + novel-only SURFACE-DECISION default to `requires_ratification=False` (proceed-with-warning) — the gate prints the warning + writes audit-log + exits with status 0 (the warning-flow does NOT fail the build under dev). Reviewer can opt-in via `--require-ratification` flag to force the dev-profile to behave like production-stake for a one-off gate run.
  - Under research: same as dev (research-profile + dev-profile are siblings with looser gating; production-stake is the strict floor).
  - Test: gate run against a tmp workspace with `safety_profile: production-stake` → SURFACE-DECISION sets requires_ratification=True; same diff against `safety_profile: dev` → SURFACE-DECISION sets requires_ratification=False (default) or True (with `--require-ratification`); HARD-BLOCK unaffected by profile; manifest absence (default profile=dev) → dev-profile behaviour.

- **AC.PRSG.9 — Component-level test surface.**
  - Per-AC test files: `test_AC_PRSG_1_component_scaffold.py` ... `test_AC_PRSG_9_component_test_surface.py` (one file per AC).
  - Plus integration tests:
    - `test_full_gate_against_fixture.py` — D1 cold-state: end-to-end `read_contract → parse_diff → classify → decide → audit` against the synthetic contract fixture + a tmp git repo with a synthetic regression diff; asserts HARD-BLOCK + audit-log entry.
    - `test_audit_log_entries.py` — D6 telemetry-floor: each gate path writes the expected event_kind entries.
    - `test_cross_session_state.py` — D5: audit-log at `<workspace>/.loam/pr-safety/audit-log/` survives a fresh process invocation; subsequent gate runs append correctly (no overwrite).
    - `test_steady_state_idempotent.py` — D2 idempotency variant: 5 gate runs against the same diff produce identical decisions (modulo timestamps via clock injection where applicable).
    - `test_classifier_accuracy.py` — accuracy aggregate across the synthetic test set (≥10 diffs); asserts ≥90% accuracy bar; halt-trigger fires below threshold.
    - `test_decision_matrix_coverage.py` — every cell of the 5-shape × 3-profile matrix tested with explicit assertions.
    - `test_override_flow.py` — synthetic `contract-update:` commit + `--override` flag end-to-end; approval-path applies override; rejection-path raises.
    - `test_no_sealed_amendments.py` — seal-fence test (mirrors `plugins/dev-sdlc/odd-extractor/tests/test_no_sealed_amendments.py` if present, OR delegated to the parent `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` which already covers the entire dev-sdlc subtree).
  - All tests must pass before seal.

---

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

### Surface #1 — sub-package vs top-level plugin (no halt — recorded)

**Decision (autonomous):** pr-safety lands at `plugins/dev-sdlc/pr-safety/` (a sub-package of the dev-sdlc plugin's tree, with its own pyproject.toml). Master plan §3 explicitly names this path. Precedent: `plugins/dev-sdlc/odd-extractor/` (v0.1.8) and `plugins/dev-sdlc/tools/loam-amend/` are also separately-pyproject'd packages inside dev-sdlc's sealed fence. The dev-sdlc plugin's seal-test (`plugins/dev-sdlc/tests/test_no_sealed_amendments.py`) gates the entire `plugins/dev-sdlc/` sub-tree.

Rationale: avoids creating a new top-level plugin (which would require its own contribution registration + seal-test scaffolding), reuses the existing dev-sdlc plugin's sealed-component infrastructure, matches the master plan's named placement.

### Surface #2 — diff classifier heuristic (no halt — recorded; F2 RF gap §10.1)

**Decision (autonomous):** Cycle 1's classifier uses **both** line-overlap (against AC `evidence.citations` parsed for `<file>:<start>[-<end>]` shapes) and symbol-overlap-via-backing-files (against AC `backing_files`). Each touch is tagged with `touch_kind: "citation_line" | "backing_file"` so downstream consumers can distinguish strict line-level matches from coarser file-level matches.

Rationale: per master plan §7.1, line-and-symbol is named as the right starting heuristic. AST-aware symbol-graph matching (via tree-sitter, which v0.1.8 Cycle 3+4a already integrates) is the escape-hatch extension if accuracy <90%; deferring AST-awareness to halt-trigger keeps Cycle 1's complexity contained.

### Surface #3 — override convention (no halt — recorded; F2 RF gap §10.2)

**Decision (autonomous):** override is recognised via `Loam-Override: <rationale>` trailer (RFC-822-style commit body trailer) AND/OR `contract-update:` subject prefix AND `--override` CLI flag. The CLI flag is structurally required (Decision I default-no): the trailer/prefix carries rationale, the flag carries the explicit opt-in.

Rationale: per master plan §7.3, the trailer is the most-compatible-with-conventional-commits choice (commitizen's `feat:`/`fix:`/`chore:` strict-prefix-validation does not interfere with trailers). The prefix is supported as ergonomics for teams that don't mind a custom prefix. The CLI flag closes the silent-override loop — Decision I demands an explicit opt-in.

### Surface #4 — override-application strategy (additive overlay vs sidecar mutation) (no halt — recorded)

**Decision (autonomous):** approved overrides are recorded as **additive overlays** at `<workspace>/.loam/pr-safety/contract-overrides/<repo-id>/<override-N>.yaml` rather than mutating the odd-extractor's `<workspace>/.loam/extractions/<repo-id>/contract-draft.yaml` sidecar in-place.

Rationale: the contract sidecar is owned by the odd-extractor component. Mutating it in-place from pr-safety violates the single-component fence (would extend scope to two components). The overlay pattern is the same separation-of-concerns the odd-extractor's `ratification_state.py` uses (Cycle 2 v0.1.8) — mutations to ratification state live in a sibling file, not in the contract draft itself. A future amendment may merge overlays back into the draft as a separate component edit; that's out of Cycle 1 scope.

The next `read_contract` call composes overlays on top: reads the draft sidecar, then iterates `<repo-id>/contract-overrides/*.yaml` in sorted order and applies each (override-N replaces an original-VERIFIED-AC with a new-VERIFIED-AC). The composition is deterministic and idempotent.

### Surface #5 — workspace state location (no halt — recorded)

**Decision (autonomous):** `<workspace>/.loam/pr-safety/` for all per-gate state. Sub-paths: `audit-log/<YYYY-MM-DD>-<NNNN>.yaml` for audit entries; `contract-overrides/<repo-id>/<override-N>.yaml` for approved overrides.

Rationale: matches the existing `<workspace>/.loam/` namespace convention (M-FBM at `<workspace>/.loam/memory/`; PM at `<workspace>/.loam/pms/<pm-name>/`; odd-extractor at `<workspace>/.loam/extractions/<repo-id>/`; pr-safety at `<workspace>/.loam/pr-safety/`).

### Surface #6 — repo-id determinism (no halt — recorded)

**Decision (autonomous):** repo-id format identical to odd-extractor's: `<basename>-<8-char-sha256-hex-of-abs-path>`. Re-uses `loam_odd_extractor.state.compute_repo_id` (read-only import).

Rationale: a single repo extracted by odd-extract and gated by pr-safety MUST share a repo-id so the gate reads from the right contract. Re-using the odd-extractor's exact function avoids drift.

### Surface #7 — Pydantic model shape (no halt — recorded)

**Decision (autonomous):** all spec models use `pydantic.BaseModel` with `ConfigDict(extra='forbid')`. Mirrors odd-extractor + per-project-pm + cost-governance conventions.

### Surface #8 — audit-log entry shape (no halt — recorded)

**Decision (autonomous):** mirror per-project-pm + odd-extractor's `audit-log/<YYYY-MM-DD>-<NNNN>.yaml` shape. Schema version 1; per-day NNNN counter via `_next_audit_seq`-style logic (not per-extraction since gate runs aren't bounded the same way).

Rationale: precedent reuse; SOC-2 audit-trail floor (Decision P); diagnosable by reading YAML files (no proprietary log format).

### Surface #9 — dry-run-by-default under production-stake (Decision D + Decision P composition)

**Decision (locked by master plan):** `loam pr-safety gate <repo>` defaults to `--dry-run` under production-stake (mirrors odd-extract's pattern). Under dev, default is live (no `--dry-run`).

Rationale: production-stake demands live-actions be opt-in; the gate is invoked at hook-time (Cycle 2) where the operator is rarely typing the flag, so dev-profile's default-live keeps the ergonomics; production-stake's default-dry-run is the safety floor.

### Surface #10 — D2/D3/D4 smoke applicability (no halt — recorded)

**Decision (autonomous):** the gate is invoked-on-demand (one-shot CLI / library, not a long-running daemon). Per smoke-test-discipline §6 quick-reference, "one-shot CLI / library? Dimensions 1, 5, 6 only." D2 (steady-state durability), D3 (restart resilience under signal), D4 (full reboot) do not apply structurally.

D2 idempotency variant exercised: 5 gate runs against the same diff produce byte-identical decisions (modulo timestamps via clock injection). Captured as `test_steady_state_idempotent.py` per AC.PRSG.9. This satisfies the master plan dispatch's "D2 idempotency variant: 5+ gate runs on same diff are byte-identical."

D5 cross-session: audit-log persists across `/clear` (filesystem state). D6 telemetry-floor: every gate decision audit-logged.

### Surface #11 — release-note promise mapping (no halt — recorded)

**Decision (autonomous):** every release-note promise must correspond to tested + reliable behavior.

| Promise | Backing AC | Test |
|---|---|---|
| "gate runs end-to-end against banded contract + diff" | AC.PRSG.{1,2,3,6} | `test_full_gate_against_fixture.py` |
| "diff classifier ≥90% accuracy on synthetic test set" | AC.PRSG.3 | `test_classifier_accuracy.py` |
| "per-band gating decision matrix is complete" | AC.PRSG.4 | `test_decision_matrix_coverage.py` |
| "override workflow runs end-to-end on `contract-update:` commits" | AC.PRSG.5 | `test_override_flow.py` |
| "production-stake demands explicit ratification" | AC.PRSG.8 | `test_AC_PRSG_8_*.py` |
| "every gate decision audit-logged" | AC.PRSG.7 | `test_audit_log_entries.py` |
| "audit-log survives /clear" | D5 + AC.PRSG.9 | `test_cross_session_state.py` |
| "no silent override" | AC.PRSG.5 (Decision I) | `test_override_flow.py::test_absent_flag_no_auto_promotion` |

If any test in the right column FAILs at build time, the corresponding promise gets de-shipped (not partially-shipped) — halt-and-surface to dispatcher.

---

## §6 — Decision matrix (3-band × 4-shape × 3-profile, locked)

Spelling out every cell explicitly so the build agent can map tests 1:1 to cells. Pre-emption order: HARD-BLOCK > SURFACE-DECISION > DOCS-ONLY > PASS.

### Cell-by-cell

| # | Touch shape | Profile | Action | requires_ratification | Notes |
|---|---|---|---|---|---|
| 1 | VERIFIED-touched | production-stake | HARD-BLOCK | True | Cycle 1 simplification — VERIFIED-touched ≡ regression-suspect (test not run in-engine) |
| 2 | VERIFIED-touched | dev | HARD-BLOCK | True | Same Cycle 1 simplification |
| 3 | VERIFIED-touched | research | HARD-BLOCK | True | Same |
| 4 | PLAUSIBLE-touched (no VERIFIED) | production-stake | SURFACE-DECISION | True | PM batch enqueues 1 question/AC per Decision Q |
| 5 | PLAUSIBLE-touched (no VERIFIED) | dev | SURFACE-DECISION | False | proceed-with-warning default; `--require-ratification` opts in |
| 6 | PLAUSIBLE-touched (no VERIFIED) | research | SURFACE-DECISION | False | Same as dev |
| 7 | HYPOTHESISED-touched (no VERIFIED, no PLAUSIBLE) | production-stake | DOCS-ONLY | False | Annotation only; no block |
| 8 | HYPOTHESISED-touched | dev | DOCS-ONLY | False | Same |
| 9 | HYPOTHESISED-touched | research | DOCS-ONLY | False | Same |
| 10 | Novel-only (no AC touched) | production-stake | SURFACE-DECISION | True | PM batch surfaces "add as PLAUSIBLE / HYPOTHESISED / skip" |
| 11 | Novel-only | dev | SURFACE-DECISION | False | Default proceed-with-warning |
| 12 | Novel-only | research | SURFACE-DECISION | False | Same |
| 13 | Untouched (no AC, no novel) | any | PASS | False | clean diff; not gating-relevant |

### Pre-emption rules

| Mixed touch | Effective action |
|---|---|
| VERIFIED + PLAUSIBLE | HARD-BLOCK (VERIFIED pre-empts) |
| VERIFIED + HYPOTHESISED | HARD-BLOCK |
| VERIFIED + novel | HARD-BLOCK |
| PLAUSIBLE + HYPOTHESISED | SURFACE-DECISION (PLAUSIBLE pre-empts; PM batch surfaces only the PLAUSIBLE questions; HYPOTHESISED-touched ACs land in audit-log notes for later annotation) |
| PLAUSIBLE + novel | SURFACE-DECISION (PM batch carries both; PLAUSIBLE-ratify questions + novel-decision questions consolidated) |
| HYPOTHESISED + novel | SURFACE-DECISION (novel pre-empts DOCS-ONLY since novel introduces an unmapped surface; HYPOTHESISED-touched lands in audit-log notes) |

13 cells + 6 mixed-touch rules = 19 explicit decision-points. `test_decision_matrix_coverage.py` asserts each.

---

## §7 — Smoke (REALISTIC CONDITION — applicable dimensions per smoke-test-discipline §6)

Cycle-level smoke. Release-level SOFT gate at v0.1.9 close (master plan §5 + Decision R), not this cycle. Quality-bar non-negotiable still applies.

### D1 — cold-state (fresh canonical workspace)

**Pattern.** Tmp workspace; tmp git repo with the synthetic banded contract written into the workspace's `.loam/extractions/<repo-id>/contract-draft.{md,yaml}` directly (so the gate reads it without invoking odd-extract; this is unit-level, not full-stack). Synthetic commit on the tmp repo touching a VERIFIED-cited line. Run `loam pr-safety gate <repo>` → assert: (a) decision = HARD-BLOCK; (b) exit code 2; (c) audit-log entry under `.loam/pr-safety/audit-log/`; (d) decision JSON output structured as expected.

**Test:** `test_full_gate_against_fixture.py`.

### D2 — steady-state durability (n/a structurally; idempotency variant covered)

**Structural rationale.** Gate is one-shot CLI / library, not a long-running daemon. Smoke-test-discipline §6 quick-reference: D2 doesn't engage.

**Idempotency variant exercised.** AC.PRSG.9's `test_steady_state_idempotent.py` runs 5 gate invocations against the same (contract, diff) pair and asserts byte-identical decisions (modulo timestamps via clock injection). This satisfies the master plan dispatch's "D2 idempotency variant: 5+ gate runs on same diff are byte-identical" wording.

### D3 — restart resilience (n/a)

**Structural rationale.** No long-running process to kill. Gate is single Python process; if it crashes mid-run, the next invocation reads the audit-log + state and continues cleanly. No supervisor needed.

### D4 — reboot resilience (n/a)

**Structural rationale.** Same as D3 — no daemon to recover after host reboot. Cross-session continuity (D5) is the relevant analog. Filesystem state (audit-log, override overlays) survives reboot trivially.

### D5 — cross-session continuity

**Pattern.** Process A: invoke gate → produce HARD-BLOCK + audit entry. Process B (subprocess invocation): re-invoke same gate command → produce HARD-BLOCK + new audit entry (sequence number incremented; no overwrite). Assert: (a) audit-log dir survives the process boundary; (b) second invocation appends, doesn't overwrite; (c) decisions are stable across processes.

**Test:** `test_cross_session_state.py`.

The `/clear` analog is "fresh process boundary"; the test validates that boundary directly (subprocess vs in-process).

### D6 — telemetry floor

**Pattern.** Run a full gate cycle covering each event-kind (gate_decision via PASS, HARD-BLOCK, SURFACE-DECISION, DOCS-ONLY paths; override_proposed + override_approved; override_rejected; dry_run). Assert: (a) `<workspace>/.loam/pr-safety/audit-log/` directory exists; (b) one entry per event-kind invocation; (c) every entry carries `schema_version: 1`, `timestamp` (ISO8601 with TZ), `repo_id`, `repo_sha`, `event_kind`, `decision` (where applicable); (d) filenames follow `<YYYY-MM-DD>-<NNNN>.yaml` with monotonic per-day NNNN sequence.

**Test:** `test_audit_log_entries.py`.

---

## §8 — Out of scope

Explicit deferrals (master plan §3 Cycle 1 + per-cycle dispatch):

- **Pre-commit / pre-push hook installer.** → Cycle 2.
- **GitHub Actions / GitLab CI / CircleCI templates.** → Cycle 2.
- **Provenance-traceable PR description template.** → Cycle 2.
- **6 dev-sdlc SKILLs second pass.** → Cycle 3.
- **Audit-allowlist cleanup.** → Cycle 3.
- **Continuous codebase-watch.** → v0.2.0+.
- **Eric's actual codebases (real OSS PR-safety smoke).** → v0.2.1 fresh-user smoke gate.
- **AST-aware symbol-graph classifier extension.** → halt-trigger escape-hatch only (master plan §7.1); not Cycle 1 scope unless accuracy <90%.
- **Test-execution integration for VERIFIED-touched diffs (running the actual test to confirm regression).** → Cycle 1 simplification: any VERIFIED-touched diff is treated as regression-suspect; reviewer ratifies via `--override`. Test-execution integration is a v0.2.x candidate.
- **Override-application that mutates the odd-extractor's contract sidecar in-place.** → would require two-component fence; out of Cycle 1 single-component fence. Cycle 1 uses additive overlay pattern (Surface #4). A future amendment may merge overlays back.
- **Persona-side wiring of override-ratification UX.** → loam-skills (out of cycle scope; harness-side primary-persona work at v0.2.0+).

---

## §9 — Halt triggers (in-flight)

Per dispatch + master plan:

- **WD drifts.** If `git rev-parse --show-toplevel` is not `/Users/lukeivers/ivers-corp-pos-v2/`, halt + surface.
- **v0.1.8 Cycles 2 + 4b not sealed.** If `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/bands.py` (Cycle 2) or the canonical fixtures (`tests/fixtures/jsts-playwright-app/`, `tests/fixtures/ruby-rails-payment/` from Cycle 4b) are absent, halt — pr-safety depends on these. (Pre-flight: both are present at HEAD `b01d3eb`.)
- **v0.1.7 Cycle 4 PM batch API absent.** If `RatificationBatch`, `surface_next_questions_batch`, `record_response`, `PendingResponseError` absent from `loam.per_project_pm`, halt — pr-safety override flow depends on these. (Pre-flight: all present.)
- **Plan-doc not authored before code.** This document IS that plan-doc. If code lands before this is committed, halt.
- **Diff classifier accuracy <90% on synthetic test set.** Master plan §7 names this as the most-load-bearing risk. Halt + surface for AST-aware extension.
- **Any AC ships partial.** If `test_AC_PRSG_<n>_*.py` is XFAIL, skipped, or asserts a degraded behaviour, halt + reframe before sealing.
- **Override workflow allows a silent promotion (Decision I violation).** Halt + RF.
- **D5 cross-session smoke fails.** This is the ship-test for cross-session continuity per master plan §3 Cycle 1; halt unconditionally on red.
- **Cycle exceeds 5 hours wall-clock.** Halt with partial findings; consider further decomposition (e.g., split engine from override).
- **ODD violations discovered in surrounding code.** Halt + surface; do not silently extend (per `feedback_subagent_odd_violation_halt`).
- **More than 3 in-build decisions need Luke escalation.** Master plan recommends 3 (this is a ship-quality cycle).
- **PM-side extension needed.** If the existing `RatificationBatch` API can't carry override-rationale + original-AC + proposed-AC payload, halt + surface for two-component fence ruling.

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **Diff classifier line-overlap is fragile against refactor diffs.** A diff that moves AC-relevant code from line 42 to line 100 (no semantic change) will register as touching the original lines AND the new lines AND the citation will become stale. Cycle 1's heuristic is "match if any cited line falls within any diff hunk." Refactor-shaped diffs may produce false-positives (touch reported where none semantically exists). The `test_classifier_accuracy.py` synthetic test set MUST include at least one refactor-shaped diff (move-without-change) to characterise this — if it passes, accuracy ≥90% holds; if not, halt + AST extension. The audit-log entry includes `touch_kind` (`citation_line` vs `backing_file`) so reviewers can distinguish strict matches from coarser ones.

2. **Override convention requires both trailer/prefix AND CLI flag.** F2 RF: this is more friction than the master plan §7.3 enumerated options. Rationale (§5 Surface #3): Decision I default-no demands an explicit opt-in; the trailer/prefix carries rationale for audit, the flag carries explicit consent for the gate run. Two-factor authentication for contract evolution. If Eric's team finds the flag friction onerous in v0.2.x usage, surface for revisit (not Cycle 1 scope).

3. **Override-application via additive overlay is forward-deferred work.** Surface #4: Cycle 1 records overlays in a separate file rather than mutating the contract sidecar. The next `read_contract` call composes overlays. This means: (a) odd-extractor's sidecar is read-only from pr-safety's perspective (single-component fence holds); (b) downstream consumers of the contract who DON'T compose overlays (e.g., a hypothetical future tool reading the sidecar directly) will see stale VERIFIED-set. Mitigation: pr-safety's `read_contract` is the single source of truth for "current effective contract"; future tools should call it, not read the sidecar directly. Documented in component README.

4. **Cycle 1 simplification "VERIFIED-touched ≡ regression-suspect" is conservative.** The engine cannot run the underlying test in-process to confirm regression. False-positives (any VERIFIED-touched diff hard-blocks even when the test would still pass) are by design — reviewer's `--override` flag is the escape hatch. Honest framing: this is over-cautious by Cycle 1's standards; Cycle 2+ may add test-execution integration. Eric's SOC-2 floor probably wants this conservative-by-default behaviour anyway.

5. **The 13 + 6 = 19 decision-points are tested individually but the combinatorial space (all multi-AC mixed touches across all profiles) isn't fully enumerated.** The pre-emption order rule is the abstraction that compresses the combinatorial space; `test_decision_matrix_coverage.py` exercises the pre-emption rules + each pure cell. Combinatorial fuzz-testing (random mixed-band diffs) is out of Cycle 1 scope; flagged as a v0.2.x candidate if Eric's team surfaces edge cases.

6. **`safety_profile: dev` PLAUSIBLE-touched is "proceed-with-warning" — this might surprise Eric.** Master plan §3 Cycle 1 dispatch says "PLAUSIBLE touched → SURFACE-DECISION through PM batch (Decision Q one-question-at-a-time); reviewer ratifies (proceed) or escalates (block)". This plan-doc adds the Cycle 1 default of `requires_ratification=False` under dev (with `--require-ratification` opt-in). If Eric expects PLAUSIBLE to always surface a question even under dev, the default may surprise. Mitigation: README documents the per-profile default + the opt-in flag. Production-stake (Eric's SOC-2 production app's actual profile) gets the strict behaviour by default.

7. **The classifier doesn't reason about line-context (added-vs-removed ratio, whitespace-only changes).** A diff that's purely whitespace + comment churn within an AC's cited lines will register as touched. Cycle 1 ships the simplest semantics; reviewer's `--override` flag is the escape. Whitespace-aware filtering is a v0.2.x candidate.

8. **`is_production_stake(workspace_root)` reads the workspace manifest at every gate invocation.** No caching. For Cycle 1 (gate is one-shot, manifests are ~hundreds of lines max), this is fine. If Cycle 2+ adds hooks that fire on every commit (frequency: tens-per-day), the read-overhead is still trivial (file read is microseconds). Flagged for awareness; not a Cycle 1 mitigation.

9. **The override flow's `OverrideRequest.proposed_acs` defaults to "promote novel candidates to PLAUSIBLE."** This is a design choice; the user via PM ratification can adjust (skip / promote-to-VERIFIED-with-evidence / promote-to-HYPOTHESISED). Cycle 1 ships the promote-to-PLAUSIBLE default because: (a) it's the most-conservative conversion (PLAUSIBLE → SURFACE-DECISION in future runs, not HARD-BLOCK), (b) HYPOTHESISED requires explicit rationale (LLM-derived inference) which Cycle 1's diff cannot synthesise, (c) VERIFIED requires a passing test pinned to a SHA which the override flow can't produce. Reviewer's PM-mediated answer overrides the default.

10. **Manifest schema v3 third-real-build-use after DPS2 + odd-extractor Cycle 1.** v3 fields exercised: `plan_doc_ref`, `ac_count`, `smoke_outcome`. Builder verifies seal-commit shape post-apply matches DPS2's expectations. (The v0.1.8 Cycle 5 dev-sdlc skills used v3 successfully — `e4512b9` is the most-recent v3 seal.)

11. **Cycle 1 wall-clock band 6–10 h with 5 h halt-trigger.** This is a tight halt-trigger for what is the highest-risk single cycle of v0.1.9 (NEW component, classifier, decision matrix, override workflow, production-stake integration, audit-log floor). The halt-trigger forces an early surface if the classifier accuracy work bleeds the schedule — that's the right escape, since the classifier is the most-load-bearing risk. If the build is on-track at hour 5 with classifier accuracy passing, dispatcher should consider extending another 1-2h to seal cleanly rather than splitting.

---

## §11 — Provenance trail

- **Master plan source authority:** `docs/plans/v0-1-9-master-plan.md` §3 + §4 Cycle 1 (sealed at `b01d3eb`).
- **Eric synthesis:** `docs/plans/eric-final-delivery-plan-2026-05-04.md` — Decisions I (PLAUSIBLE→VERIFIED default-no), P (SOC-2 floor), Q (one-question-at-a-time), R (HARD/SOFT smoke gate cadence).
- **v0.1.8 Cycle 2 (banded contract types):** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/bands.py` — `BandedAC`, `Evidence`, `ConfidenceBand`. Sealed at `4865028`.
- **v0.1.8 Cycle 4b (canonical fixtures):** `plugins/dev-sdlc/odd-extractor/tests/fixtures/jsts-playwright-app/`, `ruby-rails-payment/`, `synthetic-banded-contract.{md,yaml}`. Sealed at `c648cf9`.
- **v0.1.7 Cycle 4 (PM batch API):** `framework/per-project-pm/src/loam/per_project_pm/runtime.py` — `surface_next_questions_batch`, `record_response`, `PendingResponseError`. Sealed at `122a7c8`.
- **v0.1.7 Cycle 2 (PM RatificationBatch):** `framework/per-project-pm/src/loam/per_project_pm/ratification.py` — `RatificationBatch.from_banded_acs`. (Actually shipped at v0.1.8 Cycle 2 per the docstring; Cycle 4 batch API was the v0.1.7 lift.) Sealed at `4865028`.
- **v0.1.6 Cycle 1 (production-safety + cost-governance):** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py` — `Manifest.safety_profile`, `LEGAL_SAFETY_PROFILES`. Sealed at `3f1d237`.
- **v0.1.8 Cycle 1 (odd-extractor scaffold + state location convention):** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/state.py` — `compute_repo_id`, workspace state path convention. Sealed at `b33a0dc` → `e4512b9`.
- **Dev-pattern-simplifications #1 + #2 (manifest schema v3 + seal-narrative compression):** sealed at `019cfca` + `df3f50f`. Cycle 1 uses v3 schema.
- **Smoke-test-discipline:** `plugins/dev-sdlc/docs/smoke-test-discipline.md` — six dimensions; D2/D3/D4 marked n/a per quick-reference card §6.
- **ODD-methodology:** `plugins/dev-sdlc/docs/odd-methodology.md` — every line maps to a named AC (ODD §2.5).
- **Lens 5 (swarming) reference + stopping criterion:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md` + framework/CLAUDE.md Lens 5.
- **Quality bar (Luke directive 2026-05-04):** master plan §1 verbatim + master plan §3 Decision R framing.

---

## §12 — Bookkeeping

- **Manifest:** `docs/plans/v0-1-9-cycle-1-pr-safety-gate-engine.manifest.yaml` — schema_version: 3 with `plan_doc_ref:`. amendment.number omitted per AC.DPS1.10. ac_count: 9. smoke_outcome: "D1 + D2-idempotency + D5 + D6 exercised; D3/D4 n/a per smoke-test-discipline §6 (one-shot CLI)".
- **Apply:** `loam amend apply <manifest>` — single merged manifest+apply commit per AC.DPS1.6 (v3 schema). NOT `git commit --amend`; pos-amend creates a new commit per `feedback_no_amend_in_agent_dispatches`.
- **Seal:** `loam amend seal --plan-doc docs/plans/v0-1-9-cycle-1-pr-safety-gate-engine.md <manifest>` — synthesizes 5–15 line narrative body per AC.DPS2.{1,4} into `plugins/dev-sdlc/seals/SEAL_COMMIT.v0-1-9-cycle-1-pr-safety-gate-engine`.
- **§14 backfill (this plan-doc, post-seal):** add a `## 14.` heading + method-decision register with the apply SHA + seal SHA + post-seal commit SHA per AC.D-sa.7 lint regex (NOT `## §14`).
- **Master plan §9 backfill:** add Cycle 1 row with apply SHA + seal SHA + notes after seal lands.
- **Roadmap §8 backfill:** add v0.1.9 Cycle 1 row to `docs/plans/v0-1-x-roadmap.md` §8 method-decision register.
- **Eric-final-delivery §2 backfill:** add v0.1.9 Cycle 1 progress note to `docs/plans/eric-final-delivery-plan-2026-05-04.md` §2.
- **No tag push.** v0.1.9 tag waits on Cycles 2–3 + release-level SOFT smoke gate (Decision R) + Luke's gate-review.

---

## §13 — Acceptance gate

This plan-doc is gate-ready when:

1. All 9 AC.PRSG.* families named with explicit pytest paths (§4) ✓
2. Single-component fence named (§3) ✓
3. All 6 smoke dimensions addressed — applicable exercised, n/a documented (§7) ✓
4. Halt triggers named (§9) ✓
5. Bookkeeping path named (§12) ✓
6. F2 gaps named (§10) ✓
7. Decision matrix fully enumerated (§6) ✓

Build proceeds.

---

## 14. Method-decision record (post-seal backfill)

(Reserved; build agent backfills with apply SHA + seal SHA + post-seal commit SHA per AC.D-sa.7 lint regex. The `## 14.` heading is required by the `loam amend seal` lint, NOT `## §14`.)

| Step | SHA | Notes |
|---|---|---|
| Plan-doc commit (this file) | TBD | docs(plans): v0.1.9 Cycle 1 sub-plan + manifest |
| Source-edit commit (BASELINE) | TBD | feat(dev-sdlc): pr-safety gate engine source edits + tests |
| Apply commit (manifest+apply merged per AC.DPS1.6) | TBD | chore(amend): v0-1-9-cycle-1-pr-safety-gate-engine manifest+apply — dev-sdlc BASELINE+sidecar bump |
| Seal commit | TBD | chore(seals): v0-1-9-cycle-1-pr-safety-gate-engine — dev-sdlc at <baseline> |
| Post-seal SHA-record commit (this §14 backfill + master plan §9) | TBD | docs(plans): record v0-1-9-cycle-1 commit SHAs in method-decision register |

### Commit SHAs

- Amendment commit: `136adc6f8eca113283b5431043066684e190ee16` —
  `chore(amend): v0-1-9-cycle-1-pr-safety-gate-engine manifest+apply — dev-sdlc BASELINE+sidecar bump to bb592fa`
- Seal commit: `790807dca8fb5e5fd7cfde7d0af1ad536334148b` —
  `chore(seals): v0-1-9-cycle-1-pr-safety-gate-engine — dev-sdlc at 136adc6`
