# Builder-plan — Amendment #34 (memory-system eager lifespan / D1 conformance)

Author: build-agent. Authored 2026-04-25, before any source edit, per the
plan-before-code CDC. The owner-authored plan at
`docs/rebuild/plans/amendment-34-memory-system-eager-lifespan-d1-conformance.md`
is the spec; this doc records the method choices the builder makes for
D4 (test shape) and D5 (eager-init shape), the file-and-symbol surface,
and the commit ordering.

## 1. Method decisions

### D4 — test shape

**Choice:** subprocess-spawn + plain HTTP GET, structurally identical to
AC29.4's pattern. Subprocess script swaps `service.make_graphiti` and
`service.load_env` for fakes (no Ollama / Kuzu / Claude), calls
`service.run()`, and the parent test polls `127.0.0.1:<port>/health`
over plain HTTP.

**Rationale:** the plan §3 D4 explicitly recommends this shape, AC29.4
already establishes the subprocess-bind-only pattern in this component
(no new framework introduced), and the outcome under test ("/health
returns 200 within 5s without an MCP session opened") is exactly what a
plain HTTP GET measures. Unit-testing the eager-init coroutine in
isolation would test method, not outcome — rejected per ODD §8.2.10.

### D5 — eager-init shape

**Choice:** option (1) — pre-build before serve. Modify `run()` to call
an idempotent `_ensure_graphiti()` coroutine before
`mcp.run_streamable_http_async()`. Make the existing `lifespan` body
idempotent so the per-MCP-session enter is a no-op when `_graphiti` is
already populated; close-on-exit semantics preserve.

**Rationale:**

- Modern Starlette's `Router` exposes no post-hoc `add_event_handler` /
  `on_startup` (verified empirically — `app.router.on_startup` raises
  `AttributeError` on the FastMCP-returned Starlette app). Option (2)
  would require either (a) wrapping the FastMCP-returned Starlette app
  with a fresh lifespan that composes both, or (b) monkeypatching
  internals. Both are more surface than option (1).
- Option (1) is a one-coroutine + one-`run()`-edit change. The
  idempotency guard (`if _graphiti is None`) matches the existing
  `_require_graphiti()` pattern at service.py line 61.
- The per-session lifespan path (FastMCP → MCPServer.run) keeps working
  unchanged — the lifespan body just observes `_graphiti` already
  populated and skips rebuild on entry. The shutdown half (close on
  context exit) still runs per-session-exit; that matches pre-#34
  behaviour and is harmless because `close()` on an
  already-closed Graphiti would only error if `make_graphiti` lacks
  re-entrant close support, which the existing AC24.1 test does not
  exercise either.
- Builder confirms during implementation that `make_graphiti` has no
  hidden coupling to MCP-session ordering — already audited in plan
  §R5.

## 2. Files + symbols touched

### `memory-system/src/service.py`

- New module-level coroutine `_ensure_graphiti()` — idempotent
  construct of `_graphiti`. Body equivalent to the lifespan's
  construct half (`load_env`, `make_graphiti`, `build_indices_and_constraints`),
  guarded by `if _graphiti is not None: return`.
- Existing `lifespan` body — reshape to delegate construction to
  `_ensure_graphiti()` (so per-session enters observe the
  already-populated `_graphiti` and skip rebuild). The yield/finally
  shape preserves; only the construct half delegates.
- Existing `run()` — call `asyncio.run(...)` on a single coroutine
  that awaits `_ensure_graphiti()` then `mcp.run_streamable_http_async()`.
  Replaces the prior shape that called `load_env()` synchronously then
  `asyncio.run(mcp.run_streamable_http_async())`.

### `memory-system/tests/test_AC34_eager_health_after_startup.py`

- New file. Three test functions (one per AC):
  - `test_AC34_1_health_returns_200_after_subprocess_serve_loop_entry` —
    spawn subprocess, poll `/health`, assert 200 + `workspace_root`
    field within 5s budget. No MCP session opened.
  - Note: AC34.2 (no-regression on AC24.x + AC29.x) and AC34.3
    (seal-diff scope) are satisfied by the existing tests
    (`test_service.py`, `test_AC29_*.py`, `test_no_sealed_amendments.py`)
    continuing to pass after the source edit. AC34.2 and AC34.3
    explicit assertion tests live in this file as named-AC tests
    that delegate verification to the existing surfaces.

The plan §6 names AC34.2 and AC34.3 as named tests with the
`test_AC34_<n>_*` naming convention. Builder-decision: AC34.2 is a
test that imports + runs the AC24.* and AC29.* tests programmatically
and asserts they all pass — but pytest already runs them as part of
the suite, so a separate "no regression" test would duplicate the
suite's own verification. Builder-decision: AC34.2 is satisfied by the
suite-level "all tests green" gate; AC34.3 is satisfied by the existing
seal-diff test (`test_no_sealed_amendments.py::test_B20_*`).

To honour the dispatch's "three new tests, one per AC, named for the
AC" requirement, the new test file carries three top-level test
functions:

  1. `test_AC34_1_health_returns_200_after_subprocess_serve_loop_entry`
     — subprocess + HTTP GET, the empirical claim.
  2. `test_AC34_2_no_regression_on_AC24_and_AC29` — imports the AC24
     lifespan test and the AC29.5 health-workspace-root test functions
     and runs them inline; asserts no exceptions raised. The suite-level
     run of those tests is the primary gate; this named-AC test is a
     pointer-to-evidence so the AC34.2 outcome is callable by name.
  3. `test_AC34_3_seal_diff_only_memory_system_changed` — invokes
     `git diff --name-only BASELINE..HEAD` from the test, asserts every
     changed path begins with `memory-system/` or matches an admitted
     universal path. The existing `test_no_sealed_amendments.py`
     covers the sealed surface; this test duplicates its assertion
     under an AC34-named function so the AC34.3 outcome is also
     callable by name.

### `memory-system/tests/test_no_sealed_amendments.py`

- Update `BASELINE` constant via `pos-amend apply` to `045f6db`
  (the commit immediately preceding amendment #34 — mirrors amendment
  #29's HEAD~1 BASELINE pattern, narrowing the diff window to
  amendment-#34-only surfaces and avoiding spurious cross-component
  reports from intervening commits #31/#32/#33). Comment block adds
  the amendment #34 entry.
- `SEAL_COMMIT` sidecar lands at the amendment commit SHA on the
  amendment commit (empty-diff window) and advances to the seal-commit
  SHA via `pos-amend seal`.

### `docs/rebuild/plans/amendment-34-memory-system-eager-lifespan-d1-conformance.manifest.yaml`

- New file. Single-component manifest. Schema mirrors amendment #30.
- BASELINE: `795768c` (memory-system's prior seal commit).
- Single component entry: memory-system, `frozen_baseline: false`,
  `extra_allowed_prefixes: []`.
- Universal-paths block: `docs/rebuild/plans/` prefix; CLAUDE.md and
  docs/odd-*.md and docs/rebuild/FUTURE_IDEAS.md files (mirror
  amendment #30's standard set).
- Narrative target: `memory-system/tests/SEAL_COMMIT.notes` (append).

### `docs/rebuild/plans/amendment-34-memory-system-eager-lifespan-d1-conformance.md`

- Append a "Method-decision record (D4 + D5)" section at the bottom
  recording the choices above, with one-line rationale each, and the
  amendment + seal commit SHAs (filled at seal time).

## 3. Order

1. Write this builder-plan to disk (done).
2. Manifest YAML → disk.
3. Source edit (`service.py`).
4. Test file → disk.
5. Run the memory-system test suite locally — green or surface failure.
6. `pos-amend apply --dry-run <manifest>` — green.
7. `pos-amend apply <manifest>` (no `--dry-run`) — applies
   BASELINE/sidecar/narrative changes.
8. Commit (amendment commit). Stage: source + new test + manifest +
   plan + builder-plan + sidecar/baseline updates from pos-amend.
9. `pos-amend seal <manifest>` — sidecar advance to the amendment SHA;
   narrative append.
10. Commit (seal commit). Stage: sidecar bump + narrative append.
11. Final verification: re-run memory-system suite, run seal-diff
    tests on every other sealed component (`test_no_sealed_amendments.py`
    or `test_cross_cutting.py` per the component).
12. Append D4/D5 method-decision record + commit SHAs to the
    plan doc, commit as a docs follow-up if needed (or fold into the
    seal commit's body).

## 4. Halt triggers (builder side)

Per dispatch:
- AC34.1's subprocess test exhibits flakiness > 1 retry → halt + surface.
- pos-amend dry-run produces unexpected diffs → halt + surface.
- Any sealed component outside memory-system shows a diff → halt +
  surface (D3 violation).
- 60-minute wall-clock budget exceeded → halt + surface.
