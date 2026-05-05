# v0.2.0 Cycle 1 — Continuous codebase-watch (incremental extractor) + scheduling + PM ratification-queue + domain-batched AC surfacing

**Status:** plan-doc; pre-code per `feedback_plan_before_code`. Authored 2026-05-04 (Sonnet, build dispatch).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/` (canonical pos-v2). NOT pos3.

**Predecessor:** master plan `docs/rebuild/plans/v0-2-0-master-plan.md` committed at `7c0f87b`. v0.1.9 SHIPPED-locally at `9022df1`.

**BASELINE (pre-build tip):** to be set to the source-edit commit when the build commit lands.

**Parent plan:** `docs/rebuild/plans/v0-2-0-master-plan.md` §3 Cycle 1 + §4 Cycle 1 dispatch brief.

**Status file:** `/Users/lukeivers/pos3/workspace/.scratch/claude-output/v0-2-0-cycle-1-status-2026-05-04.md`.

**Quality bar (load-bearing):** "I want this to WOW him. It can't be half-assed. What ships needs to deliver what we promise. No excuses." — Luke 2026-05-04. The continuous-watch is the load-bearing mechanism that keeps the v0.1.8 banded-contract synchronised as Eric's Rails-app evolves; without it, v0.1.9's PR-safety gate runs against an increasingly stale contract. Diff-classifier accuracy ≥90% on synthetic test set. Domain-batched surfacing groups related drift into one PM question (not N). Production-stake honour-flow defaults to dry-run. If any AC ships partial we halt and surface.

---

## §1 — Outcome shape (the "why")

v0.2.0 Cycle 1 ships the **incremental mode** of the v0.1.8 four-stage extractor (Cycles 3+4 produced the full mode; Cycle 1 here produces the increment). When the codebase changes between sessions (external commits / file edits), the watch incrementally re-extracts only what changed, classifies which ACs are out-of-date, and surfaces re-extraction proposals as a domain-batched ratification queue through the existing v0.1.7 PM batch API.

Cycle 1's release-note promise: `loam odd-extract <repo> --incremental` against any repo with a v0.1.8-authored banded contract reads the prior contract, computes a diff against the current repo state, classifies each AC's evidence as still-current / out-of-date / orphaned, generates a re-extraction proposal for each out-of-date AC, groups proposals by domain (tag-based primary, file-path-prefix fallback), and enqueues one PM decision-question per domain-batch (not per-AC) through `loam.per_project_pm.PMRuntime.enqueue_decision`. Under `safety_profile: production-stake`, the watch defaults to dry-run; ratification is always required. Every watch run + proposal + ratification/rejection emits an audit-log entry per Decision P SOC-2 floor.

The shape (incremental engine + diff-classifier + re-extraction proposal generation + PM extension via existing batch API + domain-batching + production-stake gate + audit-log floor + scheduling-primitive integration) is the deliverable. Cycle 2 (auto-creation MVP) ships separately and serially.

**Scheduling clarification (Surface #1):** the CLI invocation `loam odd-extract <repo> --incremental` IS the schedulable primitive. Any external cron mechanism (system crontab, Anthropic Claude Code `/schedule` skill, future scope-of-work cron extension) can invoke it. Cycle 1 does NOT extend `framework/scope-of-work/` with a new trigger kind — see Surface #1 + §5.

---

## §2 — Lens checks (per CLAUDE.md design lenses)

### Lens 1 — Claude-leverage-first

The incremental watch composes on top of existing loam primitives rather than re-implementing them:

- **odd-extractor's full-mode contract artefacts (v0.1.8 Cycles 3+4).** `<workspace>/.loam/extractions/<repo-id>/contract-draft.{md,yaml}` is the canonical sidecar; the incremental mode reads + writes this exact path. No alternative contract storage.
- **odd-extractor's banded-contract types (v0.1.8 Cycle 2).** `BandedAC`, `Evidence`, `ConfidenceBand` are imported from `loam_odd_extractor.bands`; the watch never re-defines the contract shape.
- **odd-extractor's full-mode entry points (`init_extraction`, `analyze_repo`, `generate_raw_acs`, `verify_contract`).** Re-extraction of an out-of-date AC re-invokes the existing four-stage workflow scoped to the affected files; no parallel extraction code-path.
- **odd-extractor's `compute_repo_id` (v0.1.8 Cycle 1).** Repo-id derivation reused verbatim.
- **odd-extractor's `ratify.enqueue_ratification_batch` + `_question_for_banded_ac` (v0.1.8 Cycle 2).** The incremental mode's PM enqueue path mirrors the existing ratify-flow's PM-side composition; the new entry-point composes on the same `PMRuntime.enqueue_decision` interface.
- **per-project-pm's `enqueue_decision` + `surface_next_questions_batch` (v0.1.7 Cycle 4).** Domain-batched proposals enqueue through `PMRuntime.enqueue_decision(question_text, provenance=...)`; the question-text aggregates the domain's ACs; the provenance string carries `odd-extract:incremental:<extraction_id>:<domain-slug>`. Question-text shape carries the type identity — no PM-side batch-type registration needed (Cycle 1 plan-doc commits to thin-extension shape per master plan §6 open item #1).
- **workspace-bootstrap's `safety_profile` field (v0.1.6 Cycle 1).** `loam.workspace_bootstrap.load_manifest` returns the `Manifest`; production-stake-profile is the dry-run default mechanism, not a re-implemented configuration system.
- **odd-extractor's audit-log shape (`<workspace>/.loam/extractions/<repo-id>/audit-log/<YYYY-MM-DD>-<NNNN>.yaml`) via `observability.write_audit_entry`.** The incremental mode appends to this same audit-log — every watch run is an event_kind `incremental_watch_run` / `incremental_proposal` / `incremental_ratification` / `incremental_rejection`.
- **loam unified CLI (`loam.cli.subcommands` entry-point group).** The `--incremental` flag extends the existing `odd-extract` subcommand surface — no new top-level subcommand.

The required research question — **"What Claude capability does this lean on or extend?"** — answer: every load-bearing primitive is composed (banded contract from odd-extractor, ratification flow from per-project-pm, profile from workspace-bootstrap, audit-log shape from odd-extractor's `observability`, CLI registration from existing odd-extract subcommand). The watch is the orchestration layer that ties them together for the incremental-update use case.

### Lens 2 — Harness + primary-persona value

- **Primary-persona test:** translation burden drops because the persona no longer has to hand-roll "did Eric's commits drift the contract?" — the watch decides + surfaces a domain-batched question; the persona just relays + records the response. The natural-language intent ("keep the contract synced as code evolves") translates to AI-effective execution ("run the watch on a schedule; route domain-batches through PM; ratify"). Pass.
- **Harness test:** every loam-driven persona (PR-author, PR-reviewer, security-reviewer, PM-on-call) can call `loam odd-extract <repo> --incremental` instead of re-implementing diff classification + per-AC re-extraction + domain-batching. Pass — the watch is a reusable harness primitive.

Both pass.

### Lens 3 — ODD authoring

Outcome above + named ACs (§4) + halt triggers (§9) + acceptance smoke (§7). Method (which diff library, which classifier heuristic, which Pydantic model layout, which audit-log YAML shape) stays the builder's call within the constraints (line-overlap + symbol-overlap + file-existence; ≥90% accuracy on synthetic test set; domain inference tag-based + file-path-prefix fallback).

### Lens 4 — Prompt scope ↔ confidence

Outcome confidence is **HIGH** for shape: master plan §3 Cycle 1 names the incremental mode + diff-classifier + proposal generation + PM extension + domain-batching + production-stake honour + audit-log floor. Tight scope: extension to the existing `odd-extract` CLI surface; halt-and-surface if any named primitive turns out unimplementable.

Outcome confidence is **MEDIUM** for the diff-classifier heuristic: master plan §7.1 calls this the load-bearing risk. Method (line-overlap-only vs symbol-overlap-only vs both vs AST-aware) is the builder's call within the constraint of ≥90% accuracy on a synthetic test set; this plan-doc commits to **line-overlap + file-existence + backing-files-overlap** as Cycle 1's heuristic, with AST-awareness deferred to a halt-and-surface escape hatch (mirrors v0.1.9 Cycle 1's pr-safety classifier choice).

Outcome confidence is **MEDIUM** for the domain inference algorithm: master plan §9 commits to "tag-based primary + file-path-prefix fallback." This plan-doc commits to: (1) `BandedAC` carries no first-class `domain:` field today, so Cycle 1 derives domain from the AC ID prefix (`AC.<DOMAIN>.<n>`) — the convention used by all sealed contracts (`AC.SYNTH.*`, `AC.RAILS.*`, `AC.PYTHON.*`, etc.); (2) for ACs whose ID doesn't follow the convention OR whose ID-prefix is too generic (e.g., `AC.OREK.*` for the extractor itself), fall back to common file-path prefix (e.g., `app/payment/` → domain `payment`); (3) ACs that match neither heuristic land in domain `_uncategorised`.

Outcome confidence is **LOW-MEDIUM** for scope-of-work cron primitive integration: master plan §6 open item #2 names this as a halt-trigger. Pre-flight inspection of `framework/scope-of-work/` confirms NO cron primitive exists (triggers are escalation predicates, not invocation schedulers). Surface #1 commits to: Cycle 1 ships the schedulable CLI primitive (`loam odd-extract <repo> --incremental`); cron integration is the consumer's call (system crontab, Anthropic `/schedule` skill, future scope-of-work cron extension). This avoids extending scope-of-work with a non-trivial new trigger kind. AC.WATCH.6 below tightens this to: "the CLI is the schedulable primitive."

### Lens 5 — Swarming

Single-component fence under `plugins/dev-sdlc/odd-extractor/`. Within the cycle, decomposition options:

- (a) one-file per concern (`incremental.py` for engine + `diff_classifier.py` for diff-against-prior + `proposals.py` for re-extraction proposal generation + `domain_batching.py` for grouping + `incremental_ratify.py` for PM enqueue) — natural decomposition mirroring odd-extractor's existing per-stage layout. Each with its own AC test.
- (b) collapse into existing module shapes (extend `analyze.py` + `verify.py` + `ratify.py` in-place) — denser but loses the named-feature surfaces.

The builder picks **(a)** — per-concern decomposition matches the master plan's "incremental engine / diff classifier / proposal generation / PM ratification / domain batching" naming and gives the tightest AC-per-file mapping. `max_planner_depth: 1` (no sub-planners; per-concern files are the right granularity already). No further decomposition adds value.

---

## §3 — Single-component fence

**Scope:** `plugins/dev-sdlc/` (the existing dev-sdlc plugin's sealed fence; the watch lands as new modules + new tests under the existing `plugins/dev-sdlc/odd-extractor/` sub-package).

**Existing paths (read-only or extend in-place; sealed-content unchanged):**

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/__init__.py` — extend exports (additive).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/cli.py` — extend `build_odd_extract_subcommand` with `--incremental` flag + handler dispatch (additive).
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/observability.py` — extend with new event-kind names (additive; `observability.write_audit_entry` already accepts arbitrary `event_kind` strings, so no API change needed).

**New paths (this cycle):**

- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/incremental.py` — the incremental engine + entry-point.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/diff_classifier.py` — diff-against-prior-contract logic.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/proposals.py` — re-extraction proposal generation.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/domain_batching.py` — domain inference + batching.
- `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/incremental_ratify.py` — PM enqueue for incremental proposals (composes with existing `ratify.py`).
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_WATCH_1_incremental_cli.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_WATCH_2_diff_classifier.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_WATCH_3_proposal_generation.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_WATCH_4_pm_ratification.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_WATCH_5_domain_batching.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_WATCH_6_scheduling_primitive.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_WATCH_7_production_stake.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_WATCH_8_audit_log.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_AC_WATCH_9_test_surface.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_incremental_smoke.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_incremental_idempotent.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_incremental_cross_session.py`
- `plugins/dev-sdlc/odd-extractor/tests/test_diff_classifier_accuracy.py`
- `plugins/dev-sdlc/odd-extractor/tests/fixtures/incremental/` — synthetic prior-contract + synthetic-changed-repo pairs (see §6 fixture catalog).

**No PM-side edits.** Open item #1 is RESOLVED via Cycle 1 commit to existing `PMRuntime.enqueue_decision(question_text, *, provenance)` API. Domain-batching is producer-side; PM remains read-only from this cycle's perspective.

**No scope-of-work edits.** Open item #2 is RESOLVED via Surface #1 commit to "CLI is the schedulable primitive; cron integration deferred to consumer."

**No workspace-bootstrap edits.** Production-stake gating reads `Manifest.safety_profile` via existing `load_manifest`.

---

## §4 — AC family — `AC.WATCH.*` (locked)

Each AC has at least one explicit pytest. ODD §2.5 — every line of code, every branch, every test maps to a named AC.

- **AC.WATCH.1 — Incremental-mode CLI.**
  - `loam odd-extract <repo> --incremental` reads the prior contract from `<workspace>/.loam/extractions/<repo-id>/contract-draft.yaml`; if absent, raises `ContractNotFoundError` (no cold-start through `--incremental` — caller must `loam odd-extract <repo>` once first).
  - For each AC in the prior contract, classify evidence as `still_current` / `out_of_date` / `orphaned` (file deleted) per AC.WATCH.2.
  - Default dry-run; `--live` opts in (mirrors existing `_cmd_extract` pattern). Under `safety_profile: production-stake`, `--live` does NOT bypass dry-run on proposal-write — proposals always emit but auto-update is gated (per AC.WATCH.7).
  - Output (text or `--json`): summary line ("3 still-current / 5 out-of-date / 1 orphaned across 2 domains"), per-domain proposal preview, list of newly-enqueued PM decision-question provenance strings.
  - Exit codes: 0 = success (proposals enqueued OR no drift detected); 2 = `OddExtractorError` (`ContractNotFoundError`, `IncrementalRefusedError`); 3 = `BudgetExceededError` (existing budget envelope inherited).
  - Test: argparse surface; runs against synthetic prior-contract + synthetic-changed-repo fixture; asserts exit code, summary text, JSON structure, per-domain decomposition.

- **AC.WATCH.2 — Diff-against-prior-contract logic.**
  - `classify_evidence(prior_contract: BandedContract, repo_path: Path) -> EvidenceClassification` walks each `BandedAC.evidence.citations` and `BandedAC.backing_files`:
    - **Line-overlap path:** parse each citation of shape `<file_path>:<start_line>[-<end_line>]` (e.g., `app/auth.py:42-58`). Read the current file at `repo_path / file_path`. If file missing → AC marked `orphaned`. If file exists but `evidence.repo_sha` is set AND the cited line range was modified between the SHA and `HEAD` (per `git log --diff-filter=M -L <start>,<end>:<file>` reverse-walk) → marked `out_of_date`. If `evidence.repo_sha` is unset (PLAUSIBLE/HYPOTHESISED w/o SHA pin), fall through to file-existence + backing-files overlap heuristic.
    - **File-existence + backing-files heuristic (no SHA pin):** if any `backing_files` entry no longer exists at `repo_path / backing_file` → marked `orphaned`. If all `backing_files` exist AND no `git log --since=<contract.created_at>` commit touched any backing-file → marked `still_current`. If any `git log --since=<contract.created_at>` commit touched any backing-file (file mtime check is acceptable when git history unavailable) → marked `out_of_date`.
    - **Test-citation path:** citations of shape `<file_path>::<test_name>` are treated as file-only matches (test-name resolution requires test-collection which is out of Cycle 1 scope — Cycle 1 treats them as file-existence checks plus backing-files overlap).
  - `EvidenceClassification` is a Pydantic model: `still_current: list[BandedAC]`, `out_of_date: list[OutOfDateAC]`, `orphaned: list[OrphanedAC]`. `OutOfDateAC{ac: BandedAC, drift_kind: Literal["citation_line_changed", "backing_file_changed"], affected_files: list[Path], from_sha: str | None, to_sha: str}`. `OrphanedAC{ac: BandedAC, missing_files: list[Path]}`.
  - **Accuracy bar:** synthetic test set in `tests/fixtures/incremental/classifier-accuracy/` covers ≥10 synthetic prior-contract + repo-state pairs spanning all 3 classifications (still-current / out-of-date / orphaned) and 4 drift shapes (line-edit / file-rename / file-delete / refactor-move). On the test set, classifier accuracy ≥90% (true-positive-rate + true-negative-rate, weighted by AC count). If <90%, halt-and-surface for AST-aware extension (master plan §7.1 escape hatch).
  - Test: per-classification unit tests + per-drift-shape unit tests + accuracy aggregate test + classifier deterministic-for-fixed-input test.

- **AC.WATCH.3 — Re-extraction proposal generation.**
  - For each `OutOfDateAC` (NOT `orphaned` — orphans are surfaced as a separate decision via AC.WATCH.4), invoke the v0.1.8 full-mode extractor scoped to the affected files:
    - Re-run `analyze_repo` over `affected_files` only (slice scope = the affected files).
    - Re-run `generate_raw_acs` over the resulting plan.
    - Re-run `verify_contract` with the prior contract's existing ACs as the baseline; new banded ACs replace prior ones with the same `ac_id` (matched by AC ID, not by content).
    - Capture the proposed new evidence (`citations`, `repo_sha`=current HEAD, `rationale` for HYPOTHESISED).
  - Each proposal carries `(ac_id, current_evidence, proposed_new_evidence, confidence_band, drift_kind, affected_files)`. Per-band confidence is preserved by default — Decision I default-no still applies, so re-extraction does NOT silently promote PLAUSIBLE→VERIFIED (the proposal carries the same band; reviewer can opt-in to band-change via the ratification response).
  - For `orphaned` ACs, the proposal is `(ac_id, current_evidence, proposed_new_evidence=None, drift_kind="orphaned")` — reviewer's options are `keep` (mark explicitly out-of-scope), `reject` (drop AC from contract), or `re-extract` (treat as not-orphaned and re-run extraction; this requires user-supplied evidence pointer).
  - `IncrementalProposalSet{ proposals: list[IncrementalProposal], extraction_id: str, prior_repo_sha: str | None, current_repo_sha: str, generated_at: str }`.
  - Test: re-extraction against synthetic prior-contract + synthetic-changed-repo fixture; assert proposed evidence reflects the new code; assert no silent band-change; orphaned-AC proposals skip re-extraction; budget envelope inherited from full mode (re-extraction respects the same `default_budget` ceiling).

- **AC.WATCH.4 — PM ratification-queue mechanics.**
  - `enqueue_incremental_proposals(*, extraction_id, proposals, workspace_root, pm_runtime, pm_handle)` → composes one `pm_runtime.enqueue_decision(question_text, provenance=...)` call per **domain-batch** (not per-AC; per AC.WATCH.5 — batching is the surfacing axis).
  - Question text per domain-batch:
    ```
    Domain '<domain-slug>' has <N> AC re-extraction proposals (drift detected since <prior-sha-short> → <current-sha-short>):
      - AC.X.1 (PLAUSIBLE; citation-line-changed): app/payment/charge.rb:42-58 → app/payment/charge.rb:51-67
      - AC.X.2 (VERIFIED; backing-file-changed): app/payment/refund.rb (3 hunks)
      - AC.X.3 (HYPOTHESISED → orphaned): app/payment/legacy.rb (file deleted)
    Reply with: ratify-all / revise-each / reject-all (or per-AC: AC.X.1=ratify AC.X.2=revise<text> AC.X.3=keep). Note: PLAUSIBLE→VERIFIED requires explicit confirmation per Decision I.
    ```
  - Provenance string per enqueued question: `f"odd-extract:incremental:{extraction_id}:{domain_slug}"`.
  - Idempotency: if a domain's proposal-set is byte-identical to a previously-enqueued + still-pending question (same `(extraction_id, domain_slug)` already in `decision-queue.yaml`), the second enqueue is a no-op (logged as `event_kind=incremental_enqueue_skip_duplicate`). The duplicate-detection scans the existing PM queue via `PMRuntime._pm_dir / "decision-queue.yaml"` for the matching provenance prefix.
  - Returns `EnqueueResult{ enqueued_domains: list[str], skipped_duplicates: list[str], total_proposals: int }`.
  - Test: synthetic prior-contract + 5 out-of-date ACs across 2 domains → `enqueued_domains=2`; re-run with same proposals → `skipped_duplicates=2`; one new proposal added → 1 new enqueue + 1 skip; PM `decision-queue.yaml` carries N entries with correct provenance prefix.

- **AC.WATCH.5 — Domain-batched AC surfacing.**
  - `infer_domain(ac: BandedAC) -> str` runs the heuristic:
    - **AC ID prefix path (primary):** parse `ac.ac_id` for shape `AC.<DOMAIN>.<n>` (e.g., `AC.RAILS.7` → `rails`). If matches, return the lowercased `<DOMAIN>`.
    - **File-path-prefix fallback:** if AC ID doesn't match the regex OR `<DOMAIN>` is too generic (in `{"OREK", "BANDS", "SYNTH", "FIXTURES", "DPS1", "DPS2", "PRSG", "WATCH"}` — the loam-internal AC namespaces from existing sealed cycles), fall back to common file-path prefix across `ac.backing_files` and `ac.evidence.citations`. Algorithm: split each path on `/`; take the longest common prefix across all entries; if non-empty, return the last segment (e.g., `app/payment/charge.rb` + `app/payment/refund.rb` → `payment`).
    - **`_uncategorised` fallback:** if neither path produces a domain, return `_uncategorised` (the literal string).
  - `group_by_domain(proposals: list[IncrementalProposal]) -> dict[str, list[IncrementalProposal]]` runs `infer_domain` over each proposal's `ac` and groups; preserves insertion order within each group; sorted-keys output for determinism.
  - **Determinism:** `group_by_domain` is pure; same input always produces the same dict (sorted keys; insertion-order preserved within each value list). This is load-bearing for AC.WATCH.4 idempotency check (same proposals → same domain-grouping → same enqueue → no duplicates).
  - Test: AC ID prefix path with `AC.RAILS.7` + `AC.PYTHON.3` → 2 domains; file-path-prefix fallback with `AC.OREK.1` + paths under `app/payment/` → domain `payment`; `_uncategorised` fallback for AC ID `WATCH-0001` (non-conformant) + empty `backing_files` + empty citations; mixed input with all three paths.

- **AC.WATCH.6 — Scheduling integration (CLI-as-primitive).**
  - **Surface clarification:** the CLI invocation `loam odd-extract <repo> --incremental` IS the schedulable primitive. Cycle 1 does NOT extend `framework/scope-of-work/` with a new cron-trigger kind (master plan §6 open item #2 RESOLVED via this clarification — see Surface #1). The CLI is exit-code-clean (0 = success, 2/3 = failure modes documented at AC.WATCH.1) so any external scheduler (system crontab, Anthropic `/schedule` skill, future scope-of-work cron extension, GitHub Actions, etc.) can invoke it and react to exit status.
  - **Documentation surface:** `plugins/dev-sdlc/odd-extractor/README.md` appends a "Scheduling" section showing three example schedules: (1) macOS launchd plist invoking `loam odd-extract <repo> --incremental`; (2) Linux crontab `0 */6 * * * loam odd-extract <repo> --incremental >> $HOME/loam-watch.log`; (3) Anthropic `/schedule` skill invocation referencing the README.
  - **Telemetry guarantee:** every invocation (whether human-driven or scheduler-driven) writes one `event_kind=incremental_watch_run` audit-log entry with `notes` carrying the trigger source (default `cli_human` if not specified; scheduler can pass `--invocation-source <slug>` to record `cli_cron` / `cli_schedule_skill` / etc.).
  - Test: `--invocation-source` flag accepted + recorded in audit-log; default value `cli_human`; scheduler-driven invocations are observable in `<workspace>/.loam/extractions/<repo-id>/audit-log/`.

- **AC.WATCH.7 — Production-stake honour-flow.**
  - `is_production_stake(workspace_root: Path) -> bool` reads `Manifest.safety_profile` via existing `loam.workspace_bootstrap.load_manifest`; returns `True` iff value is `"production-stake"`.
  - Under production-stake: `--live` is silently downgraded to dry-run for the **proposal-write side** (proposals are GENERATED + ENQUEUED through PM, but the contract sidecar is NOT mutated; ratification through PM is the only route to contract-sidecar update). Dry-run downgrade is recorded in audit-log with `notes="production_stake_dry_run_downgrade"`.
  - Under dev / research: `--live` proposals enqueue through PM; ratification is still required (the contract sidecar is NEVER auto-mutated by the watch; only ratification flow can update it). Dev/research differs from production-stake only in the audit-log entry shape (no downgrade note).
  - **Defense in depth:** even with `--live` + dev-profile, the watch's contract-sidecar mutation path requires a ratification action (`apply_ratification_action` from existing `ratify.py`) to be invoked separately — Cycle 1's watch enqueues proposals but does NOT auto-apply them, regardless of profile. This is structural; the watch's code path simply doesn't include a sidecar-write call.
  - Test: gate run against tmp workspace with `safety_profile: production-stake` → audit-log has downgrade note + sidecar unchanged; same against `safety_profile: dev` → no downgrade note + sidecar still unchanged (defense in depth); no `loam.yaml` (default profile=dev fallback) → dev-profile behaviour.

- **AC.WATCH.8 — Audit-trail floor.**
  - Audit-log directory: existing `<workspace>/.loam/extractions/<repo-id>/audit-log/`. Filename: `<NNNN>.yaml` (the actual existing odd-extractor convention per `observability.py:80` — monotonic counter, NOT date-scoped; per-project-pm uses date-scoped `<YYYY-MM-DD>-<NNNN>.yaml` but odd-extractor's audit-log is per-extraction-bounded so no date scoping is needed).
  - Event kinds added by Cycle 1:
    - `incremental_watch_run` — written at start of every `--incremental` invocation; carries `prior_contract_path`, `prior_repo_sha`, `current_repo_sha`, `invocation_source`, `safety_profile`, `dry_run`.
    - `incremental_classification` — one entry summarising the classification result; carries `still_current_count`, `out_of_date_count`, `orphaned_count`.
    - `incremental_proposal` — one entry per **domain-batch** (NOT per proposal — domain-batching is the surfacing axis); carries `domain`, `ac_count`, `provenance_string`, `enqueued` (bool — false if duplicate-skip).
    - `incremental_enqueue_skip_duplicate` — written when a domain-batch's proposals are byte-identical to a still-pending PM question; carries `domain`, `provenance_string`.
    - `incremental_ratification` — written when a ratification-action consumed an incremental proposal; reuses existing `ratification_<kind>` event-kinds via the existing `ratify.apply_ratification_action` audit path (no new event-kind needed).
    - `incremental_rejection` — written when a domain-batch's PM question is rejected (consumed via existing PM `record_response` flow with negative response); the existing `ratification_reject` event-kind covers per-AC; the new `incremental_rejection` event covers the domain-batch-level rejection.
  - Schema (additive over existing audit-log):
    ```yaml
    schema_version: 1
    event_kind: <one of above>
    timestamp: <iso8601-tz>
    extraction_id: <repo-id>
    notes: <str>           # carries event-specific payload as " key1=val1 key2=val2"
    artefact_path: <str | null>
    ```
  - Test: D6 telemetry-floor — each event-kind writes one entry; entry parses as YAML; schema_version present; timestamp ISO8601 with TZ; required fields populated; notes carries event-specific payload.

- **AC.WATCH.9 — Component-level test surface.**
  - Per-AC test files: `test_AC_WATCH_1_incremental_cli.py` ... `test_AC_WATCH_9_test_surface.py` (one file per AC, mirroring v0.1.9 Cycle 1 convention).
  - Plus integration tests:
    - `test_incremental_smoke.py` — D1 cold-state: end-to-end `read_prior_contract → classify_evidence → generate_proposals → group_by_domain → enqueue_through_pm` against the synthetic prior-contract + synthetic-changed-repo fixture; asserts PM queue carries N domain-batched entries.
    - `test_diff_classifier_accuracy.py` — accuracy aggregate across the synthetic test set (≥10 prior-contract + repo-state pairs); asserts ≥90% accuracy bar; halt-trigger fires below threshold.
    - `test_incremental_idempotent.py` — D2 idempotency variant: 5 watch invocations against the same (prior-contract, repo-state) pair produce byte-identical proposal sets + 1 PM enqueue + 4 skip-duplicate audit entries.
    - `test_incremental_cross_session.py` — D5 cross-session: subprocess invocations of the watch against the same workspace; PM queue accumulates correctly across boundaries; no overwrite.
    - `test_no_sealed_amendments.py` — seal-fence test (delegated to existing parent `plugins/dev-sdlc/tests/test_no_sealed_amendments.py` which already covers the entire dev-sdlc subtree).
  - All tests must pass before seal.

- **AC.WATCH.10 — End-to-end smoke against canonical fixtures.**
  - **Cycle-level smoke** (release-level smoke at v0.2.0 close per master plan §5 + Decision R; Cycle 1 ships its own end-to-end against synthetic fixtures, and the canonical-fixture run is exercised at release-level).
  - For Cycle 1's end-to-end smoke: synthetic prior-contract + synthetic-changed-repo fixture with at least 2 domains (e.g., `payment` + `auth`) and at least 6 ACs split across them; expected outcome: 2 domain-batched PM questions; classifier classifies all ACs correctly; production-stake-profile dry-run downgrade observed; audit-log carries all 6 event-kinds.
  - **Eric-fixture smoke (release-level scope, NOT Cycle 1):** synthetic JS code-change on `tests/fixtures/jsts-playwright-app/` + synthetic Rails-callback addition on `tests/fixtures/ruby-rails-payment/` are exercised at v0.2.0 release-level smoke, not within Cycle 1. Cycle 1's smoke covers the engine + classifier + domain-batching against a smaller synthetic fixture; the canonical-fixture exercise lands at release-level.
  - Test: `test_incremental_smoke.py` (Cycle 1).

---

## §5 — Halt-and-surface BEFORE build (recorded autonomous decisions)

Three surfaces. Per AUTONOMY directive + LOCKED-DESIGN-NOT-LICENSE + critical-thinking-on-deviations, autonomous decisions are recorded here rather than escalated to Luke.

### Surface #1 — scope-of-work cron primitive non-existent (RESOLVED via CLI-as-primitive)

**Conflict:** master plan §6 open item #2 names this as a halt-trigger if scope-of-work doesn't admit cron cleanly. Pre-flight inspection of `framework/scope-of-work/src/loam/scope_of_work/spec.py` confirms the existing `Trigger` discriminated-union has 5 kinds (`budget_threshold`, `time_elapsed`, `event_type`, `success_criterion`, `reversibility`) but NO cron-style invocation-trigger. These are escalation predicates fired during scope evaluation, not invocation schedulers.

**Signals:**

- Reversibility: extending scope-of-work with a new cron-trigger is reversible but adds substantial new component scope (master plan halt-trigger).
- Blast radius: scope-of-work is used by all v0.1.x builds; a new trigger kind is a public-API addition with downstream contract implications.
- Time pressure: Cycle 1's wall-clock band is 8–14 h; cron-trigger work would consume 2–4 h additional, blowing the budget.
- Information asymmetry: the master plan author's intent ("compose with scope-of-work cron primitive") presumes existence; Cycle 1 plan-author has perfect information that none exists. The right move is "ship the schedulable primitive; let cron be the consumer's call."

**Resolution (recorded autonomously):** Cycle 1 ships `loam odd-extract <repo> --incremental` as the schedulable primitive (exit-code clean, observability via audit-log, idempotent on no-drift). Any external cron mechanism (system crontab, Anthropic `/schedule` skill, future scope-of-work cron extension, GitHub Actions) can invoke it. AC.WATCH.6 documents the three example schedules (launchd, crontab, `/schedule`) in the README. This avoids the substantial scope-of-work extension while satisfying the master plan's "scheduling-integration" deliverable shape.

**Halt-trigger preserved:** if AC.WATCH.6's CLI-as-primitive shape proves insufficient at v0.2.0 release-level smoke (e.g., schedulers can't observe per-run telemetry), surface for revisit at v0.2.1. Cycle 1 ships the primitive; v0.2.x can extend scope-of-work if needed.

### Surface #2 — PM-side batch-type registration not needed (RESOLVED via thin extension)

**Conflict:** master plan §6 open item #1 names this as a halt-trigger if PM extension is substantial. Pre-flight inspection of `framework/per-project-pm/src/loam/per_project_pm/runtime.py:240` confirms `enqueue_decision(question_text, *, provenance)` already accepts arbitrary text + provenance string. NO type-registration system exists; question identity is carried by the text + provenance string.

**Signals:**

- Information asymmetry: the v0.1.7 Cycle 4 PM batch API is intentionally simple — adding a typed registry is a substantial schema change with cross-component blast radius.
- Reversibility: adding a typed registry would lock-in a contract that v0.1.7's existing API consumers (odd-extract ratify-flow, pr-safety override-flow) didn't sign up for.
- Audience: every existing producer composes through `enqueue_decision`; preserving that API is the right move.

**Resolution (recorded autonomously):** Cycle 1's `enqueue_incremental_proposals` (AC.WATCH.4) composes one `pm_runtime.enqueue_decision(question_text, provenance=f"odd-extract:incremental:{extraction_id}:{domain_slug}")` call per domain-batch. Question-text shape carries the type identity (mirroring how `_question_for_banded_ac` in existing `ratify.py` carries identity for AC ratification). NO PM-side edits.

**Halt-trigger preserved:** if v0.2.0 release-level smoke reveals the question-text shape is insufficient (e.g., persona can't disambiguate incremental-proposals from full-mode-ratification), surface for revisit at v0.2.1 with explicit batch-type registry proposal.

### Surface #3 — orphaned-AC handling (RESOLVED via separate proposal kind)

**Conflict:** master plan §3 Cycle 1's AC.WATCH.3 names "out-of-date AC" but doesn't fully specify orphaned-AC handling. Pre-flight thought: orphans (file deleted entirely) can't be re-extracted because there's no source to re-read.

**Signals:**

- Outcome confidence: high — orphans are a distinct decision shape from out-of-date ACs.
- Audience: reviewer's options for orphans differ semantically (keep / reject / re-extract-with-new-evidence) from out-of-date (ratify-revised-evidence / revise / reject).

**Resolution (recorded autonomously):** Cycle 1 surfaces orphans as a distinct proposal kind with `proposed_new_evidence=None` + `drift_kind="orphaned"`. The PM question text enumerates the three options explicitly. The orphan AC's `ac_id` is included in the same domain-batch as out-of-date ACs in the same domain (consolidates the surface; reviewer ratifies all of `payment`'s drift in one decision).

---

## §6 — Synthetic fixture catalog

The synthetic-changed-repo fixture lives at `plugins/dev-sdlc/odd-extractor/tests/fixtures/incremental/`. The fixture covers all classifications + drift shapes + domain-inference paths needed for AC.WATCH.{2,5,9,10}.

### `prior-contract.yaml` (synthetic v0.1.8-shape contract)

Re-uses `synthetic-banded-contract.yaml`'s 3 ACs (`AC.SYNTH.1` VERIFIED, `AC.SYNTH.2` PLAUSIBLE, `AC.SYNTH.3` HYPOTHESISED) AS the prior contract; adds 4 more ACs covering domain-inference paths:

- `AC.PAYMENT.1` (PLAUSIBLE; `app/payment/charge.rb:12-30`; backing `app/payment/charge.rb`).
- `AC.PAYMENT.2` (VERIFIED; `tests/test_charge.rb::test_charge_idempotency` + `app/payment/charge.rb:55-72`; repo_sha `abc123` pin; backing `app/payment/charge.rb`, `tests/test_charge.rb`).
- `AC.AUTH.1` (PLAUSIBLE; `app/auth/login.rb:5-25`; backing `app/auth/login.rb`).
- `AC.LEGACY.1` (HYPOTHESISED; backing `app/legacy/old_module.rb`).

### `repo-states/` (3 synthetic repo-state directories)

Each represents a different "current" state of the repo at watch-time:

- `repo-states/no-drift/` — all files unchanged from `prior-contract.yaml`'s expectations. Expected: 7 still-current / 0 out-of-date / 0 orphaned.
- `repo-states/single-line-edit/` — `app/payment/charge.rb` lines 12-30 modified (citation-line-changed for `AC.PAYMENT.1`). Expected: 6 still-current / 1 out-of-date / 0 orphaned; domain-batch `payment` carries 1 proposal.
- `repo-states/mixed-drift/` — `app/payment/charge.rb` modified (citation-line-changed for `AC.PAYMENT.1` + backing-file-changed for `AC.PAYMENT.2`); `app/auth/login.rb` modified (citation-line-changed for `AC.AUTH.1`); `app/legacy/old_module.rb` deleted (orphaned `AC.LEGACY.1`). Expected: 3 still-current / 3 out-of-date / 1 orphaned; 3 domain-batches (`payment`, `auth`, `legacy`).

### `classifier-accuracy/` (≥10 synthetic prior-contract + repo-state pairs)

Each pair has an expected classification matrix. Used by `test_diff_classifier_accuracy.py`:

1. `01-no-drift/` — all still-current.
2. `02-single-line-edit/` — single citation-line drift.
3. `03-file-rename/` — file moved (renamed); should be detected as drift via backing-file existence-check.
4. `04-file-delete/` — file deleted; orphaned.
5. `05-refactor-move/` — code moved within same file (line range shifted); citation-line drift.
6. `06-whitespace-only/` — file-content-changed but no semantic change; characterises false-positive risk (Cycle 1 accepts as out-of-date; reviewer ratifies).
7. `07-comment-only/` — comment-only change within citation range; same as #6.
8. `08-mixed-drift-2-domains/` — drift in 2 domains; domain-batching + classifier exercised together.
9. `09-orphaned-with-new-file/` — old file deleted + new file added; orphaned + novel-candidate (Cycle 1 surfaces orphan; novel-candidate is full-mode territory, deferred).
10. `10-test-citation-stale/` — `<file>::<test_name>` citation; file unchanged but test removed; Cycle 1 treats as file-existence (still_current; test-resolution out of scope).

### `domain-inference-cases/` — fixtures for AC.WATCH.5 algorithm

Five tiny prior-contract YAMLs, one per domain-inference case (AC ID prefix path / file-path-prefix fallback / `_uncategorised` fallback / mixed / generic-prefix-skip).

---

## §7 — Smoke (REALISTIC CONDITION — applicable dimensions per smoke-test-discipline §6)

Cycle-level smoke. Release-level SOFT gate at v0.2.0 close (master plan §5 + Decision R), not this cycle. Quality-bar non-negotiable still applies. All 6 dimensions exercised at cycle level OR documented n/a.

### D1 — cold-state (fresh canonical workspace)

**Pattern.** Tmp workspace; tmp git repo seeded with the synthetic prior-contract written into `<workspace>/.loam/extractions/<repo-id>/contract-draft.yaml` directly + the `repo-states/mixed-drift/` repo-state. Run `loam odd-extract <repo> --incremental --json` → assert: (a) summary "3 still-current / 3 out-of-date / 1 orphaned"; (b) exit code 0; (c) PM `decision-queue.yaml` carries 3 entries with provenance prefixes `odd-extract:incremental:<id>:payment` / `:auth` / `:legacy`; (d) audit-log carries `incremental_watch_run` + `incremental_classification` + 3× `incremental_proposal` entries.

**Test:** `test_incremental_smoke.py`.

### D2 — steady-state durability (idempotency variant)

**Structural rationale.** Watch is one-shot CLI invocation, not a long-running daemon. Smoke-test-discipline §6 quick-reference: D2 doesn't engage in the "daemon stays up under load" sense.

**Idempotency variant exercised.** AC.WATCH.9's `test_incremental_idempotent.py` runs 5 watch invocations against the same (prior-contract, repo-state) pair and asserts: (a) byte-identical classification results across all 5 (same `still_current_count`, `out_of_date_count`, `orphaned_count`); (b) PM queue grows by N entries on first run, by 0 on runs 2-5; (c) audit-log shows 5 `incremental_watch_run` entries + 4 `incremental_enqueue_skip_duplicate` entries per affected domain. This satisfies the master plan dispatch's "D2 idempotency variant: 5+ watch runs on same state are byte-identical" wording.

### D3 — restart resilience (n/a)

**Structural rationale.** No long-running process to kill. Watch is single Python process; if it crashes mid-run (e.g., during re-extraction of an out-of-date AC), the audit-log carries the partial `incremental_watch_run` start entry; next invocation reads no completion marker + re-runs cleanly. State is stateless from watch's perspective — every invocation is fresh against the prior-contract + current-repo-state.

### D4 — reboot resilience (n/a)

**Structural rationale.** Same as D3 — no daemon to recover after host reboot. Filesystem state (audit-log, prior-contract sidecar, PM `decision-queue.yaml`) survives reboot trivially. Cross-session continuity (D5) is the relevant analog.

### D5 — cross-session continuity (load-bearing)

**Pattern.** Process A: invoke watch against `mixed-drift` → PM queue grows by 3 entries + audit-log entries written. Process B (subprocess invocation in fresh process): re-invoke same watch → all 3 enqueues skipped (duplicate detection); audit-log carries 4 entries (watch_run + classification + 3× skip). Process C (subprocess): consume the first PM question via `pm_runtime.surface_next_questions_batch(n=1)`; record affirmative response via `record_response`. Process D: re-invoke watch → 2 of 3 still-pending; 1 (consumed) is no longer in PM queue but the response is recorded — re-running watch should NOT re-enqueue that domain (the PM queue is the authority for "is this still pending"; consumed questions aren't pending anymore). Assert: (a) audit-log dir survives process boundary; (b) PM queue + responses survive; (c) decisions are stable across processes.

**Test:** `test_incremental_cross_session.py`.

The `/clear` analog is "fresh process boundary"; the test validates that boundary directly via subprocess invocations. Master plan §5 D5 calls cross-session "most-load-bearing" — Cycle 1 honours this with explicit subprocess testing.

### D6 — telemetry floor

**Pattern.** Run a full watch cycle covering each event-kind:

- `incremental_watch_run` (every invocation).
- `incremental_classification` (every invocation post-classification).
- `incremental_proposal` (per domain-batch).
- `incremental_enqueue_skip_duplicate` (per duplicate-skip).
- `ratification_<kind>` for `incremental_ratification` (existing event-kind via `apply_ratification_action`).
- `incremental_rejection` (per domain-batch rejection).

Assert: (a) `<workspace>/.loam/extractions/<repo-id>/audit-log/` directory exists; (b) one entry per event-kind invocation; (c) every entry carries `schema_version: 1`, `timestamp` (ISO8601 with TZ), `extraction_id`, `event_kind`, `notes`; (d) filenames follow `<YYYY-MM-DD>-<NNNN>.yaml` with monotonic per-day NNNN sequence (existing convention).

**Test:** `test_AC_WATCH_8_audit_log.py` + `test_incremental_smoke.py`.

---

## §8 — Out of scope

Explicit deferrals (master plan §3 Cycle 1 + per-cycle dispatch):

- **Auto-skill-creation.** → Cycle 2 (serial dependency).
- **On-merge / on-PR-open hook triggers.** → v0.2.x.
- **Automatic VERIFIED→PLAUSIBLE demotion.** → v0.2.x (Decision I default-no still applies).
- **Multi-fixture watch concurrency.** → v0.2.x.
- **AST-aware symbol-graph classifier extension.** → halt-trigger escape-hatch only (master plan §7.1); not Cycle 1 scope unless accuracy <90%.
- **Test-execution integration for VERIFIED-touched diffs (running the actual test to confirm regression).** → v0.2.x; Cycle 1's classifier checks file-existence + line-overlap + backing-files-overlap, not test-execution.
- **scope-of-work cron primitive extension.** → Surface #1; CLI is the schedulable primitive in Cycle 1; future cron extension is consumer's call.
- **PM-side batch-type registry.** → Surface #2; thin extension via existing `enqueue_decision` API.
- **Eric's actual codebases (real OSS smoke).** → v0.2.1 fresh-user smoke gate.
- **Novel-candidate AC extraction in incremental mode.** → full-mode territory; Cycle 1 surfaces orphans only (file-deleted), not novel additions (file-added). Novel additions land via re-running full mode `loam odd-extract <repo>` (without `--incremental`).
- **Persona-side wiring of incremental-ratification UX.** → loam-skills (out of cycle scope; harness-side primary-persona work at v0.2.0 Cycle 2 + v0.2.x).

---

## §9 — Halt triggers (in-flight)

Per dispatch + master plan:

- **WD drifts.** If `git rev-parse --show-toplevel` is not `/Users/lukeivers/ivers-corp-pos-v2/`, halt + surface.
- **v0.1.8 Cycles 2–4b not sealed.** If `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/bands.py` (Cycle 2) or the canonical fixtures (`tests/fixtures/jsts-playwright-app/`, `tests/fixtures/ruby-rails-payment/` from Cycle 4b) are absent, halt — incremental mode depends on these. (Pre-flight: both are present at HEAD `7c0f87b`.)
- **v0.1.7 Cycle 4 PM batch API absent.** If `enqueue_decision` absent from `loam.per_project_pm.PMRuntime`, halt — incremental mode's domain-batched enqueue depends on this. (Pre-flight: present.)
- **Plan-doc not authored before code.** This document IS that plan-doc. If code lands before this is committed, halt.
- **Diff classifier accuracy <90% on synthetic test set.** Master plan §7.1 names this as the most-load-bearing risk. Halt + surface for AST-aware extension.
- **Any AC ships partial.** If `test_AC_WATCH_<n>_*.py` is XFAIL, skipped, or asserts a degraded behaviour, halt + reframe before sealing.
- **PM-extension scope reveals more than thin batch-type registration.** If domain-batched surfacing requires non-trivial PM-side schema changes (vs Surface #2's thin commit to existing `enqueue_decision`), halt + surface (master plan §6 open item #1).
- **Scheduling-integration reveals scope-of-work primitive doesn't admit cron cleanly.** If AC.WATCH.6's CLI-as-primitive shape proves insufficient (e.g., schedulers can't observe per-run telemetry), halt + surface (master plan §6 open item #2). Surface #1's resolution is the autonomous call; halt-trigger preserved if Surface #1 turns out wrong.
- **D5 cross-session smoke fails.** Master plan §5 calls cross-session "most-load-bearing"; halt unconditionally on red.
- **Cycle exceeds 5 hours wall-clock.** Halt with partial findings; consider further decomposition.
- **ODD violations discovered in surrounding code.** Halt + surface; do not silently extend (per `feedback_subagent_odd_violation_halt`).
- **More than 3 in-build decisions need Luke escalation.** Master plan recommends 3 (this is a ship-quality cycle).
- **Watch's silent contract-mutation discovered.** If any code path in this cycle mutates `<workspace>/.loam/extractions/<repo-id>/contract-draft.yaml` outside the existing `ratify.apply_ratification_action` flow, halt + RF — defense-in-depth violation.

---

## §10 — F2 Ruthless Feedback (gaps named this turn)

1. **Diff classifier line-overlap is fragile against refactor-shaped diffs.** A diff that moves AC-relevant code from line 42 to line 100 (no semantic change) will register as drift even if the semantics are identical. Cycle 1's heuristic accepts this — reviewer ratifies via PM. The `test_diff_classifier_accuracy.py` synthetic test set MUST include refactor-shaped diffs (`05-refactor-move/`) to characterise this — accuracy ≥90% holds across the test set; if not, halt + AST extension (master plan §7.1 escape hatch). Mirrors v0.1.9 Cycle 1's same risk + same mitigation.

2. **Domain-inference falls back to `_uncategorised` for non-conformant AC IDs + no common file-path prefix.** ACs without `AC.<DOMAIN>.<n>` shape AND with no shared `backing_files` prefix produce a single `_uncategorised` domain-batch — which can swell to dozens of unrelated proposals. Mitigation: synthetic fixtures include a `_uncategorised`-fallback case to characterise the noisy bucket; v0.2.1 Eric-deliverable smoke surfaces real-world fit + may motivate first-class `domain:` field in `BandedAC`. Plan-doc commits to today's heuristic; first-class field is forward-deferred.

3. **`incremental_enqueue_skip_duplicate` detection scans PM `decision-queue.yaml` for matching provenance prefix on every domain.** O(N×M) where N=pending PM questions, M=Cycle 1 domain count. For Cycle 1 (M typically <10, N typically <100), this is trivially fast. If v0.2.x sees thousands of pending questions, this scan becomes a bottleneck. Flagged for awareness; not a Cycle 1 mitigation.

4. **The classifier doesn't reason about line-context (whitespace-only changes, comment-only changes).** A diff that's purely whitespace + comment churn within an AC's cited lines registers as drift. Cycle 1 ships the simplest semantics; reviewer ratifies. Whitespace/comment-aware filtering is a v0.2.x candidate. The fixture set includes `06-whitespace-only/` + `07-comment-only/` to characterise the false-positive frequency.

5. **Domain-batch question-text is bounded by PM's question-text length tolerance.** If a domain has 50+ ACs in a single batch, the question-text becomes a wall of bullet points. Master plan §3 Cycle 1's "12 ACs in payment-handling need re-extraction" is the design-time expectation; 50+ ACs is an edge case. Mitigation: question-text truncates at 25 ACs with a `... (and N more)` suffix; reviewer can request the full set via revise-flow. Out-of-Cycle-1: pagination of domain-batches into sub-batches with separate provenance strings.

6. **Production-stake honour-flow is structural (no `--live` overrides), but dev-profile is also no-auto-mutate.** F2 RF: Cycle 1's defense-in-depth means dev/research and production-stake have IDENTICAL contract-mutation behaviour (none). The audit-log carries the downgrade note only under production-stake. Honest framing: production-stake's distinguishing feature is observability of the downgrade-decision, not behaviour change. Eric's SOC-2 floor probably wants this conservative-by-default behaviour anyway.

7. **`infer_domain` reads AC ID prefix as the primary signal — but loam-internal AC namespaces (`AC.OREK.*`, `AC.BANDS.*`, `AC.WATCH.*`, etc.) shouldn't surface as domains.** Mitigation: blocklist hard-coded in `infer_domain` (`{"OREK", "BANDS", "SYNTH", "FIXTURES", "DPS1", "DPS2", "PRSG", "WATCH"}`). When matched against the blocklist, fall through to file-path-prefix. Risk: blocklist drifts as new loam components are added (e.g., v0.2.0 Cycle 2 adds `AC.SKILLCAP.*`). Mitigation: blocklist is a constant in `domain_batching.py` with a comment noting "update when adding new loam-internal AC namespaces." Long-term fix: first-class `BandedAC.domain` field; out of Cycle 1 scope.

8. **Manifest schema v3 fourth or later real-build-use after DPS2 + odd-extractor cycles + v0.1.9 cycles.** v3 fields exercised: `plan_doc_ref`, `ac_count`, `smoke_outcome`. Builder verifies seal-commit shape post-apply matches DPS2's expectations. The most-recent v3 seal is v0.1.9 Cycle 3 `3284087`; Cycle 1 here is the next.

9. **Cycle 1 wall-clock band 8–14 h with 5 h halt-trigger.** This is a tight halt-trigger for the highest-risk cycle of v0.2.0. The halt-trigger forces an early surface if the classifier accuracy work bleeds the schedule — that's the right escape, since the classifier is the most-load-bearing risk. If the build is on-track at hour 5 with classifier accuracy passing, dispatcher should consider extending another 1-3h to seal cleanly rather than splitting.

10. **Re-extraction proposal generation re-invokes full-mode workflow scoped to affected files — but Cycle 1's full-mode (v0.1.8) ships zero language adapters that produce real ACs.** Per `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/spec.py:84-89`, "Cycle 1 ships zero adapters, so :attr:`acs` is always empty and every input path lands in :attr:`unhandled_paths`." The synthetic-banded-contract.yaml fixture is hand-authored; real-codebase incremental re-extraction requires v0.1.8 Cycles 3+4 adapters (Ruby + Python first-class) — which DID land at `6711dd7` (Cycle 3) + `67dd302` (Cycle 4a) + `c648cf9` (Cycle 4b). Pre-flight: `tests/fixtures/jsts-playwright-app/` + `tests/fixtures/ruby-rails-payment/` are present. Cycle 1's smoke against the synthetic prior-contract uses hand-authored proposed evidence (the test fixture pre-bakes the proposed evidence; the engine path that re-invokes `verify_contract` is exercised but the evidence content is fixture-driven, not adapter-derived). Real-codebase incremental smoke lands at v0.2.0 release-level (master plan §5 Eric-path smoke).

---

## §11 — Provenance trail

- **Master plan source authority:** `docs/rebuild/plans/v0-2-0-master-plan.md` §3 Cycle 1 + §4 Cycle 1 dispatch (committed `7c0f87b`).
- **Eric synthesis:** `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` — Decisions I (PLAUSIBLE→VERIFIED default-no), P (SOC-2 floor), Q (one-question-at-a-time), R (HARD/SOFT smoke gate cadence).
- **v0.1.9 Cycle 1 (PR-safety gate engine — diff-classifier precedent):** `plugins/dev-sdlc/pr-safety/` sealed at `790807d`. Same line-overlap + symbol-overlap heuristic; same ≥90% accuracy bar.
- **v0.1.8 Cycle 2 (banded contract types):** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/bands.py` — `BandedAC`, `Evidence`, `ConfidenceBand`. Sealed at `4865028`.
- **v0.1.8 Cycle 2 (ratification flow):** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/ratify.py` — `enqueue_ratification_batch`, `_question_for_banded_ac`, `apply_ratification_action`. Same precedent shape for incremental-mode PM enqueue.
- **v0.1.8 Cycles 3+4 (full-mode extractor + adapters):** `analyze.py`, `generate.py`, `verify.py`. Sealed at `6711dd7` / `67dd302` / `c648cf9`.
- **v0.1.7 Cycle 4 (PM batch API):** `framework/per-project-pm/src/loam/per_project_pm/runtime.py:240` — `enqueue_decision(question_text, *, provenance)`. Same composition pattern.
- **v0.1.7 Cycle 2 (PM RatificationBatch):** `framework/per-project-pm/src/loam/per_project_pm/ratification.py` — `RatificationBatch.from_banded_acs`. Composes through `enqueue_decision`.
- **v0.1.6 Cycle 1 (production-safety + cost-governance):** `framework/workspace-bootstrap/src/loam/workspace_bootstrap/manifest.py` — `Manifest.safety_profile`, `LEGAL_SAFETY_PROFILES`. Sealed at `3f1d237`.
- **v0.1.8 Cycle 1 (odd-extractor scaffold + state location convention):** `plugins/dev-sdlc/odd-extractor/src/loam_odd_extractor/state.py` — `compute_repo_id`, workspace state path convention. Sealed at the v0.1.8 baseline.
- **Dev-pattern-simplifications #1 + #2 (manifest schema v3 + seal-narrative compression):** sealed at `019cfca` + `df3f50f`. Cycle 1 uses v3 schema.
- **Smoke-test-discipline:** `plugins/dev-sdlc/docs/smoke-test-discipline.md` — six dimensions; D2/D3/D4 marked n/a for one-shot CLI per quick-reference card §6 (D2 idempotency variant exercised).
- **ODD-methodology:** `plugins/dev-sdlc/docs/odd-methodology.md` — every line maps to a named AC (ODD §2.5).
- **Lens 5 (swarming) reference + stopping criterion:** `~/.claude/projects/-Users-lukeivers-pos3/memory/feedback_swarming_recursive_decomposition.md` + framework/CLAUDE.md Lens 5.
- **Quality bar (Luke directive 2026-05-04):** master plan §1 verbatim + master plan §3 Decision R framing.

---

## §12 — Bookkeeping

- **Manifest:** `docs/rebuild/plans/v0-2-0-cycle-1-continuous-watch.manifest.yaml` — schema_version: 3 with `plan_doc_ref:`. amendment.number omitted per AC.DPS1.10. ac_count: 10. smoke_outcome: "D1 + D2-idempotency + D5 + D6 exercised; D3/D4 n/a per smoke-test-discipline §6 (one-shot CLI); classifier accuracy ≥90% on synthetic test set; full-suite green sweep".
- **Apply:** `loam amend apply <manifest>` — single merged manifest+apply commit per AC.DPS1.6 (v3 schema). NOT `git commit --amend`; pos-amend creates a new commit per `feedback_no_amend_in_agent_dispatches`.
- **Seal:** `loam amend seal --plan-doc docs/rebuild/plans/v0-2-0-cycle-1-continuous-watch.md <manifest>` — synthesizes 5–15 line narrative body per AC.DPS2.{1,4} into `plugins/dev-sdlc/seals/SEAL_COMMIT.v0-2-0-cycle-1-continuous-watch`.
- **§14 backfill (this plan-doc, post-seal):** add a `## 14.` heading + method-decision register with the apply SHA + seal SHA + post-seal commit SHA per AC.D-sa.7 lint regex (NOT `## §14`).
- **Master plan §9 backfill:** add Cycle 1 row with apply SHA + seal SHA + notes after seal lands (master plan `docs/rebuild/plans/v0-2-0-master-plan.md` §9 SHA backfill table).
- **Roadmap §8 backfill (deferred to v0.2.0 release):** v0.2.0 release-level rollup updates `docs/rebuild/plans/v0-1-x-roadmap.md` §8 + `docs/rebuild/plans/eric-final-delivery-plan-2026-05-04.md` §2 only AFTER Cycle 2 + release-level smoke green per master plan §4 Cycle 2 dispatch.
- **No tag push.** v0.2.0 tag waits on Cycle 2 + release-level SOFT smoke gate (Decision R) + Luke's gate-review.

---

## §13 — Acceptance gate

This plan-doc is gate-ready when:

1. All 10 AC.WATCH.* families named with explicit pytest paths (§4) ✓
2. Single-component fence named (§3) ✓
3. All 6 smoke dimensions addressed — applicable exercised, n/a documented (§7) ✓
4. Halt triggers named (§9) ✓
5. Bookkeeping path named (§12) ✓
6. F2 gaps named (§10) ✓
7. Halt-and-surface BEFORE-build resolutions recorded (§5) ✓ — Surface #1 (scope-of-work cron); Surface #2 (PM batch-type); Surface #3 (orphaned-AC handling)

Build proceeds.

---

## 14. Method-decision record (post-seal backfill)

(Reserved; build agent backfills with apply SHA + seal SHA + post-seal commit SHA per AC.D-sa.7 lint regex. The `## 14.` heading is required by the `loam amend seal` lint, NOT `## §14`.)

| Step | SHA | Notes |
|---|---|---|
| Plan-doc commit (this file) | TBD | docs(plans): v0.2.0 Cycle 1 sub-plan + manifest |
| Source-edit commit (BASELINE) | TBD | feat(dev-sdlc): odd-extractor incremental mode + diff-classifier + proposals + domain-batching + scheduling-CLI + production-stake gate + audit-log (v0.2.0 Cycle 1) |
| Apply commit (manifest+apply merged per AC.DPS1.6) | TBD | chore(amend): v0-2-0-cycle-1-continuous-watch manifest+apply — dev-sdlc BASELINE+sidecar bump |
| Seal commit | TBD | chore(seals): v0-2-0-cycle-1-continuous-watch — dev-sdlc at <baseline> |
| Post-seal SHA-record commit (this §14 backfill + master plan §9) | TBD | docs(plans): record v0-2-0-cycle-1 commit SHAs in method-decision register |
