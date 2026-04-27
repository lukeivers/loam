# workspace-sync-ergonomics β.1 — builder-plan

**Authored:** 2026-04-27 by build-agent (β.1 sealed-component amendment dispatch).
**Companion plan:** `docs/rebuild/plans/workspace-sync-ergonomics.md` (§1-§5 + AC.β.1).
**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.
**Pre-amendment baseline (BASELINE candidate):** HEAD of canonical at amendment-commit time. Most recent prior amendment is **#57**; next free amendment number = **#58** (post-#57; amendment-J is out-of-band lettered work that does not consume a numeric slot per the existing `git log --grep` survey). β.1 ships as **#58**.
**Amendment-J note.** `7a7ba04` (HEAD) is `docs(plans): record amendment J commit SHA in method-decision register` — a plan-§14 backfill commit; no SEAL_COMMIT bump for workspace-sync. β.1's BASELINE = `7a7ba04` (HEAD~0 at the moment build agent stages the amendment commit).

This builder-plan captures (a) the **method choices** (D-build.x) within AC.β.1's outcome bound, (b) the **§2.5 reverse-direction trace** (one row per code path / branch → AC), and (c) the **build sequence** the agent will execute.

The companion plan-doc (workspace-sync-ergonomics.md) covers Bundle β at the bundle level (β.1 + β.2 + β.3). Per D-β.4 LOCKED (split into 3 separate amendments), this builder-plan + the manifest land **β.1 only**. β.2 + β.3 follow as separate amendments via same-tree-serialize; their builder-plans + manifests land at their respective dispatch times.

---

## Section A — Method choices (D-build.x)

### D-build.0 — Module placement

**Choice.** Two new modules under `workspace-sync/src/workspace_sync/`:

1. **`sync_config.py`** (NEW, ~120 LOC). Houses (1) the `SyncConfig` Pydantic model (the schema shared between `<workspace>/.pos/sync-config.yaml` and `~/.pos/sync-config.yaml`), (2) `load_sync_config(workspace_root)` resolver returning a merged `SyncConfig` (workspace-local > ~/-rooted > defaults), (3) the file-lookup helpers (`workspace_sync_config_path`, `user_sync_config_path`), (4) URL-vs-local-path discrimination (`canonical_source_kind`).

2. **`canonical_cache.py`** (NEW, ~90 LOC). Houses (1) `derive_repo_id(url)` for the `~/.pos/canonical-cache/<repo-id>/` directory key, (2) `ensure_cache_clone(url, ref) -> Path` that clones-if-absent + always-`git fetch` + returns the cache directory (a git working tree, ready for `resolve_canonical`).

**Why split into two modules?** Single-responsibility. `sync_config.py` is "schema + load + precedence chain"; `canonical_cache.py` is "URL-form clone-and-fetch". `cli.py` orchestrates: it pulls the resolved `canonical_source` string from `load_sync_config`, asks `canonical_source_kind` whether it's URL or local, calls `ensure_cache_clone` for URL form, and hands the resulting `Path` to the existing `resolve_canonical()`. Each module is independently testable.

**Why not extend `sync_protected.py`?** `sync_protected.py` is the three-class envelope (Class A/B/C protection). `sync_config.yaml` is operator preferences (canonical source, future budget tunables). Hard Constraint #8 in the plan-doc: "config layer, not state layer." Mixing them would dilute the clean separation #56 established.

ODD reverse trace targets: every export of `sync_config.py` ladders to AC.β.1 (the Pydantic schema, the precedence chain, the URL discrimination). Every export of `canonical_cache.py` ladders to AC.β.1 (the `~/.pos/canonical-cache/<repo-id>/` shape per D-β.1 LOCKED).

### D-build.1 — Schema field names + precedence

**Choice.** `SyncConfig` Pydantic model:

```python
class SyncConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")  # mirrors #56 sync_protected.py
    canonical_source: str | None = None  # NEW for β.1; URL or absolute path
    cumulative_token_budget: int | None = None  # placeholder for #57's docstring promise
    per_conflict_token_budget: int | None = None  # placeholder for #57's docstring promise
```

The two `*_token_budget` fields are added per **HALT-FOUND #2** in the plan-doc: `_resolver_client.py:292` docstring promises *"workspace-tunable via `~/.pos/sync-config.yaml`"*. β.1 lands the schema fields so the docstring becomes accurate. β.1 does NOT rewire the resolver-budget consumer paths (`_load_merge_resolver` already accepts a `--budget-tokens` CLI flag). Subsequent amendments can wire budget overrides through the precedence chain. β.1's job is to make the file shape exist + load-validate-and-pass-through; the budget-application semantics already exist via the `--budget-tokens` flag and `ResolverBudget` model.

**Why include the budget fields in β.1's schema even though the wiring is partial?**
- The `_resolver_client.py:292` docstring is a literal promise the schema makes good on. Tightening the docstring without landing the fields would shift the promise (it would say "via `~/.pos/sync-config.yaml`'s `canonical_source` only", which is not what the docstring says).
- The CLI flag `--budget-tokens` is a CLI-level override; the file is a workspace-default. Both layers will exist post-β.1; the CLI-override-vs-file-default precedence is the same precedence canonical_source uses.
- Wiring the budget defaults through `_load_merge_resolver` is a one-line change: pass `cumulative_token_budget=cfg.cumulative_token_budget` to `ResolverBudget()` when the CLI didn't override. This extends naturally; β.1 includes the wiring (it's so small the alternative — leaving budgets file-loadable but ignored — would be ODD-loose).

**Precedence chain** (resolved in `cli.py`):

1. CLI flag (`--canonical <p>`, `--budget-tokens N`) — highest priority.
2. `<workspace>/.pos/sync-config.yaml` — workspace-local.
3. `~/.pos/sync-config.yaml` — user-rooted.
4. Schema defaults (None for all fields; no canonical_source means halt-with-error if no CLI flag).

The merge is field-by-field: workspace-local field wins if set, else ~/-rooted field if set, else default. `load_sync_config(workspace_root)` returns a single merged `SyncConfig` instance.

### D-build.2 — URL-vs-local-path discrimination

**Choice.** Pure-string predicate `canonical_source_kind(source: str) -> Literal["url", "local"]` (raises `ValueError` for ambiguous shapes per D-β.1 LOCKED).

Discrimination rules (per D-β.1 LOCKED):
- Starts with `http://`, `https://`, or `git@` → `"url"`.
- Starts with `/` (absolute POSIX path) → `"local"`.
- Anything else → `ValueError("canonical_source must be an http(s) URL, a git@ SSH spec, or an absolute path")`.

**Why pure-string and not URL parsing?** Hard Constraint #3 (no new third-party deps). Pythons `urllib.parse` exists in stdlib but URL parsing for git-SSH `git@github.com:user/repo.git` requires custom logic anyway. A 3-line predicate handles the locked shapes cleanly.

**Why halt-and-surface on `file://` / `ssh://` / relative paths?** Per dispatch + plan-doc D-β.1 LOCKED: "Anything else is a halt." `file://` URLs (which `git clone` supports) and `ssh://` URLs (alternative to `git@`) are ambiguous shapes — a user *could* paste them but the locked spec narrows the surface. β.1 declines those shapes; future amendments can widen. The error message names the three accepted forms.

### D-build.3 — `~/.pos/canonical-cache/<repo-id>/` shape

**Choice.** `derive_repo_id(url: str) -> str` produces a sanitized `host/owner/repo` slug. Examples:
- `https://github.com/lukeivers/pos-v2` → `github.com/lukeivers/pos-v2`
- `https://github.com/lukeivers/pos-v2.git` → `github.com/lukeivers/pos-v2` (strips `.git` suffix)
- `git@github.com:lukeivers/pos-v2.git` → `github.com/lukeivers/pos-v2`
- `https://gitlab.example.com/owner/repo` → `gitlab.example.com/owner/repo`

Derivation algorithm:
1. Strip leading `https://` / `http://` / `git@`.
2. Replace `:` (in `git@host:owner/repo`) with `/`.
3. Strip trailing `.git`.
4. Result is `host/owner/repo` (forward slashes; safe as a path component on POSIX).

`ensure_cache_clone(url: str, ref: str = "HEAD") -> Path`:
1. Compute `cache_dir = Path.home() / ".pos" / "canonical-cache" / derive_repo_id(url)`.
2. If `cache_dir` does not exist: `git clone <url> <cache_dir>` (mkdir parents idempotently; clone target is the leaf).
3. Always run `git -C <cache_dir> fetch --all --tags` (per D-β.1 LOCKED always-fetch).
4. Return `cache_dir`.

The returned `Path` is a git working tree; the existing `resolve_canonical(<cache_dir>, ref=ref)` handles SHA resolution.

**Why `git clone` and not `git fetch` into a bare repo?** `resolve_canonical` expects a working tree (it reads `.git/`). A bare repo would force `resolve_canonical` to grow a code path. β.1 keeps `resolve_canonical` untouched (Hard Constraint #1: no regression); the cache is a normal working tree on the operator's disk. Disk cost is small (pos-v2 is ~15 MB).

**Why `--all --tags`?** D-β.1 LOCKED says always-fetch; the natural fetch shape is "all refs and tags" so that any `--ref` the user passed (HEAD, branch, tag, SHA) resolves cleanly.

### D-build.4 — `cli.py` integration

**Choice.** `--canonical` becomes optional (`required=False`); `args.canonical` resolution moves into `main()` before `resolve_canonical` is called. New flow:

```python
def main(argv):
    args = parser.parse_args(argv)
    workspace_root = derive_workspace_root(workspace_arg=args.workspace)

    # NEW: load config + resolve canonical_source
    cfg = load_sync_config(workspace_root)
    canonical_source_str = (
        str(args.canonical) if args.canonical is not None
        else cfg.canonical_source
    )
    if canonical_source_str is None:
        parser.error(
            "no canonical source: pass --canonical <path> OR set "
            "canonical_source: in <workspace>/.pos/sync-config.yaml or "
            "~/.pos/sync-config.yaml"
        )

    # NEW: URL-vs-local-path discrimination + cache-clone
    kind = canonical_source_kind(canonical_source_str)
    if kind == "url":
        canonical_path = ensure_cache_clone(canonical_source_str, args.ref)
    else:  # "local"
        canonical_path = Path(canonical_source_str)

    # ...rest of the existing flow, with canonical_path replacing args.canonical
```

**Backward-compat (HC#1) verification.** When `--canonical <p>` IS passed and no `<workspace>/.pos/sync-config.yaml` exists:
- `cfg.canonical_source` is `None` (~/-rooted file likely absent too).
- `canonical_source_str = str(args.canonical)` per the conditional.
- `canonical_source_kind` discriminates: a path passed as `--canonical /Users/.../ivers-corp-pos-v2` is absolute → `"local"` → `canonical_path = Path(...)`.
- `resolve_canonical(canonical_path, ref=args.ref)` runs with the same input as today.
- Byte-identical exit code, audit shape, state.yaml shape — verified by fixture-4 (workspace WITHOUT the file + `--canonical <p>` runs).

The CLI flag's `type=Path` becomes `type=str` (because `args.canonical` may now feed `canonical_source_kind` which expects a string). The end-result `Path(canonical_source_str)` is the same object the previous code produced. **String-vs-Path coercion is the only argparse-shape change**; back-compat is preserved (operators pass strings on CLIs anyway).

Resolver budget wiring:
```python
budget_override = None
if args.budget_tokens is not None:
    budget_override = ResolverBudget(cumulative_token_budget=args.budget_tokens)
elif cfg.cumulative_token_budget is not None or cfg.per_conflict_token_budget is not None:
    budget_override = ResolverBudget(
        cumulative_token_budget=cfg.cumulative_token_budget or 100_000,
        per_conflict_token_budget=cfg.per_conflict_token_budget or 5_000,
    )
```

**Why fall back to the model defaults when only one of the two budget fields is set in the config?** The Pydantic model `ResolverBudget` declares both as required-with-defaults. If the operator only sets `cumulative_token_budget` in the file, the per-conflict budget gets the model's default (5_000). Operator gets exactly the override they wrote.

### D-build.5 — `_resolver_client.py:292` docstring tightening

**Choice.** Tighten the docstring to match the now-wired reality:

```python
# OLD (line ~292):
"""... workspace-tunable via ``~/.pos/sync-config.yaml`` (locked plan §11 D-2)."""

# NEW:
"""... workspace-tunable via ``<workspace>/.pos/sync-config.yaml`` or ``~/.pos/sync-config.yaml``
(locked plan §11 D-2; β.1 wires the precedence chain via ``cli.py``)."""
```

The factory body is unchanged: it still receives `budget=` from `_load_merge_resolver`. The wiring lives in `cli.py` (D-build.4). The docstring now accurately names both files and the canonical wiring point.

**Why touch this in β.1?** The dispatch's HALT-FOUND #2 lists this as in-scope. β.1's commit explicitly closes the docstring promise. Per `feedback_loose_AC_text_fix_AC_not_implementation`, a docstring promise unbacked by source is a documentation-truth bug; fixing the source fixes the docstring.

### D-build.6 — Test breakdown

**Choice.** One new test file `workspace-sync/tests/test_sync_config.py` covering AC.β.1 fixture-1 through fixture-6, plus extensions to `test_cli_b_shape.py` for the CLI-flow integration.

`test_sync_config.py` (new, ~10-12 tests):
1. **fixture-1:** workspace WITH `canonical_source: <local-path>` → `pos-sync` no-args succeeds (resolves to local path).
2. **fixture-2:** workspace WITH `canonical_source: <git-url>` → `ensure_cache_clone` invoked with the URL; sync runs against cache. Mocked `git clone` + `git fetch` to avoid network.
3. **fixture-3:** workspace WITHOUT the file → `pos-sync` no-args halts with structured error naming both fall-through conditions.
4. **fixture-4:** workspace WITHOUT the file + `--canonical <p>` → byte-identical to today (compare exit code + state.yaml + audit.yaml shape against #56's fixture).
5. **fixture-5:** CLI flag `--canonical <p2>` overrides config file's `canonical_source: <p1>` → resolver runs against `<p2>`.
6. **fixture-6:** workspace-local file overrides ~/-rooted file → workspace-local `canonical_source` wins.
7. **schema-strictness:** unknown field in sync-config.yaml raises Pydantic `ExtraFieldError` (mirrors #56's `extra="forbid"` pattern).
8. **discrimination-url:** `canonical_source_kind("https://github.com/.../repo")` → `"url"`.
9. **discrimination-git-ssh:** `canonical_source_kind("git@github.com:owner/repo.git")` → `"url"`.
10. **discrimination-local:** `canonical_source_kind("/abs/path")` → `"local"`.
11. **discrimination-relative-halts:** `canonical_source_kind("relative/path")` → `ValueError`.
12. **discrimination-unsupported-scheme:** `canonical_source_kind("file:///path")` → `ValueError` (D-β.1 LOCKED narrowing).
13. **derive_repo_id-https:** `derive_repo_id("https://github.com/owner/repo")` → `"github.com/owner/repo"`.
14. **derive_repo_id-git-ssh:** `derive_repo_id("git@github.com:owner/repo.git")` → `"github.com/owner/repo"`.
15. **derive_repo_id-suffix-strip:** `.git` suffix stripped consistently.

Plus extensions to `test_cli_b_shape.py` (~3 tests) verifying:
- CLI integration: `pos-sync` no-args from a workspace WITH a config file → flow proceeds with the loaded canonical.
- CLI integration: `--canonical <p>` overrides cleanly.
- CLI integration: backward-compat fixture (the existing flow without a config file).

Test counts:
- `test_sync_config.py`: ~12-15 tests
- `test_cli_b_shape.py` extensions: ~3 tests
- **Total new: ~15-18 tests.**

Test isolation: every test uses `tmp_path` for both workspace + cache; tests stub `subprocess.run` for git operations (consistent with #56 + #57 conftest pattern); no test touches the operator's real `~/.pos/`.

### D-build.7 — Pos-amend manifest shape

**Choice.** Schema v1 manifest (no objectives block; mirrors #57's manifest pattern). One sealed component touched: workspace-sync. Universal-paths admissions for `docs/rebuild/plans/` + the four CLAUDE.md / odd-* / FUTURE_IDEAS.md files (mirrors #57). Narrative target: `workspace-sync/seals/SEAL_COMMIT.ergonomics-beta1`.

**BASELINE selection.** Per the dispatch + #57 precedent, BASELINE = HEAD~1 of the amendment commit. Build agent stages the amendment commit (which lands plan-doc + builder-plan + manifest + source + tests), records the parent SHA, writes it as `baseline:` in the manifest, then `pos-amend apply` runs.

Workflow at apply time:
- Build agent makes one feat commit covering plan + builder-plan + manifest + source + tests (mirrors #57's `f6a1cfd`).
- BASELINE = the commit immediately before the feat commit (= current HEAD when the agent starts staging).
- The manifest is committed AS PART OF the feat commit; the BASELINE SHA in the manifest is the parent of the feat commit (read at staging time as `git rev-parse HEAD`).
- `pos-amend apply` runs against the now-committed feat: bumps `tests/SEAL_COMMIT` to the feat-commit SHA, advances `BASELINE = "<feat-parent-SHA>"` literal in `test_no_sealed_amendments.py` (mirrors #57's `afcbc7a` shape).
- `pos-amend seal --plan-doc <abs-path-to-plan-doc>` runs: writes seal narrative to `workspace-sync/seals/SEAL_COMMIT.ergonomics-beta1`, backfills plan-doc §14 with commit SHAs, lands the seal commit (mirrors #57's `e619b6a`).

### D-build.8 — Speedup deltas applied

Per Luke's amendment-dispatch-speedups directive:

- **(a) Narrow seal-test rerun to workspace-sync subset.** Build agent runs `pytest workspace-sync/tests/` (not the full repo) for green-bar gating. Cross-component sweep happens at `pos-amend seal` time only (the seal-test re-runs against the post-seal commit).
- **(b) Skip pre-seal full-suite if smoke tests on workspace-sync subset pass.** Build agent runs the full workspace-sync suite (62 + ~25 from #57 + ~15-18 new = ~100 tests). If green, no full-repo sweep before seal. The test `test_no_sealed_amendments.py` enforces the no-cross-component-leak invariant at seal time.
- **(c) Inline methodology snippets in commit prose.** The amendment-commit message inlines the three relevant methodology snippets (D-β.1 LOCKED quote, D-β.4 LOCKED split-into-3 quote, HALT-FOUND #2 docstring quote) instead of cross-referencing CLAUDE.md / plan-doc only.

---

## Section B — Reverse-direction trace (every code path → AC)

| Code path / branch | AC | Note |
|---|---|---|
| `SyncConfig.canonical_source: str \| None` field | AC.β.1 | The schema slot the precedence chain populates |
| `SyncConfig.cumulative_token_budget: int \| None` | AC.β.1 (HALT-FOUND #2 closure) | Honors the `_resolver_client.py:292` docstring promise |
| `SyncConfig.per_conflict_token_budget: int \| None` | AC.β.1 (HALT-FOUND #2 closure) | Honors the docstring promise |
| `SyncConfig.model_config = ConfigDict(extra="forbid")` | AC.β.1 (schema-strictness fixture) | Mirrors #56's pattern; rejects unknown fields |
| `load_sync_config(workspace_root)` | AC.β.1 | The precedence chain's load entry-point |
| `workspace_sync_config_path(workspace_root)` | AC.β.1 | Returns `<workspace>/.pos/sync-config.yaml` |
| `user_sync_config_path()` | AC.β.1 | Returns `~/.pos/sync-config.yaml` |
| `_load_one_yaml(path)` (internal) | AC.β.1 | Fail-closed on YAML parse error |
| `canonical_source_kind(source)` URL branch | AC.β.1 (fixture-2 + discrimination-url + discrimination-git-ssh) | http/https/git@ → "url" |
| `canonical_source_kind(source)` local branch | AC.β.1 (fixture-1 + discrimination-local) | absolute POSIX → "local" |
| `canonical_source_kind(source)` halt branch | AC.β.1 (discrimination-relative-halts + discrimination-unsupported-scheme) | relative + file://+ssh:// → ValueError |
| `derive_repo_id(url)` https branch | AC.β.1 (derive_repo_id-https) | https://host/owner/repo → host/owner/repo |
| `derive_repo_id(url)` git@ branch | AC.β.1 (derive_repo_id-git-ssh) | git@host:owner/repo → host/owner/repo |
| `derive_repo_id(url)` `.git` strip | AC.β.1 (derive_repo_id-suffix-strip) | trailing `.git` removed |
| `ensure_cache_clone(url, ref)` clone branch | AC.β.1 (fixture-2) | `git clone` when cache absent |
| `ensure_cache_clone(url, ref)` fetch branch | AC.β.1 (fixture-2; always-fetch per D-β.1 LOCKED) | `git fetch --all --tags` on every invocation |
| `cli.py:main` config-load | AC.β.1 | Resolves `canonical_source_str` from CLI > workspace-local > ~/-rooted |
| `cli.py:main` halt-on-no-source | AC.β.1 (fixture-3) | parser.error structured message |
| `cli.py:main` URL form `ensure_cache_clone` invocation | AC.β.1 (fixture-2) | URL → cache_dir |
| `cli.py:main` local form `Path(...)` cast | AC.β.1 (fixture-1 + fixture-4) | local → Path; backward-compat preserved |
| `cli.py:main` budget-override file fallback | AC.β.1 (HALT-FOUND #2 closure) | File budgets honored when CLI didn't override |
| `cli.py:build_parser` `--canonical required=False` | AC.β.1 (HC#1 backward-compat) | Optional flag; no-args path unblocked |
| `cli.py:build_parser` `--canonical type=str` | AC.β.1 (string-vs-Path coercion) | String required for canonical_source_kind |
| `_resolver_client.py:292` docstring tightening | AC.β.1 (HALT-FOUND #2) | Now accurate after wiring lands |
| Test: fixture-1 (workspace + local-path config) | AC.β.1 fixture-1 | |
| Test: fixture-2 (workspace + URL config) | AC.β.1 fixture-2 | |
| Test: fixture-3 (no file, no flag → halt) | AC.β.1 fixture-3 | |
| Test: fixture-4 (no file + flag = today's behaviour) | AC.β.1 fixture-4 (HC#1) | |
| Test: fixture-5 (CLI overrides config) | AC.β.1 fixture-5 | |
| Test: fixture-6 (workspace-local overrides ~/-rooted) | AC.β.1 fixture-6 | |
| Test: schema-strictness | AC.β.1 (Pydantic invariant) | |
| Test: 4 discrimination tests | AC.β.1 (D-build.2) | |
| Test: 3 derive_repo_id tests | AC.β.1 (D-build.3) | |
| Test: cli integration (no-args from configured workspace) | AC.β.1 fixture-1 (cli-shape) | |
| Test: cli integration (--canonical override) | AC.β.1 fixture-5 (cli-shape) | |
| Test: cli integration (backward-compat) | AC.β.1 fixture-4 (HC#1, cli-shape) | |

Forward-direction match (§5 of plan-doc): 1 declared behaviour for AC.β.1, 1 outcome AC. β.1's declared behaviour is "Workspace canonical-source config; pos-sync no-args from inside a workspace." Match.

Implicit-untested code: zero. Every branch above has a test row.

---

## Section C — Build sequence

**Estimated wall-time:** 2.5-3.5h (within the 4-6h halt budget per plan §10 trigger 8).

1. **Author the schema module** (`workspace_sync/sync_config.py`). Pydantic `SyncConfig` + `load_sync_config` + path helpers + `canonical_source_kind`. ~30 min.

2. **Author the cache module** (`workspace_sync/canonical_cache.py`). `derive_repo_id` + `ensure_cache_clone`. ~20 min.

3. **Wire `cli.py`**. Make `--canonical` optional, route through `load_sync_config` + discrimination + cache-clone. ~25 min.

4. **Tighten `_resolver_client.py:292` docstring**. ~5 min.

5. **Author tests** (`test_sync_config.py` + `test_cli_b_shape.py` extensions). ~60 min.

6. **Run `pytest workspace-sync/tests/`** (per speedup-a + speedup-b). Iterate until green. ~15-30 min.

7. **Author manifest** (`docs/rebuild/plans/workspace-sync-ergonomics-beta1.manifest.yaml`). ~10 min.

8. **Stage feat commit** with plan-doc + plan-vars + builder-plan + manifest + source + tests. Commit message inlines methodology snippets (per speedup-c). ~10 min.

9. **`pos-amend apply`** against the feat commit. Bumps `tests/SEAL_COMMIT` + `BASELINE` literal. ~2 min.

10. **`pos-amend seal --plan-doc <ABSOLUTE-PATH-to-plan-doc>`** with the absolute path. Writes seal narrative + plan-doc §14 backfill + lands seal commit. ~2 min.

11. **Backfill plan-doc §14** with method-decision register + commit SHAs (D-build.0 through D-build.8 + amendment-commit SHA + seal-commit SHA + plan-SHA backfill SHA). ~10 min.

12. **Final report** to dispatcher (this document's parent context).

---

## Section D — Backwards-compatibility verification (per HC#1, binding)

The following verification steps execute as part of step 6 (pytest) and step 9 (post-apply seal-test):

1. **`pos-sync --canonical <p> --workspace <p>`** invocation against a workspace WITHOUT `<workspace>/.pos/sync-config.yaml` runs to completion (fixture-4). Exit code identical to today (the existing flow is reachable; the only argparse-shape change is `--canonical type=str` instead of `type=Path`, but the `Path(canonical_source_str)` cast in main produces the same Path object).

2. **State.yaml shape unchanged.** β.1 does not touch `state.py`, `_audit.py`, `staging.py`, `conflict_detection.py`, `merge_helper.py`, or any of the resolver internals. Existing audit YAML on disk continues to deserialise (no field additions; the new sync-config.yaml is a separate file).

3. **Audit YAML shape unchanged.** Same as state.yaml.

4. **Existing fixtures green.** `test_cli_b_shape.py` existing tests (~8) + `test_canonical.py` (~5) + `test_state.py` (~5) + the rest (~50 from #56 + ~25 from #57) MUST remain green at the amendment commit.

5. **No new third-party deps** (HC#3). β.1 uses Pydantic + PyYAML + stdlib `pathlib` + `subprocess` (already deps of workspace-sync).

6. **No edits to sealed `self-upgrade/`** (HC#2). β.1 is purely additive to `workspace-sync/`.

7. **Schema additivity** (HC#4). The new `sync-config.yaml` schema reuses existing fields (budgets) + adds one new field (`canonical_source`). Pre-β.1 sync-config.yaml files (only `~/-rooted` for budgets, per the docstring promise) continue to validate post-β.1 (the new `canonical_source` field is `str | None = None`).

8. **`extra="forbid"`** is preserved from #56's pattern — unknown fields raise; this is intentional schema-strictness and is not a back-compat regression because no pre-β.1 sync-config.yaml file exists in source (the docstring at line 292 referenced the file but no source ever wrote one).

---

## Section E — Halt-trigger surface review (pre-build)

Per plan-doc §10 (cross-referenced):

- **#1 (new top-level objective):** Will not fire. β.1 composes under VALUE_PROPOSITION's AC.PO.1 + AC.PO.2 (translation-burden absorption: no `--canonical` to type; toolkit primitive: workspace-local sync-config.yaml).
- **#2 (ODD violation in surrounding code):** β.1's pre-build sweep covers `cli.py`, `_resolver_client.py:292`, `sync_protected.py`. The docstring promise at `_resolver_client.py:292` IS the ODD-loose finding (HALT-FOUND #2); β.1 closes it in scope. No other ODD violations observed.
- **#3 (AC method-coupled):** AC.β.1 is outcome-shaped. The §11 LOCKED rulings are outcome-shape (URL/path/cache/fetch policy); D-build.0 through D-build.7 are method-shape inside the AC's outcome bound.
- **#4 (β.2 attempts to edit sealed self-upgrade/cli.py):** N/A — β.1 does NOT touch `self-upgrade/`.
- **#5 (new runtime dependency):** Will not fire. Pydantic + PyYAML + stdlib only.
- **#6 (β.2 chicken-and-egg):** N/A — this is β.1.
- **#7 (scope drift to β.4 PP):** Will not fire — β.4 is `--auto-accept` confidence-floor calibration; β.1 does not touch the auto-accept path.
- **#8 (wall-time):** Estimated 2.5-3.5h; budget 4-6h; comfortable.
- **#9 (host-OS-specific failure):** N/A — β.1 is pure Python file I/O + git subprocess; no platform-gated path.
- **Dispatch-named halts** (URL discrimination edge cases, cache-clone security, docstring hidden coupling): URL discrimination edges captured in D-β.1 LOCKED narrowing (only http(s)/git@/absolute; everything else halts at β.1's surface, not silently extends). Cache-clone trust model: β.1 trusts `canonical_source` as the operator set it; future amendments may add fingerprint pinning. Docstring hidden coupling: D-build.5 closes the literal docstring claim.

---

## Section F — Files this amendment touches

| Path | Change | LOC delta |
|---|---|---|
| `workspace-sync/src/workspace_sync/sync_config.py` | NEW | ~120 |
| `workspace-sync/src/workspace_sync/canonical_cache.py` | NEW | ~90 |
| `workspace-sync/src/workspace_sync/cli.py` | EXTEND | ~+25 / -5 |
| `workspace-sync/src/workspace_sync/_resolver_client.py` | EXTEND (docstring only) | ~+2 / -1 |
| `workspace-sync/tests/test_sync_config.py` | NEW | ~250 |
| `workspace-sync/tests/test_cli_b_shape.py` | EXTEND | ~+80 |
| `workspace-sync/tests/test_no_sealed_amendments.py` | apply-time `BASELINE = "<sha>"` bump | 1-line |
| `workspace-sync/tests/SEAL_COMMIT` | apply-time write | 1 SHA |
| `workspace-sync/seals/SEAL_COMMIT.ergonomics-beta1` | seal-time NEW | ~70 lines (narrative) |
| `docs/rebuild/plans/workspace-sync-ergonomics.md` | EXTEND (§14 backfill at seal time) | ~+30 |
| `docs/rebuild/plans/workspace-sync-ergonomics.vars.yaml` | unchanged (already authored) | 0 |
| `docs/rebuild/plans/workspace-sync-ergonomics-beta1.builder-plan.md` | NEW (this file) | this file |
| `docs/rebuild/plans/workspace-sync-ergonomics-beta1.manifest.yaml` | NEW | ~150 lines |

Net: 2 new source modules, 1 new test file, modest extensions to 2 existing source files + 1 existing test file, full bookkeeping (manifest + builder-plan + seal narrative + plan-§14 backfill) per #57 precedent.

---

## Section G — Method-decision record (post-build)

(populated post-build with D-build.0 through D-build.8 final realized values; commit SHAs auto-filled by `pos-amend seal`.)

**Commit SHAs.**
- Amendment commit (feat): `<TBD>`
- pos-amend apply commit: `<TBD>`
- pos-amend seal commit: `<TBD>`
- Plan-§14 backfill commit: `<TBD>`

**Speedup deltas vs baseline (estimated 4-6h):**
- (TBD post-build)

---

## Section H — References

- Plan-doc: `docs/rebuild/plans/workspace-sync-ergonomics.md`
- Plan-vars: `docs/rebuild/plans/workspace-sync-ergonomics.vars.yaml`
- Manifest (this amendment): `docs/rebuild/plans/workspace-sync-ergonomics-beta1.manifest.yaml`
- #56 precedent: `docs/rebuild/plans/workspace-sync.md` + `.builder-plan.md` + `.manifest.yaml`
- #57 precedent: `docs/rebuild/plans/workspace-sync-resolver-cost-overhaul.md` + `.builder-plan.md` + `.manifest.yaml`
- VALUE_PROPOSITION (binding spec): `docs/rebuild/VALUE_PROPOSITION.md`
- Source attach point: `workspace-sync/src/workspace_sync/cli.py`
- HALT-FOUND #2 site: `workspace-sync/src/workspace_sync/_resolver_client.py:292`
- pos-amend tool: `tools/pos-amend/`
