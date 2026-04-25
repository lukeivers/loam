# Builder-plan — Amendment #47: workspace-local `.mcp.json` writer

Authored 2026-04-25 by build agent.
Companion to umbrella plan
`docs/rebuild/plans/memory-into-context-integration.md` §4b.
Files + symbols this build will touch; every entry maps 1:1 to an
AC47.x criterion (or to a §2.5-compliant support artefact).

---

## 1. Pre-edit gate verified

- **HEAD at dispatch:** `3096016` (`docs(plans): record amendment #46
  commit SHAs in method-decision register`).
- **Sibling amendment #46 sealed:** seal commit `2f44bbb`, amendment
  commit `6e1cb0c`, corrective `de678f5`. Primary-persona's
  `session_start_emitter.py`, `cli.py session-start`/`user-prompt-submit`,
  and `hands-off-lifecycle`'s SessionStart + UserPromptSubmit
  registrations are in place. #47's surface is independent of #46.
- **Per-workspace memory port (#29 surface) is accessible from
  workspace-bootstrap scaffold layer.** `first_run_scaffold.py`
  already exposes `_resolve_memory_host_port(memory_yaml_path)`
  (added by amendment #29) which reads `(host, port)` from
  `<pos_root>/memory.yaml`. The scaffold's plist-installation step
  already consumes it. The `.mcp.json` writer is a sibling consumer
  of the same read-back. **Halt trigger 1 NOT triggered.**
- **`.mcp.json` schema for streamable-HTTP transport confirmed** from
  `https://code.claude.com/docs/en/mcp` (fetched mid-dispatch). The
  JSON shape is `{"mcpServers": {"<name>": {"type": "http", "url":
  "<url>"}}}`. Note: the `--transport streamable-http` value is the
  CLI flag; inside `.mcp.json` the literal value is `"http"`. The
  FastMCP service exposes its streamable-HTTP endpoint at the
  default mount `/mcp` (verified by inspecting
  `mcp.server.fastmcp.FastMCP().settings.streamable_http_path`
  inside `memory-system/.venv` — value `/mcp`). **Halt trigger 2
  NOT triggered.**
- **BASELINE for this amendment:** `3096016` — current HEAD
  (HEAD~1 of the upcoming amendment commit; mirrors the amendment
  #29/#34/#35/#36/#37/#39/#42 BASELINE-as-HEAD~1 pattern).
  Workspace-bootstrap's current `BASELINE` literal is
  `294a90e85b06aef699445b81e7ffa5f9fd0f1f73` (the pre-#42 tip);
  amendment #47 advances it to `3096016` so the BASELINE..HEAD diff
  scope is narrowed to amendment #47 only and avoids spurious
  cross-component "missing admission" reports for unrelated
  intervening commits (#43-#46).

## 2. D-build choices (refining umbrella §6)

- **D-build.1 — `.mcp.json` location.** `<workspace>/.mcp.json` —
  workspace-local, project-scope (per Claude Code MCP scope
  table). Already locked by umbrella D4 (workspace-local).
- **D-build.2 — JSON shape.** Single key `"mcpServers"` at top
  level, with one entry. The entry's keys are `"type": "http"`
  and `"url": "http://<host>:<port>/mcp"`. No headers, no oauth,
  no env block — the local FastMCP service is unauthenticated on
  loopback. Shape from Claude Code docs §4.3 / project-scoped
  example. Note: the `mcpServers` object plus a single entry is
  the minimum well-formed `.mcp.json` Claude Code accepts.
- **D-build.3 — Server name.** `memory-graphiti` — matches the
  workspace's launchd service kind (`service_label("memory-
  graphiti", slug)`) and the umbrella plan's name. Tools become
  callable as `mcp__memory-graphiti__<tool>` per Claude Code
  convention. The slug is NOT included in the server name — the
  scope is workspace-local, so the JSON file is per-workspace by
  construction; no cross-workspace name collision concern.
- **D-build.4 — Deep-merge algorithm.** Read existing
  `.mcp.json` if present; parse via `json.loads`; if the result
  is not a dict, surface a structured diagnostic and skip the
  write (preserve user content). Otherwise, set
  `data.setdefault("mcpServers", {})["memory-graphiti"] =
  <our-entry>`. Other top-level keys are left untouched; other
  `mcpServers` entries are left untouched. This is the no-clobber
  contract per AC47.2. Mirrors amendment #37's
  `merge_session_start` shape at the JSON-merge level.
- **D-build.5 — Port-source seam.** Reuse
  `_resolve_memory_host_port(memory_yaml_path)`. The scaffold
  invokes the `.mcp.json` writer with the resolved
  `(memory_host, memory_port)` already computed in
  `run_first_run_scaffold` (same values used for the launchd
  plist's `EnvironmentVariables`). No new port-discovery code.
- **D-build.6 — Idempotency on equal content.** If the merged
  output equals the on-disk content byte-for-byte, the writer
  skips the write (no mtime churn) — matches amendment #36's
  idempotency contract for the persona directory and amendment
  #37's idempotency contract for the agent file.
- **D-build.7 — Atomic write.** Write to a sibling
  `.mcp.json.tmp`, then `os.rename` into final position. Matches
  amendment #37's `agent_file_authoring.py` pattern. Avoids
  partial-write torn states if interrupted.
- **D-build.8 — Failure surface.** Any IO error or malformed
  pre-existing `.mcp.json` is caught locally; the writer returns
  a `MCPJsonWriteResult(wrote: bool, reason: str, path: Path)`
  dataclass with structured outcome. The scaffold consumes the
  result and stores it on `ScaffoldResult` so first-run completes
  and the SessionStart hook proceeds (AC47.3). Mirrors
  amendment #37's `AgentFileWriteResult` shape.
- **D-build.9 — `ScaffoldResult` extension.** Three new fields:
  `mcp_json_path: Path | None`, `mcp_json_wrote: bool`,
  `mcp_json_reason: str | None`. Matches amendment #36's
  `persona_dir`/`persona_installed` extension shape.
- **D-build.10 — AC47.S seal-diff.** Single-component amendment;
  manifest lists only `workspace-bootstrap`. `frozen_baseline:
  false` (workspace-bootstrap is not the H19-frozen component).
  No edits to other sealed components.

## 3. AC-to-file-and-symbol map

| AC | File(s) touched | Symbol(s) added/changed | Test name(s) |
|----|-----------------|-------------------------|--------------|
| AC47.1 | `workspace-bootstrap/src/workspace_bootstrap/adapters/mcp_json_writer.py` (new), `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py` (modified) | New module: `MCPJsonWriteResult`, `MEMORY_GRAPHITI_SERVER_NAME`, `build_memory_graphiti_entry(host, port)`, `merge_mcp_json(existing, host, port)`, `write_mcp_json(workspace_root, host, port)`. Modified scaffold: `run_first_run_scaffold(...)` invokes the writer after persona-directory install + before tracker-seed; `ScaffoldResult` gains `mcp_json_path`, `mcp_json_wrote`, `mcp_json_reason` fields. | `test_AC47_1_fresh_clone_writes_mcp_json.py` |
| AC47.2 | Same writer module + scaffold | (same as above) | `test_AC47_2_deep_merge_preserves_user_entries.py` |
| AC47.3 | Same writer module + scaffold | (same as above; failure-class branches) | `test_AC47_3_write_failure_graceful.py` |
| AC47.4 | All edits in this amendment | n/a (review-side audit) | Exercised by §2.5 reverse-direction audit + the seal-diff test. |
| AC47.S | `workspace-bootstrap/tests/test_no_sealed_amendments.py` (BASELINE bump), `workspace-bootstrap/tests/SEAL_COMMIT` (sidecar via pos-amend) | BASELINE literal advances `294a90e85` → `3096016`; new comment block documenting amendment #47's window. | `test_no_sealed_amendments.py` (existing test runs at new BASELINE) + per-component `test_no_sealed_amendments.py` / `test_cross_cutting.py` sweep across every other sealed component (no edits there). |

§2.5 forward+reverse check:

- **Forward:** every behaviour in umbrella §4b objective + every AC47.x
  has at least one test (AC47.1 → fresh-clone write; AC47.2 → deep-
  merge; AC47.3 → graceful-write-failure; AC47.4 → review audit;
  AC47.S → seal-diff).
- **Reverse:** every edit in every file above is cited against a
  specific AC47.x; no incidental edits, no defensive branches without
  a backing AC.

## 4. Files this build will touch

### 4.1 New source

- `workspace-bootstrap/src/workspace_bootstrap/adapters/mcp_json_writer.py`
  — pure-function `.mcp.json` writer with deep-merge + structured
  result. Stdlib-only (`json`, `pathlib`, `dataclasses`,
  `tempfile`, `os`). No imports from other workspace-bootstrap
  adapters. Exports:
  - `MEMORY_GRAPHITI_SERVER_NAME = "memory-graphiti"` — server name
    constant.
  - `MCP_JSON_FILENAME = ".mcp.json"` — workspace-local filename.
  - `STREAMABLE_HTTP_PATH = "/mcp"` — FastMCP default mount path
    confirmed against `memory-system/.venv` import inspection.
  - `MCPJsonWriteResult(wrote: bool, reason: str, path: Path)`
    dataclass — observable outcome surface for AC47.1/AC47.3.
    Reason strings: `"fresh_write"`, `"merged"`,
    `"already_current"`, `"skipped_malformed_existing"`,
    `"skipped_io_error"`.
  - `build_memory_graphiti_entry(*, host: str, port: int) -> dict`
    — pure function returning the JSON entry shape `{"type":
    "http", "url": "http://<host>:<port>/mcp"}`.
  - `merge_mcp_json(existing: dict, *, host: str, port: int) ->
    dict` — pure function returning the deep-merged dict. Sets
    `result.setdefault("mcpServers", {})["memory-graphiti"] =
    build_memory_graphiti_entry(...)`. Other top-level keys and
    other `mcpServers` entries are preserved by reference (no
    mutation of input; returns a new dict-of-dict).
  - `write_mcp_json(*, workspace_root: Path, host: str, port: int)
    -> MCPJsonWriteResult` — IO entrypoint. Reads existing file
    if present; parses JSON; on parse failure or non-dict root,
    returns `MCPJsonWriteResult(wrote=False,
    reason="skipped_malformed_existing", path=...)` without
    overwriting. On IO/permissions error during write, returns
    `MCPJsonWriteResult(wrote=False, reason="skipped_io_error",
    path=...)` with the error attached via the data field of a
    structured diagnostic logged to stderr (caught at the
    boundary so `first_run_scaffold` never raises). Atomic write
    via `.tmp` + `os.rename`. On equal-content idempotent re-run,
    skips the rename + returns `reason="already_current"`.

### 4.2 Modified source

- `workspace-bootstrap/src/workspace_bootstrap/adapters/first_run_scaffold.py`:
  - Import `mcp_json_writer` lazily inside the helper that
    invokes it (mirrors the lazy `tracker_seed` import pattern at
    line 718; keeps the module's import graph acyclic).
  - Add a new helper `_run_mcp_json_writer(*, workspace_root,
    memory_host, memory_port) -> MCPJsonWriteResult`.
  - Inside `run_first_run_scaffold(...)`: invoke the new helper
    after the persona-directory install (line ~657) and before
    the tracker-seed step (line ~673). The helper consumes the
    `(memory_host, memory_port)` already computed at line ~624
    via `_resolve_memory_host_port(pos_root / "memory.yaml")`. No
    new port-discovery code path.
  - Extend `ScaffoldResult` with three fields:
    `mcp_json_path: Path | None = None`,
    `mcp_json_wrote: bool = False`,
    `mcp_json_reason: str | None = None`.
  - Wire the result into the returned `ScaffoldResult(...)`
    construction.

### 4.3 Modified tests

- `workspace-bootstrap/tests/test_no_sealed_amendments.py`:
  BASELINE literal advances from `294a90e85b06aef699445b81e7ffa5f9fd0f1f73`
  to `3096016` (the pre-amendment-#47 tip). Append a comment block
  documenting amendment #47's window (mirrors the existing comment
  blocks for #4/#6/#7/#17/#31/#36/#39/#42).
- `workspace-bootstrap/tests/SEAL_COMMIT`: sidecar advances via
  `pos-amend apply` to amendment commit, then via `pos-amend seal`
  to seal commit.

### 4.4 New tests

- `workspace-bootstrap/tests/test_AC47_1_fresh_clone_writes_mcp_json.py`
  — drive `run_first_run_scaffold` against a clean tmp workspace +
  pos_root; assert `<workspace>/.mcp.json` exists; parse the JSON;
  assert structure `{"mcpServers": {"memory-graphiti": {"type":
  "http", "url": "http://<host>:<port>/mcp"}}}`; assert the URL's
  port equals the value seeded in `memory.yaml`.
- `workspace-bootstrap/tests/test_AC47_2_deep_merge_preserves_user_entries.py`
  — pre-write a `<workspace>/.mcp.json` carrying an unrelated
  user-added MCP server entry (e.g. `{"mcpServers": {"my-tool":
  {"type": "stdio", "command": "/usr/local/bin/my-tool"}}}` plus a
  user-added top-level key like `"_comment": "user note"`). Run
  the scaffold with the partial-recovery seam. Assert the user
  entry is unchanged AND the `memory-graphiti` entry was added.
  Assert other top-level keys are untouched. Re-run a second time
  and assert the file content is byte-equal (idempotency on
  no-op).
- `workspace-bootstrap/tests/test_AC47_3_write_failure_graceful.py`
  — two negative cases:
  1. Malformed pre-existing `.mcp.json` (invalid JSON syntax or
     a top-level array). Assert the writer returns
     `wrote=False`, `reason="skipped_malformed_existing"`; the
     pre-existing file is not overwritten; the scaffold completes
     (returns `ScaffoldResult` with `ran=True`).
  2. Read-only workspace dir simulating permission denied (use
     `os.chmod` on the workspace root or substitute via a
     monkeypatched `Path.write_text` that raises `PermissionError`).
     Assert `wrote=False`, `reason="skipped_io_error"`; the
     scaffold returns successfully; `mcp_json_reason` surfaced on
     the result.

### 4.5 New/modified non-source

- `docs/rebuild/plans/amendment-47-workspace-local-mcp-json-writer.manifest.yaml`
  — pos-amend manifest (single-component, frozen_baseline: false).
- `workspace-bootstrap/seals/SEAL_COMMIT.mcp-json-writer` — narrative
  authored by `pos-amend seal`.

## 5. JSON output shape (the literal `.mcp.json` written)

After amendment #47 lands, a freshly-scaffolded workspace's
`.mcp.json` contains:

```json
{
  "mcpServers": {
    "memory-graphiti": {
      "type": "http",
      "url": "http://127.0.0.1:8765/mcp"
    }
  }
}
```

The `127.0.0.1:8765` defaults are sourced from the workspace's
`<pos_root>/memory.yaml` (per amendment #29's per-workspace port
allocation; the read-back is `_resolve_memory_host_port`). On a
workspace whose `memory.yaml` declares a different port (e.g.
`port: 19877`), the URL becomes `http://127.0.0.1:19877/mcp`.

When deep-merging into a user-authored `.mcp.json` that already
carries other entries, the user's entries are preserved; the
`memory-graphiti` entry is added or overwritten in-place (the
overwrite covers AC47.2's "re-run replaces our entry but leaves
user entries alone" — the framework owns the `memory-graphiti`
key identity, the user owns every other key).

## 6. Idempotency contract

- Fresh-clone first-run: writes `.mcp.json` with the single
  `memory-graphiti` entry; `MCPJsonWriteResult(wrote=True,
  reason="fresh_write")`.
- Re-run with no user entries and our entry already current:
  byte-equal merge result; skip write;
  `MCPJsonWriteResult(wrote=False, reason="already_current")`.
- Re-run with user entries already present: deep-merge; if our
  entry is current and unchanged, skip write
  (`reason="already_current"`); if our entry was missing or stale
  (port changed), write with merged content
  (`reason="merged"`).
- Malformed pre-existing file: skip write, preserve user content;
  `reason="skipped_malformed_existing"`.
- IO/permissions error: skip write, surface diagnostic;
  `reason="skipped_io_error"`. Scaffold completes, SessionStart
  hook proceeds.

## 7. Test scope

- **workspace-bootstrap full suite** — required green. Existing
  ~150 tests + 3 new AC47 tests.
- **Cross-component seal-diff sweep** — every other sealed
  component's `test_no_sealed_amendments.py` (or
  `test_cross_cutting.py` for hands-off-lifecycle) green at its
  pinned `SEAL_COMMIT`. No source edits to other components, so
  they should pass by construction.
- **Skip pre-seal full-suite rerun** per
  `feedback_amendment_dispatch_speedups`.
- `pos-amend apply --dry-run` green prereq (hard, per amendment
  #22 + dispatch).

## 8. Halt triggers reaffirmed

Per umbrella §4b halt list. None active at dispatch time:

1. ~~Per-workspace port not accessible from scaffold layer~~ — NOT
   triggered. `_resolve_memory_host_port` is in place since #29.
2. ~~`.mcp.json` schema not determinable from docs in 30 min~~ —
   NOT triggered. Schema confirmed from
   `https://code.claude.com/docs/en/mcp` mid-dispatch.
3. ~~Sealed component outside fence in diff~~ — to be enforced by
   AC47.S seal-diff test + pos-amend cross-component sweep at
   seal time.

If any §2.5 violation surfaces in surrounding code during the
build, halt-and-surface per the dispatch's explicit ODD-violation
clause; do not silently extend.

## 9. Out-of-scope (named per ODD §2.5)

Per umbrella §4c:

- Persona-side memory_client wiring (UserPromptSubmit eager
  retrieval). #47 only writes `.mcp.json` for Claude-Code MCP
  tools; the Python memory client construction is a future
  amendment.
- Auto-memory ↔ graphiti unification.
- Memory seeding (`kuzu_db` has only test fixtures; real memories
  accumulate through use).
- Cross-workspace memory keying.
- Multi-MCP-server registration (a future amendment may compose
  more entries; #47 ships exactly one).

## 10. Pos-amend bookkeeping flow

1. Author manifest at
   `docs/rebuild/plans/amendment-47-workspace-local-mcp-json-writer.manifest.yaml`
   with `baseline: 3096016`, single-component
   (`workspace-bootstrap`, `frozen_baseline: false`,
   `extra_allowed_prefixes: []`), universal-paths block, narrative
   target `workspace-bootstrap/seals/SEAL_COMMIT.mcp-json-writer`.
2. Author all source edits + tests; commit as the amendment
   commit on branch `pos-v2`.
3. `pos-amend apply --dry-run <manifest>` — must exit 0. This
   reports any missing seal-diff admissions before the apply.
4. `pos-amend apply <manifest>` — advances BASELINE literal +
   widens seal-diff bindings + writes SEAL_COMMIT sidecar
   (empty-diff window).
5. `pos-amend seal --plan-doc
   /Users/lukeivers/ivers-corp-pos-v2/docs/rebuild/plans/amendment-47-workspace-local-mcp-json-writer.builder-plan.md
   <manifest>` — runs the scoped test sweep, creates the seal
   commit, advances SEAL_COMMIT to the seal commit, appends
   §14 SHA backfill + follow-up commit.
6. Verify: `pos-amend apply --dry-run <manifest>` exits 0
   against post-seal HEAD.

## 11. Seal-diff window

- BASELINE: `3096016` (this amendment's pre-amendment tip).
- Allowed paths under the seal-diff window:
  - `workspace-bootstrap/src/`
  - `workspace-bootstrap/tests/`
  - `workspace-bootstrap/seals/`
  - Universal admissions: `docs/rebuild/plans/`, `CLAUDE.md`,
    `docs/odd-in-pos.md`, `docs/odd-methodology.md`,
    `docs/rebuild/FUTURE_IDEAS.md`.

---

## 14. Method-decision record (builder, post-build)

The plan §6 left D-build choices to the builder. This section
records the choices made and rationale, plus test breakdown and
commit SHAs.

### D-build.1 — `.mcp.json` location: `<workspace>/.mcp.json`

(Locked by umbrella D4. Project-scope per Claude Code MCP scope
table.)

### D-build.2 — JSON shape: minimal `mcpServers` with one entry

`{"type": "http", "url": "http://<host>:<port>/mcp"}`. Confirmed
from Claude Code docs §4.3. The CLI flag value
`streamable-http` does NOT appear in the JSON; the JSON's `type`
field is the literal string `"http"`.

### D-build.3 — Server name: `memory-graphiti`

Matches launchd kind + umbrella plan name. Tools become
`mcp__memory-graphiti__<tool>` per Claude Code convention.

### D-build.4 — Deep-merge algorithm

`json.loads` existing file → ensure dict → set
`data.setdefault("mcpServers", {})["memory-graphiti"] = entry`.
Other keys preserved. Mirrors amendment #37's
`merge_session_start` shape at the JSON-merge level.

### D-build.5 — Port-source seam: reuse `_resolve_memory_host_port`

No new port-discovery code; the scaffold already computes
`(memory_host, memory_port)` for the launchd plist's
`EnvironmentVariables`. The `.mcp.json` writer is a sibling
consumer of the same value.

### D-build.6 — Idempotency on equal content

Byte-equal merge → skip write. Matches amendment #36 (persona)
+ #37 (agent file) idempotency contracts.

### D-build.7 — Atomic write

`.tmp` + `os.rename`. Matches amendment #37's
`agent_file_authoring.py` pattern.

### D-build.8 — Failure surface

`MCPJsonWriteResult(wrote, reason, path)` dataclass; scaffold
consumes; first-run completes regardless of write outcome.
Matches amendment #37's `AgentFileWriteResult` shape.

### D-build.9 — `ScaffoldResult` extension

Three new fields: `mcp_json_path`, `mcp_json_wrote`,
`mcp_json_reason`. Matches amendment #36's persona-field
extension shape.

### D-build.10 — AC47.S seal-diff

Single-component manifest, `frozen_baseline: false`. No edits to
other sealed components.

### Test breakdown

(populated post-build)

### Commit-SHAs

(populated by `pos-amend seal --plan-doc` post-seal)
