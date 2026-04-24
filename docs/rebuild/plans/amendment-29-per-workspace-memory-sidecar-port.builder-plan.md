# Builder plan — Amendment #29: per-workspace memory-sidecar port +
# workspace-identity health probe

**Amendment number resolved:** 29 (next sequential after #28; prior #29
"session-orientation-context" was retracted 2026-04-23 per commit
`c7ddb51`; number reclaimed per owner ruling 2026-04-24).

**BASELINE (pre-amendment tip):** `b0e3152b5ff5a5c7809d80264094ef5d4ce8e8fc`
(docs: add duration estimation rubric for AI-driven tasks).

**Working directory:** `/Users/lukeivers/ivers-corp-pos-v2/`.

**Binding amendment plan:**
`docs/rebuild/plans/amendment-29-per-workspace-memory-sidecar-port.md`
(ACs AC29.1–AC29.7 are authoritative).

This builder-plan enumerates the files, symbols, and test names I will
touch. Every entry maps 1:1 to an AC29.x criterion (or to a §2.5-
compliant support artefact). The builder-plan itself does not widen
the ACs.

---

## 1. AC-to-file-and-symbol map

| AC | File(s) touched | Symbol(s) added/changed | Test name(s) |
|----|-----------------|-------------------------|--------------|
| AC29.1 | `memory-system/src/service.py` | (no signature change; `_build_mcp()` already reads `GRAPHITI_SERVICE_PORT`). `health` tool + `/health` Starlette route gain `workspace_root` field resolved from `POS_V2_WORKSPACE_ROOT` env var. | `memory-system/tests/test_AC29_service_port_binding.py::test_AC29_1_service_port_reflects_env_var_across_distinct_values` |
| AC29.2 | `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` (`_LAUNCHD_TEMPLATES["memory-graphiti"]` gains `GRAPHITI_SERVICE_PORT` + `GRAPHITI_SERVICE_HOST` + `POS_V2_WORKSPACE_ROOT` in `EnvironmentVariables`; `_install_service_manager_files` gains a `port:int` arg; `run_first_run_scaffold` resolves the port from `~/.pos/memory.yaml` if pre-existing, else defaults + writes the default into the freshly-scaffolded `memory.yaml`). `_MEMORY_YAML` stays as a template default; the scaffold reads-back-or-writes-through the yaml file's `port` value. | `workspace-bootstrap/tests/test_AC29_scaffold_memory_port.py::test_AC29_2_scaffold_propagates_memory_yaml_port_to_plist_and_inventory` |
| AC29.3 | `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` (same seam — the scaffold already reads per-workspace `pos_root`; this AC verifies isolation between two concurrent scaffold invocations). | `workspace-bootstrap/tests/test_AC29_scaffold_memory_port.py::test_AC29_3_distinct_workspace_configs_produce_distinct_plist_ports` |
| AC29.4 | No new source. Integration-style test that spawns two `python -m src.service`-style subprocesses under distinct `GRAPHITI_SERVICE_PORT` env values on 127.0.0.1 loopback and asserts both bind. | `memory-system/tests/test_AC29_service_port_binding.py::test_AC29_4_two_subprocesses_bind_distinct_ports_without_eaddrinuse` |
| AC29.5 | (a) `memory-system/src/service.py`: `_impl_health` returns a `workspace_root` field resolved from `os.environ.get("POS_V2_WORKSPACE_ROOT")`. (b) `hands-off-lifecycle/hooks/first_run_helper.py`: `_probe_http` and `_service_health` extended to optionally verify the response body's `workspace_root` matches the probing workspace's own root; a new `_probe_http_with_identity(host, port, path, timeout_s, expected_workspace_root)` helper covers the identity check. `_poll_services_healthy` passes the current workspace root through. | `memory-system/tests/test_AC29_health_workspace_identity.py::test_AC29_5_health_response_carries_workspace_root` + `hands-off-lifecycle/tests/test_AC29_health_workspace_probe.py::test_AC29_5_probe_fails_on_workspace_identity_mismatch` + `hands-off-lifecycle/tests/test_AC29_health_workspace_probe.py::test_AC29_5_probe_succeeds_on_workspace_identity_match` |
| AC29.6 | N/A — seal-diff discipline enforced by the existing three seal-diff tests (memory-system, workspace-bootstrap, hands-off-lifecycle) after BASELINE advance. | Exercised by existing `test_B20_*` in each component's `test_no_sealed_amendments.py` + `test_H19_*` in `test_cross_cutting.py` — no new test added; the manifest's universal-paths and allowed-prefixes widen to admit this amendment's in-scope paths. |
| AC29.7 | N/A — preservation is exercised by keeping existing test suites green. No code path changes the AC6 label-derivation, AC28 state-routing, or AC24 MCP tool surface. | Existing `test_AC6_*`, `test_AC10_*..test_AC14_*`, and `test_AC24_*` tests stay green in the post-amendment full-suite runs on the three touched components. |

§2.5 forward+reverse check:

- Forward: each behaviour in the amendment-plan §1 objective (port
  isolation; probe identity match) + each AC has at least one test.
- Reverse: every edit in every file above is cited against a specific
  AC above; no incidental edits.

## 2. File-by-file edit enumeration

### 2.1 `memory-system/src/service.py` (AC29.5 primary; AC29.1 already
covered by existing env-var read)

Edit summary:

- `_impl_health` adds one new key `"workspace_root"` to the returned
  dict, resolved via `os.environ.get("POS_V2_WORKSPACE_ROOT", "")`.
  Empty string is the explicit "no workspace identity configured"
  value — probes that require identity treat it as mismatch.
- The module-level `mcp = _build_mcp()` stays unchanged; it already
  reads `GRAPHITI_SERVICE_PORT` at construction (AC29.1).
- No changes to tool signatures, no new MCP tools, no transport
  changes, no env-var renames. AC24's four-tool surface is preserved
  by construction.

### 2.2 `memory-system/tests/test_AC29_service_port_binding.py` (new file; AC29.1, AC29.4)

- `test_AC29_1_service_port_reflects_env_var_across_distinct_values`:
  `monkeypatch.setenv` each of two distinct ports (e.g. 18765, 18766),
  call `service._build_mcp()`, assert `mcp_instance.settings.port`
  equals the env value per call. Mirrors the existing AC24.6 test
  pattern.
- `test_AC29_4_two_subprocesses_bind_distinct_ports_without_eaddrinuse`:
  pick two free ephemeral ports via `socket.socket().bind((127.0.0.1, 0))`;
  spawn two subprocess instances via `[sys.executable, "-c", <inline
  probe script>]` where the probe script imports
  `starlette.applications.Starlette`, binds the declared host+port via
  `uvicorn.Server` (OR, since FastMCP wraps `uvicorn`, directly call
  the service via `python -m src.service` with env vars but stubbing
  `make_graphiti`). To keep the test CI-friendly without the full
  graphiti init path: use the FastMCP `run_streamable_http_async` on
  a stub server OR simply bind two `socket.socket` instances with
  `SO_REUSEADDR` off, proving the port-bind regression class at the
  OS-socket layer. Builder choice: follow the amendment plan's
  explicit "subprocess-spawn test" language and spawn `python -m
  src.service` with a fake-graphiti monkeypatch applied via a small
  test-fixture script. The subprocess's `_build_mcp()` constructs the
  FastMCP instance; the test calls `.run_streamable_http_async()` on
  the fresh instance via an inline fixture script that stubs
  `make_graphiti` and exits once the listen socket is open. Two such
  subprocesses on distinct env ports on 127.0.0.1 prove the bind
  succeeds. Implementation refinement is builder's call; the
  acceptance is "both bind their declared ports without EADDRINUSE."

### 2.3 `memory-system/tests/test_AC29_health_workspace_identity.py` (new file; AC29.5 memory-system side)

- `test_AC29_5_health_response_carries_workspace_root`:
  `monkeypatch.setenv("POS_V2_WORKSPACE_ROOT", "/tmp/alpha")`, construct
  a fake graphiti via the same `_impl_health` tool path, assert the
  returned dict contains `"workspace_root": "/tmp/alpha"`.

### 2.4 `memory-system/tests/integration/coexistence.sh` (new docs file; AC29.4 manual-repro companion)

Per the amendment plan §AC29.4: a documented manual-repro script for
full-stack coexistence. Operators run by hand post-amendment to verify
the claude-authed + Ollama-reachable + both-`/health`-200-concurrently
story. Not a CI gate. §2.5 backing: AC29.4 explicitly carves out the
documented manual script.

### 2.5 `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` (AC29.2, AC29.3)

Edit summary:

- `_LAUNCHD_TEMPLATES["memory-graphiti"]`: `EnvironmentVariables` dict
  grows keys `GRAPHITI_SERVICE_HOST`, `GRAPHITI_SERVICE_PORT`, and
  `POS_V2_WORKSPACE_ROOT`. Template placeholders: `{host}`, `{port}`,
  `{workspace}` (reusing the existing `{workspace}` placeholder for
  workspace_root and `{label}` placeholder already in template).
- `_install_service_manager_files` gains `host: str`, `port: int`
  kwargs and passes them into the template `.format(...)` call.
- `run_first_run_scaffold` adds a config read-back step for
  `memory.yaml`: resolves `pos_root/memory.yaml` (written by the
  scaffold earlier in the same invocation) → reads `port` + `host`
  via `yaml.safe_load` → passes them to
  `_install_service_manager_files`. If `memory.yaml` hasn't been
  written yet in this invocation (partial_recovery path where the
  user deleted it), default to the `_MEMORY_YAML` constant's
  declared values.
- The `_MEMORY_YAML` constant itself remains unchanged (still declares
  `port: 8765` as the starter default) — workspaces that want a
  different port edit `memory.yaml` per the existing "Edit any file
  to adjust" contract. This preserves the no-forced-migration pattern
  from amendment #28 §6 flagged inference #2.

Note on port-derivation method: **the amendment plan's D3 ruling
(S1) says "per-workspace port via memory.yaml seam"** — it does NOT
mandate slug-derivation vs ordinal-assignment vs static-default. This
builder-plan picks the simplest §2.5-compliant shape: the scaffold
writes `8765` into every fresh `memory.yaml` (matching current
behaviour); the user (or a later amendment under Idea 9) owns
disambiguation. AC29.3's test simulates two workspaces with distinct
ports by pre-seeding each workspace's `memory.yaml` with a distinct
value before the scaffold runs — this exercises the propagation seam
end-to-end without prescribing a port-assignment policy the ACs do
not name.

### 2.6 `workspace-bootstrap/tests/test_AC29_scaffold_memory_port.py` (new file; AC29.2, AC29.3)

- `test_AC29_2_scaffold_propagates_memory_yaml_port_to_plist_and_inventory`:
  pre-seed `pos_root/memory.yaml` with `port: 19876`, invoke
  `run_first_run_scaffold(...)`, assert the emitted plist's
  `EnvironmentVariables` block contains `GRAPHITI_SERVICE_PORT` with
  value `19876`.
- `test_AC29_3_distinct_workspace_configs_produce_distinct_plist_ports`:
  pre-seed two separate `pos_root`s with distinct `memory.yaml` port
  values (e.g. 19876 and 19877). Invoke the scaffold twice with
  distinct `workspace_root` + distinct `pos_root`. Assert the two
  emitted plists carry the two distinct port values.

### 2.7 `hands-off-lifecycle/hooks/first_run_helper.py` (AC29.5 probe side)

Edit summary:

- Add `_probe_http_with_identity(host, port, path, timeout_s, *,
  expected_workspace_root)` helper. It parses the response body as
  JSON and asserts the body's `workspace_root` equals the expected
  value; returns False if absent or mismatched.
- `_service_health` threads an optional `expected_workspace_root`
  through from caller; when present and `kind == "http"`, routes to
  the new helper.
- `_poll_services_healthy` gets an optional
  `expected_workspace_root: str | None` kwarg that defaults to None
  (preserves amendment #6/#24 callers that don't need identity).
- The `_run_bootstrap`'s phase-4b call site passes the dispatched
  `pos_v2_root` as the expected workspace root for the memory
  service probe. Orchestrator's `unix_socket` health path is
  unchanged — identity enforcement is narrowly scoped to the HTTP
  probe path (the orchestrator's socket path is already workspace-
  scoped by the existing unix-socket design and is out of this
  amendment's scope).

### 2.8 `hands-off-lifecycle/tests/test_AC29_health_workspace_probe.py` (new file; AC29.5 probe side)

- `test_AC29_5_probe_fails_on_workspace_identity_mismatch`: spin up a
  `http.server.BaseHTTPRequestHandler` stub on an ephemeral local port
  that returns 200 with body `{"status":"ok","workspace_root":
  "/tmp/beta"}`. Call `_probe_http_with_identity(...,
  expected_workspace_root="/tmp/alpha")`. Assert False.
- `test_AC29_5_probe_succeeds_on_workspace_identity_match`: same stub
  but body `{"status":"ok","workspace_root":"/tmp/alpha"}`. Call with
  `expected_workspace_root="/tmp/alpha"`. Assert True.

### 2.9 `first-run-inventory.yaml` (workspace-level manifest)

- No edit required for AC29.2 per-se: the inventory declares
  `port: 8765` as a default; the scaffold's new propagation path does
  not require removing that declaration. The inventory's `port` is
  consumed only at phase-4b probe time (hands-off-lifecycle's
  helper). Since the helper now accepts the expected-workspace-root
  through the scaffold's config, no inventory change is load-bearing.
- Optional: note in the inventory header that workspace-local port
  overrides live in `~/.pos/memory.yaml`. Defer to AC29.2's natural
  shape — if keeping the inventory's `port` unchanged doesn't block
  AC29.2's propagation test, leave it alone (matches the "delete if
  not objective-backed" §2.5 rule; leaving 8765 as a default is
  objective-backed by AC29.4's "runs on 127.0.0.1 with distinct
  ports" story).

### 2.10 Manifest + plan renames

- Plan path stays as `docs/rebuild/plans/amendment-29-per-workspace-memory-sidecar-port.md`
  (no rename — `#29` is the resolved number).
- New manifest:
  `docs/rebuild/plans/amendment-29-per-workspace-memory-sidecar-port.manifest.yaml`.
- Narrative target:
  `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run` (appended).

## 3. Commit order

1. Amendment commit with message
   `fix(memory-system, workspace-bootstrap, hands-off-lifecycle): per-workspace memory-sidecar port + workspace-identity health probe — amendment #29`.
   Contents:
   - All source edits (§2.1, §2.5, §2.7).
   - All new test files (§2.2–§2.3, §2.6, §2.8).
   - `coexistence.sh` manual-repro script.
   - BASELINE advances in the three seal-diff tests
     (memory-system, workspace-bootstrap; hands-off-lifecycle's H19
     is frozen per amendment #23).
   - Allowed-prefix widenings per manifest.
   - SEAL_COMMIT sidecars written to baseline SHA
     (`b0e3152b5ff5a5c7809d80264094ef5d4ce8e8fc`, 7-char `b0e3152`)
     by `pos-amend apply`.
   - Amendment plan + manifest + this builder plan.
2. `pos-amend apply --dry-run` exit 0 gate.
3. Seal commit via `pos-amend seal` with message
   `chore(seals): per-workspace-memory-port seal — memory-system + workspace-bootstrap + hands-off-lifecycle at <amendment-sha>`.
   Contents (auto-generated by the CLI):
   - SEAL_COMMIT sidecars advanced to amendment SHA.
   - Narrative stanza appended to
     `hands-off-lifecycle/seals/SEAL_COMMIT.true-first-run`.
4. Post-seal verification:
   `pos-amend apply --dry-run` still exit 0; seal-diff tests green.

## 4. Halt-trigger watchlist

- If `_LAUNCHD_TEMPLATES` template-format changes require touching
  `orchestrator/` plist (e.g., to add `POS_V2_WORKSPACE_ROOT`), halt
  — that is a fourth sealed component. (Scope: memory-graphiti plist
  only.)
- If AC29.4's subprocess test cannot run without touching a fourth
  sealed surface (e.g., `orchestrator`'s supervisor probe), halt.
- If the stub HTTP server for AC29.5 requires cross-component wiring
  (e.g., via orchestrator's observability aggregator), halt.
- If the `yaml.safe_load` import inside `first_run_scaffold` would
  conflict with the hands-off-lifecycle subprocess runner's stdlib-
  only constraint (it should not — the scaffold runs under the
  shared venv where PyYAML is present, per amendment #5's subprocess
  rewrite), halt.

## 5. §2.5 audit — reverse pass

Files/symbols this plan adds but does not cite an AC for: none.
Every edit in §2 maps to an AC column in §1.

Tests this plan adds but does not cite an AC for: none. Every test
name in §1 matches the ACs listed.

Dependencies added: none. The yaml-safe-load path already exists in
`workspace-bootstrap/src/workspace_bootstrap/adapters/memory_system.py`;
the scaffold adapter re-uses that dep. The `http.server` stdlib
module used in AC29.5's probe-side test is stdlib-only.

## 6. Binding of method-level choices

Per ODD §1.1, method is the builder's call. The choices locked in
this builder-plan and their rationale:

1. **Port source is a pre-seeded `memory.yaml` per workspace, not a
   slug-derived function.** The amendment plan's D3 ruling (S1) was
   "per-workspace port via memory.yaml seam" — the seam is the
   config file, not a derivation algorithm. §2.5 forbids code that
   implements slug-hashing without an AC backing it; the simplest
   §2.5-compliant shape writes the default (8765) into every fresh
   `memory.yaml` and lets the user (or a future Idea 9 cycle) edit
   it. AC29.3's test demonstrates the propagation seam is
   workspace-local by pre-seeding distinct values rather than
   asserting a derivation formula.
2. **Workspace identity on the health response is
   `POS_V2_WORKSPACE_ROOT` env var.** The launchd plist's
   `EnvironmentVariables` dict already carries `PYTHONUNBUFFERED`
   and will gain `GRAPHITI_SERVICE_PORT`; adding
   `POS_V2_WORKSPACE_ROOT` to the same dict is the cheapest seam.
   The service reads it at `_impl_health` time; absence is treated
   as empty-string (explicit "unknown"), not a crash — structural
   refusal via Pydantic would be over-reach for a health payload
   field.
3. **AC29.4 subprocess shape: FastMCP instance construction +
   `run_streamable_http_async`, with `make_graphiti` monkeypatched
   to return a fake.** The amendment plan's "subprocess-bind-only"
   shape rules out full graphiti init; stubbing the graphiti
   construction keeps the test focused on the port-bind regression
   class while honouring the plan's CI-friendly constraint.
4. **No changes to the `orchestrator` plist template.** The
   orchestrator service's port/host are not in scope; AC29.2–29.3
   target `memory-graphiti` specifically.

## 7. Estimated cost

- LOC delta: ~300–450 across source + tests.
- New test count: 6 new test functions (AC29.1, AC29.2, AC29.3,
  AC29.4, AC29.5 × 3 — but AC29.5 is split memory-system + hands-off-
  lifecycle; total 5 test functions + 1 memory-system-side stub
  `test_AC29_5_health_response_carries_workspace_root`).
- Wall-time estimate (per duration-rubric): 25–40 minutes. Bounded
  by amendment-plan halt trigger #5 at 90 minutes.
