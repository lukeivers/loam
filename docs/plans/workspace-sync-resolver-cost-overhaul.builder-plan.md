# workspace-sync resolver cost overhaul — builder-plan

**Authored:** 2026-04-26 by build-agent (Bundle α sealed-component
amendment dispatch).
**Companion plan:** `docs/plans/workspace-sync-resolver-cost-overhaul.md`.
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment baseline (BASELINE candidate):** HEAD of canonical at
amendment-commit time. Read at apply-time. Most recent prior
amendment is **#56**; next free amendment number = **57**.

This builder-plan captures (a) the **method choices** (D-build.x)
within each AC's outcome bound, (b) the **§2.5 reverse-direction
trace** (one row per code path / branch → AC), and (c) the
**build sequence** the agent will execute.

---

## Section A — Method choices (D-build.x)

### D-build.0 — Module placement

**Choice.** All α.1 + α.2 logic lives in workspace-sync's existing
package `workspace_sync/`. New module **`merge_primitives.py`**
houses (1) `MergeClassification` + `MergeVerification` Pydantic
models, (2) the file-class enum, (3) per-class deterministic merge
primitives, (4) classify-prompt + verify-prompt builders, (5)
`classify_file()` + `verify_merge()` helpers (each invokes the
LLM client and returns a typed model + token count). Existing
modules `merge_helper.py` (α.1 + α.2 wiring), `merge_resolver.py`
(unchanged shape), `_resolver_client.py` (α.3) are extended in
place.

**Why.** Single new module means a single test file
(`test_merge_primitives.py`) houses all per-class deterministic
primitives + classify/verify shape tests. `merge_helper.py`
remains the orchestration site (pre-resolver ancestor pass, then
classify→deterministic→verify, then fall-back to existing
generator path). `merge_resolver.py` stays unchanged because the
new classify/verify calls are bounded helpers — they do NOT route
through `MergeResolver.resolve()` (that path produces a
`MergeVerdict`); they are independent typed calls.

ODD reverse trace targets: every export of `merge_primitives.py`
ladders to one of AC.WSα.3 / .4 / .5; the `merge_helper.py`
extensions ladder to AC.WSα.1 / .2 / .5 / .6.

### D-build.1 — Ancestor-detection helper placement (α.1)

**Choice.** New module **`ancestor_detection.py`** under
`workspace-sync/src/workspace_sync/`. Exports:
- `walk_ancestors(canonical_path: Path, ref: str, conflict_path: str, target_sha256: str, depth_cap: int) -> AncestorMatch | None` — pure-function git walker with sha256 byte comparison.
- `AncestorMatch` Pydantic model: `commit_sha: str`, `commit_short_sha: str`, `walk_depth: int`, `walk_short: bool`.
- `AncestorCache` Pydantic model + `load_cache()` + `save_cache()` helpers (sibling YAML at `<workspace>/.pos/sync/<ref>/ancestor-cache.yaml`).

The wiring into the merge pipeline lives in `merge_helper.py` —
a new `_try_ancestor_fast_path()` private helper called from
the existing Class-C branch BEFORE the resolver call.

**Why.** Separation of concerns: `ancestor_detection.py` is a
pure git-walk primitive; `merge_helper.py` is the orchestrator;
the cache is workspace-local and reads/writes through helpers
rather than ad-hoc YAML manipulation. Keeps the existing
`conflict_detection.py` untouched (it's the file the dispatch
named as one possible attach point, but `merge_helper.py` is
cleaner because the helper already has access to the
sync-protected envelope, the resolver, the workspace_root,
and the canonical_root).

### D-build.2 — α.1 walk shape

**Choice.** Use `git -C <canonical_path> log --all --follow --format=%H -- <path>` to enumerate every commit on any branch that touched `<path>`, capped at the first `depth_cap` results. For each commit returned, run `git -C <canonical_path> show <commit>:<path>` (capturing bytes), compute sha256, compare to the workspace's `installed_sha256`. First match wins; emit `AncestorMatch(commit_sha=..., walk_depth=<index>)`.

Walk-short detection: when `git log` returns FEWER than `depth_cap` commits AND no match found, emit no match BUT set `walk_short=True` so the audit can record `ancestor_walk_short: true`. Decline to fast-path; the resolver continues per existing logic (D-1 LOCKED).

**Why.** Mirrors the empirical research note's exact shape (97.8% skip rate). `--all --follow` ensures we walk through renames and across branches. Stopping at the first match is correct: any historical match means the workspace content is just behind, not edited.

`depth_cap = 200` per D-1 LOCKED. Sibling cache file path
`<workspace>/.pos/sync/<ref>/ancestor-cache.yaml` per D-1 LOCKED.
sha256-byte comparison per D-1 LOCKED.

### D-build.3 — Cache shape

**Choice.** YAML cache file at `<workspace>/.pos/sync/<ref>/ancestor-cache.yaml`. Pydantic-validated:

```python
class AncestorCacheEntry(BaseModel):
    path: str
    workspace_sha256: str  # the installed_sha256 the cache key matched
    ancestor_sha: str | None  # full SHA on hit; None on miss
    walk_depth: int
    walk_short: bool

class AncestorCache(BaseModel):
    schema_version: int = 1
    canonical_ref_sha: str  # the resolved canonical-HEAD SHA — invalidates on canonical advance
    entries: dict[str, AncestorCacheEntry]  # keyed by f"{path}|{workspace_sha256}"
```

Cache validation on load: if `canonical_ref_sha` differs from the
current canonical-HEAD, return an empty cache (the cache is stale
and any verdicts derived from it could be wrong). The cache is
rewritten at end-of-run with the resolved `canonical_ref_sha` so
re-runs against the same canonical-HEAD hit cache; canonical-HEAD
advance invalidates wholesale.

**Why.** Per D-1 LOCKED: cache key includes the canonical ref's resolved SHA; per-conflict cache entries; cache file rewritten at end-of-run. Schema-version field is forward-compatible defense (future amendments can bump and migrate). Keying on `(path, workspace_sha256)` means a workspace-side edit naturally invalidates the entry without hand-tracking.

### D-build.4 — File-class taxonomy (α.2)

**Choice.** Five-class `Literal` union per AC.WSα.3 minimum:

```python
FileClass = Literal[
    "append-only-list",
    "log",
    "tracker-table",
    "free-prose",
    "unknown",
]
```

(Deliberately distinct from `sync_protected.py::FileClass` which is
A/B/C; the structural-class enum named `MergeClass` to avoid
collision.)

```python
class MergeClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    merge_class: MergeClass  # the Literal above
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str  # brief; bounded by output cap
```

**Why.** AC.WSα.3 names exactly these five at the AT-LEAST level.
No need to add a sixth class; if a future amendment surfaces a new
class (e.g., "cli-args-fixture" or "json-schema"), bump the
Literal then. Keeping the enum tight matches the rubber-stamp-
prevention principle (Hard Constraint #8): fewer classes means the
verifier's "is this actually structurally a {class}?" question has
a clearer rubric.

### D-build.5 — Per-class deterministic primitives (α.2)

**Choice.** Each primitive takes (`canonical_text: str`, `workspace_text: str`) and returns `(merged_text: str, trace: PrimitiveTrace)` where `PrimitiveTrace` records the primitive name + canonical_sha + workspace_sha + merged_sha + a brief operation summary. Pure, deterministic; running twice produces byte-identical output.

Per-class implementations:

1. **`append-only-list`** (markdown bullet lists, also FUTURE_IDEAS_DRAFT-style sections). Algorithm:
   - Split each side on top-level bullet boundaries (lines starting `- `, `* `, or `+ ` at column 0).
   - Compute structural prefix (lines before the first bullet) — must match across both sides; if not, fall through (raise `PrimitiveDeclined`).
   - Concatenate: prefix + canonical bullets + (workspace bullets that DON'T appear in canonical, dedup by stripped first-line). Preserves order: canonical-first, workspace-additions-after.
   - Trailing content (lines after the last bullet) — emit canonical's trailing if both have one (workspace-side trailing is appended deduplicated).

2. **`log`** (ndjson / line-oriented append-only log). Algorithm:
   - Split each side on `\n`.
   - For each line in canonical: keep.
   - For each line in workspace not in canonical (set membership): append to end.
   - No reordering. (Logs are time-ordered; merging by union preserves both sides' entries.)

3. **`tracker-table`** (markdown pipe-tables). Algorithm:
   - Parse header row + separator + body rows from each side.
   - Header rows MUST match (column count + names); if not, raise `PrimitiveDeclined`.
   - Concatenate bodies: canonical rows + (workspace rows not in canonical, dedup by full-row-string).
   - Reassemble header + separator + merged body.

4. **`free-prose`**. Always raises `PrimitiveDeclined` — free-prose has no deterministic merge primitive; the orchestrator falls through to AC.WSα.6 fall-back (existing LLM-generator).

5. **`unknown`**. Always raises `PrimitiveDeclined` — same fall-through.

**`PrimitiveDeclined` exception** carries a `reason` string (e.g.,
"prefix mismatch", "header mismatch") that lands in the audit's
`fallback_reason` field as `primitive-failed: <reason>`.

**Why.** Concatenate-with-dedupe is the simplest correct merge for append-only structures. Markdown lists in pos-v2's actual workspace-sync conflicts are mostly draft-list / log / tracker shapes (matching FUTURE_IDEAS_DRAFT.md, recent-experiments tables, etc.). The structural-prefix check catches "the file looks like a list but the lead-in differs" — falls through cleanly. Idempotency: running twice produces byte-identical output (set membership is order-independent on inputs but we preserve canonical-ordering, so output is stable). Property-test target: `merge(merge(c, w), w) == merge(c, w)`.

### D-build.6 — Classify-call prompt design (α.2 / D-2 LOCKED)

**Choice.** Bounded-input + bounded-output prompt. Inputs:
- File path.
- Canonical first-50-lines + last-10-lines (full file ≤60 lines).
- Workspace first-50-lines + last-10-lines (full file ≤60 lines).

The truncation marker is a literal `... <middle truncated, M lines> ...` line so the LLM sees the structure honestly.

Output schema: `MergeClassification(merge_class, confidence, reasoning)`. Bounded to ≤200 tokens output (rubric: a short `reasoning` field).

Prompt skeleton (keyed to AC.WSα.3 outcome): "You are classifying the structural shape of a file with a workspace-vs-canonical conflict. The file path is `{path}`. Below are bounded views of canonical and workspace... Choose ONE class from `append-only-list`, `log`, `tracker-table`, `free-prose`, `unknown`. Class definitions: ... Return MergeClassification JSON."

**Why.** Per D-2 LOCKED: 50-first + 10-last lines is enough to disambiguate the 5 classes; full file when ≤60 lines. The truncation marker prevents the LLM from inferring "this is exactly N lines" wrongly. Output cap is enforced through prompt instruction + `extra="forbid"` Pydantic validation.

### D-build.7 — Verify-call prompt design (α.2 / Hard Constraint #8)

**Choice.** Inputs (per D-2 LOCKED — full content):
- File path.
- Full canonical text.
- Full workspace text.
- Full candidate-merged text.
- The classifier's named class (NAMED INPUT per Hard Constraint #8).
- The deterministic primitive's trace summary.

Output schema:
```python
class MergeVerification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passed: bool
    class_mismatch: bool  # FIRST verification step per Hard Constraint #8
    concerns: str | None
    confidence: float = Field(ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _class_mismatch_forces_fail(self):
        if self.class_mismatch and self.passed:
            raise ValueError("class_mismatch=True requires passed=False")
        return self
```

Prompt rubric (3-step):
1. **First, structural class check.** "The merge primitive treated this file as `{class}`. Is that actually correct? Look at the WORKSPACE and CANONICAL contents — do they actually have the structure of a `{class}`? If not, set `class_mismatch=true` and `passed=false`."
2. **Second, primitive correctness.** "Given the {class} primitive {primitive_trace.operation}, did the candidate preserve both sides' material content?"
3. **Third, line-level information.** "Did any line-level information from canonical or workspace go missing in the candidate?"

Output bounded to ≤500 tokens (rubric for `concerns`).

**Why.** Hard Constraint #8 bind: rubber-stamp prevention requires the verifier to take the class as a NAMED input AND ask "is this actually structurally a {class}?" as the FIRST check. The model_validator enforces structurally that `class_mismatch=true → passed=false` so the verifier cannot accidentally rubber-stamp by setting both true. The 3-step rubric makes the structural exclusion explicit in the prompt.

### D-build.8 — α.3 MCP-isolation subprocess (D-3 RE-LOCKED)

**Choice.** `_ClaudePrintResolverClient.__init__` writes empty MCP config once at init time to a process-cached path. Every `claude -p` invocation appends `--strict-mcp-config --mcp-config <path>` to argv.

Implementation:
- Use `tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)` once per process, written at init-time, content `{"mcpServers": {}}`. Path stored on `self._empty_mcp_config_path`.
- argv extension: insert `--strict-mcp-config`, `--mcp-config`, `self._empty_mcp_config_path` between the binary path and `-p`. (Order matters: these are positional flag-style; tested locally.)

No env-scrubber changes (D-3 RE-LOCKED preserves OAuth/Claude-Max).
No opt-in config knob (D-3 RE-LOCKED ships always-on).

The path is leaked at process termination; tempfile cleanup
on `__del__` is best-effort and is OK to skip (the file is
small and lives in `/tmp` / `$TMPDIR`).

**Why.** Per D-3 RE-LOCKED: MCP isolation prevents bun-process contention with parent-session MCP servers (telegram, memory-graphiti). Empirically verified 2026-04-27 to work under Claude Max OAuth without `ANTHROPIC_API_KEY`.

### D-build.9 — α.1 / α.2 wiring into `merge_helper.py`

**Choice.** Modify `resolve_inferred_conflicts()` Class-C branch (currently lines ~185-234). New flow:

```
for entry in pending Class-C conflicts:
    # α.1: ancestor fast-path
    match = _try_ancestor_fast_path(entry, canonical_path, workspace_root, ref, depth_cap, cache)
    if match:
        entry.resolution = INFERRED_ACCEPT_CANONICAL
        entry.rationale = f"workspace path matches canonical-history ancestor at {match.short_sha}; not edited"
        entry.confidence = 1.0
        entry.ancestor_match_sha = match.commit_sha
        emit otel pos.sync.merge_gate.ancestor_check (matched=True)
        continue

    emit otel pos.sync.merge_gate.ancestor_check (matched=False, walk_depth, walk_short)

    # α.2: classifier+deterministic+verifier
    canonical_text = read(canonical / entry.path)
    workspace_text = read(workspace_root / entry.path)
    if either is None: deferred += 1; continue

    try:
        classification, classify_tokens = classify_file(client, entry.path, canonical_text, workspace_text)
        emit otel pos.sync.merge_gate.classify (class, tokens)

        if classification.merge_class == "unknown":
            fallback_reason = "classifier-unknown"
            raise FallthroughToGenerator(fallback_reason)

        try:
            merged_text, primitive_trace = run_primitive(classification.merge_class, canonical_text, workspace_text)
        except PrimitiveDeclined as exc:
            fallback_reason = f"primitive-failed: {exc}"
            raise FallthroughToGenerator(fallback_reason)

        verification, verify_tokens = verify_merge(client, entry.path, canonical_text, workspace_text, merged_text, classification, primitive_trace)
        emit otel pos.sync.merge_gate.verify (passed, tokens)

        if not verification.passed:
            fallback_reason = "verifier-rejected"
            raise FallthroughToGenerator(fallback_reason)

        # SUCCESS path — accept the deterministic merge
        entry.resolution = INFERRED_MERGED
        entry.rationale = verification.concerns or f"deterministic {classification.merge_class} merge; verifier passed (confidence {verification.confidence:.2f})"
        entry.confidence = verification.confidence
        entry.classifier_class = classification.merge_class
        entry.deterministic_primitive = primitive_trace.operation
        entry.resolved_content_path = write_merged(entry.path, merged_text)

    except FallthroughToGenerator:
        # Existing LLM-generator path (today's flow), unchanged
        verdict = resolver.resolve(entry.path, canonical_text, workspace_text, prior_text)
        entry.resolution = _verdict_to_resolution(verdict)
        entry.rationale = verdict.rationale
        entry.confidence = verdict.confidence
        entry.fallback_reason = fallback_reason
        # ... existing INFERRED_MERGED merged-content handling ...
```

The `FallthroughToGenerator` is a private control-flow exception (module-private; not part of the public API).

**Why.** Linear flow with explicit fall-back path matches the plan's §8 staging. The `FallthroughToGenerator` exception lets us surface fallback_reason to the audit even when the classify/primitive/verify chain raises mid-flight (each raise is wrapped to set `fallback_reason` first). Existing budget-exhausted / resolver-failure handling in the outer `try/except/finally` continues to apply unchanged.

The classify + verify calls go through the same `_ClaudePrintResolverClient` instance the resolver uses, so they pick up the α.3 MCP-isolation flags transparently. To keep the resolver's `cumulative_used` bookkeeping coherent, the helper increments `resolver._cumulative_used` directly with `classify_tokens + verify_tokens` (test-friendly via accessor).

Actually, to avoid reaching into private state, the cleaner shape is to call `resolver.llm_client.invoke(prompt, response_model)` directly for classify + verify, then the helper tracks classify+verify token totals separately and surfaces them through the audit. The existing per-call budget gate doesn't apply — those calls are bounded-output by design (≤200 tok / ≤500 tok), well below the per-conflict budget. So:

**Refined choice:** classify + verify call `resolver.llm_client.invoke()` directly (the duck-typed `LLMClient` surface). Token totals are aggregated into a new `_extra_tokens_used` counter exposed on the resolver as `resolver.extra_tokens_used`. The audit's run-summary records this alongside `cumulative_used`.

### D-build.10 — Audit-entry extension fields

**Choice.** New optional fields on `ConflictEntry` (extra="forbid" preserved; defaults preserve back-compat):
- `ancestor_match_sha: str | None = None` — full SHA when α.1 matched.
- `classifier_class: str | None = None` — `MergeClass` value when α.2 classifier ran.
- `deterministic_primitive: str | None = None` — primitive operation summary when α.2 primitive ran.
- `fallback_reason: str | None = None` — set on AC.WSα.6 fall-back.

All four are `Optional[str] = None`. Existing entries deserialise unchanged (back-compat preserved).

**Why.** Pydantic forward-compat: `extra="forbid"` rejects unknown fields, but fields with `None` defaults are absent from existing YAML files (no validation breakage). Per AC.WSα.7 the OTel spans carry the same data; the audit extension makes the trail self-contained for local inspection.

### D-build.11 — Test fixtures + property tests

**Choice.** New test files:

1. **`test_ancestor_detection.py`** — α.1 ACs WSα.1 + WSα.2.
   - `test_workspace_matches_ancestor_fast_paths_no_resolver_call`: fixture with workspace = canonical's HEAD~3 blob; asserts resolver NOT invoked, `INFERRED_ACCEPT_CANONICAL` verdict, `ancestor_match_sha` set, no token cost.
   - `test_workspace_genuinely_diverged_declines_to_fast_path`: workspace content matches no historical commit; ancestor walk declines; resolver IS invoked.
   - `test_ancestor_walk_terminates_at_depth_cap`: synthetic deep history (>200 commits); workspace matches a commit BEYOND the cap; walk declines (decline-on-shallow per D-1).
   - `test_ancestor_cache_hit_avoids_re_walk`: first invocation walks; second invocation against unchanged state hits cache (zero `git rev-list` / `git show` subprocess calls — verified via mock).
   - `test_ancestor_cache_invalidates_on_canonical_advance`: cache file present from prior canonical SHA; current canonical SHA differs; cache returns empty.

2. **`test_merge_primitives.py`** — α.2 ACs WSα.3 + WSα.4.
   - `test_classify_*` (5 tests, one per class): bullet list → append-only-list; ndjson → log; pipe-table → tracker-table; prose → free-prose; binary-but-text-ish → unknown.
   - `test_primitive_append_only_list_merges_dedupe`: canonical bullets {a, b}, workspace bullets {a, b, c}; merged = {a, b, c} preserving canonical order.
   - `test_primitive_log_appends_workspace_entries`.
   - `test_primitive_tracker_table_merges_rows`.
   - `test_primitive_idempotent`: property test — `merge(merge(c, w), w) == merge(c, w)` for each non-unknown class.
   - `test_primitive_free_prose_declines`: raises `PrimitiveDeclined`.
   - `test_primitive_unknown_declines`: raises `PrimitiveDeclined`.
   - `test_primitive_prefix_mismatch_declines`: append-only-list prefix differs → `PrimitiveDeclined`.
   - `test_primitive_header_mismatch_declines`: tracker-table headers differ → `PrimitiveDeclined`.
   - `test_verify_class_mismatch_forces_fail`: stub verify response with `class_mismatch=true, passed=true` → ValidationError.

3. **`test_merge_helper.py`** (extends existing) — α.1 + α.2 + α.3 integration:
   - `test_alpha1_ancestor_match_skips_resolver_and_classify`: workspace matches canonical-ancestor; flow short-circuits; classify NOT invoked; resolver NOT invoked.
   - `test_alpha2_classify_pass_primitive_pass_verify_pass_accepts_merge`: stub LLM client queue with classify + verify both OK; primitive merges successfully; verdict is INFERRED_MERGED with `classifier_class` + `deterministic_primitive` populated.
   - `test_alpha2_classifier_unknown_falls_through_to_generator`: classifier returns `unknown`; primitive NOT invoked; LLM-generator IS invoked; `fallback_reason="classifier-unknown"` recorded.
   - `test_alpha2_primitive_decline_falls_through_to_generator`: classifier returns `append-only-list` but primitive raises `PrimitiveDeclined`; LLM-generator IS invoked; `fallback_reason="primitive-failed: ..."` recorded.
   - `test_alpha2_verifier_rejects_falls_through_to_generator`: classifier + primitive succeed; verifier returns `passed=false`; LLM-generator IS invoked; `fallback_reason="verifier-rejected"` recorded.
   - `test_alpha2_otel_spans_emitted`: OTel exporter captures `pos.sync.merge_gate.ancestor_check`, `pos.sync.merge_gate.classify`, `pos.sync.merge_gate.verify` per AC.WSα.7.

4. **`test_resolver_client_mcp_isolation.py`** — α.3 AC.WSα.8.
   - `test_argv_carries_strict_mcp_config_flags`: build `_ClaudePrintResolverClient`; intercept argv via subprocess mock; assert `--strict-mcp-config` + `--mcp-config <path>` present.
   - `test_empty_mcp_config_file_contains_empty_servers`: read the path; assert content equals `{"mcpServers": {}}`.

**Property test count:** 1 (idempotency, parametrised across 3 classes).
**Total new test count:** ~25 (5 ancestor + 12 primitives + 6 helper + 2 client) — within plan §9 estimate (25-35).

### D-build.12 — Backwards-compat verification

**Choice.** Add a fixture `test_alpha_backcompat_falls_through_to_existing_generator_path` that forces ancestor-decline + classifier-`unknown`; asserts the resulting verdict matches #56's pre-amendment LLM-generator output for the same stub input. This satisfies plan §8 step 8.

The 62 existing tests in `workspace-sync/tests/` must remain green
post-amendment. Verified by running the touched-component suite at
each milestone.

### D-build.13 — Method-decision trace (one row per AC) — see Section B

(Each AC traces back to the D-build.x entry above. Built out in §B.)

---

## Section B — §2.5 reverse-direction trace (code path → AC)

| Source (file:symbol) | AC backing |
|---|---|
| `ancestor_detection.py::walk_ancestors` | AC.WSα.1 |
| `ancestor_detection.py::AncestorMatch` | AC.WSα.1 |
| `ancestor_detection.py::AncestorCache` | AC.WSα.2 |
| `ancestor_detection.py::load_cache` | AC.WSα.2 |
| `ancestor_detection.py::save_cache` | AC.WSα.2 |
| `merge_helper.py::_try_ancestor_fast_path` | AC.WSα.1 + AC.WSα.2 |
| `merge_primitives.py::MergeClassification` | AC.WSα.3 |
| `merge_primitives.py::MergeVerification` | AC.WSα.5 |
| `merge_primitives.py::classify_file` | AC.WSα.3 |
| `merge_primitives.py::verify_merge` | AC.WSα.5 |
| `merge_primitives.py::merge_append_only_list` | AC.WSα.4 |
| `merge_primitives.py::merge_log` | AC.WSα.4 |
| `merge_primitives.py::merge_tracker_table` | AC.WSα.4 |
| `merge_primitives.py::run_primitive` | AC.WSα.4 |
| `merge_primitives.py::PrimitiveDeclined` | AC.WSα.6 |
| `merge_primitives.py::PrimitiveTrace` | AC.WSα.4 |
| `merge_helper.py::FallthroughToGenerator` | AC.WSα.6 |
| `merge_helper.py::resolve_inferred_conflicts` (Class-C branch extension) | AC.WSα.1 + .2 + .5 + .6 |
| `merge_helper.py` OTel emissions for ancestor_check / classify / verify | AC.WSα.7 |
| `_resolver_client.py::_ClaudePrintResolverClient.__init__` (empty mcp config write) | AC.WSα.8 |
| `_resolver_client.py::_ClaudePrintResolverClient.invoke` (argv flag injection) | AC.WSα.8 |
| `conflict_report.py::ConflictEntry.ancestor_match_sha` | AC.WSα.1 |
| `conflict_report.py::ConflictEntry.classifier_class` | AC.WSα.3 |
| `conflict_report.py::ConflictEntry.deterministic_primitive` | AC.WSα.4 |
| `conflict_report.py::ConflictEntry.fallback_reason` | AC.WSα.6 |
| `tests/test_no_sealed_amendments.py` (BASELINE bumped to amendment HEAD~1; sidecar advanced to seal SHA) | AC.WSα.S |

Every code path / symbol → at least one AC. Reverse-direction
trace clean per ODD §2.5.

---

## Section C — Build sequence

Order chosen to land the smallest-surface change first (α.3),
then the largest cost-reduction (α.1), then the most complex
chain (α.2). Each phase ends with the touched-component suite
passing.

1. **Phase A — α.3 MCP isolation.**
   1.1 Edit `_resolver_client.py` to write empty MCP config at init + append flags to argv.
   1.2 Add `test_resolver_client_mcp_isolation.py`.
   1.3 Run `workspace-sync/tests/`. Expect 62 baseline + 2 new = 64 green.

2. **Phase B — α.1 ancestor detection.**
   2.1 Author `ancestor_detection.py` (walker + cache + Pydantic models).
   2.2 Add `ancestor_match_sha` field to `ConflictEntry` in `conflict_report.py`.
   2.3 Wire `_try_ancestor_fast_path` into `merge_helper.py::resolve_inferred_conflicts` Class-C branch.
   2.4 Add OTel `pos.sync.merge_gate.ancestor_check` span emission.
   2.5 Add `test_ancestor_detection.py` (5 tests).
   2.6 Run `workspace-sync/tests/`. Expect 64 + 5 = 69 green.

3. **Phase C — α.2 classifier+primitive+verifier.**
   3.1 Author `merge_primitives.py` (models + per-class primitives + classify_file + verify_merge).
   3.2 Add `classifier_class`, `deterministic_primitive`, `fallback_reason` fields to `ConflictEntry`.
   3.3 Extend `merge_helper.py::resolve_inferred_conflicts` Class-C branch with classify→primitive→verify→fallback chain.
   3.4 Add OTel `pos.sync.merge_gate.classify` + `verify` span emissions.
   3.5 Add `test_merge_primitives.py` (12 tests).
   3.6 Add `test_merge_helper.py` extensions (6 tests).
   3.7 Run `workspace-sync/tests/`. Expect 69 + 18 = 87 green.

4. **Phase D — Apply + Seal.**
   4.1 Author manifest at `docs/plans/workspace-sync-resolver-cost-overhaul.manifest.yaml` (next free amendment = 57; baseline = current HEAD pre-amendment-commit).
   4.2 Run `pos-amend apply --dry-run` to validate manifest shape.
   4.3 Stage all changes; create amendment commit `feat(workspace-sync): resolver cost overhaul (Bundle α: ancestor-detection + classifier+verifier + MCP-isolation) (amendment #57, AC.WSα.1–AC.WSα.8 + AC.WSα.S)`.
   4.4 Run `pos-amend apply <manifest>` (real apply — bumps BASELINE + SEAL_COMMIT sidecar to amendment SHA, widens admissions if needed).
   4.5 Inspect changes; if BASELINE/sidecar moved, amend should be a NEW corrective commit. Realistically the BASELINE bump is part of the amendment commit per pattern; verify.
   4.6 Run `pos-amend seal --plan-doc <abs-path>` — sweeps all sealed components, runs touched-component tests, creates seal commit, runs post-seal apply --dry-run, backfills plan-doc §14 SHAs.
   4.7 Verify state: 3 commits (amendment, seal, plan-doc-backfill).

**Speedups applied** (per Luke's amendment-dispatch-speedups directive):
- Per-phase tests narrowed to `workspace-sync/tests/` only; cross-component sweep happens at seal-time (pos-amend seal default behavior).
- Pre-seal full-suite skipped; smoke run via `pos-amend seal` (which runs touched-component tests + cross-component sweep).
- Methodology snippets inlined in commit prose where relevant.

---

## Section D — Halt-trigger surface review (pre-build)

| Trigger | Status |
|---|---|
| #1 (new top-level objective) | does not fire — composition under v1.0 + Gap-3 per §2 |
| #2 (ODD violation in surrounding code) | none observed at #56's seal at HEAD `f6ca2ed` (post-#56 plan-SHA backfill commit). Pre-build sweep clean. |
| #3 (AC cannot be authored outcome-shaped) | not fired — all 8 ACs are outcome-shaped per plan §4 |
| #4 (source edit outside `workspace-sync/`) | not anticipated — all sources within `workspace-sync/`; universal-paths admit only docs/plans |
| #5 (LLM-merge needs surface pos-v2 doesn't have wired) | not fired — composes on existing `_ClaudePrintResolverClient` |
| #6 (verifier rubber-stamp risk cannot be structurally excluded) | mitigated — class as named input + class_mismatch flag + model_validator forcing passed=false |
| #7 (--bare auth path issue) | redirected — D-3 RE-LOCKED uses `--strict-mcp-config --mcp-config <empty>` instead; OAuth path preserved |
| #8 (workspace data loss reproducible) | structural exclusion preserved — fall-back invokes existing generator which preserves AC.WS.12 fail-closed |
| #9 (wall-time exceeds 4-6h projected) | TBD at execution; halt + report partial state if exceeded |
| #10 (sealed-component fence crossed) | not anticipated — strict workspace-sync/ + universal-paths fence |

---

## Section E — Backwards-compat verification

Per Hard Constraint #5 (binding):

1. **`pos-sync` invocation against post-#56 workspaces.** Existing CLI args + state.yaml + audit.yaml shapes unchanged. New optional fields (`ancestor_match_sha`, `classifier_class`, `deterministic_primitive`, `fallback_reason`) are absent from pre-α audit YAMLs and Pydantic accepts them as None on load. ConflictEntry round-trip test (`test_conflict_report_b_shape.py::test_round_trip`) continues to pass.

2. **Pre-α resolver behaviour preserved on fall-through.** Test `test_alpha_backcompat_falls_through_to_existing_generator_path` asserts that classifier-`unknown` + verifier-fail paths invoke `MergeResolver.resolve()` exactly as before. Verdict shape, audit shape, OTel `pos.sync.merge_gate.resolution` + `summary` spans all unchanged.

3. **No new third-party deps.** All new modules use stdlib + Pydantic + PyYAML + OpenTelemetry — all already present.

4. **Class-A protection unchanged.** `merge_helper.py` Class-A branch (lines 148-158) is not touched. Class-A pre-resolution at detection time per `conflict_detection.py` is not touched. New code only extends the Class-C branch.

5. **Fail-closed preserved.** Outer `try/except/finally` block in `resolve_inferred_conflicts` is not restructured; `BudgetExhausted` + `ResolverFailure` propagation paths unchanged. `FallthroughToGenerator` is caught and translated to a generator call within the Class-C loop body, not the outer block.

---

## Section F — Open questions / followups

None pre-build. Plan §11 D-1..D-4 all LOCKED.

If the build surfaces a new question, halt and surface per
plan §10. Anticipated: zero such surfaces given the lock-status.

---

## Section G — Method-decision record (post-build, populated at seal)

(Filled in post-build with actual D-build.x decisions, test breakdown, backwards-compat verification results, commit SHAs.)
